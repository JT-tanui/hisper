import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  Server, 
  Search, 
  Filter, 
  Plus,
  CheckCircle,
  AlertCircle,
  Activity,
  ExternalLink,
  Package,
  Calendar
} from 'lucide-react'
import { serverApi, MCPServer } from '../services/api'

export default function Servers() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [packageManagerFilter, setPackageManagerFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data: servers, isLoading, refetch } = useQuery({
    queryKey: ['servers', search, categoryFilter, packageManagerFilter, statusFilter],
    queryFn: () => serverApi.getServers({
      search: search || undefined,
      category: categoryFilter || undefined,
      package_manager: packageManagerFilter || undefined,
      is_active: statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined,
    }).then(res => res.data),
  })

  const { data: categories } = useQuery({
    queryKey: ['server-categories'],
    queryFn: () => serverApi.getCategories().then(res => res.data.categories),
  })

  const { data: packageManagers } = useQuery({
    queryKey: ['package-managers'],
    queryFn: () => serverApi.getPackageManagers().then(res => res.data.package_managers),
  })

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-400" />
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900">MCP Servers</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and monitor your discovered MCP servers
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => refetch()}
            className="btn-outline"
          >
            <Activity className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <Link to="/discovery" className="btn-primary">
            <Plus className="h-4 w-4 mr-2" />
            Discover Servers
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="label">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search servers..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          
          <div>
            <label className="label">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input"
            >
              <option value="">All Categories</option>
              {categories?.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="label">Package Manager</label>
            <select
              value={packageManagerFilter}
              onChange={(e) => setPackageManagerFilter(e.target.value)}
              className="input"
            >
              <option value="">All Package Managers</option>
              {packageManagers?.map((pm) => (
                <option key={pm} value={pm}>
                  {pm}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="label">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Servers Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
              <div className="flex space-x-2 mb-4">
                <div className="h-6 bg-gray-200 rounded w-16"></div>
                <div className="h-6 bg-gray-200 rounded w-20"></div>
              </div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : servers && servers.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {servers.map((server: MCPServer) => (
            <div key={server.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${
                    server.health_status === 'healthy' ? 'bg-green-100' : 
                    server.health_status === 'unhealthy' ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    <Server className={`h-5 w-5 ${
                      server.health_status === 'healthy' ? 'text-green-600' : 
                      server.health_status === 'unhealthy' ? 'text-red-600' : 'text-gray-600'
                    }`} />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-gray-900">{server.name}</h3>
                    {server.author && (
                      <p className="text-sm text-gray-500">by {server.author}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  {server.is_verified && (
                    <CheckCircle className="h-4 w-4 text-green-500" title="Verified" />
                  )}
                  {getHealthStatusIcon(server.health_status)}
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {server.description || 'No description available'}
              </p>

              <div className="flex flex-wrap gap-2 mb-4">
                {server.package_manager && (
                  <span className="badge badge-info">
                    <Package className="h-3 w-3 mr-1" />
                    {server.package_manager}
                  </span>
                )}
                <span className={`badge ${getHealthStatusBadge(server.health_status)}`}>
                  {server.health_status}
                </span>
                {server.categories?.slice(0, 2).map((category) => (
                  <span key={category} className="badge badge-secondary">
                    {category}
                  </span>
                ))}
                {server.categories && server.categories.length > 2 && (
                  <span className="badge badge-secondary">
                    +{server.categories.length - 2} more
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {new Date(server.discovery_date).toLocaleDateString()}
                </div>
                <div>
                  Usage: {server.usage_count}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Link
                  to={`/servers/${server.id}`}
                  className="text-primary-600 hover:text-primary-500 text-sm font-medium"
                >
                  View Details
                </Link>
                <div className="flex space-x-2">
                  {server.repository_url && (
                    <a
                      href={server.repository_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-gray-600"
                      title="View Repository"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Server className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No servers found</h3>
          <p className="text-gray-500 mb-4">
            {search || categoryFilter || packageManagerFilter || statusFilter
              ? 'Try adjusting your filters or search terms'
              : 'Start by discovering MCP servers from various sources'}
          </p>
          <Link to="/discovery" className="btn-primary">
            <Search className="h-4 w-4 mr-2" />
            Start Discovery
          </Link>
        </div>
      )}
    </div>
  )
}