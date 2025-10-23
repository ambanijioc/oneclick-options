"""
Bot command and callback handlers.
UPDATED: 2025-10-24 01:00 AM IST
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
    logger.info("🚀 STARTING HANDLER REGISTRATION - v2.1")
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
            logger.info("✓ API handlers registered")
        except ImportError as e:
            logger.warning(f"API handler not found: {e}")
        
        try:
            from .balance_handler import register_balance_handlers
            register_balance_handlers(application)
            logger.info("✓ Balance handlers registered")
        except ImportError as e:
            logger.warning(f"Balance handler not found: {e}")
        
        try:
            from .position_handler import register_position_handlers
            register_position_handlers(application)
            logger.info("✓ Position handlers registered")
        except ImportError as e:
            logger.warning(f"Position handler not found: {e}")
        
        try:
            from .order_handler import register_order_handlers
            register_order_handlers(application)
            logger.info("✓ Order handlers registered")
        except ImportError as e:
            logger.warning(f"Order handler not found: {e}")
        
        try:
            from .trade_history_handler import register_trade_history_handlers
            register_trade_history_handlers(application)
            logger.info("✓ Trade history handlers registered")
        except ImportError as e:
            logger.warning(f"Trade history handler not found: {e}")
        
        try:
            from .options_list_handler import register_options_list_handlers
            register_options_list_handlers(application)
            logger.info("✓ Options list handlers registered")
        except ImportError as e:
            logger.warning(f"Options list handler not found: {e}")
        
        # Strategy handlers
        try:
            from .straddle_strategy_handler import register_straddle_strategy_handlers
            register_straddle_strategy_handlers(application)
            logger.info("✓ Straddle strategy handlers registered")
        except ImportError as e:
            logger.warning(f"Straddle strategy handler not found: {e}")
        
        try:
            from .strangle_strategy_handler import register_strangle_strategy_handlers
            register_strangle_strategy_handlers(application)
            logger.info("✓ Strangle strategy handlers registered")
        except ImportError as e:
            logger.warning(f"Strangle strategy handler not found: {e}")
        
        # ✅ MOVE STRATEGY HANDLERS
        try:
            logger.info("🔍 Attempting to import MOVE strategy handlers...")
            from bot.handlers.move.strategy import register_move_strategy_handlers
            logger.info("🔍 Import successful, registering handlers...")
            register_move_strategy_handlers(application)
            logger.info("✓ MOVE strategy handlers registered")
        except ImportError as e:
            logger.error(f"❌ ImportError in MOVE handler: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE handlers: {e}", exc_info=True)

        try:
            from .move_list_handler import register_move_list_handlers
            register_move_list_handlers(application)
            logger.info("✓ MOVE list handlers registered")
        except ImportError as e:
            logger.warning(f"Move list handler not found: {e}")
        
        # ✅ MOVE TRADE PRESET HANDLERS
        try:
            from .move_trade_preset_handler import register_move_trade_preset_handlers
            register_move_trade_preset_handlers(application)
            logger.info("✓ MOVE trade preset handlers registered")
        except ImportError as e:
            logger.warning(f"Move trade preset handler not found: {e}")
        
        # Manual trade handlers
        try:
            from .manual_trade_preset_handler import register_manual_preset_handlers
            register_manual_preset_handlers(application)
            logger.info("✓ Manual trade preset handlers registered")
        except ImportError as e:
            logger.warning(f"Manual trade preset handler not found: {e}")
        
        try:
            from .manual_trade_handler import register_manual_trade_handlers
            register_manual_trade_handlers(application)
            logger.info("✓ Manual trade handlers registered")
        except ImportError as e:
            logger.warning(f"Manual trade handler not found: {e}")
        
        # Auto trade handlers
        try:
            from .auto_trade_handler import register_auto_trade_handlers
            register_auto_trade_handlers(application)
            logger.info("✓ Auto trade handlers registered")
        except ImportError as e:
            logger.warning(f"Auto trade handler not found: {e}")
        
        # MOVE trade execution handlers
        try:
            from .move_manual_trade_handler import register_move_manual_trade_handlers
            register_move_manual_trade_handlers(application)
            logger.info("✓ MOVE manual trade handlers registered")
        except ImportError as e:
            logger.warning(f"Move manual trade handler not found: {e}")
        
        try:
            from .move_auto_trade_handler import register_move_auto_trade_handlers
            register_move_auto_trade_handlers(application)
            logger.info("✓ MOVE auto trade handlers registered")
        except ImportError as e:
            logger.warning(f"Move auto trade handler not found: {e}")

        # ✅✅✅ SL MONITOR HANDLERS - ENHANCED ERROR LOGGING ✅✅✅
        logger.info("=" * 60)
        logger.info("🔍 ATTEMPTING TO REGISTER SL MONITOR HANDLERS")
        logger.info("=" * 60)
        try:
            logger.info("Step 1: Importing sl_monitor_handler module...")
            from .sl_monitor_handler import register_sl_monitor_handlers
            logger.info("✅ Step 1 SUCCESS: Module imported")
            
            logger.info("Step 2: Calling register_sl_monitor_handlers()...")
            register_sl_monitor_handlers(application)
            logger.info("✅ Step 2 SUCCESS: Function called")
            
            logger.info("=" * 60)
            logger.info("✓✓✓ SL MONITOR HANDLERS REGISTERED SUCCESSFULLY ✓✓✓")
            logger.info("=" * 60)
            
        except ImportError as e:
            logger.error("=" * 60)
            logger.error("❌❌❌ IMPORT ERROR - SL MONITOR FILE NOT FOUND ❌❌❌")
            logger.error("=" * 60)
            logger.error(f"Error: {e}")
            logger.error("File should be at: bot/handlers/sl_monitor_handler.py")
            logger.error("Full traceback:", exc_info=True)
            logger.error("=" * 60)
            
        except AttributeError as e:
            logger.error("=" * 60)
            logger.error("❌❌❌ ATTRIBUTE ERROR - FUNCTION NOT FOUND ❌❌❌")
            logger.error("=" * 60)
            logger.error(f"Error: {e}")
            logger.error("The file exists but register_sl_monitor_handlers function is missing")
            logger.error("Full traceback:", exc_info=True)
            logger.error("=" * 60)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("❌❌❌ UNEXPECTED ERROR ❌❌❌")
            logger.error("=" * 60)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {e}")
            logger.error("Full traceback:", exc_info=True)
            logger.error("=" * 60)
        
        # Register message router LAST (lowest priority)
        from .message_router import route_message
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                route_message
            ),
            group=999
        )
        
        logger.info("✓ Message router registered")
        logger.info("✓ All available handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}", exc_info=True)
        raise


__all__ = ['register_all_handlers']
