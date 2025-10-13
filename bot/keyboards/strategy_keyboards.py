"""
Keyboards for strategy management.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.strategy_preset import StrategyPreset
from .main_menu import get_back_to_main_menu_button


def get_strategy_management_keyboard(
    strategy_type: str,
    presets: List[StrategyPreset] = None
) -> InlineKeyboardMarkup:
    """
    Get strategy management keyboard.
    
    Args:
        strategy_type: Strategy type (straddle/strangle)
        presets: List of existing presets
    
    Returns:
        InlineKeyboardMarkup with strategy management options
    """
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data=f"strategy_add_{strategy_type}")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data=f"strategy_edit_{strategy_type}")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data=f"strategy_delete_{strategy_type}")]
    ]
    
    # Show existing presets count if provided
    if presets:
        keyboard.insert(0, [InlineKeyboardButton(
            f"📋 {len(presets)} Preset(s) Configured",
            callback_data=f"strategy_list_{strategy_type}"
        )])
    
    # Add back button
    keyboard.append(get_back_to_main_menu_button())
    
    return InlineKeyboardMarkup(keyboard)


def get_strategy_list_keyboard(
    strategy_type: str,
    presets: List[StrategyPreset]
) -> InlineKeyboardMarkup:
    """
    Get keyboard showing list of strategy presets.
    
    Args:
        strategy_type: Strategy type (straddle/strangle)
        presets: List of strategy presets
    
    Returns:
        InlineKeyboardMarkup with preset list
    """
    keyboard = []
    
    if not presets:
        keyboard.append([InlineKeyboardButton(
            "❌ No presets found",
            callback_data=f"strategy_add_{strategy_type}"
        )])
    else:
        for preset in presets:
            # Format preset info
            direction_emoji = "📈" if preset.direction == "long" else "📉"
            button_text = f"{direction_emoji} {preset.name} ({preset.asset})"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"strategy_view_{preset.id}"
            )])
    
    # Add back button
    menu_callback = f"menu_{strategy_type}_strategy"
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=menu_callback)])
    
    return InlineKeyboardMarkup(keyboard)


def get_strategy_edit_keyboard(
    strategy_type: str,
    presets: List[StrategyPreset]
) -> InlineKeyboardMarkup:
    """
    Get keyboard for editing strategies.
    
    Args:
        strategy_type: Strategy type (straddle/strangle)
        presets: List of strategy presets
    
    Returns:
        InlineKeyboardMarkup with edit options
    """
    keyboard = []
    
    if not presets:
        keyboard.append([InlineKeyboardButton(
            "❌ No presets to edit",
            callback_data=f"strategy_add_{strategy_type}"
        )])
    else:
        for preset in presets:
            keyboard.append([InlineKeyboardButton(
                f"✏️ {preset.name}",
                callback_data=f"strategy_edit_preset_{preset.id}"
            )])
    
    # Add back button
    menu_callback = f"menu_{strategy_type}_strategy"
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=menu_callback)])
    
    return InlineKeyboardMarkup(keyboard)


def get_strategy_delete_confirmation_keyboard(
    preset_id: str,
    strategy_type: str
) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard for strategy deletion.
    
    Args:
        preset_id: Strategy preset ID
        strategy_type: Strategy type
    
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes, Delete",
                callback_data=f"strategy_delete_confirm_{preset_id}"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"menu_{strategy_type}_strategy"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_strategy_type_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting strategy type.
    
    Returns:
        InlineKeyboardMarkup with strategy type options
    """
    keyboard = [
        [InlineKeyboardButton("🎲 Straddle", callback_data="strategy_type_straddle")],
        [InlineKeyboardButton("🎰 Strangle", callback_data="strategy_type_strangle")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_manual_trade")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_direction_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting trade direction.
    
    Returns:
        InlineKeyboardMarkup with direction options
    """
    keyboard = [
        [
            InlineKeyboardButton("📈 Long", callback_data="direction_long"),
            InlineKeyboardButton("📉 Short", callback_data="direction_short")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_otm_type_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting OTM type (for strangle).
    
    Returns:
        InlineKeyboardMarkup with OTM type options
    """
    keyboard = [
        [InlineKeyboardButton("📊 Percentage", callback_data="otm_type_percentage")],
        [InlineKeyboardButton("🔢 Numeral", callback_data="otm_type_numeral")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard generation
    print("Strategy Management Keyboard:")
    keyboard = get_strategy_management_keyboard("straddle")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nStrategy Type Keyboard:")
    keyboard = get_strategy_type_keyboard()
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
    
    print("\nDirection Keyboard:")
    keyboard = get_direction_keyboard()
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
          
