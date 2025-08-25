"""
SQLAlchemy models for the AI Interview Buddy application.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, DateTime, Boolean, Text, Integer, Float, 
    ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    """User model for authentication and profile management."""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Profile information
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    notification_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    resumes: Mapped[List["Resume"]] = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="user", cascade="all, delete-orphan"
    )
    job_descriptions: Mapped[List["JobDescription"]] = relationship(
        "JobDescription", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Resume(Base, TimestampMixin):
    """Resume model for storing user resumes."""
    __tablename__ = "resumes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Parsed resume data
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON)
    skills: Mapped[Optional[List[str]]] = mapped_column(JSON)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="resume"
    )
    
    __table_args__ = (
        Index("idx_user_active_resumes", "user_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, title={self.title})>"


class JobDescription(Base, TimestampMixin):
    """Job description model for storing job postings."""
    __tablename__ = "job_descriptions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100))
    job_type: Mapped[Optional[str]] = mapped_column(String(50))  # full-time, part-time, contract, etc.
    
    # Parsed job data
    parsed_skills: Mapped[Optional[List[str]]] = mapped_column(JSON)
    experience_level: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Source information
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_descriptions")
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="job_description"
    )
    
    def __repr__(self) -> str:
        return f"<JobDescription(id={self.id}, title={self.title})>"


class InterviewSession(Base, TimestampMixin):
    """Interview session model for storing interview data."""
    __tablename__ = "interview_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"))
    job_description_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"))
    
    # Session info
    session_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, completed, paused, failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Session configuration
    interview_type: Mapped[str] = mapped_column(String(50), default="general")  # general, technical, behavioral
    difficulty_level: Mapped[str] = mapped_column(String(20), default="medium")  # easy, medium, hard
    
    # Results and analytics
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    total_responses: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[Optional[float]] = mapped_column(Float)
    overall_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Session metadata
    session_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interview_sessions")
    resume: Mapped[Optional["Resume"]] = relationship("Resume", back_populates="interview_sessions")
    job_description: Mapped[Optional["JobDescription"]] = relationship("JobDescription", back_populates="interview_sessions")
    transcriptions: Mapped[List["Transcription"]] = relationship(
        "Transcription", back_populates="session", cascade="all, delete-orphan"
    )
    ai_responses: Mapped[List["AIResponse"]] = relationship(
        "AIResponse", back_populates="session", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_user_session_status", "user_id", "status"),
        Index("idx_session_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<InterviewSession(id={self.id}, name={self.session_name})>"


class Transcription(Base, TimestampMixin):
    """Transcription model for storing speech-to-text results."""
    __tablename__ = "transcriptions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    
    # Transcription data
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    start_time: Mapped[Optional[float]] = mapped_column(Float)
    end_time: Mapped[Optional[float]] = mapped_column(Float)
    duration: Mapped[Optional[float]] = mapped_column(Float)
    
    # Audio metadata
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    audio_format: Mapped[Optional[str]] = mapped_column(String(50))
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Processing info
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    processing_time: Mapped[Optional[float]] = mapped_column(Float)
    
    # Classification
    speaker_type: Mapped[Optional[str]] = mapped_column(String(20))  # interviewer, candidate, system
    content_type: Mapped[Optional[str]] = mapped_column(String(50))  # question, answer, comment, etc.
    
    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="transcriptions")
    
    __table_args__ = (
        Index("idx_session_transcriptions", "session_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Transcription(id={self.id}, session_id={self.session_id})>"


class AIResponse(Base, TimestampMixin):
    """AI response model for storing AI-generated suggestions."""
    __tablename__ = "ai_responses"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    
    # Response data
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    response_type: Mapped[str] = mapped_column(String(50), nullable=False)  # suggestion, feedback, question, etc.
    
    # Original input
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent_detected: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Model info
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    generation_time: Mapped[Optional[float]] = mapped_column(Float)
    
    # Feedback
    user_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 rating from user
    was_helpful: Mapped[Optional[bool]] = mapped_column(Boolean)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="ai_responses")
    
    __table_args__ = (
        Index("idx_session_responses", "session_id", "created_at"),
        Index("idx_response_type", "response_type"),
    )
    
    def __repr__(self) -> str:
        return f"<AIResponse(id={self.id}, type={self.response_type})>"


class UserSession(Base, TimestampMixin):
    """User session model for managing authentication sessions."""
    __tablename__ = "user_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session data
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    device_info: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index("idx_user_active_sessions", "user_id", "is_active"),
        Index("idx_session_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class APIUsage(Base, TimestampMixin):
    """API usage tracking model."""
    __tablename__ = "api_usage"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Request info
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Usage metrics
    request_size: Mapped[Optional[int]] = mapped_column(Integer)
    response_size: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Client info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Error info (if applicable)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (
        Index("idx_user_usage", "user_id", "created_at"),
        Index("idx_endpoint_usage", "endpoint", "created_at"),
        Index("idx_status_code", "status_code"),
    )
    
    def __repr__(self) -> str:
        return f"<APIUsage(id={self.id}, endpoint={self.endpoint})>"