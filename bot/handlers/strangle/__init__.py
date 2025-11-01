"""
STRANGLE Strategy Handler Package

Organized modular structure for STRANGLE strategy operations:
- strategy/: Strategy CRUD operations (create, edit, view, delete)
- preset/: Trade preset CRUD operations (create, edit, view, delete)
- trade/: Trade execution (manual, auto)

STRANGLE = Selling Call + Put at different OTM strikes
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
    'strangle_strategy_start',
    'strangle_create_strategy',
    'strangle_edit_strategy',
    'strangle_view_strategies',
    'strangle_delete_strategy',
    'strangle_preset_create',
    'strangle_preset_edit',
    'strangle_preset_view',
    'strangle_preset_delete',
    'strangle_manual_trade',
    'strangle_auto_trade',
]
