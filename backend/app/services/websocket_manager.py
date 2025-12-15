"""
WebSocket connection manager for real-time updates
"""

import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": None
        }
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_info.pop(websocket, None)
            logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def send_personal_json(self, data: Dict[str, Any], websocket: WebSocket):
        """Send JSON data to a specific WebSocket connection"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending personal JSON: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast JSON data to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting JSON: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_user(self, user_id: str, data: Dict[str, Any]):
        """Broadcast data to all connections for a specific user"""
        user_connections = [
            conn for conn, info in self.connection_info.items()
            if info.get("user_id") == user_id
        ]
        
        disconnected = []
        for connection in user_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def notify_server_discovered(self, server_data: Dict[str, Any]):
        """Notify all clients about a newly discovered server"""
        await self.broadcast_json({
            "type": "server_discovered",
            "data": server_data
        })
    
    async def notify_server_health_update(self, server_id: int, health_data: Dict[str, Any]):
        """Notify all clients about server health updates"""
        await self.broadcast_json({
            "type": "server_health_update",
            "server_id": server_id,
            "data": health_data
        })
    
    async def notify_task_update(self, task_data: Dict[str, Any]):
        """Notify all clients about task updates"""
        await self.broadcast_json({
            "type": "task_update",
            "data": task_data
        })
    
    async def notify_task_completed(self, task_data: Dict[str, Any]):
        """Notify all clients about task completion"""
        await self.broadcast_json({
            "type": "task_completed",
            "data": task_data
        })
    
    async def notify_discovery_status(self, status: str, details: Dict[str, Any] = None):
        """Notify all clients about discovery process status"""
        await self.broadcast_json({
            "type": "discovery_status",
            "status": status,
            "details": details or {}
        })
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections"""
        return [
            {
                "user_id": info.get("user_id"),
                "connected_at": info.get("connected_at")
            }
            for info in self.connection_info.values()
        ]