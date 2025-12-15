import axios from 'axios'

const API_BASE_URL = '/api/v1'

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      // Redirect to login if needed
    }
    return Promise.reject(error)
  }
)

// Types
export interface MCPServer {
  id: number
  name: string
  description?: string
  url: string
  repository_url?: string
  package_manager?: string
  package_name?: string
  version?: string
  author?: string
  license?: string
  capabilities: string[]
  categories: string[]
  metadata: Record<string, any>
  is_active: boolean
  is_verified: boolean
  health_status: string
  last_health_check?: string
  response_time_ms?: number
  discovered_from?: string
  discovery_date: string
  last_updated: string
  usage_count: number
  success_rate: number
}

export interface Task {
  id: number
  title: string
  description?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  input_data: Record<string, any>
  output_data?: Record<string, any>
  error_message?: string
  assigned_server_id?: number
  execution_time_ms?: number
  retry_count: number
  max_retries: number
  created_at: string
  started_at?: string
  completed_at?: string
  updated_at: string
  user_id?: string
  session_id?: string
  category?: string
  tags: string[]
}

export interface ServerStats {
  total_servers: number
  active_servers: number
  healthy_servers: number
  categories: Record<string, number>
  package_managers: Record<string, number>
  discovery_sources: Record<string, number>
}

export interface TaskStats {
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  average_execution_time_ms: number
  success_rate: number
  tasks_by_category: Record<string, number>
  tasks_by_priority: Record<string, number>
}

// API functions
export const serverApi = {
  getServers: (params?: {
    skip?: number
    limit?: number
    category?: string
    package_manager?: string
    is_active?: boolean
    is_verified?: boolean
    search?: string
  }) => api.get<MCPServer[]>('/servers', { params }),
  
  getServer: (id: number) => api.get<MCPServer>(`/servers/${id}`),
  
  createServer: (data: Partial<MCPServer>) => api.post<MCPServer>('/servers', data),
  
  updateServer: (id: number, data: Partial<MCPServer>) => 
    api.put<MCPServer>(`/servers/${id}`, data),
  
  deleteServer: (id: number) => api.delete(`/servers/${id}`),
  
  getServerStats: () => api.get<ServerStats>('/servers/stats/overview'),
  
  getServerHealth: (id: number) => api.get(`/servers/${id}/health`),
  
  verifyServer: (id: number) => api.post(`/servers/${id}/verify`),
  
  checkServerHealth: (id: number) => api.post(`/servers/${id}/health-check`),
  
  getCategories: () => api.get<{ categories: string[] }>('/servers/categories/list'),
  
  getPackageManagers: () => api.get<{ package_managers: string[] }>('/servers/package-managers/list'),
}

export const taskApi = {
  getTasks: (params?: {
    skip?: number
    limit?: number
    status?: string
    priority?: string
    category?: string
    user_id?: string
    session_id?: string
  }) => api.get<Task[]>('/tasks', { params }),
  
  getTask: (id: number) => api.get<Task>(`/tasks/${id}`),
  
  createTask: (data: Partial<Task>) => api.post<Task>('/tasks', data),
  
  updateTask: (id: number, data: Partial<Task>) => 
    api.put<Task>(`/tasks/${id}`, data),
  
  deleteTask: (id: number) => api.delete(`/tasks/${id}`),
  
  executeTask: (id: number, data?: { server_id?: number; force_retry?: boolean }) => 
    api.post(`/tasks/${id}/execute`, data),
  
  cancelTask: (id: number) => api.post(`/tasks/${id}/cancel`),
  
  getTaskStats: () => api.get<TaskStats>('/tasks/stats/overview'),
  
  getTaskQueue: () => api.get('/tasks/queue/status'),
  
  getTaskCategories: () => api.get<{ categories: string[] }>('/tasks/categories/list'),
}

export const discoveryApi = {
  startDiscovery: () => api.post('/discovery/start'),
  
  stopDiscovery: () => api.post('/discovery/stop'),
  
  runDiscoveryOnce: () => api.post('/discovery/run-once'),
  
  discoverFromGitHub: () => api.post('/discovery/discover-github'),
  
  discoverFromNpm: () => api.post('/discovery/discover-npm'),
  
  discoverFromPyPI: () => api.post('/discovery/discover-pypi'),
  
  manualDiscovery: (data: { url: string; name?: string }) => 
    api.post('/discovery/manual', data),
  
  getDiscoveryStatus: () => api.get('/discovery/status'),
  
  getDiscoverySources: () => api.get('/discovery/sources'),
  
  getDiscoveryHistory: (limit?: number) => 
    api.get('/discovery/history', { params: { limit } }),
  
  clearUnverifiedServers: () => api.delete('/discovery/clear-unverified'),
  
  verifyAllServers: () => api.post('/discovery/verify-all'),
  
  getDiscoveryConfig: () => api.get('/discovery/config'),
}

export default api