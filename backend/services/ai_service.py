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
    
    async def generate_coaching_response(
        self, 
        transcribed_text: str, 
        context: str = "job interview",
        conversation_history: List[str] = None
    ) -> Optional[dict]:
        """Generate coaching response in format expected by frontend"""
        try:
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an AI interview coach assistant. You help job candidates during interviews by providing coaching tips.

Context: The user is in a {context} setting.

Your task:
1. Analyze what the interviewer said: '{transcribed_text}'
2. Provide 2-4 bullet point coaching tips
3. Suggest a follow-up question they could ask
4. Keep tips concise and actionable

Return your response as JSON with this exact format:
{{
  "bullets": ["tip 1", "tip 2", "tip 3"],
  "follow_up": "suggested follow-up question"
}}

Guidelines:
- Be professional but encouraging
- Focus on specific, actionable advice
- Make bullets 1-2 sentences each
- Follow-up should be relevant to the interview context"""
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
                "content": f"Interviewer said: '{transcribed_text}'\n\nPlease provide coaching tips in the exact JSON format specified."
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
            logger.info(f"Generated AI coaching response for: '{transcribed_text[:50]}...'")
            
            # Parse JSON response
            import json
            try:
                coaching_data = json.loads(suggestion)
                # Ensure required keys exist
                if 'bullets' not in coaching_data:
                    coaching_data['bullets'] = ["Consider the key points you want to highlight"]
                if 'follow_up' not in coaching_data:
                    coaching_data['follow_up'] = "What would you like to know about this role?"
                return coaching_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "bullets": ["Take a moment to think about your response", "Focus on relevant experience", "Be specific with examples"],
                    "follow_up": "What aspects of this role excite you most?"
                }
            
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