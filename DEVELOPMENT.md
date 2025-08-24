# Development Guide

## Architecture Overview

### Backend (FastAPI)
- **FastAPI** web framework with WebSocket support
- **Faster Whisper** for real-time speech-to-text transcription
- **OpenAI GPT** for generating intelligent response suggestions
- **WebSocket** for real-time bidirectional communication

### Frontend (Next.js)
- **Next.js 14** with App Router
- **React** with TypeScript
- **Tailwind CSS** for styling
- **PWA capabilities** for mobile installation
- **Web Audio API** for microphone access and audio processing

### Communication Flow
1. Frontend captures audio from microphone
2. Audio chunks are sent via WebSocket to backend
3. Backend transcribes audio using Whisper
4. Transcription is sent to OpenAI for response suggestions
5. Both transcription and AI suggestions are sent back to frontend
6. Frontend displays results in real-time

## Development Setup

### Prerequisites
- Node.js 18+
- Python 3.8+
- OpenAI API key

### Quick Start
```bash
# Automated setup
./setup.sh

# Start both services
./start-dev.sh
```

### Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenAI API key
python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### REST Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /config` - Configuration details
- `GET /docs` - Interactive API documentation

### WebSocket Endpoint
- `WS /ws` - Main WebSocket connection for audio streaming

### WebSocket Message Types

#### Client to Server
```json
{
  "type": "audio",
  "data": {"audio": "base64-encoded-audio-data"}
}
```

```json
{
  "type": "ping",
  "data": {"timestamp": "2024-01-01T12:00:00Z"}
}
```

```json
{
  "type": "clear_history",
  "data": {}
}
```

#### Server to Client
```json
{
  "type": "transcription",
  "data": {
    "text": "What are your strengths?",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "ai_response",
  "data": {
    "suggestion": "I would say my biggest strengths are...",
    "original_text": "What are your strengths?",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "status",
  "data": {
    "status": "connected",
    "message": "Connected to AI Interview Buddy"
  }
}
```

## File Structure

```
ai-interview-buddy/
├── backend/                 # Python FastAPI backend
│   ├── services/           # Business logic modules
│   │   ├── transcription.py    # Whisper integration
│   │   ├── ai_service.py       # OpenAI integration
│   │   └── __init__.py
│   ├── main.py             # FastAPI application
│   ├── websocket.py        # WebSocket handlers
│   ├── models.py           # Pydantic data models
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
├── frontend/               # Next.js React frontend
│   ├── app/               # Next.js App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/        # React components
│   │   ├── ui/                # Reusable UI components
│   │   └── interview-assistant.tsx  # Main component
│   ├── lib/              # Utilities and hooks
│   │   ├── websocket.ts       # WebSocket client
│   │   ├── audio.ts           # Audio recording/processing
│   │   └── utils.ts           # Helper functions
│   ├── public/           # Static assets
│   │   ├── manifest.json      # PWA manifest
│   │   └── sw.js              # Service worker
│   └── package.json      # Dependencies
├── setup.sh               # Automated setup script
├── start-dev.sh          # Development server script
└── README.md             # Project documentation
```

## Key Features Implementation

### Real-time Audio Processing
- Uses `MediaRecorder` API to capture audio chunks
- Audio is encoded as base64 and sent via WebSocket
- Backend processes 3-second chunks for optimal latency

### Speech-to-Text
- Faster Whisper model runs locally (no external API calls)
- Configurable model size (base, small, medium, large)
- Optimized for interview speech patterns

### AI Response Generation
- OpenAI GPT integration for contextual suggestions
- Maintains conversation history for better responses
- Tailored prompts for interview scenarios

### PWA Features
- Service worker for offline capability
- Web app manifest for mobile installation
- Responsive design for mobile/desktop

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
WHISPER_MODEL=base
CORS_ORIGINS=http://localhost:3000
```

## Performance Considerations

### Audio Processing
- 3-second audio chunks balance latency vs. accuracy
- Audio compression reduces bandwidth usage
- Local Whisper model avoids API rate limits

### Memory Management
- Conversation history limited to 20 messages
- Audio chunks cleared after processing
- WebSocket reconnection with exponential backoff

### Scalability
- Stateless WebSocket handlers
- Session-based audio processing
- Configurable model sizes for different hardware

## Troubleshooting

### Common Issues
1. **Microphone not accessible**: Check browser permissions
2. **WebSocket connection fails**: Ensure backend is running
3. **Transcription not working**: Check Whisper model installation
4. **AI responses failing**: Verify OpenAI API key

### Debug Mode
Enable detailed logging:
```bash
# Backend
export LOG_LEVEL=DEBUG
python main.py

# Frontend
export NODE_ENV=development
npm run dev
```

## Contributing

1. Follow TypeScript/Python typing standards
2. Add error handling for all external API calls
3. Test WebSocket reconnection scenarios
4. Ensure mobile responsiveness
5. Update documentation for new features