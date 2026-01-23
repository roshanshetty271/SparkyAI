/**
 * WebSocket Message Types
 */

// Events from server to client
export type ServerEvent =
  | { event: 'connected'; payload: { session_id: string; timestamp: string } }
  | { event: 'pong'; payload: {} }
  | { event: 'state_sync'; payload: StateSyncPayload }
  | { event: 'start'; payload: StartPayload }
  | { event: 'node_enter'; payload: { node: string } }
  | { event: 'node_complete'; payload: NodeCompletePayload }
  | { event: 'rag_results'; payload: RagResultsPayload }
  | { event: 'token'; payload: TokenPayload }
  | { event: 'complete'; payload: CompletePayload }
  | { event: 'error'; payload: ErrorPayload }

export interface StateSyncPayload {
  current_node: string | null
  node_states: Record<string, string> | null
  streaming_response: string | null
}

export interface StartPayload {
  trace_id: string
  session_id: string
  node_states: Record<string, string>
}

export interface NodeCompletePayload {
  node: string
  intent?: string
  node_states: Record<string, string>
}

export interface RagResultsPayload {
  node: string
  confidence: number
  chunk_ids: string[]
  scores: number[]
  query_projection: { x: number; y: number } | null
  node_states: Record<string, string>
}

export interface TokenPayload {
  token: string
  full_response: string
}

export interface CompletePayload {
  trace_id: string
  response: string
  node_states: Record<string, string>
  timings: Array<{
    node: string
    start_ms: number
    end_ms: number
    duration_ms: number
  }>
  total_tokens: number
  estimated_cost_usd: number
}

export interface ErrorPayload {
  code: string
  message: string
  retry_after_seconds?: number
}

// Messages from client to server
export type ClientMessage =
  | { type: 'message'; payload: { text: string } }
  | { type: 'ping' }
  | { type: 'state_sync_request' }

// WebSocket hook state
export interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
}
