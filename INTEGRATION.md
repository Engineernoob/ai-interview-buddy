# AI Interview Buddy - Backend-Frontend Integration

## Quick Start

1. **Install dependencies:**
   ```bash
   # Backend setup
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd ..
   
   # Frontend setup
   cd frontend
   npm install
   cd ..
   ```

2. **Start both servers:**
   ```bash
   ./start-dev.sh
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Architecture

### Frontend (Next.js + TypeScript)
- **Port:** 3000
- **WebSocket Client:** Connects to backend WebSocket endpoint
- **Audio Recording:** Captures microphone input and streams to backend
- **UI Components:** Real-time coaching display and interview interface

### Backend (FastAPI + Python)
- **Port:** 8000
- **WebSocket Endpoint:** `/ws/audio` for real-time audio processing
- **AI Integration:** Local LLM (Ollama) or OpenAI for coaching responses
- **Audio Processing:** Whisper for speech-to-text transcription

### Communication Flow

1. **Frontend** captures audio from microphone
2. **Frontend** sends audio data via WebSocket to backend
3. **Backend** processes audio with Whisper (speech-to-text)
4. **Backend** generates coaching tips using AI (LLM)
5. **Backend** sends coaching response back to frontend
6. **Frontend** displays coaching tips and follow-up suggestions

### Message Types

#### Frontend → Backend:
```json
{
  "type": "audio",
  "data": {
    "audio": "base64-encoded-audio-data"
  }
}
```

#### Backend → Frontend:
```json
{
  "type": "coaching",
  "data": {
    "bullets": ["Tip 1", "Tip 2", "Tip 3"],
    "follow_up": "Suggested follow-up question"
  }
}
```

## Configuration

### Backend Environment (.env)
```bash
# Basic Configuration
ENVIRONMENT=development
PORT=8000
DEBUG=true

# LLM Configuration (choose one)
USE_LOCAL_LLM=true
OLLAMA_URL=http://localhost:11434
LLM_MODEL=llama2

# OR use OpenAI
# USE_LOCAL_LLM=false
# OPENAI_API_KEY=your-api-key-here

# Audio Processing
WHISPER_MODEL=base

# CORS for frontend integration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Development Notes

- Backend automatically handles CORS for frontend development
- WebSocket reconnection is handled client-side
- Audio is processed in real-time chunks
- AI responses are generated asynchronously
- Error handling includes graceful fallbacks

## Troubleshooting

### Common Issues:

1. **WebSocket Connection Fails**
   - Ensure backend is running on port 8000
   - Check CORS configuration in backend/.env

2. **No AI Responses**
   - If using Ollama: `ollama run llama2`
   - If using OpenAI: Check API key in backend/.env

3. **Audio Not Recording**
   - Grant microphone permissions in browser
   - Check browser compatibility (HTTPS required for production)

4. **Dependencies Missing**
   - Backend: `pip install -r requirements.txt`
   - Frontend: `npm install`