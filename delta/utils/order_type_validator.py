"""
Order type validation for stop-loss and target orders.
"""

from typing import Dict, Tuple
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_order_type_for_sl(position_side: str, is_option: bool = True) -> str:
    """
    Get appropriate order type for stop-loss based on position.
    
    Args:
        position_side: Position side ("long" or "short")
        is_option: Whether position is an option
    
    Returns:
        Order type for stop-loss
    
    Logic:
        - Long options: SL uses bracket order (stop-market)
        - Short options: SL uses limit order
    """
    if is_option:
        if position_side.lower() == "long":
            # Long position needs to sell to exit
            # Use bracket/stop-market order
            order_type = "bracket_order"
        else:
            # Short position needs to buy to exit
            # Use limit order
            order_type = "limit_order"
    else:
        # For futures/perpetuals, always use stop orders
        order_type = "stop_market_order"
    
    logger.debug(
        f"SL order type for {position_side} {'option' if is_option else 'future'}: "
        f"{order_type}"
    )
    
    return order_type


def get_order_type_for_target(position_side: str, is_option: bool = True) -> str:
    """
    Get appropriate order type for target/take-profit based on position.
    
    Args:
        position_side: Position side ("long" or "short")
        is_option: Whether position is an option
    
    Returns:
        Order type for target
    
    Logic:
        - Long options: Target uses limit order
        - Short options: Target uses bracket order (to buy back)
    """
    if is_option:
        if position_side.lower() == "long":
            # Long position uses limit order to sell at profit
            order_type = "limit_order"
        else:
            # Short position uses bracket order to buy back at profit
            order_type = "bracket_order"
    else:
        # For futures/perpetuals, use limit orders
        order_type = "limit_order"
    
    logger.debug(
        f"Target order type for {position_side} {'option' if is_option else 'future'}: "
        f"{order_type}"
    )
    
    return order_type


def validate_sl_target_order_types(
    position_side: str,
    is_option: bool = True
) -> Dict[str, str]:
    """
    Get valid order types for both SL and target.
    
    Args:
        position_side: Position side ("long" or "short")
        is_option: Whether position is an option
    
    Returns:
        Dictionary with sl_order_type and target_order_type
    """
    try:
        sl_order_type = get_order_type_for_sl(position_side, is_option)
        target_order_type = get_order_type_for_target(position_side, is_option)
        
        result = {
            'sl_order_type': sl_order_type,
            'target_order_type': target_order_type,
            'position_side': position_side,
            'is_option': is_option
        }
        
        logger.debug(f"Order types validated: {result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to validate order types: {e}", exc_info=True)
        raise


def can_use_bracket_order(position_side: str, order_purpose: str) -> bool:
    """
    Check if bracket order can be used.
    
    Args:
        position_side: Position side ("long" or "short")
        order_purpose: Purpose ("sl" or "target")
    
    Returns:
        True if bracket order can be used, False otherwise
    """
    try:
        if order_purpose.lower() == "sl":
            # Long positions can use bracket for SL
            can_use = position_side.lower() == "long"
        elif order_purpose.lower() == "target":
            # Short positions can use bracket for target
            can_use = position_side.lower() == "short"
        else:
            can_use = False
        
        logger.debug(
            f"Bracket order for {position_side} {order_purpose}: "
            f"{'allowed' if can_use else 'not allowed'}"
        )
        
        return can_use
    
    except Exception as e:
        logger.error(f"Failed to check bracket order availability: {e}", exc_info=True)
        return False


def get_exit_side(position_side: str) -> str:
    """
    Get order side needed to exit a position.
    
    Args:
        position_side: Current position side ("long" or "short")
    
    Returns:
        Order side needed to exit ("sell" for long, "buy" for short)
    """
    if position_side.lower() == "long":
        return "sell"
    elif position_side.lower() == "short":
        return "buy"
    else:
        raise ValueError(f"Invalid position_side: {position_side}")


if __name__ == "__main__":
    # Test order type validator
    print("Order Type Validator Tests\n")
    
    # Test long options
    print("Long Options:")
    result = validate_sl_target_order_types("long", is_option=True)
    print(f"  SL: {result['sl_order_type']}")
    print(f"  Target: {result['target_order_type']}")
    print(f"  Bracket for SL: {can_use_bracket_order('long', 'sl')}")
    print(f"  Bracket for Target: {can_use_bracket_order('long', 'target')}")
    print(f"  Exit side: {get_exit_side('long')}")
    
    print("\n" + "="*50 + "\n")
    
    # Test short options
    print("Short Options:")
    result = validate_sl_target_order_types("short", is_option=True)
    print(f"  SL: {result['sl_order_type']}")
    print(f"  Target: {result['target_order_type']}")
    print(f"  Bracket for SL: {can_use_bracket_order('short', 'sl')}")
    print(f"  Bracket for Target: {can_use_bracket_order('short', 'target')}")
    print(f"  Exit side: {get_exit_side('short')}")
    
    print("\n" + "="*50 + "\n")
    
    # Test futures
    print("Long Futures:")
    result = validate_sl_target_order_types("long", is_option=False)
    print(f"  SL: {result['sl_order_type']}")
    print(f"  Target: {result['target_order_type']}")
  
