# ============ FILE 4: bot/handlers/move/trade/__init__.py ============

"""
MOVE Trade Sub-module Initializer

Registers trade execution handlers for auto and manual trade modes.
"""

from .auto import move_auto_trade_callback
from .manual import move_manual_trade_callback
from .input_handlers import (
    validate_price,
    validate_lot_size,
    validate_trade_quantity,
    validate_direction,
    validate_entry_exit_pair,
)

__all__ = [
    # Auto Trade
    'move_auto_trade_callback',
    # Manual Trade
    'move_manual_trade_callback',
    # Input Validators
    'validate_price',
    'validate_lot_size',
    'validate_trade_quantity',
    'validate_direction',
    'validate_entry_exit_pair',
]
