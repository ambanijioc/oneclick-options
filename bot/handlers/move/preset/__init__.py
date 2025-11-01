"""MOVE Preset Handler Submodule"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application):
    """Register MOVE preset handlers"""
    try:
        from bot.handlers.move.preset.create import register_move_preset_handlers as handler_func
        handler_func(application)
        logger.info("✓ MOVE preset handlers registered")
        return True
    except Exception as e:
        logger.error(f"❌ MOVE preset handler error: {e}", exc_info=True)
        return False


__all__ = ['register_move_preset_handlers']
