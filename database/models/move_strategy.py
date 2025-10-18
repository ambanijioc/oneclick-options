"""
MOVE strategy database model - FIXED VERSION.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class MoveStrategyBase(BaseModel):
    """MOVE trading strategy model with name and description."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    
    # Basic Info
    strategy_name: str = Field(..., description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    
    # Trading Parameters
    asset: str = Field(..., description="BTC or ETH")
    expiry: str = Field(default="daily", description="Expiry type: daily, weekly, or monthly")
    direction: str = Field(..., description="long (volatility) or short (stability)")
    atm_offset: int = Field(default=0, description="Strike offset from ATM")
    
    # Stop Loss (optional)
    stop_loss_trigger: Optional[float] = Field(None, description="SL trigger % (e.g., 50 for 50%)")
    stop_loss_limit: Optional[float] = Field(None, description="SL limit % (e.g., 55 for 55%)")
    
    # Target (optional)
    target_trigger: Optional[float] = Field(None, description="Target trigger % (e.g., 100 for 100%)")
    target_limit: Optional[float] = Field(None, description="Target limit % (e.g., 95 for 95%)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class MoveTradePresetBase(BaseModel):
    """MOVE trade preset linking API and Strategy."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    
    # Basic Info
    preset_name: str = Field(..., description="Preset name")
    
    # Links
    api_id: str = Field(..., description="API credential ID")
    strategy_id: str = Field(..., description="MOVE strategy ID")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        
