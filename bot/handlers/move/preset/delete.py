"""
MOVE Trade Preset - Delete Handlers
Handles preset deletion functionality.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from database.operations.move_preset_ops import (
    get_preset_details,
    delete_move_preset,
)
from bot.keyboards.move_preset_keyboards import (
    get_preset_list_keyboard,
    get_delete_confirmation_keyboard,
    get_move_preset_menu_keyboard,
)

logger = setup_logger(__name__)


# ============ DELETE PRESET FLOW ============

@error_handler
async def move_preset_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DELETE: Show list of presets"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"🗑️ DELETE PRESET LIST - User {user.id}")
    
    keyboard = await get_preset_list_keyboard(user.id, action="delete")
    
    await query.edit_message_text(
        "🗑️ <b>Delete Presets</b>\n\n"
        "Select a preset to delete:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@error_handler
async def move_preset_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DELETE: Show delete confirmation"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract preset ID from callback
    callback = query.data  # "move_preset_delete_{preset_id}"
    preset_id = callback.split('_')[-1]
    
    logger.info(f"⚠️ DELETE CONFIRM - Preset {preset_id}")
    
    preset = await get_preset_details(user.id, preset_id)
    
    if not preset:
        await query.answer("❌ Preset not found", show_alert=True)
        return
    
    await query.edit_message_text(
        f"⚠️ <b>Delete Preset?</b>\n\n"
        f"<b>Name:</b> {preset['name']}\n\n"
        f"This action cannot be undone!",
        reply_markup=get_delete_confirmation_keyboard(preset_id),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_delete_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DELETE: Execute delete"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract preset ID from callback
    callback = query.data  # "move_preset_delete_confirm_{preset_id}"
    preset_id = callback.split('_')[-1]
    
    logger.info(f"🗑️ DELETE EXECUTING - Preset {preset_id}")
    
    result = await delete_move_preset(user.id, preset_id)
    
    if result:
        logger.info(f"✅ Preset deleted: {preset_id}")
        log_user_action(user.id, f"Deleted preset: {preset_id}")
        
        await query.edit_message_text(
            "✅ <b>Preset deleted successfully!</b>",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        logger.error(f"❌ Failed to delete preset")
        await query.edit_message_text(
            "❌ <b>Failed to delete preset</b>",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )


# ============ REGISTRATION ============

def register_delete_handlers(application: Application):
    """Register DELETE preset handlers"""
    
    logger.info("🗑️ Registering DELETE preset handlers...")
    
    try:
        application.add_handler(
            CallbackQueryHandler(move_preset_delete_list_callback, pattern="^move_preset_delete_list$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_delete_confirm_callback, pattern="^move_preset_delete_[a-z0-9-]+$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_delete_execute_callback, pattern="^move_preset_delete_confirm_.*"),
            group=10
        )
        
        logger.info("✅ DELETE preset handlers registered")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering DELETE handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_delete_handlers',
    'move_preset_delete_list_callback',
    'move_preset_delete_confirm_callback',
    'move_preset_delete_execute_callback',
]
