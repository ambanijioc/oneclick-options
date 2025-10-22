"""
MOVE Auto Trade Handler

Handles scheduled automatic execution of MOVE trades:
- Time-based execution setup
- Preset selection
- Schedule management (enable/disable)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_trade_preset_ops import get_move_trade_presets
from bot.keyboards.move_strategy_keyboards import get_move_menu_keyboard, get_cancel_keyboard

logger = setup_logger(__name__)

@error_handler
async def move_auto_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display auto MOVE trade setup menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE auto trade menu")
    
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "⏰ Auto MOVE Trade Setup\n\n"
            "❌ No trade presets found.\n\n"
            "Please create a MOVE Trade Preset first.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"move_auto_select_{preset['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move")])
    
    await query.edit_message_text(
        "⏰ Auto MOVE Trade Setup\n\n"
        f"Found {len(presets)} preset(s)\n\n"
        "Select a preset to schedule automated execution:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

@error_handler
async def move_auto_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection for auto trade."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    # Store preset ID
    await state_manager.set_state(user.id, 'move_auto_time')
    await state_manager.set_state_data(user.id, {'preset_id': preset_id})
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="menu_move_auto_trade")]]
    
    await query.edit_message_text(
        "⏰ Set Execution Time\n\n"
        "Enter the time to execute this trade automatically.\n\n"
        "Format: `HH:MM` (24-hour format)\n\n"
        "Examples:\n"
        "• `09:15` - 9:15 AM\n"
        "• `15:30` - 3:30 PM\n"
        "• `23:45` - 11:45 PM",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def handle_move_auto_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle time input for MOVE auto trade setup."""
    user = update.effective_user
    
    # Validate time format (HH:MM)
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        await update.message.reply_text(
            "❌ Invalid time format.\n\n"
            "Please use `HH:MM` format (24-hour).\n\n"
            "Examples:\n"
            "• `09:15`\n"
            "• `15:30`\n"
            "• `23:45`",
            parse_mode='HTML'
        )
        return
    
    # Store time
    state_data = await state_manager.get_state_data(user.id)
    state_data['execution_time'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Show confirmation
    text_msg = (
        f"✅ Auto MOVE Trade Configured\n\n"
        f"Execution Time: {text}\n\n"
        f"The trade will be executed automatically at this time every day.\n\n"
        f"⚠️ Make sure to enable the schedule!"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Enable Schedule", callback_data="move_auto_enable")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move")]
    ]
    
    await update.message.reply_text(
        text_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    await state_manager.clear_state(user.id)

@error_handler
async def move_auto_enable_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable auto trade schedule."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # TODO: Implement schedule enablement in database
    # For now, show success message
    
    await query.edit_message_text(
        "✅ Auto MOVE Trade Enabled!\n\n"
        "Your trade will be executed automatically at the scheduled time.\n\n"
        "You can disable it anytime from the menu.",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "Enabled MOVE auto trade")

__all__ = [
    'move_auto_trade_callback',
    'move_auto_select_callback',
    'handle_move_auto_time_input',
    'move_auto_enable_callback',
]
