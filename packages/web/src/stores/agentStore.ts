import { create } from 'zustand'
import type { NodeState, RetrievedChunk, QueryProjection, NodeTiming, Message } from '@/types/agent'

interface AgentState {
  // Connection state
  sessionId: string | null
  isConnected: boolean
  
  // Conversation
  messages: Message[]
  isTyping: boolean
  streamingResponse: string
  
  // Agent execution state (for visualization)
  currentNode: string | null
  nodeStates: Record<string, NodeState>
  userIntent: string | null
  
  // RAG state
  retrievedChunks: RetrievedChunk[]
  retrievalConfidence: number
  queryProjection: QueryProjection | null
  
  // Trace data
  traceId: string | null
  nodeTimings: NodeTiming[]
  totalTokens: number
  estimatedCost: number
  
  // Actions
  setSessionId: (id: string) => void
  setConnected: (connected: boolean) => void
  
  addMessage: (message: Message) => void
  setTyping: (typing: boolean) => void
  appendStreamingResponse: (token: string) => void
  clearStreamingResponse: () => void
  
  setCurrentNode: (node: string | null) => void
  setNodeState: (node: string, state: NodeState) => void
  setNodeStates: (states: Record<string, NodeState>) => void
  setUserIntent: (intent: string | null) => void
  
  setRagResults: (chunks: RetrievedChunk[], confidence: number, projection: QueryProjection | null) => void
  
  setTraceData: (traceId: string, timings: NodeTiming[], tokens: number, cost: number) => void
  
  resetState: () => void
}

const initialNodeStates: Record<string, NodeState> = {
  greeter: 'pending',
  intent_classifier: 'pending',
  rag_retriever: 'pending',
  response_generator: 'pending',
  fallback_response: 'pending',
}

export const useAgentStore = create<AgentState>((set, get) => ({
  // Initial state
  sessionId: null,
  isConnected: false,
  
  messages: [],
  isTyping: false,
  streamingResponse: '',
  
  currentNode: null,
  nodeStates: { ...initialNodeStates },
  userIntent: null,
  
  retrievedChunks: [],
  retrievalConfidence: 0,
  queryProjection: null,
  
  traceId: null,
  nodeTimings: [],
  totalTokens: 0,
  estimatedCost: 0,
  
  // Actions
  setSessionId: (id) => set({ sessionId: id }),
  setConnected: (connected) => set({ isConnected: connected }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  
  setTyping: (typing) => set({ isTyping: typing }),
  
  appendStreamingResponse: (token) => set((state) => ({
    streamingResponse: state.streamingResponse + token,
  })),
  
  clearStreamingResponse: () => set({ streamingResponse: '' }),
  
  setCurrentNode: (node) => set({ currentNode: node }),
  
  setNodeState: (node, state) => set((prev) => ({
    nodeStates: { ...prev.nodeStates, [node]: state },
  })),
  
  setNodeStates: (states) => set({ nodeStates: states }),
  
  setUserIntent: (intent) => set({ userIntent: intent }),
  
  setRagResults: (chunks, confidence, projection) => set({
    retrievedChunks: chunks,
    retrievalConfidence: confidence,
    queryProjection: projection,
  }),
  
  setTraceData: (traceId, timings, tokens, cost) => set({
    traceId,
    nodeTimings: timings,
    totalTokens: tokens,
    estimatedCost: cost,
  }),
  
  resetState: () => set({
    currentNode: null,
    nodeStates: { ...initialNodeStates },
    userIntent: null,
    retrievedChunks: [],
    retrievalConfidence: 0,
    queryProjection: null,
    traceId: null,
    nodeTimings: [],
    totalTokens: 0,
    estimatedCost: 0,
    streamingResponse: '',
    isTyping: false,
  }),
}))
