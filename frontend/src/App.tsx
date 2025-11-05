import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ChatView from './views/ChatView'
import HistoryView from './views/HistoryView'
import SourcesView from './views/SourcesView'
import ProfileView from './views/ProfileView'
import AdminAgentInstructionView from './views/admin/AdminAgentInstructionView'
import AdminArtifactsView from './views/admin/AdminArtifactsView'
import AdminFeedbackView from './views/admin/AdminFeedbackView'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatView />} />
        <Route path="/chat" element={<ChatView />} />
        <Route path="/history" element={<HistoryView />} />
        <Route path="/sources" element={<SourcesView />} />
        <Route path="/profile" element={<ProfileView />} />
        <Route path="/admin" element={<Navigate to="/admin/instruction" replace />} />
        <Route path="/admin/instruction" element={<AdminAgentInstructionView />} />
        <Route path="/admin/artifacts" element={<AdminArtifactsView />} />
        <Route path="/admin/feedbacks" element={<AdminFeedbackView />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

