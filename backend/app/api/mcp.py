"""
MCP Client API endpoints
Handles MCP server connections and tool execution
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.mcp_client import mcp_client
from ..services.monitoring_service import monitoring_service
from ..models.mcp_server import MCPServer
from sqlalchemy import select

router = APIRouter()


class ToolExecutionRequest(BaseModel):
    server_id: int
    tool_name: str
    arguments: Dict[str, Any] = {}


class ServerConnectionRequest(BaseModel):
    server_id: int


@router.post("/connect")
async def connect_to_server(
    request: ServerConnectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Connect to an MCP server"""
    try:
        # Get server from database
        result = await db.execute(select(MCPServer).where(MCPServer.id == request.server_id))
        server = result.scalar_one_or_none()
        
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Attempt connection
        success = await mcp_client.connect_to_server(server)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully connected to {server.name}",
                "server_id": server.id,
                "server_name": server.name
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect to server {server.name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_from_server(request: ServerConnectionRequest):
    """Disconnect from an MCP server"""
    try:
        await mcp_client.disconnect_from_server(request.server_id)
        return {
            "success": True,
            "message": f"Disconnected from server {request.server_id}",
            "server_id": request.server_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def get_active_connections():
    """Get list of active MCP server connections"""
    try:
        connections = []
        for server_id, connection in mcp_client.active_connections.items():
            connections.append({
                "server_id": server_id,
                "connection_type": connection.get("type", "unknown"),
                "status": "connected"
            })
        
        return {
            "active_connections": connections,
            "total_connections": len(connections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/tools")
async def list_server_tools(server_id: int):
    """List available tools from an MCP server"""
    try:
        tools = await mcp_client.list_tools(server_id)
        return {
            "server_id": server_id,
            "tools": tools,
            "tool_count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-tool")
async def execute_tool(request: ToolExecutionRequest):
    """Execute a tool on an MCP server"""
    try:
        import time
        start_time = time.time()
        
        result = await mcp_client.execute_tool(
            server_id=request.server_id,
            tool_name=request.tool_name,
            arguments=request.arguments
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        monitoring_service.record_server_request(
            server_id=request.server_id,
            server_name=f"server_{request.server_id}",
            success=True,
            response_time_ms=response_time_ms
        )
        
        return {
            "success": True,
            "server_id": request.server_id,
            "tool_name": request.tool_name,
            "result": result,
            "response_time_ms": response_time_ms
        }
        
    except Exception as e:
        # Record failed request
        monitoring_service.record_server_request(
            server_id=request.server_id,
            server_name=f"server_{request.server_id}",
            success=False,
            response_time_ms=0
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/capabilities")
async def get_server_capabilities(server_id: int):
    """Get capabilities of an MCP server"""
    try:
        capabilities = await mcp_client.get_server_capabilities(server_id)
        return {
            "server_id": server_id,
            "capabilities": capabilities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/health")
async def check_server_health(server_id: int):
    """Perform health check on an MCP server"""
    try:
        health = await mcp_client.health_check(server_id)
        return {
            "server_id": server_id,
            "health": health
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_connections():
    """Clean up all MCP connections"""
    try:
        await mcp_client.cleanup()
        return {
            "success": True,
            "message": "All MCP connections cleaned up"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_mcp_status():
    """Get MCP client status"""
    try:
        return {
            "active_connections": len(mcp_client.active_connections),
            "server_processes": len(mcp_client.server_processes),
            "connections": list(mcp_client.active_connections.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))