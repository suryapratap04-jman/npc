import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Relational Database Settings
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="resource_db")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    
    # Optional direct Database URL override
    DATABASE_URL: Optional[str] = Field(default=None)

    # Vector Database Settings
    QDRANT_HOST: str = Field(default="qdrant")
    QDRANT_PORT: int = Field(default=6333)

    # LLM Settings
    LLM_PROVIDER: str = Field(default="ollama") # ollama, gemini, grok
    OLLAMA_HOST: str = Field(default="ollama")
    OLLAMA_PORT: int = Field(default=11434)
    OLLAMA_MODEL: str = Field(default="qwen2.5:7b")
    
    # API Keys for Cloud Providers
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GROK_API_KEY: Optional[str] = Field(default=None)
    
    # Embedding Model Settings
    EMBEDDING_MODEL: str = Field(default="nomic-ai/nomic-embed-text-v1.5")
    
    # Redis Caching Settings
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    CACHE_ENABLED: bool = Field(default=True)

    @property
    def computed_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        env_file_encoding = "utf-8"

# Instantiate global settings
settings = Settings()
