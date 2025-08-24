#!/bin/bash

echo "🚀 Starting AI Interview Buddy with comprehensive checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    case $2 in
        "error") echo -e "${RED}❌ $1${NC}" ;;
        "success") echo -e "${GREEN}✅ $1${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $1${NC}" ;;
        "info") echo -e "${BLUE}ℹ️  $1${NC}" ;;
        *) echo "• $1" ;;
    esac
}

# Function to cleanup processes
cleanup() {
    print_status "Shutting down services..." "info"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    if [ ! -z "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Phase 1: Environment Validation" "info"

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    print_status "Creating backend/.env from template..." "warning"
    cp backend/.env.example backend/.env
    print_status "Created backend/.env - you can customize it if needed" "success"
fi

# Check Python virtual environment
if [ ! -d "backend/venv" ]; then
    print_status "Python virtual environment not found, creating..." "warning"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    print_status "Python environment created and dependencies installed" "success"
else
    print_status "Python virtual environment found" "success"
fi

# Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    print_status "Frontend dependencies not found, installing..." "warning"
    cd frontend
    npm install
    cd ..
    print_status "Frontend dependencies installed" "success"
else
    print_status "Frontend dependencies found" "success"
fi

print_status "Phase 2: Ollama Setup" "info"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    print_status "Ollama not found. Installing Ollama..." "warning"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        print_status "Please install Ollama manually from https://ollama.ai/" "error"
        exit 1
    fi
    
    print_status "Ollama installed" "success"
else
    print_status "Ollama found" "success"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_status "Starting Ollama server..." "info"
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to start
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_status "Ollama server started" "success"
            break
        fi
        if [ $i -eq 30 ]; then
            print_status "Ollama server failed to start" "error"
            exit 1
        fi
        sleep 1
    done
else
    print_status "Ollama server already running" "success"
fi

# Check for models
print_status "Checking for language models..." "info"
if ! ollama list | grep -q "llama2\|mistral\|tinyllama"; then
    print_status "No suitable models found. Installing a lightweight model..." "warning"
    
    # Try to install tinyllama first (smallest)
    print_status "Installing tinyllama (1.1GB)..." "info"
    if ollama pull tinyllama; then
        print_status "tinyllama installed successfully" "success"
    else
        print_status "Failed to install tinyllama, trying llama2..." "warning"
        if ollama pull llama2:7b-chat-q4_0; then
            print_status "llama2 quantized model installed successfully" "success"
        else
            print_status "Failed to install any models. Will use mock responses." "warning"
            echo "USE_LOCAL_LLM=false" >> backend/.env
        fi
    fi
else
    print_status "Language models found" "success"
fi

print_status "Phase 3: Service Health Checks" "info"

# Test Python imports
cd backend
source venv/bin/activate

if python -c "
import sys
sys.path.insert(0, '.')
try:
    from services.transcription import transcribe_segment
    from services.intent import detect_intent  
    from services.retriever import retrieve_context
    from services.llm import generate_suggestions
    print('✅ All Python imports working')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"; then
    print_status "Python backend imports validated" "success"
else
    print_status "Python backend import issues found" "error"
    exit 1
fi

cd ..

# Test frontend build
cd frontend
if npm run build --silent; then
    print_status "Frontend builds successfully" "success"
else
    print_status "Frontend build issues found" "error"
    exit 1
fi
cd ..

print_status "Phase 4: Starting Services" "info"

# Start backend
print_status "Starting backend server..." "info"
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check backend health
for i in {1..10}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_status "Backend server started successfully" "success"
        break
    fi
    if [ $i -eq 10 ]; then
        print_status "Backend server failed to start" "error"
        cleanup
        exit 1
    fi
    sleep 1
done

# Start frontend
print_status "Starting frontend development server..." "info"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

print_status "Phase 5: Final Checks" "info"

# Check all services are running
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_status "Backend API: http://localhost:8000" "success"
else
    print_status "Backend health check failed" "error"
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
    print_status "Frontend: http://localhost:3000" "success"
else
    print_status "Frontend not accessible" "error"
fi

if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_status "Ollama API: http://localhost:11434" "success"
else
    print_status "Ollama not accessible" "error"
fi

print_status "🎉 AI Interview Buddy is ready!" "success"
echo ""
echo "📋 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Upload a PDF resume and job description"
echo "   3. Start the interview mode and test microphone"
echo "   4. Speak to test real-time transcription and AI coaching"
echo ""
echo "🔧 Troubleshooting:"
echo "   • If microphone doesn't work, ensure you're on HTTPS or localhost"
echo "   • If AI responses are slow, the model is downloading/loading"
echo "   • If PDF upload fails, ensure the PDF contains readable text"
echo "   • Press Ctrl+C to stop all services"
echo ""
print_status "All services running. Press Ctrl+C to stop." "info"

# Wait for processes
wait