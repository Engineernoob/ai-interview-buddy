import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Home from '@/app/page'

// Mock Next.js router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

// Mock fetch
global.fetch = jest.fn()

describe('Home Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(fetch as jest.Mock).mockClear()
  })

  it('renders the main heading and description', () => {
    render(<Home />)
    
    expect(screen.getByRole('heading', { name: /ai interview buddy/i })).toBeInTheDocument()
    expect(screen.getByText(/upload your resume and job description to get personalized interview coaching/i)).toBeInTheDocument()
  })

  it('renders resume upload section', () => {
    render(<Home />)
    
    expect(screen.getByText(/upload resume/i)).toBeInTheDocument()
    expect(screen.getByText(/upload your resume in pdf format/i)).toBeInTheDocument()
    expect(screen.getByText(/click to upload/i)).toBeInTheDocument()
  })

  it('renders job description section', () => {
    render(<Home />)
    
    expect(screen.getByText(/job description/i)).toBeInTheDocument()
    expect(screen.getByText(/paste the job description to get targeted interview preparation/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/paste the job description here/i)).toBeInTheDocument()
  })

  it('disables start interview button when no resume or job description', () => {
    render(<Home />)
    
    const startButton = screen.getByRole('button', { name: /start interview/i })
    expect(startButton).toBeDisabled()
  })

  it('handles resume file upload', async () => {
    const user = userEvent.setup()
    render(<Home />)
    
    // Create a mock PDF file
    const file = new File(['mock pdf content'], 'resume.pdf', { type: 'application/pdf' })
    
    const fileInput = screen.getByRole('textbox', { hidden: true })
    await user.upload(fileInput, file)
    
    expect(screen.getByText('resume.pdf')).toBeInTheDocument()
  })

  it('rejects non-PDF files', async () => {
    const user = userEvent.setup()
    
    // Mock window.alert
    window.alert = jest.fn()
    
    render(<Home />)
    
    // Create a mock text file
    const file = new File(['mock content'], 'resume.txt', { type: 'text/plain' })
    
    const fileInput = screen.getByRole('textbox', { hidden: true })
    await user.upload(fileInput, file)
    
    expect(window.alert).toHaveBeenCalledWith('Please upload a PDF file')
  })

  it('handles job description input', async () => {
    const user = userEvent.setup()
    render(<Home />)
    
    const textarea = screen.getByPlaceholderText(/paste the job description here/i)
    await user.type(textarea, 'Software Engineer position requiring React and TypeScript experience.')
    
    expect(textarea).toHaveValue('Software Engineer position requiring React and TypeScript experience.')
  })

  it('enables start interview button when both resume and job description are provided', async () => {
    const user = userEvent.setup()
    render(<Home />)
    
    // Upload resume
    const file = new File(['mock pdf content'], 'resume.pdf', { type: 'application/pdf' })
    const fileInput = screen.getByRole('textbox', { hidden: true })
    await user.upload(fileInput, file)
    
    // Add job description
    const textarea = screen.getByPlaceholderText(/paste the job description here/i)
    await user.type(textarea, 'Software Engineer position')
    
    const startButton = screen.getByRole('button', { name: /start interview/i })
    expect(startButton).not.toBeDisabled()
  })

  it('handles successful form submission', async () => {
    const user = userEvent.setup()
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Documents uploaded successfully' })
    })
    
    render(<Home />)
    
    // Upload resume
    const file = new File(['mock pdf content'], 'resume.pdf', { type: 'application/pdf' })
    const fileInput = screen.getByRole('textbox', { hidden: true })
    await user.upload(fileInput, file)
    
    // Add job description
    const textarea = screen.getByPlaceholderText(/paste the job description here/i)
    await user.type(textarea, 'Software Engineer position')
    
    // Submit form
    const startButton = screen.getByRole('button', { name: /start interview/i })
    await user.click(startButton)
    
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/upload',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData)
      })
    )
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/interview')
    })
  })

  it('handles upload failure', async () => {
    const user = userEvent.setup()
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
    })
    
    window.alert = jest.fn()
    
    render(<Home />)
    
    // Upload resume and add job description
    const file = new File(['mock pdf content'], 'resume.pdf', { type: 'application/pdf' })
    const fileInput = screen.getByRole('textbox', { hidden: true })
    await user.upload(fileInput, file)
    
    const textarea = screen.getByPlaceholderText(/paste the job description here/i)
    await user.type(textarea, 'Software Engineer position')
    
    // Submit form
    const startButton = screen.getByRole('button', { name: /start interview/i })
    await user.click(startButton)
    
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Failed to upload documents. Please try again.')
    })
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()
    
    // Mock a delayed response
    ;(fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100))
    )
    
    render(<Home />)
    
    // Upload resume and add job description
    const file = new File(['mock pdf content'], 'resume.pdf', { type: 'application/pdf' })
    const fileInput = screen.getByRole('textbox', { hidden: true })
    await user.upload(fileInput, file)
    
    const textarea = screen.getByPlaceholderText(/paste the job description here/i)
    await user.type(textarea, 'Software Engineer position')
    
    // Submit form
    const startButton = screen.getByRole('button', { name: /start interview/i })
    await user.click(startButton)
    
    // Check loading state
    expect(screen.getByText('Preparing...')).toBeInTheDocument()
    expect(startButton).toBeDisabled()
  })

  it('validates required fields before submission', async () => {
    const user = userEvent.setup()
    window.alert = jest.fn()
    
    render(<Home />)
    
    const startButton = screen.getByRole('button', { name: /start interview/i })
    await user.click(startButton)
    
    expect(window.alert).toHaveBeenCalledWith('Please upload your resume and enter the job description')
    expect(fetch).not.toHaveBeenCalled()
  })
})