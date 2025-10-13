"""
Pydantic models for data validation and structure.
All database documents follow these schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import pytz


class DirectionEnum(str, Enum):
    """Trade direction enumeration."""
    LONG = "long"
    SHORT = "short"


class AssetEnum(str, Enum):
    """Supported trading assets."""
    BTC = "BTC"
    ETH = "ETH"


class StrategyTypeEnum(str, Enum):
    """Strategy types."""
    STRADDLE = "straddle"
    STRANGLE = "strangle"


class OrderStatusEnum(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class StopLossTargetConfig(BaseModel):
    """Stop loss and target configuration."""
    trigger_percentage: float = Field(..., description="Trigger price percentage")
    limit_percentage: Optional[float] = Field(None, description="Limit price percentage")
    
    @field_validator('trigger_percentage')
    @classmethod
    def validate_trigger(cls, v: float) -> float:
        if not -100 <= v <= 100:
            raise ValueError("Trigger percentage must be between -100 and 100")
        return v


class APICredentials(BaseModel):
    """API credentials model for Delta Exchange."""
    user_id: int = Field(..., description="Telegram user ID")
    api_name: str = Field(..., description="Friendly name for API")
    api_description: Optional[str] = Field(None, description="API description")
    api_key: str = Field(..., description="Delta Exchange API key")
    encrypted_api_secret: str = Field(..., description="Encrypted API secret")
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    is_active: bool = Field(default=True, description="Whether API is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "api_name": "Main Account",
                "api_description": "Primary trading account",
                "api_key": "your_api_key",
                "encrypted_api_secret": "encrypted_secret_here",
                "is_active": True
            }
        }


class StraddleStrategy(BaseModel):
    """Straddle strategy preset model."""
    user_id: int = Field(..., description="Telegram user ID")
    strategy_name: str = Field(..., description="Strategy name")
    strategy_description: Optional[str] = Field(None, description="Strategy description")
    asset: AssetEnum = Field(..., description="Trading asset (BTC/ETH)")
    expiry: str = Field(..., description="Expiry notation (D, D+1, W, M, etc.)")
    direction: DirectionEnum = Field(..., description="Long or short")
    lot_size: int = Field(..., gt=0, description="Number of lots")
    atm_offset: int = Field(default=0, description="ATM offset in strike increments")
    stoploss_config: Optional[StopLossTargetConfig] = Field(None, description="Stop loss config")
    target_config: Optional[StopLossTargetConfig] = Field(None, description="Target config")
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    is_active: bool = Field(default=True, description="Whether strategy is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "strategy_name": "Conservative Daily Straddle",
                "asset": "BTC",
                "expiry": "D",
                "direction": "long",
                "lot_size": 1,
                "atm_offset": 0,
                "stoploss_config": {"trigger_percentage": -5.0, "limit_percentage": -5.5},
                "target_config": {"trigger_percentage": 10.0, "limit_percentage": 9.5}
            }
        }


class StrangleStrategy(BaseModel):
    """Strangle strategy preset model."""
    user_id: int = Field(..., description="Telegram user ID")
    strategy_name: str = Field(..., description="Strategy name")
    strategy_description: Optional[str] = Field(None, description="Strategy description")
    asset: AssetEnum = Field(..., description="Trading asset (BTC/ETH)")
    expiry: str = Field(..., description="Expiry notation (D, D+1, W, M, etc.)")
    direction: DirectionEnum = Field(..., description="Long or short")
    lot_size: int = Field(..., gt=0, description="Number of lots")
    otm_percentage: Optional[float] = Field(None, description="OTM percentage from spot")
    otm_value: Optional[int] = Field(None, description="OTM value from spot")
    stoploss_config: Optional[StopLossTargetConfig] = Field(None, description="Stop loss config")
    target_config: Optional[StopLossTargetConfig] = Field(None, description="Target config")
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    is_active: bool = Field(default=True, description="Whether strategy is active")
    
    @field_validator('otm_percentage', 'otm_value')
    @classmethod
    def validate_otm(cls, v, info):
        """Ensure either percentage or value is provided, not both."""
        values = info.data
        if 'otm_percentage' in values and 'otm_value' in values:
            if values.get('otm_percentage') and values.get('otm_value'):
                raise ValueError("Provide either otm_percentage or otm_value, not both")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "strategy_name": "Weekly Strangle 1%",
                "asset": "BTC",
                "expiry": "W",
                "direction": "long",
                "lot_size": 1,
                "otm_percentage": 1.0,
                "stoploss_config": {"trigger_percentage": -5.0, "limit_percentage": -5.5}
            }
        }


class Position(BaseModel):
    """Trading position model."""
    product_id: int = Field(..., description="Delta Exchange product ID")
    product_symbol: str = Field(..., description="Product symbol")
    size: float = Field(..., description="Position size (negative for short)")
    entry_price: float = Field(..., description="Average entry price")
    current_price: Optional[float] = Field(None, description="Current mark price")
    unrealized_pnl: Optional[float] = Field(None, description="Unrealized PnL")
    margin: Optional[float] = Field(None, description="Margin used")
    liquidation_price: Optional[float] = Field(None, description="Liquidation price")


class Order(BaseModel):
    """Order model."""
    order_id: str = Field(..., description="Delta Exchange order ID")
    product_id: int = Field(..., description="Product ID")
    product_symbol: str = Field(..., description="Product symbol")
    order_type: str = Field(..., description="Order type (limit, market, etc.)")
    side: str = Field(..., description="Buy or sell")
    size: float = Field(..., description="Order size")
    price: Optional[float] = Field(None, description="Order price")
    stop_price: Optional[float] = Field(None, description="Stop trigger price")
    status: OrderStatusEnum = Field(..., description="Order status")
    filled_size: float = Field(default=0.0, description="Filled quantity")
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))


class TradeHistory(BaseModel):
    """Trade history record model."""
    user_id: int = Field(..., description="Telegram user ID")
    api_name: str = Field(..., description="API name used for trade")
    strategy_type: StrategyTypeEnum = Field(..., description="Strategy type used")
    strategy_name: str = Field(..., description="Strategy name")
    asset: AssetEnum = Field(..., description="Asset traded")
    direction: DirectionEnum = Field(..., description="Trade direction")
    entry_time: datetime = Field(..., description="Entry timestamp")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    entry_prices: Dict[str, float] = Field(..., description="Entry prices for each leg")
    exit_prices: Optional[Dict[str, float]] = Field(None, description="Exit prices")
    lot_size: int = Field(..., description="Lot size")
    pnl: Optional[float] = Field(None, description="Realized PnL")
    commission: Optional[float] = Field(None, description="Total commission")
    positions: List[Dict[str, Any]] = Field(default_factory=list, description="Position details")
    orders: List[str] = Field(default_factory=list, description="Order IDs")
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "api_name": "Main Account",
                "strategy_type": "straddle",
                "strategy_name": "Daily ATM",
                "asset": "BTC",
                "direction": "long",
                "entry_time": "2025-10-13T09:30:00Z",
                "entry_prices": {"95200_CE": 1200.0, "95200_PE": 1100.0},
                "lot_size": 1,
                "pnl": 245.50,
                "commission": 12.50
            }
        }


class AutoExecutionSchedule(BaseModel):
    """Automated execution schedule model."""
    user_id: int = Field(..., description="Telegram user ID")
    schedule_name: str = Field(..., description="Schedule name")
    api_name: str = Field(..., description="API to use for execution")
    strategy_type: StrategyTypeEnum = Field(..., description="Strategy type")
    strategy_name: str = Field(..., description="Strategy preset name")
    execution_time: str = Field(..., description="Execution time (HH:MM AM/PM IST)")
    is_active: bool = Field(default=True, description="Whether schedule is active")
    last_executed: Optional[datetime] = Field(None, description="Last execution timestamp")
    next_execution: Optional[datetime] = Field(None, description="Next scheduled execution")
    execution_count: int = Field(default=0, description="Number of times executed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    
    @field_validator('execution_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format is HH:MM AM/PM."""
        import re
        pattern = r'^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM|am|pm)$'
        if not re.match(pattern, v):
            raise ValueError("Time must be in format HH:MM AM/PM")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "schedule_name": "Morning BTC Straddle",
                "api_name": "Main Account",
                "strategy_type": "straddle",
                "strategy_name": "Conservative Daily",
                "execution_time": "09:30 AM",
                "is_active": True
            }
        }


if __name__ == "__main__":
    # Test model validation
    print("Testing Pydantic models...")
    
    # Test APICredentials
    api_creds = APICredentials(
        user_id=123456789,
        api_name="Test API",
        api_key="test_key",
        encrypted_api_secret="test_secret"
    )
    print(f"✅ APICredentials: {api_creds.api_name}")
    
    # Test StraddleStrategy
    straddle = StraddleStrategy(
        user_id=123456789,
        strategy_name="Test Straddle",
        asset=AssetEnum.BTC,
        expiry="D",
        direction=DirectionEnum.LONG,
        lot_size=1
    )
    print(f"✅ StraddleStrategy: {straddle.strategy_name}")
    
    # Test AutoExecutionSchedule
    schedule = AutoExecutionSchedule(
        user_id=123456789,
        schedule_name="Test Schedule",
        api_name="Test API",
        strategy_type=StrategyTypeEnum.STRADDLE,
        strategy_name="Test Strategy",
        execution_time="09:30 AM"
    )
    print(f"✅ AutoExecutionSchedule: {schedule.execution_time}")
    
    print("\n✅ All models validated successfully!")
  
