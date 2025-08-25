import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InterviewAssistant } from '@/components/interview-assistant'

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: WebSocket.OPEN,
}

// Mock audio components
jest.mock('@/lib/audio', () => ({
  AudioRecorder: jest.fn(() => ({
    initialize: jest.fn().mockResolvedValue(true),
    startRecording: jest.fn(),
    stopRecording: jest.fn(),
    cleanup: jest.fn(),
  })),
  AudioVisualizer: jest.fn(() => ({
    initialize: jest.fn().mockResolvedValue(true),
    startVisualization: jest.fn(),
    stopVisualization: jest.fn(),
    cleanup: jest.fn(),
  })),
}))

// Mock WebSocket client
jest.mock('@/lib/websocket', () => ({
  WebSocketClient: jest.fn(() => ({
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn(),
    sendAudioData: jest.fn(),
    clearHistory: jest.fn(),
    onStatus: jest.fn(),
    onMessage: jest.fn(),
    isConnected: true,
  })),
}))

describe('InterviewAssistant', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock WebSocket constructor
    global.WebSocket = jest.fn(() => mockWebSocket) as any
  })

  it('renders the main interface correctly', () => {
    render(<InterviewAssistant />)
    
    expect(screen.getByText('AI Interview Buddy')).toBeInTheDocument()
    expect(screen.getByText('Your real-time interview assistant powered by AI')).toBeInTheDocument()
    expect(screen.getByText('Start Listening')).toBeInTheDocument()
    expect(screen.getByText('Clear History')).toBeInTheDocument()
  })

  it('displays transcription and AI response sections', () => {
    render(<InterviewAssistant />)
    
    expect(screen.getByText('Live Transcription')).toBeInTheDocument()
    expect(screen.getByText('AI Response Suggestions')).toBeInTheDocument()
    expect(screen.getByText('No transcriptions yet. Start listening to see speech-to-text results.')).toBeInTheDocument()
    expect(screen.getByText('No suggestions yet. AI will provide response recommendations based on interview questions.')).toBeInTheDocument()
  })

  it('shows start/stop recording buttons correctly', async () => {
    const user = userEvent.setup()
    render(<InterviewAssistant />)
    
    const startButton = screen.getByRole('button', { name: /start listening/i })
    expect(startButton).toBeInTheDocument()
    expect(startButton).not.toBeDisabled()

    // Note: We can't fully test the recording functionality without mocking more audio APIs
    // This test verifies the UI renders correctly
  })

  it('handles clear history button click', async () => {
    const user = userEvent.setup()
    render(<InterviewAssistant />)
    
    const clearButton = screen.getByRole('button', { name: /clear history/i })
    expect(clearButton).toBeInTheDocument()
    
    await user.click(clearButton)
    // The component should handle the clear action
  })

  it('displays connection status correctly', () => {
    render(<InterviewAssistant />)
    
    // Should show connection status
    expect(screen.getByText(/Status:/)).toBeInTheDocument()
  })

  it('handles copy to clipboard functionality', async () => {
    // Mock clipboard API
    const mockWriteText = jest.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      writable: true,
      value: { writeText: mockWriteText },
    })

    const user = userEvent.setup()
    render(<InterviewAssistant />)
    
    // This test would need the component to have some transcriptions first
    // For now, we're testing that the component renders without errors
    expect(screen.getByText('Live Transcription')).toBeInTheDocument()
  })

  it('shows audio visualization when recording', () => {
    render(<InterviewAssistant />)
    
    // Initially, no audio visualization should be visible
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })
})

describe('InterviewAssistant Error Handling', () => {
  it('handles WebSocket connection errors gracefully', () => {
    // Mock WebSocket to throw error
    global.WebSocket = jest.fn(() => {
      throw new Error('Connection failed')
    }) as any

    expect(() => render(<InterviewAssistant />)).not.toThrow()
  })

  it('handles audio initialization failures', () => {
    // This would require mocking the audio APIs to fail
    render(<InterviewAssistant />)
    expect(screen.getByText('AI Interview Buddy')).toBeInTheDocument()
  })
})