"""
MOVE Strategy handlers initialization and registration.

Manages handler registration for:
- Strategy creation (name, description, asset, expiry, direction)
- Risk management (SL/Target setup)
- Confirmation and cancellation
- Text input processing
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """
    Register all MOVE strategy handlers.
    
    Handler Groups:
    - Group 10: Callback Query Handlers (priority)
    - Group 11: Message Handlers (secondary)
    
    Patterns:
    - Callbacks: move_* patterns for routing
    - Messages: Filtered by state machine via message_router
    """
    
    # ==================== CREATE CALLBACKS ====================
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
        
        # ✅ SKIP DESCRIPTION - Fixed
        application.add_handler(
            CallbackQueryHandler(move_skip_description_callback, pattern="^move_skip_description$"),
            group=10
        )
        
        # ✅ SKIP TARGET - Fixed
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
        
        logger.info("✅ MOVE strategy create handlers registered (Group 10)")
        
    except ImportError as e:
        logger.error(f"❌ Error importing MOVE create handlers: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Error registering MOVE create handlers: {e}", exc_info=True)
    
    # ==================== INPUT TEXT HANDLERS ====================
    try:
        from bot.handlers.move.strategy.input_handlers import (
            handle_move_strategy_name,
            handle_move_description,           # ✅ Added
            handle_move_lot_size,
            handle_move_atm_offset,
            handle_move_sl_trigger,
            handle_move_sl_limit,
            handle_move_target_trigger,
            handle_move_target_limit
        )
        
        # All text inputs routed via state machine (message_router)
        # These handlers check state and validate input
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_strategy_name),
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_description),  # ✅ Added
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_lot_size),
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_atm_offset),
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_sl_trigger),
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_sl_limit),
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_target_trigger),
            group=11
        )
        
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_target_limit),
            group=11
        )
        
        logger.info("✅ MOVE strategy input handlers registered (Group 11)")
        
    except ImportError as e:
        logger.warning(f"⚠️ MOVE input handlers not fully available: {e}")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE input handlers: {e}", exc_info=True)


__all__ = ['register_move_strategy_handlers']
