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
async def strangle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel - return to strangle menu and clear state."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Show strangle menu
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
        [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
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
        [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
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
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
    
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
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
    
    # ✅ Updated examples with correct ETH increment (20)
    if otm_type == 'percentage':
        await query.edit_message_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"OTM Selection: <b>Percentage (Spot-based)</b>\n\n"
            f"Enter OTM percentage:\n\n"
            f"<b>Example:</b> <code>1</code> (for 1%)\n\n"
            f"<i>If spot is $120,000 and you enter 1%:\n"
            f"• Offset: $1,200 (1% of $120,000)\n"
            f"• CE strike: $121,600 (nearest to $121,200)\n"
            f"• PE strike: $118,800 (nearest to $118,800)</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:  # numeral
        asset = state_data.get('asset', 'BTC')
        increment = 200 if asset == 'BTC' else 20  # ✅ FIXED: ETH = 20
        
        await query.edit_message_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"OTM Selection: <b>Numeral (ATM-based)</b>\n\n"
            f"Enter number of strikes away from ATM:\n\n"
            f"<b>Example:</b> <code>4</code> (4 strikes)\n\n"
            f"<i>For {asset} (increment: ${increment}):\n"
            f"If ATM is $120,000:\n"
            f"• CE strike: ${120000 + (4 * increment):,} (4 strikes up)\n"
            f"• PE strike: ${120000 - (4 * increment):,} (4 strikes down)</i>",
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
        # ✅ FIXED: Safe access for both Pydantic and dict
        name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
        description = strategy.description if hasattr(strategy, 'description') else strategy.get('description', '')
        asset = strategy.asset if hasattr(strategy, 'asset') else strategy.get('asset', 'N/A')
        expiry_code = strategy.expiry_code if hasattr(strategy, 'expiry_code') else strategy.get('expiry_code', 'N/A')
        direction = strategy.direction if hasattr(strategy, 'direction') else strategy.get('direction', 'N/A')
        lot_size = strategy.lot_size if hasattr(strategy, 'lot_size') else strategy.get('lot_size', 0)
        sl_trigger = strategy.sl_trigger_pct if hasattr(strategy, 'sl_trigger_pct') else strategy.get('sl_trigger_pct', 0)
        sl_limit = strategy.sl_limit_pct if hasattr(strategy, 'sl_limit_pct') else strategy.get('sl_limit_pct', 0)
        target_trigger = strategy.target_trigger_pct if hasattr(strategy, 'target_trigger_pct') else strategy.get('target_trigger_pct', 0)
        target_limit = strategy.target_limit_pct if hasattr(strategy, 'target_limit_pct') else strategy.get('target_limit_pct', 0)
        
        text += f"<b>📊 {name}</b>\n"
        if description:
            text += f"<i>{description}</i>\n"
        text += f"Asset: {asset} | Expiry: {expiry_code}\n"
        text += f"Direction: {direction.title()} | Lots: {lot_size}\n"
        
        # ✅ FIXED: Safe OTM selection access
        otm_sel = None
        if hasattr(strategy, 'otm_selection'):
            otm_sel = strategy.otm_selection
        elif isinstance(strategy, dict):
            otm_sel = strategy.get('otm_selection')
        
        if otm_sel and isinstance(otm_sel, dict):
            otm_type = otm_sel.get('type', 'percentage')
            otm_value = otm_sel.get('value', 0)
            if otm_type == 'percentage':
                text += f"OTM: {otm_value}% (Spot-based)\n"
            else:
                text += f"OTM: {int(otm_value)} strikes (ATM-based)\n"
        
        text += f"SL: {sl_trigger:.1f}% / {sl_limit:.1f}%\n"
        
        if target_trigger > 0:
            text += f"Target: {target_trigger:.1f}% / {target_limit:.1f}%\n"
        
        text += "\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_strangle_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strangle_view", f"Viewed {len(strategies)} strategies")


# ✅ NEW: Edit List Handler
@error_handler
async def strangle_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of strategies to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>✏️ Edit Strategy</b>\n\n"
            "❌ No strategies found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
        strategy_id = str(strategy.id) if hasattr(strategy, 'id') else str(strategy.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"✏️ {name}",
            callback_data=f"strangle_edit_{strategy_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Strategy</b>\n\n"
        "Select strategy to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ✅ NEW: Edit Strategy Detail View
@error_handler
async def strangle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show strategy details and edit options."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Extract values safely
    name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
    description = strategy.description if hasattr(strategy, 'description') else strategy.get('description', '')
    asset = strategy.asset if hasattr(strategy, 'asset') else strategy.get('asset', 'N/A')
    expiry_code = strategy.expiry_code if hasattr(strategy, 'expiry_code') else strategy.get('expiry_code', 'N/A')
    direction = strategy.direction if hasattr(strategy, 'direction') else strategy.get('direction', 'N/A')
    lot_size = strategy.lot_size if hasattr(strategy, 'lot_size') else strategy.get('lot_size', 0)
    sl_trigger = strategy.sl_trigger_pct if hasattr(strategy, 'sl_trigger_pct') else strategy.get('sl_trigger_pct', 0)
    sl_limit = strategy.sl_limit_pct if hasattr(strategy, 'sl_limit_pct') else strategy.get('sl_limit_pct', 0)
    target_trigger = strategy.target_trigger_pct if hasattr(strategy, 'target_trigger_pct') else strategy.get('target_trigger_pct', 0)
    target_limit = strategy.target_limit_pct if hasattr(strategy, 'target_limit_pct') else strategy.get('target_limit_pct', 0)
    
    # OTM info
    otm_text = "Not set"
    otm_sel = None
    if hasattr(strategy, 'otm_selection'):
        otm_sel = strategy.otm_selection
    elif isinstance(strategy, dict):
        otm_sel = strategy.get('otm_selection')
    
    if otm_sel and isinstance(otm_sel, dict):
        otm_type = otm_sel.get('type', 'percentage')
        otm_value = otm_sel.get('value', 0)
        if otm_type == 'percentage':
            otm_text = f"{otm_value}% (Spot-based)"
        else:
            otm_text = f"{int(otm_value)} strikes (ATM-based)"
    
    text = (
        f"<b>✏️ Edit Strategy</b>\n\n"
        f"<b>Current Settings:</b>\n\n"
        f"Name: <b>{name}</b>\n"
    )
    
    if description:
        text += f"Description: <i>{description}</i>\n"
    
    text += (
        f"Asset: <b>{asset}</b>\n"
        f"Expiry: <b>{expiry_code}</b>\n"
        f"Direction: <b>{direction.title()}</b>\n"
        f"Lot Size: <b>{lot_size}</b>\n"
        f"OTM: <b>{otm_text}</b>\n"
        f"SL: <b>{sl_trigger}% / {sl_limit}%</b>\n"
    )
    
    if target_trigger > 0:
        text += f"Target: <b>{target_trigger}% / {target_limit}%</b>\n"
    
    text += "\n<b>Note:</b> Full editing not yet implemented. Please delete and recreate the strategy."
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to List", callback_data="strangle_edit_list")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Add these AFTER strangle_edit_callback function

@error_handler
async def strangle_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of strategies to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategies
    strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    if not strategies:
        await query.edit_message_text(
            "<b>✏️ Edit Strategy</b>\n\n"
            "❌ No strategies found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
        strategy_id = str(strategy.id) if hasattr(strategy, 'id') else str(strategy.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"✏️ {name}",
            callback_data=f"strangle_edit_{strategy_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_strangle_strategy")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Strategy</b>\n\n"
        "Select strategy to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show strategy with editable fields."""
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
    
    # Extract values safely
    name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
    description = strategy.description if hasattr(strategy, 'description') else strategy.get('description', '')
    asset = strategy.asset if hasattr(strategy, 'asset') else strategy.get('asset', 'N/A')
    expiry_code = strategy.expiry_code if hasattr(strategy, 'expiry_code') else strategy.get('expiry_code', 'N/A')
    direction = strategy.direction if hasattr(strategy, 'direction') else strategy.get('direction', 'N/A')
    lot_size = strategy.lot_size if hasattr(strategy, 'lot_size') else strategy.get('lot_size', 0)
    sl_trigger = strategy.sl_trigger_pct if hasattr(strategy, 'sl_trigger_pct') else strategy.get('sl_trigger_pct', 0)
    sl_limit = strategy.sl_limit_pct if hasattr(strategy, 'sl_limit_pct') else strategy.get('sl_limit_pct', 0)
    target_trigger = strategy.target_trigger_pct if hasattr(strategy, 'target_trigger_pct') else strategy.get('target_trigger_pct', 0)
    target_limit = strategy.target_limit_pct if hasattr(strategy, 'target_limit_pct') else strategy.get('target_limit_pct', 0)
    
    # OTM info
    otm_text = "Not set"
    otm_sel = None
    if hasattr(strategy, 'otm_selection'):
        otm_sel = strategy.otm_selection
    elif isinstance(strategy, dict):
        otm_sel = strategy.get('otm_selection')
    
    if otm_sel and isinstance(otm_sel, dict):
        otm_type = otm_sel.get('type', 'percentage')
        otm_value = otm_sel.get('value', 0)
        if otm_type == 'percentage':
            otm_text = f"{otm_value}% (Spot)"
        else:
            otm_text = f"{int(otm_value)} strikes"
    
    text = (
        f"<b>✏️ Edit Strategy</b>\n\n"
        f"<b>Current Settings:</b>\n\n"
        f"📝 Name: <b>{name}</b>\n"
    )
    
    if description:
        text += f"📄 Description: <i>{description}</i>\n"
    
    text += (
        f"💰 Asset: <b>{asset}</b>\n"
        f"📅 Expiry: <b>{expiry_code}</b>\n"
        f"📊 Direction: <b>{direction.title()}</b>\n"
        f"📦 Lot Size: <b>{lot_size}</b>\n"
        f"🎯 OTM: <b>{otm_text}</b>\n"
        f"🛡️ SL: <b>{sl_trigger}% / {sl_limit}%</b>\n"
    )
    
    if target_trigger > 0:
        text += f"🎯 Target: <b>{target_trigger}% / {target_limit}%</b>\n"
    
    text += "\n<b>Select field to edit:</b>"
    
    # Edit buttons for each field
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data=f"strangle_edit_name_{strategy_id}")],
        [InlineKeyboardButton("📄 Edit Description", callback_data=f"strangle_edit_desc_{strategy_id}")],
        [InlineKeyboardButton("💰 Edit Asset", callback_data=f"strangle_edit_asset_{strategy_id}")],
        [InlineKeyboardButton("📅 Edit Expiry", callback_data=f"strangle_edit_expiry_{strategy_id}")],
        [InlineKeyboardButton("📊 Edit Direction", callback_data=f"strangle_edit_direction_{strategy_id}")],
        [InlineKeyboardButton("📦 Edit Lot Size", callback_data=f"strangle_edit_lot_{strategy_id}")],
        [InlineKeyboardButton("🎯 Edit OTM", callback_data=f"strangle_edit_otm_{strategy_id}")],
        [InlineKeyboardButton("🛡️ Edit SL", callback_data=f"strangle_edit_sl_{strategy_id}")],
        [InlineKeyboardButton("🎯 Edit Target", callback_data=f"strangle_edit_target_{strategy_id}")],
        [InlineKeyboardButton("🔙 Back to List", callback_data="strangle_edit_list")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Name Edit
@error_handler
async def strangle_edit_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing strategy name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Set state
    await state_manager.set_state(user.id, 'strangle_edit_name_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Strategy Name</b>\n\n"
        "Enter new name for this strategy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Lot Size Edit
@error_handler
async def strangle_edit_lot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing lot size."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Set state
    await state_manager.set_state(user.id, 'strangle_edit_lot_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Lot Size</b>\n\n"
        "Enter new lot size:\n\n"
        "Example: <code>2</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Description Edit
@error_handler
async def strangle_edit_desc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing description."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Set state
    await state_manager.set_state(user.id, 'strangle_edit_desc_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Description</b>\n\n"
        "Enter new description:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Asset Edit
@error_handler
async def strangle_edit_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Store for update
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id, 'edit_field': 'asset'})
    
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data=f"strangle_edit_asset_set_btc_{strategy_id}")],
        [InlineKeyboardButton("🔵 ETH", callback_data=f"strangle_edit_asset_set_eth_{strategy_id}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]
    ]
    
    await query.edit_message_text(
        "<b>✏️ Edit Asset</b>\n\n"
        "Select new asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Asset Set
@error_handler
async def strangle_edit_asset_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update asset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    parts = query.data.split('_')
    asset = parts[-2].upper()  # BTC or ETH
    strategy_id = parts[-1]
    
    # Update strategy
    from database.models.strategy_preset import StrategyPresetUpdate
    
    update_data = StrategyPresetUpdate(asset=asset)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await query.answer("✅ Asset updated!", show_alert=True)
        # Return to edit view
        from telegram import CallbackQuery
        query.data = f"strangle_edit_{strategy_id}"
        await strangle_edit_callback(update, context)
    else:
        await query.answer("❌ Update failed", show_alert=True)


# Expiry Edit
@error_handler
async def strangle_edit_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit expiry."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id, 'edit_field': 'expiry'})
    
    keyboard = [
        [InlineKeyboardButton("📅 Daily (D)", callback_data=f"strangle_edit_expiry_set_D_{strategy_id}")],
        [InlineKeyboardButton("📅 Tomorrow (D+1)", callback_data=f"strangle_edit_expiry_set_D+1_{strategy_id}")],
        [InlineKeyboardButton("📆 Weekly (W)", callback_data=f"strangle_edit_expiry_set_W_{strategy_id}")],
        [InlineKeyboardButton("📆 Monthly (M)", callback_data=f"strangle_edit_expiry_set_M_{strategy_id}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]
    ]
    
    await query.edit_message_text(
        "<b>✏️ Edit Expiry</b>\n\n"
        "Select new expiry:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Expiry Set
@error_handler
async def strangle_edit_expiry_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update expiry."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    expiry = parts[-2]  # D, D+1, W, M
    strategy_id = parts[-1]
    
    from database.models.strategy_preset import StrategyPresetUpdate
    
    update_data = StrategyPresetUpdate(expiry_code=expiry)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await query.answer("✅ Expiry updated!", show_alert=True)
        query.data = f"strangle_edit_{strategy_id}"
        await strangle_edit_callback(update, context)
    else:
        await query.answer("❌ Update failed", show_alert=True)


# Direction Edit
@error_handler
async def strangle_edit_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit direction."""
    query = update.callback_query
    await query.answer()
    
    strategy_id = query.data.split('_')[-1]
    
    keyboard = [
        [InlineKeyboardButton("📈 Long", callback_data=f"strangle_edit_dir_set_long_{strategy_id}")],
        [InlineKeyboardButton("📉 Short", callback_data=f"strangle_edit_dir_set_short_{strategy_id}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]
    ]
    
    await query.edit_message_text(
        "<b>✏️ Edit Direction</b>\n\n"
        "Select new direction:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Direction Set
@error_handler
async def strangle_edit_dir_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update direction."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    direction = parts[-2]  # long or short
    strategy_id = parts[-1]
    
    from database.models.strategy_preset import StrategyPresetUpdate
    
    update_data = StrategyPresetUpdate(direction=direction)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await query.answer("✅ Direction updated!", show_alert=True)
        query.data = f"strangle_edit_{strategy_id}"
        await strangle_edit_callback(update, context)
    else:
        await query.answer("❌ Update failed", show_alert=True)


# Add these after the direction edit handler

# SL Edit
@error_handler
async def strangle_edit_sl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing SL."""
    query = update.callback_query
    await query.answer()
    
    strategy_id = query.data.split('_')[-1]
    
    # Set state
    await state_manager.set_state(user.id, 'strangle_edit_sl_trigger_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Stop Loss Trigger</b>\n\n"
        "Enter new SL trigger percentage:\n\n"
        "Example: <code>50</code> (for 50% loss)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# Target Edit
@error_handler
async def strangle_edit_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing target."""
    query = update.callback_query
    await query.answer()
    
    strategy_id = query.data.split('_')[-1]
    
    await state_manager.set_state(user.id, 'strangle_edit_target_trigger_input')
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Target Trigger</b>\n\n"
        "Enter new target trigger percentage:\n\n"
        "Example: <code>100</code> (for 100% profit)\n"
        "Or <code>0</code> to disable",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# OTM Edit
@error_handler
async def strangle_edit_otm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing OTM."""
    query = update.callback_query
    await query.answer()
    
    strategy_id = query.data.split('_')[-1]
    
    await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
    
    keyboard = [
        [InlineKeyboardButton("📊 Percentage", callback_data=f"strangle_edit_otm_type_percentage_{strategy_id}")],
        [InlineKeyboardButton("🔢 Numeral", callback_data=f"strangle_edit_otm_type_numeral_{strategy_id}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]
    ]
    
    await query.edit_message_text(
        "<b>✏️ Edit OTM Selection</b>\n\n"
        "Select OTM method:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def strangle_edit_otm_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTM type selection for edit."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    otm_type = parts[-2]  # percentage or numeral
    strategy_id = parts[-1]
    
    # Store OTM type
    await state_manager.set_state(user.id, 'strangle_edit_otm_value_input')
    await state_manager.set_state_data(user.id, {
        'edit_strategy_id': strategy_id,
        'otm_type': otm_type
    })
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
    
    if otm_type == 'percentage':
        await query.edit_message_text(
            "<b>✏️ Edit OTM Percentage</b>\n\n"
            "Enter new OTM percentage:\n\n"
            "Example: <code>1</code> (for 1%)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "<b>✏️ Edit OTM Strikes</b>\n\n"
            "Enter number of strikes from ATM:\n\n"
            "Example: <code>4</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

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
        name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
        strategy_id = str(strategy.id) if hasattr(strategy, 'id') else str(strategy.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {name}",
            callback_data=f"strangle_delete_{strategy_id}"
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
    
    name = strategy.name if hasattr(strategy, 'name') else strategy.get('name', 'N/A')
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="strangle_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_strangle_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>🗑️ Delete Strategy</b>\n\n"
        f"<b>Name:</b> {name}\n\n"
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
        [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
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
        [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
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
        strangle_cancel_callback,
        pattern="^strangle_cancel$"
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
    
    # ✅ ADD EDIT HANDLERS
    application.add_handler(CallbackQueryHandler(
        strangle_edit_list_callback,
        pattern="^strangle_edit_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_callback,
        pattern="^strangle_edit_[a-f0-9]{24}$"
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
    
    # ✅ ADD EDIT HANDLERS
    application.add_handler(CallbackQueryHandler(
        strangle_edit_list_callback,
        pattern="^strangle_edit_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_callback,
        pattern="^strangle_edit_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_name_callback,
        pattern="^strangle_edit_name_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_desc_callback,
        pattern="^strangle_edit_desc_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_lot_callback,
        pattern="^strangle_edit_lot_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_asset_callback,
        pattern="^strangle_edit_asset_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_asset_set_callback,
        pattern="^strangle_edit_asset_set_(btc|eth)_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_expiry_callback,
        pattern="^strangle_edit_expiry_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_expiry_set_callback,
        pattern="^strangle_edit_expiry_set_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_direction_callback,
        pattern="^strangle_edit_direction_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        strangle_edit_dir_set_callback,
        pattern="^strangle_edit_dir_set_(long|short)_[a-f0-9]{24}$"
    ))

    # Add these at the end of register_strangle_strategy_handlers function

    application.add_handler(CallbackQueryHandler(
        strangle_edit_sl_callback,
        pattern="^strangle_edit_sl_[a-f0-9]{24}$"
    ))

    application.add_handler(CallbackQueryHandler(
        strangle_edit_target_callback,
        pattern="^strangle_edit_target_[a-f0-9]{24}$"
    ))

    application.add_handler(CallbackQueryHandler(
        strangle_edit_otm_callback,
        pattern="^strangle_edit_otm_[a-f0-9]{24}$"
    ))

    application.add_handler(CallbackQueryHandler(
        strangle_edit_otm_type_callback,
        pattern="^strangle_edit_otm_type_(percentage|numeral)_[a-f0-9]{24}$"
    ))

    logger.info("Strangle strategy handlers registered")
