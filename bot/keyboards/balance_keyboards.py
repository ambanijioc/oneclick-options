"""
Keyboards for balance display.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.api_credentials import APICredential
from .main_menu import get_back_to_main_menu_button


def get_balance_keyboard(apis: List[APICredential] = None) -> InlineKeyboardMarkup:
    """
    Get balance display keyboard.
    
    Args:
        apis: List of API credentials
    
    Returns:
        InlineKeyboardMarkup with balance options
    """
    keyboard = []
    
    if apis and len(apis) > 0:
        # Add refresh button
        keyboard.append([InlineKeyboardButton("🔄 Refresh Balance", callback_data="balance_refresh")])
    
    # Add back button
    keyboard.append(get_back_to_main_menu_button())
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Balance Keyboard:")
    keyboard = get_balance_keyboard()
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
