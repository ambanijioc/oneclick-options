"""
Automated trade execution.
"""

from typing import Dict, Any

from bot.utils.logger import setup_logger
from .manual_executor import execute_manual_strategy

logger = setup_logger(__name__)


async def execute_auto_strategy(
    api_key: str,
    api_secret: str,
    preset: Any,
    user_id: int
) -> Dict[str, Any]:
    """
    Execute an automated strategy trade.
    Uses the same logic as manual execution.
    
    Args:
        api_key: Delta Exchange API key
        api_secret: Delta Exchange API secret
        preset: Strategy preset
        user_id: User ID
    
    Returns:
        Dictionary with execution result
    """
    try:
        logger.info(f"Executing auto strategy: {preset.name} for user {user_id}")
        
        # Use manual executor for actual execution
        # The difference is in how it's triggered (scheduled vs manual)
        result = await execute_manual_strategy(
            api_key=api_key,
            api_secret=api_secret,
            preset=preset,
            user_id=user_id,
            api_id="auto"  # Mark as auto execution
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to execute auto strategy: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    print("Auto executor module loaded")
  
