"""
Keyboards for position management.
"""

from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.api_credentials import APICredential
from .main_menu import get_back_to_main_menu_button


def get_position_list_keyboard(
    apis: List[APICredential],
    show_sl_target_button: bool = True
) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting API to view positions.
    
    Args:
        apis: List of API credentials
        show_sl_target_button: Whether to show set SL/target button
    
    Returns:
        InlineKeyboardMarkup with API selection
    """
    keyboard = []
    
    if not apis:
        keyboard.append([InlineKeyboardButton(
            "❌ No APIs configured",
            callback_data="menu_manage_api"
        )])
    else:
        for api in apis:
            keyboard.append([InlineKeyboardButton(
                f"📊 {api.api_name}",
                callback_data=f"position_view_{api.id}"
            )])
    
    # Add refresh button
    if apis:
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="menu_positions")])
    
    # Add back button
    keyboard.append(get_back_to_main_menu_button())
    
    return InlineKeyboardMarkup(keyboard)


def get_position_action_keyboard(
    api_id: str,
    positions: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting position to manage.
    
    Args:
        api_id: API credential ID
        positions: List of positions
    
    Returns:
        InlineKeyboardMarkup with position selection
    """
    keyboard = []
    
    if not positions:
        keyboard.append([InlineKeyboardButton(
            "❌ No open positions",
            callback_data=f"position_view_{api_id}"
        )])
    else:
        for i, position in enumerate(positions):
            symbol = position.get('symbol', 'Unknown')
            size = position.get('size', 0)
            side = "LONG 📈" if size > 0 else "SHORT 📉"
            
            button_text = f"{symbol} - {side}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"position_select_{api_id}_{i}"
            )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_positions")])
    
    return InlineKeyboardMarkup(keyboard)


def get_sl_target_type_keyboard(api_id: str, position_index: int) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting SL/target type.
    
    Args:
        api_id: API credential ID
        position_index: Position index
    
    Returns:
        InlineKeyboardMarkup with SL/target options
    """
    keyboard = [
        [InlineKeyboardButton(
            "📝 Set Manually",
            callback_data=f"sl_manual_{api_id}_{position_index}"
        )],
        [InlineKeyboardButton(
            "💰 SL to Cost",
            callback_data=f"sl_to_cost_{api_id}_{position_index}"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data=f"position_view_{api_id}")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_position_detail_keyboard(api_id: str) -> InlineKeyboardMarkup:
    """
    Get keyboard for position detail view.
    
    Args:
        api_id: API credential ID
    
    Returns:
        InlineKeyboardMarkup with action buttons
    """
    keyboard = [
        [InlineKeyboardButton(
            "🎯 Set Stoploss & Target",
            callback_data=f"position_sl_target_{api_id}"
        )],
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"position_view_{api_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_positions")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Position List Keyboard:")
    keyboard = get_position_list_keyboard([])
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nSL/Target Type Keyboard:")
    keyboard = get_sl_target_type_keyboard("test_api_id", 0)
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
