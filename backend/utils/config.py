"""
Configuration management and validation for AI Interview Buddy.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"  
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: Optional[str] = Field(None, description="Database URL")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="interview_buddy", description="Database name")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: Optional[str] = Field(None, description="OpenAI API key")
    model: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    max_tokens: int = Field(default=500, description="Maximum tokens for responses")
    temperature: float = Field(default=0.7, description="Temperature for responses")
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v < 1 or v > 4000:
            raise ValueError('max_tokens must be between 1 and 4000')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('temperature must be between 0 and 2')
        return v


class WhisperConfig(BaseModel):
    """Whisper configuration."""
    model: str = Field(default="base", description="Whisper model size")
    language: Optional[str] = Field(default="en", description="Language for transcription")
    
    @validator('model')
    def validate_model(cls, v):
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if v not in valid_models:
            raise ValueError(f'model must be one of: {", ".join(valid_models)}')
        return v


class LLMConfig(BaseModel):
    """Local LLM configuration."""
    use_local: bool = Field(default=True, description="Use local LLM instead of OpenAI")
    model_name: str = Field(default="llama2", description="Local LLM model name")
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    max_tokens: int = Field(default=500, description="Maximum tokens for responses")
    temperature: float = Field(default=0.7, description="Temperature for responses")


class SecurityConfig(BaseModel):
    """Security configuration."""
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS allowed origins")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    
    @validator('max_file_size')
    def validate_file_size(cls, v):
        if v < 1024 or v > 100 * 1024 * 1024:  # 1KB to 100MB
            raise ValueError('max_file_size must be between 1KB and 100MB')
        return v


class AppConfig(BaseModel):
    """Application configuration."""
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Service configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of: {", ".join(valid_levels)}')
        return v.upper()


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    config_dict = {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8000")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        
        "database": {
            "url": os.getenv("DATABASE_URL"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "name": os.getenv("DB_NAME", "interview_buddy"),
            "username": os.getenv("DB_USERNAME"),
            "password": os.getenv("DB_PASSWORD"),
        },
        
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "500")),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        },
        
        "whisper": {
            "model": os.getenv("WHISPER_MODEL", "base"),
            "language": os.getenv("WHISPER_LANGUAGE", "en"),
        },
        
        "llm": {
            "use_local": os.getenv("USE_LOCAL_LLM", "true").lower() == "true",
            "model_name": os.getenv("LLM_MODEL", "llama2"),
            "ollama_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "500")),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        },
        
        "security": {
            "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
            "max_file_size": int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            "rate_limit_requests": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
        }
    }
    
    try:
        config = AppConfig(**config_dict)
        logger.info(f"Configuration loaded successfully for environment: {config.environment}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def validate_required_config(config: AppConfig) -> List[str]:
    """Validate that required configuration is present."""
    errors = []
    
    # Check API key requirements
    if not config.llm.use_local and not config.openai.api_key:
        errors.append("OPENAI_API_KEY is required when USE_LOCAL_LLM=false")
    
    # Check production-specific requirements
    if config.environment == Environment.PRODUCTION:
        if config.debug:
            errors.append("DEBUG must be false in production")
        
        if "localhost" in config.security.cors_origins:
            errors.append("CORS origins should not include localhost in production")
    
    return errors


def get_service_status(config: AppConfig) -> Dict[str, Any]:
    """Get the status of various services based on configuration."""
    status = {
        "environment": config.environment,
        "debug": config.debug,
        "services": {
            "whisper": {
                "enabled": True,
                "model": config.whisper.model,
                "language": config.whisper.language
            },
            "llm": {
                "use_local": config.llm.use_local,
                "model": config.llm.model_name if config.llm.use_local else config.openai.model,
                "service": "ollama" if config.llm.use_local else "openai"
            },
            "cors": {
                "enabled": True,
                "origins": len(config.security.cors_origins)
            }
        }
    }
    
    # Add database status if configured
    if config.database.url or config.database.username:
        status["services"]["database"] = {
            "configured": True,
            "host": config.database.host,
            "port": config.database.port
        }
    
    return status


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> AppConfig:
    """Reload the configuration from environment variables."""
    global _config
    _config = load_config()
    return _config