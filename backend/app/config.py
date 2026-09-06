from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/mplads"
    REDIS_URL: str = "redis://localhost:6379/0"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
