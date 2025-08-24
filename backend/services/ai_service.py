import os
from openai import AsyncOpenAI
from typing import Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.conversation_history = []
    
    async def generate_response_suggestion(
        self, 
        transcribed_text: str, 
        context: str = "job interview",
        conversation_history: List[str] = None
    ) -> Optional[str]:
        try:
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an AI interview coach assistant. You help job candidates during interviews by providing intelligent response suggestions.

Context: The user is in a {context} setting.

Your role:
1. Analyze the interviewer's question or statement
2. Provide a concise, professional response suggestion
3. Make suggestions that are authentic and conversational
4. Focus on highlighting relevant skills and experience
5. Keep responses under 100 words

Guidelines:
- Be professional but natural
- Avoid generic responses
- Focus on specific, actionable suggestions
- Don't provide responses that sound scripted
- Consider the conversation flow"""
                }
            ]
            
            # Add conversation history if available
            if conversation_history:
                for i, msg in enumerate(conversation_history[-6:]):  # Last 6 messages for context
                    role = "assistant" if i % 2 == 0 else "user"
                    messages.append({"role": role, "content": msg})
            
            # Add current transcription
            messages.append({
                "role": "user",
                "content": f"Interviewer said: '{transcribed_text}'\n\nPlease provide a professional response suggestion that would work well in this interview context."
            })
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            suggestion = response.choices[0].message.content.strip()
            logger.info(f"Generated AI response suggestion for: '{transcribed_text[:50]}...'")
            
            return suggestion
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return None
    
    async def analyze_interview_context(self, transcribed_text: str) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze this interview dialogue and provide insights:
1. Question type (behavioral, technical, situational, etc.)
2. Key topics mentioned
3. Response strategy recommendations
4. Confidence level (1-10) for question difficulty"""
                    },
                    {
                        "role": "user", 
                        "content": transcribed_text
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content.strip()
            
            return {
                "analysis": analysis,
                "timestamp": datetime.now(),
                "input_text": transcribed_text
            }
            
        except Exception as e:
            logger.error(f"Interview context analysis failed: {e}")
            return {
                "analysis": "Analysis unavailable",
                "timestamp": datetime.now(),
                "input_text": transcribed_text
            }
    
    def add_to_conversation_history(self, text: str):
        self.conversation_history.append(text)
        # Keep only last 20 messages to manage memory
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_conversation_history(self):
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[str]:
        return self.conversation_history.copy()