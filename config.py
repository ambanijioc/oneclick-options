"""
Configuration module for loading and validating environment variables.
All application settings are centralized here using Pydantic.
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet


class TelegramConfig(BaseSettings):
    """Telegram bot configuration settings."""
    
    bot_token: str = Field(..., alias='TELEGRAM_BOT_TOKEN')
    log_bot_token: str = Field(..., alias='TELEGRAM_LOG_BOT_TOKEN')
    log_chat_id: str = Field(..., alias='TELEGRAM_LOG_CHAT_ID')
    authorized_user_ids: str = Field(..., alias='AUTHORIZED_USER_IDS')
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    @field_validator('authorized_user_ids')
    @classmethod
    def parse_user_ids(cls, v: str) -> List[int]:
        """Parse comma-separated user IDs into list of integers."""
        try:
            return [int(uid.strip()) for uid in v.split(',') if uid.strip()]
        except ValueError as e:
            raise ValueError(f"Invalid user ID format: {e}")
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user ID is authorized."""
        authorized_ids = self.parse_user_ids(self.authorized_user_ids)
        return user_id in authorized_ids


class MongoDBConfig(BaseSettings):
    """MongoDB database configuration settings."""
    
    uri: str = Field(..., alias='MONGODB_URI')
    database_name: str = Field(default='trading_bot', alias='MONGODB_DATABASE')
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


class DeltaExchangeConfig(BaseSettings):
    """Delta Exchange API configuration settings."""
    
    base_url: str = Field(
        default='https://api.india.delta.exchange',
        alias='DELTA_BASE_URL'
    )
    timeout: int = Field(default=30, alias='DELTA_TIMEOUT')
    max_retries: int = Field(default=3, alias='DELTA_MAX_RETRIES')
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


class RenderConfig(BaseSettings):
    """Render.com deployment configuration settings."""
    
    external_url: str = Field(..., alias='RENDER_EXTERNAL_URL')
    host: str = Field(default='0.0.0.0', alias='HOST')
    port: int = Field(default=10000, alias='PORT')
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    @property
    def webhook_url(self) -> str:
        """Get the full webhook URL."""
        return f"{self.external_url}/webhook"


class EncryptionConfig(BaseSettings):
    """Encryption configuration for sensitive data."""
    
    encryption_key: str = Field(..., alias='ENCRYPTION_KEY')
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    @field_validator('encryption_key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate that the encryption key is a valid Fernet key."""
        try:
            Fernet(v.encode())
            return v
        except Exception as e:
            raise ValueError(f"Invalid Fernet encryption key: {e}")
    
    def get_fernet(self) -> Fernet:
        """Get Fernet cipher instance."""
        return Fernet(self.encryption_key.encode())


class AppConfig:
    """Main application configuration aggregator."""
    
    def __init__(self):
        """Initialize all configuration sections."""
        self.telegram = TelegramConfig()
        self.mongodb = MongoDBConfig()
        self.delta = DeltaExchangeConfig()
        self.render = RenderConfig()
        self.encryption = EncryptionConfig()
    
    def validate_all(self) -> bool:
        """Validate all configurations are loaded correctly."""
        try:
            # Test each config section
            assert self.telegram.bot_token, "Telegram bot token missing"
            assert self.mongodb.uri, "MongoDB URI missing"
            assert self.render.external_url, "Render external URL missing"
            assert self.encryption.encryption_key, "Encryption key missing"
            return True
        except AssertionError as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global configuration instance
config = AppConfig()


def generate_encryption_key() -> str:
    """
    Utility function to generate a new Fernet encryption key.
    Run this once and store the key in your .env file.
    """
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration loading...")
    
    if config.validate_all():
        print("✅ All configurations loaded successfully!")
        print(f"Telegram Bot Token: {config.telegram.bot_token[:10]}...")
        print(f"MongoDB URI: {config.mongodb.uri[:30]}...")
        print(f"Webhook URL: {config.render.webhook_url}")
        print(f"Delta Exchange Base URL: {config.delta.base_url}")
    else:
        print("❌ Configuration validation failed!")
    
    # Generate new encryption key (uncomment if needed)
    # print(f"\nNew Encryption Key: {generate_encryption_key()}")
  
