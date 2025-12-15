"""
Task model definitions for MCP server task management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from ..core.database import Base


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """Task database model"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Task execution details
    status = Column(String(20), default=TaskStatus.PENDING)
    priority = Column(String(10), default=TaskPriority.NORMAL)
    
    # Input and output
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    
    # Server assignment
    assigned_server_id = Column(Integer, ForeignKey("mcp_servers.id"))
    assigned_server = relationship("MCPServer", backref="tasks")
    
    # Execution metadata
    execution_time_ms = Column(Float)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User and session info
    user_id = Column(String(100))  # For future user management
    session_id = Column(String(100))
    
    # Task categorization
    category = Column(String(100))
    tags = Column(JSON)  # List of tags
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


# Pydantic models for API
class TaskBase(BaseModel):
    """Base Task schema"""
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="Task priority")
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task input data")
    category: Optional[str] = Field(None, description="Task category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Task tags")
    max_retries: int = Field(3, description="Maximum retry attempts")


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    assigned_server_id: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: int
    status: TaskStatus
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    assigned_server_id: Optional[int]
    execution_time_ms: Optional[float]
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    
    class Config:
        from_attributes = True


class TaskExecution(BaseModel):
    """Schema for task execution request"""
    task_id: int
    server_id: Optional[int] = Field(None, description="Specific server to use (optional)")
    force_retry: bool = Field(False, description="Force retry even if max retries reached")


class TaskStats(BaseModel):
    """Schema for task statistics"""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_execution_time_ms: float
    success_rate: float
    tasks_by_category: Dict[str, int]
    tasks_by_priority: Dict[str, int]


class TaskQueue(BaseModel):
    """Schema for task queue information"""
    pending_tasks: List[TaskResponse]
    running_tasks: List[TaskResponse]
    queue_length: int
    estimated_wait_time_minutes: float