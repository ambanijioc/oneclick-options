"""
Inline keyboard builders for Telegram bot.
Creates structured button layouts for user interaction.
"""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from logger import logger, log_function_call


@log_function_call
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Create main menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with main menu buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("🔑 Manage API", callback_data="menu:manage_api"),
            InlineKeyboardButton("💰 Balance", callback_data="menu:balance")
        ],
        [
            InlineKeyboardButton("📊 Positions", callback_data="menu:positions"),
            InlineKeyboardButton("📋 Orders", callback_data="menu:orders")
        ],
        [
            InlineKeyboardButton("🎯 Stop Loss/Target", callback_data="menu:sl_tp"),
            InlineKeyboardButton("📈 Trade History", callback_data="menu:history")
        ],
        [
            InlineKeyboardButton("📝 List Options", callback_data="menu:list_options")
        ],
        [
            InlineKeyboardButton("🎲 Straddle Strategy", callback_data="menu:straddle_strategy"),
            InlineKeyboardButton("🎯 Strangle Strategy", callback_data="menu:strangle_strategy")
        ],
        [
            InlineKeyboardButton("▶️ Manual Trade", callback_data="menu:manual_trade"),
            InlineKeyboardButton("⏰ Auto Trade", callback_data="menu:auto_trade")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="menu:help")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_api_management_keyboard(apis: List[dict]) -> InlineKeyboardMarkup:
    """
    Create API management keyboard.
    
    Args:
        apis: List of API credentials
    
    Returns:
        InlineKeyboardMarkup with API management options
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ Add API", callback_data="api:add"),
            InlineKeyboardButton("✏️ Edit API", callback_data="api:edit"),
            InlineKeyboardButton("🗑️ Delete API", callback_data="api:delete")
        ]
    ]
    
    # Add existing APIs
    if apis:
        keyboard.append([InlineKeyboardButton("📋 Available APIs:", callback_data="ignore")])
        for api in apis[:5]:  # Show max 5 APIs
            api_name = api.get('api_name', 'Unknown')
            description = api.get('api_description', '')
            button_text = f"• {api_name}"
            if description:
                button_text += f" - {description[:20]}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data="ignore")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_asset_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Create asset selection keyboard (BTC/ETH).
    
    Returns:
        InlineKeyboardMarkup with asset options
    """
    keyboard = [
        [
            InlineKeyboardButton("₿ BTC", callback_data="asset:BTC"),
            InlineKeyboardButton("Ξ ETH", callback_data="asset:ETH")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="menu:main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_expiry_selection_keyboard(expiries: List[str]) -> InlineKeyboardMarkup:
    """
    Create expiry selection keyboard.
    
    Args:
        expiries: List of expiry notations (D, D+1, W, etc.)
    
    Returns:
        InlineKeyboardMarkup with expiry options
    """
    from utils.helpers import get_expiry_display_name
    
    keyboard = []
    
    # Common expiries
    common = ['D', 'D+1', 'W', 'W+1', 'W+2', 'M', 'M+1', 'M+2']
    
    row = []
    for expiry in common:
        if expiry in expiries:
            display_name = get_expiry_display_name(expiry)
            row.append(InlineKeyboardButton(display_name, callback_data=f"expiry:{expiry}"))
            
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:list_options")])
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_direction_keyboard() -> InlineKeyboardMarkup:
    """
    Create direction selection keyboard (Long/Short).
    
    Returns:
        InlineKeyboardMarkup with direction options
    """
    keyboard = [
        [
            InlineKeyboardButton("📈 Long", callback_data="direction:long"),
            InlineKeyboardButton("📉 Short", callback_data="direction:short")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="menu:main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel") -> InlineKeyboardMarkup:
    """
    Create confirmation keyboard (Confirm/Cancel).
    
    Args:
        confirm_data: Callback data for confirm button
        cancel_data: Callback data for cancel button
    
    Returns:
        InlineKeyboardMarkup with confirmation options
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=confirm_data),
            InlineKeyboardButton("❌ Cancel", callback_data=cancel_data)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_strategy_list_keyboard(strategies: List[dict], strategy_type: str) -> InlineKeyboardMarkup:
    """
    Create strategy list keyboard with CRUD operations.
    
    Args:
        strategies: List of strategy presets
        strategy_type: 'straddle' or 'strangle'
    
    Returns:
        InlineKeyboardMarkup with strategy options
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ Add", callback_data=f"strategy:{strategy_type}:add"),
            InlineKeyboardButton("✏️ Edit", callback_data=f"strategy:{strategy_type}:edit"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"strategy:{strategy_type}:delete")
        ]
    ]
    
    # Add existing strategies
    if strategies:
        keyboard.append([InlineKeyboardButton("📋 Available Strategies:", callback_data="ignore")])
        for strategy in strategies[:8]:  # Show max 8 strategies
            strategy_name = strategy.get('strategy_name', 'Unknown')
            button_text = f"• {strategy_name}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"strategy:{strategy_type}:view:{strategy_name}")
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_api_list_keyboard(apis: List[dict], action: str) -> InlineKeyboardMarkup:
    """
    Create API selection keyboard.
    
    Args:
        apis: List of API credentials
        action: Action to perform (e.g., 'select', 'edit', 'delete')
    
    Returns:
        InlineKeyboardMarkup with API options
    """
    keyboard = []
    
    for api in apis:
        api_name = api.get('api_name', 'Unknown')
        keyboard.append([
            InlineKeyboardButton(f"• {api_name}", callback_data=f"api:{action}:{api_name}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:manage_api")])
    
    return InlineKeyboardMarkup(keyboard)


@log_function_calls
def get_position_list_keyboard(positions: List[dict]) -> InlineKeyboardMarkup:
    """
    Create position list keyboard with SL/TP options.
    
    Args:
        positions: List of positions
    
    Returns:
        InlineKeyboardMarkup with position options
    """
    keyboard = []
    
    for position in positions[:10]:  # Show max 10 positions
        product_id = position.get('product_id')
        symbol = position.get('product_symbol', 'Unknown')
        size = position.get('size', 0)
        pnl = position.get('unrealized_pnl', 0)
        
        pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        button_text = f"{pnl_emoji} {symbol} | Size: {size} | PnL: ${pnl:.2f}"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"position:select:{product_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_sl_tp_options_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    Create SL/TP options keyboard.
    
    Args:
        product_id: Product ID
    
    Returns:
        InlineKeyboardMarkup with SL/TP options
    """
    keyboard = [
        [
            InlineKeyboardButton("✏️ Set Manually", callback_data=f"sltp:manual:{product_id}"),
            InlineKeyboardButton("💰 SL to Cost", callback_data=f"sltp:cost:{product_id}")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="menu:positions")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str
) -> InlineKeyboardMarkup:
    """
    Create pagination keyboard.
    
    Args:
        current_page: Current page number (1-indexed)
        total_pages: Total number of pages
        callback_prefix: Prefix for callback data
    
    Returns:
        InlineKeyboardMarkup with pagination buttons
    """
    keyboard = []
    
    row = []
    
    # Previous button
    if current_page > 1:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"{callback_prefix}:page:{current_page-1}"))
    
    # Page indicator
    row.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="ignore"))
    
    # Next button
    if current_page < total_pages:
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"{callback_prefix}:page:{current_page+1}"))
    
    keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    return InlineKeyboardMarkup(keyboard)


@log_function_call
def get_yes_no_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    """
    Create simple Yes/No keyboard.
    
    Args:
        yes_data: Callback data for Yes button
        no_data: Callback data for No button
    
    Returns:
        InlineKeyboardMarkup with Yes/No buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=yes_data),
            InlineKeyboardButton("❌ No", callback_data=no_data)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


if __name__ == "__main__":
    # Test keyboard creation
    print("Testing keyboard creation...")
    
    # Test main menu
    main_menu = get_main_menu_keyboard()
    print(f"✅ Main menu keyboard: {len(main_menu.inline_keyboard)} rows")
    
    # Test asset selection
    asset_kb = get_asset_selection_keyboard()
    print(f"✅ Asset keyboard: {len(asset_kb.inline_keyboard)} rows")
    
    # Test direction
    direction_kb = get_direction_keyboard()
    print(f"✅ Direction keyboard: {len(direction_kb.inline_keyboard)} rows")
    
    # Test confirmation
    confirm_kb = get_confirmation_keyboard("confirm:test", "cancel:test")
    print(f"✅ Confirmation keyboard: {len(confirm_kb.inline_keyboard)} rows")
    
    print("\n✅ Keyboard tests completed!")
  
