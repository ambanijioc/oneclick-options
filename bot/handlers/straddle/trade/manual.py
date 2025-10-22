"""
STRADDLE Manual Trade Execution Handler

Handles immediate execution of STRADDLE trades:
- Buy/Sell Call + Put at ATM strike
- Real-time price monitoring
- Order placement with SL/Target
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.straddle_trade_preset_ops import get_straddle_trade_presets
from bot.keyboards.straddle_strategy_keyboards import get_straddle_menu_keyboard

logger = setup_logger(__name__)

@error_handler
async def straddle_manual_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual STRADDLE trade execution menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened STRADDLE manual trade menu")
    
    presets = await get_straddle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "🎯 Manual STRADDLE Trade Execution\n\n"
            "❌ No trade presets found.\n\n"
            "Please create a STRADDLE Trade Preset first.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"straddle_manual_select_{preset['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_straddle")])
    
    await query.edit_message_text(
        "🎯 Manual STRADDLE Trade Execution\n\n"
        f"Found {len(presets)} preset(s)\n\n"
        "Select a trade preset to execute:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

__all__ = [
    'straddle_manual_trade_callback',
]
