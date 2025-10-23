"""
Main menu keyboard for the bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Get main menu inline keyboard.
    
    Returns:
        InlineKeyboardMarkup with main menu options
    """
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="menu_balance")],
        [InlineKeyboardButton("📊 Positions", callback_data="menu_positions")],
        [InlineKeyboardButton("📋 Orders", callback_data="menu_orders")],
        [InlineKeyboardButton("📜 Trade History", callback_data="menu_trade_history")],
        [InlineKeyboardButton("📋 List Options", callback_data="menu_list_options")],
        [InlineKeyboardButton("📋 List Move Options", callback_data="menu_list_move_options")],
        [InlineKeyboardButton("🎯 Straddle Strategy", callback_data="menu_straddle_strategy")],
        [InlineKeyboardButton("🎯 Strangle Strategy", callback_data="menu_strangle_strategy")],
        [InlineKeyboardButton("🎯 Move Strategy", callback_data="move_menu")],
        [InlineKeyboardButton("📋 Manual Trade Presets", callback_data="menu_manual_trade_presets")],
        [InlineKeyboardButton("🎯 Move Trade Presets", callback_data="menu_move_preset")],
        [InlineKeyboardButton("🎯 Manual Trade", callback_data="menu_manual_trade")],
        [InlineKeyboardButton("🎯 Manual Move Trade", callback_data="menu_manual_move_trade")],
        [InlineKeyboardButton("⏰ Auto Trade", callback_data="menu_auto_trade")],
        [InlineKeyboardButton("⏰ Auto Move Trade", callback_data="menu_auto_move_trade")],
        [InlineKeyboardButton("📊 SL Monitors", callback_data="menu_sl_monitors")],
        [InlineKeyboardButton("🔑 API Keys", callback_data="menu_manage_api")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_back_to_main_menu_button() -> list:
    """
    Get back to main menu button.
    
    Returns:
        List containing back button
    """
    return [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]


if __name__ == "__main__":
    # Test keyboard generation
    keyboard = get_main_menu_keyboard()
    print(f"Main menu keyboard has {len(keyboard.inline_keyboard)} rows")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"- {button.text}: {button.callback_data}")
            
