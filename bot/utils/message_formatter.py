"""
Message formatting utilities for Telegram bot.
Formats various data types into readable Telegram messages.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import html


def escape_markdown(text: str, version: int = 2) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    
    Args:
        text: Text to escape
        version: Markdown version (1 or 2)
    
    Returns:
        Escaped text
    """
    if version == 2:
        # Characters to escape in MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
    return text


def escape_html(text: str) -> str:
    """
    Escape HTML special characters.
    
    Args:
        text: Text to escape
    
    Returns:
        HTML-escaped text
    """
    return html.escape(str(text))


def format_number(value: float, decimals: int = 2) -> str:
    """
    Format number with thousand separators.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
    
    Returns:
        Formatted number string
    """
    return f"{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_pnl(value: float, with_emoji: bool = True) -> str:
    """
    Format PnL value with color emoji.
    
    Args:
        value: PnL value
        with_emoji: Include emoji indicator
    
    Returns:
        Formatted PnL string
    """
    emoji = ""
    if with_emoji:
        if value > 0:
            emoji = "🟢 "
        elif value < 0:
            emoji = "🔴 "
        else:
            emoji = "⚪ "
    
    sign = "+" if value > 0 else ""
    return f"{emoji}{sign}{format_number(value)}"


def format_balance(balance_data: Dict[str, Any], api_name: str = "Unknown") -> str:
    """
    Format balance data for display.
    
    Args:
        balance_data: Balance data from API
        api_name: API credential name
    
    Returns:
        Formatted balance message
    """
    message = f"<b>💰 Balance - {escape_html(api_name)}</b>\n\n"
    
    # Available balance
    available = balance_data.get('available_balance', 0)
    message += f"<b>Available:</b> ${format_number(available)}\n"
    
    # Used margin
    used_margin = balance_data.get('used_margin', 0)
    message += f"<b>Used Margin:</b> ${format_number(used_margin)}\n"
    
    # Unrealized PnL
    unrealized_pnl = balance_data.get('unrealized_pnl', 0)
    message += f"<b>Unrealized PnL:</b> {format_pnl(unrealized_pnl)}\n"
    
    # Position margin
    position_margin = balance_data.get('position_margin', 0)
    message += f"<b>Position Margin:</b> ${format_number(position_margin)}\n"
    
    # Total balance
    total_balance = available + used_margin
    message += f"\n<b>Total Balance:</b> ${format_number(total_balance)}\n"
    
    return message


def format_position(position_data: Dict[str, Any], index: int = 0) -> str:
    """
    Format position data for display.
    
    Args:
        position_data: Position data from API
        index: Position index for numbering
    
    Returns:
        Formatted position message
    """
    symbol = position_data.get('symbol', 'N/A')
    size = position_data.get('size', 0)
    entry_price = position_data.get('entry_price', 0)
    mark_price = position_data.get('mark_price', 0)
    unrealized_pnl = position_data.get('unrealized_pnl', 0)
    margin = position_data.get('margin', 0)
    leverage = position_data.get('leverage', 1)
    
    # Determine position side
    side = "LONG 📈" if size > 0 else "SHORT 📉"
    
    message = f"<b>Position #{index + 1}</b>\n"
    message += f"━━━━━━━━━━━━━━━━\n"
    message += f"<b>Symbol:</b> <code>{escape_html(symbol)}</code>\n"
    message += f"<b>Side:</b> {side}\n"
    message += f"<b>Size:</b> {abs(size)}\n"
    message += f"<b>Leverage:</b> {leverage}x\n"
    message += f"<b>Entry Price:</b> ${format_number(entry_price)}\n"
    message += f"<b>Mark Price:</b> ${format_number(mark_price)}\n"
    message += f"<b>Margin:</b> ${format_number(margin)}\n"
    message += f"<b>Unrealized PnL:</b> {format_pnl(unrealized_pnl)}\n"
    
    # Calculate ROI
    if margin > 0:
        roi = (unrealized_pnl / margin) * 100
        message += f"<b>ROI:</b> {format_percentage(roi)}\n"
    
    return message


