"""
MOVE Strategy handlers.
"""

from telegram.ext import CallbackQueryHandler, Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy handlers."""
    
    try:
        logger.info("🚀 Registering MOVE strategy handlers...")
        
        # Import callback
        from .create import move_add_callback
        
        # Register handler
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^menu_move_strategy$"
        ))
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in MOVE strategy registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_strategy_handlers']
