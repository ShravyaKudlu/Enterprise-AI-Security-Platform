from typing import List, Optional
import os


class Settings:
    # Application
    APP_NAME: str = "Enterprise AI Security Platform"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Database - Using SQLite for demo
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_security.db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "demo-secret-key")
    API_KEYS: str = os.getenv("API_KEYS", "test-api-key-1,test-api-key-2")
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
    )

    # Model API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

    # Model Configuration
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600

    def get_api_keys_list(self) -> List[str]:
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]

    def get_allowed_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
