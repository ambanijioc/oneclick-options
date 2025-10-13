"""
Trade history display handlers.
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
from bot.utils.message_formatter import format_trade_history, format_error_message, format_number
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.confirmation_keyboards import get_back_keyboard
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from database.operations.trade_ops import get_recent_trades, get_trades_summary
from delta.client import DeltaClient

logger = setup_logger(__name__)


@error_handler
async def trade_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle trade history menu callback.
    Display trade history for last 3 days across all APIs.
    
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
        "Fetching trades from last 3 days...",
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
                # Get trades from database
                trades = await get_recent_trades(user.id, days=3, api_id=str(api.id))
                
                if trades:
                    # Format trades for this API
                    api_trades_text = format_trade_history(trades, api.api_name)
                    all_trades_text.append(api_trades_text)
                    
                    # Add to combined stats
                    for trade in trades:
                        combined_stats['total_trades'] += 1
                        pnl = trade.realized_pnl or 0
                        combined_stats['total_pnl'] += pnl
                        combined_stats['total_commission'] += trade.commission
                        
                        if pnl > 0:
                            combined_stats['winning_trades'] += 1
                        elif pnl < 0:
                            combined_stats['losing_trades'] += 1
            
            except Exception as e:
                logger.error(f"Failed to fetch trades for API {api.id}: {e}", exc_info=True)
                all_trades_text.append(
                    f"<b>❌ {api.api_name}</b>\n"
                    f"Failed to fetch trade history\n"
                )
        
        # Construct final message
        if combined_stats['total_trades'] > 0:
            final_text = "<b>📈 Trade History (Last 3 Days)</b>\n\n"
            
            # Add per-API history
            final_text += "\n\n".join(all_trades_text)
            
            # Add combined summary if multiple APIs
            if len(apis) > 1:
                final_text += "\n\n" + "="*30 + "\n"
                final_text += "<b>📊 Combined Summary</b>\n\n"
                final_text += f"<b>Total Trades:</b> {combined_stats['total_trades']}\n"
                final_text += f"<b>Winning Trades:</b> {combined_stats['winning_trades']}\n"
                final_text += f"<b>Losing Trades:</b> {combined_stats['losing_trades']}\n"
                
                # Calculate win rate
                if combined_stats['total_trades'] > 0:
                    win_rate = (combined_stats['winning_trades'] / combined_stats['total_trades']) * 100
                    final_text += f"<b>Win Rate:</b> {win_rate:.1f}%\n"
                
                # PnL
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
  
