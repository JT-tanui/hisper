"""
Discovery management API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_sync_db
from ..services.discovery_service import DiscoveryService

router = APIRouter()

# Global discovery service instance
discovery_service = DiscoveryService()


class ManualDiscoveryRequest(BaseModel):
    """Request model for manual server discovery"""
    url: str
    name: Optional[str] = None


class DiscoveryStatusResponse(BaseModel):
    """Response model for discovery status"""
    is_running: bool
    last_discovery: Optional[str] = None
    total_discovered: int
    sources: dict


@router.post("/start")
async def start_discovery(background_tasks: BackgroundTasks):
    """Start the discovery process"""
    if discovery_service.is_running:
        raise HTTPException(status_code=400, detail="Discovery is already running")
    
    background_tasks.add_task(discovery_service.start_periodic_discovery)
    
    return {"message": "Discovery process started"}


@router.post("/stop")
async def stop_discovery():
    """Stop the discovery process"""
    if not discovery_service.is_running:
        raise HTTPException(status_code=400, detail="Discovery is not running")
    
    await discovery_service.stop()
    
    return {"message": "Discovery process stopped"}


@router.post("/run-once")
async def run_discovery_once(background_tasks: BackgroundTasks):
    """Run discovery once immediately"""
    background_tasks.add_task(discovery_service.discover_all_sources)
    
    return {"message": "One-time discovery started"}


@router.post("/discover-github")
async def discover_from_github(background_tasks: BackgroundTasks):
    """Discover servers from GitHub only"""
    background_tasks.add_task(discovery_service.discover_from_github)
    
    return {"message": "GitHub discovery started"}


@router.post("/discover-npm")
async def discover_from_npm(background_tasks: BackgroundTasks):
    """Discover servers from npm registry only"""
    background_tasks.add_task(discovery_service.discover_from_npm)
    
    return {"message": "npm discovery started"}


@router.post("/discover-pypi")
async def discover_from_pypi(background_tasks: BackgroundTasks):
    """Discover servers from PyPI only"""
    background_tasks.add_task(discovery_service.discover_from_pypi)
    
    return {"message": "PyPI discovery started"}


@router.post("/manual")
async def manual_discovery(
    request: ManualDiscoveryRequest,
    background_tasks: BackgroundTasks
):
    """Manually add a server for discovery"""
    background_tasks.add_task(
        discovery_service.manual_discovery,
        request.url,
        request.name
    )
    
    return {
        "message": "Manual discovery initiated",
        "url": request.url,
        "name": request.name
    }


@router.get("/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status(db: Session = Depends(get_sync_db)):
    """Get current discovery status"""
    from ..models.mcp_server import MCPServer
    from sqlalchemy import func
    
    # Get total discovered servers
    total_discovered = db.query(func.count(MCPServer.id)).scalar()
    
    # Get servers by discovery source
    sources = {}
    source_results = db.query(
        MCPServer.discovered_from, 
        func.count(MCPServer.id)
    ).group_by(MCPServer.discovered_from).all()
    
    for source, count in source_results:
        if source:
            sources[source] = count
    
    return DiscoveryStatusResponse(
        is_running=discovery_service.is_running,
        total_discovered=total_discovered,
        sources=sources
    )


@router.get("/sources")
async def get_discovery_sources():
    """Get available discovery sources and their status"""
    return {
        "sources": [
            {
                "name": "github",
                "description": "GitHub repositories with MCP server implementations",
                "enabled": True,
                "requires_token": True,
                "token_configured": bool(discovery_service.client.headers.get("Authorization"))
            },
            {
                "name": "npm",
                "description": "npm packages for MCP servers",
                "enabled": True,
                "requires_token": False,
                "token_configured": True
            },
            {
                "name": "pypi",
                "description": "Python packages for MCP servers",
                "enabled": True,
                "requires_token": False,
                "token_configured": True
            },
            {
                "name": "manual",
                "description": "Manually added servers",
                "enabled": True,
                "requires_token": False,
                "token_configured": True
            }
        ]
    }


@router.get("/history")
async def get_discovery_history(
    limit: int = 50,
    db: Session = Depends(get_sync_db)
):
    """Get discovery history"""
    from ..models.mcp_server import MCPServer
    
    recent_discoveries = db.query(MCPServer).order_by(
        MCPServer.discovery_date.desc()
    ).limit(limit).all()
    
    return {
        "recent_discoveries": [
            {
                "id": server.id,
                "name": server.name,
                "url": server.url,
                "discovered_from": server.discovered_from,
                "discovery_date": server.discovery_date,
                "is_active": server.is_active,
                "is_verified": server.is_verified
            }
            for server in recent_discoveries
        ]
    }


@router.delete("/clear-unverified")
async def clear_unverified_servers(db: Session = Depends(get_sync_db)):
    """Clear all unverified servers from the database"""
    from ..models.mcp_server import MCPServer
    
    deleted_count = db.query(MCPServer).filter(
        MCPServer.is_verified == False
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Cleared {deleted_count} unverified servers",
        "deleted_count": deleted_count
    }


@router.post("/verify-all")
async def verify_all_servers(background_tasks: BackgroundTasks):
    """Start verification process for all discovered servers"""
    # This would implement actual server verification
    # For now, it's a placeholder
    
    return {"message": "Server verification process started"}


@router.get("/config")
async def get_discovery_config():
    """Get current discovery configuration"""
    from ..core.config import settings
    
    return {
        "discovery_interval_minutes": settings.DISCOVERY_INTERVAL_MINUTES,
        "max_concurrent_discoveries": settings.MAX_CONCURRENT_DISCOVERIES,
        "github_token_configured": bool(settings.GITHUB_TOKEN),
        "npm_registry_url": settings.NPM_REGISTRY_URL,
        "pypi_url": settings.PYPI_URL
    }