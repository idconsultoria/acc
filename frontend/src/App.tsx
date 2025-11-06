import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ChatView from './views/ChatView'
import HistoryView from './views/HistoryView'
import SourcesView from './views/SourcesView'
import ProfileView from './views/ProfileView'
import SettingsView from './views/SettingsView'
import AdminAgentInstructionView from './views/admin/AdminAgentInstructionView'
import AdminArtifactsView from './views/admin/AdminArtifactsView'
import AdminFeedbackView from './views/admin/AdminFeedbackView'
import AdminSettingsView from './views/admin/AdminSettingsView'
import AdminHelpView from './views/admin/AdminHelpView'
import { BackendStatusNotification } from './components/shared/BackendStatusNotification'

function App() {
  return (
    <BrowserRouter>
      <BackendStatusNotification />
      <Routes>
        <Route path="/" element={<ChatView />} />
        <Route path="/chat" element={<ChatView />} />
        <Route path="/history" element={<HistoryView />} />
        <Route path="/sources" element={<SourcesView />} />
        <Route path="/profile" element={<ProfileView />} />
        <Route path="/settings" element={<SettingsView />} />
        <Route path="/admin" element={<Navigate to="/admin/instruction" replace />} />
        <Route path="/admin/instruction" element={<AdminAgentInstructionView />} />
        <Route path="/admin/artifacts" element={<AdminArtifactsView />} />
        <Route path="/admin/feedbacks" element={<AdminFeedbackView />} />
        <Route path="/admin/settings" element={<AdminSettingsView />} />
        <Route path="/admin/help" element={<AdminHelpView />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

