"""
Keyboards for order management.
"""

from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.api_credentials import APICredential
from .main_menu import get_back_to_main_menu_button


def get_order_list_keyboard(apis: List[APICredential]) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting API to view orders.
    
    Args:
        apis: List of API credentials
    
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
                f"📋 {api.api_name}",
                callback_data=f"order_view_{api.id}"
            )])
    
    # Add refresh button
    if apis:
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="menu_orders")])
    
    # Add back button
    keyboard.append(get_back_to_main_menu_button())
    
    return InlineKeyboardMarkup(keyboard)


def get_order_action_keyboard(
    api_id: str,
    orders: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    """
    Get keyboard for order actions.
    
    Args:
        api_id: API credential ID
        orders: List of orders
    
    Returns:
        InlineKeyboardMarkup with order actions
    """
    keyboard = []
    
    if not orders:
        keyboard.append([InlineKeyboardButton(
            "❌ No open orders",
            callback_data=f"order_view_{api_id}"
        )])
    else:
        # Show cancel all option if multiple orders
        if len(orders) > 1:
            keyboard.append([InlineKeyboardButton(
                "🗑️ Cancel All Orders",
                callback_data=f"order_cancel_all_{api_id}"
            )])
        
        # Show individual orders
        for i, order in enumerate(orders):
            order_id = order.get('id', 'unknown')
            symbol = order.get('symbol', 'Unknown')
            order_type = order.get('order_type', 'N/A').upper()
            
            button_text = f"📋 {symbol} - {order_type}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"order_detail_{api_id}_{order_id}"
            )])
    
    # Add refresh and back buttons
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"order_view_{api_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_orders")])
    
    return InlineKeyboardMarkup(keyboard)


def get_order_detail_keyboard(api_id: str, order_id: str) -> InlineKeyboardMarkup:
    """
    Get keyboard for order detail view.
    
    Args:
        api_id: API credential ID
        order_id: Order ID
    
    Returns:
        InlineKeyboardMarkup with order actions
    """
    keyboard = [
        [InlineKeyboardButton(
            "🗑️ Cancel Order",
            callback_data=f"order_cancel_{api_id}_{order_id}"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data=f"order_view_{api_id}")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_order_cancel_confirmation_keyboard(
    api_id: str,
    order_id: str = None,
    cancel_all: bool = False
) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard for order cancellation.
    
    Args:
        api_id: API credential ID
        order_id: Order ID (if single order)
        cancel_all: Whether canceling all orders
    
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    if cancel_all:
        confirm_callback = f"order_cancel_all_confirm_{api_id}"
        cancel_callback = f"order_view_{api_id}"
    else:
        confirm_callback = f"order_cancel_confirm_{api_id}_{order_id}"
        cancel_callback = f"order_detail_{api_id}_{order_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Cancel", callback_data=confirm_callback),
            InlineKeyboardButton("❌ No", callback_data=cancel_callback)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Order List Keyboard:")
    keyboard = get_order_list_keyboard([])
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
