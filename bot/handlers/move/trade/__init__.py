"""
MOVE Trade Handlers Module - Central registration point
Handles both manual and auto trade execution
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_manual_trade_handlers(application: Application) -> None:
    """Register MOVE manual trade handlers."""
    try:
        from bot.handlers.move.trade.manual import (
            move_manual_trade_callback,
            handle_move_manual_entry_price,
            handle_move_manual_lot_size,
            handle_move_manual_sl_price,
            handle_move_manual_target_price,
            handle_move_manual_direction,
            handle_move_manual_strategy_select
        )
        
        # Callback for initial button click
        application.add_handler(
            CallbackQueryHandler(
                move_manual_trade_callback,
                pattern=r"^move_manual_trade|^move_trade_manual_"
            )
        )
        
        # Text input handlers for multi-step form (must be low priority)
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_entry_price
            ),
            group=10  # Higher group number = lower priority
        )
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_lot_size
            ),
            group=10
        )
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_sl_price
            ),
            group=10
        )
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_target_price
            ),
            group=10
        )
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_direction
            ),
            group=10
        )
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_strategy_select
            ),
            group=10
        )
        
        logger.info("✅ MOVE manual trade handlers registered")
        
    except ImportError as e:
        logger.error(f"Import error in manual trade handlers: {e}")
    except Exception as e:
        logger.error(f"Error registering manual trade handlers: {e}")


def register_auto_trade_handlers(application: Application) -> None:
    """Register MOVE auto trade handlers."""
    try:
        from bot.handlers.move.trade.auto import (
            move_auto_trade_callback,
            move_auto_execute_trade_callback
        )
        
        # Initial callback
        application.add_handler(
            CallbackQueryHandler(
                move_auto_trade_callback,
                pattern=r"^move_auto_trade$"
            )
        )
        
        # Strategy selection callback
        application.add_handler(
            CallbackQueryHandler(
                move_auto_execute_trade_callback,
                pattern=r"^move_auto_trade_"
            )
        )
        
        logger.info("✅ MOVE auto trade handlers registered")
        
    except ImportError as e:
        logger.error(f"Import error in auto trade handlers: {e}")
    except Exception as e:
        logger.error(f"Error registering auto trade handlers: {e}")


__all__ = [
    'register_manual_trade_handlers',
    'register_auto_trade_handlers'
]
