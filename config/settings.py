from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "WealthAdvisorAI"

    # App
    app_env: str = "Development"
    log_level: str = "INFO"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "wealthadvisor_docs"

    # SEC EDGAR
    sec_api_key: str = ""
    sec_user_agent: str = "WealthAdvisor contact@wealthadvisor.ai"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()