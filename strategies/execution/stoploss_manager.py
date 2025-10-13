"""
Stop-loss order management.
"""

from typing import Dict, Any, List

from bot.utils.logger import setup_logger
from delta.client import DeltaClient
from delta.utils.order_type_validator import get_order_type_for_sl, get_exit_side

logger = setup_logger(__name__)


async def place_stoploss_orders(
    client: DeltaClient,
    positions: List[Dict[str, Any]],
    sl_trigger_pct: float,
    sl_limit_pct: float,
    direction: str
) -> Dict[str, Any]:
    """
    Place stop-loss orders for positions.
    
    Args:
        client: Delta Exchange client
        positions: List of position dictionaries
        sl_trigger_pct: SL trigger percentage
        sl_limit_pct: SL limit percentage
        direction: Position direction (long/short)
    
    Returns:
        Dictionary with SL order results
    """
    try:
        logger.info(f"Placing SL orders for {len(positions)} position(s)")
        
        placed_sl_orders = []
        
        for position in positions:
            entry_price = position['entry_price']
            product_id = position['product_id']
            size = abs(position['size'])
            
            # Calculate SL prices
            if direction == "long":
                sl_trigger = entry_price * (1 - sl_trigger_pct / 100)
                sl_limit = entry_price * (1 - sl_limit_pct / 100)
            else:
                sl_trigger = entry_price * (1 + sl_trigger_pct / 100)
                sl_limit = entry_price * (1 + sl_limit_pct / 100)
            
            # Determine order type and side
            order_type = get_order_type_for_sl(direction, is_option=True)
            side = get_exit_side(direction)
            
            # Create SL order
            if order_type == "bracket_order":
                # Bracket order (for long options SL)
                sl_order = {
                    'product_id': product_id,
                    'size': size,
                    'side': side,
                    'bracket_stop_trigger_price': str(sl_trigger),
                    'bracket_stop_limit_price': str(sl_limit)
                }
                
                response = await client.place_bracket_order(sl_order)
            else:
                # Limit order (for short options SL)
                sl_order = {
                    'product_id': product_id,
                    'size': size,
                    'side': side,
                    'order_type': 'limit_order',
                    'limit_price': str(sl_limit)
                }
                
                response = await client.place_order(sl_order)
            
            if response.get('success'):
                placed_sl_orders.append(response['result'])
                logger.info(f"Placed SL order for product {product_id}")
            else:
                logger.error(f"Failed to place SL order: {response.get('error')}")
        
        return {
            'success': True,
            'orders': placed_sl_orders
        }
    
    except Exception as e:
        logger.error(f"Failed to place SL orders: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def move_sl_to_cost(
    client: DeltaClient,
    position: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Move stop-loss to cost (breakeven).
    
    Args:
        client: Delta Exchange client
        position: Position dictionary
    
    Returns:
        Dictionary with result
    """
    try:
        entry_price = position['entry_price']
        product_id = position['product_id']
        size = abs(position['size'])
        direction = "long" if position['size'] > 0 else "short"
        
        # Calculate breakeven prices
        if direction == "long":
            sl_trigger = entry_price
            sl_limit = entry_price * 0.98  # 2% below cost
        else:
            sl_trigger = entry_price
            sl_limit = entry_price * 1.02  # 2% above cost
        
        # Get order type and side
        order_type = get_order_type_for_sl(direction, is_option=True)
        side = get_exit_side(direction)
        
        # Place SL to cost order
        if order_type == "bracket_order":
            sl_order = {
                'product_id': product_id,
                'size': size,
                'side': side,
                'bracket_stop_trigger_price': str(sl_trigger),
                'bracket_stop_limit_price': str(sl_limit)
            }
            
            response = await client.place_bracket_order(sl_order)
        else:
            sl_order = {
                'product_id': product_id,
                'size': size,
                'side': side,
                'order_type': 'limit_order',
                'limit_price': str(sl_limit)
            }
            
            response = await client.place_order(sl_order)
        
        if response.get('success'):
            logger.info(f"Moved SL to cost for product {product_id}")
            return {
                'success': True,
                'order': response['result']
            }
        else:
            return {
                'success': False,
                'error': response.get('error')
            }
    
    except Exception as e:
        logger.error(f"Failed to move SL to cost: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    print("Stoploss manager module loaded")
  
