"""
Centralized configuration management using pydantic-settings.
Loads and validates all environment variables required for the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List
import os
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot Configuration
    BOT_TOKEN: str = Field(..., description="Main Telegram bot token")
    LOG_BOT_TOKEN: str = Field(..., description="Telegram bot token for logging")
    LOG_CHAT_ID: str = Field(..., description="Chat ID for log messages")
    
    # MongoDB Configuration
    MONGO_URI: str = Field(..., description="MongoDB connection string")
    MONGO_DB_NAME: str = Field(default="trading_bot", description="MongoDB database name")
    
    # Render.com Configuration
    WEBHOOK_URL: str = Field(..., description="Public webhook URL for Telegram")
    HOST: str = Field(default="0.0.0.0", description="Host to bind the server")
    PORT: int = Field(default=10000, description="Port to bind the server")
    
    # Security Configuration
    ENCRYPTION_KEY: str = Field(..., description="Fernet encryption key for API secrets")
    ALLOWED_USER_IDS: str = Field(..., description="Comma-separated list of allowed user IDs")
    
    # Delta Exchange Configuration
    DELTA_BASE_URL: str = Field(
        default="https://api.india.delta.exchange",
        description="Delta Exchange India API base URL"
    )
    
    # Application Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    MAX_RETRIES: int = Field(default=3, description="Maximum API retry attempts")
    RETRY_DELAY: int = Field(default=2, description="Delay between retries in seconds")
    RATE_LIMIT_PER_MINUTE: int = Field(default=50, description="Max requests per user per minute")
    
    # Cache TTL Settings (in seconds)
    SPOT_PRICE_CACHE_TTL: int = Field(default=5, description="Spot price cache TTL")
    OPTION_CHAIN_CACHE_TTL: int = Field(default=60, description="Option chain cache TTL")
    USER_SETTINGS_CACHE_TTL: int = Field(default=300, description="User settings cache TTL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("ALLOWED_USER_IDS")
    @classmethod
    def validate_user_ids(cls, v: str) -> str:
        """Validate that user IDs are comma-separated integers."""
        try:
            user_ids = [int(uid.strip()) for uid in v.split(",")]
            if not user_ids:
                raise ValueError("At least one user ID must be provided")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid ALLOWED_USER_IDS format: {e}")
    
    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate that encryption key is a valid Fernet key."""
        try:
            Fernet(v.encode())
            return v
        except Exception:
            raise ValueError("Invalid ENCRYPTION_KEY. Generate a new key using Fernet.generate_key()")
    
    @field_validator("PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number is within valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    def get_allowed_user_ids(self) -> List[int]:
        """Parse and return list of allowed user IDs."""
        return [int(uid.strip()) for uid in self.ALLOWED_USER_IDS.split(",")]
    
    def get_fernet_cipher(self) -> Fernet:
        """Return Fernet cipher instance for encryption/decryption."""
        return Fernet(self.ENCRYPTION_KEY.encode())
    
    def get_webhook_endpoint(self) -> str:
        """Return full webhook endpoint URL."""
        return f"{self.WEBHOOK_URL}/webhook"


# Global settings instance
settings = Settings()


# Utility function to generate new encryption key
def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key().decode()


if __name__ == "__main__":
    # For testing: print settings (masked sensitive data)
    print("Configuration loaded successfully!")
    print(f"MongoDB Database: {settings.MONGO_DB_NAME}")
    print(f"Webhook URL: {settings.get_webhook_endpoint()}")
    print(f"Allowed Users: {len(settings.get_allowed_user_ids())} user(s)")
    print(f"Delta Base URL: {settings.DELTA_BASE_URL}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print("\nTo generate a new encryption key, run:")
    print(f"python -c 'from config import generate_encryption_key; print(generate_encryption_key())'")
    
