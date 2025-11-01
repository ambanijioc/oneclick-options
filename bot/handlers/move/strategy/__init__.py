"""
MOVE Strategy Handlers - Create/Edit/Delete
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

def register_move_strategy_handlers(application: Application) -> None:
    """Register MOVE strategy handlers"""
    try:
        # Import only what exists
        from bot.handlers.move.strategy.create import (
            move_strategy_setup_callback,
            # Don't import non-existent functions
        )
        
        logger.info("✓ MOVE strategy handlers registered")
        
    except ImportError as e:
        logger.error(f"⚠️  MOVE strategy import: {e}")
    except Exception as e:
        logger.error(f"❌ MOVE strategy handler registration failed: {e}")

__all__ = ['register_move_strategy_handlers']
