'use client'

import { memo } from 'react'
import { cn, formatTime } from '@/lib/utils'
import type { Message } from '@/types/agent'

interface MessageListProps {
  messages: Message[]
  streamingResponse: string
  isTyping: boolean
}

function MessageList({ messages, streamingResponse, isTyping }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Streaming response */}
      {streamingResponse && (
        <div className="message message-assistant">
          <p className="text-sm whitespace-pre-wrap">{streamingResponse}</p>
          <span className="inline-block w-1 h-4 ml-0.5 bg-accent-cyan animate-pulse" />
        </div>
      )}

      {/* Typing indicator (before streaming starts) */}
      {isTyping && !streamingResponse && (
        <div className="message message-assistant">
          <div className="typing-indicator">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        </div>
      )}
    </div>
  )
}

export default memo(MessageList)

const MessageBubble = memo(function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn(
      "flex",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "message",
        isUser ? "message-user" : "message-assistant"
      )}>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <span className={cn(
          "text-[10px] mt-1 block",
          isUser ? "text-blue-200" : "text-zinc-500"
        )}>
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
})
