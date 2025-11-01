"""
MOVE Preset View Handler

Displays list of all MOVE presets and their details.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_trade_preset_ops import (
    get_move_trade_presets,
    get_move_trade_preset_by_id,
)
from bot.keyboards.move_strategy_keyboards import (
    get_preset_list_keyboard,
    get_move_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_preset_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of all MOVE presets."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested MOVE presets list")
    
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No MOVE presets found.\n\n"
            "Create your first preset!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "📋 Your MOVE Presets\n\n"
        f"Total: {len(presets)} presets\n\n"
        "Select a preset to view details:",
        reply_markup=get_preset_list_keyboard(presets, action='view'),
        parse_mode='HTML'
    )

@error_handler
async def move_preset_view_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed view of selected preset."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    preset = await get_move_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = preset.get('preset_name', 'Unnamed')
    api_id = preset.get('api_id', 'N/A')
    strategy_id = preset.get('strategy_id', 'N/A')
    created_at = preset.get('created_at', 'N/A')
    
    text = (
        f"📋 MOVE Preset Details\n\n"
        f"📌 Name: {name}\n"
        f"🔑 API: {api_id}\n"
        f"📊 Strategy: {strategy_id}\n"
        f"📅 Created: {created_at}\n"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'move_preset_view_callback',
    'move_preset_view_details_callback',
]
