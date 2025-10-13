"""
Strangle strategy implementation.
"""

from typing import Dict, Any, List, Tuple

from .base_strategy import BaseStrategy
from delta.utils.otm_calculator import calculate_otm_strikes
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


class StrangleStrategy(BaseStrategy):
    """
    Strangle strategy: Buy/sell OTM call and put with different strikes.
    """
    
    async def calculate_strikes(self, spot_price: float, params: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate OTM strikes for strangle.
        
        Args:
            spot_price: Current spot price
            params: Parameters with 'otm_selection'
        
        Returns:
            Dictionary with call_strike and put_strike
        """
        otm_selection = params.get('otm_selection', {})
        otm_type = otm_selection.get('type', 'percentage')
        otm_value = otm_selection.get('value', 5.0)
        
        # Calculate OTM strikes
        call_strike, put_strike = calculate_otm_strikes(
            spot_price,
            self.asset,
            otm_type,
            otm_value
        )
        
        logger.info(
            f"Strangle strikes calculated: {self.asset} "
            f"Call={call_strike}, Put={put_strike} "
            f"({otm_type}={otm_value})"
        )
        
        return {
            'call_strike': call_strike,
            'put_strike': put_strike,
            'spot_price': spot_price
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate strangle parameters.
        
        Args:
            params: Strategy parameters
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check OTM selection
        otm_selection = params.get('otm_selection')
        if not otm_selection:
            return False, "OTM selection is required for strangle"
        
        otm_type = otm_selection.get('type')
        if otm_type not in ['percentage', 'numeral']:
            return False, "OTM type must be 'percentage' or 'numeral'"
        
        otm_value = otm_selection.get('value', 0)
        if otm_value <= 0:
            return False, "OTM value must be positive"
        
        if otm_type == 'percentage' and otm_value > 50:
            return False, "OTM percentage should not exceed 50%"
        
        return True, ""
    
    def generate_order_list(
        self,
        strikes: Dict[str, int],
        product_ids: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Generate orders for strangle strategy.
        
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
        
        logger.info(f"Generated {len(orders)} orders for strangle strategy")
        
        return orders


if __name__ == "__main__":
    print("Strangle strategy module loaded")
  
