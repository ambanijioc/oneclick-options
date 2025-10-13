"""
CRUD operations for API credentials.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from config import settings
from database.connection import get_database
from database.models.api_credentials import (
    APICredential,
    APICredentialCreate,
    APICredentialUpdate
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def _encrypt_credential(credential: str) -> str:
    """
    Encrypt API credential using Fernet.
    
    Args:
        credential: Plain text credential
    
    Returns:
        Encrypted credential
    """
    cipher = settings.get_fernet_cipher()
    return cipher.encrypt(credential.encode()).decode()


def _decrypt_credential(encrypted_credential: str) -> str:
    """
    Decrypt API credential using Fernet.
    
    Args:
        encrypted_credential: Encrypted credential
    
    Returns:
        Plain text credential
    """
    cipher = settings.get_fernet_cipher()
    return cipher.decrypt(encrypted_credential.encode()).decode()


async def create_api_credential(data: APICredentialCreate) -> str:
    """
    Create new API credential.
    
    Args:
        data: API credential creation data
    
    Returns:
        Created credential ID
    
    Raises:
        DuplicateKeyError: If API name already exists for user
    """
    try:
        db = get_database()
        
        # Encrypt credentials
        encrypted_key = _encrypt_credential(data.api_key)
        encrypted_secret = _encrypt_credential(data.api_secret)
        
        # Create credential document
        credential = APICredential(
            user_id=data.user_id,
            api_name=data.api_name,
            api_description=data.api_description,
            encrypted_api_key=encrypted_key,
            encrypted_api_secret=encrypted_secret
        )
        
        # Insert to database
        result = await db.api_credentials.insert_one(credential.to_dict())
        credential_id = str(result.inserted_id)
        
        logger.info(f"Created API credential: {credential_id} for user {data.user_id}")
        
        return credential_id
    
    except DuplicateKeyError:
        logger.warning(f"Duplicate API name '{data.api_name}' for user {data.user_id}")
        raise ValueError(f"API name '{data.api_name}' already exists")
    
    except Exception as e:
        logger.error(f"Failed to create API credential: {e}", exc_info=True)
        raise


async def get_api_credentials(
    user_id: int,
    include_inactive: bool = False
) -> List[APICredential]:
    """
    Get all API credentials for a user.
    
    Args:
        user_id: User ID
        include_inactive: Include inactive credentials
    
    Returns:
        List of API credentials
    """
    try:
        db = get_database()
        
        # Build query
        query = {"user_id": user_id}
        if not include_inactive:
            query["is_active"] = True
        
        # Fetch credentials
        cursor = db.api_credentials.find(query).sort("created_at", -1)
        credentials = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            credentials.append(APICredential(**doc))
        
        logger.debug(f"Retrieved {len(credentials)} API credential(s) for user {user_id}")
        
        return credentials
    
    except Exception as e:
        logger.error(f"Failed to get API credentials: {e}", exc_info=True)
        raise


async def get_api_credential_by_id(credential_id: str) -> Optional[APICredential]:
    """
    Get API credential by ID.
    
    Args:
        credential_id: Credential ID
    
    Returns:
        API credential or None if not found
    """
    try:
        db = get_database()
        
        # Fetch credential
        doc = await db.api_credentials.find_one({"_id": ObjectId(credential_id)})
        
        if not doc:
            logger.warning(f"API credential not found: {credential_id}")
            return None
        
        doc["_id"] = ObjectId(doc["_id"])
        credential = APICredential(**doc)
        
        logger.debug(f"Retrieved API credential: {credential_id}")
        
        return credential
    
    except Exception as e:
        logger.error(f"Failed to get API credential by ID: {e}", exc_info=True)
        raise


async def get_decrypted_api_credential(credential_id: str) -> Optional[Tuple[str, str]]:
    """
    Get decrypted API credentials.
    
    Args:
        credential_id: Credential ID
    
    Returns:
        Tuple of (api_key, api_secret) or None if not found
    """
    try:
        credential = await get_api_credential_by_id(credential_id)
        
        if not credential:
            return None
        
        # Decrypt credentials
        api_key = _decrypt_credential(credential.encrypted_api_key)
        api_secret = _decrypt_credential(credential.encrypted_api_secret)
        
        # Update last_used timestamp
        await update_api_credential(credential_id, {"last_used": datetime.now()})
        
        logger.debug(f"Decrypted API credential: {credential_id}")
        
        return (api_key, api_secret)
    
    except Exception as e:
        logger.error(f"Failed to decrypt API credential: {e}", exc_info=True)
        raise


async def update_api_credential(
    credential_id: str,
    update_data: Dict[str, Any]
) -> bool:
    """
    Update API credential.
    
    Args:
        credential_id: Credential ID
        update_data: Data to update
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Encrypt new credentials if provided
        if "api_key" in update_data:
            update_data["encrypted_api_key"] = _encrypt_credential(update_data.pop("api_key"))
        
        if "api_secret" in update_data:
            update_data["encrypted_api_secret"] = _encrypt_credential(update_data.pop("api_secret"))
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update document
        result = await db.api_credentials.update_one(
            {"_id": ObjectId(credential_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated API credential: {credential_id}")
            return True
        else:
            logger.warning(f"No changes made to API credential: {credential_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to update API credential: {e}", exc_info=True)
        raise


async def delete_api_credential(credential_id: str) -> bool:
    """
    Delete API credential.
    
    Args:
        credential_id: Credential ID
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Delete document
        result = await db.api_credentials.delete_one({"_id": ObjectId(credential_id)})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted API credential: {credential_id}")
            return True
        else:
            logger.warning(f"API credential not found for deletion: {credential_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to delete API credential: {e}", exc_info=True)
        raise


async def check_api_name_exists(user_id: int, api_name: str) -> bool:
    """
    Check if API name already exists for user.
    
    Args:
        user_id: User ID
        api_name: API name
    
    Returns:
        True if name exists, False otherwise
    """
    try:
        db = get_database()
        
        count = await db.api_credentials.count_documents({
            "user_id": user_id,
            "api_name": api_name
        })
        
        return count > 0
    
    except Exception as e:
        logger.error(f"Failed to check API name existence: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test encryption
        plain_text = "test_api_key_12345"
        encrypted = _encrypt_credential(plain_text)
        decrypted = _decrypt_credential(encrypted)
        
        print(f"Original: {plain_text}")
        print(f"Encrypted: {encrypted}")
        print(f"Decrypted: {decrypted}")
        print(f"Match: {plain_text == decrypted}")
    
    asyncio.run(test())
      
