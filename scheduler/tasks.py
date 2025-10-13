"""
Background maintenance tasks.
Periodic tasks for system health, cleanup, and monitoring.
"""

import asyncio
from typing import Optional
from datetime import datetime, timedelta
import pytz

from database.connection import get_database
from delta.market_data import MarketData
from delta.client import DeltaClient
from logger import logger, log_function_call


class BackgroundTasks:
    """Manages periodic background maintenance tasks."""
    
    def __init__(self):
        """Initialize background tasks manager."""
        self.is_running = False
        self.tasks: list[asyncio.Task] = []
        logger.info("[BackgroundTasks.__init__] Background tasks manager initialized")
    
    @log_function_call
    async def start_all_tasks(self):
        """Start all background tasks."""
        if self.is_running:
            logger.warning("[BackgroundTasks.start_all_tasks] Tasks already running")
            return
        
        self.is_running = True
        
        # Start individual task loops
        self.tasks.append(asyncio.create_task(self._position_update_loop()))
        self.tasks.append(asyncio.create_task(self._cleanup_loop()))
        self.tasks.append(asyncio.create_task(self._health_check_loop()))
        
        logger.info("[BackgroundTasks.start_all_tasks] All background tasks started")
    
    @log_function_call
    async def stop_all_tasks(self):
        """Stop all background tasks."""
        if not self.is_running:
            logger.warning("[BackgroundTasks.stop_all_tasks] Tasks not running")
            return
        
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for all to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("[BackgroundTasks.stop_all_tasks] All background tasks stopped")
    
    @log_function_call
    async def _position_update_loop(self):
        """
        Periodic task to update position PnL values.
        Runs every 5 minutes.
        """
        interval = 300  # 5 minutes
        logger.info("[BackgroundTasks._position_update_loop] Position update loop started")
        
        while self.is_running:
            try:
                await self._update_positions_pnl()
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("[BackgroundTasks._position_update_loop] Loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"[BackgroundTasks._position_update_loop] Error: {e}",
                    exc_info=True
                )
                await asyncio.sleep(interval)
    
    @log_function_call
    async def _update_positions_pnl(self):
        """Update PnL for all open positions."""
        try:
            logger.debug("[BackgroundTasks._update_positions_pnl] Updating positions PnL")
            
            # This is a placeholder - actual implementation would:
            # 1. Get all users with open positions
            # 2. Fetch current mark prices
            # 3. Calculate and update unrealized PnL
            # 4. Send alerts if needed
            
            # For now, just log
            logger.debug("[BackgroundTasks._update_positions_pnl] PnL update completed")
            
        except Exception as e:
            logger.error(f"[BackgroundTasks._update_positions_pnl] Error: {e}")
    
    @log_function_call
    async def _cleanup_loop(self):
        """
        Periodic cleanup task.
        Runs daily to clean old logs and data.
        """
        interval = 86400  # 24 hours
        logger.info("[BackgroundTasks._cleanup_loop] Cleanup loop started")
        
        while self.is_running:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("[BackgroundTasks._cleanup_loop] Loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"[BackgroundTasks._cleanup_loop] Error: {e}",
                    exc_info=True
                )
                await asyncio.sleep(interval)
    
    @log_function_call
    async def _cleanup_old_data(self):
        """Clean up old logs and expired data."""
        try:
            logger.info("[BackgroundTasks._cleanup_old_data] Starting cleanup")
            
            db = await get_database()
            
            # Calculate cutoff date (30 days ago)
            cutoff_date = datetime.now(pytz.UTC) - timedelta(days=30)
            
            # Clean old trade history (older than 90 days)
            trade_cutoff = datetime.now(pytz.UTC) - timedelta(days=90)
            result = await db.trade_history.delete_many({
                'created_at': {'$lt': trade_cutoff}
            })
            
            if result.deleted_count > 0:
                logger.info(
                    f"[BackgroundTasks._cleanup_old_data] Deleted {result.deleted_count} "
                    f"old trade records"
                )
            
            # Clean old inactive schedules
            schedule_cutoff = datetime.now(pytz.UTC) - timedelta(days=60)
            result = await db.auto_schedules.delete_many({
                'is_active': False,
                'updated_at': {'$lt': schedule_cutoff}
            })
            
            if result.deleted_count > 0:
                logger.info(
                    f"[BackgroundTasks._cleanup_old_data] Deleted {result.deleted_count} "
                    f"old schedules"
                )
            
            logger.info("[BackgroundTasks._cleanup_old_data] Cleanup completed")
            
        except Exception as e:
            logger.error(f"[BackgroundTasks._cleanup_old_data] Error: {e}")
    
    @log_function_call
    async def _health_check_loop(self):
        """
        Periodic health check task.
        Runs every 15 minutes to check system health.
        """
        interval = 900  # 15 minutes
        logger.info("[BackgroundTasks._health_check_loop] Health check loop started")
        
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("[BackgroundTasks._health_check_loop] Loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"[BackgroundTasks._health_check_loop] Error: {e}",
                    exc_info=True
                )
                await asyncio.sleep(interval)
    
    @log_function_call
    async def _perform_health_check(self):
        """Perform system health checks."""
        try:
            logger.debug("[BackgroundTasks._perform_health_check] Performing health check")
            
            health_status = {
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'database': False,
                'api_connectivity': False,
                'scheduler': self.is_running
            }
            
            # Check database connection
            try:
                from database.connection import db_manager
                db_healthy = await db_manager.health_check()
                health_status['database'] = db_healthy
            except Exception as e:
                logger.warning(f"[BackgroundTasks._perform_health_check] Database check failed: {e}")
            
            # Check API connectivity (optional)
            # This would test Delta Exchange API connectivity
            # For now, skip to avoid unnecessary API calls
            
            # Log health status
            if all([health_status['database'], health_status['scheduler']]):
                logger.info("[BackgroundTasks._perform_health_check] System healthy")
            else:
                logger.warning(
                    f"[BackgroundTasks._perform_health_check] System health issues: "
                    f"{health_status}"
                )
            
        except Exception as e:
            logger.error(f"[BackgroundTasks._perform_health_check] Error: {e}")
    
    @log_function_call
    async def run_manual_cleanup(self):
        """Manually trigger cleanup task."""
        logger.info("[BackgroundTasks.run_manual_cleanup] Running manual cleanup")
        await self._cleanup_old_data()
    
    @log_function_call
    async def run_manual_health_check(self) -> Dict[str, Any]:
        """
        Manually trigger health check.
        
        Returns:
            Health status dictionary
        """
        logger.info("[BackgroundTasks.run_manual_health_check] Running manual health check")
        await self._perform_health_check()
        
        return {
            'status': 'completed',
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }


