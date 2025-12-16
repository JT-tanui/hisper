"""
Hisper - MCP Server Discovery and Task Management Interface
Main FastAPI application entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from app.api import router as api_router
from app.core.config import settings
from app.core.database import init_db
from app.services.discovery_service import DiscoveryService
from app.services.websocket_manager import WebSocketManager
from app.services.monitoring_service import monitoring_service
from app.services.mcp_client import mcp_client
from app.services.plugin_service import PluginService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
websocket_manager = WebSocketManager()
discovery_service = DiscoveryService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Hisper application...")

    # Initialize database
    await init_db()

    # Load plugins and execute lifecycle hooks
    await app.state.plugin_service.load_plugins()

    # Start background services
    asyncio.create_task(discovery_service.start_periodic_discovery())
    
    # Start monitoring service
    if settings.MONITORING_ENABLED:
        await monitoring_service.start_monitoring()
        logger.info("Monitoring service started")
    
    logger.info("Hisper application started successfully")
    yield
    
    logger.info("Shutting down Hisper application...")
    await discovery_service.stop()
    await monitoring_service.stop_monitoring()
    await mcp_client.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Hisper - MCP Server Discovery Interface",
    description="An intelligent interface for discovering and managing MCP servers across various domains",
    version="1.0.0",
    lifespan=lifespan
)

app.state.settings = settings
app.state.plugin_sandboxes = {}
app.state.plugin_service = PluginService(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.broadcast(f"Echo: {data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "hisper",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hisper - MCP Server Discovery Interface</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .feature { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .api-link { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .api-link:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Hisper - MCP Server Discovery Interface</h1>
            <p>Welcome to Hisper, an intelligent interface for discovering and managing Model Context Protocol (MCP) servers across various domains.</p>
            
            <div class="feature">
                <h3>🔍 Server Discovery</h3>
                <p>Automatically discovers MCP servers from GitHub, npm, PyPI, and other sources</p>
            </div>
            
            <div class="feature">
                <h3>🎯 Intelligent Task Routing</h3>
                <p>Routes tasks to the most appropriate MCP servers based on their capabilities</p>
            </div>
            
            <div class="feature">
                <h3>📊 Real-time Monitoring</h3>
                <p>Monitor server health, performance, and task execution in real-time</p>
            </div>
            
            <div class="feature">
                <h3>🌐 Web Interface</h3>
                <p>User-friendly web interface for managing servers and tasks</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/docs" class="api-link">📚 API Documentation</a>
                <a href="/api/v1/servers" class="api-link">🖥️ View Servers</a>
                <a href="/api/v1/tasks" class="api-link">📋 View Tasks</a>
            </div>
        </div>
    </body>
    </html>
    """)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=12000,
        reload=True,
        log_level="info"
    )