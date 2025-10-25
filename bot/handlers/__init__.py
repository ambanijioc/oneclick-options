"""
Bot command and callback handlers.
UPDATED: 2025-10-25 10:25 AM IST - REMOVED MOVE_LIST_HANDLER (DELETED)
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
    logger.info("🚀 STARTING HANDLER REGISTRATION - v2.4 REMOVED MOVE_LIST")
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
        
        # ============================================================================
        # MOVE HANDLERS - NESTED STRUCTURE
        # ============================================================================
        
        # ✅ MOVE STRATEGY HANDLERS (bot/handlers/move/strategy/)
        try:
            logger.info("🔍 Registering MOVE strategy handlers...")
            from bot.handlers.move.strategy import register_move_strategy_handlers
            register_move_strategy_handlers(application)
            logger.info("✅ MOVE strategy handlers registered")
        except ImportError as e:
            logger.error(f"❌ ImportError in MOVE strategy handler: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE strategy handlers: {e}", exc_info=True)

        # ✅ REMOVED: move_list_handler (file deleted)
        
        # ✅ MOVE TRADE HANDLERS (bot/handlers/move/trade/)
        try:
            logger.info("🔍 Registering MOVE trade handlers (NESTED)...")
            from bot.handlers.move.trade.manual import register_move_manual_trade_handlers
            register_move_manual_trade_handlers(application)
            logger.info("✅ MOVE manual trade handlers registered")
        except ImportError as e:
            logger.error(f"❌ Move manual trade handler import failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE manual trade handlers: {e}", exc_info=True)
        
        try:
            logger.info("🔍 Registering MOVE auto trade handlers (NESTED)...")
            from bot.handlers.move.trade.auto import register_move_auto_trade_handlers
            register_move_auto_trade_handlers(application)
            logger.info("✅ MOVE auto trade handlers registered")
        except ImportError as e:
            logger.error(f"❌ Move auto trade handler import failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE auto trade handlers: {e}", exc_info=True)
        
        # ✅ MOVE PRESET HANDLERS (bot/handlers/move/preset/)
        try:
            logger.info("🔍 Registering MOVE preset handlers (NESTED)...")
            from bot.handlers.move.preset import register_move_preset_handlers
            register_move_preset_handlers(application)
            logger.info("✅ MOVE preset handlers registered")
        except ImportError as e:
            logger.warning(f"Move preset handler not found (new nested path): {e}")
        except Exception as e:
            logger.error(f"❌ Error registering MOVE preset handlers: {e}", exc_info=True)
        
        # ============================================================================
        # MANUAL TRADE HANDLERS
        # ============================================================================
        
        # Manual trade preset handlers
        try:
            from .manual_trade_preset_handler import register_manual_preset_handlers
            register_manual_preset_handlers(application)
            logger.info("✓ Manual trade preset handlers registered")
        except ImportError as e:
            logger.warning(f"Manual trade preset handler not found: {e}")
        
        # Manual trade handlers
        try:
            from .manual_trade_handler import register_manual_trade_handlers
            register_manual_trade_handlers(application)
            logger.info("✓ Manual trade handlers registered")
        except ImportError as e:
            logger.warning(f"Manual trade handler not found: {e}")
        
        # ============================================================================
        # AUTO TRADE HANDLERS
        # ============================================================================
        
        # Auto trade handlers
        try:
            from .auto_trade_handler import register_auto_trade_handlers
            register_auto_trade_handlers(application)
            logger.info("✓ Auto trade handlers registered")
        except ImportError as e:
            logger.warning(f"Auto trade handler not found: {e}")

        # ============================================================================
        # SL MONITOR HANDLERS
        # ============================================================================
        
        try:
            logger.info("🔍 Importing sl_monitor_handler module...")
            from .sl_monitor_handler import register_sl_monitor_handlers
            register_sl_monitor_handlers(application)
            logger.info("✅ SL monitor handlers registered")
        except ImportError as e:
            logger.warning(f"SL monitor handler not found: {e}")
        except Exception as e:
            logger.error(f"Error registering SL monitor handlers: {e}", exc_info=True)
        
        # ============================================================================
        # LEG PROTECTION HANDLERS
        # ============================================================================
        
        try:
            logger.info("-" * 60)
            logger.info("ATTEMPTING TO REGISTER LEG PROTECTION HANDLERS")
            logger.info("-" * 60)
        
            from .straddle_leg_protection_handler import register_leg_protection_handlers
        
            register_leg_protection_handlers(application)
        
            logger.info("-" * 60)
            logger.info("✅ LEG PROTECTION HANDLERS REGISTERED SUCCESSFULLY")
            logger.info("-" * 60)
        
        except ImportError as e:
            logger.warning(f"Leg protection handler not found: {e}")
        except Exception as e:
            logger.error(f"Error registering leg protection handlers: {e}", exc_info=True)
        
        # ============================================================================
        # MESSAGE ROUTER (LOWEST PRIORITY)
        # ============================================================================
        
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
        logger.info("✅ All available handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}", exc_info=True)
        raise


__all__ = ['register_all_handlers']
        
