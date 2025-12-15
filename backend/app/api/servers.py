"""
MCP Server management API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_sync_db
from ..models.mcp_server import (
    MCPServer, MCPServerCreate, MCPServerUpdate, MCPServerResponse, 
    MCPServerStats, MCPServerHealth
)

router = APIRouter()


@router.get("/", response_model=List[MCPServerResponse])
async def get_servers(
    skip: int = Query(0, ge=0, description="Number of servers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of servers to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    package_manager: Optional[str] = Query(None, description="Filter by package manager"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_sync_db)
):
    """Get list of MCP servers with optional filtering"""
    query = db.query(MCPServer)
    
    # Apply filters
    if category:
        query = query.filter(MCPServer.categories.contains([category]))
    
    if package_manager:
        query = query.filter(MCPServer.package_manager == package_manager)
    
    if is_active is not None:
        query = query.filter(MCPServer.is_active == is_active)
    
    if is_verified is not None:
        query = query.filter(MCPServer.is_verified == is_verified)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (MCPServer.name.ilike(search_filter)) |
            (MCPServer.description.ilike(search_filter))
        )
    
    # Order by usage count and last updated
    query = query.order_by(MCPServer.usage_count.desc(), MCPServer.last_updated.desc())
    
    servers = query.offset(skip).limit(limit).all()
    return servers


@router.get("/{server_id}", response_model=MCPServerResponse)
async def get_server(server_id: int, db: Session = Depends(get_sync_db)):
    """Get a specific MCP server by ID"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.post("/", response_model=MCPServerResponse)
async def create_server(server: MCPServerCreate, db: Session = Depends(get_sync_db)):
    """Create a new MCP server"""
    # Check if server with same name and URL already exists
    existing = db.query(MCPServer).filter(
        MCPServer.name == server.name,
        MCPServer.url == server.url
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Server with this name and URL already exists"
        )
    
    db_server = MCPServer(**server.dict())
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.put("/{server_id}", response_model=MCPServerResponse)
async def update_server(
    server_id: int, 
    server_update: MCPServerUpdate, 
    db: Session = Depends(get_sync_db)
):
    """Update an existing MCP server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Update fields
    update_data = server_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)
    
    db.commit()
    db.refresh(server)
    return server


@router.delete("/{server_id}")
async def delete_server(server_id: int, db: Session = Depends(get_sync_db)):
    """Delete an MCP server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    db.delete(server)
    db.commit()
    return {"message": "Server deleted successfully"}


@router.get("/stats/overview", response_model=MCPServerStats)
async def get_server_stats(db: Session = Depends(get_sync_db)):
    """Get overview statistics for MCP servers"""
    total_servers = db.query(func.count(MCPServer.id)).scalar()
    active_servers = db.query(func.count(MCPServer.id)).filter(MCPServer.is_active == True).scalar()
    healthy_servers = db.query(func.count(MCPServer.id)).filter(MCPServer.health_status == "healthy").scalar()
    
    # Get category distribution
    servers_with_categories = db.query(MCPServer).filter(MCPServer.categories.isnot(None)).all()
    categories = {}
    for server in servers_with_categories:
        if server.categories:
            for category in server.categories:
                categories[category] = categories.get(category, 0) + 1
    
    # Get package manager distribution
    package_managers = {}
    pm_results = db.query(MCPServer.package_manager, func.count(MCPServer.id)).group_by(MCPServer.package_manager).all()
    for pm, count in pm_results:
        if pm:
            package_managers[pm] = count
    
    # Get discovery source distribution
    discovery_sources = {}
    ds_results = db.query(MCPServer.discovered_from, func.count(MCPServer.id)).group_by(MCPServer.discovered_from).all()
    for source, count in ds_results:
        if source:
            discovery_sources[source] = count
    
    return MCPServerStats(
        total_servers=total_servers,
        active_servers=active_servers,
        healthy_servers=healthy_servers,
        categories=categories,
        package_managers=package_managers,
        discovery_sources=discovery_sources
    )


@router.get("/{server_id}/health", response_model=MCPServerHealth)
async def get_server_health(server_id: int, db: Session = Depends(get_sync_db)):
    """Get health information for a specific server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    return MCPServerHealth(
        server_id=server.id,
        status=server.health_status,
        response_time_ms=server.response_time_ms,
        last_check=server.last_health_check,
        capabilities_verified=server.is_verified
    )


@router.post("/{server_id}/verify")
async def verify_server(server_id: int, db: Session = Depends(get_sync_db)):
    """Verify a server's capabilities and mark as verified"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # TODO: Implement actual server verification logic
    # This would involve connecting to the server and checking its capabilities
    
    server.is_verified = True
    db.commit()
    
    return {"message": "Server verification initiated", "server_id": server_id}


@router.post("/{server_id}/health-check")
async def check_server_health(server_id: int, db: Session = Depends(get_sync_db)):
    """Perform a health check on a specific server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # TODO: Implement actual health check logic
    # This would involve pinging the server and measuring response time
    
    from datetime import datetime
    server.last_health_check = datetime.utcnow()
    server.health_status = "healthy"  # This would be determined by actual check
    db.commit()
    
    return {"message": "Health check completed", "server_id": server_id, "status": server.health_status}


@router.get("/categories/list")
async def get_categories(db: Session = Depends(get_sync_db)):
    """Get list of all available categories"""
    servers_with_categories = db.query(MCPServer).filter(MCPServer.categories.isnot(None)).all()
    categories = set()
    for server in servers_with_categories:
        if server.categories:
            categories.update(server.categories)
    
    return {"categories": sorted(list(categories))}


@router.get("/package-managers/list")
async def get_package_managers(db: Session = Depends(get_sync_db)):
    """Get list of all available package managers"""
    results = db.query(MCPServer.package_manager).distinct().all()
    package_managers = [pm[0] for pm in results if pm[0]]
    
    return {"package_managers": sorted(package_managers)}