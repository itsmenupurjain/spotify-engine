"""
Application configuration — reads from environment variables via Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # App
    app_env: str = "development"
    app_debug: bool = True
    api_rate_limit: int = 100
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/spotify_discovery"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/spotify_discovery"

    # AI APIs
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Reddit API
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "spotify-discovery-engine/1.0"

    # Twitter/X API
    twitter_bearer_token: Optional[str] = None

    # Apify (Twitter fallback)
    apify_api_token: Optional[str] = None

    # Auth
    clerk_secret_key: Optional[str] = None

    # AI Processing
    classification_model: str = "claude-sonnet-4-6"
    classification_temperature: float = 0.1
    classification_max_tokens: int = 500
    classification_batch_size: int = 50
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Clustering
    initial_cluster_count: int = 8
    cluster_representatives: int = 20

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
