"""
Message formatting utilities for Telegram bot.
Formats data into user-friendly messages.
"""

from typing import Dict, Any, List
from datetime import datetime
import pytz

from logger import logger, log_function_call
from utils.helpers import format_currency, format_position_size


@log_function_call
def format_balance_message(balance_data: Dict[str, Any]) -> str:
    """
    Format balance information for display.
    
    Args:
        balance_data: Balance data dictionary
    
    Returns:
        Formatted message string
    """
    try:
        message = "💰 **Account Balance**\n\n"
        
        asset = balance_data.get('asset_symbol', 'USDT')
        total = balance_data.get('balance', 0)
        available = balance_data.get('available_balance', 0)
        position_margin = balance_data.get('position_margin', 0)
        order_margin = balance_data.get('order_margin', 0)
        unrealized_pnl = balance_data.get('unrealized_pnl', 0)
        
        message += f"**Asset:** {asset}\n"
        message += f"**Total Balance:** {format_currency(total, asset)}\n"
        message += f"**Available:** {format_currency(available, asset)}\n"
        message += f"**Position Margin:** {format_currency(position_margin, asset)}\n"
        message += f"**Order Margin:** {format_currency(order_margin, asset)}\n"
        
        pnl_emoji = "🟢" if unrealized_pnl > 0 else "🔴" if unrealized_pnl < 0 else "⚪"
        message += f"**Unrealized PnL:** {pnl_emoji} {format_currency(unrealized_pnl, asset)}\n"
        
        # Calculate utilization
        if total > 0:
            utilization = ((position_margin + order_margin) / total) * 100
            message += f"\n📊 **Margin Utilization:** {utilization:.1f}%"
        
        return message
        
    except Exception as e:
        logger.error(f"[format_balance_message] Error formatting balance: {e}")
        return "❌ Error formatting balance information."


