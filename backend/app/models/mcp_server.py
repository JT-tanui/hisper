"""
MCP Server model definitions
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from ..core.database import Base


class MCPServer(Base):
    """MCP Server database model"""
    __tablename__ = "mcp_servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    repository_url = Column(String(500))
    package_manager = Column(String(50))  # npm, pip, cargo, etc.
    package_name = Column(String(255))
    version = Column(String(50))
    author = Column(String(255))
    license = Column(String(100))
    
    # Capabilities and metadata
    capabilities = Column(JSON)  # List of capabilities/tools provided
    categories = Column(JSON)    # Categories/tags for the server
    server_metadata = Column(JSON)      # Additional metadata
    
    # Status and health
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    health_status = Column(String(20), default="unknown")  # healthy, unhealthy, unknown
    last_health_check = Column(DateTime)
    response_time_ms = Column(Float)
    
    # Discovery information
    discovered_from = Column(String(100))  # github, npm, pypi, manual
    discovery_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<MCPServer(name='{self.name}', url='{self.url}')>"


# Pydantic models for API
class MCPServerBase(BaseModel):
    """Base MCP Server schema"""
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    url: str = Field(..., description="Server URL or connection string")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    package_manager: Optional[str] = Field(None, description="Package manager (npm, pip, etc.)")
    package_name: Optional[str] = Field(None, description="Package name")
    version: Optional[str] = Field(None, description="Server version")
    author: Optional[str] = Field(None, description="Author name")
    license: Optional[str] = Field(None, description="License type")
    capabilities: Optional[List[str]] = Field(default_factory=list, description="Server capabilities")
    categories: Optional[List[str]] = Field(default_factory=list, description="Server categories")
    server_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MCPServerCreate(MCPServerBase):
    """Schema for creating MCP Server"""
    discovered_from: Optional[str] = Field(None, description="Discovery source")


class MCPServerUpdate(BaseModel):
    """Schema for updating MCP Server"""
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    repository_url: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    server_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class MCPServerResponse(MCPServerBase):
    """Schema for MCP Server response"""
    id: int
    is_active: bool
    is_verified: bool
    health_status: str
    last_health_check: Optional[datetime]
    response_time_ms: Optional[float]
    discovered_from: Optional[str]
    discovery_date: datetime
    last_updated: datetime
    usage_count: int
    success_rate: float
    
    class Config:
        from_attributes = True


class MCPServerHealth(BaseModel):
    """Schema for server health information"""
    server_id: int
    status: str  # healthy, unhealthy, unknown
    response_time_ms: Optional[float]
    last_check: datetime
    error_message: Optional[str] = None
    capabilities_verified: bool = False


class MCPServerStats(BaseModel):
    """Schema for server statistics"""
    total_servers: int
    active_servers: int
    healthy_servers: int
    categories: Dict[str, int]
    package_managers: Dict[str, int]
    discovery_sources: Dict[str, int]