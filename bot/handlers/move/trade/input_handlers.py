# ============ FILE 3: bot/handlers/move/trade/input_handlers.py ============

"""
MOVE Trade Input Validators

Comprehensive validation for trade execution parameters.
"""

def validate_price(price_str: str) -> tuple[bool, str, float]:
    """✅ FIX: Validate trade price"""
    try:
        price = float(price_str.strip())
        if price <= 0:
            return False, "Price must be greater than 0", 0
        if price > 1000000:
            return False, "Price seems unreasonably high", 0
        return True, "", price
    except (ValueError, TypeError):
        return False, "Price must be a valid number", 0

def validate_lot_size(size_str: str) -> tuple[bool, str, int]:
    """✅ FIX: Validate lot size for trades"""
    try:
        size = int(size_str.strip())
        if not (1 <= size <= 1000):
            return False, "Lot size must be between 1 and 1000", 0
        return True, "", size
    except (ValueError, TypeError):
        return False, "Lot size must be a whole number", 0

def validate_trade_quantity(qty_str: str) -> tuple[bool, str, int]:
    """✅ FIX: Validate trade quantity"""
    try:
        qty = int(qty_str.strip())
        if qty < 1:
            return False, "Quantity must be at least 1", 0
        if qty > 10000:
            return False, "Quantity exceeds maximum limit", 0
        return True, "", qty
    except (ValueError, TypeError):
        return False, "Quantity must be a whole number", 0

def validate_direction(direction_str: str) -> tuple[bool, str]:
    """✅ FIX: Validate trade direction"""
    direction = direction_str.strip().upper()
    if direction not in ['BUY', 'SELL', 'LONG', 'SHORT']:
        return False, "Direction must be BUY/SELL or LONG/SHORT"
    return True, ""

def validate_entry_exit_pair(entry: float, sl: float, target: float, direction: str) -> tuple[bool, str]:
    """✅ FIX: Validate entry/SL/target relationship"""
    if direction.upper() in ['BUY', 'LONG']:
        if sl >= entry:
            return False, "SL must be below entry price for BUY"
        if target and target <= entry:
            return False, "Target must be above entry price for BUY"
    else:  # SELL/SHORT
        if sl <= entry:
            return False, "SL must be above entry price for SELL"
        if target and target >= entry:
            return False, "Target must be below entry price for SELL"
    return True, ""

__all__ = [
    'validate_price',
    'validate_lot_size',
    'validate_trade_quantity',
    'validate_direction',
    'validate_entry_exit_pair',
]
