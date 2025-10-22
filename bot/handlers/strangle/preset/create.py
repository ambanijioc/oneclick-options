"""
STRANGLE Preset Creation Handler

Handles creating trade presets for STRANGLE strategies.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_trade_preset_ops import create_strangle_preset
from bot.keyboards.strangle_strategy_keyboards import (
    get_cancel_keyboard,
    get_confirmation_keyboard,
    get_strangle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_preset_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start STRANGLE preset creation flow."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started adding STRANGLE preset")
    
    await state_manager.clear_state(user.id)
    await state_manager.set_state(user.id, 'strangle_preset_add_name')
    await state_manager.set_state_data(user.id, {'preset_type': 'strangle'})
    
    await query.edit_message_text(
        "📝 Add STRANGLE Preset\n\n"
        "Step 1/3: Preset Name\n\n"
        "Enter a name for your trading preset:\n\n"
        "Example: Quick Entry, Conservative Exit",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_preset_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save STRANGLE preset to database."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    data = await state_manager.get_state_data(user.id)
    
    try:
        preset_data = {
            'preset_name': data.get('name'),
            'description': data.get('description', ''),
            'entry_lots': data.get('entry_lots', 1),
            'exit_lots': data.get('exit_lots', 1)
        }
        
        result = await create_strangle_preset(user.id, preset_data)
        
        if not result:
            raise Exception("Failed to save preset to database")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created STRANGLE preset: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ STRANGLE Preset Created!\n\n"
            f"Name: {data.get('name')}\n"
            f"Entry Lots: {data.get('entry_lots', 1)}\n"
            f"Exit Lots: {data.get('exit_lots', 1)}\n\n"
            f"Preset has been saved successfully!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating STRANGLE preset: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error creating preset: {str(e)}\n\n"
            f"Please try again.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )

__all__ = [
    'strangle_preset_create_callback',
    'strangle_preset_confirm_save_callback',
      ]
