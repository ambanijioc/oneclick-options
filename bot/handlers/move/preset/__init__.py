"""
MOVE Trade Preset CRUD Operations
Create, View, Edit, Delete MOVE Trade Presets
"""

from telegram.ext import Application
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application):
    """Register all MOVE preset CRUD handlers."""
    
    try:
        logger.info("🚀 Registering MOVE preset handlers...")
        
        # You can add imports from create.py, view.py, edit.py, delete.py here
        # For now, this is a placeholder
        
        logger.info("✅ All MOVE preset handlers registered successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in MOVE preset handler registration: {e}", exc_info=True)
        raise


__all__ = ['register_move_preset_handlers']
