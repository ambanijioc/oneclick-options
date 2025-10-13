"""
Strike price calculation utilities.
Handles ATM, OTM, and strike price rounding for BTC and ETH options.
"""

from typing import Tuple, Optional
from logger import logger, log_function_call


@log_function_call
def get_strike_increment(asset: str) -> int:
    """
    Get strike price increment for asset.
    
    Args:
        asset: Asset symbol (BTC or ETH)
    
    Returns:
        Strike increment value
    """
    increments = {
        'BTC': 200,
        'ETH': 20
    }
    
    increment = increments.get(asset.upper(), 100)
    logger.debug(f"[calculations.get_strike_increment] {asset} increment: {increment}")
    
    return increment


@log_function_call
def calculate_atm_strike(spot_price: float, asset: str) -> float:
    """
    Calculate At-The-Money (ATM) strike price.
    Rounds spot price to nearest strike increment.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
    
    Returns:
        ATM strike price
    
    Example:
        BTC spot: 95234.5 -> ATM: 95200 (rounded to nearest 200)
        ETH spot: 3456.7 -> ATM: 3460 (rounded to nearest 20)
    """
    try:
        increment = get_strike_increment(asset)
        atm_strike = round(spot_price / increment) * increment
        
        logger.info(
            f"[calculations.calculate_atm_strike] {asset} spot: {spot_price}, "
            f"ATM strike: {atm_strike}"
        )
        
        return atm_strike
        
    except Exception as e:
        logger.error(f"[calculations.calculate_atm_strike] Error: {e}")
        return spot_price


@log_function_call
def calculate_otm_strikes(
    spot_price: float,
    asset: str,
    otm_percentage: Optional[float] = None,
    otm_value: Optional[int] = None
) -> Tuple[float, float]:
    """
    Calculate Out-of-The-Money (OTM) strike prices for call and put.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        otm_percentage: OTM percentage from spot (e.g., 1.0 for 1%)
        otm_value: OTM absolute value from spot (e.g., 1000)
    
    Returns:
        Tuple of (call_strike, put_strike)
    
    Example:
        BTC spot: 95000, OTM 1%
        - Offset: 95000 * 0.01 = 950
        - Call raw: 95000 + 950 = 95950 -> rounded to 96000
        - Put raw: 95000 - 950 = 94050 -> rounded to 94000
    """
    try:
        increment = get_strike_increment(asset)
        
        # Calculate offset
        if otm_percentage is not None:
            offset = spot_price * (otm_percentage / 100)
        elif otm_value is not None:
            offset = float(otm_value)
        else:
            raise ValueError("Either otm_percentage or otm_value must be provided")
        
        # Calculate raw strike prices
        call_strike_raw = spot_price + offset
        put_strike_raw = spot_price - offset
        
        # Round to nearest increment
        call_strike = round(call_strike_raw / increment) * increment
        put_strike = round(put_strike_raw / increment) * increment
        
        logger.info(
            f"[calculations.calculate_otm_strikes] {asset} spot: {spot_price}, "
            f"offset: {offset}, Call: {call_strike}, Put: {put_strike}"
        )
        
        return call_strike, put_strike
        
    except Exception as e:
        logger.error(f"[calculations.calculate_otm_strikes] Error: {e}")
        # Return ATM strikes as fallback
        atm = calculate_atm_strike(spot_price, asset)
        return atm, atm


@log_function_call
def calculate_strike_from_offset(
    atm_strike: float,
    offset: int,
    asset: str
) -> float:
    """
    Calculate strike price from ATM with offset.
    
    Args:
        atm_strike: ATM strike price
        offset: Number of strikes to offset (positive or negative)
        asset: Asset symbol (BTC or ETH)
    
    Returns:
        Calculated strike price
    
    Example:
        BTC ATM: 95200, offset: +2 -> 95200 + (2 * 200) = 95600
        BTC ATM: 95200, offset: -1 -> 95200 + (-1 * 200) = 95000
    """
    try:
        increment = get_strike_increment(asset)
        strike = atm_strike + (offset * increment)
        
        logger.info(
            f"[calculations.calculate_strike_from_offset] {asset} ATM: {atm_strike}, "
            f"offset: {offset}, strike: {strike}"
        )
        
        return strike
        
    except Exception as e:
        logger.error(f"[calculations.calculate_strike_from_offset] Error: {e}")
        return atm_strike


