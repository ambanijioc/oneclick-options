"""MOVE Strategy Handler Submodule"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy handlers"""
    try:
        from bot.handlers.move.strategy.move_strategy_handler import register_move_strategy_handlers as handler_func
        handler_func(application)
        logger.info("✓ MOVE strategy handlers registered")
        return True
    except Exception as e:
        logger.error(f"❌ MOVE strategy handler error: {e}", exc_info=True)
        return False


__all__ = ['register_move_strategy_handlers']
