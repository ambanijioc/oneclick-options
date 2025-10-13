"""
Background job scheduler for automated strategy execution.
Checks for due schedules and executes them at specified times.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pytz

from database.schedule_operations import ScheduleOperations
from database.api_operations import APIOperations
from strategies.execution import StrategyExecutor
from delta.client import DeltaClient
from logger import logger, log_function_call
from utils.error_handler import format_error_for_user


class SchedulerManager:
    """Manages scheduled strategy executions."""
    
    def __init__(self):
        """Initialize scheduler manager."""
        self.schedule_ops = ScheduleOperations()
        self.api_ops = APIOperations()
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.check_interval = 60  # Check every 60 seconds
        logger.info("[SchedulerManager.__init__] Scheduler manager initialized")
    
    @log_function_call
    async def start(self):
        """Start the scheduler loop."""
        if self.is_running:
            logger.warning("[SchedulerManager.start] Scheduler already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("[SchedulerManager.start] Scheduler started")
    
    @log_function_call
    async def stop(self):
        """Stop the scheduler loop."""
        if not self.is_running:
            logger.warning("[SchedulerManager.stop] Scheduler not running")
            return
        
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("[SchedulerManager.stop] Scheduler stopped")
    
    @log_function_call
    async def _scheduler_loop(self):
        """Main scheduler loop that checks for due executions."""
        logger.info("[SchedulerManager._scheduler_loop] Scheduler loop started")
        
        while self.is_running:
            try:
                # Check for due schedules
                await self._check_and_execute_schedules()
                
                # Sleep until next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("[SchedulerManager._scheduler_loop] Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"[SchedulerManager._scheduler_loop] Error in scheduler loop: {e}",
                    exc_info=True
                )
                # Continue running despite errors
                await asyncio.sleep(self.check_interval)
        
        logger.info("[SchedulerManager._scheduler_loop] Scheduler loop ended")
    
    @log_function_call
    async def _check_and_execute_schedules(self):
        """Check for schedules due for execution and execute them."""
        try:
            # Get schedules due for execution
            due_schedules = await self.schedule_ops.get_due_schedules()
            
            if not due_schedules:
                logger.debug("[SchedulerManager._check_and_execute_schedules] No due schedules")
                return
            
            logger.info(
                f"[SchedulerManager._check_and_execute_schedules] Found {len(due_schedules)} "
                f"due schedules"
            )
            
            # Execute each schedule
            for schedule in due_schedules:
                try:
                    await self._execute_scheduled_trade(schedule)
                except Exception as e:
                    logger.error(
                        f"[SchedulerManager._check_and_execute_schedules] "
                        f"Error executing schedule {schedule.get('_id')}: {e}"
                    )
                    # Continue with other schedules
            
        except Exception as e:
            logger.error(
                f"[SchedulerManager._check_and_execute_schedules] Error checking schedules: {e}"
            )
    
    @log_function_call
    async def _execute_scheduled_trade(self, schedule: Dict[str, Any]):
        """
        Execute a scheduled trade.
        
        Args:
            schedule: Schedule document
        """
        try:
            schedule_id = schedule.get('_id')
            user_id = schedule.get('user_id')
            api_name = schedule.get('api_name')
            strategy_type = schedule.get('strategy_type')
            strategy_name = schedule.get('strategy_name')
            schedule_name = schedule.get('schedule_name')
            
            logger.info(
                f"[SchedulerManager._execute_scheduled_trade] Executing scheduled trade: "
                f"Schedule='{schedule_name}', User={user_id}, API='{api_name}', "
                f"Strategy='{strategy_name}'"
            )
            
            # Get API credentials
            api_creds = await self.api_ops.get_api_by_name(
                user_id=user_id,
                api_name=api_name,
                include_secret=True
            )
            
            if not api_creds:
                raise ValueError(f"API credentials '{api_name}' not found for user {user_id}")
            
            # Create Delta client
            client = DeltaClient(
                api_key=api_creds.get('api_key'),
                api_secret=api_creds.get('api_secret')
            )
            
            try:
                # Execute strategy
                executor = StrategyExecutor(client)
                
                result = await executor.execute_strategy_from_preset(
                    user_id=user_id,
                    api_name=api_name,
                    strategy_type=strategy_type,
                    strategy_name=strategy_name
                )
                
                if result.get('success'):
                    logger.info(
                        f"[SchedulerManager._execute_scheduled_trade] Successfully executed "
                        f"scheduled trade for schedule '{schedule_name}'"
                    )
                    
                    # Send success notification (optional - implement telegram notification)
                    await self._send_execution_notification(
                        user_id=user_id,
                        schedule_name=schedule_name,
                        result=result,
                        success=True
                    )
                else:
                    error_message = result.get('error', 'Unknown error')
                    logger.error(
                        f"[SchedulerManager._execute_scheduled_trade] Failed to execute "
                        f"scheduled trade: {error_message}"
                    )
                    
                    # Send error notification
                    await self._send_execution_notification(
                        user_id=user_id,
                        schedule_name=schedule_name,
                        result=result,
                        success=False
                    )
                
            finally:
                await client.close()
            
            # Mark schedule as executed and calculate next execution
            await self.schedule_ops.mark_executed(schedule_id)
            
            logger.info(
                f"[SchedulerManager._execute_scheduled_trade] Schedule '{schedule_name}' "
                f"marked as executed"
            )
            
        except Exception as e:
            logger.error(
                f"[SchedulerManager._execute_scheduled_trade] Error executing scheduled trade: {e}",
                exc_info=True
            )
            
            # Send error notification
            await self._send_execution_notification(
                user_id=schedule.get('user_id'),
                schedule_name=schedule.get('schedule_name'),
                result={'error': str(e)},
                success=False
            )
    
    @log_function_call
    async def _send_execution_notification(
        self,
        user_id: int,
        schedule_name: str,
        result: Dict[str, Any],
        success: bool
    ):
        """
        Send execution notification to user.
        
        Args:
            user_id: User ID
            schedule_name: Schedule name
            result: Execution result
            success: Whether execution was successful
        """
        try:
            # This will be implemented in the Telegram handlers section
            # For now, just log
            if success:
                logger.info(
                    f"[SchedulerManager._send_execution_notification] "
                    f"Schedule '{schedule_name}' executed successfully for user {user_id}"
                )
            else:
                logger.warning(
                    f"[SchedulerManager._send_execution_notification] "
                    f"Schedule '{schedule_name}' execution failed for user {user_id}: "
                    f"{result.get('error')}"
                )
            
            # TODO: Implement actual Telegram notification
            # from telegram.bot import send_message
            # await send_message(user_id, notification_message)
            
        except Exception as e:
            logger.error(
                f"[SchedulerManager._send_execution_notification] "
                f"Error sending notification: {e}"
            )
    
    @log_function_call
    async def add_schedule(
        self,
        user_id: int,
        schedule_name: str,
        api_name: str,
        strategy_type: str,
        strategy_name: str,
        execution_time: str
    ) -> Dict[str, Any]:
        """
        Add a new schedule.
        
        Args:
            user_id: User ID
            schedule_name: Schedule name
            api_name: API to use
            strategy_type: Strategy type
            strategy_name: Strategy name
            execution_time: Execution time (HH:MM AM/PM)
        
        Returns:
            Creation result
        """
        try:
            result = await self.schedule_ops.create_schedule(
                user_id=user_id,
                schedule_name=schedule_name,
                api_name=api_name,
                strategy_type=strategy_type,
                strategy_name=strategy_name,
                execution_time=execution_time
            )
            
            if result.get('success'):
                logger.info(
                    f"[SchedulerManager.add_schedule] Schedule '{schedule_name}' "
                    f"added for user {user_id}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"[SchedulerManager.add_schedule] Error adding schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    @log_function_call
    async def get_user_schedules(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all schedules for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of schedules
        """
        try:
            schedules = await self.schedule_ops.get_active_schedules(user_id)
            
            logger.info(
                f"[SchedulerManager.get_user_schedules] Retrieved {len(schedules)} "
                f"schedules for user {user_id}"
            )
            
            return schedules
            
        except Exception as e:
            logger.error(f"[SchedulerManager.get_user_schedules] Error: {e}")
            return []
    
    @log_function_call
    async def remove_schedule(self, user_id: int, schedule_name: str) -> Dict[str, Any]:
        """
        Remove a schedule.
        
        Args:
            user_id: User ID
            schedule_name: Schedule name
        
        Returns:
            Deletion result
        """
        try:
            result = await self.schedule_ops.delete_schedule(user_id, schedule_name)
            
            if result.get('success'):
                logger.info(
                    f"[SchedulerManager.remove_schedule] Schedule '{schedule_name}' "
                    f"removed for user {user_id}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"[SchedulerManager.remove_schedule] Error: {e}")
            return {'success': False, 'error': str(e)}


# Global scheduler instance
_scheduler_instance: Optional[SchedulerManager] = None


def get_scheduler() -> SchedulerManager:
    """
    Get global scheduler instance.
    
    Returns:
        SchedulerManager instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerManager()
    return _scheduler_instance


async def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()
    logger.info("[start_scheduler] Global scheduler started")


async def stop_scheduler():
    """Stop the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
    logger.info("[stop_scheduler] Global scheduler stopped")


if __name__ == "__main__":
    import asyncio
    
    async def test_scheduler():
        """Test scheduler functionality."""
        print("Testing Scheduler...")
        
        scheduler = SchedulerManager()
        
        try:
            # Start scheduler
            await scheduler.start()
            print("✅ Scheduler started")
            
            # Let it run for a few seconds
            await asyncio.sleep(5)
            
            # Stop scheduler
            await scheduler.stop()
            print("✅ Scheduler stopped")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n✅ Scheduler test completed!")
    
    asyncio.run(test_scheduler())
      
