'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Mic, MicOff, Home, Volume2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CoachCard } from '@/components/CoachCard'
import { useAudioStream } from '@/lib/audioStream'

type CoachingData = {
  bullets: string[]
  follow_up: string
  transcript?: string
}

export default function InterviewPage() {
  const [isRecording, setIsRecording] = useState(false)
  const [coachingData, setCoachingData] = useState<CoachingData | null>(null)
  const [transcript, setTranscript] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const { 
    startRecording, 
    stopRecording, 
    isConnected, 
    connectionStatus,
    volumeLevel 
  } = useAudioStream({
    onCoachingData: (data: CoachingData) => {
      setCoachingData(data)
      if (data.transcript) {
        setTranscript(data.transcript)
      }
      setIsLoading(false)
    },
    onTranscript: (text: string) => {
      setTranscript(text)
      setIsLoading(true) // Show loading while waiting for coaching data
    },
    onError: (error: string) => {
      console.error('Audio stream error:', error)
      setIsLoading(false)
    }
  })

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording()
      setIsRecording(false)
    } else {
      startRecording()
      setIsRecording(true)
    }
  }

  const handleGoHome = () => {
    if (isRecording) {
      stopRecording()
    }
    router.push('/')
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500'
      case 'disconnected': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Interview Mode</h1>
          <Button variant="outline" onClick={handleGoHome}>
            <Home className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>

        {/* Connection Status */}
        <div className="flex items-center justify-center mb-6">
          <div className="flex items-center gap-2 text-sm">
            <div className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`}></div>
            <span>Status: {connectionStatus}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Recording Controls */}
          <div className="space-y-6">
            {/* Recording Card */}
            <Card>
              <CardHeader className="text-center">
                <CardTitle>Voice Recording</CardTitle>
                <CardDescription>
                  Click to start/stop recording your interview responses
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center space-y-4">
                <Button
                  onClick={handleToggleRecording}
                  disabled={!isConnected}
                  size="lg"
                  variant={isRecording ? "destructive" : "default"}
                  className="w-32 h-32 rounded-full text-lg"
                >
                  {isRecording ? (
                    <MicOff className="w-8 h-8" />
                  ) : (
                    <Mic className="w-8 h-8" />
                  )}
                </Button>
                
                <p className="text-sm text-gray-600">
                  {isRecording ? 'Recording... Click to stop' : 'Click to start recording'}
                </p>

                {/* Audio Visualization */}
                {isRecording && (
                  <div className="flex items-center justify-center gap-2">
                    <Volume2 className="w-4 h-4 text-gray-500" />
                    <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 transition-all duration-100"
                        style={{ width: `${Math.min(volumeLevel * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Transcript Card */}
            <Card>
              <CardHeader>
                <CardTitle>Live Transcript</CardTitle>
                <CardDescription>
                  Real-time transcription of your speech
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="min-h-32 p-4 bg-gray-50 rounded-lg">
                  {transcript ? (
                    <p className="text-sm text-gray-800">{transcript}</p>
                  ) : (
                    <p className="text-sm text-gray-500 italic">
                      Start recording to see live transcription...
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - AI Coaching */}
          <div>
            <CoachCard 
              data={coachingData}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </main>
  )
}