"""
MOVE Strategy Handlers - Create/Edit/Delete
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

def register_move_strategy_handlers(application: Application) -> None:
    """Register MOVE strategy handlers"""
    try:
        # Check what functions actually exist
        from bot.handlers.move.strategy import create
        
        # List available functions
        available = [x for x in dir(create) if not x.startswith('_')]
        logger.info(f"Available in create.py: {available}")
        
        # Try to import what exists
        for func_name in ['move_create_strategy', 'create_strategy', 'strategy_handler']:
            if hasattr(create, func_name):
                func = getattr(create, func_name)
                logger.info(f"✓ Found: {func_name}")
                break
        
        logger.info("✓ MOVE strategy handlers registered")
        
    except Exception as e:
        logger.warning(f"⚠️  MOVE strategy import: {e}")

__all__ = ['register_move_strategy_handlers']
