"""
Shared configuration for medagent package.
Reads settings from .env file independently from src folder.
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()


class MedAgentSettings(BaseSettings):
    """Configuration for ADK-compatible medagent package."""
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # API Keys
    GOOGLE_API_KEY: str = Field(..., description="Gemini API Key")
    
    # Model Selection
    MODEL_FAST: str = Field(default="gemini-2.0-flash-exp", description="Fast model for triage, evidence, imaging")
    MODEL_REASONING: str = Field(default="gemini-2.0-flash-exp", description="Reasoning model for hypothesis, research, orchestrator")
    MODEL_EMBEDDING: str = Field(default="models/text-embedding-004", description="Embedding model for RAG")
    
    # ChromaDB Configuration
    CHROMA_DB_DIR: str = Field(default="./datas/chroma_db", description="Directory path for ChromaDB persistent storage")
    


settings = MedAgentSettings()

__all__ = ["settings"]
