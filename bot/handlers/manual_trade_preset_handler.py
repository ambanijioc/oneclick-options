"""
Manual trade preset handlers.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.manual_trade_preset_ops import (
    create_manual_trade_preset,
    get_manual_trade_presets,
    get_manual_trade_preset,
    update_manual_trade_preset,
    delete_manual_trade_preset
)
from database.operations.api_ops import get_api_credentials, get_api_credential_by_id
from database.operations.strategy_ops import (
    get_strategy_presets_by_type,
    get_strategy_preset_by_id
)

logger = setup_logger(__name__)
#state_manager = StateManager()


def get_manual_preset_menu_keyboard():
    """Get manual trade preset menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Preset", callback_data="manual_preset_add")],
        [InlineKeyboardButton("✏️ Edit Preset", callback_data="manual_preset_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Preset", callback_data="manual_preset_delete_list")],
        [InlineKeyboardButton("👁️ View Presets", callback_data="manual_preset_view_list")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def manual_preset_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display manual trade preset menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get presets
    presets = await get_manual_trade_presets(user.id)
    
    await query.edit_message_text(
        "<b>🎯 Manual Trade Presets</b>\n\n"
        "Save your favorite API + Strategy combinations for quick trade execution.\n\n"
        "• <b>Add:</b> Create new preset\n"
        "• <b>Edit:</b> Modify existing preset\n"
        "• <b>Delete:</b> Remove preset\n"
        "• <b>View:</b> See all presets\n\n"
        f"<b>Total Presets:</b> {len(presets)}",
        reply_markup=get_manual_preset_menu_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "manual_preset_menu", f"Viewed preset menu: {len(presets)} presets")


@error_handler
async def manual_preset_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add preset flow - ask for name."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Set state
    await state_manager.set_state(user.id, 'manual_preset_add_name')
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")]]
    
    await query.edit_message_text(
        "<b>➕ Add Manual Trade Preset</b>\n\n"
        "Please enter a name for this preset:\n\n"
        "Example: <code>Quick BTC Straddle</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "manual_preset_add", "Started add preset flow")


@error_handler
async def manual_preset_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API selection - show strategy list."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    # Store API ID
    state_data = await state_manager.get_state_data(user.id)
    state_data['api_credential_id'] = api_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Get strategies (both straddle and strangle)
    straddle_strategies = await get_strategy_presets_by_type(user.id, "straddle")
    strangle_strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    if not straddle_strategies and not strangle_strategies:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_manual_preset")]]
        await query.edit_message_text(
            "<b>➕ Add Manual Trade Preset</b>\n\n"
            "❌ No strategies found.\n\n"
            "Create a strategy first.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Create strategy selection keyboard
    keyboard = []
    
    if straddle_strategies:
        keyboard.append([InlineKeyboardButton("--- Straddle Strategies ---", callback_data="noop")])
        for strategy in straddle_strategies:
            keyboard.append([InlineKeyboardButton(
                f"🎲 {strategy['name']}",
                callback_data=f"manual_preset_strategy_{strategy['_id']}_straddle"
            )])
    
    if strangle_strategies:
        keyboard.append([InlineKeyboardButton("--- Strangle Strategies ---", callback_data="noop")])
        for strategy in strangle_strategies:
            keyboard.append([InlineKeyboardButton(
                f"🎰 {strategy['name']}",
                callback_data=f"manual_preset_strategy_{strategy['_id']}_strangle"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")])
    
    await query.edit_message_text(
        "<b>➕ Add Manual Trade Preset</b>\n\n"
        "Select strategy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection - show confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Parse callback data: manual_preset_strategy_{id}_{type}
    parts = query.data.split('_')
    strategy_id = parts[3]
    strategy_type = parts[4]
    
    # Get strategy and API details
    strategy = await get_strategy_preset_by_id(strategy_id)
    state_data = await state_manager.get_state_data(user.id)
    api = await get_api_credential_by_id(state_data['api_credential_id'])
    
    if not strategy or not api:
        await query.edit_message_text("❌ Strategy or API not found")
        return
    
    # Store strategy info
    state_data['strategy_preset_id'] = strategy_id
    state_data['strategy_type'] = strategy_type
    await state_manager.set_state_data(user.id, state_data)
    
    # Format confirmation message
    text = "<b>➕ Confirm Manual Trade Preset</b>\n\n"
    text += f"<b>Preset Name:</b> {state_data['preset_name']}\n\n"
    text += f"<b>📊 API:</b> {api.api_name}\n"
    text += f"<b>🎯 Strategy:</b> {strategy['name']}\n"
    text += f"<b>Type:</b> {strategy_type.title()}\n"
    text += f"<b>Asset:</b> {strategy['asset']}\n"
    text += f"<b>Expiry:</b> {strategy['expiry_code']}\n"
    text += f"<b>Direction:</b> {strategy['direction'].title()}\n"
    text += f"<b>Lot Size:</b> {strategy['lot_size']}\n\n"
    text += "⚠️ Save this preset?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="manual_preset_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_manual_preset")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get preset data
    state_data = await state_manager.get_state_data(user.id)
    
    # Save to database
    result = await create_manual_trade_preset(user.id, state_data)
    
    if result:
        await query.edit_message_text(
            f"<b>✅ Preset Created</b>\n\n"
            f"Name: <b>{state_data['preset_name']}</b>\n\n"
            f"Your manual trade preset has been saved successfully!",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "manual_preset_create", f"Created preset: {state_data['preset_name']}")
    else:
        await query.edit_message_text(
            "<b>❌ Failed to Create Preset</b>\n\n"
            "Please try again.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


@error_handler
async def manual_preset_view_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of presets to view."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>👁️ View Presets</b>\n\n"
            "❌ No presets found.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"📋 {preset['preset_name']}",
            callback_data=f"manual_preset_view_{preset['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_manual_preset")])
    
    await query.edit_message_text(
        "<b>👁️ View Presets</b>\n\n"
        "Select a preset to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View preset details."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Get preset
    preset = await get_manual_trade_preset(preset_id)
    
    if not preset:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Get API and strategy details
    api = await get_api_credential_by_id(preset['api_credential_id'])
    strategy = await get_strategy_preset_by_id(preset['strategy_preset_id'])
    
    # Format details
    text = f"<b>📋 {preset['preset_name']}</b>\n\n"
    
    if api:
        text += f"<b>📊 API:</b> {api.api_name}\n\n"
    
    if strategy:
        text += f"<b>🎯 Strategy:</b> {strategy['name']}\n"
        text += f"<b>Type:</b> {preset['strategy_type'].title()}\n"
        text += f"<b>Asset:</b> {strategy['asset']}\n"
        text += f"<b>Expiry:</b> {strategy['expiry_code']}\n"
        text += f"<b>Direction:</b> {strategy['direction'].title()}\n"
        text += f"<b>Lot Size:</b> {strategy['lot_size']}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to List", callback_data="manual_preset_view_list")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_manual_preset")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of presets to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>🗑️ Delete Preset</b>\n\n"
            "❌ No presets found.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {preset['preset_name']}",
            callback_data=f"manual_preset_delete_{preset['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")])
    
    await query.edit_message_text(
        "<b>🗑️ Delete Preset</b>\n\n"
        "Select preset to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete preset - ask confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Get preset
    preset = await get_manual_trade_preset(preset_id)
    
    if not preset:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Store preset ID
    await state_manager.set_state_data(user.id, {'delete_preset_id': preset_id})
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delete", callback_data="manual_preset_delete_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_manual_preset")]
    ]
    
    await query.edit_message_text(
        f"<b>🗑️ Delete Preset</b>\n\n"
        f"<b>Name:</b> {preset['preset_name']}\n\n"
        f"⚠️ Are you sure you want to delete this preset?\n\n"
        f"This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    success = await delete_manual_trade_preset(preset_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Preset Deleted</b>\n\n"
            "The preset has been deleted successfully.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "manual_preset_delete", f"Deleted preset {preset_id}")
    else:
        await query.edit_message_text(
            "<b>❌ Delete Failed</b>\n\n"
            "Failed to delete preset.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


@error_handler
async def manual_preset_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of presets to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get presets
    presets = await get_manual_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "<b>✏️ Edit Preset</b>\n\n"
            "❌ No presets found.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with presets
    keyboard = []
    for preset in presets:
        keyboard.append([InlineKeyboardButton(
            f"✏️ {preset['preset_name']}",
            callback_data=f"manual_preset_edit_{preset['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Preset</b>\n\n"
        "Select preset to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit flow - get APIs."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    
    # Get preset
    preset = await get_manual_trade_preset(preset_id)
    
    if not preset:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Store preset info for edit
    await state_manager.set_state_data(user.id, {
        'edit_preset_id': preset_id,
        'preset_name': preset['preset_name']
    })
    
    # Get user's APIs
    apis = await get_api_credential_by_id(user.id)
    
    if not apis:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")]]
        await query.edit_message_text(
            "<b>✏️ Edit Preset</b>\n\n"
            "❌ No API credentials found.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Create keyboard with API options
    keyboard = []
    for api in apis:
        keyboard.append([InlineKeyboardButton(
            f"📊 {api.api_name}",
            callback_data=f"manual_preset_edit_api_{api.id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")])
    
    await query.edit_message_text(
        f"<b>✏️ Edit Preset: {preset['preset_name']}</b>\n\n"
        f"Select new API account:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_edit_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API selection for edit - show strategy list."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    # Store API ID
    state_data = await state_manager.get_state_data(user.id)
    state_data['api_credential_id'] = api_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Get strategies (both straddle and strangle)
    straddle_strategies = await get_strategy_presets_by_type(user.id, "straddle")
    strangle_strategies = await get_strategy_presets_by_type(user.id, "strangle")
    
    if not straddle_strategies and not strangle_strategies:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_manual_preset")]]
        await query.edit_message_text(
            "<b>✏️ Edit Preset</b>\n\n"
            "❌ No strategies found.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Create strategy selection keyboard
    keyboard = []
    
    if straddle_strategies:
        keyboard.append([InlineKeyboardButton("--- Straddle Strategies ---", callback_data="noop")])
        for strategy in straddle_strategies:
            keyboard.append([InlineKeyboardButton(
                f"🎲 {strategy['name']}",
                callback_data=f"manual_preset_edit_strategy_{strategy['_id']}_straddle"
            )])
    
    if strangle_strategies:
        keyboard.append([InlineKeyboardButton("--- Strangle Strategies ---", callback_data="noop")])
        for strategy in strangle_strategies:
            keyboard.append([InlineKeyboardButton(
                f"🎰 {strategy['name']}",
                callback_data=f"manual_preset_edit_strategy_{strategy['_id']}_strangle"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu_manual_preset")])
    
    await query.edit_message_text(
        "<b>✏️ Edit Preset</b>\n\n"
        "Select new strategy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_edit_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection for edit - show confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Parse callback data: manual_preset_edit_strategy_{id}_{type}
    parts = query.data.split('_')
    strategy_id = parts[4]
    strategy_type = parts[5]
    
    # Get strategy and API details
    strategy = await get_strategy_preset_by_id(strategy_id)
    state_data = await state_manager.get_state_data(user.id)
    api = await get_api_credential_by_id(state_data['api_credential_id'])
    
    if not strategy or not api:
        await query.edit_message_text("❌ Strategy or API not found")
        return
    
    # Store strategy info
    state_data['strategy_preset_id'] = strategy_id
    state_data['strategy_type'] = strategy_type
    await state_manager.set_state_data(user.id, state_data)
    
    # Format confirmation message
    text = "<b>✏️ Confirm Edit Preset</b>\n\n"
    text += f"<b>Preset Name:</b> {state_data['preset_name']}\n\n"
    text += f"<b>📊 API:</b> {api.api_name}\n"
    text += f"<b>🎯 Strategy:</b> {strategy['name']}\n"
    text += f"<b>Type:</b> {strategy_type.title()}\n"
    text += f"<b>Asset:</b> {strategy['asset']}\n"
    text += f"<b>Expiry:</b> {strategy['expiry_code']}\n"
    text += f"<b>Direction:</b> {strategy['direction'].title()}\n"
    text += f"<b>Lot Size:</b> {strategy['lot_size']}\n\n"
    text += "⚠️ Update this preset?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="manual_preset_edit_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_manual_preset")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def manual_preset_edit_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and update preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Get preset data
    state_data = await state_manager.get_state_data(user.id)
    preset_id = state_data.get('edit_preset_id')
    
    if not preset_id:
        await query.edit_message_text("❌ Preset not found")
        return
    
    # Update in database
    result = await update_manual_trade_preset(preset_id, state_data)
    
    if result:
        await query.edit_message_text(
            f"<b>✅ Preset Updated</b>\n\n"
            f"Name: <b>{state_data['preset_name']}</b>\n\n"
            f"Your manual trade preset has been updated successfully!",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "manual_preset_update", f"Updated preset: {state_data['preset_name']}")
    else:
        await query.edit_message_text(
            "<b>❌ Failed to Update Preset</b>\n\n"
            "Please try again.",
            reply_markup=get_manual_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


def register_manual_preset_handlers(application: Application):
    """Register manual trade preset handlers."""
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_menu_callback,
        pattern="^menu_manual_preset$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_add_callback,
        pattern="^manual_preset_add$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_api_callback,
        pattern="^manual_preset_api_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_strategy_callback,
        pattern="^manual_preset_strategy_[a-f0-9]{24}_(straddle|strangle)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_confirm_callback,
        pattern="^manual_preset_confirm$"
    ))
    
    # Edit handlers
    application.add_handler(CallbackQueryHandler(
        manual_preset_edit_list_callback,
        pattern="^manual_preset_edit_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_edit_callback,
        pattern="^manual_preset_edit_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_edit_api_callback,
        pattern="^manual_preset_edit_api_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_edit_strategy_callback,
        pattern="^manual_preset_edit_strategy_[a-f0-9]{24}_(straddle|strangle)$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_edit_confirm_callback,
        pattern="^manual_preset_edit_confirm$"
    ))
    
    # View handlers
    application.add_handler(CallbackQueryHandler(
        manual_preset_view_list_callback,
        pattern="^manual_preset_view_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_view_callback,
        pattern="^manual_preset_view_[a-f0-9]{24}$"
    ))
    
    # Delete handlers
    application.add_handler(CallbackQueryHandler(
        manual_preset_delete_list_callback,
        pattern="^manual_preset_delete_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_delete_callback,
        pattern="^manual_preset_delete_[a-f0-9]{24}$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        manual_preset_delete_confirm_callback,
        pattern="^manual_preset_delete_confirm$"
    ))
    
    logger.info("Manual trade preset handlers registered")
