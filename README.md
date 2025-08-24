# AI Interview Buddy

A real-time AI-powered interview assistant that listens to conversations and provides intelligent response suggestions.

## Features

- 🎤 Real-time audio capture and streaming
- 🤖 AI-powered response suggestions using OpenAI GPT
- 📱 Mobile-friendly PWA interface
- 🔄 WebSocket-based real-time communication
- 🎯 Interview-specific context awareness

## Tech Stack

### Frontend
- Next.js 14 with App Router
- Tailwind CSS for styling
- PWA capabilities
- Real-time audio recording
- WebSocket client

### Backend
- FastAPI for REST API and WebSocket
- OpenAI Whisper for speech-to-text
- OpenAI GPT for response generation
- Python async/await

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.8+
- OpenAI API key

### Setup

1. Clone and setup backend:
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="your-openai-api-key"
uvicorn main:app --reload --port 8000
```

2. Setup frontend:
```bash
cd frontend
npm install
npm run dev
```

3. Open http://localhost:3000

## Usage

1. Open the app in your browser
2. Click "Start Listening" to begin audio capture
3. Speak or let interview audio play
4. View real-time transcription and AI suggestions
5. Use suggestions to improve your responses

## Project Structure

```
ai-interview-buddy/
├── backend/              # FastAPI backend
│   ├── main.py          # Main FastAPI app
│   ├── websocket.py     # WebSocket handlers
│   ├── models.py        # Data models
│   ├── services/        # Business logic
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js frontend
│   ├── app/            # Next.js app router
│   ├── components/     # React components
│   ├── lib/           # Utilities and hooks
│   └── public/        # Static assets
└── README.md
```