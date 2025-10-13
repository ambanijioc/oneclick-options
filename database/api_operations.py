"""
CRUD operations for API credentials management.
Handles encryption/decryption of API secrets.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import pytz

from database.connection import get_database
from database.models import APICredentials
from utils.encryption import encrypt_secret, decrypt_secret
from logger import logger, log_function_call


class APIOperations:
    """API credentials database operations."""
    
    def __init__(self):
        """Initialize API operations."""
        self.collection_name = "api_credentials"
    
    @log_function_call
    async def add_api(
        self,
        user_id: int,
        api_name: str,
        api_description: Optional[str],
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """
        Add new API credentials for a user.
        
        Args:
            user_id: Telegram user ID
            api_name: Friendly name for the API
            api_description: Description of the API
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret (will be encrypted)
        
        Returns:
            Dictionary with success status and API ID
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Check if API name already exists for this user
            existing = await collection.find_one({
                "user_id": user_id,
                "api_name": api_name
            })
            
            if existing:
                logger.warning(
                    f"[APIOperations.add_api] API name '{api_name}' already exists "
                    f"for user {user_id}"
                )
                return {
                    "success": False,
                    "error": f"API name '{api_name}' already exists"
                }
            
            # Encrypt API secret
            encrypted_secret = encrypt_secret(api_secret)
            
            # Create API credentials document
            api_creds = APICredentials(
                user_id=user_id,
                api_name=api_name,
                api_description=api_description,
                api_key=api_key,
                encrypted_api_secret=encrypted_secret
            )
            
            # Insert into database
            result = await collection.insert_one(api_creds.model_dump())
            
            logger.info(
                f"[APIOperations.add_api] API '{api_name}' added successfully "
                f"for user {user_id}, ID: {result.inserted_id}"
            )
            
            return {
                "success": True,
                "api_id": str(result.inserted_id),
                "api_name": api_name
            }
            
        except Exception as e:
            logger.error(f"[APIOperations.add_api] Error adding API: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def get_all_apis(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all API credentials for a user.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            List of API credentials (without decrypted secrets)
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            cursor = collection.find(
                {"user_id": user_id, "is_active": True}
            ).sort("created_at", -1)
            
            apis = []
            async for doc in cursor:
                # Remove encrypted secret from response
                doc['_id'] = str(doc['_id'])
                doc.pop('encrypted_api_secret', None)
                apis.append(doc)
            
            logger.info(
                f"[APIOperations.get_all_apis] Retrieved {len(apis)} APIs "
                f"for user {user_id}"
            )
            
            return apis
            
        except Exception as e:
            logger.error(f"[APIOperations.get_all_apis] Error retrieving APIs: {e}")
            return []
    
    @log_function_call
    async def get_api_by_name(
        self,
        user_id: int,
        api_name: str,
        include_secret: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific API credentials by name.
        
        Args:
            user_id: Telegram user ID
            api_name: API name to retrieve
            include_secret: Whether to decrypt and include the secret
        
        Returns:
            API credentials dictionary or None
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            api_doc = await collection.find_one({
                "user_id": user_id,
                "api_name": api_name,
                "is_active": True
            })
            
            if not api_doc:
                logger.warning(
                    f"[APIOperations.get_api_by_name] API '{api_name}' not found "
                    f"for user {user_id}"
                )
                return None
            
            api_doc['_id'] = str(api_doc['_id'])
            
            # Decrypt secret if requested
            if include_secret and 'encrypted_api_secret' in api_doc:
                try:
                    api_doc['api_secret'] = decrypt_secret(
                        api_doc['encrypted_api_secret']
                    )
                except Exception as e:
                    logger.error(
                        f"[APIOperations.get_api_by_name] Error decrypting secret: {e}"
                    )
            
            # Remove encrypted version
            api_doc.pop('encrypted_api_secret', None)
            
            logger.info(
                f"[APIOperations.get_api_by_name] Retrieved API '{api_name}' "
                f"for user {user_id}"
            )
            
            return api_doc
            
        except Exception as e:
            logger.error(
                f"[APIOperations.get_api_by_name] Error retrieving API: {e}"
            )
            return None
    
    @log_function_call
    async def update_api(
        self,
        user_id: int,
        old_api_name: str,
        new_api_name: Optional[str] = None,
        api_description: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update existing API credentials.
        
        Args:
            user_id: Telegram user ID
            old_api_name: Current API name
            new_api_name: New API name (optional)
            api_description: New description (optional)
            api_key: New API key (optional)
            api_secret: New API secret (optional)
        
        Returns:
            Dictionary with success status
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Check if API exists
            existing = await collection.find_one({
                "user_id": user_id,
                "api_name": old_api_name,
                "is_active": True
            })
            
            if not existing:
                return {
                    "success": False,
                    "error": f"API '{old_api_name}' not found"
                }
            
            # Build update document
            update_doc = {"updated_at": datetime.now(pytz.UTC)}
            
            if new_api_name:
                # Check if new name conflicts
                name_conflict = await collection.find_one({
                    "user_id": user_id,
                    "api_name": new_api_name,
                    "_id": {"$ne": existing["_id"]}
                })
                if name_conflict:
                    return {
                        "success": False,
                        "error": f"API name '{new_api_name}' already exists"
                    }
                update_doc["api_name"] = new_api_name
            
            if api_description is not None:
                update_doc["api_description"] = api_description
            
            if api_key:
                update_doc["api_key"] = api_key
            
            if api_secret:
                update_doc["encrypted_api_secret"] = encrypt_secret(api_secret)
            
            # Update document
            result = await collection.update_one(
                {"_id": existing["_id"]},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[APIOperations.update_api] API '{old_api_name}' updated "
                    f"successfully for user {user_id}"
                )
                return {"success": True, "modified": True}
            else:
                return {"success": True, "modified": False}
            
        except Exception as e:
            logger.error(f"[APIOperations.update_api] Error updating API: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def delete_api(self, user_id: int, api_name: str) -> Dict[str, Any]:
        """
        Delete API credentials (soft delete by marking inactive).
        
        Args:
            user_id: Telegram user ID
            api_name: API name to delete
        
        Returns:
            Dictionary with success status
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            result = await collection.update_one(
                {"user_id": user_id, "api_name": api_name, "is_active": True},
                {"$set": {
                    "is_active": False,
                    "updated_at": datetime.now(pytz.UTC)
                }}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[APIOperations.delete_api] API '{api_name}' deleted "
                    f"for user {user_id}"
                )
                return {"success": True}
            else:
                logger.warning(
                    f"[APIOperations.delete_api] API '{api_name}' not found "
                    f"for user {user_id}"
                )
                return {"success": False, "error": "API not found"}
            
        except Exception as e:
            logger.error(f"[APIOperations.delete_api] Error deleting API: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def get_api_count(self, user_id: int) -> int:
        """
        Get count of active APIs for a user.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Number of active APIs
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            count = await collection.count_documents({
                "user_id": user_id,
                "is_active": True
            })
            
            return count
            
        except Exception as e:
            logger.error(f"[APIOperations.get_api_count] Error counting APIs: {e}")
            return 0


if __name__ == "__main__":
    import asyncio
    
    async def test_api_operations():
        """Test API operations."""
        print("Testing API Operations...")
        
        api_ops = APIOperations()
        test_user_id = 123456789
        
        # Test add API
        result = await api_ops.add_api(
            user_id=test_user_id,
            api_name="Test API",
            api_description="Test description",
            api_key="test_key_123",
            api_secret="test_secret_456"
        )
        print(f"✅ Add API: {result}")
        
        # Test get all APIs
        apis = await api_ops.get_all_apis(test_user_id)
        print(f"✅ Get All APIs: {len(apis)} found")
        
        # Test get specific API
        api = await api_ops.get_api_by_name(
            test_user_id,
            "Test API",
            include_secret=True
        )
        print(f"✅ Get API by name: {api['api_name'] if api else 'Not found'}")
        
        # Test update API
        update_result = await api_ops.update_api(
            user_id=test_user_id,
            old_api_name="Test API",
            api_description="Updated description"
        )
        print(f"✅ Update API: {update_result}")
        
        # Test API count
        count = await api_ops.get_api_count(test_user_id)
        print(f"✅ API Count: {count}")
        
        # Test delete API
        delete_result = await api_ops.delete_api(test_user_id, "Test API")
        print(f"✅ Delete API: {delete_result}")
    
    asyncio.run(test_api_operations())
              
