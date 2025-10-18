"""
MOVE Options Auto-Trade Scheduler.
Checks every minute for scheduled trades and executes them automatically.
"""

import asyncio
from datetime import datetime
import pytz
from typing import Dict, Any

from bot.utils.logger import setup_logger, log_to_telegram
from bot.executors.move_executor import MoveTradeExecutor
from database.operations.move_auto_trade_ops import (
    get_all_active_move_schedules,
    update_move_schedule_last_execution
)
from database.operations.move_trade_preset_ops import get_move_trade_preset_by_id
from database.operations.move_strategy_ops import get_move_strategy
from database.operations.api_ops import get_decrypted_api_credential, get_api_credential_by_id
from delta.client import DeltaClient

logger = setup_logger(__name__)

IST = pytz.timezone('Asia/Kolkata')


class MoveAutoTradeScheduler:
    """
    Scheduler for automatic MOVE trade execution.
    Runs as a background task checking schedules every minute.
    """
    
    def __init__(self, telegram_bot=None):
        """
        Initialize scheduler.
        
        Args:
            telegram_bot: Telegram Application instance for sending notifications
        """
        self.telegram_bot = telegram_bot
        self.running = False
        self.scheduler_task = None
        logger.info("MoveAutoTradeScheduler initialized")
    
    async def check_and_execute_schedules(self):
        """Check all active schedules and execute due trades."""
        try:
            # Get current time in IST
            now_ist = datetime.now(IST)
            current_time_str = now_ist.strftime("%I:%M %p IST")
            current_hour_minute = now_ist.strftime("%I:%M %p")
            
            logger.debug(f"Checking schedules at {current_time_str}")
            
            # Get all active schedules
            schedules = await get_all_active_move_schedules()
            
            if not schedules:
                return
            
            logger.debug(f"Found {len(schedules)} active schedules")
            
            # Check each schedule
            for schedule in schedules:
                try:
                    # Parse schedule time (format: "09:30 AM IST")
                    schedule_time = schedule.get('execution_time', '').replace(' IST', '').strip()
                    
                    # Match current time with schedule time
                    if schedule_time == current_hour_minute:
                        logger.info(f"⏰ Schedule matched: {schedule.get('preset_name')} at {schedule_time}")
                        
                        # Execute the trade
                        await self.execute_scheduled_trade(schedule)
                        
                except Exception as e:
                    logger.error(f"Error processing schedule {schedule.get('_id')}: {e}", exc_info=True)
                    # Continue with other schedules
                    continue
        
        except Exception as e:
            logger.error(f"Error in check_and_execute_schedules: {e}", exc_info=True)
    
    async def execute_scheduled_trade(self, schedule: Dict[str, Any]):
        """
        Execute a scheduled MOVE trade.
        
        Args:
            schedule: Schedule document from database
        """
        schedule_id = schedule.get('_id')
        user_id = schedule.get('user_id')
        preset_id = schedule.get('preset_id')
        preset_name = schedule.get('preset_name', 'Unknown')
        
        try:
            logger.info(f"🤖 Auto-executing: {preset_name} for user {user_id}")
            
            # Send starting notification
            if self.telegram_bot:
                await self.send_telegram_notification(
                    user_id,
                    f"🤖 <b>Auto Trade Executing</b>\n\n"
                    f"Preset: {preset_name}\n"
                    f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n\n"
                    f"⏳ Placing orders..."
                )
            
            # Get preset
            preset = await get_move_trade_preset_by_id(preset_id)
            
            if not preset:
                raise Exception(f"Preset {preset_id} not found")
            
            # Get strategy
            strategy = await get_move_strategy(preset['strategy_id'])
            
            if not strategy:
                raise Exception(f"Strategy {preset['strategy_id']} not found")
            
            # Handle dict vs Pydantic model
            if isinstance(strategy, dict):
                asset = strategy.get('asset')
                direction = strategy.get('direction')
                lot_size = strategy.get('lot_size')
                atm_offset = strategy.get('atm_offset', 0)
                sl_trigger = strategy.get('stop_loss_trigger')
                sl_limit = strategy.get('stop_loss_limit')
                target_trigger = strategy.get('target_trigger')
                target_limit = strategy.get('target_limit')
            else:
                asset = strategy.asset
                direction = strategy.direction
                lot_size = strategy.lot_size
                atm_offset = strategy.atm_offset
                sl_trigger = strategy.stop_loss_trigger
                sl_limit = strategy.stop_loss_limit
                target_trigger = strategy.target_trigger
                target_limit = strategy.target_limit
            
            # Get API credentials
            credentials = await get_decrypted_api_credential(preset['api_id'])
            
            if not credentials:
                raise Exception("Failed to decrypt API credentials")
            
            api_key, api_secret = credentials
            
            # Create Delta client
            client = DeltaClient(api_key, api_secret)
            
            try:
                # Create executor and execute trade
                executor = MoveTradeExecutor(client)
                
                result = await executor.execute_move_trade(
                    asset=asset,
                    direction=direction,
                    lot_size=lot_size,
                    atm_offset=atm_offset,
                    stop_loss_trigger=sl_trigger,
                    stop_loss_limit=sl_limit,
                    target_trigger=target_trigger,
                    target_limit=target_limit
                )
                
                # Update last execution time
                await update_move_schedule_last_execution(schedule_id, datetime.now(IST))
                
                # Send result notification
                if result['success']:
                    product = result['product']
                    entry_price = result['entry_price']
                    
                    message = (
                        f"✅ <b>Auto Trade Executed Successfully!</b>\n\n"
                        f"<b>Preset:</b> {preset_name}\n"
                        f"<b>Contract:</b> {product['symbol']}\n"
                        f"<b>Direction:</b> {direction.title()}\n"
                        f"<b>Lot Size:</b> {lot_size}\n\n"
                        f"<b>💰 Entry Price:</b> ${entry_price:.2f}\n"
                    )
                    
                    if result.get('sl_trigger'):
                        message += (
                            f"<b>🛑 Stop Loss:</b>\n"
                            f"  Trigger: ${result['sl_trigger']:.2f}\n"
                            f"  Limit: ${result['sl_limit']:.2f}\n"
                        )
                    
                    if result.get('target_trigger'):
                        message += (
                            f"<b>🎯 Target:</b>\n"
                            f"  Trigger: ${result['target_trigger']:.2f}\n"
                            f"  Limit: ${result['target_limit']:.2f}\n"
                        )
                    
                    message += "\n✅ All orders placed automatically!"
                    
                    if self.telegram_bot:
                        await self.send_telegram_notification(user_id, message)
                    
                    logger.info(f"✅ Auto trade successful: {preset_name}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    
                    if self.telegram_bot:
                        await self.send_telegram_notification(
                            user_id,
                            f"❌ <b>Auto Trade Failed</b>\n\n"
                            f"Preset: {preset_name}\n"
                            f"Error: {error_msg}\n\n"
                            f"Please check your account."
                        )
                    
                    logger.error(f"❌ Auto trade failed: {error_msg}")
            
            finally:
                await client.close()
        
        except Exception as e:
            logger.error(f"Error executing scheduled trade: {e}", exc_info=True)
            
            # Send error notification
            if self.telegram_bot:
                await self.send_telegram_notification(
                    user_id,
                    f"❌ <b>Auto Trade Error</b>\n\n"
                    f"Preset: {preset_name}\n"
                    f"Error: {str(e)[:200]}\n\n"
                    f"Schedule remains active. Please check logs."
                )
    
    async def send_telegram_notification(self, user_id: int, message: str):
        """Send Telegram notification to user."""
        try:
            await self.telegram_bot.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    async def scheduler_loop(self):
        """Main scheduler loop - runs every minute."""
        logger.info("🤖 MOVE Auto Trade Scheduler started")
        
        # Send startup notification (to all users with active schedules)
        await log_to_telegram(
            f"🤖 <b>Auto Trade Scheduler Started</b>\n"
            f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n"
            f"Status: Active\n"
            f"Checking every minute..."
        )
        
        while self.running:
            try:
                # Check and execute schedules
                await self.check_and_execute_schedules()
                
                # Wait 60 seconds
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self.scheduler_loop())
        logger.info("✅ Scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Scheduler stopped")
        
        await log_to_telegram(
            f"🛑 <b>Auto Trade Scheduler Stopped</b>\n"
            f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}"
        )


# Global scheduler instance
move_scheduler = None


def get_move_scheduler(telegram_bot=None) -> MoveAutoTradeScheduler:
    """Get or create the global scheduler instance."""
    global move_scheduler
    
    if move_scheduler is None:
        move_scheduler = MoveAutoTradeScheduler(telegram_bot)
    
    return move_scheduler
      
