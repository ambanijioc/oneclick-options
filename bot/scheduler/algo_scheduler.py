"""
Algo trading scheduler with IST timezone support.
Includes automatic stop-loss and target order placement.
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


async def place_sl_target_orders(client: DeltaClient, symbol: str, size: int, direction: str, 
                                  entry_price: float, sl_trigger_pct: float, sl_limit_pct: float,
                                  target_trigger_pct: float, target_limit_pct: float, option_type: str):
    """
    Place stop-loss and target bracket orders for an option.
    
    Args:
        client: Delta client
        symbol: Option symbol
        size: Lot size
        direction: 'long' or 'short'
        entry_price: Entry price of the option
        sl_trigger_pct: Stop-loss trigger percentage
        sl_limit_pct: Stop-loss limit percentage
        target_trigger_pct: Target trigger percentage (0 for none)
        target_limit_pct: Target limit percentage
        option_type: 'CE' or 'PE' for logging
    
    Returns:
        dict: Order IDs and details
    """
    orders = {}
    
    try:
        # Get product_id from symbol
        products_response = await client.get_products(contract_types='call_options,put_options')
        
        if not products_response.get('success'):
            raise Exception("Failed to fetch products for SL/Target placement")
        
        product = next((p for p in products_response['result'] if p['symbol'] == symbol), None)
        
        if not product:
            raise Exception(f"Product not found: {symbol}")
        
        product_id = product['id']
        
        # Calculate stop-loss prices
        if direction == 'long':
            # For long positions, SL is below entry
            sl_trigger_price = entry_price * (1 - sl_trigger_pct / 100)
            sl_limit_price = entry_price * (1 - sl_limit_pct / 100)
            sl_side = 'sell'  # Exit long by selling
            
            # Target is above entry
            if target_trigger_pct > 0:
                target_trigger_price = entry_price * (1 + target_trigger_pct / 100)
                target_limit_price = entry_price * (1 + target_limit_pct / 100)
                target_side = 'sell'
        else:  # short
            # For short positions, SL is above entry
            sl_trigger_price = entry_price * (1 + sl_trigger_pct / 100)
            sl_limit_price = entry_price * (1 + sl_limit_pct / 100)
            sl_side = 'buy'  # Exit short by buying
            
            # Target is below entry
            if target_trigger_pct > 0:
                target_trigger_price = entry_price * (1 - target_trigger_pct / 100)
                target_limit_price = entry_price * (1 - target_limit_pct / 100)
                target_side = 'buy'
        
        # Place stop-loss order
        logger.info(f"Placing SL for {option_type}: trigger={sl_trigger_price:.2f}, limit={sl_limit_price:.2f}")
        
        sl_order = await client.place_order({
            'product_id': product_id,
            'size': size,
            'side': sl_side,
            'order_type': 'limit_order',
            'stop_order_type': 'stop_loss_order',
            'stop_price': round(sl_trigger_price, 2),
            'limit_price': round(sl_limit_price, 2),
            'time_in_force': 'gtc'
        })
        
        if sl_order.get('success'):
            orders['sl_order_id'] = sl_order['result']['id']
            orders['sl_trigger'] = sl_trigger_price
            orders['sl_limit'] = sl_limit_price
            logger.info(f"{option_type} Stop-loss order placed: {sl_order['result']['id']}")
        else:
            logger.error(f"{option_type} SL order failed: {sl_order.get('error', {}).get('message')}")
            orders['sl_error'] = sl_order.get('error', {}).get('message', 'Unknown error')
        
        # Place target order if specified
        if target_trigger_pct > 0:
            logger.info(f"Placing Target for {option_type}: trigger={target_trigger_price:.2f}, limit={target_limit_price:.2f}")
            
            target_order = await client.place_order({
                'product_id': product_id,
                'size': size,
                'side': target_side,
                'order_type': 'limit_order',  # ✅ FIXED
                'stop_order_type': 'take_profit_order',  # ✅ ADDED
                'stop_price': round(target_trigger_price, 2),
                'limit_price': round(target_limit_price, 2),
                'time_in_force': 'gtc'
            })
            
            if target_order.get('success'):
                orders['target_order_id'] = target_order['result']['id']
                orders['target_trigger'] = target_trigger_price
                orders['target_limit'] = target_limit_price
                logger.info(f"{option_type} Target order placed: {target_order['result']['id']}")
            else:
                logger.error(f"{option_type} Target order failed: {target_order.get('error', {}).get('message')}")
                orders['target_error'] = target_order.get('error', {}).get('message', 'Unknown error')
    
    except Exception as e:
        logger.error(f"Error placing SL/Target for {option_type}: {e}", exc_info=True)
        orders['error'] = str(e)
    
    return orders


async def execute_algo_trade(setup_id: str, user_id: int, bot_application):
    """Execute algo trade for a setup."""
    client = None
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
        
        credentials = await get_decrypted_api_credential(preset['api_credential_id'])
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
        
        # Handle both dict and Pydantic model
        if hasattr(strategy, 'asset'):
            asset = strategy.asset
            direction = strategy.direction
            lot_size = strategy.lot_size
            sl_trigger_pct = strategy.sl_trigger_pct
            sl_limit_pct = strategy.sl_limit_pct
            target_trigger_pct = strategy.target_trigger_pct
            target_limit_pct = strategy.target_limit_pct
        else:
            asset = strategy.get('asset')
            direction = strategy.get('direction')
            lot_size = strategy.get('lot_size')
            sl_trigger_pct = strategy.get('sl_trigger_pct', 0)
            sl_limit_pct = strategy.get('sl_limit_pct', 0)
            target_trigger_pct = strategy.get('target_trigger_pct', 0)
            target_limit_pct = strategy.get('target_limit_pct', 0)
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        # Get spot price using get_spot_price (same as manual trade)
        try:
            spot_price = await client.get_spot_price(asset)
            logger.info(f"Spot price for {asset}: {spot_price}")
        except Exception as e:
            error_msg = f"Failed to fetch spot price: {str(e)}"
            logger.error(f"❌ {error_msg}")
            await update_algo_execution(setup_id, 'failed', {'error': error_msg})
    
            # Send error notification
            try:
                await bot_application.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ <b>Algo Trade Failed</b>\n\n<b>Time:</b> {datetime.now(IST).strftime('%I:%M %p IST')}\n<b>Error:</b> Unable to fetch market price from exchange",
                    parse_mode='HTML'
                )
            except Exception:
                pass
            return  # ✅ FIXED: return moved inside except block

        # ✅ FIXED: Code below unindented - runs AFTER try-except
        # Get options
        products_response = await client.get_products(contract_types='call_options,put_options')
        if not products_response.get('success'):
            raise Exception(f"Failed to fetch options: {products_response.get('error', {}).get('message')}")
        
        products = products_response['result']
        # Get current week's Friday expiry
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.hour >= 15:  # After 3 PM on Friday, use next week
            days_until_friday = 7
        target_expiry_date = today + timedelta(days=days_until_friday)
        target_expiry = target_expiry_date.strftime('%y%m%d')  # Format: 231025

        logger.info(f"Target expiry: {target_expiry} ({target_expiry_date.strftime('%d %b %Y')})")

        filtered_options = [
            p for p in products
            if asset in p.get('symbol', '') 
            and p.get('state') == 'live'
            and target_expiry in p.get('symbol', '')  # ✅ FILTER BY EXPIRY!
        ]
        
        logger.info(f"Found {len(filtered_options)} live options for {asset}")
        
        # Calculate strikes based on strategy type
        if preset['strategy_type'] == 'straddle':
            if hasattr(strategy, 'atm_offset'):
                atm_offset = strategy.atm_offset
            else:
                atm_offset = strategy.get('atm_offset', 0)
            
            target_strike = spot_price + atm_offset
            strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
            atm_strike = min(strikes, key=lambda x: abs(x - target_strike))
            
            logger.info(f"Straddle ATM strike: {atm_strike} (offset: {atm_offset})")
            
            ce_option = next((p for p in filtered_options 
                             if float(p['strike_price']) == atm_strike and 'C' in p['symbol']), None)
            pe_option = next((p for p in filtered_options 
                             if float(p['strike_price']) == atm_strike and 'P' in p['symbol']), None)
            
            if not ce_option or not pe_option:
                raise Exception("Could not find matching ATM options")
            
            ce_symbol = ce_option['symbol']
            pe_symbol = pe_option['symbol']
            ce_strike = atm_strike
            pe_strike = atm_strike
        
        else:  # strangle
            if hasattr(strategy, 'otm_selection'):
                otm_selection = strategy.otm_selection
                otm_type = otm_selection.type
                otm_value = otm_selection.value
            else:
                otm_selection = strategy.get('otm_selection', {})
                otm_type = otm_selection.get('type', 'percentage')
                otm_value = otm_selection.get('value', 0)
            
            strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
            
            if otm_type == 'percentage':
                offset = spot_price * (otm_value / 100)
                ce_target = spot_price + offset
                pe_target = spot_price - offset
                logger.info(f"Strangle OTM % calculation: CE target={ce_target}, PE target={pe_target}")
            else:  # numeral
                atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
                atm_index = strikes.index(atm_strike)
                num_strikes = int(otm_value)
                ce_target = strikes[min(atm_index + num_strikes, len(strikes) - 1)]
                pe_target = strikes[max(atm_index - num_strikes, 0)]
                logger.info(f"Strangle OTM strikes calculation: CE target={ce_target}, PE target={pe_target}")
            
            ce_strike = min(strikes, key=lambda x: abs(x - ce_target))
            pe_strike = min(strikes, key=lambda x: abs(x - pe_target))
            
            ce_option = next((p for p in filtered_options 
                             if float(p['strike_price']) == ce_strike and 'C' in p['symbol']), None)
            pe_option = next((p for p in filtered_options 
                             if float(p['strike_price']) == pe_strike and 'P' in p['symbol']), None)
            
            if not ce_option or not pe_option:
                raise Exception("Could not find matching OTM options")
            
            ce_symbol = ce_option['symbol']
            pe_symbol = pe_option['symbol']
        
        logger.info(f"Selected options - CE: {ce_symbol}, PE: {pe_symbol}")
        
        # Execute entry orders
        side = 'buy' if direction == 'long' else 'sell'
        
        # Get CE product_id
        ce_product_id = ce_option['id']

        # Place CE order
        logger.info(f"Placing CE order: {side} {lot_size} {ce_symbol}")
        ce_order = await client.place_order({
            'product_id': ce_product_id,
            'size': lot_size,
            'side': side,
            'order_type': 'market_order',
            'time_in_force': 'ioc'
        })
        
        if not ce_order.get('success'):
            raise Exception(f"CE order failed: {ce_order.get('error', {}).get('message')}")
        
        ce_order_id = ce_order['result']['id']
        ce_fill_price = float(ce_order['result'].get('average_fill_price', 0))
        logger.info(f"CE order filled: ID={ce_order_id}, Price={ce_fill_price}")
        
        # Get PE product_id
        pe_product_id = pe_option['id']

        # Place PE order
        logger.info(f"Placing PE order: {side} {lot_size} {pe_symbol}")
        pe_order = await client.place_order({
            'product_id': pe_product_id,
            'size': lot_size,
            'side': side,
            'order_type': 'market_order',
            'time_in_force': 'ioc'
        })
        
        if not pe_order.get('success'):
            raise Exception(f"PE order failed: {pe_order.get('error', {}).get('message')}")
        
        pe_order_id = pe_order['result']['id']
        pe_fill_price = float(pe_order['result'].get('average_fill_price', 0))
        logger.info(f"PE order filled: ID={pe_order_id}, Price={pe_fill_price}")
        
        # Place stop-loss and target orders for CE
        ce_bracket_orders = await place_sl_target_orders(
            client=client,
            symbol=ce_symbol,
            size=lot_size,
            direction=direction,
            entry_price=ce_fill_price,
            sl_trigger_pct=sl_trigger_pct,
            sl_limit_pct=sl_limit_pct,
            target_trigger_pct=target_trigger_pct,
            target_limit_pct=target_limit_pct,
            option_type='CE'
        )
        
        # Place stop-loss and target orders for PE
        pe_bracket_orders = await place_sl_target_orders(
            client=client,
            symbol=pe_symbol,
            size=lot_size,
            direction=direction,
            entry_price=pe_fill_price,
            sl_trigger_pct=sl_trigger_pct,
            sl_limit_pct=sl_limit_pct,
            target_trigger_pct=target_trigger_pct,
            target_limit_pct=target_limit_pct,
            option_type='PE'
        )
        
        # Build execution details
        details = {
            'spot_price': spot_price,
            'ce_symbol': ce_symbol,
            'pe_symbol': pe_symbol,
            'ce_strike': ce_strike,
            'pe_strike': pe_strike,
            'ce_order_id': ce_order_id,
            'pe_order_id': pe_order_id,
            'ce_entry_price': ce_fill_price,
            'pe_entry_price': pe_fill_price,
            'direction': direction,
            'lot_size': lot_size,
            'ce_sl_order': ce_bracket_orders.get('sl_order_id'),
            'ce_target_order': ce_bracket_orders.get('target_order_id'),
            'pe_sl_order': pe_bracket_orders.get('sl_order_id'),
            'pe_target_order': pe_bracket_orders.get('target_order_id'),
        }
        
        await update_algo_execution(setup_id, 'success', details)
        logger.info(f"Algo trade executed successfully for setup {setup_id}")
        
        # Build notification message
        notification_text = (
            f"✅ <b>Algo Trade Executed</b>\n\n"
            f"<b>Time:</b> {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}\n"
            f"<b>Preset:</b> {preset.get('preset_name', 'Unknown')}\n"
            f"<b>Strategy:</b> {preset['strategy_type'].title()}\n\n"
            f"<b>📊 Spot Price:</b> ${spot_price:,.2f}\n\n"
            f"<b>📈 CE:</b> {ce_symbol}\n"
            f"├ Entry: ${ce_fill_price:.2f}\n"
        )
        
        if ce_bracket_orders.get('sl_order_id'):
            notification_text += f"├ SL: ${ce_bracket_orders['sl_trigger']:.2f}\n"
        if ce_bracket_orders.get('target_order_id'):
            notification_text += f"└ Target: ${ce_bracket_orders['target_trigger']:.2f}\n"
        else:
            notification_text += f"└ No target set\n"
        
        notification_text += f"\n<b>📉 PE:</b> {pe_symbol}\n"
        notification_text += f"├ Entry: ${pe_fill_price:.2f}\n"
        
        if pe_bracket_orders.get('sl_order_id'):
            notification_text += f"├ SL: ${pe_bracket_orders['sl_trigger']:.2f}\n"
        if pe_bracket_orders.get('target_order_id'):
            notification_text += f"└ Target: ${pe_bracket_orders['target_trigger']:.2f}\n"
        else:
            notification_text += f"└ No target set\n"
        
        notification_text += f"\n<b>Direction:</b> {direction.title()}\n"
        notification_text += f"<b>Lot Size:</b> {lot_size}"
        
        # Send notification to user
        try:
            await bot_application.bot.send_message(
                chat_id=user_id,
                text=notification_text,
                parse_mode='HTML'
            )
        except Exception as notify_error:
            logger.error(f"Failed to send notification: {notify_error}")
    
    except Exception as e:
        logger.error(f"Algo trade execution failed for setup {setup_id}: {e}", exc_info=True)
        await update_algo_execution(setup_id, 'failed', {'error': str(e)})
        
        # Try to send error notification
        try:
            await bot_application.bot.send_message(
                chat_id=user_id,
                text=f"❌ <b>Algo Trade Failed</b>\n\n"
                     f"<b>Time:</b> {datetime.now(IST).strftime('%I:%M %p IST')}\n"
                     f"<b>Error:</b> {str(e)[:300]}",
                parse_mode='HTML'
            )
        except Exception:
            pass
    
    finally:
        if client:
            await client.close()


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
        logger.info(f"Executing trade for setup {setup_id} at {datetime.now(IST).strftime('%I:%M %p IST')}")
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
                logger.info(f"Scheduled algo setup {setup_id} for {setup['execution_time']} IST")
            
            # Clean up completed tasks
            completed = [sid for sid, task in pending_executions.items() if task.done()]
            for sid in completed:
                del pending_executions[sid]
                logger.info(f"Cleaned up completed execution for setup {sid}")
            
            # Check every 60 seconds
            await asyncio.sleep(60)
        
        except Exception as e:
            logger.error(f"Error in algo scheduler: {e}", exc_info=True)
            await asyncio.sleep(60)
