"""
MOVE Strategy Menu Handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def move_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show MOVE strategy management menu"""
    query = update.callback_query
    await query.answer()
    
    try:
        keyboard = [
            [InlineKeyboardButton("➕ Add New Strategy", callback_data="move_add")],
            [InlineKeyboardButton("👁️ View Strategies", callback_data="move_view")],
            [InlineKeyboardButton("✏️ Edit Strategy", callback_data="move_edit_menu")],
            [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="move_delete_menu")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="🎯 <b>MOVE Strategy Management</b>\n\n"
                 "Choose an action:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        
        logger.info(f"User {update.effective_user.id} opened MOVE strategy menu")
        
    except Exception as e:
        logger.error(f"Error showing MOVE strategy menu: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try again."
        )
      
