"""
MOVE Trade Preset CRUD Operations - Create, View, Edit, Delete MOVE Trade Presets
"""

from telegram.ext import CallbackQueryHandler, Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application):
    """Register all MOVE preset CRUD handlers."""
    
    try:
        logger.info("🚀 Registering MOVE preset handlers...")
        
        # Import handlers from modules
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
            move_preset_edit_select_callback,
            move_preset_edit_save_callback
        )
        
        from .delete import (
            move_preset_delete_callback,
            move_preset_delete_confirm_callback,
            move_preset_delete_execute_callback
        )
        
        # ===== REGISTER CREATE HANDLERS =====
        application.add_handler(CallbackQueryHandler(
            move_preset_add_callback, 
            pattern="^move_preset$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_add_new_callback, 
            pattern="^move_preset_add$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_confirm_save_callback, 
            pattern="^move_preset_confirm_save$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_cancel_callback, 
            pattern="^move_preset_cancel$"
        ))
        
        # ===== REGISTER VIEW HANDLERS =====
        application.add_handler(CallbackQueryHandler(
            move_preset_view_callback, 
            pattern="^move_preset_view$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_view_details_callback, 
            pattern="^move_preset_view_[a-f0-9]{24}$"
        ))
        
        # ===== REGISTER EDIT HANDLERS =====
        application.add_handler(CallbackQueryHandler(
            move_preset_edit_callback, 
            pattern="^move_preset_edit$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_edit_select_callback, 
            pattern="^move_preset_edit_[a-f0-9]{24}$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_edit_save_callback, 
            pattern="^move_preset_edit_save_"
        ))
        
        # ===== REGISTER DELETE HANDLERS =====
        application.add_handler(CallbackQueryHandler(
            move_preset_delete_callback, 
            pattern="^move_preset_delete$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_delete_confirm_callback, 
            pattern="^move_preset_delete_[a-f0-9]{24}$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            move_preset_delete_execute_callback, 
            pattern="^move_preset_delete_confirmed_"
        ))
        
        logger.info("✅ All MOVE preset handlers registered successfully!")
        
    except ImportError as e:
        logger.warning(f"⚠️ Some MOVE preset modules not found yet: {e}")
        logger.info("Create the missing preset modules (create.py, view.py, edit.py, delete.py)")
    except Exception as e:
        logger.error(f"❌ Error in MOVE preset handler registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_preset_handlers']
