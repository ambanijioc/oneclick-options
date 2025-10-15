"""
Strategy preset management handlers.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import (
    format_strategy_preset,
    format_error_message,
    escape_html
)
from bot.validators.user_validator import check_user_authorization
from bot.validators.input_validator import (
    validate_percentage,
    validate_lot_size,
    validate_expiry_code,
    validate_atm_offset,
    validate_otm_value,
    validate_api_name
)
from bot.utils.state_manager import state_manager, ConversationState
from bot.keyboards.strategy_keyboards import (
    get_strategy_management_keyboard,
    get_strategy_list_keyboard,
    get_strategy_edit_keyboard,
    get_strategy_delete_confirmation_keyboard,
    get_direction_keyboard,
    get_otm_type_keyboard
)
from bot.keyboards.options_keyboards import get_asset_selection_keyboard
from bot.keyboards.confirmation_keyboards import get_cancel_keyboard
from database.operations.strategy_ops import (
    create_strategy_preset,
    get_strategy_presets_by_type,
    get_strategy_preset_by_id,
    delete_strategy_preset
)
from database.models.strategy_preset import StrategyPresetCreate, OTMSelection

logger = setup_logger(__name__)


@error_handler
async def straddle_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle straddle strategy menu callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get user's straddle presets
    presets = await get_strategy_presets_by_type(user.id, "straddle")
    
    # Strategy menu text
    text = (
        "<b>🎲 Straddle Strategy</b>\n\n"
        "ATM call and put options with the same strike.\n"
        "Profit from high volatility in either direction.\n\n"
        f"<b>Configured Presets:</b> {len(presets)}"
    )
    
    # Show strategy management menu
    await query.edit_message_text(
        text,
        reply_markup=get_strategy_management_keyboard("straddle", presets),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "straddle_strategy", f"Opened straddle menu: {len(presets)} presets")


@error_handler
async def strangle_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strangle strategy menu callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get user's strangle presets
    presets = await get_strategy_presets_by_type(user.id, "strangle")
    
    # Strategy menu text
    text = (
        "<b>🎰 Strangle Strategy</b>\n\n"
        "OTM call and put options with different strikes.\n"
        "Lower cost than straddle, requires larger move.\n\n"
        f"<b>Configured Presets:</b> {len(presets)}"
    )
    
    # Show strategy management menu
    await query.edit_message_text(
        text,
        reply_markup=get_strategy_management_keyboard("strangle", presets),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strangle_strategy", f"Opened strangle menu: {len(presets)} presets")


@error_handler
async def strategy_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy list callback.
    Display all presets for a strategy type.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract strategy type from callback data
    strategy_type = query.data.split('_')[-1]
    
    # Get presets
    presets = await get_strategy_presets_by_type(user.id, strategy_type)
    
    # Show preset list
    await query.edit_message_text(
        f"<b>📋 {strategy_type.capitalize()} Presets</b>\n\n"
        f"Select a preset to view details:",
        reply_markup=get_strategy_list_keyboard(strategy_type, presets),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strategy_list", f"Viewed {strategy_type} presets: {len(presets)}")


@error_handler
async def strategy_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy view callback.
    Display detailed preset information.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract preset ID from callback data
    preset_id = query.data.split('_')[-1]
    
    # Get preset
    preset = await get_strategy_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            format_error_message("Strategy preset not found."),
            parse_mode='HTML'
        )
        return
    
    # Format preset details
    preset_text = format_strategy_preset(preset.model_dump())
    
    # Show preset details
    await query.edit_message_text(
        preset_text,
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strategy_view", f"Viewed preset: {preset.name}")


@error_handler
async def strategy_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle add strategy callback.
    Start strategy creation flow.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract strategy type from callback data
    strategy_type = query.data.split('_')[-1]
    
    # Set conversation state
    await state_manager.set_state(user.id, ConversationState.STRATEGY_ADD_NAME)
    await state_manager.update_data(user.id, {'strategy_type': strategy_type})
    
    # Ask for strategy name
    strategy_emoji = "🎲" if strategy_type == "straddle" else "🎰"
    text = (
        f"<b>{strategy_emoji} Add {strategy_type.capitalize()} Strategy</b>\n\n"
        "Please enter a name for this strategy:\n\n"
        "<i>Example: BTC Weekly Straddle</i>"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_cancel_keyboard(f"menu_{strategy_type}_strategy"),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strategy_add_start", f"Started {strategy_type} creation")


@error_handler
async def handle_strategy_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy name input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != ConversationState.STRATEGY_ADD_NAME:
        return
    
    # Validate name
    result = validate_api_name(update.message.text)
    if not result.is_valid:
        await update.message.reply_text(
            format_error_message(result.error_message, "Please try again."),
            parse_mode='HTML'
        )
        return
    
    # Store name and move to next step
    await state_manager.update_data(user.id, {'name': result.value})
    await state_manager.set_state(user.id, ConversationState.STRATEGY_ADD_DESCRIPTION)
    
    # Ask for description
    text = (
        "<b>➕ Add Strategy</b>\n\n"
        f"<b>Name:</b> {escape_html(result.value)}\n\n"
        "Please enter a description (optional):\n\n"
        "Or send <code>/skip</code> to skip."
    )
    
    await update.message.reply_text(text, parse_mode='HTML')


@error_handler
async def strategy_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy delete callback.
    Show preset selection for deletion.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract strategy type from callback data
    strategy_type = query.data.split('_')[-1]
    
    # Get presets
    presets = await get_strategy_presets_by_type(user.id, strategy_type)
    
    if not presets:
        await query.edit_message_text(
            f"<b>🗑️ Delete {strategy_type.capitalize()} Strategy</b>\n\n"
            f"❌ No presets to delete.\n\n"
            f"Create a strategy first.",
            parse_mode='HTML'
        )
        return
    
    # Show preset selection for deletion
    text = (
        f"<b>🗑️ Delete {strategy_type.capitalize()} Strategy</b>\n\n"
        f"Select a preset to delete:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_strategy_edit_keyboard(strategy_type, presets),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "strategy_delete_menu", f"Opened delete menu for {strategy_type}")


@error_handler
async def strategy_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy delete confirmation callback.
    Actually delete the preset.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract preset ID from callback data
    preset_id = query.data.split('_')[-1]
    
    # Get preset for display
    preset = await get_strategy_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            format_error_message("Strategy preset not found."),
            parse_mode='HTML'
        )
        return
    
    # Delete preset
    success = await delete_strategy_preset(preset_id)
    
    if success:
        await query.edit_message_text(
            "<b>✅ Strategy Deleted</b>\n\n"
            f"<b>Name:</b> {escape_html(preset.name)}\n\n"
            "The strategy preset has been deleted.",
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "strategy_delete_success", f"Deleted preset: {preset.name}")
    else:
        await query.edit_message_text(
            format_error_message("Failed to delete strategy preset."),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "strategy_delete_failed", f"Failed to delete: {preset_id}")


@error_handler
async def handle_strategy_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy description input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != ConversationState.STRATEGY_ADD_DESCRIPTION:
        return
    
    description = update.message.text.strip()
    
    # Check for skip command
    if description.lower() == '/skip':
        description = None
    
    # Get current data
    data = await state_manager.get_state_data(user.id)
    strategy_type = data.get('strategy_type')
    strategy_name = data.get('name')
    
    # Store description
    await state_manager.update_data(user.id, {'description': description})
    
    # Ask for asset selection
    text = (
        "<b>➕ Add Strategy</b>\n\n"
        f"<b>Name:</b> {escape_html(strategy_name)}\n"
    )
    
    if description:
        text += f"<b>Description:</b> {escape_html(description)}\n"
    
    text += "\nSelect underlying asset:"
    
    # Show asset selection keyboard
    await update.message.reply_text(
        text,
        reply_markup=get_asset_selection_keyboard(f"strategy_asset_{strategy_type}"),
        parse_mode='HTML'
    )
    
    # Update state to asset selection (handled by callback)
    await state_manager.set_state(user.id, None)  # Clear state, callbacks will handle from here
    
    log_user_action(user.id, "strategy_add_description", f"Set description for {strategy_name}")


def register_strategy_handlers(application: Application):
    """
    Register strategy management handlers.
    
    Args:
        application: Bot application instance
    """
    # Straddle strategy menu callback
    application.add_handler(CallbackQueryHandler(
        straddle_strategy_callback,
        pattern="^menu_straddle_strategy$"
    ))
    
    # Strangle strategy menu callback
    application.add_handler(CallbackQueryHandler(
        strangle_strategy_callback,
        pattern="^menu_strangle_strategy$"
    ))
    
    # Strategy list callback
    application.add_handler(CallbackQueryHandler(
        strategy_list_callback,
        pattern="^strategy_list_"
    ))
    
    # Strategy view callback
    application.add_handler(CallbackQueryHandler(
        strategy_view_callback,
        pattern="^strategy_view_"
    ))
    
    # Strategy add callback
    application.add_handler(CallbackQueryHandler(
        strategy_add_callback,
        pattern="^strategy_add_"
    ))
    
    # Strategy delete callback
    application.add_handler(CallbackQueryHandler(
        strategy_delete_callback,
        pattern="^strategy_delete_(?!confirm)"
    ))
    
    # Strategy delete confirmation callback
    application.add_handler(CallbackQueryHandler(
        strategy_delete_confirm_callback,
        pattern="^strategy_delete_confirm_"
    ))
    
    # Message handler for strategy name input
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_strategy_name_input
    ))
    
    logger.info("Strategy handlers registered")


if __name__ == "__main__":
    print("Strategy handler module loaded")
  
