"""
MOVE Strategy Handler Module Initializer

Registers all MOVE strategy, preset, and trade handlers.
Includes routing setup for strategy operations.
"""

from .strategy.create import move_create_strategy_callback
from .strategy.delete import move_delete_strategy_callback
from .strategy.edit import move_edit_strategy_callback
from .strategy.view import move_view_callback

from .preset.create import move_create_preset_callback
from .preset.delete import move_delete_preset_callback
from .preset.edit import move_edit_preset_callback

from .trade.auto import move_auto_trade_callback
from .trade.manual import move_manual_trade_callback

__all__ = [
    # Strategy
    'move_create_strategy_callback',
    'move_delete_strategy_callback',
    'move_edit_strategy_callback',
    'move_view_callback',
    # Preset
    'move_create_preset_callback',
    'move_delete_preset_callback',
    'move_edit_preset_callback',
    # Trade
    'move_auto_trade_callback',
    'move_manual_trade_callback',
]
