"""
MOVE Preset Handlers
Handles creation, viewing, editing, and deletion of MOVE trade presets.
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application):
    """Register all MOVE preset handlers."""
    
    try:
        logger.info("🔍 Registering MOVE preset handlers...")
        
        # Import handlers
        from .create import (
            move_preset_add_callback,
            move_preset_add_new_callback,
            move_preset_confirm_save_callback,
            move_preset_cancel_callback
        )
        from .view import (
            move_preset_view_callback,
            move_preset_view_details_callback
        )
        from .edit import (
            move_preset_edit_callback,
            move_preset_edit_select_callback
        )
        from .delete import (
            move_preset_delete_callback,
            move_preset_delete_confirm_callback,
            move_preset_delete_execute_callback
        )
        
        # Register CREATE handlers
        application.add_handler(CallbackQueryHandler(move_preset_add_callback, pattern="^menu_move_preset$"))
        application.add_handler(CallbackQueryHandler(move_preset_add_new_callback, pattern="^move_preset_add_new$"))
        application.add_handler(CallbackQueryHandler(move_preset_confirm_save_callback, pattern="^move_preset_confirm_save$"))
        application.add_handler(CallbackQueryHandler(move_preset_cancel_callback, pattern="^move_preset_cancel$"))
        
        # Register VIEW handlers
        application.add_handler(CallbackQueryHandler(move_preset_view_callback, pattern="^move_preset_view$"))
        application.add_handler(CallbackQueryHandler(move_preset_view_details_callback, pattern="^move_preset_view_details_"))
        
        # Register EDIT handlers
        application.add_handler(CallbackQueryHandler(move_preset_edit_callback, pattern="^move_preset_edit$"))
        application.add_handler(CallbackQueryHandler(move_preset_edit_select_callback, pattern="^move_preset_edit_select_"))
        
        # Register DELETE handlers
        application.add_handler(CallbackQueryHandler(move_preset_delete_callback, pattern="^move_preset_delete$"))
        application.add_handler(CallbackQueryHandler(move_preset_delete_confirm_callback, pattern="^move_preset_delete_confirm_"))
        application.add_handler(CallbackQueryHandler(move_preset_delete_execute_callback, pattern="^move_preset_delete_execute_"))
        
        # Register input handlers (text input)
        from .input_handlers import (
            handle_move_preset_name_input,
            handle_move_preset_entry_lots_input,
            handle_move_preset_exit_lots_input
        )
        
        logger.info("✅ MOVE preset handlers registered successfully!")
    
    except Exception as e:
        logger.error(f"❌ Error registering MOVE preset handlers: {e}", exc_info=True)
        raise


__all__ = ['register_move_preset_handlers']
