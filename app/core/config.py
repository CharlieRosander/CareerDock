from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    @property
    def get_database_url(self) -> str:
        """Get database URL, either from DATABASE_URL env var or construct it from components"""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if not all(
            [
                self.POSTGRES_USER,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_HOST,
                self.POSTGRES_PORT,
                self.POSTGRES_DB,
            ]
        ):
            raise ValueError(
                "Database configuration incomplete. Please check your environment variables: "
                "POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB"
            )

        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google OAuth
    CLIENT_SECRET_PATH: str = os.getenv("CLIENT_SECRET_PATH")

    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_settings()

    def _validate_settings(self):
        """Validate that all required settings are present"""
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set")

        if not all(
            [
                self.CLIENT_SECRET_PATH,
            ]
        ):
            raise ValueError(
                "Google OAuth configuration incomplete. Please check your environment variables: "
                "CLIENT_SECRET_PATH"
            )

        if not self.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY must be set for secure token storage")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
