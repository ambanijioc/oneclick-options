"""
Keyboards for options listing and selection.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .main_menu import get_back_to_main_menu_button


def get_asset_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for asset selection (BTC/ETH).
    
    Returns:
        InlineKeyboardMarkup with asset options
    """
    keyboard = [
        [
            InlineKeyboardButton("₿ BTC", callback_data="asset_BTC"),
            InlineKeyboardButton("Ξ ETH", callback_data="asset_ETH")
        ],
        get_back_to_main_menu_button()
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_expiry_selection_keyboard(asset: str) -> InlineKeyboardMarkup:
    """
    Get keyboard for expiry selection.
    
    Args:
        asset: Selected asset (BTC/ETH)
    
    Returns:
        InlineKeyboardMarkup with expiry options
    """
    keyboard = [
        [InlineKeyboardButton("📅 Daily (D)", callback_data=f"expiry_{asset}_D")],
        [InlineKeyboardButton("📅 Daily+1 (D+1)", callback_data=f"expiry_{asset}_D+1")],
        [InlineKeyboardButton("📅 Weekly (W)", callback_data=f"expiry_{asset}_W")],
        [InlineKeyboardButton("📅 Weekly+1 (W+1)", callback_data=f"expiry_{asset}_W+1")],
        [InlineKeyboardButton("📅 Weekly+2 (W+2)", callback_data=f"expiry_{asset}_W+2")],
        [InlineKeyboardButton("📅 Monthly (M)", callback_data=f"expiry_{asset}_M")],
        [InlineKeyboardButton("📅 Monthly+1 (M+1)", callback_data=f"expiry_{asset}_M+1")],
        [InlineKeyboardButton("📅 Monthly+2 (M+2)", callback_data=f"expiry_{asset}_M+2")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_list_options")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_strike_list_keyboard(
    asset: str,
    expiry: str,
    strikes: List[int],
    current_page: int = 0,
    page_size: int = 10
) -> InlineKeyboardMarkup:
    """
    Get keyboard showing available strikes (paginated).
    
    Args:
        asset: Asset (BTC/ETH)
        expiry: Expiry code
        strikes: List of available strikes
        current_page: Current page number
        page_size: Number of strikes per page
    
    Returns:
        InlineKeyboardMarkup with strike options
    """
    keyboard = []
    
    # Calculate pagination
    total_pages = (len(strikes) + page_size - 1) // page_size
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(strikes))
    
    # Add strikes for current page
    page_strikes = strikes[start_idx:end_idx]
    for strike in page_strikes:
        keyboard.append([InlineKeyboardButton(
            f"💲 {strike}",
            callback_data=f"strike_{asset}_{expiry}_{strike}"
        )])
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        if current_page > 0:
            pagination_row.append(InlineKeyboardButton(
                "⬅️ Previous",
                callback_data=f"strike_page_{asset}_{expiry}_{current_page-1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            f"📄 {current_page + 1}/{total_pages}",
            callback_data="strike_page_info"
        ))
        
        if current_page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(
                "➡️ Next",
                callback_data=f"strike_page_{asset}_{expiry}_{current_page+1}"
            ))
        
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton(
        "🔙 Back",
        callback_data=f"asset_{asset}"
    )])
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Asset Selection Keyboard:")
    keyboard = get_asset_selection_keyboard()
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nExpiry Selection Keyboard:")
    keyboard = get_expiry_selection_keyboard("BTC")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
