"""
Move strategy database model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MoveStrategy(BaseModel):
    """Move strategy preset model."""
    
    user_id: int
    strategy_name: str
    asset: str  # BTC or ETH
    direction: str  # long or short
    lot_size: int
    atm_offset: int  # 0 for ATM, +/- for offset
    stop_loss_trigger: Optional[float] = None
    stop_loss_limit: Optional[float] = None
    target_trigger: Optional[float] = None
    target_limit: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }  # ✅ FIXED - Added closing brace


class MoveAutoExecution(BaseModel):
    """Move options auto execution schedule model."""
    
    user_id: int
    api_credential_id: str
    strategy_name: str
    execution_time: str  # Format: "HH:MM AM/PM IST"
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }  # ✅ FIXED - Added closing brace
