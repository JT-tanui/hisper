"""Authentication and authorization models with tenant support."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class Role(str, Enum):
    """Supported role names for RBAC."""

    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"


class Tenant(Base):
    """Tenant/organization container."""

    __tablename__ = "tenants"

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"


class Organization(Base):
    """Organization model tied to a tenant."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(String(100), ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant")


class User(Base):
    """User account scoped to a tenant with a single role."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default=Role.OPERATOR)
    tenant_id = Column(String(100), ForeignKey("tenants.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    tenant = relationship("Tenant")
    organization = relationship("Organization")

    def __repr__(self) -> str:
        return f"<User(email={self.email}, role={self.role}, tenant={self.tenant_id})>"


# Pydantic schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    role: Role
    exp: int


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8)
    tenant_id: str = Field(..., description="Tenant identifier")
    organization_id: Optional[int] = None
    role: Role = Role.OPERATOR


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: Role
    tenant_id: str
    organization_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

