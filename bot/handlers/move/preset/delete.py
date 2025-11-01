# ============ FILE 2: bot/handlers/move/preset/delete.py ============

"""
MOVE Trade Preset Deletion Handler
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_preset_ops import (
    get_move_presets,
    get_move_preset,
    delete_move_preset
)
from bot.keyboards.move_preset_keyboards import (
    get_preset_list_keyboard,
    get_preset_menu_keyboard,
    get_confirm_delete_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_delete_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of presets to delete"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    presets = await get_move_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No presets found.",
            reply_markup=get_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "🗑️ Delete MOVE Preset\n\n"
        "Select a preset to delete:",
        reply_markup=get_preset_list_keyboard(presets, action='delete'),
        parse_mode='HTML'
    )

@error_handler
async def move_delete_preset_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Handle preset selection for deletion
    Callback format: move_delete_preset_{preset_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ FIX: Extract preset_id from "move_delete_preset_{ID}"
    parts = query.data.split('_', 3)  # ['move', 'delete', 'preset', 'ID']
    preset_id = parts[3] if len(parts) >= 4 else None
    
    logger.info(f"DELETE PRESET - callback_data: {query.data}")
    logger.info(f"DELETE PRESET - Extracted preset_id: {preset_id}")
    
    if not preset_id:
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_preset_menu_keyboard()
        )
        return
    
    preset = await get_move_preset(user.id, preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found.",
            reply_markup=get_preset_menu_keyboard()
        )
        return
    
    preset_name = preset.get('preset_name', 'Unknown')
    
    await query.edit_message_text(
        f"⚠️ Delete Preset: {preset_name}\n\n"
        f"Are you sure? This action cannot be undone.",
        reply_markup=get_confirm_delete_keyboard(preset_id, 'preset'),
        parse_mode='HTML'
    )

@error_handler
async def move_confirm_delete_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Confirm deletion
    Callback format: move_confirm_delete_preset_{preset_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ FIX: Extract preset_id
    parts = query.data.split('_', 4)  # ['move', 'confirm', 'delete', 'preset', 'ID']
    preset_id = parts[4] if len(parts) >= 5 else None
    
    if not preset_id:
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_preset_menu_keyboard()
        )
        return
    
    preset = await get_move_preset(user.id, preset_id)
    preset_name = preset.get('preset_name') if preset else 'Unknown'
    
    result = await delete_move_preset(user.id, preset_id)
    
    if result:
        await query.edit_message_text(
            f"✅ Preset '{preset_name}' deleted successfully.",
            reply_markup=get_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, f"Deleted MOVE preset: {preset_name}")
    else:
        await query.edit_message_text(
            "❌ Failed to delete preset.",
            reply_markup=get_preset_menu_keyboard()
        )
