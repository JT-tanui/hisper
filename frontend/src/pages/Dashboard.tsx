import { useQuery } from '@tanstack/react-query'
import { 
  Server, 
  CheckSquare, 
  Activity, 
  Search,
  MessageSquare,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle,
  Zap,
  Bot
} from 'lucide-react'
import { serverApi, taskApi } from '../services/api'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { data: serverStats, isLoading: serverStatsLoading } = useQuery({
    queryKey: ['server-stats'],
    queryFn: () => serverApi.getServerStats().then(res => res.data),
  })

  const { data: taskStats, isLoading: taskStatsLoading } = useQuery({
    queryKey: ['task-stats'],
    queryFn: () => taskApi.getTaskStats().then(res => res.data),
  })

  const { data: recentServers } = useQuery({
    queryKey: ['recent-servers'],
    queryFn: () => serverApi.getServers({ limit: 5 }).then(res => res.data),
  })

  const { data: recentTasks } = useQuery({
    queryKey: ['recent-tasks'],
    queryFn: () => taskApi.getTasks({ limit: 5 }).then(res => res.data),
  })

  const stats = [
    {
      name: 'Total Servers',
      value: serverStats?.total_servers || 0,
      icon: Server,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      change: '+12%',
      changeType: 'positive',
    },
    {
      name: 'Active Servers',
      value: serverStats?.active_servers || 0,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      change: '+5%',
      changeType: 'positive',
    },
    {
      name: 'Total Tasks',
      value: taskStats?.total_tasks || 0,
      icon: CheckSquare,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      change: '+23%',
      changeType: 'positive',
    },
    {
      name: 'Success Rate',
      value: `${taskStats?.success_rate?.toFixed(1) || 0}%`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
      change: '+2.1%',
      changeType: 'positive',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your MCP server discovery and task management system
        </p>
      </div>

      {/* AI Chat Feature Highlight */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 text-white mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="bg-white bg-opacity-20 rounded-lg p-3">
              <Bot className="h-8 w-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">AI-Powered MCP Assistant</h2>
              <p className="text-blue-100 mt-1">
                Interact with AI to discover and use MCP servers through natural language
              </p>
            </div>
          </div>
          <Link
            to="/chat"
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors flex items-center space-x-2"
          >
            <MessageSquare className="h-5 w-5" />
            <span>Start Chatting</span>
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Zap className="h-5 w-5" />
              <span className="font-semibold">Natural Language</span>
            </div>
            <p className="text-sm text-blue-100">
              Just describe what you need - no complex commands required
            </p>
          </div>
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Server className="h-5 w-5" />
              <span className="font-semibold">Auto Server Selection</span>
            </div>
            <p className="text-sm text-blue-100">
              AI automatically finds and connects to the right MCP servers
            </p>
          </div>
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="h-5 w-5" />
              <span className="font-semibold">Real-time Execution</span>
            </div>
            <p className="text-sm text-blue-100">
              Watch as AI executes tools and completes tasks in real-time
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-gray-900">
                    {serverStatsLoading || taskStatsLoading ? (
                      <div className="h-8 w-16 bg-gray-200 rounded animate-pulse" />
                    ) : (
                      stat.value
                    )}
                  </p>
                  <p className={`ml-2 text-sm font-medium ${
                    stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.change}
                  </p>
                </div>
                <p className="text-sm text-gray-500">{stat.name}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            to="/discovery"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Search className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">Start Discovery</p>
              <p className="text-sm text-gray-500">Find new MCP servers</p>
            </div>
          </Link>
          
          <Link
            to="/tasks"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <CheckSquare className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">Create Task</p>
              <p className="text-sm text-gray-500">Execute a new task</p>
            </div>
          </Link>
          
          <Link
            to="/servers"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Server className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">Manage Servers</p>
              <p className="text-sm text-gray-500">View and configure</p>
            </div>
          </Link>
          
          <div className="flex items-center p-4 border border-gray-200 rounded-lg">
            <Activity className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">System Health</p>
              <p className="text-sm text-gray-500">All systems operational</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Servers */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Recent Servers</h2>
            <Link to="/servers" className="text-sm text-primary-600 hover:text-primary-500">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {recentServers?.slice(0, 5).map((server) => (
              <div key={server.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${
                    server.health_status === 'healthy' ? 'bg-green-100' : 
                    server.health_status === 'unhealthy' ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    <Server className={`h-4 w-4 ${
                      server.health_status === 'healthy' ? 'text-green-600' : 
                      server.health_status === 'unhealthy' ? 'text-red-600' : 'text-gray-600'
                    }`} />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{server.name}</p>
                    <p className="text-xs text-gray-500">{server.package_manager || 'Unknown'}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {server.is_verified && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                  <span className={`badge ${
                    server.health_status === 'healthy' ? 'badge-success' : 
                    server.health_status === 'unhealthy' ? 'badge-error' : 'badge-secondary'
                  }`}>
                    {server.health_status}
                  </span>
                </div>
              </div>
            ))}
            {(!recentServers || recentServers.length === 0) && (
              <div className="text-center py-6 text-gray-500">
                <Server className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>No servers discovered yet</p>
                <Link to="/discovery" className="text-primary-600 hover:text-primary-500 text-sm">
                  Start discovery
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Recent Tasks</h2>
            <Link to="/tasks" className="text-sm text-primary-600 hover:text-primary-500">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {recentTasks?.slice(0, 5).map((task) => (
              <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${
                    task.status === 'completed' ? 'bg-green-100' : 
                    task.status === 'failed' ? 'bg-red-100' : 
                    task.status === 'running' ? 'bg-blue-100' : 'bg-gray-100'
                  }`}>
                    {task.status === 'completed' ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : task.status === 'failed' ? (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    ) : task.status === 'running' ? (
                      <Activity className="h-4 w-4 text-blue-600" />
                    ) : (
                      <Clock className="h-4 w-4 text-gray-600" />
                    )}
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{task.title}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(task.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`badge ${
                    task.status === 'completed' ? 'badge-success' : 
                    task.status === 'failed' ? 'badge-error' : 
                    task.status === 'running' ? 'badge-info' : 'badge-secondary'
                  }`}>
                    {task.status}
                  </span>
                  <span className={`badge ${
                    task.priority === 'urgent' ? 'badge-error' : 
                    task.priority === 'high' ? 'badge-warning' : 'badge-secondary'
                  }`}>
                    {task.priority}
                  </span>
                </div>
              </div>
            ))}
            {(!recentTasks || recentTasks.length === 0) && (
              <div className="text-center py-6 text-gray-500">
                <CheckSquare className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>No tasks created yet</p>
                <Link to="/tasks" className="text-primary-600 hover:text-primary-500 text-sm">
                  Create a task
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}