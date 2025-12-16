"""
Task management API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..core.database import get_sync_db
from ..core.security import get_current_tenant_context, require_role
from ..models.task import (
    Task, TaskCreate, TaskUpdate, TaskResponse, TaskExecution,
    TaskStats, TaskQueue, TaskStatus, TaskPriority
)
from ..models.mcp_server import MCPServer
from ..models.auth import Role

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of tasks to return"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    category: Optional[str] = Query(None, description="Filter by task category"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    db: Session = Depends(get_sync_db),
    request=Depends(get_current_tenant_context)
):
    """Get list of tasks with optional filtering"""
    query = db.query(Task).filter(Task.tenant_id == request.state.tenant_id)
    
    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    if category:
        query = query.filter(Task.category == category)
    
    if user_id:
        query = query.filter(Task.user_id == user_id)
    
    if session_id:
        query = query.filter(Task.session_id == session_id)
    
    # Order by priority and creation time
    priority_order = {
        TaskPriority.URGENT: 4,
        TaskPriority.HIGH: 3,
        TaskPriority.NORMAL: 2,
        TaskPriority.LOW: 1
    }
    
    query = query.order_by(desc(Task.created_at))
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_sync_db),
    request=Depends(get_current_tenant_context)
):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == request.state.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_sync_db),
    request=Depends(require_role(Role.OPERATOR)),
):
    """Create a new task"""
    payload = task.dict()
    payload["tenant_id"] = request.state.tenant_id
    db_task = Task(**payload)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Schedule task execution in background
    background_tasks.add_task(execute_task_background, db_task.id)
    
    return db_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, 
    task_update: TaskUpdate, 
    db: Session = Depends(get_sync_db),
    request=Depends(require_role(Role.OPERATOR)),
):
    """Update an existing task"""
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == request.state.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_sync_db),
    request=Depends(require_role(Role.ADMIN)),
):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == request.state.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Only allow deletion of completed, failed, or cancelled tasks
    if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete pending or running tasks. Cancel the task first."
        )
    
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: int,
    execution: TaskExecution,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_sync_db),
    request=Depends(require_role(Role.OPERATOR)),
):
    """Execute or re-execute a task"""
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == request.state.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if task can be executed
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Task is already running")
    
    if task.status == TaskStatus.FAILED and task.retry_count >= task.max_retries and not execution.force_retry:
        raise HTTPException(
            status_code=400, 
            detail="Task has exceeded maximum retries. Use force_retry=true to retry anyway."
        )
    
    # Update task status
    task.status = TaskStatus.PENDING
    if execution.server_id:
        task.assigned_server_id = execution.server_id
    
    db.commit()
    
    # Schedule task execution in background
    background_tasks.add_task(execute_task_background, task.id)
    
    return {"message": "Task execution scheduled", "task_id": task_id}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    db: Session = Depends(get_sync_db),
    request=Depends(require_role(Role.OPERATOR)),
):
    """Cancel a pending or running task"""
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == request.state.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail="Can only cancel pending or running tasks"
        )
    
    task.status = TaskStatus.CANCELLED
    db.commit()
    
    return {"message": "Task cancelled", "task_id": task_id}


@router.get("/stats/overview", response_model=TaskStats)
async def get_task_stats(
    db: Session = Depends(get_sync_db),
    request=Depends(get_current_tenant_context)
):
    """Get overview statistics for tasks"""
    scoped = db.query(Task).filter(Task.tenant_id == request.state.tenant_id)
    total_tasks = scoped.count()
    pending_tasks = scoped.filter(Task.status == TaskStatus.PENDING).count()
    running_tasks = scoped.filter(Task.status == TaskStatus.RUNNING).count()
    completed_tasks = scoped.filter(Task.status == TaskStatus.COMPLETED).count()
    failed_tasks = scoped.filter(Task.status == TaskStatus.FAILED).count()
    
    # Calculate average execution time
    avg_execution_time = db.query(func.avg(Task.execution_time_ms)).filter(
        Task.execution_time_ms.isnot(None)
    ).scalar() or 0.0
    
    # Calculate success rate
    success_rate = 0.0
    if total_tasks > 0:
        success_rate = (completed_tasks / total_tasks) * 100
    
    # Get tasks by category
    tasks_by_category = {}
    category_results = scoped.with_entities(Task.category, func.count(Task.id)).group_by(Task.category).all()
    for category, count in category_results:
        if category:
            tasks_by_category[category] = count
    
    # Get tasks by priority
    tasks_by_priority = {}
    priority_results = scoped.with_entities(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    for priority, count in priority_results:
        tasks_by_priority[priority] = count
    
    return TaskStats(
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        running_tasks=running_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        average_execution_time_ms=avg_execution_time,
        success_rate=success_rate,
        tasks_by_category=tasks_by_category,
        tasks_by_priority=tasks_by_priority
    )


@router.get("/queue/status", response_model=TaskQueue)
async def get_task_queue(
    db: Session = Depends(get_sync_db),
    request=Depends(get_current_tenant_context)
):
    """Get current task queue status"""
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING, Task.tenant_id == request.state.tenant_id).order_by(Task.created_at).all()
    running_tasks = db.query(Task).filter(Task.status == TaskStatus.RUNNING, Task.tenant_id == request.state.tenant_id).order_by(Task.started_at).all()
    
    # Estimate wait time based on average execution time and queue position
    avg_execution_time = db.query(func.avg(Task.execution_time_ms)).filter(
        Task.execution_time_ms.isnot(None)
    ).scalar() or 30000  # Default to 30 seconds
    
    estimated_wait_time_minutes = (len(pending_tasks) * avg_execution_time) / (1000 * 60)
    
    return TaskQueue(
        pending_tasks=pending_tasks,
        running_tasks=running_tasks,
        queue_length=len(pending_tasks),
        estimated_wait_time_minutes=estimated_wait_time_minutes
    )


@router.get("/categories/list")
async def get_task_categories(
    db: Session = Depends(get_sync_db),
    request=Depends(get_current_tenant_context)
):
    """Get list of all available task categories"""
    results = db.query(Task.category).filter(Task.tenant_id == request.state.tenant_id).distinct().all()
    categories = [cat[0] for cat in results if cat[0]]
    
    return {"categories": sorted(categories)}


async def execute_task_background(task_id: int):
    """Background task execution function"""
    # This would be implemented to actually execute the task
    # For now, it's a placeholder that simulates task execution
    
    from datetime import datetime
    import asyncio
    import random
    
    db = next(get_sync_db())
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        # Update task status to running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Simulate task execution
        await asyncio.sleep(random.uniform(1, 5))  # Random execution time
        
        # Simulate success/failure
        if random.random() > 0.2:  # 80% success rate
            task.status = TaskStatus.COMPLETED
            task.output_data = {"result": "Task completed successfully", "timestamp": datetime.utcnow().isoformat()}
        else:
            task.status = TaskStatus.FAILED
            task.error_message = "Simulated task failure"
            task.retry_count += 1
        
        task.completed_at = datetime.utcnow()
        task.execution_time_ms = (task.completed_at - task.started_at).total_seconds() * 1000
        
        # Update server usage statistics if assigned
        if task.assigned_server_id:
            server = db.query(MCPServer).filter(MCPServer.id == task.assigned_server_id).first()
            if server:
                server.usage_count += 1
                if task.status == TaskStatus.COMPLETED:
                    # Update success rate
                    total_tasks = db.query(func.count(Task.id)).filter(
                        Task.assigned_server_id == server.id,
                        Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED])
                    ).scalar()
                    successful_tasks = db.query(func.count(Task.id)).filter(
                        Task.assigned_server_id == server.id,
                        Task.status == TaskStatus.COMPLETED
                    ).scalar()
                    server.success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        db.commit()
        
    except Exception as e:
        # Handle execution errors
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()