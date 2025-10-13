"""
Centralized error handling utilities.
Custom exceptions and error formatting for user display.
"""

from typing import Optional, Dict, Any
from enum import Enum

from logger import logger


class ErrorType(str, Enum):
    """Error type categories."""
    VALIDATION = "validation"
    API = "api"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    NETWORK = "network"
    UNKNOWN = "unknown"


class TradingBotError(Exception):
    """Base exception for trading bot errors."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize trading bot error.
        
        Args:
            message: Error message
            error_type: Type of error
            details: Additional error details
        """
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)
        
        logger.error(
            f"[TradingBotError] {error_type.value}: {message} | Details: {details}"
        )


class ValidationError(TradingBotError):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            details: Additional details
        """
        error_details = details or {}
        if field:
            error_details['field'] = field
        
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION,
            details=error_details
        )


class DeltaAPIError(TradingBotError):
    """Exception for Delta Exchange API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None
    ):
        """
        Initialize Delta API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_data: API response data
        """
        details = {}
        if status_code:
            details['status_code'] = status_code
        if response_data:
            details['response'] = response_data
        
        super().__init__(
            message=message,
            error_type=ErrorType.API,
            details=details
        )


class InsufficientBalanceError(TradingBotError):
    """Exception for insufficient balance errors."""
    
    def __init__(
        self,
        message: str,
        required: Optional[float] = None,
        available: Optional[float] = None
    ):
        """
        Initialize insufficient balance error.
        
        Args:
            message: Error message
            required: Required balance
            available: Available balance
        """
        details = {}
        if required is not None:
            details['required'] = required
        if available is not None:
            details['available'] = available
        
        super().__init__(
            message=message,
            error_type=ErrorType.INSUFFICIENT_BALANCE,
            details=details
        )


class DatabaseError(TradingBotError):
    """Exception for database errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict] = None):
        """
        Initialize database error.
        
        Args:
            message: Error message
            operation: Database operation that failed
            details: Additional details
        """
        error_details = details or {}
        if operation:
            error_details['operation'] = operation
        
        super().__init__(
            message=message,
            error_type=ErrorType.DATABASE,
            details=error_details
        )


class AuthenticationError(TradingBotError):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            details: Additional details
        """
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHENTICATION,
            details=details or {}
        )


class NetworkError(TradingBotError):
    """Exception for network errors."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        """
        Initialize network error.
        
        Args:
            message: Error message
            details: Additional details
        """
        super().__init__(
            message=message,
            error_type=ErrorType.NETWORK,
            details=details or {}
        )


def format_error_for_user(error: Exception) -> str:
    """
    Format error message for user display.
    
    Args:
        error: Exception to format
    
    Returns:
        User-friendly error message
    """
    try:
        if isinstance(error, ValidationError):
            field = error.details.get('field', '')
            field_text = f" in {field}" if field else ""
            return f"❌ Validation Error{field_text}: {error.message}"
        
        elif isinstance(error, DeltaAPIError):
            status = error.details.get('status_code', '')
            status_text = f" (Status: {status})" if status else ""
            return f"❌ API Error{status_text}: {error.message}"
        
        elif isinstance(error, InsufficientBalanceError):
            required = error.details.get('required')
            available = error.details.get('available')
            if required and available:
                return (
                    f"❌ Insufficient Balance: {error.message}\n"
                    f"Required: ${required:.2f}\n"
                    f"Available: ${available:.2f}"
                )
            return f"❌ Insufficient Balance: {error.message}"
        
        elif isinstance(error, DatabaseError):
            operation = error.details.get('operation', '')
            op_text = f" during {operation}" if operation else ""
            return f"❌ Database Error{op_text}: {error.message}"
        
        elif isinstance(error, AuthenticationError):
            return f"❌ Authentication Error: {error.message}"
        
        elif isinstance(error, NetworkError):
            return f"❌ Network Error: {error.message}\nPlease check your connection and try again."
        
        elif isinstance(error, TradingBotError):
            return f"❌ Error: {error.message}"
        
        else:
            return f"❌ An unexpected error occurred: {str(error)}"
        
    except Exception as e:
        logger.error(f"[error_handler.format_error_for_user] Error formatting: {e}")
        return f"❌ An error occurred: {str(error)}"


def log_error_with_context(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log error with additional context.
    
    Args:
        error: Exception to log
        context: Additional context information
    """
    try:
        error_info = {
            'type': type(error).__name__,
            'message': str(error)
        }
        
        if isinstance(error, TradingBotError):
            error_info['error_type'] = error.error_type.value
            error_info['details'] = error.details
        
        if context:
            error_info['context'] = context
        
        logger.error(f"[error_handler.log_error_with_context] {error_info}")
        
    except Exception as e:
        logger.error(f"[error_handler.log_error_with_context] Failed to log error: {e}")


def handle_api_error(response_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract and format API error message from response.
    
    Args:
        response_data: API response dictionary
    
    Returns:
        Error message or None
    """
    try:
        if not response_data:
            return "Unknown API error"
        
        # Delta Exchange error format
        if 'error' in response_data:
            error_obj = response_data['error']
            if isinstance(error_obj, dict):
                return error_obj.get('message', 'Unknown API error')
            return str(error_obj)
        
        # Check for success flag
        if not response_data.get('success', True):
            return response_data.get('message', 'API request failed')
        
        return None
        
    except Exception as e:
        logger.error(f"[error_handler.handle_api_error] Error parsing API error: {e}")
        return "Error parsing API response"


def create_error_response(
    error: Exception,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response dictionary.
    
    Args:
        error: Exception to format
        include_details: Whether to include detailed error info
    
    Returns:
        Error response dictionary
    """
    try:
        response = {
            'success': False,
            'error': str(error),
            'error_type': 'unknown'
        }
        
        if isinstance(error, TradingBotError):
            response['error_type'] = error.error_type.value
            if include_details and error.details:
                response['details'] = error.details
        
        return response
        
    except Exception as e:
        logger.error(f"[error_handler.create_error_response] Error creating response: {e}")
        return {
            'success': False,
            'error': 'An unexpected error occurred',
            'error_type': 'unknown'
        }


if __name__ == "__main__":
    # Test error handling
    print("Testing error handlers...")
    
    # Test validation error
    try:
        raise ValidationError("Invalid lot size", field="lot_size")
    except ValidationError as e:
        formatted = format_error_for_user(e)
        print(f"✅ Validation error: {formatted}")
    
    # Test API error
    try:
        raise DeltaAPIError("Order placement failed", status_code=400)
    except DeltaAPIError as e:
        formatted = format_error_for_user(e)
        print(f"✅ API error: {formatted}")
    
    # Test insufficient balance error
    try:
        raise InsufficientBalanceError(
            "Not enough funds",
            required=1000.0,
            available=500.0
        )
    except InsufficientBalanceError as e:
        formatted = format_error_for_user(e)
        print(f"✅ Insufficient balance: {formatted}")
    
    # Test error response creation
    error = ValidationError("Test error")
    response = create_error_response(error, include_details=True)
    print(f"✅ Error response: {response}")
    
    print("\n✅ Error handler tests completed!")
  
