"""
MOVE Preset Handlers Module
Registers all MOVE preset callbacks (create, edit, delete)
"""

from telegram.ext import Application, CallbackQueryHandler
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_preset_handlers(application: Application) -> None:
    """Register MOVE preset handlers."""
    
    try:
        from bot.handlers.move.preset.create import handle_move_preset_create
        from bot.handlers.move.preset.edit import handle_move_preset_edit
        from bot.handlers.move.preset.delete import handle_move_preset_delete
        
        application.add_handler(
            CallbackQueryHandler(
                handle_move_preset_create,
                pattern=r"^move_preset_create|^move_preset_add"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_move_preset_edit,
                pattern=r"^move_preset_edit_"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_move_preset_delete,
                pattern=r"^move_preset_delete_"
            )
        )
        
        logger.info("✅ MOVE preset handlers registered")
        
    except ImportError as e:
        logger.error(f"Import error in MOVE preset handlers: {e}")
    except Exception as e:
        logger.error(f"Error registering MOVE preset handlers: {e}")


__all__ = ['register_move_preset_handlers']
