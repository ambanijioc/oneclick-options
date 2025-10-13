"""
Message router to direct messages to appropriate handlers based on state.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager, ConversationState

logger = setup_logger(__name__)


async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Route text messages to appropriate handler based on user's conversation state.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    user = update.effective_user
    
    # Get current state
    state = await state_manager.get_state(user.id)
    
    # If no state, ignore the message (let other handlers process it)
    if state is None:
        return
    
    # Import handlers dynamically to avoid circular imports
    from .api_handler import (
        handle_api_name_input,
        handle_api_description_input,
        handle_api_key_input,
        handle_api_secret_input
    )
    
    # Route based on state
    if state == ConversationState.API_ADD_NAME:
        await handle_api_name_input(update, context)
    
    elif state == ConversationState.API_ADD_DESCRIPTION:
        await handle_api_description_input(update, context)
    
    elif state == ConversationState.API_ADD_KEY:
        await handle_api_key_input(update, context)
    
    elif state == ConversationState.API_ADD_SECRET:
        await handle_api_secret_input(update, context)
    
    # Add other state handlers here as needed
    else:
        logger.warning(f"Unhandled conversation state: {state} for user {user.id}")


if __name__ == "__main__":
    print("Message router module loaded")
  
