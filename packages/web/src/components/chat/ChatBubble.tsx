'use client'

import { MessageCircle } from 'lucide-react'

interface ChatBubbleProps {
    onToggle: () => void
}

export function ChatBubble({ onToggle }: ChatBubbleProps) {
    return (
        <button
            onClick={onToggle}
            className="chat-bubble group"
            aria-label="Open chat"
        >
            <div className="relative w-14 h-14 bg-gradient-to-br from-accent-cyan to-accent-purple 
                    rounded-full flex items-center justify-center shadow-lg 
                    shadow-accent-purple/30 transition-transform group-hover:scale-105">
                <MessageCircle className="w-6 h-6 text-white" />

                {/* Pulse ring */}
                <span className="absolute inset-0 rounded-full bg-accent-cyan/20 animate-ping" />
            </div>
        </button>
    )
}
