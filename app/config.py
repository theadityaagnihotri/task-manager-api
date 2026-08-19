import os


class Settings:
    """Application settings, sourced from environment variables."""

    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
    APP_NAME: str = os.getenv("APP_NAME", "task-manager")


settings = Settings()
