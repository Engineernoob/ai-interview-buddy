from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AudioChunk(BaseModel):
    audio_data: bytes
    timestamp: datetime
    session_id: str

class TranscriptionResult(BaseModel):
    text: str
    confidence: float
    timestamp: datetime
    session_id: str

class AIResponse(BaseModel):
    suggestion: str
    context: str
    confidence: float
    timestamp: datetime
    session_id: str

class InterviewSession(BaseModel):
    session_id: str
    started_at: datetime
    is_active: bool
    transcriptions: List[TranscriptionResult] = []
    ai_responses: List[AIResponse] = []

class WebSocketMessage(BaseModel):
    type: str  # 'audio', 'transcription', 'ai_response', 'error', 'status'
    data: dict
    session_id: Optional[str] = None
    timestamp: datetime