"""
Message router to direct messages to appropriate handlers based on state.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager, ConversationState

logger = setup_logger(__name__)


async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Route text messages to appropriate handler based on user's conversation state.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        # Log that we received a message
        logger.info("=" * 50)
        logger.info("MESSAGE ROUTER CALLED")
        logger.info("=" * 50)
        
        if not update.message:
            logger.warning("No message in update")
            return
        
        if not update.message.text:
            logger.warning("No text in message")
            return
        
        user = update.effective_user
        text = update.message.text.strip()
        
        logger.info(f"User {user.id} ({user.first_name}) sent: '{text[:50]}'")
        
        # Skip commands (they're handled by command handlers)
        if text.startswith('/'):
            logger.info(f"Skipping command: {text}")
            return
        
        # Get current state
        state = await state_manager.get_state(user.id)
        
        logger.info(f"Current conversation state: {state.value if state else 'None'}")
        
        # If no state, send helpful message
        if state is None:
            logger.warning(f"No active conversation for user {user.id}")
            await update.message.reply_text(
                "Please use /start to begin.",
                parse_mode='HTML'
            )
            return
        
        logger.info(f"Routing to handler for state: {state.value}")
        
        # Route based on conversation state
        # API conversation states
        if state == ConversationState.API_ADD_NAME:
            logger.info("→ Calling handle_api_name_input")
            from .api_handler import handle_api_name_input
            await handle_api_name_input(update, context)
        
        elif state == ConversationState.API_ADD_DESCRIPTION:
            logger.info("→ Calling handle_api_description_input")
            from .api_handler import handle_api_description_input
            await handle_api_description_input(update, context)
        
        elif state == ConversationState.API_ADD_KEY:
            logger.info("→ Calling handle_api_key_input")
            from .api_handler import handle_api_key_input
            await handle_api_key_input(update, context)
        
        elif state == ConversationState.API_ADD_SECRET:
            logger.info("→ Calling handle_api_secret_input")
            from .api_handler import handle_api_secret_input
            await handle_api_secret_input(update, context)
        
        # Add more state handlers here as needed
        
        else:
            logger.warning(f"Unhandled conversation state: {state.value}")
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
            await update.message.reply_text(
                "❌ An error occurred. Please try /start.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(update.effective_user.id)
        except Exception:
            pass

# Add to existing message_router.py

async def handle_move_strategy_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str, text: str):
    """Handle move strategy input states."""
    user = update.effective_user
    
    if state == 'move_strategy_add_name':
        # Store strategy name
        await state_manager.set_state_data(user.id, {'strategy_name': text})
        
        # Ask for asset
        keyboard = [
            [InlineKeyboardButton("🟠 BTC", callback_data="move_strategy_asset_btc")],
            [InlineKeyboardButton("🔵 ETH", callback_data="move_strategy_asset_eth")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Move Strategy</b>\n\n"
            f"Name: <b>{text}</b>\n\n"
            f"Select asset:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    elif state == 'move_strategy_add_lot_size':
        try:
            lot_size = int(text)
            if lot_size <= 0:
                raise ValueError("Lot size must be positive")
            
            # Store lot size
            state_data = await state_manager.get_state_data(user.id)
            state_data['lot_size'] = lot_size
            await state_manager.set_state_data(user.id, state_data)
            
            # Ask for ATM offset
            await state_manager.set_state(user.id, 'move_strategy_add_atm_offset')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Move Strategy</b>\n\n"
                f"Lot Size: <b>{lot_size}</b>\n\n"
                f"Enter ATM offset:\n\n"
                f"• <code>0</code> = ATM (At The Money)\n"
                f"• <code>+1000</code> = Strike $1000 above ATM\n"
                f"• <code>-1000</code> = Strike $1000 below ATM",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]]
            await update.message.reply_text(
                "❌ Invalid lot size. Please enter a positive number.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif state == 'move_strategy_add_atm_offset':
        try:
            atm_offset = int(text)
            
            # Store ATM offset
            state_data = await state_manager.get_state_data(user.id)
            state_data['atm_offset'] = atm_offset
            await state_manager.set_state_data(user.id, state_data)
            
            # Ask for stop loss trigger
            await state_manager.set_state(user.id, 'move_strategy_add_sl_trigger')
            
            keyboard = [
                [InlineKeyboardButton("⏭️ Skip Stop Loss", callback_data="move_strategy_skip_sl")],
                [InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]
            ]
            
            await update.message.reply_text(
                f"<b>➕ Add Move Strategy</b>\n\n"
                f"ATM Offset: <b>{atm_offset:+d}</b>\n\n"
                f"Enter Stop Loss trigger price (or skip):\n\n"
                f"Example: <code>50.00</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]]
            await update.message.reply_text(
                "❌ Invalid offset. Please enter a number.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif state == 'move_auto_add_time':
        # Validate time format
        import re
        time_pattern = r'^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM|am|pm)$'
        
        if re.match(time_pattern, text):
            # Store time
            state_data = await state_manager.get_state_data(user.id)
            state_data['execution_time'] = text.upper()
            
            # Create schedule
            result = await create_move_auto_execution(user.id, {
                'api_credential_id': state_data['api_id'],
                'strategy_name': state_data['strategy_id'],
                'execution_time': text.upper()
            })
            
            if result:
                await update.message.reply_text(
                    f"<b>✅ Schedule Created</b>\n\n"
                    f"Execution Time: <b>{text.upper()} IST</b>\n\n"
                    f"Trade will execute automatically at the scheduled time.",
                    reply_markup=get_move_auto_trade_keyboard(),
                    parse_mode='HTML'
                )
                log_user_action(user.id, "move_auto_add", f"Created schedule for {text}")
            else:
                await update.message.reply_text(
                    "❌ Failed to create schedule.",
                    reply_markup=get_move_auto_trade_keyboard()
                )
            
            # Clear state
            await state_manager.clear_state(user.id)
        else:
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")]]
            await update.message.reply_text(
                "❌ Invalid time format.\n\n"
                "Please use: <code>HH:MM AM/PM</code>\n\n"
                "Example: <code>09:30 AM</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
                )

if __name__ == "__main__":
    print("Message router module loaded")
            
