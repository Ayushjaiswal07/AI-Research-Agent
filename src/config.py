import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CHROMA_DB_DIR: str = "./data/chroma_db"
    MAX_SEARCH_RESULTS: int = 3
    MAX_SCRAPE_CHARS: int = 15000 # Prevent overloading token limits

    class Config:
        env_file = ".env"

# Instantiate a global settings object
settings = Settings()