import axios from 'axios'

// Detecta automaticamente a URL da API baseada no ambiente
// No Vercel, usa URL relativa para a mesma origem
// Localmente, usa localhost ou a variável de ambiente configurada
const getApiBaseUrl = () => {
  // Se VITE_API_BASE_URL estiver definida, usa ela (prioridade)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // Se estiver em produção (Vercel), usa URL relativa
  // Isso faz com que as requisições sejam feitas para a mesma origem
  if (import.meta.env.PROD) {
    return '/api/v1'
  }
  
  // Em desenvolvimento, usa localhost
  return 'http://localhost:8000/api/v1'
}

const API_BASE_URL = getApiBaseUrl()

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types baseados no OpenAPI
export interface Artifact {
  id: string
  title: string
  source_type: 'PDF' | 'TEXT'
  created_at: string
  description?: string
  tags?: string[]
  color?: string
}

export interface Message {
  id: string
  conversation_id: string
  author: 'USER' | 'AGENT'
  content: string
  cited_sources: CitedSource[]
  created_at: string
}

export interface CitedSource {
  artifact_id: string
  title: string
  chunk_content_preview: string
}

export interface PendingFeedback {
  id: string
  message_id: string
  feedback_text: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  created_at: string
  message_preview?: string
  feedback_type?: 'POSITIVE' | 'NEGATIVE' | null
}

export interface Learning {
  id: string
  content: string
  source_feedback_id: string
  created_at: string
}

export interface AgentInstruction {
  instruction: string
  updated_at: string
}

export interface Topic {
  id: string
  name: string
  conversation_count: number
}

export interface ConversationSummary {
  id: string
  title: string
  summary: string
  topic: string | null
  created_at: string
}

export interface ConversationTopic {
  topic: string | null
  is_processing: boolean
}

// API calls
export const api = {
  // Artifacts
  listArtifacts: async (): Promise<Artifact[]> => {
    const response = await apiClient.get('/artifacts')
    return response.data
  },
  
  createArtifact: async (formData: FormData): Promise<Artifact> => {
    const response = await apiClient.post('/artifacts', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  deleteArtifact: async (artifact_id: string): Promise<void> => {
    await apiClient.delete(`/artifacts/${artifact_id}`)
  },
  
  getArtifactContent: async (artifact_id: string): Promise<{ content: string }> => {
    const response = await apiClient.get(`/artifacts/${artifact_id}/content`)
    return response.data
  },

  updateArtifact: async (artifact_id: string, formData: FormData): Promise<Artifact> => {
    const response = await apiClient.patch(`/artifacts/${artifact_id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  updateArtifactTags: async (artifact_id: string, tags: string[]): Promise<Artifact> => {
    const response = await apiClient.patch(`/artifacts/${artifact_id}/tags`, { tags })
    return response.data
  },
  
  // Conversations
  createConversation: async (): Promise<{ conversation_id: string }> => {
    const response = await apiClient.post('/conversations')
    return response.data
  },
  
  getConversationMessages: async (conversation_id: string): Promise<Message[]> => {
    const response = await apiClient.get(`/conversations/${conversation_id}/messages`)
    return response.data
  },
  
  postMessage: async (conversation_id: string, content: string): Promise<Message> => {
    const response = await apiClient.post(`/conversations/${conversation_id}/messages`, { content })
    return response.data
  },
  
  // Feedbacks
  submitFeedback: async (message_id: string, feedback_text: string, feedback_type?: 'POSITIVE' | 'NEGATIVE' | null): Promise<PendingFeedback> => {
    const response = await apiClient.post(`/messages/${message_id}/feedback`, { feedback_text, feedback_type })
    return response.data
  },
  
  listPendingFeedbacks: async (): Promise<PendingFeedback[]> => {
    const response = await apiClient.get('/feedbacks/pending')
    return response.data
  },
  
  approveFeedback: async (feedback_id: string): Promise<{ feedback: PendingFeedback; learning: Learning }> => {
    const response = await apiClient.post(`/feedbacks/${feedback_id}/approve`)
    return response.data
  },
  
  rejectFeedback: async (feedback_id: string): Promise<PendingFeedback> => {
    const response = await apiClient.post(`/feedbacks/${feedback_id}/reject`)
    return response.data
  },

  listReviewedFeedbacks: async (): Promise<PendingFeedback[]> => {
    const response = await apiClient.get('/feedbacks/reviewed')
    return response.data
  },

  getConversationIdByMessageId: async (message_id: string): Promise<{ conversation_id: string }> => {
    const response = await apiClient.get(`/messages/${message_id}/conversation_id`)
    return response.data
  },

  getFeedbackByMessageId: async (message_id: string): Promise<PendingFeedback | null> => {
    const response = await apiClient.get(`/messages/${message_id}/feedback`)
    return response.data
  },

  updateFeedback: async (feedback_id: string, feedback_text: string, feedback_type?: 'POSITIVE' | 'NEGATIVE' | null): Promise<PendingFeedback> => {
    const response = await apiClient.put(`/feedbacks/${feedback_id}`, { feedback_text, feedback_type })
    return response.data
  },

  deleteFeedback: async (feedback_id: string): Promise<void> => {
    await apiClient.delete(`/feedbacks/${feedback_id}`)
  },
  
  // Learnings
  listLearnings: async (): Promise<Learning[]> => {
    const response = await apiClient.get('/learnings')
    return response.data
  },
  
  // Agent
  getAgentInstruction: async (): Promise<AgentInstruction> => {
    const response = await apiClient.get('/agent/instruction')
    return response.data
  },
  
  updateAgentInstruction: async (instruction: string): Promise<AgentInstruction> => {
    const response = await apiClient.put('/agent/instruction', { instruction })
    return response.data
  },
  
  // Topics
  listTopics: async (): Promise<Topic[]> => {
    const response = await apiClient.get('/topics')
    return response.data
  },
  
  getConversationsByTopic: async (topic_id?: string): Promise<ConversationSummary[]> => {
    const url = topic_id ? `/topics/${topic_id}/conversations` : '/topics/conversations'
    const response = await apiClient.get(url)
    return response.data
  },
  
  // Conversation Topic
  getConversationTopic: async (conversation_id: string): Promise<ConversationTopic> => {
    const response = await apiClient.get(`/conversations/${conversation_id}/topic`)
    return response.data
  },
  
  // Settings
  getSettings: async (): Promise<{ hasCustomApiKey: boolean }> => {
    const response = await apiClient.get('/settings')
    return response.data
  },
  
  saveGeminiApiKey: async (apiKey: string): Promise<void> => {
    await apiClient.put('/settings/gemini-api-key', { api_key: apiKey })
  },
}

