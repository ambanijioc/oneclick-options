"""
Confirmation and general-purpose keyboards.
"""

from typing import Optional, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_confirmation_keyboard(
    confirm_callback: str,
    cancel_callback: str,
    confirm_text: str = "✅ Confirm",
    cancel_text: str = "❌ Cancel"
) -> InlineKeyboardMarkup:
    """
    Get generic confirmation keyboard.
    
    Args:
        confirm_callback: Callback data for confirm button
        cancel_callback: Callback data for cancel button
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
    
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(confirm_text, callback_data=confirm_callback),
            InlineKeyboardButton(cancel_text, callback_data=cancel_callback)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(
    yes_callback: str,
    no_callback: str
) -> InlineKeyboardMarkup:
    """
    Get yes/no keyboard.
    
    Args:
        yes_callback: Callback data for yes button
        no_callback: Callback data for no button
    
    Returns:
        InlineKeyboardMarkup with yes/no buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=yes_callback),
            InlineKeyboardButton("❌ No", callback_data=no_callback)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(callback_data: str, text: str = "🔙 Back") -> InlineKeyboardMarkup:
    """
    Get keyboard with single back button.
    
    Args:
        callback_data: Callback data for back button
        text: Button text
    
    Returns:
        InlineKeyboardMarkup with back button
    """
    keyboard = [[InlineKeyboardButton(text, callback_data=callback_data)]]
    
    return InlineKeyboardMarkup(keyboard)


def get_trade_confirmation_keyboard(
    trade_data: Dict[str, Any],
    confirm_callback: str,
    cancel_callback: str
) -> InlineKeyboardMarkup:
    """
    Get trade confirmation keyboard with details.
    
    Args:
        trade_data: Trade data dictionary
        confirm_callback: Callback for confirmation
        cancel_callback: Callback for cancellation
    
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Execute Trade", callback_data=confirm_callback),
            InlineKeyboardButton("❌ Cancel", callback_data=cancel_callback)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_skip_or_continue_keyboard(
    skip_callback: str,
    continue_callback: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Get keyboard for skipping optional steps.
    
    Args:
        skip_callback: Callback for skip button
        continue_callback: Callback for continue button (if provided)
    
    Returns:
        InlineKeyboardMarkup with skip/continue buttons
    """
    keyboard = []
    
    if continue_callback:
        keyboard.append([
            InlineKeyboardButton("➡️ Continue", callback_data=continue_callback),
            InlineKeyboardButton("⏭️ Skip", callback_data=skip_callback)
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("⏭️ Skip", callback_data=skip_callback)
        ])
    
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    extra_data: str = ""
) -> InlineKeyboardMarkup:
    """
    Get pagination keyboard.
    
    Args:
        current_page: Current page number (0-indexed)
        total_pages: Total number of pages
        callback_prefix: Prefix for callback data
        extra_data: Additional data to include in callback
    
    Returns:
        InlineKeyboardMarkup with pagination buttons
    """
    keyboard = []
    
    pagination_row = []
    
    # Previous button
    if current_page > 0:
        prev_callback = f"{callback_prefix}_{current_page-1}"
        if extra_data:
            prev_callback += f"_{extra_data}"
        pagination_row.append(InlineKeyboardButton(
            "⬅️ Previous",
            callback_data=prev_callback
        ))
    
    # Page indicator
    pagination_row.append(InlineKeyboardButton(
        f"📄 {current_page + 1}/{total_pages}",
        callback_data="pagination_info"
    ))
    
    # Next button
    if current_page < total_pages - 1:
        next_callback = f"{callback_prefix}_{current_page+1}"
        if extra_data:
            next_callback += f"_{extra_data}"
        pagination_row.append(InlineKeyboardButton(
            "➡️ Next",
            callback_data=next_callback
        ))
    
    keyboard.append(pagination_row)
    
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard(callback_data: str = "cancel_operation") -> InlineKeyboardMarkup:
    """
    Get keyboard with cancel button.
    
    Args:
        callback_data: Callback data for cancel button
    
    Returns:
        InlineKeyboardMarkup with cancel button
    """
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data=callback_data)]]
    
    return InlineKeyboardMarkup(keyboard)


def get_loading_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard showing loading state.
    
    Returns:
        InlineKeyboardMarkup with loading indicator
    """
    keyboard = [[InlineKeyboardButton("⏳ Loading...", callback_data="loading")]]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Confirmation Keyboard:")
    keyboard = get_confirmation_keyboard("confirm_action", "cancel_action")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nYes/No Keyboard:")
    keyboard = get_yes_no_keyboard("yes_action", "no_action")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nPagination Keyboard:")
    keyboard = get_pagination_keyboard(1, 5, "page", "extra_data")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nSkip/Continue Keyboard:")
    keyboard = get_skip_or_continue_keyboard("skip", "continue")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
