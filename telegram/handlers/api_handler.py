"""
API management handler.
Handles adding, editing, and deleting Delta Exchange API credentials.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.api_operations import APIOperations
from telegram.keyboards import get_api_management_keyboard, get_api_list_keyboard, get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_api_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show API management menu.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        # Get all APIs for this user
        api_ops = APIOperations()
        apis = await api_ops.get_all_apis(user_id)
        
        message = "🔑 **API Management**\n\n"
        
        if apis:
            message += f"You have {len(apis)} API credential(s) configured.\n\n"
            message += "Select an action below:"
        else:
            message += "No API credentials configured yet.\n\n"
            message += "Add your Delta Exchange India API credentials to get started."
        
        keyboard = get_api_management_keyboard(apis)
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        logger.info(f"[show_api_management] Displayed API management for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_api_management] Error: {e}", exc_info=True)
        error_msg = "❌ Error loading API management. Please try again."
        
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)


@require_auth
@log_function_call
async def handle_add_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start API addition conversation.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        query = update.callback_query
        
        message = (
            "➕ **Add New API**\n\n"
            "To add Delta Exchange India API credentials, please provide the following:\n\n"
            "1️⃣ API Name (e.g., 'Main Account')\n"
            "2️⃣ API Description (optional)\n"
            "3️⃣ API Key\n"
            "4️⃣ API Secret\n\n"
            "⚠️ **Important:**\n"
            "• Your API secret will be encrypted and stored securely\n"
            "• Never share your API credentials with anyone\n"
            "• You can find your API credentials at https://api.india.delta.exchange\n\n"
            "**Please send your API name:**"
        )
        
        await query.edit_message_text(message, parse_mode='Markdown')
        
        # Set conversation state
        context.user_data['conversation'] = 'add_api'
        context.user_data['add_api_step'] = 'name'
        
        logger.info(f"[handle_add_api] Started API addition for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"[handle_add_api] Error: {e}", exc_info=True)
        await query.edit_message_text("❌ Error starting API addition.")


@require_auth
@log_function_call
async def handle_edit_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show API list for editing.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        api_ops = APIOperations()
        apis = await api_ops.get_all_apis(user_id)
        
        if not apis:
            await query.edit_message_text(
                "❌ No APIs configured to edit.\n\n"
                "Add an API first.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        message = "✏️ **Edit API**\n\nSelect an API to edit:"
        keyboard = get_api_list_keyboard(apis, 'edit')
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[handle_edit_api] Showed API list for user {user_id}")
        
    except Exception as e:
        logger.error(f"[handle_edit_api] Error: {e}", exc_info=True)
        await query.edit_message_text("❌ Error loading APIs.")


@require_auth
@log_function_call
async def handle_delete_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show API list for deletion.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        api_ops = APIOperations()
        apis = await api_ops.get_all_apis(user_id)
        
        if not apis:
            await query.edit_message_text(
                "❌ No APIs configured to delete.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        message = "🗑️ **Delete API**\n\n⚠️ Select an API to delete:"
        keyboard = get_api_list_keyboard(apis, 'delete')
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[handle_delete_api] Showed API list for deletion for user {user_id}")
        
    except Exception as e:
        logger.error(f"[handle_delete_api] Error: {e}", exc_info=True)
        await query.edit_message_text("❌ Error loading APIs.")


@require_auth
@log_function_call
async def confirm_delete_api(update: Update, context: ContextTypes.DEFAULT_TYPE, api_name: str):
    """
    Confirm API deletion.
    
    Args:
        update: Telegram update
        context: Callback context
        api_name: API name to delete
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        from telegram.keyboards import get_yes_no_keyboard
        
        message = (
            f"⚠️ **Confirm Deletion**\n\n"
            f"Are you sure you want to delete API '{api_name}'?\n\n"
            f"This action cannot be undone."
        )
        
        keyboard = get_yes_no_keyboard(
            yes_data=f"api:delete:confirm:{api_name}",
            no_data="menu:manage_api"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[confirm_delete_api] Asked confirmation for deleting {api_name}")
        
    except Exception as e:
        logger.error(f"[confirm_delete_api] Error: {e}", exc_info=True)
        await query.edit_message_text("❌ Error confirming deletion.")


@require_auth
@log_function_call
async def execute_delete_api(update: Update, context: ContextTypes.DEFAULT_TYPE, api_name: str):
    """
    Execute API deletion.
    
    Args:
        update: Telegram update
        context: Callback context
        api_name: API name to delete
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        api_ops = APIOperations()
        result = await api_ops.delete_api(user_id, api_name)
        
        if result.get('success'):
            message = f"✅ API '{api_name}' deleted successfully!"
            logger.info(f"[execute_delete_api] Deleted API {api_name} for user {user_id}")
        else:
            message = f"❌ Failed to delete API: {result.get('error', 'Unknown error')}"
            logger.error(f"[execute_delete_api] Failed to delete API: {result}")
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"[execute_delete_api] Error: {e}", exc_info=True)
        await query.edit_message_text("❌ Error deleting API.")


if __name__ == "__main__":
    print("API handler module loaded")
