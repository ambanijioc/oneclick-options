"""
MOVE Trade Preset Management Handler - COMPLETE CRUD FLOW
Links API Keys + MOVE Strategies into executable presets
Flow: Add, Edit, Delete, View, Back to Main Menu
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import StateManager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_trade_preset,
    get_move_trade_presets,
    get_move_trade_preset,
    update_move_trade_preset,
    delete_move_trade_preset,
    get_move_strategy
)
from database.operations.api_ops import get_api_credentials, get_api_credential_by_id
from bot.keyboard.move_trade_preset_keyboards import (
    main_menu_keyboard,
    view_presets_keyboard,
    preset_detail_keyboard,
    delete_confirm_keyboard,
    add_cancel_keyboard
)

logger = setup_logger(__name__)
state_manager = StateManager()

# MAIN MENU
@error_handler
async def move_trade_preset_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    presets = await get_move_trade_presets(user.id)
    await query.edit_message_text(
        "<b>🎯 MOVE Trade Preset Management</b>\n\n"
        f"You have <b>{len(presets)}</b> trade {'preset' if len(presets) == 1 else 'presets'}.\n\n"
        "<b>What is a Trade Preset?</b>\n"
        "A preset combines:\n"
        "• <b>API Key:</b> Your Delta Exchange credentials\n"
        "• <b>Strategy:</b> Your MOVE trading strategy\n\n"
        "Once created, you can execute trades with one click!\n\n"
        "What would you like to do?",
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )
    log_user_action(user.id, "move_preset_menu", f"Viewed menu with {len(presets)} presets")

# VIEW PRESETS
@error_handler
async def move_preset_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    presets = await get_move_trade_presets(user.id)
    if not presets:
        await query.edit_message_text(
            "<b>📋 MOVE Trade Presets</b>\n\n"
            "❌ No trade presets found.\n\n"
            "Create your first preset to start trading!",
            reply_markup=add_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    await query.edit_message_text(
        f"<b>📋 Your MOVE Trade Presets ({len(presets)})</b>\n\n"
        "Select a preset to view details:",
        reply_markup=view_presets_keyboard(presets),
        parse_mode='HTML'
    )

# VIEW PRESET DETAIL
@error_handler
async def move_preset_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    preset = await get_move_trade_preset(preset_id)
    if not preset:
        await query.edit_message_text(
            "❌ Trade preset not found.",
            reply_markup=add_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    api = await get_api_credential_by_id(preset['api_id'])
    strategy = await get_move_strategy(preset['strategy_id'])
    if not api or not strategy:
        await query.edit_message_text(
            "❌ Linked API or Strategy not found. Preset may be corrupted.",
            reply_markup=delete_confirm_keyboard(preset_id),
            parse_mode='HTML'
        )
        return
    # Construct your details text as before, e.g.:
    text = (
        f"<b>Preset Name:</b> {preset.get('preset_name','Unnamed')}\n"
        f"<b>API:</b> {api.api_name if api else 'Missing'}\n"
        f"<b>Strategy:</b> {strategy.get('strategy_name','Unnamed') if strategy else 'Missing'}"
    )
    await query.edit_message_text(
        text,
        reply_markup=preset_detail_keyboard(preset_id),
        parse_mode='HTML'
    )

# DELETE PRESET CONFIRM
@error_handler
async def move_preset_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    preset_id = query.data.split('_')[-1]
    preset = await get_move_trade_preset(preset_id)
    if not preset:
        await query.edit_message_text(
            "❌ Trade preset not found.",
            reply_markup=add_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    await query.edit_message_text(
        f"<b>⚠️ Delete Trade Preset?</b>\n\n"
        f"Are you sure you want to delete:\n"
        f"<b>{preset.get('preset_name', 'Unnamed')}</b>?\n\n"
        "This will NOT delete the linked strategy or API key.\n"
        "This action cannot be undone!",
        reply_markup=delete_confirm_keyboard(preset_id),
        parse_mode='HTML'
    )

# DELETE PRESET
@error_handler
async def move_preset_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    preset_id = query.data.split('_')[-1]
    preset = await get_move_trade_preset(preset_id)
    if not preset:
        await query.edit_message_text(
            "❌ Trade preset not found.",
            reply_markup=add_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    success = await delete_move_trade_preset(preset_id)
    if success:
        await query.edit_message_text(
            f"✅ Trade preset '<b>{preset.get('preset_name', 'Unnamed')}</b>' deleted successfully!",
            reply_markup=view_presets_keyboard(await get_move_trade_presets(user.id)),
            parse_mode='HTML'
        )
        log_user_action(user.id, "move_preset_delete", f"Deleted preset {preset_id}")
    else:
        await query.edit_message_text(
            "❌ Failed to delete trade preset. Please try again.",
            reply_markup=preset_detail_keyboard(preset_id),
            parse_mode='HTML'
        )

# ADD/CANCEL (same, but uses add_cancel_keyboard for reply_markup)
@error_handler
async def move_preset_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    await state_manager.set_state(user.id, 'awaiting_move_preset_name')
    await state_manager.set_state_data(user.id, {})
    await query.edit_message_text(
        "<b>➕ Add Trade Preset - Step 1/3</b>\n\n"
        "Enter a <b>name</b> for your trade preset:\n\n"
        "Examples:\n"
        "• Main BTC Long Setup\n"
        "• ETH Short Trading\n"
        "• Daily Volatility Play\n\n"
        "👉 Type the name below:",
        reply_markup=add_cancel_keyboard(),
        parse_mode='HTML'
    )
    log_user_action(user.id, "move_preset_add", "Started preset creation")

@error_handler
async def move_preset_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    await state_manager.clear_state(user.id)
    await move_trade_preset_menu_callback(update, context)

@error_handler
async def move_preset_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel preset creation/editing."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Return to menu
    await move_trade_preset_menu_callback(update, context)


# ============================================================================
# TEXT INPUT HANDLERS
# ============================================================================

@error_handler
async def handle_move_preset_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text inputs during preset creation."""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    state_data = await state_manager.get_state_data(user.id)
    
    if not state:
        return
    
    # Handle preset name input
    if state == 'awaiting_move_preset_name':
        await handle_preset_name_input(update, context, text, state_data)


