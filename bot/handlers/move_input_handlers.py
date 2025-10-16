"""
Input handlers for move strategy creation flow.
Handles text input during strategy creation.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager

logger = setup_logger(__name__)


async def handle_move_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy name input."""
    user = update.effective_user
    
    # Store strategy name
    await state_manager.set_state_data(user.id, {'strategy_name': text})
    
    # Ask for description
    await state_manager.set_state(user.id, 'move_strategy_add_description')
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="move_skip_description")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Enter description (optional):",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_move_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy description input."""
    user = update.effective_user
    
    # Store description
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data="move_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="move_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Name: <b>{state_data['strategy_name']}</b>\n"
        f"Description: <i>{text}</i>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_move_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy lot size input."""
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
        await state_manager.set_state(user.id, 'move_strategy_add_sl_trigger')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Move Strategy</b>\n\n"
            f"Lot Size: <b>{lot_size}</b>\n\n"
            f"Enter stop loss trigger percentage:\n\n"
            f"Example: <code>50</code> (for 50% loss)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        await update.message.reply_text(
            "❌ Invalid lot size. Please enter a positive number.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy stop loss trigger input."""
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
        await state_manager.set_state(user.id, 'move_strategy_add_sl_limit')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Move Strategy</b>\n\n"
            f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"Example: <code>55</code> (exit at 55% loss if triggered)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy stop loss limit input."""
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
        await state_manager.set_state(user.id, 'move_strategy_add_target_trigger')
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target (0)", callback_data="move_skip_target")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Move Strategy</b>\n\n"
            f"SL Trigger: <b>{state_data['sl_trigger_pct']}%</b>\n"
            f"SL Limit: <b>{sl_limit}%</b>\n\n"
            f"Enter target trigger percentage (optional):\n\n"
            f"Example: <code>100</code> (for 100% profit)\n"
            f"Or enter <code>0</code> to skip",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy target trigger input."""
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
            await state_manager.set_state(user.id, 'move_strategy_add_atm_offset')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Move Strategy</b>\n\n"
                f"Enter ATM offset (in strikes):\n\n"
                f"• <code>0</code> = ATM (At The Money)\n"
                f"• <code>+1</code> = 1 strike above ATM (BTC: $200, ETH: $20)\n"
                f"• <code>-1</code> = 1 strike below ATM\n"
                f"• <code>+5</code> = 5 strikes above ATM (BTC: $1000, ETH: $100)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            # Ask for target limit
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'move_strategy_add_target_limit')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Move Strategy</b>\n\n"
                f"Target Trigger: <b>{target_trigger}%</b>\n\n"
                f"Enter target limit percentage:\n\n"
                f"Example: <code>105</code> (exit at 105% profit if triggered)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_move_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy target limit input."""
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
        await state_manager.set_state(user.id, 'move_strategy_add_atm_offset')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Move Strategy</b>\n\n"
            f"Enter ATM offset (in strikes):\n\n"
            f"• <code>0</code> = ATM (At The Money)\n"
            f"• <code>+1</code> = 1 strike above ATM (BTC: $200, ETH: $20)\n"
            f"• <code>-1</code> = 1 strike below ATM\n"
            f"• <code>+5</code> = 5 strikes above ATM (BTC: $1000, ETH: $100)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move strategy ATM offset input."""
    user = update.effective_user
    
    try:
        # Parse ATM offset (in strikes)
        atm_strikes = int(text)
        
        # Get state data
        state_data = await state_manager.get_state_data(user.id)
        
        # ✅ Convert strikes to dollar offset (BTC = 200, ETH = 20)
        strike_increment = 200 if state_data['asset'] == 'BTC' else 20
        atm_offset = atm_strikes * strike_increment
        
        # Store ATM offset
        state_data['atm_offset'] = atm_offset
        await state_manager.set_state_data(user.id, state_data)
        
        # Save to database
        from database.operations.move_strategy_ops import create_move_strategy
        from bot.handlers.move_strategy_handler import get_move_strategy_menu_keyboard
        
        result = await create_move_strategy(user.id, state_data)
        
        if result:
            target_text = ""
            if state_data.get('target_trigger_pct', 0) > 0:
                target_text = f"Target: <b>{state_data['target_trigger_pct']}% / {state_data['target_limit_pct']}%</b>\n"
            
            await update.message.reply_text(
                f"<b>✅ Move Strategy Created</b>\n\n"
                f"Name: <b>{state_data['strategy_name']}</b>\n"
                f"Asset: <b>{state_data['asset']}</b>\n"
                f"Direction: <b>{state_data['direction'].title()}</b>\n"
                f"Lot Size: <b>{state_data['lot_size']}</b>\n"
                f"ATM Offset: <b>{atm_strikes:+d} strikes</b> ({atm_offset:+d} USD)\n"
                f"Stop Loss: <b>{state_data['sl_trigger_pct']}% / {state_data['sl_limit_pct']}%</b>\n"
                + target_text,
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
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
        await update.message.reply_text(
            "❌ Invalid offset. Please enter a whole number.\n\n"
            "Example:\n"
            "• <code>0</code> = ATM\n"
            "• <code>1</code> = 1 strike away (BTC: $200, ETH: $20)\n"
            "• <code>-2</code> = 2 strikes below ATM",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
      )
  
