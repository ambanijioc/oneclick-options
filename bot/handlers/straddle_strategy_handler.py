"""
Straddle strategy management handlers.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.strategy_ops import (
    create_strategy_preset,
    get_strategy_presets_by_type,
    get_strategy_preset_by_id,
    update_strategy_preset,
    delete_strategy_preset
)

logger = setup_logger(__name__)
#state_manager = StateManager()


def get_straddle_menu_keyboard():
    """Get straddle strategy management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data="straddle_add")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="straddle_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="straddle_delete_list")],
        [InlineKeyboardButton("👁️ View Strategies", callback_data="straddle_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def straddle_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display straddle strategy management menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "straddle")
    
    await query.edit_message_text(
        "<b>🎯 Straddle Strategy Management</b>\n\n"
        "Manage your ATM straddle trading strategies:\n\n"
        "• <b>Add:</b> Create new strategy\n"
        "• <b>Edit:</b> Modify existing strategy\n"
        "• <b>Delete:</b> Remove strategy\n"
        "• <b>View:</b> See all strategies\n\n"
        f"<b>Total Strategies:</b> {len(strategies)}",
        reply_markup=get_straddle_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_menu", f"Viewed straddle menu: {len(strategies)} strategies")


@error_handler
async def straddle_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add straddle strategy flow - ask for name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'straddle_add_name')

    # DEBUG: Verify state was set
    current_state = await state_manager.get_state(user.id)
    logger.info(f"✅ State SET for user {user.id}: {current_state}")
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
    
    await query.edit_message_text(
        "<b>➕ Add Straddle Strategy</b>\n\n"
        "Please enter a name for this strategy:\n\n"
        "Example: <code>BTC Weekly Straddle</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_add", "Started add strategy flow")

@error_handler
async def straddle_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip description."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Set empty description
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = ""
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data="straddle_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="straddle_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Name: <b>{state_data['name']}</b>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip target."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Set target to 0
    state_data = await state_manager.get_state_data(user.id)
    state_data['target_trigger_pct'] = 0
    state_data['target_limit_pct'] = 0
    await state_manager.set_state_data(user.id, state_data)
    await state_manager.set_state(user.id, 'straddle_add_atm_offset')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
    
    await query.edit_message_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Enter ATM offset:\n\n"
        f"• <code>0</code> = ATM (At The Money)\n"
        f"• <code>+1000</code> = Strike $1000 above ATM\n"
        f"• <code>-1000</code> = Strike $1000 below ATM",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel - return to straddle menu and clear state."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Show straddle menu
    strategies = await get_strategy_presets_by_type(user.id, "straddle")
    
    await query.edit_message_text(
        "<b>🎯 Straddle Strategy Management</b>\n\n"
        "Manage your ATM straddle trading strategies:\n\n"
        "• <b>Add:</b> Create new strategy\n"
        "• <b>Edit:</b> Modify existing strategy\n"
        "• <b>Delete:</b> Remove strategy\n"
        "• <b>View:</b> See all strategies\n\n"
        f"<b>Total Strategies:</b> {len(strategies)}",
        reply_markup=get_straddle_menu_keyboard(),
        parse_mode='HTML'
    )


# Register the skip handlers
def register_straddle_strategy_handlers(application: Application):
    """Register straddle strategy handlers."""
    
    # ... existing handlers ...
    
    application.add_handler(CallbackQueryHandler(
        straddle_skip_description_callback,
        pattern="^straddle_skip_description$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_skip_target_callback,
        pattern="^straddle_skip_target$"
    ))
    
    logger.info("Straddle strategy handlers registered")


@error_handler
async def straddle_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[-1].upper()  # BTC or ETH
    
    # Store asset
    state_data = await state_manager.get_state_data(user.id)
    state_data['asset'] = asset
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for expiry
    keyboard = [
        [InlineKeyboardButton("📅 Daily (D)", callback_data="straddle_expiry_D")],
        [InlineKeyboardButton("📅 Tomorrow (D+1)", callback_data="straddle_expiry_D+1")],
        [InlineKeyboardButton("📆 Weekly (W)", callback_data="straddle_expiry_W")],
        [InlineKeyboardButton("📆 Monthly (M)", callback_data="straddle_expiry_M")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Asset: <b>{asset}</b>\n\n"
        f"Select expiry:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    expiry = query.data.split('_')[-1]  # D, D+1, W, M
    
    # Store expiry
    state_data = await state_manager.get_state_data(user.id)
    state_data['expiry_code'] = expiry
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for direction
    keyboard = [
        [InlineKeyboardButton("📈 Long", callback_data="straddle_direction_long")],
        [InlineKeyboardButton("📉 Short", callback_data="straddle_direction_short")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Asset: <b>{state_data['asset']}</b>\n"
        f"Expiry: <b>{expiry}</b>\n\n"
        f"Select direction:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    direction = query.data.split('_')[-1]  # long or short
    
    # Store direction
    state_data = await state_manager.get_state_data(user.id)
    state_data['direction'] = direction
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for lot size
    await state_manager.set_state(user.id, 'straddle_add_lot_size')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
    
    await query.edit_message_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Asset: <b>{state_data['asset']}</b>\n"
        f"Expiry: <b>{state_data['expiry_code']}</b>\n"
        f"Direction: <b>{direction.title()}</b>\n\n"
        f"Enter lot size (number of contracts):\n\n"
        f"Example: <code>1</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all straddle strategies."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "straddle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>👁️ Straddle Strategies</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create one using <b>Add Strategy</b>.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    text = "<b>👁️ Straddle Strategies</b>\n\n"
    
    for strategy in strategies:
        text += f"<b>📊 {strategy['name']}</b>\n"
        if strategy.get('description'):
            text += f"<i>{strategy['description']}</i>\n"
        text += f"Asset: {strategy['asset']} | Expiry: {strategy['expiry_code']}\n"
        text += f"Direction: {strategy['direction'].title()} | Lots: {strategy['lot_size']}\n"
        text += f"ATM Offset: {strategy.get('atm_offset', 0):+d}\n"
        text += f"SL: {strategy['sl_trigger_pct']:.1f}% / {strategy['sl_limit_pct']:.1f}%\n"
        
        if strategy.get('target_trigger_pct', 0) > 0:
            text += f"Target: {strategy['target_trigger_pct']:.1f}% / {strategy['target_limit_pct']:.1f}%\n"
        
        text += "\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_straddle_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_view", f"Viewed {len(strategies)} strategies")


@error_handler
async def straddle_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of strategies to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "straddle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>🗑️ Delete Strategy</b>\n\n"
            "❌ No strategies found.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {strategy['name']}",
            callback_data=f"straddle_delete_{strategy['_id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Strategy</b>\n\n"
        "Select strategy to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete strategy - ask confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Store strategy ID
    await state_manager.set_state_data(user.id, {'delete_strategy_id': strategy_id})
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="straddle_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_straddle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>🗑️ Delete Strategy</b>\n\n"
        f"<b>Name:</b> {strategy['name']}\n\n"
        f"⚠️ Are you sure you want to delete this strategy?\n\n"
        f"This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete strategy."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategy ID
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('delete_strategy_id')
    
    if not strategy_id:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Delete strategy
    success = await delete_strategy_preset(strategy_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Strategy Deleted</b>\n\n"
            "The strategy has been deleted successfully.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "straddle_delete", f"Deleted strategy {strategy_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete strategy.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


def register_straddle_strategy_handlers(application: Application):
    """Register straddle strategy handlers."""
    
    application.add_handler(CallbackQueryHandler(
        straddle_strategy_menu_callback,
        pattern="^menu_straddle_strategy$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_add_callback,
        pattern="^straddle_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_asset_callback,
        pattern="^straddle_asset_(btc|eth)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_expiry_callback,
        pattern="^straddle_expiry_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_direction_callback,
        pattern="^straddle_direction_(long|short)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_view_callback,
        pattern="^straddle_view$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_delete_list_callback,
        pattern="^straddle_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_delete_callback,
        pattern="^straddle_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_delete_confirm_callback,
        pattern="^straddle_delete_confirm$"
    ))
    
    logger.info("Straddle strategy handlers registered")
  
