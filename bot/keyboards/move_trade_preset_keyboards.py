# move_trade_preset_keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Trade Presets", callback_data="movepresetview")],
        [InlineKeyboardButton("Add Trade Preset", callback_data="movepresetadd")],
        [InlineKeyboardButton("Back to Main Menu", callback_data="menumain")],
    ])

def view_presets_keyboard(presets):
    keyboard = []
    for preset in presets:
        name = preset.get("presetname", "Unnamed")
        preset_id = str(preset.get("_id") or preset.get("id"))
        keyboard.append([InlineKeyboardButton(name, callback_data=f"movepresetdetail-{preset_id}")])
    keyboard.append([InlineKeyboardButton("Add Preset", callback_data="movepresetadd")])
    keyboard.append([InlineKeyboardButton("Back", callback_data="menumovetradepreset")])
    return InlineKeyboardMarkup(keyboard)

def preset_detail_keyboard(preset_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Edit", callback_data=f"movepresetedit-{preset_id}")],
        [InlineKeyboardButton("Delete", callback_data=f"movepresetdeleteconfirm-{preset_id}")],
        [InlineKeyboardButton("Back to List", callback_data="movepresetview")],
    ])

def delete_confirm_keyboard(preset_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes, Delete", callback_data=f"movepresetdelete-{preset_id}")],
        [InlineKeyboardButton("Cancel", callback_data=f"movepresetdetail-{preset_id}")],
    ])

def add_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel", callback_data="movepresetcancel")],
    ])
  
