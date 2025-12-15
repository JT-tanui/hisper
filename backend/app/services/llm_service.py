"""
LLM Service
Handles AI/LLM integration for task processing and MCP server interaction
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from ..core.config import settings
from ..models.task import Task
from ..models.mcp_server import MCPServer
from .mcp_client import mcp_client, MCPClientError

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class LLMServiceError(Exception):
    """Base exception for LLM service errors"""
    pass


class LLMService:
    """
    Service for handling AI/LLM interactions and task processing
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.openrouter_api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        
        # Initialize clients based on available API keys
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on available configuration"""
        try:
            # OpenAI client
            openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized")
            
            # Anthropic client
            anthropic_api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if anthropic_api_key:
                self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
                logger.info("Anthropic client initialized")
            
            # OpenRouter client (uses OpenAI-compatible API)
            if self.openrouter_api_key:
                self.openrouter_client = AsyncOpenAI(
                    api_key=self.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                logger.info("OpenRouter client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing LLM clients: {e}")
    
    async def process_task_with_llm(
        self, 
        task: Task, 
        available_servers: List[MCPServer],
        provider: LLMProvider = LLMProvider.OPENROUTER,
        model: str = "deepseek/deepseek-chat"
    ) -> Dict[str, Any]:
        """
        Process a task using LLM to determine the best approach and execute it
        
        Args:
            task: Task to process
            available_servers: List of available MCP servers
            provider: LLM provider to use
            model: Model name to use
            
        Returns:
            Dict containing the task execution result
        """
        try:
            logger.info(f"Processing task {task.id} with LLM using {provider}/{model}")
            
            # Step 1: Analyze task and select appropriate MCP servers
            selected_servers = await self._select_servers_for_task(
                task, available_servers, provider, model
            )
            
            if not selected_servers:
                return {
                    "success": False,
                    "error": "No suitable MCP servers found for this task",
                    "task_id": task.id
                }
            
            # Step 2: Generate execution plan
            execution_plan = await self._generate_execution_plan(
                task, selected_servers, provider, model
            )
            
            # Step 3: Execute the plan
            result = await self._execute_plan(task, execution_plan, selected_servers)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing task {task.id} with LLM: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task.id
            }
    
    async def _select_servers_for_task(
        self,
        task: Task,
        available_servers: List[MCPServer],
        provider: LLMProvider,
        model: str
    ) -> List[MCPServer]:
        """Select the most appropriate MCP servers for a task"""
        try:
            # Create server descriptions for the LLM
            server_descriptions = []
            for server in available_servers:
                desc = {
                    "id": server.id,
                    "name": server.name,
                    "description": server.description or "No description available",
                    "capabilities": server.capabilities or [],
                    "categories": server.categories or [],
                    "package_manager": server.package_manager,
                    "url": server.url
                }
                server_descriptions.append(desc)
            
            # Create prompt for server selection
            prompt = f"""
You are an AI assistant that helps select the most appropriate MCP (Model Context Protocol) servers for a given task.

Task Details:
- Title: {task.title}
- Description: {task.description}
- Priority: {task.priority}
- Parameters: {json.dumps(task.parameters or {}, indent=2)}

Available MCP Servers:
{json.dumps(server_descriptions, indent=2)}

Please analyze the task and select the most appropriate MCP servers that could help accomplish this task. Consider:
1. The task description and requirements
2. Server capabilities and categories
3. Relevance to the task domain

Respond with a JSON object containing:
{{
    "selected_servers": [list of server IDs that are most relevant],
    "reasoning": "explanation of why these servers were selected",
    "confidence": "high/medium/low confidence in the selection"
}}

Only select servers that are clearly relevant to the task. If no servers are suitable, return an empty list.
"""
            
            # Get LLM response
            response = await self._call_llm(prompt, provider, model)
            
            # Parse response
            try:
                result = json.loads(response)
                selected_ids = result.get("selected_servers", [])
                
                # Filter servers by selected IDs
                selected_servers = [
                    server for server in available_servers 
                    if server.id in selected_ids
                ]
                
                logger.info(f"Selected {len(selected_servers)} servers for task {task.id}: {result.get('reasoning', '')}")
                return selected_servers
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response for server selection: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error selecting servers for task {task.id}: {e}")
            return []
    
    async def _generate_execution_plan(
        self,
        task: Task,
        selected_servers: List[MCPServer],
        provider: LLMProvider,
        model: str
    ) -> Dict[str, Any]:
        """Generate an execution plan for the task using selected servers"""
        try:
            # Get available tools from selected servers
            server_tools = {}
            for server in selected_servers:
                try:
                    # Try to connect and get tools
                    connected = await mcp_client.connect_to_server(server)
                    if connected:
                        tools = await mcp_client.list_tools(server.id)
                        server_tools[server.id] = {
                            "server": server,
                            "tools": tools
                        }
                except Exception as e:
                    logger.warning(f"Could not get tools from server {server.name}: {e}")
                    # Use mock tools based on server description
                    server_tools[server.id] = {
                        "server": server,
                        "tools": self._generate_mock_tools(server)
                    }
            
            # Create prompt for execution plan
            prompt = f"""
