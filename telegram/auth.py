"""
Telegram bot authentication and authorization.
Controls access to the bot based on whitelisted user IDs.
"""

from typing import Optional
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from config import config
from logger import logger, log_function_call


@log_function_call
def is_user_authorized(user_id: int) -> bool:
    """
    Check if user is authorized to use the bot.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        True if authorized, False otherwise
    """
    try:
        authorized = config.telegram.is_authorized(user_id)
        
        if not authorized:
            logger.warning(f"[is_user_authorized] Unauthorized access attempt by user {user_id}")
        
        return authorized
        
    except Exception as e:
        logger.error(f"[is_user_authorized] Error checking authorization: {e}")
        return False


def require_auth(func):
    """
    Decorator to require authentication for handler functions.
    
    Args:
        func: Handler function to wrap
    
    Returns:
        Wrapped function with auth check
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        
        if not user:
            logger.warning("[require_auth] No user in update")
            return
        
        if not is_user_authorized(user.id):
            # Send unauthorized message
            if update.message:
                await update.message.reply_text(
                    "❌ **Unauthorized Access**\n\n"
                    "You are not authorized to use this bot.",
                    parse_mode='Markdown'
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "❌ Unauthorized access",
                    show_alert=True
                )
            
            logger.warning(f"[require_auth] Blocked unauthorized user {user.id}")
            return
        
        # User is authorized, proceed with handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper


@log_function_call
async def validate_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Validate user and send appropriate response if unauthorized.
    
    Args:
        update: Telegram update
        context: Callback context
    
    Returns:
        True if user is authorized, False otherwise
    """
    try:
        user = update.effective_user
        
        if not user:
            logger.warning("[validate_user] No user in update")
            return False
        
        if not is_user_authorized(user.id):
            if update.message:
                await update.message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "❌ Unauthorized",
                    show_alert=True
                )
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"[validate_user] Error validating user: {e}")
        return False


if __name__ == "__main__":
    # Test authorization
    print("Testing authorization...")
    
    # Test with dummy user ID
    test_user_id = 123456789
    
    is_auth = is_user_authorized(test_user_id)
    print(f"User {test_user_id} authorized: {is_auth}")
    
    print("\n✅ Auth module test completed!")
              
