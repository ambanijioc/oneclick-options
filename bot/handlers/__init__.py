"""
Bot Handlers Master Initialization - v3.0
Updated: 2025-11-02

Comprehensive handler registration with priority grouping.

Handler Execution Priority:
┌─────────────────────────────────────────┐
│ Group 0: Commands (/start, /help)       │ Highest
├─────────────────────────────────────────┤
│ Group 10-40: Strategy Callbacks         │
│ - Group 10: MOVE Strategy               │
│ - Group 15: MOVE Presets                │
│ - Group 20: MOVE Trading                │
│ - Group 30: Straddle                    │
│ - Group 40: Strangle                    │
├─────────────────────────────────────────┤
│ Group 100: General Callbacks            │ 
│ - API, Balance, Orders, History, etc.   │
├─────────────────────────────────────────┤
│ Group 999: Message Router (catch-all)   │ Lowest
└─────────────────────────────────────────┘
"""

from telegram.ext import Application, MessageHandler, filters
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# Handler configurations with module paths and names
STRATEGY_HANDLERS = [
    {
        "name": "MOVE Strategy",
        "group": 10,
        "module": "bot.handlers.move.strategy",
        "func": "register_move_strategy_handlers",
        "critical": True,
    },
    {
        "name": "MOVE Preset",
        "group": 15,
        "module": "bot.handlers.move.preset",
        "func": "register_move_preset_handlers",
        "critical": False,
    },
    {
        "name": "MOVE Trade",
        "group": 20,
        "module": "bot.handlers.move.trade",
        "funcs": [
            "register_move_manual_trade_handlers",
            "register_move_auto_trade_handlers",
        ],
        "critical": False,
    },
    {
        "name": "Straddle Strategy",
        "group": 30,
        "module": "bot.handlers",
        "func": "straddle_strategy_handler.register_straddle_strategy_handlers",
        "critical": False,
    },
    {
        "name": "Strangle Strategy",
        "group": 40,
        "module": "bot.handlers",
        "func": "strangle_strategy_handler.register_strangle_strategy_handlers",
        "critical": False,
    },
]

GENERAL_HANDLERS = [
    ("API Configuration", "api_handler", "register_api_handlers"),
    ("Balance Queries", "balance_handler", "register_balance_handlers"),
    ("Position Management", "position_handler", "register_position_handlers"),
    ("Order Management", "order_handler", "register_order_handlers"),
    ("Trade History", "trade_history_handler", "register_trade_history_handlers"),
    ("Options List", "options_list_handler", "register_options_list_handlers"),
    ("MOVE List", "move_list_handler", "register_move_list_handlers"),
    ("Manual Presets", "manual_trade_preset_handler", "register_manual_preset_handlers"),
    ("Manual Trade", "manual_trade_handler", "register_manual_trade_handlers"),
    ("Auto Trade", "auto_trade_handler", "register_auto_trade_handlers"),
    ("SL Monitor", "sl_monitor_handler", "register_sl_monitor_handlers"),
    ("Leg Protection", "straddle_leg_protection_handler", "register_leg_protection_handlers"),
]


def register_all_handlers(application: Application):
    """
    Master handler registration orchestrator.
    
    Registers all bot handlers with proper priority grouping and error handling.
    Execution order:
    1. Command handlers (Group 0)
    2. Strategy callbacks (Groups 10-40)
    3. General callbacks (Group 100)
    4. Message router (Group 999)
    """
    
    logger.info("=" * 80)
    logger.info("🚀 MASTER HANDLER REGISTRATION - v3.0 Starting")
    logger.info("=" * 80)
    
    try:
        # Level 0: Commands
        _register_command_handlers(application)
        
        # Level 10-40: Strategy-specific callbacks
        _register_strategy_handlers(application)
        
        # Level 100: General callbacks
        _register_general_handlers(application)
        
        # Level 999: Message router
        _register_message_router(application)
        
        # Final summary
        _log_registration_summary()
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ CRITICAL: Handler registration failed: {e}", exc_info=True)
        logger.error("=" * 80)
        raise


