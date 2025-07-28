from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_user: str = "postgres"
    database_password: str = ""
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "tiffin_times"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # JECC
    jecc_url: str = "http://www.jecc-ema.org/jecc/jecccfs.php"
    
    # Geocoding
    geocoding_service: str = "nominatim"
    geocoding_api_key: Optional[str] = None
    
    # Cache TTL (seconds)
    cache_ttl: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


settings = Settings()