"""
MOVE Strategy Keyboard Layouts
All inline keyboard definitions for MOVE strategy management
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_move_menu_keyboard():
    """Get MOVE strategy management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data="move_add")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="move_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="move_delete_list")],
        [InlineKeyboardButton("👁️ View Strategies", callback_data="move_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard():
    """Get simple cancel keyboard."""
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]]
    return InlineKeyboardMarkup(keyboard)


def get_asset_keyboard():
    """Get asset selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_asset_BTC")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_asset_ETH")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_expiry_keyboard():
    """Get expiry selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("📅 Daily", callback_data="move_expiry_daily")],
        [InlineKeyboardButton("📆 Weekly", callback_data="move_expiry_weekly")],
        [InlineKeyboardButton("📊 Monthly", callback_data="move_expiry_monthly")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_direction_keyboard():
    """Get direction selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("🟢 Long (Buy)", callback_data="move_direction_long")],
        [InlineKeyboardButton("🔴 Short (Sell)", callback_data="move_direction_short")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard():
    """Get save confirmation keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="move_confirm_save")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_skip_target_keyboard():
    """Get keyboard with skip target option."""
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Target", callback_data="move_skip_target")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_continue_edit_keyboard(strategy_id):
    """Get keyboard for continuing edit after update."""
    keyboard = [
        [InlineKeyboardButton("✏️ Continue Editing", callback_data=f"move_edit_{strategy_id}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="move_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_delete_confirmation_keyboard(strategy_id):
    """Get delete confirmation keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"move_delete_confirmed_{strategy_id}")],
        [InlineKeyboardButton("❌ No, Cancel", callback_data="move_delete_list")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_strategy_list_keyboard(strategies, action="edit"):
    """
    Build keyboard for strategy selection (edit or delete).
    
    Args:
        strategies: List of strategy dicts
        action: "edit" or "delete"
    """
    keyboard = []
    for strategy in strategies:
        strategy_id = strategy.get('id')
        name = strategy.get('strategy_name', 'Unnamed')
        asset = strategy.get('asset', 'N/A')
        direction = strategy.get('direction', 'unknown')
        
        # Safe capitalize
        direction_display = direction.capitalize() if direction else 'N/A'
        
        if action == "delete":
            button_text = f"❌ {name} ({asset} - {direction_display})"
        else:
            button_text = f"{name} ({asset} - {direction_display})"
        
        callback_data = f"move_{action}_{strategy_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_edit_fields_keyboard():
    """Get keyboard for selecting field to edit."""
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data="move_edit_field_name")],
        [InlineKeyboardButton("📄 Edit Description", callback_data="move_edit_field_description")],
        [InlineKeyboardButton("💰 Edit Asset", callback_data="move_edit_field_asset")],
        [InlineKeyboardButton("📅 Edit Expiry", callback_data="move_edit_field_expiry")],
        [InlineKeyboardButton("🎯 Edit Direction", callback_data="move_edit_field_direction")],
        [InlineKeyboardButton("📊 Edit ATM Offset", callback_data="move_edit_field_atm_offset")],
        [InlineKeyboardButton("🔴 Edit SL Trigger", callback_data="move_edit_field_sl_trigger")],
        [InlineKeyboardButton("🔴 Edit SL Limit", callback_data="move_edit_field_sl_limit")],
        [InlineKeyboardButton("🟢 Edit Target Trigger", callback_data="move_edit_field_target_trigger")],
        [InlineKeyboardButton("🟢 Edit Target Limit", callback_data="move_edit_field_target_limit")],
        [InlineKeyboardButton("🔙 Back", callback_data="move_edit_list")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_asset_keyboard(strategy_id):
    """Get asset edit keyboard."""
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_edit_save_asset_BTC")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_edit_save_asset_ETH")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_expiry_keyboard(strategy_id):
    """Get expiry edit keyboard."""
    keyboard = [
        [InlineKeyboardButton("📅 Daily", callback_data="move_edit_save_expiry_daily")],
        [InlineKeyboardButton("📆 Weekly", callback_data="move_edit_save_expiry_weekly")],
        [InlineKeyboardButton("📊 Monthly", callback_data="move_edit_save_expiry_monthly")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_direction_keyboard(strategy_id):
    """Get direction edit keyboard."""
    keyboard = [
        [InlineKeyboardButton("🟢 Long", callback_data="move_edit_save_direction_long")],
        [InlineKeyboardButton("🔴 Short", callback_data="move_edit_save_direction_short")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
