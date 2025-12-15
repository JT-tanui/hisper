import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Key, 
  Bot, 
  Save, 
  TestTube, 
  Trash2, 
  RefreshCw,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  Upload
} from 'lucide-react';

interface APIKeys {
  openai_api_key?: string;
  anthropic_api_key?: string;
  openrouter_api_key?: string;
  ollama_base_url?: string;
}

interface ModelSettings {
  default_provider: string;
  default_model: string;
  auto_execute: boolean;
  show_server_details: boolean;
  max_context_messages: number;
  request_timeout: number;
}

interface UserSettings {
  api_keys: APIKeys;
  model_settings: ModelSettings;
}

interface AvailableModels {
  [provider: string]: string[];
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [availableModels, setAvailableModels] = useState<AvailableModels>({});
  const [providersWithKeys, setProvidersWithKeys] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [showKeys, setShowKeys] = useState<{[key: string]: boolean}>({});
  const [testResults, setTestResults] = useState<{[key: string]: any}>({});
  
  // Form state
  const [apiKeys, setApiKeys] = useState<APIKeys>({});
  const [modelSettings, setModelSettings] = useState<ModelSettings>({
    default_provider: 'openrouter',
    default_model: 'deepseek/deepseek-chat',
    auto_execute: true,
    show_server_details: true,
    max_context_messages: 10,
    request_timeout: 30
  });

