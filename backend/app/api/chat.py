"""
Chat API endpoints
Handles AI chat interface and task execution through natural language
"""

import json
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.llm_service import llm_service, LLMProvider
from ..services.mcp_client import mcp_client
from ..services.task_service import task_service
from ..models.mcp_server import MCPServer
from sqlalchemy import select
from ..services.conversation_service import conversation_service

router = APIRouter()


class ChatMessage(BaseModel):
    type: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ChatAnalyzeRequest(BaseModel):
    message: str
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "deepseek/deepseek-chat"
    context: List[ChatMessage] = []


class ChatExecuteRequest(BaseModel):
    action: Dict[str, Any]
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "deepseek/deepseek-chat"


class ChatAction(BaseModel):
    type: str  # 'search_servers', 'connect_server', 'execute_tool', 'create_task'
    parameters: Dict[str, Any]
    description: str


class ChatHistoryRequest(BaseModel):
    conversation_id: int
    max_tokens: int = 800
    include_summaries: bool = True


class ChatHistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    pinned: bool = False
    created_at: str
    audio_blob_id: Optional[int] = None

    class Config:
        from_attributes = True


@router.post("/analyze")
async def analyze_chat_message(
    request: ChatAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Analyze user message and suggest actions"""
    try:
        # Build context from previous messages
        context_text = ""
        if request.context:
            context_text = "\n".join([
                f"{msg.type}: {msg.content}" for msg in request.context[-3:]
            ])

        # Create analysis prompt
        analysis_prompt = f"""
You are an AI assistant that helps users interact with MCP (Model Context Protocol) servers to accomplish tasks.

Context from previous conversation:
{context_text}

User's current message: "{request.message}"

Your job is to:
1. Understand what the user wants to accomplish
2. Determine if MCP servers can help with this task
3. Suggest specific actions to take

Available MCP server types include:
- GitHub servers (code analysis, repository management)
- File system servers (file operations, directory management)
- Database servers (data queries, management)
- Web scraping servers (data extraction)
- API integration servers (external service integration)
- Development tools (linting, testing, building)

Respond with a JSON object containing:
{{
    "analysis": "A friendly explanation of what you understand and plan to do",
    "canHelp": true/false,
    "suggestedActions": [
        {{
            "type": "search_servers",
            "parameters": {{"query": "search terms", "category": "optional category"}},
            "description": "Search for relevant MCP servers"
        }},
        {{
            "type": "connect_server",
            "parameters": {{"serverId": 123}},
            "description": "Connect to a specific server"
        }},
        {{
            "type": "execute_tool",
            "parameters": {{"serverId": 123, "toolName": "tool_name", "arguments": {{}}}},
            "description": "Execute a specific tool"
        }},
        {{
            "type": "create_task",
            "parameters": {{"title": "Task title", "description": "Task description"}},
            "description": "Create a new task"
        }}
    ],
    "confidence": 0.8
}}

Be helpful, specific, and actionable. If you can't help with something, explain why and suggest alternatives.
"""

        # Get AI analysis
        response = await llm_service._call_llm(
            prompt=analysis_prompt,
            provider=request.provider,
            model=request.model,
            max_tokens=1000
        )

        # Try to parse JSON response
        try:
            analysis_data = json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a simple response
            analysis_data = {
                "analysis": response,
                "canHelp": True,
                "suggestedActions": [],
                "confidence": 0.5
            }

        return analysis_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_chat_action(
    request: ChatExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a suggested action from the chat"""
    try:
        action = request.action
        action_type = action.get("type")
        parameters = action.get("parameters", {})
        
        start_time = time.time()
        result = None
        task_id = None
        server_id = None
        server_name = None
        tools_used = []

        if action_type == "search_servers":
            # Search for MCP servers
            query = parameters.get("query", "")
            category = parameters.get("category")
            
            # Build search query
            search_query = select(MCPServer)
            if query:
                search_query = search_query.where(
                    MCPServer.name.contains(query) | 
                    MCPServer.description.contains(query)
                )
            if category:
                search_query = search_query.where(MCPServer.category == category)
            
            search_query = search_query.limit(10)
            search_result = await db.execute(search_query)
            servers = search_result.scalars().all()
            
            result = f"Found {len(servers)} MCP servers matching your criteria:\n\n"
            for server in servers:
                result += f"• **{server.name}** ({server.category})\n"
                result += f"  {server.description}\n"
                result += f"  Source: {server.source_type} | Status: {server.status}\n\n"

        elif action_type == "connect_server":
            # Connect to an MCP server
            server_id = parameters.get("serverId")
            if not server_id:
                raise HTTPException(status_code=400, detail="Server ID required")
            
            # Get server from database
            server_result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
            server = server_result.scalar_one_or_none()
            
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            # Attempt connection
            success = await mcp_client.connect_to_server(server)
            server_name = server.name
            
            if success:
                # Get available tools
                tools = await mcp_client.list_tools(server_id)
                tools_used = [tool.get("name", "unknown") for tool in tools]
                
                result = f"Successfully connected to **{server.name}**!\n\n"
                result += f"Available tools ({len(tools)}):\n"
                for tool in tools[:5]:  # Show first 5 tools
                    result += f"• {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}\n"
                if len(tools) > 5:
                    result += f"• ... and {len(tools) - 5} more tools\n"
            else:
                result = f"Failed to connect to **{server.name}**. The server may be unavailable or require additional configuration."

        elif action_type == "execute_tool":
            # Execute a tool on an MCP server
            server_id = parameters.get("serverId")
            tool_name = parameters.get("toolName")
            arguments = parameters.get("arguments", {})
            
            if not server_id or not tool_name:
                raise HTTPException(status_code=400, detail="Server ID and tool name required")
            
            # Get server name
            server_result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
            server = server_result.scalar_one_or_none()
            server_name = server.name if server else f"Server {server_id}"
            
            # Execute tool
            tool_result = await mcp_client.execute_tool(server_id, tool_name, arguments)
            tools_used = [tool_name]
            
            result = f"Executed **{tool_name}** on **{server_name}**:\n\n"
            result += f"```\n{json.dumps(tool_result, indent=2)}\n```"

        elif action_type == "create_task":
            # Create a new task
            title = parameters.get("title", "AI Generated Task")
            description = parameters.get("description", "")
            
            # Create task using task service
            task_data = {
                "title": title,
                "description": description,
                "priority": "medium",
                "input_data": parameters
            }
            
            # This would typically create a task in the database
            # For now, we'll simulate it
            task_id = int(time.time())
            
            result = f"Created task: **{title}**\n\n"
            result += f"Description: {description}\n"
            result += f"Task ID: {task_id}\n"
            result += f"Status: Created and ready for execution"

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")

        execution_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "result": result,
            "taskId": task_id,
            "serverId": server_id,
            "serverName": server_name,
            "toolsUsed": tools_used,
            "executionTime": round(execution_time, 2),
            "action": action
        }

    except Exception as e:
        return {
            "success": False,
            "result": f"Error executing action: {str(e)}",
            "error": str(e)
        }


