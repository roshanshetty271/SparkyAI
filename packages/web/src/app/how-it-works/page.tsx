'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Sparkles, Play, RefreshCw } from 'lucide-react'
import AgentGraph from '@/components/visualizations/AgentGraph'
import EmbeddingExplorer from '@/components/visualizations/EmbeddingExplorer'
import TraceTimeline from '@/components/visualizations/TraceTimeline'
import ChatWidget from '@/components/chat/ChatWidget'
import { useAgentStore } from '@/stores/agentStore'

export default function HowItWorksPage() {
  const [activeTab, setActiveTab] = useState<'graph' | 'embeddings' | 'timeline'>('graph')
  const [chatOpen, setChatOpen] = useState(false)
  const [demoRunning, setDemoRunning] = useState(false)
  
  const { 
    nodeStates, 
    currentNode, 
    retrievedChunks, 
    queryProjection,
    nodeTimings,
    resetState,
  } = useAgentStore()

  const runDemo = () => {
    setDemoRunning(true)
    setChatOpen(true)
    // Demo will run through the chat widget
  }

  return (
    <main className="min-h-screen bg-dark-bg">
      {/* Header */}
      <header className="border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link 
              href="/"
              className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
            <div className="w-px h-6 bg-dark-border" />
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent-cyan" />
              <span className="font-semibold">How SparkyAI Works</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={resetState}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-400 
                       hover:text-white transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Reset
            </button>
            <button
              onClick={runDemo}
              disabled={demoRunning}
              className="flex items-center gap-2 px-4 py-2 bg-accent-blue hover:bg-accent-blue/90 
                       text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              Run Demo
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Intro */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-3">Inside the AI Agent</h1>
          <p className="text-zinc-400 max-w-3xl">
            Watch the agent process your messages in real-time. Every node activation, 
            every RAG retrieval, every token generated — visualized as it happens.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {[
            { id: 'graph', label: 'Agent Graph', desc: 'Node execution flow' },
            { id: 'embeddings', label: 'Embedding Space', desc: 'Semantic search' },
            { id: 'timeline', label: 'Trace Timeline', desc: 'Performance metrics' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-dark-card border border-accent-cyan/50 text-white'
                  : 'bg-dark-card/50 border border-dark-border text-zinc-400 hover:text-white'
              }`}
            >
              <div className="text-sm font-medium">{tab.label}</div>
              <div className="text-xs opacity-60">{tab.desc}</div>
            </button>
          ))}
        </div>

        {/* Visualization panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main visualization */}
          <div className="lg:col-span-2 bg-dark-card border border-dark-border rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-dark-border flex items-center justify-between">
              <h2 className="font-semibold">
                {activeTab === 'graph' && 'Agent Execution Graph'}
                {activeTab === 'embeddings' && 'Embedding Space Explorer'}
                {activeTab === 'timeline' && 'Execution Timeline'}
              </h2>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
                <span className="text-xs text-zinc-400">
                  {currentNode ? `Active: ${currentNode}` : 'Ready'}
                </span>
              </div>
            </div>
            
            <div className="h-[500px]">
              {activeTab === 'graph' && (
                <AgentGraph 
                  nodeStates={nodeStates} 
                  currentNode={currentNode} 
                />
              )}
              {activeTab === 'embeddings' && (
                <EmbeddingExplorer 
                  retrievedChunks={retrievedChunks}
                  queryProjection={queryProjection}
                />
              )}
              {activeTab === 'timeline' && (
                <TraceTimeline 
                  timings={nodeTimings} 
                />
              )}
            </div>
          </div>

          {/* Side panel - Legend & Info */}
          <div className="space-y-6">
            {/* Legend */}
            <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
              <h3 className="font-semibold mb-4">Node States</h3>
              <div className="space-y-3">
                {[
                  { color: 'bg-node-pending', label: 'Pending', desc: 'Waiting to execute' },
                  { color: 'bg-node-active', label: 'Active', desc: 'Currently processing' },
                  { color: 'bg-node-complete', label: 'Complete', desc: 'Finished successfully' },
                  { color: 'bg-node-error', label: 'Error', desc: 'Something went wrong' },
                ].map((state) => (
                  <div key={state.label} className="flex items-center gap-3">
                    <span className={`w-3 h-3 rounded-full ${state.color}`} />
                    <div>
                      <div className="text-sm font-medium">{state.label}</div>
                      <div className="text-xs text-zinc-400">{state.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Current State */}
            <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
              <h3 className="font-semibold mb-4">Current State</h3>
              <div className="space-y-4 font-mono text-sm">
                {Object.entries(nodeStates).map(([node, state]) => (
                  <div key={node} className="flex items-center justify-between">
                    <span className="text-zinc-400">{node}</span>
                    <span className={`
                      px-2 py-0.5 rounded text-xs
                      ${state === 'pending' ? 'bg-zinc-800 text-zinc-400' : ''}
                      ${state === 'active' ? 'bg-accent-blue/20 text-accent-blue' : ''}
                      ${state === 'complete' ? 'bg-accent-green/20 text-accent-green' : ''}
                      ${state === 'error' ? 'bg-red-500/20 text-red-400' : ''}
                    `}>
                      {state}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Architecture info */}
            <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
              <h3 className="font-semibold mb-4">Architecture</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Framework</span>
                  <span>LangGraph</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">LLM</span>
                  <span>GPT-4o-mini</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Embeddings</span>
                  <span>text-embedding-3-small</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Streaming</span>
                  <span>WebSocket</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Technical explanation */}
        <div className="mt-12 grid md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-semibold mb-3 text-accent-cyan">1. Intent Classification</h3>
            <p className="text-zinc-400 text-sm">
              The agent first classifies your message into categories like skill_question, 
              project_inquiry, or general. This determines the routing path.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-3 text-accent-purple">2. RAG Retrieval</h3>
            <p className="text-zinc-400 text-sm">
              For knowledge-based questions, the agent searches through my resume and projects 
              using semantic similarity. You can see the retrieved chunks in the embedding space.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-3 text-accent-green">3. Response Generation</h3>
            <p className="text-zinc-400 text-sm">
              Using the retrieved context, the LLM generates a response. If confidence is low, 
              the fallback node provides a graceful redirect.
            </p>
          </div>
        </div>
      </div>

      {/* Chat Widget */}
      <ChatWidget 
        isOpen={chatOpen} 
        onToggle={() => setChatOpen(!chatOpen)} 
        showVisualization={true}
      />
    </main>
  )
}
