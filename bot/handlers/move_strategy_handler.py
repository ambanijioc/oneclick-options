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
#state_manager = StateManager()


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
    
    await query.edit_message_text(
        "<b>🎯 Move Options Strategy Management</b>\n\n"
        "Manage your Move Options trading strategies:\n\n"
        "• <b>Add:</b> Create new strategy preset\n"
        "• <b>Edit:</b> Modify existing strategy\n"
        "• <b>Delete:</b> Remove strategy\n"
        "• <b>View:</b> See all strategies\n\n"
        "Select an option:",
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
async def move_strategy_add_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[-1]  # btc or eth
    
    # Store asset
    state_data = await state_manager.get_state_data(user.id)
    state_data['asset'] = asset.upper()
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for direction
    keyboard = [
        [InlineKeyboardButton("📈 Long", callback_data="move_strategy_direction_long")],
        [InlineKeyboardButton("📉 Short", callback_data="move_strategy_direction_short")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]
    ]
    
    await query.edit_message_text(
        f"<b>➕ Add Move Strategy</b>\n\n"
        f"Asset: <b>{asset.upper()}</b>\n\n"
        f"Select trading direction:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_strategy_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_strategy")]]
    
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
        text += f"<b>📊 {strategy['strategy_name']}</b>\n"
        text += f"Asset: {strategy['asset']}\n"
        text += f"Direction: {strategy['direction'].title()}\n"
        text += f"Lot Size: {strategy['lot_size']}\n"
        text += f"ATM Offset: {strategy['atm_offset']:+d}\n"
        
        if strategy.get('stop_loss_trigger'):
            text += f"SL: Trigger ${strategy['stop_loss_trigger']:.2f}, Limit ${strategy['stop_loss_limit']:.2f}\n"
        
        if strategy.get('target_trigger'):
            text += f"Target: Trigger ${strategy['target_trigger']:.2f}, Limit ${strategy['target_limit']:.2f}\n"
        
        text += "\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_move_strategy_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy_view", f"Viewed {len(strategies)} strategies")


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
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_add_asset_callback,
        pattern="^move_strategy_asset_(btc|eth)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_direction_callback,
        pattern="^move_strategy_direction_(long|short)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_strategy_view_callback,
        pattern="^move_strategy_view$"
    ))
    
    logger.info("Move strategy handlers registered")
    
