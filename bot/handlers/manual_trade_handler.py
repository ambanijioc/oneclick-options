"""
Manual trade execution handler - uses saved presets.
FIXED: Retry logic for order status checking + proper SL placement
"""

import asyncio
from datetime import datetime
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.manual_trade_preset_ops import (
    get_manual_trade_presets,
    get_manual_trade_preset
)
from database.operations.api_ops import get_api_credential_by_id, get_decrypted_api_credential
from database.operations.strategy_ops import get_strategy_preset_by_id
from delta.client import DeltaClient

logger = setup_logger(__name__)


def get_manual_trade_keyboard():
    """Get manual trade keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def safe_get_attr(obj, attr, default=None):
    """Safely get attribute from Pydantic object or dict."""
    if hasattr(obj, attr):
        return getattr(obj, attr, default)
    elif isinstance(obj, dict):
        return obj.get(attr, default)
    return default


@error_handler
async def manual_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual trade execution menu - list presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>🎯 Manual Trade Execution</b>\n\n"
            "❌ No trade presets found.\n\n"
            "Please create a Manual Trade Preset first using the menu.",
            reply_markup=get_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    keyboard = []
    for preset in presets:
        preset_name = safe_get_attr(preset, 'preset_name', 'Unnamed')
        preset_id = safe_get_attr(preset, 'id', safe_get_attr(preset, '_id'))
        
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset_name}",
            callback_data=f"manual_trade_select_{preset_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")])
    
    await query.edit_message_text(
        "<b>🎯 Manual Trade Execution</b>\n\n"
        "Select a trade preset to execute:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "manual_trade_menu", f"Viewed {len(presets)} trade presets")


@error_handler
async def manual_trade_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - fetch details and show confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    await query.edit_message_text(
        "⏳ <b>Loading trade details...</b>\n\n"
        "Fetching market data and calculating strikes...",
        parse_mode='HTML'
    )
    
    try:
        preset = await get_manual_trade_preset(preset_id)
        
        if not preset:
            await query.edit_message_text(
                "❌ Trade preset not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        api_credential_id = safe_get_attr(preset, 'api_credential_id')
        strategy_preset_id = safe_get_attr(preset, 'strategy_preset_id')
        strategy_type = safe_get_attr(preset, 'strategy_type', 'straddle')
        preset_name = safe_get_attr(preset, 'preset_name', 'Unnamed')
        
        api = await get_api_credential_by_id(api_credential_id)
        if not api:
            await query.edit_message_text(
                "❌ API credential not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        credentials = await get_decrypted_api_credential(api_credential_id)
        if not credentials:
            await query.edit_message_text(
                "❌ Failed to decrypt API credentials.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        strategy = await get_strategy_preset_by_id(strategy_preset_id)
        if not strategy:
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        asset = safe_get_attr(strategy, 'asset', 'BTC')
        direction = safe_get_attr(strategy, 'direction', 'short')
        lot_size = safe_get_attr(strategy, 'lot_size', 1)
        strategy_name = safe_get_attr(strategy, 'name', 'Unnamed Strategy')
        api_name = safe_get_attr(api, 'api_name', 'Unknown API')
        
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            ticker_symbol = f"{asset}USD"
            ticker_response = await client.get_ticker(ticker_symbol)
    
            if ticker_response is None:
                await query.edit_message_text(
                    "❌ Failed to connect to Delta Exchange API.",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            if not ticker_response.get('success'):
                error_msg = ticker_response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    f"❌ Failed to fetch spot price: {error_msg}",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
    
            if not ticker_response.get('result'):
                await query.edit_message_text(
                    "❌ Invalid response from Delta Exchange API.",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
    
            spot_price = float(ticker_response['result']['spot_price'])
            
            products_response = await client.get_products(contract_types='call_options,put_options')
            if not products_response.get('success'):
                await query.edit_message_text(
                    f"❌ Failed to fetch options: {products_response.get('error', {}).get('message', 'Unknown error')}",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            products = products_response['result']
            
            filtered_options = [
                p for p in products
                if asset in p.get('symbol', '')
                and p.get('state') == 'live'
            ]

            expiry_groups = defaultdict(list)
            for opt in filtered_options:
                settlement_time = opt.get('settlement_time')
                if settlement_time:
                    try:
                        if isinstance(settlement_time, str):
                            from dateutil import parser as date_parser
                            timestamp = int(date_parser.parse(settlement_time).timestamp())
                        else:
                            timestamp = int(settlement_time)
                        expiry_groups[timestamp].append(opt)
                    except Exception as e:
                        logger.error(f"Failed to parse settlement_time {settlement_time}: {e}")
                        continue

            if not expiry_groups:
                await query.edit_message_text(
                    "❌ No active options found for this asset.",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return

            nearest_expiry = min(expiry_groups.keys())
            filtered_options = expiry_groups[nearest_expiry]

            logger.info(f"✅ Selected expiry: {nearest_expiry} with {len(filtered_options)} options")

            if strategy_type == 'straddle':
                atm_offset = safe_get_attr(strategy, 'atm_offset', 0)
                target_strike = spot_price + atm_offset

                strikes = sorted(set(p['strike_price'] for p in filtered_options if p.get('strike_price')))
                atm_strike = min(strikes, key=lambda x: abs(float(x) - target_strike))

                ce_option = next((p for p in filtered_options 
                                 if p['strike_price'] == atm_strike 
                                 and 'C' in p['symbol']), None)
                pe_option = next((p for p in filtered_options 
                                 if p['strike_price'] == atm_strike 
                                 and 'P' in p['symbol']), None)

                if not ce_option or not pe_option:
                    await query.edit_message_text(
                        f"❌ Could not find matching Call and Put options.\n\n"
                        f"Strike: ${float(atm_strike):,.0f}\n"
                        f"Expiry: {datetime.fromtimestamp(nearest_expiry).strftime('%Y-%m-%d')}\n\n"
                        f"CE found: {'Yes' if ce_option else 'No'}\n"
                        f"PE found: {'Yes' if pe_option else 'No'}",
                        reply_markup=get_manual_trade_keyboard(),
                        parse_mode='HTML'
                    )            
                    return

                ce_mark_price = float(ce_option.get('mark_price', 0) or 0)
                pe_mark_price = float(pe_option.get('mark_price', 0) or 0)
                total_premium = (ce_mark_price + pe_mark_price) * lot_size

                expiry_date = datetime.fromtimestamp(nearest_expiry).strftime('%d %b %Y')
                
                text = f"<b>🎯 Confirm Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset_name}\n"
                text += f"<b>API:</b> {api_name}\n"
                text += f"<b>Strategy:</b> {strategy_name}\n\n"
                text += f"<b>📊 Market Data:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${float(atm_strike):,.0f}\n"
                text += f"Expiry: {expiry_date}\n\n"
                text += f"<b>🎲 Straddle Details:</b>\n"
                text += f"CE: {ce_option['symbol']}\n"
                text += f"  Mark: ${ce_mark_price:,.4f}\n"
                text += f"PE: {pe_option['symbol']}\n"
                text += f"  Mark: ${pe_mark_price:,.4f}\n\n"
                text += f"<b>💰 Trade Summary:</b>\n"
                text += f"Direction: {direction.title()}\n"
                text += f"Lot Size: {lot_size}\n"
                text += f"Total Premium: ${total_premium:,.2f}\n\n"
                text += "⚠️ Execute this trade?"

                context.user_data['pending_trade'] = {
                    'preset_id': preset_id,
                    'ce_symbol': ce_option['symbol'],
                    'pe_symbol': pe_option['symbol'],
                    'strike': float(atm_strike),
                    'expiry': expiry_date,
                    'direction': direction,
                    'lot_size': lot_size,
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            
            else:  # strangle
                otm_selection = safe_get_attr(strategy, 'otm_selection')
                if otm_selection:
                    otm_type = safe_get_attr(otm_selection, 'type', 'percentage')
                    otm_value = safe_get_attr(otm_selection, 'value', 0)
                else:
                    otm_type = 'percentage'
                    otm_value = 0
                
                if otm_type == 'percentage':
                    offset = spot_price * (otm_value / 100)
                    ce_target = spot_price + offset
                    pe_target = spot_price - offset
                else:
                    strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
                    atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
                    atm_index = strikes.index(atm_strike)
        
                    num_strikes = int(otm_value)
                    ce_target = strikes[min(atm_index + num_strikes, len(strikes) - 1)]
                    pe_target = strikes[max(atm_index - num_strikes, 0)]
    
                strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
                ce_strike = min(strikes, key=lambda x: abs(x - ce_target))
                pe_strike = min(strikes, key=lambda x: abs(x - pe_target))
    
                ce_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == ce_strike 
                                 and 'C' in p['symbol']), None)
                pe_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == pe_strike 
                                 and 'P' in p['symbol']), None)
    
                if not ce_option or not pe_option:
                    await query.edit_message_text(
                        "❌ Could not find matching Call and Put options.",
                        reply_markup=get_manual_trade_keyboard(),
                        parse_mode='HTML'
                    )
                    return
    
                ce_mark_price = float(ce_option.get('mark_price', 0) or 0)
                pe_mark_price = float(pe_option.get('mark_price', 0) or 0)
                total_premium = (ce_mark_price + pe_mark_price) * lot_size
    
                expiry_date = datetime.fromtimestamp(nearest_expiry).strftime('%d %b %Y')
                otm_desc = f"{otm_value}% (Spot-based)" if otm_type == 'percentage' else f"{int(otm_value)} strikes (ATM-based)"
    
                text = f"<b>🎯 Confirm Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset_name}\n"
                text += f"<b>API:</b> {api_name}\n"
                text += f"<b>Strategy:</b> {strategy_name}\n\n"
                text += f"<b>📊 Market Data:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"Expiry: {expiry_date}\n"
                text += f"OTM: {otm_desc}\n\n"
                text += f"<b>🎰 Strangle Details:</b>\n"
                text += f"CE: {ce_option['symbol']}\n"
                text += f"  Strike: ${ce_strike:,.0f}\n"
                text += f"  Mark: ${ce_mark_price:,.2f}\n"
                text += f"PE: {pe_option['symbol']}\n"
                text += f"  Strike: ${pe_strike:,.0f}\n"
                text += f"  Mark: ${pe_mark_price:,.2f}\n\n"
                text += f"<b>💰 Trade Summary:</b>\n"
                text += f"Direction: {direction.title()}\n"
                text += f"Lot Size: {lot_size}\n"
                text += f"Total Premium: ${total_premium:,.2f}\n\n"
                text += "⚠️ Execute this trade?"
    
                context.user_data['pending_trade'] = {
                    'preset_id': preset_id,
                    'ce_symbol': ce_option['symbol'],
                    'pe_symbol': pe_option['symbol'],
                    'ce_strike': ce_strike,
                    'pe_strike': pe_strike,
                    'expiry': expiry_date,
                    'direction': direction,
                    'lot_size': lot_size,
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            
            keyboard = [
                [InlineKeyboardButton("✅ Execute Trade", callback_data="manual_trade_execute")],
                [InlineKeyboardButton("❌ Cancel", callback_data="menu_manual_trade")]
            ]
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to prepare trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error: {str(e)[:200]}",
            reply_markup=get_manual_trade_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def manual_trade_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute trade with SL and Target orders - WITH RETRY LOGIC."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    pending_trade = context.user_data.get('pending_trade')
    
    if not pending_trade:
        await query.edit_message_text(
            "❌ No pending trade found.",
            reply_markup=get_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "⏳ <b>Executing trade...</b>\n\n"
        "Placing entry orders...",
        parse_mode='HTML'
    )
    
    try:
        preset = await get_manual_trade_preset(pending_trade['preset_id'])
        strategy_preset_id = safe_get_attr(preset, 'strategy_preset_id')
        strategy = await get_strategy_preset_by_id(strategy_preset_id)
        
        sl_trigger = safe_get_attr(strategy, 'sl_trigger_pct')
        sl_limit = safe_get_attr(strategy, 'sl_limit_pct')
        target_trigger = safe_get_attr(strategy, 'target_trigger_pct')
        target_limit = safe_get_attr(strategy, 'target_limit_pct')
        
        logger.info(f"📊 SL: {sl_trigger}%, Target: {target_trigger}%")
        
        client = DeltaClient(pending_trade['api_key'], pending_trade['api_secret'])
        
        try:
            side = 'buy' if pending_trade['direction'] == 'long' else 'sell'
            
            # Place CE order
            ce_order = await client.place_order({
                'product_symbol': pending_trade['ce_symbol'],
                'size': pending_trade['lot_size'],
                'side': side,
                'order_type': 'market_order'
            })
            
            if not ce_order.get('success'):
                raise Exception(f"CE order failed: {ce_order.get('error', {}).get('message')}")
            
            ce_order_id = ce_order['result']['id']
            
            # Place PE order
            pe_order = await client.place_order({
                'product_symbol': pending_trade['pe_symbol'],
                'size': pending_trade['lot_size'],
                'side': side,
                'order_type': 'market_order'
            })
            
            if not pe_order.get('success'):
                raise Exception(f"PE order failed: {pe_order.get('error', {}).get('message')}")
            
            pe_order_id = pe_order['result']['id']
            
            logger.info(f"✅ Orders placed - CE: {ce_order_id}, PE: {pe_order_id}")

            # ✅ RETRY LOGIC with correct Delta Exchange state handling
            max_retries = 3
            retry_count = 0
            ce_state = 'unknown'
            pe_state = 'unknown'
            ce_avg_fill_price = 0
            pe_avg_fill_price = 0
            ce_filled_qty = 0
            pe_filled_qty = 0

            logger.info("⏳ Waiting for orders to fill...")

            while retry_count < max_retries:
                await asyncio.sleep(3)
                retry_count += 1
    
                logger.info(f"🔍 Attempt {retry_count}/{max_retries} - Checking order status...")
    
                # Fetch CE order
                ce_order_details = await client.get_order(ce_order_id)
                if ce_order_details.get('success'):
                    ce_state = ce_order_details['result'].get('state', 'unknown')
                    ce_avg_fill_price = float(ce_order_details['result'].get('avg_fill_price', 0))
                    ce_filled_qty = float(ce_order_details['result'].get('filled_qty', 0))
    
                # Fetch PE order
                pe_order_details = await client.get_order(pe_order_id)
                if pe_order_details.get('success'):
                    pe_state = pe_order_details['result'].get('state', 'unknown')
                    pe_avg_fill_price = float(pe_order_details['result'].get('avg_fill_price', 0))
                    pe_filled_qty = float(pe_order_details['result'].get('filled_qty', 0))
    
                logger.info(f"📊 Status: CE={ce_state}, PE={pe_state}")
    
                # ✅ FIXED: Delta API uses 'closed' for filled orders
                if ce_state in ['filled', 'closed'] and pe_state in ['filled', 'closed']:
                    logger.info("✅ Both orders completed!")
                    break
    
                if retry_count < max_retries:
                    logger.info(f"⏳ Not completed yet, retrying in 3s...")

            # ✅ Position fallback if prices are still 0
            if ce_avg_fill_price == 0 or pe_avg_fill_price == 0:
                logger.warning("⚠️ Fill prices are 0, fetching from positions...")
                try:
                    positions_response = await client.get_positions()
                    if positions_response.get('success'):
                        positions = positions_response['result']
            
                        ce_position = next((p for p in positions 
                                           if p.get('product', {}).get('symbol') == pending_trade['ce_symbol']), None)
                        pe_position = next((p for p in positions 
                                           if p.get('product', {}).get('symbol') == pending_trade['pe_symbol']), None)
                        
                        if ce_position:
                            ce_avg_fill_price = float(ce_position.get('entry_price', 0))
                            ce_filled_qty = abs(float(ce_position.get('size', 0)))
                            logger.info(f"✅ CE from position: ${ce_avg_fill_price:.4f} x {ce_filled_qty}")
            
                        if pe_position:
                            pe_avg_fill_price = float(pe_position.get('entry_price', 0))
                            pe_filled_qty = abs(float(pe_position.get('size', 0)))
                            logger.info(f"✅ PE from position: ${pe_avg_fill_price:.4f} x {pe_filled_qty}")
            
                except Exception as e:
                    logger.error(f"Position fallback error: {e}")

            # ✅ FIXED: Final validation accepts both 'filled' and 'closed'
            if (ce_state not in ['filled', 'closed'] or 
                pe_state not in ['filled', 'closed'] or 
                ce_avg_fill_price == 0 or 
                pe_avg_fill_price == 0):
    
                logger.error(f"❌ Orders not completed - CE: {ce_state}, PE: {pe_state}")
                await query.edit_message_text(
                    "<b>❌ Entry Orders Failed</b>\n\n"
                    f"<b>CE:</b> {pending_trade['ce_symbol']}\n"
                    f"  Order ID: {ce_order_id}\n"
                    f"  Status: <code>{ce_state}</code>\n\n"
                    f"<b>PE:</b> {pending_trade['pe_symbol']}\n"
                    f"  Order ID: {pe_order_id}\n"
                    f"  Status: <code>{pe_state}</code>\n\n"
                    "<b>Possible reasons:</b>\n"
                    "• Insufficient margin\n"
                    "• Low liquidity\n"
                    "• Order rejected\n\n"
                    "<i>Check Delta Exchange for details</i>",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return

            logger.info(f"✅ Final - CE: ${ce_avg_fill_price:.4f} x {ce_filled_qty}, PE: ${pe_avg_fill_price:.4f} x {pe_filled_qty}")

            # Place SL and Target
            sl_orders_placed = []
            target_orders_placed = []
            
            logger.info("🔄 Placing SL/Target orders...")
            
            # Stop Loss
            if sl_trigger is not None and sl_limit is not None and sl_trigger > 0:
                try:
                    logger.info(f"📍 SL - Trigger: {sl_trigger}%, Limit: {sl_limit}%")
                    if side == 'sell':
                        ce_sl_trigger = ce_avg_fill_price * (1 + abs(float(sl_trigger)) / 100)
                        ce_sl_limit = ce_avg_fill_price * (1 + abs(float(sl_limit)) / 100)
                        pe_sl_trigger = pe_avg_fill_price * (1 + abs(float(sl_trigger)) / 100)
                        pe_sl_limit = pe_avg_fill_price * (1 + abs(float(sl_limit)) / 100)
                        sl_side = 'buy'
                    else:
                        ce_sl_trigger = ce_avg_fill_price * (1 - abs(float(sl_trigger)) / 100)
                        ce_sl_limit = ce_avg_fill_price * (1 - abs(float(sl_limit)) / 100)
                        pe_sl_trigger = pe_avg_fill_price * (1 - abs(float(sl_trigger)) / 100)
                        pe_sl_limit = pe_avg_fill_price * (1 - abs(float(sl_limit)) / 100)
                        sl_side = 'sell'
                    
                    ce_sl_order = await client.place_order({
                        'product_symbol': pending_trade['ce_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': sl_side,
                        'order_type': 'limit_order',
                        'limit_price': str(ce_sl_limit),
                        'stop_order_type': 'stop_loss_order',
                        'stop_price': str(ce_sl_trigger),
                        'reduce_only': True
                    })
                    
                    if ce_sl_order.get('success'):
                        sl_orders_placed.append(f"CE SL: {ce_sl_order['result']['id']}")
                        logger.info(f"✅ CE SL placed: {ce_sl_order['result']['id']}")
                    
                    pe_sl_order = await client.place_order({
                        'product_symbol': pending_trade['pe_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': sl_side,
                        'order_type': 'limit_order',
                        'limit_price': str(pe_sl_limit),
                        'stop_order_type': 'stop_loss_order',
                        'stop_price': str(pe_sl_trigger),
                        'reduce_only': True
                    })
                    
                    if pe_sl_order.get('success'):
                        sl_orders_placed.append(f"PE SL: {pe_sl_order['result']['id']}")
                        logger.info(f"✅ PE SL placed: {pe_sl_order['result']['id']}")
                    
                except Exception as e:
                    logger.error(f"❌ SL error: {e}", exc_info=True)
            else:
                logger.info("⚠️ No SL configured")

            # Target
            if target_trigger is not None and target_limit is not None and target_trigger > 0:
                try:
                    logger.info(f"📍 Target - Trigger: {target_trigger}%, Limit: {target_limit}%")
                    if side == 'sell':
                        ce_target_limit = ce_avg_fill_price * (1 - abs(float(target_limit)) / 100)
                        pe_target_limit = pe_avg_fill_price * (1 - abs(float(target_limit)) / 100)
                        target_side = 'buy'
                    else:
                        ce_target_limit = ce_avg_fill_price * (1 + abs(float(target_limit)) / 100)
                        pe_target_limit = pe_avg_fill_price * (1 + abs(float(target_limit)) / 100)
                        target_side = 'sell'
                    
                    ce_target_order = await client.place_order({
                        'product_symbol': pending_trade['ce_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': target_side,
                        'order_type': 'limit_order',
                        'limit_price': str(ce_target_limit),
                        'reduce_only': True
                    })
                    
                    if ce_target_order.get('success'):
                        target_orders_placed.append(f"CE Target: {ce_target_order['result']['id']}")
                    
                    pe_target_order = await client.place_order({
                        'product_symbol': pending_trade['pe_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': target_side,
                        'order_type': 'limit_order',
                        'limit_price': str(pe_target_limit),
                        'reduce_only': True
                    })
                    
                    if pe_target_order.get('success'):
                        target_orders_placed.append(f"PE Target: {pe_target_order['result']['id']}")
                    
                except Exception as e:
                    logger.error(f"❌ Target error: {e}", exc_info=True)
            else:
                logger.info("⚠️ No Target configured")

            logger.info(f"✅ Complete - SL: {len(sl_orders_placed)}, Target: {len(target_orders_placed)}")

            text = "<b>✅ Trade Executed!</b>\n\n"
            text += f"<b>Entry:</b>\n"
            text += f"<b>CE:</b> {pending_trade['ce_symbol']}\n"
            text += f"  ID: <code>{ce_order_id}</code>\n"
            text += f"  Fill: ${ce_avg_fill_price:.4f} x {ce_filled_qty}\n\n"
            text += f"<b>PE:</b> {pending_trade['pe_symbol']}\n"
            text += f"  ID: <code>{pe_order_id}</code>\n"
            text += f"  Fill: ${pe_avg_fill_price:.4f} x {pe_filled_qty}\n\n"
            
            if sl_orders_placed:
                text += f"<b>✅ Stop Loss ({len(sl_orders_placed)}):</b>\n"
                for sl in sl_orders_placed:
                    text += f"  • {sl}\n"
                text += "\n"
            else:
                text += "<b>⚠️ Stop Loss:</b> Not placed\n\n"
            
            if target_orders_placed:
                text += f"<b>✅ Target ({len(target_orders_placed)}):</b>\n"
                for target in target_orders_placed:
                    text += f"  • {target}\n"
                text += "\n"
            else:
                text += "<b>⚠️ Target:</b> Not placed\n\n"
            
            text += "<i>Check 'Open Orders' for status</i>"
            
            await query.edit_message_text(
                text,
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            
            log_user_action(
                user.id, 
                "manual_trade_execute", 
                f"Executed - SL: {len(sl_orders_placed)}, Target: {len(target_orders_placed)}"
            )
        
        finally:
            await client.close()
            context.user_data.pop('pending_trade', None)
    
    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>❌ Failed</b>\n\n{str(e)[:200]}",
            reply_markup=get_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        context.user_data.pop('pending_trade', None)


def register_manual_trade_handlers(application: Application):
    """Register manual trade handlers."""
    
    application.add_handler(CallbackQueryHandler(
        manual_trade_menu_callback,
        pattern="^menu_manual_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_trade_select_callback,
        pattern="^manual_trade_select_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_trade_execute_callback,
        pattern="^manual_trade_execute$"
    ))
    
    logger.info("Manual trade handlers registered")
