"""
MOVE Strategy Handlers Module
Nested structure for MOVE strategy, preset, and trade handlers.
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy handlers from bot/handlers/move/strategy/"""
    try:
        from bot.handlers.move.strategy import register_handlers
        register_handlers(application)
        logger.info("✓ MOVE strategy handlers loaded")
        return True
    except Exception as e:
        logger.error(f"Error in MOVE strategy handlers: {e}")
        return False


def register_move_preset_handlers(application: Application):
    """Register MOVE preset handlers from bot/handlers/move/preset/"""
    try:
        from bot.handlers.move.preset import register_handlers
        register_handlers(application)
        logger.info("✓ MOVE preset handlers loaded")
        return True
    except Exception as e:
        logger.error(f"Error in MOVE preset handlers: {e}")
        return False


def register_move_manual_trade_handlers(application: Application):
    """Register MOVE manual trade handlers from bot/handlers/move/trade/"""
    try:
        from bot.handlers.move.trade import register_handlers
        register_handlers(application)
        logger.info("✓ MOVE manual trade handlers loaded")
        return True
    except Exception as e:
        logger.error(f"Error in MOVE trade handlers: {e}")
        return False


__all__ = [
    'register_move_strategy_handlers',
    'register_move_preset_handlers',
    'register_move_manual_trade_handlers',
]
