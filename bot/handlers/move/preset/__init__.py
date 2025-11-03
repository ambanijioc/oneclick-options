"""MOVE Preset Handler Submodule - Modular Architecture"""

from telegram.ext import Application, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application):
    """
    Register ALL MOVE preset handlers - Modular approach.
    
    Splits handlers into:
    - create.py: Add preset flow
    - view.py: View presets
    - edit.py: Edit presets
    - delete.py: Delete presets
    - menu.py: Main menu & navigation
    """
    
    logger.info("🎯 Initializing MOVE Preset Handlers (Modular)...")
    
    try:
        # 1. Register callback handlers (Group 15)
        from bot.handlers.move.preset.menu import register_menu_handlers
        from bot.handlers.move.preset.create import register_create_handlers
        from bot.handlers.move.preset.view import register_view_handlers
        from bot.handlers.move.preset.edit import register_edit_handlers
        from bot.handlers.move.preset.delete import register_delete_handlers
        
        register_menu_handlers(application)
        register_create_handlers(application)
        register_view_handlers(application)
        register_edit_handlers(application)
        register_delete_handlers(application)
        
        logger.info("✓ All preset callback handlers registered (Group 15)")
        
        # 2. Register text input message handler (Group 11)
        # This should be added in your main bot initialization
        # See instruction below
        
        logger.info("✅ MOVE preset handlers initialized successfully (MODULAR)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing MOVE preset handlers: {e}", exc_info=True)
        return False


__all__ = ['register_move_preset_handlers']
