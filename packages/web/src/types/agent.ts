/**
 * Agent State Types
 */

export type NodeState = 'pending' | 'active' | 'complete' | 'error'

export interface RetrievedChunk {
  id: string
  content: string
  source: string
  similarity: number
  metadata: Record<string, unknown>
}

export interface QueryProjection {
  x: number
  y: number
}

export interface NodeTiming {
  node: string
  start_ms: number
  end_ms: number
  duration_ms: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatResponse {
  response: string
  session_id: string
  trace_id: string
  intent?: string
  retrieval_confidence?: number
}

export interface HealthStatus {
  status: string
  timestamp: string
  version: string
  openai_connected: boolean
  redis_connected: boolean
  embeddings_loaded: boolean
  chunks_count: number
}

export interface GraphNode {
  id: string
  label: string
  description: string
}

export interface GraphEdge {
  source: string
  target: string
  label?: string
}

export interface GraphStructure {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface EmbeddingPoint {
  id: string
  x: number
  y: number
  content: string
  source: string
  category: string
}

export interface EmbeddingsData {
  points: EmbeddingPoint[]
  total_count: number
}
