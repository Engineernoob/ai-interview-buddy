import json
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextRetriever:
    def __init__(self):
        self.resume_data = {}
        self.job_description = ""
        self.storage_path = "data"
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def store_resume(self, resume_text: str, filename: str = None) -> bool:
        """
        Store resume content for context retrieval
        """
        try:
            # Simple keyword extraction (replace with more sophisticated processing)
            self.resume_data = {
                "raw_text": resume_text,
                "filename": filename,
                "stored_at": datetime.now().isoformat(),
                "keywords": self._extract_keywords(resume_text),
                "skills": self._extract_skills(resume_text),
                "experience": self._extract_experience(resume_text)
            }
            
            # Save to file
            resume_file = os.path.join(self.storage_path, "resume.json")
            with open(resume_file, 'w') as f:
                json.dump(self.resume_data, f, indent=2)
            
            logger.info(f"Resume stored successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store resume: {e}")
            return False
    
    def store_job_description(self, jd_text: str) -> bool:
        """
        Store job description for context retrieval
        """
        try:
            job_data = {
                "raw_text": jd_text,
                "stored_at": datetime.now().isoformat(),
                "requirements": self._extract_requirements(jd_text),
                "company_info": self._extract_company_info(jd_text),
                "role_keywords": self._extract_keywords(jd_text)
            }
            
            self.job_description = jd_text
            
            # Save to file
            jd_file = os.path.join(self.storage_path, "job_description.json")
            with open(jd_file, 'w') as f:
                json.dump(job_data, f, indent=2)
            
            logger.info("Job description stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store job description: {e}")
            return False
    
    def retrieve_context(self, question_text: str, intent: str = None) -> Dict:
        """
        Retrieve relevant context from resume and job description
        """
        context = {
            "relevant_experience": [],
            "matching_skills": [],
            "suggested_points": [],
            "company_connection": []
        }
        
        try:
            # Load stored data if not in memory
            self._load_stored_data()
            
            # Extract relevant experience based on question
            if self.resume_data:
                context["relevant_experience"] = self._find_relevant_experience(question_text)
                context["matching_skills"] = self._find_matching_skills(question_text)
            
            # Find connections to job requirements
            if self.job_description:
                context["company_connection"] = self._find_company_connections(question_text)
            
            # Generate suggestion points based on intent
            context["suggested_points"] = self._generate_suggestions(question_text, intent)
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
        
        return context
    
    def _load_stored_data(self):
        """Load resume and job description from storage if not in memory"""
        try:
            if not self.resume_data:
                resume_file = os.path.join(self.storage_path, "resume.json")
                if os.path.exists(resume_file):
                    with open(resume_file, 'r') as f:
                        self.resume_data = json.load(f)
            
            if not self.job_description:
                jd_file = os.path.join(self.storage_path, "job_description.json")
                if os.path.exists(jd_file):
                    with open(jd_file, 'r') as f:
                        jd_data = json.load(f)
                        self.job_description = jd_data.get("raw_text", "")
        
        except Exception as e:
            logger.error(f"Failed to load stored data: {e}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from text (simple implementation)"""
        # Simple keyword extraction - replace with more sophisticated NLP
        common_words = set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        words = text.lower().split()
        keywords = [word.strip('.,!?;:') for word in words if len(word) > 3 and word not in common_words]
        return list(set(keywords))[:20]  # Return top 20 unique keywords
    
    def _extract_skills(self, resume_text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common technical skills to look for
        skill_patterns = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'aws', 'docker',
            'kubernetes', 'git', 'machine learning', 'data science', 'tensorflow',
            'project management', 'agile', 'scrum', 'leadership', 'communication'
        ]
        
        found_skills = []
        text_lower = resume_text.lower()
        for skill in skill_patterns:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_experience(self, resume_text: str) -> List[str]:
        """Extract experience highlights from resume"""
        # Simple experience extraction (look for bullet points, years, etc.)
        lines = resume_text.split('\n')
        experience_lines = []
        
        for line in lines:
            line = line.strip()
            # Look for lines that might contain experience
            if any(keyword in line.lower() for keyword in ['year', 'month', 'led', 'developed', 'managed', 'implemented']):
                if len(line) > 20:  # Ignore very short lines
                    experience_lines.append(line)
        
        return experience_lines[:5]  # Return top 5
    
    def _extract_requirements(self, jd_text: str) -> List[str]:
        """Extract requirements from job description"""
        lines = jd_text.split('\n')
        requirements = []
        
        for line in lines:
            line = line.strip()
            # Look for requirement indicators
            if any(keyword in line.lower() for keyword in ['required', 'must have', 'experience with', 'proficient']):
                if len(line) > 15:
                    requirements.append(line)
        
        return requirements[:10]
    
    def _extract_company_info(self, jd_text: str) -> Dict:
        """Extract company information from job description"""
        # Simple company info extraction
        return {
            "culture_keywords": self._extract_keywords(jd_text)[:10],
            "benefits_mentioned": 'benefits' in jd_text.lower(),
            "company_size": "startup" if "startup" in jd_text.lower() else "enterprise"
        }
    
    def _find_relevant_experience(self, question: str) -> List[str]:
        """Find relevant experience based on question keywords"""
        if not self.resume_data:
            return []
        
        question_keywords = set(self._extract_keywords(question))
        relevant_exp = []
        
        for exp in self.resume_data.get("experience", []):
            exp_keywords = set(self._extract_keywords(exp))
            if question_keywords.intersection(exp_keywords):
                relevant_exp.append(exp)
        
        return relevant_exp[:3]
    
    def _find_matching_skills(self, question: str) -> List[str]:
        """Find skills that match question context"""
        if not self.resume_data:
            return []
        
        question_lower = question.lower()
        matching_skills = []
        
        for skill in self.resume_data.get("skills", []):
            if skill.lower() in question_lower:
                matching_skills.append(skill)
        
        return matching_skills
    
    def _find_company_connections(self, question: str) -> List[str]:
        """Find ways to connect answer to company/role"""
        connections = []
        
        if "why" in question.lower() and "company" in question.lower():
            connections.append("Research shows this aligns with company values")
        
        if "experience" in question.lower():
            connections.append("This experience directly relates to the job requirements")
        
        return connections
    
    def _generate_suggestions(self, question: str, intent: str) -> List[str]:
        """Generate contextual suggestions based on available data"""
        suggestions = []
        
        # Add generic suggestions based on intent
        if intent == "experience":
            suggestions.append("Focus on quantifiable achievements")
            suggestions.append("Connect your experience to job requirements")
        
        elif intent == "behavioral":
            suggestions.append("Use the STAR method for structured responses")
            suggestions.append("Choose examples that show leadership or problem-solving")
        
        elif intent == "motivation":
            suggestions.append("Show knowledge of company values and mission")
            suggestions.append("Explain how this role fits your career goals")
        
        return suggestions

# Global instance
retriever = ContextRetriever()

def retrieve_context(question_text: str, intent: str = None) -> Dict:
    """
    Simple function interface for context retrieval
    """
    return retriever.retrieve_context(question_text, intent)
