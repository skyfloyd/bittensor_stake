from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bittensor Stake API"
    
    # Security
    SECRET_KEY: str = ""  # Must be set via environment variable
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_TOKEN: str = ""  # Must be set via environment variable
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "bittensor_stake"
    
    # Bittensor
    BITTENSOR_NETWORK: str = "test"  # Use testnet for development
    DEFAULT_NETUID: int = 18
    DEFAULT_HOTKEY: str = ""
    
    # External APIs
    DATURA_API_KEY: str = ""  # Must be set via environment variable
    CHUTES_API_KEY: str = ""  # Must be set via environment variable
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 