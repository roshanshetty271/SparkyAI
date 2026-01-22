import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTime(value: Date | string | number): string {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '--:--'
  }

  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms)) {
    return '-'
  }

  const totalMs = Math.max(0, Math.round(ms))
  if (totalMs < 1000) {
    return `${totalMs}ms`
  }

  const totalSeconds = totalMs / 1000
  if (totalSeconds < 60) {
    const precision = totalSeconds < 10 ? 1 : 0
    return `${totalSeconds.toFixed(precision)}s`
  }

  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.round(totalSeconds % 60)
  return `${minutes}m ${seconds.toString().padStart(2, '0')}s`
}
