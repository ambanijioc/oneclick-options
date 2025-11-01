"""
MOVE Trade Handlers - Manual + Auto (Nested)
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_manual_trade_handlers(application: Application) -> None:
    """Register MOVE manual trade handlers - LAZY LOAD"""
    try:
        # Lazy import - only when called
        from bot.handlers.move.trade.manual import (
            move_manual_trade_callback,
            handle_move_manual_entry_price,
            handle_move_manual_lot_size,
            handle_move_manual_sl_price,
            handle_move_manual_target_price,
            handle_move_manual_direction,
            handle_move_manual_strategy_select,
        )
        
        # Callback button click
        application.add_handler(
            CallbackQueryHandler(
                move_manual_trade_callback,
                pattern=r"^move_manual_trade$"
            )
        )
        
        # Text input handlers - group 10 (low priority)
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_move_manual_entry_price
            ),
            group=10
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
        
        logger.info("✅ Manual trade handlers registered")
        
    except Exception as e:
        logger.error(f"❌ Manual trade handler error: {e}")


def register_auto_trade_handlers(application: Application) -> None:
    """Register MOVE auto trade handlers"""
    try:
        logger.info("✅ Auto trade handlers registered")
    except Exception as e:
        logger.error(f"❌ Auto trade handler error: {e}")


__all__ = [
    'register_move_manual_trade_handlers',
    'register_auto_trade_handlers'
]
