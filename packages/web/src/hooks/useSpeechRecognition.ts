'use client'

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'

interface UseSpeechRecognitionOptions {
    onResult?: (transcript: string) => void
    onError?: (error: string) => void
    continuous?: boolean
    language?: string
}

interface UseSpeechRecognitionReturn {
    isListening: boolean
    isSupported: boolean
    isPermissionGranted: boolean | null // null = unknown, true = granted, false = denied
    transcript: string
    error: string | null
    startListening: () => Promise<void>
    stopListening: () => void
}

export function useSpeechRecognition({
    onResult,
    onError,
    continuous = false,
    language = 'en-US'
}: UseSpeechRecognitionOptions = {}): UseSpeechRecognitionReturn {
    const [isListening, setIsListening] = useState(false)
    const [isSupported, setIsSupported] = useState(false)
    const [isPermissionGranted, setIsPermissionGranted] = useState<boolean | null>(null)
    const [transcript, setTranscript] = useState('')
    const [error, setError] = useState<string | null>(null)

    const recognitionRef = useRef<SpeechRecognition | null>(null)
    const onResultRef = useRef(onResult)
    const onErrorRef = useRef(onError)

    // Keep refs in sync
    useEffect(() => {
        onResultRef.current = onResult
        onErrorRef.current = onError
    }, [onResult, onError])


    // Check browser support and secure context on mount
    useEffect(() => {
        if (typeof window === 'undefined') return

        // Check secure context
        if (!window.isSecureContext && window.location.hostname !== 'localhost') {
            setError('Microphone requires HTTPS or localhost.')
            setIsSupported(false)
            return
        }

        // Check browser support
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

        if (!SpeechRecognition) {
            setError('Speech recognition not supported in this browser. Try Chrome.')
            setIsSupported(false)
            return
        }

        setIsSupported(true)

        // Check existing permission status (if Permissions API available)
        checkPermissionStatus()

        // Setup recognition instance
        const recognition = new SpeechRecognition()
        recognition.continuous = continuous
        recognition.interimResults = true
        recognition.lang = language

        recognition.onstart = () => {
            console.log('🎤 Recognition started')
            setIsListening(true)
            setError(null)
        }

        recognition.onend = () => {
            console.log('🎤 Recognition ended')
            setIsListening(false)
        }

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            console.error('🎤 Recognition error:', event.error)

            let message = 'An error occurred with voice input.'
            switch (event.error) {
                case 'not-allowed':
                case 'service-not-allowed':
                    message = 'Microphone access denied. Click the lock icon in your address bar → Site settings → Allow microphone.'
                    setIsPermissionGranted(false)
                    break
                case 'no-speech':
                    message = 'No speech detected. Please try again.'
                    break
                case 'audio-capture':
                    message = 'No microphone found. Please connect a microphone.'
                    break
                case 'network':
                    message = 'Network error. Please check your connection.'
                    break
                case 'aborted':
                    // User or code stopped it, not really an error
                    message = ''
                    break
                default:
                    message = `Voice error: ${event.error}`
            }

            if (message) {
                setError(message)
                onErrorRef.current?.(message)
            }
            setIsListening(false)
        }

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            let finalTranscript = ''
            let interimTranscript = ''

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i]
                if (result.isFinal) {
                    finalTranscript += result[0].transcript
                } else {
                    interimTranscript += result[0].transcript
                }
            }

            // Update transcript with interim results for visual feedback
            const currentTranscript = finalTranscript || interimTranscript
            if (currentTranscript) {
                setTranscript(currentTranscript)
            }

            // Only call onResult with final transcript
            if (finalTranscript) {
                onResultRef.current?.(finalTranscript.trim())
            }
        }

        recognitionRef.current = recognition

        return () => {
            recognition.stop()
        }
    }, [continuous, language])

    // Check permission status using Permissions API
    const checkPermissionStatus = async () => {
        try {
            if (navigator.permissions) {
                const result = await navigator.permissions.query({ name: 'microphone' as PermissionName })

                const updateState = () => {
                    if (result.state === 'granted') setIsPermissionGranted(true)
                    else if (result.state === 'denied') setIsPermissionGranted(false)
                    else setIsPermissionGranted(null) // 'prompt' means unknown/not yet granted
                }

                updateState()

                // Listen for permission changes
                result.addEventListener('change', () => {
                    updateState()
                    if (result.state === 'granted') {
                        setError(null)
                    }
                })
            }
        } catch {
            // Permissions API not fully supported, that's okay
            console.log('Permissions API not available for microphone check')
        }
    }

    // Request microphone permission explicitly (warm-up)
    const requestMicrophonePermission = async (): Promise<boolean> => {
        try {
            // This triggers the browser's permission prompt
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

            // Permission granted - clean up the stream
            stream.getTracks().forEach(track => track.stop())
            setIsPermissionGranted(true)
            setError(null)
            return true
        } catch (err: any) {
            console.error('Mic permission error:', err)

            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                const message = 'Microphone access denied. Click the lock icon in your address bar to allow access.'
                setError(message)
                setIsPermissionGranted(false)
                onErrorRef.current?.(message)
            } else if (err.name === 'NotFoundError') {
                const message = 'No microphone found. Please connect a microphone.'
                setError(message)
                onErrorRef.current?.(message)
            } else if (err.name === 'NotReadableError') {
                const message = 'Microphone is in use by another application.'
                setError(message)
                onErrorRef.current?.(message)
            } else {
                const message = `Microphone error: ${err.message || 'Unknown error'}`
                setError(message)
                onErrorRef.current?.(message)
            }
            return false
        }
    }

    const startListening = useCallback(async () => {
        if (!recognitionRef.current || !isSupported) {
            setError('Speech recognition not available')
            return
        }

        setError(null)
        setTranscript('')

        // Step 1: Request permission FIRST (ensures browser prompt appears)
        const hasPermission = await requestMicrophonePermission()
        if (!hasPermission) {
            return
        }

        // Step 2: Start recognition
        try {
            recognitionRef.current.start()
        } catch (err: any) {
            if (err.message?.includes('already started')) {
                // Already listening, that's fine
            } else {
                const message = `Failed to start: ${err.message}`
                setError(message)
                onErrorRef.current?.(message)
            }
        }
    }, [isSupported, onError])

    const stopListening = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop()
        }
        setIsListening(false)
    }, [])

    return useMemo(() => ({
        isListening,
        isSupported,
        isPermissionGranted,
        transcript,
        error,
        startListening,
        stopListening
    }), [isListening, isSupported, isPermissionGranted, transcript, error, startListening, stopListening])
}
