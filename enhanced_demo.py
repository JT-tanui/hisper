#!/usr/bin/env python3
"""
Enhanced Hisper Demo Script
Demonstrates the enhanced functionality including LLM integration, MCP communication, and monitoring
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:12000"
API_BASE = f"{BASE_URL}/api/v1"

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_json(data: Any, title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))

def test_health():
    """Test system health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_json(response.json(), "System Health")
            return True
        else:
            print(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False

def test_monitoring():
    """Test monitoring endpoints"""
    try:
        print("\n🔍 Testing Monitoring System:")
        
        # System health
        response = requests.get(f"{API_BASE}/monitoring/health", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "System Health Status")
        
        # Monitoring status
        response = requests.get(f"{API_BASE}/monitoring/status", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "Monitoring Service Status")
        
        # Metrics summary
        response = requests.get(f"{API_BASE}/monitoring/metrics/summary?hours=1", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "Metrics Summary (Last Hour)")
        
        # Active alerts
        response = requests.get(f"{API_BASE}/monitoring/alerts", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "Active Alerts")
        
        return True
        
    except Exception as e:
        print(f"Error testing monitoring: {e}")
        return False

def test_llm_providers():
    """Test LLM provider endpoints"""
    try:
        print("\n🤖 Testing LLM Integration:")
        
        # Get available providers
        response = requests.get(f"{API_BASE}/llm/providers", timeout=10)
        if response.status_code == 200:
            providers = response.json()
            print_json(providers, "Available LLM Providers")
            
            # Test connection to OpenRouter (free model)
            if "openrouter" in providers and providers["openrouter"]:
                test_data = {
                    "provider": "openrouter",
                    "model": "deepseek/deepseek-chat"
                }
                
                response = requests.post(f"{API_BASE}/llm/test-connection", json=test_data, timeout=30)
                if response.status_code == 200:
                    print_json(response.json(), "LLM Connection Test")
                else:
                    print(f"LLM connection test failed: {response.status_code}")
            
            return True
        else:
            print(f"Failed to get LLM providers: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing LLM providers: {e}")
        return False

def test_mcp_client():
    """Test MCP client functionality"""
    try:
        print("\n🔌 Testing MCP Client:")
        
        # Get MCP status
        response = requests.get(f"{API_BASE}/mcp/status", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "MCP Client Status")
        
        # Get active connections
        response = requests.get(f"{API_BASE}/mcp/connections", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "Active MCP Connections")
        
        # Try to connect to a server (using first available server)
        servers_response = requests.get(f"{API_BASE}/servers/?limit=1", timeout=10)
        if servers_response.status_code == 200:
            servers = servers_response.json()
            if servers:
                server = servers[0]
                print(f"\n🔗 Attempting to connect to server: {server['name']}")
                
                connect_data = {"server_id": server["id"]}
                response = requests.post(f"{API_BASE}/mcp/connect", json=connect_data, timeout=30)
                
                if response.status_code == 200:
                    print_json(response.json(), "MCP Connection Result")
                    
                    # Try to list tools
                    response = requests.get(f"{API_BASE}/mcp/servers/{server['id']}/tools", timeout=10)
                    if response.status_code == 200:
                        print_json(response.json(), f"Available Tools for {server['name']}")
                    
                    # Get server capabilities
                    response = requests.get(f"{API_BASE}/mcp/servers/{server['id']}/capabilities", timeout=10)
                    if response.status_code == 200:
                        print_json(response.json(), f"Server Capabilities for {server['name']}")
                    
                else:
                    print(f"Failed to connect to MCP server: {response.status_code}")
                    if response.text:
                        print(f"Error: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"Error testing MCP client: {e}")
        return False

def test_enhanced_task_creation():
    """Test enhanced task creation with LLM integration"""
    try:
        print("\n📋 Testing Enhanced Task Creation:")
        
        # Create a complex task that would benefit from LLM analysis
        task_data = {
            "title": "Analyze GitHub Repository and Generate Report",
            "description": "I need to analyze a GitHub repository, extract key information about the codebase, identify the main technologies used, count lines of code, and generate a comprehensive report with insights and recommendations.",
            "priority": "high",
            "parameters": {
                "repository_url": "https://github.com/microsoft/vscode",
                "analysis_depth": "comprehensive",
                "include_metrics": True,
                "output_format": "markdown"
            }
        }
        
        response = requests.post(f"{API_BASE}/tasks/", json=task_data, timeout=10)
        if response.status_code == 200:
            task = response.json()
            print_json(task, "Created Enhanced Task")
            
            # Analyze the task using LLM
            analysis_data = {
                "task_id": task["id"],
                "provider": "openrouter",
                "model": "deepseek/deepseek-chat"
            }
            
            print(f"\n🧠 Analyzing task {task['id']} with LLM...")
            response = requests.post(f"{API_BASE}/llm/analyze-task", json=analysis_data, timeout=30)
            if response.status_code == 200:
                print_json(response.json(), "LLM Task Analysis")
            else:
                print(f"Task analysis failed: {response.status_code}")
                if response.text:
                    print(f"Error: {response.text}")
            
            return task["id"]
        else:
            print(f"Failed to create task: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error testing enhanced task creation: {e}")
        return None

def test_task_execution_monitoring(task_id: int):
    """Monitor task execution"""
    try:
        print(f"\n⏱️ Monitoring Task Execution (ID: {task_id}):")
        
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(f"{API_BASE}/tasks/{task_id}", timeout=10)
            if response.status_code == 200:
                task = response.json()
                status = task.get("status", "unknown")
                
                print(f"Attempt {attempt + 1}: Task status = {status}")
                
                if status in ["completed", "failed", "cancelled"]:
                    print_json(task, f"Final Task State (Status: {status})")
                    break
                
                time.sleep(3)  # Wait 3 seconds before next check
                attempt += 1
            else:
                print(f"Failed to get task status: {response.status_code}")
                break
        
        if attempt >= max_attempts:
            print("⚠️ Task monitoring timeout - task may still be running")
        
    except Exception as e:
        print(f"Error monitoring task execution: {e}")

def test_discovery_stats():
    """Test discovery statistics"""
    try:
        print("\n📊 Testing Discovery Statistics:")
        
        response = requests.get(f"{API_BASE}/discovery/stats", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "Discovery Statistics")
        
        # Get server statistics
        response = requests.get(f"{API_BASE}/servers/stats", timeout=10)
        if response.status_code == 200:
            print_json(response.json(), "Server Statistics")
        else:
            print(f"Server stats request failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"Error testing discovery stats: {e}")
        return False

def main():
    """Main demo function"""
    print_header("Enhanced Hisper Demo - AI-Powered MCP Server Management")
    
    # Basic health check
    print_header("1. System Health Check")
    if not test_health():
        print("❌ System is not healthy. Please ensure the backend is running.")
        return
    
    print("✅ System is healthy and operational!")
    
    # Test monitoring system
    print_header("2. Monitoring System")
    test_monitoring()
    
    # Test LLM integration
    print_header("3. LLM Integration")
    test_llm_providers()
    
    # Test MCP client
    print_header("4. MCP Client Functionality")
    test_mcp_client()
    
    # Test enhanced task creation
    print_header("5. Enhanced Task Management")
    task_id = test_enhanced_task_creation()
    
    if task_id:
        # Monitor task execution
        test_task_execution_monitoring(task_id)
    
    # Test discovery and statistics
    print_header("6. Discovery and Statistics")
    test_discovery_stats()
    
    # Summary of new features
    print_header("7. New Features Summary")
    print("""
🚀 Enhanced Hisper Features:

🤖 AI/LLM Integration:
   • Support for multiple LLM providers (OpenRouter, OpenAI, Anthropic, Ollama)
   • Intelligent task analysis and routing
   • Automatic server selection based on task requirements
   • Free models available through OpenRouter (DeepSeek, Llama, etc.)

🔌 MCP Protocol Communication:
   • Direct communication with MCP servers
   • Tool discovery and execution
   • Server health monitoring
   • Connection management

📊 Comprehensive Monitoring:
   • Real-time system metrics
   • Server performance tracking
   • Task execution monitoring
   • Prometheus metrics export
   • Alert system

🎯 Intelligent Task Routing:
   • LLM-powered task analysis
   • Automatic server selection
   • Execution plan generation
   • Real-time progress tracking

🔧 Configuration Options:
   • Multiple LLM provider support
   • Configurable monitoring thresholds
   • Flexible MCP server connections
   • Environment-based configuration

📈 Advanced Analytics:
   • Task success rates
   • Server performance metrics
   • Usage statistics
   • Historical data tracking
    """)
    
    print_header("Demo Complete!")
    print("""
✅ Enhanced Hisper is fully operational with AI-powered capabilities!

🔗 Access Points:
   • Frontend: http://localhost:12003
   • Backend API: http://localhost:12000
   • API Documentation: http://localhost:12000/docs
   • Monitoring Metrics: http://localhost:12000/api/v1/monitoring/metrics/prometheus

🚀 Next Steps:
   1. Configure your preferred LLM provider (OpenRouter, OpenAI, Anthropic, or Ollama)
   2. Set up API keys in environment variables
   3. Create complex tasks and watch AI route them intelligently
   4. Monitor system performance through the comprehensive dashboard
   5. Explore MCP server connections and tool execution

🔧 Configuration:
   • Set OPENROUTER_API_KEY for free AI models
   • Set OPENAI_API_KEY for OpenAI models
   • Set ANTHROPIC_API_KEY for Claude models
   • Configure OLLAMA_BASE_URL for local Ollama instance
    """)

if __name__ == "__main__":
    main()