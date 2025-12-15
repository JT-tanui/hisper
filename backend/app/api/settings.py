"""
Settings API endpoints
Handles user settings including API keys and model configurations
"""

import os
import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.llm_service import llm_service, LLMProvider

router = APIRouter()


class APIKeySettings(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = "http://localhost:11434"


class ModelSettings(BaseModel):
    default_provider: LLMProvider = LLMProvider.OPENROUTER
    default_model: str = "deepseek/deepseek-chat"
    auto_execute: bool = True
    show_server_details: bool = True
    max_context_messages: int = 10
    request_timeout: int = 30


class UserSettings(BaseModel):
    api_keys: APIKeySettings
    model_settings: ModelSettings


class UpdateAPIKeysRequest(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None


class UpdateModelSettingsRequest(BaseModel):
    default_provider: Optional[LLMProvider] = None
    default_model: Optional[str] = None
    auto_execute: Optional[bool] = None
    show_server_details: Optional[bool] = None
    max_context_messages: Optional[int] = None
    request_timeout: Optional[int] = None


# In-memory settings storage (in production, this would be in a database)
_user_settings = {
    "api_keys": {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    },
    "model_settings": {
        "default_provider": "openrouter",
        "default_model": "deepseek/deepseek-chat",
        "auto_execute": True,
        "show_server_details": True,
        "max_context_messages": 10,
        "request_timeout": 30
    }
}


@router.get("/", response_model=UserSettings)
async def get_settings():
    """Get current user settings"""
    try:
        # Mask API keys for security (only show if they exist)
        masked_api_keys = {}
        for key, value in _user_settings["api_keys"].items():
            if value:
                masked_api_keys[key] = "***" + value[-4:] if len(value) > 4 else "***"
            else:
                masked_api_keys[key] = None
        
        return {
            "api_keys": masked_api_keys,
            "model_settings": _user_settings["model_settings"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys")
async def update_api_keys(request: UpdateAPIKeysRequest):
    """Update API keys"""
    try:
        # Update API keys
        if request.openai_api_key is not None:
            _user_settings["api_keys"]["openai_api_key"] = request.openai_api_key
            os.environ["OPENAI_API_KEY"] = request.openai_api_key
        
        if request.anthropic_api_key is not None:
            _user_settings["api_keys"]["anthropic_api_key"] = request.anthropic_api_key
            os.environ["ANTHROPIC_API_KEY"] = request.anthropic_api_key
        
        if request.openrouter_api_key is not None:
            _user_settings["api_keys"]["openrouter_api_key"] = request.openrouter_api_key
            os.environ["OPENROUTER_API_KEY"] = request.openrouter_api_key
        
        if request.ollama_base_url is not None:
            _user_settings["api_keys"]["ollama_base_url"] = request.ollama_base_url
            os.environ["OLLAMA_BASE_URL"] = request.ollama_base_url
        
        # Reinitialize LLM service with new keys
        await llm_service.initialize()
        
        return {"message": "API keys updated successfully", "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model-settings")
async def update_model_settings(request: UpdateModelSettingsRequest):
    """Update model settings"""
    try:
        # Update model settings
        if request.default_provider is not None:
            _user_settings["model_settings"]["default_provider"] = request.default_provider.value
        
        if request.default_model is not None:
            _user_settings["model_settings"]["default_model"] = request.default_model
        
        if request.auto_execute is not None:
            _user_settings["model_settings"]["auto_execute"] = request.auto_execute
        
        if request.show_server_details is not None:
            _user_settings["model_settings"]["show_server_details"] = request.show_server_details
        
        if request.max_context_messages is not None:
            _user_settings["model_settings"]["max_context_messages"] = request.max_context_messages
        
        if request.request_timeout is not None:
            _user_settings["model_settings"]["request_timeout"] = request.request_timeout
        
        return {"message": "Model settings updated successfully", "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-models")
async def get_available_models():
    """Get available models for each provider based on current API keys"""
    try:
        available_models = {}
        
        # Check which providers have valid API keys
        providers_with_keys = []
        
        if _user_settings["api_keys"].get("openai_api_key"):
            providers_with_keys.append("openai")
        
        if _user_settings["api_keys"].get("anthropic_api_key"):
            providers_with_keys.append("anthropic")
        
        if _user_settings["api_keys"].get("openrouter_api_key"):
            providers_with_keys.append("openrouter")
        
        # Ollama doesn't require API key, just check if URL is accessible
        providers_with_keys.append("ollama")
        
        # Get models for each provider
        all_providers = await llm_service.get_available_providers()
        
        for provider in providers_with_keys:
            if provider in all_providers:
                available_models[provider] = all_providers[provider]
        
        return {
            "available_models": available_models,
            "providers_with_keys": providers_with_keys
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_provider_connection(provider: LLMProvider, model: str):
    """Test connection to a specific provider and model"""
    try:
        # Test the connection by making a simple API call
        test_prompt = "Hello, this is a test. Please respond with 'Connection successful.'"
        
        response = await llm_service._call_llm(
            prompt=test_prompt,
            provider=provider,
            model=model,
            max_tokens=50
        )
        
        if "Connection successful" in response or len(response) > 0:
            return {
                "success": True,
                "message": f"Successfully connected to {provider.value} with model {model}",
                "response": response[:100] + "..." if len(response) > 100 else response
            }
        else:
            return {
                "success": False,
                "message": f"Connection test failed for {provider.value} with model {model}",
                "error": "No valid response received"
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection test failed for {provider.value} with model {model}",
            "error": str(e)
        }


@router.delete("/api-keys/{provider}")
async def delete_api_key(provider: str):
    """Delete API key for a specific provider"""
    try:
        key_mapping = {
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "openrouter": "openrouter_api_key",
            "ollama": "ollama_base_url"
        }
        
        if provider not in key_mapping:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        
        key_name = key_mapping[provider]
        _user_settings["api_keys"][key_name] = None
        
        # Remove from environment
        env_key = key_name.upper()
        if env_key in os.environ:
            del os.environ[env_key]
        
        return {"message": f"API key for {provider} deleted successfully", "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_settings():
    """Reset all settings to defaults"""
    try:
        # Reset to default values
        _user_settings["api_keys"] = {
            "openai_api_key": None,
            "anthropic_api_key": None,
            "openrouter_api_key": None,
            "ollama_base_url": "http://localhost:11434"
        }
        
        _user_settings["model_settings"] = {
            "default_provider": "openrouter",
            "default_model": "deepseek/deepseek-chat",
            "auto_execute": True,
            "show_server_details": True,
            "max_context_messages": 10,
            "request_timeout": 30
        }
        
        # Clear environment variables
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]:
            if key in os.environ:
                del os.environ[key]
        
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
        
        return {"message": "Settings reset to defaults", "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_settings():
    """Export settings (without API keys for security)"""
    try:
        export_data = {
            "model_settings": _user_settings["model_settings"],
            "api_key_status": {
                key: bool(value) for key, value in _user_settings["api_keys"].items()
            }
        }
        
        return export_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))