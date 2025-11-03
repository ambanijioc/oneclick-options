"""
MOVE Trade Preset - Menu & Navigation Handlers
Handles main menu and navigation callbacks.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from bot.utils.logger import setup_logger
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.move_preset_keyboards import get_move_preset_menu_keyboard

logger = setup_logger(__name__)


# ============ MAIN MENU ============

@error_handler
async def move_preset_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main MOVE Trade Presets menu"""
    query = update.callback_query
    
    logger.info(f"🎯 PRESET MAIN MENU CALLED - callback_data: {query.data}")
    
    try:
        await query.answer()
        logger.info("✅ Callback answer sent")
    except Exception as e:
        logger.error(f"❌ Failed to answer callback: {e}")
    
    user = query.from_user
    logger.info(f"👤 User {user.id} ({user.first_name}) accessing preset menu")
    
    if not await check_user_authorization(user):
        logger.warning(f"⛔ Unauthorized user {user.id}")
        await query.edit_message_text("❌ Unauthorized")
        return
    
    try:
        await query.edit_message_text(
            "📋 <b>MOVE Trade Presets</b>\n\n"
            "Choose an action:",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        logger.info("✅ Preset menu displayed successfully")
    except Exception as e:
        logger.error(f"❌ Error editing message: {e}", exc_info=True)
        await query.answer("❌ Failed to load menu", show_alert=True)


# ============ NAVIGATION ============

@error_handler
async def move_back_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    
    logger.info(f"🔙 BACK TO MAIN - callback_data: {query.data}")
    
    try:
        await query.answer()
        logger.info("✅ Callback answer sent")
    except Exception as e:
        logger.error(f"❌ Failed to answer callback: {e}")
    
    user = query.from_user
    logger.info(f"👤 User {user.id} going back to main menu")
    
    try:
        await state_manager.clear_state(user.id)
        logger.info(f"✅ State cleared for user {user.id}")
    except Exception as e:
        logger.error(f"⚠️ Error clearing state: {e}")
    
    try:
        await query.edit_message_text(
            "📋 <b>MOVE Trade Presets</b>\n\n"
            "Choose an action:",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        logger.info("✅ Preset menu displayed successfully after back")
    except Exception as e:
        logger.error(f"❌ Error editing message: {e}", exc_info=True)
        await query.answer("❌ Failed to load menu", show_alert=True)


# ============ REGISTRATION ============

def register_menu_handlers(application: Application):
    """Register MENU preset handlers"""
    
    logger.info("📋 Registering MENU preset handlers (Group 15)...")
    
    try:
        # ✅ FIXED: Register at Group 15 (MOVE Presets group)
        application.add_handler(
            CallbackQueryHandler(move_preset_menu_callback, pattern="^move_preset_menu$"),
            group=15  # ✅ CORRECT GROUP FOR PRESETS
        )
        logger.info("✅ move_preset_menu callback registered (Group 15)")
        
        application.add_handler(
            CallbackQueryHandler(move_back_main_callback, pattern="^move_back_main$"),
            group=15  # ✅ CORRECT GROUP FOR PRESETS
        )
        logger.info("✅ move_back_main callback registered (Group 15)")
        
        logger.info("✅ ALL MENU preset handlers registered successfully (Group 15)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering MENU handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_menu_handlers',
    'move_preset_menu_callback',
    'move_back_main_callback',
]
