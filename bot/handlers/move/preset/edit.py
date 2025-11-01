# ============ FILE 3: bot/handlers/move/preset/edit.py ============

"""
MOVE Trade Preset Edit Handler
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_preset_ops import (
    get_move_presets,
    get_move_preset,
    update_move_preset
)
from bot.keyboards.move_preset_keyboards import (
    get_preset_list_keyboard,
    get_edit_preset_fields_keyboard,
    get_preset_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_edit_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of presets to edit"""
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
        "📝 Edit MOVE Preset\n\n"
        "Select a preset to edit:",
        reply_markup=get_preset_list_keyboard(presets, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def move_edit_preset_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Handle preset selection for editing
    Callback format: move_edit_preset_{preset_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ FIX: Extract preset_id from "move_edit_preset_{ID}"
    parts = query.data.split('_', 3)  # ['move', 'edit', 'preset', 'ID']
    preset_id = parts[3] if len(parts) >= 4 else None
    
    logger.info(f"EDIT PRESET SELECT - callback_data: {query.data}")
    logger.info(f"EDIT PRESET SELECT - Extracted preset_id: {preset_id}")
    
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
    
    # Store preset in state
    await state_manager.set_state_data(user.id, {
        'editing_preset_id': preset_id,
        'preset_data': preset
    })
    
    preset_name = preset.get('preset_name', 'Unknown')
    
    await query.edit_message_text(
        f"📝 Edit Preset: {preset_name}\n\n"
        f"Current Settings:\n"
        f"• SL Trigger: {preset.get('sl_trigger_percent')}%\n"
        f"• SL Limit: {preset.get('sl_limit_percent')}%\n"
        f"• Target Trigger: {preset.get('target_trigger_percent', 'N/A')}%\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_preset_fields_keyboard(preset_id),
        parse_mode='HTML'
    )

@error_handler
async def move_edit_preset_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Handle field selection for editing
    Callback format: move_edit_preset_field_{preset_id}_{field_name}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ FIX: Extract preset_id and field from callback_data
    parts = query.data.split('_', 5)  # ['move', 'edit', 'preset', 'field', 'ID', 'field_name']
    preset_id = parts[4] if len(parts) >= 5 else None
    field = parts[5] if len(parts) >= 6 else None
    
    logger.info(f"EDIT PRESET FIELD - callback_data: {query.data}")
    logger.info(f"EDIT PRESET FIELD - preset_id: {preset_id}, field: {field}")
    
    if not preset_id or not field:
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_preset_menu_keyboard()
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_preset_id': preset_id,
        'editing_field': field
    })
    
    # Set appropriate state for input handling
    await state_manager.set_state(user.id, f'move_edit_preset_{field}')
    
    field_display = field.replace('_', ' ').title()
    
    await query.edit_message_text(
        f"📝 Edit {field_display}\n\n"
        f"Enter new value (0-100):",
        parse_mode='HTML'
    )

@error_handler
async def handle_move_edit_preset_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field value input for preset edit"""
    user = update.effective_user
    text = update.message.text.strip()
    
    data = await state_manager.get_state_data(user.id)
    preset_id = data.get('editing_preset_id')
    field = data.get('editing_field')
    
    try:
        value = float(text)
        if not (0 <= value <= 100):
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        await update.message.reply_text(
            "❌ Please enter a valid number (0-100)"
        )
        return
    
    # Map field to database column
    field_mapping = {
        'sl_trigger_percent': 'sl_trigger_percent',
        'sl_limit_percent': 'sl_limit_percent',
        'target_trigger_percent': 'target_trigger_percent'
    }
    
    db_field = field_mapping.get(field)
    
    if not db_field:
        await update.message.reply_text("❌ Invalid field.")
        return
    
    result = await update_move_preset(user.id, preset_id, {db_field: value})
    
    if result:
        await update.message.reply_text(
            f"✅ Preset updated!\n\n"
            f"{field.replace('_', ' ').title()}: {value}%",
            reply_markup=get_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, f"Updated MOVE preset field: {field}")
    else:
        await update.message.reply_text(
            "❌ Failed to update preset.",
            reply_markup=get_preset_menu_keyboard()
        )

__all__ = [
    'move_create_preset_callback',
    'handle_move_preset_name',
    'handle_move_preset_sl_trigger',
    'handle_move_preset_sl_limit',
    'handle_move_preset_target',
    'move_delete_preset_callback',
    'move_delete_preset_select_callback',
    'move_confirm_delete_preset_callback',
    'move_edit_preset_callback',
    'move_edit_preset_select_callback',
    'move_edit_preset_field_callback',
    'handle_move_edit_preset_field',
]
