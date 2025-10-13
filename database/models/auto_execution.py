"""
Pydantic models for auto execution schedules.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId

from .api_credentials import PyObjectId


class AutoExecution(BaseModel):
    """
    Auto execution schedule model.
    """
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    api_id: str = Field(..., description="API credential ID")
    strategy_preset_id: str = Field(..., description="Strategy preset ID")
    execution_time: str = Field(..., description="Execution time in HH:MM format (IST)")
    enabled: bool = Field(default=True, description="Whether auto execution is enabled")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_execution: Optional[datetime] = Field(default=None, description="Last execution timestamp")
    last_execution_status: Optional[str] = Field(default=None, description="Last execution status")
    execution_count: int = Field(default=0, description="Total number of executions")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
    
    @field_validator('execution_time')
    @classmethod
    def validate_execution_time(cls, v: str) -> str:
        """Validate execution time format."""
        try:
            # Parse time to validate format
            time_parts = v.split(':')
            if len(time_parts) != 2:
                raise ValueError("Time must be in HH:MM format")
            
            hour, minute = int(time_parts[0]), int(time_parts[1])
            
            if not (0 <= hour <= 23):
                raise ValueError("Hour must be between 0 and 23")
            
            if not (0 <= minute <= 59):
                raise ValueError("Minute must be between 0 and 59")
            
            # Return formatted time
            return f"{hour:02d}:{minute:02d}"
        
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid time format. Use HH:MM (24-hour format): {e}")
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        data = self.model_dump(by_alias=True, exclude={'id'})
        if self.id:
            data['_id'] = ObjectId(self.id) if isinstance(self.id, str) else self.id
        return data


class AutoExecutionCreate(BaseModel):
    """Model for creating new auto execution schedule."""
    
    user_id: int
    api_id: str
    strategy_preset_id: str
    execution_time: str = Field(..., description="Execution time in HH:MM format (IST)")
    enabled: bool = Field(default=True)
    
    @field_validator('execution_time')
    @classmethod
    def validate_execution_time(cls, v: str) -> str:
        """Validate execution time format."""
        try:
            time_parts = v.split(':')
            if len(time_parts) != 2:
                raise ValueError("Time must be in HH:MM format")
            
            hour, minute = int(time_parts[0]), int(time_parts[1])
            
            if not (0 <= hour <= 23):
                raise ValueError("Hour must be between 0 and 23")
            
            if not (0 <= minute <= 59):
                raise ValueError("Minute must be between 0 and 59")
            
            return f"{hour:02d}:{minute:02d}"
        
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid time format. Use HH:MM (24-hour format): {e}")


class AutoExecutionUpdate(BaseModel):
    """Model for updating auto execution schedule."""
    
    execution_time: Optional[str] = None
    enabled: Optional[bool] = None
    last_execution_status: Optional[str] = None
    
