"""
Keyboards for API credential management.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.api_credentials import APICredential
from .main_menu import get_back_to_main_menu_button


def get_api_management_keyboard(apis: List[APICredential] = None) -> InlineKeyboardMarkup:
    """
    Get API management keyboard.
    
    Args:
        apis: List of existing API credentials
    
    Returns:
        InlineKeyboardMarkup with API management options
    """
    keyboard = [
        [InlineKeyboardButton("➕ Add API", callback_data="api_add")],
        [InlineKeyboardButton("✏️ Edit API", callback_data="api_edit")],
        [InlineKeyboardButton("🗑️ Delete API", callback_data="api_delete")]
    ]
    
    # Show existing APIs if provided
    if apis:
        keyboard.insert(0, [InlineKeyboardButton(
            f"📋 {len(apis)} API(s) Configured",
            callback_data="api_list"
        )])
    
    # Add back button
    keyboard.append(get_back_to_main_menu_button())
    
    return InlineKeyboardMarkup(keyboard)


def get_api_list_keyboard(apis: List[APICredential]) -> InlineKeyboardMarkup:
    """
    Get keyboard showing list of APIs.
    
    Args:
        apis: List of API credentials
    
    Returns:
        InlineKeyboardMarkup with API list
    """
    keyboard = []
    
    for api in apis:
        # Truncate description if too long
        desc = api.api_description[:30] + "..." if len(api.api_description) > 30 else api.api_description
        button_text = f"🔑 {api.api_name}"
        if desc:
            button_text += f"\n   {desc}"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"api_view_{api.id}"
        )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_manage_api")])
    
    return InlineKeyboardMarkup(keyboard)


def get_api_edit_keyboard(apis: List[APICredential]) -> InlineKeyboardMarkup:
    """
    Get keyboard for editing APIs.
    
    Args:
        apis: List of API credentials
    
    Returns:
        InlineKeyboardMarkup with edit options
    """
    keyboard = []
    
    for api in apis:
        keyboard.append([InlineKeyboardButton(
            f"✏️ {api.api_name}",
            callback_data=f"api_edit_{api.id}"
        )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_manage_api")])
    
    return InlineKeyboardMarkup(keyboard)


def get_api_delete_confirmation_keyboard(api_id: str) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard for API deletion.
    
    Args:
        api_id: API credential ID
    
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"api_delete_confirm_{api_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="menu_manage_api")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("API Management Keyboard:")
    keyboard = get_api_management_keyboard()
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
