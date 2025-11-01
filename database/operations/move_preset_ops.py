"""
MOVE Trade Preset Database Operations

Handle MOVE preset creation, updates, and retrievals.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_move_preset(
    db: AsyncIOMotorDatabase,
    user_id: int,
    preset_data: dict
) -> str:
    """Create a MOVE preset"""
    try:
        preset_doc = {
            'user_id': user_id,
            'name': preset_data.get('name'),
            'entry_price': preset_data.get('entry_price'),
            'lot_size': preset_data.get('lot_size'),
            'sl_price': preset_data.get('sl_price'),
            'target_price': preset_data.get('target_price'),
            'direction': preset_data.get('direction'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        
        result = await db.move_presets.insert_one(preset_doc)
        logger.info(f"✅ MOVE preset created: {result.inserted_id}")
        
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"❌ Error creating MOVE preset: {e}")
        raise


async def get_move_preset(
    db: AsyncIOMotorDatabase,
    preset_id: str
) -> dict:
    """Get a MOVE preset by ID"""
    try:
        preset = await db.move_presets.find_one({'_id': ObjectId(preset_id)})
        return preset or {}
    except Exception as e:
        logger.error(f"❌ Error fetching MOVE preset: {e}")
        return {}


async def get_user_move_presets(
    db: AsyncIOMotorDatabase,
    user_id: int
) -> list:
    """Get all MOVE presets for a user"""
    try:
        presets = await db.move_presets.find({'user_id': user_id}).to_list(None)
        return presets or []
    except Exception as e:
        logger.error(f"❌ Error fetching MOVE presets: {e}")
        return []


async def update_move_preset(
    db: AsyncIOMotorDatabase,
    preset_id: str,
    updates: dict
) -> bool:
    """Update a MOVE preset"""
    try:
        updates['updated_at'] = datetime.utcnow()
        
        result = await db.move_presets.update_one(
            {'_id': ObjectId(preset_id)},
            {'$set': updates}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ MOVE preset {preset_id} updated")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error updating MOVE preset: {e}")
        raise


async def delete_move_preset(
    db: AsyncIOMotorDatabase,
    preset_id: str
) -> bool:
    """Delete a MOVE preset"""
    try:
        result = await db.move_presets.delete_one({'_id': ObjectId(preset_id)})
        
        if result.deleted_count > 0:
            logger.info(f"✅ MOVE preset {preset_id} deleted")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error deleting MOVE preset: {e}")
        raise


__all__ = [
    'create_move_preset',
    'get_move_preset',
    'get_user_move_presets',
    'update_move_preset',
    'delete_move_preset',
]
