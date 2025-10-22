"""
STRADDLE Strategy View Handler

Displays list of all STRADDLE strategies and their details.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.straddle_strategy_ops import get_straddle_strategies, get_straddle_strategy
from bot.keyboards.straddle_strategy_keyboards import (
    get_strategy_list_keyboard,
    get_straddle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def straddle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of all STRADDLE strategies."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRADDLE strategies list")
    
    strategies = await get_straddle_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No STRADDLE strategies found.\n\n"
            "Create your first strategy!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "📋 Your STRADDLE Strategies\n\n"
        f"Total: {len(strategies)} strategies\n\n"
        "Select a strategy to view details:",
        reply_markup=get_strategy_list_keyboard(strategies, action='view'),
        parse_mode='HTML'
    )

@error_handler
async def straddle_view_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed view of selected strategy."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_straddle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = strategy.get('strategy_name', 'Unnamed')
    description = strategy.get('description', 'No description')
    asset = strategy.get('asset', 'N/A')
    expiry = strategy.get('expiry', 'daily')
    direction = strategy.get('direction', 'long')
    lot_size = strategy.get('lot_size', 1)
    sl_trigger = strategy.get('stop_loss_trigger', 'N/A')
    sl_limit = strategy.get('stop_loss_limit', 'N/A')
    target_trigger = strategy.get('target_trigger')
    target_limit = strategy.get('target_limit')
    
    text = (
        f"📋 STRADDLE Strategy Details\n\n"
        f"📌 Name: {name}\n"
        f"📝 Description: {description}\n\n"
        f"⚙️ Configuration:\n"
        f"• Asset: {asset}\n"
        f"• Expiry: {expiry.capitalize()}\n"
        f"• Direction: {direction.capitalize()}\n"
        f"• Lot Size: {lot_size}\n\n"
        f"📊 Strike: ATM (At-The-Money)\n"
        f"Both Call + Put at same ATM strike\n\n"
        f"📊 Risk Management:\n"
        f"• SL Trigger: {sl_trigger}%\n"
        f"• SL Limit: {sl_limit}%\n"
    )
    
    if target_trigger is not None:
        text += (
            f"• Target Trigger: {target_trigger}%\n"
            f"• Target Limit: {target_limit}%\n"
        )
    else:
        text += "• Target: Not set\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_straddle_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'straddle_view_callback',
    'straddle_view_details_callback',
]
