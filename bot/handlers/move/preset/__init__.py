"""MOVE Preset Handler Submodule"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_handlers(application: Application):
    """Register all MOVE preset handlers"""
    try:
        from bot.handlers.move.preset.create import register_move_preset_handlers
        register_move_preset_handlers(application)
        return True
    except Exception as e:
        logger.error(f"Error registering MOVE preset handlers: {e}")
        return False


__all__ = ['register_handlers']
