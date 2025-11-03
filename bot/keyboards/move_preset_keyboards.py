"""
MOVE Trade Preset Keyboards - FIXED
All inline keyboard definitions for preset management.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

# ============ MAIN MENU ============

def get_move_preset_menu_keyboard():
    """Main MOVE Trade Presets menu"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Preset", callback_data="move_preset_add")],
        [InlineKeyboardButton("📝 Edit Preset", callback_data="move_preset_edit_list")],
        [InlineKeyboardButton("👁️ View Preset", callback_data="move_preset_view_list")],
        [InlineKeyboardButton("🗑️ Delete Preset", callback_data="move_preset_delete_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="move_back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============ CONFIRMATION ============

def get_preset_confirmation_keyboard():
    """Confirmation keyboard for saving preset"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Save Preset", callback_data="move_preset_save"),
            InlineKeyboardButton("❌ Cancel", callback_data="move_preset_add"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============ VIEW PRESET (NON-ASYNC) ============

def get_preset_list_keyboard(presets: list, action="view"):
    """
    Show available presets as inline keyboard.
    
    Args:
        presets: List of preset dicts with 'id' and 'name'
        action: "view", "edit", or "delete"
    """
    if not presets:
        keyboard = [
            [InlineKeyboardButton("❌ No Presets Found", callback_data="no_action")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_back_main")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    for preset in presets:
        callback = f"move_preset_{action}_{preset['id']}"
        keyboard.append([
            InlineKeyboardButton(f"🎯 {preset['name']}", callback_data=callback)
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_back_main")])
    return InlineKeyboardMarkup(keyboard)


# ============ PRESET DETAILS ============

def get_preset_details_keyboard():
    """Back button for preset details view"""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Presets", callback_data="move_preset_view_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="move_back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============ PRESET EDIT OPTIONS ============

def get_preset_edit_options_keyboard(preset_id):
    """Edit options for each preset field"""
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"move_preset_edit_name_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit Description", callback_data=f"move_preset_edit_description_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit API", callback_data=f"move_preset_edit_api_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data=f"move_preset_edit_strategy_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit SL Trigger", callback_data=f"move_preset_edit_sl_trigger_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit SL Limit", callback_data=f"move_preset_edit_sl_limit_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit Target Trigger", callback_data=f"move_preset_edit_target_trigger_{preset_id}")],
        [InlineKeyboardButton("✏️ Edit Target Limit", callback_data=f"move_preset_edit_target_limit_{preset_id}")],
        [InlineKeyboardButton("💾 Save Changes", callback_data=f"move_preset_save_changes_{preset_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="move_preset_edit_list")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============ DELETE CONFIRMATION ============

def get_delete_confirmation_keyboard(preset_id):
    """Confirmation for deleting preset"""
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes, Delete",
                callback_data=f"move_preset_delete_confirm_{preset_id}"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="move_preset_delete_list"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============ CANCEL KEYBOARD ============

def get_cancel_keyboard():
    """Cancel button for input prompts"""
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="move_back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


__all__ = [
    'get_move_preset_menu_keyboard',
    'get_preset_confirmation_keyboard',
    'get_preset_list_keyboard',
    'get_preset_details_keyboard',
    'get_preset_edit_options_keyboard',
    'get_delete_confirmation_keyboard',
    'get_cancel_keyboard',
]
