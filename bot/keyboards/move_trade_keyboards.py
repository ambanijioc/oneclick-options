"""MOVE Trade Keyboards"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_trade_menu_keyboard():
    """Trade menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 View Trade", callback_data="move_view_trade")],
        [InlineKeyboardButton("🔚 Close Trade", callback_data="move_close_trade")],
        [InlineKeyboardButton("⬅️ Back", callback_data="move_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trade_status_keyboard(trade_id: str):
    """Trade status keyboard"""
    keyboard = [
        [InlineKeyboardButton("📈 Update PnL", callback_data=f"move_update_pnl_{trade_id}")],
        [InlineKeyboardButton("🛑 Exit Trade", callback_data=f"move_exit_trade_{trade_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="move_trade_list")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trade_list_keyboard(trades: list):
    """Trade list keyboard"""
    keyboard = []
    for trade in trades:
        trade_id = str(trade.get('_id', ''))
        direction = trade.get('direction', 'N/A')
        entry = trade.get('entry_price', 0)
        keyboard.append([
            InlineKeyboardButton(
                f"{direction} @ {entry}",
                callback_data=f"move_trade_detail_{trade_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="move_main_menu")])
    return InlineKeyboardMarkup(keyboard)


__all__ = [
    'get_trade_menu_keyboard',
    'get_trade_status_keyboard',
    'get_trade_list_keyboard',
]
