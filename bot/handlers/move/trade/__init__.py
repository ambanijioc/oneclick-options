"""MOVE Trade Handler Submodule - Manual & Auto Trading"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_trade_handlers(application: Application):
    """
    Register all MOVE trade handlers.
    
    Includes:
    - Manual trade execution
    - Auto trade execution
    - Trade monitoring
    """
    
    # ✅ Import and register manual trade handlers
    try:
        from bot.handlers.move.trade.manual import register_move_manual_trade_handlers as _register_manual
        _register_manual(application)
        logger.info("✅ MOVE Manual Trade handlers registered")
    except ImportError as e:
        logger.warning(f"⚠️ MOVE Manual Trade handlers not available: {e}")
    except Exception as e:
        logger.error(f"❌ MOVE Manual Trade handler error: {e}")
    
    # ✅ Import and register auto trade handlers
    try:
        from bot.handlers.move.trade.auto import register_move_auto_trade_handlers as _register_auto
        _register_auto(application)
        logger.info("✅ MOVE Auto Trade handlers registered")
    except ImportError:
        logger.warning("⚠️ MOVE Auto Trade handlers not available")
    except Exception as e:
        logger.error(f"❌ MOVE Auto Trade handler error: {e}")
    
    logger.info("✅ All MOVE Trade handlers registered")


# ✅ EXPORT for direct imports in main handler registration
def register_move_manual_trade_handlers(application: Application):
    """Wrapper for manual trade handler registration"""
    try:
        from bot.handlers.move.trade.manual import register_move_manual_trade_handlers as _reg
        return _reg(application)
    except ImportError:
        logger.warning("⚠️ Manual trade handler not found")
        return None


def register_move_auto_trade_handlers(application: Application):
    """Wrapper for auto trade handler registration"""
    try:
        from bot.handlers.move.trade.auto import register_move_auto_trade_handlers as _reg
        return _reg(application)
    except ImportError:
        logger.warning("⚠️ Auto trade handler not found")
        return None


__all__ = [
    'register_move_trade_handlers',
    'register_move_manual_trade_handlers',  # ✅ EXPORT
    'register_move_auto_trade_handlers',     # ✅ EXPORT
]
