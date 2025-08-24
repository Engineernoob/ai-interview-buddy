import asyncio
import tempfile
import os
from typing import Optional
import logging

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: faster-whisper not available. Using mock transcription.")

logger = logging.getLogger(__name__)

def transcribe_segment(audio_buffer: bytes) -> str:
    """
    Transcribe audio segment to text (synchronous interface for backward compatibility)
    """
    service = STTService()
    # Convert to async call
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(service.transcribe_segment(audio_buffer)) or ""

class STTService:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        
        if WHISPER_AVAILABLE:
            self._initialize_model()
        else:
            logger.warning("Whisper not available, using mock transcription")
    
    def _initialize_model(self):
        try:
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            logger.info(f"Whisper model '{self.model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    async def transcribe_segment(self, audio_buffer: bytes) -> Optional[str]:
        """
        Transcribe audio segment to text
        """
        if not WHISPER_AVAILABLE or not self.model:
            # Mock transcription for development
            return await self._mock_transcription(audio_buffer)
        
        try:
            # Save audio buffer to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_buffer)
                temp_file_path = temp_file.name
            
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._transcribe_file, 
                temp_file_path
            )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            return None
    
    def _transcribe_file(self, file_path: str) -> Optional[str]:
        """
        Internal method to transcribe a file using Whisper
        """
        try:
            segments, info = self.model.transcribe(file_path, beam_size=5)
            
            # Combine all segments into one text
            full_text = ""
            for segment in segments:
                full_text += segment.text
            
            return full_text.strip() if full_text.strip() else None
            
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            return None
    
    async def _mock_transcription(self, audio_buffer: bytes) -> Optional[str]:
        """
        Mock transcription for development when Whisper is not available
        """
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Return mock transcription based on buffer size
        buffer_size = len(audio_buffer)
        
        mock_responses = [
            "Tell me about yourself.",
            "What are your greatest strengths?",
            "Why do you want to work here?",
            "Describe a challenging project you worked on.",
            "Where do you see yourself in five years?",
            "What is your biggest weakness?",
            "Why should we hire you?",
            "Tell me about a time you failed.",
            "How do you handle stress and pressure?",
            "Do you have any questions for us?"
        ]
        
        # Use buffer size to deterministically pick a response
        index = (buffer_size // 1000) % len(mock_responses)
        return mock_responses[index]

# Legacy class for backward compatibility
class TranscriptionService(STTService):
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        return await self.transcribe_segment(audio_data)