@log_function_call
def format_positions_message(positions: List[Dict[str, Any]]) -> str:
    """
    Format positions list for display.
    
    Args:
        positions: List of position dictionaries
    
    Returns:
        Formatted message string
    """
    try:
        if not positions:
            return "📊 **Positions**\n\nNo open positions."
        
        message = f"📊 **Open Positions** ({len(positions)})\n\n"
        
        for i, position in enumerate(positions[:10], 1):
            symbol = position.get('product_symbol', 'Unknown')
            size = position.get('size', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('mark_price', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            
            pnl_emoji = "🟢" if unrealized_pnl > 0 else "🔴" if unrealized_pnl < 0 else "⚪"
            direction = "📈 Long" if size > 0 else "📉 Short"
            
            message += f"**{i}. {symbol}**\n"
            message += f"   {direction} | Size: {abs(size)}\n"
            message += f"   Entry: ${entry_price:.2f} | Current: ${current_price:.2f}\n"
            message += f"   PnL: {pnl_emoji} ${unrealized_pnl:.2f}\n\n"
        
        if len(positions) > 10:
            message += f"_... and {len(positions) - 10} more positions_\n"
        
        return message
        
    except Exception as e:
        logger.error(f"[format_positions_message] Error formatting positions: {e}")
        return "❌ Error formatting positions."


@log_function_call
def format_trade_history_message(
    trades: List[Dict[str, Any]],
    api_name: str,
    stats: Dict[str, Any]
) -> str:
    """
    Format trade history for display.
    
    Args:
        trades: List of trade dictionaries
        api_name: API name
        stats: Aggregated statistics
    
    Returns:
        Formatted message string
    """
    try:
        message = f"📈 **Trade History - {api_name}**\n\n"
        
        if not trades:
            message += "No trades in the selected period.\n"
        else:
            for trade in trades[:5]:  # Show max 5 recent trades
                entry_time = trade.get('entry_time')
                exit_time = trade.get('exit_time')
                pnl = trade.get('pnl', 0)
                commission = trade.get('commission', 0)
                
                if isinstance(entry_time, datetime):
                    entry_str = entry_time.strftime('%m/%d %H:%M')
                else:
                    entry_str = "Unknown"
                
                if exit_time and isinstance(exit_time, datetime):
                    exit_str = exit_time.strftime('%m/%d %H:%M')
                else:
                    exit_str = "Open"
                
                pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                
                message += f"{entry_str} → {exit_str}\n"
                message += f"PnL: {pnl_emoji} ${pnl:.2f} | Commission: ${commission:.2f}\n\n"
        
        # Add statistics
        if stats:
            message += "**📊 Statistics:**\n"
            message += f"Total Trades: {stats.get('total_trades', 0)}\n"
            message += f"Winning: {stats.get('winning_trades', 0)} | "
            message += f"Losing: {stats.get('losing_trades', 0)}\n"
            message += f"Win Rate: {stats.get('win_rate', 0):.1f}%\n"
            message += f"Gross PnL: ${stats.get('total_pnl', 0):.2f}\n"
            message += f"Commission: ${stats.get('total_commission', 0):.2f}\n"
            message += f"**Net PnL: ${stats.get('net_pnl', 0):.2f}**\n"
        
        return message
        
    except Exception as e:
        logger.error(f"[format_trade_history_message] Error formatting history: {e}")
        return "❌ Error formatting trade history."


@log_function_call
def format_strategy_preview_message(preview: Dict[str, Any]) -> str:
    """
    Format strategy preview for display.
    
    Args:
        preview: Strategy preview dictionary
    
    Returns:
        Formatted message string
    """
    try:
        strategy = preview.get('strategy', 'Unknown').capitalize()
        asset = preview.get('asset', 'Unknown')
        direction = preview.get('direction', 'Unknown')
        spot_price = preview.get('spot_price', 0)
        lot_size = preview.get('lot_size', 0)
        expiry = preview.get('expiry', 'Unknown')
        
        message = f"🎯 **{strategy} Strategy Preview**\n\n"
        message += f"**Asset:** {asset}\n"
        message += f"**Direction:** {direction.capitalize()}\n"
        message += f"**Spot Price:** ${spot_price:.2f}\n"
        message += f"**Lot Size:** {lot_size}\n"
        message += f"**Expiry:** {expiry}\n\n"
        
        if strategy == 'Straddle':
            strike = preview.get('strike', 0)
            message += f"**Strike:** ${strike:.0f}\n"
            message += f"**Call:** {strike} CE\n"
            message += f"**Put:** {strike} PE\n"
        else:  # Strangle
            call_strike = preview.get('call_strike', 0)
            put_strike = preview.get('put_strike', 0)
            message += f"**Call Strike:** ${call_strike:.0f}\n"
            message += f"**Put Strike:** ${put_strike:.0f}\n"
        
        # Add SL/TP info
        sl_config = preview.get('stoploss_config')
        tp_config = preview.get('target_config')
        
        if sl_config:
            message += f"\n**Stop Loss:** {sl_config.get('trigger_percentage')}%"
        
        if tp_config:
            message += f"\n**Take Profit:** {tp_config.get('trigger_percentage')}%"
        
        return message
        
    except Exception as e:
        logger.error(f"[format_strategy_preview_message] Error formatting preview: {e}")
        return "❌ Error formatting strategy preview."


@log_function_call
def escape_markdown(text: str) -> str:
    """
    Escape special characters for Markdown.
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


if __name__ == "__main__":
    # Test formatters
    print("Testing message formatters...")
    
    # Test balance formatting
    balance_data = {
        'asset_symbol': 'USDT',
        'balance': 10000.0,
        'available_balance': 8500.0,
        'position_margin': 1000.0,
        'order_margin': 500.0,
        'unrealized_pnl': 245.50
    }
    
    balance_msg = format_balance_message(balance_data)
    print("✅ Balance message formatted")
    print(balance_msg)
    
    print("\n✅ Formatter tests completed!")
      
