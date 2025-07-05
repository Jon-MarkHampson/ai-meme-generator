"""
Module for application configuration using Pydantic Settings.
Loads environment variables (e.g., JWT settings) from a .env file and provides
easy access to configuration values throughout the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Pydantic BaseSettings subclass defining configuration variables:
    - JWT_SECRET: secret key for signing JWT tokens
    - JWT_ALGORITHM: algorithm used to sign tokens (default HS256)
    - ACCESS_TOKEN_EXPIRE_MINUTES: token expiration time in minutes
    """

    # crypto for signing JWTs
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Load the database URL from .env
    DATABASE_URL: str

    # Supabase credentials (if/when needed elsewhere)
    SUPABASE_URL: str
    SUPABASE_PASSWORD: str
    SUPABASE_API_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    LOG_LEVEL: str

    OPENAI_MODEL: str
    OPENAI_API_KEY: str
    LOGFIRE_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    AI_IMAGE_BUCKET: str


settings = Settings()
