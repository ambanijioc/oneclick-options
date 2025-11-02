"""
Trading Bot Main Application - v2.0 (Production Ready)
Date: 2025-11-02

FastAPI application with comprehensive lifespan management.
Handles webhook integration, scheduler management, and graceful shutdown.

Architecture:
┌────────────────────────────────────────────────┐
│ Startup                                        │
├────────────────────────────────────────────────┤
│ 1. Connect Database                            │
│ 2. Initialize Bot Application                  │
│ 3. Delete existing webhook + Set new webhook   │
│ 4. Initialize schedulers (Algo, MOVE)          │
│ 5. Start keep-alive service                    │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│ Running - Listen for updates                   │
├────────────────────────────────────────────────┤
│ - Process webhook updates                      │
│ - Execute scheduled tasks                      │
│ - Monitor health                               │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│ Shutdown                                       │
├────────────────────────────────────────────────┤
│ 1. Cancel background tasks                     │
│ 2. Stop schedulers (Algo, MOVE)                │
│ 3. Stop keep-alive service                     │
│ 4. Shutdown bot & database                     │
│ 5. Send notifications                          │
└────────────────────────────────────────────────┘
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


# ============= GLOBAL STATE AT MODULE LEVEL =============
# ✅ All globals declared here and used in lifespan
bot_app: Application = None
algo_scheduler_task: asyncio.Task = None
move_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ✅ Lifespan context manager for FastAPI startup and shutdown.
    
    Manages:
    - Database connections
    - Bot application initialization
    - Scheduler management (Algo, MOVE, Job)
    - Keep-alive service
    - Graceful shutdown with error handling
    
    All globals are declared and used here.
    """
    global bot_app, algo_scheduler_task, move_scheduler
    
    # ==================== STARTUP ====================
    logger.info("=" * 80)
    logger.info("🤖 TELEGRAM TRADING BOT - STARTUP")
    logger.info("=" * 80)
    
    startup_errors = []
    
    try:
        # Step 1: Connect to database
        logger.info("\n📊 Step 1: Connecting to MongoDB...")
        try:
            await connect_db()
            logger.info("  ✓ MongoDB connected successfully")
        except Exception as e:
            msg = f"Database connection failed: {e}"
            logger.error(f"  ❌ {msg}")
            startup_errors.append(msg)
            raise
        
        # Step 2: Initialize bot application
        logger.info("\n🤖 Step 2: Initializing bot application...")
        try:
            bot_app = await create_application()
            await bot_app.initialize()
            logger.info("  ✓ Bot application initialized")
        except Exception as e:
            msg = f"Bot initialization failed: {e}"
            logger.error(f"  ❌ {msg}")
            startup_errors.append(msg)
            raise

        # Step 3: Start state manager cleanup
        logger.info("\n💾 Step 3: Starting state manager...")
        try:
            from bot.utils.state_manager import state_manager
            await state_manager.start_cleanup_task()
            logger.info("  ✓ State manager started")
        except Exception as e:
            logger.warning(f"  ⚠️ State manager warning: {e}")
        
        # Step 4: Setup webhook
        logger.info("\n🔗 Step 4: Configuring webhook...")
        try:
            # Delete existing webhook
            logger.info("  • Deleting existing webhook...")
            await bot_app.bot.delete_webhook(drop_pending_updates=True)
            logger.info("    ✓ Existing webhook deleted")
            
            # Set new webhook
            webhook_url = settings.get_webhook_endpoint()
            logger.info(f"  • Setting webhook to: {webhook_url}")
            await bot_app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=False
            )
            
            # Verify webhook
            webhook_info = await bot_app.bot.get_webhook_info()
            if webhook_info.url == webhook_url:
                logger.info(f"  ✓ Webhook configured successfully")
                logger.info(f"    - URL: {webhook_info.url}")
                logger.info(f"    - Pending updates: {webhook_info.pending_update_count}")
            else:
                msg = f"Webhook mismatch. Expected: {webhook_url}, Got: {webhook_info.url}"
                logger.error(f"  ❌ {msg}")
                startup_errors.append(msg)
        
        except Exception as e:
            msg = f"Webhook configuration failed: {e}"
            logger.error(f"  ❌ {msg}")
            startup_errors.append(msg)
        
        # Step 5: Initialize job scheduler
        logger.info("\n⏰ Step 5: Initializing job scheduler...")
        try:
            await init_scheduler(bot_app)
            logger.info("  ✓ Job scheduler initialized")
        except Exception as e:
            logger.warning(f"  ⚠️ Job scheduler warning: {e}")
        
        # Step 6: Start algo scheduler
        logger.info("\n🔄 Step 6: Starting algo scheduler...")
        try:
            algo_scheduler_task = asyncio.create_task(start_algo_scheduler(bot_app))
            logger.info("  ✓ Algo scheduler started (background task)")
        except Exception as e:
            logger.warning(f"  ⚠️ Algo scheduler warning: {e}")
        
        # Step 7: Start MOVE scheduler
        logger.info("\n📈 Step 7: Starting MOVE auto-trade scheduler...")
        try:
            move_scheduler = get_move_scheduler(bot_app)
            await move_scheduler.start()
            logger.info("  ✓ MOVE scheduler started")
        except Exception as e:
            logger.warning(f"  ⚠️ MOVE scheduler warning: {e}")
        
        # Step 8: Start keep-alive service
        logger.info("\n💚 Step 8: Starting keep-alive service...")
        try:
            base_url = os.getenv(
                'RENDER_EXTERNAL_URL',
                'https://oneclick-options.onrender.com'
            )
            logger.info(f"  • Base URL: {base_url}")
            start_keepalive(base_url)
            logger.info("  ✓ Keep-alive service started")
        except Exception as e:
            logger.warning(f"  ⚠️ Keep-alive warning: {e}")
        
        # Startup complete
        logger.info("\n" + "=" * 80)
        logger.info("✅ BOT STARTUP COMPLETE - Ready to receive updates!")
        logger.info("=" * 80 + "\n")
        
        # Send startup notification
        try:
            message = f"""
🟢 <b>Bot Started Successfully!</b>

<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
<b>Webhook:</b> Configured ✓
<b>Database:</b> Connected ✓
<b>Schedulers:</b> Algo & MOVE Active ✓
<b>Keep-Alive:</b> Running ✓
            """.strip()
            await log_to_telegram(message)
        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")
        
    except Exception as e:
        logger.critical(f"\n❌ STARTUP FAILED: {e}", exc_info=True)
        
        # Send error notification
        try:
            await log_to_telegram(f"🔴 <b>Startup Failed!</b>\n\nError: {str(e)}")
        except Exception as log_err:
            logger.warning(f"Failed to send error notification: {log_err}")
        
        raise
    
    # ==================== YIELD (APP RUNNING) ====================
    yield
    
    # ==================== SHUTDOWN ====================
    logger.info("\n" + "=" * 80)
    logger.info("🛑 BOT SHUTDOWN - Cleaning up...")
    logger.info("=" * 80)
    
    shutdown_errors = []
    
    # Step 1: Stop algo scheduler
    logger.info("\n🔄 Step 1: Stopping algo scheduler...")
    try:
        if algo_scheduler_task and not algo_scheduler_task.done():
            algo_scheduler_task.cancel()
            try:
                await algo_scheduler_task
            except asyncio.CancelledError:
                pass
            logger.info("  ✓ Algo scheduler stopped")
        else:
            logger.info("  ✓ Algo scheduler not running")
    except Exception as e:
        msg = f"Algo scheduler shutdown error: {e}"
        logger.error(f"  ❌ {msg}")
        shutdown_errors.append(msg)
    
    # Step 2: Stop MOVE scheduler
    logger.info("\n📈 Step 2: Stopping MOVE scheduler...")
    try:
        if move_scheduler:
            await move_scheduler.stop()
            logger.info("  ✓ MOVE scheduler stopped")
        else:
            logger.info("  ✓ MOVE scheduler not running")
    except Exception as e:
        msg = f"MOVE scheduler shutdown error: {e}"
        logger.error(f"  ❌ {msg}")
        shutdown_errors.append(msg)
    
    # Step 3: Stop keep-alive
    logger.info("\n💚 Step 3: Stopping keep-alive service...")
    try:
        await stop_keepalive()
        logger.info("  ✓ Keep-alive service stopped")
    except Exception as e:
        msg = f"Keep-alive shutdown error: {e}"
        logger.error(f"  ❌ {msg}")
        shutdown_errors.append(msg)
    
    # Step 4: Stop state manager
    logger.info("\n💾 Step 4: Stopping state manager...")
    try:
        from bot.utils.state_manager import state_manager
        await state_manager.stop_cleanup_task()
        logger.info("  ✓ State manager stopped")
    except Exception as e:
        logger.warning(f"  ⚠️ State manager warning: {e}")
    
    # Step 5: Shutdown job scheduler
    logger.info("\n⏰ Step 5: Shutting down job scheduler...")
    try:
        await shutdown_scheduler()
        logger.info("  ✓ Job scheduler shutdown complete")
    except Exception as e:
        msg = f"Job scheduler shutdown error: {e}"
        logger.error(f"  ❌ {msg}")
        shutdown_errors.append(msg)
    
    # Step 6: Shutdown bot
    logger.info("\n🤖 Step 6: Shutting down bot application...")
    try:
        if bot_app:
            await bot_app.shutdown()
            logger.info("  ✓ Bot shutdown complete")
        else:
            logger.info("  ✓ Bot not initialized")
    except Exception as e:
        msg = f"Bot shutdown error: {e}"
        logger.error(f"  ❌ {msg}")
        shutdown_errors.append(msg)
    
    # Step 7: Close database
    logger.info("\n📊 Step 7: Closing database connection...")
    try:
        await close_db()
        logger.info("  ✓ Database connection closed")
    except Exception as e:
        msg = f"Database close error: {e}"
        logger.error(f"  ❌ {msg}")
        shutdown_errors.append(msg)
    
    # Shutdown complete
    logger.info("\n" + "=" * 80)
    if shutdown_errors:
        logger.warning(f"⚠️ SHUTDOWN COMPLETE WITH {len(shutdown_errors)} ERRORS")
        for error in shutdown_errors:
            logger.warning(f"  - {error}")
    else:
        logger.info("✅ SHUTDOWN COMPLETE - All services stopped gracefully")
    logger.info("=" * 80 + "\n")
    
    # Send shutdown notification
    try:
        await log_to_telegram(
            f"🔴 <b>Bot Shutting Down</b>\n\n"
            f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
        )
    except Exception as e:
        logger.warning(f"Failed to send shutdown notification: {e}")


