"""
Main application entry point.
Initializes FastAPI app, sets up webhook, and starts the server.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application

from config import settings
from bot.application import create_application
from database.connection import connect_db, close_db
from scheduler.job_scheduler import init_scheduler, shutdown_scheduler
from bot.utils.logger import setup_logger, log_to_telegram
from bot.scheduler.algo_scheduler import start_algo_scheduler  # NEW - Algo scheduler

# Setup logging
logger = setup_logger(__name__)


# Global bot application instance
bot_app: Application = None

# Global scheduler task
algo_scheduler_task = None  # NEW


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    global bot_app, algo_scheduler_task
    
    # Startup
    logger.info("=" * 50)
    logger.info("Starting Telegram Trading Bot...")
    logger.info("=" * 50)
    
    try:
        # Connect to database
        logger.info("Connecting to MongoDB...")
        await connect_db()
        logger.info("✓ MongoDB connected successfully")
        
        # Initialize bot application
        logger.info("Initializing bot application...")
        bot_app = await create_application()
        await bot_app.initialize()
        logger.info("✓ Bot application initialized")

        # Start state manager cleanup task
        logger.info("Starting state manager...")
        from bot.utils.state_manager import state_manager
        await state_manager.start_cleanup_task()
        logger.info("✓ State manager started")
        
        # Delete existing webhook
        logger.info("Deleting existing webhook...")
        await bot_app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✓ Existing webhook deleted")
        
        # Set new webhook
        webhook_url = settings.get_webhook_endpoint()
        logger.info(f"Setting webhook: {webhook_url}")
        await bot_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False
        )
        
        # Verify webhook
        webhook_info = await bot_app.bot.get_webhook_info()
        if webhook_info.url == webhook_url:
            logger.info(f"✓ Webhook set successfully: {webhook_info.url}")
            logger.info(f"  Pending updates: {webhook_info.pending_update_count}")
        else:
            logger.error(f"✗ Webhook verification failed. Expected: {webhook_url}, Got: {webhook_info.url}")
            asyncio.create_task(log_to_telegram(f"🔴 CRITICAL: Webhook verification failed!"))
        
        # Initialize scheduler (existing job scheduler)
        logger.info("Initializing job scheduler...")
        await init_scheduler(bot_app)
        logger.info("✓ Job scheduler initialized")
        
        # NEW - Start algo scheduler in background
        logger.info("Starting algo scheduler...")
        algo_scheduler_task = asyncio.create_task(start_algo_scheduler(bot_app))
        logger.info("✓ Algo scheduler started in background")
        
        logger.info("=" * 50)
        logger.info("Bot started successfully! Ready to receive updates.")
        logger.info("=" * 50)
        asyncio.create_task(log_to_telegram(
            f"🟢 Bot started successfully!\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n"
            f"Webhook: {webhook_url}\n"
            f"Algo Scheduler: Active"
        ))
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        asyncio.create_task(log_to_telegram(f"🔴 CRITICAL: Failed to start bot!\nError: {str(e)}"))
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info("Shutting down bot...")
    logger.info("=" * 50)
    
    try:
        # NEW - Stop algo scheduler
        if algo_scheduler_task:
            logger.info("Stopping algo scheduler...")
            algo_scheduler_task.cancel()
            try:
                await algo_scheduler_task
            except asyncio.CancelledError:
                pass
            logger.info("✓ Algo scheduler stopped")
        
        # Stop state manager cleanup task
        logger.info("Stopping state manager...")
        from bot.utils.state_manager import state_manager
        await state_manager.stop_cleanup_task()
        logger.info("✓ State manager stopped")
        
        # Shutdown scheduler
        logger.info("Shutting down scheduler...")
        await shutdown_scheduler()
        logger.info("✓ Scheduler shutdown complete")
        
        # Shutdown bot
        if bot_app:
            logger.info("Shutting down bot application...")
            await bot_app.shutdown()
            logger.info("✓ Bot shutdown complete")
        
        # Close database connection
        logger.info("Closing database connection...")
        await close_db()
        logger.info("✓ Database connection closed")
        
        logger.info("=" * 50)
        logger.info("Bot shutdown complete")
        logger.info("=" * 50)
        asyncio.create_task(log_to_telegram(
            f"🔴 Bot shutting down\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
        ))
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="Telegram Trading Bot",
    description="Options trading bot with Delta Exchange India API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint - basic info."""
    return {
        "status": "running",
        "service": "Telegram Trading Bot",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for UptimeRobot monitoring.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "telegram_trading_bot"
    }


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Webhook endpoint to receive Telegram updates.
    """
    try:
        # Parse incoming update
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)
        
        # Log incoming update
        update_id = update.update_id if update else "unknown"
        logger.debug(f"Received update: {update_id}")
        
        # Process update asynchronously
        if update:
            await bot_app.process_update(update)  # ✅ AWAIT - Sequential processing
        
        # Return 200 OK immediately
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        # Still return 200 to prevent Telegram from retrying
        return Response(status_code=200)


@app.get("/webhook/info")
async def webhook_info():
    """
    Get current webhook information (for debugging).
    """
    try:
        if bot_app:
            webhook_info = await bot_app.bot.get_webhook_info()
            return {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date,
                "last_error_message": webhook_info.last_error_message,
                "max_connections": webhook_info.max_connections,
                "allowed_updates": webhook_info.allowed_updates
            }
        else:
            return {"error": "Bot not initialized"}
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        return {"error": str(e)}


# NEW - Algo scheduler status endpoint
@app.get("/algo/status")
async def algo_status():
    """Get algo scheduler status."""
    try:
        from database.operations.algo_setup_ops import get_all_active_algo_setups
        
        setups = await get_all_active_algo_setups()
        
        return {
            "status": "running" if algo_scheduler_task and not algo_scheduler_task.done() else "stopped",
            "active_setups": len(setups),
            "setups": [
                {
                    "user_id": s['user_id'],
                    "execution_time": s['execution_time'],
                    "last_execution": s.get('last_execution'),
                    "last_status": s.get('last_execution_status')
                }
                for s in setups
            ]
        }
    except Exception as e:
        logger.error(f"Error getting algo status: {e}", exc_info=True)
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
    
