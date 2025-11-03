"""
MOVE Trade Preset Keyboards
All inline keyboard definitions for preset management.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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


# ============ API SELECTION ============

async def get_api_selection_keyboard(user_id):
    """Show available APIs as inline keyboard for selection"""
    # TODO: Fetch available APIs from database for user_id
    # This is a placeholder - adjust based on your API database structure
    
    apis = await get_user_apis(user_id)  # Your database function
    
    if not apis:
        keyboard = [
            [InlineKeyboardButton("❌ No APIs Found", callback_data="no_action")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    for api in apis:
        keyboard.append([
            InlineKeyboardButton(f"🔌 {api['name']}", callback_data=f"move_preset_api_{api['id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")])
    return InlineKeyboardMarkup(keyboard)


# ============ STRATEGY SELECTION ============

async def get_strategy_selection_keyboard(user_id):
    """Show available MOVE strategies as inline keyboard for selection"""
    # TODO: Fetch predefined strategies from database
    
    strategies = await get_user_move_strategies(user_id)  # Your database function
    
    if not strategies:
        keyboard = [
            [InlineKeyboardButton("❌ No Strategies Found", callback_data="no_action")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    keyboard = []
    for strategy in strategies:
        keyboard.append([
            InlineKeyboardButton(
                f"📊 {strategy['name']}", 
                callback_data=f"move_preset_strategy_{strategy['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_preset_add")])
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


# ============ VIEW PRESET ============

async def get_preset_list_keyboard(user_id, action="view"):
    """Show available presets as inline keyboard"""
    # action: "view", "edit", "delete"
    
    presets = await get_user_presets(user_id)  # Your database function
    
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

def get_preset_edit_options_keyboard():
    """Edit options for each preset field"""
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data="move_preset_edit_name")],
        [InlineKeyboardButton("✏️ Edit Description", callback_data="move_preset_edit_description")],
        [InlineKeyboardButton("✏️ Edit API", callback_data="move_preset_edit_api")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="move_preset_edit_strategy")],
        [InlineKeyboardButton("✏️ Edit SL Trigger", callback_data="move_preset_edit_sl_trigger")],
        [InlineKeyboardButton("✏️ Edit SL Limit", callback_data="move_preset_edit_sl_limit")],
        [InlineKeyboardButton("✏️ Edit Target Trigger", callback_data="move_preset_edit_target_trigger")],
        [InlineKeyboardButton("✏️ Edit Target Limit", callback_data="move_preset_edit_target_limit")],
        [InlineKeyboardButton("💾 Save Changes", callback_data="move_preset_save_changes")],
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
    'get_api_selection_keyboard',
    'get_strategy_selection_keyboard',
    'get_preset_confirmation_keyboard',
    'get_preset_list_keyboard',
    'get_preset_details_keyboard',
    'get_preset_edit_options_keyboard',
    'get_delete_confirmation_keyboard',
    'get_cancel_keyboard',
]
