"""
STRANGLE Manual Trade Execution Handler

Handles immediate execution of STRANGLE trades:
- Sell OTM Call + OTM Put
- Real-time strike selection
- Order placement with SL/Target
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_trade_preset_ops import get_strangle_trade_presets
from bot.keyboards.strangle_strategy_keyboards import get_strangle_menu_keyboard

logger = setup_logger(__name__)

@error_handler
async def strangle_manual_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual STRANGLE trade execution menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened STRANGLE manual trade menu")
    
    presets = await get_strangle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "🎯 Manual STRANGLE Trade Execution\n\n"
            "❌ No trade presets found.\n\n"
            "Please create a STRANGLE Trade Preset first.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"strangle_manual_select_{preset['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_strangle")])
    
    await query.edit_message_text(
        "🎯 Manual STRANGLE Trade Execution\n\n"
        f"Found {len(presets)} preset(s)\n\n"
        "Select a trade preset to execute:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# Additional handler functions follow same pattern as MOVE manual trade...

__all__ = [
    'strangle_manual_trade_callback',
]
