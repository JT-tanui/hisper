"""
MCP Server Discovery Service
Discovers MCP servers from various sources like GitHub, npm, PyPI, etc.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_sync_db
from ..models.mcp_server import MCPServer, MCPServerCreate

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service for discovering MCP servers from various sources"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        self.discovery_task = None
        
    async def start_periodic_discovery(self):
        """Start periodic discovery of MCP servers"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Starting periodic MCP server discovery")
        
        while self.is_running:
            try:
                await self.discover_all_sources()
                await asyncio.sleep(settings.DISCOVERY_INTERVAL_MINUTES * 60)
            except Exception as e:
                logger.error(f"Error in periodic discovery: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def stop(self):
        """Stop the discovery service"""
        self.is_running = False
        if self.discovery_task:
            self.discovery_task.cancel()
        await self.client.aclose()
        logger.info("Discovery service stopped")
    
    async def discover_all_sources(self):
        """Discover MCP servers from all available sources"""
        logger.info("Starting discovery from all sources")
        
        tasks = [
            self.discover_from_github(),
            self.discover_from_npm(),
            self.discover_from_pypi(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_discovered = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Discovery task {i} failed: {result}")
            else:
                total_discovered += result
        
        logger.info(f"Discovery completed. Total new servers discovered: {total_discovered}")
        return total_discovered
    
    async def discover_from_github(self) -> int:
        """Discover MCP servers from GitHub repositories"""
        logger.info("Discovering MCP servers from GitHub")
        
        discovered_count = 0
        
        try:
            # Search for repositories with MCP-related keywords
            search_queries = [
                "mcp server",
                "model context protocol",
                "mcp-server",
                "anthropic mcp",
                "claude mcp"
            ]
            
            headers = {}
            if settings.GITHUB_TOKEN:
                headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
            
            for query in search_queries:
                url = f"https://api.github.com/search/repositories"
                params = {
                    "q": query,
                    "sort": "updated",
                    "order": "desc",
                    "per_page": 50
                }
                
                response = await self.client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    for repo in data.get("items", []):
                        if await self._is_mcp_server_repo(repo):
                            server_data = await self._extract_github_server_info(repo)
                            if server_data and await self._save_discovered_server(server_data):
                                discovered_count += 1
                
                # Rate limiting
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error discovering from GitHub: {e}")
        
        logger.info(f"Discovered {discovered_count} servers from GitHub")
        return discovered_count
    
    async def discover_from_npm(self) -> int:
        """Discover MCP servers from npm registry"""
        logger.info("Discovering MCP servers from npm")
        
        discovered_count = 0
        
        try:
            # Search npm registry for MCP-related packages
            search_terms = ["mcp-server", "mcp", "model-context-protocol"]
            
            for term in search_terms:
                url = f"https://registry.npmjs.org/-/v1/search"
                params = {
                    "text": term,
                    "size": 50
                }
                
                response = await self.client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    for package in data.get("objects", []):
                        if await self._is_mcp_server_package(package, "npm"):
                            server_data = await self._extract_npm_server_info(package)
                            if server_data and await self._save_discovered_server(server_data):
                                discovered_count += 1
                
                await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error discovering from npm: {e}")
        
        logger.info(f"Discovered {discovered_count} servers from npm")
        return discovered_count
    
    async def discover_from_pypi(self) -> int:
        """Discover MCP servers from PyPI"""
        logger.info("Discovering MCP servers from PyPI")
        
        discovered_count = 0
        
        try:
            # Search PyPI for MCP-related packages
            search_terms = ["mcp-server", "mcp", "model-context-protocol"]
            
            for term in search_terms:
                url = f"https://pypi.org/search/"
                params = {"q": term}
                
                response = await self.client.get(url, params=params)
                if response.status_code == 200:
                    # Parse HTML response to extract package names
                    package_names = self._extract_pypi_package_names(response.text)
                    
                    for package_name in package_names[:20]:  # Limit to first 20
                        package_info = await self._get_pypi_package_info(package_name)
                        if package_info and await self._is_mcp_server_package(package_info, "pypi"):
                            server_data = await self._extract_pypi_server_info(package_info)
                            if server_data and await self._save_discovered_server(server_data):
                                discovered_count += 1
                        
                        await asyncio.sleep(0.5)
                
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error discovering from PyPI: {e}")
        
        logger.info(f"Discovered {discovered_count} servers from PyPI")
        return discovered_count
    
    async def _is_mcp_server_repo(self, repo: Dict[str, Any]) -> bool:
        """Check if a GitHub repository is likely an MCP server"""
        name = repo.get("name", "").lower()
        description = repo.get("description", "").lower()
        
        mcp_indicators = [
            "mcp", "model context protocol", "server", "anthropic", "claude"
        ]
        
        return any(indicator in name or indicator in description for indicator in mcp_indicators)
    
    async def _is_mcp_server_package(self, package: Dict[str, Any], source: str) -> bool:
        """Check if a package is likely an MCP server"""
        if source == "npm":
            name = package.get("package", {}).get("name", "").lower()
            description = package.get("package", {}).get("description", "").lower()
        else:  # pypi
            name = package.get("name", "").lower()
            description = package.get("summary", "").lower()
        
        mcp_indicators = [
            "mcp", "model context protocol", "server", "anthropic", "claude"
        ]
        
        return any(indicator in name or indicator in description for indicator in mcp_indicators)
    
    async def _extract_github_server_info(self, repo: Dict[str, Any]) -> Optional[MCPServerCreate]:
        """Extract server information from GitHub repository"""
        try:
            return MCPServerCreate(
                name=repo["name"],
                description=repo.get("description"),
                url=repo["clone_url"],
                repository_url=repo["html_url"],
                package_manager="git",
                author=repo["owner"]["login"],
                license=repo.get("license", {}).get("name") if repo.get("license") else None,
                discovered_from="github",
                metadata={
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language"),
                    "updated_at": repo.get("updated_at")
                }
            )
        except Exception as e:
            logger.error(f"Error extracting GitHub server info: {e}")
            return None
    
    async def _extract_npm_server_info(self, package: Dict[str, Any]) -> Optional[MCPServerCreate]:
        """Extract server information from npm package"""
        try:
            pkg_info = package["package"]
            return MCPServerCreate(
                name=pkg_info["name"],
                description=pkg_info.get("description"),
                url=f"npm:{pkg_info['name']}",
                repository_url=pkg_info.get("links", {}).get("repository"),
                package_manager="npm",
                package_name=pkg_info["name"],
                version=pkg_info.get("version"),
                author=pkg_info.get("author", {}).get("name") if isinstance(pkg_info.get("author"), dict) else pkg_info.get("author"),
                license=pkg_info.get("license"),
                discovered_from="npm",
                metadata={
                    "keywords": pkg_info.get("keywords", []),
                    "homepage": pkg_info.get("links", {}).get("homepage"),
                    "npm_url": pkg_info.get("links", {}).get("npm")
                }
            )
        except Exception as e:
            logger.error(f"Error extracting npm server info: {e}")
            return None
    
    async def _extract_pypi_server_info(self, package: Dict[str, Any]) -> Optional[MCPServerCreate]:
        """Extract server information from PyPI package"""
        try:
            info = package["info"]
            return MCPServerCreate(
                name=info["name"],
                description=info.get("summary"),
                url=f"pip:{info['name']}",
                repository_url=info.get("project_urls", {}).get("Repository") or info.get("home_page"),
                package_manager="pip",
                package_name=info["name"],
                version=info.get("version"),
                author=info.get("author"),
                license=info.get("license"),
                discovered_from="pypi",
                metadata={
                    "keywords": info.get("keywords"),
                    "classifiers": info.get("classifiers", []),
                    "pypi_url": f"https://pypi.org/project/{info['name']}/"
                }
            )
        except Exception as e:
            logger.error(f"Error extracting PyPI server info: {e}")
            return None
    
    def _extract_pypi_package_names(self, html_content: str) -> List[str]:
        """Extract package names from PyPI search results HTML"""
        # Simple regex to extract package names from search results
        pattern = r'href="/project/([^/]+)/"'
        matches = re.findall(pattern, html_content)
        return list(set(matches))  # Remove duplicates
    
    async def _get_pypi_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed package information from PyPI API"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting PyPI package info for {package_name}: {e}")
        return None
    
    async def _save_discovered_server(self, server_data: MCPServerCreate) -> bool:
        """Save discovered server to database if it doesn't already exist"""
        try:
            db = next(get_sync_db())
            
            # Check if server already exists
            existing = db.query(MCPServer).filter(
                MCPServer.name == server_data.name,
                MCPServer.url == server_data.url
            ).first()
            
            if existing:
                # Update last_updated timestamp
                existing.last_updated = datetime.utcnow()
                db.commit()
                return False
            
            # Create new server
            db_server = MCPServer(**server_data.dict())
            db.add(db_server)
            db.commit()
            
            logger.info(f"Saved new MCP server: {server_data.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving discovered server: {e}")
            return False
        finally:
            db.close()
    
    async def manual_discovery(self, url: str, name: Optional[str] = None) -> bool:
        """Manually add a server for discovery"""
        try:
            server_data = MCPServerCreate(
                name=name or f"Manual Server {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                url=url,
                discovered_from="manual"
            )
            
            return await self._save_discovered_server(server_data)
            
        except Exception as e:
            logger.error(f"Error in manual discovery: {e}")
            return False