"""
Helper utility functions.
Common operations like date parsing, formatting, and calculations.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pytz

from logger import logger, log_function_call


@log_function_call
def parse_expiry_notation(
    notation: str,
    base_date: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Parse expiry notation to actual datetime.
    
    Notation examples:
    - D: Daily (current day)
    - D+1: Daily + 1 day
    - W: Weekly (next Friday)
    - W+1: Weekly + 1 week
    - M: Monthly (last Friday of current month)
    - M+1: Monthly + 1 month
    
    Args:
        notation: Expiry notation string
        base_date: Base date for calculation (default: current date in IST)
    
    Returns:
        Expiry datetime in IST or None if invalid
    """
    try:
        ist = pytz.timezone('Asia/Kolkata')
        
        if base_date is None:
            base_date = datetime.now(ist)
        elif base_date.tzinfo is None:
            base_date = ist.localize(base_date)
        
        notation_upper = notation.upper().strip()
        
        # Parse notation
        match = re.match(r'^(D|W|M)(\+(\d+))?$', notation_upper)
        if not match:
            logger.warning(f"[helpers.parse_expiry_notation] Invalid notation: {notation}")
            return None
        
        expiry_type = match.group(1)
        offset = int(match.group(3)) if match.group(3) else 0
        
        # Calculate expiry date
        if expiry_type == 'D':
            # Daily expiry
            expiry_date = base_date + timedelta(days=offset)
        
        elif expiry_type == 'W':
            # Weekly expiry (next Friday)
            days_until_friday = (4 - base_date.weekday()) % 7
            if days_until_friday == 0 and base_date.hour >= 15:  # After 3 PM on Friday
                days_until_friday = 7
            
            expiry_date = base_date + timedelta(days=days_until_friday + (offset * 7))
        
        elif expiry_type == 'M':
            # Monthly expiry (last Friday of month)
            # Add offset months
            target_month = base_date.month + offset
            target_year = base_date.year
            
            while target_month > 12:
                target_month -= 12
                target_year += 1
            
            # Find last Friday of target month
            # Start with last day of month
            if target_month == 12:
                last_day = datetime(target_year, 12, 31, tzinfo=ist)
            else:
                last_day = datetime(target_year, target_month + 1, 1, tzinfo=ist) - timedelta(days=1)
            
            # Find last Friday
            days_back = (last_day.weekday() - 4) % 7
            expiry_date = last_day - timedelta(days=days_back)
        
        else:
            return None
        
        # Set to 3:30 PM IST (typical expiry time)
        expiry_date = expiry_date.replace(hour=15, minute=30, second=0, microsecond=0)
        
        logger.info(
            f"[helpers.parse_expiry_notation] Parsed '{notation}' to {expiry_date}"
        )
        
        return expiry_date
        
    except Exception as e:
        logger.error(f"[helpers.parse_expiry_notation] Error parsing notation: {e}")
        return None


@log_function_call
def format_currency(amount: float, currency: str = "USD", decimals: int = 2) -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency symbol (default "USD")
        decimals: Number of decimal places (default 2)
    
    Returns:
        Formatted currency string
    """
    try:
        if currency == "USD" or currency == "$":
            symbol = "$"
        elif currency == "USDT":
            symbol = "₮"
        elif currency == "INR" or currency == "₹":
            symbol = "₹"
        else:
            symbol = currency + " "
        
        # Format with commas
        formatted = f"{symbol}{amount:,.{decimals}f}"
        
        return formatted
        
    except Exception as e:
        logger.error(f"[helpers.format_currency] Error formatting: {e}")
        return str(amount)


@log_function_call
def calculate_percentage(value: float, total: float) -> float:
    """
    Calculate percentage of value relative to total.
    
    Args:
        value: Value to calculate percentage for
        total: Total amount
    
    Returns:
        Percentage as float
    """
    try:
        if total == 0:
            return 0.0
        
        percentage = (value / total) * 100
        return round(percentage, 2)
        
    except Exception as e:
        logger.error(f"[helpers.calculate_percentage] Error: {e}")
        return 0.0


@log_function_call
def get_ist_time() -> datetime:
    """
    Get current time in IST timezone.
    
    Returns:
        Current datetime in IST
    """
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)


@log_function_call
def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_str: Format string (default: "%Y-%m-%d %H:%M:%S %Z")
    
    Returns:
        Formatted datetime string
    """
    try:
        # Ensure timezone aware
        if dt.tzinfo is None:
            ist = pytz.timezone('Asia/Kolkata')
            dt = ist.localize(dt)
        
        return dt.strftime(format_str)
        
    except Exception as e:
        logger.error(f"[helpers.format_datetime] Error formatting: {e}")
        return str(dt)


