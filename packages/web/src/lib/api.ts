import type { ChatResponse, EmbeddingsData, GraphStructure, HealthStatus } from '@/types/agent'

/**
 * API Client for SparkyAI
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Warn if API URL is missing in production
if (process.env.NODE_ENV === 'production' && !process.env.NEXT_PUBLIC_API_URL) {
  console.warn('⚠️ NEXT_PUBLIC_API_URL is not set. API requests will target localhost.')
}

export interface ApiError {
  error: string
  status_code: number
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      error: 'An unexpected error occurred',
      status_code: response.status,
    }))
    throw new Error(error.error)
  }
  return response.json()
}

function buildApiUrl(path: string) {
  const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL
  return `${base}${path}`
}

/**
 * Health check
 */
export async function checkHealth() {
  const response = await fetch(buildApiUrl('/health'))
  return handleResponse<HealthStatus>(response)
}

/**
 * Send a chat message (non-streaming)
 */
export async function sendChatMessage(message: string, sessionId?: string) {
  const response = await fetch(buildApiUrl('/chat'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  })

  return handleResponse<ChatResponse>(response)
}

/**
 * Get agent graph structure
 */
export async function getGraphStructure() {
  const response = await fetch(buildApiUrl('/graph/structure'))
  return handleResponse<GraphStructure>(response)
}

/**
 * Get embedding points for visualization
 */
export async function getEmbeddingPoints(): Promise<EmbeddingsData> {
  const response = await fetch(buildApiUrl('/embeddings/knowledge'))
  return handleResponse<EmbeddingsData>(response)
}

/**
 * Generate a unique session ID
 */
export function generateSessionId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }

  return `session-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
}
