"""
STRANGLE Preset View Handler

Displays list of all STRANGLE trade presets and their details.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_trade_preset_ops import (
    get_strangle_trade_presets,
    get_strangle_trade_preset_by_id
)
from bot.keyboards.strangle_strategy_keyboards import (
    get_preset_list_keyboard,
    get_strangle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_preset_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of all STRANGLE presets."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRANGLE presets list")
    
    presets = await get_strangle_trade_presets(user.id)
    
    if not presets:
        await query.edit_message_text(
            "📋 No STRANGLE presets found.\n\n"
            "Create your first preset!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "📋 Your STRANGLE Presets\n\n"
        f"Total: {len(presets)} presets\n\n"
        "Select a preset to view details:",
        reply_markup=get_preset_list_keyboard(presets, action='view'),
        parse_mode='HTML'
    )

@error_handler
async def strangle_preset_view_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed view of selected preset."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    preset_id = query.data.split('_')[-1]
    
    preset = await get_strangle_trade_preset_by_id(preset_id)
    
    if not preset:
        await query.edit_message_text(
            "❌ Preset not found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = preset.get('preset_name', 'Unnamed')
    description = preset.get('description', 'No description')
    entry_lots = preset.get('entry_lots', 1)
    exit_lots = preset.get('exit_lots', 1)
    
    # Get associated strategy if exists
    strategy_name = "N/A"
    if preset.get('strategy_id'):
        from database.operations.strangle_strategy_ops import get_strangle_strategy
        strategy = await get_strangle_strategy(user.id, preset.get('strategy_id'))
        if strategy:
            strategy_name = strategy.get('strategy_name', 'N/A')
    
    # Get associated API if exists
    api_name = "N/A"
    if preset.get('api_id'):
        from database.operations.api_ops import get_api_credential_by_id
        api = await get_api_credential_by_id(preset.get('api_id'))
        if api:
            api_name = api.api_name
    
    text = (
        f"📋 STRANGLE Preset Details\n\n"
        f"📌 Name: {name}\n"
        f"📝 Description: {description}\n\n"
        f"⚙️ Configuration:\n"
        f"• Entry Lots: {entry_lots}\n"
        f"• Exit Lots: {exit_lots}\n\n"
        f"🔗 Associations:\n"
        f"• Strategy: {strategy_name}\n"
        f"• API: {api_name}\n"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_strangle_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'strangle_preset_view_callback',
    'strangle_preset_view_details_callback',
      ]
