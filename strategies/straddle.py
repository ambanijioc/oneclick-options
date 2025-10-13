"""
Straddle strategy implementation.
"""

from typing import Dict, Any, List, Tuple

from .base_strategy import BaseStrategy
from delta.utils.atm_calculator import calculate_atm_strike
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


class StraddleStrategy(BaseStrategy):
    """
    Straddle strategy: Buy/sell ATM call and put with same strike.
    """
    
    async def calculate_strikes(self, spot_price: float, params: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate ATM strike for straddle.
        
        Args:
            spot_price: Current spot price
            params: Parameters with 'atm_offset'
        
        Returns:
            Dictionary with call_strike and put_strike
        """
        atm_offset = params.get('atm_offset', 0)
        
        # Calculate ATM strike
        atm_strike = calculate_atm_strike(spot_price, self.asset, atm_offset)
        
        logger.info(
            f"Straddle strikes calculated: {self.asset} ATM={atm_strike} "
            f"(offset={atm_offset})"
        )
        
        return {
            'call_strike': atm_strike,
            'put_strike': atm_strike,
            'spot_price': spot_price
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate straddle parameters.
        
        Args:
            params: Strategy parameters
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check ATM offset
        atm_offset = params.get('atm_offset', 0)
        if not isinstance(atm_offset, int):
            return False, "ATM offset must be an integer"
        
        if abs(atm_offset) > 10:
            return False, "ATM offset must be between -10 and +10"
        
        return True, ""
    
    def generate_order_list(
        self,
        strikes: Dict[str, int],
        product_ids: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Generate orders for straddle strategy.
        
        Args:
            strikes: Strike information
            product_ids: Product IDs for call and put
        
        Returns:
            List of order dictionaries
        """
        orders = []
        
        # Determine order side based on direction
        side = "buy" if self.direction == "long" else "sell"
        
        # Call order
        orders.append({
            'product_id': product_ids['call'],
            'size': self.lot_size,
            'side': side,
            'order_type': 'limit_order',
            'time_in_force': 'gtc'
        })
        
        # Put order
        orders.append({
            'product_id': product_ids['put'],
            'size': self.lot_size,
            'side': side,
            'order_type': 'limit_order',
            'time_in_force': 'gtc'
        })
        
        logger.info(f"Generated {len(orders)} orders for straddle strategy")
        
        return orders


if __name__ == "__main__":
    print("Straddle strategy module loaded")
  
