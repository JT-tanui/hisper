"""
Base plugin interfaces for Hisper
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from fastapi import APIRouter

from ..models.plugin import PluginManifest, PluginCapability


@dataclass
class PluginContext:
    """Context shared with plugins for lifecycle hooks"""

    app_name: str
    sandbox: Dict[str, Any]


class BasePlugin(ABC):
    """Base class for all plugins"""

    manifest: PluginManifest

    @abstractmethod
    def capability_descriptors(self) -> List[PluginCapability]:
        """Return a list of capability descriptors used for registry and sandboxing"""

    def register_routes(self) -> List[APIRouter]:
        """Optional: return routers to mount on the main FastAPI app"""

        return []

    async def schedule_jobs(self) -> List[asyncio.Task]:
        """Optional: start background jobs. Override to schedule recurring work"""

        return []

    async def contribute_metrics(self) -> Dict[str, Any]:
        """Optional: publish plugin metrics"""

        return {}

    def sandbox_context(self) -> Dict[str, Any]:
        """Declare sandbox rules for the plugin"""

        return {
            "network": False,
            "filesystem": False,
        }

    def get_manifest(self) -> PluginManifest:
        """Return the manifest with capability descriptors attached"""

        manifest = self.manifest.copy()
        manifest.capabilities = self.capability_descriptors()
        return manifest
