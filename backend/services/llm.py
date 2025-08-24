import os
import json
import aiohttp
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Use Ollama for local LLM inference
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "llama2")
        self.use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
        self.model_ready = False
        
        if self.use_local_llm:
            logger.info(f"Using local LLM: {self.model} via Ollama at {self.ollama_url}")
        else:
            logger.info("Using mock LLM responses only")
    
    async def ensure_model_ready(self):
        """Ensure Ollama model is ready"""
        if self.model_ready or not self.use_local_llm:
            return True
            
        try:
            from .ollama_setup import ollama_manager
            success, model_name = await ollama_manager.setup_default_model()
            
            if success:
                self.model = model_name  # Use the working model
                self.model_ready = True
                logger.info(f"Model ready: {model_name}")
                return True
            else:
                logger.warning("Failed to setup Ollama model, falling back to mock responses")
                self.use_local_llm = False
                return False
                
        except Exception as e:
            logger.error(f"Error setting up Ollama: {e}")
            self.use_local_llm = False
            return False
    
    async def generate_suggestions(self, text: str, intent: str, context: Dict) -> Dict:
        """
        Generate coaching suggestions based on interview question, intent, and context
        Returns: { "bullets": ["tip1","tip2"], "follow_up": "suggested question" }
        """
        # Ensure model is ready
        await self.ensure_model_ready()
        
        if not self.use_local_llm:
            return await self._mock_suggestions(text, intent, context)
        
        try:
            # Try to use Ollama first
            result = await self._generate_with_ollama(text, intent, context)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        
        # Fallback to mock responses
        return await self._mock_suggestions(text, intent, context)
    
    async def _generate_with_ollama(self, text: str, intent: str, context: Dict) -> Optional[Dict]:
        """Generate suggestions using local Ollama LLM"""
        try:
            prompt = self._build_coaching_prompt(text, intent, context)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 200
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("response", "")
                        
                        # Try to parse as JSON first
                        try:
                            result = json.loads(content)
                            if "bullets" in result and "follow_up" in result:
                                return result
                        except json.JSONDecodeError:
                            pass
                        
                        # Fallback: parse text response
                        return self._parse_text_response(content)
                    else:
                        logger.error(f"Ollama request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return None
    
    def _build_coaching_prompt(self, question: str, intent: str, context: Dict) -> str:
        """Build a detailed prompt for the LLM with context"""
        prompt = f"""You are an expert interview coach helping job candidates prepare for interviews.

Interview Question: "{question}"
Question Type: {intent}

"""
        
        # Add context information
        if context.get("relevant_experience"):
            exp_text = "; ".join(context["relevant_experience"][:2])
            prompt += f"Candidate's Relevant Experience: {exp_text}\n"
        
        if context.get("matching_skills"):
            skills_text = ", ".join(context["matching_skills"])
            prompt += f"Relevant Skills: {skills_text}\n"
        
        if context.get("company_connection"):
            conn_text = "; ".join(context["company_connection"])
            prompt += f"Job Context: {conn_text}\n"
        
        prompt += """
Provide interview coaching advice in JSON format:
{
  "bullets": ["specific tip 1", "specific tip 2", "specific tip 3"],
  "follow_up": "good follow-up question the candidate can ask"
}

Focus on:
- Specific, actionable advice
- Professional but conversational tone
- Practical tips that can be immediately applied
- Incorporating the candidate's background when available

JSON response:"""
        
        return prompt
    
    def _parse_text_response(self, content: str) -> Dict:
        """Parse non-JSON text response into expected format"""
        lines = content.split('\n')
        bullets = []
        follow_up = ""
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for bullets or numbered items
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                bullets.append(line[1:].strip())
            elif line[0].isdigit() and line[1] in '.):':
                bullets.append(line[2:].strip())
            elif 'follow' in line.lower() and 'up' in line.lower():
                current_section = 'follow_up'
            elif current_section == 'follow_up' and line:
                if not follow_up:
                    follow_up = line
        
        # Ensure we have at least some content
        if not bullets:
            bullets = ["Focus on specific examples from your experience", "Connect your answer to the job requirements"]
        
        if not follow_up:
            follow_up = "What questions do you have about the role or the team?"
        
        return {"bullets": bullets[:3], "follow_up": follow_up}
    
    async def _mock_suggestions(self, text: str, intent: str, context: Dict) -> Dict:
        """Generate mock suggestions when LLM is not available"""
        # Mock responses based on intent
        mock_responses = {
            "experience": {
                "bullets": [
                    "Highlight your most relevant achievements with specific metrics",
                    "Connect your background directly to the job requirements",
                    "Show progression and growth in your career"
                ],
                "follow_up": "What opportunities for professional development does this role offer?"
            },
            "behavioral": {
                "bullets": [
                    "Use the STAR method: Situation, Task, Action, Result",
                    "Choose an example that shows leadership or problem-solving",
                    "Quantify your impact with specific numbers or outcomes"
                ],
                "follow_up": "How does the team handle challenging situations like this?"
            },
            "motivation": {
                "bullets": [
                    "Research the company's mission and values beforehand",
                    "Explain how this role aligns with your career goals",
                    "Show genuine enthusiasm and specific knowledge about the company"
                ],
                "follow_up": "What excites the team most about working here?"
            },
            "strengths_weaknesses": {
                "bullets": [
                    "Choose strengths that are directly relevant to the job",
                    "For weaknesses, show how you're actively improving",
                    "Provide concrete examples to support your points"
                ],
                "follow_up": "What qualities do your most successful team members have?"
            },
            "technical": {
                "bullets": [
                    "Break down complex concepts into clear, simple terms",
                    "Use specific examples from your experience",
                    "Show your thought process and problem-solving approach"
                ],
                "follow_up": "What technical challenges is the team currently facing?"
            }
        }
        
        # Get response based on intent or use default
        response = mock_responses.get(intent, {
            "bullets": [
                "Take a moment to organize your thoughts before answering",
                "Provide specific examples whenever possible",
                "Keep your answer focused and concise"
            ],
            "follow_up": "What questions do you have about the role or team?"
        })
        
        # Add context-aware modifications
        if context.get("matching_skills"):
            skills = ", ".join(context["matching_skills"][:2])
            response["bullets"].append(f"Mention your experience with {skills}")
        
        return response

# Global instance
llm_service = LLMService()

def generate_suggestions(text: str, intent: str, context: Dict) -> Dict:
    """
    Simple function interface for LLM suggestions
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(llm_service.generate_suggestions(text, intent, context))
