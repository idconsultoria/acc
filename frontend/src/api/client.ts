import axios from 'axios'

// URL da API no Google Cloud Run
// Em produção, usa a variável de ambiente VITE_API_BASE_URL
// Em desenvolvimento, usa localhost
const getApiBaseUrl = () => {
  // Se VITE_API_BASE_URL estiver definida, usa ela (prioridade)
  // Esta variável deve conter a URL completa do Cloud Run, ex: https://seu-servico-xxxxx.run.app
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
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
  timeout: 30000, // 30 segundos de timeout para dar tempo do cold start
})

export interface RagPhaseDefinition {
  id: string
  label: string
}

export interface RagPhaseUpdatePayload {
  phase: string
  [key: string]: unknown
}

export interface StreamHandlers {
  onPhaseStart?(payload: { phases: RagPhaseDefinition[] }): void
  onPhaseUpdate?(payload: RagPhaseUpdatePayload): void
  onPhaseComplete?(payload: RagPhaseUpdatePayload): void
  onToken?(payload: { value: string }): void
  onMessageComplete?(payload: Message): void
  onError?(error: Error): void
  onClose?(): void
}

export interface StreamController {
  close: () => void
  completed: Promise<void>
}

const streamConversationMessage = (
  conversationId: string,
  content: string,
  handlers: StreamHandlers
): StreamController => {
  const controller = new AbortController()
  const url = `${API_BASE_URL}/conversations/${conversationId}/messages/stream`
  let finished = false
  let resolveCompletion: (() => void) | null = null
  let rejectCompletion: ((reason?: unknown) => void) | null = null

  const completed = new Promise<void>((resolve, reject) => {
    resolveCompletion = resolve
    rejectCompletion = reject
  })

  const resolveOnce = () => {
    if (!finished && resolveCompletion) {
      finished = true
      resolveCompletion()
    }
  }

  const rejectOnce = (reason: unknown) => {
    if (!finished && rejectCompletion) {
      finished = true
      rejectCompletion(reason)
    }
  }

  const dispatchEvent = (eventName: string, payload: any) => {
    switch (eventName) {
      case 'phase:start':
        handlers.onPhaseStart?.(payload as { phases: RagPhaseDefinition[] })
        break
      case 'phase:update':
        handlers.onPhaseUpdate?.(payload as RagPhaseUpdatePayload)
        break
      case 'phase:complete':
        handlers.onPhaseComplete?.(payload as RagPhaseUpdatePayload)
        break
      case 'token':
        handlers.onToken?.(payload as { value: string })
        break
      case 'message:complete':
        handlers.onMessageComplete?.(payload as Message)
        resolveOnce()
        break
      case 'error': {
        const detail = payload?.detail
        const error = new Error(detail ? String(detail) : 'Erro no streaming de mensagens')
        handlers.onError?.(error)
        rejectOnce(error)
        break
      }
      default:
        break
    }
  }

  const processBuffer = (input: string, flush = false): string => {
    let buffer = input
    let boundary = buffer.indexOf('\n\n')

    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary).trim()
      buffer = buffer.slice(boundary + 2)

      if (rawEvent) {
        const lines = rawEvent.split('\n')
        let eventName = ''
        let dataBuffer = ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventName = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            dataBuffer += line.slice(5).trim()
          }
        }

        if (eventName) {
          let parsedPayload: any = {}
          if (dataBuffer) {
            try {
              parsedPayload = JSON.parse(dataBuffer)
            } catch (error) {
              const parsingError = new Error('Não foi possível interpretar dados de streaming')
              handlers.onError?.(parsingError)
              rejectOnce(parsingError)
              return ''
            }
          }
          dispatchEvent(eventName, parsedPayload)
        }
      }

      boundary = buffer.indexOf('\n\n')
    }

    if (flush && buffer.trim().length > 0) {
      const leftover = buffer.trim()
      buffer = ''
      const lines = leftover.split('\n')
      let eventName = ''
      let dataBuffer = ''
      for (const line of lines) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          dataBuffer += line.slice(5).trim()
        }
      }
      if (eventName) {
        let parsedPayload: any = {}
        if (dataBuffer) {
          try {
            parsedPayload = JSON.parse(dataBuffer)
          } catch (error) {
            const parsingError = new Error('Não foi possível interpretar dados de streaming')
            handlers.onError?.(parsingError)
            rejectOnce(parsingError)
            return ''
          }
        }
        dispatchEvent(eventName, parsedPayload)
      }
    }

    return buffer
  }

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ content }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const error = new Error(`Falha ao iniciar streaming (${response.status})`)
        handlers.onError?.(error)
        rejectOnce(error)
        return
      }

      if (!response.body) {
        const error = new Error('Resposta de streaming sem corpo legível')
        handlers.onError?.(error)
        rejectOnce(error)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        buffer = processBuffer(buffer)
      }

      processBuffer(buffer, true)
      resolveOnce()
    })
    .catch((error) => {
      if (controller.signal.aborted) {
        const abortError = new Error('Streaming cancelado pelo cliente')
        rejectOnce(abortError)
      } else {
        const finalError = error instanceof Error ? error : new Error(String(error))
        handlers.onError?.(finalError)
        rejectOnce(finalError)
      }
    })
    .finally(() => {
      handlers.onClose?.()
    })

  const close = () => {
    if (!controller.signal.aborted) {
      controller.abort()
    }
  }

  return {
    close,
    completed,
  }
}

