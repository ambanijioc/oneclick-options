"""
STRANGLE Preset Delete Handler

Handles safe deletion of STRANGLE trade presets with confirmation.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_trade_preset_ops import (
    get_strangle_trade_presets,
    get_strangle_trade_preset_by_id,
    delete_strangle_trade_preset
)
from bot.keyboards.strangle_strategy_keyboards import (
    get_preset_list_keyboard,
    get_delete_confirmation_keyboard,
    get_strangle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_preset_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRANGLE presets to delete."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRANGLE preset list for deletion")
    
    presets = await get_strangle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No STRANGLE presets found.\n\n"
            "Nothing to delete!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "🗑️ Delete STRANGLE Preset\n\n"
        "⚠️ This action cannot be undone!\n\n"
        "Select a preset to delete:",
        reply_markup=get_preset_list_keyboard(presets, action='delete'),
        parse_mode='HTML'
    )

@error_handler
async def strangle_preset_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation before deleting preset."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    preset = await get_strangle_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = preset.get('preset_name', 'Unnamed')
    
    await query.edit_message_text(
        f"🗑️ Delete Preset Confirmation\n\n"
        f"Are you sure you want to delete:\n\n"
        f"📌 {name}\n\n"
        f"⚠️ This action cannot be undone!",
        reply_markup=get_delete_confirmation_keyboard(preset_id, preset_type='strangle_preset'),
        parse_mode='HTML'
    )

@error_handler
async def strangle_preset_delete_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute preset deletion."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    preset = await get_strangle_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found or already deleted.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = preset.get('preset_name', 'Unnamed')
    
    result = await delete_strangle_trade_preset(user.id, preset_id)
    
    if result:
        log_user_action(user.id, f"Deleted STRANGLE preset: {name}")
        
        await query.edit_message_text(
            f"✅ Preset Deleted!\n\n"
            f"'{name}' has been successfully deleted.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete preset.\n\n"
            "Please try again.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )

__all__ = [
    'strangle_preset_delete_callback',
    'strangle_preset_delete_confirm_callback',
    'strangle_preset_delete_execute_callback',
]