@log_function_call
def parse_time_to_datetime(time_str: str, base_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse time string (HH:MM AM/PM) to datetime for today.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
        base_date: Base date to use (default: today)
    
    Returns:
        Datetime object or None
    """
    try:
        ist = pytz.timezone('Asia/Kolkata')
        
        if base_date is None:
            base_date = datetime.now(ist)
        
        # Parse time
        match = re.match(r'(\d{1,2}):(\d{2})\s?(AM|PM)', time_str.upper())
        if not match:
            return None
        
        hour = int(match.group(1))
        minute = int(match.group(2))
        meridiem = match.group(3)
        
        # Convert to 24-hour format
        if meridiem == 'PM' and hour != 12:
            hour += 12
        elif meridiem == 'AM' and hour == 12:
            hour = 0
        
        # Create datetime
        result = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        logger.debug(f"[helpers.parse_time_to_datetime] Parsed '{time_str}' to {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"[helpers.parse_time_to_datetime] Error: {e}")
        return None


@log_function_call
def round_to_increment(value: float, increment: float) -> float:
    """
    Round value to nearest increment.
    
    Args:
        value: Value to round
        increment: Increment to round to
    
    Returns:
        Rounded value
    """
    try:
        rounded = round(value / increment) * increment
        return rounded
        
    except Exception as e:
        logger.error(f"[helpers.round_to_increment] Error: {e}")
        return value


@log_function_call
def calculate_pnl(
    entry_price: float,
    exit_price: float,
    size: float,
    is_long: bool
) -> float:
    """
    Calculate PnL for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        size: Position size
        is_long: True if long position
    
    Returns:
        PnL value
    """
    try:
        if is_long:
            pnl = (exit_price - entry_price) * size
        else:
            pnl = (entry_price - exit_price) * abs(size)
        
        return round(pnl, 2)
        
    except Exception as e:
        logger.error(f"[helpers.calculate_pnl] Error: {e}")
        return 0.0


@log_function_call
def format_position_size(size: float) -> str:
    """
    Format position size with direction indicator.
    
    Args:
        size: Position size (negative for short)
    
    Returns:
        Formatted string with direction
    """
    try:
        if size > 0:
            return f"+{size} (Long)"
        elif size < 0:
            return f"{size} (Short)"
        else:
            return "0 (No Position)"
        
    except Exception as e:
        logger.error(f"[helpers.format_position_size] Error: {e}")
        return str(size)


@log_function_call
def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated (default "...")
    
    Returns:
        Truncated string
    """
    try:
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
        
    except Exception as e:
        logger.error(f"[helpers.truncate_string] Error: {e}")
        return text


@log_function_call
def get_expiry_display_name(notation: str) -> str:
    """
    Get user-friendly display name for expiry notation.
    
    Args:
        notation: Expiry notation (D, D+1, W, etc.)
    
    Returns:
        Display name
    """
    try:
        notation_upper = notation.upper()
        
        display_map = {
            'D': 'Daily',
            'D+1': 'Daily +1',
            'D+2': 'Daily +2',
            'W': 'Weekly',
            'W+1': 'Weekly +1',
            'W+2': 'Weekly +2',
            'M': 'Monthly',
            'M+1': 'Monthly +1',
            'M+2': 'Monthly +2'
        }
        
        return display_map.get(notation_upper, notation_upper)
        
    except Exception as e:
        logger.error(f"[helpers.get_expiry_display_name] Error: {e}")
        return notation


if __name__ == "__main__":
    # Test helpers
    print("Testing helpers...")
    
    # Test expiry parsing
    expiry = parse_expiry_notation("D+1")
    print(f"✅ Parsed D+1: {expiry}")
    
    expiry = parse_expiry_notation("W")
    print(f"✅ Parsed W: {expiry}")
    
    # Test currency formatting
    formatted = format_currency(1234.56, "USD")
    print(f"✅ Formatted currency: {formatted}")
    
    # Test percentage calculation
    pct = calculate_percentage(250, 1000)
    print(f"✅ Percentage: {pct}%")
    
    # Test IST time
    ist_time = get_ist_time()
    print(f"✅ IST time: {ist_time}")
    
    # Test time parsing
    dt = parse_time_to_datetime("09:30 AM")
    print(f"✅ Parsed time: {dt}")
    
    # Test rounding
    rounded = round_to_increment(95234.5, 200)
    print(f"✅ Rounded to 200: {rounded}")
    
    # Test PnL calculation
    pnl = calculate_pnl(95000, 96000, 1, True)
    print(f"✅ PnL: ${pnl}")
    
    print("\n✅ Helper tests completed!")
  
