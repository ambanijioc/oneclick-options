"""
Pydantic models for API credentials.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
            raise ValueError("Invalid ObjectId")
        raise ValueError("Invalid ObjectId type")


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
            data['_id'] = ObjectId(self.id) if isinstance(self.id, str) else self.id
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
    
