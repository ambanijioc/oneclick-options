"""
MOVE Trade Handlers Module
Unified handler registration for BOTH manual & auto trades
(Manual + Auto in same folder - no subfolders)
"""

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_handlers(application: Application) -> None:
    """
    ✅ MAIN ENTRY POINT
    Register all MOVE trade handlers (manual + auto)
    Called from: bot/handlers/move/__init__.py
    """
    try:
        logger.info("🔍 Registering MOVE trade handlers (manual + auto)...")
        
        # Register manual trade handlers
        register_move_manual_trade_handlers(application)
        
        # Register auto trade handlers
        register_move_auto_trade_handlers(application)
        
        logger.info("✅ All MOVE trade handlers registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE trade handlers: {e}", exc_info=True)


def register_move_manual_trade_handlers(application: Application) -> None:
    """Register MOVE manual trade handlers"""
    try:
        from bot.handlers.move.trade.move_manual_trade_handler import (
            move_manual_trade_callback,
        )
        
        logger.info("  └─ Loading manual trade handlers...")
        
        # Callback: move_manual_trade (button click)
        application.add_handler(
            CallbackQueryHandler(
                move_manual_trade_callback,
                pattern=r"^move_manual_trade$"
            ),
            group=1
        )
        
        logger.info("  ✓ Manual trade handlers registered")
        
    except Exception as e:
        logger.error(f"❌ Manual trade handler error: {e}", exc_info=True)


def register_move_auto_trade_handlers(application: Application) -> None:
    """Register MOVE auto trade handlers"""
    try:
        from bot.handlers.move.trade.move_auto_trade_handler import (
            move_auto_trade_callback,
            move_auto_execute_trade_callback,
        )
        
        logger.info("  └─ Loading auto trade handlers...")
        
        # Callback: move_auto_trade (button click to show strategies)
        application.add_handler(
            CallbackQueryHandler(
                move_auto_trade_callback,
                pattern=r"^move_auto_trade$"
            ),
            group=1
        )
        
        # Callback: move_auto_trade_{strategy_id} (execute trade)
        application.add_handler(
            CallbackQueryHandler(
                move_auto_execute_trade_callback,
                pattern=r"^move_auto_trade_.*"
            ),
            group=1
        )
        
        logger.info("  ✓ Auto trade handlers registered")
        
    except Exception as e:
        logger.error(f"❌ Auto trade handler error: {e}", exc_info=True)


__all__ = [
    'register_handlers',
    'register_move_manual_trade_handlers',
    'register_move_auto_trade_handlers',
]
