import { Routes, Route } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Servers from './pages/Servers'
import Tasks from './pages/Tasks'
import Discovery from './pages/Discovery'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import ServerDetail from './pages/ServerDetail'
import TaskDetail from './pages/TaskDetail'
import { fetchPluginManifests } from './services/plugins'
import { PluginManifest, PluginPanel as PluginPanelType } from './types/plugins'
import { PluginPanel } from './components/PluginPanel'

function App() {
  const [pluginManifests, setPluginManifests] = useState<PluginManifest[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPluginManifests()
      .then(setPluginManifests)
      .catch((err) => setError(err.message))
  }, [])

  const pluginPanels: { panel: PluginPanelType; manifest: PluginManifest }[] = useMemo(() => {
    return pluginManifests.flatMap((manifest) =>
      (manifest.frontend?.panels || []).map((panel) => ({ panel, manifest }))
    )
  }, [pluginManifests])

  return (
    <Layout
      pluginPanels={pluginPanels.map(({ panel, manifest }) => ({
        title: panel.title,
        route: panel.route,
        navigationLabel: manifest.frontend?.navigationLabel || panel.title,
      }))}
    >
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/servers" element={<Servers />} />
        <Route path="/servers/:id" element={<ServerDetail />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/tasks/:id" element={<TaskDetail />} />
        <Route path="/discovery" element={<Discovery />} />
        <Route path="/settings" element={<Settings />} />
        {pluginPanels.map(({ panel, manifest }) => (
          <Route
            key={`${manifest.identifier}-${panel.id}`}
            path={panel.route}
            element={<PluginPanel panel={panel} pluginName={manifest.name} />}
          />
        ))}
      </Routes>
      {error && <p className="mt-4 text-sm text-red-600">Plugin loader error: {error}</p>}
    </Layout>
  )
}

export default App