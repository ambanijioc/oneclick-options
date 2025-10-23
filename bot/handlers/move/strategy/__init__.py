"""
MOVE Strategy handlers package.
"""

from telegram.ext import CallbackQueryHandler, Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# ✅ Import ONLY the callback you have
from .create import move_add_callback


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy callback handlers."""
    
    try:
        logger.info("🚀 Registering MOVE strategy handlers...")
        
        # ✅ Register for BOTH patterns (main menu button + add button)
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^menu_move_strategy$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_add$"
        ))
        
        logger.info("✅ MOVE strategy handlers registered!")
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE handlers: {e}", exc_info=True)
        raise


__all__ = ['register_move_strategy_handlers']
