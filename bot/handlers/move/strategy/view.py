"""
MOVE Strategy View Handler
Displays strategies as inline keyboard → Shows details with Edit/Delete/Back buttons.
Author: Ambani Jio
Date: 2025-11-02
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import get_move_strategies, get_move_strategy
from bot.keyboards.move_strategy_keyboards import (
    get_strategies_list_keyboard,
    get_strategy_details_keyboard,
    get_cancel_keyboard
)

logger = setup_logger(__name__)


@error_handler
async def view_strategies_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ STEP 1: Display all strategies as inline keyboard buttons
    Callback: move_view_list
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "move_view_list", "Viewing strategy list")
    
    # Fetch all strategies for this user
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📊 <b>Your MOVE Strategies</b>\n\n"
            "❌ No strategies found.\n\n"
            "💡 Create your first strategy to get started!",
            reply_markup=get_cancel_keyboard(),  # Use keyboard function
            parse_mode='HTML'
        )
        logger.info(f"User {user.id}: No strategies found")
        return
    
    # Use keyboard builder function
    await query.edit_message_text(
        "📊 <b>Your MOVE Strategies</b>\n\n"
        "✅ Select a strategy to view details:",
        reply_markup=get_strategies_list_keyboard(strategies),
        parse_mode='HTML'
    )
    
    logger.info(f"✅ User {user.id}: Displayed {len(strategies)} strategies")


@error_handler
async def view_strategy_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ STEP 2: Display full strategy details with Edit/Delete/Back buttons
    Callback: move_view_strategy_{strategy_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract strategy_id from callback
    callback_data = query.data  # e.g., "move_view_strategy_abc123"
    prefix = "move_view_strategy_"
    
    if not callback_data.startswith(prefix):
        logger.error(f"❌ Invalid callback: {callback_data}")
        await query.edit_message_text(
            "❌ Invalid request.\n\n"
            "This might be an expired button. Please try again.",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    strategy_id = callback_data[len(prefix):]
    
    if not strategy_id:
        logger.error(f"❌ Empty strategy ID from callback: {callback_data}")
        await query.edit_message_text(
            "❌ Invalid strategy ID.",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    # Fetch strategy from database
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        logger.warning(f"❌ Strategy {strategy_id} not found for user {user.id}")
        await query.edit_message_text(
            "❌ Strategy not found or has been deleted.",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    log_user_action(user.id, f"view_strategy_{strategy_id}", 
                   f"Viewed: {strategy.get('strategy_name')}")
    
    # Format strategy details
    message = format_strategy_details(strategy)
    
    # Use keyboard builder function
    await query.edit_message_text(
        message,
        reply_markup=get_strategy_details_keyboard(strategy_id),
        parse_mode='HTML'
    )
    
    logger.info(f"✅ User {user.id}: Displayed strategy {strategy_id} details")


def format_strategy_details(strategy: dict) -> str:
    """
    ✅ Format strategy details into readable HTML message
    Shows ALL available information about the strategy
    """
    # Basic Info
    name = strategy.get('strategy_name', 'Unnamed')
    description = strategy.get('description', 'No description')
    asset = strategy.get('asset', 'N/A')
    expiry = strategy.get('expiry', 'daily').capitalize()
    direction = strategy.get('direction', 'N/A').upper()
    is_active = strategy.get('is_active', False)
    
    # Configuration
    atm_offset = strategy.get('atm_offset', 0)
    lot_size = strategy.get('lot_size', 'N/A')
    
    # Risk Management
    sl_trigger = strategy.get('sl_trigger_percent', 'N/A')
    sl_limit = strategy.get('sl_limit_percent', 'N/A')
    target_trigger = strategy.get('target_trigger_percent', 'N/A')
    target_limit = strategy.get('target_limit_percent', 'N/A')
    
    # Metadata
    created_at = strategy.get('created_at', 'N/A')
    updated_at = strategy.get('updated_at', 'N/A')
    
    # Status indicator
    status = '🟢 <b>ACTIVE</b>' if is_active else '⚫ <b>INACTIVE</b>'
    
    # Build detailed message
    message = (
        f"📊 <b>Strategy: {name}</b>\n\n"
        
        f"<b>📋 Basic Information</b>\n"
        f"├─ Description: <i>{description}</i>\n"
        f"├─ Status: {status}\n"
        f"├─ Asset: <code>{asset}</code>\n"
        f"├─ Created: {created_at}\n"
        f"└─ Last Updated: {updated_at}\n\n"
        
        f"<b>⚙️ Strategy Configuration</b>\n"
        f"├─ Expiry: <code>{expiry}</code>\n"
        f"├─ Direction: <code>{direction}</code>\n"
        f"├─ ATM Offset: <code>{atm_offset:+d}</code>\n"
        f"└─ Lot Size: <code>{lot_size}</code>\n\n"
        
        f"<b>🛡️ Stop Loss Management</b>\n"
        f"├─ Trigger: <b>{sl_trigger}%</b>\n"
        f"└─ Limit: <b>{sl_limit}%</b>\n\n"
        
        f"<b>🎯 Target Management</b>\n"
    )
    
    if target_trigger != 'N/A':
        message += (
            f"├─ Trigger: <b>{target_trigger}%</b>\n"
            f"└─ Limit: <b>{target_limit}%</b>"
        )
    else:
        message += "└─ <i>Target not configured</i>"
    
    return message


__all__ = [
    'view_strategies_list',
    'view_strategy_details',
    'format_strategy_details',
]
