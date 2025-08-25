import pytest
import json
import base64
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from main import app
from websocket import ConnectionManager, manager


class TestWebSocketIntegration:
    """Test WebSocket integration."""
    
    @pytest.fixture
    def websocket_client(self):
        """Create WebSocket test client."""
        return TestClient(app)

    @patch('websocket.manager.transcription_service')
    @patch('websocket.manager.ai_service')
    def test_websocket_connection_flow(self, mock_ai_service, mock_transcription_service, websocket_client):
        """Test complete WebSocket connection flow."""
        # Mock services
        mock_transcription_service.transcribe_audio = AsyncMock(return_value="Test transcription")
        mock_ai_service.generate_response_suggestion = AsyncMock(return_value="Test AI response")
        
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert data["data"]["status"] == "connected"
            assert "session_id" in data["data"]

    @patch('websocket.manager.transcription_service')
    @patch('websocket.manager.ai_service')
    def test_websocket_audio_processing(self, mock_ai_service, mock_transcription_service, websocket_client):
        """Test WebSocket audio processing."""
        # Mock services
        mock_transcription_service.transcribe_audio = AsyncMock(return_value="Hello world")
        mock_ai_service.generate_response_suggestion = AsyncMock(return_value="Great response!")
        
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send audio message
            audio_data = base64.b64encode(b"fake_audio_data").decode()
            message = {
                "type": "audio",
                "data": {"audio": audio_data}
            }
            websocket.send_json(message)
            
            # Should receive status message (transcribing)
            status_msg = websocket.receive_json()
            assert status_msg["type"] == "status"
            assert "transcribing" in status_msg["data"]["status"] or "Processing" in status_msg["data"]["message"]
            
            # Should receive transcription
            transcription_msg = websocket.receive_json()
            assert transcription_msg["type"] == "transcription"
            assert transcription_msg["data"]["text"] == "Hello world"
            
            # Should receive status message (generating)
            status_msg2 = websocket.receive_json()
            assert status_msg2["type"] == "status"
            assert "generating" in status_msg2["data"]["status"] or "Generating" in status_msg2["data"]["message"]
            
            # Should receive AI response
            ai_msg = websocket.receive_json()
            assert ai_msg["type"] == "ai_response"
            assert ai_msg["data"]["suggestion"] == "Great response!"

    def test_websocket_ping_pong(self, websocket_client):
        """Test WebSocket ping-pong functionality."""
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send ping
            ping_message = {
                "type": "ping",
                "data": {"timestamp": "2023-01-01T00:00:00Z"}
            }
            websocket.send_json(ping_message)
            
            # Should receive pong
            pong_msg = websocket.receive_json()
            assert pong_msg["type"] == "pong"
            assert "timestamp" in pong_msg["data"]

    @patch('websocket.manager.ai_service')
    def test_websocket_clear_history(self, mock_ai_service, websocket_client):
        """Test WebSocket clear history functionality."""
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send clear history message
            clear_message = {
                "type": "clear_history",
                "data": {}
            }
            websocket.send_json(clear_message)
            
            # Should receive confirmation
            response = websocket.receive_json()
            assert response["type"] == "status"
            assert "history_cleared" in response["data"]["status"]
            
            # Verify service was called
            mock_ai_service.clear_conversation_history.assert_called_once()

    def test_websocket_invalid_message_type(self, websocket_client):
        """Test WebSocket handles invalid message types."""
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send invalid message type
            invalid_message = {
                "type": "invalid_type",
                "data": {}
            }
            websocket.send_json(invalid_message)
            
            # Should receive error message
            error_msg = websocket.receive_json()
            assert error_msg["type"] == "error"
            assert "Unknown message type" in error_msg["data"]["message"]

    def test_websocket_invalid_json(self, websocket_client):
        """Test WebSocket handles invalid JSON."""
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send invalid JSON
            websocket.send_text("invalid json{}")
            
            # Should receive error message
            error_msg = websocket.receive_json()
            assert error_msg["type"] == "error"
            assert "Invalid JSON format" in error_msg["data"]["message"]

    @patch('websocket.manager.transcription_service')
    def test_websocket_audio_processing_no_speech(self, mock_transcription_service, websocket_client):
        """Test WebSocket audio processing when no speech detected."""
        # Mock transcription service to return None (no speech)
        mock_transcription_service.transcribe_audio = AsyncMock(return_value=None)
        
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send audio message
            audio_data = base64.b64encode(b"silent_audio_data").decode()
            message = {
                "type": "audio",
                "data": {"audio": audio_data}
            }
            websocket.send_json(message)
            
            # Should receive status message (transcribing)
            status_msg = websocket.receive_json()
            assert status_msg["type"] == "status"
            
            # Should receive no speech detected message
            no_speech_msg = websocket.receive_json()
            assert no_speech_msg["type"] == "status"
            assert "no_speech" in no_speech_msg["data"]["status"] or "No speech detected" in no_speech_msg["data"]["message"]

    def test_websocket_invalid_audio_data(self, websocket_client):
        """Test WebSocket handles invalid audio data."""
        with websocket_client.websocket_connect("/ws/audio") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send message with invalid audio data
            message = {
                "type": "audio",
                "data": {"audio": "invalid_base64!!!"}
            }
            websocket.send_json(message)
            
            # Should receive error message
            error_msg = websocket.receive_json()
            assert error_msg["type"] == "error"
            assert "Invalid audio data" in error_msg["data"]["message"]


class TestConnectionManager:
    """Test ConnectionManager class directly."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()
        return mock_ws
    
    async def test_connect_creates_session(self, manager, mock_websocket):
        """Test that connect creates a new session."""
        session_id = await manager.connect(mock_websocket)
        
        assert session_id in manager.active_connections
        assert session_id in manager.sessions
        assert manager.sessions[session_id].is_active is True
        mock_websocket.accept.assert_called_once()

    async def test_disconnect_cleanup(self, manager, mock_websocket):
        """Test that disconnect properly cleans up."""
        session_id = await manager.connect(mock_websocket)
        manager.disconnect(session_id)
        
        assert session_id not in manager.active_connections
        assert manager.sessions[session_id].is_active is False

    async def test_send_message(self, manager, mock_websocket):
        """Test sending messages to connected clients."""
        session_id = await manager.connect(mock_websocket)
        
        test_message = {"type": "test", "data": {"content": "hello"}}
        await manager.send_message(session_id, test_message)
        
        mock_websocket.send_text.assert_called_once_with(json.dumps(test_message))

    async def test_send_message_to_disconnected_client(self, manager, mock_websocket):
        """Test sending message to disconnected client."""
        session_id = await manager.connect(mock_websocket)
        manager.disconnect(session_id)
        
        test_message = {"type": "test", "data": {"content": "hello"}}
        await manager.send_message(session_id, test_message)
        
        # Should not attempt to send
        mock_websocket.send_text.assert_not_called()

    @patch('websocket.logger')
    async def test_send_message_error_handling(self, mock_logger, manager, mock_websocket):
        """Test error handling when sending messages fails."""
        session_id = await manager.connect(mock_websocket)
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        
        test_message = {"type": "test", "data": {"content": "hello"}}
        await manager.send_message(session_id, test_message)
        
        # Should log error and disconnect
        mock_logger.error.assert_called()
        assert session_id not in manager.active_connections