import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class IntentDetector:
    def __init__(self):
        # Define question type patterns
        self.question_patterns = {
            "behavioral": [
                r"tell me about a time",
                r"describe a situation",
                r"give me an example",
                r"walk me through",
                r"how did you handle",
                r"what would you do if"
            ],
            "technical": [
                r"how does .* work",
                r"explain .* algorithm",
                r"what is .*",
                r"how would you implement",
                r"design a system",
                r"code",
                r"programming"
            ],
            "experience": [
                r"tell me about yourself",
                r"your background",
                r"your experience",
                r"worked on",
                r"previous role",
                r"career"
            ],
            "motivation": [
                r"why do you want",
                r"why are you interested",
                r"why should we hire",
                r"what motivates you",
                r"why this company"
            ],
            "strengths_weaknesses": [
                r"greatest strength",
                r"biggest weakness",
                r"what are you good at",
                r"areas for improvement"
            ],
            "future": [
                r"where do you see yourself",
                r"career goals",
                r"five years",
                r"future plans"
            ],
            "situational": [
                r"what would you do",
                r"how would you approach",
                r"if you were",
                r"imagine you"
            ]
        }
    
    def detect_intent(self, text: str) -> str:
        """
        Detect the type of interview question based on text patterns
        """
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        
        # Check each category for pattern matches
        for intent, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.info(f"Detected intent: {intent} for text: {text[:50]}...")
                    return intent
        
        # Default fallback based on question words
        if any(word in text_lower for word in ["what", "how", "why", "when", "where", "who"]):
            return "general_question"
        
        return "unknown"
    
    def get_question_tips(self, intent: str) -> List[str]:
        """
        Get general tips based on question type
        """
        tips_by_intent = {
            "behavioral": [
                "Use the STAR method (Situation, Task, Action, Result)",
                "Focus on specific examples from your experience",
                "Quantify your impact with numbers when possible"
            ],
            "technical": [
                "Break down complex concepts into simple terms",
                "Use examples to illustrate your points",
                "Mention relevant experience with the technology"
            ],
            "experience": [
                "Highlight relevant skills and achievements",
                "Connect your experience to the job requirements",
                "Keep it concise and focused"
            ],
            "motivation": [
                "Show genuine enthusiasm for the role",
                "Connect your goals with company values",
                "Be specific about what interests you"
            ],
            "strengths_weaknesses": [
                "Choose strengths relevant to the job",
                "For weaknesses, show how you're improving",
                "Provide concrete examples"
            ],
            "future": [
                "Align your goals with the company's direction",
                "Show ambition but be realistic",
                "Demonstrate long-term thinking"
            ],
            "situational": [
                "Think through the problem systematically",
                "Consider multiple perspectives",
                "Explain your reasoning clearly"
            ],
            "general_question": [
                "Listen carefully to the full question",
                "Take a moment to organize your thoughts",
                "Provide specific examples when possible"
            ]
        }
        
        return tips_by_intent.get(intent, [
            "Stay calm and confident",
            "Be honest and authentic",
            "Ask clarifying questions if needed"
        ])

# Global instance for easy access
intent_detector = IntentDetector()

def detect_intent(text: str) -> str:
    """
    Simple function interface for intent detection
    """
    return intent_detector.detect_intent(text)
