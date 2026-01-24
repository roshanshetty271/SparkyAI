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
    <div className="p-4 border-t border-white/5 bg-black/20 backdrop-blur-md">
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
              "w-full px-4 py-3 bg-white/5 border border-white/10 rounded-2xl",
              "text-sm text-white placeholder-white/40 resize-none",
              "focus:outline-none focus:ring-1 focus:ring-accent-cyan/50 focus:bg-white/10",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-200"
            )}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!message.trim() || disabled}
          className={cn(
            "p-3 rounded-xl transition-all duration-200 shadow-lg",
            message.trim() && !disabled
              ? "bg-gradient-to-br from-accent-cyan to-accent-blue text-white hover:scale-105 active:scale-95"
              : "bg-white/5 text-white/20 cursor-not-allowed"
          )}
          aria-label="Send message"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      <p className="text-[10px] text-white/30 mt-2 text-center font-medium">
        Press <kbd className="font-mono bg-white/10 px-1 rounded text-white/50">Enter</kbd> to send
      </p>
    </div>
  )
}
