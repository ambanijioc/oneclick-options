"""
STRANGLE Strategy Delete Handler

Handles safe deletion of STRANGLE strategies with confirmation.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_strategy_ops import (
    get_strangle_strategies,
    get_strangle_strategy,
    delete_strangle_strategy
)
from bot.keyboards.strangle_strategy_keyboards import (
    get_strategy_list_keyboard,
    get_delete_confirmation_keyboard,
    get_strangle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRANGLE strategies to delete."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRANGLE strategy list for deletion")
    
    strategies = await get_strangle_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No STRANGLE strategies found.\n\n"
            "Nothing to delete!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "🗑️ Delete STRANGLE Strategy\n\n"
        "⚠️ This action cannot be undone!\n\n"
        "Select a strategy to delete:",
        reply_markup=get_strategy_list_keyboard(strategies, action='delete'),
        parse_mode='HTML'
    )

@error_handler
async def strangle_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation before deleting strategy."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_strangle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = strategy.get('strategy_name', 'Unnamed')
    
    await query.edit_message_text(
        f"🗑️ Delete Strategy Confirmation\n\n"
        f"Are you sure you want to delete:\n\n"
        f"📌 {name}\n\n"
        f"⚠️ This action cannot be undone!",
        reply_markup=get_delete_confirmation_keyboard(strategy_id),
        parse_mode='HTML'
    )

@error_handler
async def strangle_delete_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute strategy deletion."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_strangle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found or already deleted.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = strategy.get('strategy_name', 'Unnamed')
    
    result = await delete_strangle_strategy(user.id, strategy_id)
    
    if result:
        log_user_action(user.id, f"Deleted STRANGLE strategy: {name}")
        
        await query.edit_message_text(
            f"✅ Strategy Deleted!\n\n"
            f"'{name}' has been successfully deleted.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete strategy.\n\n"
            "Please try again.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )

__all__ = [
    'strangle_delete_callback',
    'strangle_delete_confirm_callback',
    'strangle_delete_execute_callback',
]
