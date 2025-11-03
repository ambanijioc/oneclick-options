"""
MOVE Preset Handlers Module

Registers MOVE preset handlers (menu + navigation only).
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application):
    """Register MOVE preset handlers"""
    logger.info("🔍 Registering MOVE preset handlers...")
    
    try:
        # Import and register menu handlers
        from .menu import register_menu_handlers
        
        success = register_menu_handlers(application)
        
        if success:
            logger.info("✅ MOVE preset handlers registered successfully")
        else:
            logger.error("❌ Failed to register MOVE preset handlers")
        
        return success
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"❌ Error registering MOVE preset handlers: {e}", exc_info=True)
        return False


__all__ = ['register_move_preset_handlers']
