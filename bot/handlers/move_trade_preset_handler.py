"""
Move Options Trade Preset management handlers.
Manages presets that combine API + Move Strategy for quick execution.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.api_ops import get_api_credentials
from database.operations.move_strategy_ops import get_move_strategies
from database.operations.move_trade_preset_ops import (
    create_move_trade_preset,
    get_move_trade_presets,
    get_move_trade_preset_by_id,
    update_move_trade_preset,
    delete_move_trade_preset
)

logger = setup_logger(__name__)


def get_move_preset_menu_keyboard():
    """Get move trade preset management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Preset", callback_data="move_preset_add")],
        [InlineKeyboardButton("✏️ Edit Preset", callback_data="move_preset_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Preset", callback_data="move_preset_delete_list")],
        [InlineKeyboardButton("👁️ View Presets", callback_data="move_preset_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_preset_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display move trade preset management menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get presets count
    presets = await get_move_trade_presets(user.id)
    
    await query.edit_message_text(
        "<b>🎯 Move Options Trade Preset Management</b>\n\n"
        "Create quick-execute presets combining:\n"
        "• API Credentials\n"
        "• Move Strategy Settings\n\n"
        "Select an option:\n\n"
        f"<b>Total Presets:</b> {len(presets)}",
        reply_markup=get_move_preset_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_preset_menu", "Viewed move preset menu")


# ========== ADD PRESET ==========

@error_handler
async def move_preset_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add move preset flow - ask for name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'move_preset_add_name')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_preset")]]
    
    await query.edit_message_text(
        "<b>➕ Add Move Preset</b>\n\n"
        "Enter a name for this preset:\n\n"
        "Example: <code>BTC Quick Move</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_preset_add", "Started add preset flow")


@error_handler
async def move_preset_select_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show API selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    if not apis:
        await query.edit_message_text(
            "<b>❌ No API Credentials</b>\n\n"
            "Please add API credentials first.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with APIs
    keyboard = []
    for api in apis:
        name = api.name if hasattr(api, 'name') else api.get('name', 'N/A')
        api_id = str(api.id) if hasattr(api, 'id') else str(api.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"🔑 {name}",
            callback_data=f"move_preset_api_{api_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_preset")])
    
    await query.edit_message_text(
        "<b>➕ Add Move Preset</b>\n\n"
        "Select API Credentials:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_api_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    # Store API ID
    state_data = await state_manager.get_state_data(user.id)
    state_data['api_id'] = api_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Get move strategies
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "<b>❌ No Move Strategies</b>\n\n"
            "Please create a move strategy first.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with strategies
    keyboard = []
    for strategy in strategies:
        name = strategy.strategy_name if hasattr(strategy, 'strategy_name') else strategy.get('strategy_name', 'N/A')
        strategy_id = str(strategy.id) if hasattr(strategy, 'id') else str(strategy.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"📊 {name}",
            callback_data=f"move_preset_strategy_{strategy_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_preset")])
    
    await query.edit_message_text(
        "<b>➕ Add Move Preset</b>\n\n"
        "Select Move Strategy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_strategy_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection and show confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    # Store strategy ID
    state_data = await state_manager.get_state_data(user.id)
    state_data['strategy_id'] = strategy_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Get API details
    from database.operations.api_ops import get_api_credential_by_id
    api = await get_api_credential_by_id(state_data['api_id'])
    
    # Get strategy details
    from database.operations.move_strategy_ops import get_move_strategy
    strategy = await get_move_strategy(strategy_id)
    
    if not api or not strategy:
        await query.edit_message_text(
            "❌ Error loading details",
            reply_markup=get_move_preset_menu_keyboard()
        )
        return
    
    # Extract details
    api_name = api.name if hasattr(api, 'name') else api.get('name', 'N/A')
    strategy_name = strategy.strategy_name if hasattr(strategy, 'strategy_name') else strategy.get('strategy_name', 'N/A')
    asset = strategy.asset if hasattr(strategy, 'asset') else strategy.get('asset', 'N/A')
    direction = strategy.direction if hasattr(strategy, 'direction') else strategy.get('direction', 'N/A')
    lot_size = strategy.lot_size if hasattr(strategy, 'lot_size') else strategy.get('lot_size', 0)
    atm_offset = strategy.atm_offset if hasattr(strategy, 'atm_offset') else strategy.get('atm_offset', 0)
    sl_trigger = strategy.sl_trigger_pct if hasattr(strategy, 'sl_trigger_pct') else strategy.get('sl_trigger_pct', 0)
    sl_limit = strategy.sl_limit_pct if hasattr(strategy, 'sl_limit_pct') else strategy.get('sl_limit_pct', 0)
    
    text = (
        f"<b>✅ Confirm Move Preset</b>\n\n"
        f"<b>Preset Name:</b> {state_data['preset_name']}\n\n"
        f"<b>📡 API:</b> {api_name}\n\n"
        f"<b>📊 Strategy:</b> {strategy_name}\n"
        f"• Asset: {asset}\n"
        f"• Direction: {direction.title()}\n"
        f"• Lot Size: {lot_size}\n"
        f"• ATM Offset: {atm_offset:+d}\n"
        f"• SL: {sl_trigger}% / {sl_limit}%\n\n"
        f"<b>Confirm to save this preset?</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="move_preset_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_preset")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save move preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get state data
    state_data = await state_manager.get_state_data(user.id)
    
    # Create preset
    preset_data = {
        'preset_name': state_data['preset_name'],
        'api_id': state_data['api_id'],
        'strategy_id': state_data['strategy_id']
    }
    
    success = await create_move_trade_preset(user.id, preset_data)
    
    if success:
        await query.edit_message_text(
            f"<b>✅ Preset Created Successfully!</b>\n\n"
            f"Name: <b>{state_data['preset_name']}</b>\n\n"
            f"You can now use this preset for quick move option trades.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_preset_create", f"Created preset: {state_data['preset_name']}")
    else:
        await query.edit_message_text(
            "❌ Failed to create preset.",
            reply_markup=get_move_preset_menu_keyboard()
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


# ========== VIEW PRESETS ==========

@error_handler
async def move_preset_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all move presets."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get presets
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>👁️ Move Trade Presets</b>\n\n"
            "❌ No presets found.\n\n"
            "Create one using <b>Add Preset</b>.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    text = "<b>👁️ Move Trade Presets</b>\n\n"
    
    for preset in presets:
        name = preset.preset_name if hasattr(preset, 'preset_name') else preset.get('preset_name', 'N/A')
        
        # Get linked API and strategy names
        api_id = preset.api_id if hasattr(preset, 'api_id') else preset.get('api_id')
        strategy_id = preset.strategy_id if hasattr(preset, 'strategy_id') else preset.get('strategy_id')
        
        # Fetch names (simplified for display)
        text += f"<b>📊 {name}</b>\n"
        text += f"API ID: {api_id}\n"
        text += f"Strategy ID: {strategy_id}\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_move_preset_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_preset_view", f"Viewed {len(presets)} presets")


# ========== DELETE PRESET ==========

@error_handler
async def move_preset_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of presets to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get presets
    presets = await get_move_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>🗑️ Delete Preset</b>\n\n"
            "❌ No presets found.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard
    keyboard = []
    for preset in presets:
        name = preset.preset_name if hasattr(preset, 'preset_name') else preset.get('preset_name', 'N/A')
        preset_id = str(preset.id) if hasattr(preset, 'id') else str(preset.get('_id', ''))
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {name}",
            callback_data=f"move_preset_delete_{preset_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_move_preset")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Preset</b>\n\n"
        "Select preset to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete - ask confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Get preset
    preset = await get_move_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Store preset ID
    await state_manager.set_state_data(user.id, {'delete_preset_id': preset_id})
    
    name = preset.preset_name if hasattr(preset, 'preset_name') else preset.get('preset_name', 'N/A')
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="move_preset_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_move_preset")]
    ]
    
    await query.edit_message_text(
        f"<b>🗑️ Delete Preset</b>\n\n"
        f"<b>Name:</b> {name}\n\n"
        f"⚠️ Are you sure you want to delete this preset?\n\n"
        f"This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get preset ID
    state_data = await state_manager.get_state_data(user.id)
    preset_id = state_data.get('delete_preset_id')
    
    if not preset_id:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Delete preset
    success = await delete_move_trade_preset(preset_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Preset Deleted</b>\n\n"
            "The preset has been deleted successfully.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_preset_delete", f"Deleted preset {preset_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete preset.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


# ========== REGISTER HANDLERS ==========

def register_move_preset_handlers(application: Application):
    """Register move trade preset handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_preset_menu_callback,
        pattern="^menu_move_preset$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_add_callback,
        pattern="^move_preset_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_select_api_callback,
        pattern="^move_preset_select_api$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_api_selected_callback,
        pattern="^move_preset_api_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_strategy_selected_callback,
        pattern="^move_preset_strategy_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_confirm_callback,
        pattern="^move_preset_confirm$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_view_callback,
        pattern="^move_preset_view$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_delete_list_callback,
        pattern="^move_preset_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_delete_callback,
        pattern="^move_preset_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_delete_confirm_callback,
        pattern="^move_preset_delete_confirm$"
    ))
    
    logger.info("Move trade preset handlers registered")
      
