"""
Validation modules for bot inputs and authorization.
"""

from .user_validator import (
    is_user_authorized,
    check_user_authorization,
    get_user_info
)
from .input_validator import (
    validate_percentage,
    validate_price,
    validate_lot_size,
    validate_time_format,
    validate_expiry_code,
    validate_atm_offset,
    validate_otm_value,
    ValidationResult
)
from .api_validator import (
    validate_api_credentials,
    test_api_connection,
    check_api_permissions
)
from .trade_validator import (
    validate_strategy_parameters,
    validate_strike_price,
    check_sufficient_balance,
    validate_trade_request
)

__all__ = [
    # User validation
    'is_user_authorized',
    'check_user_authorization',
    'get_user_info',
    
    # Input validation
    'validate_percentage',
    'validate_price',
    'validate_lot_size',
    'validate_time_format',
    'validate_expiry_code',
    'validate_atm_offset',
    'validate_otm_value',
    'ValidationResult',
    
    # API validation
    'validate_api_credentials',
    'test_api_connection',
    'check_api_permissions',
    
    # Trade validation
    'validate_strategy_parameters',
    'validate_strike_price',
    'check_sufficient_balance',
    'validate_trade_request'
]