  useEffect(() => {
    loadSettings();
    loadAvailableModels();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings/');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        setApiKeys(data.api_keys);
        setModelSettings(data.model_settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const response = await fetch('/api/v1/settings/available-models');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.available_models);
        setProvidersWithKeys(data.providers_with_keys);
      }
    } catch (error) {
      console.error('Failed to load available models:', error);
    }
  };

  const saveApiKeys = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/settings/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiKeys),
      });

      if (response.ok) {
        await loadSettings();
        await loadAvailableModels();
        alert('API keys saved successfully!');
      } else {
        alert('Failed to save API keys');
      }
    } catch (error) {
      console.error('Failed to save API keys:', error);
      alert('Failed to save API keys');
    } finally {
      setSaving(false);
    }
  };

  const saveModelSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/settings/model-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modelSettings),
      });

      if (response.ok) {
        await loadSettings();
        alert('Model settings saved successfully!');
      } else {
        alert('Failed to save model settings');
      }
    } catch (error) {
      console.error('Failed to save model settings:', error);
      alert('Failed to save model settings');
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async (provider: string, model: string) => {
    const testKey = `${provider}-${model}`;
    setTesting(testKey);
    
    try {
      const response = await fetch(`/api/v1/settings/test-connection?provider=${provider}&model=${model}`, {
        method: 'POST',
      });

      const result = await response.json();
      setTestResults(prev => ({ ...prev, [testKey]: result }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [testKey]: { 
          success: false, 
          message: 'Connection test failed', 
          error: error instanceof Error ? error.message : 'Unknown error' 
        } 
      }));
    } finally {
      setTesting(null);
    }
  };

  const deleteApiKey = async (provider: string) => {
    if (!confirm(`Are you sure you want to delete the API key for ${provider}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/settings/api-keys/${provider}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadSettings();
        await loadAvailableModels();
        alert(`API key for ${provider} deleted successfully!`);
      } else {
        alert(`Failed to delete API key for ${provider}`);
      }
    } catch (error) {
      console.error(`Failed to delete API key for ${provider}:`, error);
      alert(`Failed to delete API key for ${provider}`);
    }
  };

  const resetSettings = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults? This will delete all API keys.')) {
      return;
    }

    try {
      const response = await fetch('/api/v1/settings/reset', {
        method: 'POST',
      });

      if (response.ok) {
        await loadSettings();
        await loadAvailableModels();
        alert('Settings reset to defaults!');
      } else {
        alert('Failed to reset settings');
      }
    } catch (error) {
      console.error('Failed to reset settings:', error);
      alert('Failed to reset settings');
    }
  };

  const exportSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings/export');
      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'hisper-settings.json';
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to export settings:', error);
      alert('Failed to export settings');
    }
  };

  const toggleShowKey = (keyName: string) => {
    setShowKeys(prev => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <SettingsIcon className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          </div>
          <p className="text-lg text-gray-600">
            Configure your AI providers, API keys, and model preferences
          </p>
        </div>

        <div className="space-y-8">
          {/* API Keys Section */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <Key className="w-6 h-6 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-900">API Keys</h2>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={exportSettings}
                  className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-1"
                >
                  <Download className="w-4 h-4" />
                  <span>Export</span>
                </button>
                <button
                  onClick={resetSettings}
                  className="px-3 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors flex items-center space-x-1"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Reset</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* OpenAI */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  OpenAI API Key
                </label>
                <div className="flex space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type={showKeys.openai ? "text" : "password"}
                      value={apiKeys.openai_api_key || ''}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, openai_api_key: e.target.value }))}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      onClick={() => toggleShowKey('openai')}
                      className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                    >
                      {showKeys.openai ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  {providersWithKeys.includes('openai') && (
                    <button
                      onClick={() => deleteApiKey('openai')}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">OpenAI Platform</a>
                </p>
              </div>

              {/* Anthropic */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Anthropic API Key
                </label>
                <div className="flex space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type={showKeys.anthropic ? "text" : "password"}
                      value={apiKeys.anthropic_api_key || ''}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, anthropic_api_key: e.target.value }))}
                      placeholder="sk-ant-..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      onClick={() => toggleShowKey('anthropic')}
                      className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                    >
                      {showKeys.anthropic ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  {providersWithKeys.includes('anthropic') && (
                    <button
                      onClick={() => deleteApiKey('anthropic')}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  Get your API key from <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Anthropic Console</a>
                </p>
              </div>

              {/* OpenRouter */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  OpenRouter API Key <span className="text-green-600 text-xs">(Free models available)</span>
                </label>
                <div className="flex space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type={showKeys.openrouter ? "text" : "password"}
                      value={apiKeys.openrouter_api_key || ''}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, openrouter_api_key: e.target.value }))}
                      placeholder="sk-or-..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      onClick={() => toggleShowKey('openrouter')}
                      className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                    >
                      {showKeys.openrouter ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  {providersWithKeys.includes('openrouter') && (
                    <button
                      onClick={() => deleteApiKey('openrouter')}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  Get your API key from <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">OpenRouter</a>. Includes free models!
                </p>
              </div>

              {/* Ollama */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Ollama Base URL <span className="text-blue-600 text-xs">(Local models)</span>
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={apiKeys.ollama_base_url || ''}
                    onChange={(e) => setApiKeys(prev => ({ ...prev, ollama_base_url: e.target.value }))}
                    placeholder="http://localhost:11434"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-500">
                  Install Ollama locally from <a href="https://ollama.ai" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">ollama.ai</a>
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={saveApiKeys}
                disabled={saving}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                <span>{saving ? 'Saving...' : 'Save API Keys'}</span>
              </button>
            </div>
          </div>

          {/* Model Settings Section */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center space-x-3 mb-6">
              <Bot className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">Model Settings</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Default Provider */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Default AI Provider
                </label>
                <select
                  value={modelSettings.default_provider}
                  onChange={(e) => setModelSettings(prev => ({ ...prev, default_provider: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.keys(availableModels).map(provider => (
                    <option key={provider} value={provider}>
                      {provider.charAt(0).toUpperCase() + provider.slice(1)}
                      {providersWithKeys.includes(provider) ? ' ✓' : ' (No API key)'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Default Model */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Default Model
                </label>
                <div className="flex space-x-2">
                  <select
                    value={modelSettings.default_model}
                    onChange={(e) => setModelSettings(prev => ({ ...prev, default_model: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {availableModels[modelSettings.default_provider]?.map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => testConnection(modelSettings.default_provider, modelSettings.default_model)}
                    disabled={testing === `${modelSettings.default_provider}-${modelSettings.default_model}`}
                    className="px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors flex items-center space-x-1"
                  >
                    {testing === `${modelSettings.default_provider}-${modelSettings.default_model}` ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <TestTube className="w-4 h-4" />
                    )}
                    <span>Test</span>
                  </button>
                </div>
                
                {/* Test Result */}
                {testResults[`${modelSettings.default_provider}-${modelSettings.default_model}`] && (
                  <div className={`p-3 rounded-lg text-sm ${
                    testResults[`${modelSettings.default_provider}-${modelSettings.default_model}`].success
                      ? 'bg-green-50 text-green-800 border border-green-200'
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    <div className="flex items-center space-x-2">
                      {testResults[`${modelSettings.default_provider}-${modelSettings.default_model}`].success ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      <span>{testResults[`${modelSettings.default_provider}-${modelSettings.default_model}`].message}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Settings */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Max Context Messages
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={modelSettings.max_context_messages}
                  onChange={(e) => setModelSettings(prev => ({ ...prev, max_context_messages: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500">Number of previous messages to include for context</p>
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Request Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="10"
                  max="120"
                  value={modelSettings.request_timeout}
                  onChange={(e) => setModelSettings(prev => ({ ...prev, request_timeout: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500">Maximum time to wait for AI responses</p>
              </div>
            </div>

            {/* Checkboxes */}
            <div className="mt-6 space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={modelSettings.auto_execute}
                  onChange={(e) => setModelSettings(prev => ({ ...prev, auto_execute: e.target.checked }))}
                  className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">Auto-execute suggested actions</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={modelSettings.show_server_details}
                  onChange={(e) => setModelSettings(prev => ({ ...prev, show_server_details: e.target.checked }))}
                  className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">Show server and tool details in chat</span>
              </label>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={saveModelSettings}
                disabled={saving}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                <span>{saving ? 'Saving...' : 'Save Model Settings'}</span>
              </button>
            </div>
          </div>

          {/* Available Models Overview */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Models</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(availableModels).map(([provider, models]) => (
                <div key={provider} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900 capitalize">{provider}</h4>
                    {providersWithKeys.includes(provider) ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-yellow-600" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{models.length} models available</p>
                  <div className="space-y-1">
                    {models.slice(0, 3).map(model => (
                      <div key={model} className="text-xs text-gray-500 truncate" title={model}>
                        {model}
                      </div>
                    ))}
                    {models.length > 3 && (
                      <div className="text-xs text-gray-400">
                        +{models.length - 3} more...
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;