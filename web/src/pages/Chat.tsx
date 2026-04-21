import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, MessageSquare } from 'lucide-react'
import { useChatStore } from '../store/chatStore'
import { api } from '../services/api'

const QUICK_REPLIES = [
  'What are common NSAID contraindications?',
  'Explain Stage 3 CKD risks',
  'What is HITL validation?',
  'How does openFDA work?',
]

export default function Chat() {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const messages = useChatStore((s) => s.messages)
  const isTyping = useChatStore((s) => s.isTyping)
  const sessionId = useChatStore((s) => s.sessionId)
  const addMessage = useChatStore((s) => s.addMessage)
  const setTyping = useChatStore((s) => s.setTyping)

  const canSend = input.trim().length > 0 && !isTyping

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    setInput('')
    addMessage('user', trimmed)
    setTyping(true)

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const res = await api.chat(trimmed, sessionId, history)
      addMessage('assistant', res.reply)
    } catch (err: any) {
      addMessage(
        'assistant',
        `I'm sorry, I couldn't process your request. Error: ${err.message}\n\nPlease make sure the HealthMind server is running at the configured URL.`,
      )
    } finally {
      setTyping(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) send(input)
    }
  }

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <h1 className="page-title" style={{ fontSize: 24 }}>Ask AI</h1>
          <p className="page-subtitle" style={{ fontSize: 13 }}>
            Chat with HealthMind about medications, interactions, and safety
          </p>
        </motion.div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && !isTyping && (
          <div className="chat-empty">
            <div className="chat-empty-icon">
              <MessageSquare size={28} color="var(--accent)" />
            </div>
            <div style={{ fontSize: 15, color: 'var(--text-secondary)' }}>
              Ask me anything about medications, drug interactions, or clinical safety guidelines.
            </div>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className={`msg-bubble ${msg.role === 'user' ? 'msg-user' : 'msg-assistant'}`}
            >
              {msg.role === 'assistant' && <div className="msg-assistant-label">HealthMind AI</div>}
              {msg.content}
              <div className="msg-time">
                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing Indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="typing-indicator"
            >
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>

      {/* Quick Replies */}
      {(messages.length === 0 || (!isTyping && messages.length > 0)) && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.3 }}
          className="quick-replies"
        >
          {QUICK_REPLIES.map((q) => (
            <button key={q} className="quick-reply-btn" onClick={() => send(q)}>
              {q}
            </button>
          ))}
        </motion.div>
      )}

      {/* Input Bar */}
      <div className="chat-input-bar">
        <textarea
          ref={inputRef}
          className="chat-input"
          rows={1}
          placeholder="Type your question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{
            borderColor: input ? 'var(--accent)' : undefined,
            height: 48,
          }}
        />
        <button
          className={`chat-send-btn ${canSend ? 'active' : 'inactive'}`}
          onClick={() => canSend && send(input)}
          disabled={!canSend}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
