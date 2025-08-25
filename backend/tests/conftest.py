import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import tempfile
import os
from io import BytesIO

from main import app
from models import InterviewSession


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create a mock interview session."""
    return InterviewSession(
        session_id="test-session-123",
        started_at="2023-01-01T00:00:00Z",
        is_active=True,
        transcriptions=[],
        ai_responses=[]
    )


@pytest.fixture
def sample_pdf_bytes():
    """Create a sample PDF file as bytes."""
    # Create a minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
271
%%EOF"""
    return pdf_content


@pytest.fixture
def sample_job_description():
    """Sample job description text."""
    return """
    Senior Software Engineer - Full Stack
    
    We are looking for an experienced full-stack developer with expertise in:
    - React and TypeScript
    - Python and FastAPI
    - WebSocket programming
    - Real-time applications
    
    Requirements:
    - 5+ years of experience
    - Strong problem-solving skills
    - Experience with AI/ML integration
    """


@pytest.fixture
def mock_transcription_service():
    """Mock transcription service."""
    mock_service = Mock()
    mock_service.transcribe_audio = AsyncMock(return_value="Hello, this is a test transcription")
    return mock_service


@pytest.fixture
def mock_ai_service():
    """Mock AI service."""
    mock_service = Mock()
    mock_service.generate_response_suggestion = AsyncMock(
        return_value="This is a great question! Consider highlighting your experience with..."
    )
    mock_service.add_to_conversation_history = Mock()
    mock_service.get_conversation_history = Mock(return_value=[])
    mock_service.clear_conversation_history = Mock()
    return mock_service


@pytest.fixture
def mock_retriever():
    """Mock document retriever."""
    mock_retriever = Mock()
    mock_retriever.store_resume = Mock(return_value=True)
    mock_retriever.store_job_description = Mock(return_value=True)
    return mock_retriever


@pytest.fixture
async def websocket_client():
    """Create a WebSocket test client."""
    from fastapi.websockets import WebSocket
    from unittest.mock import AsyncMock
    
    mock_websocket = Mock(spec=WebSocket)
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_text = AsyncMock()
    mock_websocket.receive_bytes = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    return mock_websocket


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        'OPENAI_API_KEY': 'test-key-123',
        'USE_LOCAL_LLM': 'true',
        'WHISPER_MODEL': 'base',
        'LLM_MODEL': 'llama2'
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Write minimal WAV header
        f.write(b'RIFF')
        f.write((44).to_bytes(4, 'little'))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))  # PCM
        f.write((1).to_bytes(2, 'little'))  # Mono
        f.write((44100).to_bytes(4, 'little'))  # Sample rate
        f.write((88200).to_bytes(4, 'little'))  # Byte rate
        f.write((2).to_bytes(2, 'little'))  # Block align
        f.write((16).to_bytes(2, 'little'))  # Bits per sample
        f.write(b'data')
        f.write((8).to_bytes(4, 'little'))
        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')  # 8 bytes of silence
        
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)