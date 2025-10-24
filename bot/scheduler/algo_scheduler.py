"""
Algo trading scheduler with IST timezone support.
Includes automatic stop-loss and target order placement.
✅ INCLUDES LEG PROTECTION FEATURE
"""

import asyncio
import calendar
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
                'order_type': 'limit_order',
                'stop_order_type': 'take_profit_order',
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
            return

        # Get options
        products_response = await client.get_products(contract_types='call_options,put_options')
        if not products_response.get('success'):
            raise Exception(f"Failed to fetch options: {products_response.get('error', {}).get('message')}")

        products = products_response['result']

        # READ EXPIRY TYPE FROM STRATEGY PRESET
        if hasattr(strategy, 'expiry_type'):
            expiry_type = strategy.expiry_type
        elif isinstance(strategy, dict):
            expiry_type = strategy.get('expiry_type', 'daily')
        else:
            expiry_type = 'daily'

        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)

        # CALCULATE TARGET EXPIRY BASED ON STRATEGY'S EXPIRY_TYPE
        if expiry_type == 'daily':
            if now_ist.hour < 17 or (now_ist.hour == 17 and now_ist.minute < 30):
                target_expiry_date = now_ist.date()
            else:
                target_expiry_date = now_ist.date() + timedelta(days=1)

        elif expiry_type == 'weekly':
            current_weekday = now_ist.weekday()
            if current_weekday < 4:
                days_to_friday = 4 - current_weekday
            elif current_weekday == 4:
                if now_ist.hour >= 17 and now_ist.minute >= 30:
                    days_to_friday = 7
                else:
                    days_to_friday = 0
            else:
                days_to_friday = (7 - current_weekday + 4) % 7
    
            target_expiry_date = now_ist.date() + timedelta(days=days_to_friday)

        elif expiry_type == 'monthly':
            year = now_ist.year
            month = now_ist.month
            last_day = calendar.monthrange(year, month)[1]
            last_date = datetime(year, month, last_day, tzinfo=ist).date()
    
            while last_date.weekday() != 4:
                last_date -= timedelta(days=1)
    
            if now_ist.date() > last_date or (now_ist.date() == last_date and now_ist.hour >= 17 and now_ist.minute >= 30):
                if month == 12:
                    next_month = 1
                    next_year = year + 1
                else:
                    next_month = month + 1
                    next_year = year
        
                last_day = calendar.monthrange(next_year, next_month)[1]
                target_expiry_date = datetime(next_year, next_month, last_day, tzinfo=ist).date()
        
                while target_expiry_date.weekday() != 4:
                    target_expiry_date -= timedelta(days=1)
            else:
                target_expiry_date = last_date

        else:
            raise ValueError(f"Invalid expiry_type: {expiry_type}")

        target_expiry = target_expiry_date.strftime('%d%m%y')
        logger.info(f"Expiry Type: {expiry_type.upper()} | Target: {target_expiry} ({target_expiry_date.strftime('%d %b %Y')})")

        # Filter options by expiry
        filtered_options = [
            p for p in products
            if asset in p.get('symbol', '') 
            and p.get('state') == 'live'
            and target_expiry in p.get('symbol', '')
        ]

        if not filtered_options:
            logger.warning(f"No options found for expiry {target_expiry}, trying next day...")
            target_expiry_date = target_expiry_date + timedelta(days=1)
            target_expiry = target_expiry_date.strftime('%d%m%y')
            logger.info(f"Using next day's expiry: {target_expiry} ({target_expiry_date.strftime('%d %b %Y')})")
    
            filtered_options = [
                p for p in products
                if asset in p.get('symbol', '') 
                and p.get('state') == 'live'
                and target_expiry in p.get('symbol', '')
            ]
    
            if not filtered_options:
                raise Exception(f"No options found for {asset} with expiry {target_expiry}")

        logger.info(f"Found {len(filtered_options)} live options for {asset} expiring {target_expiry}")
 
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
        
        # ============================================================
        # ✅ START LEG PROTECTION (USING SHARED SERVICE)
        # ============================================================
        
        enable_leg_protection = False
        if hasattr(preset, 'enable_sl_monitor'):
            enable_leg_protection = preset.enable_sl_monitor
        elif isinstance(preset, dict):
            enable_leg_protection = preset.get('enable_sl_monitor', False)
        
        if enable_leg_protection:
            logger.info(f"🛡️ Starting leg protection monitor for auto trade (setup {setup_id})")
            
            # Prepare strategy details for monitoring
            strategy_details = {
                'user_id': user_id,
                'api_id': preset['api_credential_id'],
                'strategy_type': preset['strategy_type'],
                'ce_symbol': ce_symbol,
                'pe_symbol': pe_symbol,
                'ce_entry_price': ce_fill_price,
                'pe_entry_price': pe_fill_price,
                'ce_sl_order_id': ce_bracket_orders.get('sl_order_id'),
                'pe_sl_order_id': pe_bracket_orders.get('sl_order_id'),
                'direction': direction,
                'lot_size': lot_size
            }
            
            # Start monitoring task using shared service
            asyncio.create_task(
                start_leg_protection_monitor(strategy_details, bot_application)
            )
            
            logger.info(f"✅ Leg protection monitor started for {ce_symbol}/{pe_symbol}")
        else:
            logger.info(f"⏸️ Leg protection disabled for setup {setup_id}")
        # ============================================================
        # END LEG PROTECTION SETUP
        # ============================================================
        
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


