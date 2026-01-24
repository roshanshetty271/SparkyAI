'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, Mic, MicOff, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  isListening?: boolean
  onStartListening?: () => void
  onStopListening?: () => void
  transcript?: string
  // NEW: Enhanced status props
  isVoiceReady?: boolean
  isPermissionGranted?: boolean | null
}

export default function ChatInput({
  onSend,
  disabled = false,
  isListening = false,
  onStartListening,
  onStopListening,
  transcript = '',
  isVoiceReady = true,
  isPermissionGranted = null
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Sync transcript to message
  useEffect(() => {
    if (transcript) {
      setMessage(transcript)
    }
  }, [transcript])

  // Auto-send when listening stops if we have a transcript
  useEffect(() => {
    if (!isListening && transcript.trim()) {
      onSend(transcript.trim())
      setMessage('')
    }
  }, [isListening, transcript, onSend])

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

  const toggleListening = () => {
    if (isListening) {
      onStopListening?.()
    } else {
      onStartListening?.()
    }
  }

  // Determine mic button state
  const getMicButtonState = () => {
    if (isListening) return 'listening'
    if (isPermissionGranted === false) return 'denied'
    if (!isVoiceReady) return 'loading'
    return 'ready'
  }

  const micState = getMicButtonState()

  // Get mic button tooltip
  const getMicTooltip = () => {
    switch (micState) {
      case 'listening': return 'Stop listening'
      case 'denied': return 'Microphone blocked - click lock icon in address bar to allow'
      case 'loading': return 'Voice initializing...'
      default: return 'Start voice input'
    }
  }

  return (
    <div className="p-4 border-t border-white/5 bg-black/20 backdrop-blur-md">
      <div className="flex items-end gap-2">
        <div className="flex-1 relative group">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? "Listening..." : "Ask me anything..."}
            disabled={disabled || isListening}
            rows={1}
            className={cn(
              "w-full px-4 py-3 bg-white/5 border border-white/10 rounded-2xl",
              "text-sm text-white placeholder-white/40 resize-none",
              "focus:outline-none focus:ring-1 focus:ring-accent-cyan/50 focus:bg-white/10",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-200",
              isListening && "pl-10 ring-1 ring-red-500/50 bg-red-500/5"
            )}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />

          {/* Listening Indicator Overlay */}
          {isListening && (
            <div className="absolute left-3 top-3 animate-pulse">
              <div className="w-2 h-2 rounded-full bg-red-500" />
            </div>
          )}
        </div>

        {/* Voice Button */}
        {onStartListening && (
          <div className="relative group">
            <button
              onClick={toggleListening}
              disabled={micState === 'loading'}
              className={cn(
                "p-3 rounded-xl transition-all duration-200 shadow-lg border border-white/5 relative z-10",
                // Listening state
                micState === 'listening' && "bg-red-500/20 text-red-400 hover:bg-red-500/30 border-red-500/20",
                // Permission denied state
                micState === 'denied' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20 cursor-help",
                // Loading state
                micState === 'loading' && "bg-white/5 text-white/30 cursor-wait",
                // Ready state
                micState === 'ready' && "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
              )}
              aria-label={getMicTooltip()}
              title={getMicTooltip()}
            >
              {micState === 'listening' ? (
                <MicOff className="w-5 h-5" />
              ) : micState === 'denied' ? (
                <AlertCircle className="w-5 h-5" />
              ) : micState === 'loading' ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Mic className="w-5 h-5" />
              )}
            </button>

            {/* Ping animation when listening */}
            {isListening && (
              <span className="absolute inset-0 rounded-xl bg-red-500/20 animate-ping z-0" />
            )}

            {/* Tooltip for denied state */}
            {micState === 'denied' && (
              <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 border border-yellow-500/30 
                rounded-lg text-xs text-yellow-200 whitespace-nowrap opacity-0 group-hover:opacity-100 
                transition-opacity pointer-events-none z-20 max-w-xs">
                <div className="font-medium mb-1">Microphone blocked</div>
                <div className="text-yellow-200/70">
                  Click the lock icon in your address bar to allow microphone access
                </div>
              </div>
            )}
          </div>
        )}

        {/* Send Button */}
        <button
          onClick={handleSubmit}
          disabled={!message.trim() || disabled || isListening}
          className={cn(
            "p-3 rounded-xl transition-all duration-200 shadow-lg",
            message.trim() && !disabled && !isListening
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
        {isVoiceReady && isPermissionGranted !== false && (
          <span className="ml-2">• Click mic for voice input</span>
        )}
      </p>
    </div>
  )
}
