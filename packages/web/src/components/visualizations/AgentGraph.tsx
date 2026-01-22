'use client'

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { NodeState } from '@/types/agent'

interface AgentGraphProps {
  nodeStates: Record<string, NodeState>
  currentNode: string | null
}

interface GraphNode {
  id: string
  label: string
  description: string
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  label?: string
}

// Static graph structure
const GRAPH_DATA = {
  nodes: [
    { id: 'greeter', label: 'Greeter', description: 'Initial greeting check' },
    { id: 'intent_classifier', label: 'Intent', description: 'Classify user intent' },
    { id: 'rag_retriever', label: 'RAG', description: 'Retrieve relevant context' },
    { id: 'response_generator', label: 'Response', description: 'Generate answer' },
    { id: 'fallback_response', label: 'Fallback', description: 'Handle unknown queries' },
  ],
  links: [
    { source: 'greeter', target: 'intent_classifier' },
    { source: 'intent_classifier', target: 'rag_retriever', label: 'needs_context' },
    { source: 'intent_classifier', target: 'response_generator', label: 'direct' },
    { source: 'rag_retriever', target: 'response_generator', label: 'confident' },
    { source: 'rag_retriever', target: 'fallback_response', label: 'low_confidence' },
  ],
}

const NODE_COLORS: Record<NodeState, string> = {
  pending: '#9ca3af',
  active: '#3b82f6',
  complete: '#10b981',
  error: '#ef4444',
}

export default function AgentGraph({ nodeStates, currentNode }: AgentGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 })
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null)

  // Handle resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect()
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Initialize D3 visualization
  useEffect(() => {
    if (!svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions
    
    // Create a copy of nodes with positions
    const nodes: GraphNode[] = GRAPH_DATA.nodes.map((n, i) => ({
      ...n,
      x: width / 2 + (i - 2) * 120,
      y: height / 2,
    }))

    const links: GraphLink[] = GRAPH_DATA.links.map(l => ({
      ...l,
      source: l.source,
      target: l.target,
    }))

    // Create arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 35)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#3f3f46')

    // Create force simulation
    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(150)
        .strength(0.5))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50))

    simulationRef.current = simulation

    // Create container group
    const g = svg.append('g')

    // Create links
    const linkGroup = g.append('g')
      .attr('class', 'links')
      .selectAll('g')
      .data(links)
      .join('g')

    const linkPaths = linkGroup.append('path')
      .attr('class', 'edge-line')
      .attr('stroke', '#3f3f46')
      .attr('stroke-width', 2)
      .attr('fill', 'none')
      .attr('marker-end', 'url(#arrowhead)')

    // Link labels
    linkGroup.append('text')
      .attr('class', 'text-[10px] fill-zinc-500')
      .attr('text-anchor', 'middle')
      .attr('dy', -8)
      .text(d => d.label || '')

    // Create nodes
    const nodeGroup = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        }))

    // Node circles - outer glow
    nodeGroup.append('circle')
      .attr('r', 35)
      .attr('class', 'node-glow')
      .attr('fill', 'none')
      .attr('stroke', d => NODE_COLORS[nodeStates[d.id] || 'pending'])
      .attr('stroke-width', 2)
      .attr('opacity', 0.3)

    // Node circles - main
    nodeGroup.append('circle')
      .attr('r', 30)
      .attr('class', 'node-circle')
      .attr('fill', '#18181b')
      .attr('stroke', d => NODE_COLORS[nodeStates[d.id] || 'pending'])
      .attr('stroke-width', 3)

    // Node labels
    nodeGroup.append('text')
      .attr('class', 'node-label')
      .attr('dy', 4)
      .text(d => d.label)

    // Tooltip on hover
    nodeGroup.on('mouseenter', function(event, d) {
      d3.select(this).select('.node-glow')
        .transition()
        .duration(200)
        .attr('opacity', 0.6)
        .attr('r', 40)
    })
    .on('mouseleave', function() {
      d3.select(this).select('.node-glow')
        .transition()
        .duration(200)
        .attr('opacity', 0.3)
        .attr('r', 35)
    })

    // Update positions on tick
    simulation.on('tick', () => {
      linkPaths.attr('d', (d: any) => {
        const sourceX = d.source.x
        const sourceY = d.source.y
        const targetX = d.target.x
        const targetY = d.target.y
        return `M${sourceX},${sourceY}L${targetX},${targetY}`
      })

      linkGroup.selectAll('text')
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2)

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 2])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    return () => {
      simulation.stop()
    }
  }, [dimensions])

  // Update node colors when states change
  useEffect(() => {
    if (!svgRef.current) return

    const svg = d3.select(svgRef.current)

    // Update stroke colors
    svg.selectAll('.node-circle')
      .transition()
      .duration(300)
      .attr('stroke', (d: any) => NODE_COLORS[nodeStates[d.id] || 'pending'])

    svg.selectAll('.node-glow')
      .transition()
      .duration(300)
      .attr('stroke', (d: any) => NODE_COLORS[nodeStates[d.id] || 'pending'])

    // Pulse animation for active node
    svg.selectAll('.node')
      .classed('node-active', (d: any) => d.id === currentNode)

  }, [nodeStates, currentNode])

  return (
    <div ref={containerRef} className="viz-container">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="bg-dark-bg"
      />
    </div>
  )
}
