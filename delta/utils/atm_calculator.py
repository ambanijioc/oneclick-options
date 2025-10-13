"""
ATM (At The Money) strike calculator.
"""

from typing import Tuple
from .strike_rounder import round_to_strike
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_atm_strike(
    spot_price: float,
    asset: str,
    offset: int = 0
) -> int:
    """
    Calculate ATM strike price.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        offset: Strike offset (0 for exact ATM, ±n for n strikes away)
    
    Returns:
        ATM strike price
    
    Example:
        >>> calculate_atm_strike(65432.50, "BTC", 0)
        65400  # Rounded to nearest 200
        
        >>> calculate_atm_strike(65432.50, "BTC", 1)
        65600  # One strike above ATM
        
        >>> calculate_atm_strike(65432.50, "BTC", -1)
        65200  # One strike below ATM
    """
    try:
        # Round to nearest strike
        atm_strike = round_to_strike(spot_price, asset)
        
        # Apply offset
        if offset != 0:
            from .strike_rounder import get_strike_increment
            increment = get_strike_increment(asset)
            atm_strike += (offset * increment)
        
        logger.debug(
            f"Calculated ATM strike for {asset}: "
            f"Spot={spot_price:.2f}, Strike={atm_strike}, Offset={offset}"
        )
        
        return atm_strike
    
    except Exception as e:
        logger.error(f"Failed to calculate ATM strike: {e}", exc_info=True)
        raise


def get_atm_call_put_strikes(
    spot_price: float,
    asset: str,
    offset: int = 0
) -> Tuple[int, int]:
    """
    Get ATM call and put strike prices.
    For straddle strategies, both call and put have the same strike.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        offset: Strike offset
    
    Returns:
        Tuple of (call_strike, put_strike)
    
    Example:
        >>> get_atm_call_put_strikes(65432.50, "BTC", 0)
        (65400, 65400)
    """
    try:
        atm_strike = calculate_atm_strike(spot_price, asset, offset)
        
        # For straddle, both call and put use the same strike
        logger.debug(f"ATM Call/Put strikes for {asset}: {atm_strike}")
        
        return (atm_strike, atm_strike)
    
    except Exception as e:
        logger.error(f"Failed to get ATM call/put strikes: {e}", exc_info=True)
        raise


def calculate_atm_range(
    spot_price: float,
    asset: str,
    range_strikes: int = 5
) -> list:
    """
    Calculate a range of strikes around ATM.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol
        range_strikes: Number of strikes on each side of ATM
    
    Returns:
        List of strike prices around ATM
    
    Example:
        >>> calculate_atm_range(65432.50, "BTC", 2)
        [65000, 65200, 65400, 65600, 65800]
    """
    try:
        atm_strike = calculate_atm_strike(spot_price, asset)
        from .strike_rounder import get_strike_increment
        increment = get_strike_increment(asset)
        
        strikes = []
        for i in range(-range_strikes, range_strikes + 1):
            strike = atm_strike + (i * increment)
            strikes.append(strike)
        
        logger.debug(f"ATM range for {asset}: {strikes}")
        
        return strikes
    
    except Exception as e:
        logger.error(f"Failed to calculate ATM range: {e}", exc_info=True)
        raise


def get_atm_premium_estimate(
    spot_price: float,
    asset: str,
    volatility: float = 0.5
) -> dict:
    """
    Estimate premium for ATM options (simplified calculation).
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol
        volatility: Implied volatility (default 50%)
    
    Returns:
        Dictionary with estimated premiums
    
    Note:
        This is a simplified estimate. Real premiums should be fetched from API.
    """
    try:
        atm_strike = calculate_atm_strike(spot_price, asset)
        
        # Simplified premium calculation (roughly volatility * sqrt(time) * price)
        # Assuming 1 day to expiry for estimate
        estimated_premium = spot_price * volatility * 0.06  # Rough estimate
        
        result = {
            'atm_strike': atm_strike,
            'estimated_call_premium': estimated_premium,
            'estimated_put_premium': estimated_premium,
            'note': 'This is an estimate. Use real market data for trading.'
        }
        
        logger.debug(f"ATM premium estimate for {asset}: {result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to estimate ATM premium: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test ATM calculator
    print("ATM Calculator Tests\n")
    
    # Test BTC
    btc_spot = 65432.50
    print(f"BTC Spot: ${btc_spot}")
    print(f"ATM Strike: {calculate_atm_strike(btc_spot, 'BTC')}")
    print(f"ATM +1: {calculate_atm_strike(btc_spot, 'BTC', 1)}")
    print(f"ATM -1: {calculate_atm_strike(btc_spot, 'BTC', -1)}")
    print(f"ATM Call/Put: {get_atm_call_put_strikes(btc_spot, 'BTC')}")
    print(f"ATM Range: {calculate_atm_range(btc_spot, 'BTC', 2)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test ETH
    eth_spot = 3456.78
    print(f"ETH Spot: ${eth_spot}")
    print(f"ATM Strike: {calculate_atm_strike(eth_spot, 'ETH')}")
    print(f"ATM +2: {calculate_atm_strike(eth_spot, 'ETH', 2)}")
    print(f"ATM -2: {calculate_atm_strike(eth_spot, 'ETH', -2)}")
    print(f"ATM Call/Put: {get_atm_call_put_strikes(eth_spot, 'ETH')}")
    print(f"ATM Range: {calculate_atm_range(eth_spot, 'ETH', 3)}")
  
