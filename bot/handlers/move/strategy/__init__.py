"""
MOVE Strategy handlers initialization and registration.
"""

from telegram.ext import Application, CallbackQueryHandler
from bot.handlers.move.strategy.create import (
    move_add_callback,
    move_skip_description_callback,
    move_asset_callback,
    move_expiry_callback,
    move_direction_callback,
    move_confirm_save_callback,
    move_skip_target_callback,
    move_cancel_callback
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

def register_move_strategy_handlers(application: Application):
    """Register all MOVE strategy handlers."""
    
    # Main menu button - "🎯 Move Strategy"
    application.add_handler(CallbackQueryHandler(
        move_add_callback,
        pattern="^move_menu$"  # ✅ THIS WAS MISSING!
    ))
    
    # Description skip
    application.add_handler(CallbackQueryHandler(
        move_skip_description_callback,
        pattern="^move_skip_description$"
    ))
    
    # Asset selection
    application.add_handler(CallbackQueryHandler(
        move_asset_callback,
        pattern="^move_asset_(btc|eth)$"
    ))
    
    # Expiry selection
    application.add_handler(CallbackQueryHandler(
        move_expiry_callback,
        pattern="^move_expiry_(daily|weekly)$"
    ))
    
    # Direction selection
    application.add_handler(CallbackQueryHandler(
        move_direction_callback,
        pattern="^move_direction_(long|short)$"
    ))
    
    # Confirm & Save
    application.add_handler(CallbackQueryHandler(
        move_confirm_save_callback,
        pattern="^move_confirm_save$"
    ))
    
    # Skip Target
    application.add_handler(CallbackQueryHandler(
        move_skip_target_callback,
        pattern="^move_skip_target$"
    ))
    
    # Cancel
    application.add_handler(CallbackQueryHandler(
        move_cancel_callback,
        pattern="^move_cancel$"
    ))
    
    logger.info("✅ MOVE strategy handlers registered")

__all__ = ['register_move_strategy_handlers']