// Função para verificar o status do backend (health check)
export const checkBackendStatus = async (): Promise<{ status: 'online' | 'waking' | 'offline', message?: string }> => {
  try {
    // Remove /api/v1 do baseURL para fazer o health check na raiz
    const baseUrl = API_BASE_URL.replace('/api/v1', '')
    const response = await axios.get(`${baseUrl}/health`, {
      timeout: 10000, // 10 segundos para health check
    })
    
    if (response.status === 200) {
      return { status: 'online' }
    }
    return { status: 'offline', message: 'Backend não respondeu corretamente' }
  } catch (error: any) {
    // Se o erro for de timeout ou conexão, o backend pode estar "dormindo"
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT' || error.message?.includes('timeout')) {
      return { status: 'waking', message: 'Backend está sendo acordado...' }
    }
    
    // Se for erro de conexão, o backend está offline
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      return { status: 'offline', message: 'Não foi possível conectar ao backend' }
    }
    
    // Outros erros podem indicar que o backend está acordando
    if (error.response?.status === 503 || error.response?.status === 502) {
      return { status: 'waking', message: 'Backend está sendo acordado...' }
    }
    
    return { status: 'offline', message: error.message || 'Erro desconhecido' }
  }
}

// Types baseados no OpenAPI
export interface Artifact {
  id: string
  title: string
  source_type: 'PDF' | 'TEXT'
  created_at: string
  description?: string
  tags?: string[]
  color?: string
  source_url?: string | null
  original_content?: string | null
}

export interface ArtifactChunkMetadata {
  section_title?: string | null
  section_level?: number | null
  content_type?: string | null
  position?: number | null
  token_count?: number | null
  breadcrumbs: string[]
}

export interface ArtifactChunk {
  id: string
  artifact_id: string
  content: string
  metadata?: ArtifactChunkMetadata | null
}

export type ArtifactContentResponse =
  | { source_type: 'TEXT'; content: string }
  | { source_type: 'PDF'; source_url?: string | null }

export interface Message {
  id: string
  conversation_id: string
  author: 'USER' | 'AGENT'
  content: string
  cited_sources: CitedSource[]
  created_at: string
}

export interface CitedSource {
  chunk_id: string
  artifact_id: string
  title: string
  chunk_content_preview: string
  section_title?: string | null
  section_level?: number | null
  content_type?: string | null
  breadcrumbs: string[]
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
  
  getArtifactContent: async (artifact_id: string): Promise<ArtifactContentResponse> => {
    const response = await apiClient.get(`/artifacts/${artifact_id}/content`)
    return response.data
  },

  getArtifactChunks: async (artifact_id: string): Promise<ArtifactChunk[]> => {
    const response = await apiClient.get(`/artifacts/${artifact_id}/chunks`)
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

    streamMessage: (conversation_id: string, content: string, handlers: StreamHandlers): StreamController => {
      return streamConversationMessage(conversation_id, content, handlers)
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

  getFeedbacksByMessageIds: async (message_ids: string[]): Promise<Record<string, PendingFeedback | null>> => {
    const response = await apiClient.post('/messages/feedbacks/batch', { message_ids })
    return response.data
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

