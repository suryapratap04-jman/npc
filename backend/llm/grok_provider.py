import logging
import httpx
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.llm.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GrokProvider(BaseLLMProvider):
    """Integrates xAI Grok API services (using OpenAI compatible REST calls)."""
    
    def __init__(self):
        self.client = httpx.Client(timeout=60.0)
        self.api_key = settings.GROK_API_KEY
        self.model = "grok-beta"
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.api_key:
            return "Grok API key is not configured."
            
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        
        try:
            logger.info("Sending request to xAI Grok API generate...")
            response = self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Grok API generate error: {e}")
            return f"Error communicating with Grok API: {e}"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            return "Grok API key is not configured."
            
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        
        try:
            logger.info("Sending request to xAI Grok API chat...")
            response = self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Grok API chat error: {e}")
            return f"Error communicating with Grok API chat: {e}"