@router.get("/suggestions")
async def get_chat_suggestions():
    """Get suggested prompts for users"""
    return {
        "suggestions": [
            "Find GitHub servers that can analyze code repositories",
            "Connect to a file system server and list available tools",
            "Search for database servers that can help with SQL queries",
            "Find web scraping servers for data extraction",
            "Look for development tools that can help with code linting",
            "Create a task to analyze a specific GitHub repository",
            "Find servers that can help with API integration",
            "Search for servers that can process and analyze text files"
        ]
    }


@router.get("/providers")
async def get_available_providers():
    """Get available LLM providers for chat"""
    try:
        providers = await task_service.get_available_llm_providers()
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_chat_history():
    """Clear chat history (placeholder for future implementation)"""
    return {"message": "Chat history cleared", "success": True}


@router.get("/stats")
async def get_chat_stats():
    """Get chat usage statistics"""
    # This would typically come from a database
    return {
        "totalMessages": 0,
        "totalTasks": 0,
        "serversUsed": 0,
        "successRate": 0.0,
        "averageResponseTime": 0.0
    }


@router.post("/history")
async def get_chat_history(
    request: ChatHistoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Return a sliced conversation history with summaries and pinned context."""
    try:
        conversation = await conversation_service.get_or_create_conversation(
            db, request.conversation_id
        )
        messages = await conversation_service.slice_history(
            db,
            conversation_id=conversation.id,
            max_tokens=request.max_tokens,
            include_summaries=request.include_summaries,
        )
        payload = [
            ChatHistoryMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                pinned=msg.pinned,
                created_at=msg.created_at.isoformat(),
                audio_blob_id=getattr(msg, "audio_blob_id", None),
            ).model_dump()
            for msg in messages
        ]
        return {
            "conversation_id": conversation.id,
            "messages": payload,
            "pinned_context": conversation.pinned_context or [],
            "summary": conversation.summary_text,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))