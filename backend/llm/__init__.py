import logging
from backend.config.settings import settings
from backend.llm.base_provider import BaseLLMProvider
from backend.llm.ollama_provider import OllamaProvider
from backend.llm.gemini_provider import GeminiProvider
from backend.llm.grok_provider import GrokProvider

logger = logging.getLogger(__name__)

# Cache provider instance
_provider_instance = None

def get_llm_provider() -> BaseLLMProvider:
    """Factory to retrieve the active LLM provider based on settings."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance
        
    provider_type = settings.LLM_PROVIDER.lower().strip()
    
    if provider_type == "gemini":
        if settings.GEMINI_API_KEY:
            logger.info("Initializing Google Gemini API LLM Provider.")
            _provider_instance = GeminiProvider()
        else:
            logger.warning("Gemini requested but GEMINI_API_KEY is missing. Falling back to Ollama.")
            _provider_instance = OllamaProvider()
            
    elif provider_type == "grok":
        if settings.GROK_API_KEY:
            logger.info("Initializing xAI Grok API LLM Provider.")
            _provider_instance = GrokProvider()
        else:
            logger.warning("Grok requested but GROK_API_KEY is missing. Falling back to Ollama.")
            _provider_instance = OllamaProvider()
            
    else:
        logger.info("Initializing local Ollama LLM Provider.")
        _provider_instance = OllamaProvider()
        
    return _provider_instance
