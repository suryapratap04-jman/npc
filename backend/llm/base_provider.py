from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract interface defining standard methods for LLM client integration."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Sends a direct prompt generation request. Returns text response."""
        pass
        
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Sends structured chat messages histories. Returns assistant's text response."""
        pass
