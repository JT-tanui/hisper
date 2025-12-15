"""
MCP Client Service
Handles communication with MCP servers using the Model Context Protocol
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.mcp_server import MCPServer
from ..models.task import Task

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client errors"""
    pass


class MCPServerConnectionError(MCPClientError):
    """Raised when unable to connect to MCP server"""
    pass


class MCPToolExecutionError(MCPClientError):
    """Raised when tool execution fails"""
    pass


class MCPClient:
    """
    MCP Client for communicating with Model Context Protocol servers
    """
    
    def __init__(self):
        self.active_connections: Dict[int, Any] = {}
        self.server_processes: Dict[int, subprocess.Popen] = {}
    
    async def connect_to_server(self, server: MCPServer) -> bool:
        """
        Connect to an MCP server
        
        Args:
            server: MCPServer instance to connect to
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MCP server: {server.name}")
            
            # Handle different server types
            if server.package_manager == "npm":
                return await self._connect_npm_server(server)
            elif server.package_manager == "pip":
                return await self._connect_pip_server(server)
            elif server.discovered_from == "github":
                return await self._connect_github_server(server)
            else:
                return await self._connect_generic_server(server)
                
        except Exception as e:
            logger.error(f"Failed to connect to server {server.name}: {e}")
            raise MCPServerConnectionError(f"Connection failed: {e}")
    
    async def _connect_npm_server(self, server: MCPServer) -> bool:
        """Connect to npm-based MCP server"""
        try:
            # For npm packages, we need to install and run them
            package_name = server.package_name
            
            # Create a temporary directory for the server
            temp_dir = tempfile.mkdtemp(prefix=f"mcp_{server.id}_")
            
            # Install the package
            install_cmd = ["npm", "install", package_name]
            process = await asyncio.create_subprocess_exec(
                *install_cmd,
                cwd=temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to install npm package {package_name}: {stderr.decode()}")
                return False
            
            # Try to run the server
            run_cmd = ["npx", package_name]
            server_process = await asyncio.create_subprocess_exec(
                *run_cmd,
                cwd=temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            
            self.server_processes[server.id] = server_process
            
            # Test basic communication
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "hisper",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send initialization message
            message_str = json.dumps(test_message) + "\n"
            server_process.stdin.write(message_str.encode())
            await server_process.stdin.drain()
            
            # Wait for response (with timeout)
            try:
                response_line = await asyncio.wait_for(
                    server_process.stdout.readline(),
                    timeout=10.0
                )
                
                if response_line:
                    response = json.loads(response_line.decode().strip())
                    if "result" in response:
                        logger.info(f"Successfully connected to npm server: {server.name}")
                        self.active_connections[server.id] = {
                            "type": "npm",
                            "process": server_process,
                            "temp_dir": temp_dir
                        }
                        return True
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response from {server.name}")
                server_process.terminate()
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to npm server {server.name}: {e}")
            return False
        
        return False
    
    async def _connect_pip_server(self, server: MCPServer) -> bool:
        """Connect to pip-based MCP server"""
        try:
            # For pip packages, install and run them
            package_name = server.package_name
            
            # Install the package
            install_cmd = ["pip", "install", package_name]
            process = await asyncio.create_subprocess_exec(
                *install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to install pip package {package_name}: {stderr.decode()}")
                return False
            
            # Try to run the server (assuming it has a standard entry point)
            run_cmd = ["python", "-m", package_name]
            server_process = await asyncio.create_subprocess_exec(
                *run_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            
            self.server_processes[server.id] = server_process
            
            # Test basic communication similar to npm
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "hisper",
                        "version": "1.0.0"
                    }
                }
            }
            
            message_str = json.dumps(test_message) + "\n"
            server_process.stdin.write(message_str.encode())
            await server_process.stdin.drain()
            
            try:
                response_line = await asyncio.wait_for(
                    server_process.stdout.readline(),
                    timeout=10.0
                )
                
                if response_line:
                    response = json.loads(response_line.decode().strip())
                    if "result" in response:
                        logger.info(f"Successfully connected to pip server: {server.name}")
                        self.active_connections[server.id] = {
                            "type": "pip",
                            "process": server_process
                        }
                        return True
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response from {server.name}")
                server_process.terminate()
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to pip server {server.name}: {e}")
            return False
        
        return False
    
    async def _connect_github_server(self, server: MCPServer) -> bool:
        """Connect to GitHub-based MCP server"""
        try:
            # For GitHub servers, we need to clone and run them
            repo_url = server.repository_url
            if not repo_url:
                logger.error(f"No repository URL for GitHub server: {server.name}")
                return False
            
            # Create temporary directory and clone
            temp_dir = tempfile.mkdtemp(prefix=f"mcp_github_{server.id}_")
            
            clone_cmd = ["git", "clone", repo_url, temp_dir]
            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to clone repository {repo_url}: {stderr.decode()}")
                return False
            
            # Try to determine how to run the server
            # Look for common files
            repo_path = Path(temp_dir)
            
            if (repo_path / "package.json").exists():
                # Node.js project
                # Install dependencies
                install_process = await asyncio.create_subprocess_exec(
                    "npm", "install",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await install_process.communicate()
                
                # Try to run
                run_cmd = ["npm", "start"]
            elif (repo_path / "requirements.txt").exists():
                # Python project
                install_process = await asyncio.create_subprocess_exec(
                    "pip", "install", "-r", "requirements.txt",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await install_process.communicate()
                
                run_cmd = ["python", "main.py"]
            else:
                logger.warning(f"Unknown project type for {server.name}")
                return False
            
            # Start the server
            server_process = await asyncio.create_subprocess_exec(
                *run_cmd,
                cwd=temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            
            self.server_processes[server.id] = server_process
            self.active_connections[server.id] = {
                "type": "github",
                "process": server_process,
                "temp_dir": temp_dir
            }
            
            logger.info(f"Started GitHub server: {server.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to GitHub server {server.name}: {e}")
            return False
    
    async def _connect_generic_server(self, server: MCPServer) -> bool:
        """Connect to a generic MCP server"""
        try:
            # For generic servers, try HTTP connection first
            if server.url.startswith("http"):
                return await self._connect_http_server(server)
            else:
                logger.warning(f"Unknown server type for {server.name}: {server.url}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to generic server {server.name}: {e}")
            return False
    
    async def _connect_http_server(self, server: MCPServer) -> bool:
        """Connect to HTTP-based MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to ping the server
                async with session.get(f"{server.url}/health", timeout=10) as response:
                    if response.status == 200:
                        self.active_connections[server.id] = {
                            "type": "http",
                            "url": server.url
                        }
                        logger.info(f"Successfully connected to HTTP server: {server.name}")
                        return True
                        
        except Exception as e:
            logger.error(f"Error connecting to HTTP server {server.name}: {e}")
            return False
        
        return False
    
    async def disconnect_from_server(self, server_id: int):
        """Disconnect from an MCP server"""
        try:
            if server_id in self.active_connections:
                connection = self.active_connections[server_id]
                
                if connection["type"] in ["npm", "pip", "github"]:
                    process = connection.get("process")
                    if process:
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=5.0)
                        except asyncio.TimeoutError:
                            process.kill()
                
                # Clean up temporary directories
                if "temp_dir" in connection:
                    import shutil
                    shutil.rmtree(connection["temp_dir"], ignore_errors=True)
                
                del self.active_connections[server_id]
                
            if server_id in self.server_processes:
                del self.server_processes[server_id]
                
            logger.info(f"Disconnected from server {server_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from server {server_id}: {e}")
    
    async def list_tools(self, server_id: int) -> List[Dict[str, Any]]:
        """List available tools from an MCP server"""
        try:
            if server_id not in self.active_connections:
                raise MCPServerConnectionError(f"Not connected to server {server_id}")
            
            connection = self.active_connections[server_id]
            
            if connection["type"] == "http":
                return await self._list_tools_http(connection)
            else:
                return await self._list_tools_stdio(connection)
                
        except Exception as e:
            logger.error(f"Error listing tools for server {server_id}: {e}")
            raise MCPToolExecutionError(f"Failed to list tools: {e}")
    
    async def _list_tools_http(self, connection: Dict) -> List[Dict[str, Any]]:
        """List tools from HTTP server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{connection['url']}/tools/list",
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", {}).get("tools", [])
                        
        except Exception as e:
            logger.error(f"Error listing HTTP tools: {e}")
            return []
    
    async def _list_tools_stdio(self, connection: Dict) -> List[Dict[str, Any]]:
        """List tools from stdio server"""
        try:
            process = connection["process"]
            
            message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            message_str = json.dumps(message) + "\n"
            process.stdin.write(message_str.encode())
            await process.stdin.drain()
            
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=10.0
            )
            
            if response_line:
                response = json.loads(response_line.decode().strip())
                return response.get("result", {}).get("tools", [])
                
        except Exception as e:
            logger.error(f"Error listing stdio tools: {e}")
            return []
        
        return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def execute_tool(
        self, 
        server_id: int, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server
        
        Args:
            server_id: ID of the MCP server
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Dict containing the tool execution result
        """
        try:
            if server_id not in self.active_connections:
                raise MCPServerConnectionError(f"Not connected to server {server_id}")
            
            connection = self.active_connections[server_id]
            
            logger.info(f"Executing tool {tool_name} on server {server_id}")
            
            if connection["type"] == "http":
                return await self._execute_tool_http(connection, tool_name, arguments)
            else:
                return await self._execute_tool_stdio(connection, tool_name, arguments)
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name} on server {server_id}: {e}")
            raise MCPToolExecutionError(f"Tool execution failed: {e}")
    
    async def _execute_tool_http(
        self, 
        connection: Dict, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool on HTTP server"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                async with session.post(
                    f"{connection['url']}/tools/call",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", {})
                    else:
                        raise MCPToolExecutionError(f"HTTP error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error executing HTTP tool: {e}")
            raise
    
    async def _execute_tool_stdio(
        self, 
        connection: Dict, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool on stdio server"""
        try:
            process = connection["process"]
            
            message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            message_str = json.dumps(message) + "\n"
            process.stdin.write(message_str.encode())
            await process.stdin.drain()
            
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=30.0
            )
            
            if response_line:
                response = json.loads(response_line.decode().strip())
                if "result" in response:
                    return response["result"]
                elif "error" in response:
                    raise MCPToolExecutionError(f"Tool error: {response['error']}")
                    
        except Exception as e:
            logger.error(f"Error executing stdio tool: {e}")
            raise
        
        return {}
    
    async def get_server_capabilities(self, server_id: int) -> Dict[str, Any]:
        """Get capabilities of an MCP server"""
        try:
            if server_id not in self.active_connections:
                raise MCPServerConnectionError(f"Not connected to server {server_id}")
            
            # Get tools list as a proxy for capabilities
            tools = await self.list_tools(server_id)
            
            return {
                "tools": tools,
                "tool_count": len(tools),
                "connected": True
            }
            
        except Exception as e:
            logger.error(f"Error getting capabilities for server {server_id}: {e}")
            return {"connected": False, "error": str(e)}
    
    async def health_check(self, server_id: int) -> Dict[str, Any]:
        """Perform health check on an MCP server"""
        try:
            if server_id not in self.active_connections:
                return {"status": "disconnected", "healthy": False}
            
            connection = self.active_connections[server_id]
            
            if connection["type"] == "http":
                return await self._health_check_http(connection)
            else:
                return await self._health_check_stdio(connection)
                
        except Exception as e:
            logger.error(f"Health check failed for server {server_id}: {e}")
            return {"status": "error", "healthy": False, "error": str(e)}
    
    async def _health_check_http(self, connection: Dict) -> Dict[str, Any]:
        """Health check for HTTP server"""
        try:
            import time
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{connection['url']}/health", timeout=5) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "healthy": True,
                            "response_time_ms": response_time
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "healthy": False,
                            "response_time_ms": response_time
                        }
                        
        except Exception as e:
            return {"status": "error", "healthy": False, "error": str(e)}
    
    async def _health_check_stdio(self, connection: Dict) -> Dict[str, Any]:
        """Health check for stdio server"""
        try:
            process = connection["process"]
            
            if process.poll() is not None:
                return {"status": "dead", "healthy": False}
            
            # Try a simple ping
            import time
            start_time = time.time()
            
            message = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "ping",
                "params": {}
            }
            
            message_str = json.dumps(message) + "\n"
            process.stdin.write(message_str.encode())
            await process.stdin.drain()
            
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=5.0
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response_line:
                    return {
                        "status": "healthy",
                        "healthy": True,
                        "response_time_ms": response_time
                    }
                    
            except asyncio.TimeoutError:
                return {"status": "timeout", "healthy": False}
                
        except Exception as e:
            return {"status": "error", "healthy": False, "error": str(e)}
        
        return {"status": "unknown", "healthy": False}
    
    async def cleanup(self):
        """Clean up all connections and processes"""
        try:
            server_ids = list(self.active_connections.keys())
            for server_id in server_ids:
                await self.disconnect_from_server(server_id)
                
            logger.info("MCP Client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during MCP client cleanup: {e}")


# Global MCP client instance
mcp_client = MCPClient()