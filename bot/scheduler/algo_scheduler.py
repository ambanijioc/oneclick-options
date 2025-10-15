"""
Algo trading scheduler with IST timezone support.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set
import pytz

from bot.utils.logger import setup_logger
from database.operations.algo_setup_ops import (
    get_all_active_algo_setups,
    update_algo_execution
)
from database.operations.manual_trade_preset_ops import get_manual_trade_preset
from database.operations.api_ops import get_api_credential_by_id, get_decrypted_api_credential
from database.operations.strategy_ops import get_strategy_preset_by_id
from delta.client import DeltaClient

logger = setup_logger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Track pending executions (setup_id -> task)
pending_executions: Dict[str, asyncio.Task] = {}

# Track which setups are already scheduled for current minute
scheduled_setups: Set[str] = set()


async def execute_algo_trade(setup_id: str, user_id: int, bot_application):
    """Execute algo trade for a setup."""
    try:
        logger.info(f"Executing algo trade for setup {setup_id}")
        
        # Get algo setup
        from database.operations.algo_setup_ops import get_algo_setup
        setup = await get_algo_setup(setup_id)
        
        if not setup or not setup.get('is_active'):
            logger.warning(f"Setup {setup_id} not found or inactive")
            return
        
        # Get manual preset
        preset = await get_manual_trade_preset(setup['manual_preset_id'])
        if not preset:
            logger.error(f"Manual preset not found for setup {setup_id}")
            await update_algo_execution(setup_id, 'failed', {'error': 'Manual preset not found'})
            return
        
        # Get API credentials
        api = await get_api_credential_by_id(preset['api_credential_id'])
        if not api:
            logger.error(f"API credential not found for setup {setup_id}")
            await update_algo_execution(setup_id, 'failed', {'error': 'API credential not found'})
            return
        
        credentials = await decrypt_api_credentials(preset['api_credential_id'])
        if not credentials:
            logger.error(f"Failed to decrypt credentials for setup {setup_id}")
            await update_algo_execution(setup_id, 'failed', {'error': 'Failed to decrypt credentials'})
            return
        
        # Get strategy
        strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
        if not strategy:
            logger.error(f"Strategy not found for setup {setup_id}")
            await update_algo_execution(setup_id, 'failed', {'error': 'Strategy not found'})
            return
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Get spot price
            ticker_response = await client.get_ticker(strategy['asset'])
            if not ticker_response.get('success'):
                raise Exception(f"Failed to fetch spot price: {ticker_response.get('error', {}).get('message')}")
            
            spot_price = float(ticker_response['result']['spot_price'])
            
            # Get options
            products_response = await client.get_products(contract_types='call_options,put_options')
            if not products_response.get('success'):
                raise Exception(f"Failed to fetch options: {products_response.get('error', {}).get('message')}")
            
            products = products_response['result']
            filtered_options = [
                p for p in products
                if strategy['asset'] in p.get('symbol', '') and p.get('state') == 'live'
            ]
            
            # Calculate strikes based on strategy type
            if preset['strategy_type'] == 'straddle':
                atm_offset = strategy.get('atm_offset', 0)
                target_strike = spot_price + atm_offset
                strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
                atm_strike = min(strikes, key=lambda x: abs(x - target_strike))
                
                ce_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == atm_strike and 'C' in p['symbol']), None)
                pe_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == atm_strike and 'P' in p['symbol']), None)
                
                if not ce_option or not pe_option:
                    raise Exception("Could not find matching options")
                
                ce_symbol = ce_option['symbol']
                pe_symbol = pe_option['symbol']
            
            else:  # strangle
                otm_selection = strategy.get('otm_selection', {})
                otm_type = otm_selection.get('type', 'percentage')
                otm_value = otm_selection.get('value', 0)
                
                strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
                
                if otm_type == 'percentage':
                    offset = spot_price * (otm_value / 100)
                    ce_target = spot_price + offset
                    pe_target = spot_price - offset
                else:
                    atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
                    atm_index = strikes.index(atm_strike)
                    num_strikes = int(otm_value)
                    ce_target = strikes[min(atm_index + num_strikes, len(strikes) - 1)]
                    pe_target = strikes[max(atm_index - num_strikes, 0)]
                
                ce_strike = min(strikes, key=lambda x: abs(x - ce_target))
                pe_strike = min(strikes, key=lambda x: abs(x - pe_target))
                
                ce_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == ce_strike and 'C' in p['symbol']), None)
                pe_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == pe_strike and 'P' in p['symbol']), None)
                
                if not ce_option or not pe_option:
                    raise Exception("Could not find matching options")
                
                ce_symbol = ce_option['symbol']
                pe_symbol = pe_option['symbol']
            
            # Execute orders
            side = 'buy' if strategy['direction'] == 'long' else 'sell'
            
            ce_order = await client.place_order(
                product_symbol=ce_symbol,
                size=strategy['lot_size'],
                side=side,
                order_type='market'
            )
            
            if not ce_order.get('success'):
                raise Exception(f"CE order failed: {ce_order.get('error', {}).get('message')}")
            
            pe_order = await client.place_order(
                product_symbol=pe_symbol,
                size=strategy['lot_size'],
                side=side,
                order_type='market'
            )
            
            if not pe_order.get('success'):
                raise Exception(f"PE order failed: {pe_order.get('error', {}).get('message')}")
            
            # Update execution details
            details = {
                'spot_price': spot_price,
                'ce_symbol': ce_symbol,
                'pe_symbol': pe_symbol,
                'ce_order_id': ce_order['result']['id'],
                'pe_order_id': pe_order['result']['id'],
                'direction': strategy['direction'],
                'lot_size': strategy['lot_size']
            }
            
            await update_algo_execution(setup_id, 'success', details)
            logger.info(f"Algo trade executed successfully for setup {setup_id}")
            
            # Send notification to user
            try:
                await bot_application.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ <b>Algo Trade Executed</b>\n\n"
                         f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n"
                         f"Preset: {preset.get('preset_name', 'Unknown')}\n"
                         f"CE: {ce_symbol}\n"
                         f"PE: {pe_symbol}\n"
                         f"Direction: {strategy['direction'].title()}\n"
                         f"Lot Size: {strategy['lot_size']}",
                    parse_mode='HTML'
                )
            except Exception as notify_error:
                logger.error(f"Failed to send notification: {notify_error}")
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Algo trade execution failed for setup {setup_id}: {e}", exc_info=True)
        await update_algo_execution(setup_id, 'failed', {'error': str(e)})
        
        # Try to send error notification
        try:
            await bot_application.bot.send_message(
                chat_id=user_id,
                text=f"❌ <b>Algo Trade Failed</b>\n\n"
                     f"Time: {datetime.now(IST).strftime('%I:%M %p IST')}\n"
                     f"Error: {str(e)[:200]}",
                parse_mode='HTML'
            )
        except Exception:
            pass


async def schedule_algo_execution(setup: dict, bot_application):
    """Schedule algo execution 5 minutes before target time."""
    setup_id = setup['id']
    
    # Parse execution time (format: "HH:MM")
    exec_hour, exec_minute = map(int, setup['execution_time'].split(':'))
    
    # Get current IST time
    now_ist = datetime.now(IST)
    
    # Calculate target execution time
    target_time = now_ist.replace(hour=exec_hour, minute=exec_minute, second=0, microsecond=0)
    
    # If target time has passed today, schedule for tomorrow
    if target_time <= now_ist:
        target_time += timedelta(days=1)
    
    # Calculate pre-activation time (5 minutes before)
    pre_activation_time = target_time - timedelta(minutes=5)
    
    # Calculate wait time
    wait_seconds = (pre_activation_time - now_ist).total_seconds()
    
    if wait_seconds > 0:
        logger.info(f"Scheduling setup {setup_id} to pre-activate in {wait_seconds:.0f} seconds at {pre_activation_time.strftime('%I:%M %p IST')}")
        
        # Wait until pre-activation
        await asyncio.sleep(wait_seconds)
        
        logger.info(f"Pre-activating setup {setup_id} - 5 minutes to execution")
        
        # Wait final 5 minutes until exact execution time
        final_wait = (target_time - datetime.now(IST)).total_seconds()
        if final_wait > 0:
            await asyncio.sleep(final_wait)
        
        # Execute trade
        await execute_algo_trade(setup_id, setup['user_id'], bot_application)


async def start_algo_scheduler(bot_application):
    """Start the algo scheduler."""
    logger.info("Starting algo scheduler...")
    
    while True:
        try:
            # Get all active setups
            setups = await get_all_active_algo_setups()
            
            for setup in setups:
                setup_id = setup['id']
                
                # Skip if already scheduled
                if setup_id in pending_executions:
                    continue
                
                # Create and store task
                task = asyncio.create_task(schedule_algo_execution(setup, bot_application))
                pending_executions[setup_id] = task
                logger.info(f"Scheduled algo setup {setup_id}")
            
            # Clean up completed tasks
            completed = [sid for sid, task in pending_executions.items() if task.done()]
            for sid in completed:
                del pending_executions[sid]
            
            # Check every 60 seconds
            await asyncio.sleep(60)
        
        except Exception as e:
            logger.error(f"Error in algo scheduler: {e}", exc_info=True)
            await asyncio.sleep(60)
      
