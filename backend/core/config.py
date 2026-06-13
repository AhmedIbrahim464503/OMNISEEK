from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings class validating configurations from environment variables."""
    
    PROJECT_NAME: str = "OMNISEEK"
    DEBUG: bool = True
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    DB_URL: str
    REDIS_URL: str
    
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Convert comma-separated string origins into a list of strings."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
