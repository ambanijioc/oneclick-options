"""
Strike price rounding utilities.
"""

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_strike_increment(asset: str) -> int:
    """
    Get strike price increment for asset.
    
    Args:
        asset: Asset symbol (BTC or ETH)
    
    Returns:
        Strike increment
    
    Raises:
        ValueError: If asset is not supported
    """
    increments = {
        'BTC': 200,
        'ETH': 20
    }
    
    asset_upper = asset.upper()
    
    if asset_upper not in increments:
        raise ValueError(f"Unsupported asset: {asset}. Supported: {list(increments.keys())}")
    
    return increments[asset_upper]


def round_to_strike(price: float, asset: str) -> int:
    """
    Round price to nearest valid strike.
    
    Args:
        price: Price to round
        asset: Asset symbol (BTC or ETH)
    
    Returns:
        Rounded strike price
    
    Example:
        >>> round_to_strike(65432.50, "BTC")
        65400  # Rounded to nearest 200
        
        >>> round_to_strike(3456.78, "ETH")
        3460  # Rounded to nearest 20
    """
    try:
        increment = get_strike_increment(asset)
        
        # Round to nearest increment
        strike = round(price / increment) * increment
        
        logger.debug(f"Rounded {price:.2f} to {strike} for {asset}")
        
        return int(strike)
    
    except Exception as e:
        logger.error(f"Failed to round strike: {e}", exc_info=True)
        raise


def round_up_to_strike(price: float, asset: str) -> int:
    """
    Round price UP to next valid strike.
    
    Args:
        price: Price to round
        asset: Asset symbol
    
    Returns:
        Rounded up strike price
    """
    try:
        increment = get_strike_increment(asset)
        
        # Round up
        import math
        strike = math.ceil(price / increment) * increment
        
        logger.debug(f"Rounded {price:.2f} up to {strike} for {asset}")
        
        return int(strike)
    
    except Exception as e:
        logger.error(f"Failed to round up strike: {e}", exc_info=True)
        raise


def round_down_to_strike(price: float, asset: str) -> int:
    """
    Round price DOWN to previous valid strike.
    
    Args:
        price: Price to round
        asset: Asset symbol
    
    Returns:
        Rounded down strike price
    """
    try:
        increment = get_strike_increment(asset)
        
        # Round down
        import math
        strike = math.floor(price / increment) * increment
        
        logger.debug(f"Rounded {price:.2f} down to {strike} for {asset}")
        
        return int(strike)
    
    except Exception as e:
        logger.error(f"Failed to round down strike: {e}", exc_info=True)
        raise


def is_valid_strike(strike: int, asset: str) -> bool:
    """
    Check if strike is valid for asset.
    
    Args:
        strike: Strike price
        asset: Asset symbol
    
    Returns:
        True if strike is valid, False otherwise
    """
    try:
        increment = get_strike_increment(asset)
        is_valid = (strike % increment) == 0
        
        if not is_valid:
            logger.warning(f"Invalid strike {strike} for {asset} (increment: {increment})")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"Failed to validate strike: {e}", exc_info=True)
        return False


def get_nearest_strikes(price: float, asset: str, count: int = 5) -> list:
    """
    Get nearest valid strikes around a price.
    
    Args:
        price: Reference price
        asset: Asset symbol
        count: Number of strikes on each side
    
    Returns:
        List of nearest strikes (sorted)
    """
    try:
        increment = get_strike_increment(asset)
        center_strike = round_to_strike(price, asset)
        
        strikes = []
        for i in range(-count, count + 1):
            strike = center_strike + (i * increment)
            strikes.append(strike)
        
        logger.debug(f"Generated {len(strikes)} strikes around {price:.2f} for {asset}")
        
        return strikes
    
    except Exception as e:
        logger.error(f"Failed to get nearest strikes: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test strike rounder
    print("Strike Rounder Tests\n")
    
    # Test BTC
    print("BTC (increment: 200)")
    test_prices = [65432.50, 65100.00, 65600.00, 64999.99]
    for price in test_prices:
        rounded = round_to_strike(price, "BTC")
        up = round_up_to_strike(price, "BTC")
        down = round_down_to_strike(price, "BTC")
        print(f"  {price:8.2f} -> Round: {rounded}, Up: {up}, Down: {down}")
    
    print("\n" + "="*50 + "\n")
    
    # Test ETH
    print("ETH (increment: 20)")
    test_prices = [3456.78, 3410.00, 3490.00, 3499.99]
    for price in test_prices:
        rounded = round_to_strike(price, "ETH")
        up = round_up_to_strike(price, "ETH")
        down = round_down_to_strike(price, "ETH")
        print(f"  {price:7.2f} -> Round: {rounded}, Up: {up}, Down: {down}")
    
    print("\n" + "="*50 + "\n")
    
    # Test validation
    print("Strike Validation:")
    print(f"  65400 (BTC): {is_valid_strike(65400, 'BTC')}")
    print(f"  65450 (BTC): {is_valid_strike(65450, 'BTC')}")
    print(f"  3460 (ETH): {is_valid_strike(3460, 'ETH')}")
    print(f"  3455 (ETH): {is_valid_strike(3455, 'ETH')}")
    
    print("\n" + "="*50 + "\n")
    
    # Test nearest strikes
    print("Nearest Strikes (BTC, 65432.50, ±2):")
    strikes = get_nearest_strikes(65432.50, "BTC", 2)
    print(f"  {strikes}")
  
