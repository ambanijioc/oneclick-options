"""
MOVE strategy input handlers with expiry selection support.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import StateManager

logger = setup_logger(__name__)
state_manager = StateManager()


async def handle_move_expiry_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection for MOVE strategy."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    expiry = query.data.split('_')[-1]  # daily, weekly, or monthly
    
    # Store expiry
    state_data = await state_manager.get_state_data(user.id)
    state_data['expiry'] = expiry
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to direction selection
    keyboard = [
        [InlineKeyboardButton("📈 Long (High Volatility)", callback_data="move_direction_long")],
        [InlineKeyboardButton("📉 Short (Low Volatility)", callback_data="move_direction_short")],
        [InlineKeyboardButton("🔙 Back", callback_data="move_strategy_create")]
    ]
    
    await query.edit_message_text(
        f"<b>📊 MOVE Strategy - Direction</b>\n\n"
        f"<b>Selected Expiry:</b> {expiry.title()}\n\n"
        f"Choose your trading direction:\n\n"
        f"<b>Long (Buy):</b> Profit from high volatility\n"
        f"• You expect BIG price movement (up or down)\n"
        f"• Premium rises when volatility increases\n\n"
        f"<b>Short (Sell):</b> Profit from stability\n"
        f"• You expect SMALL price movement\n"
        f"• Premium drops when volatility is low",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle ATM offset input for MOVE strategy."""
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        
        # Validate offset range (-5 to +5 is reasonable)
        if not -5 <= atm_offset <= 5:
            await update.message.reply_text(
                "❌ ATM offset must be between -5 and +5.\n\n"
                "Examples:\n"
                "• 0 = ATM strike\n"
                "• +1 = One strike above ATM\n"
                "• -1 = One strike below ATM",
                parse_mode='HTML'
            )
            return
        
        # Store offset
        state_data = await state_manager.get_state_data(user.id)
        state_data['atm_offset'] = atm_offset
        await state_manager.set_state_data(user.id, state_data)
        
        # Move to lot size input
        await state_manager.set_state(user.id, 'awaiting_move_lot_size')
        
        await update.message.reply_text(
            f"<b>📊 MOVE Strategy - Lot Size</b>\n\n"
            f"<b>ATM Offset:</b> {atm_offset:+d}\n\n"
            f"Enter the number of contracts (lot size):\n\n"
            f"Examples:\n"
            f"• 1 = 1 contract\n"
            f"• 5 = 5 contracts\n"
            f"• 10 = 10 contracts",
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a whole number.\n\n"
            "Examples: 0, 1, -1, 2, -2",
            parse_mode='HTML'
        )


async def handle_move_stop_loss_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle stop loss trigger percentage input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        
        # Validate percentage (0-100%)
        if not 0 < sl_trigger <= 100:
            await update.message.reply_text(
                "❌ Stop loss trigger must be between 0% and 100%.\n\n"
                "Examples:\n"
                "• 30 = 30% loss triggers stop\n"
                "• 50 = 50% loss triggers stop",
                parse_mode='HTML'
            )
            return
        
        # Store trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['stop_loss_trigger'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Move to stop loss limit input
        await state_manager.set_state(user.id, 'awaiting_move_stop_loss_limit')
        
        await update.message.reply_text(
            f"<b>📊 MOVE Strategy - Stop Loss Limit</b>\n\n"
            f"<b>SL Trigger:</b> {sl_trigger}%\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"The limit should be slightly worse than trigger to ensure execution.\n\n"
            f"Examples:\n"
            f"• If trigger is 30%, limit could be 35%\n"
            f"• If trigger is 50%, limit could be 55%",
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number (percentage).\n\n"
            "Examples: 30, 50, 70",
            parse_mode='HTML'
        )


async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target trigger percentage input."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        
        # Validate percentage (0-500% is reasonable for MOVE)
        if not 0 < target_trigger <= 500:
            await update.message.reply_text(
                "❌ Target trigger must be between 0% and 500%.\n\n"
                "Examples:\n"
                "• 50 = 50% profit triggers target\n"
                "• 100 = 100% profit (2x) triggers target\n"
                "• 200 = 200% profit (3x) triggers target",
                parse_mode='HTML'
            )
            return
        
        # Store trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger'] = target_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Move to target limit input
        await state_manager.set_state(user.id, 'awaiting_move_target_limit')
        
        await update.message.reply_text(
            f"<b>📊 MOVE Strategy - Target Limit</b>\n\n"
            f"<b>Target Trigger:</b> {target_trigger}%\n\n"
            f"Enter target limit percentage:\n\n"
            f"The limit should be slightly lower than trigger to ensure execution.\n\n"
            f"Examples:\n"
            f"• If trigger is 100%, limit could be 95%\n"
            f"• If trigger is 200%, limit could be 190%",
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number (percentage).\n\n"
            "Examples: 50, 100, 200",
            parse_mode='HTML'
        )
        
