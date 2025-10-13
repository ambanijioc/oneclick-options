"""
Database package initialization.
Exports all database operations for easy imports.
"""

from database.connection import DatabaseManager, get_database
from database.models import (
    APICredentials,
    StraddleStrategy,
    StrangleStrategy,
    TradeHistory,
    AutoExecutionSchedule,
    Position,
    Order
)
from database.api_operations import APIOperations
from database.strategy_operations import StrategyOperations
from database.trade_operations import TradeOperations
from database.schedule_operations import ScheduleOperations

__all__ = [
    'DatabaseManager',
    'get_database',
    'APICredentials',
    'StraddleStrategy',
    'StrangleStrategy',
    'TradeHistory',
    'AutoExecutionSchedule',
    'Position',
    'Order',
    'APIOperations',
    'StrategyOperations',
    'TradeOperations',
    'ScheduleOperations'
]
