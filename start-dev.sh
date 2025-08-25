#!/bin/bash

echo "🚀 Starting AI Interview Buddy in development mode..."

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found. Please run setup.sh first."
    exit 1
fi

# Check LLM configuration
if grep -q "USE_LOCAL_LLM=true" backend/.env; then
    echo "📋 Using local LLM (Ollama) - make sure Ollama is running"
    echo "   If Ollama is not installed, run: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   Then run: ollama run llama2"
elif ! grep -q "OPENAI_API_KEY=" backend/.env || grep -q "OPENAI_API_KEY=your-openai-api-key-here" backend/.env; then
    echo "❌ Neither local LLM nor OpenAI API key configured."
    echo "   Please either:"
    echo "   1. Set USE_LOCAL_LLM=true and install Ollama, or"
    echo "   2. Add your OpenAI API key to backend/.env"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📦 Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || echo "⚠️  Virtual environment not found, using system Python"
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

echo "🎨 Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Services started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait