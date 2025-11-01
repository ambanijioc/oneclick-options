"""
Bot command and callback handlers.
UPDATED: 2025-11-01 - Handler priority groups to avoid conflicts
"""

from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_all_handlers(application: Application):
    """
    Register all bot handlers with proper priority grouping.
    
    Handler Groups (execution order):
    - Group 0 (default): Commands
    - Group 10-50: Specific strategy callbacks (MOVE, Straddle, Strangle)
    - Group 100: General callbacks (API, Balance, etc.)
    - Group 999: Message router (lowest priority - catch-all)
    """
    logger.info("🚀 STARTING HANDLER REGISTRATION - v2.5 with Priority Groups")
    try:
        # ==================== LEVEL 0: COMMANDS ====================
        logger.info("Registering command handlers...")
        
        from .start_handler import register_start_handler
        from .help_handler import register_help_handler
        
        register_start_handler(application)
        logger.info("✓ Start handler registered (Group 0)")
        
        register_help_handler(application)
        logger.info("✓ Help handler registered (Group 0)")
        
        # ==================== LEVEL 10-50: SPECIFIC CALLBACKS ====================
        
        # ✅ MOVE STRATEGY HANDLERS (Group 10)
        try:
            logger.info("🔍 Registering MOVE strategy handlers (Group 10)...")
            from bot.handlers.move.strategy import register_move_strategy_handlers
            register_move_strategy_handlers(application)
            logger.info("✅ MOVE strategy handlers registered (Group 10)")
        except ImportError as e:
            logger.error(f"❌ ImportError in MOVE strategy handler: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE strategy handlers: {e}", exc_info=True)

        # ✅ MOVE PRESET HANDLERS (Group 15)
        try:
            logger.info("🔍 Registering MOVE preset handlers (Group 15)...")
            from bot.handlers.move.preset import register_move_preset_handlers
            register_move_preset_handlers(application)
            logger.info("✅ MOVE preset handlers registered (Group 15)")
        except ImportError as e:
            logger.warning(f"⚠️ Move preset handler: {e}")
        except Exception as e:
            logger.error(f"❌ Error registering MOVE preset handlers: {e}", exc_info=True)
        
        # ✅ MOVE TRADE HANDLERS (Group 20)
        try:
            logger.info("🔍 Registering MOVE trade handlers (Group 20)...")
            from bot.handlers.move.trade import (
                register_move_manual_trade_handlers,
                register_move_auto_trade_handlers
            )
            register_move_manual_trade_handlers(application)
            register_move_auto_trade_handlers(application)
            logger.info("✅ MOVE trade handlers registered (Group 20)")
        except ImportError as e:
            logger.error(f"❌ Move trade handler import failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error registering MOVE trade handlers: {e}", exc_info=True)
        
        # Straddle Strategy (Group 30)
        try:
            logger.info("🔍 Registering Straddle strategy handlers (Group 30)...")
            from .straddle_strategy_handler import register_straddle_strategy_handlers
            register_straddle_strategy_handlers(application)
            logger.info("✓ Straddle strategy handlers registered (Group 30)")
        except ImportError as e:
            logger.warning(f"Straddle handler: {e}")
        except Exception as e:
            logger.error(f"Error registering Straddle: {e}", exc_info=True)
        
        # Strangle Strategy (Group 40)
        try:
            logger.info("🔍 Registering Strangle strategy handlers (Group 40)...")
            from .strangle_strategy_handler import register_strangle_strategy_handlers
            register_strangle_strategy_handlers(application)
            logger.info("✓ Strangle strategy handlers registered (Group 40)")
        except ImportError as e:
            logger.warning(f"Strangle handler: {e}")
        except Exception as e:
            logger.error(f"Error registering Strangle: {e}", exc_info=True)
        
        # ==================== LEVEL 100: GENERAL CALLBACKS ====================
        logger.info("🔍 Registering general handlers (Group 100)...")
        
        # API handlers
        try:
            from .api_handler import register_api_handlers
            register_api_handlers(application)
            logger.info("✓ API handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"API handler: {e}")
        except Exception as e:
            logger.error(f"Error in API handlers: {e}", exc_info=True)
        
        # Balance handlers
        try:
            from .balance_handler import register_balance_handlers
            register_balance_handlers(application)
            logger.info("✓ Balance handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Balance handler: {e}")
        except Exception as e:
            logger.error(f"Error in Balance: {e}", exc_info=True)
        
        # Position handlers
        try:
            from .position_handler import register_position_handlers
            register_position_handlers(application)
            logger.info("✓ Position handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Position handler: {e}")
        except Exception as e:
            logger.error(f"Error in Position: {e}", exc_info=True)
        
        # Order handlers
        try:
            from .order_handler import register_order_handlers
            register_order_handlers(application)
            logger.info("✓ Order handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Order handler: {e}")
        except Exception as e:
            logger.error(f"Error in Order: {e}", exc_info=True)
        
        # Trade history handlers
        try:
            from .trade_history_handler import register_trade_history_handlers
            register_trade_history_handlers(application)
            logger.info("✓ Trade history handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Trade history handler: {e}")
        except Exception as e:
            logger.error(f"Error in Trade history: {e}", exc_info=True)
        
        # Options list handlers
        try:
            from .options_list_handler import register_options_list_handlers
            register_options_list_handlers(application)
            logger.info("✓ Options list handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Options list handler: {e}")
        except Exception as e:
            logger.error(f"Error in Options list: {e}", exc_info=True)

        # Move list handlers
        try:
            from .move_list_handler import register_move_list_handlers
            register_move_list_handlers(application)
            logger.info("✓ Move list handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Move list handler: {e}")
        except Exception as e:
            logger.error(f"Error in Move list: {e}", exc_info=True)
        
        # Manual trade preset handlers
        try:
            from .manual_trade_preset_handler import register_manual_preset_handlers
            register_manual_preset_handlers(application)
            logger.info("✓ Manual trade preset handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Manual preset handler: {e}")
        except Exception as e:
            logger.error(f"Error in Manual preset: {e}", exc_info=True)
        
        # Manual trade handlers
        try:
            from .manual_trade_handler import register_manual_trade_handlers
            register_manual_trade_handlers(application)
            logger.info("✓ Manual trade handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Manual trade handler: {e}")
        except Exception as e:
            logger.error(f"Error in Manual trade: {e}", exc_info=True)
        
        # Auto trade handlers
        try:
            from .auto_trade_handler import register_auto_trade_handlers
            register_auto_trade_handlers(application)
            logger.info("✓ Auto trade handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"Auto trade handler: {e}")
        except Exception as e:
            logger.error(f"Error in Auto trade: {e}", exc_info=True)

        # SL monitor handlers
        try:
            logger.info("🔍 Registering SL monitor handlers (Group 100)...")
            from .sl_monitor_handler import register_sl_monitor_handlers
            register_sl_monitor_handlers(application)
            logger.info("✅ SL monitor handlers registered (Group 100)")
        except ImportError as e:
            logger.warning(f"SL monitor handler: {e}")
        except Exception as e:
            logger.error(f"Error in SL monitor: {e}", exc_info=True)
        
        # Leg protection handlers
        try:
            logger.info("-" * 60)
            logger.info("REGISTERING LEG PROTECTION HANDLERS (Group 100)")
            logger.info("-" * 60)
            from .straddle_leg_protection_handler import register_leg_protection_handlers
            register_leg_protection_handlers(application)
            logger.info("-" * 60)
            logger.info("✅ LEG PROTECTION HANDLERS REGISTERED SUCCESSFULLY")
            logger.info("-" * 60)
        except ImportError as e:
            logger.warning(f"Leg protection handler: {e}")
        except Exception as e:
            logger.error(f"Error in Leg protection: {e}", exc_info=True)
        
        # ==================== LEVEL 999: MESSAGE ROUTER ====================
        logger.info("📝 Registering message router (Group 999 - Lowest priority)...")
        
        from .message_router import route_message
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                route_message
            ),
            group=999  # ✅ LOWEST priority - catches unhandled messages only
        )
        
        logger.info("✓ Message router registered (Group 999)")
        logger.info("✅ ALL HANDLERS REGISTERED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("Handler Priority Order:")
        logger.info("  Group 0:   Commands (/start, /help)")
        logger.info("  Group 10:  MOVE Strategy callbacks")
        logger.info("  Group 15:  MOVE Preset callbacks")
        logger.info("  Group 20:  MOVE Trade callbacks")
        logger.info("  Group 30:  Straddle callbacks")
        logger.info("  Group 40:  Strangle callbacks")
        logger.info("  Group 100: General callbacks (API, Balance, etc.)")
        logger.info("  Group 999: Message router (catch-all)")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to register handlers: {e}", exc_info=True)
        raise


__all__ = ['register_all_handlers']
