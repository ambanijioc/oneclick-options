"""
Manual trade execution handler - uses saved presets.
"""

import asyncio
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
    
    # Get user's manual trade presets
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
    
    # Create keyboard with presets
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
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading trade details...</b>\n\n"
        "Fetching market data and calculating strikes...",
        parse_mode='HTML'
    )
    
    try:
        # Get preset
        preset = await get_manual_trade_preset(preset_id)
        
        if not preset:
            await query.edit_message_text(
                "❌ Trade preset not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # ✅ FIXED: Safe attribute access
        api_credential_id = safe_get_attr(preset, 'api_credential_id')
        strategy_preset_id = safe_get_attr(preset, 'strategy_preset_id')
        strategy_type = safe_get_attr(preset, 'strategy_type', 'straddle')
        preset_name = safe_get_attr(preset, 'preset_name', 'Unnamed')
        
        # Get API credentials
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
        
        # Get strategy
        strategy = await get_strategy_preset_by_id(strategy_preset_id)
        if not strategy:
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # ✅ FIXED: Safe attribute access for strategy
        asset = safe_get_attr(strategy, 'asset', 'BTC')
        direction = safe_get_attr(strategy, 'direction', 'short')
        lot_size = safe_get_attr(strategy, 'lot_size', 1)
        strategy_name = safe_get_attr(strategy, 'name', 'Unnamed Strategy')
        api_name = safe_get_attr(api, 'api_name', 'Unknown API')
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Get current spot price
            ticker_symbol = f"{asset}USD"
            ticker_response = await client.get_ticker(ticker_symbol)
    
            # ✅ Check if response is None
            if ticker_response is None:
                await query.edit_message_text(
                    "❌ Failed to connect to Delta Exchange API. Please try again later.",
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
    
            # ✅ Check if result exists
            if not ticker_response.get('result'):
                await query.edit_message_text(
                    "❌ Invalid response from Delta Exchange API.",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
    
            spot_price = float(ticker_response['result']['spot_price'])
            
            # Get available options
            products_response = await client.get_products(contract_types='call_options,put_options')
            
            if not products_response.get('success'):
                await query.edit_message_text(
                    f"❌ Failed to fetch options: {products_response.get('error', {}).get('message', 'Unknown error')}",
                    reply_markup=get_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            products = products_response['result']
            
            # Filter by asset and expiry
            filtered_options = [
                p for p in products
                if asset in p.get('symbol', '')
                and p.get('state') == 'live'
            ]
            
            # Calculate strikes based on strategy type
            if strategy_type == 'straddle':
                # Straddle: ATM with offset
                atm_offset = safe_get_attr(strategy, 'atm_offset', 0)
                target_strike = spot_price + atm_offset
    
                # Find nearest strike
                strikes = sorted(set(p['strike_price'] for p in filtered_options if p.get('strike_price')))
                atm_strike = min(strikes, key=lambda x: abs(float(x) - target_strike))
    
                # Find CE and PE at ATM
                ce_option = next((p for p in filtered_options 
                                 if p['strike_price'] == atm_strike 
                                 and 'C' in p['symbol']), None)
                pe_option = next((p for p in filtered_options 
                                 if p['strike_price'] == atm_strike 
                                 and 'P' in p['symbol']), None)
    
                if not ce_option or not pe_option:
                    await query.edit_message_text(
                        "❌ Could not find matching Call and Put options at the calculated strike.",
                        reply_markup=get_manual_trade_keyboard(),
                        parse_mode='HTML'
                    )
                    return
    
                # Calculate trade details
                ce_mark_price = float(ce_option.get('mark_price', 0) or 0)
                pe_mark_price = float(pe_option.get('mark_price', 0) or 0)
                total_premium = (ce_mark_price + pe_mark_price) * lot_size
    
                # Build confirmation message
                text = f"<b>🎯 Confirm Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset_name}\n"
                text += f"<b>API:</b> {api_name}\n"
                text += f"<b>Strategy:</b> {strategy_name}\n\n"
                text += f"<b>📊 Market Data:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${float(atm_strike):,.0f}\n\n"
                text += f"<b>🎲 Straddle Details:</b>\n"
                text += f"CE: {ce_option['symbol']}\n"
                text += f"  Mark: ${ce_mark_price:,.2f}\n"
                text += f"PE: {pe_option['symbol']}\n"
                text += f"  Mark: ${pe_mark_price:,.2f}\n\n"
                text += f"<b>💰 Trade Summary:</b>\n"
                text += f"Direction: {direction.title()}\n"
                text += f"Lot Size: {lot_size}\n"
                text += f"Total Premium: ${total_premium:,.2f}\n\n"
                text += "⚠️ Execute this trade?"
    
                # Store trade details in context for execution
                context.user_data['pending_trade'] = {
                    'preset_id': preset_id,
                    'ce_symbol': ce_option['symbol'],
                    'pe_symbol': pe_option['symbol'],
                    'strike': float(atm_strike),
                    'direction': direction,
                    'lot_size': lot_size,
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            
            else:  # strangle
                # Strangle: OTM strikes
                # ✅ FIXED: Safe nested attribute access
                otm_selection = safe_get_attr(strategy, 'otm_selection')
                if otm_selection:
                    otm_type = safe_get_attr(otm_selection, 'type', 'percentage')
                    otm_value = safe_get_attr(otm_selection, 'value', 0)
                else:
                    # Fallback defaults
                    otm_type = 'percentage'
                    otm_value = 0
                
                if otm_type == 'percentage':
                    # Percentage-based: from spot price
                    offset = spot_price * (otm_value / 100)
                    ce_target = spot_price + offset
                    pe_target = spot_price - offset
                else:
                    # Numeral-based: from ATM
                    strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
                    atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
                    atm_index = strikes.index(atm_strike)
        
                    # Get strikes N positions away
                    num_strikes = int(otm_value)
                    ce_target = strikes[min(atm_index + num_strikes, len(strikes) - 1)]
                    pe_target = strikes[max(atm_index - num_strikes, 0)]
    
                # Find nearest strikes
                strikes = sorted(set(float(p['strike_price']) for p in filtered_options if p.get('strike_price')))
                ce_strike = min(strikes, key=lambda x: abs(x - ce_target))
                pe_strike = min(strikes, key=lambda x: abs(x - pe_target))
    
                # Find CE and PE
                ce_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == ce_strike 
                                 and 'C' in p['symbol']), None)
                pe_option = next((p for p in filtered_options 
                                 if float(p['strike_price']) == pe_strike 
                                 and 'P' in p['symbol']), None)
    
                if not ce_option or not pe_option:
                    await query.edit_message_text(
                        "❌ Could not find matching Call and Put options at the calculated strikes.",
                        reply_markup=get_manual_trade_keyboard(),
                        parse_mode='HTML'
                    )
                    return
    
                # Calculate trade details
                ce_mark_price = float(ce_option.get('mark_price', 0) or 0)
                pe_mark_price = float(pe_option.get('mark_price', 0) or 0)
                total_premium = (ce_mark_price + pe_mark_price) * lot_size
    
                # Build confirmation message
                otm_desc = f"{otm_value}% (Spot-based)" if otm_type == 'percentage' else f"{int(otm_value)} strikes (ATM-based)"
    
                text = f"<b>🎯 Confirm Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset_name}\n"
                text += f"<b>API:</b> {api_name}\n"
                text += f"<b>Strategy:</b> {strategy_name}\n\n"
                text += f"<b>📊 Market Data:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"OTM Selection: {otm_desc}\n\n"
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
    
                # Store trade details in context for execution
                context.user_data['pending_trade'] = {
                    'preset_id': preset_id,
                    'ce_symbol': ce_option['symbol'],
                    'pe_symbol': pe_option['symbol'],
                    'ce_strike': ce_strike,
                    'pe_strike': pe_strike,
                    'direction': direction,
                    'lot_size': lot_size,
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            
            # Show confirmation
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
            f"❌ Error preparing trade: {str(e)[:200]}",
            reply_markup=get_manual_trade_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def manual_trade_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the confirmed trade with SL and Target orders."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get pending trade from context
    pending_trade = context.user_data.get('pending_trade')
    
    if not pending_trade:
        await query.edit_message_text(
            "❌ No pending trade found. Please start again.",
            reply_markup=get_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Show executing message
    await query.edit_message_text(
        "⏳ <b>Executing trade...</b>\n\n"
        "Placing entry orders...",
        parse_mode='HTML'
    )
    
    try:
        # Get preset and strategy for SL/Target settings
        preset = await get_manual_trade_preset(pending_trade['preset_id'])
        strategy_preset_id = safe_get_attr(preset, 'strategy_preset_id')
        strategy = await get_strategy_preset_by_id(strategy_preset_id)
        
        # Extract SL/Target settings
        sl_trigger = (
            safe_get_attr(strategy, 'stop_loss_trigger') or 
            safe_get_attr(strategy, 'sl_trigger_percentage') or
            safe_get_attr(strategy, 'sl_trigger')
        )
        
        sl_limit = (
            safe_get_attr(strategy, 'stop_loss_limit') or 
            safe_get_attr(strategy, 'sl_limit_percentage') or
            safe_get_attr(strategy, 'sl_limit')
        )
        
        target_trigger = (
            safe_get_attr(strategy, 'target_trigger') or 
            safe_get_attr(strategy, 'target_percentage') or
            safe_get_attr(strategy, 'target_trigger_percentage')
        )
        
        target_limit = (
            safe_get_attr(strategy, 'target_limit') or 
            safe_get_attr(strategy, 'target_limit_percentage') or
            safe_get_attr(strategy, 'target_limit_pct')
        )
        
        # Create Delta client
        client = DeltaClient(pending_trade['api_key'], pending_trade['api_secret'])
        
        try:
            # Determine order side based on direction
            side = 'buy' if pending_trade['direction'] == 'long' else 'sell'
            
            # ========== PLACE CE ENTRY ORDER ==========
            ce_order = await client.place_order({
                'product_symbol': pending_trade['ce_symbol'],
                'size': pending_trade['lot_size'],
                'side': side,
                'order_type': 'market_order'
            })
            
            if not ce_order.get('success'):
                raise Exception(f"CE order failed: {ce_order.get('error', {}).get('message', 'Unknown error')}")
            
            ce_order_id = ce_order['result']['id']
            ce_avg_fill_price = float(ce_order['result'].get('avg_fill_price', 0))
            
            # ========== PLACE PE ENTRY ORDER ==========
            pe_order = await client.place_order({
                'product_symbol': pending_trade['pe_symbol'],
                'size': pending_trade['lot_size'],
                'side': side,
                'order_type': 'market_order'
            })
            
            if not pe_order.get('success'):
                raise Exception(f"PE order failed: {pe_order.get('error', {}).get('message', 'Unknown error')}")
            
            pe_order_id = pe_order['result']['id']
            pe_avg_fill_price = float(pe_order['result'].get('avg_fill_price', 0))
            
            logger.info(f"✅ Entry orders placed - CE: {ce_order_id}, PE: {pe_order_id}")
            
            # ========== PLACE STOP-LOSS & TARGET ORDERS ==========
            sl_orders_placed = []
            target_orders_placed = []
            
            # Wait briefly for orders to fully process
            await asyncio.sleep(0.5)
            
            if sl_trigger and sl_limit:
                try:
                    # For SHORT (sell): SL when price INCREASES
                    # For LONG (buy): SL when price DECREASES
                    
                    if side == 'sell':
                        # Short position: SL when price goes UP
                        ce_sl_trigger = ce_avg_fill_price * (1 + abs(sl_trigger) / 100)
                        ce_sl_limit = ce_avg_fill_price * (1 + abs(sl_limit) / 100)
                        pe_sl_trigger = pe_avg_fill_price * (1 + abs(sl_trigger) / 100)
                        pe_sl_limit = pe_avg_fill_price * (1 + abs(sl_limit) / 100)
                        sl_side = 'buy'  # Close short with buy
                    else:
                        # Long position: SL when price goes DOWN
                        ce_sl_trigger = ce_avg_fill_price * (1 - abs(sl_trigger) / 100)
                        ce_sl_limit = ce_avg_fill_price * (1 - abs(sl_limit) / 100)
                        pe_sl_trigger = pe_avg_fill_price * (1 - abs(sl_trigger) / 100)
                        pe_sl_limit = pe_avg_fill_price * (1 - abs(sl_limit) / 100)
                        sl_side = 'sell'  # Close long with sell
                    
                    logger.info(f"CE SL - Trigger: ${ce_sl_trigger:.4f}, Limit: ${ce_sl_limit:.4f}")
                    logger.info(f"PE SL - Trigger: ${pe_sl_trigger:.4f}, Limit: ${pe_sl_limit:.4f}")
                    
                    # Place SL for CE
                    ce_sl_order = await client.place_order({
                        'product_symbol': pending_trade['ce_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': sl_side,
                        'order_type': 'stop_loss_order',
                        'stop_order_type': 'stop_loss_order',
                        'stop_price': str(ce_sl_trigger),
                        'limit_price': str(ce_sl_limit),
                        'stop_trigger_method': 'mark_price'  # Use mark price for trigger
                    })
                    
                    if ce_sl_order.get('success'):
                        sl_orders_placed.append(f"CE SL: {ce_sl_order['result']['id']}")
                        logger.info(f"✅ CE SL order placed: {ce_sl_order['result']['id']}")
                    else:
                        logger.error(f"❌ CE SL failed: {ce_sl_order.get('error')}")
                    
                    # Place SL for PE
                    pe_sl_order = await client.place_order({
                        'product_symbol': pending_trade['pe_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': sl_side,
                        'order_type': 'stop_loss_order',
                        'stop_order_type': 'stop_loss_order',
                        'stop_price': str(pe_sl_trigger),
                        'limit_price': str(pe_sl_limit),
                        'stop_trigger_method': 'mark_price'
                    })
                    
                    if pe_sl_order.get('success'):
                        sl_orders_placed.append(f"PE SL: {pe_sl_order['result']['id']}")
                        logger.info(f"✅ PE SL order placed: {pe_sl_order['result']['id']}")
                    else:
                        logger.error(f"❌ PE SL failed: {pe_sl_order.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Failed to place SL orders: {e}", exc_info=True)
            
            if target_trigger and target_limit:
                try:
                    # For both LONG and SHORT: Target is when price moves favorably
                    
                    if side == 'sell':
                        # Short position: Target when price goes DOWN
                        ce_target_limit = ce_avg_fill_price * (1 - abs(target_limit) / 100)
                        pe_target_limit = pe_avg_fill_price * (1 - abs(target_limit) / 100)
                        target_side = 'buy'  # Close short with buy
                    else:
                        # Long position: Target when price goes UP
                        ce_target_limit = ce_avg_fill_price * (1 + abs(target_limit) / 100)
                        pe_target_limit = pe_avg_fill_price * (1 + abs(target_limit) / 100)
                        target_side = 'sell'  # Close long with sell
                    
                    logger.info(f"CE Target Limit: ${ce_target_limit:.4f}")
                    logger.info(f"PE Target Limit: ${pe_target_limit:.4f}")
                    
                    # Place Target for CE (limit order)
                    ce_target_order = await client.place_order({
                        'product_symbol': pending_trade['ce_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': target_side,
                        'order_type': 'limit_order',
                        'limit_price': str(ce_target_limit)
                    })
                    
                    if ce_target_order.get('success'):
                        target_orders_placed.append(f"CE Target: {ce_target_order['result']['id']}")
                        logger.info(f"✅ CE Target order placed: {ce_target_order['result']['id']}")
                    else:
                        logger.error(f"❌ CE Target failed: {ce_target_order.get('error')}")
                    
                    # Place Target for PE (limit order)
                    pe_target_order = await client.place_order({
                        'product_symbol': pending_trade['pe_symbol'],
                        'size': pending_trade['lot_size'],
                        'side': target_side,
                        'order_type': 'limit_order',
                        'limit_price': str(pe_target_limit)
                    })
                    
                    if pe_target_order.get('success'):
                        target_orders_placed.append(f"PE Target: {pe_target_order['result']['id']}")
                        logger.info(f"✅ PE Target order placed: {pe_target_order['result']['id']}")
                    else:
                        logger.error(f"❌ PE Target failed: {pe_target_order.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Failed to place Target orders: {e}", exc_info=True)
            
            # Build success message
            text = "<b>✅ Trade Executed Successfully!</b>\n\n"
            text += f"<b>Entry Orders:</b>\n"
            text += f"CE: {pending_trade['ce_symbol']}\n"
            text += f"  Order ID: {ce_order_id}\n"
            text += f"  Fill Price: ${ce_avg_fill_price:.2f}\n\n"
            text += f"PE: {pending_trade['pe_symbol']}\n"
            text += f"  Order ID: {pe_order_id}\n"
            text += f"  Fill Price: ${pe_avg_fill_price:.2f}\n\n"
            
            if sl_orders_placed:
                text += f"<b>✅ Stop Loss Orders:</b>\n"
                for sl in sl_orders_placed:
                    text += f"  {sl}\n"
                text += "\n"
            
            if target_orders_placed:
                text += f"<b>✅ Target Orders:</b>\n"
                for target in target_orders_placed:
                    text += f"  {target}\n"
                text += "\n"
            
            text += "Check 'Open Orders' and 'Positions' for live updates."
            
            await query.edit_message_text(
                text,
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            
            log_user_action(
                user.id, 
                "manual_trade_execute", 
                f"Executed {pending_trade['direction']} trade with {len(sl_orders_placed)} SL + {len(target_orders_placed)} Target orders"
            )
        
        finally:
            await client.close()
            context.user_data.pop('pending_trade', None)
    
    except Exception as e:
        logger.error(f"Failed to execute trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>❌ Trade Execution Failed</b>\n\n"
            f"Error: {str(e)[:200]}\n\n"
            f"Please try again or check your account.",
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
