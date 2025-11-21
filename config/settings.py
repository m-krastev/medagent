import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from google.genai import types
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class SystemSettings(BaseSettings):
    """
    Centralized configuration management using Pydantic Settings.
    Reads from Environment Variables automatically.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # --- API Keys ---
    GOOGLE_API_KEY: str = Field(..., description="Gemini API Key")
    
    # --- Model Selection ---
    MODEL_FAST: str = "gemini-2.5-flash-lite"
    MODEL_REASONING: str = "gemini-2.5-flash-lite"
    # Embeddings: For RAG
    MODEL_EMBEDDING: str = "models/text-embedding-004"
    
    # --- Paths ---
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    CHROMA_DB_DIR: str = os.path.join(DATA_DIR, "chroma_db")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")
    
    # --- Resilience Configuration ---
    MAX_RETRIES: int = 5
    RETRY_DELAY: int = 2
    
    # --- Safety Thresholds ---
    # In medical contexts, we block hate speech aggressively but allow
    # "dangerous content" (medical descriptions) with a high threshold
    # to prevent false positives on medical terminology.
    SAFETY_SETTINGS: list = [
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_LOW_AND_ABOVE"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE"
        ),
    ]

    @property
    def retry_options(self) -> types.HttpRetryOptions:
        return types.HttpRetryOptions(
            attempts=self.MAX_RETRIES,
            exp_base=self.RETRY_DELAY,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

settings = SystemSettings()
