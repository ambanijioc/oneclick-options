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
#state_manager = StateManager()


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
        keyboard.append([InlineKeyboardButton(
            f"📊 {strategy['strategy_name']}",
            callback_data=f"move_manual_strategy_{strategy['id']}"
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
    
    # Show confirmation
    text = "<b>🎯 Confirm Move Trade</b>\n\n"
    text += f"<b>Strategy:</b> {strategy['strategy_name']}\n"
    text += f"<b>Asset:</b> {strategy['asset']}\n"
    text += f"<b>Direction:</b> {strategy['direction'].title()}\n"
    text += f"<b>Lot Size:</b> {strategy['lot_size']}\n"
    text += f"<b>ATM Offset:</b> {strategy['atm_offset']:+d}\n"
    
    if strategy.get('stop_loss_trigger'):
        text += f"<b>Stop Loss:</b> ${strategy['stop_loss_trigger']:.2f} / ${strategy['stop_loss_limit']:.2f}\n"
    
    if strategy.get('target_trigger'):
        text += f"<b>Target:</b> ${strategy['target_trigger']:.2f} / ${strategy['target_limit']:.2f}\n"
    
    text += "\n⚠️ Execute this trade?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="move_manual_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


def register_move_manual_trade_handlers(application: Application):
    """Register move manual trade handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_manual_trade_menu_callback,
        pattern="^menu_move_manual_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_api_callback,
        pattern="^move_manual_api_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_strategy_callback,
        pattern="^move_manual_strategy_"
    ))
    
    logger.info("Move manual trade handlers registered")
      
