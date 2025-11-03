"""
MOVE Strategy Keyboard Layouts - CLEANED & DEDUPED
All inline keyboard definitions for MOVE strategy management
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ========== BASIC KEYBOARDS ==========

def get_move_menu_keyboard() -> InlineKeyboardMarkup:
    """Get MOVE Strategy Management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data="move_add_strategy")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="move_edit")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="move_delete")],
        [InlineKeyboardButton("👁️ View Strategies", callback_data="move_view_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get simple cancel keyboard."""
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]]
    return InlineKeyboardMarkup(keyboard)

# ========== STEP-BY-STEP KEYBOARDS ==========

def get_description_skip_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for description step with Skip button (UNIFIED)."""
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="move_skip_description")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_asset_keyboard() -> InlineKeyboardMarkup:
    """Get asset selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_asset_BTC")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_asset_ETH")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_expiry_keyboard() -> InlineKeyboardMarkup:
    """Get expiry selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("📅 Daily", callback_data="move_expiry_daily")],
        [InlineKeyboardButton("📆 Weekly", callback_data="move_expiry_weekly")],
        [InlineKeyboardButton("📊 Monthly", callback_data="move_expiry_monthly")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_direction_keyboard() -> InlineKeyboardMarkup:
    """Get direction selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("🟢 Long (Buy)", callback_data="move_direction_long")],
        [InlineKeyboardButton("🔴 Short (Sell)", callback_data="move_direction_short")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get save confirmation keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="move_confirm_save")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_skip_target_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with skip target option."""
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Target", callback_data="move_skip_target")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== EDIT/MANAGE KEYBOARDS ==========

def get_strategy_list_keyboard(strategies, action="edit") -> InlineKeyboardMarkup:
    """Build keyboard for strategy selection (edit or delete)."""
    keyboard = []
    
    for strategy in strategies:
        strategy_id = str(strategy.get('id') or strategy.get('_id', ''))  # ✅ FIX: Handle both id/_id
        name = strategy.get('strategy_name', 'Unnamed')
        asset = strategy.get('asset', 'N/A')
        direction = (strategy.get('direction') or 'unknown').capitalize()
        
        if action == "delete":
            button_text = f"❌ {name} ({asset} - {direction})"
        else:
            button_text = f"{name} ({asset} - {direction})"
        
        callback_data = f"move_{action}_{strategy_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_edit_fields_keyboard(strategy_id) -> InlineKeyboardMarkup:
    """Get keyboard for selecting which field to edit."""
    keyboard = [
        [InlineKeyboardButton("📝 Name", callback_data=f"move_edit_field_{strategy_id}_name")],
        [InlineKeyboardButton("📄 Description", callback_data=f"move_edit_field_{strategy_id}_description")],
        [InlineKeyboardButton("📊 Asset", callback_data=f"move_edit_field_{strategy_id}_asset")],
        [InlineKeyboardButton("📅 Expiry", callback_data=f"move_edit_field_{strategy_id}_expiry")],
        [InlineKeyboardButton("🎯 Direction", callback_data=f"move_edit_field_{strategy_id}_direction")],
        [InlineKeyboardButton("🔢 ATM Offset", callback_data=f"move_edit_field_{strategy_id}_atm_offset")],
        [InlineKeyboardButton("🛑 SL Trigger", callback_data=f"move_edit_field_{strategy_id}_sl_trigger")],
        [InlineKeyboardButton("🛑 SL Limit", callback_data=f"move_edit_field_{strategy_id}_sl_limit")],
        [InlineKeyboardButton("🎯 Target Trigger", callback_data=f"move_edit_field_{strategy_id}_target_trigger")],
        [InlineKeyboardButton("🎯 Target Limit", callback_data=f"move_edit_field_{strategy_id}_target_limit")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_edit_asset_keyboard(strategy_id) -> InlineKeyboardMarkup:
    """Get keyboard for editing asset."""
    keyboard = [
        [InlineKeyboardButton("📊 BTC", callback_data=f"move_edit_save_asset_{strategy_id}_BTC")],
        [InlineKeyboardButton("💰 ETH", callback_data=f"move_edit_save_asset_{strategy_id}_ETH")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_edit_expiry_keyboard(strategy_id) -> InlineKeyboardMarkup:
    """Get keyboard for editing expiry."""
    keyboard = [
        [InlineKeyboardButton("📅 Daily", callback_data=f"move_edit_save_expiry_{strategy_id}_daily")],
        [InlineKeyboardButton("📆 Weekly", callback_data=f"move_edit_save_expiry_{strategy_id}_weekly")],
        [InlineKeyboardButton("📊 Monthly", callback_data=f"move_edit_save_expiry_{strategy_id}_monthly")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_edit_direction_keyboard(strategy_id) -> InlineKeyboardMarkup:
    """Get keyboard for editing direction."""
    keyboard = [
        [InlineKeyboardButton("🔼 Long", callback_data=f"move_edit_save_direction_{strategy_id}_long")],
        [InlineKeyboardButton("🔽 Short", callback_data=f"move_edit_save_direction_{strategy_id}_short")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== CONTINUE EDIT KEYBOARD ==========

def get_continue_edit_keyboard(strategy_id) -> InlineKeyboardMarkup:
    """Get keyboard for continuing or finishing edits."""
    keyboard = [
        [InlineKeyboardButton("✏️ Continue Editing", callback_data=f"move_edit_{strategy_id}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="move_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== PRESET KEYBOARDS ==========

def get_preset_list_keyboard(presets, action="view") -> InlineKeyboardMarkup:
    """Build keyboard for preset selection (view, edit, or delete)."""
    keyboard = []
    
    for preset in presets:
        preset_id = str(preset.get('_id'))
        name = preset.get('preset_name', 'Unnamed')
        
        if action == "delete":
            button_text = f"❌ {name}"
            callback_data = f"move_preset_delete_confirm_{preset_id}"
        elif action == "edit":
            button_text = f"✏️ {name}"
            callback_data = f"move_preset_edit_select_{preset_id}"
        else:  # view
            button_text = f"📋 {name}"
            callback_data = f"move_preset_view_{preset_id}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_move")])
    return InlineKeyboardMarkup(keyboard)

def get_preset_edit_fields_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting preset field to edit."""
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data="move_preset_edit_field_name")],
        [InlineKeyboardButton("📊 Edit API", callback_data="move_preset_edit_field_api")],
        [InlineKeyboardButton("🎯 Edit Strategy", callback_data="move_preset_edit_field_strategy")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_move")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== VIEW KEYBOARDS ==========

def get_strategies_list_keyboard(strategies) -> InlineKeyboardMarkup:
    """Build keyboard for displaying user's strategies with status indicators."""
    keyboard = []
    
    for strategy in strategies:
        strategy_id = str(strategy.get('id') or strategy.get('_id', ''))
        name = strategy.get('strategy_name', 'Unnamed')
        status = '🟢' if strategy.get('is_active', False) else '⚫'
        
        # Each strategy is a button
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {name}",
                callback_data=f"move_view_strategy_{strategy_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="move_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_strategy_details_keyboard(strategy_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for strategy details with Edit/Delete/Back options."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"move_edit_{strategy_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"move_delete_{strategy_id}")
        ],
        [InlineKeyboardButton("🔙 Back to List", callback_data="move_view_list")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== DELETE KEYBOARDS ==========

def get_delete_list_keyboard(strategies) -> InlineKeyboardMarkup:
    """Build keyboard for deleting strategies with ❌ icons."""
    keyboard = []
    
    for strategy in strategies:
        strategy_id = str(strategy.get('id') or strategy.get('_id', ''))
        name = strategy.get('strategy_name', 'Unnamed')
        asset = strategy.get('asset', 'N/A')
        direction = (strategy.get('direction') or 'unknown').capitalize()
        
        keyboard.append([
            InlineKeyboardButton(
                f"❌ {name} ({asset} - {direction})",
                callback_data=f"move_delete_{strategy_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="move_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_delete_confirmation_keyboard(strategy_id: str) -> InlineKeyboardMarkup:
    """Get delete confirmation keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"move_delete_confirmed_{strategy_id}")],
        [InlineKeyboardButton("❌ No, Cancel", callback_data="move_view_list")]
    ]
    return InlineKeyboardMarkup(keyboard)


__all__ = [
    'get_move_menu_keyboard',
    'get_cancel_keyboard',
    'get_description_skip_keyboard',
    'get_asset_keyboard',
    'get_expiry_keyboard',
    'get_direction_keyboard',
    'get_confirmation_keyboard',
    'get_skip_target_keyboard',
    'get_strategy_list_keyboard',
    'get_edit_fields_keyboard',
    'get_edit_asset_keyboard',
    'get_edit_expiry_keyboard',
    'get_edit_direction_keyboard',
    'get_continue_edit_keyboard',      # ✅ NEW
    'get_preset_list_keyboard',
    'get_preset_edit_fields_keyboard',
    'get_delete_list_keyboard',
    'get_delete_confirmation_keyboard',
    'get_strategies_list_keyboard',
    'get_strategy_details_keyboard',
]
