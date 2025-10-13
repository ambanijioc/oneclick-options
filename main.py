"""
Main application entry point.
FastAPI application with Telegram webhook integration.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from telegram import Update
from telegram.ext import Application

from config import config
from logger import logger, log_function_call
from database.connection import db_manager, shutdown_database
from scheduler.job_scheduler import start_scheduler, stop_scheduler
from scheduler.tasks import start_background_tasks, stop_background_tasks


# Global telegram application instance
telegram_app: Application = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("[lifespan] Application starting up...")
    
    try:
        # Initialize database connection
        logger.info("[lifespan] Connecting to database...")
        await db_manager.connect()
        logger.info("[lifespan] Database connected successfully")
        
        # Initialize Telegram bot
        logger.info("[lifespan] Initializing Telegram bot...")
        await initialize_telegram_bot()
        logger.info("[lifespan] Telegram bot initialized")
        
        # Start scheduler
        logger.info("[lifespan] Starting scheduler...")
        await start_scheduler()
        logger.info("[lifespan] Scheduler started")
        
        # Start background tasks
        logger.info("[lifespan] Starting background tasks...")
        await start_background_tasks()
        logger.info("[lifespan] Background tasks started")
        
        logger.info("[lifespan] ✅ Application startup completed successfully")
        
    except Exception as e:
        logger.critical(f"[lifespan] Failed to start application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("[lifespan] Application shutting down...")
    
    try:
        # Stop background tasks
        logger.info("[lifespan] Stopping background tasks...")
        await stop_background_tasks()
        
        # Stop scheduler
        logger.info("[lifespan] Stopping scheduler...")
        await stop_scheduler()
        
        # Shutdown Telegram bot
        logger.info("[lifespan] Shutting down Telegram bot...")
        await shutdown_telegram_bot()
        
        # Close database connection
        logger.info("[lifespan] Closing database connection...")
        await shutdown_database()
        
        logger.info("[lifespan] ✅ Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"[lifespan] Error during shutdown: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="Delta Exchange Trading Bot",
    description="Telegram bot for automated options trading on Delta Exchange India",
    version="1.0.0",
    lifespan=lifespan
)


@log_function_call
async def initialize_telegram_bot():
    """Initialize Telegram bot application."""
    global telegram_app
    
    try:
        from telegram.bot import create_application
        
        # Create application
        telegram_app = await create_application()
        
        # Initialize the application
        await telegram_app.initialize()
        
        # Set webhook
        webhook_url = config.render.webhook_url
        logger.info(f"[initialize_telegram_bot] Setting webhook to: {webhook_url}")
        
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        # Start the application (without polling)
        await telegram_app.start()
        
        logger.info("[initialize_telegram_bot] Telegram bot initialized successfully")
        
    except Exception as e:
        logger.error(f"[initialize_telegram_bot] Error initializing bot: {e}", exc_info=True)
        raise


@log_function_call
async def shutdown_telegram_bot():
    """Shutdown Telegram bot application."""
    global telegram_app
    
    try:
        if telegram_app:
            # Delete webhook
            await telegram_app.bot.delete_webhook()
            
            # Stop application
            await telegram_app.stop()
            
            # Shutdown
            await telegram_app.shutdown()
            
            logger.info("[shutdown_telegram_bot] Telegram bot shut down successfully")
        
    except Exception as e:
        logger.error(f"[shutdown_telegram_bot] Error shutting down bot: {e}")


@app.get("/")
@log_function_call
async def root():
    """Root endpoint - basic info."""
    return {
        "name": "Delta Exchange Trading Bot",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
@log_function_call
async def health_check():
    """
    Health check endpoint for monitoring services like UptimeRobot.
    
    Returns:
        Health status JSON
    """
    try:
        # Check database health
        db_healthy = await db_manager.health_check()
        
        # Check if bot is initialized
        bot_healthy = telegram_app is not None
        
        health_status = {
            "status": "healthy" if (db_healthy and bot_healthy) else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "telegram_bot": "initialized" if bot_healthy else "not_initialized",
            "timestamp": None
        }
        
        # Import datetime here to avoid circular imports
        from datetime import datetime
        import pytz
        health_status["timestamp"] = datetime.now(pytz.UTC).isoformat()
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        logger.info(f"[health_check] Health check: {health_status['status']}")
        
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"[health_check] Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )


@app.post("/webhook")
@log_function_call
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint.
    Receives updates from Telegram and processes them.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Response confirming receipt
    """
    try:
        # Get update data
        update_data = await request.json()
        
        logger.debug(f"[telegram_webhook] Received update: {update_data.get('update_id')}")
        
        # Create Update object
        update = Update.de_json(update_data, telegram_app.bot)
        
        # Process update
        await telegram_app.process_update(update)
        
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"[telegram_webhook] Error processing webhook: {e}", exc_info=True)
        # Return 200 to prevent Telegram from retrying
        return Response(status_code=200)


@app.get("/api/status")
@log_function_call
async def api_status():
    """
    Get detailed API status.
    
    Returns:
        Detailed status information
    """
    try:
        from scheduler.job_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        # Get active schedules count
        schedules = await scheduler.schedule_ops.get_active_schedules()
        
        status = {
            "application": "running",
            "database": "connected" if await db_manager.health_check() else "disconnected",
            "telegram_bot": "active" if telegram_app else "inactive",
            "scheduler": "running" if scheduler.is_running else "stopped",
            "active_schedules": len(schedules),
            "webhook_url": config.render.webhook_url
        }
        
        logger.info("[api_status] Status check completed")
        
        return status
        
    except Exception as e:
        logger.error(f"[api_status] Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schedules")
@log_function_call
async def get_all_schedules():
    """
    Get all active schedules (admin endpoint).
    
    Returns:
        List of active schedules
    """
    try:
        from scheduler.job_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        schedules = await scheduler.schedule_ops.get_active_schedules()
        
        logger.info(f"[get_all_schedules] Retrieved {len(schedules)} schedules")
        
        return {
            "count": len(schedules),
            "schedules": schedules
        }
        
    except Exception as e:
        logger.error(f"[get_all_schedules] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/manual-cleanup")
@log_function_call
async def manual_cleanup():
    """
    Manually trigger database cleanup (admin endpoint).
    
    Returns:
        Cleanup result
    """
    try:
        from scheduler.tasks import get_background_tasks
        
        tasks = get_background_tasks()
        await tasks.run_manual_cleanup()
        
        logger.info("[manual_cleanup] Manual cleanup completed")
        
        return {
            "status": "success",
            "message": "Cleanup completed successfully"
        }
        
    except Exception as e:
        logger.error(f"[manual_cleanup] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: Request that caused the error
        exc: Exception that was raised
    
    Returns:
        JSON error response
    """
    logger.error(
        f"[global_exception_handler] Unhandled exception: {exc}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


@app.on_event("startup")
async def log_startup_info():
    """Log startup information."""
    logger.info("=" * 80)
    logger.info("DELTA EXCHANGE TRADING BOT")
    logger.info("=" * 80)
    logger.info(f"Host: {config.render.host}")
    logger.info(f"Port: {config.render.port}")
    logger.info(f"Webhook URL: {config.render.webhook_url}")
    logger.info(f"Database: {config.mongodb.database_name}")
    logger.info("=" * 80)


if __name__ == "__main__":
    """
    Run the application directly (for local development).
    In production, use: gunicorn main:app --worker-class uvicorn.workers.UvicornWorker
    """
    logger.info("[main] Starting application in development mode...")
    
    uvicorn.run(
        "main:app",
        host=config.render.host,
        port=config.render.port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
  
