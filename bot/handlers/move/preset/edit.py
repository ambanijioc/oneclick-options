"""
MOVE Trade Preset - Edit Handlers
Handles preset editing functionality.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from database.operations.move_preset_ops import (
    get_preset_details,
    update_move_preset,
)
from bot.keyboards.move_preset_keyboards import (
    get_preset_list_keyboard,
    get_preset_edit_options_keyboard,
    get_move_preset_menu_keyboard,
    get_cancel_keyboard,
)

logger = setup_logger(__name__)


# ============ EDIT PRESET FLOW ============

@error_handler
async def move_preset_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """EDIT: Show list of presets"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"✏️ EDIT PRESET LIST - User {user.id}")
    
    keyboard = await get_preset_list_keyboard(user.id, action="edit")
    
    await query.edit_message_text(
        "✏️ <b>Edit Presets</b>\n\n"
        "Select a preset to edit:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@error_handler
async def move_preset_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """EDIT: Show edit options for preset"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract preset ID from callback
    callback = query.data  # "move_preset_edit_{preset_id}"
    preset_id = callback.split('_')[-1]
    
    logger.info(f"✏️ EDIT PRESET - Preset {preset_id}")
    
    preset = await get_preset_details(user.id, preset_id)
    
    if not preset:
        await query.answer("❌ Preset not found", show_alert=True)
        return
    
    # Save preset ID to state
    await state_manager.set_state_data(user.id, {'editing_preset_id': preset_id, **preset})
    await state_manager.set_state(user.id, 'move_preset_edit_options')
    
    details_text = (
        f"✏️ <b>Edit: {preset['name']}</b>\n\n"
        f"<b>Name:</b> {preset['name']}\n"
        f"<b>Description:</b> {preset.get('description', 'None')}\n"
        f"<b>API:</b> {preset.get('api_name', 'N/A')}\n"
        f"<b>Strategy:</b> {preset.get('strategy_name', 'N/A')}\n"
        f"<b>SL Trigger:</b> {preset.get('sl_trigger_percent', 'N/A')}%\n"
        f"<b>SL Limit:</b> {preset.get('sl_limit_percent', 'N/A')}%\n"
        f"<b>Target Trigger:</b> {preset.get('target_trigger_percent', 'N/A')}%\n"
        f"<b>Target Limit:</b> {preset.get('target_limit_percent', 'N/A')}%\n\n"
        f"Select a field to edit:"
    )
    
    await query.edit_message_text(
        details_text,
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """EDIT: Select field to edit"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    callback = query.data  # "move_preset_edit_name", "move_preset_edit_sl_trigger", etc.
    field = callback.split('_')[-1]
    
    logger.info(f"✏️ EDIT FIELD - Field: {field}")
    
    # Map field to state and prompt
    field_prompts = {
        'name': ('move_preset_edit_name', "Enter new preset name:"),
        'description': ('move_preset_edit_description', "Enter new description (or skip):"),
        'api': ('move_preset_edit_api', "Select new API:"),
        'strategy': ('move_preset_edit_strategy', "Select new strategy:"),
        'sl_trigger': ('move_preset_edit_sl_trigger', "Enter new SL Trigger % (0-100):"),
        'sl_limit': ('move_preset_edit_sl_limit', "Enter new SL Limit % (0-100):"),
        'target_trigger': ('move_preset_edit_target_trigger', "Enter new Target Trigger % (0-100):"),
        'target_limit': ('move_preset_edit_target_limit', "Enter new Target Limit % (0-100):"),
    }
    
    if field not in field_prompts:
        await query.answer("❌ Invalid field", show_alert=True)
        return
    
    state, prompt = field_prompts[field]
    await state_manager.set_state(user.id, state)
    
    await query.edit_message_text(prompt, reply_markup=get_cancel_keyboard(), parse_mode='HTML')


@error_handler
async def move_preset_save_changes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """EDIT: Save all changes"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"💾 SAVE CHANGES - User {user.id}")
    
    data = await state_manager.get_state_data(user.id)
    preset_id = data.get('editing_preset_id')
    
    if not preset_id:
        await query.answer("❌ No preset selected", show_alert=True)
        return
    
    # Update preset in database
    result = await update_move_preset(
        user_id=user.id,
        preset_id=preset_id,
        name=data.get('name'),
        description=data.get('preset_description'),
        api_id=data.get('api_id'),
        strategy_id=data.get('strategy_id'),
        sl_trigger_percent=data.get('sl_trigger_percent'),
        sl_limit_percent=data.get('sl_limit_percent'),
        target_trigger_percent=data.get('target_trigger_percent'),
        target_limit_percent=data.get('target_limit_percent'),
    )
    
    if result:
        logger.info(f"✅ Changes saved for preset {preset_id}")
        log_user_action(user.id, f"Updated preset: {preset_id}")
        await query.edit_message_text(
            f"✅ <b>Preset updated successfully!</b>",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        logger.error(f"❌ Failed to save changes")
        await query.edit_message_text(
            "❌ <b>Failed to save changes</b>",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    
    await state_manager.clear_state(user.id)


# ============ REGISTRATION ============

def register_edit_handlers(application: Application):
    """Register EDIT preset handlers"""
    
    logger.info("✏️ Registering EDIT preset handlers...")
    
    try:
        application.add_handler(
            CallbackQueryHandler(move_preset_edit_list_callback, pattern="^move_preset_edit_list$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_edit_callback, pattern="^move_preset_edit_[a-z0-9-]+$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(
                move_preset_edit_field_callback,
                pattern="^move_preset_edit_(name|description|api|strategy|sl_trigger|sl_limit|target_trigger|target_limit)$"
            ),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_save_changes_callback, pattern="^move_preset_save_changes$"),
            group=10
        )
        
        logger.info("✅ EDIT preset handlers registered")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering EDIT handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_edit_handlers',
    'move_preset_edit_list_callback',
    'move_preset_edit_callback',
    'move_preset_edit_field_callback',
    'move_preset_save_changes_callback',
]
