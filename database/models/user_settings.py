"""
Pydantic models for user settings.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

# Import PyObjectId from api_credentials (it's already defined there)
from .api_credentials import PyObjectId


class UserSettings(BaseModel):
    """
    User settings model for storing user preferences.
    """
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID", unique=True)
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    
    # Preferences
    default_api_id: Optional[str] = Field(None, description="Default API credential ID")
    notifications_enabled: bool = Field(default=True, description="Enable trade notifications")
    log_trades: bool = Field(default=True, description="Log all trades to history")
    
    # Rate limiting
    daily_trade_limit: int = Field(default=20, description="Maximum trades per day")
    trades_today: int = Field(default=0, description="Number of trades executed today")
    last_trade_date: Optional[datetime] = Field(None, description="Date of last trade")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")
    
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
    
    def can_trade_today(self) -> bool:
        """Check if user can execute more trades today."""
        # Reset counter if it's a new day
        if self.last_trade_date and self.last_trade_date.date() < datetime.now().date():
            self.trades_today = 0
        
        return self.trades_today < self.daily_trade_limit
    
    def increment_trade_count(self):
        """Increment today's trade count."""
        current_date = datetime.now().date()
        
        # Reset if new day
        if self.last_trade_date and self.last_trade_date.date() < current_date:
            self.trades_today = 0
        
        self.trades_today += 1
        self.last_trade_date = datetime.now()


class UserSettingsCreate(BaseModel):
    """Model for creating new user settings."""
    
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    notifications_enabled: bool = True
    log_trades: bool = True
    daily_trade_limit: int = 20


class UserSettingsUpdate(BaseModel):
    """Model for updating user settings."""
    
    default_api_id: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    log_trades: Optional[bool] = None
    daily_trade_limit: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
