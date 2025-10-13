"""
CRUD operations for auto execution schedules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from database.connection import get_database
from database.models.auto_execution import (
    AutoExecution,
    AutoExecutionCreate,
    AutoExecutionUpdate
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_auto_execution(data: AutoExecutionCreate) -> str:
    """
    Create new auto execution schedule.
    
    Args:
        data: Auto execution creation data
    
    Returns:
        Created schedule ID
    """
    try:
        db = get_database()
        
        # Create schedule document
        schedule = AutoExecution(
            user_id=data.user_id,
            api_id=data.api_id,
            strategy_preset_id=data.strategy_preset_id,
            execution_time=data.execution_time,
            enabled=data.enabled
        )
        
        # Insert to database
        result = await db.auto_executions.insert_one(schedule.to_dict())
        schedule_id = str(result.inserted_id)
        
        logger.info(
            f"Created auto execution: {schedule_id} for user {data.user_id} "
            f"at {data.execution_time}"
        )
        
        return schedule_id
    
    except Exception as e:
        logger.error(f"Failed to create auto execution: {e}", exc_info=True)
        raise


async def get_auto_executions(
    user_id: int,
    include_disabled: bool = False
) -> List[AutoExecution]:
    """
    Get all auto execution schedules for a user.
    
    Args:
        user_id: User ID
        include_disabled: Include disabled schedules
    
    Returns:
        List of auto execution schedules
    """
    try:
        db = get_database()
        
        # Build query
        query = {"user_id": user_id}
        if not include_disabled:
            query["enabled"] = True
        
        # Fetch schedules
        cursor = db.auto_executions.find(query).sort("created_at", -1)
        schedules = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            schedules.append(AutoExecution(**doc))
        
        logger.debug(f"Retrieved {len(schedules)} auto execution(s) for user {user_id}")
        
        return schedules
    
    except Exception as e:
        logger.error(f"Failed to get auto executions: {e}", exc_info=True)
        raise


async def get_enabled_auto_executions() -> List[AutoExecution]:
    """
    Get all enabled auto execution schedules.
    
    Returns:
        List of enabled auto execution schedules
    """
    try:
        db = get_database()
        
        # Fetch all enabled schedules
        cursor = db.auto_executions.find({"enabled": True}).sort("execution_time", 1)
        schedules = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            schedules.append(AutoExecution(**doc))
        
        logger.debug(f"Retrieved {len(schedules)} enabled auto execution(s)")
        
        return schedules
    
    except Exception as e:
        logger.error(f"Failed to get enabled auto executions: {e}", exc_info=True)
        raise


async def get_auto_execution_by_id(schedule_id: str) -> Optional[AutoExecution]:
    """
    Get auto execution schedule by ID.
    
    Args:
        schedule_id: Schedule ID
    
    Returns:
        Auto execution schedule or None if not found
    """
    try:
        db = get_database()
        
        # Fetch schedule
        doc = await db.auto_executions.find_one({"_id": ObjectId(schedule_id)})
        
        if not doc:
            logger.warning(f"Auto execution not found: {schedule_id}")
            return None
        
        doc["_id"] = ObjectId(doc["_id"])
        schedule = AutoExecution(**doc)
        
        logger.debug(f"Retrieved auto execution: {schedule_id}")
        
        return schedule
    
    except Exception as e:
        logger.error(f"Failed to get auto execution by ID: {e}", exc_info=True)
        raise


async def update_auto_execution(
    schedule_id: str,
    update_data: Dict[str, Any]
) -> bool:
    """
    Update auto execution schedule.
    
    Args:
        schedule_id: Schedule ID
        update_data: Data to update
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update document
        result = await db.auto_executions.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated auto execution: {schedule_id}")
            return True
        else:
            logger.warning(f"No changes made to auto execution: {schedule_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to update auto execution: {e}", exc_info=True)
        raise


async def update_execution_status(
    schedule_id: str,
    status: str,
    increment_count: bool = True
) -> bool:
    """
    Update auto execution status after execution.
    
    Args:
        schedule_id: Schedule ID
        status: Execution status
        increment_count: Whether to increment execution count
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db = get_database()
        
        update_data = {
            "last_execution": datetime.now(),
            "last_execution_status": status,
            "updated_at": datetime.now()
        }
        
        # Build update operation
        if increment_count:
            result = await db.auto_executions.update_one(
                {"_id": ObjectId(schedule_id)},
                {
                    "$set": update_data,
                    "$inc": {"execution_count": 1}
                }
            )
        else:
            result = await db.auto_executions.update_one(
                {"_id": ObjectId(schedule_id)},
                {"$set": update_data}
            )
        
        if result.modified_count > 0:
            logger.info(f"Updated execution status for: {schedule_id} - Status: {status}")
            return True
        else:
            logger.warning(f"Failed to update execution status: {schedule_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to update execution status: {e}", exc_info=True)
        raise


async def delete_auto_execution(schedule_id: str) -> bool:
    """
    Delete auto execution schedule.
    
    Args:
        schedule_id: Schedule ID
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Delete document
        result = await db.auto_executions.delete_one({"_id": ObjectId(schedule_id)})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted auto execution: {schedule_id}")
            return True
        else:
            logger.warning(f"Auto execution not found for deletion: {schedule_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to delete auto execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio
    
    async def test():
        from database.connection import connect_db, close_db
        
        await connect_db()
        
        # Test create auto execution
        auto_exec_data = AutoExecutionCreate(
            user_id=12345,
            api_id="507f1f77bcf86cd799439011",
            strategy_preset_id="507f1f77bcf86cd799439012",
            execution_time="09:15",
            enabled=True
        )
        
        try:
            schedule_id = await create_auto_execution(auto_exec_data)
            print(f"Created auto execution: {schedule_id}")
            
            # Get schedule
            schedule = await get_auto_execution_by_id(schedule_id)
            print(f"Retrieved schedule: {schedule.execution_time}")
            
            # Update status
            updated = await update_execution_status(schedule_id, "success")
            print(f"Updated status: {updated}")
            
            # Delete schedule
            deleted = await delete_auto_execution(schedule_id)
            print(f"Deleted schedule: {deleted}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        await close_db()
    
    asyncio.run(test())
      
