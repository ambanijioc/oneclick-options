"""
Manual move options trade execution handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from database.operations.move_strategy_ops import get_move_strategies, get_move_strategy

logger = setup_logger(__name__)


def get_move_manual_trade_keyboard():
    """Get move manual trade keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_manual_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual move trade menu - select API."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    if not apis:
        await query.edit_message_text(
            "<b>🎯 Manual Move Trade</b>\n\n"
            "❌ No API credentials configured.\n\n"
            "Please add an API credential first.",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with API options
    keyboard = []
    for api in apis:
        keyboard.append([InlineKeyboardButton(
            f"📊 {api.api_name}",
            callback_data=f"move_manual_api_{api.id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_main")])
    
    await query.edit_message_text(
        "<b>🎯 Manual Move Trade</b>\n\n"
        "Select API account for trade execution:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_manual_trade", "Started manual trade flow")


@error_handler
async def move_manual_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API selection - show strategies."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    # Store API ID
    await state_manager.set_state_data(user.id, {'api_id': api_id})
    
    # Get strategies
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_move_manual_trade")]]
        await query.edit_message_text(
            "<b>🎯 Manual Move Trade</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create a strategy first.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Create strategy selection keyboard
    keyboard = []
    for strategy in strategies:
        # Handle both Pydantic and dict
        if hasattr(strategy, 'strategy_name'):
            name = strategy.strategy_name
            strategy_id = str(strategy.id)
        else:
            name = strategy.get('strategy_name', 'N/A')
            strategy_id = str(strategy.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"📊 {name}",
            callback_data=f"move_manual_strategy_{strategy_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move_manual_trade")])
    
    await query.edit_message_text(
        "<b>🎯 Manual Move Trade</b>\n\n"
        "Select strategy to execute:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_manual_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection - show confirmation."""
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
    state_data = await state_manager.get_state_data(user.id)
    state_data['strategy_id'] = strategy_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Handle both Pydantic and dict
    if hasattr(strategy, 'strategy_name'):
        name = strategy.strategy_name
        asset = strategy.asset
        direction = strategy.direction
        lot_size = strategy.lot_size
        atm_offset = strategy.atm_offset
        sl_trigger = getattr(strategy, 'stop_loss_trigger', None)
        sl_limit = getattr(strategy, 'stop_loss_limit', None)
        target_trigger = getattr(strategy, 'target_trigger', None)
        target_limit = getattr(strategy, 'target_limit', None)
    else:
        name = strategy.get('strategy_name', 'N/A')
        asset = strategy.get('asset', 'N/A')
        direction = strategy.get('direction', 'N/A')
        lot_size = strategy.get('lot_size', 0)
        atm_offset = strategy.get('atm_offset', 0)
        sl_trigger = strategy.get('stop_loss_trigger')
        sl_limit = strategy.get('stop_loss_limit')
        target_trigger = strategy.get('target_trigger')
        target_limit = strategy.get('target_limit')
    
    # Show confirmation
    text = "<b>🎯 Confirm Move Trade</b>\n\n"
    text += f"<b>Strategy:</b> {name}\n"
    text += f"<b>Asset:</b> {asset}\n"
    text += f"<b>Direction:</b> {direction.title()}\n"
    text += f"<b>Lot Size:</b> {lot_size}\n"
    text += f"<b>ATM Offset:</b> {atm_offset:+d}\n"
    
    if sl_trigger:
        text += f"<b>Stop Loss:</b> ${sl_trigger:.2f} / ${sl_limit:.2f}\n"
    
    if target_trigger:
        text += f"<b>Target:</b> ${target_trigger:.2f} / ${target_limit:.2f}\n"
    
    text += "\n⚠️ <b>Execute this trade?</b>"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="move_manual_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ✅ ADDED: This function was missing!
@error_handler
async def move_manual_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the trade."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # TODO: Implement actual trade execution
    
    await query.edit_message_text(
        "<b>✅ Trade Execution</b>\n\n"
        "⏳ Executing trade...\n\n"
        "🚧 <i>Trade execution logic to be implemented</i>",
        reply_markup=get_move_manual_trade_keyboard(),
        parse_mode='HTML'
    )
    
    await state_manager.clear_state(user.id)
    
    log_user_action(user.id, "move_manual_execute", "Executed move trade")


def register_move_manual_trade_handlers(application: Application):
    """Register move manual trade handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_manual_trade_menu_callback,
        pattern="^menu_move_manual_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_api_callback,
        pattern="^move_manual_api_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_strategy_callback,
        pattern="^move_manual_strategy_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_confirm_callback,
        pattern="^move_manual_confirm$"
    ))
    
    logger.info("Move manual trade handlers registered")
    