# ============================================================
# ✅ LEG PROTECTION MONITORING FUNCTIONS
# ============================================================

async def monitor_leg_protection(strategy: Dict, bot_application):
    """
    Monitor strategy legs and protect remaining leg when one closes.
    Checks every 30 seconds for closed positions.
    """
    client = None
    try:
        logger.info(f"🔍 Starting leg protection monitor for {strategy['ce_symbol']}/{strategy['pe_symbol']}")
        
        # Get API credentials
        from database.operations.api_ops import get_decrypted_api_credential
        credentials = await get_decrypted_api_credential(strategy['api_id'])
        
        if not credentials:
            logger.error("Failed to get API credentials for monitoring")
            return
        
        api_key, api_secret = credentials
        from delta.client import DeltaClient
        client = DeltaClient(api_key, api_secret)
        
        # Monitor for up to 24 hours (2880 checks at 30sec intervals)
        for _ in range(2880):
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # Skip if already protected
            if strategy.get('leg_protection_activated'):
                logger.info("Leg protection already activated, stopping monitor")
                break
            
            try:
                # Get current positions
                positions = await client.get_positions()
                
                if not positions.get('success'):
                    continue
                
                positions_data = positions['result']
                
                # Find CE and PE positions
                ce_position = next((p for p in positions_data 
                                  if strategy['ce_symbol'] in p.get('product', {}).get('symbol', '')), None)
                pe_position = next((p for p in positions_data 
                                  if strategy['pe_symbol'] in p.get('product', {}).get('symbol', '')), None)
                
                # Check if positions exist
                ce_size = int(ce_position.get('size', 0)) if ce_position else 0
                pe_size = int(pe_position.get('size', 0)) if pe_position else 0
                
                # Check if ONE leg is closed
                ce_closed = ce_size == 0
                pe_closed = pe_size == 0
                
                # ONE leg closed, other still open → PROTECT!
                if ce_closed and not pe_closed:
                    logger.info(f"🛡️ CE leg closed, protecting PE leg")
                    await protect_remaining_leg(
                        client=client,
                        strategy=strategy,
                        remaining_symbol=strategy['pe_symbol'],
                        remaining_entry_price=strategy['pe_entry_price'],
                        remaining_sl_order_id=strategy.get('pe_sl_order_id'),
                        closed_leg='CE',
                        bot_application=bot_application
                    )
                    strategy['leg_protection_activated'] = True
                    break
                
                elif pe_closed and not ce_closed:
                    logger.info(f"🛡️ PE leg closed, protecting CE leg")
                    await protect_remaining_leg(
                        client=client,
                        strategy=strategy,
                        remaining_symbol=strategy['ce_symbol'],
                        remaining_entry_price=strategy['ce_entry_price'],
                        remaining_sl_order_id=strategy.get('ce_sl_order_id'),
                        closed_leg='PE',
                        bot_application=bot_application
                    )
                    strategy['leg_protection_activated'] = True
                    break
                
                # Both legs still open - continue monitoring
                elif not ce_closed and not pe_closed:
                    continue
                
                # Both legs closed - stop monitoring
                else:
                    logger.info("Both legs closed, stopping monitor")
                    break
                    
            except Exception as e:
                logger.error(f"Error checking leg status: {e}")
                continue
        
        logger.info("Leg protection monitoring ended")
        
    except Exception as e:
        logger.error(f"Error in leg protection monitor: {e}", exc_info=True)
    finally:
        if client:
            await client.close()


