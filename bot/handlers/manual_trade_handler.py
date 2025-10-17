"""
Manual trade execution handler - uses saved presets.
"""

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
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"manual_trade_select_{preset['id']}"
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
        
        # Get API credentials
        api = await get_api_credential_by_id(preset['api_credential_id'])
        if not api:
            await query.edit_message_text(
                "❌ API credential not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        credentials = await get_decrypted_api_credential(preset['api_credential_id'])
        if not credentials:
            await query.edit_message_text(
                "❌ Failed to decrypt API credentials.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Get strategy
        strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
        if not strategy:
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Get current spot price
            ticker_symbol = f"{strategy.asset}USD"
            ticker_response = await client.get_ticker(ticker_symbol)
    
            # ✅ ADDED: Check if response is None
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
    
            # ✅ ADDED: Check if result exists
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
                if strategy.asset in p.get('symbol', '')
                and p.get('state') == 'live'
            ]
            
            # Calculate strikes based on strategy type
            if preset['strategy_type'] == 'straddle':
                # Straddle: ATM with offset
                atm_offset = getattr(strategy, 'atm_offset', 0)
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
                total_premium = (ce_mark_price + pe_mark_price) * strategy.lot_size
    
                # Build confirmation message
                text = f"<b>🎯 Confirm Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset['preset_name']}\n"
                text += f"<b>API:</b> {api.api_name}\n"
                text += f"<b>Strategy:</b> {strategy.name}\n\n"
                text += f"<b>📊 Market Data:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${float(atm_strike):,.0f}\n\n"
                text += f"<b>🎲 Straddle Details:</b>\n"
                text += f"CE: {ce_option['symbol']}\n"
                text += f"  Mark: ${ce_mark_price:,.2f}\n"
                text += f"PE: {pe_option['symbol']}\n"
                text += f"  Mark: ${pe_mark_price:,.2f}\n\n"
                text += f"<b>💰 Trade Summary:</b>\n"
                text += f"Direction: {strategy.direction.title()}\n"
                text += f"Lot Size: {strategy.lot_size}\n"
                text += f"Total Premium: ${total_premium:,.2f}\n\n"
                text += "⚠️ Execute this trade?"
    
                # Store trade details in context for execution
                context.user_data['pending_trade'] = {
                    'preset_id': preset_id,
                    'ce_symbol': ce_option['symbol'],
                    'pe_symbol': pe_option['symbol'],
                    'strike': float(atm_strike),
                    'direction': strategy.direction,
                    'lot_size': strategy.lot_size,
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            
            else:  # strangle
                # Strangle: OTM strikes
                # ✅ CORRECT:
                otm_selection = getattr(strategy, 'otm_selection', None)
                if otm_selection:
                    # otm_selection is a Pydantic model, use dot notation
                    otm_type = getattr(otm_selection, 'type', 'percentage')
                    otm_value = getattr(otm_selection, 'value', 0)
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
                # ✅ FIXED: Use dot notation
                total_premium = (ce_mark_price + pe_mark_price) * strategy.lot_size
    
                # Build confirmation message
                otm_desc = f"{otm_value}% (Spot-based)" if otm_type == 'percentage' else f"{int(otm_value)} strikes (ATM-based)"
    
                text = f"<b>🎯 Confirm Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset['preset_name']}\n"
                # ✅ FIXED: Use dot notation for api and strategy
                text += f"<b>API:</b> {api.api_name}\n"
                text += f"<b>Strategy:</b> {strategy.name}\n\n"
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
                # ✅ FIXED: Use dot notation
                text += f"Direction: {strategy.direction.title()}\n"
                text += f"Lot Size: {strategy.lot_size}\n"
                text += f"Total Premium: ${total_premium:,.2f}\n\n"
                text += "⚠️ Execute this trade?"
    
                # Store trade details in context for execution
                context.user_data['pending_trade'] = {
                    'preset_id': preset_id,
                    'ce_symbol': ce_option['symbol'],
                    'pe_symbol': pe_option['symbol'],
                    'ce_strike': ce_strike,
                    'pe_strike': pe_strike,
                    # ✅ FIXED: Use dot notation
                    'direction': strategy.direction,
                    'lot_size': strategy.lot_size,
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
    """Execute the confirmed trade."""
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
        "Placing orders...",
        parse_mode='HTML'
    )
    
    try:
        # Create Delta client
        client = DeltaClient(pending_trade['api_key'], pending_trade['api_secret'])
        
        try:
            # Determine order side based on direction
            side = 'buy' if pending_trade['direction'] == 'long' else 'sell'
            
            # ✅ CORRECT:
            ce_order = await client.place_order({
                'product_symbol': pending_trade['ce_symbol'],
                'size': pending_trade['lot_size'],
                'side': side,
                'order_type': 'market'
            })
            
            if not ce_order.get('success'):
                raise Exception(f"CE order failed: {ce_order.get('error', {}).get('message', 'Unknown error')}")
            
            # ✅ CORRECT:
            pe_order = await client.place_order({
                'product_symbol': pending_trade['pe_symbol'],
                'size': pending_trade['lot_size'],
                'side': side,
                'order_type': 'market'
            })
            
            if not pe_order.get('success'):
                raise Exception(f"PE order failed: {pe_order.get('error', {}).get('message', 'Unknown error')}")
            
            # Success
            text = "<b>✅ Trade Executed Successfully!</b>\n\n"
            text += f"<b>CE Order:</b> {pending_trade['ce_symbol']}\n"
            text += f"Order ID: {ce_order['result']['id']}\n\n"
            text += f"<b>PE Order:</b> {pending_trade['pe_symbol']}\n"
            text += f"Order ID: {pe_order['result']['id']}\n\n"
            text += "Check your positions for details."
            
            await query.edit_message_text(
                text,
                reply_markup=get_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            
            log_user_action(user.id, "manual_trade_execute", f"Executed {pending_trade['direction']} trade")
        
        finally:
            await client.close()
            # Clear pending trade
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
        
        # Clear pending trade
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
                                                  
