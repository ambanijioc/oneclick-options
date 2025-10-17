"""
Database operations for move strategies.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from database.models.move_strategy import MoveStrategy, MoveAutoExecution
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_move_strategy(user_id: int, strategy_data: dict) -> Optional[str]:
    """Create a new move strategy."""
    try:
        db = get_database()
        
        strategy = {
            'user_id': user_id,
            'strategy_name': strategy_data['strategy_name'],
            'asset': strategy_data['asset'],
            'direction': strategy_data['direction'],
            'lot_size': strategy_data['lot_size'],
            'atm_offset': strategy_data.get('atm_offset', 0),
            'stop_loss_trigger': strategy_data.get('stop_loss_trigger'),
            'stop_loss_limit': strategy_data.get('stop_loss_limit'),
            'target_trigger': strategy_data.get('target_trigger'),
            'target_limit': strategy_data.get('target_limit'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_strategies.insert_one(strategy)
        logger.info(f"Created move strategy: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create move strategy: {e}", exc_info=True)
        return None


async def get_move_strategies(user_id: int) -> List[dict]:
    """Get all move strategies for a user."""
    try:
        db = get_database()
        
        cursor = db.move_strategies.find({'user_id': user_id})
        strategies = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for strategy in strategies:
            strategy['id'] = str(strategy['_id'])
            del strategy['_id']
        
        return strategies
    
    except Exception as e:
        logger.error(f"Failed to get move strategies: {e}", exc_info=True)
        return []


async def get_move_strategy(strategy_id: str) -> Optional[dict]:
    """Get a specific move strategy."""
    try:
        db = get_database()
        
        strategy = await db.move_strategies.find_one({'_id': ObjectId(strategy_id)})
        
        if strategy:
            strategy['id'] = str(strategy['_id'])
            del strategy['_id']
        
        return strategy
    
    except Exception as e:
        logger.error(f"Failed to get move strategy: {e}", exc_info=True)
        return None


async def update_move_strategy(strategy_id: str, strategy_data: dict) -> bool:
    """Update a move strategy."""
    try:
        db = get_database()
        
        update_data = {
            'asset': strategy_data['asset'],
            'direction': strategy_data['direction'],
            'lot_size': strategy_data['lot_size'],
            'atm_offset': strategy_data.get('atm_offset', 0),
            'stop_loss_trigger': strategy_data.get('stop_loss_trigger'),
            'stop_loss_limit': strategy_data.get('stop_loss_limit'),
            'target_trigger': strategy_data.get('target_trigger'),
            'target_limit': strategy_data.get('target_limit'),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_strategies.update_one(
            {'_id': ObjectId(strategy_id)},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update move strategy: {e}", exc_info=True)
        return False


async def delete_move_strategy(strategy_id: str) -> bool:
    """Delete a move strategy."""
    try:
        db = get_database()
        
        result = await db.move_strategies.delete_one({'_id': ObjectId(strategy_id)})
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete move strategy: {e}", exc_info=True)
        return False


# Auto execution operations

async def create_move_auto_execution(user_id: int, execution_data: dict) -> Optional[str]:
    """Create a new move auto execution schedule using preset."""
    try:
        db = get_database()
        
        # Get preset to extract API and strategy info
        preset_id = execution_data.get('preset_id')
        if not preset_id:
            logger.error("No preset_id provided in execution_data")
            return None
        
        # Get the preset
        preset = await db.move_trade_presets.find_one({'_id': ObjectId(preset_id)})
        if not preset:
            logger.error(f"Preset not found: {preset_id}")
            return None
        
        execution = {
            'user_id': user_id,
            'preset_id': preset_id,
            'preset_name': preset.get('preset_name', 'Unknown'),
            'api_credential_id': preset.get('api_credential_id'),
            'strategy_id': preset.get('strategy_id'),
            'execution_time': execution_data['execution_time'],
            'enabled': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_auto_executions.insert_one(execution)
        logger.info(f"Created move auto execution: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Failed to create move auto execution: {e}", exc_info=True)
        return None


async def get_move_auto_executions(user_id: int) -> List[dict]:
    """Get all move auto executions for a user."""
    try:
        db = get_database()
        
        cursor = db.move_auto_executions.find({'user_id': user_id})
        executions = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for execution in executions:
            execution['id'] = str(execution['_id'])
            del execution['_id']
        
        return executions
    
    except Exception as e:
        logger.error(f"Failed to get move auto executions: {e}", exc_info=True)
        return []


async def update_move_auto_execution(execution_id: str, execution_data: dict) -> bool:
    """Update a move auto execution schedule."""
    try:
        db = get_database()
        
        # Get preset to extract API and strategy info
        preset_id = execution_data.get('preset_id')
        if not preset_id:
            logger.error("No preset_id provided in execution_data")
            return False
        
        # Get the preset
        preset = await db.move_trade_presets.find_one({'_id': ObjectId(preset_id)})
        if not preset:
            logger.error(f"Preset not found: {preset_id}")
            return False
        
        update_data = {
            'preset_id': preset_id,
            'preset_name': preset.get('preset_name', 'Unknown'),
            'api_credential_id': preset.get('api_credential_id'),
            'strategy_id': preset.get('strategy_id'),
            'execution_time': execution_data['execution_time'],
            'updated_at': datetime.utcnow()
        }
        
        result = await db.move_auto_executions.update_one(
            {'_id': ObjectId(execution_id)},
            {'$set': update_data}
        )
        
        logger.info(f"Updated move auto execution: {execution_id}")
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Failed to update move auto execution: {e}", exc_info=True)
        return False


async def delete_move_auto_execution(execution_id: str) -> bool:
    """Delete a move auto execution."""
    try:
        db = get_database()
        
        result = await db.move_auto_executions.delete_one({'_id': ObjectId(execution_id)})
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete move auto execution: {e}", exc_info=True)
        return False


async def get_enabled_move_auto_executions() -> List[dict]:
    """Get all enabled move auto executions."""
    try:
        db = get_database()
        
        cursor = db.move_auto_executions.find({'enabled': True})
        executions = await cursor.to_list(length=1000)
        
        # Convert ObjectId to string
        for execution in executions:
            execution['id'] = str(execution['_id'])
            del execution['_id']
        
        return executions
    
    except Exception as e:
        logger.error(f"Failed to get enabled move auto executions: {e}", exc_info=True)
        return []
        
