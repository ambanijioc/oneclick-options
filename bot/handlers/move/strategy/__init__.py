"""
MOVE Strategy handlers package.
Handles all MOVE strategy CRUD operations and callbacks.
"""

from telegram.ext import CallbackQueryHandler, Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# Import all callback handlers
from .create import (
    move_menu_callback,
    move_add_callback,
    move_asset_callback,
    move_direction_callback,
    move_skip_description_callback,
    move_skip_target_callback,
    move_cancel_callback,
    move_save_callback,
)

from .view import (
    move_view_callback,
    move_detail_callback,
)

from .edit import (
    move_edit_list_callback,
    move_edit_select_callback,
    move_edit_field_callback,
    move_edit_save_callback,
    move_edit_cancel_callback,
)

from .delete import (
    move_delete_list_callback,
    move_delete_confirm_callback,
    move_delete_cancel_callback,
)

def register_move_strategy_handlers(application: Application):
    """
    Register all MOVE strategy callback handlers.
    
    Args:
        application: Telegram bot application instance
    """
    
    try:
        logger.info("🚀 Registering MOVE strategy handlers...")
        
        # Menu
        application.add_handler(CallbackQueryHandler(
            move_menu_callback, 
            pattern="^menu_move_strategy$"
        ))
        
        # Create handlers
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_add$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_asset_callback, 
            pattern="^move_asset_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_direction_callback, 
            pattern="^move_direction_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_skip_description_callback, 
            pattern="^move_skip_description$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_skip_target_callback, 
            pattern="^move_skip_target$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_cancel_callback, 
            pattern="^move_cancel$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_save_callback, 
            pattern="^move_save$"
        ))
        
        # View handlers
        application.add_handler(CallbackQueryHandler(
            move_view_callback, 
            pattern="^move_view$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_detail_callback, 
            pattern="^move_detail_"
        ))
        
        # Edit handlers
        application.add_handler(CallbackQueryHandler(
            move_edit_list_callback, 
            pattern="^move_edit_list$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_edit_select_callback, 
            pattern="^move_edit_select_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_edit_field_callback, 
            pattern="^move_field_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_edit_save_callback, 
            pattern="^move_edit_save$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_edit_cancel_callback, 
            pattern="^move_edit_cancel$"
        ))
        
        # Delete handlers
        application.add_handler(CallbackQueryHandler(
            move_delete_list_callback, 
            pattern="^move_delete_list$"
        ))
        application.add_handler(CallbackQueryHandler(
            move_delete_confirm_callback, 
            pattern="^move_delete_confirm_"
        ))
        application.add_handler(CallbackQueryHandler(
            move_delete_cancel_callback, 
            pattern="^move_delete_cancel$"
        ))
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE strategy handlers: {e}")
        raise

__all__ = [
    'register_move_strategy_handlers',
    # Expose callbacks for testing
    'move_menu_callback',
    'move_add_callback',
    'move_view_callback',
    'move_edit_list_callback',
    'move_delete_list_callback',
]
