"""JWT-based security helpers with tenant scoping and RBAC checks."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_sync_db
from ..models.auth import Role, TokenPayload, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, tenant_id: str, role: Role, expires_delta: Optional[int] = None) -> str:
    expire_minutes = expires_delta or 60 * 24
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": subject, "tenant_id": tenant_id, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as exc:  # pragma: no cover - handled by FastAPI response
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def get_current_user(request: Request, db: Session = Depends(get_sync_db)) -> User:
    """Extract the current user from the Authorization header and attach tenant context."""

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = auth_header.split()[1]
    payload = _decode_token(token)

    user = db.query(User).filter(User.id == int(payload.sub), User.tenant_id == payload.tenant_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found for tenant")

    request.state.tenant_id = payload.tenant_id
    request.state.role = payload.role
    return user


def require_role(required: Role):
    """Dependency factory enforcing RBAC role ordering."""

    def dependency(request: Request = Depends(get_current_user)):
        # get_current_user ensures request.state.role is populated
        role_value = getattr(request.state, "role", None)
        # Simple ordering: admin > operator > analyst
        hierarchy = {Role.ADMIN.value: 3, Role.OPERATOR.value: 2, Role.ANALYST.value: 1}
        if hierarchy.get(role_value, 0) < hierarchy[required.value]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for action")
        return request

    return dependency


def get_current_tenant_context(request: Request) -> Request:
    """Ensure tenant id is available on request state."""

    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return request

    explicit_header = request.headers.get("X-Tenant-ID")
    if explicit_header:
        request.state.tenant_id = explicit_header
        return request

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context missing")

