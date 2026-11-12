from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "SHIVANK AI")
    owner_name: str = os.getenv("OWNER_NAME", "Shivank Dwivedi")
    app_password: str = os.getenv("APP_PASSWORD", "")
    device_agent_token: str = os.getenv("DEVICE_AGENT_TOKEN", "")
    database_path: str = os.getenv("DATABASE_PATH", "./data/shivank_ai.db")
    max_task_chars: int = int(os.getenv("MAX_TASK_CHARS", "6000"))
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    openrouter_site_url: str = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
    openrouter_app_name: str = os.getenv("OPENROUTER_APP_NAME", "SHIVANK AI")

@lru_cache
def get_settings() -> Settings:
    return Settings()
