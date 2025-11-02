"""
MOVE Strategy handlers initialization and registration.

Manages handler registration for:
- Strategy creation (name, description, asset, expiry, direction)
- Risk management (SL/Target setup)
- Confirmation and cancellation
- Text input processing via centralized message router

Key Fix: Single message handler with state-based routing instead of multiple handlers
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
        
        # ✅ Skip description
        application.add_handler(
            CallbackQueryHandler(move_skip_description_callback, pattern="^move_skip_description$"),
            group=10
        )
        
        # ✅ Skip target
        application.add_handler(
            CallbackQueryHandler(move_skip_target_callback, pattern="^move_skip_target$"),
            group=10
        )
        
        # Asset selection
        application.add_handler(
            CallbackQueryHandler(move_asset_callback, pattern="^move_asset_(BTC|ETH)$"),
            group=10
        )
        
        # Expiry selection
        application.add_handler(
            CallbackQueryHandler(move_expiry_callback, pattern="^move_expiry_(daily|weekly)$"),
            group=10
        )
        
        # Direction selection
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
        
        logger.info("✅ MOVE strategy callback handlers registered (Group 10)")
        
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE callback handlers: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Error registering MOVE callback handlers: {e}", exc_info=True)
    
    # ==================== TEXT INPUT HANDLER (Group 11) ====================
    # ✅ FIX: SINGLE MESSAGE HANDLER instead of multiple handlers
    try:
        from bot.handlers.move.strategy.message_router import route_move_message
        
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


__all__ = ['register_move_strategy_handlers']