def format_order(order_data: Dict[str, Any]) -> str:
    """
    Format order data for display.
    
    Args:
        order_data: Order data from API
    
    Returns:
        Formatted order message
    """
    order_id = order_data.get('id', 'N/A')
    symbol = order_data.get('symbol', 'N/A')
    order_type = order_data.get('order_type', 'N/A').upper()
    side = order_data.get('side', 'N/A').upper()
    size = order_data.get('size', 0)
    
    # Convert prices to float - API returns them as strings
    limit_price = float(order_data.get('limit_price', 0) or 0)
    stop_price = float(order_data.get('stop_price', 0) or 0)
    
    status = order_data.get('state', 'N/A').upper()
    
    message = f"<b>📋 Order #{order_id}</b>\n"
    message += f"━━━━━━━━━━━━━━━━\n"
    message += f"<b>Symbol:</b> <code>{escape_html(symbol)}</code>\n"
    message += f"<b>Type:</b> {order_type}\n"
    message += f"<b>Side:</b> {side}\n"
    message += f"<b>Size:</b> {size}\n"
    
    if limit_price > 0:
        message += f"<b>Limit Price:</b> ${format_number(limit_price)}\n"
    
    if stop_price > 0:
        message += f"<b>Stop Price:</b> ${format_number(stop_price)}\n"
    
    message += f"<b>Status:</b> {status}\n"
    
    return message

def format_trade_history(trades: List[Dict[str, Any]], api_name: str = "Unknown") -> str:
    """
    Format trade history for display.
    
    Args:
        trades: List of trade data
        api_name: API credential name
    
    Returns:
        Formatted trade history message
    """
    if not trades:
        return f"<b>📊 Trade History - {escape_html(api_name)}</b>\n\n<i>No trades found</i>"
    
    message = f"<b>📊 Trade History - {escape_html(api_name)}</b>\n\n"
    
    total_pnl = 0
    total_commission = 0
    
    for i, trade in enumerate(trades, 1):
        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', 0)
        pnl = trade.get('pnl', 0)
        commission = trade.get('commission', 0)
        entry_time = trade.get('entry_time', 'N/A')
        
        total_pnl += pnl
        total_commission += commission
        
        message += f"<b>Trade #{i}</b>\n"
        message += f"Entry: ${format_number(entry_price)} | Exit: ${format_number(exit_price)}\n"
        message += f"PnL: {format_pnl(pnl, with_emoji=False)} | Fee: ${format_number(commission)}\n"
        message += f"Time: {entry_time}\n\n"
    
    message += f"━━━━━━━━━━━━━━━━\n"
    message += f"<b>Total Trades:</b> {len(trades)}\n"
    message += f"<b>Gross PnL:</b> {format_pnl(total_pnl)}\n"
    message += f"<b>Total Commission:</b> ${format_number(total_commission)}\n"
    message += f"<b>Net PnL:</b> {format_pnl(total_pnl - total_commission)}\n"
    
    return message


