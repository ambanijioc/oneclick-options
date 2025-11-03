"""
MOVE Strategy & Preset Handlers Module
Complete handler registration for MOVE trading features
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy handlers (Create, Edit, Delete, View, Trade)"""
    try:
        logger.info("🔍 Importing MOVE strategy handlers...")
        from bot.handlers.move.strategy import register_move_strategy_handlers as register_strategy
        register_strategy(application)  # ✅ CORRECT - imports actual handler module
        logger.info("✅ MOVE strategy handlers registered successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ ImportError - MOVE strategy handlers not found: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error registering MOVE strategy handlers: {e}", exc_info=True)
        return False


def register_move_preset_handlers(application: Application):
    """Register MOVE preset handlers (Add, Edit, Delete, View)"""
    try:
        logger.info("🔍 Importing MOVE preset handlers...")
        from bot.handlers.move.preset import register_move_preset_handlers as register_preset
        register_preset(application)  # ✅ CORRECT - imports actual handler module
        logger.info("✅ MOVE preset handlers registered successfully")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ ImportError - MOVE preset handlers not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error registering MOVE preset handlers: {e}", exc_info=True)
        return False


def register_move_trade_handlers(application: Application):
    """Register MOVE trade handlers (Manual Trade, Auto Trade)"""
    try:
        logger.info("🔍 Importing MOVE trade handlers...")
        from bot.handlers.move.trade import (
            register_move_manual_trade_handlers,
            register_move_auto_trade_handlers
        )
        register_move_manual_trade_handlers(application)
        register_move_auto_trade_handlers(application)
        logger.info("✅ MOVE trade handlers registered successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ ImportError - MOVE trade handlers not found: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error registering MOVE trade handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_move_strategy_handlers',
    'register_move_preset_handlers',
    'register_move_trade_handlers',
]
