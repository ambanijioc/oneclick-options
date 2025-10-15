"""
Auto move options trade execution handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.api_ops import get_api_credentials
from database.operations.move_strategy_ops import (
    get_move_strategies,
    create_move_auto_execution,
    get_move_auto_executions,
    delete_move_auto_execution
)

logger = setup_logger(__name__)
#state_manager = StateManager()


def get_move_auto_trade_keyboard():
    """Get move auto trade keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Schedule", callback_data="move_auto_add")],
        [InlineKeyboardButton("✏️ Edit Schedule", callback_data="move_auto_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Schedule", callback_data="move_auto_delete_list")],
        [InlineKeyboardButton("👁️ View Schedules", callback_data="move_auto_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_auto_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display auto trade menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    await query.edit_message_text(
        "<b>⏰ Auto Move Trade Execution</b>\n\n"
        "Schedule automated move option trades:\n\n"
        "• <b>Add:</b> Schedule new trade\n"
        "• <b>Edit:</b> Modify schedule\n"
        "• <b>Delete:</b> Remove schedule\n"
        "• <b>View:</b> See all schedules\n\n"
        "Select an option:",
        reply_markup=get_move_auto_trade_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_auto_trade", "Viewed auto trade menu")


@error_handler
async def move_auto_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add schedule flow - select API."""
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
            "<b>➕ Add Auto Trade Schedule</b>\n\n"
            "❌ No API credentials configured.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with API options
    keyboard = []
    for api in apis:
        keyboard.append([InlineKeyboardButton(
            f"📊 {api.api_name}",
            callback_data=f"move_auto_api_{api.id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")])
    
    await query.edit_message_text(
        "<b>➕ Add Auto Trade Schedule</b>\n\n"
        "Select API account:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_move_auto_trade")]]
        await query.edit_message_text(
            "<b>➕ Add Auto Trade Schedule</b>\n\n"
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
            callback_data=f"move_auto_strategy_{strategy['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move_auto_trade")])
    
    await query.edit_message_text(
        "<b>➕ Add Auto Trade Schedule</b>\n\n"
        "Select strategy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection - ask for time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Store strategy ID
    state_data = await state_manager.get_state_data(user.id)
    state_data['strategy_id'] = strategy_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for execution time
    await state_manager.set_state(user.id, 'move_auto_add_time')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")]]
    
    await query.edit_message_text(
        "<b>➕ Add Auto Trade Schedule</b>\n\n"
        "Enter execution time (IST):\n\n"
        "Format: <code>HH:MM AM</code> or <code>HH:MM PM</code>\n\n"
        "Examples:\n"
        "• <code>09:30 AM</code>\n"
        "• <code>03:15 PM</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all scheduled auto trades."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get schedules
    schedules = await get_move_auto_executions(user.id)
    
    if not schedules:
        await query.edit_message_text(
            "<b>👁️ Auto Trade Schedules</b>\n\n"
            "❌ No schedules found.\n\n"
            "Create one using <b>Add Schedule</b>.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Get API credentials for display
    apis = await get_api_credentials(user.id)
    api_map = {str(api.id): api.api_name for api in apis}
    
    text = "<b>👁️ Auto Trade Schedules</b>\n\n"
    
    for schedule in schedules:
        api_name = api_map.get(schedule['api_credential_id'], 'Unknown')
        status = "✅ Enabled" if schedule.get('enabled', True) else "❌ Disabled"
        
        text += f"<b>📊 {schedule['strategy_name']}</b>\n"
        text += f"API: {api_name}\n"
        text += f"Time: {schedule['execution_time']} IST\n"
        text += f"Status: {status}\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_move_auto_trade_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_auto_view", f"Viewed {len(schedules)} schedules")


@error_handler
async def move_auto_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of schedules to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get schedules
    schedules = await get_move_auto_executions(user.id)
    
    if not schedules:
        await query.edit_message_text(
            "<b>🗑️ Delete Schedule</b>\n\n"
            "❌ No schedules found.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with schedules
    keyboard = []
    for schedule in schedules:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {schedule['strategy_name']} - {schedule['execution_time']}",
            callback_data=f"move_auto_delete_{schedule['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Schedule</b>\n\n"
        "Select schedule to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete schedule - ask confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    schedule_id = query.data.split('_')[-1]
    
    # Store schedule ID
    await state_manager.set_state_data(user.id, {'delete_schedule_id': schedule_id})
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="move_auto_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_auto_trade")]
    ]
    
    await query.edit_message_text(
        "<b>🗑️ Delete Schedule</b>\n\n"
        "⚠️ Are you sure you want to delete this schedule?\n\n"
        "This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete schedule."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get schedule ID
    state_data = await state_manager.get_state_data(user.id)
    schedule_id = state_data.get('delete_schedule_id')
    
    if not schedule_id:
        await query.edit_message_text("❌ Schedule not found")
        return
    
    # Delete schedule
    success = await delete_move_auto_execution(schedule_id)
    
    if success:
        await query.edit_message_text(
            "<b>🗑️ Delete Schedule</b>\n\n"
            "✅ Schedule deleted successfully!",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_auto_delete", f"Deleted schedule {schedule_id}")
    else:
        await query.edit_message_text(
            "<b>🗑️ Delete Schedule</b>\n\n"
            "❌ Failed to delete schedule.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


def register_move_auto_trade_handlers(application: Application):
    """Register move auto trade handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_auto_trade_menu_callback,
        pattern="^menu_move_auto_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_add_callback,
        pattern="^move_auto_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_api_callback,
        pattern="^move_auto_api_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_strategy_callback,
        pattern="^move_auto_strategy_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_view_callback,
        pattern="^move_auto_view$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_delete_list_callback,
        pattern="^move_auto_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_delete_callback,
        pattern="^move_auto_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_delete_confirm_callback,
        pattern="^move_auto_delete_confirm$"
    ))
    
    logger.info("Move auto trade handlers registered")
      
