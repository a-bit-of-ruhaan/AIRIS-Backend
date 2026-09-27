from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # API Keys
    AMADEUS_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
