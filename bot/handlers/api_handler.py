"""
API credential management handlers.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_api_list, format_error_message, escape_html
from bot.validators.user_validator import check_user_authorization
from bot.validators.input_validator import validate_api_name, validate_api_key
from bot.validators.api_validator import validate_api_credentials, test_api_connection
from bot.utils.state_manager import state_manager, ConversationState
from bot.keyboards.api_keyboards import (
    get_api_management_keyboard,
    get_api_list_keyboard,
    get_api_edit_keyboard,
    get_api_delete_confirmation_keyboard
)
from bot.keyboards.confirmation_keyboards import get_back_keyboard, get_cancel_keyboard
from database.operations.api_ops import (
    create_api_credential,
    get_api_credentials,
    get_api_credential_by_id,
    update_api_credential,
    delete_api_credential
)
from database.models.api_credentials import APICredentialCreate

logger = setup_logger(__name__)


@error_handler
async def manage_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle manage API menu callback.
    Show API management options.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    apis = await get_api_credentials(user.id)
    
    text = (
        "<b>🔑 API Management</b>\n\n"
        f"You have <b>{len(apis)}</b> API credential(s) configured.\n\n"
        "Select an option:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_api_management_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "manage_api", "Opened API management")


@error_handler
async def api_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all configured APIs."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    apis = await get_api_credentials(user.id)
    
    text = format_api_list(apis)
    
    await query.edit_message_text(
        text,
        reply_markup=get_api_list_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "api_list", f"Viewed {len(apis)} API(s)")


# ✅ ADDED: View API details callback
@error_handler
async def api_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View specific API details."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    api = await get_api_credential_by_id(api_id)
    
    if not api or api.user_id != user.id:
        await query.edit_message_text("❌ API not found")
        return
    
    text = (
        f"<b>🔑 API Details</b>\n\n"
        f"<b>Name:</b> {escape_html(api.api_name)}\n"
        f"<b>Description:</b> {escape_html(api.api_description) if api.api_description else '<i>None</i>'}\n"
        f"<b>API Key:</b> <code>{api.api_key[:10]}...{api.api_key[-4:]}</code>\n"
        f"<b>Created:</b> {api.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"<b>Status:</b> {'✅ Active' if api.is_active else '❌ Inactive'}"
    )
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit", callback_data=f"api_edit_{api_id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"api_delete_{api_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="api_list")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def add_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start API addition flow."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    await state_manager.set_state(user.id, ConversationState.API_ADD_NAME)
    
    text = (
        "<b>➕ Add New API</b>\n\n"
        "Please enter a name for this API credential:\n\n"
        "<i>Example: Main Trading Account</i>"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_cancel_keyboard("menu_manage_api"),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "add_api_start", "Started API addition")


# ✅ ADDED: Edit API callback
@error_handler
async def api_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start API edit flow."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    api = await get_api_credential_by_id(api_id)
    
    if not api or api.user_id != user.id:
        await query.edit_message_text("❌ API not found")
        return
    
    text = (
        f"<b>✏️ Edit API</b>\n\n"
        f"<b>Current Name:</b> {escape_html(api.api_name)}\n\n"
        "What would you like to edit?"
    )
    
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data=f"api_edit_name_{api_id}")],
        [InlineKeyboardButton("📄 Edit Description", callback_data=f"api_edit_desc_{api_id}")],
        [InlineKeyboardButton("🔑 Edit Credentials", callback_data=f"api_edit_creds_{api_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"api_view_{api_id}")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ✅ ADDED: Delete API callback
@error_handler
async def api_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show delete confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    api = await get_api_credential_by_id(api_id)
    
    if not api or api.user_id != user.id:
        await query.edit_message_text("❌ API not found")
        return
    
    text = (
        f"<b>🗑️ Delete API</b>\n\n"
        f"<b>Name:</b> {escape_html(api.api_name)}\n\n"
        f"⚠️ Are you sure you want to delete this API credential?\n\n"
        f"This action cannot be undone."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data=f"api_delete_confirm_{api_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"api_view_{api_id}")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ✅ ADDED: Confirm delete callback
@error_handler
async def api_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete API."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    api = await get_api_credential_by_id(api_id)
    
    if not api or api.user_id != user.id:
        await query.edit_message_text("❌ API not found")
        return
    
    success = await delete_api_credential(api_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ API Deleted</b>\n\n"
            "The API credential has been deleted successfully.",
            reply_markup=get_back_keyboard("menu_manage_api"),
            parse_mode='HTML'
        )
        log_user_action(user.id, "api_delete", f"Deleted API: {api.api_name}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete API credential.",
            reply_markup=get_back_keyboard("menu_manage_api"),
            parse_mode='HTML'
        )


@error_handler
async def handle_skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /skip command during conversations."""
    user = update.effective_user
    state = await state_manager.get_state(user.id)
    
    if state is None:
        return
    
    if state == ConversationState.API_ADD_DESCRIPTION:
        await state_manager.update_data(user.id, {'api_description': ''})
        await state_manager.set_state(user.id, ConversationState.API_ADD_KEY)
        
        data = await state_manager.get_data(user.id)
        
        text = (
            "<b>➕ Add New API</b>\n\n"
            f"<b>Name:</b> {escape_html(data.get('api_name', ''))}\n"
            f"<b>Description:</b> <i>None</i>\n\n"
            "Please enter your Delta Exchange <b>API Key</b>:"
        )
        
        await update.message.reply_text(text, parse_mode='HTML')
        log_user_action(user.id, "api_description_skipped", "Skipped API description")