# ==================== CREATE FASTAPI APP ====================
app = FastAPI(
    title="Telegram Trading Bot",
    description="Delta Exchange options trading bot via Telegram",
    version="2.0.0",
    lifespan=lifespan
)


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint - service information."""
    return {
        "status": "running",
        "service": "Telegram Trading Bot",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs"
    }


@app.api_route("/health", methods=["GET", "HEAD", "POST", "OPTIONS"])
async def health_check(request: Request):
    """
    Universal health check endpoint.
    Supports multiple methods for maximum compatibility.
    """
    return {
        "status": "ok",
        "service": "telegram_trading_bot",
        "timestamp": datetime.now().isoformat(),
        "method": request.method
    }


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    ✅ Webhook endpoint for Telegram updates.
    - Parses JSON update
    - Processes update sequentially
    - Always returns 200 OK
    """
    try:
        # Parse incoming update
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)
        
        # Log update
        update_id = update.update_id if update else "unknown"
        logger.debug(f"Received update: {update_id}")
        
        # Process update (await for proper ordering)
        if update:
            await bot_app.process_update(update)
        
        # Return 200 immediately
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        # Still return 200 to prevent Telegram retries
        return Response(status_code=200)


@app.get("/webhook/info")
async def webhook_info():
    """Get current webhook information (debugging)."""
    try:
        if not bot_app:
            return {"error": "Bot not initialized"}
        
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
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/algo/status")
async def algo_status():
    """Get algo scheduler status and active setups."""
    try:
        from database.operations.algo_setup_ops import get_all_active_algo_setups
        
        setups = await get_all_active_algo_setups()
        is_running = (
            algo_scheduler_task and 
            not algo_scheduler_task.done()
        )
        
        return {
            "status": "running" if is_running else "stopped",
            "active_setups": len(setups),
            "setups": [
                {
                    "user_id": s.get('user_id'),
                    "execution_time": s.get('execution_time'),
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
        is_running = move_scheduler and move_scheduler.running
        
        return {
            "status": "running" if is_running else "stopped",
            "active_schedules": len(schedules),
            "schedules": [
                {
                    "user_id": s.get('user_id'),
                    "preset_name": s.get('preset_name'),
                    "execution_time": s.get('execution_time'),
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


# ==================== RUN SERVER ====================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
    
