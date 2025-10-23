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
        
        # Import callbacks
        from .create import (
            move_add_callback,
            move_add_new_callback,
            move_skip_description_callback,
            move_asset_callback,
            move_expiry_callback,
            move_direction_callback,
            move_confirm_save_callback,
            move_skip_target_callback,
            move_cancel_callback
        )
        from .view import move_view_callback, move_view_strategy_callback
        from .edit import move_edit_callback, move_save_edit_callback
        from .delete import move_delete_callback, move_confirm_delete_callback
        
        # Register MENU handler (shows options)
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_menu"
        ))
        
        # Register CREATE NEW handler (starts creation)
        application.add_handler(CallbackQueryHandler(
            move_add_new_callback,
            pattern="^move_add$"
        ))
        
        # Register other CREATE handlers
        application.add_handler(CallbackQueryHandler(
            move_skip_description_callback,
            pattern="^move_skip_description$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_asset_callback,
            pattern="^move_asset_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_expiry_callback,
            pattern="^move_expiry_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_direction_callback,
            pattern="^move_direction_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_confirm_save_callback,
            pattern="^move_confirm_save$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_skip_target_callback,
            pattern="^move_skip_target$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_cancel_callback,
            pattern="^move_cancel$"
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
