"""
Additional keyboards for expiry and strike selection.
"""

from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_expiry_list_keyboard(
    asset: str,
    expiries: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    """
    Get keyboard with available expiries for asset.
    
    Args:
        asset: Asset (BTC/ETH)
        expiries: List of expiry data dictionaries
    
    Returns:
        InlineKeyboardMarkup with expiry options
    """
    keyboard = []
    
    if not expiries:
        keyboard.append([InlineKeyboardButton(
            "❌ No expiries available",
            callback_data=f"asset_{asset}"
        )])
    else:
        for expiry in expiries:
            expiry_date = expiry.get('expiry_date', 'N/A')
            expiry_code = expiry.get('code', 'N/A')
            strike_count = expiry.get('strike_count', 0)
            
            button_text = f"📅 {expiry_date} ({expiry_code}) - {strike_count} strikes"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"expiry_select_{asset}_{expiry_code}"
            )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_list_options")])
    
    return InlineKeyboardMarkup(keyboard)


def get_call_put_selection_keyboard(
    asset: str,
    expiry: str,
    strike: int
) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting call or put option.
    
    Args:
        asset: Asset (BTC/ETH)
        expiry: Expiry code
        strike: Strike price
    
    Returns:
        InlineKeyboardMarkup with call/put options
    """
    keyboard = [
        [InlineKeyboardButton(
            "📞 Call",
            callback_data=f"option_{asset}_{expiry}_{strike}_C"
        )],
        [InlineKeyboardButton(
            "📱 Put",
            callback_data=f"option_{asset}_{expiry}_{strike}_P"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data=f"expiry_{asset}_{expiry}")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    test_expiries = [
        {'expiry_date': '2025-10-20', 'code': 'D', 'strike_count': 50},
        {'expiry_date': '2025-10-27', 'code': 'W', 'strike_count': 75},
        {'expiry_date': '2025-11-30', 'code': 'M', 'strike_count': 100}
    ]
    
    print("Expiry List Keyboard:")
    keyboard = get_expiry_list_keyboard("BTC", test_expiries)
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nCall/Put Selection Keyboard:")
    keyboard = get_call_put_selection_keyboard("BTC", "W", 65000)
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