def _register_command_handlers(application: Application) -> None:
    """Register command handlers (Group 0)."""
    
    logger.info("\n📋 Level 0: Command Handlers")
    logger.info("-" * 60)
    
    commands = [
        ("Start", "start_handler", "register_start_handler"),
        ("Help", "help_handler", "register_help_handler"),
    ]
    
    for display_name, module_name, func_name in commands:
        try:
            module = __import__(f".{module_name}", fromlist=[func_name], level=1)
            handler_func = getattr(module, func_name)
            handler_func(application)
            logger.info(f"  ✓ {display_name} handler /{module_name.split('_')[0]}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"  ⚠️ {display_name} handler: {type(e).__name__}")
        except Exception as e:
            logger.error(f"  ❌ {display_name} handler error: {e}", exc_info=True)


def _register_strategy_handlers(application: Application) -> None:
    """Register strategy-specific handlers (Groups 10-40)."""
    
    logger.info("\n📋 Levels 10-40: Strategy Handlers")
    logger.info("-" * 60)
    
    for handler_config in STRATEGY_HANDLERS:
        _register_strategy_handler(application, handler_config)


def _register_strategy_handler(
    application: Application, config: dict
) -> None:
    """
    Register a single strategy handler with error handling.
    
    Args:
        application: Telegram Application instance
        config: Handler configuration dictionary
    """
    
    name = config["name"]
    group = config["group"]
    is_critical = config.get("critical", False)
    
    try:
        logger.info(f"  🔍 {name} (Group {group})...")
        
        # Handle multiple functions in one config
        if "funcs" in config:
            for func_name in config["funcs"]:
                module = __import__(config["module"], fromlist=[func_name])
                handler_func = getattr(module, func_name)
                handler_func(application)
        else:
            # Single function
            module_path = config["module"]
            func_path = config["func"]
            
            if "." in func_path:
                # Nested module path
                sub_module, func_name = func_path.rsplit(".", 1)
                module = __import__(
                    f"{module_path}.{sub_module}",
                    fromlist=[func_name]
                )
            else:
                module = __import__(module_path, fromlist=[func_path])
                func_name = func_path
            
            handler_func = getattr(module, func_name)
            handler_func(application)
        
        logger.info(f"    ✓ {name} registered")
        
    except ImportError as e:
        msg = f"⚠️ {name}: Module not found"
        logger.warning(f"    {msg}")
        if is_critical:
            raise
    except AttributeError as e:
        msg = f"⚠️ {name}: Function not found"
        logger.warning(f"    {msg}")
    except Exception as e:
        msg = f"❌ {name} error: {e}"
        logger.error(f"    {msg}", exc_info=True)
        if is_critical:
            raise


def _register_general_handlers(application: Application) -> None:
    """Register general handlers (Group 100)."""
    
    logger.info("\n📋 Level 100: General Handlers")
    logger.info("-" * 60)
    
    success_count = 0
    
    for display_name, module_name, func_name in GENERAL_HANDLERS:
        try:
            logger.info(f"  🔍 {display_name}...")
            module = __import__(f".{module_name}", fromlist=[func_name], level=1)
            handler_func = getattr(module, func_name)
            handler_func(application)
            logger.info(f"    ✓ {display_name}")
            success_count += 1
        except ImportError as e:
            logger.warning(f"    ⚠️ {display_name}: Module not found")
        except AttributeError as e:
            logger.warning(f"    ⚠️ {display_name}: Function not found")
        except Exception as e:
            logger.error(f"    ❌ {display_name} error: {e}", exc_info=True)
    
    logger.info(f"  → {success_count}/{len(GENERAL_HANDLERS)} handlers registered")


def _register_message_router(application: Application) -> None:
    """Register global message router (Group 999)."""
    
    logger.info("\n📋 Level 999: Message Router (Catch-All)")
    logger.info("-" * 60)
    
    try:
        from .message_router import route_message
        
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                route_message
            ),
            group=999
        )
        
        logger.info("  ✓ Global message router registered")
        logger.info("    └─ Routes state-based text input to handlers")
        
    except ImportError as e:
        logger.error(f"  ❌ Message router import failed: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"  ❌ Message router error: {e}", exc_info=True)
        raise


def _log_registration_summary() -> None:
    """Log handler registration summary."""
    
    logger.info("=" * 80)
    logger.info("✅ ALL HANDLERS REGISTERED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info("\n📊 Handler Execution Priority:")
    logger.info("  ├─ Group 0:   Commands (/start, /help, ...)")
    logger.info("  │")
    logger.info("  ├─ Group 10:  MOVE Strategy (create, view, list)")
    logger.info("  ├─ Group 15:  MOVE Presets (create, edit, delete)")
    logger.info("  ├─ Group 20:  MOVE Trading (manual, auto, execution)")
    logger.info("  ├─ Group 30:  Straddle (strategy callbacks)")
    logger.info("  ├─ Group 40:  Strangle (strategy callbacks)")
    logger.info("  │")
    logger.info("  ├─ Group 100: General Callbacks")
    logger.info("  │  ├─ API Configuration")
    logger.info("  │  ├─ Balance & Positions")
    logger.info("  │  ├─ Orders & History")
    logger.info("  │  ├─ Options & MOVE List")
    logger.info("  │  ├─ Manual & Auto Trading")
    logger.info("  │  └─ SL Monitor & Leg Protection")
    logger.info("  │")
    logger.info("  └─ Group 999: Message Router (catch-all)")
    logger.info("\n💡 How it works:")
    logger.info("  1. User sends message/callback")
    logger.info("  2. Handlers checked by group (lower = higher priority)")
    logger.info("  3. First matching handler processes input")
    logger.info("  4. Group 999 router handles unmatched text via state")
    logger.info("\n" + "=" * 80 + "\n")


__all__ = ['register_all_handlers']
