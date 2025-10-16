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
        state = await state_manager.get_state(user.id)
        state_str = state.value if hasattr(state, 'value') else str(state) if state else None
        
        logger.info(f"Current conversation state: {state_str}")
        
        # If no state, send helpful message
        if state is None:
            logger.warning(f"No active conversation for user {user.id}")
            await update.message.reply_text("Please use /start to begin.", parse_mode='HTML')
            return
        
        logger.info(f"Routing to handler for state: {state_str}")
        
        # API conversation states
        if state_str == 'api_add_name' or state == ConversationState.API_ADD_NAME:
            from .api_handler import handle_api_name_input
            await handle_api_name_input(update, context)
        
        elif state_str == 'api_add_description' or state == ConversationState.API_ADD_DESCRIPTION:
            from .api_handler import handle_api_description_input
            await handle_api_description_input(update, context)
        
        elif state_str == 'api_add_key' or state == ConversationState.API_ADD_KEY:
            from .api_handler import handle_api_key_input
            await handle_api_key_input(update, context)
        
        elif state_str == 'api_add_secret' or state == ConversationState.API_ADD_SECRET:
            from .api_handler import handle_api_secret_input
            await handle_api_secret_input(update, context)
        
        # Straddle strategy states
        elif state_str == 'straddle_add_name':
            from .straddle_input_handlers import handle_straddle_name_input
            logger.info("→ Calling handle_straddle_name_input")
            await handle_straddle_name_input(update, context, text)
        
        elif state_str == 'straddle_add_description':
            from .straddle_input_handlers import handle_straddle_description_input
            logger.info("→ Calling handle_straddle_description_input")
            await handle_straddle_description_input(update, context, text)
        
        elif state_str == 'straddle_add_lot_size':
            from .straddle_input_handlers import handle_straddle_lot_size_input
            logger.info("→ Calling handle_straddle_lot_size_input")
            await handle_straddle_lot_size_input(update, context, text)
        
        elif state_str == 'straddle_add_sl_trigger':
            from .straddle_input_handlers import handle_straddle_sl_trigger_input
            logger.info("→ Calling handle_straddle_sl_trigger_input")
            await handle_straddle_sl_trigger_input(update, context, text)
        
        elif state_str == 'straddle_add_sl_limit':
            from .straddle_input_handlers import handle_straddle_sl_limit_input
            logger.info("→ Calling handle_straddle_sl_limit_input")
            await handle_straddle_sl_limit_input(update, context, text)
        
        elif state_str == 'straddle_add_target_trigger':
            from .straddle_input_handlers import handle_straddle_target_trigger_input
            logger.info("→ Calling handle_straddle_target_trigger_input")
            await handle_straddle_target_trigger_input(update, context, text)
        
        elif state_str == 'straddle_add_target_limit':
            from .straddle_input_handlers import handle_straddle_target_limit_input
            logger.info("→ Calling handle_straddle_target_limit_input")
            await handle_straddle_target_limit_input(update, context, text)
        
        elif state_str == 'straddle_add_atm_offset':
            from .straddle_input_handlers import handle_straddle_atm_offset_input
            logger.info("→ Calling handle_straddle_atm_offset_input")
            await handle_straddle_atm_offset_input(update, context, text)

        # Strangle strategy states - USE strangle_input_handlers.py
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

        # Add these after the strangle_add_otm_value state in message_router.py

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

        # ✅ Move strategy states - NEW
        elif state_str == 'move_strategy_add_name':
            from .move_input_handlers import handle_move_name_input
            logger.info("→ Calling handle_move_name_input")
            await handle_move_name_input(update, context, text)
        
        elif state_str == 'move_strategy_add_description':
            from .move_input_handlers import handle_move_description_input
            logger.info("→ Calling handle_move_description_input")
            await handle_move_description_input(update, context, text)
        
        elif state_str == 'move_strategy_add_lot_size':
            from .move_input_handlers import handle_move_lot_size_input
            logger.info("→ Calling handle_move_lot_size_input")
            await handle_move_lot_size_input(update, context, text)
        
        elif state_str == 'move_strategy_add_sl_trigger':
            from .move_input_handlers import handle_move_sl_trigger_input
            logger.info("→ Calling handle_move_sl_trigger_input")
            await handle_move_sl_trigger_input(update, context, text)
        
        elif state_str == 'move_strategy_add_sl_limit':
            from .move_input_handlers import handle_move_sl_limit_input
            logger.info("→ Calling handle_move_sl_limit_input")
            await handle_move_sl_limit_input(update, context, text)
        
        elif state_str == 'move_strategy_add_target_trigger':
            from .move_input_handlers import handle_move_target_trigger_input
            logger.info("→ Calling handle_move_target_trigger_input")
            await handle_move_target_trigger_input(update, context, text)
        
        elif state_str == 'move_strategy_add_target_limit':
            from .move_input_handlers import handle_move_target_limit_input
            logger.info("→ Calling handle_move_target_limit_input")
            await handle_move_target_limit_input(update, context, text)
        
        elif state_str == 'move_strategy_add_atm_offset':
            from .move_input_handlers import handle_move_atm_offset_input
            logger.info("→ Calling handle_move_atm_offset_input")
            await handle_move_atm_offset_input(update, context, text)

        # Manual trade preset states
        elif state_str == 'manual_preset_add_name':
            from .manual_trade_preset_handler import handle_manual_preset_name_input
            await handle_manual_preset_name_input(update, context, text)
        
        elif state_str == 'manual_preset_edit_name':
            from .manual_trade_preset_handler import handle_manual_preset_name_input
            await handle_manual_preset_name_input(update, context, text)

        # Auto trade states
        elif state_str == 'auto_trade_add_time':
            from .auto_trade_handler import handle_auto_trade_time_input
            await handle_auto_trade_time_input(update, context, text)
        
        elif state_str == 'auto_trade_edit_time':
            from .auto_trade_handler import handle_auto_trade_edit_time_input
            await handle_auto_trade_edit_time_input(update, context, text)
            
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
            
