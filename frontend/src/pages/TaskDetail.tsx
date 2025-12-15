import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  CheckSquare, 
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
  Play,
  X,
  RefreshCw,
  Calendar,
  Server,
  User,
  Tag
} from 'lucide-react'
import { taskApi } from '../services/api'

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const taskId = parseInt(id || '0')

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.getTask(taskId).then(res => res.data),
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Refresh more frequently for running tasks
      return data?.status === 'running' ? 2000 : 10000
    },
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

  if (error || !task) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-400" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Task not found</h3>
        <p className="text-gray-500 mb-4">The task you're looking for doesn't exist or has been removed.</p>
        <Link to="/tasks" className="btn-primary">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Tasks
        </Link>
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'running':
        return <Activity className="h-5 w-5 text-blue-500 animate-spin" />
      case 'cancelled':
        return <X className="h-5 w-5 text-gray-500" />
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return 'badge-success'
      case 'failed':
        return 'badge-error'
      case 'running':
        return 'badge-info'
      case 'cancelled':
        return 'badge-secondary'
      default:
        return 'badge-warning'
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'badge-error'
      case 'high':
        return 'badge-warning'
      case 'normal':
        return 'badge-info'
      default:
        return 'badge-secondary'
    }
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${(ms / 60000).toFixed(2)}m`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/tasks" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-lg ${
              task.status === 'completed' ? 'bg-green-100' : 
              task.status === 'failed' ? 'bg-red-100' : 
              task.status === 'running' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              {getStatusIcon(task.status)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{task.title}</h1>
              <p className="text-sm text-gray-500">Task #{task.id}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`badge ${getStatusBadge(task.status)}`}>
            {task.status}
          </span>
          <span className={`badge ${getPriorityBadge(task.priority)}`}>
            {task.priority}
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
              {task.description || 'No description provided for this task.'}
            </p>
          </div>

          {/* Input Data */}
          {task.input_data && Object.keys(task.input_data).length > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Input Data</h2>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(task.input_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Output Data */}
          {task.output_data && Object.keys(task.output_data).length > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Output Data</h2>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(task.output_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Error Message */}
          {task.error_message && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Error Details</h2>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-medium text-red-800">Task Failed</h3>
                    <p className="text-sm text-red-700 mt-1">{task.error_message}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {task.tags.map((tag, index) => (
                  <span key={index} className="badge badge-secondary">
                    <Tag className="h-3 w-3 mr-1" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Task Information */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Task Information</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Status:</span>
                <div className="flex items-center space-x-1">
                  {getStatusIcon(task.status)}
                  <span className="text-sm text-gray-900">{task.status}</span>
                </div>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Priority:</span>
                <span className={`badge ${getPriorityBadge(task.priority)}`}>
                  {task.priority}
                </span>
              </div>
              
              {task.category && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Category:</span>
                  <span className="text-sm text-gray-900">{task.category}</span>
                </div>
              )}
              
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-500">Created:</span>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-900">
                    {new Date(task.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              
              {task.started_at && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Started:</span>
                  <span className="text-sm text-gray-900">
                    {new Date(task.started_at).toLocaleString()}
                  </span>
                </div>
              )}
              
              {task.completed_at && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Completed:</span>
                  <span className="text-sm text-gray-900">
                    {new Date(task.completed_at).toLocaleString()}
                  </span>
                </div>
              )}
              
              {task.execution_time_ms && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Duration:</span>
                  <span className="text-sm text-gray-900">
                    {formatDuration(task.execution_time_ms)}
                  </span>
                </div>
              )}
              
              {task.user_id && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">User:</span>
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-900">{task.user_id}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Retry Information */}
          {task.retry_count > 0 || task.max_retries > 0 && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Retry Information</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Retry Count:</span>
                  <span className="text-sm text-gray-900">{task.retry_count}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-500">Max Retries:</span>
                  <span className="text-sm text-gray-900">{task.max_retries}</span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(task.retry_count / task.max_retries) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {/* Assigned Server */}
          {task.assigned_server_id && (
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Assigned Server</h2>
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Server className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Server #{task.assigned_server_id}</p>
                  <Link 
                    to={`/servers/${task.assigned_server_id}`}
                    className="text-xs text-primary-600 hover:text-primary-500"
                  >
                    View Server Details
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Actions</h2>
            <div className="space-y-3">
              {task.status === 'pending' && (
                <button className="btn-primary w-full">
                  <Play className="h-4 w-4 mr-2" />
                  Execute Task
                </button>
              )}
              
              {(task.status === 'pending' || task.status === 'running') && (
                <button className="btn-outline w-full text-red-600 hover:text-red-700">
                  <X className="h-4 w-4 mr-2" />
                  Cancel Task
                </button>
              )}
              
              {task.status === 'failed' && task.retry_count < task.max_retries && (
                <button className="btn-outline w-full">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry Task
                </button>
              )}
              
              <button className="btn-outline w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Status
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}