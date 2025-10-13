"""
Conversation state management for multi-step user interactions.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from .logger import setup_logger

logger = setup_logger(__name__)


class ConversationState(Enum):
    """Enumeration of conversation states."""
    
    # API Management States
    API_ADD_NAME = "api_add_name"
    API_ADD_DESCRIPTION = "api_add_description"
    API_ADD_KEY = "api_add_key"
    API_ADD_SECRET = "api_add_secret"
    API_EDIT_SELECT = "api_edit_select"
    API_DELETE_CONFIRM = "api_delete_confirm"
    
    # Strategy Management States
    STRATEGY_ADD_NAME = "strategy_add_name"
    STRATEGY_ADD_DESCRIPTION = "strategy_add_description"
    STRATEGY_ADD_ASSET = "strategy_add_asset"
    STRATEGY_ADD_EXPIRY = "strategy_add_expiry"
    STRATEGY_ADD_DIRECTION = "strategy_add_direction"
    STRATEGY_ADD_LOT_SIZE = "strategy_add_lot_size"
    STRATEGY_ADD_SL_TRIGGER = "strategy_add_sl_trigger"
    STRATEGY_ADD_SL_LIMIT = "strategy_add_sl_limit"
    STRATEGY_ADD_TARGET_TRIGGER = "strategy_add_target_trigger"
    STRATEGY_ADD_TARGET_LIMIT = "strategy_add_target_limit"
    STRATEGY_ADD_ATM_OFFSET = "strategy_add_atm_offset"
    STRATEGY_ADD_OTM_TYPE = "strategy_add_otm_type"
    STRATEGY_ADD_OTM_VALUE = "strategy_add_otm_value"
    
    # Order Management States
    ORDER_SELECT_API = "order_select_api"
    ORDER_SELECT_POSITION = "order_select_position"
    ORDER_SL_TRIGGER = "order_sl_trigger"
    ORDER_SL_LIMIT = "order_sl_limit"
    ORDER_TARGET_TRIGGER = "order_target_trigger"
    ORDER_TARGET_LIMIT = "order_target_limit"
    
    # Trade Execution States
    TRADE_SELECT_API = "trade_select_api"
    TRADE_SELECT_STRATEGY_TYPE = "trade_select_strategy_type"
    TRADE_SELECT_PRESET = "trade_select_preset"
    TRADE_CONFIRM = "trade_confirm"
    
    # Auto Execution States
    AUTO_SELECT_API = "auto_select_api"
    AUTO_SELECT_STRATEGY_TYPE = "auto_select_strategy_type"
    AUTO_SELECT_PRESET = "auto_select_preset"
    AUTO_SET_TIME = "auto_set_time"
    AUTO_CONFIRM = "auto_confirm"


class StateManager:
    """
    Manages conversation states for users.
    Stores temporary data during multi-step conversations.
    """
    
    def __init__(self, timeout_minutes: int = 10):
        """
        Initialize state manager.
        
        Args:
            timeout_minutes: Minutes until state expires
        """
        self._states: Dict[int, Dict[str, Any]] = {}
        self._timeout = timedelta(minutes=timeout_minutes)
        self._lock = asyncio.Lock()
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_states())
        
        logger.info(f"StateManager initialized with {timeout_minutes} minute timeout")
    
    async def set_state(
        self,
        user_id: int,
        state: ConversationState,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Set conversation state for a user.
        
        Args:
            user_id: User ID
            state: Conversation state
            data: Additional data to store
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = {}
            
            self._states[user_id].update({
                'state': state,
                'data': data or {},
                'timestamp': datetime.now()
            })
            
            logger.debug(f"Set state for user {user_id}: {state.value}")
    
    async def get_state(self, user_id: int) -> Optional[ConversationState]:
        """
        Get current conversation state for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Current state or None
        """
        async with self._lock:
            user_data = self._states.get(user_id)
            
            if not user_data:
                return None
            
            # Check if expired
            if datetime.now() - user_data['timestamp'] > self._timeout:
                logger.debug(f"State expired for user {user_id}")
                del self._states[user_id]
                return None
            
            return user_data.get('state')
    
    async def get_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get stored data for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Stored data dictionary
        """
        async with self._lock:
            user_data = self._states.get(user_id)
            
            if not user_data:
                return {}
            
            # Check if expired
            if datetime.now() - user_data['timestamp'] > self._timeout:
                logger.debug(f"State expired for user {user_id}")
                del self._states[user_id]
                return {}
            
            return user_data.get('data', {})
    
    async def update_data(self, user_id: int, data: Dict[str, Any]):
        """
        Update stored data for a user.
        
        Args:
            user_id: User ID
            data: Data to update (merged with existing)
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = {
                    'state': None,
                    'data': {},
                    'timestamp': datetime.now()
                }
            
            self._states[user_id]['data'].update(data)
            self._states[user_id]['timestamp'] = datetime.now()
            
            logger.debug(f"Updated data for user {user_id}")
    
    async def clear_state(self, user_id: int):
        """
        Clear conversation state for a user.
        
        Args:
            user_id: User ID
        """
        async with self._lock:
            if user_id in self._states:
                del self._states[user_id]
                logger.debug(f"Cleared state for user {user_id}")
    
    async def has_state(self, user_id: int) -> bool:
        """
        Check if user has an active conversation state.
        
        Args:
            user_id: User ID
        
        Returns:
            True if user has active state
        """
        state = await self.get_state(user_id)
        return state is not None
    
    async def _cleanup_expired_states(self):
        """
        Periodic task to clean up expired states.
        Runs every 5 minutes.
        """
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                async with self._lock:
                    current_time = datetime.now()
                    expired_users = [
                        user_id
                        for user_id, data in self._states.items()
                        if current_time - data['timestamp'] > self._timeout
                    ]
                    
                    for user_id in expired_users:
                        del self._states[user_id]
                    
                    if expired_users:
                        logger.info(f"Cleaned up {len(expired_users)} expired state(s)")
            
            except Exception as e:
                logger.error(f"Error in state cleanup task: {e}")


# Global state manager instance
state_manager = StateManager(timeout_minutes=10)


if __name__ == "__main__":
    # Test state manager
    async def test():
        # Set state
        await state_manager.set_state(
            user_id=12345,
            state=ConversationState.API_ADD_NAME,
            data={'step': 1}
        )
        
        # Get state
        state = await state_manager.get_state(12345)
        print(f"Current state: {state}")
        
        # Update data
        await state_manager.update_data(12345, {'step': 2, 'name': 'Test API'})
        
        # Get data
        data = await state_manager.get_data(12345)
        print(f"Current data: {data}")
        
        # Clear state
        await state_manager.clear_state(12345)
        
        # Check if has state
        has_state = await state_manager.has_state(12345)
        print(f"Has state: {has_state}")
    
    asyncio.run(test())
  
