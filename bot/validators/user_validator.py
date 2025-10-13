"""
User authorization and validation.
"""

from typing import Optional, Dict, Any
from telegram import User

from config import settings
from bot.utils.logger import setup_logger, log_to_telegram

logger = setup_logger(__name__)


def is_user_authorized(user_id: int) -> bool:
    """
    Check if user is authorized to use the bot.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        True if authorized, False otherwise
    """
    allowed_users = settings.get_allowed_user_ids()
    is_authorized = user_id in allowed_users
    
    if not is_authorized:
        logger.warning(f"Unauthorized access attempt by user {user_id}")
    
    return is_authorized


async def check_user_authorization(user: User) -> bool:
    """
    Check user authorization and log unauthorized attempts.
    
    Args:
        user: Telegram user object
    
    Returns:
        True if authorized, False otherwise
    """
    if not is_user_authorized(user.id):
        logger.warning(
            f"Unauthorized access attempt - "
            f"User ID: {user.id}, Username: {user.username}, "
            f"Name: {user.first_name} {user.last_name or ''}"
        )
        
        # Log to Telegram
        await log_to_telegram(
            message=f"Unauthorized access attempt by user {user.id} (@{user.username})",
            level="WARNING",
            module="user_validator",
            user_id=user.id
        )
        
        return False
    
    return True


def get_user_info(user: User) -> Dict[str, Any]:
    """
    Extract user information from Telegram user object.
    
    Args:
        user: Telegram user object
    
    Returns:
        Dictionary with user information
    """
    return {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code,
        "is_bot": user.is_bot
    }


if __name__ == "__main__":
    # Test validation
    print(f"Allowed user IDs: {settings.get_allowed_user_ids()}")
    
    # Test authorization
    test_user_id = 12345
    is_auth = is_user_authorized(test_user_id)
    print(f"User {test_user_id} authorized: {is_auth}")
  
