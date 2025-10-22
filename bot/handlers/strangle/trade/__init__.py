"""STRANGLE Trade Execution Handlers"""

from .manual import *
from .auto import *

__all__ = [
    'strangle_manual_trade',
    'strangle_auto_trade',
]
