"""
MOVE Strategy handlers package.
Handles all MOVE strategy CRUD operations and callbacks.
"""

from telegram.ext import CallbackQueryHandler, MessageHandler, filters, Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# Import all callback handlers from create.py
from .create import (
    move_menu_callback,
    move_asset_input,
    move_description_input,
    move_target_input,
)

# Import from other modules if they exist
try:
    from .view import move_view_callback, move_detail_callback
except ImportError:
    logger.warning("⚠️ view.py not found")
    move_view_callback = None
    move_detail_callback = None

try:
    from .edit import move_edit_callback
except ImportError:
    logger.warning("⚠️ edit.py not found")
    move_edit_callback = None

try:
    from .delete import move_delete_callback
except ImportError:
    logger.warning("⚠️ delete.py not found")
    move_delete_callback = None


def register_move_strategy_handlers(application: Application):
    """
    Register all MOVE strategy callback and message handlers.
    
    Args:
        application: Telegram bot application instance
    """
    
    try:
        logger.info("🚀 Registering MOVE strategy handlers...")
        
        # ✅ MENU CALLBACK
        application.add_handler(CallbackQueryHandler(
            move_menu_callback, 
            pattern="^menu_move_strategy$"
        ))
        logger.info("  ✓ menu_move_strategy registered")
        
        # ✅ MESSAGE HANDLERS FOR INPUT STATES
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            move_asset_input
        ))
        
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            move_description_input
        ))
        
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            move_target_input
        ))
        
        # ✅ VIEW HANDLERS (if available)
        if move_view_callback:
            application.add_handler(CallbackQueryHandler(
                move_view_callback, 
                pattern="^move_view$"
            ))
        
        if move_detail_callback:
            application.add_handler(CallbackQueryHandler(
                move_detail_callback, 
                pattern="^move_detail_"
            ))
        
        # ✅ EDIT HANDLER (if available)
        if move_edit_callback:
            application.add_handler(CallbackQueryHandler(
                move_edit_callback, 
                pattern="^move_edit_"
            ))
        
        # ✅ DELETE HANDLER (if available)
        if move_delete_callback:
            application.add_handler(CallbackQueryHandler(
                move_delete_callback, 
                pattern="^move_delete_"
            ))
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE strategy handlers: {e}", exc_info=True)
        raise


__all__ = [
    'register_move_strategy_handlers',
    'move_menu_callback',
]
