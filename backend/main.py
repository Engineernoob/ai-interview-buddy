import os
import logging
from fastapi import FastAPI, WebSocket, File, UploadFile, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import PyPDF2
import io

from utils.errors import (
    AppError, 
    ValidationError, 
    FileProcessingError,
    handle_unexpected_error,
    create_error_response,
    COMMON_ERRORS,
    ErrorCode
)
from utils.config import get_config, validate_required_config, get_service_status
from utils.health import get_health_checker
from utils.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    CacheControlMiddleware
)

from services.transcription import transcribe_segment
from services.intent import detect_intent
from services.retriever import retrieve_context, retriever
from services.llm import generate_suggestions
from services.pdf_parser import extract_pdf_text, validate_pdf_content

# Load environment variables
load_dotenv()

# Load and validate configuration
config = get_config()
config_errors = validate_required_config(config)

if config_errors:
    print("Configuration errors found:")
    for error in config_errors:
        print(f"  - {error}")
    exit(1)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f"Starting AI Interview Buddy API in {config.environment} mode")

# Create FastAPI app
app = FastAPI(
    title="AI Interview Buddy API",
    description="Real-time AI-powered interview assistant with audio processing",
    version="1.0.0",
    debug=config.debug
)

# Add security middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CacheControlMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add operational middleware
if config.environment.value != "testing":
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

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
    # Validate job description
    if not job_description or len(job_description.strip()) < 10:
        raise ValidationError("Job description must be at least 10 characters long", "job_description")
    
    # Validate file size
    resume_content = await resume.read()
    
    if len(resume_content) > config.security.max_file_size:
        raise AppError(
            f"File too large. Maximum size is {config.security.max_file_size // (1024*1024)}MB.",
            ErrorCode.FILE_TOO_LARGE,
            413,
            details={"file_size": len(resume_content), "max_size": config.security.max_file_size}
        )
    
    # Validate PDF before processing
    if resume.content_type != "application/pdf":
        raise COMMON_ERRORS["unsupported_file"]
    
    # Validate PDF content
    is_valid, validation_message = validate_pdf_content(resume_content)
    if not is_valid:
        raise FileProcessingError(
            f"Invalid PDF: {validation_message}",
            filename=resume.filename
        )
    
    # Extract text from PDF resume with multiple methods
    try:
        resume_text = await extract_pdf_text(resume_content, resume.filename or "resume.pdf")
    except Exception as e:
        raise FileProcessingError(
            "Failed to extract text from PDF",
            filename=resume.filename
        ) from e
    
    # Validate extracted text
    if not resume_text or len(resume_text.strip()) < 50:
        raise COMMON_ERRORS["insufficient_text"]
    
    # Store documents in retriever
    try:
        resume_success = retriever.store_resume(resume_text, resume.filename)
        jd_success = retriever.store_job_description(job_description)
        
        if not (resume_success and jd_success):
            raise COMMON_ERRORS["storage_failed"]
        
        return {"message": "Documents uploaded successfully"}
        
    except Exception as e:
        raise AppError(
            "Failed to store documents",
            ErrorCode.STORAGE_ERROR,
            500,
            details={"filename": resume.filename}
        ) from e

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
async def health_check(detailed: bool = False):
    """Comprehensive health check endpoint"""
    health_checker = get_health_checker()
    return await health_checker.check_all(include_details=detailed)

@app.get("/config")
async def get_app_config():
    """Get API configuration"""
    return get_service_status(config)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle application-specific errors."""
    exc.log(logger)
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    exc.log(logger, logging.WARNING)
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    app_error = handle_unexpected_error(exc, f"{request.method} {request.url.path}")
    app_error.log(logger)
    return JSONResponse(
        status_code=app_error.status_code,
        content=create_error_response(app_error)
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Interview Buddy API server...")
    logger.info(f"Using {'Ollama' if config.llm.use_local else 'OpenAI'} for LLM inference")
    logger.info(f"Using Whisper model: {config.whisper.model}")
    logger.info(f"CORS origins: {config.security.cors_origins}")
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.log_level.lower()
    )