@error_handler
async def handle_api_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API name input."""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'api_add_name':  # Compare as string!
        return
    
    result = validate_api_name(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    await state_manager.update_data(user.id, {'api_name': result.value})
    await state_manager.set_state(user.id, ConversationState.API_ADD_DESCRIPTION)
    
    text = (
        "<b>➕ Add New API</b>\n\n"
        f"<b>Name:</b> {escape_html(result.value)}\n\n"
        "Please enter a description (optional):\n\n"
        "<i>Example: Primary trading account for BTC options</i>\n\n"
        "Or send <code>/skip</code> to skip."
    )
    
    await update.message.reply_text(text, parse_mode='HTML')
    log_user_action(user.id, "add_api_name", f"Set API name: {result.value}")


@error_handler
async def handle_api_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API description input."""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'api_add_description':  # Compare as string!
        return
    
    description = ""
    if update.message.text and update.message.text != "/skip":
        description = update.message.text.strip()
    
    await state_manager.update_data(user.id, {'api_description': description})
    await state_manager.set_state(user.id, ConversationState.API_ADD_KEY)
    
    data = await state_manager.get_data(user.id)
    
    text = (
        "<b>➕ Add New API</b>\n\n"
        f"<b>Name:</b> {escape_html(data.get('api_name', ''))}\n"
        f"<b>Description:</b> {escape_html(description) if description else '<i>None</i>'}\n\n"
        "Please enter your Delta Exchange <b>API Key</b>:"
    )
    
    await update.message.reply_text(text, parse_mode='HTML')
    log_user_action(user.id, "add_api_description", "Set API description")


