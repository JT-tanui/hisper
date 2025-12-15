import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Search, 
  Play, 
  Pause, 
  RefreshCw,
  Github,
  Package,
  Settings,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react'
import { discoveryApi } from '../services/api'
import toast from 'react-hot-toast'

export default function Discovery() {
  const [manualUrl, setManualUrl] = useState('')
  const [manualName, setManualName] = useState('')
  const queryClient = useQueryClient()

  const { data: discoveryStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['discovery-status'],
    queryFn: () => discoveryApi.getDiscoveryStatus().then(res => res.data),
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const { data: discoverySources } = useQuery({
    queryKey: ['discovery-sources'],
    queryFn: () => discoveryApi.getDiscoverySources().then(res => res.data),
  })

  const { data: discoveryHistory } = useQuery({
    queryKey: ['discovery-history'],
    queryFn: () => discoveryApi.getDiscoveryHistory(20).then(res => res.data),
  })

  const { data: discoveryConfig } = useQuery({
    queryKey: ['discovery-config'],
    queryFn: () => discoveryApi.getDiscoveryConfig().then(res => res.data),
  })

  const startDiscoveryMutation = useMutation({
    mutationFn: discoveryApi.startDiscovery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-status'] })
      toast.success('Discovery process started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start discovery')
    },
  })

  const stopDiscoveryMutation = useMutation({
    mutationFn: discoveryApi.stopDiscovery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-status'] })
      toast.success('Discovery process stopped')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to stop discovery')
    },
  })

  const runOnceDiscoveryMutation = useMutation({
    mutationFn: discoveryApi.runDiscoveryOnce,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-status'] })
      toast.success('One-time discovery started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start discovery')
    },
  })

  const githubDiscoveryMutation = useMutation({
    mutationFn: discoveryApi.discoverFromGitHub,
    onSuccess: () => {
      toast.success('GitHub discovery started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start GitHub discovery')
    },
  })

  const npmDiscoveryMutation = useMutation({
    mutationFn: discoveryApi.discoverFromNpm,
    onSuccess: () => {
      toast.success('npm discovery started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start npm discovery')
    },
  })

  const pypiDiscoveryMutation = useMutation({
    mutationFn: discoveryApi.discoverFromPyPI,
    onSuccess: () => {
      toast.success('PyPI discovery started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start PyPI discovery')
    },
  })

  const manualDiscoveryMutation = useMutation({
    mutationFn: (data: { url: string; name?: string }) => discoveryApi.manualDiscovery(data),
    onSuccess: () => {
      setManualUrl('')
      setManualName('')
      queryClient.invalidateQueries({ queryKey: ['discovery-history'] })
      toast.success('Manual discovery initiated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add server manually')
    },
  })

  const clearUnverifiedMutation = useMutation({
    mutationFn: discoveryApi.clearUnverifiedServers,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['discovery-status'] })
      queryClient.invalidateQueries({ queryKey: ['discovery-history'] })
      toast.success(`Cleared ${data.data.deleted_count} unverified servers`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to clear unverified servers')
    },
  })

  const handleManualDiscovery = (e: React.FormEvent) => {
    e.preventDefault()
    if (!manualUrl.trim()) {
      toast.error('Please enter a URL')
      return
    }
    manualDiscoveryMutation.mutate({
      url: manualUrl.trim(),
      name: manualName.trim() || undefined,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Server Discovery</h1>
        <p className="mt-1 text-sm text-gray-500">
          Discover and manage MCP servers from various sources
        </p>
      </div>

      {/* Discovery Status */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Discovery Status</h2>
          <div className="flex items-center space-x-2">
            <div className={`h-2 w-2 rounded-full ${
              discoveryStatus?.is_running ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
            }`}></div>
            <span className="text-sm text-gray-500">
              {discoveryStatus?.is_running ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {discoveryStatus?.total_discovered || 0}
            </div>
            <div className="text-sm text-gray-500">Total Discovered</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-600">
              {discoveryConfig?.discovery_interval_minutes || 60}m
            </div>
            <div className="text-sm text-gray-500">Discovery Interval</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {Object.keys(discoveryStatus?.sources || {}).length}
            </div>
            <div className="text-sm text-gray-500">Active Sources</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          {discoveryStatus?.is_running ? (
            <button
              onClick={() => stopDiscoveryMutation.mutate()}
              disabled={stopDiscoveryMutation.isPending}
              className="btn-danger"
            >
              <Pause className="h-4 w-4 mr-2" />
              Stop Discovery
            </button>
          ) : (
            <button
              onClick={() => startDiscoveryMutation.mutate()}
              disabled={startDiscoveryMutation.isPending}
              className="btn-primary"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Discovery
            </button>
          )}
          
          <button
            onClick={() => runOnceDiscoveryMutation.mutate()}
            disabled={runOnceDiscoveryMutation.isPending}
            className="btn-outline"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Run Once
          </button>
          
          <button
            onClick={() => clearUnverifiedMutation.mutate()}
            disabled={clearUnverifiedMutation.isPending}
            className="btn-outline text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Unverified
          </button>
        </div>
      </div>

      {/* Discovery Sources */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Discovery Sources</h2>
          <div className="space-y-4">
            {discoverySources?.sources?.map((source: any) => (
              <div key={source.name} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-gray-100 rounded-lg mr-3">
                    {source.name === 'github' && <Github className="h-5 w-5 text-gray-600" />}
                    {source.name === 'npm' && <Package className="h-5 w-5 text-red-600" />}
                    {source.name === 'pypi' && <Package className="h-5 w-5 text-blue-600" />}
                    {source.name === 'manual' && <Plus className="h-5 w-5 text-green-600" />}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 capitalize">{source.name}</h3>
                    <p className="text-sm text-gray-500">{source.description}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {source.token_configured ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : source.requires_token ? (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                  <button
                    onClick={() => {
                      if (source.name === 'github') githubDiscoveryMutation.mutate()
                      else if (source.name === 'npm') npmDiscoveryMutation.mutate()
                      else if (source.name === 'pypi') pypiDiscoveryMutation.mutate()
                    }}
                    disabled={source.name === 'manual'}
                    className="btn-outline text-xs"
                  >
                    Discover
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Manual Discovery */}
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Manual Discovery</h2>
          <form onSubmit={handleManualDiscovery} className="space-y-4">
            <div>
              <label className="label">Server URL *</label>
              <input
                type="url"
                value={manualUrl}
                onChange={(e) => setManualUrl(e.target.value)}
                placeholder="https://github.com/user/mcp-server or npm:package-name"
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Server Name (Optional)</label>
              <input
                type="text"
                value={manualName}
                onChange={(e) => setManualName(e.target.value)}
                placeholder="Custom server name"
                className="input"
              />
            </div>
            <button
              type="submit"
              disabled={manualDiscoveryMutation.isPending}
              className="btn-primary w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Server
            </button>
          </form>
        </div>
      </div>

      {/* Discovery Statistics */}
      {discoveryStatus?.sources && Object.keys(discoveryStatus.sources).length > 0 && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Discovery Statistics</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Object.entries(discoveryStatus.sources).map(([source, count]) => (
              <div key={source} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{count as number}</div>
                <div className="text-sm text-gray-500 capitalize">{source}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Discoveries */}
      {discoveryHistory?.recent_discoveries && discoveryHistory.recent_discoveries.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Discoveries</h2>
          <div className="space-y-3">
            {discoveryHistory.recent_discoveries.slice(0, 10).map((server: any) => (
              <div key={server.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg mr-3 ${
                    server.is_verified ? 'bg-green-100' : 'bg-gray-100'
                  }`}>
                    <Search className={`h-4 w-4 ${
                      server.is_verified ? 'text-green-600' : 'text-gray-600'
                    }`} />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{server.name}</h3>
                    <p className="text-sm text-gray-500">
                      From {server.discovered_from} • {new Date(server.discovery_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {server.is_verified && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                  <span className={`badge ${
                    server.is_active ? 'badge-success' : 'badge-secondary'
                  }`}>
                    {server.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}