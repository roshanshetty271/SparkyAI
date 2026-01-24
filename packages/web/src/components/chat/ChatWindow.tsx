'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Minimize2, Maximize2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAgentStore } from '@/stores/agentStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import MessageList from './MessageList'
import ChatInput from './ChatInput'

interface ChatWindowProps {
    onClose: () => void
    isConnected: boolean
    isConnecting: boolean
    error: string | null
    sendMessage: (text: string) => boolean
}

export function ChatWindow({
    onClose,
    isConnected,
    isConnecting,
    error,
    sendMessage
}: ChatWindowProps) {
    const [isMinimized, setIsMinimized] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const { messages, isTyping, streamingResponse } = useAgentStore()

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, streamingResponse])

    const handleSend = (text: string) => {
        if (!text.trim()) return
        sendMessage(text)
    }

    return (
        <div
            className={cn(
                "chat-window",
                isMinimized && "h-14"
            )}
        >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-dark-border bg-dark-bg/80 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-cyan to-accent-purple 
                        flex items-center justify-center">
                        <MessageCircle className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold">SparkyAI</h3>
                        <div className="flex items-center gap-1.5">
                            <span className={cn(
                                "w-1.5 h-1.5 rounded-full",
                                isConnected ? "bg-accent-green" : isConnecting ? "bg-yellow-400 animate-pulse" : "bg-zinc-500"
                            )} />
                            <span className="text-xs text-zinc-400">
                                {isConnected ? 'Online' : isConnecting ? 'Connecting...' : 'Offline'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsMinimized(!isMinimized)}
                        className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
                        aria-label={isMinimized ? 'Expand' : 'Minimize'}
                    >
                        {isMinimized ? (
                            <Maximize2 className="w-4 h-4 text-zinc-400" />
                        ) : (
                            <Minimize2 className="w-4 h-4 text-zinc-400" />
                        )}
                    </button>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
                        aria-label="Close chat"
                    >
                        <X className="w-4 h-4 text-zinc-400" />
                    </button>
                </div>
            </div>

            {/* Body */}
            {!isMinimized && (
                <>
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {/* Welcome message */}
                        {messages.length === 0 && !isTyping && (
                            <div className="text-center py-8">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br 
                              from-accent-cyan/20 to-accent-purple/20 
                              flex items-center justify-center">
                                    <MessageCircle className="w-8 h-8 text-accent-cyan" />
                                </div>
                                <h3 className="text-lg font-semibold mb-2">Hey there! 👋</h3>
                                <p className="text-zinc-400 text-sm max-w-xs mx-auto">
                                    I&apos;m SparkyAI. Ask me anything about Roshan&apos;s skills,
                                    experience, or projects!
                                </p>

                                {/* Quick suggestions */}
                                <div className="mt-6 flex flex-wrap justify-center gap-2">
                                    {[
                                        'What are your skills?',
                                        'Tell me about your experience',
                                        'What projects have you built?',
                                    ].map((suggestion) => (
                                        <button
                                            key={suggestion}
                                            onClick={() => handleSend(suggestion)}
                                            disabled={!isConnected}
                                            className="px-3 py-1.5 text-sm bg-dark-hover border border-dark-border 
                               rounded-full hover:border-accent-cyan/50 transition-colors
                               disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        <MessageList
                            messages={messages}
                            streamingResponse={streamingResponse}
                            isTyping={isTyping}
                        />

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Error banner */}
                    {error && (
                        <div className="px-4 py-2 bg-red-500/10 border-t border-red-500/20 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Input */}
                    <ChatInput
                        onSend={handleSend}
                        disabled={!isConnected || isTyping}
                    />
                </>
            )}
        </div>
    )
}