# Global tasks instance
_tasks_instance: Optional[BackgroundTasks] = None


def get_background_tasks() -> BackgroundTasks:
    """
    Get global background tasks instance.
    
    Returns:
        BackgroundTasks instance
    """
    global _tasks_instance
    if _tasks_instance is None:
        _tasks_instance = BackgroundTasks()
    return _tasks_instance


async def start_background_tasks():
    """Start all background tasks."""
    tasks = get_background_tasks()
    await tasks.start_all_tasks()
    logger.info("[start_background_tasks] Background tasks started")


async def stop_background_tasks():
    """Stop all background tasks."""
    tasks = get_background_tasks()
    await tasks.stop_all_tasks()
    logger.info("[stop_background_tasks] Background tasks stopped")


if __name__ == "__main__":
    import asyncio
    from typing import Dict, Any
    
    async def test_background_tasks():
        """Test background tasks."""
        print("Testing Background Tasks...")
        
        tasks = BackgroundTasks()
        
        try:
            # Start tasks
            await tasks.start_all_tasks()
            print("✅ Background tasks started")
            
            # Let them run for a bit
            await asyncio.sleep(10)
            
            # Run manual health check
            health = await tasks.run_manual_health_check()
            print(f"✅ Health check: {health}")
            
            # Stop tasks
            await tasks.stop_all_tasks()
            print("✅ Background tasks stopped")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n✅ Background tasks test completed!")
    
    asyncio.run(test_background_tasks())
  
