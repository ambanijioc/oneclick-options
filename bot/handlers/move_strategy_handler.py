"""
Move options strategy management handlers.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_strategy,
    get_move_strategies,
    get_move_strategy,
    update_move_strategy,
    delete_move_strategy
)

logger = setup_logger(__name__)


def get_move_strategy_menu_keyboard():
    """Get move strategy management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data="move_strategy_add")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="move_strategy_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="move_strategy_delete_list")],
        [InlineKeyboardButton("👁️ View Strategies", callback_data="move_strategy_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle move strategy management menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get strategies
    strategies = await get_move_strategies(user.id)
    
    await query.edit_message_text(
        "<b>🎯 Move Options Strategy Management</b>\n\n"
        "Manage your Move Options trading strategies:\n\n"
        "• <b>Add:</b> Create new strategy preset\n"
        "• <b>Edit:</b> Modify existing strategy\n"
        "• <b>Delete:</b> Remove strategy\n"
        "• <b>View:</b> See all strategies\n\n"
        f"<b>Total Strategies:</b> {len(strategies)}",
        reply_markup=get_move_strategy_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_menu", "Viewed strategy management menu")


@error_handler
async def move_strategy_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add strategy flow - ask for strategy name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'move_strategy_add_name')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]]
    
    await query.edit_message_text(
        "<b>➕ Add Move Strategy</b>\n\n"
        "Please enter a name for this strategy:\n\n"
        "Example: <code>BTC Long Move</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_add", "Started add strategy flow")


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
        "<b>🎯 Move Options Strategy Management</b>\n\n"
        "Manage your Move Options trading strategies:\n\n"
        "• <b>Add:</b> Create new strategy preset\n"
        "• <b>Edit:</b> Modify existing strategy\n"
        "• <b>Delete:</b> Remove strategy\n"
        "• <b>View:</b> See all strategies\n\n"
        f"<b>Total Strategies:</b> {len(strategies)}",
        reply_markup=get_move_strategy_menu_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("🟠 BTC", callback_data="move_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="move_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Name: <b>{state_data['strategy_name']}</b>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip target."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Set target to 0
    state_data = await state_manager.get_state_data(user.id)
    state_data['target_trigger_pct'] = 0
    state_data['target_limit_pct'] = 0
    await state_manager.set_state_data(user.id, state_data)
    await state_manager.set_state(user.id, 'move_strategy_add_atm_offset')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
    
    await query.edit_message_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Enter ATM offset (in strikes):\n\n"
        f"• <code>0</code> = ATM (At The Money)\n"
        f"• <code>+1</code> = 1 strike above ATM (BTC: $200, ETH: $20)\n"
        f"• <code>-1</code> = 1 strike below ATM\n"
        f"• <code>+5</code> = 5 strikes above ATM (BTC: $1000, ETH: $100)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[-1].upper()  # BTC or ETH
    
    # Store asset
    state_data = await state_manager.get_state_data(user.id)
    state_data['asset'] = asset
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for direction
    keyboard = [
        [InlineKeyboardButton("📈 Long", callback_data="move_direction_long")],
        [InlineKeyboardButton("📉 Short", callback_data="move_direction_short")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Name: <b>{state_data['strategy_name']}</b>\n"
        f"Asset: <b>{asset}</b>\n\n"
        f"Select trading direction:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await state_manager.set_state(user.id, 'move_strategy_add_lot_size')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="move_cancel")]]
    
    await query.edit_message_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Asset: <b>{state_data['asset']}</b>\n"
        f"Direction: <b>{direction.title()}</b>\n\n"
        f"Enter lot size (number of contracts):\n\n"
        f"Example: <code>1</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
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
            "<b>👁️ Move Strategies</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create one using <b>Add Strategy</b>.",
            reply_markup=get_move_strategy_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    text = "<b>👁️ Move Strategies</b>\n\n"
    
    for strategy in strategies:
        # ✅ Use dot notation for Pydantic models OR dict access
        name = strategy.strategy_name if hasattr(strategy, 'strategy_name') else strategy.get('strategy_name')
        asset = strategy.asset if hasattr(strategy, 'asset') else strategy.get('asset')
        direction = strategy.direction if hasattr(strategy, 'direction') else strategy.get('direction')
        lot_size = strategy.lot_size if hasattr(strategy, 'lot_size') else strategy.get('lot_size')
        atm_offset = strategy.atm_offset if hasattr(strategy, 'atm_offset') else strategy.get('atm_offset')
        
        text += f"<b>📊 {name}</b>\n"
        if hasattr(strategy, 'description') and strategy.description:
            text += f"<i>{strategy.description}</i>\n"
        elif strategy.get('description'):
            text += f"<i>{strategy.get('description')}</i>\n"
        
        text += f"Asset: {asset}\n"
        text += f"Direction: {direction.title()}\n"
        text += f"Lot Size: {lot_size}\n"
        text += f"ATM Offset: {atm_offset:+d}\n"
        
        # SL percentages
        sl_trigger = strategy.sl_trigger_pct if hasattr(strategy, 'sl_trigger_pct') else strategy.get('sl_trigger_pct')
        sl_limit = strategy.sl_limit_pct if hasattr(strategy, 'sl_limit_pct') else strategy.get('sl_limit_pct')
        
        if sl_trigger is not None:
            text += f"SL: {sl_trigger}% / {sl_limit}%\n"
        
        # Target percentages
        target_trigger = strategy.target_trigger_pct if hasattr(strategy, 'target_trigger_pct') else strategy.get('target_trigger_pct', 0)
        target_limit = strategy.target_limit_pct if hasattr(strategy, 'target_limit_pct') else strategy.get('target_limit_pct', 0)
        
        if target_trigger and target_trigger > 0:
            text += f"Target: {target_trigger}% / {target_limit}%\n"
        
        text += "\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_move_strategy_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_view", f"Viewed {len(strategies)} strategies")


@error_handler
async def move_strategy_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of strategies to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get strategies
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "<b>🗑️ Delete Strategy</b>\n\n"
            "❌ No strategies found.",
            reply_markup=get_move_strategy_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        name = strategy.strategy_name if hasattr(strategy, 'strategy_name') else strategy.get('strategy_name')
        strategy_id = str(strategy.id) if hasattr(strategy, 'id') else str(strategy.get('_id'))
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {name}",
            callback_data=f"move_delete_{strategy_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Strategy</b>\n\n"
        "Select strategy to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete strategy - ask confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Get strategy
    strategy = await get_move_strategy(strategy_id)
    
    if not strategy:
        await query.edit_message_text("❌ Strategy not found")
        return
    
    # Store strategy ID
    await state_manager.set_state_data(user.id, {'delete_strategy_id': strategy_id})
    
    name = strategy.strategy_name if hasattr(strategy, 'strategy_name') else strategy.get('strategy_name')
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="move_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_strategy")]
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
async def move_strategy_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    success = await delete_move_strategy(strategy_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Strategy Deleted</b>\n\n"
            "The strategy has been deleted successfully.",
            reply_markup=get_move_strategy_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_delete", f"Deleted strategy {strategy_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete strategy.",
            reply_markup=get_move_strategy_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


def register_move_strategy_handlers(application: Application):
    """Register move strategy handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_menu_callback,
        pattern="^menu_move_strategy$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_add_callback,
        pattern="^move_strategy_add$"
    ))
    
    # ✅ ADD CANCEL HANDLER
    application.add_handler(CallbackQueryHandler(
        move_cancel_callback,
        pattern="^move_cancel$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_skip_description_callback,
        pattern="^move_skip_description$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_skip_target_callback,
        pattern="^move_skip_target$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_asset_callback,
        pattern="^move_asset_(btc|eth)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_direction_callback,
        pattern="^move_direction_(long|short)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_view_callback,
        pattern="^move_strategy_view$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_delete_list_callback,
        pattern="^move_strategy_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_delete_callback,
        pattern="^move_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_delete_confirm_callback,
        pattern="^move_delete_confirm$"
    ))
    
    logger.info("Move strategy handlers registered")
