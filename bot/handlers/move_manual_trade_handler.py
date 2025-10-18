"""
Manual move options trade execution handler - uses saved presets.
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


def get_move_manual_trade_keyboard():
    """Get move manual trade keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_manual_trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual move trade execution menu - list presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
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
    keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")])
    
    await query.edit_message_text(
        "<b>🎯 Manual Move Trade Execution</b>\n\n"
        "Select a trade preset to execute:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_manual_trade_menu", f"Viewed {len(presets)} trade presets")


@error_handler
async def move_manual_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset selection - fetch details and show confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading trade details...</b>\n\n"
        "Fetching market data and calculating positions...",
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

        # ✅ ADDED: Handle both dict and Pydantic model
        if isinstance(strategy, dict):
            # It's a dict from MongoDB
            strategy_name = strategy.get('strategy_name', 'N/A')
            asset = strategy.get('asset', 'BTC')
            direction = strategy.get('direction', 'long')
            lot_size = strategy.get('lot_size', 1)
            atm_offset = strategy.get('atm_offset', 0)
        else:
            # It's a Pydantic model
            strategy_name = strategy.strategy_name
            asset = strategy.asset
            direction = strategy.direction
            lot_size = strategy.lot_size
            atm_offset = strategy.atm_offset
        
        # Create Delta client
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Get current spot price - ✅ FIXED: Use variable instead of strategy.asset
            ticker_symbol = f"{asset}USD"
            ticker_response = await client.get_ticker(ticker_symbol)
    
            if ticker_response is None or not ticker_response.get('success') or not ticker_response.get('result'):
                await query.edit_message_text(
                    "❌ Failed to fetch market data from Delta Exchange API.",
                    reply_markup=get_move_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            spot_price = float(ticker_response['result']['spot_price'])
    
            # Build confirmation message - ✅ FIXED: Use variables
            text = f"<b>🎯 Confirm Move Trade Execution</b>\n\n"
            text += f"<b>Preset:</b> {preset['preset_name']}\n"
            text += f"<b>API:</b> {api.api_name}\n"
            text += f"<b>Strategy:</b> {strategy_name}\n\n"
            text += f"<b>📊 Market Data:</b>\n"
            text += f"Spot Price: ${spot_price:,.2f}\n"
            text += f"ATM Offset: {atm_offset:+d}\n\n"
            text += f"<b>💰 Trade Summary:</b>\n"
            text += f"Direction: {direction.title()}\n"
            text += f"Lot Size: {lot_size}\n\n"
            text += "⚠️ Execute this trade?"
            
            # Store trade details in context for execution - ✅ FIXED: Use variables
            context.user_data['pending_move_trade'] = {
                'preset_id': preset_id,
                'direction': direction,
                'lot_size': lot_size,
                'asset': asset,
                'atm_offset': atm_offset,
                'api_key': api_key,
                'api_secret': api_secret
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
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to prepare move trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error preparing trade: {str(e)[:200]}",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )


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
    
    # Show executing message
    await query.edit_message_text(
        "⏳ <b>Executing trade...</b>\n\n"
        "📊 Finding ATM option...\n"
        "📈 Placing entry order...\n"
        "🛡️ Setting up SL/Target orders...",
        parse_mode='HTML'
    )
    
    try:
        # Create Delta client
        client = DeltaClient(pending_trade['api_key'], pending_trade['api_secret'])
        
        try:
            # ✅ NEW: Import and use the executor
            from bot.executors.move_executor import MoveTradeExecutor
            
            executor = MoveTradeExecutor(client)
            
            # Get strategy details from pending trade
            preset_id = pending_trade.get('preset_id')
            preset = await get_move_trade_preset_by_id(preset_id)
            strategy = await get_move_strategy(preset['strategy_id'])
            
            # Handle dict vs Pydantic model
            if isinstance(strategy, dict):
                sl_trigger = strategy.get('stop_loss_trigger')
                sl_limit = strategy.get('stop_loss_limit')
                target_trigger = strategy.get('target_trigger')
                target_limit = strategy.get('target_limit')
            else:
                sl_trigger = strategy.stop_loss_trigger
                sl_limit = strategy.stop_loss_limit
                target_trigger = strategy.target_trigger
                target_limit = strategy.target_limit
            
            # ✅ Execute trade with full automation
            result = await executor.execute_move_trade(
                asset=pending_trade['asset'],
                direction=pending_trade['direction'],
                lot_size=pending_trade['lot_size'],
                atm_offset=pending_trade['atm_offset'],
                stop_loss_trigger=sl_trigger,
                stop_loss_limit=sl_limit,
                target_trigger=target_trigger,
                target_limit=target_limit
            )
            
            if result['success']:
                # Build success message
                product = result['product']
                entry_price = result['entry_price']
                sl_price = result.get('sl_price')
                target_price = result.get('target_price')
                
                text = "<b>✅ Move Trade Executed Successfully!</b>\n\n"
                text += f"<b>📊 Contract:</b> {product['symbol']}\n"
                text += f"<b>Strike:</b> ${product['strike_price']}\n"
                text += f"<b>Direction:</b> {pending_trade['direction'].title()}\n"
                text += f"<b>Lot Size:</b> {pending_trade['lot_size']}\n\n"
                text += f"<b>💰 Entry Price:</b> ${entry_price:.2f}\n"
                
                if sl_price:
                    text += f"<b>🛑 Stop Loss:</b> ${sl_price:.2f}\n"
                if target_price:
                    text += f"<b>🎯 Target:</b> ${target_price:.2f}\n"
                
                text += "\n✅ All orders placed successfully!"
                
                await query.edit_message_text(
                    text,
                    reply_markup=get_move_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
                
                log_user_action(user.id, "move_manual_execute", f"Executed {pending_trade['direction']} move trade with SL/Target")
            else:
                # Execution failed
                await query.edit_message_text(
                    f"<b>❌ Trade Execution Failed</b>\n\n"
                    f"Error: {result.get('error', 'Unknown error')}\n\n"
                    f"Please check your account and try again.",
                    reply_markup=get_move_manual_trade_keyboard(),
                    parse_mode='HTML'
                )
        
        finally:
            await client.close()
            # Clear pending trade
            context.user_data.pop('pending_move_trade', None)
    
    except Exception as e:
        logger.error(f"Failed to execute move trade: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>❌ Trade Execution Failed</b>\n\n"
            f"Error: {str(e)[:200]}\n\n"
            f"Please try again or check your account.",
            reply_markup=get_move_manual_trade_keyboard(),
            parse_mode='HTML'
        )
        
        # Clear pending trade
        context.user_data.pop('pending_move_trade', None)


def register_move_manual_trade_handlers(application: Application):
    """Register move manual trade handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_manual_trade_menu_callback,
        pattern="^menu_move_manual_trade$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_select_callback,
        pattern="^move_manual_select_"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_manual_execute_callback,
        pattern="^move_manual_execute$"
    ))
    
    logger.info("Move manual trade handlers registered")
        
