# ============ FILE 1: bot/handlers/move/__init__.py ============

"""
MOVE Strategy Handler Module Initializer

Registers all MOVE strategy, preset, and trade handlers.
Includes routing setup for strategy operations.
"""

from .strategy.create import (
    move_create_strategy_callback,
    handle_move_strategy_name,
    handle_move_strategy_asset,
    handle_move_strategy_direction,
    handle_move_strategy_expiry,
)
from .strategy.delete import (
    move_delete_strategy_callback,
    move_delete_strategy_select_callback,
    move_confirm_delete_strategy_callback,
)
from .strategy.edit import (
    move_edit_strategy_callback,
    move_edit_strategy_select_callback,
    move_edit_strategy_field_callback,
    handle_move_edit_strategy_field,
)
from .strategy.view import (
    move_view_callback,
    move_view_detail_callback,
    move_list_all_callback,
    move_strategy_status,
)
from .preset.create import (
    move_create_preset_callback,
    handle_move_preset_name,
    handle_move_preset_sl_trigger,
    handle_move_preset_sl_limit,
    handle_move_preset_target,
)
from .preset.delete import (
    move_delete_preset_callback,
    move_delete_preset_select_callback,
    move_confirm_delete_preset_callback,
)
from .preset.edit import (
    move_edit_preset_callback,
    move_edit_preset_select_callback,
    move_edit_preset_field_callback,
    handle_move_edit_preset_field,
)
from .trade.auto import (
    move_auto_trade_callback,
    move_auto_execute_trade_callback,
)
from .trade.manual import (
    move_manual_trade_callback,
    handle_move_manual_entry_price,
    handle_move_manual_lot_size,
    handle_move_manual_sl_price,
    handle_move_manual_target_price,
    handle_move_manual_direction,
    handle_move_manual_strategy_select,
)

# ✅ FIX: Consolidated handler list
__all__ = [
    # Strategy Create
    'move_create_strategy_callback',
    'handle_move_strategy_name',
    'handle_move_strategy_asset',
    'handle_move_strategy_direction',
    'handle_move_strategy_expiry',
    # Strategy Delete
    'move_delete_strategy_callback',
    'move_delete_strategy_select_callback',
    'move_confirm_delete_strategy_callback',
    # Strategy Edit
    'move_edit_strategy_callback',
    'move_edit_strategy_select_callback',
    'move_edit_strategy_field_callback',
    'handle_move_edit_strategy_field',
    # Strategy View
    'move_view_callback',
    'move_view_detail_callback',
    'move_list_all_callback',
    'move_strategy_status',
    # Preset Create
    'move_create_preset_callback',
    'handle_move_preset_name',
    'handle_move_preset_sl_trigger',
    'handle_move_preset_sl_limit',
    'handle_move_preset_target',
    # Preset Delete
    'move_delete_preset_callback',
    'move_delete_preset_select_callback',
    'move_confirm_delete_preset_callback',
    # Preset Edit
    'move_edit_preset_callback',
    'move_edit_preset_select_callback',
    'move_edit_preset_field_callback',
    'handle_move_edit_preset_field',
    # Trade Auto
    'move_auto_trade_callback',
    'move_auto_execute_trade_callback',
    # Trade Manual
    'move_manual_trade_callback',
    'handle_move_manual_entry_price',
    'handle_move_manual_lot_size',
    'handle_move_manual_sl_price',
    'handle_move_manual_target_price',
    'handle_move_manual_direction',
    'handle_move_manual_strategy_select',
]
