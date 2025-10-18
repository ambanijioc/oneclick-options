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
# ============================================================================
# CANCEL FLOW
# ============================================================================

@error_handler
async def move_strategy_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel strategy creation/editing."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Return to menu
    await move_strategy_menu_callback(update, context)


# ============================================================================
# TEXT INPUT HANDLERS (for Add Strategy flow)
# ============================================================================

@error_handler
async def handle_move_strategy_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text inputs during strategy creation."""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    state_data = await state_manager.get_state_data(user.id)
    
    if not state:
        return
    
    # Handle different input states
    if state == 'awaiting_move_strategy_name':
        await handle_strategy_name_input(update, context, text, state_data)
    
    elif state == 'awaiting_move_strategy_description':
        await handle_strategy_description_input(update, context, text, state_data)
    
    elif state == 'awaiting_move_strategy_atm_offset':
        await handle_strategy_atm_offset_input(update, context, text, state_data)
    
    elif state == 'awaiting_move_strategy_sl_trigger':
        await handle_strategy_sl_trigger_input(update, context, text, state_data)
    
    elif state == 'awaiting_move_strategy_sl_limit':
        await handle_strategy_sl_limit_input(update, context, text, state_data)
    
    elif state == 'awaiting_move_strategy_target_trigger':
        await handle_strategy_target_trigger_input(update, context, text, state_data)
    
    elif state == 'awaiting_move_strategy_target_limit':
        await handle_strategy_target_limit_input(update, context, text, state_data)


# ============================================================================
# INDIVIDUAL INPUT HANDLERS
# ============================================================================

async def handle_strategy_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle strategy name input."""
    user = update.effective_user
    
    if len(text) < 3:
        await update.message.reply_text(
            "❌ Strategy name must be at least 3 characters long.\n\n"
            "Please try again:",
            parse_mode='HTML'
        )
        return
    
    if len(text) > 50:
        await update.message.reply_text(
            "❌ Strategy name must be 50 characters or less.\n\n"
            "Please try again:",
            parse_mode='HTML'
        )
        return
    
    # Store name
    state_data['strategy_name'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to description input
    await state_manager.set_state(user.id, 'awaiting_move_strategy_description')
    
    await update.message.reply_text(
        "<b>➕ Add MOVE Strategy - Step 2/9</b>\n\n"
        "Enter a <b>description</b> for your strategy (optional):\n\n"
        "Examples:\n"
        "• Long volatility during high impact news\n"
        "• Short stability during quiet markets\n"
        "• Earnings play strategy\n\n"
        "Type 'skip' to skip this step, or enter description:",
        parse_mode='HTML'
    )


async def handle_strategy_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle strategy description input."""
    user = update.effective_user
    
    # Allow skipping
    if text.lower() == 'skip':
        state_data['description'] = ''
    else:
        if len(text) > 200:
            await update.message.reply_text(
                "❌ Description must be 200 characters or less.\n\n"
                "Please try again (or type 'skip' to skip):",
                parse_mode='HTML'
            )
            return
        
        state_data['description'] = text
    
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to asset selection (button-based)
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_strategy_asset_btc")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_strategy_asset_eth")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_strategy_cancel")]
    ]
    
    await update.message.reply_text(
        "<b>➕ Add MOVE Strategy - Step 3/9</b>\n\n"
        "Select the <b>underlying asset</b>:\n\n"
        "<b>BTC:</b>\n"
        "• Bitcoin MOVE contracts\n"
        "• Higher volatility\n"
        "• Strike increments: $200\n\n"
        "<b>ETH:</b>\n"
        "• Ethereum MOVE contracts\n"
        "• Moderate volatility\n"
        "• Strike increments: $20",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# ASSET SELECTION
# ============================================================================

@error_handler
async def move_strategy_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[-1].upper()  # BTC or ETH
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['asset'] = asset
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to expiry selection
    keyboard = [
        [InlineKeyboardButton("📅 Daily (1-2 days)", callback_data="move_strategy_expiry_daily")],
        [InlineKeyboardButton("📆 Weekly (3-10 days)", callback_data="move_strategy_expiry_weekly")],
        [InlineKeyboardButton("📊 Monthly (10-40 days)", callback_data="move_strategy_expiry_monthly")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_strategy_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add MOVE Strategy - Step 4/9</b>\n\n"
        f"<b>Asset:</b> {asset}\n\n"
        f"Select <b>expiry type</b>:\n\n"
        f"<b>Daily:</b> High gamma, fast decay\n"
        f"• Best for intraday volatility\n"
        f"• Expires 1-2 days\n\n"
        f"<b>Weekly:</b> Balanced risk/reward\n"
        f"• Moderate time decay\n"
        f"• Expires 3-10 days\n\n"
        f"<b>Monthly:</b> Lower gamma, slow decay\n"
        f"• Long-term plays\n"
        f"• Expires 10-40 days",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# EXPIRY SELECTION
# ============================================================================

@error_handler
async def move_strategy_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    expiry = query.data.split('_')[-1]  # daily, weekly, monthly
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['expiry'] = expiry
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to direction selection
    keyboard = [
        [InlineKeyboardButton("📈 Long (High Volatility)", callback_data="move_strategy_direction_long")],
        [InlineKeyboardButton("📉 Short (Low Volatility)", callback_data="move_strategy_direction_short")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_strategy_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add MOVE Strategy - Step 5/9</b>\n\n"
        f"<b>Asset:</b> {state_data['asset']}\n"
        f"<b>Expiry:</b> {expiry.title()}\n\n"
        f"Select <b>trading direction</b>:\n\n"
        f"<b>Long (Buy MOVE):</b>\n"
        f"• Profit from BIG price movements\n"
        f"• Expect high volatility\n"
        f"• Premium rises with volatility\n\n"
        f"<b>Short (Sell MOVE):</b>\n"
        f"• Profit from SMALL price movements\n"
        f"• Expect low volatility\n"
        f"• Premium drops when market is calm",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# DIRECTION SELECTION
# ============================================================================

@error_handler
async def move_strategy_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    direction = query.data.split('_')[-1]  # long or short
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['direction'] = direction
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to ATM offset input
    await state_manager.set_state(user.id, 'awaiting_move_strategy_atm_offset')
    
    asset = state_data['asset']
    strike_increment = "$200" if asset == "BTC" else "$20"
    
    await query.edit_message_text(
        f"<b>➕ Add MOVE Strategy - Step 6/9</b>\n\n"
        f"<b>Asset:</b> {asset}\n"
        f"<b>Expiry:</b> {state_data['expiry'].title()}\n"
        f"<b>Direction:</b> {direction.title()}\n\n"
        f"Enter <b>ATM offset</b> (whole number):\n\n"
        f"<b>What is ATM Offset?</b>\n"
        f"Offset from At-The-Money strike:\n\n"
        f"• <code>0</code> = ATM (closest to spot price)\n"
        f"• <code>+1</code> = 1 strike above ATM ({strike_increment})\n"
        f"• <code>-1</code> = 1 strike below ATM ({strike_increment})\n"
        f"• <code>+2</code> = 2 strikes above ATM\n\n"
        f"<b>Recommended:</b> Use <code>0</code> (ATM) for standard MOVE trading\n\n"
        f"👉 Type the offset number below:",
        parse_mode='HTML'
    )


async def handle_strategy_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle ATM offset input."""
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        
        # Validate range
        if not -10 <= atm_offset <= 10:
            await update.message.reply_text(
                "❌ ATM offset must be between -10 and +10.\n\n"
                "Please enter a valid offset:",
                parse_mode='HTML'
            )
            return
        
        state_data['atm_offset'] = atm_offset
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask if user wants to set SL/Target
        keyboard = [
            [InlineKeyboardButton("✅ Yes, set SL/Target", callback_data="move_strategy_sl_yes")],
            [InlineKeyboardButton("⏭️ Skip SL/Target", callback_data="move_strategy_sl_skip")],
            [InlineKeyboardButton("❌ Cancel", callback_data="move_strategy_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add MOVE Strategy - Step 7/9</b>\n\n"
            f"<b>ATM Offset:</b> {atm_offset:+d}\n\n"
            f"Would you like to set <b>Stop Loss and Target</b>?\n\n"
            f"<b>Stop Loss:</b> Auto-exit when loss reaches %\n"
            f"<b>Target:</b> Auto-exit when profit reaches %\n\n"
            f"You can skip and add these later if you prefer.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a whole number.\n\n"
            "Examples: 0, 1, -1, 2, -2",
            parse_mode='HTML'
        )


# ============================================================================
# SL/TARGET SETUP
# ============================================================================

@error_handler
async def move_strategy_sl_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User wants to set SL/Target."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Move to SL trigger input
    await state_manager.set_state(user.id, 'awaiting_move_strategy_sl_trigger')
    
    await query.edit_message_text(
        "<b>➕ Add MOVE Strategy - Step 7a/9</b>\n\n"
        "<b>Stop Loss Trigger Percentage</b>\n\n"
        "Enter the loss percentage that triggers your stop loss:\n\n"
        "Examples:\n"
        "• 30 = Exit when 30% loss\n"
        "• 50 = Exit when 50% loss\n"
        "• 70 = Exit when 70% loss\n\n"
        "👉 Enter percentage (number only):",
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_sl_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User skipped SL/Target - finalize strategy."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    state_data = await state_manager.get_state_data(user.id)
    
    # Set SL/Target to None
    state_data['stop_loss_trigger'] = None
    state_data['stop_loss_limit'] = None
    state_data['target_trigger'] = None
    state_data['target_limit'] = None
    
    # Finalize and save
    await finalize_strategy_creation(query, user, state_data)


async def handle_strategy_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle SL trigger input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        
        if not 0 < sl_trigger <= 100:
            await update.message.reply_text(
                "❌ Stop loss trigger must be between 0% and 100%.\n\n"
                "Please enter a valid percentage:",
                parse_mode='HTML'
            )
            return
        
        state_data['stop_loss_trigger'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Move to SL limit
        await state_manager.set_state(user.id, 'awaiting_move_strategy_sl_limit')
        
        await update.message.reply_text(
            f"<b>➕ Add MOVE Strategy - Step 7b/9</b>\n\n"
            f"<b>SL Trigger:</b> {sl_trigger}%\n\n"
            f"<b>Stop Loss Limit Percentage</b>\n\n"
            f"Enter the limit percentage (slightly worse than trigger):\n\n"
            f"Examples:\n"
            f"• If trigger is {sl_trigger}%, limit could be {sl_trigger + 5}%\n"
            f"• Limit ensures execution even if price moves fast\n\n"
            f"👉 Enter limit percentage:",
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number.\n\n"
            "Examples: 30, 50, 70",
            parse_mode='HTML'
        )


async def handle_strategy_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle SL limit input."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        
        if not 0 < sl_limit <= 100:
            await update.message.reply_text(
                "❌ Stop loss limit must be between 0% and 100%.\n\n"
                "Please enter a valid percentage:",
                parse_mode='HTML'
            )
            return
        
        state_data['stop_loss_limit'] = sl_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Move to target trigger
        await state_manager.set_state(user.id, 'awaiting_move_strategy_target_trigger')
        
        await update.message.reply_text(
            f"<b>➕ Add MOVE Strategy - Step 8/9</b>\n\n"
            f"<b>SL Complete:</b> {state_data['stop_loss_trigger']}% trigger, {sl_limit}% limit\n\n"
            f"<b>Target Trigger Percentage</b>\n\n"
            f"Enter the profit percentage that triggers your target:\n\n"
            f"Examples:\n"
            f"• 50 = Exit at 50% profit\n"
            f"• 100 = Exit at 100% profit (2x)\n"
            f"• 200 = Exit at 200% profit (3x)\n\n"
            f"👉 Enter percentage:",
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number.\n\n"
            "Examples: 35, 55, 75",
            parse_mode='HTML'
        )


async def handle_strategy_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle target trigger input."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        
        if not 0 < target_trigger <= 1000:
            await update.message.reply_text(
                "❌ Target trigger must be between 0% and 1000%.\n\n"
                "Please enter a valid percentage:",
                parse_mode='HTML'
            )
            return
        
        state_data['target_trigger'] = target_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Move to target limit
        await state_manager.set_state(user.id, 'awaiting_move_strategy_target_limit')
        
        await update.message.reply_text(
            f"<b>➕ Add MOVE Strategy - Step 9/9</b>\n\n"
            f"<b>Target Trigger:</b> {target_trigger}%\n\n"
            f"<b>Target Limit Percentage</b>\n\n"
            f"Enter the limit percentage (slightly lower than trigger):\n\n"
            f"Examples:\n"
            f"• If trigger is {target_trigger}%, limit could be {target_trigger - 5}%\n"
            f"• Ensures you lock in profits\n\n"
            f"👉 Enter limit percentage:",
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number.\n\n"
            "Examples: 50, 100, 200",
            parse_mode='HTML'
        )


async def handle_strategy_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle target limit input and finalize strategy."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        
        if not 0 < target_limit <= 1000:
            await update.message.reply_text(
                "❌ Target limit must be between 0% and 1000%.\n\n"
                "Please enter a valid percentage:",
                parse_mode='HTML'
            )
            return
        
        state_data['target_limit'] = target_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Finalize and save
        await finalize_strategy_creation_text(update, user, state_data)
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number.\n\n"
            "Examples: 45, 95, 190",
            parse_mode='HTML'
        )


# ============================================================================
# FINALIZE STRATEGY CREATION
# ============================================================================

async def finalize_strategy_creation(query, user, state_data: dict):
    """Finalize strategy creation (from callback query)."""
    
    # Save to database
    strategy_id = await create_move_strategy(user.id, state_data)
    
    if strategy_id:
        # Build success message
        text = "<b>✅ MOVE Strategy Created!</b>\n\n"
        text += f"<b>Name:</b> {state_data['strategy_name']}\n"
        
        if state_data.get('description'):
            text += f"<b>Description:</b> {state_data['description']}\n"
        
        text += f"\n<b>Setup:</b>\n"
        text += f"• Asset: {state_data['asset']}\n"
        text += f"• Expiry: {state_data['expiry'].title()}\n"
        text += f"• Direction: {state_data['direction'].title()}\n"
        text += f"• ATM Offset: {state_data['atm_offset']:+d}\n"
        
        if state_data.get('stop_loss_trigger'):
            text += f"\n<b>Risk Management:</b>\n"
            text += f"• SL: {state_data['stop_loss_trigger']}% / {state_data['stop_loss_limit']}%\n"
            text += f"• Target: {state_data['target_trigger']}% / {state_data['target_limit']}%"
        
        text += "\n\nYou can now use this strategy in Trade Presets!"
        
        keyboard = [
            [InlineKeyboardButton("➕ Create Trade Preset", callback_data="menu_move_trade_preset")],
            [InlineKeyboardButton("📋 View Strategies", callback_data="move_strategy_view")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "move_strategy_create", f"Created strategy: {state_data['strategy_name']}")
    else:
        await query.edit_message_text(
            "❌ Failed to create strategy. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu_move_strategy")]
            ]),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


async def finalize_strategy_creation_text(update: Update, user, state_data: dict):
    """Finalize strategy creation (from text message)."""
    
    # Save to database
    strategy_id = await create_move_strategy(user.id, state_data)
    
    if strategy_id:
        # Build success message
        text = "<b>✅ MOVE Strategy Created!</b>\n\n"
        text += f"<b>Name:</b> {state_data['strategy_name']}\n"
        
        if state_data.get('description'):
            text += f"<b>Description:</b> {state_data['description']}\n"
        
        text += f"\n<b>Setup:</b>\n"
        text += f"• Asset: {state_data['asset']}\n"
        text += f"• Expiry: {state_data['expiry'].title()}\n"
        text += f"• Direction: {state_data['direction'].title()}\n"
        text += f"• ATM Offset: {state_data['atm_offset']:+d}\n"
        
        if state_data.get('stop_loss_trigger'):
            text += f"\n<b>Risk Management:</b>\n"
            text += f"• SL: {state_data['stop_loss_trigger']}% / {state_data['stop_loss_limit']}%\n"
            text += f"• Target: {state_data['target_trigger']}% / {state_data['target_limit']}%"
        
        text += "\n\nYou can now use this strategy in Trade Presets!"
        
        keyboard = [
            [InlineKeyboardButton("➕ Create Trade Preset", callback_data="menu_move_trade_preset")],
            [InlineKeyboardButton("📋 View Strategies", callback_data="move_strategy_view")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "move_strategy_create", f"Created strategy: {state_data['strategy_name']}")
    else:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_move_strategy")]]
        await update.message.reply_text(
            "❌ Failed to create strategy. Please try again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


# ============================================================================
# REGISTER HANDLERS
# ============================================================================

def register_move_strategy_handlers(application: Application):
    """Register all MOVE strategy handlers."""
    
    # Main menu
    application.add_handler(CallbackQueryHandler(
        move_strategy_menu_callback,
        pattern="^menu_move_strategy$"
    ))
    
    # View strategies
    application.add_handler(CallbackQueryHandler(
        move_strategy_view_callback,
        pattern="^move_strategy_view$"
    ))
    
    # View detail
    application.add_handler(CallbackQueryHandler(
        move_strategy_detail_callback,
        pattern="^move_strategy_detail_"
    ))
    
    # Delete (confirmation + action)
    application.add_handler(CallbackQueryHandler(
        move_strategy_delete_confirm_callback,
        pattern="^move_strategy_delete_confirm_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_delete_callback,
        pattern="^move_strategy_delete_(?!confirm)"
    ))
    
    # Add strategy flow
    application.add_handler(CallbackQueryHandler(
        move_strategy_add_callback,
        pattern="^move_strategy_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_asset_callback,
        pattern="^move_strategy_asset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_expiry_callback,
        pattern="^move_strategy_expiry_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_direction_callback,
        pattern="^move_strategy_direction_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_sl_yes_callback,
        pattern="^move_strategy_sl_yes$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_sl_skip_callback,
        pattern="^move_strategy_sl_skip$"
    ))
    
    # Cancel
    application.add_handler(CallbackQueryHandler(
        move_strategy_cancel_callback,
        pattern="^move_strategy_cancel$"
    ))
    
    # Text input handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_move_strategy_text_input
    )), group=0)  # ← FIX: Explicit priority
    
    logger.info("MOVE strategy handlers registered successfully")
