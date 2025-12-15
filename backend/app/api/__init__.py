"""
API routes module
"""

from fastapi import APIRouter

from .servers import router as servers_router
from .tasks import router as tasks_router
from .discovery import router as discovery_router
from .llm import router as llm_router
from .monitoring import router as monitoring_router
from .mcp import router as mcp_router
from .chat import router as chat_router
from .settings import router as settings_router

router = APIRouter()

router.include_router(servers_router, prefix="/servers", tags=["servers"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
router.include_router(llm_router, prefix="/llm", tags=["llm"])
router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
router.include_router(mcp_router, prefix="/mcp", tags=["mcp"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])