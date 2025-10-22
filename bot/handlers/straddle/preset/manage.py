"""
STRADDLE Preset Management (Create, Edit, View, Delete)

Simplified preset handler for STRADDLE trade presets.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.straddle_trade_preset_ops import (
    create_straddle_preset,
    get_straddle_trade_presets,
    get_straddle_trade_preset_by_id,
    update_straddle_trade_preset,
    delete_straddle_trade_preset
)
from bot.keyboards.straddle_strategy_keyboards import (
    get_preset_list_keyboard,
    get_preset_edit_fields_keyboard,
    get_delete_confirmation_keyboard,
    get_straddle_menu_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard
)

logger = setup_logger(__name__)

# CREATE
@error_handler
async def straddle_preset_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start STRADDLE preset creation flow."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started adding STRADDLE preset")
    
    await state_manager.clear_state(user.id)
    await state_manager.set_state(user.id, 'straddle_preset_add_name')
    await state_manager.set_state_data(user.id, {'preset_type': 'straddle'})
    
    await query.edit_message_text(
        "📝 Add STRADDLE Preset\n\n"
        "Step 1/3: Preset Name\n\n"
        "Enter a name for your trading preset:\n\n"
        "Example: Quick Entry, Conservative Exit",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def straddle_preset_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save STRADDLE preset to database."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    data = await state_manager.get_state_data(user.id)
    
    try:
        preset_data = {
            'preset_name': data.get('name'),
            'description': data.get('description', ''),
            'entry_lots': data.get('entry_lots', 1),
            'exit_lots': data.get('exit_lots', 1)
        }
        
        result = await create_straddle_preset(user.id, preset_data)
        
        if not result:
            raise Exception("Failed to save preset to database")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created STRADDLE preset: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ STRADDLE Preset Created!\n\n"
            f"Name: {data.get('name')}\n"
            f"Entry Lots: {data.get('entry_lots', 1)}\n"
            f"Exit Lots: {data.get('exit_lots', 1)}\n\n"
            f"Preset has been saved successfully!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating STRADDLE preset: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error creating preset: {str(e)}\n\nPlease try again.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )

# VIEW
@error_handler
async def straddle_preset_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of all STRADDLE presets."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRADDLE presets list")
    
    presets = await get_straddle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No STRADDLE presets found.\n\nCreate your first preset!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "📋 Your STRADDLE Presets\n\n"
        f"Total: {len(presets)} presets\n\n"
        "Select a preset to view details:",
        reply_markup=get_preset_list_keyboard(presets, action='view'),
        parse_mode='HTML'
    )

# EDIT  
@error_handler
async def straddle_preset_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRADDLE presets to edit."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRADDLE preset list for editing")
    
    presets = await get_straddle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No STRADDLE presets found.\n\nCreate your first preset!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state(user.id, 'straddle_preset_edit_select')
    
    await query.edit_message_text(
        "📝 Edit STRADDLE Preset\n\nSelect a preset to edit:",
        reply_markup=get_preset_list_keyboard(presets, action='edit'),
        parse_mode='HTML'
    )

# DELETE
@error_handler
async def straddle_preset_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRADDLE presets to delete."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRADDLE preset list for deletion")
    
    presets = await get_straddle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No STRADDLE presets found.\n\nNothing to delete!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "🗑️ Delete STRADDLE Preset\n\n"
        "⚠️ This action cannot be undone!\n\n"
        "Select a preset to delete:",
        reply_markup=get_preset_list_keyboard(presets, action='delete'),
        parse_mode='HTML'
    )

@error_handler
async def straddle_preset_delete_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute preset deletion."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    preset = await get_straddle_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found or already deleted.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = preset.get('preset_name', 'Unnamed')
    result = await delete_straddle_trade_preset(user.id, preset_id)
    
    if result:
        log_user_action(user.id, f"Deleted STRADDLE preset: {name}")
        await query.edit_message_text(
            f"✅ Preset Deleted!\n\n'{name}' has been successfully deleted.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete preset.\n\nPlease try again.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )

__all__ = [
    'straddle_preset_create_callback',
    'straddle_preset_confirm_save_callback',
    'straddle_preset_view_callback',
    'straddle_preset_edit_callback',
    'straddle_preset_delete_callback',
    'straddle_preset_delete_execute_callback',
]
