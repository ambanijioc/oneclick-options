"""
Telegram bot initialization and configuration.
Sets up handlers and creates the bot application.
"""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler

from config import config
from logger import logger, log_function_call


@log_function_call
async def create_application() -> Application:
    """
    Create and configure Telegram bot application.
    
    Returns:
        Configured Application instance
    """
    try:
        # Create application builder
        builder = Application.builder()
        
        # Set bot token
        builder.token(config.telegram.bot_token)
        
        # Build application
        application = builder.build()
        
        # Register handlers
        await register_handlers(application)
        
        logger.info("[create_application] Telegram application created and configured")
        
        return application
        
    except Exception as e:
        logger.error(f"[create_application] Error creating application: {e}", exc_info=True)
        raise


@log_function_call
async def register_handlers(application: Application):
    """
    Register all command and callback handlers.
    
    Args:
        application: Telegram Application instance
    """
    try:
        # Import handlers (will be implemented in next step)
        from telegram.commands import start_command, help_command
        from telegram.callbacks import callback_query_router
        
        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        
        # Register callback query handler (for inline keyboards)
        application.add_handler(CallbackQueryHandler(callback_query_router))
        
        # Additional handlers will be registered here as they are implemented
        
        logger.info("[register_handlers] All handlers registered successfully")
        
    except ImportError as e:
        logger.warning(
            f"[register_handlers] Some handlers not yet implemented: {e}. "
            f"This is expected during initial setup."
        )
    except Exception as e:
        logger.error(f"[register_handlers] Error registering handlers: {e}", exc_info=True)
        raise


@log_function_call
async def post_init(application: Application):
    """
    Post-initialization tasks for the bot.
    
    Args:
        application: Telegram Application instance
    """
    try:
        # Set bot commands menu
        from telegram import BotCommand
        
        commands = [
            BotCommand("start", "Start the bot and show main menu"),
            BotCommand("help", "Show help and available commands")
        ]
        
        await application.bot.set_my_commands(commands)
        
        logger.info("[post_init] Bot commands menu configured")
        
    except Exception as e:
        logger.error(f"[post_init] Error in post-init: {e}")


if __name__ == "__main__":
    import asyncio
    
    async def test_bot_creation():
        """Test bot creation."""
        print("Testing bot creation...")
        
        try:
            app = await create_application()
            print(f"✅ Bot created: @{(await app.bot.get_me()).username}")
            
            # Initialize
            await app.initialize()
            print("✅ Bot initialized")
            
            # Get bot info
            bot_info = await app.bot.get_me()
            print(f"✅ Bot name: {bot_info.first_name}")
            print(f"✅ Bot username: @{bot_info.username}")
            
            # Shutdown
            await app.shutdown()
            print("✅ Bot shutdown")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n✅ Bot creation test completed!")
    
    asyncio.run(test_bot_creation())
          
