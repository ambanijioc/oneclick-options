"""
Message router to direct messages to appropriate handlers based on state.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager, ConversationState

logger = setup_logger(__name__)

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route text messages to appropriate handler based on user's conversation state."""
    try:
        logger.info("=" * 50)
        logger.info("MESSAGE ROUTER CALLED")
        logger.info("=" * 50)
        
        if not update.message or not update.message.text:
            logger.warning("No message or text in update")
            return
        
        user = update.effective_user
        text = update.message.text.strip()
        
        logger.info(f"User {user.id} ({user.first_name}) sent: '{text[:50]}'")
        
        # Skip commands
        if text.startswith('/'):
            logger.info(f"Skipping command: {text}")
            return
        
        # Get current state
        state_str = await state_manager.get_state(user.id)
        
        logger.info(f"Current conversation state: {state_str}")
        
        # If no state, send helpful message
        if state_str is None:  # ✅ FIXED!
            logger.warning(f"No active conversation for user {user.id}")
            await update.message.reply_text("Please use /start to begin.", parse_mode='HTML')
            return
        
        logger.info(f"Routing to handler for state: {state_str}")
        
        # ==================== API STATES ====================
        if state_str == 'api_add_name':  # ✅ REMOVED enum check
            from .api_handler import handle_api_name_input
            await handle_api_name_input(update, context)
        
        elif state_str == 'api_add_description':
            from .api_handler import handle_api_description_input
            await handle_api_description_input(update, context)
        
        elif state_str == 'api_add_key':
            from .api_handler import handle_api_key_input
            await handle_api_key_input(update, context)
        
        elif state_str == 'api_add_secret':
            from .api_handler import handle_api_secret_input
            await handle_api_secret_input(update, context)
        
        # ==================== STRADDLE STRATEGY STATES ====================
        elif state_str == 'straddle_add_name':
            from .straddle_input_handlers import handle_straddle_name_input
            await handle_straddle_name_input(update, context, text)
        
        elif state_str == 'straddle_add_description':
            from .straddle_input_handlers import handle_straddle_description_input
            await handle_straddle_description_input(update, context, text)
        
        elif state_str == 'straddle_add_lot_size':
            from .straddle_input_handlers import handle_straddle_lot_size_input
            await handle_straddle_lot_size_input(update, context, text)
        
        elif state_str == 'straddle_add_sl_trigger':
            from .straddle_input_handlers import handle_straddle_sl_trigger_input
            await handle_straddle_sl_trigger_input(update, context, text)
        
        elif state_str == 'straddle_add_sl_limit':
            from .straddle_input_handlers import handle_straddle_sl_limit_input
            await handle_straddle_sl_limit_input(update, context, text)
        
        elif state_str == 'straddle_add_target_trigger':
            from .straddle_input_handlers import handle_straddle_target_trigger_input
            await handle_straddle_target_trigger_input(update, context, text)
        
        elif state_str == 'straddle_add_target_limit':
            from .straddle_input_handlers import handle_straddle_target_limit_input
            await handle_straddle_target_limit_input(update, context, text)
        
        elif state_str == 'straddle_add_atm_offset':
            from .straddle_input_handlers import handle_straddle_atm_offset_input
            await handle_straddle_atm_offset_input(update, context, text)

        # ==================== STRANGLE STRATEGY STATES ====================
        elif state_str == 'strangle_add_name':
            from .strangle_input_handlers import handle_strangle_name_input
            await handle_strangle_name_input(update, context, text)

        elif state_str == 'strangle_add_description':
            from .strangle_input_handlers import handle_strangle_description_input
            await handle_strangle_description_input(update, context, text)

        elif state_str == 'strangle_add_lot_size':
            from .strangle_input_handlers import handle_strangle_lot_size_input
            await handle_strangle_lot_size_input(update, context, text)

        elif state_str == 'strangle_add_sl_trigger':
            from .strangle_input_handlers import handle_strangle_sl_trigger_input
            await handle_strangle_sl_trigger_input(update, context, text)

        elif state_str == 'strangle_add_sl_limit':
            from .strangle_input_handlers import handle_strangle_sl_limit_input
            await handle_strangle_sl_limit_input(update, context, text)

        elif state_str == 'strangle_add_target_trigger':
            from .strangle_input_handlers import handle_strangle_target_trigger_input
            await handle_strangle_target_trigger_input(update, context, text)

        elif state_str == 'strangle_add_target_limit':
            from .strangle_input_handlers import handle_strangle_target_limit_input
            await handle_strangle_target_limit_input(update, context, text)

        elif state_str == 'strangle_add_otm_value':
            from .strangle_input_handlers import handle_strangle_otm_value_input
            await handle_strangle_otm_value_input(update, context, text)

        # Strangle EDIT states
        elif state_str == 'strangle_edit_name_input':
            from .strangle_input_handlers import handle_strangle_edit_name_input
            await handle_strangle_edit_name_input(update, context, text)

        elif state_str == 'strangle_edit_desc_input':
            from .strangle_input_handlers import handle_strangle_edit_desc_input
            await handle_strangle_edit_desc_input(update, context, text)

        elif state_str == 'strangle_edit_lot_input':
            from .strangle_input_handlers import handle_strangle_edit_lot_input
            await handle_strangle_edit_lot_input(update, context, text)

        elif state_str == 'strangle_edit_sl_trigger_input':
            from .strangle_input_handlers import handle_strangle_edit_sl_trigger_input
            await handle_strangle_edit_sl_trigger_input(update, context, text)

        elif state_str == 'strangle_edit_sl_limit_input':
            from .strangle_input_handlers import handle_strangle_edit_sl_limit_input
            await handle_strangle_edit_sl_limit_input(update, context, text)

        elif state_str == 'strangle_edit_target_trigger_input':
            from .strangle_input_handlers import handle_strangle_edit_target_trigger_input
            await handle_strangle_edit_target_trigger_input(update, context, text)

        elif state_str == 'strangle_edit_target_limit_input':
            from .strangle_input_handlers import handle_strangle_edit_target_limit_input
            await handle_strangle_edit_target_limit_input(update, context, text)

        elif state_str == 'strangle_edit_otm_value_input':
            from .strangle_input_handlers import handle_strangle_edit_otm_value_input
            await handle_strangle_edit_otm_value_input(update, context, text)

        # ==================== MOVE STRATEGY STATES ====================
        elif state_str == 'move_add_name':
            from .move_input_handlers import handle_move_name_input
            await handle_move_name_input(update, context, text)

        elif state_str == 'move_add_description':
            from .move_input_handlers import handle_move_description_input
            await handle_move_description_input(update, context, text)

        elif state_str == 'move_add_atm_offset':
            from .move_input_handlers import handle_move_atm_offset_input
            await handle_move_atm_offset_input(update, context, text)

        elif state_str == 'move_add_sl_trigger':
            from .move_input_handlers import handle_move_sl_trigger_input
            await handle_move_sl_trigger_input(update, context, text)

        elif state_str == 'move_add_sl_limit':
            from .move_input_handlers import handle_move_sl_limit_input
            await handle_move_sl_limit_input(update, context, text)

        elif state_str == 'move_add_target_trigger':
            from .move_input_handlers import handle_move_target_trigger_input
            await handle_move_target_trigger_input(update, context, text)

        elif state_str == 'move_add_target_limit':
            from .move_input_handlers import handle_move_target_limit_input
            await handle_move_target_limit_input(update, context, text)

        # MOVE edit states
        elif state_str == 'move_edit_name_input':
            from .move_input_handlers import handle_move_edit_name_input
            await handle_move_edit_name_input(update, context, text)

        elif state_str == 'move_edit_desc_input':
            from .move_input_handlers import handle_move_edit_desc_input
            await handle_move_edit_desc_input(update, context, text)

        elif state_str == 'move_edit_atm_offset_input':
            from .move_input_handlers import handle_move_edit_atm_offset_input
            await handle_move_edit_atm_offset_input(update, context, text)

        elif state_str == 'move_edit_sl_trigger_input':
            from .move_input_handlers import handle_move_edit_sl_trigger_input
            await handle_move_edit_sl_trigger_input(update, context, text)
        
        elif state_str == 'move_edit_sl_limit_input':
            from .move_input_handlers import handle_move_edit_sl_limit_input
            await handle_move_edit_sl_limit_input(update, context, text)

        elif state_str == 'move_edit_target_trigger_input':
            from .move_input_handlers import handle_move_edit_target_trigger_input
            await handle_move_edit_target_trigger_input(update, context, text)

        elif state_str == 'move_edit_target_limit_input':
            from .move_input_handlers import handle_move_edit_target_limit_input
            await handle_move_edit_target_limit_input(update, context, text)

        # ==================== MOVE TRADE PRESET STATES ====================
        elif state_str == 'awaiting_move_preset_name':
            from .move_trade_preset_handler import handle_move_preset_text_input
            await handle_move_preset_text_input(update, context)

        elif state_str == 'move_preset_add_name':
            from .move_preset_input_handlers import handle_move_preset_name_input
            await handle_move_preset_name_input(update, context, text)

        elif state_str == 'move_preset_edit_name':
            from .move_preset_input_handlers import handle_move_preset_name_input
            await handle_move_preset_name_input(update, context, text)

        # ==================== MANUAL TRADE PRESET STATES ====================
        elif state_str == 'manual_preset_add_name':
            from .manual_preset_input_handlers import handle_manual_preset_name_input
            await handle_manual_preset_name_input(update, context, text)

        elif state_str == 'manual_preset_edit_name':
            from .manual_preset_input_handlers import handle_manual_preset_name_input
            await handle_manual_preset_name_input(update, context, text)

        # ==================== AUTO TRADE STATES ====================
        elif state_str == 'auto_trade_add_time':
            from .auto_trade_handler import handle_auto_trade_time_input
            await handle_auto_trade_time_input(update, context, text)
        
        elif state_str == 'auto_trade_edit_time':
            from .auto_trade_handler import handle_auto_trade_edit_time_input
            await handle_auto_trade_edit_time_input(update, context, text)

        # ==================== MOVE AUTO TRADE STATES ====================
        elif state_str == 'move_auto_add_time':
            from .move_auto_trade_handler import handle_move_auto_time_input
            await handle_move_auto_time_input(update, context, text)

        elif state_str == 'move_auto_edit_time':
            from .move_auto_trade_handler import handle_move_auto_edit_time_input
            await handle_move_auto_edit_time_input(update, context, text)
            
        else:
            logger.warning(f"Unhandled conversation state: {state_str}")
            await update.message.reply_text(
                "❌ Something went wrong. Please use /start to return to main menu.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
        
        logger.info("=" * 50)
        logger.info("MESSAGE ROUTER COMPLETE")
        logger.info("=" * 50)
    
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"ERROR IN MESSAGE ROUTER: {e}", exc_info=True)
        logger.error("=" * 50)
        
        try:
            await update.message.reply_text("❌ An error occurred. Please try /start.", parse_mode='HTML')
            await state_manager.clear_state(update.effective_user.id)
        except Exception:
            pass
            
