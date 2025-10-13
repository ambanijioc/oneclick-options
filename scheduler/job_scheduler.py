"""
APScheduler configuration and management.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime
import pytz

from bot.utils.logger import setup_logger, log_to_telegram
from database.operations.auto_execution_ops import get_enabled_auto_executions
from .auto_trade_jobs import execute_auto_trade

logger = setup_logger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler = None


async def init_scheduler(bot_application):
    """
    Initialize APScheduler and load all enabled auto executions.
    
    Args:
        bot_application: Bot application instance
    """
    global _scheduler
    
    try:
        logger.info("Initializing job scheduler...")
        
        # Configure job stores
        jobstores = {
            'default': MemoryJobStore()
        }
        
        # Configure scheduler
        _scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone=pytz.timezone('Asia/Kolkata')
        )
        
        # Start scheduler
        _scheduler.start()
        logger.info("✓ Scheduler started")
        
        # Load all enabled auto executions
        await load_auto_executions(bot_application)
        
        logger.info("✓ Job scheduler initialized successfully")
        
        await log_to_telegram(
            message="Job scheduler initialized and started",
            level="INFO",
            module="scheduler.job_scheduler"
        )
    
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
        await log_to_telegram(
            message=f"Failed to initialize scheduler: {str(e)}",
            level="ERROR",
            module="scheduler.job_scheduler"
        )
        raise


async def shutdown_scheduler():
    """
    Shutdown the scheduler gracefully.
    """
    global _scheduler
    
    if _scheduler:
        logger.info("Shutting down scheduler...")
        _scheduler.shutdown(wait=True)
        logger.info("✓ Scheduler shutdown complete")


async def load_auto_executions(bot_application):
    """
    Load all enabled auto executions and schedule jobs.
    
    Args:
        bot_application: Bot application instance
    """
    try:
        # Get all enabled auto executions
        auto_execs = await get_enabled_auto_executions()
        
        logger.info(f"Loading {len(auto_execs)} enabled auto execution(s)...")
        
        for auto_exec in auto_execs:
            try:
                await add_auto_execution_job(auto_exec, bot_application)
            except Exception as e:
                logger.error(
                    f"Failed to add job for auto execution {auto_exec.id}: {e}",
                    exc_info=True
                )
        
        logger.info(f"✓ Loaded {len(auto_execs)} auto execution job(s)")
    
    except Exception as e:
        logger.error(f"Failed to load auto executions: {e}", exc_info=True)


async def add_auto_execution_job(auto_exec, bot_application):
    """
    Add a scheduled job for an auto execution.
    
    Args:
        auto_exec: AutoExecution instance
        bot_application: Bot application instance
    """
    try:
        # Parse execution time (format: HH:MM)
        hour, minute = map(int, auto_exec.execution_time.split(':'))
        
        # Create job ID
        job_id = f"auto_exec_{auto_exec.id}"
        
        # Create cron trigger (runs daily at specified time)
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=pytz.timezone('Asia/Kolkata')
        )
        
        # Add job to scheduler
        _scheduler.add_job(
            func=execute_auto_trade,
            trigger=trigger,
            id=job_id,
            args=[str(auto_exec.id), bot_application],
            replace_existing=True,
            misfire_grace_time=300  # 5 minutes grace time
        )
        
        logger.info(
            f"Added auto execution job: {job_id} at {auto_exec.execution_time} IST"
        )
    
    except Exception as e:
        logger.error(f"Failed to add auto execution job: {e}", exc_info=True)
        raise


async def remove_auto_execution_job(auto_exec_id: str):
    """
    Remove a scheduled job for an auto execution.
    
    Args:
        auto_exec_id: Auto execution ID
    """
    try:
        job_id = f"auto_exec_{auto_exec_id}"
        
        # Remove job from scheduler
        if _scheduler.get_job(job_id):
            _scheduler.remove_job(job_id)
            logger.info(f"Removed auto execution job: {job_id}")
        else:
            logger.warning(f"Job not found: {job_id}")
    
    except Exception as e:
        logger.error(f"Failed to remove auto execution job: {e}", exc_info=True)


def get_scheduled_jobs():
    """
    Get list of all scheduled jobs.
    
    Returns:
        List of scheduled jobs
    """
    if _scheduler:
        return _scheduler.get_jobs()
    return []


if __name__ == "__main__":
    import asyncio
    
    async def test():
        await init_scheduler(None)
        
        jobs = get_scheduled_jobs()
        print(f"Scheduled jobs: {len(jobs)}")
        
        await shutdown_scheduler()
    
    asyncio.run(test())
