"""
MOVE Strategy & Trade Handlers - Nested structure
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# ✅ NO DIRECT IMPORTS - Use lazy loading to avoid circular dependencies

def register_move_handlers(application: Application) -> None:
    """Register all MOVE handlers (strategy + trade)"""
    
    try:
        # Strategy handlers
        logger.info("🔍 Registering MOVE strategy handlers...")
        from bot.handlers.move.strategy import register_move_strategy_handlers
        register_move_strategy_handlers(application)
        logger.info("✓ MOVE strategy handlers registered")
    except Exception as e:
        logger.error(f"❌ MOVE strategy handler error: {e}")
    
    try:
        # Trade handlers (manual + auto)
        logger.info("🔍 Registering MOVE trade handlers (nested: manual + auto)...")
        from bot.handlers.move.trade import (
            register_manual_trade_handlers,
            register_auto_trade_handlers
        )
        register_manual_trade_handlers(application)
        register_auto_trade_handlers(application)
        logger.info("✓ MOVE trade handlers registered")
    except Exception as e:
        logger.error(f"❌ Move trade handler error: {e}")


__all__ = ['register_move_handlers']
