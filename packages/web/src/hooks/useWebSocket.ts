'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import { useAgentStore } from '@/stores/agentStore'
import type { ServerEvent, ClientMessage, WebSocketState } from '@/types/websocket'
import type { NodeState } from '@/types/agent'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 1000

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempt: 0,
  })

  const {
    setConnected,
    setCurrentNode,
    setNodeState,
    setNodeStates,
    setUserIntent,
    setRagResults,
    appendStreamingResponse,
    clearStreamingResponse,
    setTraceData,
    addMessage,
    setTyping,
  } = useAgentStore()

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data: ServerEvent = JSON.parse(event.data)
      
      switch (data.event) {
        case 'connected':
          console.log('WebSocket connected:', data.payload.session_id)
          setConnected(true)
          break

        case 'pong':
          // Heartbeat response
          break

        case 'state_sync':
          // Restore state after reconnection
          if (data.payload.current_node) {
            setCurrentNode(data.payload.current_node)
          }
          if (data.payload.node_states) {
            setNodeStates(data.payload.node_states as Record<string, NodeState>)
          }
          break

        case 'start':
          setTyping(true)
          clearStreamingResponse()
          setNodeStates(data.payload.node_states as Record<string, NodeState>)
          break

        case 'node_enter':
          setCurrentNode(data.payload.node)
          setNodeState(data.payload.node, 'active')
          break

        case 'node_complete':
          setNodeState(data.payload.node, 'complete')
          setNodeStates(data.payload.node_states as Record<string, NodeState>)
          if (data.payload.intent) {
            setUserIntent(data.payload.intent)
          }
          break

        case 'rag_results':
          setNodeState(data.payload.node, 'complete')
          setNodeStates(data.payload.node_states as Record<string, NodeState>)
          setRagResults(
            [], // Full chunks will be fetched separately if needed
            data.payload.confidence,
            data.payload.query_projection
          )
          break

        case 'token':
          appendStreamingResponse(data.payload.token)
          break

        case 'complete':
          setTyping(false)
          setCurrentNode(null)
          setNodeStates(data.payload.node_states as Record<string, NodeState>)
          setTraceData(
            data.payload.trace_id,
            data.payload.timings,
            data.payload.total_tokens,
            data.payload.estimated_cost_usd
          )
          // Add assistant message
          addMessage({
            id: data.payload.trace_id,
            role: 'assistant',
            content: data.payload.response,
            timestamp: new Date(),
          })
          clearStreamingResponse()
          break

        case 'error':
          console.error('Server error:', data.payload)
          setState(prev => ({
            ...prev,
            error: data.payload.message,
          }))
          setTyping(false)
          break
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err)
    }
  }, [
    setConnected,
    setCurrentNode,
    setNodeState,
    setNodeStates,
    setUserIntent,
    setRagResults,
    appendStreamingResponse,
    clearStreamingResponse,
    setTraceData,
    addMessage,
    setTyping,
  ])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!sessionId || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }))

    const ws = new WebSocket(`${WS_URL}/ws/${sessionId}`)

    ws.onopen = () => {
      console.log('WebSocket opened')
      setState({
        isConnected: true,
        isConnecting: false,
        error: null,
        reconnectAttempt: 0,
      })
    }

    ws.onmessage = handleMessage

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      setConnected(false)
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
      }))

      // Attempt reconnection
      if (event.code !== 1000 && state.reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAY * Math.pow(2, state.reconnectAttempt)
        console.log(`Reconnecting in ${delay}ms...`)
        
        reconnectTimeoutRef.current = setTimeout(() => {
          setState(prev => ({
            ...prev,
            reconnectAttempt: prev.reconnectAttempt + 1,
          }))
          connect()
        }, delay)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setState(prev => ({
        ...prev,
        error: 'Connection error',
      }))
    }

    wsRef.current = ws
  }, [sessionId, handleMessage, setConnected, state.reconnectAttempt])

  // Send message
  const sendMessage = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      return false
    }

    // Add user message to store
    addMessage({
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    })

    const message: ClientMessage = {
      type: 'message',
      payload: { text },
    }

    wsRef.current.send(JSON.stringify(message))
    return true
  }, [addMessage])

  // Send ping
  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }))
    }
  }, [])

  // Request state sync
  const requestStateSync = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'state_sync_request' }))
    }
  }, [])

  // Disconnect
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect')
      wsRef.current = null
    }
    
    setState({
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempt: 0,
    })
  }, [])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (sessionId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [sessionId, connect, disconnect])

  // Heartbeat
  useEffect(() => {
    if (!state.isConnected) return

    const interval = setInterval(sendPing, 30000) // Every 30 seconds
    return () => clearInterval(interval)
  }, [state.isConnected, sendPing])

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    requestStateSync,
  }
}
