"""
services/sl_monitor_service.py

SL-to-Cost Monitor Service
Monitors straddle/strangle strategies and moves SL to breakeven when one leg closes.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.utils.logger import setup_logger
from delta.client import DeltaClient
from database.operations.api_ops import get_decrypted_api_credential

logger = setup_logger(__name__)

# ✅ GLOBAL REGISTRY - Tracks all active monitors
active_monitors: Dict[str, dict] = {}


async def start_strategy_monitor(
    strategy_id: str,
    user_id: int,
    api_id: str,
    strategy_type: str,
    call_symbol: str,
    put_symbol: str,
    call_entry_price: float,
    put_entry_price: float,
    db: AsyncIOMotorDatabase
):
    """
    Start monitoring a straddle/strangle strategy.
    This is called AFTER successful execution.
    """
    # Check if already monitoring
    if strategy_id in active_monitors:
        logger.warning(f"Strategy {strategy_id} already being monitored")
        return
    
    logger.info(f"🔍 Starting SL monitor for strategy {strategy_id}")
    
    # Store monitor details
    active_monitors[strategy_id] = {
        'user_id': user_id,
        'strategy_type': strategy_type,
        'call_symbol': call_symbol,
        'put_symbol': put_symbol,
        'status': 'running',
        'started_at': datetime.now(),
        'check_count': 0
    }
    
    # Create and start monitor task
    task = asyncio.create_task(
        _monitor_loop(
            strategy_id,
            user_id,
            api_id,
            strategy_type,
            call_symbol,
            put_symbol,
            call_entry_price,
            put_entry_price,
            db
        )
    )
    
    active_monitors[strategy_id]['task'] = task


async def _monitor_loop(
    strategy_id: str,
    user_id: int,
    api_id: str,
    strategy_type: str,
    call_symbol: str,
    put_symbol: str,
    call_entry_price: float,
    put_entry_price: float,
    db: AsyncIOMotorDatabase
):
    """
    Main monitoring loop - checks positions every 5 seconds.
    """
    try:
        # Get API credentials
        credentials = await get_decrypted_api_credential(api_id)
        if not credentials:
            logger.error(f"No credentials for API {api_id}")
            active_monitors[strategy_id]['status'] = 'error'
            return
        
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            while True:
                # Increment check count
                active_monitors[strategy_id]['check_count'] += 1
                check_num = active_monitors[strategy_id]['check_count']
                
                logger.debug(f"Check #{check_num} for {strategy_id}")
                
                # ✅ FETCH CURRENT POSITIONS
                response = await client.get_positions()
                
                if not response.get('success'):
                    logger.warning(f"Failed to fetch positions for {strategy_id}")
                    await asyncio.sleep(10)
                    continue
                
                positions = response.get('result', [])
                
                # ✅ FIND BOTH LEGS
                call_pos = None
                put_pos = None
                
                for pos in positions:
                    symbol = pos.get('product_symbol', '')
                    size = abs(pos.get('size', 0))
                    
                    if symbol == call_symbol and size > 0:
                        call_pos = pos
                        logger.debug(f"CALL position found: size={size}")
                    
                    elif symbol == put_symbol and size > 0:
                        put_pos = pos
                        logger.debug(f"PUT position found: size={size}")
                
                # ✅ DETECTION LOGIC
                
                if call_pos and not put_pos:
                    # 🔴 PUT CLOSED (SL HIT)
                    logger.info(f"🔴 PUT leg SL HIT for {strategy_id}! Moving CALL SL to cost.")
                    active_monitors[strategy_id]['status'] = 'moving_sl'
                    
                    success = await _move_sl_to_cost(client, call_pos, call_entry_price)
                    
                    if success:
                        logger.info(f"✅ Successfully moved CALL SL to {call_entry_price}")
                        active_monitors[strategy_id]['status'] = 'completed'
                    else:
                        logger.error(f"❌ Failed to move CALL SL")
                        active_monitors[strategy_id]['status'] = 'error'
                    
                    break
                
                elif put_pos and not call_pos:
                    # 🔴 CALL CLOSED (SL HIT)
                    logger.info(f"🔴 CALL leg SL HIT for {strategy_id}! Moving PUT SL to cost.")
                    active_monitors[strategy_id]['status'] = 'moving_sl'
                    
                    success = await _move_sl_to_cost(client, put_pos, put_entry_price)
                    
                    if success:
                        logger.info(f"✅ Successfully moved PUT SL to {put_entry_price}")
                        active_monitors[strategy_id]['status'] = 'completed'
                    else:
                        logger.error(f"❌ Failed to move PUT SL")
                        active_monitors[strategy_id]['status'] = 'error'
                    
                    break
                
                elif not call_pos and not put_pos:
                    # 🟡 BOTH LEGS CLOSED
                    logger.info(f"🟡 Both legs closed for {strategy_id}")
                    active_monitors[strategy_id]['status'] = 'both_closed'
                    break
                
                else:
                    # ✅ BOTH LEGS STILL OPEN
                    logger.debug(f"✅ Both legs open for {strategy_id}")
                
                # Sleep before next check
                await asyncio.sleep(5)
        
        finally:
            await client.close()
            
            # Mark completion time
            active_monitors[strategy_id]['completed_at'] = datetime.now()
            
            logger.info(f"🛑 Stopped monitoring {strategy_id}")
    
    except Exception as e:
        logger.error(f"Error monitoring strategy {strategy_id}: {e}", exc_info=True)
        if strategy_id in active_monitors:
            active_monitors[strategy_id]['status'] = 'error'
            active_monitors[strategy_id]['error'] = str(e)


async def _move_sl_to_cost(client: DeltaClient, position: dict, entry_price: float) -> bool:
    """
    Move stop loss to entry price (breakeven).
    """
    try:
        product_id = position.get('product_id')
        
        # Modify position with SL at entry price
        response = await client.change_position_margin(
            product_id=product_id,
            stop_loss_price=entry_price,
            delta_margin=0
        )
        
        if response.get('success'):
            logger.info(f"✅ Successfully moved SL to {entry_price}")
            return True
        else:
            error = response.get('error', {}).get('message', 'Unknown error')
            logger.error(f"❌ Failed to move SL: {error}")
            return False
    
    except Exception as e:
        logger.error(f"Error moving SL: {e}", exc_info=True)
        return False


def stop_strategy_monitor(strategy_id: str):
    """
    Manually stop monitoring a strategy.
    """
    if strategy_id in active_monitors:
        task = active_monitors[strategy_id].get('task')
        if task:
            task.cancel()
        active_monitors[strategy_id]['status'] = 'stopped'
        active_monitors[strategy_id]['stopped_at'] = datetime.now()
        logger.info(f"🛑 Manually stopped monitor for {strategy_id}")


def get_active_monitors() -> list:
    """
    Get list of currently monitored strategy IDs.
    """
    return list(active_monitors.keys())


def get_monitor_status(strategy_id: str) -> Optional[dict]:
    """
    Get detailed status of a specific monitor.
    """
    return active_monitors.get(strategy_id)


def get_all_monitor_details() -> dict:
    """
    Get details of all monitors.
    """
    return active_monitors.copy()
                  