You are an AI assistant that creates execution plans for tasks using MCP (Model Context Protocol) servers.

Task Details:
- Title: {task.title}
- Description: {task.description}
- Priority: {task.priority}
- Parameters: {json.dumps(task.parameters or {}, indent=2)}

Available Servers and Tools:
{json.dumps(server_tools, indent=2, default=str)}

Please create a detailed execution plan that breaks down the task into steps using the available MCP servers and their tools.

Respond with a JSON object containing:
{{
    "plan": [
        {{
            "step": 1,
            "description": "What this step accomplishes",
            "server_id": "ID of the MCP server to use",
            "tool_name": "Name of the tool to call",
            "arguments": {{"key": "value"}},
            "expected_output": "What we expect from this step"
        }}
    ],
    "summary": "Overall summary of the execution plan",
    "estimated_duration": "estimated time to complete",
    "dependencies": ["any external dependencies or requirements"]
}}

Make the plan as detailed and actionable as possible. Each step should be executable using the available tools.
"""
            
            # Get LLM response
            response = await self._call_llm(prompt, provider, model)
            
            # Parse response
            try:
                plan = json.loads(response)
                logger.info(f"Generated execution plan for task {task.id}: {plan.get('summary', '')}")
                return plan
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response for execution plan: {response}")
                return {"plan": [], "summary": "Failed to generate plan"}
                
        except Exception as e:
            logger.error(f"Error generating execution plan for task {task.id}: {e}")
            return {"plan": [], "summary": f"Error: {e}"}
    
    def _generate_mock_tools(self, server: MCPServer) -> List[Dict[str, Any]]:
        """Generate mock tools based on server description and name"""
        mock_tools = []
        
        # Generate tools based on server name and description
        server_name_lower = server.name.lower()
        
        if "filesystem" in server_name_lower or "file" in server_name_lower:
            mock_tools.extend([
                {"name": "read_file", "description": "Read contents of a file"},
                {"name": "write_file", "description": "Write content to a file"},
                {"name": "list_directory", "description": "List files in a directory"}
            ])
        
        if "database" in server_name_lower or "sql" in server_name_lower:
            mock_tools.extend([
                {"name": "execute_query", "description": "Execute SQL query"},
                {"name": "list_tables", "description": "List database tables"},
                {"name": "describe_table", "description": "Describe table structure"}
            ])
        
        if "browser" in server_name_lower or "web" in server_name_lower:
            mock_tools.extend([
                {"name": "navigate", "description": "Navigate to a URL"},
                {"name": "click_element", "description": "Click on a web element"},
                {"name": "extract_text", "description": "Extract text from page"}
            ])
        
        if "search" in server_name_lower:
            mock_tools.extend([
                {"name": "search", "description": "Perform search query"},
                {"name": "get_results", "description": "Get search results"}
            ])
        
        # Default tools if none match
        if not mock_tools:
            mock_tools = [
                {"name": "execute", "description": f"Execute {server.name} functionality"},
                {"name": "query", "description": f"Query {server.name} for information"}
            ]
        
        return mock_tools
    
    async def _execute_plan(
        self,
        task: Task,
        execution_plan: Dict[str, Any],
        selected_servers: List[MCPServer]
    ) -> Dict[str, Any]:
        """Execute the generated plan"""
        try:
            plan_steps = execution_plan.get("plan", [])
            results = []
            
            logger.info(f"Executing plan with {len(plan_steps)} steps for task {task.id}")
            
            for step in plan_steps:
                step_num = step.get("step", 0)
                server_id = step.get("server_id")
                tool_name = step.get("tool_name")
                arguments = step.get("arguments", {})
                
                logger.info(f"Executing step {step_num}: {step.get('description', '')}")
                
                try:
                    # Find the server
                    server = next((s for s in selected_servers if s.id == server_id), None)
                    if not server:
                        results.append({
                            "step": step_num,
                            "success": False,
                            "error": f"Server {server_id} not found"
                        })
                        continue
                    
                    # Execute the tool
                    tool_result = await mcp_client.execute_tool(server_id, tool_name, arguments)
                    
                    results.append({
                        "step": step_num,
                        "success": True,
                        "result": tool_result,
                        "server": server.name,
                        "tool": tool_name
                    })
                    
                except MCPClientError as e:
                    logger.error(f"MCP error in step {step_num}: {e}")
                    results.append({
                        "step": step_num,
                        "success": False,
                        "error": str(e),
                        "server": server.name if server else "unknown",
                        "tool": tool_name
                    })
                
                except Exception as e:
                    logger.error(f"Error in step {step_num}: {e}")
                    results.append({
                        "step": step_num,
                        "success": False,
                        "error": str(e)
                    })
            
            # Summarize results
            successful_steps = sum(1 for r in results if r.get("success", False))
            total_steps = len(results)
            
            return {
                "success": successful_steps > 0,
                "task_id": task.id,
                "execution_plan": execution_plan,
                "step_results": results,
                "summary": f"Completed {successful_steps}/{total_steps} steps successfully",
                "total_steps": total_steps,
                "successful_steps": successful_steps
            }
            
        except Exception as e:
            logger.error(f"Error executing plan for task {task.id}: {e}")
            return {
                "success": False,
                "task_id": task.id,
                "error": str(e)
            }
    
    async def _call_llm(
        self,
        prompt: str,
        provider: LLMProvider,
        model: str,
        max_tokens: int = 4000
    ) -> str:
        """Call the specified LLM provider"""
        try:
            if provider == LLMProvider.OPENROUTER:
                return await self._call_openrouter(prompt, model, max_tokens)
            elif provider == LLMProvider.OPENAI:
                return await self._call_openai(prompt, model, max_tokens)
            elif provider == LLMProvider.ANTHROPIC:
                return await self._call_anthropic(prompt, model, max_tokens)
            elif provider == LLMProvider.OLLAMA:
                return await self._call_ollama(prompt, model, max_tokens)
            else:
                raise LLMServiceError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Error calling LLM {provider}/{model}: {e}")
            raise LLMServiceError(f"LLM call failed: {e}")
    
    async def _call_openrouter(self, prompt: str, model: str, max_tokens: int) -> str:
        """Call OpenRouter API"""
        if not self.openrouter_api_key:
            raise LLMServiceError("OpenRouter API key not configured")
        
        try:
            response = await self.openrouter_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise LLMServiceError(f"OpenRouter call failed: {e}")
    
    async def _call_openai(self, prompt: str, model: str, max_tokens: int) -> str:
        """Call OpenAI API"""
        if not self.openai_client:
            raise LLMServiceError("OpenAI client not initialized")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(f"OpenAI call failed: {e}")
    
    async def _call_anthropic(self, prompt: str, model: str, max_tokens: int) -> str:
        """Call Anthropic API"""
        if not self.anthropic_client:
            raise LLMServiceError("Anthropic client not initialized")
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMServiceError(f"Anthropic call failed: {e}")
    
    async def _call_ollama(self, prompt: str, model: str, max_tokens: int) -> str:
        """Call Ollama API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.1
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    raise LLMServiceError(f"Ollama API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise LLMServiceError(f"Ollama call failed: {e}")
    
    async def analyze_task_complexity(
        self,
        task: Task,
        provider: LLMProvider = LLMProvider.OPENROUTER,
        model: str = "deepseek/deepseek-chat"
    ) -> Dict[str, Any]:
        """Analyze task complexity and requirements"""
        try:
            prompt = f"""
Analyze the following task and provide insights about its complexity and requirements:

Task Details:
- Title: {task.title}
- Description: {task.description}
- Priority: {task.priority}
- Parameters: {json.dumps(task.parameters or {}, indent=2)}

Please analyze and respond with a JSON object containing:
{{
    "complexity": "low/medium/high",
    "estimated_duration": "estimated time to complete",
    "required_capabilities": ["list of capabilities needed"],
    "potential_challenges": ["list of potential challenges"],
    "recommended_approach": "suggested approach to tackle this task",
    "resource_requirements": ["list of resources needed"]
}}
"""
            
            response = await self._call_llm(prompt, provider, model)
            
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                return {
                    "complexity": "unknown",
                    "error": "Failed to parse analysis response"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing task complexity: {e}")
            return {
                "complexity": "unknown",
                "error": str(e)
            }
    
    async def get_available_models(self, provider: LLMProvider) -> List[str]:
        """Get list of available models for a provider"""
        try:
            if provider == LLMProvider.OPENROUTER:
                return [
                    "deepseek/deepseek-chat",
                    "deepseek/deepseek-coder",
                    "anthropic/claude-3-haiku",
                    "anthropic/claude-3-sonnet",
                    "openai/gpt-4o-mini",
                    "openai/gpt-4o",
                    "meta-llama/llama-3.1-8b-instruct:free",
                    "microsoft/phi-3-mini-128k-instruct:free",
                    "google/gemma-2-9b-it:free"
                ]
            elif provider == LLMProvider.OPENAI:
                return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            elif provider == LLMProvider.ANTHROPIC:
                return ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
            elif provider == LLMProvider.OLLAMA:
                # Try to get models from Ollama API
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.ollama_base_url}/api/tags")
                        if response.status_code == 200:
                            data = response.json()
                            return [model["name"] for model in data.get("models", [])]
                except:
                    pass
                return ["llama2", "codellama", "mistral", "phi"]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting available models for {provider}: {e}")
            return []


# Global LLM service instance
llm_service = LLMService()