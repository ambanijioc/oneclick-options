"""
MOVE Strategy Edit Handler

Handles editing existing MOVE strategies:
- Select strategy from list
- Choose field to edit
- Update strategy data
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    get_move_strategies,
    get_move_strategy,
    update_move_strategy
)
from bot.keyboards.move_strategy_keyboards import (
    get_strategy_list_keyboard,
    get_edit_fields_keyboard,
    get_move_menu_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_direction_keyboard,
    get_cancel_keyboard,
    get_continue_edit_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of MOVE strategies to edit."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested MOVE strategy list for editing")
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No MOVE strategies found.\n\n"
            "Create your first strategy!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state(user.id, 'move_edit_select')
    
    await query.edit_message_text(
        "📝 Edit MOVE Strategy\n\n"
        "Select a strategy to edit:",
        reply_markup=get_strategy_list_keyboard(strategies, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def move_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract strategy ID: move_edit_select_{strategy_id}
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Store strategy ID in state
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    await state_manager.set_state(user.id, 'move_edit_field')
    
    await query.edit_message_text(
        f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
        f"Current Settings:\n"
        f"• Asset: {strategy.get('asset')}\n"
        f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
        f"• Direction: {strategy.get('direction', 'N/A').capitalize()}\n"
        f"• ATM Offset: {strategy.get('atm_offset', 0)}\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_fields_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract field: move_edit_field_name, move_edit_field_asset, etc.
    field = query.data.split('_')[-1]
    
    await state_manager.set_state_data(user.id, {'editing_field': field})
    data = await state_manager.get_state_data(user.id)
    strategy = data.get('strategy_data', {})
    
    if field == 'name':
        await state_manager.set_state(user.id, 'move_edit_name')
        await query.edit_message_text(
            f"📝 Edit Strategy Name\n\n"
            f"Current: {strategy.get('strategy_name')}\n\n"
            f"Enter new name:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'asset':
        await state_manager.set_state(user.id, 'move_edit_asset')
        await query.edit_message_text(
            f"📝 Edit Asset\n\n"
            f"Current: {strategy.get('asset')}\n\n"
            f"Select new asset:",
            reply_markup=get_asset_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'expiry':
        await state_manager.set_state(user.id, 'move_edit_expiry')
        await query.edit_message_text(
            f"📝 Edit Expiry\n\n"
            f"Current: {strategy.get('expiry', 'daily').capitalize()}\n\n"
            f"Select new expiry:",
            reply_markup=get_expiry_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'direction':
        await state_manager.set_state(user.id, 'move_edit_direction')
        await query.edit_message_text(
            f"📝 Edit Direction\n\n"
            f"Current: {strategy.get('direction', 'N/A').capitalize()}\n\n"
            f"Select new direction:",
            reply_markup=get_direction_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'atm_offset':
        await state_manager.set_state(user.id, 'move_edit_atm_offset')
        await query.edit_message_text(
            f"📝 Edit ATM Offset\n\n"
            f"Current: {strategy.get('atm_offset', 0)}\n\n"
            f"Enter new ATM offset (-10 to +10):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_update_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update strategy field (for callbacks like asset, expiry, direction)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('editing_strategy_id')
    editing_field = data.get('editing_field')
    
    # Extract the new value based on callback pattern
    # move_asset_BTC, move_expiry_daily, move_direction_long
    new_value = query.data.split('_')[-1]
    
    # Map callback to database field
    field_mapping = {
        'asset': 'asset',
        'expiry': 'expiry',
        'direction': 'direction'
    }
    
    db_field = field_mapping.get(editing_field)
    
    if not db_field:
        await query.edit_message_text(
            "❌ Invalid field selected.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    # Update strategy
    update_data = {db_field: new_value}
    result = await update_move_strategy(user.id, strategy_id, update_data)
    
    if result:
        log_user_action(user.id, f"Updated MOVE strategy {strategy_id} - {db_field}: {new_value}")
        
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
            reply_markup=get_move_menu_keyboard()
        )

@error_handler
async def move_continue_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continue editing the same strategy."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract strategy_id from callback: move_continue_edit_{strategy_id}
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    await state_manager.set_state(user.id, 'move_edit_field')
    
    await query.edit_message_text(
        f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
        f"Current Settings:\n"
        f"• Asset: {strategy.get('asset')}\n"
        f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
        f"• Direction: {strategy.get('direction', 'N/A').capitalize()}\n"
        f"• ATM Offset: {strategy.get('atm_offset', 0)}\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_fields_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'move_edit_callback',
    'move_edit_select_callback',
    'move_edit_field_callback',
    'move_update_field_callback',
    'move_continue_edit_callback',
  ]
  
