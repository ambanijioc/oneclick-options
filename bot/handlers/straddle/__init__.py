"""
STRADDLE Strategy Handler Package

Organized modular structure for STRADDLE strategy operations:
- strategy/: Strategy CRUD operations (create, edit, view, delete)
- preset/: Trade preset CRUD operations (create, edit, view, delete)
- trade/: Trade execution (manual, auto)

STRADDLE = Buy/Sell Call + Put at the SAME ATM strike
"""

from .strategy.create import *
from .strategy.edit import *
from .strategy.view import *
from .strategy.delete import *
from .preset.create import *
from .preset.edit import *
from .preset.view import *
from .preset.delete import *
from .trade.manual import *
from .trade.auto import *

__all__ = [
    'straddle_strategy_start',
    'straddle_create_strategy',
    'straddle_edit_strategy',
    'straddle_view_strategies',
    'straddle_delete_strategy',
    'straddle_preset_create',
    'straddle_preset_edit',
    'straddle_preset_view',
    'straddle_preset_delete',
    'straddle_manual_trade',
    'straddle_auto_trade',
]
