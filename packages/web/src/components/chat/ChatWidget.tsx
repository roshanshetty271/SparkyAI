'use client'

import { useState, useEffect } from 'react'
import { useAgentStore } from '@/stores/agentStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { generateSessionId } from '@/lib/api'
import { ChatBubble } from './ChatBubble'
import { ChatWindow } from './ChatWindow'

interface ChatWidgetProps {
  isOpen: boolean
  onToggle: () => void
}

export default function ChatWidget({ isOpen, onToggle }: ChatWidgetProps) {
  const {
    sessionId,
    setSessionId
  } = useAgentStore()

  // Initialize session ID
  useEffect(() => {
    if (!sessionId) {
      setSessionId(generateSessionId())
    }
  }, [sessionId, setSessionId])

  // WebSocket connection
  const {
    isConnected,
    isConnecting,
    error,
    sendMessage
  } = useWebSocket(isOpen ? sessionId : null)

  if (!isOpen) {
    return <ChatBubble onToggle={onToggle} />
  }

  return (
    <ChatWindow
      onClose={onToggle}
      isConnected={isConnected}
      isConnecting={isConnecting}
      error={error}
      sendMessage={sendMessage}
    />
  )
}
