"""
STRANGLE Preset Edit Handler

Handles editing existing STRANGLE trade presets.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_trade_preset_ops import (
    get_strangle_trade_presets,
    get_strangle_trade_preset_by_id,
    update_strangle_trade_preset
)
from bot.keyboards.strangle_strategy_keyboards import (
    get_preset_list_keyboard,
    get_preset_edit_fields_keyboard,
    get_strangle_menu_keyboard,
    get_cancel_keyboard,
    get_continue_edit_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_preset_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRANGLE presets to edit."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRANGLE preset list for editing")
    
    presets = await get_strangle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No STRANGLE presets found.\n\n"
            "Create your first preset!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state(user.id, 'strangle_preset_edit_select')
    
    await query.edit_message_text(
        "📝 Edit STRANGLE Preset\n\n"
        "Select a preset to edit:",
        reply_markup=get_preset_list_keyboard(presets, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def strangle_preset_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection for editing."""
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
    
    await state_manager.set_state_data(user.id, {
        'editing_preset_id': preset_id,
        'preset_data': preset
    })
    await state_manager.set_state(user.id, 'strangle_preset_edit_field')
    
    await query.edit_message_text(
        f"📝 Edit Preset: {preset.get('preset_name')}\n\n"
        f"Current Settings:\n"
        f"• Entry Lots: {preset.get('entry_lots', 1)}\n"
        f"• Exit Lots: {preset.get('exit_lots', 1)}\n\n"
        f"What would you like to edit?",
        reply_markup=get_preset_edit_fields_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_preset_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    field = query.data.split('_')[-1]
    
    await state_manager.set_state_data(user.id, {'editing_field': field})
    data = await state_manager.get_state_data(user.id)
    preset = data.get('preset_data', {})
    
    if field == 'name':
        await state_manager.set_state(user.id, 'strangle_preset_edit_name')
        await query.edit_message_text(
            f"📝 Edit Preset Name\n\n"
            f"Current: {preset.get('preset_name')}\n\n"
            f"Enter new name:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'entry_lots':
        await state_manager.set_state(user.id, 'strangle_preset_edit_entry_lots')
        await query.edit_message_text(
            f"📝 Edit Entry Lots\n\n"
            f"Current: {preset.get('entry_lots', 1)}\n\n"
            f"Enter new entry lot size (1-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'exit_lots':
        await state_manager.set_state(user.id, 'strangle_preset_edit_exit_lots')
        await query.edit_message_text(
            f"📝 Edit Exit Lots\n\n"
            f"Current: {preset.get('exit_lots', 1)}\n\n"
            f"Enter new exit lot size (1-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def strangle_preset_update_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update preset field after text input."""
    user = update.effective_user
    text = update.message.text
    
    data = await state_manager.get_state_data(user.id)
    preset_id = data.get('editing_preset_id')
    editing_field = data.get('editing_field')
    
    # Validate and prepare update
    update_data = {}
    
    if editing_field == 'name':
        update_data['preset_name'] = text
    elif editing_field in ['entry_lots', 'exit_lots']:
        try:
            lot_value = int(text)
            if lot_value < 1 or lot_value > 100:
                raise ValueError("Lot size must be between 1-100")
            update_data[editing_field] = lot_value
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Invalid input: {str(e)}\n\nPlease try again.",
                parse_mode='HTML'
            )
            return
    
    # Update preset
    result = await update_strangle_trade_preset(user.id, preset_id, update_data)
    
    if result:
        log_user_action(user.id, f"Updated STRANGLE preset {preset_id} - {editing_field}")
        
        keyboard = get_continue_edit_keyboard(preset_id, preset_type='strangle_preset')
        
        await update.message.reply_text(
            f"✅ Preset Updated!\n\n"
            f"{editing_field.replace('_', ' ').title()} changed successfully!\n\n"
            f"Continue editing or return to menu?",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update preset.",
            reply_markup=get_strangle_menu_keyboard()
        )

@error_handler
async def strangle_preset_continue_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continue editing the same preset."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    preset = await get_strangle_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found.",
            reply_markup=get_strangle_menu_keyboard()
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_preset_id': preset_id,
        'preset_data': preset
    })
    await state_manager.set_state(user.id, 'strangle_preset_edit_field')
    
    await query.edit_message_text(
        f"📝 Edit Preset: {preset.get('preset_name')}\n\n"
        f"Current Settings:\n"
        f"• Entry Lots: {preset.get('entry_lots', 1)}\n"
        f"• Exit Lots: {preset.get('exit_lots', 1)}\n\n"
        f"What would you like to edit?",
        reply_markup=get_preset_edit_fields_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'strangle_preset_edit_callback',
    'strangle_preset_edit_select_callback',
    'strangle_preset_edit_field_callback',
    'strangle_preset_update_field_callback',
    'strangle_preset_continue_edit_callback',
]
