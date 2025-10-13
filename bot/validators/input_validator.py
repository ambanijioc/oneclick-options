"""
Input validation for user inputs.
"""

from typing import Union, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    
    is_valid: bool
    value: Optional[Union[int, float, str]] = None
    error_message: Optional[str] = None


def validate_percentage(
    value: str,
    min_val: float = 0,
    max_val: float = 100,
    allow_zero: bool = True
) -> ValidationResult:
    """
    Validate percentage input.
    
    Args:
        value: Input value as string
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_zero: Whether zero is allowed
    
    Returns:
        ValidationResult with parsed value or error
    """
    try:
        # Remove % symbol if present
        clean_value = value.strip().replace('%', '').strip()
        
        # Parse as float
        percentage = float(clean_value)
        
        # Check range
        if not allow_zero and percentage == 0:
            return ValidationResult(
                is_valid=False,
                error_message="Percentage cannot be zero"
            )
        
        if percentage < min_val or percentage > max_val:
            return ValidationResult(
                is_valid=False,
                error_message=f"Percentage must be between {min_val}% and {max_val}%"
            )
        
        return ValidationResult(is_valid=True, value=percentage)
    
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="Invalid percentage format. Please enter a number (e.g., 50 or 50%)"
        )


def validate_price(value: str, min_val: float = 0) -> ValidationResult:
    """
    Validate price input.
    
    Args:
        value: Input value as string
        min_val: Minimum allowed value
    
    Returns:
        ValidationResult with parsed value or error
    """
    try:
        # Remove currency symbols if present
        clean_value = value.strip().replace('$', '').replace('₹', '').strip()
        
        # Parse as float
        price = float(clean_value)
        
        # Check minimum
        if price < min_val:
            return ValidationResult(
                is_valid=False,
                error_message=f"Price must be at least {min_val}"
            )
        
        return ValidationResult(is_valid=True, value=price)
    
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="Invalid price format. Please enter a number (e.g., 1000 or 1000.50)"
        )


def validate_lot_size(value: str, min_val: int = 1, max_val: int = 10000) -> ValidationResult:
    """
    Validate lot size input.
    
    Args:
        value: Input value as string
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        ValidationResult with parsed value or error
    """
    try:
        # Parse as integer
        lot_size = int(value.strip())
        
        # Check range
        if lot_size < min_val or lot_size > max_val:
            return ValidationResult(
                is_valid=False,
                error_message=f"Lot size must be between {min_val} and {max_val}"
            )
        
        return ValidationResult(is_valid=True, value=lot_size)
    
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="Invalid lot size. Please enter a whole number (e.g., 10)"
        )


def validate_time_format(value: str) -> ValidationResult:
    """
    Validate time input in HH:MM format (IST).
    
    Args:
        value: Time string in HH:MM format
    
    Returns:
        ValidationResult with parsed time or error
    """
    try:
        # Clean input
        clean_value = value.strip()
        
        # Parse time
        time_obj = datetime.strptime(clean_value, "%H:%M")
        
        # Format as HH:MM
        formatted_time = time_obj.strftime("%H:%M")
        
        return ValidationResult(is_valid=True, value=formatted_time)
    
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="Invalid time format. Please use HH:MM (24-hour format), e.g., 09:15 or 15:30"
        )


def validate_expiry_code(value: str) -> ValidationResult:
    """
    Validate expiry code input.
    
    Args:
        value: Expiry code (D, D+1, W, M, etc.)
    
    Returns:
        ValidationResult with validated code or error
    """
    # Valid expiry codes
    valid_codes = ['D', 'D+1', 'D+2', 'W', 'W+1', 'W+2', 'M', 'M+1', 'M+2']
    
    # Clean and uppercase
    clean_value = value.strip().upper()
    
    if clean_value not in valid_codes:
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid expiry code. Valid options: {', '.join(valid_codes)}"
        )
    
    return ValidationResult(is_valid=True, value=clean_value)


def validate_atm_offset(value: str) -> ValidationResult:
    """
    Validate ATM offset input.
    
    Args:
        value: ATM offset value
    
    Returns:
        ValidationResult with parsed value or error
    """
    try:
        # Parse as integer
        offset = int(value.strip())
        
        # Check range (-10 to +10)
        if abs(offset) > 10:
            return ValidationResult(
                is_valid=False,
                error_message="ATM offset must be between -10 and +10"
            )
        
        return ValidationResult(is_valid=True, value=offset)
    
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="Invalid ATM offset. Please enter a whole number (e.g., 0, -2, +3)"
        )


