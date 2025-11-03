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
    await query.answer()
    user = query.from_user
    
    logger.info(f"🎯 PRESET MAIN MENU - User {user.id}")
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized")
        return
    
    await query.edit_message_text(
        "📋 <b>MOVE Trade Presets</b>\n\n"
        "Choose an action:",
        reply_markup=get_move_preset_menu_keyboard(),
        parse_mode='HTML'
    )


# ============ NAVIGATION ============

@error_handler
async def move_back_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"🔙 BACK TO MAIN - User {user.id}")
    
    await state_manager.clear_state(user.id)
    
    await query.edit_message_text(
        "📋 <b>MOVE Trade Presets</b>\n\n"
        "Choose an action:",
        reply_markup=get_move_preset_menu_keyboard(),
        parse_mode='HTML'
    )


# ============ REGISTRATION ============

def register_menu_handlers(application: Application):
    """Register MENU preset handlers"""
    
    logger.info("📋 Registering MENU preset handlers...")
    
    try:
        application.add_handler(
            CallbackQueryHandler(move_preset_menu_callback, pattern="^move_preset_menu$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_back_main_callback, pattern="^move_back_main$"),
            group=10
        )
        
        logger.info("✅ MENU preset handlers registered")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering MENU handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_menu_handlers',
    'move_preset_menu_callback',
    'move_back_main_callback',
]
