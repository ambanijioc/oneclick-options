"""MOVE Trade Handler Submodule - Manual & Auto"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_trade_handlers(application: Application):
    """Register all MOVE trade handlers"""
    
    # ✅ Import and register manual trade handlers
    from bot.handlers.move.trade.manual import register_move_manual_trade_handlers
    register_move_manual_trade_handlers(application)
    
    logger.info("✅ MOVE Trade handlers registered")


__all__ = ['register_move_trade_handlers']