async def handle_preset_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state_data: dict):
    """Handle preset name input."""
    user = update.effective_user
    
    if len(text) < 3:
        await update.message.reply_text(
            "❌ Preset name must be at least 3 characters long.\n\n"
            "Please try again:",
            parse_mode='HTML'
        )
        return
    
    if len(text) > 50:
        await update.message.reply_text(
            "❌ Preset name must be 50 characters or less.\n\n"
            "Please try again:",
            parse_mode='HTML'
        )
        return
    
    # Store name
    state_data['preset_name'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Move to API selection
    apis = await get_api_credentials(user.id)
    
    keyboard = []
    for api in apis:
        keyboard.append([InlineKeyboardButton(
            f"🔑 {api.api_name}",
            callback_data=f"move_preset_api_{api.id}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="move_preset_cancel")])
    
    await update.message.reply_text(
        f"<b>➕ Add Trade Preset - Step 2/3</b>\n\n"
        f"<b>Preset Name:</b> {text}\n\n"
        f"Select an <b>API Key</b> to use:\n\n"
        f"You have {len(apis)} API {'key' if len(apis) == 1 else 'keys'} configured.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# API SELECTION
# ============================================================================

@error_handler
async def move_preset_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API key selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    api_id = query.data.split('_')[-1]
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['api_id'] = api_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Get API name for display
    api = await get_api_credential_by_id(api_id)
    
    # Move to strategy selection
    from database.operations.move_strategy_ops import get_move_strategies
    strategies = await get_move_strategies(user.id)
    
    keyboard = []
    for strategy in strategies:
        name = strategy.get('strategy_name', 'Unnamed')
        asset = strategy.get('asset', 'BTC')
        direction = strategy.get('direction', 'long')
        direction_emoji = "📈" if direction == "long" else "📉"
        
        button_text = f"{direction_emoji} {name} ({asset})"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"move_preset_strategy_{strategy['id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="move_preset_cancel")])
    
    await query.edit_message_text(
        f"<b>➕ Add Trade Preset - Step 3/3</b>\n\n"
        f"<b>Preset Name:</b> {state_data['preset_name']}\n"
        f"<b>API Key:</b> {api.api_name}\n\n"
        f"Select a <b>MOVE Strategy</b> to use:\n\n"
        f"You have {len(strategies)} {'strategy' if len(strategies) == 1 else 'strategies'} configured.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# STRATEGY SELECTION & CONFIRMATION
# ============================================================================

@error_handler
async def move_preset_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection and show confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[-1]
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['strategy_id'] = strategy_id
    await state_manager.set_state_data(user.id, state_data)
    
    # Get full details for confirmation
    api = await get_api_credential_by_id(state_data['api_id'])
    strategy = await get_move_strategy(strategy_id)
    
    if not api or not strategy:
        await query.edit_message_text(
            "❌ Error loading details. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu_move_trade_preset")]
            ]),
            parse_mode='HTML'
        )
        return
    
    # Build confirmation message
    text = f"<b>✅ Confirm Trade Preset Creation</b>\n\n"
    text += f"<b>Preset Name:</b> {state_data['preset_name']}\n\n"
    
    text += f"<b>🔑 API Credentials:</b>\n"
    text += f"• {api.api_name}\n\n"
    
    text += f"<b>📊 Trading Strategy:</b>\n"
    text += f"• Name: {strategy.get('strategy_name', 'Unnamed')}\n"
    text += f"• Asset: {strategy.get('asset', 'BTC')}\n"
    text += f"• Expiry: {strategy.get('expiry', 'daily').title()}\n"
    text += f"• Direction: {strategy.get('direction', 'long').title()}\n"
    text += f"• ATM Offset: {strategy.get('atm_offset', 0):+d}\n"
    
    sl_trigger = strategy.get('stop_loss_trigger')
    if sl_trigger:
        text += f"• Stop Loss: {sl_trigger:.1f}%\n"
    
    target_trigger = strategy.get('target_trigger')
    if target_trigger:
        text += f"• Target: {target_trigger:.1f}%\n"
    
    text += "\n⚠️ Create this trade preset?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Create Preset", callback_data="move_preset_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_preset_cancel")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ============================================================================
# CONFIRM & CREATE
# ============================================================================

@error_handler
async def move_preset_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and create the trade preset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    state_data = await state_manager.get_state_data(user.id)
    
    # Create preset
    preset_data = {
        'preset_name': state_data['preset_name'],
        'api_id': state_data['api_id'],
        'strategy_id': state_data['strategy_id']
    }
    
    preset_id = await create_move_trade_preset(user.id, preset_data)
    
    if preset_id:
        text = f"<b>✅ Trade Preset Created!</b>\n\n"
        text += f"<b>Preset Name:</b> {state_data['preset_name']}\n\n"
        text += f"Your trade preset is ready to use!\n\n"
        text += f"You can now:\n"
        text += f"• Execute manual trades with one click\n"
        text += f"• Set up automated trading schedules\n"
        text += f"• Monitor your active positions"
        
        keyboard = [
            [InlineKeyboardButton("🚀 Execute Manual Trade", callback_data="menu_move_manual_trade")],
            [InlineKeyboardButton("📋 View Presets", callback_data="move_preset_view")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "move_preset_create", f"Created preset: {state_data['preset_name']}")
    else:
        await query.edit_message_text(
            "❌ Failed to create trade preset. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu_move_trade_preset")]
            ]),
            parse_mode='HTML'
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


