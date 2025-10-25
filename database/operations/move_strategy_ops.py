"""
Database operations for MOVE strategies - COMPLETE CRUD.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_move_strategy(user_id: int, strategy_data: dict) -> Optional[str]:
    """Create a new MOVE strategy."""
    try:
        db = get_database()
        
        strategy = {
            'user_id': user_id,
            'strategy_name': strategy_data['strategy_name'],
            'description': strategy_data.get('description', ''),
            'asset': strategy_data['asset'],
            'expiry': strategy_data.get('expiry', 'daily'),
            'direction': strategy_data['direction'],
            'atm_offset': strategy_data.get('atm_offset', 0),
            'lot_size': strategy_data.get('lot_size', 1),  # ✅ ADD LOT SIZE
            'stop_loss_trigger': strategy_data.get('stop_loss_trigger'),
            'stop_loss_limit': strategy_data.get('stop_loss_limit'),
            'target_trigger': strategy_data.get('target_trigger'),
            'target_limit': strategy_data.get('target_limit'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_strategies.insert_one(strategy)
        logger.info(f"Created MOVE strategy: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create MOVE strategy: {e}", exc_info=True)
        return None


async def get_move_strategies(user_id: int) -> List[dict]:
    """Get all MOVE strategies for a user."""
    try:
        db = get_database()
        cursor = db.move_strategies.find({'user_id': user_id}).sort('created_at', -1)
        strategies = await cursor.to_list(length=100)
        
        for strategy in strategies:
            strategy['id'] = str(strategy['_id'])
            del strategy['_id']
            
            # Backward compatibility
            if 'expiry' not in strategy:
                strategy['expiry'] = 'daily'
            if 'description' not in strategy:
                strategy['description'] = ''
            if 'lot_size' not in strategy:
                strategy['lot_size'] = 1
        
        return strategies
    
    except Exception as e:
        logger.error(f"Failed to get MOVE strategies: {e}", exc_info=True)
        return []


# ✅ FIX: Add user_id parameter for security
async def get_move_strategy(user_id: int, strategy_id: str) -> Optional[dict]:
    """Get a specific MOVE strategy for a user."""
    try:
        db = get_database()
        
        # ✅ Verify strategy belongs to user
        strategy = await db.move_strategies.find_one({
            '_id': ObjectId(strategy_id),
            'user_id': user_id
        })
        
        if strategy:
            strategy['id'] = str(strategy['_id'])
            del strategy['_id']
            
            # Backward compatibility
            if 'expiry' not in strategy:
                strategy['expiry'] = 'daily'
            if 'description' not in strategy:
                strategy['description'] = ''
            if 'lot_size' not in strategy:
                strategy['lot_size'] = 1
        
        return strategy
    
    except Exception as e:
        logger.error(f"Failed to get MOVE strategy: {e}", exc_info=True)
        return None


# ✅ FIX: Add user_id parameter for security
async def update_move_strategy(user_id: int, strategy_id: str, strategy_data: dict) -> bool:
    """Update a MOVE strategy."""
    try:
        db = get_database()
        
        update_data = {
            **strategy_data,  # Use all provided fields
            'updated_at': datetime.utcnow()
        }
        
        # ✅ Only update if strategy belongs to user
        result = await db.move_strategies.update_one(
            {
                '_id': ObjectId(strategy_id),
                'user_id': user_id
            },
            {'$set': update_data}
        )
        
        logger.info(f"Updated MOVE strategy: {strategy_id}")
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update MOVE strategy: {e}", exc_info=True)
        return False


# ✅ FIX: Add user_id parameter for security
async def delete_move_strategy(user_id: int, strategy_id: str) -> bool:
    """Delete a MOVE strategy."""
    try:
        db = get_database()
        
        # ✅ Only delete if strategy belongs to user
        result = await db.move_strategies.delete_one({
            '_id': ObjectId(strategy_id),
            'user_id': user_id
        })
        
        if result.deleted_count > 0:
            logger.info(f"Deleted MOVE strategy: {strategy_id}")
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete MOVE strategy: {e}", exc_info=True)
        return False


# Trade Preset Operations

async def create_move_trade_preset(user_id: int, preset_data: dict) -> Optional[str]:
    """Create a new MOVE trade preset."""
    try:
        db = get_database()
        
        preset = {
            'user_id': user_id,
            'preset_name': preset_data['preset_name'],
            'api_id': preset_data['api_id'],
            'strategy_id': preset_data['strategy_id'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_trade_presets.insert_one(preset)
        logger.info(f"Created MOVE trade preset: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create MOVE trade preset: {e}", exc_info=True)
        return None


async def get_move_trade_presets(user_id: int) -> List[dict]:
    """Get all MOVE trade presets for a user."""
    try:
        db = get_database()
        cursor = db.move_trade_presets.find({'user_id': user_id}).sort('created_at', -1)
        presets = await cursor.to_list(length=100)
        
        for preset in presets:
            preset['id'] = str(preset['_id'])
            del preset['_id']
        
        return presets
    
    except Exception as e:
        logger.error(f"Failed to get MOVE trade presets: {e}", exc_info=True)
        return []


async def get_move_trade_preset(user_id: int, preset_id: str) -> Optional[dict]:
    """Get a specific MOVE trade preset."""
    try:
        db = get_database()
        preset = await db.move_trade_presets.find_one({
            '_id': ObjectId(preset_id),
            'user_id': user_id
        })
        
        if preset:
            preset['id'] = str(preset['_id'])
            del preset['_id']
        
        return preset
    
    except Exception as e:
        logger.error(f"Failed to get MOVE trade preset: {e}", exc_info=True)
        return None


async def update_move_trade_preset(user_id: int, preset_id: str, preset_data: dict) -> bool:
    """Update a MOVE trade preset."""
    try:
        db = get_database()
        
        update_data = {
            'preset_name': preset_data['preset_name'],
            'api_id': preset_data['api_id'],
            'strategy_id': preset_data['strategy_id'],
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_trade_presets.update_one(
            {
                '_id': ObjectId(preset_id),
                'user_id': user_id
            },
            {'$set': update_data}
        )
        
        logger.info(f"Updated MOVE trade preset: {preset_id}")
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update MOVE trade preset: {e}", exc_info=True)
        return False


async def delete_move_trade_preset(user_id: int, preset_id: str) -> bool:
    """Delete a MOVE trade preset."""
    try:
        db = get_database()
        result = await db.move_trade_presets.delete_one({
            '_id': ObjectId(preset_id),
            'user_id': user_id
        })
        
        if result.deleted_count > 0:
            logger.info(f"Deleted MOVE trade preset: {preset_id}")
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete MOVE trade preset: {e}", exc_info=True)
        return False
        
