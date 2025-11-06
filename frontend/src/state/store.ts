import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  conversationId: string | null
  setConversationId: (id: string | null) => void
  backendStatusChecked: boolean
  setBackendStatusChecked: (checked: boolean) => void
  backendStatus: 'unknown' | 'online' | 'waking' | 'offline'
  setBackendStatus: (status: 'unknown' | 'online' | 'waking' | 'offline') => void
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      conversationId: null,
      setConversationId: (id) => set({ conversationId: id }),
      backendStatusChecked: false,
      setBackendStatusChecked: (checked) => set({ backendStatusChecked: checked }),
      backendStatus: 'unknown',
      setBackendStatus: (status) => set({ backendStatus: status }),
    }),
    {
      name: 'ai-cultural-agent-storage',
      version: 2, // Incrementa versão para resetar cache antigo
    }
  )
)

