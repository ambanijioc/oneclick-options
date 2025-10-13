"""
Bot command and callback handlers.
"""

from .message_router import route_message
from telegram.ext import Application, MessageHandler, filters
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
        
        # Import handlers
        from .start_handler import register_start_handler
        from .help_handler import register_help_handler
        from .message_router import route_message
        
        # Register command handlers first (highest priority)
        register_start_handler(application)
        register_help_handler(application)
        
        # Register callback handlers
        try:
            from .api_handler import register_api_handlers
            register_api_handlers(application)
        except ImportError:
            logger.warning("API handler not found, skipping")
        
        try:
            from .balance_handler import register_balance_handlers
            register_balance_handlers(application)
        except ImportError:
            logger.warning("Balance handler not found, skipping")
        
        try:
            from .position_handler import register_position_handlers
            register_position_handlers(application)
        except ImportError:
            logger.warning("Position handler not found, skipping")
        
        try:
            from .order_handler import register_order_handlers
            register_order_handlers(application)
        except ImportError:
            logger.warning("Order handler not found, skipping")
        
        try:
            from .trade_history_handler import register_trade_history_handlers
            register_trade_history_handlers(application)
        except ImportError:
            logger.warning("Trade history handler not found, skipping")
        
        try:
            from .options_list_handler import register_options_list_handlers
            register_options_list_handlers(application)
        except ImportError:
            logger.warning("Options list handler not found, skipping")
        
        try:
            from .strategy_handler import register_strategy_handlers
            register_strategy_handlers(application)
        except ImportError:
            logger.warning("Strategy handler not found, skipping")
        
        try:
            from .manual_trade_handler import register_manual_trade_handlers
            register_manual_trade_handlers(application)
        except ImportError:
            logger.warning("Manual trade handler not found, skipping")
        
        try:
            from .auto_trade_handler import register_auto_trade_handlers
            register_auto_trade_handlers(application)
        except ImportError:
            logger.warning("Auto trade handler not found, skipping")
        
        # Register message router LAST (lowest priority, catches all text)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            route_message
        ))
        logger.info("Message router registered")
        
        logger.info("✓ All available handlers registered successfully")
    
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}", exc_info=True)
        raise


__all__ = ['register_all_handlers']
