"""
Configuration settings for Hisper application
"""

import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Hisper"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./hisper.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # MCP Discovery
    DISCOVERY_INTERVAL_MINUTES: int = 60
    MAX_CONCURRENT_DISCOVERIES: int = 10
    
    # GitHub API (for discovering MCP servers)
    GITHUB_TOKEN: Optional[str] = None
    
    # NPM Registry
    NPM_REGISTRY_URL: str = "https://registry.npmjs.org"
    
    # PyPI
    PYPI_URL: str = "https://pypi.org/pypi"
    
    # Redis (for caching and task queue)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Default LLM settings
    DEFAULT_LLM_PROVIDER: str = "openrouter"
    DEFAULT_LLM_MODEL: str = "deepseek/deepseek-chat"
    
    # MCP Settings
    MCP_TIMEOUT: int = 30  # seconds
    MCP_MAX_RETRIES: int = 3
    
    # Monitoring
    MONITORING_ENABLED: bool = True
    METRICS_RETENTION_HOURS: int = 168  # 7 days
    ALERT_WEBHOOK_URL: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()