from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "EduGenius AI (Kids Edition)"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./edugenius.db"
    JWT_SECRET: str = "temporary-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    @property
    def google_api_key(self) -> str:
        """Accept either environment variable name used by Google SDK setups."""
        return self.GEMINI_API_KEY.strip() or self.GOOGLE_API_KEY.strip()

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
