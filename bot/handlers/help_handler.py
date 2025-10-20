"""
Help command handler - FIXED VERSION
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization

logger = setup_logger(__name__)

# ✅ SHORTENED HELP TEXT to avoid timeout
HELP_TEXT = """<b>📚 Help & Commands</b>

<b>🔑 API Management</b>
• Add/edit/delete Delta Exchange API keys
• Secure encrypted storage
• Multiple API support

<b>💰 Trading Features</b>
• Balance & Positions monitoring
• Manual & Auto trading
• Straddle/Strangle strategies
• MOVE strategies with SL to Cost

<b>📊 Market Data</b>
• List Options (BTC/ETH)
• Trade History
• Real-time position tracking

<b>⚠️ Important</b>
• Review trades before confirming
• Set appropriate stop-losses
• Test with small sizes first

<b>📖 Documentation</b>
Delta API: https://docs.delta.exchange

<b>Version:</b> 1.0.0 ✅"""


@error_handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user = update.effective_user
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized", parse_mode='HTML')
        return
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
    
    await update.message.reply_text(
        HELP_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    
    log_user_action(user.id, "help_command", "Viewed help")


@error_handler
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help menu callback."""
    query = update.callback_query
    await query.answer()  # ✅ Answer immediately to prevent timeout
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized", parse_mode='HTML')
        return
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
    
    try:
        await query.edit_message_text(
            HELP_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        log_user_action(user.id, "help_callback", "Viewed help from menu")
    except Exception as e:
        logger.error(f"Help error: {e}")
        await query.answer("❌ Error loading help", show_alert=True)


def register_help_handler(application: Application):
    """Register help command handlers."""
    # /help command
    application.add_handler(CommandHandler("help", help_command))
    
    # Help menu callback
    application.add_handler(CallbackQueryHandler(
        help_callback,
        pattern="^menu_help$"
    ))
    
    logger.info("Help handler registered")


if __name__ == "__main__":
    print("Help handler module loaded")
    
