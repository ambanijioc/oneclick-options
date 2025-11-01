"""MOVE Trade Handlers - Manual + Auto (same folder)"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_handlers(application: Application) -> None:
    """Main entry point - register all trade handlers"""
    try:
        logger.info("🔍 Registering MOVE trade handlers (manual + auto)...")
        register_move_manual_trade_handlers(application)
        register_move_auto_trade_handlers(application)
        logger.info("✅ All MOVE trade handlers registered")
    except Exception as e:
        logger.error(f"❌ Error registering MOVE trade handlers: {e}", exc_info=True)


def register_move_manual_trade_handlers(application: Application) -> None:
    """Register MOVE manual trade handlers - NOT ASYNC"""
    try:
        from bot.handlers.move.trade.move_manual_trade_handler import (
            move_manual_trade_callback,
        )
        
        logger.info("  └─ Loading manual trade handlers...")
        
        # Callback: move_manual_trade button
        application.add_handler(
            CallbackQueryHandler(
                move_manual_trade_callback,
                pattern=r"^move_manual_trade$"
            ),
            group=1
        )
        
        logger.info("  ✓ Manual trade handlers registered")
        
    except ModuleNotFoundError as e:
        logger.warning(f"⚠️ Manual trade handler not found: {e}")
    except Exception as e:
        logger.error(f"❌ Manual trade handler error: {e}", exc_info=True)


def register_move_auto_trade_handlers(application: Application) -> None:
    """Register MOVE auto trade handlers - NOT ASYNC"""
    try:
        from bot.handlers.move.trade.move_auto_trade_handler import (
            move_auto_trade_callback,
            move_auto_execute_trade_callback,
        )
        
        logger.info("  └─ Loading auto trade handlers...")
        
        # Callback: move_auto_trade (button click)
        application.add_handler(
            CallbackQueryHandler(
                move_auto_trade_callback,
                pattern=r"^move_auto_trade$"
            ),
            group=1
        )
        
        # Callback: move_auto_trade_* (execute strategy)
        application.add_handler(
            CallbackQueryHandler(
                move_auto_execute_trade_callback,
                pattern=r"^move_auto_trade_.*"
            ),
            group=1
        )
        
        logger.info("  ✓ Auto trade handlers registered")
        
    except ModuleNotFoundError as e:
        logger.warning(f"⚠️ Auto trade handler not found: {e}")
    except Exception as e:
        logger.error(f"❌ Auto trade handler error: {e}", exc_info=True)


__all__ = [
    'register_handlers',
    'register_move_manual_trade_handlers',
    'register_move_auto_trade_handlers',
]