@error_handler
async def handle_api_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API key input."""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'api_add_key':  # Compare as string!
        return
    
    result = validate_api_key(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    existing_data = await state_manager.get_data(user.id)
    logger.info(f"Existing data before storing API key: {existing_data}")
    
    await state_manager.update_data(user.id, {'api_key': result.value})
    
    updated_data = await state_manager.get_data(user.id)
    logger.info(f"Data after storing API key: {updated_data}")
    
    await state_manager.set_state(user.id, ConversationState.API_ADD_SECRET)
    
    text = (
        "<b>➕ Add New API</b>\n\n"
        "✅ API Key received\n\n"
        "Please enter your Delta Exchange <b>API Secret</b>:"
    )
    
    await context.bot.send_message(
        chat_id=user.id,
        text=text,
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "add_api_key", "API key received")


@error_handler
async def handle_api_secret_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API secret input and create credential."""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'api_add_secret':  # Compare as string!
        return
    
    result = validate_api_key(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    data = await state_manager.get_data(user.id)
    logger.info(f"Retrieved data: {data}")
    
    api_key = data.get('api_key')
    api_secret = result.value
    
    if not api_key:
        logger.error(f"API key missing for user {user.id}")
        await context.bot.send_message(
            chat_id=user.id,
            text=format_error_message(
                "API Key not found.",
                "Please start over with /start"
            ),
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        return
    
    processing_msg = await context.bot.send_message(
        chat_id=user.id,
        text="⏳ <b>Processing...</b>\n\nValidating API credentials...",
        parse_mode='HTML'
    )
    
    try:
        is_valid, error = await validate_api_credentials(api_key, api_secret)
        if not is_valid:
            await processing_msg.edit_text(
                format_error_message(error, "Please start over."),
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
            return
        
        await processing_msg.edit_text(
            "⏳ <b>Processing...</b>\n\nTesting API connection...",
            parse_mode='HTML'
        )
        
        is_valid, error = await test_api_connection(api_key, api_secret)
        if not is_valid:
            await processing_msg.edit_text(
                format_error_message(
                    f"API connection test failed: {error}",
                    "Please check your credentials."
                ),
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
            return
        
        await processing_msg.edit_text(
            "⏳ <b>Processing...</b>\n\nSaving API credentials...",
            parse_mode='HTML'
        )
        
        credential_data = APICredentialCreate(
            user_id=user.id,
            api_name=data.get('api_name'),
            api_description=data.get('api_description', ''),
            api_key=api_key,
            api_secret=api_secret
        )
        
        credential_id = await create_api_credential(credential_data)
        
        await processing_msg.edit_text(
            "✅ <b>API Credential Added!</b>\n\n"
            f"<b>Name:</b> {escape_html(data.get('api_name'))}\n"
            f"<b>Status:</b> Active\n\n"
            "You can now use this API for trading.",
            reply_markup=get_back_keyboard("menu_manage_api"),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "add_api_complete", f"Added API: {data.get('api_name')}")
    
    except Exception as e:
        logger.error(f"Failed to create API credential: {e}", exc_info=True)
        await processing_msg.edit_text(
            format_error_message(
                "Failed to save API credentials.",
                f"Error: {str(e)}"
            ),
            parse_mode='HTML'
        )
    
    finally:
        await state_manager.clear_state(user.id)


def register_api_handlers(application: Application):
    """Register API management handlers."""
    
    application.add_handler(CommandHandler("skip", handle_skip_command))
    
    application.add_handler(CallbackQueryHandler(
        manage_api_callback,
        pattern="^menu_manage_api$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        api_list_callback,
        pattern="^api_list$"
    ))
    
    # ✅ ADDED: View API handler
    application.add_handler(CallbackQueryHandler(
        api_view_callback,
        pattern="^api_view_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        add_api_callback,
        pattern="^api_add$"
    ))
    
    # ✅ ADDED: Edit API handler
    application.add_handler(CallbackQueryHandler(
        api_edit_callback,
        pattern="^api_edit_[a-f0-9]{24}$"
    ))
    
    # ✅ ADDED: Delete API handler
    application.add_handler(CallbackQueryHandler(
        api_delete_callback,
        pattern="^api_delete_[a-f0-9]{24}$"
    ))
    
    # ✅ ADDED: Confirm delete handler
    application.add_handler(CallbackQueryHandler(
        api_delete_confirm_callback,
        pattern="^api_delete_confirm_[a-f0-9]{24}$"
    ))
    
    logger.info("API handlers registered")


if __name__ == "__main__":
    print("API handler module loaded")
    
