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
    CACHE_TTL: int = 120  # Cache time-to-live in seconds
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "bittensor_stake"
    
    # Bittensor
    BITTENSOR_NETWORK: str = "test"  # Use testnet for development
    DEFAULT_NETUID: int = 18
    DEFAULT_HOTKEY: str = ""
    SUBTENSOR_URL: str = "ws://127.0.0.1:9944"  # Default to local node # wss://entrypoint-testnet.opentensor.ai:443 # wss://entrypoint-finney.opentensor.ai:443
    
    # Wallet Settings
    WALLET_NAME: str = "default"
    WALLET_HOTKEY: str = "default"
    WALLET_PATH: str = "~/.bittensor/wallets"
    WALLET_SEED: str = ""  # Must be set via environment variable
    
    # External APIs
    DATURA_API_KEY: str = ""  # Must be set via environment variable
    DATURA_API_URL: str = "https://apis.datura.ai/twitter"
    CHUTES_API_KEY: str = ""  # Must be set via environment variable
    CHUTES_API_URL: str = "https://api.chutes.ai/v1/chat/completions"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 