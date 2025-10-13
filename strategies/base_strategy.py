"""
Base strategy class for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    """
    
    def __init__(self, asset: str, direction: str, lot_size: int):
        """
        Initialize strategy.
        
        Args:
            asset: Asset symbol (BTC/ETH)
            direction: Trade direction (long/short)
            lot_size: Position lot size
        """
        self.asset = asset
        self.direction = direction
        self.lot_size = lot_size
    
    @abstractmethod
    async def calculate_strikes(self, spot_price: float, params: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate strike prices for the strategy.
        
        Args:
            spot_price: Current spot price
            params: Strategy-specific parameters
        
        Returns:
            Dictionary with strike information
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate strategy parameters.
        
        Args:
            params: Strategy parameters
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def generate_order_list(
        self,
        strikes: Dict[str, int],
        product_ids: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Generate list of orders for the strategy.
        
        Args:
            strikes: Strike information
            product_ids: Product IDs for each option
        
        Returns:
            List of order dictionaries
        """
        pass
    
    def calculate_sl_target_prices(
        self,
        entry_price: float,
        sl_trigger_pct: float,
        sl_limit_pct: float,
        target_trigger_pct: float,
        target_limit_pct: float
    ) -> Dict[str, float]:
        """
        Calculate stop-loss and target prices.
        
        Args:
            entry_price: Average entry price
            sl_trigger_pct: SL trigger percentage
            sl_limit_pct: SL limit percentage
            target_trigger_pct: Target trigger percentage
            target_limit_pct: Target limit percentage
        
        Returns:
            Dictionary with SL and target prices
        """
        # For long positions
        if self.direction == "long":
            sl_trigger = entry_price * (1 - sl_trigger_pct / 100)
            sl_limit = entry_price * (1 - sl_limit_pct / 100)
            target_trigger = entry_price * (1 + target_trigger_pct / 100) if target_trigger_pct > 0 else 0
            target_limit = entry_price * (1 + target_limit_pct / 100) if target_limit_pct > 0 else 0
        
        # For short positions
        else:
            sl_trigger = entry_price * (1 + sl_trigger_pct / 100)
            sl_limit = entry_price * (1 + sl_limit_pct / 100)
            target_trigger = entry_price * (1 - target_trigger_pct / 100) if target_trigger_pct > 0 else 0
            target_limit = entry_price * (1 - target_limit_pct / 100) if target_limit_pct > 0 else 0
        
        return {
            'sl_trigger': sl_trigger,
            'sl_limit': sl_limit,
            'target_trigger': target_trigger,
            'target_limit': target_limit
        }


if __name__ == "__main__":
    print("Base strategy module loaded")
  
