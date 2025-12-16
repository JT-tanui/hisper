import { useMemo } from 'react'
import { Shield } from 'lucide-react'
import { PluginPanel as PluginPanelType } from '../types/plugins'

type PluginPanelProps = {
  panel: PluginPanelType
  pluginName: string
  allowedPermissions?: string[]
}

export function PluginPanel({ panel, pluginName, allowedPermissions = [] }: PluginPanelProps) {
  const hasPermission = useMemo(() => {
    if (!panel.permissions || panel.permissions.length === 0) return true
    return panel.permissions.some((permission) => allowedPermissions.includes(permission))
  }, [panel.permissions, allowedPermissions])

  if (!hasPermission) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        <div className="flex items-center space-x-2 text-amber-700">
          <Shield className="h-5 w-5" />
          <div>
            <p className="font-semibold">Permission required</p>
            <p className="text-sm text-amber-700/80">This panel requires additional permissions to view.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">{panel.title}</h2>
          <p className="text-sm text-gray-500">Provided by {pluginName}</p>
        </div>
      </div>
      {panel.description && <p className="text-gray-600">{panel.description}</p>}
      {panel.iframeUrl ? (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <iframe
            src={panel.iframeUrl}
            title={panel.title}
            className="h-[600px] w-full"
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-6 text-gray-500">
          <p>
            No remote UI specified for this panel. Use the plugin manifest to point at an iframe or render instructions
            here.
          </p>
        </div>
      )}
    </div>
  )
}
