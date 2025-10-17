"""
Keep-alive service to prevent Render.com free tier from sleeping.
"""

import asyncio
import aiohttp
from datetime import datetime
import pytz
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

IST = pytz.timezone('Asia/Kolkata')


async def ping_self(url: str):
    """Ping the bot's own URL to keep it alive."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    logger.info("✅ Keep-alive ping successful")
                else:
                    logger.warning(f"⚠️ Keep-alive ping returned {response.status}")
    except Exception as e:
        logger.error(f"❌ Keep-alive ping failed: {e}")


async def keepalive_loop(base_url: str):
    """
    Run keep-alive pings every 10 minutes.
    Only ping during Indian trading hours (8 AM - 4 PM IST).
    """
    logger.info("🔄 Keep-alive service started")
    
    while True:
        try:
            # Check current IST time
            now_ist = datetime.now(IST)
            current_hour = now_ist.hour
            
            # Only ping during trading hours (8 AM - 4 PM IST)
            if 8 <= current_hour < 16:
                await ping_self(base_url)
                logger.info(f"⏰ Keep-alive ping at {now_ist.strftime('%I:%M %p IST')}")
            else:
                logger.info(f"🌙 Off-hours ({now_ist.strftime('%I:%M %p IST')}) - skipping ping")
            
            # Wait 10 minutes
            await asyncio.sleep(600)  # 10 minutes
        
        except Exception as e:
            logger.error(f"❌ Keep-alive loop error: {e}", exc_info=True)
            await asyncio.sleep(60)  # Retry after 1 minute


def start_keepalive(app: Application, base_url: str):
    """Start the keep-alive service."""
    asyncio.create_task(keepalive_loop(base_url))
    logger.info(f"✅ Keep-alive service initialized for {base_url}")
  
