"""
Input validation utilities.
Validates user inputs for trading parameters, time formats, and data integrity.
"""

import re
from typing import Optional, Tuple
from datetime import datetime
import pytz

from logger import logger, log_function_call


@log_function_call
def validate_percentage(value: float, min_val: float = -100, max_val: float = 100) -> Tuple[bool, Optional[str]]:
    """
    Validate percentage value is within acceptable range.
    
    Args:
        value: Percentage value to validate
        min_val: Minimum allowed value (default -100)
        max_val: Maximum allowed value (default 100)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not isinstance(value, (int, float)):
            return False, "Percentage must be a number"
        
        if value < min_val or value > max_val:
            return False, f"Percentage must be between {min_val} and {max_val}"
        
        logger.debug(f"[validators.validate_percentage] Valid: {value}%")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_percentage] Error: {e}")
        return False, str(e)


@log_function_call
def validate_time_format(time_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate time string format (HH:MM AM/PM).
    
    Args:
        time_str: Time string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Pattern: HH:MM AM/PM (12-hour format)
        pattern = r'^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM|am|pm)$'
        
        if not re.match(pattern, time_str):
            return False, "Time must be in format HH:MM AM/PM (e.g., 09:30 AM)"
        
        # Try parsing to ensure it's a valid time
        time_upper = time_str.upper()
        match = re.match(r'(\d{1,2}):(\d{2})\s?(AM|PM)', time_upper)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            if hour < 1 or hour > 12:
                return False, "Hour must be between 1 and 12"
            
            if minute < 0 or minute > 59:
                return False, "Minute must be between 0 and 59"
        
        logger.debug(f"[validators.validate_time_format] Valid time: {time_str}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_time_format] Error: {e}")
        return False, str(e)


@log_function_call
def validate_lot_size(size: int, min_size: int = 1, max_size: int = 1000) -> Tuple[bool, Optional[str]]:
    """
    Validate lot size is within acceptable range.
    
    Args:
        size: Lot size to validate
        min_size: Minimum allowed size (default 1)
        max_size: Maximum allowed size (default 1000)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not isinstance(size, int):
            return False, "Lot size must be an integer"
        
        if size < min_size:
            return False, f"Lot size must be at least {min_size}"
        
        if size > max_size:
            return False, f"Lot size cannot exceed {max_size}"
        
        logger.debug(f"[validators.validate_lot_size] Valid lot size: {size}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_lot_size] Error: {e}")
        return False, str(e)


@log_function_call
def validate_api_credentials(api_key: str, api_secret: str) -> Tuple[bool, Optional[str]]:
    """
    Validate API credentials format.
    
    Args:
        api_key: API key to validate
        api_secret: API secret to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not api_key or not api_key.strip():
            return False, "API key cannot be empty"
        
        if not api_secret or not api_secret.strip():
            return False, "API secret cannot be empty"
        
        if len(api_key) < 10:
            return False, "API key seems too short"
        
        if len(api_secret) < 10:
            return False, "API secret seems too short"
        
        logger.debug("[validators.validate_api_credentials] Credentials format valid")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_api_credentials] Error: {e}")
        return False, str(e)


@log_function_call
def validate_strategy_name(name: str, max_length: int = 50) -> Tuple[bool, Optional[str]]:
    """
    Validate strategy name format.
    
    Args:
        name: Strategy name to validate
        max_length: Maximum length allowed (default 50)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not name or not name.strip():
            return False, "Strategy name cannot be empty"
        
        if len(name) > max_length:
            return False, f"Strategy name cannot exceed {max_length} characters"
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            return False, "Strategy name can only contain letters, numbers, spaces, hyphens, and underscores"
        
        logger.debug(f"[validators.validate_strategy_name] Valid name: {name}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_strategy_name] Error: {e}")
        return False, str(e)


