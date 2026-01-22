'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [message])

  const handleSubmit = () => {
    if (!message.trim() || disabled) return
    onSend(message.trim())
    setMessage('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="p-4 border-t border-dark-border bg-dark-bg/80 backdrop-blur-sm">
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full px-4 py-3 bg-dark-card border border-dark-border rounded-xl",
              "text-sm text-white placeholder-zinc-500 resize-none",
              "focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 focus:border-accent-cyan/50",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all"
            )}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
        </div>
        
        <button
          onClick={handleSubmit}
          disabled={!message.trim() || disabled}
          className={cn(
            "p-3 rounded-xl transition-all",
            message.trim() && !disabled
              ? "bg-accent-blue hover:bg-accent-blue/90 text-white"
              : "bg-dark-card text-zinc-500 cursor-not-allowed"
          )}
          aria-label="Send message"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      
      <p className="text-[10px] text-zinc-500 mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
}
