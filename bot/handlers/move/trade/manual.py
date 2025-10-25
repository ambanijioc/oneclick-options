"""
MOVE Manual Trade Execution Handler

Handles immediate manual execution of MOVE trades with:
- Preset selection
- Strike availability checking
- Fallback strike suggestions
- Real-time order placement
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_trade_preset_ops import get_move_trade_presets, get_move_trade_preset_by_id
from database.operations.api_ops import get_api_credential_by_id, get_decrypted_api_credential
from database.operations.move_strategy_ops import get_move_strategy
from delta.client import DeltaClient
from bot.keyboards.move_strategy_keyboards import get_move_menu_keyboard

logger = setup_logger(__name__)

@error_handler
async def move_manual_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual MOVE trade execution menu - list presets."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE manual trade menu")
    
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "🎯 Manual MOVE Trade Execution\n\n"
            "❌ No trade presets found.\n\n"
            "Please create a MOVE Trade Preset first.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"move_manual_select_{preset['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move")])
    
    await query.edit_message_text(
        "🎯 Manual MOVE Trade Execution\n\n"
        f"Found {len(presets)} preset(s)\n\n"
        "Select a trade preset to execute:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

@error_handler
async def move_manual_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - fetch details and check strike availability."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    await query.edit_message_text(
        "⏳ Loading trade details...\n\n"
        "Fetching market data and checking strike availability...",
        parse_mode='HTML'
    )
    
    try:
        # Get preset
        preset = await get_move_trade_preset_by_id(user.id, preset_id)
        if not preset:
            await query.edit_message_text(
                "❌ Trade preset not found.",
                reply_markup=get_move_menu_keyboard()
            )
            return
        
        # Get API credentials
        api = await get_api_credential_by_id(user.id, preset['api_id'])
        if not api:
            await query.edit_message_text(
                "❌ API credential not found.",
                reply_markup=get_move_menu_keyboard()
            )
            return
        
        credentials = await get_decrypted_api_credential(preset['api_id'])
        if not credentials:
            await query.edit_message_text(
                "❌ Failed to decrypt API credentials.",
                reply_markup=get_move_menu_keyboard()
            )
            return
        
        # Get strategy
        strategy = await get_move_strategy(user.id, preset['strategy_id'])
        if not strategy:
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=get_move_menu_keyboard()
            )
            return
        
        # Extract strategy data
        strategy_name = strategy.get('strategy_name', 'N/A')
        asset = strategy.get('asset', 'BTC')
        expiry = strategy.get('expiry', 'daily')
        direction = strategy.get('direction', 'long')
        lot_size = strategy.get('lot_size', 1)
        atm_offset = strategy.get('atm_offset', 0)
        sl_trigger = strategy.get('stop_loss_trigger')
        sl_limit = strategy.get('stop_loss_limit')
        target_trigger = strategy.get('target_trigger')
        target_limit = strategy.get('target_limit')
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Check strike availability
            from bot.executors.move_executor import MoveTradeExecutor
            executor = MoveTradeExecutor(client)
            
            result = await executor.find_atm_strike(asset, expiry)
            
            if not result:
                await query.edit_message_text(
                    f"❌ No {expiry.title()} MOVE Contracts Available\n\n"
                    f"Asset: {asset}\n"
                    f"Expiry: {expiry.title()}\n\n"
                    f"Please try:\n"
                    f"• Different expiry (Daily/Weekly/Monthly)\n"
                    f"• Check Delta Exchange for available MOVE contracts",
                    reply_markup=get_move_menu_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            atm_strike, contracts = result
            spot_price = await client.get_spot_price(asset)
            
            # Get available strikes
            strikes = sorted(set(float(c.get('strike_price', 0)) for c in contracts if c.get('strike_price')))
            
            # Calculate target strike with offset
            atm_index = strikes.index(atm_strike)
            target_index = atm_index + atm_offset
            
            # Check if target strike is available
            exact_strike_available = 0 <= target_index < len(strikes)
            
            if exact_strike_available:
                target_strike = strikes[target_index]
                
                # Build confirmation message
                text = f"🎯 Confirm MOVE Trade Execution\n\n"
                text += f"Preset: {preset['preset_name']}\n"
                text += f"API: {api['api_name']}\n"
                text += f"Strategy: {strategy_name}\n\n"
                text += f"📊 Market Data:\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${atm_strike:,.2f}\n"
                text += f"Target Strike: ${target_strike:,.2f} ({atm_offset:+d})\n"
                text += f"Expiry: {expiry.title()}\n\n"
                text += f"💰 Trade Setup:\n"
                text += f"Direction: {direction.title()}\n"
                text += f"Lot Size: {lot_size}\n"
                
                if sl_trigger:
                    text += f"Stop Loss: {sl_trigger:.0f}% trigger, {sl_limit:.0f}% limit\n"
                if target_trigger:
                    text += f"Target: {target_trigger:.0f}% trigger, {target_limit:.0f}% limit\n"
                
                text += "\n⚠️ Execute this trade?"
                
                # Store trade details
                context.user_data['pending_move_trade'] = {
                    'preset_id': preset_id,
                    'asset': asset,
                    'expiry': expiry,
                    'direction': direction,
                    'lot_size': lot_size,
                    'atm_offset': atm_offset,
                    'sl_trigger': sl_trigger,
                    'sl_limit': sl_limit,
                    'target_trigger': target_trigger,
                    'target_limit': target_limit,
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'fallback_direction': None
                }
                
                # Show confirmation
                keyboard = [
                    [InlineKeyboardButton("✅ Execute Trade", callback_data="move_manual_execute")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_manual_trade")]
                ]
                
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
            else:
                # Strike not available - offer alternatives
                if target_index < 0:
                    suggested_strike = strikes[0]
                    fallback_direction = "down"
                    message = f"Requested strike (ATM{atm_offset:+d}) is below lowest available."
                else:
                    suggested_strike = strikes[-1]
                    fallback_direction = "up"
                    message = f"Requested strike (ATM{atm_offset:+d}) is above highest available."
                
                # Build fallback message
                text = f"⚠️ Requested Strike Unavailable\n\n"
                text += f"{message}\n\n"
                text += f"📊 Available Options:\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${atm_strike:,.2f}\n"
                text += f"Suggested: ${suggested_strike:,.2f}\n\n"
                text += f"Available Strikes ({expiry.title()}):\n"
                
                for i, strike in enumerate(strikes[:5]):
                    if strike == atm_strike:
                        text += f"• ${strike:,.2f} ⭐ ATM\n"
                    else:
                        text += f"• ${strike:,.2f}\n"
                
                if len(strikes) > 5:
                    text += f"...and {len(strikes) - 5} more\n"
                
                text += f"\nUse suggested strike (${suggested_strike:,.2f})?"
                
                # Store trade details with fallback
                context.user_data['pending_move_trade'] = {
                    'preset_id': preset_id,
                    'asset': asset,
                    'expiry': expiry,
                    'direction': direction,
                    'lot_size': lot_size,
                    'atm_offset': atm_offset,
                    'sl_trigger': sl_trigger,
                    'sl_limit': sl_limit,
                    'target_trigger': target_trigger,
                    'target_limit': target_limit,
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'fallback_direction': fallback_direction,
                    'suggested_strike': suggested_strike
                }
                
                keyboard = [
                    [InlineKeyboardButton(f"✅ Use ${suggested_strike:,.0f} Strike", callback_data="move_manual_execute_fallback")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_manual_trade")]
                ]
                
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to prepare move trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error preparing trade: {str(e)[:200]}",
            reply_markup=get_move_menu_keyboard()
        )

@error_handler
async def move_manual_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the confirmed MOVE trade (exact strike)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    pending_trade = context.user_data.get('pending_move_trade')
    
    if not pending_trade:
        await query.edit_message_text(
            "❌ No pending trade found. Please start again.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    await query.edit_message_text(
        "⏳ Executing MOVE trade...\n\n"
        "📊 Finding contract...\n"
        "📈 Placing entry order...\n"
        "🛡️ Setting up SL/Target orders...",
        parse_mode='HTML'
    )
    
    await _execute_move_trade(query, context, user, pending_trade, fallback=False)

@error_handler
async def move_manual_execute_fallback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the MOVE trade with fallback strike."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    pending_trade = context.user_data.get('pending_move_trade')
    
    if not pending_trade:
        await query.edit_message_text(
            "❌ No pending trade found. Please start again.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    await query.edit_message_text(
        "⏳ Executing MOVE trade (fallback strike)...\n\n"
        "📊 Finding contract...\n"
        "📈 Placing entry order...\n"
        "🛡️ Setting up SL/Target orders...",
        parse_mode='HTML'
    )
    
    await _execute_move_trade(query, context, user, pending_trade, fallback=True)

async def _execute_move_trade(query, context, user, pending_trade: dict, fallback: bool):
    """Internal helper to execute MOVE trade."""
    try:
        client = DeltaClient(pending_trade['api_key'], pending_trade['api_secret'])
        
        try:
            from bot.executors.move_executor import MoveTradeExecutor
            executor = MoveTradeExecutor(client)
            
            result = await executor.execute_move_trade(
                asset=pending_trade['asset'],
                expiry=pending_trade['expiry'],
                direction=pending_trade['direction'],
                lot_size=pending_trade['lot_size'],
                atm_offset=pending_trade['atm_offset'],
                stop_loss_trigger=pending_trade['sl_trigger'],
                stop_loss_limit=pending_trade['sl_limit'],
                target_trigger=pending_trade['target_trigger'],
                target_limit=pending_trade['target_limit'],
                fallback_direction=pending_trade.get('fallback_direction') if fallback else None
            )
            
            if result['success']:
                product = result['product']
                strike_price = result['strike_price']
                entry_price = result['entry_price']
                sl_trigger = result.get('sl_trigger')
                target_trigger = result.get('target_trigger')
                
                text = "✅ MOVE Trade Executed Successfully!\n\n"
                text += f"📊 Contract: {product['symbol']}\n"
                text += f"Strike: ${strike_price:,.2f}\n"
                text += f"Expiry: {pending_trade['expiry'].title()}\n"
                text += f"Direction: {pending_trade['direction'].title()}\n"
                text += f"Lot Size: {pending_trade['lot_size']}\n\n"
                text += f"💰 Entry Price: ${entry_price:.2f}\n"
                
                if sl_trigger:
                    text += f"🛑 Stop Loss: ${sl_trigger:.2f}\n"
                if target_trigger:
                    text += f"🎯 Target: ${target_trigger:.2f}\n"
                
                text += "\n✅ All orders placed successfully!"
                
                if fallback:
                    text += f"\n\n⚠️ Used fallback strike: ${strike_price:,.2f}"
                
                await query.edit_message_text(
                    text,
                    reply_markup=get_move_menu_keyboard(),
                    parse_mode='HTML'
                )
                
                log_user_action(
                    user.id,
                    "move_manual_execute",
                    f"Executed {pending_trade['direction']} MOVE trade: {product['symbol']}"
                )
            else:
                await query.edit_message_text(
                    f"❌ Trade Execution Failed\n\n"
                    f"Error: {result.get('error', 'Unknown error')}\n\n"
                    f"Please check your account and try again.",
                    reply_markup=get_move_menu_keyboard(),
                    parse_mode='HTML'
                )
        
        finally:
            await client.close()
        
        context.user_data.pop('pending_move_trade', None)
    
    except Exception as e:
        logger.error(f"Failed to execute MOVE trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Trade Execution Failed\n\n"
            f"Error: {str(e)[:200]}\n\n"
            f"Please try again or check your account.",
            reply_markup=get_move_menu_keyboard()
        )
        context.user_data.pop('pending_move_trade', None)

# ✅✅ REGISTRATION FUNCTION ✅✅
def register_move_manual_trade_handlers(application: Application):
    """Register MOVE manual trade handlers."""
    application.add_handler(CallbackQueryHandler(move_manual_trade_callback, pattern="^menu_move_manual_trade$"))
    application.add_handler(CallbackQueryHandler(move_manual_select_callback, pattern="^move_manual_select_"))
    application.add_handler(CallbackQueryHandler(move_manual_execute_callback, pattern="^move_manual_execute$"))
    application.add_handler(CallbackQueryHandler(move_manual_execute_fallback_callback, pattern="^move_manual_execute_fallback$"))
    logger.info("✓ MOVE manual trade handlers registered")

__all__ = [
    'register_move_manual_trade_handlers',
    'move_manual_trade_callback',
    'move_manual_select_callback',
    'move_manual_execute_callback',
    'move_manual_execute_fallback_callback',
]
                    
