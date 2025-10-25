"""
MOVE Trade Execution Handlers
Manual + Auto Trade Execution for MOVE strategies
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_trade_handlers(application: Application):
    """Register all MOVE trade execution handlers."""
    
    try:
        logger.info("🚀 Registering MOVE trade handlers...")
        
        # ===== MOVE MANUAL TRADE HANDLERS =====
        try:
            from .manual import register_move_manual_trade_handlers
            register_move_manual_trade_handlers(application)
            logger.info("✅ MOVE manual trade handlers registered")
        except ImportError as e:
            logger.error(f"❌ Move manual trade handler import failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE manual trade handlers: {e}", exc_info=True)
        
        # ===== MOVE AUTO TRADE HANDLERS =====
        try:
            from .auto import register_move_auto_trade_handlers
            register_move_auto_trade_handlers(application)
            logger.info("✅ MOVE auto trade handlers registered")
        except ImportError as e:
            logger.error(f"❌ Move auto trade handler import failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE auto trade handlers: {e}", exc_info=True)
        
        logger.info("✅ All MOVE trade handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in MOVE trade handler registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_trade_handlers']
