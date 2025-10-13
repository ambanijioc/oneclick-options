"""
CRUD operations for auto-execution schedules.
Handles scheduling automated strategy executions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pytz
import re

from database.connection import get_database
from database.models import AutoExecutionSchedule
from logger import logger, log_function_call


class ScheduleOperations:
    """Auto-execution schedule database operations."""
    
    def __init__(self):
        """Initialize schedule operations."""
        self.collection_name = "auto_schedules"
    
    @log_function_call
    async def create_schedule(
        self,
        user_id: int,
        schedule_name: str,
        api_name: str,
        strategy_type: str,
        strategy_name: str,
        execution_time: str
    ) -> Dict[str, Any]:
        """
        Create a new auto-execution schedule.
        
        Args:
            user_id: Telegram user ID
            schedule_name: Name for the schedule
            api_name: API to use for execution
            strategy_type: Type of strategy (straddle/strangle)
            strategy_name: Strategy preset name
            execution_time: Execution time (HH:MM AM/PM)
        
        Returns:
            Dictionary with success status and schedule ID
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Check if schedule name already exists
            existing = await collection.find_one({
                "user_id": user_id,
                "schedule_name": schedule_name,
                "is_active": True
            })
            
            if existing:
                logger.warning(
                    f"[ScheduleOperations.create_schedule] Schedule '{schedule_name}' "
                    f"already exists for user {user_id}"
                )
                return {
                    "success": False,
                    "error": f"Schedule name '{schedule_name}' already exists"
                }
            
            # Calculate next execution time
            next_execution = self._calculate_next_execution(execution_time)
            
            # Create schedule document
            schedule = AutoExecutionSchedule(
                user_id=user_id,
                schedule_name=schedule_name,
                api_name=api_name,
                strategy_type=strategy_type,
                strategy_name=strategy_name,
                execution_time=execution_time,
                next_execution=next_execution
            )
            
            # Insert into database
            result = await collection.insert_one(schedule.model_dump())
            
            logger.info(
                f"[ScheduleOperations.create_schedule] Schedule '{schedule_name}' created "
                f"for user {user_id}, ID: {result.inserted_id}, Next: {next_execution}"
            )
            
            return {
                "success": True,
                "schedule_id": str(result.inserted_id),
                "schedule_name": schedule_name,
                "next_execution": next_execution
            }
            
        except Exception as e:
            logger.error(f"[ScheduleOperations.create_schedule] Error creating schedule: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_next_execution(self, execution_time: str) -> datetime:
        """
        Calculate next execution datetime from time string.
        
        Args:
            execution_time: Time in format "HH:MM AM/PM"
        
        Returns:
            Next execution datetime in UTC
        """
        try:
            # Parse time
            match = re.match(r'(\d{1,2}):(\d{2})\s?(AM|PM)', execution_time, re.IGNORECASE)
            if not match:
                raise ValueError(f"Invalid time format: {execution_time}")
            
            hour = int(match.group(1))
            minute = int(match.group(2))
            meridiem = match.group(3).upper()
            
            # Convert to 24-hour format
            if meridiem == 'PM' and hour != 12:
                hour += 12
            elif meridiem == 'AM' and hour == 12:
                hour = 0
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            
            # Create execution datetime for today
            execution_dt = now_ist.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
            # If time has passed today, schedule for tomorrow
            if execution_dt <= now_ist:
                execution_dt += timedelta(days=1)
            
            # Convert to UTC
            execution_utc = execution_dt.astimezone(pytz.UTC)
            
            return execution_utc
            
        except Exception as e:
            logger.error(
                f"[ScheduleOperations._calculate_next_execution] Error calculating time: {e}"
            )
            # Default to 1 hour from now
            return datetime.now(pytz.UTC) + timedelta(hours=1)
    
    @log_function_call
    async def get_active_schedules(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all active schedules.
        
        Args:
            user_id: Optional user ID filter
        
        Returns:
            List of active schedule documents
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            query = {"is_active": True}
            if user_id:
                query["user_id"] = user_id
            
            cursor = collection.find(query).sort("next_execution", 1)
            
            schedules = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                schedules.append(doc)
            
            logger.info(
                f"[ScheduleOperations.get_active_schedules] Retrieved {len(schedules)} "
                f"active schedules"
            )
            
            return schedules
            
        except Exception as e:
            logger.error(
                f"[ScheduleOperations.get_active_schedules] Error retrieving schedules: {e}"
            )
            return []
    
    @log_function_call
    async def get_due_schedules(self) -> List[Dict[str, Any]]:
        """
        Get schedules that are due for execution.
        
        Returns:
            List of due schedule documents
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            now = datetime.now(pytz.UTC)
            
            cursor = collection.find({
                "is_active": True,
                "next_execution": {"$lte": now}
            })
            
            schedules = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                schedules.append(doc)
            
            logger.info(
                f"[ScheduleOperations.get_due_schedules] Found {len(schedules)} "
                f"due schedules"
            )
            
            return schedules
            
        except Exception as e:
            logger.error(
                f"[ScheduleOperations.get_due_schedules] Error retrieving due schedules: {e}"
            )
            return []
    
    @log_function_call
    async def mark_executed(self, schedule_id: str) -> Dict[str, Any]:
        """
        Mark schedule as executed and calculate next execution time.
        
        Args:
            schedule_id: Schedule document ID
        
        Returns:
            Dictionary with success status
        """
        try:
            from bson import ObjectId
            
            db = await get_database()
            collection = db[self.collection_name]
            
            # Get current schedule
            schedule = await collection.find_one({"_id": ObjectId(schedule_id)})
            
            if not schedule:
                return {"success": False, "error": "Schedule not found"}
            
            # Calculate next execution
            next_execution = self._calculate_next_execution(schedule['execution_time'])
            
            # Update schedule
            result = await collection.update_one(
                {"_id": ObjectId(schedule_id)},
                {"$set": {
                    "last_executed": datetime.now(pytz.UTC),
                    "next_execution": next_execution,
                    "execution_count": schedule.get('execution_count', 0) + 1,
                    "updated_at": datetime.now(pytz.UTC)
                }}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[ScheduleOperations.mark_executed] Schedule {schedule_id} marked "
                    f"as executed, Next: {next_execution}"
                )
                return {"success": True, "next_execution": next_execution}
            else:
                return {"success": False, "error": "Update failed"}
            
        except Exception as e:
            logger.error(f"[ScheduleOperations.mark_executed] Error updating schedule: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def update_schedule(
        self,
        user_id: int,
        schedule_name: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update existing schedule.
        
        Args:
            user_id: Telegram user ID
            schedule_name: Schedule name to update
            update_data: Dictionary of fields to update
        
        Returns:
            Dictionary with success status
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Get existing schedule
            existing = await collection.find_one({
                "user_id": user_id,
                "schedule_name": schedule_name,
                "is_active": True
            })
            
            if not existing:
                return {"success": False, "error": f"Schedule '{schedule_name}' not found"}
            
            # Recalculate next execution if time changed
            if "execution_time" in update_data:
                update_data["next_execution"] = self._calculate_next_execution(
                    update_data["execution_time"]
                )
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.now(pytz.UTC)
            
            # Update document
            result = await collection.update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[ScheduleOperations.update_schedule] Schedule '{schedule_name}' "
                    f"updated for user {user_id}"
                )
                return {"success": True}
            else:
                return {"success": True, "modified": False}
            
        except Exception as e:
            logger.error(f"[ScheduleOperations.update_schedule] Error updating schedule: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def delete_schedule(self, user_id: int, schedule_name: str) -> Dict[str, Any]:
        """
        Delete schedule (soft delete by marking inactive).
        
        Args:
            user_id: Telegram user ID
            schedule_name: Schedule name to delete
        
        Returns:
            Dictionary with success status
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            result = await collection.update_one(
                {"user_id": user_id, "schedule_name": schedule_name, "is_active": True},
                {"$set": {
                    "is_active": False,
                    "updated_at": datetime.now(pytz.UTC)
                }}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[ScheduleOperations.delete_schedule] Schedule '{schedule_name}' "
                    f"deleted for user {user_id}"
                )
                return {"success": True}
            else:
                logger.warning(
                    f"[ScheduleOperations.delete_schedule] Schedule '{schedule_name}' "
                    f"not found for user {user_id}"
                )
                return {"success": False, "error": "Schedule not found"}
            
        except Exception as e:
            logger.error(f"[ScheduleOperations.delete_schedule] Error deleting schedule: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    
    async def test_schedule_operations():
        """Test schedule operations."""
        print("Testing Schedule Operations...")
        
        schedule_ops = ScheduleOperations()
        test_user_id = 123456789
        
        # Test create schedule
        result = await schedule_ops.create_schedule(
            user_id=test_user_id,
            schedule_name="Morning Trade",
            api_name="Test API",
            strategy_type="straddle",
            strategy_name="Test Strategy",
            execution_time="09:30 AM"
        )
        print(f"✅ Create Schedule: {result}")
        
        # Test get active schedules
        schedules = await schedule_ops.get_active_schedules(test_user_id)
        print(f"✅ Get Active Schedules: {len(schedules)} found")
        
        # Test get due schedules
        due_schedules = await schedule_ops.get_due_schedules()
        print(f"✅ Get Due Schedules: {len(due_schedules)} found")
        
        print("\n✅ Schedule operations test completed!")
    
    asyncio.run(test_schedule_operations())
  
