import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    CHROMA_DB_DIR: str = "./data/chroma_db"
    MAX_SEARCH_RESULTS: int = 3
    MAX_SCRAPE_CHARS: int = 15000

    class Config:
        env_file = ".env"

settings = Settings()