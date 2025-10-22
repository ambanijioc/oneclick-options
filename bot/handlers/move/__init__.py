"""
MOVE Strategy Handler Package

This package contains all MOVE strategy related handlers organized into:
- strategy/ : Strategy CRUD operations
- preset/ : Trade preset CRUD operations  
- trade/ : Manual and auto trade execution
"""

# Import all strategy handlers
from .strategy.create import *
from .strategy.edit import *
from .strategy.view import *
from .strategy.delete import *

# Import all preset handlers
from .preset.create import *
from .preset.edit import *
from .preset.view import *
from .preset.delete import *

# Import trade handlers
from .trade.manual import *
from .trade.auto import *

__all__ = [
    # Strategy operations
    'move_strategy_start',
    'move_create_start',
    'move_create_callback',
    'move_edit_strategy',
    'move_view_strategies',
    'move_delete_strategy',
    
    # Preset operations
    'move_preset_create',
    'move_preset_edit',
    'move_preset_view',
    'move_preset_delete',
    
    # Trade operations
    'move_manual_trade',
    'move_auto_trade',
]
