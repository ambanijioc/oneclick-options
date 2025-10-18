"""
MOVE Strategy Management Handler - COMPLETE CRUD FLOW
Supports: Add, Edit, Delete, View, Back to Main Menu
Includes: Name, Description, Asset, Expiry, Direction, ATM Offset, SL, Target
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import StateManager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_strategy,
    get_move_strategies,
    get_move_strategy,
    update_move_strategy,
    delete_move_strategy
)

logger = setup_logger(__name__)
state_manager = StateManager()


# ============================================================================
# MAIN MENU
# ============================================================================

@error_handler
async def move_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main MOVE Strategy menu with Add/View/Back options."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get existing strategies
    strategies = await get_move_strategies(user.id)
    
    # Build keyboard
    keyboard = []
    
    if strategies:
        keyboard.append([InlineKeyboardButton("📋 View Strategies", callback_data="move_strategy_view")])
    
    keyboard.extend([
        [InlineKeyboardButton("➕ Add Strategy", callback_data="move_strategy_add")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ])
    
    await query.edit_message_text(
        "<b>📊 MOVE Strategy Management</b>\n\n"
        f"You have <b>{len(strategies)}</b> MOVE {'strategy' if len(strategies) == 1 else 'strategies'}.\n\n"
        "<b>What are MOVE Options?</b>\n"
        "MOVE contracts are ATM straddles (Call + Put at same strike):\n"
        "• <b>Long:</b> Profit from HIGH volatility (big moves)\n"
        "• <b>Short:</b> Profit from LOW volatility (stability)\n\n"
        "What would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_menu", f"Viewed menu with {len(strategies)} strategies")


# ============================================================================
# VIEW STRATEGIES
# ============================================================================

@error_handler
async def move_strategy_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all MOVE strategies."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "<b>📋 MOVE Strategies</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create your first strategy to get started!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Strategy", callback_data="move_strategy_add")],
                [InlineKeyboardButton("🔙 Back", callback_data="menu_move_strategy")]
            ]),
            parse_mode='HTML'
        )
        return
    
    # Build strategy list
    keyboard = []
    for strategy in strategies:
        name = strategy.get('strategy_name', 'Unnamed')
        asset = strategy.get('asset', 'BTC')
        direction = strategy.get('direction', 'long')
        expiry = strategy.get('expiry', 'daily')
        
        # Emoji for direction
        direction_emoji = "📈" if direction == "long" else "📉"
        
        # Short display
        button_text = f"{direction_emoji} {name} ({asset} {expiry[0].upper()})"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"move_strategy_detail_{strategy['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move_strategy")])
    
    await query.edit_message_text(
        f"<b>📋 Your MOVE Strategies ({len(strategies)})</b>\n\n"
        "Select a strategy to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# VIEW STRATEGY DETAIL
# ============================================================================

@error_handler
async def move_strategy_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View detailed strategy information with Edit/Delete options."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_move_strategy(strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_strategy_view")]
            ]),
            parse_mode='HTML'
        )
        return
    
    # Build details message
    text = f"<b>📊 MOVE Strategy Details</b>\n\n"
    text += f"<b>Name:</b> {strategy.get('strategy_name', 'Unnamed')}\n"
    
    description = strategy.get('description', '')
    if description:
        text += f"<b>Description:</b> {description}\n"
    
    text += f"\n<b>📈 Trading Setup:</b>\n"
    text += f"• Asset: {strategy.get('asset', 'BTC')}\n"
    text += f"• Expiry: {strategy.get('expiry', 'daily').title()}\n"
    text += f"• Direction: {strategy.get('direction', 'long').title()}\n"
    text += f"• ATM Offset: {strategy.get('atm_offset', 0):+d}\n"
    
    # Stop Loss
    sl_trigger = strategy.get('stop_loss_trigger')
    sl_limit = strategy.get('stop_loss_limit')
    if sl_trigger and sl_limit:
        text += f"\n<b>🛑 Stop Loss:</b>\n"
        text += f"• Trigger: {sl_trigger:.1f}%\n"
        text += f"• Limit: {sl_limit:.1f}%\n"
    else:
        text += f"\n<b>🛑 Stop Loss:</b> Not set\n"
    
    # Target
    target_trigger = strategy.get('target_trigger')
    target_limit = strategy.get('target_limit')
    if target_trigger and target_limit:
        text += f"\n<b>🎯 Target:</b>\n"
        text += f"• Trigger: {target_trigger:.1f}%\n"
        text += f"• Limit: {target_limit:.1f}%"
    else:
        text += f"\n<b>🎯 Target:</b> Not set"
    
    # Keyboard
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"move_strategy_edit_{strategy_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"move_strategy_delete_confirm_{strategy_id}")
        ],
        [InlineKeyboardButton("🔙 Back to List", callback_data="move_strategy_view")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# DELETE STRATEGY (with confirmation)
# ============================================================================

@error_handler
async def move_strategy_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm strategy deletion."""
    query = update.callback_query
    await query.answer()
    
    strategy_id = query.data.split('_')[-1]
    strategy = await get_move_strategy(strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_strategy_view")]
            ]),
            parse_mode='HTML'
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"move_strategy_delete_{strategy_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"move_strategy_detail_{strategy_id}")]
    ]
    
    await query.edit_message_text(
        f"<b>⚠️ Delete Strategy?</b>\n\n"
        f"Are you sure you want to delete:\n"
        f"<b>{strategy.get('strategy_name', 'Unnamed')}</b>?\n\n"
        f"This action cannot be undone!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete strategy after confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_move_strategy(strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="move_strategy_view")]
            ]),
            parse_mode='HTML'
        )
        return
    
    success = await delete_move_strategy(strategy_id)
    
    if success:
        await query.edit_message_text(
            f"✅ Strategy '<b>{strategy.get('strategy_name', 'Unnamed')}</b>' deleted successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to List", callback_data="move_strategy_view")]
            ]),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_strategy_delete", f"Deleted strategy {strategy_id}")
    else:
        await query.edit_message_text(
            "❌ Failed to delete strategy. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data=f"move_strategy_detail_{strategy_id}")]
            ]),
            parse_mode='HTML'
        )


# ============================================================================
# ADD STRATEGY - STEP 1: Name
# ============================================================================

@error_handler
async def move_strategy_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding new strategy - ask for name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Initialize state
    await state_manager.set_state(user.id, 'awaiting_move_strategy_name')
    await state_manager.set_state_data(user.id, {})
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="move_strategy_cancel")]]
    
    await query.edit_message_text(
        "<b>➕ Add MOVE Strategy - Step 1/9</b>\n\n"
        "Enter a <b>name</b> for your strategy:\n\n"
        "Examples:\n"
        "• BTC Long Volatility Play\n"
        "• ETH Short Stability\n"
        "• Daily BTC Straddle\n\n"
        "👉 Type the name below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_add", "Started strategy creation")


# Continue in next message due to length...
