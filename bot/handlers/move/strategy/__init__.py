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
        
        # Import all callbacks
        from .create import move_add_callback
        from .view import move_view_callback, move_view_strategy_callback
        from .edit import move_edit_callback, move_save_edit_callback
        from .delete import move_delete_callback, move_confirm_delete_callback
        
        # Register CREATE handler
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_menu$"
        ))
        
        # Register VIEW handlers
        application.add_handler(CallbackQueryHandler(
            move_view_callback,
            pattern="^move_view$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_view_strategy_callback,
            pattern="^move_view_strategy_"
        ))
        
        # Register EDIT handlers
        application.add_handler(CallbackQueryHandler(
            move_edit_callback,
            pattern="^move_edit_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_save_edit_callback,
            pattern="^move_save_edit_"
        ))
        
        # Register DELETE handlers
        application.add_handler(CallbackQueryHandler(
            move_delete_callback,
            pattern="^move_delete_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_confirm_delete_callback,
            pattern="^move_confirm_delete_"
        ))
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in MOVE strategy registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_strategy_handlers']
