"""
Keep-alive service to prevent Render.com free tier from sleeping.
Optimized for 24x7 Delta Exchange India trading.
"""

import asyncio
import aiohttp
from datetime import datetime
import pytz
from bot.utils.logger import setup_logger

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
    Run keep-alive pings every 10 minutes.
    
    For 24x7 operation (Delta Exchange India):
    - Pings continuously to prevent sleep
    - Render free tier sleeps after 15 minutes inactivity
    - 10-minute interval ensures 100% uptime
    """
    logger.info("🔄 Keep-alive service started (24x7 mode)")
    logger.info(f"🎯 Pinging: {base_url}/health every 10 minutes")
    
    ping_count = 0
    failed_count = 0
    
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
            else:
                failed_count += 1
                logger.warning(f"⚠️ Keep-alive failed {failed_count} times")
            
            # Alert if multiple failures
            if failed_count >= 3:
                from bot.utils.logger import log_to_telegram
                await log_to_telegram(
                    f"🔴 Keep-alive failing!\n"
                    f"Failed {failed_count} consecutive pings\n"
                    f"Bot may be sleeping!"
                )
            
            # Wait 10 minutes (600 seconds)
            await asyncio.sleep(600)
        
        except Exception as e:
            logger.error(f"❌ Keep-alive loop error: {e}", exc_info=True)
            # Wait 1 minute before retry
            await asyncio.sleep(60)


# Task reference for graceful shutdown
keepalive_task = None


def start_keepalive(base_url: str):
    """
    Start the keep-alive background task.
    
    Args:
        base_url: Your Render.com URL (e.g., https://oneclick-options.onrender.com)
    """
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
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
        logger.info("✓ Keep-alive service stopped")
        
