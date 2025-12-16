"""Analytics and audit models scoped by tenant."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, JSON, String

from ..core.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), index=True, default="default")
    category = Column(String(100))
    action = Column(String(255))
    actor_id = Column(String(100))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalyticsEventCreate(BaseModel):
    category: str
    action: str
    metadata: Dict[str, str]
    actor_id: Optional[str] = None

