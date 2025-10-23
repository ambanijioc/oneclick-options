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
        
        # Import CREATE callbacks (these exist)
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
        
        # Register MENU handler (shows options)
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_menu$"
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
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in MOVE strategy registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_strategy_handlers']
