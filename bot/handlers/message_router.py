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
        
        # Convert state to string for easier comparison
        state_str = state.value if hasattr(state, 'value') else str(state) if state else None
        
        logger.info(f"Current conversation state: {state_str}")
        
        # If no state, send helpful message
        if state is None:
            logger.warning(f"No active conversation for user {user.id}")
            await update.message.reply_text(
                "Please use /start to begin.",
                parse_mode='HTML'
            )
            return
        
        logger.info(f"Routing to handler for state: {state_str}")
        
        # Route based on conversation state
        # API conversation states
        if state_str == 'api_add_name' or state == ConversationState.API_ADD_NAME:
            logger.info("→ Calling handle_api_name_input")
            from .api_handler import handle_api_name_input
            await handle_api_name_input(update, context)
        
        elif state_str == 'api_add_description' or state == ConversationState.API_ADD_DESCRIPTION:
            logger.info("→ Calling handle_api_description_input")
            from .api_handler import handle_api_description_input
            await handle_api_description_input(update, context)
        
        elif state_str == 'api_add_key' or state == ConversationState.API_ADD_KEY:
            logger.info("→ Calling handle_api_key_input")
            from .api_handler import handle_api_key_input
            await handle_api_key_input(update, context)
        
        elif state_str == 'api_add_secret' or state == ConversationState.API_ADD_SECRET:
            logger.info("→ Calling handle_api_secret_input")
            from .api_handler import handle_api_secret_input
            await handle_api_secret_input(update, context)
        
        # Strategy states (handles both straddle and strangle)
        elif state_str == 'strategy_add_name' or state == ConversationState.STRATEGY_ADD_NAME:
            logger.info("→ Calling handle_strategy_name_input")
            from .strategy_handler import handle_strategy_name_input
            await handle_strategy_name_input(update, context)
        
        elif state_str == 'strategy_add_description' or state == ConversationState.STRATEGY_ADD_DESCRIPTION:
            logger.info("→ Calling handle_strategy_description_input")
            from .strategy_handler import handle_strategy_description_input
            await handle_strategy_description_input(update, context)
        
        # Move strategy states (string-based)
        elif state_str == 'move_strategy_add_name':
            logger.info("→ Calling handle_move_strategy_name_input")
            await handle_move_strategy_name_input(update, context, text)
        
        elif state_str == 'move_strategy_add_lot_size':
            logger.info("→ Calling handle_move_strategy_lot_size_input")
            await handle_move_strategy_lot_size_input(update, context, text)
        
        elif state_str == 'move_strategy_add_atm_offset':
            logger.info("→ Calling handle_move_strategy_atm_offset_input")
            await handle_move_strategy_atm_offset_input(update, context, text)
        
        elif state_str == 'move_auto_add_time':
            logger.info("→ Calling handle_move_auto_time_input")
            await handle_move_auto_time_input(update, context, text)
        
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
            await update.message.reply_text(
                "❌ An error occurred. Please try /start.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(update.effective_user.id)
        except Exception:
            pass


# Move strategy input handlers
async def handle_move_strategy_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy name input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
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


async def handle_move_strategy_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy lot size input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
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


async def handle_move_strategy_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy ATM offset input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        
        # Store ATM offset and save strategy
        state_data = await state_manager.get_state_data(user.id)
        state_data['atm_offset'] = atm_offset
        
        # Save to database
        from database.operations.move_strategy_ops import create_move_strategy
        
        result = await create_move_strategy(user.id, state_data)
        
        if result:
            from .move_strategy_handler import get_move_strategy_menu_keyboard
            await update.message.reply_text(
                f"<b>✅ Move Strategy Created</b>\n\n"
                f"Name: <b>{state_data['strategy_name']}</b>\n"
                f"Asset: <b>{state_data['asset']}</b>\n"
                f"Direction: <b>{state_data['direction'].title()}</b>\n"
                f"Lot Size: <b>{state_data['lot_size']}</b>\n"
                f"ATM Offset: <b>{atm_offset:+d}</b>",
                reply_markup=get_move_strategy_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create strategy.",
                reply_markup=get_move_strategy_menu_keyboard()
            )
        
        # Clear state
        await state_manager.clear_state(user.id)
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]]
        await update.message.reply_text(
            "❌ Invalid offset. Please enter a number.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_move_auto_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move auto execution time input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import re
    
    user = update.effective_user
    time_pattern = r'^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM|am|pm)$'
    
    if re.match(time_pattern, text):
        # Store time and create schedule
        from database.operations.move_strategy_ops import create_move_auto_execution
        from .move_auto_trade_handler import get_move_auto_trade_keyboard
        
        state_data = await state_manager.get_state_data(user.id)
        
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

# Straddle strategy input handlers
async def handle_straddle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy name input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    # Store strategy name
    await state_manager.set_state_data(user.id, {'name': text})
    
    # Ask for description
    await state_manager.set_state(user.id, 'straddle_add_description')
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="straddle_skip_description")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Enter description (optional):\n\n"
        f"Example: <code>Weekly BTC straddle for high volatility</code>\n\n"
        f"Or click Skip to continue.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_straddle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy description input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    # Store description
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data="straddle_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="straddle_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Name: <b>{state_data['name']}</b>\n"
        f"Description: <i>{text}</i>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_straddle_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy lot size input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        lot_size = int(text)
        if lot_size <= 0:
            raise ValueError("Lot size must be positive")
        
        # Store lot size
        state_data = await state_manager.get_state_data(user.id)
        state_data['lot_size'] = lot_size
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for stop loss trigger percentage
        await state_manager.set_state(user.id, 'straddle_add_sl_trigger')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"Lot Size: <b>{lot_size}</b>\n\n"
            f"Enter stop loss trigger percentage:\n\n"
            f"Example: <code>50</code> (for 50% loss)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid lot size. Please enter a positive number.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy stop loss trigger input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for stop loss limit percentage
        await state_manager.set_state(user.id, 'straddle_add_sl_limit')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"Example: <code>55</code> (exit at 55% loss if triggered)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy stop loss limit input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_limit_pct'] = sl_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for target percentage (optional)
        await state_manager.set_state(user.id, 'straddle_add_target_trigger')
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target (0)", callback_data="straddle_skip_target")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"SL Trigger: <b>{state_data['sl_trigger_pct']}%</b>\n"
            f"SL Limit: <b>{sl_limit}%</b>\n\n"
            f"Enter target trigger percentage (optional):\n\n"
            f"Example: <code>100</code> (for 100% profit)\n"
            f"Or enter <code>0</code> to skip",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy target trigger input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Store target trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger_pct'] = target_trigger
        
        if target_trigger == 0:
            # Skip target - go to ATM offset
            state_data['target_limit_pct'] = 0
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'straddle_add_atm_offset')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Straddle Strategy</b>\n\n"
                f"Enter ATM offset:\n\n"
                f"• <code>0</code> = ATM (At The Money)\n"
                f"• <code>+1000</code> = Strike $1000 above ATM\n"
                f"• <code>-1000</code> = Strike $1000 below ATM",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            # Ask for target limit
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'straddle_add_target_limit')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Straddle Strategy</b>\n\n"
                f"Target Trigger: <b>{target_trigger}%</b>\n\n"
                f"Enter target limit percentage:\n\n"
                f"Example: <code>105</code> (exit at 105% profit if triggered)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy target limit input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Store target limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_limit_pct'] = target_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for ATM offset
        await state_manager.set_state(user.id, 'straddle_add_atm_offset')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"Enter ATM offset:\n\n"
            f"• <code>0</code> = ATM (At The Money)\n"
            f"• <code>+1000</code> = Strike $1000 above ATM\n"
            f"• <code>-1000</code> = Strike $1000 below ATM",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy ATM offset input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        
        # Store ATM offset and save strategy
        state_data = await state_manager.get_state_data(user.id)
        state_data['atm_offset'] = atm_offset
        state_data['strategy_type'] = 'straddle'
        
        # Save to database
        from database.operations.strategy_ops import create_strategy_preset
        from .straddle_strategy_handler import get_straddle_menu_keyboard
        
        result = await create_strategy_preset(user.id, state_data)
        
        if result:
            await update.message.reply_text(
                f"<b>✅ Straddle Strategy Created</b>\n\n"
                f"Name: <b>{state_data['name']}</b>\n"
                f"Asset: <b>{state_data['asset']}</b>\n"
                f"Expiry: <b>{state_data['expiry_code']}</b>\n"
                f"Direction: <b>{state_data['direction'].title()}</b>\n"
                f"Lot Size: <b>{state_data['lot_size']}</b>\n"
                f"ATM Offset: <b>{atm_offset:+d}</b>\n"
                f"Stop Loss: <b>{state_data['sl_trigger_pct']}% / {state_data['sl_limit_pct']}%</b>\n"
                + (f"Target: <b>{state_data['target_trigger_pct']}% / {state_data['target_limit_pct']}%</b>\n" 
                   if state_data.get('target_trigger_pct', 0) > 0 else ""),
                reply_markup=get_straddle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create strategy.",
                reply_markup=get_straddle_menu_keyboard()
            )
        
        # Clear state
        await state_manager.clear_state(user.id)
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid offset. Please enter a whole number.\n\n"
            "Example: <code>0</code>, <code>+500</code>, <code>-1000</code>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
if __name__ == "__main__":
    print("Message router module loaded")
            
