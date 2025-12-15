import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, Settings, Zap, Server, AlertCircle } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    taskId?: number;
    serverId?: number;
    serverName?: string;
    toolsUsed?: string[];
    executionTime?: number;
    status?: 'success' | 'error' | 'pending';
  };
}

interface ChatSettings {
  provider: string;
  model: string;
  autoExecute: boolean;
  showServerDetails: boolean;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: 'Welcome to Hisper AI Chat! I can help you discover and use MCP servers to accomplish various tasks. Just tell me what you need to do, and I\'ll find the right tools and execute them for you.',
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<ChatSettings>({
    provider: 'openrouter',
    model: 'deepseek/deepseek-chat',
    autoExecute: true,
    showServerDetails: true,
  });
  const [availableModels, setAvailableModels] = useState<{[key: string]: string[]}>({});
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load settings and available models on component mount
    loadUserSettings();
    loadAvailableModels();
  }, []);

  const loadUserSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings/');
      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({
          ...prev,
          provider: data.model_settings.default_provider,
          model: data.model_settings.default_model,
          autoExecute: data.model_settings.auto_execute,
          showServerDetails: data.model_settings.show_server_details,
        }));
      }
    } catch (error) {
      console.error('Failed to load user settings:', error);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const response = await fetch('/api/v1/settings/available-models');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.available_models);
      }
    } catch (error) {
      console.error('Failed to load available models:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // First, analyze the task with AI
      const analysisResponse = await fetch('/api/v1/chat/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputMessage,
          provider: settings.provider,
          model: settings.model,
          context: messages.slice(-5), // Send last 5 messages for context
        }),
      });

      if (!analysisResponse.ok) {
        throw new Error('Failed to analyze message');
      }

      const analysis = await analysisResponse.json();

      // Add AI analysis message
      const analysisMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: analysis.analysis,
        timestamp: new Date(),
        metadata: {
          status: 'pending',
        },
      };

      setMessages(prev => [...prev, analysisMessage]);

      // If auto-execute is enabled and the AI suggests actions, execute them
      if (settings.autoExecute && analysis.suggestedActions?.length > 0) {
        for (const action of analysis.suggestedActions) {
          await executeAction(action);
        }
      }

    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
        metadata: { status: 'error' },
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const executeAction = async (action: any) => {
    try {
      const executionResponse = await fetch('/api/v1/chat/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          provider: settings.provider,
          model: settings.model,
        }),
      });

      if (!executionResponse.ok) {
        throw new Error('Failed to execute action');
      }

      const result = await executionResponse.json();

      const resultMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: result.result,
        timestamp: new Date(),
        metadata: {
          taskId: result.taskId,
          serverId: result.serverId,
          serverName: result.serverName,
          toolsUsed: result.toolsUsed,
          executionTime: result.executionTime,
          status: result.success ? 'success' : 'error',
        },
      };

      setMessages(prev => [...prev, resultMessage]);

    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'system',
        content: `Execution error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: { status: 'error' },
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getMessageIcon = (type: string, status?: string) => {
    if (type === 'user') return <User className="w-5 h-5" />;
    if (type === 'system') return <AlertCircle className="w-5 h-5" />;
    if (status === 'pending') return <Loader className="w-5 h-5 animate-spin" />;
    return <Bot className="w-5 h-5" />;
  };

  const getMessageBgColor = (type: string, status?: string) => {
    if (type === 'user') return 'bg-blue-50 border-blue-200';
    if (type === 'system') return 'bg-yellow-50 border-yellow-200';
    if (status === 'error') return 'bg-red-50 border-red-200';
    if (status === 'success') return 'bg-green-50 border-green-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Bot className="w-6 h-6 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
            {settings.provider} • {settings.model}
          </span>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AI Provider
              </label>
              <select
                value={settings.provider}
                onChange={(e) => setSettings(prev => ({ ...prev, provider: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.keys(availableModels).map(provider => (
                  <option key={provider} value={provider}>
                    {provider.charAt(0).toUpperCase() + provider.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model
              </label>
              <select
                value={settings.model}
                onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableModels[settings.provider]?.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.autoExecute}
                  onChange={(e) => setSettings(prev => ({ ...prev, autoExecute: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Auto-execute suggested actions</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.showServerDetails}
                  onChange={(e) => setSettings(prev => ({ ...prev, showServerDetails: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Show server details</span>
              </label>
            </div>
            <a
              href="/settings"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Advanced Settings →
            </a>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start space-x-3 p-3 rounded-lg border ${getMessageBgColor(message.type, message.metadata?.status)}`}
          >
            <div className="flex-shrink-0 mt-1">
              {getMessageIcon(message.type, message.metadata?.status)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-sm font-medium text-gray-900">
                  {message.type === 'user' ? 'You' : message.type === 'system' ? 'System' : 'AI Assistant'}
                </span>
                <span className="text-xs text-gray-500">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <div className="text-sm text-gray-700 whitespace-pre-wrap">
                {message.content}
              </div>
              
              {/* Metadata */}
              {message.metadata && settings.showServerDetails && (
                <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                  <div className="flex items-center space-x-4 text-xs text-gray-600">
                    {message.metadata.serverName && (
                      <div className="flex items-center space-x-1">
                        <Server className="w-3 h-3" />
                        <span>{message.metadata.serverName}</span>
                      </div>
                    )}
                    {message.metadata.toolsUsed && (
                      <div className="flex items-center space-x-1">
                        <Zap className="w-3 h-3" />
                        <span>{message.metadata.toolsUsed.join(', ')}</span>
                      </div>
                    )}
                    {message.metadata.executionTime && (
                      <span>{message.metadata.executionTime}ms</span>
                    )}
                    {message.metadata.status && (
                      <span className={`px-2 py-1 rounded-full ${
                        message.metadata.status === 'success' ? 'bg-green-100 text-green-800' :
                        message.metadata.status === 'error' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {message.metadata.status}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-center space-x-3 p-3 rounded-lg border bg-gray-50 border-gray-200">
            <Loader className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-sm text-gray-600">AI is thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me to help you with any task using MCP servers..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;