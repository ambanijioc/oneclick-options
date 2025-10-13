"""
CRUD operations for user settings.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from database.models.user_settings import (
    UserSettings,
    UserSettingsCreate,
    UserSettingsUpdate
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_user_settings(data: UserSettingsCreate) -> str:
    """
    Create new user settings.
    
    Args:
        data: User settings creation data
    
    Returns:
        Created settings ID
    """
    try:
        db = get_database()
        
        # Check if settings already exist
        existing = await db.user_settings.find_one({"user_id": data.user_id})
        if existing:
            logger.warning(f"User settings already exist for user {data.user_id}")
            return str(existing["_id"])
        
        # Create settings document
        settings = UserSettings(
            user_id=data.user_id,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            notifications_enabled=data.notifications_enabled,
            log_trades=data.log_trades,
            daily_trade_limit=data.daily_trade_limit
        )
        
        # Insert to database
        result = await db.user_settings.insert_one(settings.to_dict())
        settings_id = str(result.inserted_id)
        
        logger.info(f"Created user settings: {settings_id} for user {data.user_id}")
        
        return settings_id
    
    except Exception as e:
        logger.error(f"Failed to create user settings: {e}", exc_info=True)
        raise


async def get_user_settings(user_id: int) -> Optional[UserSettings]:
    """
    Get user settings by user ID.
    
    Args:
        user_id: User ID
    
    Returns:
        User settings or None if not found
    """
    try:
        db = get_database()
        
        # Fetch settings
        doc = await db.user_settings.find_one({"user_id": user_id})
        
        if not doc:
            logger.debug(f"User settings not found for user {user_id}")
            return None
        
        doc["_id"] = ObjectId(doc["_id"])
        settings = UserSettings(**doc)
        
        # Update last_active
        await update_user_settings(user_id, {"last_active": datetime.now()})
        
        logger.debug(f"Retrieved user settings for user {user_id}")
        
        return settings
    
    except Exception as e:
        logger.error(f"Failed to get user settings: {e}", exc_info=True)
        raise


async def get_or_create_user_settings(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> UserSettings:
    """
    Get existing user settings or create new ones.
    
    Args:
        user_id: User ID
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
    
    Returns:
        User settings
    """
    try:
        # Try to get existing settings
        settings = await get_user_settings(user_id)
        
        if settings:
            return settings
        
        # Create new settings
        create_data = UserSettingsCreate(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        settings_id = await create_user_settings(create_data)
        settings = await get_user_settings(user_id)
        
        logger.info(f"Created new user settings for user {user_id}")
        
        return settings
    
    except Exception as e:
        logger.error(f"Failed to get or create user settings: {e}", exc_info=True)
        raise


async def update_user_settings(
    user_id: int,
    update_data: Dict[str, Any]
) -> bool:
    """
    Update user settings.
    
    Args:
        user_id: User ID
        update_data: Data to update
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update document
        result = await db.user_settings.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.debug(f"Updated user settings for user {user_id}")
            return True
        else:
            return False
    
    except Exception as e:
        logger.error(f"Failed to update user settings: {e}", exc_info=True)
        raise


async def increment_user_trade_count(user_id: int) -> bool:
    """
    Increment user's daily trade count.
    
    Args:
        user_id: User ID
    
    Returns:
        True if incremented successfully
    """
    try:
        db = get_database()
        
        # Get current settings
        settings = await get_user_settings(user_id)
        
        if not settings:
            logger.warning(f"Cannot increment trade count - no settings for user {user_id}")
            return False
        
        # Check if new day
        current_date = datetime.now().date()
        reset_count = False
        
        if settings.last_trade_date:
            if settings.last_trade_date.date() < current_date:
                reset_count = True
        
        # Update trade count
        if reset_count:
            result = await db.user_settings.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "trades_today": 1,
                        "last_trade_date": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
            )
        else:
            result = await db.user_settings.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"trades_today": 1},
                    "$set": {
                        "last_trade_date": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
            )
        
        if result.modified_count > 0:
            logger.debug(f"Incremented trade count for user {user_id}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Failed to increment trade count: {e}", exc_info=True)
        raise


async def can_user_trade_today(user_id: int) -> bool:
    """
    Check if user can execute more trades today.
    
    Args:
        user_id: User ID
    
    Returns:
        True if user can trade, False otherwise
    """
    try:
        settings = await get_user_settings(user_id)
        
        if not settings:
            # No settings means user can trade (will be created on first trade)
            return True
        
        # Check trade limit
        current_date = datetime.now().date()
        
        # Reset if new day
        if settings.last_trade_date and settings.last_trade_date.date() < current_date:
            return True
        
        # Check against limit
        can_trade = settings.trades_today < settings.daily_trade_limit
        
        if not can_trade:
            logger.warning(
                f"User {user_id} has reached daily trade limit "
                f"({settings.trades_today}/{settings.daily_trade_limit})"
            )
        
        return can_trade
    
    except Exception as e:
        logger.error(f"Failed to check trade limit: {e}", exc_info=True)
        # Default to allowing trade if check fails
        return True


if __name__ == "__main__":
    import asyncio
    
    async def test():
        from database.connection import connect_db, close_db
        
        await connect_db()
        
        # Test create user settings
        settings_data = UserSettingsCreate(
            user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        try:
            settings_id = await create_user_settings(settings_data)
            print(f"Created user settings: {settings_id}")
            
            # Get settings
            settings = await get_user_settings(12345)
            print(f"Retrieved settings: {settings.username}")
            
            # Check trade limit
            can_trade = await can_user_trade_today(12345)
            print(f"Can trade: {can_trade}")
            
            # Increment trade count
            incremented = await increment_user_trade_count(12345)
            print(f"Incremented: {incremented}")
            
            # Get updated settings
            settings = await get_user_settings(12345)
            print(f"Trades today: {settings.trades_today}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        await close_db()
    
    asyncio.run(test())
  
