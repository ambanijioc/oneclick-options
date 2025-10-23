"""
Auto trade (Algo Trading) handler with countdown and live status.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from datetime import datetime
from services.sl_monitor_service import start_strategy_monitor
import pytz

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
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
from database.operations.api_ops import get_api_credential_by_id
from database.operations.strategy_ops import get_strategy_preset_by_id

logger = setup_logger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


def safe_get_attr(obj, attr, default=None):
    """Safely get attribute from Pydantic object or dict."""
    if obj is None:
        return default
    if hasattr(obj, attr):
        return getattr(obj, attr, default)
    elif isinstance(obj, dict):
        return obj.get(attr, default)
    return default


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
        # ✅ FIXED: Safe attribute access
        manual_preset_id = safe_get_attr(setup, 'manual_preset_id')
        execution_time = safe_get_attr(setup, 'execution_time', 'N/A')
        setup_id = safe_get_attr(setup, 'id', safe_get_attr(setup, '_id'))
        
        # Get preset name
        preset = await get_manual_trade_preset(manual_preset_id)
        preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
        
        keyboard.append([InlineKeyboardButton(
            f"⏰ {preset_name} - {execution_time}",
            callback_data=f"auto_trade_view_{setup_id}"
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
    
    # ✅ FIXED: Safe attribute access for setup
    manual_preset_id = safe_get_attr(setup, 'manual_preset_id')
    execution_time = safe_get_attr(setup, 'execution_time', 'N/A')
    last_execution = safe_get_attr(setup, 'last_execution')
    last_execution_status = safe_get_attr(setup, 'last_execution_status', 'unknown')
    last_execution_details = safe_get_attr(setup, 'last_execution_details', {})
    
    # Get preset
    preset = await get_manual_trade_preset(manual_preset_id)
    if not preset:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # ✅ FIXED: Safe attribute access for preset
    preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
    api_credential_id = safe_get_attr(preset, 'api_credential_id')
    strategy_preset_id = safe_get_attr(preset, 'strategy_preset_id')
    strategy_type = safe_get_attr(preset, 'strategy_type', 'straddle')
    
    # Get API and strategy
    api = await get_api_credential_by_id(api_credential_id)
    strategy = await get_strategy_preset_by_id(strategy_preset_id)
    
    # ✅ FIXED: Safe attribute access for API
    api_name = safe_get_attr(api, 'api_name', 'Unknown')
    
    # Calculate countdown
    now_ist = datetime.now(IST)
    exec_hour, exec_minute = map(int, execution_time.split(':'))
    target_time = now_ist.replace(hour=exec_hour, minute=exec_minute, second=0, microsecond=0)
    
    if target_time <= now_ist:
        from datetime import timedelta
        target_time += timedelta(days=1)
    
    time_diff = target_time - now_ist
    hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Build message
    text = f"<b>⏰ Algo Trade Details</b>\n\n"
    text += f"<b>Preset:</b> {preset_name}\n"
    text += f"<b>API:</b> {api_name}\n"
    
    if strategy:
        # ✅ FIXED: Safe attribute access for strategy
        strategy_name = safe_get_attr(strategy, 'name', 'Unknown')
        asset = safe_get_attr(strategy, 'asset', 'BTC')
        direction = safe_get_attr(strategy, 'direction', 'short')
        
        text += f"<b>Strategy:</b> {strategy_name}\n"
        text += f"<b>Type:</b> {strategy_type.title()}\n"
        text += f"<b>Asset:</b> {asset}\n"
        text += f"<b>Direction:</b> {direction.title()}\n"
    
    text += f"\n<b>⏰ Execution Time:</b> {execution_time} IST\n"
    text += f"<b>⏳ Countdown:</b> {hours}h {minutes}m {seconds}s\n\n"
    
    # Last execution info
    if last_execution:
        # ✅ FIXED: Handle datetime conversion safely
        if isinstance(last_execution, str):
            from dateutil import parser
            try:
                last_exec = parser.parse(last_execution)
            except:
                last_exec = None
        else:
            last_exec = last_execution
        
        if last_exec:
            last_exec_ist = last_exec.replace(tzinfo=pytz.UTC).astimezone(IST)
            text += f"<b>📝 Last Execution:</b>\n"
            text += f"Time: {last_exec_ist.strftime('%d %b %Y, %I:%M %p IST')}\n"
            text += f"Status: {last_execution_status.title()}\n"
            
            if last_execution_details and last_execution_status == 'success':
                # ✅ FIXED: Safe dict access
                ce_symbol = last_execution_details.get('ce_symbol', 'N/A') if isinstance(last_execution_details, dict) else 'N/A'
                pe_symbol = last_execution_details.get('pe_symbol', 'N/A') if isinstance(last_execution_details, dict) else 'N/A'
                text += f"CE: {ce_symbol}\n"
                text += f"PE: {pe_symbol}\n"
            elif last_execution_details and last_execution_status == 'failed':
                # ✅ FIXED: Safe dict access
                error_msg = last_execution_details.get('error', 'Unknown') if isinstance(last_execution_details, dict) else 'Unknown'
                text += f"Error: {error_msg[:100]}\n"
        else:
            text += f"<b>📝 Last Execution:</b> Never\n"
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
    """Start adding new algo setup - select preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get user's manual trade presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>➕ Add Algo Setup</b>\n\n"
            "❌ No manual trade presets found.\n\n"
            "Create a Manual Trade Preset first.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        # ✅ FIXED: Safe attribute access
        preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
        preset_id = safe_get_attr(preset, 'id', safe_get_attr(preset, '_id'))
        
        keyboard.append([InlineKeyboardButton(
            f"📋 {preset_name}",
            callback_data=f"auto_trade_select_preset_{preset_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>➕ Add Algo Setup</b>\n\n"
        "Select a trade preset to schedule:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_select_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - ask for execution time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Store preset ID in state
    await state_manager.set_state_data(user.id, {'manual_preset_id': preset_id})
    await state_manager.set_state(user.id, 'auto_trade_add_time')
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")]]
    
    await query.edit_message_text(
        "<b>➕ Add Algo Setup</b>\n\n"
        "Enter execution time in <code>HH:MM</code> format (24-hour).\n\n"
        "Examples:\n"
        "• <code>09:15</code> - 9:15 AM\n"
        "• <code>15:30</code> - 3:30 PM\n"
        "• <code>23:45</code> - 11:45 PM",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def handle_auto_trade_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle time input for auto trade setup."""
    user = update.effective_user
    
    # Validate time format (HH:MM)
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        await update.message.reply_text(
            "❌ Invalid time format.\n\n"
            "Please enter time in <code>HH:MM</code> format (24-hour).\n\n"
            "Examples:\n"
            "• <code>09:15</code>\n"
            "• <code>15:30</code>\n"
            "• <code>23:45</code>",
            parse_mode='HTML'
        )
        return
    
    # Store time
    state_data = await state_manager.get_state_data(user.id)
    state_data['execution_time'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Get preset details for confirmation
    preset = await get_manual_trade_preset(state_data['manual_preset_id'])
    
    if not preset:
        await update.message.reply_text("❌ Preset not found")
        await state_manager.clear_state(user.id)
        return
    
    # ✅ FIXED: Safe attribute access for preset
    preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
    api_credential_id = safe_get_attr(preset, 'api_credential_id')
    strategy_preset_id = safe_get_attr(preset, 'strategy_preset_id')
    strategy_type = safe_get_attr(preset, 'strategy_type', 'straddle')
    
    # Get API and strategy
    api = await get_api_credential_by_id(api_credential_id)
    strategy = await get_strategy_preset_by_id(strategy_preset_id)
    
    # ✅ FIXED: Safe attribute access
    api_name = safe_get_attr(api, 'api_name', 'Unknown')
    strategy_name = safe_get_attr(strategy, 'name', 'Unknown')
    asset = safe_get_attr(strategy, 'asset', 'BTC')
    direction = safe_get_attr(strategy, 'direction', 'short')
    
    # Show confirmation
    text_msg = (
        f"<b>⏰ Confirm Algo Setup</b>\n\n"
        f"<b>Preset:</b> {preset_name}\n"
        f"<b>API:</b> {api_name}\n"
        f"<b>Strategy:</b> {strategy_name}\n"
        f"<b>Type:</b> {strategy_type.title()}\n"
        f"<b>Asset:</b> {asset}\n"
        f"<b>Direction:</b> {direction.title()}\n\n"
        f"<b>⏰ Execution Time:</b> {text} IST\n\n"
        "⚠️ This trade will execute automatically at the scheduled time."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="auto_trade_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")]
    ]
    
    await update.message.reply_text(
        text_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create the algo setup."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    
    if not state_data or 'manual_preset_id' not in state_data or 'execution_time' not in state_data:
        await query.edit_message_text(
            "❌ Setup data not found. Please start again.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    try:
        # Create algo setup
        setup = await create_algo_setup(
            user_id=user.id,
            setup_data={
                'manual_preset_id': state_data['manual_preset_id'],
                'execution_time': state_data['execution_time']
            }
        )
   
        await query.edit_message_text(
            "<b>✅ Algo Setup Created!</b>\n\n"
            f"Trade will execute automatically at <b>{state_data['execution_time']} IST</b>.\n\n"
            "You'll receive notifications before execution.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "auto_trade_create", f"Created algo setup at {state_data['execution_time']}")
    
    except Exception as e:
        logger.error(f"Failed to create algo setup: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Failed to create algo setup: {str(e)[:200]}",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
    
    finally:
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
            "No active setups found.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Build keyboard
    keyboard = []
    for setup in setups:
        # ✅ FIXED: Safe attribute access
        setup_id = safe_get_attr(setup, 'id', safe_get_attr(setup, '_id'))
        execution_time = safe_get_attr(setup, 'execution_time', 'N/A')
        manual_preset_id = safe_get_attr(setup, 'manual_preset_id')
        
        # Get preset name
        preset = await get_manual_trade_preset(manual_preset_id)
        preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
        
        keyboard.append([InlineKeyboardButton(
            f"✏️ {preset_name} - {execution_time}",
            callback_data=f"auto_trade_edit_{setup_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Algo Setup</b>\n\n"
        "Select a setup to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit options for a setup."""
    query = update.callback_query
    await query.answer()
    
    setup_id = query.data.split('_')[-1]
    
    keyboard = [
        [InlineKeyboardButton("⏰ Change Time", callback_data=f"auto_trade_edit_time_{setup_id}")],
        [InlineKeyboardButton("📋 Change Preset", callback_data=f"auto_trade_edit_preset_{setup_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="auto_trade_edit_list")]
    ]
    
    await query.edit_message_text(
        "<b>✏️ Edit Algo Setup</b>\n\n"
        "What would you like to edit?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_edit_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for new execution time."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    setup_id = query.data.split('_')[-1]
    
    # Store setup ID in state
    await state_manager.set_state_data(user.id, {'edit_setup_id': setup_id})
    await state_manager.set_state(user.id, 'auto_trade_edit_time')
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data=f"auto_trade_edit_{setup_id}")]]
    
    await query.edit_message_text(
        "<b>✏️ Edit Execution Time</b>\n\n"
        "Enter new execution time in <code>HH:MM</code> format (24-hour).\n\n"
        "Examples:\n"
        "• <code>09:15</code> - 9:15 AM\n"
        "• <code>15:30</code> - 3:30 PM\n"
        "• <code>23:45</code> - 11:45 PM",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def handle_auto_trade_edit_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle time edit input."""
    user = update.effective_user
    
    # Validate time format
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    
    if not re.match(time_pattern, text):
        await update.message.reply_text(
            "❌ Invalid time format.\n\n"
            "Please enter time in <code>HH:MM</code> format.",
            parse_mode='HTML'
        )
        return
    
    # Get setup ID from state
    state_data = await state_manager.get_state_data(user.id)
    setup_id = state_data.get('edit_setup_id')
    
    if not setup_id:
        await update.message.reply_text("❌ Setup not found")
        await state_manager.clear_state(user.id)
        return
    
    # Update setup
    try:
        success = await update_algo_setup(setup_id, {'execution_time': text})
        
        if success:
            await update.message.reply_text(
                f"<b>✅ Time Updated!</b>\n\n"
                f"New execution time: <b>{text} IST</b>",
                reply_markup=get_auto_trade_menu_keyboard(),
                parse_mode='HTML'
            )
            log_user_action(user.id, "auto_trade_edit", f"Updated time to {text}")
        else:
            await update.message.reply_text(
                "❌ Failed to update time.",
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Failed to update time: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error: {str(e)[:200]}",
            parse_mode='HTML'
        )
    
    finally:
        await state_manager.clear_state(user.id)


@error_handler
async def auto_trade_edit_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show preset selection for editing."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    setup_id = query.data.split('_')[-1]
    
    # Get presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "❌ No presets found.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard
    keyboard = []
    for preset in presets:
        # ✅ FIXED: Safe attribute access
        preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
        preset_id = safe_get_attr(preset, 'id', safe_get_attr(preset, '_id'))
        
        keyboard.append([InlineKeyboardButton(
            f"📋 {preset_name}",
            callback_data=f"auto_trade_update_preset_{setup_id}_{preset_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"auto_trade_edit_{setup_id}")])
    
    await query.edit_message_text(
        "<b>✏️ Change Preset</b>\n\n"
        "Select new preset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_update_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update setup with new preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    parts = query.data.split('_')
    setup_id = parts[-2]
    preset_id = parts[-1]
    
    try:
        success = await update_algo_setup(setup_id, {'manual_preset_id': preset_id})
        
        if success:
            await query.edit_message_text(
                "<b>✅ Preset Updated!</b>",
                reply_markup=get_auto_trade_menu_keyboard(),
                parse_mode='HTML'
            )
            log_user_action(user.id, "auto_trade_edit", f"Updated preset to {preset_id}")
        else:
            await query.edit_message_text(
                "❌ Failed to update preset.",
                reply_markup=get_auto_trade_menu_keyboard(),
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Failed to update preset: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error: {str(e)[:200]}",
            reply_markup=get_auto_trade_menu_keyboard(),
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
            "No active setups found.",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Build keyboard
    keyboard = []
    for setup in setups:
        # ✅ FIXED: Safe attribute access
        setup_id = safe_get_attr(setup, 'id', safe_get_attr(setup, '_id'))
        execution_time = safe_get_attr(setup, 'execution_time', 'N/A')
        manual_preset_id = safe_get_attr(setup, 'manual_preset_id')
        
        # Get preset name
        preset = await get_manual_trade_preset(manual_preset_id)
        preset_name = safe_get_attr(preset, 'preset_name', 'Unknown')
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {preset_name} - {execution_time}",
            callback_data=f"auto_trade_delete_{setup_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="menu_auto_trade")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Algo Setup</b>\n\n"
        "Select a setup to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def auto_trade_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete algo setup."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    setup_id = query.data.split('_')[-1]
    
    try:
        success = await delete_algo_setup(setup_id)
        
        if success:
            await query.edit_message_text(
                "<b>✅ Setup Deleted</b>\n\n"
                "Algo setup has been removed.",
                reply_markup=get_auto_trade_menu_keyboard(),
                parse_mode='HTML'
            )
            log_user_action(user.id, "auto_trade_delete", f"Deleted setup {setup_id}")
        else:
            await query.edit_message_text(
                "❌ Failed to delete setup.",
                reply_markup=get_auto_trade_menu_keyboard(),
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Failed to delete setup: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error: {str(e)[:200]}",
            reply_markup=get_auto_trade_menu_keyboard(),
            parse_mode='HTML'
        )


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
        auto_trade_select_preset_callback,
        pattern="^auto_trade_select_preset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_confirm_callback,
        pattern="^auto_trade_confirm$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_list_callback,
        pattern="^auto_trade_edit_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_callback,
        pattern="^auto_trade_edit_[a-f0-9]+$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_time_callback,
        pattern="^auto_trade_edit_time_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_edit_preset_callback,
        pattern="^auto_trade_edit_preset_[a-f0-9]+$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_update_preset_callback,
        pattern="^auto_trade_update_preset_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_delete_list_callback,
        pattern="^auto_trade_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        auto_trade_delete_callback,
        pattern="^auto_trade_delete_[a-f0-9]+$"
    ))
    
    logger.info("Auto trade handlers registered")
