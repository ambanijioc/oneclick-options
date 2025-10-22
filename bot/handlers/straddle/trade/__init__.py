"""STRADDLE Trade Execution Handlers"""

from .manual import *
from .auto import *

__all__ = [
    'straddle_manual_trade',
    'straddle_auto_trade',
]
