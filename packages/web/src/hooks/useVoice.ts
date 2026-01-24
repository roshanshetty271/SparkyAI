'use client'

import { useCallback, useMemo, useState, useRef } from 'react'
import { useSpeechRecognition } from './useSpeechRecognition'
import { useSpeechSynthesis } from './useSpeechSynthesis'

interface UseVoiceOptions {
    onTranscript?: (transcript: string) => void
    onSpeechEnd?: () => void
    preferredVoices?: string[]
}

interface UseVoiceReturn {
    // === ORIGINAL API (backward compatible) ===
    isListening: boolean
    isSpeaking: boolean
    transcript: string
    error: string | null
    startListening: () => Promise<void>
    stopListening: () => void
    speak: (text: string, queue?: boolean) => void
    stopSpeaking: () => void
    supported: boolean

    // === NEW ENHANCED API ===
    // Initialization (MUST call on first user interaction)
    initialize: () => void
    isInitialized: boolean

    // Detailed status
    isReady: boolean              // Everything loaded and ready to use
    isPermissionGranted: boolean | null  // Mic permission status

    // Synthesis extras
    isPaused: boolean
    pauseSpeaking: () => void
    resumeSpeaking: () => void
    voices: SpeechSynthesisVoice[]
    selectedVoice: SpeechSynthesisVoice | null
}

export function useVoice(options: UseVoiceOptions = {}): UseVoiceReturn {
    const [isInitialized, setIsInitialized] = useState(false)
    const isInitializedRef = useRef(false)

    // Memoize options to prevent sub-hook re-initialization
    const onTranscript = options.onTranscript
    const onSpeechEnd = options.onSpeechEnd
    const preferredVoices = options.preferredVoices

    const defaultVoices = useMemo(() => ['Google US English', 'Samantha'], [])


    // Compose the two specialized hooks
    const recognition = useSpeechRecognition({
        onResult: onTranscript,
        onError: (err) => console.error('Voice recognition error:', err)
    })

    const synthesis = useSpeechSynthesis({
        preferredVoices: preferredVoices || defaultVoices,
        onEnd: onSpeechEnd,
        onError: (err) => {
            console.error('Voice synthesis error:', err)
        }
    })

    const { startListening: rawStartListening, stopListening: rawStopListening } = recognition
    const { speak: rawSpeak, stop: rawStopSynthesis } = synthesis

    const { initializeAudio: rawInitializeAudio } = synthesis

    // Combined initialization - call this on first user interaction!
    const initialize = useCallback(() => {
        if (!isInitializedRef.current) {
            console.log('🎯 Initializing voice system...')
            rawInitializeAudio()
            isInitializedRef.current = true
            setIsInitialized(true)
        }
    }, [rawInitializeAudio])

    // Combined error (show first error from either hook)
    const error = useMemo(() => {
        return recognition.error || synthesis.error
    }, [recognition.error, synthesis.error])

    // Combined supported status
    const supported = useMemo(() => {
        return recognition.isSupported && synthesis.isSupported
    }, [recognition.isSupported, synthesis.isSupported])

    // Combined ready status (everything is loaded and ready to use)
    const isReady = useMemo(() => {
        return recognition.isSupported && synthesis.isReady
        // Note: We don't require isInitialized here because we want the UI to be active
        // so the user can click to trigger initialization!
    }, [recognition.isSupported, synthesis.isReady])

    // Wrapped startListening that initializes audio first
    const startListening = useCallback(async () => {
        // Auto-initialize if not already done
        if (!isInitialized) {
            initialize()
        }
        await rawStartListening()
    }, [isInitialized, initialize, rawStartListening])

    // Wrapped speak that initializes audio first
    const speak = useCallback((text: string, queue: boolean = false) => {
        // Auto-initialize if not already done
        if (!isInitialized) {
            initialize()
        }
        rawSpeak(text, queue)
    }, [isInitialized, initialize, rawSpeak])

    return useMemo(() => ({
        // === ORIGINAL API (backward compatible) ===
        isListening: recognition.isListening,
        isSpeaking: synthesis.isSpeaking,
        transcript: recognition.transcript,
        error,
        startListening,
        stopListening: rawStopListening,
        speak,
        stopSpeaking: rawStopSynthesis,
        supported,

        // === NEW ENHANCED API ===
        initialize,
        isInitialized,
        isReady,
        isPermissionGranted: recognition.isPermissionGranted,

        // Synthesis extras
        isPaused: synthesis.isPaused,
        pauseSpeaking: synthesis.pause,
        resumeSpeaking: synthesis.resume,
        voices: synthesis.voices,
        selectedVoice: synthesis.selectedVoice
    }), [
        recognition.isListening, recognition.transcript, recognition.stopListening, recognition.isPermissionGranted,
        synthesis.isSpeaking, synthesis.stop, synthesis.isPaused, synthesis.pause, synthesis.resume,
        synthesis.voices, synthesis.selectedVoice,
        error, startListening, speak, supported, initialize, isInitialized, isReady
    ])
}
