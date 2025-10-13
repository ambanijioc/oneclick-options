"""
Help command handler.
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
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.confirmation_keyboards import get_back_keyboard

logger = setup_logger(__name__)


HELP_TEXT = """
<b>🤖 Telegram Trading Bot - Help</b>

<b>📋 Available Commands:</b>

<b>/start</b> - Start the bot and show main menu

<b>🔑 API Management:</b>
• Add, edit, and delete Delta Exchange API credentials
• Securely store encrypted API keys
• Manage multiple API accounts

<b>💰 Balance:</b>
• View wallet balance across all APIs
• Check available margin and unrealized PnL
• Monitor position margins

<b>📊 Positions:</b>
• View all open positions
• Set stop-loss and target prices
• Monitor position PnL and margin usage

<b>🎯 Stoploss & Target:</b>
• Set manual SL/target with custom percentages
• Use "SL to Cost" for breakeven protection
• Supports both bracket and limit orders

<b>📋 Orders:</b>
• View all open orders
• Cancel individual or all orders
• Monitor order status and fills

<b>📈 Trade History:</b>
• View recent trades (last 3 days)
• Track PnL, commissions, and win rate
• Get detailed trade statistics

<b>📑 List Options:</b>
• Browse BTC and ETH options
• View available expiries (Daily, Weekly, Monthly)
• Check strike prices and premiums

<b>🎲 Straddle Strategy:</b>
• ATM call and put options
• Configure lot size, SL, and target
• Save strategy presets for quick execution

<b>🎰 Strangle Strategy:</b>
• OTM call and put options
• Percentage or numeral strike selection
• Customizable strategy parameters

<b>⚡ Manual Trade:</b>
• Execute trades using saved presets
• Auto-calculate strikes based on spot price
• Review trade details before execution

<b>🤖 Auto Trade:</b>
• Schedule automated trade execution
• Set execution time in IST
• Enable/disable scheduled trades

<b>📚 Key Features:</b>
• Real-time price updates from Delta Exchange
• Automatic strike calculation (ATM/OTM)
• Multiple API support
• Encrypted credential storage
• Comprehensive error logging
• Position-aware order types

<b>⚠️ Important Notes:</b>
• Always review trade details before confirming
• Ensure sufficient balance before trading
• Monitor positions regularly
• Set appropriate stop-losses
• Test strategies with small sizes first

<b>🔗 Documentation:</b>
Delta Exchange API: https://docs.delta.exchange

<b>📞 Support:</b>
For issues or questions, contact the administrator.

<b>Version:</b> 1.0.0
<b>Status:</b> ✅ Active
"""


@error_handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await update.message.reply_text(
            "❌ You are not authorized to use this bot.",
            parse_mode='HTML'
        )
        return
    
    # Send help text
    await update.message.reply_text(
        HELP_TEXT,
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    
    log_user_action(user.id, "help_command", "Viewed help")


@error_handler
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle help menu callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text(
            "❌ You are not authorized to use this bot.",
            parse_mode='HTML'
        )
        return
    
    # Edit message with help text
    await query.edit_message_text(
        HELP_TEXT,
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    
    log_user_action(user.id, "help_callback", "Viewed help from menu")


def register_help_handler(application: Application):
    """
    Register help command handlers.
    
    Args:
        application: Bot application instance
    """
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
    print("\nHelp text preview:")
    print(HELP_TEXT)
      
