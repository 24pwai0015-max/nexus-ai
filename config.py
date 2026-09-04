import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    _raw_base_url: str = os.getenv("OPENAI_BASE_URL", "").strip()
    _raw_model: str = os.getenv("DEFAULT_MODEL", "").strip()
    
    @property
    def OPENAI_BASE_URL(self) -> str:
        if self._raw_base_url and self._raw_base_url != "https://api.openai.com/v1":
            return self._raw_base_url
        # Auto-detect Groq keys
        if self.OPENAI_API_KEY.startswith("gsk_"):
            return "https://api.groq.com/openai/v1"
        # Auto-detect OpenRouter keys
        if self.OPENAI_API_KEY.startswith("sk-or-"):
            return "https://openrouter.ai/api/v1"
        return self._raw_base_url or "https://api.openai.com/v1"

    @property
    def DEFAULT_MODEL(self) -> str:
        if self._raw_model and self._raw_model != "gpt-4o-mini":
            return self._raw_model
        # If using Groq, default to active high-performance Qwen 3.8 27B model
        if self.OPENAI_API_KEY.startswith("gsk_"):
            return "qwen/qwen3.8-27b"
        return self._raw_model or "gpt-4o-mini"

    # Search Settings
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()
    
    # Image Settings
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "auto").strip().lower()

    # Nexus Platform API Keys (comma-separated). Always includes dev master key by default.
    NEXUS_API_KEYS_RAW: str = os.getenv("NEXUS_API_KEYS", "nexus_dev_master_key")

    @property
    def valid_api_keys(self) -> set:
        keys = {k.strip() for k in self.NEXUS_API_KEYS_RAW.split(",") if k.strip()}
        keys.add("nexus_dev_master_key")
        return keys

    @property
    def has_openai_key(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_tavily_key(self) -> bool:
        return bool(self.TAVILY_API_KEY)

settings = Settings()
