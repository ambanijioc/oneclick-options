"""
MOVE Strategy handlers package.
Handles all MOVE strategy CRUD operations and callbacks.
"""

from telegram.ext import CallbackQueryHandler, Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# ✅ FIXED - Added closing parentheses
from .create import (
    move_add_callback,
    move_skip_description_callback,
    move_asset_callback,
    move_direction_callback,
    move_skip_target_callback,
    move_cancel_callback,
    move_confirm_save_callback,
    move_expiry_callback,
)

# ✅ Import view handlers if they exist
try:
    from .view import (
        move_view_callback,
        move_detail_callback,
    )
except (ImportError, ModuleNotFoundError):
    logger.warning("⚠️ view.py not found - view handlers disabled")
    move_view_callback = None
    move_detail_callback = None

# ✅ Import edit handlers if they exist
try:
    from .edit import (
        move_edit_list_callback,
        move_edit_select_callback,
        move_edit_field_callback,
        move_edit_save_callback,
        move_edit_cancel_callback,
    )
except (ImportError, ModuleNotFoundError):
    logger.warning("⚠️ edit.py not found - edit handlers disabled")
    move_edit_list_callback = None
    move_edit_select_callback = None
    move_edit_field_callback = None
    move_edit_save_callback = None
    move_edit_cancel_callback = None

# ✅ Import delete handlers if they exist
try:
    from .delete import (
        move_delete_list_callback,
        move_delete_confirm_callback,
        move_delete_cancel_callback,
    )
except (ImportError, ModuleNotFoundError):
    logger.warning("⚠️ delete.py not found - delete handlers disabled")
    move_delete_list_callback = None
    move_delete_confirm_callback = None
    move_delete_cancel_callback = None


def register_move_strategy_handlers(application: Application):
    """
    Register all MOVE strategy callback handlers.
    
    Args:
        application: Telegram bot application instance
    """
    
    try:
        logger.info("🚀 Registering MOVE strategy handlers...")
        
        # ✅ Menu callback (from main_menu.py button)
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^menu_move_strategy$"
        ))
        logger.info("  ✓ menu_move_strategy registered")
        
        # Create handlers
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_add$"
        ))
        
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
            move_skip_target_callback, 
            pattern="^move_skip_target$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_cancel_callback, 
            pattern="^move_cancel$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_confirm_save_callback, 
            pattern="^move_save$"
        ))
        
        # View handlers (if available)
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
        
        # Edit handlers (if available)
        if move_edit_list_callback:
            application.add_handler(CallbackQueryHandler(
                move_edit_list_callback, 
                pattern="^move_edit_list$"
            ))
        
        if move_edit_select_callback:
            application.add_handler(CallbackQueryHandler(
                move_edit_select_callback, 
                pattern="^move_edit_select_"
            ))
        
        if move_edit_field_callback:
            application.add_handler(CallbackQueryHandler(
                move_edit_field_callback, 
                pattern="^move_field_"
            ))
        
        if move_edit_save_callback:
            application.add_handler(CallbackQueryHandler(
                move_edit_save_callback, 
                pattern="^move_edit_save$"
            ))
        
        if move_edit_cancel_callback:
            application.add_handler(CallbackQueryHandler(
                move_edit_cancel_callback, 
                pattern="^move_edit_cancel$"
            ))
        
        # Delete handlers (if available)
        if move_delete_list_callback:
            application.add_handler(CallbackQueryHandler(
                move_delete_list_callback, 
                pattern="^move_delete_list$"
            ))
        
        if move_delete_confirm_callback:
            application.add_handler(CallbackQueryHandler(
                move_delete_confirm_callback, 
                pattern="^move_delete_confirm_"
            ))
        
        if move_delete_cancel_callback:
            application.add_handler(CallbackQueryHandler(
                move_delete_cancel_callback, 
                pattern="^move_delete_cancel$"
            ))
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE strategy handlers: {e}", exc_info=True)
        raise


__all__ = [
    'register_move_strategy_handlers',
    'move_add_callback',
            ]
