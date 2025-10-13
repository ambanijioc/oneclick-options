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
    try:
        # Log that we received a message
        logger.info("=" * 50)
        logger.info("MESSAGE ROUTER CALLED")
        logger.info("=" * 50)
        
        if not update.message:
            logger.warning("No message in update")
            return
        
        if not update.message.text:
            logger.warning("No text in message")
            return
        
        user = update.effective_user
        text = update.message.text.strip()
        
        logger.info(f"User {user.id} ({user.first_name}) sent: '{text[:50]}'")
        
        # Skip commands (they're handled by command handlers)
        if text.startswith('/'):
            logger.info(f"Skipping command: {text}")
            return
        
        # Get current state
        state = await state_manager.get_state(user.id)
        
        logger.info(f"Current conversation state: {state.value if state else 'None'}")
        
        # If no state, send helpful message
        if state is None:
            logger.warning(f"No active conversation for user {user.id}")
            await update.message.reply_text(
                "Please use /start to begin.",
                parse_mode='HTML'
            )
            return
        
        logger.info(f"Routing to handler for state: {state.value}")
        
        # Route based on conversation state
        # API conversation states
        if state == ConversationState.API_ADD_NAME:
            logger.info("→ Calling handle_api_name_input")
            from .api_handler import handle_api_name_input
            await handle_api_name_input(update, context)
        
        elif state == ConversationState.API_ADD_DESCRIPTION:
            logger.info("→ Calling handle_api_description_input")
            from .api_handler import handle_api_description_input
            await handle_api_description_input(update, context)
        
        elif state == ConversationState.API_ADD_KEY:
            logger.info("→ Calling handle_api_key_input")
            from .api_handler import handle_api_key_input
            await handle_api_key_input(update, context)
        
        elif state == ConversationState.API_ADD_SECRET:
            logger.info("→ Calling handle_api_secret_input")
            from .api_handler import handle_api_secret_input
            await handle_api_secret_input(update, context)
        
        # Add more state handlers here as needed
        
        else:
            logger.warning(f"Unhandled conversation state: {state.value}")
            await update.message.reply_text(
                "❌ Something went wrong. Please use /start to return to main menu.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(user.id)
        
        logger.info("=" * 50)
        logger.info("MESSAGE ROUTER COMPLETE")
        logger.info("=" * 50)
    
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"ERROR IN MESSAGE ROUTER: {e}", exc_info=True)
        logger.error("=" * 50)
        
        try:
            await update.message.reply_text(
                "❌ An error occurred. Please try /start.",
                parse_mode='HTML'
            )
            await state_manager.clear_state(update.effective_user.id)
        except Exception:
            pass


if __name__ == "__main__":
    print("Message router module loaded")
            
