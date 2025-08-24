import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging

from models import WebSocketMessage, InterviewSession
from services import TranscriptionService, AIService

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, InterviewSession] = {}
        self.transcription_service = TranscriptionService()
        self.ai_service = AIService()
    
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        
        self.active_connections[session_id] = websocket
        self.sessions[session_id] = InterviewSession(
            session_id=session_id,
            started_at=datetime.now(),
            is_active=True
        )
        
        logger.info(f"WebSocket connected: session {session_id}")
        
        # Send connection confirmation
        await self.send_message(session_id, {
            "type": "status",
            "data": {
                "status": "connected",
                "session_id": session_id,
                "message": "Connected to AI Interview Buddy"
            }
        })
        
        return session_id
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
        
        logger.info(f"WebSocket disconnected: session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def handle_audio_data(self, session_id: str, audio_data: bytes):
        try:
            # Transcribe audio
            await self.send_message(session_id, {
                "type": "status",
                "data": {"status": "transcribing", "message": "Processing audio..."}
            })
            
            transcription = await self.transcription_service.transcribe_audio(audio_data)
            
            if transcription:
                # Send transcription result
                await self.send_message(session_id, {
                    "type": "transcription",
                    "data": {
                        "text": transcription,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                # Add to conversation history
                self.ai_service.add_to_conversation_history(transcription)
                
                # Generate AI response
                await self.send_message(session_id, {
                    "type": "status",
                    "data": {"status": "generating", "message": "Generating response suggestion..."}
                })
                
                ai_suggestion = await self.ai_service.generate_response_suggestion(
                    transcription,
                    conversation_history=self.ai_service.get_conversation_history()
                )
                
                if ai_suggestion:
                    await self.send_message(session_id, {
                        "type": "ai_response",
                        "data": {
                            "suggestion": ai_suggestion,
                            "original_text": transcription,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                else:
                    await self.send_message(session_id, {
                        "type": "error",
                        "data": {"message": "Failed to generate AI response"}
                    })
            else:
                await self.send_message(session_id, {
                    "type": "status",
                    "data": {"status": "no_speech", "message": "No speech detected in audio"}
                })
                
        except Exception as e:
            logger.error(f"Audio processing error for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "data": {"message": f"Audio processing failed: {str(e)}"}
            })
    
    async def handle_message(self, session_id: str, message: dict):
        message_type = message.get("type")
        
        if message_type == "audio":
            # Expect audio data in base64 format
            import base64
            try:
                audio_data = base64.b64decode(message["data"]["audio"])
                await self.handle_audio_data(session_id, audio_data)
            except Exception as e:
                await self.send_message(session_id, {
                    "type": "error",
                    "data": {"message": f"Invalid audio data: {str(e)}"}
                })
        
        elif message_type == "ping":
            await self.send_message(session_id, {
                "type": "pong",
                "data": {"timestamp": datetime.now().isoformat()}
            })
        
        elif message_type == "clear_history":
            self.ai_service.clear_conversation_history()
            await self.send_message(session_id, {
                "type": "status",
                "data": {"status": "history_cleared", "message": "Conversation history cleared"}
            })
        
        else:
            await self.send_message(session_id, {
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"}
            })

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.handle_message(session_id, message)
            except json.JSONDecodeError:
                await manager.send_message(session_id, {
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)