from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str  # used for session signing
    ENCRYPTION_KEY: str  # Fernet key for OAuth token encryption

    # Database
    DATABASE_URL: str = "sqlite:///./classroom_copilot.db"

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"

    # Gemini
    GEMINI_API_KEY: str

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Poller
    POLL_INTERVAL_MINUTES: int = 15


settings = Settings()