async def protect_remaining_leg(client, strategy: Dict, remaining_symbol: str, 
                                remaining_entry_price: float, remaining_sl_order_id: str,
                                closed_leg: str, bot_application):
    """
    Move remaining leg's SL to breakeven (entry price).
    """
    try:
        logger.info(f"🛡️ Protecting remaining leg: {remaining_symbol}")
        
        # Cancel existing SL order
        if remaining_sl_order_id:
            try:
                cancel_result = await client.cancel_order(remaining_sl_order_id)
                if cancel_result.get('success'):
                    logger.info(f"✅ Cancelled old SL order: {remaining_sl_order_id}")
                else:
                    logger.warning(f"Failed to cancel SL: {cancel_result.get('error')}")
            except Exception as e:
                logger.error(f"Error cancelling SL: {e}")
        
        # Get product details
        products_response = await client.get_products(contract_types='call_options,put_options')
        if not products_response.get('success'):
            raise Exception("Failed to fetch products")
        
        product = next((p for p in products_response['result'] 
                       if p['symbol'] == remaining_symbol), None)
        
        if not product:
            raise Exception(f"Product not found: {remaining_symbol}")
        
        # Place new SL at breakeven (entry price)
        direction = strategy.get('direction', 'long')
        side = 'sell' if direction == 'long' else 'buy'
        
        new_sl_order = await client.place_order({
            'product_id': product['id'],
            'size': strategy.get('lot_size', 1),
            'side': side,
            'order_type': 'limit_order',
            'stop_order_type': 'stop_loss_order',
            'stop_price': round(remaining_entry_price, 2),
            'limit_price': round(remaining_entry_price * 0.98, 2),  # 2% below for execution
            'time_in_force': 'gtc'
        })
        
        if new_sl_order.get('success'):
            new_sl_id = new_sl_order['result']['id']
            logger.info(f"✅ New breakeven SL placed: {new_sl_id} at ${remaining_entry_price:.2f}")
            
            # Send notification
            remaining_leg = 'CE' if closed_leg == 'PE' else 'PE'
            message = (
                f"🛡️ **Leg Protection Activated!**\n\n"
                f"🔄 **{closed_leg} leg closed**\n"
                f"🛡️ **{remaining_leg} leg protected**\n\n"
                f"💰 **New SL:** ${remaining_entry_price:.2f} (Breakeven)\n\n"
                f"✅ You're now protected from further losses!"
            )
            
            try:
                await bot_application.bot.send_message(
                    chat_id=strategy['user_id'],
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
            
        else:
            logger.error(f"Failed to place new SL: {new_sl_order.get('error')}")
        
    except Exception as e:
        logger.error(f"Error protecting remaining leg: {e}", exc_info=True)

# ============================================================
# END OF LEG PROTECTION FUNCTIONS
# ============================================================


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
