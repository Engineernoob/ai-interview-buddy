# Open Source Setup Guide

This version uses **completely free and open-source** components:
- **Ollama** for local LLM inference (no API keys needed)
- **Whisper** for speech-to-text (runs locally)
- **No external API dependencies**

## Prerequisites

### 1. Install Ollama (Local LLM)
```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai/download
```

### 2. Pull a Language Model
```bash
# Recommended models (choose one):
ollama pull llama2           # 7B model (~4GB) - Good balance
ollama pull llama2:13b       # 13B model (~7GB) - Better quality
ollama pull mistral          # 7B model (~4GB) - Fast and good
ollama pull codellama        # 7B model (~4GB) - Code-focused

# For lower resource usage:
ollama pull llama2:7b-chat-q4_0  # Quantized version (~3.8GB)
```

### 3. System Requirements
- **RAM**: Minimum 8GB (16GB recommended for larger models)
- **Storage**: 4-8GB for model storage
- **CPU**: Any modern CPU (GPU acceleration optional)

## Quick Start

### 1. Setup Project
```bash
# Clone/setup the project
./setup.sh

# Configure environment (no API keys needed!)
cp backend/.env.example backend/.env
```

### 2. Start Ollama
```bash
# Start Ollama server (runs on port 11434)
ollama serve
```

### 3. Start Application
```bash
# In a new terminal
./start-dev.sh
```

### 4. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Ollama: http://localhost:11434

## Configuration Options

### Environment Variables (backend/.env)
```bash
# Enable/disable local LLM
USE_LOCAL_LLM=true

# Ollama configuration
OLLAMA_URL=http://localhost:11434
LLM_MODEL=llama2

# Whisper model size (affects accuracy vs speed)
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large

# CORS
CORS_ORIGINS=http://localhost:3000
```

### Model Options
| Model | Size | RAM | Quality | Speed |
|-------|------|-----|---------|-------|
| llama2 | ~4GB | 8GB+ | Good | Medium |
| llama2:13b | ~7GB | 12GB+ | Better | Slower |
| mistral | ~4GB | 8GB+ | Good | Fast |
| codellama | ~4GB | 8GB+ | Code-focused | Medium |

## Features

### ✅ What Works Without APIs
- Real-time speech transcription (Whisper)
- Question type detection (rule-based)
- Resume/JD analysis (keyword extraction)
- Local LLM coaching suggestions
- Complete offline operation

### 🔧 Fallback Options
- If Ollama is unavailable: Uses intelligent mock responses
- If Whisper fails: Falls back to mock transcription for development
- Progressive enhancement: App works even with limited resources

## Troubleshooting

### Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
killall ollama
ollama serve

# Check available models
ollama list
```

### Memory Issues
```bash
# Use smaller model
ollama pull llama2:7b-chat-q4_0

# Or disable LLM entirely
echo "USE_LOCAL_LLM=false" >> backend/.env
```

### Performance Tuning
```bash
# For faster responses (lower quality)
LLM_MODEL=mistral

# For better quality (slower)
LLM_MODEL=llama2:13b

# Adjust Whisper model
WHISPER_MODEL=small  # tiny < base < small < medium < large
```

## Development Mode

### Mock-Only Mode (No Dependencies)
```bash
# Disable all external services
echo "USE_LOCAL_LLM=false" >> backend/.env

# This will use:
# - Mock transcription responses
# - Rule-based intent detection  
# - Smart mock coaching suggestions
```

### Testing Different Models
```bash
# Switch models on the fly
ollama pull mistral
echo "LLM_MODEL=mistral" >> backend/.env

# Restart backend to pick up changes
```

## Resource Usage

### Minimal Setup
- **Whisper (base)**: ~1GB RAM
- **Backend**: ~100MB RAM
- **Frontend**: ~50MB RAM
- **Total**: ~1.2GB RAM

### With Local LLM
- **+ Llama2**: ~4GB additional RAM
- **Total**: ~5.2GB RAM

### Storage
- **Project**: ~100MB
- **Dependencies**: ~500MB  
- **Whisper models**: ~1GB
- **LLM model**: 3-8GB
- **Total**: 4.5-9.5GB

## Architecture Benefits

### Privacy
- No data sent to external APIs
- All processing happens locally
- Conversations never leave your machine

### Cost
- Zero ongoing costs
- No API rate limits
- No usage quotas

### Reliability
- Works offline
- No external dependencies
- Predictable performance

## Production Deployment

### Docker Option
```bash
# Build with Ollama included
docker-compose up --build

# Or use separate Ollama container
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Server Deployment
```bash
# Install Ollama on server
curl -fsSL https://ollama.ai/install.sh | sh

# Start with systemd
sudo systemctl enable ollama
sudo systemctl start ollama

# Deploy application
./setup.sh
./start-dev.sh
```

This setup gives you a fully functional AI interview assistant without any external API dependencies or costs!