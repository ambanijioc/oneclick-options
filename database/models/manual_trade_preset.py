"""
Manual trade preset database model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

from .api_credentials import PyObjectId


class ManualTradePreset(BaseModel):
    """Manual trade preset model - saved API + Strategy combination."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    preset_name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    api_credential_id: str = Field(..., description="API credential ID")
    strategy_preset_id: str = Field(..., description="Strategy preset ID")
    strategy_type: str = Field(..., description="Strategy type (straddle/strangle)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        data = self.model_dump(by_alias=True, exclude={'id'})
        if self.id:
            data['_id'] = ObjectId(self.id) if isinstance(self.id, str) else self.id
        return data
      
