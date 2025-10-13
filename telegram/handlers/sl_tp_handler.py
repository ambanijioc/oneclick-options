"""
Stop Loss and Take Profit handler.
Manages SL/TP for positions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_sl_tp_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show SL/TP management menu.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        query = update.callback_query
        
        message = (
            "🎯 **Stop Loss & Take Profit**\n\n"
            "Manage stop loss and take profit for your positions.\n\n"
            "First, view your positions to select one for SL/TP management.\n\n"
            "Use the 'Positions' menu to see your open positions."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_sl_tp_menu] Displayed SL/TP menu for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"[show_sl_tp_menu] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error showing SL/TP menu.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("SL/TP handler module loaded")
  
