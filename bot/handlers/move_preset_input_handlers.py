"""
Input handlers for move trade preset name entry.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager

logger = setup_logger(__name__)


async def handle_move_preset_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move preset name input."""
    user = update.effective_user
    
    # Store preset name
    await state_manager.set_state_data(user.id, {'preset_name': text})
    
    # Trigger API selection
    from bot.handlers.move_trade_preset_handler import get_move_preset_menu_keyboard
    from database.operations.api_ops import get_api_credentials
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    if not apis:
        await update.message.reply_text(
            "<b>❌ No API Credentials</b>\n\n"
            "Please add API credentials first.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        return
    
    # ✅ FIXED: Use api_name (correct field name)
    keyboard = []
    for api in apis:
        name = api.api_name  # ✅ Correct attribute
        api_id = str(api.id)
        
        keyboard.append([InlineKeyboardButton(
            f"🔑 {name}",
            callback_data=f"move_preset_api_{api_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_preset")])
    
    await update.message.reply_text(
        f"<b>➕ Add Move Preset</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Select API Credentials:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
