"""
API credential validation.
"""

from typing import Optional, Tuple
import httpx

from config import settings
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def validate_api_credentials(api_key: str, api_secret: str) -> Tuple[bool, Optional[str]]:
    """
    Validate API credentials format.
    
    Args:
        api_key: API key
        api_secret: API secret
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check key length
    if len(api_key.strip()) < 10:
        return False, "API key is too short"
    
    if len(api_secret.strip()) < 10:
        return False, "API secret is too short"
    
    # Check for whitespace
    if ' ' in api_key or ' ' in api_secret:
        return False, "API credentials should not contain spaces"
    
    return True, None


async def test_api_connection(api_key: str, api_secret: str) -> Tuple[bool, Optional[str]]:
    """
    Test API connection by making a simple API call.
    
    Args:
        api_key: API key
        api_secret: API secret
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Import here to avoid circular dependency
        from delta.client import DeltaClient
        
        # Create client
        client = DeltaClient(api_key, api_secret)
        
        # Test connection with a simple call (get wallet balance)
        response = await client.get_wallet_balance()
        
        if response.get('success'):
            logger.info("API credentials validated successfully")
            return True, None
        else:
            error_msg = response.get('error', {}).get('message', 'Unknown error')
            logger.warning(f"API validation failed: {error_msg}")
            return False, f"API validation failed: {error_msg}"
    
    except Exception as e:
        logger.error(f"API connection test failed: {e}", exc_info=True)
        return False, f"Connection test failed: {str(e)}"


async def check_api_permissions(api_key: str, api_secret: str) -> Tuple[bool, list]:
    """
    Check API permissions (read, trade, etc.).
    
    Args:
        api_key: API key
        api_secret: API secret
    
    Returns:
        Tuple of (has_required_permissions, missing_permissions)
    """
    try:
        # Import here to avoid circular dependency
        from delta.client import DeltaClient
        
        # Required permissions
        required_permissions = ['read', 'trade']
        missing_permissions = []
        
        # Create client
        client = DeltaClient(api_key, api_secret)
        
        # Try to get wallet balance (read permission)
        try:
            await client.get_wallet_balance()
        except Exception as e:
            logger.warning(f"Read permission check failed: {e}")
            missing_permissions.append('read')
        
        # Try to get open orders (trade permission check)
        try:
            await client.get_open_orders()
        except Exception as e:
            logger.warning(f"Trade permission check failed: {e}")
            missing_permissions.append('trade')
        
        has_all_permissions = len(missing_permissions) == 0
        
        if has_all_permissions:
            logger.info("API has all required permissions")
        else:
            logger.warning(f"API missing permissions: {missing_permissions}")
        
        return has_all_permissions, missing_permissions
    
    except Exception as e:
        logger.error(f"Permission check failed: {e}", exc_info=True)
        return False, required_permissions


if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test validation
        is_valid, error = await validate_api_credentials("test_key_123", "test_secret_456")
        print(f"Format validation: Valid={is_valid}, Error={error}")
        
        is_valid, error = await validate_api_credentials("short", "too_short")
        print(f"Format validation (short): Valid={is_valid}, Error={error}")
    
    asyncio.run(test())
  
