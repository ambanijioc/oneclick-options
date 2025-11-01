"""
MOVE Strategy Handlers Module
Registers all MOVE strategy callbacks (create, edit, delete, view)
"""

from telegram.ext import Application, CallbackQueryHandler
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_move_strategy_handlers(application: Application) -> None:
    """Register MOVE strategy handlers."""
    
    try:
        # Import actual handler modules
        from bot.handlers.move.strategy.create import handle_move_strategy_create
        from bot.handlers.move.strategy.edit import handle_move_strategy_edit
        from bot.handlers.move.strategy.delete import handle_move_strategy_delete
        from bot.handlers.move.strategy.view import handle_move_strategy_view
        
        # Register callbacks
        application.add_handler(
            CallbackQueryHandler(
                handle_move_strategy_create,
                pattern=r"^move_strategy_create"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_move_strategy_edit,
                pattern=r"^move_strategy_edit_"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_move_strategy_delete,
                pattern=r"^move_strategy_delete_"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_move_strategy_view,
                pattern=r"^move_strategy_view|^move_list"
            )
        )
        
        logger.info("✅ MOVE strategy handlers registered")
        
    except ImportError as e:
        logger.error(f"Import error in MOVE strategy handlers: {e}")
    except Exception as e:
        logger.error(f"Error registering MOVE strategy handlers: {e}")


__all__ = ['register_move_strategy_handlers']
