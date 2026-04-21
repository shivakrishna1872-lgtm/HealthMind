import { create } from 'zustand'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface ChatState {
  messages: ChatMessage[]
  isTyping: boolean
  sessionId: string
  addMessage: (role: 'user' | 'assistant', content: string) => void
  setTyping: (typing: boolean) => void
  clearMessages: () => void
}

const genId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
const genSession = () => `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isTyping: false,
  sessionId: genSession(),

  addMessage: (role, content) =>
    set((s) => ({
      messages: [...s.messages, { id: genId(), role, content, timestamp: Date.now() }],
    })),

  setTyping: (typing) => set({ isTyping: typing }),

  clearMessages: () =>
    set({ messages: [], isTyping: false, sessionId: genSession() }),
}))
