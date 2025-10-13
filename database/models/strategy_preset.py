"""
Pydantic models for strategy presets.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId

from .api_credentials import PyObjectId


class OTMSelection(BaseModel):
    """OTM selection configuration for strangle strategies."""
    
    type: Literal["percentage", "numeral"] = Field(..., description="Selection type")
    value: float = Field(..., gt=0, description="Selection value")
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: float, info) -> float:
        """Validate OTM value based on type."""
        if info.data.get('type') == 'percentage' and v > 100:
            raise ValueError("Percentage value cannot exceed 100")
        return v


class StrategyPreset(BaseModel):
    """
    Base strategy preset model.
    """
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    strategy_type: Literal["straddle", "strangle"] = Field(..., description="Strategy type")
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: str = Field(default="", max_length=500, description="Strategy description")
    asset: Literal["BTC", "ETH"] = Field(..., description="Trading asset")
    expiry_code: str = Field(..., description="Expiry code (D, D+1, W, M, etc.)")
    direction: Literal["long", "short"] = Field(..., description="Trade direction")
    lot_size: int = Field(..., gt=0, description="Lot size")
    sl_trigger_pct: float = Field(..., ge=0, le=100, description="Stop-loss trigger percentage")
    sl_limit_pct: float = Field(..., ge=0, le=100, description="Stop-loss limit percentage")
    target_trigger_pct: float = Field(default=0, ge=0, le=100, description="Target trigger percentage (0 for none)")
    target_limit_pct: float = Field(default=0, ge=0, le=100, description="Target limit percentage")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True, description="Whether preset is active")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate strategy name."""
        if not v.strip():
            raise ValueError("Strategy name cannot be empty")
        return v.strip()
    
    @field_validator('expiry_code')
    @classmethod
    def validate_expiry_code(cls, v: str) -> str:
        """Validate expiry code format."""
        valid_codes = ['D', 'D+1', 'D+2', 'W', 'W+1', 'W+2', 'M', 'M+1', 'M+2']
        if v.upper() not in valid_codes:
            raise ValueError(f"Invalid expiry code. Must be one of: {', '.join(valid_codes)}")
        return v.upper()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        data = self.model_dump(by_alias=True, exclude={'id'})
        if self.id:
            data['_id'] = str(self.id)
        return data


class StraddlePreset(StrategyPreset):
    """
    Straddle strategy preset model.
    Trades ATM call and put options.
    """
    
    strategy_type: Literal["straddle"] = "straddle"
    atm_offset: int = Field(default=0, description="ATM offset (0 for exact ATM, ±n for offset)")
    
    @field_validator('atm_offset')
    @classmethod
    def validate_atm_offset(cls, v: int) -> int:
        """Validate ATM offset is reasonable."""
        if abs(v) > 10:
            raise ValueError("ATM offset must be between -10 and 10")
        return v


class StranglePreset(StrategyPreset):
    """
    Strangle strategy preset model.
    Trades OTM call and put options.
    """
    
    strategy_type: Literal["strangle"] = "strangle"
    otm_selection: OTMSelection = Field(..., description="OTM strike selection configuration")


class StrategyPresetCreate(BaseModel):
    """Model for creating new strategy preset."""
    
    user_id: int
    strategy_type: Literal["straddle", "strangle"]
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    asset: Literal["BTC", "ETH"]
    expiry_code: str
    direction: Literal["long", "short"]
    lot_size: int = Field(..., gt=0)
    sl_trigger_pct: float = Field(..., ge=0, le=100)
    sl_limit_pct: float = Field(..., ge=0, le=100)
    target_trigger_pct: float = Field(default=0, ge=0, le=100)
    target_limit_pct: float = Field(default=0, ge=0, le=100)
    
    # Straddle-specific
    atm_offset: Optional[int] = Field(default=0)
    
    # Strangle-specific
    otm_selection: Optional[OTMSelection] = None
    
    @field_validator('otm_selection')
    @classmethod
    def validate_otm_for_strangle(cls, v, info) -> Optional[OTMSelection]:
        """Validate OTM selection is provided for strangle strategies."""
        if info.data.get('strategy_type') == 'strangle' and v is None:
            raise ValueError("OTM selection is required for strangle strategies")
        return v


if __name__ == "__main__":
    # Test models
    straddle = StraddlePreset(
        user_id=12345,
        name="BTC Weekly Straddle",
        description="Weekly BTC straddle strategy",
        asset="BTC",
        expiry_code="W",
        direction="long",
        lot_size=10,
        sl_trigger_pct=50.0,
        sl_limit_pct=55.0,
        target_trigger_pct=100.0,
        target_limit_pct=95.0,
        atm_offset=0
    )
    print("Straddle Preset:")
    print(straddle.model_dump_json(indent=2))
    
    print("\n" + "="*50 + "\n")
    
    strangle = StranglePreset(
        user_id=12345,
        name="ETH Monthly Strangle",
        description="Monthly ETH strangle strategy",
        asset="ETH",
        expiry_code="M",
        direction="long",
        lot_size=20,
        sl_trigger_pct=50.0,
        sl_limit_pct=55.0,
        target_trigger_pct=100.0,
        target_limit_pct=95.0,
        otm_selection=OTMSelection(type="percentage", value=5.0)
    )
    print("Strangle Preset:")
    print(strangle.model_dump_json(indent=2))
  