def format_strategy_preset(preset: Dict[str, Any]) -> str:
    """
    Format strategy preset for display.
    
    Args:
        preset: Strategy preset data
    
    Returns:
        Formatted strategy preset message
    """
    name = preset.get('name', 'N/A')
    description = preset.get('description', 'No description')
    strategy_type = preset.get('strategy_type', 'N/A').upper()
    asset = preset.get('asset', 'N/A')
    expiry = preset.get('expiry_code', 'N/A')
    direction = preset.get('direction', 'N/A').upper()
    lot_size = preset.get('lot_size', 0)
    sl_trigger = preset.get('sl_trigger_pct', 0)
    sl_limit = preset.get('sl_limit_pct', 0)
    target_trigger = preset.get('target_trigger_pct', 0)
    
    message = f"<b>🎯 {escape_html(name)}</b>\n"
    message += f"<i>{escape_html(description)}</i>\n\n"
    message += f"<b>Strategy:</b> {strategy_type}\n"
    message += f"<b>Asset:</b> {asset}\n"
    message += f"<b>Expiry:</b> {expiry}\n"
    message += f"<b>Direction:</b> {direction}\n"
    message += f"<b>Lot Size:</b> {lot_size}\n"
    message += f"<b>SL Trigger:</b> {format_percentage(sl_trigger)}\n"
    message += f"<b>SL Limit:</b> {format_percentage(sl_limit)}\n"
    
    if target_trigger > 0:
        message += f"<b>Target:</b> {format_percentage(target_trigger)}\n"
    else:
        message += f"<b>Target:</b> None\n"
    
    if strategy_type == "STRADDLE":
        atm_offset = preset.get('atm_offset', 0)
        message += f"<b>ATM Offset:</b> {atm_offset}\n"
    elif strategy_type == "STRANGLE":
        otm_selection = preset.get('otm_selection', {})
        otm_type = otm_selection.get('type', 'N/A')
        otm_value = otm_selection.get('value', 0)
        message += f"<b>OTM Selection:</b> {otm_type.capitalize()} - {otm_value}\n"
    
    return message


def format_api_list(apis: List[Dict[str, Any]]) -> str:
    """
    Format API list for display.
    
    Args:
        apis: List of API credentials
    
    Returns:
        Formatted API list message
    """
    if not apis:
        return "<b>🔑 API Credentials</b>\n\n<i>No API credentials found</i>"
    
    message = "<b>🔑 API Credentials</b>\n\n"
    
    for i, api in enumerate(apis, 1):
        name = api.get('api_name', 'Unnamed')
        description = api.get('api_description', 'No description')
        created_at = api.get('created_at', 'N/A')
        
        message += f"<b>{i}. {escape_html(name)}</b>\n"
        message += f"<small>{escape_html(description)}</small>\n"
        
        if isinstance(created_at, datetime):
            message += f"<small>Added: {created_at.strftime('%Y-%m-%d')}</small>\n"
        
        message += "\n"
    
    return message


def format_error_message(error: str, context: Optional[str] = None) -> str:
    """
    Format error message for user display.
    
    Args:
        error: Error message
        context: Additional context
    
    Returns:
        Formatted error message
    """
    message = "❌ <b>Error</b>\n\n"
    message += f"{escape_html(error)}\n"
    
    if context:
        message += f"\n<i>{escape_html(context)}</i>\n"
    
    message += "\nPlease try again or contact support if the issue persists."
    
    return message


def format_confirmation_message(
    title: str,
    details: Dict[str, Any],
    warning: Optional[str] = None
) -> str:
    """
    Format confirmation message for user actions.
    
    Args:
        title: Confirmation title
        details: Details to display
        warning: Optional warning message
    
    Returns:
        Formatted confirmation message
    """
    message = f"<b>⚠️ {escape_html(title)}</b>\n\n"
    
    for key, value in details.items():
        message += f"<b>{escape_html(key)}:</b> {escape_html(str(value))}\n"
    
    if warning:
        message += f"\n<i>⚠️ {escape_html(warning)}</i>\n"
    
    message += "\n<b>Please confirm:</b>"
    
    return message


if __name__ == "__main__":
    # Test formatting functions
    print(format_balance({
        'available_balance': 10000.50,
        'used_margin': 2500.25,
        'unrealized_pnl': 150.75,
        'position_margin': 2000.00
    }, "Test API"))
    
    print("\n" + "="*50 + "\n")
    
    print(format_position({
        'symbol': 'BTCUSD',
        'size': 10,
        'entry_price': 65000.00,
        'mark_price': 65500.00,
        'unrealized_pnl': 500.00,
        'margin': 6500.00,
        'leverage': 10
    }))
  
