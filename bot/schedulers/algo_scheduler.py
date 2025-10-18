"""
Background scheduler for auto trade execution.
"""

import asyncio
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.operations.algo_setup_ops import get_all_active_algo_setups
from database.operations.manual_trade_preset_ops import get_manual_trade_preset
from database.operations.api_ops import get_decrypted_api_credential
from database.operations.strategy_ops import get_strategy_preset_by_id
from delta.client import DeltaClient
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class AlgoScheduler:
    """Background scheduler for automated trade execution."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=IST)
        
    def start(self):
        """Start the scheduler."""
        # Check every minute for due executions
        self.scheduler.add_job(
            self.check_and_execute,
            'cron',
            minute='*',  # Every minute
            id='algo_check'
        )
        self.scheduler.start()
        logger.info("✅ Algo scheduler started")
    
    async def check_and_execute(self):
        """Check for algo setups that need execution."""
        try:
            now = datetime.now(IST)
            current_time = now.strftime('%H:%M')
            
            # Get all active algo setups
            setups = await get_all_active_algo_setups()
            
            for setup in setups:
                # Check if execution time matches
                if setup['execution_time'] == current_time:
                    logger.info(f"⏰ Executing algo setup {setup['id']} at {current_time}")
                    await self.execute_algo_trade(setup)
        
        except Exception as e:
            logger.error(f"Error in algo scheduler: {e}", exc_info=True)
    
    async def execute_algo_trade(self, setup: dict):
        """
        Execute algo trade - THIS IS WHERE STRIKE SELECTION HAPPENS!
        
        🔴 SPOT PRICE IS FETCHED HERE (AT EXECUTION TIME)
        """
        try:
            # Load preset
            preset = await get_manual_trade_preset(setup['manual_preset_id'])
            if not preset:
                logger.error(f"Preset not found for setup {setup['id']}")
                return
            
            # Load API credentials
            credentials = await get_decrypted_api_credential(preset['api_credential_id'])
            if not credentials:
                logger.error("Failed to decrypt API credentials")
                return
            
            api_key, api_secret = credentials
            
            # Load strategy
            strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
            if not strategy:
                logger.error("Strategy not found")
                return
            
            # Initialize Delta client
            client = DeltaClient(api_key, api_secret)
            
            try:
                # 🔴 GET SPOT PRICE (THIS MOMENT - EXECUTION TIME!)
                spot_price = await client.get_spot_price(strategy['asset'])
                
                # 🔴 CALCULATE STRIKES BASED ON CURRENT SPOT
                if preset['strategy_type'] == 'straddle':
                    # Calculate ATM strike
                    strike_increment = 100 if strategy['asset'] == 'BTC' else 10
                    atm_strike = round(spot_price / strike_increment) * strike_increment
                    
                    # Find CE and PE at ATM
                    products = await client.get_products(contract_types='call_options,put_options')
                    # ... (same logic as manual_trade_handler.py)
                
                elif preset['strategy_type'] == 'strangle':
                    # Calculate OTM strikes
                    # ... (same logic as manual_trade_handler.py)
                
                # 🔴 PLACE ORDERS WITH FRESH STRIKES
                # ... (execute trade using calculated strikes)
                
            finally:
                await client.close()
        
        except Exception as e:
            logger.error(f"Failed to execute algo trade: {e}", exc_info=True)


# Global instance
algo_scheduler = AlgoScheduler()
              
