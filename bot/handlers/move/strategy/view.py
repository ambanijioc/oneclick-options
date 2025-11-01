"""
MOVE Strategy View Handler

Displays detailed MOVE strategy information and status.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    get_move_strategies,
    get_move_strategy
)
from bot.keyboards.move_strategy_keyboards import (
    get_strategy_actions_keyboard,
    get_move_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of MOVE strategies to view"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Viewed MOVE strategy list")
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No MOVE strategies found.\n\n"
            "Create your first strategy!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # ✅ FIX: Build strategy list with proper formatting
    strategy_list = "📊 Your MOVE Strategies:\n\n"
    for idx, strat in enumerate(strategies, 1):
        name = strat.get('strategy_name', 'Unnamed')
        asset = strat.get('asset', 'N/A')
        status = '🟢' if strat.get('is_active', False) else '⚫'
        strategy_list += f"{idx}. {status} {name} ({asset})\n"
    
    strategy_list += "\n✅ Tap a strategy to view details"
    
    await query.edit_message_text(
        strategy_list,
        reply_markup=get_strategy_list_keyboard(strategies, action='view'),
        parse_mode='HTML'
    )

@error_handler
async def move_view_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Display detailed MOVE strategy information
    Callback format: move_view_{strategy_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ FIX: Extract strategy_id from "move_view_{ID}"
    parts = query.data.split('_')  # ['move', 'view', 'ID']
    strategy_id = parts[2] if len(parts) >= 3 else None
    
    logger.info(f"VIEW DETAIL - Raw callback_data: {query.data}")
    logger.info(f"VIEW DETAIL - Extracted strategy_id: {strategy_id}")
    
    if not strategy_id:
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    log_user_action(user.id, f"Viewed strategy: {strategy.get('strategy_name')}")
    
    # ✅ FIX: Format strategy details
    message = format_strategy_details(strategy)
    
    await query.edit_message_text(
        message,
        reply_markup=get_strategy_actions_keyboard(strategy_id),
        parse_mode='HTML'
    )

def format_strategy_details(strategy: dict) -> str:
    """
    ✅ FIX: Format strategy dict into readable message
    """
    name = strategy.get('strategy_name', 'Unnamed')
    description = strategy.get('description', 'No description')
    asset = strategy.get('asset', 'N/A')
    expiry = strategy.get('expiry', 'daily').capitalize()
    direction = strategy.get('direction', 'N/A').capitalize()
    is_active = strategy.get('is_active', False)
    
    atm_offset = strategy.get('atm_offset', 0)
    lot_size = strategy.get('lot_size', 'N/A')
    
    sl_trigger = strategy.get('sl_trigger_percent', 'N/A')
    sl_limit = strategy.get('sl_limit_percent', 'N/A')
    target_trigger = strategy.get('target_trigger_percent', 'N/A')
    target_limit = strategy.get('target_limit_percent', 'N/A')
    
    created_at = strategy.get('created_at', 'N/A')
    
    status = '🟢 Active' if is_active else '⚫ Inactive'
    
    message = (
        f"📊 <b>MOVE Strategy Details</b>\n\n"
        
        f"<b>Basic Info:</b>\n"
        f"• Name: {name}\n"
        f"• Description: {description}\n"
        f"• Status: {status}\n"
        f"• Created: {created_at}\n\n"
        
        f"<b>Configuration:</b>\n"
        f"• Asset: {asset}\n"
        f"• Expiry: {expiry}\n"
        f"• Direction: {direction}\n"
        f"• ATM Offset: {atm_offset:+d}\n"
        f"• Lot Size: {lot_size}\n\n"
        
        f"<b>Stop Loss:</b>\n"
        f"• Trigger: {sl_trigger}%\n"
        f"• Limit: {sl_limit}%\n\n"
        
        f"<b>Target:</b>\n"
        f"• Trigger: {target_trigger}%\n"
        f"• Limit: {target_limit}%\n\n"
        
        f"<b>Actions:</b>"
    )
    
    return message

@error_handler
async def move_list_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show summary of all MOVE strategies"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📊 No strategies created yet.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # ✅ FIX: Build summary table
    summary = "📋 <b>MOVE Strategy Summary</b>\n\n"
    
    active_count = sum(1 for s in strategies if s.get('is_active', False))
    inactive_count = len(strategies) - active_count
    
    summary += (
        f"<b>Overview:</b>\n"
        f"• Total Strategies: {len(strategies)}\n"
        f"• Active: {active_count}\n"
        f"• Inactive: {inactive_count}\n\n"
        
        f"<b>Strategies:</b>\n"
    )
    
    for strat in strategies:
        name = strat.get('strategy_name', 'Unnamed')
        asset = strat.get('asset', 'N/A')
        status = '🟢' if strat.get('is_active', False) else '⚫'
        summary += f"{status} {name} - {asset}\n"
    
    summary += (
        f"\n<i>Use View to see strategy details</i>"
    )
    
    await query.edit_message_text(
        summary,
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_strategy_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Get detailed status of a single strategy
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract from: move_status_{strategy_id}
    parts = query.data.split('_', 2)
    strategy_id = parts[2] if len(parts) >= 3 else None
    
    if not strategy_id:
        await query.edit_message_text("❌ Invalid request.")
        return
    
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    # ✅ FIX: Build status message
    status_msg = (
        f"📊 Strategy Status: {strategy.get('strategy_name')}\n\n"
        f"<b>Runtime Info:</b>\n"
    )
    
    is_active = strategy.get('is_active', False)
    status_msg += f"• Status: {'🟢 ACTIVE' if is_active else '⚫ INACTIVE'}\n"
    
    # Add runtime metrics if available
    if strategy.get('last_traded'):
        status_msg += f"• Last Trade: {strategy.get('last_traded')}\n"
    
    if strategy.get('pnl'):
        pnl = strategy.get('pnl')
        pnl_emoji = '📈' if pnl > 0 else '📉'
        status_msg += f"• P&L: {pnl_emoji} {pnl}\n"
    
    status_msg += f"\n<i>View details for full information</i>"
    
    await query.edit_message_text(
        status_msg,
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'move_view_callback',
    'move_view_detail_callback',
    'move_list_all_callback',
    'move_strategy_status',
    'format_strategy_details',
]
