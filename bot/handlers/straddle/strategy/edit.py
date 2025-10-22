"""
STRADDLE Strategy Edit Handler

Handles editing existing STRADDLE strategies.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.straddle_strategy_ops import (
    get_straddle_strategies,
    get_straddle_strategy,
    update_straddle_strategy
)
from bot.keyboards.straddle_strategy_keyboards import (
    get_strategy_list_keyboard,
    get_edit_fields_keyboard,
    get_straddle_menu_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_direction_keyboard,
    get_cancel_keyboard,
    get_continue_edit_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def straddle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRADDLE strategies to edit."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRADDLE strategy list for editing")
    
    strategies = await get_straddle_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No STRADDLE strategies found.\n\n"
            "Create your first strategy!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state(user.id, 'straddle_edit_select')
    
    await query.edit_message_text(
        "📝 Edit STRADDLE Strategy\n\n"
        "Select a strategy to edit:",
        reply_markup=get_strategy_list_keyboard(strategies, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def straddle_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_straddle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    await state_manager.set_state(user.id, 'straddle_edit_field')
    
    await query.edit_message_text(
        f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
        f"Current Settings:\n"
        f"• Asset: {strategy.get('asset')}\n"
        f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
        f"• Direction: {strategy.get('direction', 'long').capitalize()}\n"
        f"• Lot Size: {strategy.get('lot_size', 1)}\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_fields_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def straddle_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    field = query.data.split('_')[-1]
    
    await state_manager.set_state_data(user.id, {'editing_field': field})
    data = await state_manager.get_state_data(user.id)
    strategy = data.get('strategy_data', {})
    
    if field == 'name':
        await state_manager.set_state(user.id, 'straddle_edit_name')
        await query.edit_message_text(
            f"📝 Edit Strategy Name\n\n"
            f"Current: {strategy.get('strategy_name')}\n\n"
            f"Enter new name:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'asset':
        await state_manager.set_state(user.id, 'straddle_edit_asset')
        await query.edit_message_text(
            f"📝 Edit Asset\n\n"
            f"Current: {strategy.get('asset')}\n\n"
            f"Select new asset:",
            reply_markup=get_asset_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'expiry':
        await state_manager.set_state(user.id, 'straddle_edit_expiry')
        await query.edit_message_text(
            f"📝 Edit Expiry\n\n"
            f"Current: {strategy.get('expiry', 'daily').capitalize()}\n\n"
            f"Select new expiry:",
            reply_markup=get_expiry_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'direction':
        await state_manager.set_state(user.id, 'straddle_edit_direction')
        await query.edit_message_text(
            f"📝 Edit Direction\n\n"
            f"Current: {strategy.get('direction', 'long').capitalize()}\n\n"
            f"Select new direction:",
            reply_markup=get_direction_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'lot_size':
        await state_manager.set_state(user.id, 'straddle_edit_lot_size')
        await query.edit_message_text(
            f"📝 Edit Lot Size\n\n"
            f"Current: {strategy.get('lot_size', 1)}\n\n"
            f"Enter new lot size (1-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def straddle_update_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update strategy field (for callbacks like asset, expiry, direction)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('editing_strategy_id')
    editing_field = data.get('editing_field')
    
    new_value = query.data.split('_')[-1]
    
    field_mapping = {
        'asset': 'asset',
        'expiry': 'expiry',
        'direction': 'direction'
    }
    
    db_field = field_mapping.get(editing_field)
    
    if not db_field:
        await query.edit_message_text(
            "❌ Invalid field selected.",
            reply_markup=get_straddle_menu_keyboard()
        )
        return
    
    update_data = {db_field: new_value}
    result = await update_straddle_strategy(user.id, strategy_id, update_data)
    
    if result:
        log_user_action(user.id, f"Updated STRADDLE strategy {strategy_id} - {db_field}: {new_value}")
        
        await query.edit_message_text(
            f"✅ Strategy Updated!\n\n"
            f"{editing_field.capitalize()} changed to: {new_value.capitalize()}\n\n"
            f"Continue editing or return to menu?",
            reply_markup=get_continue_edit_keyboard(strategy_id),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "❌ Failed to update strategy.",
            reply_markup=get_straddle_menu_keyboard()
        )

@error_handler
async def straddle_continue_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continue editing the same strategy."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_straddle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_straddle_menu_keyboard()
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    await state_manager.set_state(user.id, 'straddle_edit_field')
    
    await query.edit_message_text(
        f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
        f"Current Settings:\n"
        f"• Asset: {strategy.get('asset')}\n"
        f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
        f"• Direction: {strategy.get('direction', 'long').capitalize()}\n"
        f"• Lot Size: {strategy.get('lot_size', 1)}\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_fields_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'straddle_edit_callback',
    'straddle_edit_select_callback',
    'straddle_edit_field_callback',
    'straddle_update_field_callback',
    'straddle_continue_edit_callback',
]
