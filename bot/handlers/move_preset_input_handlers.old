"""
Input handlers for move trade preset name entry.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager
from bot.utils.message_formatter import escape_html

logger = setup_logger(__name__)


async def handle_move_preset_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle move preset name input."""
    user = update.effective_user
    
    logger.info(f"Handling move preset name input for user {user.id}: {text}")
    
    # Store preset name
    await state_manager.update_data(user.id, {'preset_name': text})
    
    # Get user's APIs
    from database.operations.api_ops import get_api_credentials
    apis = await get_api_credentials(user.id)
    
    if not apis:
        logger.warning(f"No APIs found for user {user.id}")
        
        # Create back button
        keyboard = [[InlineKeyboardButton("🔙 Back to Move Preset Menu", callback_data="menu_move_preset")]]
        
        await update.message.reply_text(
            "<b>❌ No API Credentials</b>\n\n"
            "Please add API credentials first from the main menu.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await state_manager.clear_state(user.id)
        return
    
    logger.info(f"Found {len(apis)} APIs for user {user.id}")
    
    # Build API selection keyboard
    keyboard = []
    for api in apis:
        # Handle both Pydantic model and dict
        if hasattr(api, 'api_name'):
            api_name = api.api_name
            api_id = str(api.id)
        else:
            api_name = api.get('api_name', 'Unknown')
            api_id = str(api.get('_id') or api.get('id'))
        
        keyboard.append([InlineKeyboardButton(
            f"🔑 {api_name}",
            callback_data=f"move_preset_api_{api_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_preset")])
    
    # Update state to API selection
    await state_manager.set_state(user.id, 'move_preset_select_api')
    
    await update.message.reply_text(
        f"<b>➕ Add Move Preset</b>\n\n"
        f"<b>Name:</b> {escape_html(text)}\n\n"
        f"Select API Credentials:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    logger.info(f"Sent API selection to user {user.id}")
    
