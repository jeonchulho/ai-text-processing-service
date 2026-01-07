"""
Configuration management using Pydantic Settings.

This module provides centralized configuration for the application,
loading values from environment variables with sensible defaults.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ai_text_service",
        description="PostgreSQL database connection URL"
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_CACHE_TTL: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )

    # Milvus Configuration
    MILVUS_HOST: str = Field(
        default="localhost",
        description="Milvus host address"
    )
    MILVUS_PORT: int = Field(
        default=19530,
        description="Milvus port"
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4",
        description="OpenAI model to use"
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-ada-002",
        description="OpenAI embedding model"
    )

    # Security Configuration
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token generation"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )

    # API Configuration
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version 1 prefix"
    )
    PROJECT_NAME: str = Field(
        default="AI Text Processing Service",
        description="Project name"
    )
    VERSION: str = Field(
        default="0.1.0",
        description="API version"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )

    # Feature Flags
    ENABLE_TRANSLATION: bool = Field(
        default=True,
        description="Enable translation service"
    )
    ENABLE_SUMMARIZATION: bool = Field(
        default=True,
        description="Enable summarization service"
    )
    ENABLE_SCHEDULE_DETECTION: bool = Field(
        default=True,
        description="Enable schedule detection service"
    )

    # Performance Configuration
    MAX_WORKERS: int = Field(
        default=4,
        description="Maximum number of worker threads"
    )
    MAX_BATCH_SIZE: int = Field(
        default=10,
        description="Maximum batch size for batch operations"
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
