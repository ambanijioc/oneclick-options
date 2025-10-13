"""
Database package for MongoDB operations.
"""

from .connection import connect_db, close_db, get_database
from .models.api_credentials import APICredential
from .models.strategy_preset import StrategyPreset
from .models.auto_execution import AutoExecution
from .models.trade_history import TradeHistory
from .models.user_settings import UserSettings

__all__ = [
    'connect_db',
    'close_db',
    'get_database',
    'APICredential',
    'StrategyPreset',
    'AutoExecution',
    'TradeHistory',
    'UserSettings'
]
