'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Minimize2, Maximize2, Volume2, VolumeX } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAgentStore } from '@/stores/agentStore'
import { useVoice } from '@/hooks/useVoice'
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
    const [soundEnabled, setSoundEnabled] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const lastSpokenMessageId = useRef<string | null>(null)

    const { messages, isTyping, streamingResponse } = useAgentStore()
    const lastSpokenIndexRef = useRef(0)
    const sentencesQueueRef = useRef<string[]>([])

    // Voice Hook (with new enhanced API)
    const {
        isListening,
        transcript,
        startListening,
        stopListening,
        speak,
        stopSpeaking,
        error: voiceError,
        // NEW: Enhanced API
        initialize: initializeVoice,
        isInitialized: isVoiceInitialized,
        isReady: isVoiceReady,
        isPermissionGranted
    } = useVoice()

    // Initialize voice on first user interaction
    // This unlocks audio autoplay restrictions
    const handleFirstInteraction = () => {
        if (!isVoiceInitialized) {
            console.log('🎯 First interaction detected - initializing voice')
            initializeVoice()
        }
    }

    // Stream-speak sentences as they appear
    useEffect(() => {
        if (!soundEnabled || !streamingResponse) {
            if (!streamingResponse) {
                lastSpokenIndexRef.current = 0
                sentencesQueueRef.current = []
            }
            return
        }

        // Look for sentences in the streaming response
        const text = streamingResponse
        const remainingText = text.slice(lastSpokenIndexRef.current)

        // Match sentences ending with . ! ? or newline
        const sentenceRegex = /[^.!?\n]+[.!?\n]+/g
        let match

        while ((match = sentenceRegex.exec(remainingText)) !== null) {
            const sentence = match[0].trim()
            if (sentence) {
                console.log('🤖 Buffer: found sentence:', sentence)
                speak(sentence, true) // QUEUE the speech during streaming
            }
            lastSpokenIndexRef.current += match.index + match[0].length
        }
    }, [streamingResponse, soundEnabled, speak])

    // Auto-speak completed messages (only if we didn't speak them during streaming)
    useEffect(() => {
        if (!soundEnabled || messages.length === 0) {
            if (!soundEnabled) {
                lastSpokenMessageId.current = null
            }
            return
        }

        const lastMessage = messages[messages.length - 1]

        // Only speak if it's an assistant message and we haven't spoken it yet
        // If it was already mostly spoken during streaming, we skip the bulk but maybe speak any left-over bit
        if (lastMessage.role === 'assistant' && !isTyping && lastMessage.id !== lastSpokenMessageId.current) {
            // Check if we missed any tail end sentence that didn't have punctuation
            const spokenLength = lastSpokenIndexRef.current
            if (spokenLength < lastMessage.content.length) {
                const tail = lastMessage.content.slice(spokenLength).trim()
                if (tail) {
                    console.log('🔊 Speaking tail end:', tail)
                    speak(tail)
                }
            }

            lastSpokenMessageId.current = lastMessage.id || lastMessage.content
        }
    }, [messages, isTyping, soundEnabled, speak])

    const handleSend = (text: string) => {
        if (!text.trim()) return

        // CRITICAL: Explicitly stop listening when sending
        if (isListening) {
            console.log('🎤 Force-stopping mic for outbound message')
            stopListening()
        }

        // Initialize voice on first message send
        handleFirstInteraction()

        // Enable sound automatically if user typed something (intent to interact)
        if (!soundEnabled) setSoundEnabled(true)

        sendMessage(text)
    }

    // Handle suggestion clicks (also triggers initialization)
    const handleSuggestionClick = (suggestion: string) => {
        if (isListening) {
            console.log('🎤 Force-stopping mic for suggestion click')
            stopListening()
        }
        handleFirstInteraction()
        setSoundEnabled(true) // Enable sound for suggestions too
        handleSend(suggestion)
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
                    {/* Sound Toggle - also initializes voice */}
                    <button
                        onClick={() => {
                            handleFirstInteraction() // Initialize on toggle
                            const newState = !soundEnabled
                            setSoundEnabled(newState)
                            if (newState === false) stopSpeaking()
                        }}
                        className={cn(
                            "p-2 rounded-lg transition-colors",
                            soundEnabled ? "bg-accent-blue/10 text-accent-cyan" : "hover:bg-white/10 text-white/60 hover:text-white"
                        )}
                        aria-label={soundEnabled ? 'Mute' : 'Enable sound'}
                        title={soundEnabled ? 'Mute Text-to-Speech' : 'Enable Text-to-Speech'}
                    >
                        {soundEnabled ? (
                            <Volume2 className="w-4 h-4" />
                        ) : (
                            <VolumeX className="w-4 h-4" />
                        )}
                    </button>
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
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
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

                                {/* Quick suggestions - clicking initializes voice */}
                                <div className="mt-6 flex flex-wrap justify-center gap-2">
                                    {[
                                        'What are your skills?',
                                        'Tell me about your experience',
                                        'What projects have you built?',
                                    ].map((suggestion) => (
                                        <button
                                            key={suggestion}
                                            onClick={() => handleSuggestionClick(suggestion)}
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

                    {/* Error banner - now with more specific voice error info */}
                    {(error || voiceError) && (
                        <div className="px-4 py-2 bg-red-500/10 border-t border-red-500/20">
                            <p className="text-red-400 text-sm">{error || voiceError}</p>
                            {/* Show permission status if mic permission was denied */}
                            {isPermissionGranted === false && (
                                <p className="text-red-300/70 text-xs mt-1">
                                    Tip: Click the lock icon in your address bar → Site settings → Allow microphone
                                </p>
                            )}
                        </div>
                    )}

                    {/* Input */}
                    <ChatInput
                        onSend={handleSend}
                        disabled={!isConnected || isTyping}
                        isListening={isListening}
                        onStartListening={() => {
                            handleFirstInteraction() // Initialize on mic click
                            // Also enable sound if they are using voice
                            if (!soundEnabled) setSoundEnabled(true)
                            startListening()
                        }}
                        onStopListening={stopListening}
                        transcript={transcript}
                        isVoiceReady={isVoiceReady}
                        isPermissionGranted={isPermissionGranted}
                    />
                </>
            )}
        </div>
    )
}
