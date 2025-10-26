"""
Keep-alive service to prevent Render.com free tier from sleeping.
Optimized for 24x7 Delta Exchange India trading with Telegram notifications.
"""

import asyncio
import aiohttp
from datetime import datetime
import pytz
from bot.utils.logger import setup_logger, log_to_telegram

logger = setup_logger(__name__)

IST = pytz.timezone('Asia/Kolkata')


async def ping_self(url: str):
    """Ping the bot's own health endpoint to keep it alive."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logger.info("✅ Keep-alive ping successful")
                    return True
                else:
                    logger.warning(f"⚠️ Keep-alive ping returned {response.status}")
                    return False
    except asyncio.TimeoutError:
        logger.error("❌ Keep-alive ping timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Keep-alive ping failed: {e}")
        return False


async def keepalive_loop(base_url: str):
    """
    Run keep-alive pings every 10 minutes (24x7 operation).
    Sends Telegram notification every hour.
    """
    logger.info("🔄 Keep-alive service started (24x7 mode)")
    logger.info(f"🎯 Pinging: {base_url}/health every 10 minutes")
    
    # Send startup notification
    await log_to_telegram(
        f"🔄 Keep-Alive Started\n"
        f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n"
        f"Interval: Every 10 minutes\n"
        f"Status: Active 24x7"
    )
    
    ping_count = 0
    failed_count = 0
    last_telegram_log = datetime.now(IST)
    
    while True:
        try:
            now_ist = datetime.now(IST)
            
            # Ping regardless of time (24x7 operation)
            success = await ping_self(base_url)
            
            ping_count += 1
            
            if success:
                logger.info(
                    f"⏰ Keep-alive #{ping_count} at {now_ist.strftime('%I:%M %p IST')} "
                    f"| Failed: {failed_count}"
                )
                failed_count = 0  # Reset on success
                
                # Send hourly status to Telegram (every 12 pings = 1 hour)
                if ping_count % 12 == 0:
                    await log_to_telegram(
                        f"✅ Keep-Alive Status\n"
                        f"Time: {now_ist.strftime('%I:%M %p IST')}\n"
                        f"Total Pings: {ping_count}\n"
                        f"Status: All systems operational"
                    )
            else:
                failed_count += 1
                logger.warning(f"⚠️ Keep-alive failed {failed_count} times")
                
                # Immediate Telegram alert on failure
                await log_to_telegram(
                    f"⚠️ Keep-Alive Warning\n"
                    f"Failed {failed_count} consecutive pings\n"
                    f"Time: {now_ist.strftime('%I:%M %p IST')}\n"
                    f"Retrying..."
                )
            
            # Critical alert if multiple failures
            if failed_count >= 3:
                await log_to_telegram(
                    f"🔴 Keep-Alive CRITICAL\n"
                    f"Failed {failed_count} consecutive pings!\n"
                    f"Time: {now_ist.strftime('%I:%M %p IST')}\n"
                    f"Bot may be sleeping!\n"
                    f"Action Required: Check Render logs"
                )
            
            # Wait 5 minutes (300 seconds)
            await asyncio.sleep(300)
        
        except Exception as e:
            logger.error(f"❌ Keep-alive loop error: {e}", exc_info=True)
            await log_to_telegram(
                f"❌ Keep-Alive Error\n"
                f"Error: {str(e)[:100]}\n"
                f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n"
                f"Restarting in 1 minute..."
            )
            await asyncio.sleep(60)


keepalive_task = None


def start_keepalive(base_url: str):
    """Start the keep-alive background task."""
    global keepalive_task
    
    if keepalive_task and not keepalive_task.done():
        logger.warning("⚠️ Keep-alive already running!")
        return
    
    keepalive_task = asyncio.create_task(keepalive_loop(base_url))
    logger.info(f"✅ Keep-alive service initialized for {base_url}")


async def stop_keepalive():
    """Stop the keep-alive service gracefully."""
    global keepalive_task
    
    if keepalive_task and not keepalive_task.done():
        logger.info("Stopping keep-alive service...")
        
        # Send shutdown notification
        await log_to_telegram(
            f"🔴 Keep-Alive Stopped\n"
            f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n"
            f"Bot shutting down..."
        )
        
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
        logger.info("✓ Keep-alive service stopped")
    
