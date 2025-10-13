"""
Target order management.
"""

from typing import Dict, Any, List

from bot.utils.logger import setup_logger
from delta.client import DeltaClient
from delta.utils.order_type_validator import get_order_type_for_target, get_exit_side

logger = setup_logger(__name__)


async def place_target_orders(
    client: DeltaClient,
    positions: List[Dict[str, Any]],
    target_trigger_pct: float,
    target_limit_pct: float,
    direction: str
) -> Dict[str, Any]:
    """
    Place target (take-profit) orders for positions.
    
    Args:
        client: Delta Exchange client
        positions: List of position dictionaries
        target_trigger_pct: Target trigger percentage
        target_limit_pct: Target limit percentage
        direction: Position direction (long/short)
    
    Returns:
        Dictionary with target order results
    """
    try:
        logger.info(f"Placing target orders for {len(positions)} position(s)")
        
        placed_target_orders = []
        
        for position in positions:
            entry_price = position['entry_price']
            product_id = position['product_id']
            size = abs(position['size'])
            
            # Calculate target prices
            if direction == "long":
                target_trigger = entry_price * (1 + target_trigger_pct / 100)
                target_limit = entry_price * (1 + target_limit_pct / 100)
            else:
                target_trigger = entry_price * (1 - target_trigger_pct / 100)
                target_limit = entry_price * (1 - target_limit_pct / 100)
            
            # Determine order type and side
            order_type = get_order_type_for_target(direction, is_option=True)
            side = get_exit_side(direction)
            
            # Create target order
            if order_type == "limit_order":
                # Limit order (for long options target)
                target_order = {
                    'product_id': product_id,
                    'size': size,
                    'side': side,
                    'order_type': 'limit_order',
                    'limit_price': str(target_limit)
                }
                
                response = await client.place_order(target_order)
            else:
                # Bracket order (for short options target)
                target_order = {
                    'product_id': product_id,
                    'size': size,
                    'side': side,
                    'bracket_take_profit_trigger_price': str(target_trigger),
                    'bracket_take_profit_limit_price': str(target_limit)
                }
                
                response = await client.place_bracket_order(target_order)
            
            if response.get('success'):
                placed_target_orders.append(response['result'])
                logger.info(f"Placed target order for product {product_id}")
            else:
                logger.error(f"Failed to place target order: {response.get('error')}")
        
        return {
            'success': True,
            'orders': placed_target_orders
        }
    
    except Exception as e:
        logger.error(f"Failed to place target orders: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    print("Target manager module loaded")
  
