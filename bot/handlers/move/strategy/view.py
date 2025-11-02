"""
MOVE Strategy View Handler - Nested Structure
Displays detailed MOVE strategy information and status.
Routes through callbacks in nested structure.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    get_move_strategies,
    get_move_strategy
)

logger = setup_logger(__name__)


def get_strategy_list_keyboard(strategies: list, action: str = 'view') -> InlineKeyboardMarkup:
    """Build keyboard for strategy list."""
    keyboard = []
    
    for strat in strategies:
        strategy_id = str(strat.get('id', strat.get('_id', '')))
        name = strat.get('strategy_name', 'Unnamed')
        
        # ✅ Fixed callback format
        callback_data = f"move_view_strategy_{strategy_id}"
        
        keyboard.append([
            InlineKeyboardButton(
                f"📋 {name}",
                callback_data=callback_data
            )
        ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data="move_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Show list of MOVE strategies to view - Entry point."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "move_view_list", "Viewed strategy list")
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📊 <b>Your MOVE Strategies</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create your first strategy to get started!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_menu")]
            ]),
            parse_mode='HTML'
        )
        logger.info(f"User {user.id}: No strategies found")
        return
    
    # Build strategy list
    strategy_list = "📊 <b>Your MOVE Strategies</b>\n\n"
    for idx, strat in enumerate(strategies, 1):
        name = strat.get('strategy_name', 'Unnamed')
        asset = strat.get('asset', 'N/A')
        status = '🟢' if strat.get('is_active', False) else '⚫'
        strategy_list += f"{idx}. {status} <code>{name}</code> ({asset})\n"
    
    strategy_list += "\n✅ <i>Select a strategy to view details</i>"
    
    await query.edit_message_text(
        strategy_list,
        reply_markup=get_strategy_list_keyboard(strategies, action='view'),
        parse_mode='HTML'
    )
    logger.info(f"User {user.id}: Listed {len(strategies)} strategies")


@error_handler
async def move_view_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ Display detailed MOVE strategy information
    Callback format: move_view_strategy_{strategy_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ Extract strategy_id from "move_view_strategy_{ID}"
    callback_data = query.data
    
    logger.info(f"👤 USER {user.id} - VIEW STRATEGY DETAIL")
    logger.info(f"  📍 Raw callback_data: {callback_data}")
    
    # ✅ Safe extraction with prefix matching
    prefix = "move_view_strategy_"
    if not callback_data.startswith(prefix):
        logger.error(f"❌ Invalid callback prefix. Expected: {prefix}, Got: {callback_data}")
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_view_list")]
            ]),
            parse_mode='HTML'
        )
        return
    
    strategy_id = callback_data[len(prefix):]  # Remove prefix
    
    logger.info(f"  ✅ Extracted strategy_id: {strategy_id}")
    
    if not strategy_id or strategy_id.strip() == '':
        logger.warning(f"❌ Empty strategy ID after extraction")
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_view_list")]
            ]),
            parse_mode='HTML'
        )
        return
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    # Fetch strategy details
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        logger.warning(f"❌ USER {user.id}: Strategy {strategy_id} not found in DB")
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to List", callback_data="move_view_list")]
            ]),
            parse_mode='HTML'
        )
        return
    
    log_user_action(user.id, f"move_view_detail_{strategy_id}", f"Viewed: {strategy.get('strategy_name')}")
    
    # Format strategy details
    message = format_strategy_details(strategy)
    
    # ✅ Action keyboard with proper nested callback format
    action_keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"move_edit_strategy_{strategy_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"move_delete_strategy_{strategy_id}")
        ],
        [InlineKeyboardButton("🔙 Back to List", callback_data="move_view_list")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(action_keyboard),
        parse_mode='HTML'
    )
    
    logger.info(f"✅ USER {user.id}: Successfully displayed strategy {strategy_id}")


def format_strategy_details(strategy: dict) -> str:
    """✅ Format strategy dict into readable message."""
    
    name = strategy.get('strategy_name', 'Unnamed')
    description = strategy.get('description', 'No description')
    asset = strategy.get('asset', 'N/A')
    expiry = strategy.get('expiry', 'daily').capitalize()
    direction = strategy.get('direction', 'N/A').upper()
    is_active = strategy.get('is_active', False)
    
    atm_offset = strategy.get('atm_offset', 0)
    lot_size = strategy.get('lot_size', 'N/A')
    
    sl_trigger = strategy.get('sl_trigger_percent', 'N/A')
    sl_limit = strategy.get('sl_limit_percent', 'N/A')
    target_trigger = strategy.get('target_trigger_percent', 'N/A')
    target_limit = strategy.get('target_limit_percent', 'N/A')
    
    created_at = strategy.get('created_at', 'N/A')
    
    status = '🟢 <b>ACTIVE</b>' if is_active else '⚫ <b>INACTIVE</b>'
    
    # Build message
    message = (
        f"📊 <b>Strategy: {name}</b>\n\n"
        
        f"<b>📋 Basic Information</b>\n"
        f"├─ Description: <code>{description}</code>\n"
        f"├─ Status: {status}\n"
        f"├─ Created: <code>{created_at}</code>\n"
        f"└─ Asset: <code>{asset}</code>\n\n"
        
        f"<b>⚙️ Configuration</b>\n"
        f"├─ Expiry: <code>{expiry}</code>\n"
        f"├─ Direction: <code>{direction}</code>\n"
        f"├─ ATM Offset: <code>{atm_offset:+d}</code>\n"
        f"└─ Lot Size: <code>{lot_size}</code>\n\n"
        
        f"<b>🛡️ Stop Loss</b>\n"
        f"├─ Trigger: <code>{sl_trigger}%</code>\n"
        f"└─ Limit: <code>{sl_limit}%</code>\n\n"
        
        f"<b>🎯 Target</b>\n"
    )
    
    if target_trigger != 'N/A':
        message += (
            f"├─ Trigger: <code>{target_trigger}%</code>\n"
            f"└─ Limit: <code>{target_limit}%</code>\n"
        )
    else:
        message += f"└─ Status: <code>Not Configured</code>\n"
    
    return message


@error_handler
async def move_list_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Show summary of all MOVE strategies."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📊 <b>Strategy Summary</b>\n\n"
            "No strategies created yet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_menu")]
            ]),
            parse_mode='HTML'
        )
        return
    
    # Build summary
    active_count = sum(1 for s in strategies if s.get('is_active', False))
    inactive_count = len(strategies) - active_count
    
    summary = (
        f"📋 <b>MOVE Strategy Summary</b>\n\n"
        f"<b>📊 Overview</b>\n"
        f"├─ Total: {len(strategies)}\n"
        f"├─ 🟢 Active: {active_count}\n"
        f"└─ ⚫ Inactive: {inactive_count}\n\n"
        f"<b>📝 Strategies</b>\n"
    )
    
    for strat in strategies:
        name = strat.get('strategy_name', 'Unnamed')
        asset = strat.get('asset', 'N/A')
        status = '🟢' if strat.get('is_active', False) else '⚫'
        summary += f"{status} <code>{name}</code> - {asset}\n"
    
    await query.edit_message_text(
        summary,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Details", callback_data="move_view_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_menu")]
        ]),
        parse_mode='HTML'
    )
    
    logger.info(f"✅ USER {user.id}: Displayed summary of {len(strategies)} strategies")


__all__ = [
    'move_view_callback',
    'move_view_detail_callback',
    'move_list_all_callback',
    'get_strategy_list_keyboard',
    'format_strategy_details',
]
