'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Trash2, Copy, Volume2 } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { WebSocketClient, WebSocketStatus } from '@/lib/websocket'
import { AudioRecorder, AudioVisualizer } from '@/lib/audio'
import { cn, formatTimestamp } from '@/lib/utils'

type TranscriptionItem = {
  id: string
  text: string
  timestamp: string
}

type AIResponseItem = {
  id: string
  suggestion: string
  originalText: string
  timestamp: string
}

export function InterviewAssistant() {
  const [isRecording, setIsRecording] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<WebSocketStatus>('disconnected')
  const [transcriptions, setTranscriptions] = useState<TranscriptionItem[]>([])
  const [aiResponses, setAIResponses] = useState<AIResponseItem[]>([])
  const [currentStatus, setCurrentStatus] = useState<string>('')
  const [volumeLevel, setVolumeLevel] = useState(0)
  
  const wsClient = useRef<WebSocketClient | null>(null)
  const audioRecorder = useRef<AudioRecorder | null>(null)
  const audioVisualizer = useRef<AudioVisualizer | null>(null)

  useEffect(() => {
    // Initialize WebSocket connection
    const wsUrl = process.env.NODE_ENV === 'development' 
      ? 'ws://localhost:8000/ws' 
      : `ws://${window.location.host}/ws`
    
    wsClient.current = new WebSocketClient(wsUrl)
    
    // Set up WebSocket event handlers
    wsClient.current.onStatus(setConnectionStatus)
    
    wsClient.current.onMessage('status', (data) => {
      setCurrentStatus(data.message || data.status)
    })
    
    wsClient.current.onMessage('transcription', (data) => {
      const newTranscription: TranscriptionItem = {
        id: Date.now().toString(),
        text: data.text,
        timestamp: data.timestamp || new Date().toISOString()
      }
      setTranscriptions(prev => [...prev, newTranscription])
    })
    
    wsClient.current.onMessage('ai_response', (data) => {
      const newResponse: AIResponseItem = {
        id: Date.now().toString(),
        suggestion: data.suggestion,
        originalText: data.original_text,
        timestamp: data.timestamp || new Date().toISOString()
      }
      setAIResponses(prev => [...prev, newResponse])
    })
    
    wsClient.current.onMessage('error', (data) => {
      setCurrentStatus(`Error: ${data.message}`)
      console.error('WebSocket error:', data.message)
    })

    // Initialize audio components
    audioRecorder.current = new AudioRecorder()
    audioVisualizer.current = new AudioVisualizer()

    // Connect to WebSocket
    wsClient.current.connect().catch(console.error)

    return () => {
      if (wsClient.current) {
        wsClient.current.disconnect()
      }
      if (audioRecorder.current) {
        audioRecorder.current.cleanup()
      }
      if (audioVisualizer.current) {
        audioVisualizer.current.cleanup()
      }
    }
  }, [])

  const handleStartRecording = async () => {
    if (!audioRecorder.current || !wsClient.current) return

    try {
      // Initialize audio recorder
      const success = await audioRecorder.current.initialize()
      if (!success) {
        setCurrentStatus('Failed to access microphone')
        return
      }

      // Start recording
      audioRecorder.current.startRecording((audioData) => {
        if (wsClient.current && wsClient.current.isConnected) {
          wsClient.current.sendAudioData(audioData)
        }
      })

      setIsRecording(true)
      setCurrentStatus('Listening...')

      // Start audio visualization if available
      const stream = (audioRecorder.current as any).audioStream
      if (stream && audioVisualizer.current) {
        const vizSuccess = await audioVisualizer.current.initialize(stream)
        if (vizSuccess) {
          audioVisualizer.current.startVisualization(setVolumeLevel)
        }
      }

    } catch (error) {
      console.error('Failed to start recording:', error)
      setCurrentStatus('Recording failed')
    }
  }

  const handleStopRecording = () => {
    if (audioRecorder.current) {
      audioRecorder.current.stopRecording()
    }
    if (audioVisualizer.current) {
      audioVisualizer.current.stopVisualization()
    }
    
    setIsRecording(false)
    setVolumeLevel(0)
    setCurrentStatus('Stopped listening')
  }

  const handleClearHistory = () => {
    setTranscriptions([])
    setAIResponses([])
    if (wsClient.current) {
      wsClient.current.clearHistory()
    }
  }

  const handleCopyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCurrentStatus('Copied to clipboard!')
      setTimeout(() => setCurrentStatus(''), 2000)
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
    }
  }

  const getStatusIndicatorClass = () => {
    switch (connectionStatus) {
      case 'connected': return 'status-connected'
      case 'disconnected': return 'status-disconnected'
      case 'connecting': return 'status-processing'
      default: return 'status-disconnected'
    }
  }

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <Card className="mb-6">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            AI Interview Buddy
          </CardTitle>
          <CardDescription className="text-lg">
            Your real-time interview assistant powered by AI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center space-y-4">
            {/* Connection Status */}
            <div className="flex items-center space-x-2 text-sm">
              <span className={cn('status-indicator', getStatusIndicatorClass())}></span>
              <span>Status: {connectionStatus}</span>
            </div>

            {/* Recording Controls */}
            <div className="flex items-center space-x-4">
              <Button
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                size="lg"
                variant={isRecording ? "destructive" : "default"}
                disabled={connectionStatus !== 'connected'}
                className={cn(
                  "px-8 py-4 text-lg",
                  isRecording && "recording-pulse"
                )}
              >
                {isRecording ? (
                  <>
                    <MicOff className="w-5 h-5 mr-2" />
                    Stop Listening
                  </>
                ) : (
                  <>
                    <Mic className="w-5 h-5 mr-2" />
                    Start Listening
                  </>
                )}
              </Button>

              <Button
                onClick={handleClearHistory}
                variant="outline"
                size="lg"
              >
                <Trash2 className="w-5 h-5 mr-2" />
                Clear History
              </Button>
            </div>

            {/* Audio Visualization */}
            {isRecording && (
              <div className="flex items-center space-x-2">
                <Volume2 className="w-4 h-4 text-muted-foreground" />
                <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-green-500 transition-all duration-100"
                    style={{ width: `${Math.min(volumeLevel * 100, 100)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Current Status */}
            {currentStatus && (
              <p className="text-sm text-muted-foreground text-center">
                {currentStatus}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Transcriptions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Live Transcription</CardTitle>
            <CardDescription>
              Real-time speech-to-text from the interview
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {transcriptions.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No transcriptions yet. Start listening to see speech-to-text results.
                </p>
              ) : (
                transcriptions.map((item) => (
                  <div key={item.id} className="p-3 bg-muted rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(item.timestamp)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyToClipboard(item.text)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                    <p className="text-sm">{item.text}</p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* AI Suggestions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">AI Response Suggestions</CardTitle>
            <CardDescription>
              Intelligent response recommendations for interview questions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {aiResponses.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No suggestions yet. AI will provide response recommendations based on interview questions.
                </p>
              ) : (
                aiResponses.map((item) => (
                  <div key={item.id} className="p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(item.timestamp)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyToClipboard(item.suggestion)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                    <p className="text-sm font-medium text-blue-900 mb-2">
                      💡 Suggestion:
                    </p>
                    <p className="text-sm mb-2">{item.suggestion}</p>
                    <p className="text-xs text-muted-foreground">
                      In response to: "{item.originalText}"
                    </p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}