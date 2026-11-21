"""
Configuration settings for Solmar Workflow Automation Platform.
Supports environment-based configuration with sensible defaults.
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = Field(default="Solmar Workflow Automation Platform", env="APP_NAME")
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./solmar.db",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=5, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Authentication & Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    # JWT Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password hashing
    ARGON2_TIME_COST: int = Field(default=2, env="ARGON2_TIME_COST")
    ARGON2_MEMORY_COST: int = Field(default=102400, env="ARGON2_MEMORY_COST")
    ARGON2_PARALLELISM: int = Field(default=8, env="ARGON2_PARALLELISM")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # External integrations (mocked)
    CRM_API_URL: str = Field(
        default="https://api.crm.mock/v1",
        env="CRM_API_URL"
    )
    ERP_API_URL: str = Field(
        default="https://api.erp.mock/v1",
        env="ERP_API_URL"
    )
    RPA_WEBHOOK_URL: str = Field(
        default="https://rpa.mock/webhook",
        env="RPA_WEBHOOK_URL"
    )
    
    # Email notifications (mocked)
    SMTP_SERVER: str = Field(default="smtp.mock.com", env="SMTP_SERVER")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(default="user@mock.com", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="mockpassword", env="SMTP_PASSWORD")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()