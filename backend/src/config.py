"""
Application configuration management using Pydantic settings.

Loads configuration from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables.
    """

    # Batfish connection
    batfish_host: str = Field(default="localhost", description="Batfish container hostname")
    batfish_port: int = Field(default=9996, description="Batfish container port (v2025.07.07 uses 9996 only)")

    # API configuration
    api_title: str = Field(default="Batfish Visualization & Verification API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins for frontend"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    # File upload
    max_upload_size_mb: int = Field(default=100, description="Maximum upload size in MB")
    temp_upload_dir: str = Field(default="./uploads", description="Temporary upload directory")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
