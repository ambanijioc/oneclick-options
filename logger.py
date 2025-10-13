"""
Centralized logging module with Telegram log bot integration.
All modules use this logger for consistent logging across the application.
"""

import logging
import asyncio
import traceback
from datetime import datetime
from typing import Optional
from functools import wraps
import sys

import httpx
from config import config


class TelegramLogHandler(logging.Handler):
    """Custom logging handler that sends logs to Telegram bot."""
    
    def __init__(self, bot_token: str, chat_id: str, level=logging.WARNING):
        """
        Initialize Telegram log handler.
        
        Args:
            bot_token: Telegram bot token for log bot
            chat_id: Chat ID to send logs to
            level: Minimum log level to send to Telegram
        """
        super().__init__(level)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.client = httpx.AsyncClient(timeout=10.0)
        self._loop = None
    
    def emit(self, record: logging.LogRecord):
        """Send log record to Telegram."""
        try:
            log_entry = self.format(record)
            
            # Create event loop if it doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Send message asynchronously
            if loop.is_running():
                asyncio.create_task(self._send_log(log_entry))
            else:
                loop.run_until_complete(self._send_log(log_entry))
        except Exception as e:
            # Fallback to console if Telegram fails
            print(f"Failed to send log to Telegram: {e}")
    
    async def _send_log(self, message: str):
        """
        Asynchronously send log message to Telegram.
        
        Args:
            message: Formatted log message
        """
        try:
            # Split long messages (Telegram limit is 4096 characters)
            max_length = 4000
            if len(message) > max_length:
                messages = [message[i:i+max_length] 
                           for i in range(0, len(message), max_length)]
            else:
                messages = [message]
            
            for msg in messages:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": f"``````",
                    "parse_mode": "Markdown"
                }
                
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                
        except Exception as e:
            print(f"Error sending log to Telegram: {e}")
    
    async def close_async(self):
        """Close the async HTTP client."""
        await self.client.aclose()


class AppLogger:
    """Application logger with multiple handlers."""
    
    def __init__(self, name: str = "trading_bot"):
        """
        Initialize application logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler for all logs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(module)s.%(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        try:
            file_handler = logging.FileHandler('trading_bot.log')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - [%(levelname)s] - %(module)s.%(funcName)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not create file handler: {e}")
        
        # Telegram handler for warnings and errors
        try:
            telegram_handler = TelegramLogHandler(
                bot_token=config.telegram.log_bot_token,
                chat_id=config.telegram.log_chat_id,
                level=logging.WARNING
            )
            telegram_formatter = logging.Formatter(
                '🚨 %(levelname)s\n'
                '⏰ %(asctime)s\n'
                '📁 %(module)s.%(funcName)s\n'
                '💬 %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S IST'
            )
            telegram_handler.setFormatter(telegram_formatter)
            self.logger.addHandler(telegram_handler)
        except Exception as e:
            self.logger.warning(f"Could not create Telegram handler: {e}")
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger


# Global logger instance
app_logger = AppLogger()
logger = app_logger.get_logger()


def log_function_call(func):
    """
    Decorator to log function entry, exit, and exceptions.
    
    Args:
        func: Function to wrap with logging
    
    Returns:
        Wrapped function with logging
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(f"[{func_name}] Called with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"[{func_name}] Completed successfully")
            return result
        except Exception as e:
            logger.error(
                f"[{func_name}] Exception occurred: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(f"[{func_name}] Called with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"[{func_name}] Completed successfully")
            return result
        except Exception as e:
            logger.error(
                f"[{func_name}] Exception occurred: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            raise
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_with_context(level: str, message: str, **context):
    """
    Log message with additional context information.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context key-value pairs
    """
    context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
    full_message = f"{message} | {context_str}" if context else message
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(full_message)


if __name__ == "__main__":
    # Test logging
    logger.info("Testing logger configuration")
    logger.debug("Debug message test")
    logger.warning("Warning message test")
    logger.error("Error message test")
    
    # Test function decorator
    @log_function_call
    async def test_async_function(param1, param2):
        logger.info(f"Processing: {param1}, {param2}")
        return param1 + param2
    
    # Run test
    asyncio.run(test_async_function("Hello", " World"))
    
    print("✅ Logger configuration test completed!")
      
