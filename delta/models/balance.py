"""
Balance models for Delta Exchange.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MarginMode(str, Enum):
    """Margin modes."""
    CROSS = "cross_margin"
    ISOLATED = "isolated_margin"


class Balance(BaseModel):
    """Wallet balance model."""
    
    asset_id: int = Field(..., description="Asset ID")
    asset_symbol: str = Field(..., description="Asset symbol")
    available_balance: float = Field(default=0.0, description="Available balance")
    balance: float = Field(default=0.0, description="Total balance")
    order_margin: float = Field(default=0.0, description="Margin locked in orders")
    position_margin: float = Field(default=0.0, description="Margin used in positions")
    commission: float = Field(default=0.0, description="Commission paid")
    unrealized_pnl: float = Field(default=0.0, description="Unrealized PnL")
    unrealized_funding: float = Field(default=0.0, description="Unrealized funding")
    
    @property
    def used_margin(self) -> float:
        """Calculate total used margin."""
        return self.order_margin + self.position_margin
    
    @property
    def total_equity(self) -> float:
        """Calculate total equity."""
        return self.balance + self.unrealized_pnl
    
    @property
    def margin_usage_percentage(self) -> float:
        """Calculate margin usage percentage."""
        if self.balance == 0:
            return 0.0
        return (self.used_margin / self.balance) * 100


if __name__ == "__main__":
    # Test balance model
    balance = Balance(
        asset_id=1,
        asset_symbol="USDT",
        available_balance=10000.0,
        balance=12500.0,
        order_margin=500.0,
        position_margin=2000.0,
        unrealized_pnl=150.0
    )
    
    print("Balance data:")
    print(balance.model_dump_json(indent=2))
    print(f"\nUsed Margin: ${balance.used_margin}")
    print(f"Total Equity: ${balance.total_equity}")
    print(f"Margin Usage: {balance.margin_usage_percentage:.2f}%")
  
