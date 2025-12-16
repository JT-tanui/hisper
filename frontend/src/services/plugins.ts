import { PluginManifest } from '../types/plugins'

export async function fetchPluginManifests(): Promise<PluginManifest[]> {
  const response = await fetch('/api/v1/plugins/manifests')
  if (!response.ok) {
    throw new Error('Failed to load plugin manifests')
  }

  return response.json()
}
