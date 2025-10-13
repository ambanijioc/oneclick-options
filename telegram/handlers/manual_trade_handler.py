"""
Manual trade execution handler.
Handles manual strategy execution.
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_manual_trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show manual trade execution menu.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        query = update.callback_query
        
        message = (
            "▶️ **Manual Trade Execution**\n\n"
            "Execute your strategy presets manually.\n\n"
            "**Steps:**\n"
            "1. Select API\n"
            "2. Choose Strategy Type (Straddle/Strangle)\n"
            "3. Select Strategy Preset\n"
            "4. Review and Confirm\n"
            "5. Execute Trade\n\n"
            "This feature is coming soon!"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_manual_trade_menu] Displayed manual trade menu for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"[show_manual_trade_menu] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error showing manual trade menu.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Manual trade handler module loaded")
  
