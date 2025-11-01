"""
MOVE Trade Handlers Module (Manual + Auto)
Handles both manual and automatic trade execution for MOVE strategies.
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_handlers(application: Application) -> None:
    """Register manual trade handlers (entry point from parent)"""
    register_move_manual_trade_handlers(application)


def register_move_manual_trade_handlers(application: Application) -> None:
    """
    ✅ Register MOVE manual trade handlers
    Imports actual handler functions from the manual submodule
    """
    try:
        # Import from manual submodule
        from bot.handlers.move.trade.manual import (
            move_manual_trade_callback,
        )
        
        logger.info("🔍 Registering MOVE manual trade handlers...")
        
        # Callback handler for button click: move_manual_trade
        application.add_handler(
            CallbackQueryHandler(
                move_manual_trade_callback,
                pattern=r"^move_manual_trade$"
            ),
            group=1  # High priority
        )
        
        logger.info("✅ Manual trade handlers registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Manual trade handler error: {e}", exc_info=True)


def register_move_auto_trade_handlers(application: Application) -> None:
    """
    ✅ Register MOVE auto trade handlers
    Imports from the auto submodule
    """
    try:
        # Import auto trade handler
        from bot.handlers.move.trade.auto import (
            move_auto_trade_callback,
            move_auto_execute_trade_callback,
        )
        
        logger.info("🔍 Registering MOVE auto trade handlers...")
        
        # Main auto trade button click
        application.add_handler(
            CallbackQueryHandler(
                move_auto_trade_callback,
                pattern=r"^move_auto_trade$"
            ),
            group=1  # High priority
        )
        
        # Auto trade strategy selection callback
        application.add_handler(
            CallbackQueryHandler(
                move_auto_execute_trade_callback,
                pattern=r"^move_auto_trade_.*"  # Matches: move_auto_trade_{ID}
            ),
            group=1
        )
        
        logger.info("✅ Auto trade handlers registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Auto trade handler error: {e}", exc_info=True)


__all__ = [
    'register_handlers',
    'register_move_manual_trade_handlers',
    'register_move_auto_trade_handlers',
]
