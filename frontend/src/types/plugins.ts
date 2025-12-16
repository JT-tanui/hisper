export type PluginCapability = {
  kind: string
  description?: string
  resources?: Record<string, unknown>
}

export type PluginPanel = {
  id: string
  title: string
  route: string
  description?: string
  iframeUrl?: string
  permissions?: string[]
}

export type PluginManifest = {
  identifier: string
  name: string
  version: string
  description?: string
  plugin_type: string
  capabilities: PluginCapability[]
  frontend?: {
    panels?: PluginPanel[]
    navigationLabel?: string
  }
}
