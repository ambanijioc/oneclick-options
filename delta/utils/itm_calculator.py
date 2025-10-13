"""
ITM (In The Money) strike calculator.
"""

from typing import Tuple
from .strike_rounder import round_to_strike, get_strike_increment
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_itm_strikes(
    spot_price: float,
    asset: str,
    percentage: float
) -> Tuple[int, int]:
    """
    Calculate ITM strikes based on percentage into the money.
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol (BTC or ETH)
        percentage: Percentage into the money (e.g., 5.0 for 5% ITM)
    
    Returns:
        Tuple of (call_strike, put_strike)
        - Call strike is BELOW spot (ITM for calls)
        - Put strike is ABOVE spot (ITM for puts)
    
    Example:
        >>> calculate_itm_strikes(65000, "BTC", 5.0)
        (61800, 68400)
        # Call: 65000 * 0.95 = 61750 → 61800 (below spot, ITM)
        # Put: 65000 * 1.05 = 68250 → 68400 (above spot, ITM)
    """
    try:
        # Calculate distance
        distance = spot_price * (percentage / 100)
        
        # For ITM:
        # - Call strike should be BELOW spot
        # - Put strike should be ABOVE spot
        call_price = spot_price - distance
        put_price = spot_price + distance
        
        # Round to valid strikes
        call_strike = round_to_strike(call_price, asset)
        put_strike = round_to_strike(put_price, asset)
        
        logger.debug(
            f"ITM strikes {percentage}% for {asset}: "
            f"Spot={spot_price:.2f}, Call={call_strike}, Put={put_strike}"
        )
        
        return (call_strike, put_strike)
    
    except Exception as e:
        logger.error(f"Failed to calculate ITM strikes: {e}", exc_info=True)
        raise


def calculate_deep_itm_strikes(
    spot_price: float,
    asset: str,
    num_strikes: int = 5
) -> dict:
    """
    Calculate deep ITM strikes (multiple strikes in the money).
    
    Args:
        spot_price: Current spot price
        asset: Asset symbol
        num_strikes: Number of ITM strikes to calculate
    
    Returns:
        Dictionary with call and put strike lists
    
    Example:
        >>> calculate_deep_itm_strikes(65000, "BTC", 3)
        {
            'call_strikes': [64800, 64600, 64400],
            'put_strikes': [65200, 65400, 65600]
        }
    """
    try:
        increment = get_strike_increment(asset)
        atm_strike = round_to_strike(spot_price, asset)
        
        call_strikes = []
        put_strikes = []
        
        for i in range(1, num_strikes + 1):
            # Calls: strikes below ATM
            call_strike = atm_strike - (i * increment)
            call_strikes.append(call_strike)
            
            # Puts: strikes above ATM
            put_strike = atm_strike + (i * increment)
            put_strikes.append(put_strike)
        
        result = {
            'call_strikes': call_strikes,
            'put_strikes': put_strikes,
            'atm_strike': atm_strike
        }
        
        logger.debug(f"Deep ITM strikes for {asset}: {result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to calculate deep ITM strikes: {e}", exc_info=True)
        raise


def is_strike_itm(
    strike: int,
    spot_price: float,
    option_type: str
) -> bool:
    """
    Check if a strike is in the money.
    
    Args:
        strike: Strike price
        spot_price: Current spot price
        option_type: "call" or "put"
    
    Returns:
        True if strike is ITM, False otherwise
    """
    try:
        if option_type.lower() == "call":
            # Call is ITM when strike < spot
            is_itm = strike < spot_price
        elif option_type.lower() == "put":
            # Put is ITM when strike > spot
            is_itm = strike > spot_price
        else:
            raise ValueError(f"Invalid option_type: {option_type}")
        
        logger.debug(
            f"Strike {strike} is {'ITM' if is_itm else 'OTM'} "
            f"for {option_type} at spot {spot_price}"
        )
        
        return is_itm
    
    except Exception as e:
        logger.error(f"Failed to check ITM status: {e}", exc_info=True)
        raise


def get_intrinsic_value(
    strike: int,
    spot_price: float,
    option_type: str
) -> float:
    """
    Calculate intrinsic value of an option.
    
    Args:
        strike: Strike price
        spot_price: Current spot price
        option_type: "call" or "put"
    
    Returns:
        Intrinsic value (0 if OTM)
    """
    try:
        if option_type.lower() == "call":
            # Call intrinsic value = max(spot - strike, 0)
            intrinsic = max(spot_price - strike, 0)
        elif option_type.lower() == "put":
            # Put intrinsic value = max(strike - spot, 0)
            intrinsic = max(strike - spot_price, 0)
        else:
            raise ValueError(f"Invalid option_type: {option_type}")
        
        logger.debug(
            f"Intrinsic value for {option_type} "
            f"(strike={strike}, spot={spot_price}): {intrinsic:.2f}"
        )
        
        return intrinsic
    
    except Exception as e:
        logger.error(f"Failed to calculate intrinsic value: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test ITM calculator
    print("ITM Calculator Tests\n")
    
    # Test BTC
    btc_spot = 65000
    print(f"BTC Spot: ${btc_spot}")
    print(f"ITM 5%: {calculate_itm_strikes(btc_spot, 'BTC', 5.0)}")
    print(f"ITM 10%: {calculate_itm_strikes(btc_spot, 'BTC', 10.0)}")
    
    print("\nDeep ITM Strikes:")
    deep_itm = calculate_deep_itm_strikes(btc_spot, 'BTC', 3)
    print(f"  Calls (below spot): {deep_itm['call_strikes']}")
    print(f"  Puts (above spot): {deep_itm['put_strikes']}")
    
    print("\n" + "="*50 + "\n")
    
    # Test ITM check
    print("ITM Status Tests:")
    print(f"64000 Call at spot 65000: {is_strike_itm(64000, 65000, 'call')}")
    print(f"66000 Call at spot 65000: {is_strike_itm(66000, 65000, 'call')}")
    print(f"64000 Put at spot 65000: {is_strike_itm(64000, 65000, 'put')}")
    print(f"66000 Put at spot 65000: {is_strike_itm(66000, 65000, 'put')}")
    
    print("\n" + "="*50 + "\n")
    
    # Test intrinsic value
    print("Intrinsic Value Tests:")
    print(f"64000 Call: ${get_intrinsic_value(64000, 65000, 'call')}")
    print(f"66000 Call: ${get_intrinsic_value(66000, 65000, 'call')}")
    print(f"64000 Put: ${get_intrinsic_value(64000, 65000, 'put')}")
    print(f"66000 Put: ${get_intrinsic_value(66000, 65000, 'put')}")
  
