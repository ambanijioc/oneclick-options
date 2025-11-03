"""
MOVE Trade Preset - View Handlers
Handles preset viewing functionality.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from bot.utils.logger import setup_logger
from bot.utils.error_handler import error_handler
from database.operations.move_preset_ops import get_preset_details
from bot.keyboards.move_preset_keyboards import (
    get_preset_list_keyboard,
    get_preset_details_keyboard,
)

logger = setup_logger(__name__)


# ============ VIEW PRESET FLOW ============

@error_handler
async def move_preset_view_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """VIEW: Show list of presets"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"👁️ VIEW PRESET LIST - User {user.id}")
    
    keyboard = await get_preset_list_keyboard(user.id, action="view")
    
    await query.edit_message_text(
        "👁️ <b>View Presets</b>\n\n"
        "Select a preset to view details:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@error_handler
async def move_preset_view_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """VIEW: Show preset details"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract preset ID from callback
    callback = query.data  # "move_preset_view_{preset_id}"
    preset_id = callback.split('_')[-1]
    
    logger.info(f"📊 VIEW PRESET DETAILS - Preset {preset_id}")
    
    preset = await get_preset_details(user.id, preset_id)
    
    if not preset:
        await query.answer("❌ Preset not found", show_alert=True)
        return
    
    details_text = (
        f"📊 <b>{preset['name']}</b>\n\n"
        f"<b>Description:</b> {preset.get('description', 'N/A')}\n"
        f"<b>API:</b> {preset.get('api_name', 'N/A')}\n"
        f"<b>Strategy:</b> {preset.get('strategy_name', 'N/A')}\n"
        f"<b>SL Trigger:</b> {preset.get('sl_trigger_percent', 'N/A')}%\n"
        f"<b>SL Limit:</b> {preset.get('sl_limit_percent', 'N/A')}%\n"
        f"<b>Target Trigger:</b> {preset.get('target_trigger_percent', 'N/A')}%\n"
        f"<b>Target Limit:</b> {preset.get('target_limit_percent', 'N/A')}%\n"
        f"<b>Created:</b> {preset.get('created_at', 'N/A')}"
    )
    
    await query.edit_message_text(
        details_text,
        reply_markup=get_preset_details_keyboard(),
        parse_mode='HTML'
    )


# ============ REGISTRATION ============

def register_view_handlers(application: Application):
    """Register VIEW preset handlers"""
    
    logger.info("👁️ Registering VIEW preset handlers...")
    
    try:
        application.add_handler(
            CallbackQueryHandler(move_preset_view_list_callback, pattern="^move_preset_view_list$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_view_details_callback, pattern="^move_preset_view_.*"),
            group=10
        )
        
        logger.info("✅ VIEW preset handlers registered")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering VIEW handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_view_handlers',
    'move_preset_view_list_callback',
    'move_preset_view_details_callback',
]
