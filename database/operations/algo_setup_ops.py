"""
Database operations for algo setups.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from database.models.algo_setup import AlgoSetup
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_algo_setup(user_id: int, setup_data: dict) -> Optional[str]:
    """Create a new algo setup."""
    try:
        db = get_database()
        
        setup = {
            'user_id': user_id,
            'manual_preset_id': setup_data['manual_preset_id'],
            'execution_time': setup_data['execution_time'],
            'is_active': True,
            'last_execution': None,
            'last_execution_status': None,
            'last_execution_details': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.algo_setups.insert_one(setup)
        logger.info(f"Created algo setup: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create algo setup: {e}", exc_info=True)
        return None


async def get_algo_setups(user_id: int, active_only: bool = False) -> List[dict]:
    """Get all algo setups for a user."""
    try:
        db = get_database()
        
        query = {'user_id': user_id}
        if active_only:
            query['is_active'] = True
        
        cursor = db.algo_setups.find(query)
        setups = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for setup in setups:
            setup['id'] = str(setup['_id'])
            del setup['_id']
        
        return setups
    
    except Exception as e:
        logger.error(f"Failed to get algo setups: {e}", exc_info=True)
        return []


async def get_algo_setup(setup_id: str) -> Optional[dict]:
    """Get a specific algo setup."""
    try:
        db = get_database()
        
        setup = await db.algo_setups.find_one({'_id': ObjectId(setup_id)})
        
        if setup:
            setup['id'] = str(setup['_id'])
            del setup['_id']
        
        return setup
    
    except Exception as e:
        logger.error(f"Failed to get algo setup: {e}", exc_info=True)
        return None


async def update_algo_setup(setup_id: str, setup_data: dict) -> bool:
    """Update an algo setup."""
    try:
        db = get_database()
        
        update_data = {
            'manual_preset_id': setup_data['manual_preset_id'],
            'execution_time': setup_data['execution_time'],
            'updated_at': datetime.utcnow()
        }
        
        result = await db.algo_setups.update_one(
            {'_id': ObjectId(setup_id)},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update algo setup: {e}", exc_info=True)
        return False


async def delete_algo_setup(setup_id: str) -> bool:
    """Delete an algo setup."""
    try:
        db = get_database()
        
        result = await db.algo_setups.delete_one({'_id': ObjectId(setup_id)})
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete algo setup: {e}", exc_info=True)
        return False


async def update_algo_execution(setup_id: str, status: str, details: dict = None) -> bool:
    """Update algo setup execution details."""
    try:
        db = get_database()
        
        update_data = {
            'last_execution': datetime.utcnow(),
            'last_execution_status': status,
            'last_execution_details': details or {},
            'updated_at': datetime.utcnow()
        }
        
        result = await db.algo_setups.update_one(
            {'_id': ObjectId(setup_id)},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update algo execution: {e}", exc_info=True)
        return False


async def get_all_active_algo_setups() -> List[dict]:
    """Get all active algo setups across all users."""
    try:
        db = get_database()
        
        cursor = db.algo_setups.find({'is_active': True})
        setups = await cursor.to_list(length=1000)
        
        # Convert ObjectId to string
        for setup in setups:
            setup['id'] = str(setup['_id'])
            del setup['_id']
        
        return setups
    
    except Exception as e:
        logger.error(f"Failed to get all active algo setups: {e}", exc_info=True)
        return []
  
