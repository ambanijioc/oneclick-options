"""
Strangle strategy management handlers.
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


def get_strangle_menu_keyboard():
    """Get strangle strategy management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data="strangle_add")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="strangle_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="strangle_delete_list")],
        [InlineKeyboardButton("👁️ View Strategies", callback_data="strangle_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def strangle_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display strangle strategy management menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    await query.edit_message_text(
        "<b>🎯 Strangle Strategy Management</b>\n\n"
        "Manage your OTM strangle trading strategies:\n\n"
        "• <b>Add:</b> Create new strategy\n"
        "• <b>Edit:</b> Modify existing strategy\n"
        "• <b>Delete:</b> Remove strategy\n"
        "• <b>View:</b> See all strategies\n\n"
        f"<b>Total Strategies:</b> {len(strategies)}",
        reply_markup=get_strangle_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strangle_menu", f"Viewed strangle menu: {len(strategies)} strategies")


@error_handler
async def strangle_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add strangle strategy flow - ask for name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'strangle_add_name')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
    
    await query.edit_message_text(
        "<b>➕ Add Strangle Strategy</b>\n\n"
        "Please enter a name for this strategy:\n\n"
        "Example: <code>BTC Weekly Strangle</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strangle_add", "Started add strategy flow")


@error_handler
async def strangle_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("📅 Daily (D)", callback_data="strangle_expiry_D")],
        [InlineKeyboardButton("📅 Tomorrow (D+1)", callback_data="strangle_expiry_D+1")],
        [InlineKeyboardButton("📆 Weekly (W)", callback_data="strangle_expiry_W")],
        [InlineKeyboardButton("📆 Monthly (M)", callback_data="strangle_expiry_M")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Asset: <b>{asset}</b>\n\n"
        f"Select expiry:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("📈 Long", callback_data="strangle_direction_long")],
        [InlineKeyboardButton("📉 Short", callback_data="strangle_direction_short")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Asset: <b>{state_data['asset']}</b>\n"
        f"Expiry: <b>{expiry}</b>\n\n"
        f"Select direction:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await state_manager.set_state(user.id, 'strangle_add_lot_size')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
    
    await query.edit_message_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Asset: <b>{state_data['asset']}</b>\n"
        f"Expiry: <b>{state_data['expiry_code']}</b>\n"
        f"Direction: <b>{direction.title()}</b>\n\n"
        f"Enter lot size (number of contracts):\n\n"
        f"Example: <code>1</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_otm_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTM selection type."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    otm_type = query.data.split('_')[-1]  # percentage or numeral
    
    # Store OTM type
    state_data = await state_manager.get_state_data(user.id)
    state_data['otm_type'] = otm_type
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for OTM value
    await state_manager.set_state(user.id, 'strangle_add_otm_value')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]]
    
    if otm_type == 'percentage':
        await query.edit_message_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"OTM Selection: <b>Percentage (Spot-based)</b>\n\n"
            f"Enter OTM percentage:\n\n"
            f"<b>Example:</b> <code>1</code> (for 1%)\n\n"
            f"<i>If spot is $120,000 and you enter 1%:\n"
            f"• CE strike: $121,200 (120000 + 1200)\n"
            f"• PE strike: $118,800 (120000 - 1200)</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:  # numeral
        await query.edit_message_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"OTM Selection: <b>Numeral (ATM-based)</b>\n\n"
            f"Enter number of strikes away from ATM:\n\n"
            f"<b>Example:</b> <code>4</code> (4 strikes)\n\n"
            f"<i>If spot is $120,150 (ATM $120,200):\n"
            f"• CE strike: $121,000 (4 strikes up)\n"
            f"• PE strike: $119,400 (4 strikes down)</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


@error_handler
async def strangle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all strangle strategies."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>👁️ Strangle Strategies</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create one using <b>Add Strategy</b>.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    text = "<b>👁️ Strangle Strategies</b>\n\n"
    
    for strategy in strategies:
        text += f"<b>📊 {strategy['name']}</b>\n"
        if strategy.get('description'):
            text += f"<i>{strategy['description']}</i>\n"
        text += f"Asset: {strategy['asset']} | Expiry: {strategy['expiry_code']}\n"
        text += f"Direction: {strategy['direction'].title()} | Lots: {strategy['lot_size']}\n"
        
        # OTM selection
        otm_sel = strategy.get('otm_selection', {})
        if otm_sel:
            otm_type = otm_sel.get('type', 'percentage')
            otm_value = otm_sel.get('value', 0)
            if otm_type == 'percentage':
                text += f"OTM: {otm_value}% (Spot-based)\n"
            else:
                text += f"OTM: {int(otm_value)} strikes (ATM-based)\n"
        
        text += f"SL: {strategy['sl_trigger_pct']:.1f}% / {strategy['sl_limit_pct']:.1f}%\n"
        
        if strategy.get('target_trigger_pct', 0) > 0:
            text += f"Target: {strategy['target_trigger_pct']:.1f}% / {strategy['target_limit_pct']:.1f}%\n"
        
        text += "\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_strangle_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strangle_view", f"Viewed {len(strategies)} strategies")


@error_handler
async def strangle_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of strategies to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>🗑️ Delete Strategy</b>\n\n"
            "❌ No strategies found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {strategy['name']}",
            callback_data=f"strangle_delete_{strategy['_id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Strategy</b>\n\n"
        "Select strategy to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="strangle_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_strangle_strategy")]
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
async def strangle_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "strangle_delete", f"Deleted strategy {strategy_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete strategy.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


@error_handler
async def strangle_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("🟠 BTC", callback_data="strangle_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="strangle_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Name: <b>{state_data['name']}</b>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip target."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Set target to 0
    state_data = await state_manager.get_state_data(user.id)
    state_data['target_trigger_pct'] = 0
    state_data['target_limit_pct'] = 0
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for OTM selection type
    keyboard = [
        [InlineKeyboardButton("📊 Percentage (Spot-based)", callback_data="strangle_otm_percentage")],
        [InlineKeyboardButton("🔢 Numeral (ATM-based)", callback_data="strangle_otm_numeral")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Select OTM strike selection method:\n\n"
        f"<b>Percentage:</b> Based on spot price\n"
        f"<i>Example: 1% of $120,000 = $1,200 offset</i>\n\n"
        f"<b>Numeral:</b> Based on number of strikes from ATM\n"
        f"<i>Example: 4 strikes away from ATM</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


def register_strangle_strategy_handlers(application: Application):
    """Register strangle strategy handlers."""
    
    application.add_handler(CallbackQueryHandler(
        strangle_strategy_menu_callback,
        pattern="^menu_strangle_strategy$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_add_callback,
        pattern="^strangle_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_asset_callback,
        pattern="^strangle_asset_(btc|eth)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_expiry_callback,
        pattern="^strangle_expiry_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_direction_callback,
        pattern="^strangle_direction_(long|short)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_otm_type_callback,
        pattern="^strangle_otm_(percentage|numeral)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_view_callback,
        pattern="^strangle_view$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_delete_list_callback,
        pattern="^strangle_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_delete_callback,
        pattern="^strangle_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_delete_confirm_callback,
        pattern="^strangle_delete_confirm$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_skip_description_callback,
        pattern="^strangle_skip_description$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_skip_target_callback,
        pattern="^strangle_skip_target$"
    ))
    
    logger.info("Strangle strategy handlers registered")
  
