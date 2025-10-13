"""
Bot command and callback handlers.
"""

from telegram.ext import Application

from .start_handler import register_start_handler
from .api_handler import register_api_handlers
from .balance_handler import register_balance_handlers
from .position_handler import register_position_handlers
from .order_handler import register_order_handlers
from .trade_history_handler import register_trade_history_handlers
from .options_list_handler import register_options_list_handlers
from .strategy_handler import register_strategy_handlers
from .manual_trade_handler import register_manual_trade_handlers
from .auto_trade_handler import register_auto_trade_handlers
from .help_handler import register_help_handler

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_all_handlers(application: Application):
    """
    Register all bot handlers.
    
    Args:
        application: Bot application instance
    """
    try:
        logger.info("Registering all handlers...")
        
        # Register handlers in order of priority
        register_start_handler(application)
        register_api_handlers(application)
        register_balance_handlers(application)
        register_position_handlers(application)
        register_order_handlers(application)
        register_trade_history_handlers(application)
        register_options_list_handlers(application)
        register_strategy_handlers(application)
        register_manual_trade_handlers(application)
        register_auto_trade_handlers(application)
        register_help_handler(application)
        
        logger.info("✓ All handlers registered successfully")
    
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}", exc_info=True)
        raise


__all__ = [
    'register_all_handlers',
    'register_start_handler',
    'register_api_handlers',
    'register_balance_handlers',
    'register_position_handlers',
    'register_order_handlers',
    'register_trade_history_handlers',
    'register_options_list_handlers',
    'register_strategy_handlers',
    'register_manual_trade_handlers',
    'register_auto_trade_handlers',
    'register_help_handler'
]