@log_function_call
def validate_asset(asset: str) -> Tuple[bool, Optional[str]]:
    """
    Validate asset symbol.
    
    Args:
        asset: Asset symbol to validate (BTC, ETH)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        valid_assets = ['BTC', 'ETH']
        
        if not asset:
            return False, "Asset cannot be empty"
        
        asset_upper = asset.upper().strip()
        
        if asset_upper not in valid_assets:
            return False, f"Asset must be one of: {', '.join(valid_assets)}"
        
        logger.debug(f"[validators.validate_asset] Valid asset: {asset_upper}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_asset] Error: {e}")
        return False, str(e)


@log_function_call
def validate_direction(direction: str) -> Tuple[bool, Optional[str]]:
    """
    Validate trade direction.
    
    Args:
        direction: Direction to validate (long, short)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        valid_directions = ['long', 'short']
        
        if not direction:
            return False, "Direction cannot be empty"
        
        direction_lower = direction.lower().strip()
        
        if direction_lower not in valid_directions:
            return False, f"Direction must be either 'long' or 'short'"
        
        logger.debug(f"[validators.validate_direction] Valid direction: {direction_lower}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_direction] Error: {e}")
        return False, str(e)


@log_function_call
def validate_expiry_notation(expiry: str) -> Tuple[bool, Optional[str]]:
    """
    Validate expiry notation format.
    
    Args:
        expiry: Expiry notation to validate (D, D+1, W, W+1, M, M+1, etc.)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not expiry:
            return False, "Expiry notation cannot be empty"
        
        expiry_upper = expiry.upper().strip()
        
        # Valid patterns: D, D+N, W, W+N, M, M+N
        pattern = r'^(D|W|M)(\+\d+)?$'
        
        if not re.match(pattern, expiry_upper):
            return False, "Expiry must be in format: D, D+1, W, W+1, M, M+1, etc."
        
        logger.debug(f"[validators.validate_expiry_notation] Valid expiry: {expiry_upper}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_expiry_notation] Error: {e}")
        return False, str(e)


@log_function_call
def validate_otm_input(
    otm_percentage: Optional[float] = None,
    otm_value: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate OTM input (either percentage or value, not both).
    
    Args:
        otm_percentage: OTM percentage value
        otm_value: OTM absolute value
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if otm_percentage is None and otm_value is None:
            return False, "Either OTM percentage or OTM value must be provided"
        
        if otm_percentage is not None and otm_value is not None:
            return False, "Provide either OTM percentage OR OTM value, not both"
        
        if otm_percentage is not None:
            if otm_percentage <= 0 or otm_percentage > 50:
                return False, "OTM percentage must be between 0 and 50"
        
        if otm_value is not None:
            if otm_value <= 0:
                return False, "OTM value must be positive"
        
        logger.debug(
            f"[validators.validate_otm_input] Valid OTM: "
            f"percentage={otm_percentage}, value={otm_value}"
        )
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_otm_input] Error: {e}")
        return False, str(e)


@log_function_call
def validate_price(price: float, min_price: float = 0.01) -> Tuple[bool, Optional[str]]:
    """
    Validate price value.
    
    Args:
        price: Price to validate
        min_price: Minimum allowed price (default 0.01)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not isinstance(price, (int, float)):
            return False, "Price must be a number"
        
        if price < min_price:
            return False, f"Price must be at least {min_price}"
        
        logger.debug(f"[validators.validate_price] Valid price: {price}")
        return True, None
        
    except Exception as e:
        logger.error(f"[validators.validate_price] Error: {e}")
        return False, str(e)


if __name__ == "__main__":
    # Test validators
    print("Testing validators...")
    
    # Test percentage
    is_valid, error = validate_percentage(5.5)
    print(f"✅ Percentage 5.5%: {is_valid}")
    
    is_valid, error = validate_percentage(150)
    print(f"❌ Percentage 150%: {is_valid} - {error}")
    
    # Test time format
    is_valid, error = validate_time_format("09:30 AM")
    print(f"✅ Time '09:30 AM': {is_valid}")
    
    is_valid, error = validate_time_format("25:00 PM")
    print(f"❌ Time '25:00 PM': {is_valid} - {error}")
    
    # Test lot size
    is_valid, error = validate_lot_size(5)
    print(f"✅ Lot size 5: {is_valid}")
    
    # Test asset
    is_valid, error = validate_asset("BTC")
    print(f"✅ Asset 'BTC': {is_valid}")
    
    is_valid, error = validate_asset("XRP")
    print(f"❌ Asset 'XRP': {is_valid} - {error}")
    
    # Test expiry notation
    is_valid, error = validate_expiry_notation("D+1")
    print(f"✅ Expiry 'D+1': {is_valid}")
    
    is_valid, error = validate_expiry_notation("X+5")
    print(f"❌ Expiry 'X+5': {is_valid} - {error}")
    
    print("\n✅ Validator tests completed!")
      
