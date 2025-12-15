import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Server, 
  ExternalLink, 
  Package, 
  Calendar,
  CheckCircle,
  AlertCircle,
  Activity,
  Clock,
  TrendingUp,
  Settings
} from 'lucide-react'
import { serverApi } from '../services/api'

export default function ServerDetail() {
  const { id } = useParams<{ id: string }>()
  const serverId = parseInt(id || '0')

  const { data: server, isLoading, error } = useQuery({
    queryKey: ['server', serverId],
    queryFn: () => serverApi.getServer(serverId).then(res => res.data),
    enabled: !!serverId,
  })

  const { data: serverHealth } = useQuery({
    queryKey: ['server-health', serverId],
    queryFn: () => serverApi.getServerHealth(serverId).then(res => res.data),
    enabled: !!serverId,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <div className="h-8 w-8 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <div className="h-6 w-32 bg-gray-200 rounded mb-4 animate-pulse"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>
              </div>
            </div>
          </div>
          <div className="space-y-6">
            <div className="card">
              <div className="h-6 w-24 bg-gray-200 rounded mb-4 animate-pulse"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !server) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-400" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Server not found</h3>
        <p className="text-gray-500 mb-4">The server you're looking for doesn't exist or has been removed.</p>
        <Link to="/servers" className="btn-primary">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Servers
        </Link>
      </div>
    )
  }

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'unhealthy':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Activity className="h-5 w-5 text-gray-400" />
    }
  }

  const getHealthStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'badge-success'
      case 'unhealthy':
        return 'badge-error'
      default:
        return 'badge-secondary'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/servers" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-lg ${
              server.health_status === 'healthy' ? 'bg-green-100' : 
              server.health_status === 'unhealthy' ? 'bg-red-100' : 'bg-gray-100'
            }`}>
              <Server className={`h-6 w-6 ${
                server.health_status === 'healthy' ? 'text-green-600' : 
                server.health_status === 'unhealthy' ? 'text-red-600' : 'text-gray-600'
              }`} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{server.name}</h1>
              {server.author && (
                <p className="text-sm text-gray-500">by {server.author}</p>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {server.is_verified && (
            <div className="flex items-center space-x-1 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Verified</span>
            </div>
          )}
          <span className={`badge ${getHealthStatusBadge(server.health_status)}`}>
            {server.health_status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Description</h2>
            <p className="text-gray-600">
              {server.description || 'No description available for this server.'}
            </p>
          </div>

          {/* Capabilities */}
          {server.capabilities && server.capabilities.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Capabilities</h2>
              <div className="flex flex-wrap gap-2">
                {server.capabilities.map((capability, index) => (
                  <span key={index} className="badge badge-info">
                    {capability}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Categories */}
          {server.categories && server.categories.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Categories</h2>
              <div className="flex flex-wrap gap-2">
                {server.categories.map((category, index) => (
                  <span key={index} className="badge badge-secondary">
                    {category}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          {server.metadata && Object.keys(server.metadata).length > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Additional Information</h2>
              <div className="space-y-3">
                {Object.entries(server.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500 capitalize">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-sm text-gray-900">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Server Info */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Server Information</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Status:</span>
                <div className="flex items-center space-x-1">
                  {getHealthStatusIcon(server.health_status)}
                  <span className="text-sm text-gray-900">{server.health_status}</span>
                </div>
              </div>
              
              {server.package_manager && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Package Manager:</span>
                  <div className="flex items-center space-x-1">
                    <Package className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-900">{server.package_manager}</span>
                  </div>
                </div>
              )}
              
              {server.version && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Version:</span>
                  <span className="text-sm text-gray-900">{server.version}</span>
                </div>
              )}
              
              {server.license && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">License:</span>
                  <span className="text-sm text-gray-900">{server.license}</span>
                </div>
              )}
              
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Discovered:</span>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-900">
                    {new Date(server.discovery_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
              
              {server.discovered_from && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Source:</span>
                  <span className="text-sm text-gray-900 capitalize">{server.discovered_from}</span>
                </div>
              )}
            </div>
          </div>

          {/* Health Status */}
          {serverHealth && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Health Status</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Status:</span>
                  <span className={`badge ${getHealthStatusBadge(serverHealth.status)}`}>
                    {serverHealth.status}
                  </span>
                </div>
                
                {serverHealth.response_time_ms && (
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Response Time:</span>
                    <span className="text-sm text-gray-900">{serverHealth.response_time_ms}ms</span>
                  </div>
                )}
                
                {serverHealth.last_check && (
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Last Check:</span>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-900">
                        {new Date(serverHealth.last_check).toLocaleString()}
                      </span>
                    </div>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Capabilities Verified:</span>
                  <span className="text-sm text-gray-900">
                    {serverHealth.capabilities_verified ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Usage Statistics */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Usage Statistics</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Usage Count:</span>
                <span className="text-sm text-gray-900">{server.usage_count}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Success Rate:</span>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-gray-900">{server.success_rate.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Actions</h2>
            <div className="space-y-3">
              {server.repository_url && (
                <a
                  href={server.repository_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-outline w-full"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Repository
                </a>
              )}
              
              <button className="btn-outline w-full">
                <Activity className="h-4 w-4 mr-2" />
                Check Health
              </button>
              
              <button className="btn-outline w-full">
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}