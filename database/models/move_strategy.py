"""
MOVE strategy database model with expiry selection.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

from .api_credentials import PyObjectId


class MoveStrategyBase(BaseModel):
    """MOVE trading strategy model."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    strategy_name: str = Field(..., description="Strategy name")
    asset: str = Field(..., description="BTC or ETH")
    expiry: str = Field(default="daily", description="Expiry type: daily, weekly, or monthly")
    direction: str = Field(..., description="long (volatility) or short (stability)")
    lot_size: int = Field(default=1, description="Number of contracts")
    atm_offset: int = Field(default=0, description="Strike offset from ATM (0 = ATM, +1/-1 = offset)")
    
    # Stop Loss (percentages)
    stop_loss_trigger: Optional[float] = Field(default=None, description="SL trigger % (e.g., 50 for 50%)")
    stop_loss_limit: Optional[float] = Field(default=None, description="SL limit % (e.g., 55 for 55%)")
    
    # Target (percentages)
    target_trigger: Optional[float] = Field(default=None, description="Target trigger % (e.g., 100 for 100%)")
    target_limit: Optional[float] = Field(default=None, description="Target limit % (e.g., 95 for 95%)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class MoveStrategyCreate(BaseModel):
    """Schema for creating MOVE strategy."""
    strategy_name: str
    asset: str
    expiry: str = "daily"
    direction: str
    lot_size: int = 1
    atm_offset: int = 0
    stop_loss_trigger: Optional[float] = None
    stop_loss_limit: Optional[float] = None
    target_trigger: Optional[float] = None
    target_limit: Optional[float] = None


class MoveStrategyUpdate(BaseModel):
    """Schema for updating MOVE strategy."""
    strategy_name: Optional[str] = None
    asset: Optional[str] = None
    expiry: Optional[str] = None
    direction: Optional[str] = None
    lot_size: Optional[int] = None
    atm_offset: Optional[int] = None
    stop_loss_trigger: Optional[float] = None
    stop_loss_limit: Optional[float] = None
    target_trigger: Optional[float] = None
    target_limit: Optional[float] = None
    
