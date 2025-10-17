"""
Auto move options trade execution handler - uses Move Trade Presets.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_trade_preset_ops import get_move_trade_presets, get_move_trade_preset_by_id
from database.operations.move_strategy_ops import create_move_auto_execution, get_move_auto_executions, delete_move_auto_execution

logger = setup_logger(__name__)


def get_move_auto_trade_keyboard():
    """Get move auto trade keyboard."""
    keyboard = [
        [InlineKeyboardButton("📊 List Current Schedules", callback_data="move_auto_list")],
        [InlineKeyboardButton("➕ Add Schedule", callback_data="move_auto_add")],
        [InlineKeyboardButton("✏️ Edit Schedule", callback_data="move_auto_edit_list")],  # ✅ ADD THIS LINE!
        [InlineKeyboardButton("🗑️ Delete Schedule", callback_data="move_auto_delete_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_auto_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display auto move trade menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get active schedules count
    schedules = await get_move_auto_executions(user.id)
    
    await query.edit_message_text(
        "<b>⏰ Auto Move Trade Execution</b>\n\n"
        "Automate your move option trades with scheduled execution:\n\n"
        "• <b>List:</b> View running schedules\n"
        "• <b>Add:</b> Create new schedule\n"
        "• <b>Delete:</b> Remove schedule\n\n"
        f"<b>Active Schedules:</b> {len(schedules)}",
        reply_markup=get_move_auto_trade_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_auto_trade_menu", f"Viewed move auto trade menu: {len(schedules)} schedules")


@error_handler
async def move_auto_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all current auto move trade schedules."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get schedules
    schedules = await get_move_auto_executions(user.id)
    
    if not schedules:
        await query.edit_message_text(
            "<b>📊 Current Auto Move Trade Schedules</b>\n\n"
            "❌ No active schedules.\n\n"
            "Create one using <b>Add Schedule</b>.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Build list
    text = "<b>📊 Current Auto Move Trade Schedules</b>\n\n"
    
    for idx, schedule in enumerate(schedules, 1):
        # Get preset name
        preset = await get_move_trade_preset_by_id(schedule.get('preset_id', ''))
        preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
        
        text += f"<b>{idx}. {preset_name}</b>\n"
        text += f"⏰ Time: {schedule.get('execution_time', 'N/A')} IST\n"
        text += f"📍 Status: {'✅ Active' if schedule.get('enabled', True) else '❌ Disabled'}\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_move_auto_trade_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add schedule flow - list Move Trade Presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get move trade presets
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>➕ Add Auto Move Trade Schedule</b>\n\n"
            "❌ No Move Trade Presets found.\n\n"
            "Please create a Move Trade Preset first using the menu.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"move_auto_preset_{preset['_id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")])
    
    await query.edit_message_text(
        "<b>➕ Add Auto Move Trade Schedule</b>\n\n"
        "Select a Move Trade Preset to automate:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_auto_add", "Started add schedule flow")


@error_handler
async def move_auto_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - ask for time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Store preset ID
    from bot.utils.state_manager import state_manager
    await state_manager.set_state_data(user.id, {'preset_id': preset_id})
    await state_manager.set_state(user.id, 'move_auto_add_time')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")]]
    
    await query.edit_message_text(
        "<b>➕ Add Auto Move Trade Schedule</b>\n\n"
        "Enter execution time in IST (24-hour format):\n\n"
        "<b>Format:</b> <code>HH:MM</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>09:15</code> - 9:15 AM\n"
        "• <code>15:30</code> - 3:30 PM\n"
        "• <code>23:45</code> - 11:45 PM",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def handle_move_auto_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle time input for move auto trade setup."""
    user = update.effective_user
    
    # Validate time format (HH:MM)
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        await update.message.reply_text(
            "<b>❌ Invalid Time Format</b>\n\n"
            "Please enter time in <code>HH:MM</code> format (24-hour).\n\n"
            "<b>Examples:</b>\n"
            "• <code>09:15</code>\n"
            "• <code>15:30</code>\n"
            "• <code>23:45</code>",
            parse_mode='HTML'
        )
        return
    
    # Store time
    from bot.utils.state_manager import state_manager
    state_data = await state_manager.get_state_data(user.id)
    state_data['execution_time'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Get preset details for confirmation
    preset = await get_move_trade_preset_by_id(state_data['preset_id'])
    
    if not preset:
        await update.message.reply_text("❌ Preset not found")
        await state_manager.clear_state(user.id)
        return
    
    # Show confirmation
    text_msg = (
        f"<b>➕ Confirm Auto Move Trade Schedule</b>\n\n"
        f"<b>Preset:</b> {preset['preset_name']}\n"
        f"<b>Execution Time:</b> {text} IST\n\n"
        f"⚠️ This will execute automatically every day at the specified time.\n\n"
        f"Confirm to create?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="move_auto_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_auto_trade")]
    ]
    
    await update.message.reply_text(
        text_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    # DON'T clear state yet - need it for confirmation
    
    log_user_action(user.id, "move_auto_time", f"Set execution time: {text}")


@error_handler
async def move_auto_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and create move auto trade schedule."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get state data
    from bot.utils.state_manager import state_manager
    state_data = await state_manager.get_state_data(user.id)
    
    if not state_data or not state_data.get('preset_id'):
        await query.edit_message_text(
            "❌ Missing data. Please start again.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        return
    
    # Create auto execution
    result = await create_move_auto_execution(user.id, state_data)
    
    if result:
        await query.edit_message_text(
            f"<b>✅ Auto Move Trade Schedule Created</b>\n\n"
            f"<b>Execution Time:</b> {state_data['execution_time']} IST\n\n"
            f"🤖 The bot is now monitoring and will automatically execute this trade daily at the scheduled time.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_auto_create", f"Created schedule for {state_data['execution_time']}")
    else:
        await query.edit_message_text(
            "<b>❌ Failed to Create Schedule</b>\n\n"
            "Please try again.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


@error_handler
async def move_auto_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of schedules to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get schedules
    schedules = await get_move_auto_executions(user.id)
    
    if not schedules:
        await query.edit_message_text(
            "<b>✏️ Edit Schedule</b>\n\n"
            "❌ No active schedules found.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with schedules
    keyboard = []
    for schedule in schedules:
        preset = await get_move_trade_preset_by_id(schedule.get('preset_id', ''))
        preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
        
        keyboard.append([InlineKeyboardButton(
            f"✏️ {preset_name} - {schedule.get('execution_time', 'N/A')}",
            callback_data=f"move_auto_edit_{schedule['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Schedule</b>\n\n"
        "Select schedule to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit flow - select new preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    schedule_id = query.data.split('_')[-1]
    
    # Store schedule ID for edit
    from bot.utils.state_manager import state_manager
    await state_manager.set_state_data(user.id, {'edit_schedule_id': schedule_id})
    
    # Get move trade presets
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>✏️ Edit Schedule</b>\n\n"
            "❌ No Move Trade Presets found.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"move_auto_edit_preset_{preset['_id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Schedule</b>\n\n"
        "Select new Move Trade Preset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_edit_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit preset selection - ask for time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Store preset ID
    from bot.utils.state_manager import state_manager
    state_data = await state_manager.get_state_data(user.id)
    state_data['preset_id'] = preset_id
    await state_manager.set_state_data(user.id, state_data)
    await state_manager.set_state(user.id, 'move_auto_edit_time')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_auto_trade")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Schedule</b>\n\n"
        "Enter new execution time in IST (24-hour format):\n\n"
        "<b>Format:</b> <code>HH:MM</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>09:15</code> - 9:15 AM\n"
        "• <code>15:30</code> - 3:30 PM\n"
        "• <code>23:45</code> - 11:45 PM",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def handle_move_auto_edit_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle time input for editing move auto trade setup."""
    user = update.effective_user
    
    # Validate time format (HH:MM)
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        await update.message.reply_text(
            "<b>❌ Invalid Time Format</b>\n\n"
            "Please enter time in <code>HH:MM</code> format (24-hour).\n\n"
            "<b>Examples:</b>\n"
            "• <code>09:15</code>\n"
            "• <code>15:30</code>\n"
            "• <code>23:45</code>",
            parse_mode='HTML'
        )
        return
    
    # Store time
    from bot.utils.state_manager import state_manager
    state_data = await state_manager.get_state_data(user.id)
    state_data['execution_time'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Get preset details for confirmation
    preset = await get_move_trade_preset_by_id(state_data['preset_id'])
    
    if not preset:
        await update.message.reply_text("❌ Preset not found")
        await state_manager.clear_state(user.id)
        return
    
    # Show confirmation
    text_msg = (
        f"<b>✏️ Confirm Edit Schedule</b>\n\n"
        f"<b>New Preset:</b> {preset['preset_name']}\n"
        f"<b>New Execution Time:</b> {text} IST\n\n"
        f"Confirm to update?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="move_auto_edit_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_auto_trade")]
    ]
    
    await update.message.reply_text(
        text_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_auto_edit_time", f"Set new execution time: {text}")


@error_handler
async def move_auto_edit_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and update move auto trade schedule."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get state data
    from bot.utils.state_manager import state_manager
    state_data = await state_manager.get_state_data(user.id)
    schedule_id = state_data.get('edit_schedule_id')
    
    if not schedule_id:
        await query.edit_message_text("❌ Schedule not found")
        return
    
    # Update schedule
    from database.operations.move_strategy_ops import update_move_auto_execution
    result = await update_move_auto_execution(schedule_id, state_data)
    
    if result:
        await query.edit_message_text(
            f"<b>✅ Schedule Updated</b>\n\n"
            f"<b>New Execution Time:</b> {state_data['execution_time']} IST\n\n"
            f"The updated schedule is now active.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_auto_update", f"Updated schedule {schedule_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Failed to Update Schedule</b>\n\n"
            "Please try again.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


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
            "❌ No active schedules found.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with schedules
    keyboard = []
    for schedule in schedules:
        preset = await get_move_trade_preset_by_id(schedule.get('preset_id', ''))
        preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {preset_name} - {schedule.get('execution_time', 'N/A')}",
            callback_data=f"move_auto_delete_{schedule['_id']}"
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
    from bot.utils.state_manager import state_manager
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
    from bot.utils.state_manager import state_manager
    state_data = await state_manager.get_state_data(user.id)
    schedule_id = state_data.get('delete_schedule_id')
    
    if not schedule_id:
        await query.edit_message_text("❌ Schedule not found")
        return
    
    # Delete schedule
    success = await delete_move_auto_execution(schedule_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Schedule Deleted</b>\n\n"
            "The schedule has been deleted and automatic execution has been stopped.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_auto_delete", f"Deleted schedule {schedule_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete schedule.",
            reply_markup=get_move_auto_trade_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


def register_move_auto_trade_handlers(application: Application):
    """Register move auto trade handlers."""
    
    # ✅ FIXED: Accept BOTH patterns!
    application.add_handler(CallbackQueryHandler(
        move_auto_trade_menu_callback,
        pattern="^menu_(move_auto|auto_move)_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_list_callback,
        pattern="^move_auto_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_add_callback,
        pattern="^move_auto_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_preset_callback,
        pattern="^move_auto_preset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_auto_confirm_callback,
        pattern="^move_auto_confirm$"
    ))

    application.add_handler(CallbackQueryHandler(
    move_auto_edit_list_callback,
    pattern="^move_auto_edit_list$"
    ))

    application.add_handler(CallbackQueryHandler(
        move_auto_edit_callback,
        pattern="^move_auto_edit_[a-f0-9]{24}$"
    ))

    application.add_handler(CallbackQueryHandler(
        move_auto_edit_preset_callback,
        pattern="^move_auto_edit_preset_"
    ))

    application.add_handler(CallbackQueryHandler(
        move_auto_edit_confirm_callback,
        pattern="^move_auto_edit_confirm$"
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
    
