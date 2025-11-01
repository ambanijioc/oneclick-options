"""
Database operations for MOVE options auto-execution schedules.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# ✅ CORRECT - Get database connection when needed
def get_collections():
    """Get database collections (called when needed, not at import)."""
    db = get_database()
    return db['move_auto_executions'], db['move_trade_presets']

async def create_move_auto_execution(
    user_id: int,
    preset_id: str,
    preset_name: str,
    execution_time: str
) -> Optional[str]:
    """
    Create a new MOVE auto-execution schedule.
    
    Args:
        user_id: User ID
        preset_id: Move trade preset ID
        preset_name: Preset name (for display)
        execution_time: Execution time (format: "HH:MM AM/PM IST")
    
    Returns:
        Schedule ID if successful, None otherwise
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        schedule = {
            'user_id': user_id,
            'preset_id': preset_id,
            'preset_name': preset_name,
            'execution_time': execution_time,
            'enabled': True,
            'last_executed': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await auto_execution_collection.insert_one(schedule)
        
        logger.info(f"Created MOVE auto-execution schedule: {result.inserted_id}")
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Error creating auto-execution schedule: {e}", exc_info=True)
        return None


async def get_move_auto_executions(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all MOVE auto-execution schedules for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        List of schedule documents
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        schedules = await auto_execution_collection.find({
            'user_id': user_id
        }).sort('created_at', -1).to_list(length=None)
        
        # Convert ObjectId to string
        for schedule in schedules:
            schedule['_id'] = str(schedule['_id'])
        
        return schedules
    
    except Exception as e:
        logger.error(f"Error getting auto-execution schedules: {e}", exc_info=True)
        return []


async def get_move_auto_execution_by_id(schedule_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific MOVE auto-execution schedule by ID.
    
    Args:
        schedule_id: Schedule ID
    
    Returns:
        Schedule document or None
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        schedule = await auto_execution_collection.find_one({
            '_id': ObjectId(schedule_id)
        })
        
        if schedule:
            schedule['_id'] = str(schedule['_id'])
        
        return schedule
    
    except Exception as e:
        logger.error(f"Error getting auto-execution schedule: {e}", exc_info=True)
        return None


async def get_all_active_move_schedules() -> List[Dict[str, Any]]:
    """
    Get all active MOVE auto-execution schedules across all users.
    Used by scheduler to find trades to execute.
    
    Returns:
        List of active schedule documents
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        schedules = await auto_execution_collection.find({
            'enabled': True
        }).to_list(length=None)
        
        # Convert ObjectId to string
        for schedule in schedules:
            schedule['_id'] = str(schedule['_id'])
        
        logger.debug(f"Found {len(schedules)} active schedules")
        return schedules
    
    except Exception as e:
        logger.error(f"Error getting active schedules: {e}", exc_info=True)
        return []


async def update_move_schedule_last_execution(
    schedule_id: str,
    execution_time: datetime
) -> bool:
    """
    Update last execution time for a schedule.
    
    Args:
        schedule_id: Schedule ID
        execution_time: Execution timestamp
    
    Returns:
        True if successful, False otherwise
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        result = await auto_execution_collection.update_one(
            {'_id': ObjectId(schedule_id)},
            {
                '$set': {
                    'last_executed': execution_time,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated last execution for schedule {schedule_id}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error updating schedule execution: {e}", exc_info=True)
        return False


async def toggle_move_schedule_status(
    schedule_id: str,
    enabled: bool
) -> bool:
    """
    Enable or disable a MOVE auto-execution schedule.
    
    Args:
        schedule_id: Schedule ID
        enabled: True to enable, False to disable
    
    Returns:
        True if successful, False otherwise
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        result = await auto_execution_collection.update_one(
            {'_id': ObjectId(schedule_id)},
            {
                '$set': {
                    'enabled': enabled,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            status = "enabled" if enabled else "disabled"
            logger.info(f"Schedule {schedule_id} {status}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error toggling schedule status: {e}", exc_info=True)
        return False


async def delete_move_schedule(schedule_id: str) -> bool:
    """
    Delete a MOVE auto-execution schedule.
    
    Args:
        schedule_id: Schedule ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        result = await auto_execution_collection.delete_one({
            '_id': ObjectId(schedule_id)
        })
        
        if result.deleted_count > 0:
            logger.info(f"Deleted schedule {schedule_id}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}", exc_info=True)
        return False


async def update_move_schedule_time(
    schedule_id: str,
    new_time: str
) -> bool:
    """
    Update execution time for a schedule.
    
    Args:
        schedule_id: Schedule ID
        new_time: New execution time (format: "HH:MM AM/PM IST")
    
    Returns:
        True if successful, False otherwise
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        result = await auto_execution_collection.update_one(
            {'_id': ObjectId(schedule_id)},
            {
                '$set': {
                    'execution_time': new_time,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated schedule {schedule_id} time to {new_time}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error updating schedule time: {e}", exc_info=True)
        return False


async def get_schedules_count(user_id: int) -> int:
    """
    Get count of schedules for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Number of schedules
    """
    try:
        auto_execution_collection, _ = get_collections()  # ✅ Get collection here
        
        count = await auto_execution_collection.count_documents({
            'user_id': user_id
        })
        
        return count
    
    except Exception as e:
        logger.error(f"Error getting schedules count: {e}", exc_info=True)
        return 0
      
