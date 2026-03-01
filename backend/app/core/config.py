from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Financial Risk Scoring System"
    
    # DB Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/finaccess"
    
    # JWT Configuration
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Inference Configuration
    INFERENCE_MODE: str = "single"  # supports: 'single' or 'threaded'
    THREADPOOL_WORKERS: str = "auto"
    
    # Database Configuration Overrides
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # System Extensions
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL: int = 300
    LOG_LEVEL: str = "WARNING"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
