"""
Centralized error handling utilities for the AI Interview Buddy backend.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard error codes for the application."""
    
    # Client errors (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    INSUFFICIENT_TEXT = "INSUFFICIENT_TEXT"
    INVALID_PDF = "INVALID_PDF"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    WEBSOCKET_ERROR = "WEBSOCKET_ERROR"
    
    # Audio processing errors
    AUDIO_PROCESSING_ERROR = "AUDIO_PROCESSING_ERROR"
    MICROPHONE_ERROR = "MICROPHONE_ERROR"
    
    # External service errors
    OPENAI_API_ERROR = "OPENAI_API_ERROR"
    WHISPER_ERROR = "WHISPER_ERROR"


class AppError(Exception):
    """Base application error class."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        error_dict = {
            "message": self.message,
            "code": self.code.value,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.details:
            error_dict["details"] = self.details
            
        return error_dict

    def log(self, logger: logging.Logger, level: int = logging.ERROR):
        """Log the error with appropriate context."""
        logger.log(
            level,
            f"AppError [{self.code.value}]: {self.message}",
            extra={
                "error_code": self.code.value,
                "status_code": self.status_code,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
                "cause": str(self.cause) if self.cause else None
            },
            exc_info=self.cause
        )


class ValidationError(AppError):
    """Error for input validation failures."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
            
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details
        )


class FileProcessingError(AppError):
    """Error for file processing failures."""
    
    def __init__(self, message: str, filename: Optional[str] = None, file_size: Optional[int] = None):
        details = {}
        if filename:
            details["filename"] = filename
        if file_size:
            details["file_size"] = file_size
            
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_PDF,
            status_code=422,
            details=details
        )


class ServiceError(AppError):
    """Error for external service failures."""
    
    def __init__(
        self, 
        message: str, 
        service: str, 
        code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
        status_code: int = 503,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details={"service": service},
            cause=cause
        )


class TranscriptionError(ServiceError):
    """Error for transcription service failures."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            service="transcription",
            code=ErrorCode.TRANSCRIPTION_FAILED,
            cause=cause
        )


class AIServiceError(ServiceError):
    """Error for AI service failures."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            service="ai_response",
            code=ErrorCode.AI_SERVICE_ERROR,
            cause=cause
        )


class WebSocketError(AppError):
    """Error for WebSocket operations."""
    
    def __init__(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        details = {}
        if session_id:
            details["session_id"] = session_id
            
        super().__init__(
            message=message,
            code=ErrorCode.WEBSOCKET_ERROR,
            status_code=500,
            details=details,
            cause=cause
        )


def handle_unexpected_error(error: Exception, context: str = "") -> AppError:
    """Convert unexpected errors to AppError instances."""
    logger.error(
        f"Unexpected error in {context}: {str(error)}",
        exc_info=True
    )
    
    return AppError(
        message=f"An unexpected error occurred{': ' + context if context else ''}",
        code=ErrorCode.INTERNAL_ERROR,
        status_code=500,
        details={"context": context} if context else None,
        cause=error
    )


def log_error(error: Exception, context: str = "", level: int = logging.ERROR):
    """Log error with full context and stack trace."""
    logger.log(
        level,
        f"Error in {context}: {str(error)}",
        extra={
            "context": context,
            "error_type": type(error).__name__,
            "stack_trace": traceback.format_exc()
        },
        exc_info=True
    )


def create_error_response(error: AppError) -> Dict[str, Any]:
    """Create standardized error response."""
    response = {
        "error": error.to_dict()
    }
    
    # Add request ID if available (would be set by middleware)
    # if hasattr(error, 'request_id'):
    #     response["request_id"] = error.request_id
    
    return response


# Common error instances for reuse
COMMON_ERRORS = {
    "file_too_large": AppError(
        "File too large. Maximum size is 10MB.",
        ErrorCode.FILE_TOO_LARGE,
        413
    ),
    "unsupported_file": AppError(
        "Only PDF files are supported for resume upload",
        ErrorCode.UNSUPPORTED_FILE_TYPE,
        400
    ),
    "insufficient_text": AppError(
        "Could not extract sufficient text from PDF. Please ensure the PDF contains readable text (not just images).",
        ErrorCode.INSUFFICIENT_TEXT,
        422
    ),
    "storage_failed": AppError(
        "Failed to store documents",
        ErrorCode.STORAGE_ERROR,
        500
    ),
    "transcription_unavailable": ServiceError(
        "Transcription service is currently unavailable",
        "transcription",
        ErrorCode.TRANSCRIPTION_FAILED
    ),
    "ai_service_unavailable": ServiceError(
        "AI response service is currently unavailable",
        "ai_response", 
        ErrorCode.AI_SERVICE_ERROR
    )
}