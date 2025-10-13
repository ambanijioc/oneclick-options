"""
Database CRUD operations.
"""

from .api_ops import (
    create_api_credential,
    get_api_credentials,
    get_api_credential_by_id,
    update_api_credential,
    delete_api_credential,
    get_decrypted_api_credential
)
from .strategy_ops import (
    create_strategy_preset,
    get_strategy_presets,
    get_strategy_preset_by_id,
    update_strategy_preset,
    delete_strategy_preset,
    get_strategy_presets_by_type
)
from .auto_execution_ops import (
    create_auto_execution,
    get_auto_executions,
    get_auto_execution_by_id,
    update_auto_execution,
    delete_auto_execution,
    get_enabled_auto_executions,
    update_execution_status
)
from .trade_ops import (
    create_trade_history,
    get_trade_history,
    get_trade_by_id,
    update_trade_history,
    close_trade,
    get_recent_trades,
    get_trades_summary
)
from .user_ops import (
    create_user_settings,
    get_user_settings,
    update_user_settings,
    increment_user_trade_count,
    can_user_trade_today
)

__all__ = [
    # API operations
    'create_api_credential',
    'get_api_credentials',
    'get_api_credential_by_id',
    'update_api_credential',
    'delete_api_credential',
    'get_decrypted_api_credential',
    
    # Strategy operations
    'create_strategy_preset',
    'get_strategy_presets',
    'get_strategy_preset_by_id',
    'update_strategy_preset',
    'delete_strategy_preset',
    'get_strategy_presets_by_type',
    
    # Auto execution operations
    'create_auto_execution',
    'get_auto_executions',
    'get_auto_execution_by_id',
    'update_auto_execution',
    'delete_auto_execution',
    'get_enabled_auto_executions',
    'update_execution_status',
    
    # Trade operations
    'create_trade_history',
    'get_trade_history',
    'get_trade_by_id',
    'update_trade_history',
    'close_trade',
    'get_recent_trades',
    'get_trades_summary',
    
    # User operations
    'create_user_settings',
    'get_user_settings',
    'update_user_settings',
    'increment_user_trade_count',
    'can_user_trade_today'
]
