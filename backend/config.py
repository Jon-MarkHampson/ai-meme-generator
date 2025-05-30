from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # crypto for signing JWTs
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # you can also put DB_URL here later
    # DATABASE_URL: str = "sqlite:///./database.db"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()