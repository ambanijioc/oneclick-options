"""
Options listing handler.
Displays available options contracts.
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram.keyboards import get_asset_selection_keyboard, get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_options_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show options menu with asset selection.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        query = update.callback_query
        
        message = (
            "📝 **List Options**\n\n"
            "Select an asset to view available options contracts:"
        )
        
        keyboard = get_asset_selection_keyboard()
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_options_menu] Displayed options menu for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"[show_options_menu] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error showing options menu.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Options handler module loaded")
  
