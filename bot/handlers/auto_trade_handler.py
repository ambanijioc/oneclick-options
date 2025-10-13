"""
Automated trade execution handlers.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_error_message, escape_html
from bot.validators.user_validator import check_user_authorization
from bot.validators.input_validator import validate_time_format
from bot.utils.state_manager import state_manager, ConversationState
from bot.keyboards.trade_keyboards import (
    get_api_selection_keyboard,
    get_auto_execution_time_keyboard,
    get_auto_execution_list_keyboard,
    get_auto_execution_toggle_keyboard
)
from bot.keyboards.confirmation_keyboards import get_cancel_keyboard
from database.operations.api_ops import get_api_credentials
from database.operations.auto_execution_ops import (
    create_auto_execution,
    get_auto_executions,
    get_auto_execution_by_id,
    update_auto_execution,
    delete_auto_execution
)
from database.models.auto_execution import AutoExecutionCreate

logger = setup_logger(__name__)


@error_handler
async def auto_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle auto trade menu callback.
    Display list of auto executions.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get user's auto executions
    auto_execs = await get_auto_executions(user.id)
    
    # Format auto execution list
    auto_exec_data = []
    for auto_exec in auto_execs:
        # Get preset name (you would fetch this from strategy_ops)
        auto_exec_data.append({
            'id': str(auto_exec.id),
            'execution_time': auto_exec.execution_time,
            'enabled': auto_exec.enabled,
            'preset_name': 'Strategy Preset'  # TODO: Fetch actual preset name
        })
    
    # Auto trade text
    text = (
        "<b>🤖 Auto Trade Execution</b>\n\n"
        f"Scheduled executions: {len(auto_execs)}\n\n"
        "Manage your automated trade schedules:"
    )
    
    # Show auto execution list
    await query.edit_message_text(
        text,
        reply_markup=get_auto_execution_list_keyboard(auto_exec_data),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "auto_trade", f"Viewed {len(auto_execs)} auto executions")


@error_handler
async def auto_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle add auto execution callback.
    Start auto execution creation flow.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    if not apis:
        await query.edit_message_text(
            "<b>🤖 Add Auto Execution</b>\n\n"
            "❌ No API credentials configured.\n\n"
            "Please add an API credential first.",
            parse_mode='HTML'
        )
        return
    
    # Set conversation state
    await state_manager.set_state(user.id, ConversationState.AUTO_SELECT_API)
    
    # Show API selection
    text = (
        "<b>🤖 Add Auto Execution</b>\n\n"
        "Select an API for automated execution:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_api_selection_keyboard(apis, action="auto_trade"),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "auto_add_start", "Started auto execution creation")


@error_handler
async def auto_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle auto execution view callback.
    Display details and management options.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract auto execution ID from callback data
    auto_exec_id = query.data.split('_')[-1]
    
    # Get auto execution
    auto_exec = await get_auto_execution_by_id(auto_exec_id)
    
    if not auto_exec:
        await query.edit_message_text(
            format_error_message("Auto execution not found."),
            parse_mode='HTML'
        )
        return
    
    # Format auto execution details
    status_emoji = "✅ Active" if auto_exec.enabled else "❌ Disabled"
    
    text = (
        "<b>🤖 Auto Execution Details</b>\n\n"
        f"<b>Status:</b> {status_emoji}\n"
        f"<b>Execution Time:</b> {auto_exec.execution_time} IST\n"
        f"<b>Created:</b> {auto_exec.created_at.strftime('%Y-%m-%d')}\n"
    )
    
    if auto_exec.last_execution:
        text += f"<b>Last Execution:</b> {auto_exec.last_execution.strftime('%Y-%m-%d %H:%M')}\n"
        text += f"<b>Last Status:</b> {auto_exec.last_execution_status or 'N/A'}\n"
    
    text += f"\n<b>Total Executions:</b> {auto_exec.execution_count}"
    
    # Show details with management options
    await query.edit_message_text(
        text,
        reply_markup=get_auto_execution_toggle_keyboard(auto_exec_id, auto_exec.enabled),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "auto_view", f"Viewed auto execution: {auto_exec_id}")


@error_handler
async def auto_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle auto execution toggle callback.
    Enable or disable auto execution.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract auto execution ID from callback data
    auto_exec_id = query.data.split('_')[-1]
    
    # Get current state
    auto_exec = await get_auto_execution_by_id(auto_exec_id)
    
    if not auto_exec:
        await query.edit_message_text(
            format_error_message("Auto execution not found."),
            parse_mode='HTML'
        )
        return
    
    # Toggle enabled state
    new_state = not auto_exec.enabled
    success = await update_auto_execution(auto_exec_id, {'enabled': new_state})
    
    if success:
        status = "enabled" if new_state else "disabled"
        await query.edit_message_text(
            f"<b>✅ Auto Execution {status.capitalize()}</b>\n\n"
            f"The auto execution has been {status}.",
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "auto_toggle", f"Toggled to {status}: {auto_exec_id}")
    else:
        await query.edit_message_text(
            format_error_message("Failed to update auto execution."),
            parse_mode='HTML'
        )


@error_handler
async def auto_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle auto execution delete callback.
    Show confirmation and delete.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract auto execution ID from callback data
    auto_exec_id = query.data.split('_')[-1]
    
    # Delete auto execution
    success = await delete_auto_execution(auto_exec_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Auto Execution Deleted</b>\n\n"
            "The scheduled execution has been removed.",
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "auto_delete_success", f"Deleted: {auto_exec_id}")
    else:
        await query.edit_message_text(
            format_error_message("Failed to delete auto execution."),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "auto_delete_failed", f"Failed to delete: {auto_exec_id}")


def register_auto_trade_handlers(application: Application):
    """
    Register auto trade handlers.
    
    Args:
        application: Bot application instance
    """
    # Auto trade menu callback
    application.add_handler(CallbackQueryHandler(
        auto_trade_callback,
        pattern="^menu_auto_trade$"
    ))
    
    # Auto add callback
    application.add_handler(CallbackQueryHandler(
        auto_add_callback,
        pattern="^auto_add$"
    ))
    
    # Auto view callback
    application.add_handler(CallbackQueryHandler(
        auto_view_callback,
        pattern="^auto_view_"
    ))
    
    # Auto toggle callback
    application.add_handler(CallbackQueryHandler(
        auto_toggle_callback,
        pattern="^auto_toggle_"
    ))
    
    # Auto delete callback
    application.add_handler(CallbackQueryHandler(
        auto_delete_callback,
        pattern="^auto_delete_(?!confirm)"
    ))
    
    logger.info("Auto trade handlers registered")


if __name__ == "__main__":
    print("Auto trade handler module loaded")
  
