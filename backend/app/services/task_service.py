"""
Task Service
Handles task management, routing, and execution with LLM integration
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.task import Task, TaskCreate, TaskUpdate, TaskStatus, TaskPriority
from ..models.mcp_server import MCPServer
from ..core.database import get_db
from .llm_service import llm_service, LLMProvider
from .monitoring_service import monitoring_service

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing and executing tasks with AI/LLM integration"""
    
    def __init__(self):
        self.active_tasks: Dict[int, asyncio.Task] = {}
    
    async def create_task(self, db: AsyncSession, task_data: TaskCreate) -> Task:
        """Create a new task"""
        task = Task(
            title=task_data.title,
            description=task_data.description,
            server_id=task_data.server_id,
            priority=task_data.priority,
            parameters=task_data.parameters,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Created task {task.id}: {task.title}")
        
        # Start task execution in background
        execution_task = asyncio.create_task(self._execute_task_with_llm(task))
        self.active_tasks[task.id] = execution_task
        
        return task
    
    async def get_task(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        """Get a task by ID"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    async def get_tasks(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None
    ) -> List[Task]:
        """Get tasks with optional filtering"""
        query = select(Task)
        
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_task(self, db: AsyncSession, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """Update a task"""
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        update_data = task_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            await db.execute(
                update(Task)
                .where(Task.id == task_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(task)
        
        return task
    
    async def delete_task(self, db: AsyncSession, task_id: int) -> bool:
        """Delete a task"""
        task = await self.get_task(db, task_id)
        if not task:
            return False
        
        # Cancel if running
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
        
        await db.delete(task)
        await db.commit()
        
        logger.info(f"Deleted task {task_id}")
        return True
    
    async def _execute_task_with_llm(self, task: Task):
        """Execute a task using LLM for intelligent routing and execution"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting LLM-powered execution of task {task.id}")
            
            # Update status to running
            async for db in get_db():
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(status=TaskStatus.RUNNING, started_at=datetime.utcnow())
                )
                await db.commit()
                break
            
            # Get available MCP servers
            available_servers = await self._get_available_servers()
            
            if not available_servers:
                raise Exception("No MCP servers available for task execution")
            
            # Use LLM to analyze and execute the task
            result = await llm_service.process_task_with_llm(
                task=task,
                available_servers=available_servers,
                provider=LLMProvider.OPENROUTER,  # Default provider
                model="deepseek/deepseek-chat"    # Default model
            )
            
            # Update task with results
            duration_ms = (time.time() - start_time) * 1000
            
            if result.get("success", False):
                status = TaskStatus.COMPLETED
                error_message = None
            else:
                status = TaskStatus.FAILED
                error_message = result.get("error", "Unknown error")
            
            async for db in get_db():
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(
                        status=status,
                        completed_at=datetime.utcnow(),
                        result=result,
                        error_message=error_message
                    )
                )
                await db.commit()
                break
            
            # Record metrics
            monitoring_service.record_task_execution(
                task_id=task.id,
                status=status.value,
                priority=task.priority.value,
                duration_ms=duration_ms,
                success=result.get("success", False),
                error_message=error_message
            )
            
            logger.info(f"Completed task {task.id} with LLM in {duration_ms:.0f}ms")
            
        except asyncio.CancelledError:
            logger.info(f"Task {task.id} was cancelled")
            
            # Update status to cancelled
            async for db in get_db():
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(status=TaskStatus.CANCELLED)
                )
                await db.commit()
                break
            
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            monitoring_service.record_task_execution(
                task_id=task.id,
                status=TaskStatus.CANCELLED.value,
                priority=task.priority.value,
                duration_ms=duration_ms,
                success=False,
                error_message="Task cancelled"
            )
        
        except Exception as e:
            logger.error(f"Error executing task {task.id}: {e}")
            
            # Update status to failed
            async for db in get_db():
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(
                        status=TaskStatus.FAILED,
                        error_message=str(e)
                    )
                )
                await db.commit()
                break
            
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            monitoring_service.record_task_execution(
                task_id=task.id,
                status=TaskStatus.FAILED.value,
                priority=task.priority.value,
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
        
        finally:
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
    
    async def _get_available_servers(self) -> List[MCPServer]:
        """Get list of available MCP servers"""
        try:
            async for db in get_db():
                result = await db.execute(
                    select(MCPServer).where(MCPServer.is_active == True)
                )
                servers = result.scalars().all()
                return list(servers)
        except Exception as e:
            logger.error(f"Error getting available servers: {e}")
            return []
    
    async def execute_task_with_custom_llm(
        self,
        task_id: int,
        provider: LLMProvider,
        model: str
    ) -> Dict[str, Any]:
        """Execute a task with custom LLM provider and model"""
        try:
            async for db in get_db():
                task = await self.get_task(db, task_id)
                if not task:
                    return {"success": False, "error": "Task not found"}
                
                if task.status != TaskStatus.PENDING:
                    return {"success": False, "error": "Task is not in pending status"}
                
                # Get available servers
                available_servers = await self._get_available_servers()
                
                # Execute with custom LLM
                result = await llm_service.process_task_with_llm(
                    task=task,
                    available_servers=available_servers,
                    provider=provider,
                    model=model
                )
                
                # Update task status
                status = TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED
                await db.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(
                        status=status,
                        completed_at=datetime.utcnow(),
                        result=result,
                        error_message=result.get("error") if not result.get("success") else None
                    )
                )
                await db.commit()
                
                return result
                
        except Exception as e:
            logger.error(f"Error executing task {task_id} with custom LLM: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_task(self, task_id: int) -> Dict[str, Any]:
        """Analyze a task using LLM without executing it"""
        try:
            async for db in get_db():
                task = await self.get_task(db, task_id)
                if not task:
                    return {"error": "Task not found"}
                
                # Analyze task complexity and requirements
                analysis = await llm_service.analyze_task_complexity(task)
                return analysis
                
        except Exception as e:
            logger.error(f"Error analyzing task {task_id}: {e}")
            return {"error": str(e)}
    
    async def get_task_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get task statistics"""
        try:
            # Get counts by status
            stats = {}
            
            for status in TaskStatus:
                result = await db.execute(
                    select(Task).where(Task.status == status)
                )
                count = len(result.scalars().all())
                stats[f"{status.value}_tasks"] = count
            
            stats["active_tasks"] = len(self.active_tasks)
            stats["total_tasks"] = sum(v for k, v in stats.items() if k.endswith("_tasks"))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting task stats: {e}")
            return {
                "total_tasks": 0,
                "pending_tasks": 0,
                "running_tasks": len(self.active_tasks),
                "completed_tasks": 0,
                "failed_tasks": 0,
                "error": str(e)
            }
    
    async def retry_failed_task(self, task_id: int) -> Dict[str, Any]:
        """Retry a failed task"""
        try:
            async for db in get_db():
                task = await self.get_task(db, task_id)
                if not task:
                    return {"success": False, "error": "Task not found"}
                
                if task.status != TaskStatus.FAILED:
                    return {"success": False, "error": "Task is not in failed status"}
                
                # Reset task status
                await db.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(
                        status=TaskStatus.PENDING,
                        error_message=None,
                        result=None,
                        started_at=None,
                        completed_at=None,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # Start execution again
                execution_task = asyncio.create_task(self._execute_task_with_llm(task))
                self.active_tasks[task.id] = execution_task
                
                return {"success": True, "message": "Task retry initiated"}
                
        except Exception as e:
            logger.error(f"Error retrying task {task_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_task(self, task_id: int) -> Dict[str, Any]:
        """Cancel a running task"""
        try:
            if task_id in self.active_tasks:
                self.active_tasks[task_id].cancel()
                del self.active_tasks[task_id]
                
                async for db in get_db():
                    await db.execute(
                        update(Task)
                        .where(Task.id == task_id)
                        .values(status=TaskStatus.CANCELLED)
                    )
                    await db.commit()
                    break
                
                return {"success": True, "message": "Task cancelled"}
            else:
                return {"success": False, "error": "Task is not running"}
                
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_available_llm_providers(self) -> Dict[str, List[str]]:
        """Get available LLM providers and their models"""
        try:
            providers = {}
            
            for provider in LLMProvider:
                models = await llm_service.get_available_models(provider)
                providers[provider.value] = models
            
            return providers
            
        except Exception as e:
            logger.error(f"Error getting LLM providers: {e}")
            return {}


# Global task service instance
task_service = TaskService()