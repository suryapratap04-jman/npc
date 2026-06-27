import logging
import httpx
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.llm.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Integrates local Ollama LLM provider services using REST APIs."""
    
    def __init__(self):
        self.client = httpx.Client(timeout=60.0)
        self.base_url = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            logger.info(f"Ollama generate request with model: {settings.OLLAMA_MODEL}")
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama API generate error: {e}")
            return f"Error communicating with local Ollama: {e}"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }
        try:
            logger.info(f"Ollama chat request with model: {settings.OLLAMA_MODEL}")
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama API chat error: {e}")
            return f"Error communicating with local Ollama chat: {e}"
