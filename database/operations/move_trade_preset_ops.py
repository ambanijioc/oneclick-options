"""
Move Trade Preset database operations.
Stores combinations of API + Move Strategy for quick execution.
"""

from typing import List, Optional
from bson import ObjectId

from database.connection import get_database
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_move_trade_preset(user_id: int, preset_data: dict) -> bool:
    """Create a new move trade preset."""
    try:
        db = get_database()
        
        document = {
            'user_id': user_id,
            'preset_name': preset_data['preset_name'],
            'api_id': preset_data['api_id'],
            'strategy_id': preset_data['strategy_id'],
        }
        
        result = await db.move_trade_presets.insert_one(document)
        logger.info(f"Created move trade preset for user {user_id}: {preset_data['preset_name']}")
        return bool(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create move trade preset: {e}", exc_info=True)
        return False


async def get_move_trade_presets(user_id: int) -> List[dict]:
    """Get all move trade presets for a user."""
    try:
        db = get_database()
        
        cursor = db.move_trade_presets.find({'user_id': user_id})
        presets = await cursor.to_list(length=None)
        
        return presets
    
    except Exception as e:
        logger.error(f"Failed to get move trade presets: {e}", exc_info=True)
        return []


async def get_move_trade_preset_by_id(preset_id: str) -> Optional[dict]:
    """Get a specific move trade preset by ID."""
    try:
        db = get_database()
        
        preset = await db.move_trade_presets.find_one({'_id': ObjectId(preset_id)})
        return preset
    
    except Exception as e:
        logger.error(f"Failed to get move trade preset: {e}", exc_info=True)
        return None


async def update_move_trade_preset(preset_id: str, update_data: dict) -> bool:
    """Update a move trade preset."""
    try:
        db = get_database()
        
        result = await db.move_trade_presets.update_one(
            {'_id': ObjectId(preset_id)},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update move trade preset: {e}", exc_info=True)
        return False


async def delete_move_trade_preset(preset_id: str) -> bool:
    """Delete a move trade preset."""
    try:
        db = get_database()
        
        result = await db.move_trade_presets.delete_one({'_id': ObjectId(preset_id)})
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete move trade preset: {e}", exc_info=True)
        return False
      
