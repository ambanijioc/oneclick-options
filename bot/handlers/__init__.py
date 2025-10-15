"""
Bot command and callback handlers.
"""

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
        
        # Import command handlers
        from .start_handler import register_start_handler
        from .help_handler import register_help_handler
        
        # Register command handlers FIRST (highest priority)
        register_start_handler(application)
        logger.info("✓ Start handler registered")
        
        register_help_handler(application)
        logger.info("✓ Help handler registered")
        
        # Register callback query handlers
        try:
            from .api_handler import register_api_handlers
            register_api_handlers(application)
        except ImportError as e:
            logger.warning(f"API handler not found: {e}")
        
        try:
            from .balance_handler import register_balance_handlers
            register_balance_handlers(application)
        except ImportError as e:
            logger.warning(f"Balance handler not found: {e}")
        
        try:
            from .position_handler import register_position_handlers
            register_position_handlers(application)
        except ImportError as e:
            logger.warning(f"Position handler not found: {e}")
        
        try:
            from .order_handler import register_order_handlers
            register_order_handlers(application)
        except ImportError as e:
            logger.warning(f"Order handler not found: {e}")
        
        try:
            from .trade_history_handler import register_trade_history_handlers
            register_trade_history_handlers(application)
        except ImportError as e:
            logger.warning(f"Trade history handler not found: {e}")
        
        try:
            from .options_list_handler import register_options_list_handlers
            register_options_list_handlers(application)
        except ImportError as e:
            logger.warning(f"Options list handler not found: {e}")
        
        try:
            from .strategy_handler import register_strategy_handlers
            register_strategy_handlers(application)
        except ImportError as e:
            logger.warning(f"Strategy handler not found: {e}")

        try:
            from .move_strategy_handler import register_move_strategy_handlers
            register_move_strategy_handlers(application)
        except ImportError as e:
            logger.warning(f"Move strategy handler not found: {e}")
        
        try:
            from .manual_trade_handler import register_manual_trade_handlers
            register_manual_trade_handlers(application)
        except ImportError as e:
            logger.warning(f"Manual trade handler not found: {e}")
        
        try:
            from .auto_trade_handler import register_auto_trade_handlers
            register_auto_trade_handlers(application)
        except ImportError as e:
            logger.warning(f"Auto trade handler not found: {e}")

        # Add after existing imports
        try:
            from .move_strategy_handler import register_move_strategy_handlers
            register_move_strategy_handlers(application)
        except ImportError as e:
            logger.warning(f"Move strategy handler not found: {e}")

        try:
            from .move_list_handler import register_move_list_handlers
            register_move_list_handlers(application)
        except ImportError as e:
            logger.warning(f"Move list handler not found: {e}")

        try:
            from .move_manual_trade_handler import register_move_manual_trade_handlers
            register_move_manual_trade_handlers(application)
        except ImportError as e:
            logger.warning(f"Move manual trade handler not found: {e}")

        try:
            from .move_auto_trade_handler import register_move_auto_trade_handlers
            register_move_auto_trade_handlers(application)
        except ImportError as e:
            logger.warning(f"Move auto trade handler not found: {e}")
     
        # Register message router LAST (lowest priority)
        # This catches all text messages and routes based on conversation state
        from .message_router import route_message
        
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                route_message
            ),
            group=999  # Use high group number to ensure it runs last
        )
        logger.info("✓ Message router registered")
        
        logger.info("✓ All available handlers registered successfully")
    
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}", exc_info=True)
        raise


__all__ = ['register_all_handlers']
