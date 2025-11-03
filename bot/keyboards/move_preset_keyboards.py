"""
MOVE Trade Preset Keyboards - COMPLETE & FIXED
All inline keyboard definitions for MOVE preset management.

UPDATED: 2025-11-03 - Final working version with all handlers aligned
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


# ==================== MAIN MENU ====================

def get_move_preset_menu_keyboard() -> InlineKeyboardMarkup:
    """Main MOVE Trade Presets menu - 5 options."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Preset", callback_data="move_preset_add")],
        [InlineKeyboardButton("📝 Edit Preset", callback_data="move_preset_edit_list")],
        [InlineKeyboardButton("👁️ View Preset", callback_data="move_preset_view_list")],
        [InlineKeyboardButton("🗑️ Delete Preset", callback_data="move_preset_delete_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== API/STRATEGY SELECTION ====================

def get_api_selection_keyboard(apis: list) -> InlineKeyboardMarkup:
    """Get keyboard for API selection during preset creation."""
    if not apis or not isinstance(apis, list):
        keyboard = [
            [InlineKeyboardButton("❌ No APIs Found", callback_data="no_action")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    for api in apis:
        api_name = api.get('api_name', f"API {api.get('_id', 'Unknown')}")
        api_id = str(api.get('_id', ''))
        keyboard.append([
            InlineKeyboardButton(
                f"🔌 {api_name}",
                callback_data=f"move_preset_api_{api_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")])
    return InlineKeyboardMarkup(keyboard)


def get_strategy_selection_keyboard(strategies: list) -> InlineKeyboardMarkup:
    """Get keyboard for strategy selection during preset creation."""
    if not strategies or not isinstance(strategies, list):
        keyboard = [
            [InlineKeyboardButton("❌ No Strategies Found", callback_data="no_action")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    for strategy in strategies:
        strategy_name = strategy.get('strategy_name', f"Strategy {strategy.get('_id', 'Unknown')}")
        strategy_id = str(strategy.get('_id', ''))
        keyboard.append([
            InlineKeyboardButton(
                f"📊 {strategy_name}",
                callback_data=f"move_preset_strategy_{strategy_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")])
    return InlineKeyboardMarkup(keyboard)


# ==================== CONFIRMATION ============

def get_preset_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard for saving preset."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Save Preset", callback_data="move_preset_save"),
            InlineKeyboardButton("❌ Cancel", callback_data="move_preset_add"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== PRESET LISTS ====================

def get_preset_list_keyboard(presets: list, action: str = "view") -> InlineKeyboardMarkup:
    """
    Show available presets as inline keyboard.
    
    Args:
        presets: List of preset dicts with '_id' and 'preset_name'
        action: "view", "edit", or "delete"
    
    Returns:
        InlineKeyboardMarkup with preset buttons
    """
    # ✅ CRITICAL: Type checking and safety
    if not presets or not isinstance(presets, list):
        keyboard = [
            [InlineKeyboardButton("❌ No Presets Found", callback_data="no_action")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_preset_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    for preset in presets:
        # ✅ Validate preset is dict
        if not isinstance(preset, dict):
            logger.warning(f"⚠️ Invalid preset object: {preset}")
            continue
        
        preset_id = str(preset.get('_id', ''))
        preset_name = preset.get('preset_name', f"Preset {preset_id[:8]}")
        
        # ✅ Build callback data
        if action == "view":
            callback = f"move_preset_view_{preset_id}"
        elif action == "edit":
            callback = f"move_preset_edit_{preset_id}"
        elif action == "delete":
            callback = f"move_preset_delete_{preset_id}"
        else:
            callback = f"move_preset_view_{preset_id}"
        
        keyboard.append([
            InlineKeyboardButton(f"🎯 {preset_name}", callback_data=callback)
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_preset_menu")])
    return InlineKeyboardMarkup(keyboard)


# ==================== PRESET DETAILS ============

def get_preset_details_keyboard(preset_id: str = None) -> InlineKeyboardMarkup:
    """Back button for preset details view."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Presets", callback_data="move_preset_view_list")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="move_preset_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== PRESET EDIT OPTIONS ============

def get_preset_edit_options_keyboard(preset_id: str) -> InlineKeyboardMarkup:
    """Edit options for each preset field."""
    keyboard = [
        [InlineKeyboardButton("✏️ Name", callback_data=f"move_preset_edit_name_{preset_id}")],
        [InlineKeyboardButton("✏️ Description", callback_data=f"move_preset_edit_description_{preset_id}")],
        [InlineKeyboardButton("✏️ API", callback_data=f"move_preset_edit_api_{preset_id}")],
        [InlineKeyboardButton("✏️ Strategy", callback_data=f"move_preset_edit_strategy_{preset_id}")],
        [InlineKeyboardButton("💾 Save Changes", callback_data=f"move_preset_save_changes_{preset_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="move_preset_edit_list")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== DELETE CONFIRMATION ============

def get_delete_confirmation_keyboard(preset_id: str) -> InlineKeyboardMarkup:
    """Confirmation for deleting preset."""
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm Delete",
                callback_data=f"move_preset_delete_confirm_{preset_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="move_preset_delete_list"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== CANCEL KEYBOARD ============

def get_cancel_keyboard(back_callback: str = "move_preset_menu") -> InlineKeyboardMarkup:
    """Cancel button for input prompts."""
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== EXPORTS ============

__all__ = [
    'get_move_preset_menu_keyboard',
    'get_api_selection_keyboard',
    'get_strategy_selection_keyboard',
    'get_preset_confirmation_keyboard',
    'get_preset_list_keyboard',
    'get_preset_details_keyboard',
    'get_preset_edit_options_keyboard',
    'get_delete_confirmation_keyboard',
    'get_cancel_keyboard',
    ]
