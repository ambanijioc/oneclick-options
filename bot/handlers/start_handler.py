"""
Start command handler - main menu.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import escape_html
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization, get_user_info
from bot.keyboards.main_menu import get_main_menu_keyboard
from database.operations.user_ops import get_or_create_user_settings

logger = setup_logger(__name__)


@error_handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command. Display main menu and create user settings if needed."""
    user = update.effective_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await update.message.reply_text(
            "❌ <b>Unauthorized Access</b>\n\n"
            "You are not authorized to use this bot.\n"
            "Please contact the administrator.",
            parse_mode='HTML'
        )
        return
    
    # Log user action
    log_user_action(user.id, "start_command", "User started bot")
    
    # Get or create user settings
    user_info = get_user_info(user)
    user_settings = await get_or_create_user_settings(
        user_id=user.id,
        username=user_info.get('username'),
        first_name=user_info.get('first_name'),
        last_name=user_info.get('last_name')
    )
    
    # Welcome message
    welcome_text = (
        f"👋 <b>Welcome {escape_html(user.first_name)}!</b>\n\n"
        f"🤖 <b>Telegram Trading Bot</b>\n"
        f"Automated options trading with Delta Exchange India\n\n"
        f"📊 Select an option from the menu below:"
    )
    
    # Send main menu
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )
    
    logger.info(f"User {user.id} started bot")


@error_handler
async def menu_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle 'Back to Main Menu' button.
    Handles BOTH 'menu_main' and 'back_to_main' callback patterns.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text(
            "❌ <b>Unauthorized Access</b>",
            parse_mode='HTML'
        )
        return
    
    # Clear any active state when returning to main menu
    await state_manager.clear_state(user.id)
    
    # Main menu text
    menu_text = (
        f"👋 <b>Welcome {escape_html(user.first_name)}!</b>\n\n"
        f"🤖 <b>Telegram Trading Bot</b>\n"
        f"Automated options trading with Delta Exchange India\n\n"
        f"📊 Select an option from the menu below:"
    )
    
    # Edit message with main menu
    await query.edit_message_text(
        menu_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "menu_main", "Returned to main menu")


def register_start_handler(application: Application):
    """Register start command and main menu handlers."""
    # /start command
    application.add_handler(CommandHandler("start", start_command))
    
    # Main menu callbacks - handles BOTH patterns
    application.add_handler(CallbackQueryHandler(
        menu_main_callback,
        pattern="^(menu_main|back_to_main)$"
    ))
    
    logger.info("Start handler registered")


if __name__ == "__main__":
    print("Start handler module loaded")
    
