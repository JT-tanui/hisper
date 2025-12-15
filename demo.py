#!/usr/bin/env python3
"""
Hisper API Demo Script
Demonstrates the functionality of the Hisper MCP Server Discovery Platform
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
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_json(data: Any, title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))

def check_health() -> bool:
    """Check if the API is healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print_json(health_data, "Health Check")
            return True
        else:
            print(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False

def get_server_stats() -> Dict:
    """Get server statistics"""
    try:
        response = requests.get(f"{API_BASE}/servers/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get server stats: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error getting server stats: {e}")
        return {}

def get_servers(limit: int = 10) -> List[Dict]:
    """Get list of discovered servers"""
    try:
        response = requests.get(f"{API_BASE}/servers/?limit={limit}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get servers: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting servers: {e}")
        return []

def get_server_details(server_id: int) -> Dict:
    """Get detailed information about a specific server"""
    try:
        response = requests.get(f"{API_BASE}/servers/{server_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get server details: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error getting server details: {e}")
        return {}

def create_sample_task(server_id: int) -> Dict:
    """Create a sample task"""
    task_data = {
        "title": "Demo Task - Test MCP Server Connection",
        "description": "This is a demonstration task created by the demo script",
        "server_id": server_id,
        "priority": "normal",
        "parameters": {
            "action": "test_connection",
            "timeout": 30
        }
    }
    
    try:
        response = requests.post(f"{API_BASE}/tasks/", json=task_data, timeout=10)
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Failed to create task: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error creating task: {e}")
        return {}

def get_tasks(limit: int = 5) -> List[Dict]:
    """Get list of tasks"""
    try:
        response = requests.get(f"{API_BASE}/tasks/?limit={limit}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get tasks: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return []

def trigger_discovery() -> Dict:
    """Trigger manual discovery"""
    try:
        response = requests.post(f"{API_BASE}/discovery/discover", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to trigger discovery: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error triggering discovery: {e}")
        return {}

def main():
    """Main demo function"""
    print_header("Hisper MCP Server Discovery Platform - API Demo")
    
    # Check health
    print_header("1. Health Check")
    if not check_health():
        print("❌ API is not healthy. Please ensure the backend is running.")
        return
    
    print("✅ API is healthy and running!")
    
    # Get server statistics
    print_header("2. Server Statistics")
    stats = get_server_stats()
    if stats:
        print_json(stats, "Server Statistics")
        print(f"\n📊 Summary:")
        print(f"   • Total Servers: {stats.get('total_servers', 0)}")
        print(f"   • Active Servers: {stats.get('active_servers', 0)}")
        print(f"   • Healthy Servers: {stats.get('healthy_servers', 0)}")
    
    # Get discovered servers
    print_header("3. Discovered MCP Servers (Top 10)")
    servers = get_servers(10)
    if servers:
        print(f"Found {len(servers)} servers. Here are the details:\n")
        
        for i, server in enumerate(servers[:5], 1):
            print(f"{i}. {server['name']}")
            print(f"   📦 Package: {server.get('package_name', 'N/A')}")
            print(f"   🔗 URL: {server.get('url', 'N/A')}")
            print(f"   📝 Description: {server.get('description', 'No description')[:100]}...")
            print(f"   🏷️  Version: {server.get('version', 'N/A')}")
            print(f"   📊 Source: {server.get('discovered_from', 'N/A')}")
            print(f"   ✅ Status: {'Active' if server.get('is_active') else 'Inactive'}")
            print()
    
    # Get detailed information about the first server
    if servers:
        print_header("4. Server Details Example")
        first_server = servers[0]
        server_details = get_server_details(first_server['id'])
        if server_details:
            print_json(server_details, f"Details for '{first_server['name']}'")
    
    # Create a sample task
    if servers:
        print_header("5. Task Creation Demo")
        first_server = servers[0]
        task = create_sample_task(first_server['id'])
        if task:
            print_json(task, "Created Task")
            print(f"\n✅ Successfully created task with ID: {task.get('id')}")
    
    # Get tasks
    print_header("6. Task List")
    tasks = get_tasks(5)
    if tasks:
        print(f"Found {len(tasks)} tasks:\n")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task['title']}")
            print(f"   📋 Status: {task.get('status', 'Unknown')}")
            print(f"   🎯 Priority: {task.get('priority', 'Normal')}")
            print(f"   📅 Created: {task.get('created_at', 'N/A')}")
            print()
    
    # Discovery capabilities
    print_header("7. Discovery Sources")
    print("Hisper discovers MCP servers from multiple sources:")
    print("   🐙 GitHub Repositories")
    print("   📦 npm Registry")
    print("   🐍 PyPI (Python Package Index)")
    print("   ✋ Manual Registration")
    
    print("\n🔍 Discovery Features:")
    print("   • Automated periodic discovery")
    print("   • Real-time server health monitoring")
    print("   • Capability detection and categorization")
    print("   • Version tracking and updates")
    print("   • Usage statistics and success rates")
    
    # API endpoints summary
    print_header("8. Available API Endpoints")
    endpoints = [
        ("GET", "/health", "Application health check"),
        ("GET", "/api/v1/servers/", "List all discovered servers"),
        ("GET", "/api/v1/servers/{id}", "Get server details"),
        ("POST", "/api/v1/servers/", "Register new server"),
        ("PUT", "/api/v1/servers/{id}", "Update server"),
        ("DELETE", "/api/v1/servers/{id}", "Remove server"),
        ("GET", "/api/v1/servers/stats", "Server statistics"),
        ("GET", "/api/v1/tasks/", "List all tasks"),
        ("POST", "/api/v1/tasks/", "Create new task"),
        ("GET", "/api/v1/tasks/{id}", "Get task details"),
        ("PUT", "/api/v1/tasks/{id}", "Update task"),
        ("POST", "/api/v1/discovery/discover", "Trigger manual discovery"),
        ("GET", "/api/v1/discovery/stats", "Discovery statistics"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:6} {endpoint:30} - {description}")
    
    # Web interface information
    print_header("9. Web Interface")
    print("🌐 Frontend Application:")
    print("   • Modern React-based interface")
    print("   • Real-time updates via WebSocket")
    print("   • Server browsing and management")
    print("   • Task creation and monitoring")
    print("   • Discovery interface")
    print("   • Responsive design for all devices")
    
    print(f"\n🔗 Access URLs:")
    print(f"   • Frontend: http://localhost:12003")
    print(f"   • Backend API: {BASE_URL}")
    print(f"   • API Documentation: {BASE_URL}/docs")
    print(f"   • OpenAPI Schema: {BASE_URL}/openapi.json")
    
    print_header("Demo Complete!")
    print("✅ Hisper is fully operational and ready to discover and manage MCP servers!")
    print("\n🚀 Next Steps:")
    print("   1. Open the web interface at http://localhost:12003")
    print("   2. Browse the discovered MCP servers")
    print("   3. Create and manage tasks")
    print("   4. Explore the API documentation at http://localhost:12000/docs")
    print("\n🔧 For development:")
    print("   • Backend logs: Check the terminal where you started the backend")
    print("   • Frontend logs: Check frontend.log in the frontend directory")
    print("   • Database: SQLite file at backend/hisper.db")

if __name__ == "__main__":
    main()