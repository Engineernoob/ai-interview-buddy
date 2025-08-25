import pytest
from datetime import datetime
from pydantic import ValidationError

from models import (
    AudioChunk,
    TranscriptionResult,
    AIResponse,
    InterviewSession,
    WebSocketMessage
)


class TestModels:
    """Test Pydantic models."""
    
    def test_audio_chunk_model(self):
        """Test AudioChunk model validation."""
        chunk = AudioChunk(
            audio_data=b"sample_audio_data",
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        assert isinstance(chunk.audio_data, bytes)
        assert isinstance(chunk.timestamp, datetime)
        assert chunk.session_id == "test-session-123"

    def test_audio_chunk_validation_error(self):
        """Test AudioChunk model validation with invalid data."""
        with pytest.raises(ValidationError):
            AudioChunk(
                audio_data="invalid_bytes",  # Should be bytes
                timestamp=datetime.now(),
                session_id="test-session-123"
            )

    def test_transcription_result_model(self):
        """Test TranscriptionResult model validation."""
        result = TranscriptionResult(
            text="Hello, this is a test transcription",
            confidence=0.95,
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        assert result.text == "Hello, this is a test transcription"
        assert result.confidence == 0.95
        assert isinstance(result.timestamp, datetime)
        assert result.session_id == "test-session-123"

    def test_transcription_result_confidence_validation(self):
        """Test TranscriptionResult confidence validation."""
        # Valid confidence values
        for confidence in [0.0, 0.5, 1.0]:
            result = TranscriptionResult(
                text="Test text",
                confidence=confidence,
                timestamp=datetime.now(),
                session_id="test-session"
            )
            assert result.confidence == confidence

    def test_ai_response_model(self):
        """Test AIResponse model validation."""
        response = AIResponse(
            suggestion="This is a great question! You should highlight your experience with...",
            context="Interview question about technical skills",
            confidence=0.85,
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        assert "great question" in response.suggestion
        assert response.context == "Interview question about technical skills"
        assert response.confidence == 0.85
        assert isinstance(response.timestamp, datetime)
        assert response.session_id == "test-session-123"

    def test_interview_session_model(self):
        """Test InterviewSession model validation."""
        session = InterviewSession(
            session_id="test-session-123",
            started_at=datetime.now(),
            is_active=True
        )
        
        assert session.session_id == "test-session-123"
        assert isinstance(session.started_at, datetime)
        assert session.is_active is True
        assert session.transcriptions == []
        assert session.ai_responses == []

    def test_interview_session_with_data(self):
        """Test InterviewSession with transcriptions and responses."""
        transcription = TranscriptionResult(
            text="Test transcription",
            confidence=0.9,
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        ai_response = AIResponse(
            suggestion="Test suggestion",
            context="Test context",
            confidence=0.8,
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        session = InterviewSession(
            session_id="test-session-123",
            started_at=datetime.now(),
            is_active=True,
            transcriptions=[transcription],
            ai_responses=[ai_response]
        )
        
        assert len(session.transcriptions) == 1
        assert len(session.ai_responses) == 1
        assert session.transcriptions[0].text == "Test transcription"
        assert session.ai_responses[0].suggestion == "Test suggestion"

    def test_websocket_message_model(self):
        """Test WebSocketMessage model validation."""
        message = WebSocketMessage(
            type="transcription",
            data={"text": "Hello world", "confidence": 0.95},
            session_id="test-session-123",
            timestamp=datetime.now()
        )
        
        assert message.type == "transcription"
        assert message.data["text"] == "Hello world"
        assert message.session_id == "test-session-123"
        assert isinstance(message.timestamp, datetime)

    def test_websocket_message_without_optional_fields(self):
        """Test WebSocketMessage with only required fields."""
        message = WebSocketMessage(
            type="status",
            data={"status": "connected"},
            timestamp=datetime.now()
        )
        
        assert message.type == "status"
        assert message.data["status"] == "connected"
        assert message.session_id is None

    def test_websocket_message_types(self):
        """Test different WebSocket message types."""
        message_types = ['audio', 'transcription', 'ai_response', 'error', 'status']
        
        for msg_type in message_types:
            message = WebSocketMessage(
                type=msg_type,
                data={"test": "data"},
                timestamp=datetime.now()
            )
            assert message.type == msg_type

    def test_model_serialization(self):
        """Test model serialization to dict/JSON."""
        transcription = TranscriptionResult(
            text="Test transcription",
            confidence=0.9,
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        data = transcription.model_dump()
        assert isinstance(data, dict)
        assert data["text"] == "Test transcription"
        assert data["confidence"] == 0.9
        assert data["session_id"] == "test-session-123"

    def test_model_json_serialization(self):
        """Test model JSON serialization."""
        ai_response = AIResponse(
            suggestion="Test suggestion",
            context="Test context",
            confidence=0.8,
            timestamp=datetime.now(),
            session_id="test-session-123"
        )
        
        json_str = ai_response.model_dump_json()
        assert isinstance(json_str, str)
        assert "Test suggestion" in json_str
        assert "test-session-123" in json_str

    def test_model_validation_errors(self):
        """Test various model validation errors."""
        # Test missing required field
        with pytest.raises(ValidationError):
            TranscriptionResult(
                confidence=0.9,
                timestamp=datetime.now(),
                session_id="test-session-123"
                # Missing 'text' field
            )

        # Test invalid data type
        with pytest.raises(ValidationError):
            AIResponse(
                suggestion="Test suggestion",
                context="Test context",
                confidence="invalid_float",  # Should be float
                timestamp=datetime.now(),
                session_id="test-session-123"
            )

        # Test invalid timestamp
        with pytest.raises(ValidationError):
            WebSocketMessage(
                type="test",
                data={},
                timestamp="invalid_datetime"  # Should be datetime
            )