def validate_otm_value(
    value: str,
    otm_type: str,
    asset: str
) -> ValidationResult:
    """
    Validate OTM selection value.
    
    Args:
        value: OTM value
        otm_type: Type of selection (percentage or numeral)
        asset: Asset (BTC or ETH)
    
    Returns:
        ValidationResult with parsed value or error
    """
    try:
        # Parse as float
        otm_value = float(value.strip())
        
        if otm_value <= 0:
            return ValidationResult(
                is_valid=False,
                error_message="OTM value must be positive"
            )
        
        # Validate based on type
        if otm_type == "percentage":
            if otm_value > 50:
                return ValidationResult(
                    is_valid=False,
                    error_message="OTM percentage should not exceed 50%"
                )
        else:  # numeral
            # Check reasonable strike distance
            max_distance = 10000 if asset == "BTC" else 1000
            if otm_value > max_distance:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"OTM distance too large. Maximum: {max_distance}"
                )
        
        return ValidationResult(is_valid=True, value=otm_value)
    
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="Invalid OTM value. Please enter a number"
        )


def validate_api_name(value: str) -> ValidationResult:
    """
    Validate API name input.
    
    Args:
        value: API name
    
    Returns:
        ValidationResult with validated name or error
    """
    # Clean input
    clean_value = value.strip()
    
    # Check length
    if len(clean_value) < 1:
        return ValidationResult(
            is_valid=False,
            error_message="API name cannot be empty"
        )
    
    if len(clean_value) > 100:
        return ValidationResult(
            is_valid=False,
            error_message="API name too long (maximum 100 characters)"
        )
    
    # Check for invalid characters
    invalid_chars = ['<', '>', '"', "'", '\\', '/', '&']
    if any(char in clean_value for char in invalid_chars):
        return ValidationResult(
            is_valid=False,
            error_message="API name contains invalid characters"
        )
    
    return ValidationResult(is_valid=True, value=clean_value)


def validate_api_key(value: str) -> ValidationResult:
    """
    Validate API key format.
    
    Args:
        value: API key
    
    Returns:
        ValidationResult with validated key or error
    """
    # Clean input
    clean_value = value.strip()
    
    # Check length
    if len(clean_value) < 10:
        return ValidationResult(
            is_valid=False,
            error_message="API key too short (minimum 10 characters)"
        )
    
    if len(clean_value) > 200:
        return ValidationResult(
            is_valid=False,
            error_message="API key too long (maximum 200 characters)"
        )
    
    return ValidationResult(is_valid=True, value=clean_value)


if __name__ == "__main__":
    # Test validators
    print("Testing validators...\n")
    
    # Test percentage
    result = validate_percentage("50")
    print(f"Percentage '50': Valid={result.is_valid}, Value={result.value}")
    
    result = validate_percentage("150")
    print(f"Percentage '150': Valid={result.is_valid}, Error={result.error_message}")
    
    # Test price
    result = validate_price("1000.50")
    print(f"\nPrice '1000.50': Valid={result.is_valid}, Value={result.value}")
    
    # Test lot size
    result = validate_lot_size("10")
    print(f"\nLot size '10': Valid={result.is_valid}, Value={result.value}")
    
    # Test time
    result = validate_time_format("09:15")
    print(f"\nTime '09:15': Valid={result.is_valid}, Value={result.value}")
    
    result = validate_time_format("25:99")
    print(f"Time '25:99': Valid={result.is_valid}, Error={result.error_message}")
    
    # Test expiry
    result = validate_expiry_code("W")
    print(f"\nExpiry 'W': Valid={result.is_valid}, Value={result.value}")
    
    # Test ATM offset
    result = validate_atm_offset("-2")
    print(f"\nATM offset '-2': Valid={result.is_valid}, Value={result.value}")
    
    # Test OTM value
    result = validate_otm_value("5", "percentage", "BTC")
    print(f"\nOTM '5%': Valid={result.is_valid}, Value={result.value}")
