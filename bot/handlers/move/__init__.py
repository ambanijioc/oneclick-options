"""MOVE Strategy Handlers Module"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy handlers"""
    try:
        from bot.handlers.move.strategy import register_move_strategy_handlers as reg
        reg(application)
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def register_move_preset_handlers(application: Application):
    """Register MOVE preset handlers"""
    try:
        from bot.handlers.move.preset import register_move_preset_handlers as reg
        reg(application)
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


__all__ = [
    'register_move_strategy_handlers',
    'register_move_preset_handlers',
]
