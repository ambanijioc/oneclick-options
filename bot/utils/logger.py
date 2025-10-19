"""
Logging configuration with dual output: file and Telegram.
Sends critical logs to a separate Telegram bot for monitoring.
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from functools import wraps
import traceback

from telegram import Bot
from telegram.error import TelegramError

from config import settings

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Rate limiting for Telegram logs
_telegram_log_queue = []
_last_telegram_log_time = datetime.now()
_telegram_log_lock = asyncio.Lock()
MAX_TELEGRAM_LOGS_PER_MINUTE = 10

# Telegram bot for logging
_log_bot: Optional[Bot] = None


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # ✅ PREVENT DUPLICATE HANDLERS - Check if THIS logger already has handlers
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # ✅ PREVENT PROPAGATION TO ROOT LOGGER
    logger.propagate = False
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (daily rotation)
    log_file = LOGS_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_log_file = LOGS_DIR / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_file_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_file_handler)
    
    return logger


def _get_log_bot() -> Bot:
    """Get or create the logging bot instance."""
    global _log_bot
    if _log_bot is None:
        _log_bot = Bot(token=settings.LOG_BOT_TOKEN)
    return _log_bot


def _get_log_emoji(level: str) -> str:
    """Get emoji for log level."""
    emoji_map = {
        'DEBUG': '🔍',
        'INFO': '🟢',
        'WARNING': '🟡',
        'ERROR': '🔴',
        'CRITICAL': '🚨'
    }
    return emoji_map.get(level.upper(), '📝')


async def log_to_telegram(
    message: str,
    level: str = "INFO",
    module: Optional[str] = None,
    user_id: Optional[int] = None,
    error_details: Optional[str] = None,
    timeout: float = 3.0  # ✅ ADD TIMEOUT
) -> bool:
    """
    Send log message to Telegram bot with rate limiting and timeout.
    
    Args:
        message: Log message to send
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        module: Module name where log originated
        user_id: User ID if applicable
        error_details: Additional error details (traceback)
        timeout: Maximum time to wait for send (seconds)
    
    Returns:
        True if message was sent successfully, False otherwise
    """
    global _last_telegram_log_time, _telegram_log_queue
    
    # Only log INFO and above to Telegram
    if level.upper() == 'DEBUG':
        return False
    
    try:
        # ✅ ADD TIMEOUT PROTECTION
        async with asyncio.timeout(timeout):  # Python 3.11+
            async with _telegram_log_lock:
                current_time = datetime.now()
                
                # Reset queue if more than a minute has passed
                if (current_time - _last_telegram_log_time).seconds >= 60:
                    _telegram_log_queue.clear()
                    _last_telegram_log_time = current_time
                
                # Check rate limit
                if len(_telegram_log_queue) >= MAX_TELEGRAM_LOGS_PER_MINUTE:
                    return False
                
                # Format message
                emoji = _get_log_emoji(level)
                formatted_message = f"{emoji} <b>{level.upper()}</b>\n"
                formatted_message += f"⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
                
                if module:
                    formatted_message += f"📦 Module: <code>{module}</code>\n"
                
                if user_id:
                    formatted_message += f"👤 User: <code>{user_id}</code>\n"
                
                formatted_message += f"\n💬 {message}\n"
                
                if error_details:
                    # Truncate if too long
                    if len(error_details) > 500:
                        error_details = error_details[:500] + "...\n[Truncated]"
                    formatted_message += f"\n<pre>{error_details}</pre>"
                
                # Truncate entire message if too long (Telegram limit: 4096 chars)
                if len(formatted_message) > 4000:
                    formatted_message = formatted_message[:4000] + "\n...\n[Message truncated]"
                
                # Send message
                bot = _get_log_bot()
                await bot.send_message(
                    chat_id=settings.LOG_CHAT_ID,
                    text=formatted_message,
                    parse_mode='HTML'
                )
                
                _telegram_log_queue.append(current_time)
                return True
    
    except asyncio.TimeoutError:  # ✅ HANDLE TIMEOUT
        logger = logging.getLogger(__name__)
        logger.warning(f"Telegram log timed out after {timeout}s")
        return False
    except TelegramError as e:
        # Log to console if Telegram fails
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send log to Telegram: {e}")
        return False
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in log_to_telegram: {e}")
        return False


def log_user_action(user_id: int, action: str, details: Optional[str] = None):
    """
    Log user action for audit trail.
    
    Args:
        user_id: User ID
        action: Action performed
        details: Additional details
    """
    logger = logging.getLogger("user_actions")
    log_message = f"User {user_id} - {action}"
    if details:
        log_message += f" - {details}"
    logger.info(log_message)


def log_api_call(
    api_id: str,
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
    error: Optional[str] = None
):
    """
    Log API call for monitoring.
    
    Args:
        api_id: API credential ID
        endpoint: API endpoint called
        method: HTTP method
        status_code: Response status code
        error: Error message if failed
    """
    logger = logging.getLogger("api_calls")
    log_message = f"API {api_id} - {method} {endpoint}"
    
    if status_code:
        log_message += f" - Status: {status_code}"
    
    if error:
        log_message += f" - Error: {error}"
        logger.error(log_message)
    else:
        logger.info(log_message)


def log_trade_execution(
    user_id: int,
    api_id: str,
    strategy_type: str,
    asset: str,
    action: str,
    details: Optional[dict] = None
):
    """
    Log trade execution for audit trail.
    
    Args:
        user_id: User ID
        api_id: API credential ID
        strategy_type: Strategy type (straddle/strangle)
        asset: Asset (BTC/ETH)
        action: Action (entry/exit/sl/target)
        details: Additional details (prices, order IDs, etc.)
    """
    logger = logging.getLogger("trade_execution")
    log_message = f"User {user_id} - API {api_id} - {strategy_type} {asset} - {action}"
    
    if details:
        log_message += f" - {details}"
    
    logger.info(log_message)
    
    # Also log to Telegram for important trade events
    if action in ['entry', 'exit']:
        asyncio.create_task(
            log_to_telegram(
                message=f"Trade {action}: {strategy_type} {asset}",
                level="INFO",
                module="trade_execution",
                user_id=user_id
            )
        )


class TelegramLogHandler(logging.Handler):
    """
    Custom logging handler that sends logs to Telegram.
    """
    
    def __init__(self, level=logging.WARNING):
        super().__init__(level)
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record to Telegram."""
        try:
            # Format the message
            log_entry = self.format(record)
            
            # Extract error details if exception
            error_details = None
            if record.exc_info:
                error_details = ''.join(traceback.format_exception(*record.exc_info))
            
            # Send to Telegram (non-blocking)
            asyncio.create_task(
                log_to_telegram(
                    message=record.getMessage(),
                    level=record.levelname,
                    module=record.name,
                    error_details=error_details
                )
            )
        except Exception:
            self.handleError(record)


def add_telegram_handler(logger: logging.Logger, level=logging.WARNING):
    """
    Add Telegram handler to existing logger.
    
    Args:
        logger: Logger instance
        level: Minimum level to send to Telegram
    """
    telegram_handler = TelegramLogHandler(level)
    telegram_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(telegram_handler)


# Create a default logger
logger = setup_logger(__name__)


if __name__ == "__main__":
    # Test logging
    test_logger = setup_logger("test")
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    # Test Telegram logging
    async def test_telegram_log():
        await log_to_telegram("Test message", "INFO", "test_module", 123456789)
        await log_to_telegram("Test error", "ERROR", "test_module", 123456789, "Traceback details...")
    
    asyncio.run(test_telegram_log())
              
