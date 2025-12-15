"""
LLM API endpoints
Handles AI/LLM related operations
"""

from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..services.llm_service import llm_service, LLMProvider
from ..services.task_service import task_service

router = APIRouter()


class LLMProviderRequest(BaseModel):
    provider: LLMProvider
    model: str


class TaskExecutionRequest(BaseModel):
    task_id: int
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "deepseek/deepseek-chat"


class TaskAnalysisRequest(BaseModel):
    task_id: int
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "deepseek/deepseek-chat"


@router.get("/providers", response_model=Dict[str, List[str]])
async def get_available_providers():
    """Get available LLM providers and their models"""
    try:
        providers = await task_service.get_available_llm_providers()
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-task")
async def execute_task_with_llm(request: TaskExecutionRequest):
    """Execute a task with specific LLM provider and model"""
    try:
        result = await task_service.execute_task_with_custom_llm(
            task_id=request.task_id,
            provider=request.provider,
            model=request.model
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-task")
async def analyze_task(request: TaskAnalysisRequest):
    """Analyze a task using LLM without executing it"""
    try:
        analysis = await task_service.analyze_task(request.task_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{provider}")
async def get_provider_models(provider: LLMProvider):
    """Get available models for a specific provider"""
    try:
        models = await llm_service.get_available_models(provider)
        return {"provider": provider.value, "models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_llm_connection(request: LLMProviderRequest):
    """Test connection to an LLM provider"""
    try:
        # Simple test prompt
        test_prompt = "Hello! Please respond with 'Connection successful' if you can read this."
        
        response = await llm_service._call_llm(
            prompt=test_prompt,
            provider=request.provider,
            model=request.model,
            max_tokens=50
        )
        
        return {
            "success": True,
            "provider": request.provider.value,
            "model": request.model,
            "response": response,
            "message": "Connection test successful"
        }
    except Exception as e:
        return {
            "success": False,
            "provider": request.provider.value,
            "model": request.model,
            "error": str(e),
            "message": "Connection test failed"
        }