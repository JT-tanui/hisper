"""
Plugin registry model definitions
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from pydantic import BaseModel, Field

from ..core.database import Base


class Plugin(Base):
    """Database model for registered plugins"""

    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(50), default="0.0.0")
    description = Column(Text)
    plugin_type = Column(String(50))  # discovery, connector, analytics, ui
    entrypoint = Column(String(255))
    manifest_path = Column(String(500))
    enabled = Column(Boolean, default=True)
    status = Column(String(50), default="registered")
    capabilities = Column(JSON, default=list)
    ui_extensions = Column(JSON, default=dict)
    last_loaded = Column(DateTime)
    last_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Plugin(identifier='{self.identifier}', type='{self.plugin_type}')>"


class PluginCapability(BaseModel):
    """Descriptor for plugin capabilities"""

    kind: str = Field(..., description="Capability type (discovery, connector, analytics, ui)")
    description: Optional[str] = Field(None, description="What this capability provides")
    resources: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements or limitations")


class PluginManifest(BaseModel):
    """Manifest shared between backend and frontend"""

    identifier: str
    name: str
    version: str
    description: Optional[str] = None
    plugin_type: str = Field(..., description="Plugin family: discovery, connector, analytics, ui")
    entrypoint: Optional[str] = None
    manifest_path: Optional[str] = None
    capabilities: List[PluginCapability] = Field(default_factory=list)
    frontend: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class PluginRead(PluginManifest):
    """Schema returned by plugin registry endpoints"""

    id: int
    status: str
    enabled: bool
    last_loaded: Optional[datetime]
    last_error: Optional[str] = None

    class Config:
        from_attributes = True
