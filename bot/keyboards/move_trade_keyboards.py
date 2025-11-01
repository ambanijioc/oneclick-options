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

__all__ = ['get_trade_menu_keyboard']
