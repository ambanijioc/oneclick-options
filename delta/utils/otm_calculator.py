"""
OTM (Out of The Money) strike calculator for strangle strategies.
"""

from typing import Tuple
from .strike_rounder import round_to_strike, get_strike_increment
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_otm_by_percentage(
    spot_price: float,
    asset: str,
    percentage: float
) -> Tuple[int, int]:
    """
    Calculate OTM strikes based on percentage from spot.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        percentage: Percentage distance from spot (e.g., 5.0 for 5%)
    
    Returns:
        Tuple of (call_strike, put_strike)
    
    Example:
        >>> calculate_otm_by_percentage(65000, "BTC", 5.0)
        (68400, 61800)
        # Call: 65000 * 1.05 = 68250 → rounded to 68400
        # Put: 65000 * 0.95 = 61750 → rounded to 61800
    """
    try:
        # Calculate distance
        distance = spot_price * (percentage / 100)
        
        # Calculate raw OTM prices
        call_price = spot_price + distance
        put_price = spot_price - distance
        
        # Round to valid strikes
        call_strike = round_to_strike(call_price, asset)
        put_strike = round_to_strike(put_price, asset)
        
        logger.debug(
            f"OTM by percentage {percentage}% for {asset}: "
            f"Spot={spot_price:.2f}, Call={call_strike}, Put={put_strike}"
        )
        
        return (call_strike, put_strike)
    
    except Exception as e:
        logger.error(f"Failed to calculate OTM by percentage: {e}", exc_info=True)
        raise


def calculate_otm_by_numeral(
    spot_price: float,
    asset: str,
    distance: float
) -> Tuple[int, int]:
    """
    Calculate OTM strikes based on fixed distance from spot.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        distance: Fixed distance from spot price
    
    Returns:
        Tuple of (call_strike, put_strike)
    
    Example:
        >>> calculate_otm_by_numeral(65000, "BTC", 2000)
        (67000, 63000)
        # Call: 65000 + 2000 = 67000
        # Put: 65000 - 2000 = 63000
    """
    try:
        # Calculate raw OTM prices
        call_price = spot_price + distance
        put_price = spot_price - distance
        
        # Round to valid strikes
        call_strike = round_to_strike(call_price, asset)
        put_strike = round_to_strike(put_price, asset)
        
        logger.debug(
            f"OTM by numeral {distance} for {asset}: "
            f"Spot={spot_price:.2f}, Call={call_strike}, Put={put_strike}"
        )
        
        return (call_strike, put_strike)
    
    except Exception as e:
        logger.error(f"Failed to calculate OTM by numeral: {e}", exc_info=True)
        raise


def calculate_otm_strikes(
    spot_price: float,
    asset: str,
    selection_type: str,
    value: float
) -> Tuple[int, int]:
    """
    Calculate OTM strikes using specified method.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        selection_type: "percentage" or "numeral"
        value: Selection value
    
    Returns:
        Tuple of (call_strike, put_strike)
    
    Raises:
        ValueError: If selection_type is invalid
    """
    try:
        if selection_type == "percentage":
            return calculate_otm_by_percentage(spot_price, asset, value)
        elif selection_type == "numeral":
            return calculate_otm_by_numeral(spot_price, asset, value)
        else:
            raise ValueError(f"Invalid selection_type: {selection_type}")
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate OTM strikes: {e}", exc_info=True)
        raise


def calculate_otm_range(
    spot_price: float,
    asset: str,
    min_percentage: float,
    max_percentage: float,
    step_percentage: float = 1.0
) -> list:
    """
    Calculate a range of OTM strike pairs.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol
        min_percentage: Minimum OTM percentage
        max_percentage: Maximum OTM percentage
        step_percentage: Step size for percentage
    
    Returns:
        List of (call_strike, put_strike) tuples
    
    Example:
        >>> calculate_otm_range(65000, "BTC", 3.0, 7.0, 2.0)
        [(67000, 63000), (69000, 61000), (71000, 59000)]
    """
    try:
        ranges = []
        current_pct = min_percentage
        
        while current_pct <= max_percentage:
            strikes = calculate_otm_by_percentage(spot_price, asset, current_pct)
            ranges.append(strikes)
            current_pct += step_percentage
        
        logger.debug(f"OTM range for {asset}: {len(ranges)} pairs")
        
        return ranges
    
    except Exception as e:
        logger.error(f"Failed to calculate OTM range: {e}", exc_info=True)
        raise


def get_otm_strikes_by_delta(
    spot_price: float,
    asset: str,
    target_delta: float = 0.25
) -> Tuple[int, int]:
    """
    Estimate OTM strikes based on target delta (simplified).
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol
        target_delta: Target delta (0.1 to 0.4)
    
    Returns:
        Tuple of (call_strike, put_strike)
    
    Note:
        This is a simplified calculation. Real delta-based strikes
        require option pricing models and volatility data.
    """
    try:
        # Simplified: Higher delta = closer to ATM
        # 0.5 delta ≈ ATM
        # 0.25 delta ≈ ~5-10% OTM
        # 0.1 delta ≈ ~15-20% OTM
        
        # Rough approximation
        if target_delta >= 0.4:
            percentage = 2.0
        elif target_delta >= 0.3:
            percentage = 5.0
        elif target_delta >= 0.2:
            percentage = 10.0
        else:
            percentage = 15.0
        
        call_strike, put_strike = calculate_otm_by_percentage(
            spot_price, asset, percentage
        )
        
        logger.debug(
            f"OTM strikes for delta {target_delta}: "
            f"Call={call_strike}, Put={put_strike}"
        )
        
        return (call_strike, put_strike)
    
    except Exception as e:
        logger.error(f"Failed to calculate OTM by delta: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test OTM calculator
    print("OTM Calculator Tests\n")
    
    # Test BTC
    btc_spot = 65000
    print(f"BTC Spot: ${btc_spot}")
    print(f"OTM 5%: {calculate_otm_by_percentage(btc_spot, 'BTC', 5.0)}")
    print(f"OTM 10%: {calculate_otm_by_percentage(btc_spot, 'BTC', 10.0)}")
    print(f"OTM 2000: {calculate_otm_by_numeral(btc_spot, 'BTC', 2000)}")
    print(f"OTM 5000: {calculate_otm_by_numeral(btc_spot, 'BTC', 5000)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test ETH
    eth_spot = 3500
    print(f"ETH Spot: ${eth_spot}")
    print(f"OTM 5%: {calculate_otm_by_percentage(eth_spot, 'ETH', 5.0)}")
    print(f"OTM 10%: {calculate_otm_by_percentage(eth_spot, 'ETH', 10.0)}")
    print(f"OTM 200: {calculate_otm_by_numeral(eth_spot, 'ETH', 200)}")
    print(f"OTM 500: {calculate_otm_by_numeral(eth_spot, 'ETH', 500)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test range
    print("OTM Range (BTC, 3-7%, step 2%):")
    ranges = calculate_otm_range(btc_spot, 'BTC', 3.0, 7.0, 2.0)
    for i, (call, put) in enumerate(ranges, 1):
        print(f"  {i}. Call: {call}, Put: {put}")
      
