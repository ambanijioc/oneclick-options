"""
MOVE Preset Edit Handler

Handles editing existing MOVE presets.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_trade_preset_ops import (
    get_move_trade_presets,
    get_move_trade_preset_by_id,
    update_move_trade_preset
)
from bot.keyboards.move_strategy_keyboards import (
    get_preset_list_keyboard,
    get_preset_edit_fields_keyboard,
    get_move_menu_keyboard,
    get_cancel_keyboard,
    get_continue_edit_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_preset_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of MOVE presets to edit."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested MOVE preset list for editing")
    
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No MOVE presets found.\n\n"
            "Create your first preset!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state(user.id, 'move_preset_edit_select')
    
    await query.edit_message_text(
        "📝 Edit MOVE Preset\n\n"
        "Select a preset to edit:",
        reply_markup=get_preset_list_keyboard(presets, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def move_preset_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    preset = await get_move_preset(user.id, preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_preset_id': preset_id,
        'preset_data': preset
    })
    await state_manager.set_state(user.id, 'move_preset_edit_field')
    
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
    'move_preset_edit_callback',
    'move_preset_edit_select_callback',
]
