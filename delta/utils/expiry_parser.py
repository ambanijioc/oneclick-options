"""
Option expiry date parser and formatter.
"""

from datetime import datetime, timedelta
from typing import Optional
import pytz

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_next_friday(from_date: datetime) -> datetime:
    """
    Get next Friday from given date.
    
    Args:
        from_date: Starting date
    
    Returns:
        Next Friday datetime
    """
    # Friday is weekday 4 (Monday is 0)
    days_ahead = 4 - from_date.weekday()
    
    if days_ahead <= 0:  # Already past Friday this week
        days_ahead += 7
    
    return from_date + timedelta(days=days_ahead)


def get_last_friday_of_month(year: int, month: int) -> datetime:
    """
    Get last Friday of a given month.
    
    Args:
        year: Year
        month: Month
    
    Returns:
        Last Friday of the month
    """
    # Get first day of next month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    # Get last day of current month
    last_day = next_month - timedelta(days=1)
    
    # Find last Friday
    while last_day.weekday() != 4:  # 4 = Friday
        last_day -= timedelta(days=1)
    
    return last_day


def parse_expiry_code(expiry_code: str, reference_date: Optional[datetime] = None) -> datetime:
    """
    Parse expiry code to datetime.
    
    Args:
        expiry_code: Expiry code (D, D+1, D+2, W, W+1, W+2, M, M+1, M+2)
        reference_date: Reference date (defaults to now in IST)
    
    Returns:
        Expiry datetime
    
    Raises:
        ValueError: If expiry code is invalid
    
    Examples:
        D    = Today's daily expiry (usually 15:30 IST)
        D+1  = Tomorrow's daily expiry
        W    = This week's Friday
        W+1  = Next week's Friday
        M    = This month's last Friday
        M+1  = Next month's last Friday
    """
    try:
        # Get reference date in IST
        if reference_date is None:
            ist = pytz.timezone('Asia/Kolkata')
            reference_date = datetime.now(ist)
        
        expiry_code = expiry_code.upper().strip()
        
        # Daily expiry
        if expiry_code == "D":
            expiry = reference_date.replace(hour=15, minute=30, second=0, microsecond=0)
        
        elif expiry_code.startswith("D+"):
            try:
                days = int(expiry_code[2:])
                expiry = reference_date + timedelta(days=days)
                expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
            except ValueError:
                raise ValueError(f"Invalid daily expiry code: {expiry_code}")
        
        # Weekly expiry (Friday)
        elif expiry_code == "W":
            expiry = get_next_friday(reference_date)
            expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
        
        elif expiry_code.startswith("W+"):
            try:
                weeks = int(expiry_code[2:])
                base_friday = get_next_friday(reference_date)
                expiry = base_friday + timedelta(weeks=weeks)
                expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
            except ValueError:
                raise ValueError(f"Invalid weekly expiry code: {expiry_code}")
        
        # Monthly expiry (last Friday of month)
        elif expiry_code == "M":
            last_friday = get_last_friday_of_month(
                reference_date.year,
                reference_date.month
            )
            
            # If we're past last Friday this month, get next month
            if reference_date > last_friday:
                next_month = reference_date.month + 1
                next_year = reference_date.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                last_friday = get_last_friday_of_month(next_year, next_month)
            
            expiry = last_friday.replace(hour=15, minute=30, second=0, microsecond=0)
        
        elif expiry_code.startswith("M+"):
            try:
                months = int(expiry_code[2:])
                
                # Calculate target month
                target_month = reference_date.month + months
                target_year = reference_date.year
                
                while target_month > 12:
                    target_month -= 12
                    target_year += 1
                
                expiry = get_last_friday_of_month(target_year, target_month)
                expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
            
            except ValueError:
                raise ValueError(f"Invalid monthly expiry code: {expiry_code}")
        
        else:
            raise ValueError(f"Invalid expiry code: {expiry_code}")
        
        logger.debug(f"Parsed expiry code '{expiry_code}': {expiry.strftime('%Y-%m-%d %H:%M')}")
        
        return expiry
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse expiry code: {e}", exc_info=True)
        raise ValueError(f"Error parsing expiry code: {str(e)}")


def get_expiry_date(expiry_code: str) -> str:
    """
    Get expiry date string from code.
    
    Args:
        expiry_code: Expiry code
    
    Returns:
        Expiry date in YYYY-MM-DD format
    """
    try:
        expiry_dt = parse_expiry_code(expiry_code)
        return expiry_dt.strftime('%Y-%m-%d')
    
    except Exception as e:
        logger.error(f"Failed to get expiry date: {e}", exc_info=True)
        raise


def format_expiry_date(expiry_dt: datetime, format: str = '%d %b %Y') -> str:
    """
    Format expiry datetime for display.
    
    Args:
        expiry_dt: Expiry datetime
        format: Date format string
    
    Returns:
        Formatted date string
    """
    try:
        return expiry_dt.strftime(format)
    
    except Exception as e:
        logger.error(f"Failed to format expiry date: {e}", exc_info=True)
        return str(expiry_dt)


def get_days_to_expiry(expiry_code: str) -> int:
    """
    Get number of days until expiry.
    
    Args:
        expiry_code: Expiry code
    
    Returns:
        Number of days to expiry
    """
    try:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        expiry = parse_expiry_code(expiry_code, now)
        
        delta = expiry - now
        days = delta.days
        
        # If expiry is later today, count as 1 day
        if days == 0 and delta.seconds > 0:
            days = 1
        
        logger.debug(f"Days to expiry for '{expiry_code}': {days}")
        
        return days
    
    except Exception as e:
        logger.error(f"Failed to calculate days to expiry: {e}", exc_info=True)
        raise


def get_all_expiry_dates(num_weeks: int = 4, num_months: int = 3) -> dict:
    """
    Get all available expiry dates.
    
    Args:
        num_weeks: Number of weekly expiries to include
        num_months: Number of monthly expiries to include
    
    Returns:
        Dictionary with expiry codes and dates
    """
    try:
        expiries = {}
        
        # Daily expiries
        expiries['D'] = get_expiry_date('D')
        expiries['D+1'] = get_expiry_date('D+1')
        
        # Weekly expiries
        expiries['W'] = get_expiry_date('W')
        for i in range(1, num_weeks):
            expiries[f'W+{i}'] = get_expiry_date(f'W+{i}')
        
        # Monthly expiries
        expiries['M'] = get_expiry_date('M')
        for i in range(1, num_months):
            expiries[f'M+{i}'] = get_expiry_date(f'M+{i}')
        
        logger.debug(f"Generated {len(expiries)} expiry dates")
        
        return expiries
    
    except Exception as e:
        logger.error(f"Failed to get all expiry dates: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test expiry parser
    print("Expiry Parser Tests\n")
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    print(f"Reference Date: {now.strftime('%Y-%m-%d %H:%M IST')}\n")
    
    # Test various codes
    codes = ['D', 'D+1', 'W', 'W+1', 'W+2', 'M', 'M+1', 'M+2']
    
    for code in codes:
        try:
            expiry = parse_expiry_code(code, now)
            formatted = format_expiry_date(expiry)
            days = get_days_to_expiry(code)
            print(f"{code:6} = {formatted} ({days} days)")
        except Exception as e:
            print(f"{code:6} = ERROR: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test all expiries
    print("All Available Expiries:")
    all_expiries = get_all_expiry_dates(3, 2)
    for code, date in all_expiries.items():
        print(f"  {code:6} = {date}")
      
