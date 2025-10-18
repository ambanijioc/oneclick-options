"""
MOVE strategy management handlers with expiry selection support.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

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


def get_move_strategy_keyboard(strategies):
    """Get move strategy menu keyboard."""
    keyboard = []
    
    if strategies:
        keyboard.append([InlineKeyboardButton("📋 View Strategies", callback_data="move_strategy_view")])
    
    keyboard.extend([
        [InlineKeyboardButton("➕ Add Strategy", callback_data="move_strategy_add")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ])
    
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display move strategy management menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get existing strategies
    strategies = await get_move_strategies(user.id)
    
    await query.edit_message_text(
        "<b>📊 MOVE Strategy Management</b>\n\n"
        f"You have <b>{len(strategies)}</b> MOVE {'strategy' if len(strategies) == 1 else 'strategies'}.\n\n"
        "MOVE options are volatility products:\n"
        "• <b>Long:</b> Profit from high volatility\n"
        "• <b>Short:</b> Profit from stability\n\n"
        "What would you like to do?",
        reply_markup=get_move_strategy_keyboard(strategies),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_menu", f"Viewed menu with {len(strategies)} strategies")


@error_handler
async def move_strategy_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start MOVE strategy creation - Asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Initialize state
    await state_manager.set_state(user.id, 'creating_move_strategy')
    await state_manager.set_state_data(user.id, {})
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_asset_btc")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        "<b>📊 MOVE Strategy - Asset Selection</b>\n\n"
        "Select the underlying asset:\n\n"
        "<b>BTC:</b> Bitcoin MOVE contracts\n"
        "• Higher volatility\n"
        "• Larger strike increments ($100)\n\n"
        "<b>ETH:</b> Ethereum MOVE contracts\n"
        "• Moderate volatility\n"
        "• Smaller strike increments ($10)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_add", "Started add strategy flow")


@error_handler
async def move_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection - Move to expiry selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[-1].upper()  # BTC or ETH
    
    # Store asset
    state_data = await state_manager.get_state_data(user.id)
    state_data['asset'] = asset
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for expiry type (NEW STEP)
    keyboard = [
        [InlineKeyboardButton("📅 Daily (1-2 days)", callback_data="move_expiry_daily")],
        [InlineKeyboardButton("📆 Weekly (3-10 days)", callback_data="move_expiry_weekly")],
        [InlineKeyboardButton("📊 Monthly (10-40 days)", callback_data="move_expiry_monthly")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>📊 MOVE Strategy - Expiry Selection</b>\n\n"
        f"<b>Asset:</b> {asset}\n\n"
        f"Choose the expiry type for your MOVE contracts:\n\n"
        f"<b>Daily:</b> High gamma, fast decay\n"
        f"• Best for intraday volatility plays\n"
        f"• Expires within 1-2 days\n\n"
        f"<b>Weekly:</b> Balanced risk/reward\n"
        f"• Moderate time decay\n"
        f"• Expires in 3-10 days\n\n"
        f"<b>Monthly:</b> Lower gamma, slow decay\n"
        f"• Longer-term volatility bets\n"
        f"• Expires in 10-40 days",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection - Move to direction selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    expiry = query.data.split('_')[-1]  # daily, weekly, or monthly
    
    # Store expiry
    state_data = await state_manager.get_state_data(user.id)
    state_data['expiry'] = expiry
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for direction
    keyboard = [
        [InlineKeyboardButton("📈 Long (High Volatility)", callback_data="move_direction_long")],
        [InlineKeyboardButton("📉 Short (Low Volatility)", callback_data="move_direction_short")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>📊 MOVE Strategy - Direction</b>\n\n"
        f"<b>Asset:</b> {state_data['asset']}\n"
        f"<b>Expiry:</b> {expiry.title()}\n\n"
        f"Choose your trading direction:\n\n"
        f"<b>Long (Buy):</b> Profit from high volatility\n"
        f"• You expect BIG price movement (up or down)\n"
        f"• Premium rises when volatility increases\n"
        f"• Example: Earnings, major news events\n\n"
        f"<b>Short (Sell):</b> Profit from stability\n"
        f"• You expect SMALL price movement\n"
        f"• Premium drops when volatility is low\n"
        f"• Example: Quiet trading periods",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection - Move to ATM offset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    direction = query.data.split('_')[-1]  # long or short
    
    # Store direction
    state_data = await state_manager.get_state_data(user.id)
    state_data['direction'] = direction
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for ATM offset
    await state_manager.set_state(user.id, 'awaiting_move_atm_offset')
    
    keyboard = [
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>📊 MOVE Strategy - ATM Offset</b>\n\n"
        f"<b>Asset:</b> {state_data['asset']}\n"
        f"<b>Expiry:</b> {state_data['expiry'].title()}\n"
        f"<b>Direction:</b> {direction.title()}\n\n"
        f"Enter ATM offset (whole number):\n\n"
        f"<b>What is ATM Offset?</b>\n"
        f"Offset from At-The-Money strike:\n\n"
        f"• <code>0</code> = ATM (At The Money)\n"
        f"• <code>+1</code> = 1 strike above ATM (BTC: $100, ETH: $10)\n"
        f"• <code>-1</code> = 1 strike below ATM\n"
        f"• <code>+5</code> = 5 strikes above ATM (BTC: $500, ETH: $50)\n\n"
        f"<b>Recommendation:</b> Start with <code>0</code> (ATM)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel - return to move menu and clear state."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Show move menu
    strategies = await get_move_strategies(user.id)
    
    await query.edit_message_text(
        "<b>📊 MOVE Strategy Management</b>\n\n"
        f"You have <b>{len(strategies)}</b> MOVE {'strategy' if len(strategies) == 1 else 'strategies'}.\n\n"
        "MOVE options are volatility products:\n"
        "• <b>Long:</b> Profit from high volatility\n"
        "• <b>Short:</b> Profit from stability\n\n"
        "What would you like to do?",
        reply_markup=get_move_strategy_keyboard(strategies),
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all move strategies."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get strategies
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "<b>📊 MOVE Strategies</b>\n\n"
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
        strategy_name = strategy.get('strategy_name', 'Unnamed')
        asset = strategy.get('asset', 'BTC')
        direction = strategy.get('direction', 'long')
        expiry = strategy.get('expiry', 'daily')
        
        button_text = f"{asset} {direction.title()} ({expiry.title()[0]})"  # e.g., "BTC Long (D)"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"move_strategy_detail_{strategy['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move_strategy")])
    
    await query.edit_message_text(
        f"<b>📊 Your MOVE Strategies ({len(strategies)})</b>\n\n"
        "Select a strategy to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display strategy details with edit/delete options."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy
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
    text += f"<b>Asset:</b> {strategy.get('asset', 'BTC')}\n"
    text += f"<b>Expiry:</b> {strategy.get('expiry', 'daily').title()}\n"
    text += f"<b>Direction:</b> {strategy.get('direction', 'long').title()}\n"
    text += f"<b>Lot Size:</b> {strategy.get('lot_size', 1)}\n"
    text += f"<b>ATM Offset:</b> {strategy.get('atm_offset', 0):+d}\n\n"
    
    # Stop Loss
    sl_trigger = strategy.get('stop_loss_trigger')
    sl_limit = strategy.get('stop_loss_limit')
    if sl_trigger and sl_limit:
        text += f"<b>🛑 Stop Loss:</b>\n"
        text += f"• Trigger: {sl_trigger}%\n"
        text += f"• Limit: {sl_limit}%\n\n"
    else:
        text += "<b>🛑 Stop Loss:</b> Not set\n\n"
    
    # Target
    target_trigger = strategy.get('target_trigger')
    target_limit = strategy.get('target_limit')
    if target_trigger and target_limit:
        text += f"<b>🎯 Target:</b>\n"
        text += f"• Trigger: {target_trigger}%\n"
        text += f"• Limit: {target_limit}%"
    else:
        text += "<b>🎯 Target:</b> Not set"
    
    # Keyboard
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data=f"move_strategy_delete_{strategy_id}")],
        [InlineKeyboardButton("🔙 Back to List", callback_data="move_strategy_view")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a strategy with confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy for name
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
    
    # Delete strategy
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


def register_move_strategy_handlers(application: Application):
    """Register MOVE strategy handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_menu_callback,
        pattern="^menu_move_strategy$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_add_callback,
        pattern="^move_strategy_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_asset_callback,
        pattern="^move_asset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_expiry_callback,
        pattern="^move_expiry_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_direction_callback,
        pattern="^move_direction_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_cancel_callback,
        pattern="^move_cancel$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_view_callback,
        pattern="^move_strategy_view$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_detail_callback,
        pattern="^move_strategy_detail_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_delete_callback,
        pattern="^move_strategy_delete_"
    ))
    
    logger.info("MOVE strategy handlers registered")
    
