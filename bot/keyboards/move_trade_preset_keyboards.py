# move_trade_preset_keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Trade Presets", callback_data="move_preset_view$")],
        [InlineKeyboardButton("Add Trade Preset", callback_data="move_preset_add")],
        [InlineKeyboardButton("Back to Main Menu", callback_data="menu_main")],
    ])

def view_presets_keyboard(presets):
    keyboard = []
    for preset in presets:
        name = preset.get("presetname", "Unnamed")
        preset_id = str(preset.get("_id") or preset.get("id"))
        keyboard.append([InlineKeyboardButton(name, callback_data=f"move_preset_detail_-{preset_id}")])
    keyboard.append([InlineKeyboardButton("Add Preset", callback_data="move_preset_add")])
    keyboard.append([InlineKeyboardButton("Back", callback_data="menu_move_trade_preset$")])
    return InlineKeyboardMarkup(keyboard)

def preset_detail_keyboard(preset_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Edit", callback_data=f"move_preset_edit_-{preset_id}")],
        [InlineKeyboardButton("Delete", callback_data=f"move_preset_delete_confirm_-{preset_id}")],
        [InlineKeyboardButton("Back to List", callback_data="move_preset_view$")],
    ])

def delete_confirm_keyboard(preset_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes, Delete", callback_data=f"move_preset_delete_-{preset_id}")],
        [InlineKeyboardButton("Cancel", callback_data=f"move_preset_detail_-{preset_id}")],
    ])

def add_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel", callback_data="move_preset_cancel$")],
    ])
  
