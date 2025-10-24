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
        [InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]
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
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
    
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
async def straddle_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of strategies to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "straddle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>✏️ Edit Strategy</b>\n\n"
            "❌ No strategies found.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        keyboard.append([InlineKeyboardButton(
            f"✏️ {strategy.name}",
            callback_data=f"straddle_edit_{str(strategy.id)}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Strategy</b>\n\n"
        "Select strategy to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def straddle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit options for selected strategy."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Store strategy ID for editing
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    # Show current strategy details with edit options
    target_text = ""
    if strategy.target_trigger_pct > 0:
        target_text = f"Target: {strategy.target_trigger_pct:.1f}% / {strategy.target_limit_pct:.1f}%\n"
    
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data=f"straddle_edit_name_{strategy_id}")],
        [InlineKeyboardButton("📝 Edit Description", callback_data=f"straddle_edit_desc_{strategy_id}")],
        [InlineKeyboardButton("📝 Edit SL %", callback_data=f"straddle_edit_sl_{strategy_id}")],
        [InlineKeyboardButton("📝 Edit Target %", callback_data=f"straddle_edit_target_{strategy_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="straddle_edit_list")]
    ]
    
    await query.edit_message_text(
        f"<b>✏️ Edit Strategy</b>\n\n"
        f"<b>Current Settings:</b>\n\n"
        f"Name: <b>{strategy.name}</b>\n"
        f"Description: <i>{strategy.description or 'None'}</i>\n"
        f"Asset: {strategy.asset} | Expiry: {strategy.expiry_code}\n"
        f"Direction: {strategy.direction.title()} | Lots: {strategy.lot_size}\n"
        f"ATM Offset: {strategy.atm_offset:+d}\n"
        f"SL: {strategy.sl_trigger_pct:.1f}% / {strategy.sl_limit_pct:.1f}%\n"
        + target_text +
        "\nSelect what you want to edit:",
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
        # ✅ Use dot notation for Pydantic model
        text += f"<b>📊 {strategy.name}</b>\n"
        if strategy.description:
            text += f"<i>{strategy.description}</i>\n"
        text += f"Asset: {strategy.asset} | Expiry: {strategy.expiry_code}\n"
        text += f"Direction: {strategy.direction.title()} | Lots: {strategy.lot_size}\n"
        text += f"ATM Offset: {strategy.atm_offset:+d}\n"
        text += f"SL: {strategy.sl_trigger_pct:.1f}% / {strategy.sl_limit_pct:.1f}%\n"
        
        if strategy.target_trigger_pct > 0:
            text += f"Target: {strategy.target_trigger_pct:.1f}% / {strategy.target_limit_pct:.1f}%\n"
        
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
            f"🗑️ {strategy.name}",
            callback_data=f"straddle_delete_{str(strategy.id)}"
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
        f"<b>Name:</b> {strategy.name}\n\n"
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


@error_handler
async def handle_sl_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose to enable SL monitoring"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    context.user_data['enable_sl_monitor'] = True
    await save_straddle_preset(update, context)


@error_handler
async def handle_sl_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose to disable SL monitoring"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    context.user_data['enable_sl_monitor'] = False
    await save_straddle_preset(update, context)


@error_handler
async def save_straddle_preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final save of the straddle preset with SL preference"""
    from database.models.strategy_preset import StrategyPresetCreate
    
    query = update.callback_query if update.callback_query else None
    user = update.effective_user
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    
    # Build preset
    preset = StrategyPresetCreate(
        user_id=user.id,
        strategy_type='straddle',
        name=state_data.get('name', 'Straddle'),
        description=state_data.get('description', ''),
        asset=state_data['asset'],
        expiry_code=state_data['expiry_code'],
        direction=state_data['direction'],
        lot_size=state_data['lot_size'],
        sl_trigger_pct=state_data.get('sl_trigger_pct', 0.0),
        sl_limit_pct=state_data.get('sl_limit_pct', 0.0),
        target_trigger_pct=state_data.get('target_trigger_pct', 0.0),
        target_limit_pct=state_data.get('target_limit_pct', 0.0),
        atm_offset=state_data.get('atm_offset', 0),
        enable_sl_monitor=context.user_data.get('enable_sl_monitor', False)
    )
    
    result = await create_strategy_preset(preset)
    
    sl_status = "✅ Enabled" if preset.enable_sl_monitor else "❌ Disabled"
    
    if result:
        success_message = (
            f"✅ <b>Preset Saved!</b>\n\n"
            f"<b>Name:</b> {preset.name}\n"
            f"<b>Asset:</b> {preset.asset}\n"
            f"<b>Direction:</b> {preset.direction.title()}\n"
            f"<b>SL Monitor:</b> {sl_status}"
        )
        
        if query:
            await query.edit_message_text(
                success_message,
                reply_markup=get_straddle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                success_message,
                reply_markup=get_straddle_menu_keyboard(),
                parse_mode='HTML'
            )
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, "straddle_save", f"Saved strategy: {preset.name}")
    else:
        error_message = "❌ Error saving preset."
        if query:
            await query.edit_message_text(error_message, reply_markup=get_straddle_menu_keyboard())
        else:
            await update.message.reply_text(error_message, reply_markup=get_straddle_menu_keyboard())


# ============================================================================
# EDIT FIELD HANDLERS
# ============================================================================

@error_handler
async def straddle_edit_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing strategy name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy to show current name
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'straddle_edit_name_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"straddle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        f"<b>✏️ Edit Strategy Name</b>\n\n"
        f"Current name: <b>{strategy.name}</b>\n\n"
        f"Enter new name for this strategy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_edit_name", f"Editing name for strategy {strategy_id}")


@error_handler
async def straddle_edit_desc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing description."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy to show current description
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'straddle_edit_desc_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    current_desc = strategy.description or "None"
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"straddle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        f"<b>✏️ Edit Description</b>\n\n"
        f"Current description: <i>{current_desc}</i>\n\n"
        f"Enter new description:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_edit_desc", f"Editing description for strategy {strategy_id}")


@error_handler
async def straddle_edit_sl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing SL percentages."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy to show current SL
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'straddle_edit_sl_trigger_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"straddle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        f"<b>✏️ Edit Stop Loss</b>\n\n"
        f"Current SL: <b>{strategy.sl_trigger_pct:.1f}%</b> trigger / <b>{strategy.sl_limit_pct:.1f}%</b> limit\n\n"
        f"Enter new SL trigger percentage:\n\n"
        f"Example: <code>50</code> (for 50% loss)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_edit_sl", f"Editing SL for strategy {strategy_id}")


@error_handler
async def straddle_edit_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing target percentages."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy to show current target
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'straddle_edit_target_trigger_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    current_target = f"{strategy.target_trigger_pct:.1f}% trigger / {strategy.target_limit_pct:.1f}% limit" if strategy.target_trigger_pct > 0 else "Not set"
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"straddle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        f"<b>✏️ Edit Target</b>\n\n"
        f"Current target: <b>{current_target}</b>\n\n"
        f"Enter new target trigger percentage:\n\n"
        f"Example: <code>100</code> (for 100% profit)\n"
        f"Or <code>0</code> to disable target",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_edit_target", f"Editing target for strategy {strategy_id}")


@error_handler
async def handle_straddle_sl_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YES to enable SL monitoring."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"🟢 SL Monitor YES clicked by user {user.id}")
    
    # Store preference
    context.user_data['enable_sl_monitor'] = True
    
    # Save the preset
    from database.models.strategy_preset import StrategyPresetCreate
    from database.operations.strategy_ops import create_strategy_preset
    from datetime import datetime
    
    state_data = await state_manager.get_state_data(user.id)
    
    logger.info(f"📋 State data for user {user.id}: {state_data}")
    
    preset_data = StrategyPresetCreate(
        user_id=user.id,
        name=state_data['name'],
        description=state_data.get('description', ''),
        strategy_type='straddle',
        asset=state_data['asset'],
        expiry_code=state_data['expiry_code'],
        direction=state_data['direction'],
        lot_size=state_data['lot_size'],
        sl_trigger_pct=state_data['sl_trigger_pct'],
        sl_limit_pct=state_data['sl_limit_pct'],
        target_trigger_pct=state_data.get('target_trigger_pct', 0.0),
        target_limit_pct=state_data.get('target_limit_pct', 0.0),
        atm_offset=state_data['atm_offset'],
        enable_sl_monitor=True,  # ✅ ENABLED
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    logger.info(f"💾 Saving preset with SL Monitor: {preset_data.enable_sl_monitor}")
    
    result = await create_strategy_preset(preset_data)
    
    if result:
        logger.info(f"✅ Preset saved successfully with ID: {result}")
        
        await query.edit_message_text(
            f"✅ <b>Strategy Saved!</b>\n\n"
            f"<b>Name:</b> {preset_data.name}\n"
            f"<b>Asset:</b> {preset_data.asset}\n"
            f"<b>Direction:</b> {preset_data.direction.title()}\n"
            f"<b>SL Monitor:</b> ✅ Enabled",
            reply_markup=get_straddle_menu_keyboard(),  # ✅ BACK BUTTON
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        context.user_data.clear()
        log_user_action(user.id, "straddle_save", f"Saved: {preset_data.name} (SL Monitor: ON)")
    else:
        logger.error(f"❌ Failed to save preset for user {user.id}")
        await query.edit_message_text(
            "❌ Error saving strategy.",
            reply_markup=get_straddle_menu_keyboard(),  # ✅ BACK BUTTON
            parse_mode='HTML'
        )


@error_handler
async def handle_straddle_sl_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle NO to disable SL monitoring."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"🔴 SL Monitor NO clicked by user {user.id}")
    
    # Store preference
    context.user_data['enable_sl_monitor'] = False
    
    # Save the preset
    from database.models.strategy_preset import StrategyPresetCreate
    from database.operations.strategy_ops import create_strategy_preset
    from datetime import datetime
    
    state_data = await state_manager.get_state_data(user.id)
    
    logger.info(f"📋 State data for user {user.id}: {state_data}")
    
    preset_data = StrategyPresetCreate(
        user_id=user.id,
        name=state_data['name'],
        description=state_data.get('description', ''),
        strategy_type='straddle',
        asset=state_data['asset'],
        expiry_code=state_data['expiry_code'],
        direction=state_data['direction'],
        lot_size=state_data['lot_size'],
        sl_trigger_pct=state_data['sl_trigger_pct'],
        sl_limit_pct=state_data['sl_limit_pct'],
        target_trigger_pct=state_data.get('target_trigger_pct', 0.0),
        target_limit_pct=state_data.get('target_limit_pct', 0.0),
        atm_offset=state_data['atm_offset'],
        enable_sl_monitor=False,  # ✅ DISABLED
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    logger.info(f"💾 Saving preset with SL Monitor: {preset_data.enable_sl_monitor}")
    
    result = await create_strategy_preset(preset_data)
    
    if result:
        logger.info(f"✅ Preset saved successfully with ID: {result}")
        
        await query.edit_message_text(
            f"✅ <b>Strategy Saved!</b>\n\n"
            f"<b>Name:</b> {preset_data.name}\n"
            f"<b>Asset:</b> {preset_data.asset}\n"
            f"<b>Direction:</b> {preset_data.direction.title()}\n"
            f"<b>SL Monitor:</b> ❌ Disabled",
            reply_markup=get_straddle_menu_keyboard(),  # ✅ BACK BUTTON
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        context.user_data.clear()
        log_user_action(user.id, "straddle_save", f"Saved: {preset_data.name} (SL Monitor: OFF)")
    else:
        logger.error(f"❌ Failed to save preset for user {user.id}")
        await query.edit_message_text(
            "❌ Error saving strategy.",
            reply_markup=get_straddle_menu_keyboard(),  # ✅ BACK BUTTON
            parse_mode='HTML'
        )


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
        straddle_cancel_callback,
        pattern="^straddle_cancel$"
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
        straddle_skip_description_callback,
        pattern="^straddle_skip_description$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_skip_target_callback,
        pattern="^straddle_skip_target$"
    ))
    
    # SL Monitor handlers
    application.add_handler(CallbackQueryHandler(
        handle_straddle_sl_yes_callback,
        pattern="^straddle_sl_yes$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        handle_straddle_sl_no_callback,
        pattern="^straddle_sl_no$"
    ))
    
    # Edit/View/Delete handlers
    application.add_handler(CallbackQueryHandler(
        straddle_edit_list_callback,
        pattern="^straddle_edit_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_edit_callback,
        pattern="^straddle_edit_[a-f0-9]{24}$"
    ))
    
    # 🆕 NEW: Edit field handlers
    application.add_handler(CallbackQueryHandler(
        straddle_edit_name_callback,
        pattern="^straddle_edit_name_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_edit_desc_callback,
        pattern="^straddle_edit_desc_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_edit_sl_callback,
        pattern="^straddle_edit_sl_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        straddle_edit_target_callback,
        pattern="^straddle_edit_target_[a-f0-9]{24}$"
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
    
