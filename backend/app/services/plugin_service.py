"""
Plugin loader and registry service
"""

import asyncio
import json
import logging
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import FastAPI

from ..core.database import AsyncSessionLocal
from ..models.plugin import Plugin, PluginManifest, PluginRead
from ..plugins import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry stored in the database"""

    async def upsert(self, manifest: PluginManifest, status: str, entrypoint: Optional[str], manifest_path: Optional[str], last_error: Optional[str] = None) -> None:
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Plugin).where(Plugin.identifier == manifest.identifier))
                plugin = result.scalars().first()
                if not plugin:
                    plugin = Plugin(identifier=manifest.identifier)
                    session.add(plugin)

                plugin.name = manifest.name
                plugin.version = manifest.version
                plugin.description = manifest.description
                plugin.plugin_type = manifest.plugin_type
                plugin.entrypoint = entrypoint
                plugin.manifest_path = manifest_path
                plugin.capabilities = [cap.model_dump() for cap in manifest.capabilities]
                plugin.ui_extensions = manifest.frontend or {}
                plugin.status = status
                plugin.last_error = last_error
                plugin.last_loaded = None if status != "loaded" else datetime.utcnow()
                await session.commit()
            except SQLAlchemyError as exc:
                logger.error("Failed to upsert plugin %s: %s", manifest.identifier, exc)
                await session.rollback()

    async def list_plugins(self) -> List[PluginRead]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Plugin))
            return [PluginRead.model_validate(plugin) for plugin in result.scalars().all()]


class PluginService:
    """Loads plugins via entry points or manifest files and executes lifecycle hooks"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.registry = PluginRegistry()
        self.loaded_manifests: List[PluginManifest] = []

    async def load_plugins(self) -> None:
        entrypoint_plugins = await self._load_entrypoint_plugins()
        manifest_plugins = await self._load_manifest_files()
        self.loaded_manifests = entrypoint_plugins + manifest_plugins

    async def _load_entrypoint_plugins(self) -> List[PluginManifest]:
        manifests: List[PluginManifest] = []
        for entry_point in metadata.entry_points().select(group="hisper.plugins"):
            try:
                plugin_class = entry_point.load()
                plugin: BasePlugin = plugin_class()
                manifest = plugin.get_manifest()
                logger.info("Discovered plugin %s", manifest.identifier)
                await self._register_plugin(manifest, entry_point=entry_point.name)
                self._mount_plugin(plugin)
                manifests.append(manifest)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to load plugin via entrypoint %s: %s", entry_point.name, exc)
                manifest = PluginManifest(
                    identifier=entry_point.name,
                    name=entry_point.name,
                    version="0.0.0",
                    description=f"Failed to load: {exc}",
                    plugin_type="unknown",
                    capabilities=[],
                )
                await self.registry.upsert(manifest, status="error", entrypoint=entry_point.name, manifest_path=None, last_error=str(exc))
        return manifests

    async def _load_manifest_files(self) -> List[PluginManifest]:
        manifests: List[PluginManifest] = []
        manifest_dirs = self.app.state.settings.PLUGIN_MANIFEST_DIRS
        for folder in manifest_dirs:
            path = Path(folder)
            if not path.exists():
                continue
            for manifest_path in path.glob("*.plugin.json"):
                try:
                    raw_manifest = json.loads(manifest_path.read_text())
                    manifest = PluginManifest(**raw_manifest, manifest_path=str(manifest_path))
                    logger.info("Discovered manifest plugin %s", manifest.identifier)
                    await self._register_plugin(manifest, entrypoint=None, manifest_path=str(manifest_path))
                    manifests.append(manifest)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to read manifest %s: %s", manifest_path, exc)
        return manifests

    def _mount_plugin(self, plugin: BasePlugin) -> None:
        sandbox = plugin.sandbox_context()
        context = {
            "app": self.app.title,
            "sandbox": sandbox,
        }
        self.app.state.plugin_sandboxes[plugin.manifest.identifier] = context

        for router in plugin.register_routes():
            self.app.include_router(router)

        async def schedule():
            jobs = await plugin.schedule_jobs()
            for job in jobs:
                if isinstance(job, asyncio.Task):
                    logger.info("Started background job for plugin %s", plugin.manifest.identifier)

        asyncio.create_task(schedule())

    async def _register_plugin(self, manifest: PluginManifest, entrypoint: Optional[str], manifest_path: Optional[str]) -> None:
        await self.registry.upsert(manifest, status="loaded", entrypoint=entrypoint, manifest_path=manifest_path)

