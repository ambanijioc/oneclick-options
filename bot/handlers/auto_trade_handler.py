"""
Auto trade (Algo Trading) handler with countdown and live status.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from datetime import datetime
import pytz

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import StateManager
from bot.validators.user_validator import check_user_authorization
from database.operations.algo_setup_ops import (
    create_algo_setup,
    get_algo_setups,
    get_algo_setup,
    update_algo_setup,
    delete_algo_setup
)
from database.operations.manual_trade_preset_ops import (
    get_manual_trade_presets,
    get_manual_trade_preset
)
from database.operations.api_ops import get_api_credential
from database.operations.strategy_ops import get_strategy_preset_by_id

logger = setup_logger(__name__)
state_manager = StateManager()

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


def get_auto_trade_menu_keyboard():
    """Get auto trade main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("📊 List Current Algo Trades", callback_data="auto_trade_list")],
        [InlineKeyboardButton("➕ Add Algo Setup", callback_data="auto_trade_add")],
        [InlineKeyboardButton("✏️ Edit Algo Setup", callback_data="auto_trade_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Algo Setup", callback_data="auto_trade_delete_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def auto_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display auto trade main menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get setups
    setups = await get_algo_setups(user.id, active_only=True)
    
    await query.edit_message_text(
        "<b>⏰ Auto Trade (Algo Trading)</b>\n\n"
        "Automate your trades with scheduled execution:\n\n"
        "• <b>List:</b> View running algo trades\n"
        "• <b>Add:</b> Create new algo setup\n"
        "• <b>Edit:</b> Modify existing setup\n"
        "• <b>Delete:</b> Remove algo setup\n\n"
        f"<b>Active Setups:</b> {len(setups)}",
        reply_markup=get_auto_trade_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "auto_trade_menu", f"Viewed auto trade menu: {len(setups)} setups")


@error_handler
async def auto_trade_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all current algo trades."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get active setups
    setups = await get_algo_setups(user.id, active_only=True)
    
    if not setups:
        await query.edit_message_text(
            "<b>📊 Current Algo Trades</b>\n\n"
            "❌ No active algo trades.\n\n"
            "Create one using <b>Add Algo Setup</b>.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with setups
    keyboard = []
    for setup in setups:
        # Get preset name
        preset = await get_manual_trade_preset(setup['manual_preset_id'])
        preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
        
        keyboard.append([InlineKeyboardButton(
            f"⏰ {preset_name} - {setup['execution_time']}",
            callback_data=f"auto_trade_view_{setup['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>📊 Current Algo Trades</b>\n\n"
        "Select a setup to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View algo trade details with countdown."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    setup_id = query.data.split('_')[-1]
    
    # Get setup
    setup = await get_algo_setup(setup_id)
    
    if not setup:
        await query.edit_message_text("❌ Setup not found")
        return
    
    # Get preset
    preset = await get_manual_trade_preset(setup['manual_preset_id'])
    if not preset:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Get API and strategy
    api = await get_api_credential(preset['api_credential_id'])
    strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
    
    # Calculate countdown
    now_ist = datetime.now(IST)
    exec_hour, exec_minute = map(int, setup['execution_time'].split(':'))
    target_time = now_ist.replace(hour=exec_hour, minute=exec_minute, second=0, microsecond=0)
    
    if target_time <= now_ist:
        from datetime import timedelta
        target_time += timedelta(days=1)
    
    time_diff = target_time - now_ist
    hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Build message
    text = f"<b>⏰ Algo Trade Details</b>\n\n"
    text += f"<b>Preset:</b> {preset['preset_name']}\n"
    text += f"<b>API:</b> {api.api_name if api else 'Unknown'}\n"
    
    if strategy:
        text += f"<b>Strategy:</b> {strategy['name']}\n"
        text += f"<b>Type:</b> {preset['strategy_type'].title()}\n"
        text += f"<b>Asset:</b> {strategy['asset']}\n"
        text += f"<b>Direction:</b> {strategy['direction'].title()}\n"
    
    text += f"\n<b>⏰ Execution Time:</b> {setup['execution_time']} IST\n"
    text += f"<b>⏳ Countdown:</b> {hours}h {minutes}m {seconds}s\n\n"
    
    # Last execution info
    if setup.get('last_execution'):
        last_exec = setup['last_execution']
        if isinstance(last_exec, str):
            from dateutil import parser
            last_exec = parser.parse(last_exec)
        
        last_exec_ist = last_exec.replace(tzinfo=pytz.UTC).astimezone(IST)
        text += f"<b>📝 Last Execution:</b>\n"
        text += f"Time: {last_exec_ist.strftime('%d %b %Y, %I:%M %p IST')}\n"
        text += f"Status: {setup.get('last_execution_status', 'Unknown').title()}\n"
        
        details = setup.get('last_execution_details', {})
        if details and setup.get('last_execution_status') == 'success':
            text += f"CE: {details.get('ce_symbol', 'N/A')}\n"
            text += f"PE: {details.get('pe_symbol', 'N/A')}\n"
        elif details and setup.get('last_execution_status') == 'failed':
            text += f"Error: {details.get('error', 'Unknown')[:100]}\n"
    else:
        text += f"<b>📝 Last Execution:</b> Never\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"auto_trade_view_{setup_id}")],
        [InlineKeyboardButton("🔙 Back to List", callback_data="auto_trade_list")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add algo setup flow - list presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get manual trade presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>➕ Add Algo Setup</b>\n\n"
            "❌ No manual trade presets found.\n\n"
            "Please create a Manual Trade Preset first.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"auto_trade_preset_{preset['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>➕ Add Algo Setup</b>\n\n"
        "Select a Manual Trade Preset to automate:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "auto_trade_add", "Started add algo setup flow")


@error_handler
async def auto_trade_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - ask for time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Store preset ID
    await state_manager.set_state_data(user.id, {'manual_preset_id': preset_id})
    await state_manager.set_state(user.id, 'auto_trade_add_time')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")]]
    
    await query.edit_message_text(
        "<b>➕ Add Algo Setup</b>\n\n"
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
async def auto_trade_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of setups to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get setups
    setups = await get_algo_setups(user.id, active_only=True)
    
    if not setups:
        await query.edit_message_text(
            "<b>🗑️ Delete Algo Setup</b>\n\n"
            "❌ No active setups found.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with setups
    keyboard = []
    for setup in setups:
        preset = await get_manual_trade_preset(setup['manual_preset_id'])
        preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {preset_name} - {setup['execution_time']}",
            callback_data=f"auto_trade_delete_{setup['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Algo Setup</b>\n\n"
        "Select setup to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete setup - ask confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    setup_id = query.data.split('_')[-1]
    
    # Get setup
    setup = await get_algo_setup(setup_id)
    
    if not setup:
        await query.edit_message_text("❌ Setup not found")
        return
    
    # Get preset
    preset = await get_manual_trade_preset(setup['manual_preset_id'])
    preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
    
    # Store setup ID
    await state_manager.set_state_data(user.id, {'delete_setup_id': setup_id})
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="auto_trade_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")]
    ]
    
    await query.edit_message_text(
        f"<b>🗑️ Delete Algo Setup</b>\n\n"
        f"<b>Preset:</b> {preset_name}\n"
        f"<b>Time:</b> {setup['execution_time']} IST\n\n"
        f"⚠️ This will stop automatic execution.\n\n"
        f"Are you sure you want to delete?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete setup."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get setup ID
    state_data = await state_manager.get_state_data(user.id)
    setup_id = state_data.get('delete_setup_id')
    
    if not setup_id:
        await query.edit_message_text("❌ Setup not found")
        return
    
    # Delete setup
    success = await delete_algo_setup(setup_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Algo Setup Deleted</b>\n\n"
            "The algo setup has been deleted and automatic execution has been stopped.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "auto_trade_delete", f"Deleted setup {setup_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete algo setup.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


@error_handler
async def auto_trade_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of setups to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get setups
    setups = await get_algo_setups(user.id, active_only=True)
    
    if not setups:
        await query.edit_message_text(
            "<b>✏️ Edit Algo Setup</b>\n\n"
            "❌ No active setups found.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with setups
    keyboard = []
    for setup in setups:
        preset = await get_manual_trade_preset(setup['manual_preset_id'])
        preset_name = preset.get('preset_name', 'Unknown') if preset else 'Unknown'
        
        keyboard.append([InlineKeyboardButton(
            f"✏️ {preset_name} - {setup['execution_time']}",
            callback_data=f"auto_trade_edit_{setup['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Algo Setup</b>\n\n"
        "Select setup to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit flow - list presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    setup_id = query.data.split('_')[-1]
    
    # Store setup ID for edit
    await state_manager.set_state_data(user.id, {'edit_setup_id': setup_id})
    
    # Get manual trade presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>✏️ Edit Algo Setup</b>\n\n"
            "❌ No manual trade presets found.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"auto_trade_edit_preset_{preset['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Algo Setup</b>\n\n"
        "Select new Manual Trade Preset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_edit_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit preset selection - ask for time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Store preset ID
    state_data = await state_manager.get_state_data(user.id)
    state_data['manual_preset_id'] = preset_id
    await state_manager.set_state_data(user.id, state_data)
    await state_manager.set_state(user.id, 'auto_trade_edit_time')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_auto_trade")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Algo Setup</b>\n\n"
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
async def auto_trade_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and create algo setup."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    
    # Create algo setup
    result = await create_algo_setup(user.id, state_data)
    
    if result:
        await query.edit_message_text(
            f"<b>✅ Algo Setup Created</b>\n\n"
            f"<b>Execution Time:</b> {state_data['execution_time']} IST\n\n"
            f"🤖 The bot is now monitoring and will automatically execute this trade daily at the scheduled time.\n\n"
            f"💡 <i>Tip: The bot pre-activates 5 minutes before execution to ensure no delays.</i>",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "auto_trade_create", f"Created algo setup for {state_data['execution_time']}")
    else:
        await query.edit_message_text(
            "<b>❌ Failed to Create Algo Setup</b>\n\n"
            "Please try again.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


@error_handler
async def auto_trade_edit_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and update algo setup."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    setup_id = state_data.get('edit_setup_id')
    
    if not setup_id:
        await query.edit_message_text("❌ Setup not found")
        return
    
    # Update algo setup
    result = await update_algo_setup(setup_id, state_data)
    
    if result:
        await query.edit_message_text(
            f"<b>✅ Algo Setup Updated</b>\n\n"
            f"<b>New Execution Time:</b> {state_data['execution_time']} IST\n\n"
            f"The updated schedule is now active.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "auto_trade_update", f"Updated algo setup {setup_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Failed to Update Algo Setup</b>\n\n"
            "Please try again.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)
    

def register_auto_trade_handlers(application: Application):
    """Register auto trade handlers."""
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_menu_callback,
        pattern="^menu_auto_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_list_callback,
        pattern="^auto_trade_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_view_callback,
        pattern="^auto_trade_view_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_add_callback,
        pattern="^auto_trade_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_preset_callback,
        pattern="^auto_trade_preset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_list_callback,
        pattern="^auto_trade_edit_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_callback,
        pattern="^auto_trade_edit_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_preset_callback,
        pattern="^auto_trade_edit_preset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_delete_list_callback,
        pattern="^auto_trade_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_delete_callback,
        pattern="^auto_trade_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_delete_confirm_callback,
        pattern="^auto_trade_delete_confirm$"
    ))

        application.add_handler(CallbackQueryHandler(
        auto_trade_confirm_callback,
        pattern="^auto_trade_confirm$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_confirm_callback,
        pattern="^auto_trade_edit_confirm$"
    ))

    logger.info("Auto trade handlers registered")
    
