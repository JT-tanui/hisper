import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Servers from './pages/Servers'
import Tasks from './pages/Tasks'
import Discovery from './pages/Discovery'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import ServerDetail from './pages/ServerDetail'
import TaskDetail from './pages/TaskDetail'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/servers" element={<Servers />} />
        <Route path="/servers/:id" element={<ServerDetail />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/tasks/:id" element={<TaskDetail />} />
        <Route path="/discovery" element={<Discovery />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App