# ============================================================================
# EDIT PRESET (Simplified - just change name for now)
# ============================================================================

@error_handler
async def move_preset_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing preset (currently only name)."""
    query = update.callback_query
    await query.answer()
    
    preset_id = query.data.split('_')[-1]
    
    # For now, just show option to change name
    # Full edit would allow changing API/Strategy
    await query.edit_message_text(
        "<b>✏️ Edit Trade Preset</b>\n\n"
        "Editing is currently limited.\n\n"
        "To change API or Strategy, please:\n"
        "1. Delete this preset\n"
        "2. Create a new one with desired settings\n\n"
        "Full edit functionality coming soon!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data=f"move_preset_detail{preset_id}")]
        ]),
        parse_mode='HTML'
    )


# ============================================================================
# REGISTER HANDLERS
# ============================================================================

def register_move_trade_preset_handlers(application: Application):
    """Register all MOVE trade preset handlers."""
    
    # Main menu
    application.add_handler(CallbackQueryHandler(
        move_trade_preset_menu_callback,
        pattern="^menu_move_trade_preset"
    ))
    
    # View presets
    application.add_handler(CallbackQueryHandler(
        move_preset_view_callback,
        pattern="^move_preset_view"
    ))
    
    # View detail
    application.add_handler(CallbackQueryHandler(
        move_preset_detail_callback,
        pattern="^move_preset_detail"
    ))
    
    # Delete (confirmation + action)
    application.add_handler(CallbackQueryHandler(
        move_preset_delete_confirm_callback,
        pattern="^move_preset_delete_confirm"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_delete_callback,
        pattern="^move_preset_delete"
    ))
    
    # Add preset flow
    application.add_handler(CallbackQueryHandler(
        move_preset_add_callback,
        pattern="^move_preset_add"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_api_callback,
        pattern="^move_preset_api"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_strategy_callback,
        pattern="^move_preset_strategy"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_preset_confirm_callback,
        pattern="^move_preset_confirm"
    ))
    
    # Edit
    application.add_handler(CallbackQueryHandler(
        move_preset_edit_callback,
        pattern="^move_preset_edit"
    ))
    
    # Cancel
    application.add_handler(CallbackQueryHandler(
        move_preset_cancel_callback,
        pattern="^move_preset_cancel"
    ))
    
    # Text input handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_move_preset_text_input
        ),
        group=0
    )
    
    logger.info("MOVE trade preset handlers registered successfully")
