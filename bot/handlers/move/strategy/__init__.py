"""
MOVE Strategy handlers initialization and registration.
"""

from telegram.ext import Application, CallbackQueryHandler
from bot.handlers.move.strategy.create import (
    move_add_callback,
    move_skip_description_callback,
    move_asset_callback,
    move_expiry_callback,
    move_direction_callback,
    move_confirm_save_callback,
    move_skip_target_callback,
    move_cancel_callback
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

def register_move_strategy_handlers(application: Application):
    """Register all MOVE strategy handlers - Create, Edit, Delete, View."""
    
    # ==================== CREATE HANDLERS ====================
    
    # Main menu button - "🎯 Move Strategy"
    application.add_handler(CallbackQueryHandler(
        move_add_callback,
        pattern="^move_menu$"
    ), group=10)
    
    # Description skip
    application.add_handler(CallbackQueryHandler(
        move_skip_description_callback,
        pattern="^move_skip_description$"
    ), group=10)
    
    # Asset selection
    application.add_handler(CallbackQueryHandler(
        move_asset_callback,
        pattern="^move_asset_(btc|eth)$"
    ), group=10)
    
    # Expiry selection
    application.add_handler(CallbackQueryHandler(
        move_expiry_callback,
        pattern="^move_expiry_(daily|weekly)$"
    ), group=10)
    
    # Direction selection
    application.add_handler(CallbackQueryHandler(
        move_direction_callback,
        pattern="^move_direction_(long|short)$"
    ), group=10)
    
    # Confirm & Save
    application.add_handler(CallbackQueryHandler(
        move_confirm_save_callback,
        pattern="^move_confirm_save$"
    ), group=10)
    
    # Skip Target
    application.add_handler(CallbackQueryHandler(
        move_skip_target_callback,
        pattern="^move_skip_target$"
    ), group=10)
    
    # Cancel
    application.add_handler(CallbackQueryHandler(
        move_cancel_callback,
        pattern="^move_cancel$"
    ), group=10)
    
    # ==================== EDIT HANDLERS ====================
    try:
        from bot.handlers.move.strategy.edit import (
            move_edit_callback,
            move_edit_name_callback,
            move_edit_description_callback,
            move_edit_lot_size_callback,
            move_save_edited_callback,
            move_cancel_edit_callback
        )
        
        # Edit menu
        application.add_handler(CallbackQueryHandler(
            move_edit_callback,
            pattern="^move_edit$"
        ), group=10)
        
        # Edit name
        application.add_handler(CallbackQueryHandler(
            move_edit_name_callback,
            pattern="^move_edit_name$"
        ), group=10)
        
        # Edit description
        application.add_handler(CallbackQueryHandler(
            move_edit_description_callback,
            pattern="^move_edit_description$"
        ), group=10)
        
        # Edit lot size
        application.add_handler(CallbackQueryHandler(
            move_edit_lot_size_callback,
            pattern="^move_edit_lot_size$"
        ), group=10)
        
        # Save edited
        application.add_handler(CallbackQueryHandler(
            move_save_edited_callback,
            pattern="^move_save_edited$"
        ), group=10)
        
        # Cancel edit
        application.add_handler(CallbackQueryHandler(
            move_cancel_edit_callback,
            pattern="^move_cancel_edit$"
        ), group=10)
        
        logger.info("✅ MOVE edit handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE edit handlers not found: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE edit handlers: {e}", exc_info=True)
    
    # ==================== DELETE HANDLERS ====================
    try:
        from bot.handlers.move.strategy.delete import (
            move_delete_callback,
            move_confirm_delete_callback,
            move_cancel_delete_callback
        )
        
        # Delete menu
        application.add_handler(CallbackQueryHandler(
            move_delete_callback,
            pattern="^move_delete$"
        ), group=10)
        
        # Confirm delete
        application.add_handler(CallbackQueryHandler(
            move_confirm_delete_callback,
            pattern="^move_confirm_delete$"
        ), group=10)
        
        # Cancel delete
        application.add_handler(CallbackQueryHandler(
            move_cancel_delete_callback,
            pattern="^move_cancel_delete$"
        ), group=10)
        
        logger.info("✅ MOVE delete handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE delete handlers not found: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE delete handlers: {e}", exc_info=True)
    
    # ==================== VIEW HANDLERS ====================
    try:
        from bot.handlers.move.strategy.view import (
            move_view_callback,
            move_select_strategy_callback
        )
        
        # View menu
        application.add_handler(CallbackQueryHandler(
            move_view_callback,
            pattern="^move_view$"
        ), group=10)
        
        # Select strategy to view
        application.add_handler(CallbackQueryHandler(
            move_select_strategy_callback,
            pattern="^move_view_strategy_.*$"
        ), group=10)
        
        logger.info("✅ MOVE view handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE view handlers not found: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE view handlers: {e}", exc_info=True)
    
    logger.info("✅ ALL MOVE strategy handlers registered")

__all__ = ['register_move_strategy_handlers']
