"""
Message router to direct messages to appropriate handlers based on state.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re

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

                # Straddle strategy states
        elif state_str == 'straddle_add_name':
            logger.info("→ Calling handle_straddle_name_input")
            await handle_straddle_name_input(update, context, text)
        
        elif state_str == 'straddle_add_description':
            logger.info("→ Calling handle_straddle_description_input")
            await handle_straddle_description_input(update, context, text)
        
        elif state_str == 'straddle_add_lot_size':
            logger.info("→ Calling handle_straddle_lot_size_input")
            await handle_straddle_lot_size_input(update, context, text)
        
        elif state_str == 'straddle_add_sl_trigger':
            logger.info("→ Calling handle_straddle_sl_trigger_input")
            await handle_straddle_sl_trigger_input(update, context, text)
        
        elif state_str == 'straddle_add_sl_limit':
            logger.info("→ Calling handle_straddle_sl_limit_input")
            await handle_straddle_sl_limit_input(update, context, text)
        
        elif state_str == 'straddle_add_target_trigger':
            logger.info("→ Calling handle_straddle_target_trigger_input")
            await handle_straddle_target_trigger_input(update, context, text)
        
        elif state_str == 'straddle_add_target_limit':
            logger.info("→ Calling handle_straddle_target_limit_input")
            await handle_straddle_target_limit_input(update, context, text)
        
        elif state_str == 'straddle_add_atm_offset':
            logger.info("→ Calling handle_straddle_atm_offset_input")
            await handle_straddle_atm_offset_input(update, context, text)

                # Strangle strategy states
        elif state_str == 'strangle_add_name':
            logger.info("→ Calling handle_strangle_name_input")
            await handle_strangle_name_input(update, context, text)
        
        elif state_str == 'strangle_add_description':
            logger.info("→ Calling handle_strangle_description_input")
            await handle_strangle_description_input(update, context, text)
        
        elif state_str == 'strangle_add_lot_size':
            logger.info("→ Calling handle_strangle_lot_size_input")
            await handle_strangle_lot_size_input(update, context, text)
        
        elif state_str == 'strangle_add_sl_trigger':
            logger.info("→ Calling handle_strangle_sl_trigger_input")
            await handle_strangle_sl_trigger_input(update, context, text)
        
        elif state_str == 'strangle_add_sl_limit':
            logger.info("→ Calling handle_strangle_sl_limit_input")
            await handle_strangle_sl_limit_input(update, context, text)
        
        elif state_str == 'strangle_add_target_trigger':
            logger.info("→ Calling handle_strangle_target_trigger_input")
            await handle_strangle_target_trigger_input(update, context, text)
        
        elif state_str == 'strangle_add_target_limit':
            logger.info("→ Calling handle_strangle_target_limit_input")
            await handle_strangle_target_limit_input(update, context, text)
        
        elif state_str == 'strangle_add_otm_value':
            logger.info("→ Calling handle_strangle_otm_value_input")
            await handle_strangle_otm_value_input(update, context, text)

                # Manual trade preset states
        elif state_str == 'manual_preset_add_name':
            logger.info("→ Calling handle_manual_preset_name_input")
            await handle_manual_preset_name_input(update, context, text)
        
        elif state_str == 'manual_preset_edit_name':
            logger.info("→ Calling handle_manual_preset_edit_name_input")
            await handle_manual_preset_name_input(update, context, text)

                # Auto trade states
        elif state_str == 'auto_trade_add_time':
            logger.info("→ Calling handle_auto_trade_time_input")
            await handle_auto_trade_time_input(update, context, text)
        
        elif state_str == 'auto_trade_edit_time':
            logger.info("→ Calling handle_auto_trade_edit_time_input")
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

# Strangle strategy input handlers
async def handle_strangle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy name input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    # Store strategy name
    await state_manager.set_state_data(user.id, {'name': text})
    
    # Ask for description
    await state_manager.set_state(user.id, 'strangle_add_description')
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="strangle_skip_description")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Enter description (optional):\n\n"
        f"Example: <code>Weekly BTC strangle for moderate volatility</code>\n\n"
        f"Or click Skip to continue.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_strangle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy description input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    # Store description
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data="strangle_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="strangle_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Name: <b>{state_data['name']}</b>\n"
        f"Description: <i>{text}</i>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_strangle_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy lot size input."""
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
        await state_manager.set_state(user.id, 'strangle_add_sl_trigger')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"Lot Size: <b>{lot_size}</b>\n\n"
            f"Enter stop loss trigger percentage:\n\n"
            f"Example: <code>50</code> (for 50% loss)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid lot size. Please enter a positive number.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy stop loss trigger input."""
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
        await state_manager.set_state(user.id, 'strangle_add_sl_limit')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"Example: <code>55</code> (exit at 55% loss if triggered)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy stop loss limit input."""
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
        await state_manager.set_state(user.id, 'strangle_add_target_trigger')
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target (0)", callback_data="strangle_skip_target")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"SL Trigger: <b>{state_data['sl_trigger_pct']}%</b>\n"
            f"SL Limit: <b>{sl_limit}%</b>\n\n"
            f"Enter target trigger percentage (optional):\n\n"
            f"Example: <code>100</code> (for 100% profit)\n"
            f"Or enter <code>0</code> to skip",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy target trigger input."""
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
            # Skip target - go to OTM selection
            state_data['target_limit_pct'] = 0
            await state_manager.set_state_data(user.id, state_data)
            
            keyboard = [
                [InlineKeyboardButton("📊 Percentage (Spot-based)", callback_data="strangle_otm_percentage")],
                [InlineKeyboardButton("🔢 Numeral (ATM-based)", callback_data="strangle_otm_numeral")],
                [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
            ]
            
            await update.message.reply_text(
                f"<b>➕ Add Strangle Strategy</b>\n\n"
                f"Select OTM strike selection method:\n\n"
                f"<b>Percentage:</b> Based on spot price\n"
                f"<i>Example: 1% of $120,000 = $1,200 offset</i>\n\n"
                f"<b>Numeral:</b> Based on strikes from ATM\n"
                f"<i>Example: 4 strikes away from ATM</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            # Ask for target limit
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'strangle_add_target_limit')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Strangle Strategy</b>\n\n"
                f"Target Trigger: <b>{target_trigger}%</b>\n\n"
                f"Enter target limit percentage:\n\n"
                f"Example: <code>105</code> (exit at 105% profit if triggered)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy target limit input."""
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
        
        # Ask for OTM selection type
        keyboard = [
            [InlineKeyboardButton("📊 Percentage (Spot-based)", callback_data="strangle_otm_percentage")],
            [InlineKeyboardButton("🔢 Numeral (ATM-based)", callback_data="strangle_otm_numeral")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"Select OTM strike selection method:\n\n"
            f"<b>Percentage:</b> Based on spot price\n"
            f"<i>Example: 1% of $120,000 = $1,200 offset</i>\n\n"
            f"<b>Numeral:</b> Based on strikes from ATM\n"
            f"<i>Example: 4 strikes away from ATM</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        await update.message.reply_text(
            f"❌ Invalid percentage. {str(e)}\n\n"
            f"Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_otm_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy OTM value input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    try:
        otm_value = float(text)
        
        # Get state data
        state_data = await state_manager.get_state_data(user.id)
        otm_type = state_data.get('otm_type', 'percentage')
        
        # Validate based on type
        if otm_type == 'percentage':
            if otm_value <= 0 or otm_value > 50:
                raise ValueError("Percentage must be between 0 and 50")
        else:  # numeral
            if otm_value <= 0 or otm_value > 100:
                raise ValueError("Number of strikes must be between 1 and 100")
            otm_value = int(otm_value)  # Convert to integer for numeral
        
        # Store OTM selection and save strategy
        state_data['otm_selection'] = {
            'type': otm_type,
            'value': otm_value
        }
        state_data['strategy_type'] = 'strangle'
        
        # Save to database
        from database.operations.strategy_ops import create_strategy_preset
        from .strangle_strategy_handler import get_strangle_menu_keyboard
        
        result = await create_strategy_preset(user.id, state_data)
        
        if result:
            otm_desc = f"{otm_value}% (Spot-based)" if otm_type == 'percentage' else f"{int(otm_value)} strikes (ATM-based)"
            
            await update.message.reply_text(
                f"<b>✅ Strangle Strategy Created</b>\n\n"
                f"Name: <b>{state_data['name']}</b>\n"
                f"Asset: <b>{state_data['asset']}</b>\n"
                f"Expiry: <b>{state_data['expiry_code']}</b>\n"
                f"Direction: <b>{state_data['direction'].title()}</b>\n"
                f"Lot Size: <b>{state_data['lot_size']}</b>\n"
                f"OTM Selection: <b>{otm_desc}</b>\n"
                f"Stop Loss: <b>{state_data['sl_trigger_pct']}% / {state_data['sl_limit_pct']}%</b>\n"
                + (f"Target: <b>{state_data['target_trigger_pct']}% / {state_data['target_limit_pct']}%</b>\n" 
                   if state_data.get('target_trigger_pct', 0) > 0 else ""),
                reply_markup=get_strangle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create strategy.",
                reply_markup=get_strangle_menu_keyboard()
            )
        
        # Clear state
        await state_manager.clear_state(user.id)
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
        
        state_data = await state_manager.get_state_data(user.id)
        otm_type = state_data.get('otm_type', 'percentage')
        
        if otm_type == 'percentage':
            await update.message.reply_text(
                f"❌ Invalid percentage. {str(e)}\n\n"
                f"Please enter a number between 0 and 50.\n\n"
                f"Example: <code>1</code> or <code>2.5</code>",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"❌ Invalid value. {str(e)}\n\n"
                f"Please enter a whole number between 1 and 100.\n\n"
                f"Example: <code>4</code> or <code>8</code>",
                reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Manual trade preset input handlers
async def handle_manual_preset_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle manual trade preset name input."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    
    # Store preset name
    await state_manager.set_state_data(user.id, {'preset_name': text})
    
    # Get user's APIs
    from database.operations.api_ops import get_api_credentials
    apis = await get_api_credentials(user.id)
    
    if not apis:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")]]
        await update.message.reply_text(
            "<b>➕ Add Manual Trade Preset</b>\n\n"
            "❌ No API credentials found.\n\n"
            "Please add an API credential first.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        return
    
    # Create keyboard with API options
    keyboard = []
    for api in apis:
        keyboard.append([InlineKeyboardButton(
            f"📊 {api.api_name}",
            callback_data=f"manual_preset_api_{api.id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")])
    
    await update.message.reply_text(
        f"<b>➕ Add Manual Trade Preset</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Select API account:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# Auto trade input handlers
async def handle_auto_trade_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle auto trade time input for add."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import re
    user = update.effective_user
    
    # Validate time format (HH:MM in 24-hour format)
    time_pattern = r'^([0-1][0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")]]
        await update.message.reply_text(
            "❌ Invalid time format.\n\n"
            "Please use <b>HH:MM</b> in 24-hour format.\n\n"
            "<b>Examples:</b>\n"
            "• <code>09:15</code> (9:15 AM)\n"
            "• <code>15:30</code> (3:30 PM)\n"
            "• <code>23:45</code> (11:45 PM)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    state_data['execution_time'] = text
    
    # Get preset details for confirmation
    from database.operations.manual_trade_preset_ops import get_manual_trade_preset
    from database.operations.api_ops import get_api_credential
    from database.operations.strategy_ops import get_strategy_preset_by_id
    from .auto_trade_handler import get_auto_trade_menu_keyboard
    
    preset = await get_manual_trade_preset(state_data['manual_preset_id'])
    
    if not preset:
        await update.message.reply_text(
            "❌ Preset not found.",
            reply_markup=get_auto_trade_menu_keyboard()
        )
        await state_manager.clear_state(user.id)
        return
    
    # Get API and strategy
    api = await get_api_credential(preset['api_credential_id'])
    strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
    
    # Build confirmation message
    confirmation_text = "<b>✅ Confirm Algo Setup</b>\n\n"
    confirmation_text += f"<b>Preset:</b> {preset['preset_name']}\n"
    confirmation_text += f"<b>API:</b> {api.api_name if api else 'Unknown'}\n"
    
    if strategy:
        confirmation_text += f"<b>Strategy:</b> {strategy['name']}\n"
        confirmation_text += f"<b>Type:</b> {preset['strategy_type'].title()}\n"
        confirmation_text += f"<b>Asset:</b> {strategy['asset']}\n"
        confirmation_text += f"<b>Direction:</b> {strategy['direction'].title()}\n"
    
    confirmation_text += f"\n<b>⏰ Execution Time:</b> {text} IST\n\n"
    confirmation_text += "⚠️ The bot will automatically execute this trade daily at the scheduled time.\n\n"
    confirmation_text += "Confirm to activate?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="auto_trade_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")]
    ]
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def handle_auto_trade_edit_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle auto trade time input for edit."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import re
    user = update.effective_user
    
    # Validate time format
    time_pattern = r'^([0-1][0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")]]
        await update.message.reply_text(
            "❌ Invalid time format.\n\n"
            "Please use <b>HH:MM</b> in 24-hour format.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    state_data['execution_time'] = text
    
    # Get preset details for confirmation
    from database.operations.manual_trade_preset_ops import get_manual_trade_preset
    from database.operations.api_ops import get_api_credential
    from database.operations.strategy_ops import get_strategy_preset_by_id
    from .auto_trade_handler import get_auto_trade_menu_keyboard
    
    preset = await get_manual_trade_preset(state_data['manual_preset_id'])
    
    if not preset:
        await update.message.reply_text(
            "❌ Preset not found.",
            reply_markup=get_auto_trade_menu_keyboard()
        )
        await state_manager.clear_state(user.id)
        return
    
    # Get API and strategy
    api = await get_api_credential(preset['api_credential_id'])
    strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
    
    # Build confirmation message
    confirmation_text = "<b>✅ Confirm Edit</b>\n\n"
    confirmation_text += f"<b>Preset:</b> {preset['preset_name']}\n"
    confirmation_text += f"<b>API:</b> {api.api_name if api else 'Unknown'}\n"
    
    if strategy:
        confirmation_text += f"<b>Strategy:</b> {strategy['name']}\n"
    
    confirmation_text += f"\n<b>⏰ New Execution Time:</b> {text} IST\n\n"
    confirmation_text += "Confirm to update?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="auto_trade_edit_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")]
    ]
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
if __name__ == "__main__":
    print("Message router module loaded")
            
