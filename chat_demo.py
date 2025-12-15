#!/usr/bin/env python3
"""
Hisper Chat Interface Demo Script
Demonstrates the new AI-powered chat interface for interacting with MCP servers
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

def test_chat_suggestions():
    """Test chat suggestions endpoint"""
    try:
        print("\n🎯 Testing Chat Suggestions:")
        
        response = requests.get(f"{API_BASE}/chat/suggestions", timeout=10)
        if response.status_code == 200:
            suggestions = response.json()
            print_json(suggestions, "Available Chat Suggestions")
            return suggestions["suggestions"]
        else:
            print(f"Failed to get suggestions: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error testing chat suggestions: {e}")
        return []

def test_chat_analysis(message: str):
    """Test chat message analysis"""
    try:
        print(f"\n🧠 Testing Chat Analysis for: '{message}'")
        
        analysis_data = {
            "message": message,
            "provider": "openrouter",
            "model": "deepseek/deepseek-chat",
            "context": []
        }
        
        response = requests.post(f"{API_BASE}/chat/analyze", json=analysis_data, timeout=30)
        if response.status_code == 200:
            analysis = response.json()
            print_json(analysis, "AI Analysis Result")
            return analysis
        else:
            print(f"Analysis failed: {response.status_code}")
            if response.text:
                print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error testing chat analysis: {e}")
        return None

def test_chat_execution(action: Dict[str, Any]):
    """Test chat action execution"""
    try:
        print(f"\n⚡ Testing Action Execution: {action.get('type', 'unknown')}")
        
        execution_data = {
            "action": action,
            "provider": "openrouter",
            "model": "deepseek/deepseek-chat"
        }
        
        response = requests.post(f"{API_BASE}/chat/execute", json=execution_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print_json(result, "Execution Result")
            return result
        else:
            print(f"Execution failed: {response.status_code}")
            if response.text:
                print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error testing chat execution: {e}")
        return None

def test_chat_providers():
    """Test available chat providers"""
    try:
        print("\n🤖 Testing Available Chat Providers:")
        
        response = requests.get(f"{API_BASE}/chat/providers", timeout=10)
        if response.status_code == 200:
            providers = response.json()
            print_json(providers, "Available LLM Providers for Chat")
            return providers
        else:
            print(f"Failed to get providers: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"Error testing chat providers: {e}")
        return {}

def test_chat_stats():
    """Test chat statistics"""
    try:
        print("\n📊 Testing Chat Statistics:")
        
        response = requests.get(f"{API_BASE}/chat/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print_json(stats, "Chat Usage Statistics")
            return stats
        else:
            print(f"Failed to get stats: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"Error testing chat stats: {e}")
        return {}

def simulate_chat_conversation():
    """Simulate a complete chat conversation"""
    print_header("Simulating Complete Chat Conversation")
    
    # Test messages that demonstrate different capabilities
    test_messages = [
        "Find GitHub servers that can analyze code repositories",
        "Connect to a file system server and show me what tools are available",
        "Search for servers that can help with web scraping",
        "Create a task to analyze the Microsoft VS Code repository"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Chat Turn {i} ---")
        print(f"User: {message}")
        
        # Analyze the message
        analysis = test_chat_analysis(message)
        
        if analysis and analysis.get("suggestedActions"):
            # Execute the first suggested action
            first_action = analysis["suggestedActions"][0]
            print(f"\nExecuting suggested action: {first_action.get('description', 'No description')}")
            
            execution_result = test_chat_execution(first_action)
            
            if execution_result and execution_result.get("success"):
                print(f"✅ Action completed successfully!")
                print(f"Result: {execution_result.get('result', 'No result')[:200]}...")
            else:
                print(f"❌ Action failed")
        
        # Add a small delay between messages
        time.sleep(2)

def test_frontend_integration():
    """Test frontend integration points"""
    print_header("Testing Frontend Integration Points")
    
    # Test all the endpoints that the frontend will use
    endpoints_to_test = [
        ("/chat/suggestions", "GET", None),
        ("/chat/providers", "GET", None),
        ("/chat/stats", "GET", None),
        ("/chat/analyze", "POST", {
            "message": "Hello, can you help me find some servers?",
            "provider": "openrouter",
            "model": "deepseek/deepseek-chat"
        }),
    ]
    
    for endpoint, method, data in endpoints_to_test:
        try:
            print(f"\n🔗 Testing {method} {endpoint}")
            
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Success")
                result = response.json()
                if isinstance(result, dict) and len(str(result)) > 500:
                    print(f"   Response: Large response ({len(str(result))} chars)")
                else:
                    print(f"   Response: {result}")
            else:
                print(f"❌ {endpoint} - Failed ({response.status_code})")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def main():
    """Main demo function"""
    print_header("Hisper AI Chat Interface Demo")
    
    # Test basic health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy and operational!")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Test chat suggestions
    suggestions = test_chat_suggestions()
    
    # Test chat providers
    providers = test_chat_providers()
    
    # Test chat stats
    stats = test_chat_stats()
    
    # Test frontend integration
    test_frontend_integration()
    
    # Simulate a complete conversation
    simulate_chat_conversation()
    
    # Summary
    print_header("Demo Summary")
    print("""
🎉 Chat Interface Demo Complete!

✅ Features Tested:
   • Chat suggestions endpoint
   • LLM provider integration
   • Message analysis with AI
   • Action execution system
   • Frontend integration points
   • Complete conversation simulation

🚀 Key Capabilities Demonstrated:
   • Natural language understanding
   • Intelligent server discovery
   • Automatic action suggestion
   • Real-time task execution
   • Multi-provider AI support

🔗 Frontend Access:
   • Chat Interface: http://localhost:12003/chat
   • API Documentation: http://localhost:12000/docs
   • Backend Health: http://localhost:12000/health

💡 Next Steps:
   1. Open the frontend at http://localhost:12003/chat
   2. Try the suggested prompts or create your own
   3. Watch as AI analyzes your requests and executes actions
   4. Explore the different LLM providers and models
   5. Monitor real-time execution and results

🔧 Configuration Tips:
   • Set OPENROUTER_API_KEY for free AI models
   • Enable auto-execution for seamless experience
   • Turn on server details to see which tools are used
   • Try different AI providers for varied responses
    """)

if __name__ == "__main__":
    main()