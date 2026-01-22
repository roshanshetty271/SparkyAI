'use client'

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { getEmbeddingPoints } from '@/lib/api'
import type { RetrievedChunk, QueryProjection, EmbeddingPoint } from '@/types/agent'

interface EmbeddingExplorerProps {
  retrievedChunks: RetrievedChunk[]
  queryProjection: QueryProjection | null
}

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  resume: '#22d3ee',   // cyan
  projects: '#a855f7', // purple
  meta: '#10b981',     // green
  general: '#3b82f6',  // blue
}

export default function EmbeddingExplorer({ retrievedChunks, queryProjection }: EmbeddingExplorerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 })
  const [points, setPoints] = useState<EmbeddingPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [hoveredPoint, setHoveredPoint] = useState<EmbeddingPoint | null>(null)

  // Load embedding points
  useEffect(() => {
    async function loadPoints() {
      try {
        const data = await getEmbeddingPoints()
        setPoints(data.points)
      } catch (error) {
        console.error('Failed to load embedding points:', error)
        // Use mock data for demo
        setPoints(generateMockPoints())
      } finally {
        setLoading(false)
      }
    }
    loadPoints()
  }, [])

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

  // D3 visualization
  useEffect(() => {
    if (!svgRef.current || loading || points.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions
    const margin = { top: 40, right: 40, bottom: 40, left: 40 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // Scales
    const xExtent = d3.extent(points, d => d.x) as [number, number]
    const yExtent = d3.extent(points, d => d.y) as [number, number]

    const xScale = d3.scaleLinear()
      .domain([xExtent[0] - 0.1, xExtent[1] + 0.1])
      .range([0, innerWidth])

    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - 0.1, yExtent[1] + 0.1])
      .range([innerHeight, 0])

    // Container group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Grid lines
    const gridColor = '#1f1f23'
    
    g.append('g')
      .attr('class', 'grid-x')
      .selectAll('line')
      .data(xScale.ticks(10))
      .join('line')
      .attr('x1', d => xScale(d))
      .attr('x2', d => xScale(d))
      .attr('y1', 0)
      .attr('y2', innerHeight)
      .attr('stroke', gridColor)
      .attr('stroke-dasharray', '2,2')

    g.append('g')
      .attr('class', 'grid-y')
      .selectAll('line')
      .data(yScale.ticks(10))
      .join('line')
      .attr('x1', 0)
      .attr('x2', innerWidth)
      .attr('y1', d => yScale(d))
      .attr('y2', d => yScale(d))
      .attr('stroke', gridColor)
      .attr('stroke-dasharray', '2,2')

    // Get retrieved chunk IDs for highlighting
    const retrievedIds = new Set(retrievedChunks.map(c => c.id))

    // Draw connections from query to retrieved chunks
    if (queryProjection && retrievedChunks.length > 0) {
      const queryX = xScale(queryProjection.x)
      const queryY = yScale(queryProjection.y)

      // Lines to retrieved points
      g.append('g')
        .attr('class', 'connections')
        .selectAll('line')
        .data(points.filter(p => retrievedIds.has(p.id)))
        .join('line')
        .attr('class', 'embedding-connection')
        .attr('x1', queryX)
        .attr('y1', queryY)
        .attr('x2', d => xScale(d.x))
        .attr('y2', d => yScale(d.y))
        .attr('stroke', '#22d3ee')
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.5)
        .attr('stroke-dasharray', '4,4')
    }

    // Draw knowledge points
    g.append('g')
      .attr('class', 'points')
      .selectAll('circle')
      .data(points)
      .join('circle')
      .attr('class', 'embedding-point')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => retrievedIds.has(d.id) ? 8 : 5)
      .attr('fill', d => CATEGORY_COLORS[d.category] || CATEGORY_COLORS.general)
      .attr('fill-opacity', d => retrievedIds.has(d.id) ? 1 : 0.6)
      .attr('stroke', d => retrievedIds.has(d.id) ? '#fff' : 'none')
      .attr('stroke-width', 2)
      .on('mouseenter', function(event, d) {
        setHoveredPoint(d)
        d3.select(this)
          .transition()
          .duration(150)
          .attr('r', 12)
        
        // Position tooltip
        if (tooltipRef.current) {
          const [x, y] = d3.pointer(event, containerRef.current)
          tooltipRef.current.style.left = `${x + 10}px`
          tooltipRef.current.style.top = `${y - 10}px`
        }
      })
      .on('mouseleave', function(event, d) {
        setHoveredPoint(null)
        d3.select(this)
          .transition()
          .duration(150)
          .attr('r', retrievedIds.has(d.id) ? 8 : 5)
      })

    // Draw query point
    if (queryProjection) {
      g.append('circle')
        .attr('class', 'query-point')
        .attr('cx', xScale(queryProjection.x))
        .attr('cy', yScale(queryProjection.y))
        .attr('r', 10)
        .attr('fill', '#f97316')
        .attr('stroke', '#fff')
        .attr('stroke-width', 3)

      // Pulse animation
      g.append('circle')
        .attr('class', 'query-pulse')
        .attr('cx', xScale(queryProjection.x))
        .attr('cy', yScale(queryProjection.y))
        .attr('r', 10)
        .attr('fill', 'none')
        .attr('stroke', '#f97316')
        .attr('stroke-width', 2)
        .attr('opacity', 0.8)
        .transition()
        .duration(1000)
        .attr('r', 25)
        .attr('opacity', 0)
        .ease(d3.easeQuadOut)
        .on('end', function() {
          d3.select(this).remove()
        })
    }

    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        g.attr('transform', 
          `translate(${margin.left + event.transform.x},${margin.top + event.transform.y}) scale(${event.transform.k})`
        )
      })

    svg.call(zoom)

  }, [dimensions, points, loading, retrievedChunks, queryProjection])

  // Legend
  const categories = [
    { key: 'resume', label: 'Resume', color: CATEGORY_COLORS.resume },
    { key: 'projects', label: 'Projects', color: CATEGORY_COLORS.projects },
    { key: 'meta', label: 'Contact/FAQ', color: CATEGORY_COLORS.meta },
    { key: 'query', label: 'Your Query', color: '#f97316' },
  ]

  return (
    <div ref={containerRef} className="viz-container relative">
      {loading ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-zinc-400">Loading embeddings...</div>
        </div>
      ) : (
        <>
          <svg
            ref={svgRef}
            width={dimensions.width}
            height={dimensions.height}
            className="bg-dark-bg"
          />
          
          {/* Legend */}
          <div className="absolute top-4 left-4 bg-dark-card/80 backdrop-blur-sm 
                        border border-dark-border rounded-lg p-3">
            <div className="text-xs font-medium text-zinc-400 mb-2">Categories</div>
            <div className="space-y-1.5">
              {categories.map(cat => (
                <div key={cat.key} className="flex items-center gap-2">
                  <span 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: cat.color }}
                  />
                  <span className="text-xs text-zinc-300">{cat.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tooltip */}
          {hoveredPoint && (
            <div 
              ref={tooltipRef}
              className="absolute z-10 max-w-xs p-3 bg-dark-card border border-dark-border 
                       rounded-lg shadow-xl pointer-events-none"
            >
              <div className="text-xs font-medium text-zinc-400 mb-1">
                {hoveredPoint.source}
              </div>
              <p className="text-sm text-white line-clamp-3">
                {hoveredPoint.content}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// Mock data for when API is unavailable
function generateMockPoints(): EmbeddingPoint[] {
  const categories = ['resume', 'projects', 'meta']
  const points: EmbeddingPoint[] = []
  
  for (let i = 0; i < 50; i++) {
    const category = categories[Math.floor(Math.random() * categories.length)]
    const clusterCenter = {
      resume: { x: -0.5, y: 0.3 },
      projects: { x: 0.4, y: -0.2 },
      meta: { x: 0.1, y: 0.5 },
    }[category]!
    
    points.push({
      id: `mock-${i}`,
      x: clusterCenter.x + (Math.random() - 0.5) * 0.4,
      y: clusterCenter.y + (Math.random() - 0.5) * 0.4,
      content: `Sample content for ${category} chunk ${i}...`,
      source: `${category}/sample.md`,
      category,
    })
  }
  
  return points
}
