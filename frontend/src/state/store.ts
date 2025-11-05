import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  conversationId: string | null
  setConversationId: (id: string | null) => void
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      conversationId: null,
      setConversationId: (id) => set({ conversationId: id }),
    }),
    {
      name: 'ai-cultural-agent-storage',
      version: 1,
    }
  )
)

