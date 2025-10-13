"""
Auto trade job execution functions.
"""

from datetime import datetime

from bot.utils.logger import setup_logger, log_to_telegram
from database.operations.auto_execution_ops import (
    get_auto_execution_by_id,
    update_execution_status
)
from database.operations.strategy_ops import get_strategy_preset_by_id
from database.operations.api_ops import get_decrypted_api_credential
from strategies.execution.auto_executor import execute_auto_strategy

logger = setup_logger(__name__)


async def execute_auto_trade(auto_exec_id: str, bot_application):
    """
    Execute an automated trade.
    
    Args:
        auto_exec_id: Auto execution ID
        bot_application: Bot application instance
    """
    try:
        logger.info(f"Executing auto trade: {auto_exec_id}")
        
        # Get auto execution
        auto_exec = await get_auto_execution_by_id(auto_exec_id)
        
        if not auto_exec:
            logger.error(f"Auto execution not found: {auto_exec_id}")
            return
        
        # Check if enabled
        if not auto_exec.enabled:
            logger.info(f"Auto execution disabled, skipping: {auto_exec_id}")
            return
        
        # Get strategy preset
        preset = await get_strategy_preset_by_id(auto_exec.strategy_preset_id)
        
        if not preset:
            logger.error(f"Strategy preset not found: {auto_exec.strategy_preset_id}")
            await update_execution_status(auto_exec_id, "failed: preset not found")
            return
        
        # Get API credentials
        credentials = await get_decrypted_api_credential(auto_exec.api_id)
        
        if not credentials:
            logger.error(f"Failed to decrypt API credentials: {auto_exec.api_id}")
            await update_execution_status(auto_exec_id, "failed: invalid credentials")
            return
        
        api_key, api_secret = credentials
        
        # Execute strategy
        result = await execute_auto_strategy(
            api_key=api_key,
            api_secret=api_secret,
            preset=preset,
            user_id=auto_exec.user_id
        )
        
        if result.get('success'):
            # Update execution status
            await update_execution_status(auto_exec_id, "success", increment_count=True)
            
            # Send notification to user
            message = (
                f"✅ <b>Auto Trade Executed</b>\n\n"
                f"<b>Strategy:</b> {preset.name}\n"
                f"<b>Asset:</b> {preset.asset}\n"
                f"<b>Time:</b> {datetime.now().strftime('%H:%M IST')}\n"
                f"<b>Status:</b> Success\n\n"
                f"<b>Details:</b>\n"
                f"{result.get('message', 'Trade executed successfully')}"
            )
            
            await bot_application.bot.send_message(
                chat_id=auto_exec.user_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"✓ Auto trade executed successfully: {auto_exec_id}")
            
            await log_to_telegram(
                message=f"Auto trade executed: {preset.name}",
                level="INFO",
                module="auto_trade_jobs",
                user_id=auto_exec.user_id
            )
        
        else:
            # Update execution status with error
            error_msg = result.get('error', 'Unknown error')
            await update_execution_status(auto_exec_id, f"failed: {error_msg}")
            
            # Send notification to user
            message = (
                f"❌ <b>Auto Trade Failed</b>\n\n"
                f"<b>Strategy:</b> {preset.name}\n"
                f"<b>Asset:</b> {preset.asset}\n"
                f"<b>Time:</b> {datetime.now().strftime('%H:%M IST')}\n"
                f"<b>Error:</b> {error_msg}\n\n"
                f"Please check your settings and try again."
            )
            
            await bot_application.bot.send_message(
                chat_id=auto_exec.user_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.error(f"Auto trade failed: {auto_exec_id} - {error_msg}")
            
            await log_to_telegram(
                message=f"Auto trade failed: {preset.name} - {error_msg}",
                level="ERROR",
                module="auto_trade_jobs",
                user_id=auto_exec.user_id
            )
    
    except Exception as e:
        logger.error(f"Error executing auto trade {auto_exec_id}: {e}", exc_info=True)
        
        try:
            await update_execution_status(auto_exec_id, f"error: {str(e)}")
            
            await log_to_telegram(
                message=f"Auto trade error: {str(e)}",
                level="ERROR",
                module="auto_trade_jobs",
                error_details=str(e)
            )
        except Exception:
            pass


if __name__ == "__main__":
    print("Auto trade jobs module loaded")
          
