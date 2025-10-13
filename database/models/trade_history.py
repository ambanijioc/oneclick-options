"""
Pydantic models for trade history.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

from .api_credentials import PyObjectId


class OrderInfo(BaseModel):
    """Information about an order in a trade."""
    
    order_id: str = Field(..., description="Delta Exchange order ID")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Order side (buy/sell)")
    order_type: str = Field(..., description="Order type (limit/market/bracket)")
    size: float = Field(..., description="Order size")
    price: Optional[float] = Field(None, description="Order price")
    status: str = Field(..., description="Order status")
    filled_size: float = Field(default=0, description="Filled size")
    avg_fill_price: Optional[float] = Field(None, description="Average fill price")


class TradeHistory(BaseModel):
    """
    Trade history model for storing executed trades.
    """
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    api_id: str = Field(..., description="API credential ID")
    strategy_type: str = Field(..., description="Strategy type (straddle/strangle)")
    strategy_preset_id: Optional[str] = Field(None, description="Strategy preset ID if used")
    asset: str = Field(..., description="Trading asset (BTC/ETH)")
    expiry: str = Field(..., description="Option expiry date")
    
    # Entry information
    entry_time: datetime = Field(default_factory=datetime.now, description="Entry timestamp")
    entry_orders: List[OrderInfo] = Field(default_factory=list, description="Entry order details")
    entry_price: float = Field(..., description="Average entry price")
    lot_size: int = Field(..., description="Position lot size")
    
    # Exit information
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    exit_orders: List[OrderInfo] = Field(default_factory=list, description="Exit order details")
    exit_price: Optional[float] = Field(None, description="Average exit price")
    exit_reason: Optional[str] = Field(None, description="Exit reason (sl/target/manual)")
    
    # Financial metrics
    realized_pnl: Optional[float] = Field(None, description="Realized PnL")
    commission: float = Field(default=0, description="Total commission paid")
    net_pnl: Optional[float] = Field(None, description="Net PnL after commission")
    roi_percentage: Optional[float] = Field(None, description="ROI percentage")
    
    # Status
    status: str = Field(default="open", description="Trade status (open/closed)")
    notes: str = Field(default="", description="Additional notes")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        data = self.model_dump(by_alias=True, exclude={'id'})
        if self.id:
            data['_id'] = str(self.id)
        return data
    
    def calculate_net_pnl(self):
        """Calculate net PnL after commission."""
        if self.realized_pnl is not None:
            self.net_pnl = self.realized_pnl - self.commission
    
    def calculate_roi(self, invested_amount: float):
        """Calculate ROI percentage."""
        if invested_amount > 0 and self.net_pnl is not None:
            self.roi_percentage = (self.net_pnl / invested_amount) * 100


class TradeHistoryCreate(BaseModel):
    """Model for creating new trade history entry."""
    
    user_id: int
    api_id: str
    strategy_type: str
    strategy_preset_id: Optional[str] = None
    asset: str
    expiry: str
    entry_orders: List[OrderInfo]
    entry_price: float
    lot_size: int
    commission: float = 0


if __name__ == "__main__":
    # Test model
    trade = TradeHistory(
        user_id=12345,
        api_id="507f1f77bcf86cd799439011",
        strategy_type="straddle",
        asset="BTC",
        expiry="2025-10-20",
        entry_orders=[
            OrderInfo(
                order_id="order_123",
                symbol="BTCUSD-20OCT25-65000-C",
                side="buy",
                order_type="limit",
                size=10,
                price=1000.0,
                status="filled",
                filled_size=10,
                avg_fill_price=1000.0
            ),
            OrderInfo(
                order_id="order_124",
                symbol="BTCUSD-20OCT25-65000-P",
                side="buy",
                order_type="limit",
                size=10,
                price=1000.0,
                status="filled",
                filled_size=10,
                avg_fill_price=1000.0
            )
        ],
        entry_price=2000.0,
        lot_size=10,
        commission=5.0
    )
    
    print(trade.model_dump_json(indent=2))
  
