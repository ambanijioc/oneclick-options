"""
Position models for Delta Exchange.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PositionSide(str, Enum):
    """Position sides."""
    LONG = "long"
    SHORT = "short"


class Position(BaseModel):
    """Position model."""
    
    product_id: int = Field(..., description="Product ID")
    product_symbol: str = Field(..., description="Product symbol")
    size: int = Field(..., description="Position size (+ for long, - for short)")
    entry_price: Optional[float] = Field(None, description="Average entry price")
    margin: float = Field(default=0.0, description="Position margin")
    liquidation_price: Optional[float] = Field(None, description="Liquidation price")
    bankruptcy_price: Optional[float] = Field(None, description="Bankruptcy price")
    unrealized_pnl: float = Field(default=0.0, description="Unrealized PnL")
    realized_pnl: float = Field(default=0.0, description="Realized PnL")
    realized_cashflow: float = Field(default=0.0, description="Realized cashflow")
    leverage: Optional[float] = Field(None, description="Position leverage")
    
    @property
    def side(self) -> PositionSide:
        """Get position side based on size."""
        return PositionSide.LONG if self.size > 0 else PositionSide.SHORT
    
    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.size > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.size < 0
    
    @property
    def abs_size(self) -> int:
        """Get absolute position size."""
        return abs(self.size)


if __name__ == "__main__":
    # Test position model
    position = Position(
        product_id=12345,
        product_symbol="BTCUSD",
        size=10,
        entry_price=65000.0,
        margin=6500.0,
        unrealized_pnl=500.0,
        leverage=10.0
    )
    
    print("Position data:")
    print(position.model_dump_json(indent=2))
    print(f"\nSide: {position.side}")
    print(f"Is Long: {position.is_long}")
    print(f"Absolute Size: {position.abs_size}")
  
