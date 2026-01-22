'use client'

import { useMemo } from 'react'
import { formatDuration } from '@/lib/utils'
import type { NodeTiming } from '@/types/agent'

interface TraceTimelineProps {
  timings: NodeTiming[]
}

const NODE_COLORS: Record<string, string> = {
  greeter: '#22d3ee',
  intent_classifier: '#a855f7',
  rag_retriever: '#10b981',
  response_generator: '#3b82f6',
  fallback_response: '#f97316',
}

const NODE_LABELS: Record<string, string> = {
  greeter: 'Greeter',
  intent_classifier: 'Intent Classifier',
  rag_retriever: 'RAG Retriever',
  response_generator: 'Response Generator',
  fallback_response: 'Fallback',
}

export default function TraceTimeline({ timings }: TraceTimelineProps) {
  const { timelineData, totalDuration, minTime } = useMemo(() => {
    if (timings.length === 0) {
      return { timelineData: [], totalDuration: 0, minTime: 0 }
    }

    const minTime = Math.min(...timings.map(t => t.start_ms))
    const maxTime = Math.max(...timings.map(t => t.end_ms))
    const totalDuration = maxTime - minTime

    const timelineData = timings.map(timing => ({
      ...timing,
      relativeStart: ((timing.start_ms - minTime) / totalDuration) * 100,
      relativeWidth: (timing.duration_ms / totalDuration) * 100,
      color: NODE_COLORS[timing.node] || '#6b7280',
      label: NODE_LABELS[timing.node] || timing.node,
    }))

    return { timelineData, totalDuration, minTime }
  }, [timings])

  if (timings.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-400">
        <div className="text-center">
          <p className="text-lg mb-2">No trace data yet</p>
          <p className="text-sm">Send a message to see execution timeline</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full p-6 overflow-auto">
      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
          <div className="text-xs text-zinc-400 mb-1">Total Time</div>
          <div className="text-2xl font-mono font-bold text-white">
            {formatDuration(totalDuration)}
          </div>
        </div>
        <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
          <div className="text-xs text-zinc-400 mb-1">Nodes Executed</div>
          <div className="text-2xl font-mono font-bold text-white">
            {timings.length}
          </div>
        </div>
        <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
          <div className="text-xs text-zinc-400 mb-1">Slowest Node</div>
          <div className="text-2xl font-mono font-bold text-white">
            {timings.length > 0 
              ? formatDuration(Math.max(...timings.map(t => t.duration_ms)))
              : '-'}
          </div>
        </div>
      </div>

      {/* Timeline visualization */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
          <span>0ms</span>
          <span>{formatDuration(totalDuration)}</span>
        </div>

        {timelineData.map((item, index) => (
          <div key={index} className="relative">
            {/* Node label */}
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{item.label}</span>
              <span className="text-xs font-mono text-zinc-400">
                {formatDuration(item.duration_ms)}
              </span>
            </div>

            {/* Timeline bar background */}
            <div className="h-8 bg-dark-bg rounded relative overflow-hidden">
              {/* Bar */}
              <div
                className="timeline-bar absolute top-0 bottom-0"
                style={{
                  left: `${item.relativeStart}%`,
                  width: `${Math.max(item.relativeWidth, 2)}%`,
                  backgroundColor: item.color,
                }}
              >
                {/* Glow effect */}
                <div 
                  className="absolute inset-0 opacity-30"
                  style={{
                    boxShadow: `0 0 20px ${item.color}`,
                  }}
                />
              </div>

              {/* Time markers */}
              <div 
                className="absolute top-1/2 -translate-y-1/2 text-[10px] font-mono text-white/80 pointer-events-none px-2"
                style={{
                  left: `${item.relativeStart}%`,
                }}
              >
                {item.relativeWidth > 15 && formatDuration(item.duration_ms)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Waterfall breakdown */}
      <div className="mt-8">
        <h3 className="text-sm font-medium text-zinc-400 mb-4">Detailed Breakdown</h3>
        <div className="space-y-2">
          {timelineData.map((item, index) => (
            <div 
              key={index}
              className="flex items-center gap-4 p-3 bg-dark-bg rounded-lg"
            >
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <div className="flex-1">
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-zinc-500">
                  Started at {formatDuration(item.start_ms - minTime)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono">{formatDuration(item.duration_ms)}</div>
                <div className="text-xs text-zinc-500">
                  {((item.duration_ms / totalDuration) * 100).toFixed(1)}% of total
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
