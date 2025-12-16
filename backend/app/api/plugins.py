"""
Plugin registry API
"""

from typing import List
from fastapi import APIRouter, Depends, Request

from ..models.plugin import PluginRead, PluginManifest

router = APIRouter()


def get_plugin_service(request: Request):
    return request.app.state.plugin_service


@router.get("/", response_model=List[PluginRead])
async def list_plugins(request: Request):
    """Return plugins stored in the registry"""

    registry = request.app.state.plugin_service.registry
    return await registry.list_plugins()


@router.get("/manifests", response_model=List[PluginManifest])
async def list_manifests(plugin_service=Depends(get_plugin_service)):
    """Return manifests for client-side extensions"""

    return plugin_service.loaded_manifests
