"""
Trade history display handlers - UPDATED TO FETCH FROM DELTA API
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)
from datetime import datetime, timedelta

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_error_message, format_number
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.confirmation_keyboards import get_back_keyboard
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from delta.client import DeltaClient

logger = setup_logger(__name__)


@error_handler
async def trade_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle trade history menu callback.
    Display trade history for last 3 days by fetching from Delta Exchange API.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading trade history...</b>\n\n"
        "Fetching trades from Delta Exchange...",
        parse_mode='HTML'
    )
    
    try:
        # Get user's APIs
        apis = await get_api_credentials(user.id)
        
        if not apis:
            await query.edit_message_text(
                "<b>📈 Trade History</b>\n\n"
                "❌ No API credentials configured.\n\n"
                "Please add an API credential first.",
                reply_markup=get_back_keyboard("back_to_main"),
                parse_mode='HTML'
            )
            return
        
        # Calculate time range (last 3 days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=3)
        
        # Convert to Unix timestamps (microseconds)
        start_timestamp = int(start_time.timestamp() * 1000000)
        end_timestamp = int(end_time.timestamp() * 1000000)
        
        # Fetch trade history for each API
        all_trades_text = []
        combined_stats = {
            'total_trades': 0,
            'total_pnl': 0,
            'total_commission': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        
        for api in apis:
            try:
                # Get API credentials
                credentials = await get_decrypted_api_credential(str(api.id))
                if not credentials:
                    all_trades_text.append(
                        f"<b>❌ {api.api_name}</b>\n"
                        f"Failed to decrypt credentials\n"
                    )
                    continue
                
                api_key, api_secret = credentials
                
                # Create Delta client
                client = DeltaClient(api_key, api_secret)
                
                try:
                    # Fetch fills (executed trades) from Delta Exchange
                    response = await client.get_fills(
                        start_time=start_timestamp,
                        end_time=end_timestamp
                    )
                    
                    if not response.get('success'):
                        error_msg = response.get('error', {}).get('message', 'Unknown error')
                        all_trades_text.append(
                            f"<b>❌ {api.api_name}</b>\n"
                            f"API Error: {error_msg}\n"
                        )
                        continue
                    
                    fills = response.get('result', [])
                    
                    if fills:
                        # Format trades for this API
                        api_text = f"<b>📊 {api.api_name}</b>\n\n"
                        
                        api_stats = {
                            'trades': 0,
                            'pnl': 0,
                            'commission': 0
                        }
                        
                        # Group fills by product (symbol)
                        trades_by_symbol = {}
                        for fill in fills:
                            symbol = fill.get('product_symbol', 'Unknown')
                            if symbol not in trades_by_symbol:
                                trades_by_symbol[symbol] = []
                            trades_by_symbol[symbol].append(fill)
                        
                        # Format each symbol's trades
                        for symbol, symbol_fills in trades_by_symbol.items():
                            api_text += f"<b>{symbol}</b>\n"
                            
                            for fill in symbol_fills[:5]:  # Show max 5 trades per symbol
                                side = fill.get('side', 'unknown').upper()
                                size = fill.get('size', 0)
                                price = fill.get('price', 0)
                                commission = fill.get('commission', 0)
                                pnl = fill.get('realized_pnl', 0)
                                
                                # Calculate stats
                                api_stats['trades'] += 1
                                api_stats['pnl'] += pnl
                                api_stats['commission'] += commission
                                
                                if pnl > 0:
                                    combined_stats['winning_trades'] += 1
                                elif pnl < 0:
                                    combined_stats['losing_trades'] += 1
                                
                                # Format PnL with color
                                if pnl > 0:
                                    pnl_str = f"🟢 +${format_number(pnl)}"
                                elif pnl < 0:
                                    pnl_str = f"🔴 -${format_number(abs(pnl))}"
                                else:
                                    pnl_str = f"⚪ ${format_number(pnl)}"
                                
                                api_text += (
                                    f"  {side} {size} @ ${format_number(price)}\n"
                                    f"  PnL: {pnl_str} | Fee: ${format_number(commission)}\n\n"
                                )
                            
                            if len(symbol_fills) > 5:
                                api_text += f"  <i>...and {len(symbol_fills) - 5} more trades</i>\n\n"
                        
                        # API Summary
                        net_pnl = api_stats['pnl'] - api_stats['commission']
                        if net_pnl > 0:
                            net_pnl_str = f"🟢 +${format_number(net_pnl)}"
                        elif net_pnl < 0:
                            net_pnl_str = f"🔴 -${format_number(abs(net_pnl))}"
                        else:
                            net_pnl_str = f"⚪ ${format_number(net_pnl)}"
                        
                        api_text += (
                            f"<b>Trades:</b> {api_stats['trades']}\n"
                            f"<b>Net PnL:</b> {net_pnl_str}\n"
                        )
                        
                        all_trades_text.append(api_text)
                        
                        # Update combined stats
                        combined_stats['total_trades'] += api_stats['trades']
                        combined_stats['total_pnl'] += api_stats['pnl']
                        combined_stats['total_commission'] += api_stats['commission']
                    
                    else:
                        all_trades_text.append(
                            f"<b>📊 {api.api_name}</b>\n"
                            f"No trades found\n"
                        )
                
                finally:
                    await client.close()
            
            except Exception as e:
                logger.error(f"Failed to fetch trades for API {api.id}: {e}", exc_info=True)
                all_trades_text.append(
                    f"<b>❌ {api.api_name}</b>\n"
                    f"Error: {str(e)}\n"
                )
        
        # Construct final message
        if combined_stats['total_trades'] > 0:
            final_text = "<b>📈 Trade History (Last 3 Days)</b>\n\n"
            
            # Add per-API history
            final_text += "\n".join(all_trades_text)
            
            # Add combined summary if multiple APIs
            if len(apis) > 1:
                final_text += "\n" + "="*30 + "\n"
                final_text += "<b>📊 Combined Summary</b>\n\n"
                final_text += f"<b>Total Trades:</b> {combined_stats['total_trades']}\n"
                final_text += f"<b>Winning Trades:</b> {combined_stats['winning_trades']}\n"
                final_text += f"<b>Losing Trades:</b> {combined_stats['losing_trades']}\n"
                
                # Calculate win rate
                if combined_stats['total_trades'] > 0:
                    win_rate = (combined_stats['winning_trades'] / combined_stats['total_trades']) * 100
                    final_text += f"<b>Win Rate:</b> {win_rate:.1f}%\n"
                
                # Net PnL
                net_pnl = combined_stats['total_pnl'] - combined_stats['total_commission']
                final_text += f"\n<b>Gross PnL:</b> ${format_number(combined_stats['total_pnl'])}\n"
                final_text += f"<b>Total Commission:</b> ${format_number(combined_stats['total_commission'])}\n"
                
                # Net PnL with emoji
                if net_pnl > 0:
                    final_text += f"<b>Net PnL:</b> 🟢 +${format_number(net_pnl)}\n"
                elif net_pnl < 0:
                    final_text += f"<b>Net PnL:</b> 🔴 -${format_number(abs(net_pnl))}\n"
                else:
                    final_text += f"<b>Net PnL:</b> ⚪ ${format_number(net_pnl)}\n"
        else:
            final_text = (
                "<b>📈 Trade History</b>\n\n"
                "❌ No trades found in the last 3 days.\n\n"
                "Execute some trades to see history here."
            )
        
        # Display trade history
        await query.edit_message_text(
            final_text,
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode='HTML'
        )
        
        log_user_action(
            user.id,
            "trade_history_view",
            f"Viewed history: {combined_stats['total_trades']} trades"
        )
    
    except Exception as e:
        logger.error(f"Failed to fetch trade history: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to fetch trade history.", str(e)),
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode='HTML'
        )


def register_trade_history_handlers(application: Application):
    """
    Register trade history handlers.
    
    Args:
        application: Bot application instance
    """
    # Trade history menu callback
    application.add_handler(CallbackQueryHandler(
        trade_history_callback,
        pattern="^menu_trade_history$"
    ))
    
    logger.info("Trade history handlers registered")


if __name__ == "__main__":
    print("Trade history handler module loaded")
                            
