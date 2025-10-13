"""
Error handling decorators and utilities.
"""

import functools
import traceback
from typing import Callable, Optional, Any
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, NetworkError, TimedOut

from .logger import setup_logger, log_to_telegram
from .message_formatter import format_error_message

logger = setup_logger(__name__)


def error_handler(func: Callable) -> Callable:
    """
    Decorator for handling errors in bot handlers.
    Logs errors and sends user-friendly messages.
    
    Args:
        func: Handler function to wrap
    
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> Any:
        try:
            return await func(update, context, *args, **kwargs)
        
        except TelegramError as e:
            # Telegram-specific errors
            logger.error(f"Telegram error in {func.__name__}: {e}", exc_info=True)
            
            user_id = update.effective_user.id if update.effective_user else None
            
            await log_to_telegram(
                message=f"Telegram error in {func.__name__}: {str(e)}",
                level="ERROR",
                module=func.__module__,
                user_id=user_id,
                error_details=traceback.format_exc()
            )
            
            # Try to notify user
            try:
                if update.effective_message:
                    await update.effective_message.reply_text(
                        format_error_message(
                            "A communication error occurred with Telegram.",
                            "Please try again in a moment."
                        ),
                        parse_mode='HTML'
                    )
            except Exception:
                pass  # If we can't send message, just log it
        
        except Exception as e:
            # General errors
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            user_id = update.effective_user.id if update.effective_user else None
            
            await log_to_telegram(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                level="ERROR",
                module=func.__module__,
                user_id=user_id,
                error_details=traceback.format_exc()
            )
            
            # Try to notify user
            try:
                if update.effective_message:
                    await update.effective_message.reply_text(
                        format_error_message(
                            "An unexpected error occurred.",
                            "Our team has been notified. Please try again later."
                        ),
                        parse_mode='HTML'
                    )
            except Exception:
                pass
    
    return wrapper


def api_error_handler(func: Callable) -> Callable:
    """
    Decorator for handling API-related errors.
    
    Args:
        func: API function to wrap
    
    Returns:
        Wrapped function with API error handling
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        
        except NetworkError as e:
            logger.error(f"Network error in {func.__name__}: {e}")
            await log_to_telegram(
                message=f"Network error in {func.__name__}: {str(e)}",
                level="ERROR",
                module=func.__module__
            )
            raise APINetworkError(f"Network error: {str(e)}")
        
        except TimedOut as e:
            logger.error(f"Timeout in {func.__name__}: {e}")
            await log_to_telegram(
                message=f"Timeout in {func.__name__}: {str(e)}",
                level="WARNING",
                module=func.__module__
            )
            raise APITimeoutError(f"Request timed out: {str(e)}")
        
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {e}", exc_info=True)
            await log_to_telegram(
                message=f"API error in {func.__name__}: {str(e)}",
                level="ERROR",
                module=func.__module__,
                error_details=traceback.format_exc()
            )
            raise
    
    return wrapper


class BotError(Exception):
    """Base exception for bot errors."""
    pass


class APIError(BotError):
    """Base exception for API errors."""
    pass


class APINetworkError(APIError):
    """Network-related API error."""
    pass


class APITimeoutError(APIError):
    """Timeout API error."""
    pass


class APIAuthenticationError(APIError):
    """Authentication-related API error."""
    pass


class APIRateLimitError(APIError):
    """Rate limit API error."""
    pass


class ValidationError(BotError):
    """Input validation error."""
    pass


class InsufficientBalanceError(BotError):
    """Insufficient balance error."""
    pass


class PositionNotFoundError(BotError):
    """Position not found error."""
    pass


def handle_api_response(response: dict, context: str = "") -> dict:
    """
    Handle API response and raise appropriate errors.
    
    Args:
        response: API response dictionary
        context: Context for error messages
    
    Returns:
        Response data if successful
    
    Raises:
        APIError: If API returns an error
    """
    if not response:
        raise APIError(f"Empty response from API{': ' + context if context else ''}")
    
    # Check for error in response
    if response.get('success') is False or 'error' in response:
        error_msg = response.get('error', {})
        
        if isinstance(error_msg, dict):
            error_code = error_msg.get('code', 'unknown')
            error_message = error_msg.get('message', 'Unknown error')
        else:
            error_code = 'unknown'
            error_message = str(error_msg)
        
        # Handle specific error codes
        if error_code == 'authentication_error':
            raise APIAuthenticationError(f"Authentication failed: {error_message}")
        elif error_code == 'rate_limit_exceeded':
            raise APIRateLimitError(f"Rate limit exceeded: {error_message}")
        elif error_code == 'insufficient_balance':
            raise InsufficientBalanceError(f"Insufficient balance: {error_message}")
        else:
            raise APIError(f"API error ({error_code}): {error_message}")
    
    return response


async def global_error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler for the bot application.
    Catches all unhandled errors.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        # Log the error
        logger.error("Unhandled exception:", exc_info=context.error)
        
        # Get user ID if available
        user_id = None
        if update and update.effective_user:
            user_id = update.effective_user.id
        
        # Log to Telegram
        await log_to_telegram(
            message=f"Unhandled exception: {str(context.error)}",
            level="CRITICAL",
            module="global_error_handler",
            user_id=user_id,
            error_details=traceback.format_exc()
        )
        
        # Try to notify user
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    format_error_message(
                        "An unexpected error occurred.",
                        "Our team has been notified. Please try again later."
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to send error message to user: {e}")
    
    except Exception as e:
        # Last resort logging
        logger.critical(f"Error in global error handler: {e}", exc_info=True)


if __name__ == "__main__":
    # Test error handlers
    @error_handler
    async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        raise ValueError("Test error")
    
    @api_error_handler
    async def test_api():
        raise APINetworkError("Test network error")
    
    print("Error handlers defined successfully!")
  
