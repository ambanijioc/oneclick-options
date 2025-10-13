"""
Bot application initialization and configuration.
"""

from telegram.ext import Application, ApplicationBuilder

from config import settings
from bot.utils.logger import setup_logger, log_to_telegram
from bot.utils.error_handler import global_error_handler
from bot.handlers import register_all_handlers

logger = setup_logger(__name__)


async def create_application() -> Application:
    """
    Create and configure the bot application.
    
    Returns:
        Configured Application instance
    """
    try:
        logger.info("Creating bot application...")
        
        # Build application
        application = (
            ApplicationBuilder()
            .token(settings.BOT_TOKEN)
            .concurrent_updates(True)  # Enable concurrent update processing
            .build()
        )
        
        # Register all handlers
        logger.info("Registering handlers...")
        register_all_handlers(application)
        
        # Register global error handler
        application.add_error_handler(global_error_handler)
        logger.info("Registered global error handler")
        
        logger.info("✓ Bot application created successfully")
        
        return application
    
    except Exception as e:
        logger.critical(f"Failed to create bot application: {e}", exc_info=True)
        await log_to_telegram(
            message=f"Failed to create bot application: {str(e)}",
            level="CRITICAL",
            module="bot.application"
        )
        raise


if __name__ == "__main__":
    import asyncio
    
    async def test():
        app = await create_application()
        print(f"Application created: {app is not None}")
        print(f"Bot username: {app.bot.username if app.bot else 'Unknown'}")
    
    asyncio.run(test())
  