@log_function_call
def validate_strike_price(strike: float, asset: str) -> bool:
    """
    Validate that strike price is aligned to proper increment.
    
    Args:
        strike: Strike price to validate
        asset: Asset symbol
    
    Returns:
        True if valid, False otherwise
    """
    try:
        increment = get_strike_increment(asset)
        is_valid = (strike % increment) == 0
        
        if not is_valid:
            logger.warning(
                f"[calculations.validate_strike_price] Invalid strike {strike} "
                f"for {asset} (increment: {increment})"
            )
        
        return is_valid
        
    except Exception as e:
        logger.error(f"[calculations.validate_strike_price] Error: {e}")
        return False


@log_function_call
def calculate_straddle_strikes(
    spot_price: float,
    asset: str,
    atm_offset: int = 0
) -> Tuple[float, float]:
    """
    Calculate straddle strike prices (same strike for call and put).
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol
        atm_offset: ATM offset in strike increments (default 0)
    
    Returns:
        Tuple of (call_strike, put_strike) - both same value
    """
    try:
        # Calculate ATM
        atm_strike = calculate_atm_strike(spot_price, asset)
        
        # Apply offset
        if atm_offset != 0:
            strike = calculate_strike_from_offset(atm_strike, atm_offset, asset)
        else:
            strike = atm_strike
        
        logger.info(
            f"[calculations.calculate_straddle_strikes] {asset} spot: {spot_price}, "
            f"ATM: {atm_strike}, offset: {atm_offset}, strike: {strike}"
        )
        
        return strike, strike
        
    except Exception as e:
        logger.error(f"[calculations.calculate_straddle_strikes] Error: {e}")
        atm = calculate_atm_strike(spot_price, asset)
        return atm, atm


@log_function_call
def calculate_breakeven_points(
    strike_call: float,
    strike_put: float,
    premium_call: float,
    premium_put: float,
    is_long: bool
) -> Tuple[float, float]:
    """
    Calculate breakeven points for straddle/strangle.
    
    Args:
        strike_call: Call strike price
        strike_put: Put strike price
        premium_call: Call option premium paid/received
        premium_put: Put option premium paid/received
        is_long: True if long position
    
    Returns:
        Tuple of (upper_breakeven, lower_breakeven)
    """
    try:
        total_premium = premium_call + premium_put
        
        if is_long:
            # Long straddle/strangle
            upper_breakeven = strike_call + total_premium
            lower_breakeven = strike_put - total_premium
        else:
            # Short straddle/strangle
            upper_breakeven = strike_call + total_premium
            lower_breakeven = strike_put - total_premium
        
        logger.info(
            f"[calculations.calculate_breakeven_points] Upper: {upper_breakeven}, "
            f"Lower: {lower_breakeven}"
        )
        
        return upper_breakeven, lower_breakeven
        
    except Exception as e:
        logger.error(f"[calculations.calculate_breakeven_points] Error: {e}")
        return 0.0, 0.0


if __name__ == "__main__":
    # Test calculations
    print("Testing strike calculations...")
    
    # Test ATM calculation
    btc_spot = 95234.5
    atm = calculate_atm_strike(btc_spot, "BTC")
    print(f"✅ BTC ATM: Spot={btc_spot}, ATM={atm}")
    
    eth_spot = 3456.7
    atm = calculate_atm_strike(eth_spot, "ETH")
    print(f"✅ ETH ATM: Spot={eth_spot}, ATM={atm}")
    
    # Test OTM calculation
    call_strike, put_strike = calculate_otm_strikes(btc_spot, "BTC", otm_percentage=1.0)
    print(f"✅ BTC OTM 1%: Call={call_strike}, Put={put_strike}")
    
    # Test strike from offset
    strike = calculate_strike_from_offset(95200, 2, "BTC")
    print(f"✅ BTC ATM 95200 + offset 2: {strike}")
    
    # Test straddle strikes
    call_strike, put_strike = calculate_straddle_strikes(btc_spot, "BTC", atm_offset=0)
    print(f"✅ BTC Straddle strikes: Call={call_strike}, Put={put_strike}")
    
    # Test strike validation
    is_valid = validate_strike_price(95200, "BTC")
    print(f"✅ Strike 95200 valid for BTC: {is_valid}")
    
    is_valid = validate_strike_price(95250, "BTC")
    print(f"❌ Strike 95250 valid for BTC: {is_valid}")
    
    print("\n✅ Calculation tests completed!")
  
