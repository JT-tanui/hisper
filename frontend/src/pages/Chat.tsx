import React, { useState, useEffect } from 'react';
import { MessageSquare, Zap, Server, TrendingUp, HelpCircle } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import VoiceChatWidget from '../components/VoiceChatWidget';

const Chat: React.FC = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [stats, setStats] = useState({
    totalMessages: 0,
    totalTasks: 0,
    serversUsed: 0,
    successRate: 0,
    averageResponseTime: 0
  });

  useEffect(() => {
    // Load suggestions and stats
    loadSuggestions();
    loadStats();
  }, []);

  const loadSuggestions = async () => {
    try {
      const response = await fetch('/api/v1/chat/suggestions');
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/v1/chat/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <MessageSquare className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">AI Chat Interface</h1>
          </div>
          <p className="text-lg text-gray-600">
            Interact with AI to discover and use MCP servers for any task. Just describe what you need, 
            and I'll find the right tools and execute them for you.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Chat Interface */}
          <div className="lg:col-span-3">
            <div className="h-[700px]">
              <ChatInterface />
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <VoiceChatWidget />
            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                Chat Statistics
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Messages</span>
                  <span className="text-sm font-medium">{stats.totalMessages}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Tasks Created</span>
                  <span className="text-sm font-medium">{stats.totalTasks}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Servers Used</span>
                  <span className="text-sm font-medium">{stats.serversUsed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Success Rate</span>
                  <span className="text-sm font-medium">{(stats.successRate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Avg Response</span>
                  <span className="text-sm font-medium">{stats.averageResponseTime.toFixed(0)}ms</span>
                </div>
              </div>
            </div>

            {/* Suggested Prompts */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2" />
                Try These Prompts
              </h3>
              <div className="space-y-2">
                {suggestions.slice(0, 6).map((suggestion, index) => (
                  <button
                    key={index}
                    className="w-full text-left p-3 text-sm text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                    onClick={() => {
                      // This would set the input in the chat interface
                      // For now, we'll just copy to clipboard
                      navigator.clipboard.writeText(suggestion);
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>

            {/* Server Status */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Server className="w-5 h-5 mr-2" />
                MCP Servers
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Discovered</span>
                  <span className="text-sm font-medium text-green-600">132</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Active Connections</span>
                  <span className="text-sm font-medium text-blue-600">0</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Available Tools</span>
                  <span className="text-sm font-medium text-purple-600">500+</span>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <a
                  href="/servers"
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  View All Servers →
                </a>
              </div>
            </div>

            {/* Help & Tips */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <HelpCircle className="w-5 h-5 mr-2" />
                Tips & Help
              </h3>
              <div className="space-y-3 text-sm text-gray-600">
                <div>
                  <strong>Natural Language:</strong> Describe tasks in plain English. 
                  The AI will understand and find the right tools.
                </div>
                <div>
                  <strong>Auto-Execute:</strong> Enable auto-execution in settings 
                  to have the AI automatically run suggested actions.
                </div>
                <div>
                  <strong>Server Details:</strong> Turn on server details to see 
                  which MCP servers and tools are being used.
                </div>
                <div>
                  <strong>Examples:</strong> Try asking to "analyze a GitHub repo", 
                  "find file servers", or "create a development task".
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Highlights */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6 text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Natural Language Interface</h3>
            <p className="text-gray-600">
              Describe what you need in plain English. No need to learn complex commands or APIs.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Intelligent Automation</h3>
            <p className="text-gray-600">
              AI automatically finds the right MCP servers and executes the appropriate tools for your tasks.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Server className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibent text-gray-900 mb-2">Vast Tool Ecosystem</h3>
            <p className="text-gray-600">
              Access hundreds of tools across 132+ MCP servers for development, analysis, and automation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;