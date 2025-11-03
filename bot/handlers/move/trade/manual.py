"""
Manual MOVE Options Trade Execution Handler

WITH STRIKE CONFIRMATION - Includes fallback strike selection if exact ATM+offset not available.

Flow:
1. User clicks "Manual Move Trade" button
2. Select from presets list
3. Show market data + strike availability check
4. Confirm/fallback strike selection
5. Execute trade with SL/Target orders
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_trade_preset_ops import get_move_trade_presets, get_move_trade_preset_by_id
from database.operations.api_ops import get_api_credential_by_id, get_decrypted_api_credential
from database.operations.move_strategy_ops import get_move_strategy
from delta.client import DeltaClient

logger = setup_logger(__name__)


# ==================== KEYBOARDS ====================
def get_move_manual_trade_keyboard():
    """Get move manual trade keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== STEP 1: MENU DISPLAY ====================
@error_handler
async def move_manual_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual move trade execution menu - list presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    logger.info(f"🎯 User {user.id} opening MOVE manual trade menu")
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get user's move trade presets
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>🎯 Manual Move Trade Execution</b>\n\n"
            "❌ No trade presets found.\n\n"
            "Please create a Move Trade Preset first using the menu.",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🎯 {preset['preset_name']}",
            callback_data=f"move_manual_select_{preset['_id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    
    await query.edit_message_text(
        "<b>🎯 Manual Move Trade Execution</b>\n\n"
        f"Select a preset ({len(presets)} available):",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_manual_trade_menu", f"Viewed {len(presets)} presets")


# ==================== STEP 2: PRESET SELECTION & STRIKE CHECK ====================
@error_handler
async def move_manual_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - fetch details and check strike availability."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    logger.info(f"🎯 User {user.id} selected preset: {preset_id}")
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading trade details...</b>\n\n"
        "Fetching market data and checking strike availability...",
        parse_mode='HTML'
    )
    
    try:
        # Get preset
        preset = await get_move_trade_preset_by_id(preset_id)
        
        if not preset:
            await query.edit_message_text(
                "❌ Trade preset not found.",
                reply_markup=get_move_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Get API credentials
        api = await get_api_credential_by_id(preset['api_id'])
        if not api:
            await query.edit_message_text(
                "❌ API credential not found.",
                reply_markup=get_move_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        credentials = await get_decrypted_api_credential(preset['api_id'])
        if not credentials:
            await query.edit_message_text(
                "❌ Failed to decrypt API credentials.",
                reply_markup=get_move_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Get strategy
        strategy = await get_move_strategy(preset['strategy_id'])
        if not strategy:
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=get_move_manual_trade_keyboard(),
                parse_mode='HTML'
            )
            return

        # Handle both dict and Pydantic model
        if isinstance(strategy, dict):
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
        else:
            strategy_name = strategy.strategy_name
            asset = strategy.asset
            expiry = strategy.expiry
            direction = strategy.direction
            lot_size = strategy.lot_size
            atm_offset = strategy.atm_offset
            sl_trigger = strategy.stop_loss_trigger
            sl_limit = strategy.stop_loss_limit
            target_trigger = strategy.target_trigger
            target_limit = strategy.target_limit
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Import executor
            from bot.executors.move_executor import MoveTradeExecutor
            executor = MoveTradeExecutor(client)
            
            # Check strike availability
            result = await executor.find_atm_strike(asset, expiry)
            
            if not result:
                await query.edit_message_text(
                    f"❌ <b>No {expiry.title()} MOVE Contracts Available</b>\n\n"
                    f"Asset: {asset}\n"
                    f"Expiry: {expiry.title()}\n\n"
                    f"Please try:\n"
                    f"• Different expiry (Daily/Weekly/Monthly)\n"
                    f"• Check Delta Exchange for available MOVE contracts",
                    reply_markup=get_move_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                logger.warning(f"No MOVE contracts available for {asset} {expiry}")
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
                # ✅ EXACT STRIKE AVAILABLE
                target_strike = strikes[target_index]
                
                # Build confirmation message
                text = f"<b>🎯 Confirm Move Trade Execution</b>\n\n"
                text += f"<b>Preset:</b> {preset['preset_name']}\n"
                text += f"<b>API:</b> {api.api_name}\n"
                text += f"<b>Strategy:</b> {strategy_name}\n\n"
                text += f"<b>📊 Market Data:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${atm_strike:,.2f}\n"
                text += f"Target Strike: ${target_strike:,.2f} ({atm_offset:+d})\n"
                text += f"Expiry: {expiry.title()}\n\n"
                text += f"<b>💰 Trade Setup:</b>\n"
                text += f"Direction: {direction.title()}\n"
                text += f"Lot Size: {lot_size}\n"
                
                if sl_trigger:
                    text += f"Stop Loss: {sl_trigger:.0f}% trigger, {sl_limit:.0f}% limit\n"
                if target_trigger:
                    text += f"Target: {target_trigger:.0f}% trigger, {target_limit:.0f}% limit\n"
                
                text += "\n⚠️ Execute this trade?"
                
                # Store trade details in context
                context.user_data['pending_move_trade'] = {
                    'preset_id': preset_id,
                    'preset_name': preset['preset_name'],
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
                    'strike_price': target_strike,
                    'is_fallback': False
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
                logger.info(f"✅ Strike available: ${target_strike}")
            
            else:
                # ⚠️ EXACT STRIKE NOT AVAILABLE - OFFER FALLBACK
                if target_index < 0:
                    suggested_strike = strikes[0]
                    fallback_message = f"Requested strike (ATM{atm_offset:+d}) is below lowest available."
                else:
                    suggested_strike = strikes[-1]
                    fallback_message = f"Requested strike (ATM{atm_offset:+d}) is above highest available."
                
                # Build fallback message
                text = f"⚠️ <b>Requested Strike Unavailable</b>\n\n"
                text += f"{fallback_message}\n\n"
                text += f"<b>📊 Available Options:</b>\n"
                text += f"Spot Price: ${spot_price:,.2f}\n"
                text += f"ATM Strike: ${atm_strike:,.2f}\n"
                text += f"Requested: ${atm_strike + (atm_offset * (100 if asset == 'BTC' else 10)):,.2f}\n"
                text += f"Suggested: ${suggested_strike:,.2f}\n\n"
                text += f"<b>Available Strikes ({expiry.title()}):</b>\n"
                
                # Show up to 5 strikes
                for i, strike in enumerate(strikes[:5]):
                    if strike == atm_strike:
                        text += f"• ${strike:,.2f} ⭐ ATM\n"
                    else:
                        text += f"• ${strike:,.2f}\n"
                
                if len(strikes) > 5:
                    text += f"...and {len(strikes) - 5} more\n"
                
                text += f"\nUse suggested strike?"
                
                # Store trade details with fallback
                context.user_data['pending_move_trade'] = {
                    'preset_id': preset_id,
                    'preset_name': preset['preset_name'],
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
                    'strike_price': suggested_strike,
                    'is_fallback': True
                }
                
                # Show fallback confirmation
                keyboard = [
                    [InlineKeyboardButton(f"✅ Use ${suggested_strike:,.0f}", callback_data="move_manual_execute")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_manual_trade")]
                ]
                
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                logger.warning(f"⚠️ Using fallback strike: ${suggested_strike}")
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"❌ Failed to prepare move trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>❌ Error preparing trade</b>\n\n"
            f"Error: {str(e)[:200]}\n\n"
            f"Please try again.",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )


# ==================== STEP 3: EXECUTE TRADE ====================
@error_handler
async def move_manual_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the confirmed move trade."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get pending trade from context
    pending_trade = context.user_data.get('pending_move_trade')
    
    if not pending_trade:
        await query.edit_message_text(
            "❌ No pending trade found. Please start again.",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        return
    
    logger.info(f"🎯 Executing MOVE trade for user {user.id}")
    
    # Show executing message
    await query.edit_message_text(
        "⏳ <b>Executing MOVE trade...</b>\n\n"
        "📊 Finding contract...\n"
        "📈 Placing entry order...\n"
        "🛡️ Setting up SL/Target orders...",
        parse_mode='HTML'
    )
    
    try:
        # Create Delta client
        client = DeltaClient(pending_trade['api_key'], pending_trade['api_secret'])
        
        try:
            # Import executor
            from bot.executors.move_executor import MoveTradeExecutor
            executor = MoveTradeExecutor(client)
            
            # Execute trade
            result = await executor.execute_move_trade(
                asset=pending_trade['asset'],
                expiry=pending_trade['expiry'],
                direction=pending_trade['direction'],
                lot_size=pending_trade['lot_size'],
                strike_price=pending_trade['strike_price'],
                stop_loss_trigger=pending_trade['sl_trigger'],
                stop_loss_limit=pending_trade['sl_limit'],
                target_trigger=pending_trade['target_trigger'],
                target_limit=pending_trade['target_limit'],
            )
            
            if result.get('success'):
                # ✅ TRADE EXECUTED SUCCESSFULLY
                product = result.get('product', {})
                entry_price = result.get('entry_price', 0)
                
                text = "<b>✅ Move Trade Executed Successfully!</b>\n\n"
                text += f"<b>📊 Contract:</b> {product.get('symbol', 'N/A')}\n"
                text += f"<b>Strike:</b> ${pending_trade['strike_price']:,.2f}\n"
                text += f"<b>Expiry:</b> {pending_trade['expiry'].title()}\n"
                text += f"<b>Direction:</b> {pending_trade['direction'].title()}\n"
                text += f"<b>Lot Size:</b> {pending_trade['lot_size']}\n\n"
                text += f"<b>💰 Entry Price:</b> ${entry_price:.2f}\n"
                
                if pending_trade['sl_trigger']:
                    text += f"<b>🛑 Stop Loss:</b> {pending_trade['sl_trigger']:.0f}%\n"
                if pending_trade['target_trigger']:
                    text += f"<b>🎯 Target:</b> {pending_trade['target_trigger']:.0f}%\n"
                
                text += "\n✅ All orders placed successfully!"
                
                if pending_trade.get('is_fallback'):
                    text += f"\n\n⚠️ Used fallback strike: ${pending_trade['strike_price']:,.2f}"
                
                await query.edit_message_text(
                    text,
                    reply_markup=get_move_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                
                log_user_action(
                    user.id,
                    "move_manual_execute",
                    f"Executed {pending_trade['direction']} MOVE trade: {product.get('symbol')}"
                )
                logger.info(f"✅ MOVE trade executed for user {user.id}")
            else:
                # ❌ EXECUTION FAILED
                error_msg = result.get('error', 'Unknown error')
                await query.edit_message_text(
                    f"<b>❌ Trade Execution Failed</b>\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Please check your account and try again.",
                    reply_markup=get_move_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                logger.error(f"❌ Trade execution failed: {error_msg}")
        
        finally:
            await client.close()
            # Clear pending trade
            context.user_data.pop('pending_move_trade', None)
    
    except Exception as e:
        logger.error(f"❌ Exception in move_manual_execute_callback: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>❌ Trade Execution Failed</b>\n\n"
            f"Error: {str(e)[:200]}\n\n"
            f"Please try again or check your account.",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        # Clear pending trade
        context.user_data.pop('pending_move_trade', None)


# ==================== HANDLER REGISTRATION ====================
def register_move_manual_trade_handlers(application: Application):
    """Register move manual trade handlers - callback based only."""
    
    # GROUP 19: MOVE Manual Trade Callbacks
    application.add_handler(
        CallbackQueryHandler(
            move_manual_trade_menu_callback,
            pattern="^menu_move_manual_trade$",
            block=False
        ),
        group=19
    )
    
    application.add_handler(
        CallbackQueryHandler(
            move_manual_select_callback,
            pattern="^move_manual_select_",
            block=False
        ),
        group=19
    )
    
    application.add_handler(
        CallbackQueryHandler(
            move_manual_execute_callback,
            pattern="^move_manual_execute$",
            block=False
        ),
        group=19
    )
    
    logger.info("✅ MOVE Manual Trade handlers registered (Group 19)")


__all__ = [
    'move_manual_trade_menu_callback',
    'move_manual_select_callback',
    'move_manual_execute_callback',
    'register_move_manual_trade_handlers',
    'get_move_manual_trade_keyboard',
            ]
