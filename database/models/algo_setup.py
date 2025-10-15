"""
Algo setup database model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

from .api_credentials import PyObjectId


class AlgoSetup(BaseModel):
    """Algo trading setup model."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    manual_preset_id: str = Field(..., description="Manual trade preset ID")
    execution_time: str = Field(..., description="Execution time in IST (HH:MM format)")
    is_active: bool = Field(default=True, description="Whether setup is active")
    last_execution: Optional[datetime] = Field(default=None, description="Last execution timestamp")
    last_execution_status: Optional[str] = Field(default=None, description="Last execution status")
    last_execution_details: Optional[dict] = Field(default=None, description="Last execution details")
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
      
