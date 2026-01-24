'use client'

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'

interface UseSpeechSynthesisOptions {
    preferredVoices?: string[] // e.g., ['Google US English', 'Samantha']
    rate?: number              // 0.1 to 10, default 1
    pitch?: number             // 0 to 2, default 1
    volume?: number            // 0 to 1, default 1
    onStart?: () => void
    onEnd?: () => void
    onError?: (error: string) => void
}

interface UseSpeechSynthesisReturn {
    speak: (text: string, queue?: boolean) => void
    stop: () => void
    pause: () => void
    resume: () => void
    isSpeaking: boolean
    isPaused: boolean
    isSupported: boolean
    isReady: boolean           // Voices loaded and ready
    voices: SpeechSynthesisVoice[]
    selectedVoice: SpeechSynthesisVoice | null
    error: string | null
    initializeAudio: () => void // MUST call on first user interaction!
}

export function useSpeechSynthesis({
    preferredVoices = ['Google US English', 'Samantha'],
    rate = 1,
    pitch = 1,
    volume = 1,
    onStart,
    onEnd,
    onError
}: UseSpeechSynthesisOptions = {}): UseSpeechSynthesisReturn {
    const [isSpeaking, setIsSpeaking] = useState(false)
    const [isPaused, setIsPaused] = useState(false)
    const [isSupported, setIsSupported] = useState(false)
    const [isReady, setIsReady] = useState(false)
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
    const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [isAudioUnlocked, setIsAudioUnlocked] = useState(false)

    const synthesisRef = useRef<SpeechSynthesis | null>(null)
    const heartbeatRef = useRef<NodeJS.Timeout | null>(null)
    const onStartRef = useRef(onStart)
    const onEndRef = useRef(onEnd)
    const onErrorRef = useRef(onError)

    // Keep refs in sync
    useEffect(() => {
        onStartRef.current = onStart
        onEndRef.current = onEnd
        onErrorRef.current = onError
    }, [onStart, onEnd, onError])

    // Check browser support
    useEffect(() => {
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
            setIsSupported(true)
            synthesisRef.current = window.speechSynthesis
            loadVoices()
        } else {
            setIsSupported(false)
            setError('Text-to-speech not supported in this browser.')
        }
    }, [])

    // Load voices (they load asynchronously!)
    const loadVoices = useCallback(() => {
        if (!synthesisRef.current) return

        const updateVoices = () => {
            const availableVoices = synthesisRef.current!.getVoices()

            if (availableVoices.length > 0) {
                console.log('🔊 Loaded', availableVoices.length, 'voices')
                setVoices(availableVoices)

                // Find preferred voice
                let voice: SpeechSynthesisVoice | undefined

                // Try each preferred voice in order
                for (const preferred of preferredVoices) {
                    voice = availableVoices.find(v =>
                        v.name.includes(preferred) || v.name === preferred
                    )
                    if (voice) break
                }

                // Fallback: any English voice with "Female" or Google
                if (!voice) {
                    voice = availableVoices.find(v =>
                        v.lang.startsWith('en') && (v.name.includes('Female') || v.name.includes('Google'))
                    )
                }

                // Fallback: any English voice
                if (!voice) {
                    voice = availableVoices.find(v => v.lang.startsWith('en'))
                }

                // Fallback: first voice
                if (!voice) {
                    voice = availableVoices[0]
                }

                setSelectedVoice(voice || null)
                setIsReady(true)
                console.log('🔊 Selected voice:', voice?.name)
            }
        }

        // Voices might already be loaded
        updateVoices()

        // But usually they load async, so listen for the event
        synthesisRef.current.addEventListener('voiceschanged', updateVoices)

        // Chrome sometimes needs a nudge
        setTimeout(updateVoices, 100)
        setTimeout(updateVoices, 500)

        return () => {
            synthesisRef.current?.removeEventListener('voiceschanged', updateVoices)
        }
    }, [preferredVoices])

    // CRITICAL: Initialize audio on first user interaction
    // This unlocks autoplay restrictions in modern browsers
    const initializeAudio = useCallback(() => {
        if (!isSupported || isAudioUnlocked) return

        console.log('🔊 Initializing audio context...')

        // Speak empty/silent utterance to "unlock" audio
        if (synthesisRef.current) {
            const utterance = new SpeechSynthesisUtterance('')
            utterance.volume = 0
            synthesisRef.current.speak(utterance)
        }

        // Also try to resume AudioContext if it exists (for other audio features)
        try {
            const AudioContext = window.AudioContext || (window as any).webkitAudioContext
            if (AudioContext) {
                const ctx = new AudioContext()
                ctx.resume().then(() => {
                    console.log('🔊 AudioContext resumed')
                }).catch(() => {
                    // Ignore errors
                })
            }
        } catch {
            // AudioContext not needed for basic TTS
        }

        setIsAudioUnlocked(true)
    }, [isSupported, isAudioUnlocked])

    // Start heartbeat to prevent Chrome 15-second cutoff bug
    const startHeartbeat = useCallback(() => {
        // Chrome bug: speech stops after ~15 seconds
        // Fix: pause and resume every 10 seconds to keep it alive
        heartbeatRef.current = setInterval(() => {
            if (synthesisRef.current?.speaking && !synthesisRef.current?.paused) {
                console.log('🔊 Heartbeat: keeping speech alive')
                synthesisRef.current.pause()
                synthesisRef.current.resume()
            }
        }, 10000) // Every 10 seconds
    }, [])

    const stopHeartbeat = useCallback(() => {
        if (heartbeatRef.current) {
            clearInterval(heartbeatRef.current)
            heartbeatRef.current = null
        }
    }, [])

    // Main speak function
    const speak = useCallback((text: string, queue: boolean = false) => {
        if (!isSupported || !synthesisRef.current) {
            const message = 'Speech synthesis not available'
            setError(message)
            onErrorRef.current?.(message)
            return
        }

        if (!text.trim()) {
            console.log('🔊 Empty text, skipping')
            return
        }

        // Clean text of markdown
        const cleanText = text
            .replace(/\*\*(.*?)\*\*/g, '$1') // Bold
            .replace(/\*(.*?)\*/g, '$1')    // Italic
            .replace(/__(.*?)__/g, '$1')    // Bold
            .replace(/_(.*?)_/g, '$1')     // Italic
            .replace(/`{1,3}([\s\S]*?)`{1,3}/g, '$1') // Code
            .replace(/\[(.*?)\]\(.*?\)/g, '$1') // Links
            .replace(/#+\s+(.*)/g, '$1')    // Headers
            .replace(/([*+\-]\s+|[0-9]+\.\s+)/g, '') // List markers
            .replace(/[#*`~_]/g, '') // Leftover markers
            .trim()

        if (!cleanText) return

        // Warn if audio not initialized
        if (!isAudioUnlocked) {
            console.warn('🔊 Warning: Audio may be blocked. Call initializeAudio() on user interaction first.')
        }

        // Handle queuing vs cancelling
        if (!queue) {
            console.log('🔊 Cancelling previous speech and speaking now')
            synthesisRef.current.cancel()
            stopHeartbeat()
        } else {
            console.log('🔊 Queuing speech')
        }

        synthesisRef.current.resume()
        setError(null)

        // Small delay for cancel to complete if not queuing
        setTimeout(() => {
            const utterance = new SpeechSynthesisUtterance(cleanText)

            // Configure
            if (selectedVoice) {
                utterance.voice = selectedVoice
            }
            utterance.rate = rate
            utterance.pitch = pitch
            utterance.volume = volume
            utterance.lang = selectedVoice?.lang || 'en-US'

            // Event handlers
            utterance.onstart = () => {
                console.log('🔊 Speech started')
                setIsSpeaking(true)
                setIsPaused(false)
                startHeartbeat()
                onStartRef.current?.()
            }

            utterance.onend = () => {
                console.log('🔊 Speech ended')
                setIsSpeaking(false)
                setIsPaused(false)
                stopHeartbeat()
                onEndRef.current?.()
            }

            utterance.onerror = (event) => {
                console.error('🔊 Speech error:', event.error)

                let message = ''
                switch (event.error) {
                    case 'canceled':
                        // Not really an error
                        message = ''
                        break
                    case 'interrupted':
                        // User manually stopped or new speech started - not an error we want to show
                        message = ''
                        break
                    case 'audio-busy':
                        message = 'Audio is busy. Try again.'
                        break
                    case 'network':
                        message = 'Network error during speech'
                        break
                    case 'not-allowed':
                        message = 'Speech blocked. Click anywhere on the page first, then try again.'
                        break
                    default:
                        message = `Speech error: ${event.error}`
                }

                if (message) {
                    setError(message)
                    onErrorRef.current?.(message)
                }

                setIsSpeaking(false)
                setIsPaused(false)
                stopHeartbeat()
            }

            utterance.onpause = () => setIsPaused(true)
            utterance.onresume = () => setIsPaused(false)

            // SPEAK!
            try {
                synthesisRef.current!.speak(utterance)

                // Double-check it actually started (Chrome quirk)
                setTimeout(() => {
                    if (!synthesisRef.current?.speaking && !synthesisRef.current?.pending) {
                        console.warn('🔊 Speech may have been blocked')
                        // Don't set error here, it might just be very short text
                    }
                }, 100)
            } catch (err: any) {
                const message = `Failed to speak: ${err.message}`
                setError(message)
                onErrorRef.current?.(message)
            }
        }, 50)
    }, [isSupported, selectedVoice, rate, pitch, volume, isAudioUnlocked, startHeartbeat, stopHeartbeat])

    const stop = useCallback(() => {
        if (!synthesisRef.current) return
        synthesisRef.current.cancel()
        stopHeartbeat()
        setIsSpeaking(false)
        setIsPaused(false)
    }, [stopHeartbeat])

    const pause = useCallback(() => {
        if (!synthesisRef.current) return
        synthesisRef.current.pause()
        setIsPaused(true)
    }, [])

    const resume = useCallback(() => {
        if (!synthesisRef.current) return
        synthesisRef.current.resume()
        setIsPaused(false)
    }, [])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (synthesisRef.current) {
                synthesisRef.current.cancel()
            }
            stopHeartbeat()
        }
    }, [stopHeartbeat])

    return useMemo(() => ({
        speak,
        stop,
        pause,
        resume,
        isSpeaking,
        isPaused,
        isSupported,
        isReady,
        voices,
        selectedVoice,
        error,
        initializeAudio
    }), [
        speak, stop, pause, resume, isSpeaking, isPaused,
        isSupported, isReady, voices, selectedVoice, error, initializeAudio
    ])
}
