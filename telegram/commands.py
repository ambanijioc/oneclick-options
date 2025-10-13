"""
Telegram bot command handlers.
Handles /start, /help, and other slash commands.
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import is_user_authorized
from logger import logger, log_function_call


@log_function_call
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    Display welcome message and main menu.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user = update.effective_user
        
        # Check authorization
        if not is_user_authorized(user.id):
            await update.message.reply_text(
                "❌ Unauthorized Access\n\n"
                "You are not authorized to use this bot. "
                "Please contact the administrator."
            )
            logger.warning(f"[start_command] Unauthorized access attempt by user {user.id}")
            return
        
        # Welcome message
        welcome_text = (
            f"👋 Welcome {user.first_name}!\n\n"
            "🤖 **Delta Exchange Trading Bot**\n\n"
            "I can help you automate options trading on Delta Exchange India. "
            "Use the menu below to get started.\n\n"
            "💡 Tip: Use /help to see all available commands."
        )
        
        # Get main menu keyboard
        keyboard = get_main_menu_keyboard()
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[start_command] User {user.id} started bot")
        
    except Exception as e:
        logger.error(f"[start_command] Error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@log_function_call
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command.
    Display help information and available commands.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user = update.effective_user
        
        # Check authorization
        if not is_user_authorized(user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        help_text = (
            "📖 **Help & Commands**\n\n"
            "**Main Features:**\n"
            "• Manage API - Add/edit Delta Exchange API credentials\n"
            "• Balance - View account balance and margin\n"
            "• Positions - View and manage open positions\n"
            "• Orders - View open orders and order history\n"
            "• Trade History - View past trades and PnL\n\n"
            "**Strategy Features:**\n"
            "• List Options - Browse available options contracts\n"
            "• Straddle Strategy - Create ATM straddle presets\n"
            "• Strangle Strategy - Create OTM strangle presets\n"
            "• Manual Trade - Execute strategy manually\n"
            "• Auto Trade - Schedule automatic executions\n\n"
            "**Commands:**\n"
            "/start - Show main menu\n"
            "/help - Show this help message\n\n"
            "**Stop Loss & Take Profit:**\n"
            "• Set SL/TP manually with trigger and limit percentages\n"
            "• Use 'SL to Cost' to move stop loss to entry price\n"
            "• Different order types for long/short positions\n\n"
            "**Support:**\n"
            "For issues or questions, contact the administrator.\n\n"
            "💡 Use the inline keyboard buttons to navigate!"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
        
        logger.info(f"[help_command] User {user.id} requested help")
        
    except Exception as e:
        logger.error(f"[help_command] Error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


if __name__ == "__main__":
    print("Telegram command handlers module loaded")
    print("Available commands: /start, /help")
  
