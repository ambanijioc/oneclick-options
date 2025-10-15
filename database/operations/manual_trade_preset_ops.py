"""
Database operations for manual trade presets.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from database.models.manual_trade_preset import ManualTradePreset
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_manual_trade_preset(user_id: int, preset_data: dict) -> Optional[str]:
    """Create a new manual trade preset."""
    try:
        db = await get_database()
        
        preset = {
            'user_id': user_id,
            'preset_name': preset_data['preset_name'],
            'api_credential_id': preset_data['api_credential_id'],
            'strategy_preset_id': preset_data['strategy_preset_id'],
            'strategy_type': preset_data['strategy_type'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.manual_trade_presets.insert_one(preset)
        logger.info(f"Created manual trade preset: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create manual trade preset: {e}", exc_info=True)
        return None


async def get_manual_trade_presets(user_id: int) -> List[dict]:
    """Get all manual trade presets for a user."""
    try:
        db = await get_database()
        
        cursor = db.manual_trade_presets.find({'user_id': user_id})
        presets = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for preset in presets:
            preset['id'] = str(preset['_id'])
            del preset['_id']
        
        return presets
    
    except Exception as e:
        logger.error(f"Failed to get manual trade presets: {e}", exc_info=True)
        return []


async def get_manual_trade_preset(preset_id: str) -> Optional[dict]:
    """Get a specific manual trade preset."""
    try:
        db = await get_database()
        
        preset = await db.manual_trade_presets.find_one({'_id': ObjectId(preset_id)})
        
        if preset:
            preset['id'] = str(preset['_id'])
            del preset['_id']
        
        return preset
    
    except Exception as e:
        logger.error(f"Failed to get manual trade preset: {e}", exc_info=True)
        return None


async def update_manual_trade_preset(preset_id: str, preset_data: dict) -> bool:
    """Update a manual trade preset."""
    try:
        db = await get_database()
        
        update_data = {
            'api_credential_id': preset_data['api_credential_id'],
            'strategy_preset_id': preset_data['strategy_preset_id'],
            'strategy_type': preset_data['strategy_type'],
            'updated_at': datetime.utcnow()
        }
        
        result = await db.manual_trade_presets.update_one(
            {'_id': ObjectId(preset_id)},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update manual trade preset: {e}", exc_info=True)
        return False


async def delete_manual_trade_preset(preset_id: str) -> bool:
    """Delete a manual trade preset."""
    try:
        db = await get_database()
        
        result = await db.manual_trade_presets.delete_one({'_id': ObjectId(preset_id)})
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete manual trade preset: {e}", exc_info=True)
        return False
  
