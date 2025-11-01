"""
MOVE Trade Handlers Module  
Registers manual and auto trade handlers
"""

from telegram.ext import Application


def register_move_manual_trade_handlers(application: Application) -> None:
    """Register MOVE manual trade handlers."""
    from bot.handlers.move.trade.manual import register_manual_trade_handlers
    register_manual_trade_handlers(application)


def register_move_auto_trade_handlers(application: Application) -> None:
    """Register MOVE auto trade handlers."""
    from bot.handlers.move.trade.auto import register_auto_trade_handlers
    register_auto_trade_handlers(application)


__all__ = [
    'register_move_manual_trade_handlers',
    'register_move_auto_trade_handlers'
]
