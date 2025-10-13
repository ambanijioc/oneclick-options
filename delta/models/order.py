"""
Order models for Delta Exchange.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OrderType(str, Enum):
    """Order types."""
    LIMIT = "limit_order"
    MARKET = "market_order"
    STOP_MARKET = "stop_market_order"
    STOP_LIMIT = "stop_limit_order"


class OrderSide(str, Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


class TimeInForce(str, Enum):
    """Time in force options."""
    GTC = "gtc"  # Good till cancelled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill


class Order(BaseModel):
    """Order model."""
    
    product_id: int = Field(..., description="Product ID")
    size: int = Field(..., description="Order size")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    order_type: OrderType = Field(..., description="Order type")
    limit_price: Optional[str] = Field(None, description="Limit price (required for limit orders)")
    stop_price: Optional[str] = Field(None, description="Stop price (required for stop orders)")
    time_in_force: TimeInForce = Field(default=TimeInForce.GTC, description="Time in force")
    post_only: bool = Field(default=False, description="Post only (maker only)")
    reduce_only: bool = Field(default=False, description="Reduce only")
    client_order_id: Optional[str] = Field(None, description="Client order ID")
    
    def to_dict(self) -> dict:
        """Convert to API request format."""
        data = {
            'product_id': self.product_id,
            'size': self.size,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'time_in_force': self.time_in_force.value,
            'post_only': self.post_only,
            'reduce_only': self.reduce_only
        }
        
        if self.limit_price is not None:
            data['limit_price'] = str(self.limit_price)
        
        if self.stop_price is not None:
            data['stop_price'] = str(self.stop_price)
        
        if self.client_order_id:
            data['client_order_id'] = self.client_order_id
        
        return data


class BracketOrder(BaseModel):
    """Bracket order with stop loss and/or take profit."""
    
    product_id: int = Field(..., description="Product ID")
    size: int = Field(..., description="Order size")
    side: OrderSide = Field(..., description="Order side")
    limit_price: Optional[str] = Field(None, description="Entry limit price")
    stop_loss_order: Optional[dict] = Field(None, description="Stop loss order params")
    take_profit_order: Optional[dict] = Field(None, description="Take profit order params")
    bracket_stop_trigger_price: Optional[str] = Field(None, description="Bracket stop trigger")
    bracket_stop_limit_price: Optional[str] = Field(None, description="Bracket stop limit")
    bracket_take_profit_trigger_price: Optional[str] = Field(None, description="Bracket TP trigger")
    bracket_take_profit_limit_price: Optional[str] = Field(None, description="Bracket TP limit")
    
    def to_dict(self) -> dict:
        """Convert to API request format."""
        data = {
            'product_id': self.product_id,
            'size': self.size,
            'side': self.side.value
        }
        
        if self.limit_price is not None:
            data['limit_price'] = str(self.limit_price)
        
        if self.bracket_stop_trigger_price:
            data['bracket_stop_trigger_price'] = str(self.bracket_stop_trigger_price)
        
        if self.bracket_stop_limit_price:
            data['bracket_stop_limit_price'] = str(self.bracket_stop_limit_price)
        
        if self.bracket_take_profit_trigger_price:
            data['bracket_take_profit_trigger_price'] = str(self.bracket_take_profit_trigger_price)
        
        if self.bracket_take_profit_limit_price:
            data['bracket_take_profit_limit_price'] = str(self.bracket_take_profit_limit_price)
        
        return data


if __name__ == "__main__":
    # Test order model
    order = Order(
        product_id=12345,
        size=10,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        limit_price="65000"
    )
    
    print("Order data:")
    print(order.model_dump_json(indent=2))
    print("\nAPI format:")
    print(order.to_dict())
  
