import asyncio
import aiohttp
import subprocess
import logging
import os

logger = logging.getLogger(__name__)

class OllamaManager:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("LLM_MODEL", "llama2")
    
    async def check_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_available_models(self) -> list:
        """Get list of available models"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error getting models: {e}")
        return []
    
    async def pull_model_if_needed(self, model_name: str) -> bool:
        """Pull model if it doesn't exist"""
        available_models = await self.get_available_models()
        
        # Check if model already exists
        if any(model_name in model for model in available_models):
            logger.info(f"Model {model_name} already available")
            return True
        
        logger.info(f"Pulling model {model_name}...")
        try:
            # Use subprocess to pull model
            result = subprocess.run([
                "ollama", "pull", model_name
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled model {model_name}")
                return True
            else:
                logger.error(f"Failed to pull model {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout pulling model {model_name}")
            return False
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def setup_default_model(self) -> tuple[bool, str]:
        """Setup default model, try alternatives if main model fails"""
        models_to_try = [
            self.default_model,
            "llama2:7b-chat-q4_0",  # Smaller quantized version
            "mistral:7b-instruct-q4_0",  # Alternative model
            "tinyllama"  # Tiny fallback model
        ]
        
        if not await self.check_ollama_running():
            return False, "Ollama server not running"
        
        for model in models_to_try:
            logger.info(f"Trying to setup model: {model}")
            if await self.pull_model_if_needed(model):
                # Test the model works
                if await self.test_model(model):
                    logger.info(f"Successfully setup model: {model}")
                    return True, model
        
        return False, "No working models available"
    
    async def test_model(self, model_name: str) -> bool:
        """Test if model works with a simple prompt"""
        try:
            payload = {
                "model": model_name,
                "prompt": "Hello",
                "stream": False,
                "options": {"num_predict": 5}
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error testing model {model_name}: {e}")
            return False

ollama_manager = OllamaManager()