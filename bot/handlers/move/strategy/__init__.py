"""
MOVE Strategy handlers initialization and registration.
Imports from create, delete, edit, and view modules.
"""

from telegram.ext import Application, CallbackQueryHandler
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

def register_move_strategy_handlers(application: Application):
    """Register all MOVE strategy handlers."""
    
    # ==================== CREATE HANDLERS ====================
    try:
        from bot.handlers.move.strategy.create import (
            move_add_callback,
            move_add_new_strategy_callback,  # ✅ ADD THIS
            move_skip_description_callback,
            move_asset_callback,
            move_expiry_callback,
            move_direction_callback,
            move_confirm_save_callback,
            move_skip_target_callback,
            move_cancel_callback
        )
        
        application.add_handler(CallbackQueryHandler(
            move_add_callback, pattern="^move_menu$"), group=10)

        # ✅ ADD THIS - Handle "Add Strategy" button
        application.add_handler(CallbackQueryHandler(
            move_add_new_strategy_callback, pattern="^move_add_strategy$"), group=10)
     
        application.add_handler(CallbackQueryHandler(
            move_skip_description_callback, pattern="^move_skip_description$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_asset_callback, pattern="^move_asset_(btc|eth)$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_expiry_callback, pattern="^move_expiry_(daily|weekly)$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_direction_callback, pattern="^move_direction_(long|short)$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_confirm_save_callback, pattern="^move_confirm_save$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_skip_target_callback, pattern="^move_skip_target$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_cancel_callback, pattern="^move_cancel$"), group=10)
        
        logger.info("✅ MOVE create handlers registered")
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE create handlers: {e}")
    
    # ==================== EDIT HANDLERS ====================
    try:
        from bot.handlers.move.strategy.edit import (
            move_edit_callback,
            move_edit_select_callback,
            move_edit_field_callback,
            move_edit_save_callback
        )
        
        application.add_handler(CallbackQueryHandler(
            move_edit_callback, pattern="^move_edit$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_edit_select_callback, pattern="^move_edit_[0-9a-f]{24}$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_edit_field_callback, pattern="^move_edit_field_"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_edit_save_callback, pattern="^move_edit_save_"), group=10)
        
        logger.info("✅ MOVE edit handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE edit handlers not available: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE edit handlers: {e}")
    
    # ==================== DELETE HANDLERS ====================
    try:
        from bot.handlers.move.strategy.delete import (
            move_delete_callback,
            move_delete_confirm_callback,
            move_delete_execute_callback
        )
        
        application.add_handler(CallbackQueryHandler(
            move_delete_callback, pattern="^move_delete$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_delete_confirm_callback, pattern="^move_delete_[0-9a-f]{24}$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_delete_execute_callback, pattern="^move_delete_confirmed_"), group=10)
        
        logger.info("✅ MOVE delete handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE delete handlers not available: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE delete handlers: {e}")
    
    # ==================== VIEW HANDLERS ====================
    try:
        from bot.handlers.move.strategy.view import (
            move_view_callback,
            move_view_detail_callback,
            move_list_all_callback,
            move_strategy_status
        )
        
        application.add_handler(CallbackQueryHandler(
            move_view_callback, pattern="^move_view$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_view_detail_callback, pattern="^move_view_[0-9a-f]{24}$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_list_all_callback, pattern="^move_list_all$"), group=10)
        application.add_handler(CallbackQueryHandler(
            move_strategy_status, pattern="^move_status_"), group=10)
        
        logger.info("✅ MOVE view handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE view handlers not available: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE view handlers: {e}")
    
    logger.info("✅ ALL MOVE strategy handlers registered")

__all__ = ['register_move_strategy_handlers']
        
