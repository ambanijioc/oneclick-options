"""MOVE Strategy Handler Submodule"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_handlers(application: Application):
    """Register all MOVE strategy handlers"""
    try:
        from bot.handlers.move.strategy.move_strategy_handler import register_move_strategy_handlers
        register_move_strategy_handlers(application)
        return True
    except Exception as e:
        logger.error(f"Error registering MOVE strategy handlers: {e}")
        return False


__all__ = ['register_handlers']
