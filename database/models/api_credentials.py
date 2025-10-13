"""
Pydantic models for API credentials.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class APICredential(BaseModel):
    """
    API Credential model for storing Delta Exchange API keys.
    API secrets are encrypted before storage.
    """
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    api_name: str = Field(..., min_length=1, max_length=100, description="User-friendly API name")
    api_description: str = Field(default="", max_length=500, description="API description")
    encrypted_api_key: str = Field(..., description="Encrypted API key")
    encrypted_api_secret: str = Field(..., description="Encrypted API secret")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True, description="Whether API is active")
    last_used: Optional[datetime] = Field(default=None, description="Last time API was used")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
    
    @field_validator('api_name')
    @classmethod
    def validate_api_name(cls, v: str) -> str:
        """Validate API name."""
        if not v.strip():
            raise ValueError("API name cannot be empty")
        return v.strip()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        data = self.model_dump(by_alias=True, exclude={'id'})
        if self.id:
            data['_id'] = str(self.id)
        return data


class APICredentialCreate(BaseModel):
    """Model for creating new API credentials."""
    
    user_id: int
    api_name: str = Field(..., min_length=1, max_length=100)
    api_description: str = Field(default="", max_length=500)
    api_key: str = Field(..., min_length=10, description="Plain API key (will be encrypted)")
    api_secret: str = Field(..., min_length=10, description="Plain API secret (will be encrypted)")
    
    @field_validator('api_key', 'api_secret')
    @classmethod
    def validate_credentials(cls, v: str) -> str:
        """Validate API credentials."""
        if not v.strip():
            raise ValueError("API credentials cannot be empty")
        return v.strip()


class APICredentialUpdate(BaseModel):
    """Model for updating API credentials."""
    
    api_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_description: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, min_length=10)
    api_secret: Optional[str] = Field(None, min_length=10)
    is_active: Optional[bool] = None


if __name__ == "__main__":
    # Test model
    api_cred = APICredential(
        user_id=12345,
        api_name="Test API",
        api_description="Test API for development",
        encrypted_api_key="encrypted_key_here",
        encrypted_api_secret="encrypted_secret_here"
    )
    
    print(api_cred.model_dump_json(indent=2))
