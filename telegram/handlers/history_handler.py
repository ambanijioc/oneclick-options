"""
Trade history handler.
Displays past trades and statistics.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.trade_operations import TradeOperations
from telegram.formatters import format_trade_history_message
from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_trade_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show trade history for user.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        # Show loading message
        await query.edit_message_text(
            "⏳ Fetching trade history...\n\n"
            "Please wait..."
        )
        
        # Get trade operations
        trade_ops = TradeOperations()
        
        # Get trades by API
        trades_by_api = await trade_ops.get_trades_by_api(user_id, days=3)
        
        # Get aggregated stats
        stats = await trade_ops.get_aggregated_pnl(user_id, days=3)
        
        # Format message
        if not trades_by_api:
            message = "📈 **Trade History**\n\nNo trades in the last 3 days."
        else:
            message = "📈 **Trade History (Last 3 Days)**\n\n"
            
            for api_name, trades in trades_by_api.items():
                message += format_trade_history_message(trades, api_name, None)
                message += "\n" + "─" * 30 + "\n\n"
            
            # Add combined statistics
            if stats:
                message += "**📊 Combined Statistics:**\n"
                message += f"Total Trades: {stats.get('total_trades', 0)}\n"
                message += f"Winning: {stats.get('winning_trades', 0)} | "
                message += f"Losing: {stats.get('losing_trades', 0)}\n"
                message += f"Win Rate: {stats.get('win_rate', 0):.1f}%\n"
                message += f"Gross PnL: ${stats.get('total_pnl', 0):.2f}\n"
                message += f"Commission: ${stats.get('total_commission', 0):.2f}\n"
                message += f"**Net PnL: ${stats.get('net_pnl', 0):.2f}**\n"
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_trade_history] Displayed trade history for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_trade_history] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error fetching trade history.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("History handler module loaded")
  
