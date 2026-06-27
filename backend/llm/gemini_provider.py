import logging
import httpx
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.llm.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Integrates Google Gemini LLM API services using REST interface."""
    
    def __init__(self):
        self.client = httpx.Client(timeout=60.0)
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-1.5-flash"
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.api_key:
            return "Gemini API key is not configured."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
            
        try:
            logger.info("Sending request to Google Gemini API generate...")
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            # Extract text from response structure
            candidates = response.json().get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "Empty response from Gemini API."
        except Exception as e:
            logger.error(f"Gemini API generate error: {e}")
            return f"Error communicating with Gemini API: {e}"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            return "Gemini API key is not configured."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Translate role names (user, assistant -> user, model)
        contents = []
        for msg in messages:
            role = "user"
            if msg.get("role") == "assistant" or msg.get("role") == "model":
                role = "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })
            
        payload = {"contents": contents}
        
        try:
            logger.info("Sending request to Google Gemini API chat...")
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            candidates = response.json().get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "Empty response from Gemini API."
        except Exception as e:
            logger.error(f"Gemini API chat error: {e}")
            return f"Error communicating with Gemini API chat: {e}"
