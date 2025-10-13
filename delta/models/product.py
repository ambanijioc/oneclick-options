"""
Product models for Delta Exchange.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProductType(str, Enum):
    """Product types."""
    FUTURE = "future"
    PERPETUAL = "perpetual_futures"
    CALL_OPTION = "call_options"
    PUT_OPTION = "put_options"
    SPOT = "spot"
    INTEREST_RATE_SWAPS = "interest_rate_swaps"
    MOVE = "move_options"


class Product(BaseModel):
    """Product model."""
    
    id: int = Field(..., description="Product ID")
    symbol: str = Field(..., description="Product symbol")
    description: str = Field(default="", description="Product description")
    contract_type: ProductType = Field(..., description="Contract type")
    settlement_time: Optional[datetime] = Field(None, description="Settlement time")
    underlying_asset: Optional[str] = Field(None, description="Underlying asset symbol")
    quote_asset: Optional[str] = Field(None, description="Quote asset symbol")
    tick_size: float = Field(..., description="Minimum price increment")
    contract_value: float = Field(..., description="Contract value")
    strike_price: Optional[float] = Field(None, description="Strike price (for options)")
    is_active: bool = Field(default=True, description="Whether product is active")


class Ticker(BaseModel):
    """Ticker model."""
    
    symbol: str = Field(..., description="Product symbol")
    mark_price: Optional[float] = Field(None, description="Mark price")
    last_price: Optional[float] = Field(None, description="Last traded price")
    bid: Optional[float] = Field(None, description="Best bid price")
    ask: Optional[float] = Field(None, description="Best ask price")
    volume: float = Field(default=0.0, description="24h volume")
    open_interest: float = Field(default=0.0, description="Open interest")
    funding_rate: Optional[float] = Field(None, description="Funding rate (for perpetuals)")
    index_price: Optional[float] = Field(None, description="Index price")
    high_24h: Optional[float] = Field(None, description="24h high")
    low_24h: Optional[float] = Field(None, description="24h low")
    change_24h: Optional[float] = Field(None, description="24h change percentage")


if __name__ == "__main__":
    # Test product model
    product = Product(
        id=12345,
        symbol="BTCUSD",
        contract_type=ProductType.PERPETUAL,
        underlying_asset="BTC",
        quote_asset="USD",
        tick_size=0.5,
        contract_value=1.0
    )
    
    print("Product data:")
    print(product.model_dump_json(indent=2))
    
    # Test ticker model
    ticker = Ticker(
        symbol="BTCUSD",
        mark_price=65000.0,
        last_price=64995.0,
        bid=64990.0,
        ask=65000.0,
        volume=1000000.0,
        open_interest=50000.0
    )
    
    print("\nTicker data:")
    print(ticker.model_dump_json(indent=2))
  
