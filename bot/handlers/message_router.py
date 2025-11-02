"""
✅ COMPREHENSIVE MESSAGE ROUTER
Global message router for directing ALL text input based on user state.

Handles:
- API Configuration
- MOVE Strategy (Create, Edit, Trade)
- STRADDLE Strategy
- STRANGLE Strategy
- Manual/Auto Presets and Trades

Key Features:
- Single entry point for all text messages
- State-based routing
- Comprehensive error handling
- Detailed logging
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager
from bot.utils.error_handler import error_handler

logger = setup_logger(__name__)


@error_handler
async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ GLOBAL MESSAGE ROUTER
    
    Routes ALL text messages to appropriate handler based on user's state.
    This is the ONLY MessageHandler for the entire bot.
    """
    
    try:
        logger.info("=" * 80)
        logger.info("🌍 GLOBAL MESSAGE ROUTER CALLED")
        logger.info("=" * 80)
        
        # Validate message
        if not update.message or not update.message.text:
            logger.warning("❌ No message or text in update")
            return
        
        user = update.effective_user
        text = update.message.text.strip()
        
        logger.info(f"👤 User {user.id} ({user.first_name}) sent: '{text[:50]}'")
        
        # Skip commands
        if text.startswith('/'):
            logger.info(f"⏭️ Skipping command: {text}")
            return
        
        # Get current state
        state_str = await state_manager.get_state(user.id)
        logger.info(f"📍 Current state: {state_str}")
        
        # If no state, send helpful message
        if state_str is None:
            logger.warning(f"❌ No active state for user {user.id}")
            await update.message.reply_text(
                "ℹ️ Please use /start to begin.",
                parse_mode='HTML'
            )
            return
        
        logger.info(f"🎯 Routing to handler for state: {state_str}")
        
        # ==================== API CONFIGURATION STATES ====================
        if state_str == 'api_add_name':
            from bot.handlers.api_handler import handle_api_name_input
            await handle_api_name_input(update, context)
            
        elif state_str == 'api_add_description':
            from bot.handlers.api_handler import handle_api_description_input
            await handle_api_description_input(update, context)
            
        elif state_str == 'api_add_key':
            from bot.handlers.api_handler import handle_api_key_input
            await handle_api_key_input(update, context)
            
        elif state_str == 'api_add_secret':
            from bot.handlers.api_handler import handle_api_secret_input
            await handle_api_secret_input(update, context)
        
        # ==================== MOVE STRATEGY CREATION ====================
        elif state_str == 'move_add_name':
            from bot.handlers.move.strategy.create import handle_move_add_name_input
            await handle_move_add_name_input(update, context)
            logger.info("✅ Routed to: handle_move_add_name_input")

        elif state_str == 'move_add_description':
            from bot.handlers.move.strategy.create import handle_move_description_input
            await handle_move_description_input(update, context)
            logger.info("✅ Routed to: handle_move_description_input")

        elif state_str == 'move_add_lot_size':
            from bot.handlers.move.strategy.create import handle_move_lot_size_input
            await handle_move_lot_size_input(update, context)
            logger.info("✅ Routed to: handle_move_lot_size_input")

        elif state_str == 'move_add_atm_offset':
            from bot.handlers.move.strategy.create import handle_move_atm_offset_input
            await handle_move_atm_offset_input(update, context)
            logger.info("✅ Routed to: handle_move_atm_offset_input")

        elif state_str == 'move_add_sl_trigger':
            from bot.handlers.move.strategy.create import handle_move_sl_trigger_input
            await handle_move_sl_trigger_input(update, context)
            logger.info("✅ Routed to: handle_move_sl_trigger_input")

        elif state_str == 'move_add_sl_limit':
            from bot.handlers.move.strategy.create import handle_move_sl_limit_input
            await handle_move_sl_limit_input(update, context)
            logger.info("✅ Routed to: handle_move_sl_limit_input")

        elif state_str == 'move_add_target_trigger':
            from bot.handlers.move.strategy.create import handle_move_target_trigger_input
            await handle_move_target_trigger_input(update, context)
            logger.info("✅ Routed to: handle_move_target_trigger_input")

        elif state_str == 'move_add_target_limit':
            from bot.handlers.move.strategy.create import handle_move_target_limit_input
            await handle_move_target_limit_input(update, context)
            logger.info("✅ Routed to: handle_move_target_limit_input")
        
        # ==================== MOVE STRATEGY EDITING ====================
        elif state_str == 'move_edit_name':
            from bot.handlers.move.strategy.input_handlers import handle_move_edit_name_input
            await handle_move_edit_name_input(update, context, text)
            logger.info("✅ Routed to: handle_move_edit_name_input")
        
        elif state_str == 'move_edit_description':
            from bot.handlers.move.strategy.input_handlers import handle_move_edit_description_input
            await handle_move_edit_description_input(update, context, text)
            logger.info("✅ Routed to: handle_move_edit_description_input")
        
        elif state_str == 'move_edit_lot_size':
            from bot.handlers.move.strategy.input_handlers import handle_move_edit_lot_size_input
            await handle_move_edit_lot_size_input(update, context, text)
            logger.info("✅ Routed to: handle_move_edit_lot_size_input")
        
        # ==================== MOVE PRESET STATES ====================
        elif state_str == 'move_create_preset_name':
            from bot.handlers.move.preset.create import handle_move_preset_name
            await handle_move_preset_name(update, context)
            logger.info("✅ Routed to: handle_move_preset_name")
        
        elif state_str == 'move_preset_sl_trigger':
            from bot.handlers.move.preset.create import handle_move_preset_sl_trigger
            await handle_move_preset_sl_trigger(update, context)
            logger.info("✅ Routed to: handle_move_preset_sl_trigger")
        
        elif state_str == 'move_preset_sl_limit':
            from bot.handlers.move.preset.create import handle_move_preset_sl_limit
            await handle_move_preset_sl_limit(update, context)
            logger.info("✅ Routed to: handle_move_preset_sl_limit")
        
        elif state_str == 'move_preset_target':
            from bot.handlers.move.preset.create import handle_move_preset_target
            await handle_move_preset_target(update, context)
            logger.info("✅ Routed to: handle_move_preset_target")
        
        elif state_str == 'move_preset_target_limit':
            from bot.handlers.move.preset.create import handle_move_preset_target_limit
            await handle_move_preset_target_limit(update, context)
            logger.info("✅ Routed to: handle_move_preset_target_limit")
        
        elif state_str.startswith('move_edit_preset_'):
            from bot.handlers.move.preset.edit import handle_move_edit_preset_field
            await handle_move_edit_preset_field(update, context)
            logger.info("✅ Routed to: handle_move_edit_preset_field")
        
        # ==================== MOVE MANUAL TRADE ====================
        elif state_str == 'move_manual_entry_price':
            from bot.handlers.move.trade.manual import handle_move_manual_entry_price
            await handle_move_manual_entry_price(update, context)
            logger.info("✅ Routed to: handle_move_manual_entry_price")
        
        elif state_str == 'move_manual_lot_size':
            from bot.handlers.move.trade.manual import handle_move_manual_lot_size
            await handle_move_manual_lot_size(update, context)
            logger.info("✅ Routed to: handle_move_manual_lot_size")
        
        elif state_str == 'move_manual_sl_price':
            from bot.handlers.move.trade.manual import handle_move_manual_sl_price
            await handle_move_manual_sl_price(update, context)
            logger.info("✅ Routed to: handle_move_manual_sl_price")
        
        elif state_str == 'move_manual_target_price':
            from bot.handlers.move.trade.manual import handle_move_manual_target_price
            await handle_move_manual_target_price(update, context)
            logger.info("✅ Routed to: handle_move_manual_target_price")
        
        elif state_str == 'move_manual_direction':
            from bot.handlers.move.trade.manual import handle_move_manual_direction
            await handle_move_manual_direction(update, context)
            logger.info("✅ Routed to: handle_move_manual_direction")
        
        elif state_str == 'move_manual_strategy_select':
            from bot.handlers.move.trade.manual import handle_move_manual_strategy_select
            await handle_move_manual_strategy_select(update, context)
            logger.info("✅ Routed to: handle_move_manual_strategy_select")
        
        # ==================== MOVE AUTO TRADE ====================
        elif state_str == 'move_auto_add_time':
            from bot.handlers.move_auto_trade_handler import handle_move_auto_time_input
            await handle_move_auto_time_input(update, context, text)
            logger.info("✅ Routed to: handle_move_auto_time_input")
        
        elif state_str == 'move_auto_edit_time':
            from bot.handlers.move_auto_trade_handler import handle_move_auto_edit_time_input
            await handle_move_auto_edit_time_input(update, context, text)
            logger.info("✅ Routed to: handle_move_auto_edit_time_input")
        
        # ==================== STRADDLE STRATEGY ====================
        elif state_str == 'straddle_add_name':
            from bot.handlers.straddle_input_handlers import handle_straddle_name_input
            await handle_straddle_name_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_name_input")
        
        elif state_str == 'straddle_add_description':
            from bot.handlers.straddle_input_handlers import handle_straddle_description_input
            await handle_straddle_description_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_description_input")
        
        elif state_str == 'straddle_add_lot_size':
            from bot.handlers.straddle_input_handlers import handle_straddle_lot_size_input
            await handle_straddle_lot_size_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_lot_size_input")
        
        elif state_str == 'straddle_add_sl_trigger':
            from bot.handlers.straddle_input_handlers import handle_straddle_sl_trigger_input
            await handle_straddle_sl_trigger_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_sl_trigger_input")
        
        elif state_str == 'straddle_add_sl_limit':
            from bot.handlers.straddle_input_handlers import handle_straddle_sl_limit_input
            await handle_straddle_sl_limit_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_sl_limit_input")
        
        elif state_str == 'straddle_add_target_trigger':
            from bot.handlers.straddle_input_handlers import handle_straddle_target_trigger_input
            await handle_straddle_target_trigger_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_target_trigger_input")
        
        elif state_str == 'straddle_add_target_limit':
            from bot.handlers.straddle_input_handlers import handle_straddle_target_limit_input
            await handle_straddle_target_limit_input(update, context, text)
            logger.info("✅ Routed to: handle_straddle_target_limit_input")

        elif state_str == 'straddle_add_atm_offset':
            from bot.handlers.straddle_input_handlers import handle_atm_offset_input
            await handle_atm_offset_input(update, context, text)
            logger.info("✅ Routed to: handle_atm_offset_input")
        
        # ==================== STRANGLE STRATEGY ====================
        elif state_str == 'strangle_add_name':
            from bot.handlers.strangle_input_handlers import handle_strangle_name_input
            await handle_strangle_name_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_name_input")
        
        elif state_str == 'strangle_add_description':
            from bot.handlers.strangle_input_handlers import handle_strangle_description_input
            await handle_strangle_description_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_description_input")
        
        elif state_str == 'strangle_add_lot_size':
            from bot.handlers.strangle_input_handlers import handle_strangle_lot_size_input
            await handle_strangle_lot_size_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_lot_size_input")
        
        elif state_str == 'strangle_add_sl_trigger':
            from bot.handlers.strangle_input_handlers import handle_strangle_sl_trigger_input
            await handle_strangle_sl_trigger_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_sl_trigger_input")
        
        elif state_str == 'strangle_add_sl_limit':
            from bot.handlers.strangle_input_handlers import handle_strangle_sl_limit_input
            await handle_strangle_sl_limit_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_sl_limit_input")
        
        elif state_str == 'strangle_add_target_trigger':
            from bot.handlers.strangle_input_handlers import handle_strangle_target_trigger_input
            await handle_strangle_target_trigger_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_target_trigger_input")
        
        elif state_str == 'strangle_add_target_limit':
            from bot.handlers.strangle_input_handlers import handle_strangle_target_limit_input
            await handle_strangle_target_limit_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_target_limit_input")
        
        elif state_str == 'strangle_add_otm_value':
            from bot.handlers.strangle_input_handlers import handle_strangle_otm_value_input
            await handle_strangle_otm_value_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_otm_value_input")
        
        elif state_str == 'strangle_edit_name_input':
            from bot.handlers.strangle_input_handlers import handle_strangle_edit_name_input
            await handle_strangle_edit_name_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_edit_name_input")
        
        elif state_str == 'strangle_edit_desc_input':
            from bot.handlers.strangle_input_handlers import handle_strangle_edit_desc_input
            await handle_strangle_edit_desc_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_edit_desc_input")
        
        elif state_str == 'strangle_edit_lot_input':
            from bot.handlers.strangle_input_handlers import handle_strangle_edit_lot_input
            await handle_strangle_edit_lot_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_edit_lot_input")
        
        elif state_str == 'strangle_edit_otm_value_input':
            from bot.handlers.strangle_input_handlers import handle_strangle_edit_otm_value_input
            await handle_strangle_edit_otm_value_input(update, context, text)
            logger.info("✅ Routed to: handle_strangle_edit_otm_value_input")
        
        # ==================== MANUAL TRADE PRESET ====================
        elif state_str == 'manual_preset_add_name':
            from bot.handlers.manual_preset_input_handlers import handle_manual_preset_name_input
            await handle_manual_preset_name_input(update, context, text)
            logger.info("✅ Routed to: handle_manual_preset_name_input")
        
        elif state_str == 'manual_preset_edit_name':
            from bot.handlers.manual_preset_input_handlers import handle_manual_preset_name_input
            await handle_manual_preset_name_input(update, context, text)
            logger.info("✅ Routed to: handle_manual_preset_name_input (edit)")
        
        # ==================== AUTO TRADE ====================
        elif state_str == 'auto_trade_add_time':
            from bot.handlers.auto_trade_handler import handle_auto_trade_time_input
            await handle_auto_trade_time_input(update, context, text)
            logger.info("✅ Routed to: handle_auto_trade_time_input")
        
        elif state_str == 'auto_trade_edit_time':
            from bot.handlers.auto_trade_handler import handle_auto_trade_edit_time_input
            await handle_auto_trade_edit_time_input(update, context, text)
            logger.info("✅ Routed to: handle_auto_trade_edit_time_input")

        # ==================== CALLBACK-BASED STATES ====================
        elif state_str in ['straddle_sl_monitor_confirm', 'strangle_sl_monitor_confirm']:
            logger.info(f"📌 State {state_str} is callback-based, skipping text handler")
            await update.message.reply_text(
                "ℹ️ Please use the buttons to confirm your choice.",
                parse_mode='HTML'
            )

        # ==================== UNHANDLED STATE ====================
        else:
            logger.warning(f"⚠️ UNHANDLED STATE: {state_str}")
            await update.message.reply_text(
                "❌ Something went wrong. Please use /start.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
        
        logger.info("=" * 80)
        logger.info("✅ MESSAGE ROUTER COMPLETE")
        logger.info("=" * 80)
    
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ ERROR IN MESSAGE ROUTER: {e}", exc_info=True)
        logger.error("=" * 80)
        try:
            await update.message.reply_text(
                "❌ An error occurred. Please try /start.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(update.effective_user.id)
        except Exception as err:
            logger.error(f"Failed to send error message: {err}")


__all__ = ['route_message']
        
