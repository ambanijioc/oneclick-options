"""
Keyboards specific to trade execution.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.api_credentials import APICredential
from database.models.strategy_preset import StrategyPreset


def get_api_selection_keyboard(
    apis: List[APICredential],
    action: str = "trade"
) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting API for trade execution.
    
    Args:
        apis: List of API credentials
        action: Action type (trade/auto_trade)
    
    Returns:
        InlineKeyboardMarkup with API options
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
                f"🔑 {api.api_name}",
                callback_data=f"{action}_select_api_{api.id}"
            )])
    
    # Add back button
    back_callback = "menu_manual_trade" if action == "trade" else "menu_auto_trade"
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(keyboard)


def get_strategy_preset_selection_keyboard(
    presets: List[StrategyPreset],
    api_id: str,
    strategy_type: str
) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting strategy preset for execution.
    
    Args:
        presets: List of strategy presets
        api_id: Selected API ID
        strategy_type: Strategy type (straddle/strangle)
    
    Returns:
        InlineKeyboardMarkup with preset options
    """
    keyboard = []
    
    if not presets:
        keyboard.append([InlineKeyboardButton(
            "❌ No presets available",
            callback_data=f"strategy_add_{strategy_type}"
        )])
    else:
        for preset in presets:
            direction_emoji = "📈" if preset.direction == "long" else "📉"
            button_text = f"{direction_emoji} {preset.name} ({preset.asset})"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"trade_preset_{api_id}_{preset.id}"
            )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(
        "🔙 Back",
        callback_data=f"trade_select_api_{api_id}"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_auto_execution_time_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard with preset execution times.
    
    Returns:
        InlineKeyboardMarkup with time options
    """
    keyboard = [
        [InlineKeyboardButton("🕘 09:00", callback_data="auto_time_09:00")],
        [InlineKeyboardButton("🕘 09:15", callback_data="auto_time_09:15")],
        [InlineKeyboardButton("🕛 12:00", callback_data="auto_time_12:00")],
        [InlineKeyboardButton("🕒 15:00", callback_data="auto_time_15:00")],
        [InlineKeyboardButton("🕒 15:15", callback_data="auto_time_15:15")],
        [InlineKeyboardButton("✏️ Custom Time", callback_data="auto_time_custom")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_auto_trade")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_auto_execution_list_keyboard(
    auto_executions: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    """
    Get keyboard showing list of auto executions.
    
    Args:
        auto_executions: List of auto execution schedules
    
    Returns:
        InlineKeyboardMarkup with auto execution list
    """
    keyboard = []
    
    if not auto_executions:
        keyboard.append([InlineKeyboardButton(
            "❌ No auto executions configured",
            callback_data="menu_auto_trade"
        )])
    else:
        for auto_exec in auto_executions:
            status_emoji = "✅" if auto_exec.get('enabled') else "❌"
            time = auto_exec.get('execution_time', 'N/A')
            preset_name = auto_exec.get('preset_name', 'Unknown')
            
            button_text = f"{status_emoji} {time} - {preset_name}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"auto_view_{auto_exec.get('id')}"
            )])
    
    # Add management buttons
    keyboard.append([
        InlineKeyboardButton("➕ Add", callback_data="auto_add"),
        InlineKeyboardButton("✏️ Edit", callback_data="auto_edit"),
        InlineKeyboardButton("🗑️ Delete", callback_data="auto_delete")
    ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)


def get_auto_execution_toggle_keyboard(
    auto_exec_id: str,
    is_enabled: bool
) -> InlineKeyboardMarkup:
    """
    Get keyboard for toggling auto execution.
    
    Args:
        auto_exec_id: Auto execution ID
        is_enabled: Current enabled state
    
    Returns:
        InlineKeyboardMarkup with toggle option
    """
    toggle_text = "❌ Disable" if is_enabled else "✅ Enable"
    toggle_callback = f"auto_toggle_{auto_exec_id}"
    
    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=toggle_callback)],
        [InlineKeyboardButton("✏️ Edit", callback_data=f"auto_edit_{auto_exec_id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"auto_delete_{auto_exec_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_auto_trade")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Auto Execution Time Keyboard:")
    keyboard = get_auto_execution_time_keyboard()
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
