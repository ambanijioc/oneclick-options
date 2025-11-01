"""MOVE Preset Keyboards"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_preset_menu_keyboard():
    """Main preset menu"""
    keyboard = [
        [InlineKeyboardButton("➕ Create Preset", callback_data="move_preset_create")],
        [InlineKeyboardButton("📋 View Presets", callback_data="move_preset_list")],
        [InlineKeyboardButton("✏️ Edit Preset", callback_data="move_preset_edit")],
        [InlineKeyboardButton("🗑️ Delete Preset", callback_data="move_preset_delete")],
        [InlineKeyboardButton("⬅️ Back", callback_data="move_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_move_preset_menu_keyboard():
    """Alias for get_preset_menu_keyboard"""
    return get_preset_menu_keyboard()


def get_preset_select_keyboard(presets: list):
    """Select preset from list"""
    keyboard = []
    for preset in presets:
        preset_name = preset.get('name', 'Unknown')
        preset_id = str(preset.get('_id', ''))
        keyboard.append([
            InlineKeyboardButton(
                preset_name,
                callback_data=f"move_preset_select_{preset_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="move_preset_menu")])
    return InlineKeyboardMarkup(keyboard)


__all__ = [
    'get_preset_menu_keyboard',
    'get_move_preset_menu_keyboard',
    'get_preset_select_keyboard',
]
