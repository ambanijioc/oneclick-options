"""
API credential management handlers.
"""

from telegram import Update
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
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    # API management text
    text = (
        "<b>🔑 API Management</b>\n\n"
        f"You have <b>{len(apis)}</b> API credential(s) configured.\n\n"
        "Select an option:"
    )
    
    # Show API management menu
    await query.edit_message_text(
        text,
        reply_markup=get_api_management_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "manage_api", "Opened API management")


@error_handler
async def api_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle API list callback.
    Display all configured APIs.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    # Format API list
    text = format_api_list(apis)
    
    # Show API list
    await query.edit_message_text(
        text,
        reply_markup=get_api_list_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "api_list", f"Viewed {len(apis)} API(s)")


@error_handler
async def add_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle add API callback.
    Start API addition flow.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Set conversation state
    await state_manager.set_state(user.id, ConversationState.API_ADD_NAME)
    
    # Ask for API name
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


@error_handler
async def handle_skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /skip command during conversations.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    state = await state_manager.get_state(user.id)
    
    if state is None:
        return  # No active conversation
    
    # Handle skip for API description
    if state == ConversationState.API_ADD_DESCRIPTION:
        # Skip description, move to API key
        await state_manager.update_data(user.id, {'api_description': ''})
        await state_manager.set_state(user.id, ConversationState.API_ADD_KEY)
        
        # Get current data
        data = await state_manager.get_data(user.id)
        
        # Ask for API key
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
    """
    Handle API name input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != ConversationState.API_ADD_NAME:
        return
    
    # Validate name
    result = validate_api_name(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    # Store name and move to next step
    await state_manager.update_data(user.id, {'api_name': result.value})
    await state_manager.set_state(user.id, ConversationState.API_ADD_DESCRIPTION)
    
    # Ask for description
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
    """
    Handle API description input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != ConversationState.API_ADD_DESCRIPTION:
        return
    
    # Get description (or skip)
    description = ""
    if update.message.text and update.message.text != "/skip":
        description = update.message.text.strip()
    
    # Store description and move to next step
    await state_manager.update_data(user.id, {'api_description': description})
    await state_manager.set_state(user.id, ConversationState.API_ADD_KEY)
    
    # Get current data
    data = await state_manager.get_data(user.id)
    
    # Ask for API key
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
    """
    Handle API key input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != ConversationState.API_ADD_KEY:
        return
    
    # Validate API key
    result = validate_api_key(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    # Delete user's message (contains API key)
    try:
        await update.message.delete()
    except Exception:
        pass
    
    # Get existing data BEFORE updating
    existing_data = await state_manager.get_data(user.id)
    logger.info(f"Existing data before storing API key: {existing_data}")
    
    # Store key
    await state_manager.update_data(user.id, {'api_key': result.value})
    
    # Verify data was stored
    updated_data = await state_manager.get_data(user.id)
    logger.info(f"Data after storing API key: {updated_data}")
    logger.info(f"API key stored: {updated_data.get('api_key')[:10]}..." if updated_data.get('api_key') else "API key NOT stored!")
    
    # Move to next step
    await state_manager.set_state(user.id, ConversationState.API_ADD_SECRET)
    
    # Ask for API secret
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
    """
    Handle API secret input and create credential.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != ConversationState.API_ADD_SECRET:
        return
    
    # Validate API secret
    result = validate_api_key(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    # Delete user's message (contains API secret)
    try:
        await update.message.delete()
    except Exception:
        pass
    
    # Get stored data
    data = await state_manager.get_data(user.id)
    api_key = data.get('api_key')
    api_secret = result.value
    
    # Check if api_key exists
    if not api_key:
        await context.bot.send_message(
            chat_id=user.id,
            text=format_error_message(
                "API Key not found in conversation data.",
                "Please start over with /start"
            ),
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        logger.error(f"API key missing for user {user.id}. Data: {data}")
        return
    
    # Send processing message
    processing_msg = await context.bot.send_message(
        chat_id=user.id,
        text="⏳ <b>Processing...</b>\n\nValidating API credentials...",
        parse_mode='HTML'
    )
    
    try:
        # Validate credentials format
        is_valid, error = await validate_api_credentials(api_key, api_secret)
        if not is_valid:
            await processing_msg.edit_text(
                format_error_message(error, "Please start over with /start"),
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
            return
        
        # Test API connection
        await processing_msg.edit_text(
            "⏳ <b>Processing...</b>\n\nTesting API connection...",
            parse_mode='HTML'
        )
        
        is_valid, error = await test_api_connection(api_key, api_secret)
        if not is_valid:
            await processing_msg.edit_text(
                format_error_message(
                    f"API connection test failed: {error}",
                    "Please check your credentials and try again."
                ),
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
            return
        
        # Create API credential
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
        
        # Success message
        await processing_msg.edit_text(
            "✅ <b>API Credential Added!</b>\n\n"
            f"<b>Name:</b> {escape_html(data.get('api_name'))}\n"
            f"<b>Status:</b> Active\n\n"
            "You can now use this API for trading.",
            reply_markup=get_back_keyboard("menu_manage_api"),
            parse_mode='HTML'
        )
        
        log_user_action(
            user.id,
            "add_api_complete",
            f"Added API: {data.get('api_name')}"
        )
    
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
        # Clear conversation state
        await state_manager.clear_state(user.id)
        logger.info(f"Cleared conversation state for user {user.id}")


def register_api_handlers(application: Application):
    """
    Register API management handlers.
    
    Args:
        application: Bot application instance
    """
    # Command handlers
    application.add_handler(CommandHandler("skip", handle_skip_command))
    
    # Callback query handlers  
    application.add_handler(CallbackQueryHandler(
        manage_api_callback,
        pattern="^menu_manage_api$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        api_list_callback,
        pattern="^api_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        add_api_callback,
        pattern="^api_add$"
    ))
    
    # DON'T ADD ANY MESSAGE HANDLERS HERE
    # Messages are handled by message_router.py
    
    logger.info("API handlers registered")


if __name__ == "__main__":
    print("API handler module loaded")
    
