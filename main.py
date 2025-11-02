"""
Main application entry point.
Initializes FastAPI app, sets up webhook, and starts the server.

FIXES APPLIED:
- ✅ Global move_scheduler properly managed
- ✅ Lifespan globals correctly declared
- ✅ Proper async/await for logging (no fire-and-forget tasks)
- ✅ Safe error handling in shutdown
"""

import asyncio
import logging
import os
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
from bot.utils.keepalive import start_keepalive, stop_keepalive
from bot.scheduler.algo_scheduler import start_algo_scheduler
from bot.scheduler.move_scheduler import get_move_scheduler

# Setup logging
logger = setup_logger(__name__)


# ============= GLOBALS AT MODULE LEVEL =============
bot_app: Application = None
algo_scheduler_task = None
move_scheduler = None  # ✅ NEW - Global move scheduler instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Manages:
    - Database connection
    - Bot application initialization
    - Scheduler tasks (algo, move, job)
    - Keep-alive service
    - Clean shutdown
    """
    global bot_app, algo_scheduler_task, move_scheduler  # ✅ DECLARE ALL GLOBALS
    
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
            try:
                await log_to_telegram(f"🔴 CRITICAL: Webhook verification failed!")
            except Exception as e:
                logger.warning(f"Failed to send webhook error log: {e}")
        
        # Initialize job scheduler (existing scheduler)
        logger.info("Initializing job scheduler...")
        await init_scheduler(bot_app)
        logger.info("✓ Job scheduler initialized")
        
        # ✅ Start algo scheduler in background
        logger.info("Starting algo scheduler...")
        algo_scheduler_task = asyncio.create_task(start_algo_scheduler(bot_app))
        logger.info("✓ Algo scheduler started in background")

        # ✅ Start MOVE auto-trade scheduler (STORE AS GLOBAL)
        logger.info("Starting MOVE auto-trade scheduler...")
        move_scheduler = get_move_scheduler(bot_app)
        await move_scheduler.start()
        logger.info("✓ MOVE scheduler started")
        
        # ✅ Start keep-alive service
        BASE_URL = os.getenv(
            'RENDER_EXTERNAL_URL', 
            'https://oneclick-options.onrender.com'
        )
        logger.info(f"Starting keep-alive service for {BASE_URL}...")
        start_keepalive(BASE_URL)
        logger.info("✓ Keep-alive service started")
        
        logger.info("=" * 50)
        logger.info("Bot started successfully! Ready to receive updates.")
        logger.info("=" * 50)
        
        # ✅ Await startup notification (no fire-and-forget)
        try:
            await log_to_telegram(
                f"🟢 Bot started successfully!\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n"
                f"Webhook: {webhook_url}\n"
                f"Algo Scheduler: Active\n"
                f"MOVE Scheduler: Active ✅"
            )
        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        try:
            await log_to_telegram(f"🔴 CRITICAL: Failed to start bot!\nError: {str(e)}")
        except Exception as log_err:
            logger.warning(f"Failed to send error notification: {log_err}")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info("Shutting down bot...")
    logger.info("=" * 50)
    
    try:
        # ✅ Stop algo scheduler (check if running)
        if algo_scheduler_task and not algo_scheduler_task.done():
            logger.info("Stopping algo scheduler...")
            algo_scheduler_task.cancel()
            try:
                await algo_scheduler_task
            except asyncio.CancelledError:
                pass
            logger.info("✓ Algo scheduler stopped")

        # ✅ Stop MOVE scheduler (use global instance)
        if move_scheduler:
            logger.info("Stopping MOVE scheduler...")
            try:
                await move_scheduler.stop()
                logger.info("✓ MOVE scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping MOVE scheduler: {e}", exc_info=True)
        
        # ✅ Stop keep-alive service
        logger.info("Stopping keep-alive service...")
        try:
            await stop_keepalive()
            logger.info("✓ Keep-alive stopped")
        except Exception as e:
            logger.error(f"Error stopping keep-alive: {e}", exc_info=True)
        
        # Stop state manager cleanup task
        logger.info("Stopping state manager...")
        try:
            from bot.utils.state_manager import state_manager
            await state_manager.stop_cleanup_task()
            logger.info("✓ State manager stopped")
        except Exception as e:
            logger.error(f"Error stopping state manager: {e}", exc_info=True)
        
        # Shutdown job scheduler
        logger.info("Shutting down job scheduler...")
        try:
            await shutdown_scheduler()
            logger.info("✓ Job scheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}", exc_info=True)
        
        # Shutdown bot application
        if bot_app:
            logger.info("Shutting down bot application...")
            try:
                await bot_app.shutdown()
                logger.info("✓ Bot shutdown complete")
            except Exception as e:
                logger.error(f"Error during bot shutdown: {e}", exc_info=True)
        
        # Close database connection
        logger.info("Closing database connection...")
        try:
            await close_db()
            logger.info("✓ Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}", exc_info=True)
        
        logger.info("=" * 50)
        logger.info("Bot shutdown complete")
        logger.info("=" * 50)
        
        # ✅ Await shutdown notification (no fire-and-forget)
        try:
            await log_to_telegram(
                f"🔴 Bot shutting down\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
            )
        except Exception as e:
            logger.warning(f"Failed to send shutdown notification: {e}")
        
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


@app.api_route("/health", methods=["GET", "HEAD", "POST", "OPTIONS"])
async def health_check(request: Request):
    """
    Universal health check endpoint.
    Supports GET, HEAD, POST, and OPTIONS for maximum compatibility.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "telegram_trading_bot",
        "method": request.method
    }


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Webhook endpoint to receive Telegram updates.
    Processes updates sequentially with proper error handling.
    """
    try:
        # Parse incoming update
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)
        
        # Log incoming update
        update_id = update.update_id if update else "unknown"
        logger.debug(f"Received update: {update_id}")
        
        # Process update sequentially (await for proper ordering)
        if update:
            await bot_app.process_update(update)
        
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
            info = await bot_app.bot.get_webhook_info()
            return {
                "url": info.url,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date,
                "last_error_message": info.last_error_message,
                "max_connections": info.max_connections,
                "allowed_updates": info.allowed_updates
            }
        else:
            return {"error": "Bot not initialized"}
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/algo/status")
async def algo_status():
    """Get algo scheduler status."""
    try:
        from database.operations.algo_setup_ops import get_all_active_algo_setups
        
        setups = await get_all_active_algo_setups()
        
        return {
            "status": "running" if (algo_scheduler_task and not algo_scheduler_task.done()) else "stopped",
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


@app.get("/move/scheduler/status")
async def move_scheduler_status():
    """Get MOVE auto-trade scheduler status."""
    try:
        from database.operations.move_auto_trade_ops import get_all_active_move_schedules
        
        schedules = await get_all_active_move_schedules()
        
        # ✅ Use global move_scheduler instance
        scheduler_status = "running" if (move_scheduler and move_scheduler.running) else "stopped"
        
        return {
            "status": scheduler_status,
            "active_schedules": len(schedules),
            "schedules": [
                {
                    "user_id": s['user_id'],
                    "preset_name": s.get('preset_name'),
                    "execution_time": s['execution_time'],
                    "enabled": s.get('enabled', True),
                    "last_executed": s.get('last_executed')
                }
                for s in schedules
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting MOVE scheduler status: {e}", exc_info=True)
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
               
