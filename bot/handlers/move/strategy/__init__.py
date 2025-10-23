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
        
        # ===== CREATE HANDLERS =====
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
        
        # ===== VIEW HANDLERS =====
        from .view import (
            move_view_callback,
            move_view_details_callback
        )
        
        # ===== EDIT HANDLERS =====
        from .edit import (
            move_edit_callback,
            move_edit_select_callback,
            move_edit_field_callback,
            move_update_field_callback,
            move_continue_edit_callback
        )
        
        # ===== DELETE HANDLERS =====
        from .delete import (
            move_delete_callback,
            move_delete_confirm_callback,
            move_delete_execute_callback
        )
        
        # ===== REGISTER MENU HANDLER =====
        application.add_handler(CallbackQueryHandler(
            move_add_callback, 
            pattern="^move_menu$"
        ))
        
        # ===== REGISTER CREATE HANDLERS =====
        application.add_handler(CallbackQueryHandler(move_add_new_callback, pattern="^move_add$"))
        application.add_handler(CallbackQueryHandler(move_skip_description_callback, pattern="^move_skip_description$"))
        application.add_handler(CallbackQueryHandler(move_asset_callback, pattern="^move_asset_"))
        application.add_handler(CallbackQueryHandler(move_expiry_callback, pattern="^move_expiry_"))
        application.add_handler(CallbackQueryHandler(move_direction_callback, pattern="^move_direction_"))
        application.add_handler(CallbackQueryHandler(move_confirm_save_callback, pattern="^move_confirm_save$"))
        application.add_handler(CallbackQueryHandler(move_skip_target_callback, pattern="^move_skip_target$"))
        application.add_handler(CallbackQueryHandler(move_cancel_callback, pattern="^move_cancel$"))
        
        # ===== REGISTER VIEW HANDLERS =====
        application.add_handler(CallbackQueryHandler(move_view_callback, pattern="^move_view$"))
        application.add_handler(CallbackQueryHandler(move_view_details_callback, pattern="^move_view_details_"))
        
        # ===== REGISTER EDIT HANDLERS =====
        application.add_handler(CallbackQueryHandler(move_edit_callback, pattern="^move_edit_list$"))
        application.add_handler(CallbackQueryHandler(move_edit_select_callback, pattern="^move_edit_select_"))
        application.add_handler(CallbackQueryHandler(move_edit_field_callback, pattern="^move_edit_field_"))
        application.add_handler(CallbackQueryHandler(move_update_field_callback, pattern="^move_(asset|expiry|direction)_"))
        application.add_handler(CallbackQueryHandler(move_continue_edit_callback, pattern="^move_continue_edit_"))
        
        # ===== REGISTER DELETE HANDLERS =====
        application.add_handler(CallbackQueryHandler(move_delete_callback, pattern="^move_delete_list$"))
        application.add_handler(CallbackQueryHandler(move_delete_confirm_callback, pattern="^move_delete_confirm_"))
        application.add_handler(CallbackQueryHandler(move_delete_execute_callback, pattern="^move_delete_execute_"))
        
        logger.info("✅ MOVE strategy handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in MOVE strategy registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_strategy_handlers']
