"""
MOVE Strategy handlers initialization and registration.

Manages handler registration for:
- Strategy creation (name, description, asset, expiry, direction)
- Risk management (SL/Target setup)
- Confirmation and cancellation
- Text input processing via centralized message router
- Strategy viewing and listing

Key Architecture:
- Group 10: Callback Query Handlers (button clicks)
- Group 11: Message Handler (text input via centralized router)
- All nested imports with proper error handling
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """
    Register all MOVE strategy handlers with proper state-based routing.
    
    Handler Groups:
    - Group 10: Callback Query Handlers (button clicks)
    - Group 11: Message Handler (text input via centralized router)
    
    Key Improvement:
    - Only ONE message handler instead of 8 duplicate handlers
    - State machine determines which input handler processes the message
    - No more conflicting handler chains
    """
    
    logger.info("🔄 Registering MOVE strategy handlers...")
    
    # ==================== CALLBACK HANDLERS (Group 10) ====================
    try:
        from bot.handlers.move.strategy.create import (
            move_add_callback,
            move_add_new_strategy_callback,
            move_skip_description_callback,
            move_skip_target_callback,
            move_asset_callback,
            move_expiry_callback,
            move_direction_callback,
            move_confirm_save_callback,
            move_cancel_callback
        )
        
        # Entry point - "Add Strategy" button
        application.add_handler(
            CallbackQueryHandler(move_add_callback, pattern="^move_menu$"),
            group=10
        )
        
        # New strategy creation flow
        application.add_handler(
            CallbackQueryHandler(move_add_new_strategy_callback, pattern="^move_add_strategy$"),
            group=10
        )
        
        # ✅ Skip description (Optional step)
        application.add_handler(
            CallbackQueryHandler(move_skip_description_callback, pattern="^move_skip_description$"),
            group=10
        )
        
        # ✅ Skip target (Optional step)
        application.add_handler(
            CallbackQueryHandler(move_skip_target_callback, pattern="^move_skip_target$"),
            group=10
        )
        
        # Asset selection (BTC/ETH)
        application.add_handler(
            CallbackQueryHandler(move_asset_callback, pattern="^move_asset_(BTC|ETH)$"),
            group=10
        )
        
        # Expiry selection (daily/weekly)
        application.add_handler(
            CallbackQueryHandler(move_expiry_callback, pattern="^move_expiry_(daily|weekly)$"),
            group=10
        )
        
        # Direction selection (long/short)
        application.add_handler(
            CallbackQueryHandler(move_direction_callback, pattern="^move_direction_(long|short)$"),
            group=10
        )
        
        # Confirmation
        application.add_handler(
            CallbackQueryHandler(move_confirm_save_callback, pattern="^move_confirm_save$"),
            group=10
        )
        
        # Global cancel
        application.add_handler(
            CallbackQueryHandler(move_cancel_callback, pattern="^move_cancel$"),
            group=10
        )
        
        logger.info("✅ MOVE strategy CREATE callbacks registered (Group 10)")
        
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE create callbacks: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Error registering MOVE create callbacks: {e}", exc_info=True)
    
    # ==================== VIEW STRATEGY HANDLERS (Group 10) ====================
    try:
        from bot.handlers.move.strategy.view import (
            view_strategies_list,
            view_strategy_details
        )
        
        # List all strategies
        application.add_handler(
            CallbackQueryHandler(view_strategies_list, pattern="^move_view_list$"),
            group=10
        )
    
        # ✅ View Strategy Details
        application.add_handler(
            CallbackQueryHandler(view_strategy_details, pattern="^move_view_strategy_.*"),
            group=10
        )
        
        logger.info("✅ MOVE strategy VIEW callbacks registered (Group 10)")
        
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE view callbacks: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Error registering MOVE view callbacks: {e}", exc_info=True)

    # ==================== EDIT CALLBACKS (Group 10) ====================
    # ✅ FIXED: Patterns ordered by SPECIFICITY (most specific LAST for Telegram!)
    try:
        from bot.handlers.move.strategy.edit import (
            move_edit_callback,
            move_edit_select_callback,
            move_edit_field_callback,
            move_edit_save_callback
        )
        
        # 1️⃣ Entry point - "Edit Strategy" button FROM MAIN MENU (move_edit)
        application.add_handler(
            CallbackQueryHandler(move_edit_callback, pattern="^move_edit$"),
            group=10
        )
        
        # 2️⃣ SPECIFIC - Save callback-based edits (move_edit_save_*)
        application.add_handler(
            CallbackQueryHandler(move_edit_save_callback, pattern="^move_edit_save_"),
            group=10
        )
        
        # 3️⃣ SPECIFIC - Select field to edit (move_edit_field_*)
        application.add_handler(
            CallbackQueryHandler(move_edit_field_callback, pattern="^move_edit_field_"),
            group=10
        )
        
        # 4️⃣ GENERIC LAST - Select strategy to edit (move_edit_{id})
        # This pattern MUST be LAST because it's the most generic!
        application.add_handler(
            CallbackQueryHandler(move_edit_select_callback, pattern="^move_edit_[0-9a-f]{24}$"),
            group=10
        )
        
        logger.info("✅ MOVE strategy EDIT callbacks registered (Group 10)")
        
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE edit callbacks: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Error registering MOVE edit callbacks: {e}", exc_info=True)

    # ==================== DELETE CALLBACKS (Group 10) ====================
    try:
        from bot.handlers.move.strategy.delete import (
            move_delete_callback,
            move_delete_confirm_callback,
            move_delete_execute_callback
        )
        
        # Show delete list
        application.add_handler(
            CallbackQueryHandler(move_delete_callback, pattern="^move_delete$"),
            group=10
        )
        
        # ✅ SPECIFIC FIRST - Execute deletion (callback: move_delete_confirmed_{strategy_id})
        application.add_handler(
            CallbackQueryHandler(move_delete_execute_callback, pattern="^move_delete_confirmed_.*"),
            group=10
        )
        
        # ✅ GENERIC LAST - Confirm deletion (callback: move_delete_{strategy_id})
        application.add_handler(
            CallbackQueryHandler(move_delete_confirm_callback, pattern="^move_delete_[^_]+$"),
            group=10
        )
        
        logger.info("✅ MOVE strategy DELETE callbacks registered (Group 10)")
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE delete callbacks: {e}", exc_info=True)
        
    # ==================== TEXT INPUT HANDLER (Group 11) ====================
    # ✅ KEY FIX: SINGLE MESSAGE HANDLER instead of multiple handlers
    try:
        from bot.handlers.move.strategy.input_handlers import route_move_message
        
        # Single handler for ALL MOVE text input
        # State machine determines which input handler processes the message
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,  # Match text messages (no commands)
                route_move_message  # Centralized router by state
            ),
            group=11
        )
        
        logger.info("✅ MOVE strategy message router registered (Group 11)")
        
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE message router: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Error registering MOVE message router: {e}", exc_info=True)
    
    logger.info("✅ ALL MOVE strategy handlers registered successfully!")


__all__ = ['register_move_strategy_handlers']
