import os
import logging
from fastapi import FastAPI, WebSocket, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import PyPDF2
import io

from services.transcription import transcribe_segment
from services.intent import detect_intent
from services.retriever import retrieve_context, retriever
from services.llm import generate_suggestions
from services.pdf_parser import extract_pdf_text, validate_pdf_content

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Interview Buddy API",
    description="Real-time AI-powered interview assistant with audio processing",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AI Interview Buddy API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "websocket": "/ws/audio",
            "upload": "/api/upload",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.post("/api/upload")
async def upload_documents(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    """Upload resume and job description for personalized coaching"""
    try:
        # Validate file size (10MB limit)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        resume_content = await resume.read()
        
        if len(resume_content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={"message": "File too large. Maximum size is 10MB."}
            )
        
        # Validate PDF before processing
        if resume.content_type != "application/pdf":
            return JSONResponse(
                status_code=400,
                content={"message": "Only PDF files are supported for resume upload"}
            )
        
        # Validate PDF content
        is_valid, validation_message = validate_pdf_content(resume_content)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"message": f"Invalid PDF: {validation_message}"}
            )
        
        # Extract text from PDF resume with multiple methods
        resume_text = await extract_pdf_text(resume_content, resume.filename or "resume.pdf")
        
        # Validate extracted text
        if not resume_text or len(resume_text.strip()) < 50:
            return JSONResponse(
                status_code=422,
                content={
                    "message": "Could not extract sufficient text from PDF. Please ensure the PDF contains readable text (not just images)."
                }
            )
        
        # Store documents in retriever
        resume_success = retriever.store_resume(resume_text, resume.filename)
        jd_success = retriever.store_job_description(job_description)
        
        if resume_success and jd_success:
            return {"message": "Documents uploaded successfully"}
        else:
            return JSONResponse(
                status_code=500,
                content={"message": "Failed to store documents"}
            )
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Upload failed: {str(e)}"}
        )

@app.websocket("/ws/audio")
async def audio_socket(ws: WebSocket):
    """WebSocket endpoint for real-time audio processing"""
    await ws.accept()
    buffer = bytearray()
    
    try:
        while True:
            frame = await ws.receive_bytes()
            buffer.extend(frame)
            
            # Process audio when buffer reaches threshold
            if len(buffer) > 32000:  # ~2 seconds at 16kHz
                try:
                    # Transcribe audio
                    text = transcribe_segment(bytes(buffer))
                    buffer.clear()
                    
                    if text and len(text.strip()) > 0:
                        # Detect intent
                        intent = detect_intent(text)
                        
                        # Retrieve context
                        ctx = retrieve_context(text, intent)
                        
                        # Generate suggestions
                        tips = generate_suggestions(text, intent, ctx)
                        
                        # Add transcript to response
                        tips["transcript"] = text
                        
                        # Send response
                        await ws.send_json(tips)
                        
                except Exception as e:
                    logger.error(f"Audio processing error: {e}")
                    await ws.send_json({
                        "bullets": ["Error processing audio"],
                        "follow_up": None,
                        "error": str(e)
                    })
                    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
    
    return {
        "status": "healthy",
        "message": "All systems operational",
        "services": {
            "local_llm": "enabled" if use_local_llm else "disabled",
            "whisper": "available",
            "websocket": "available",
            "document_upload": "available"
        }
    }

@app.get("/config")
async def get_config():
    """Get API configuration"""
    return {
        "whisper_model": os.getenv("WHISPER_MODEL", "base"),
        "llm_model": os.getenv("LLM_MODEL", "llama2"),
        "use_local_llm": os.getenv("USE_LOCAL_LLM", "true").lower() == "true",
        "websocket_url": "/ws/audio",
        "features": [
            "real_time_transcription",
            "local_llm_coaching", 
            "resume_upload",
            "job_description_analysis",
            "intent_detection"
        ]
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Interview Buddy API server with free/open-source components...")
    logger.info("Using Ollama for local LLM inference")
    logger.info("Using Whisper for speech recognition")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
