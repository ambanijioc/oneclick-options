"""
STRANGLE Strategy Edit Handler

Handles editing existing STRANGLE strategies with OTM configuration.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_strategy_ops import (
    get_strangle_strategies,
    get_strangle_strategy,
    update_strangle_strategy
)
from bot.keyboards.strangle_strategy_keyboards import (
    get_strategy_list_keyboard,
    get_edit_fields_keyboard,
    get_strangle_menu_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_cancel_keyboard,
    get_continue_edit_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of STRANGLE strategies to edit."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Requested STRANGLE strategy list for editing")
    
    strategies = await get_strangle_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No STRANGLE strategies found.\n\n"
            "Create your first strategy!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state(user.id, 'strangle_edit_select')
    
    await query.edit_message_text(
        "📝 Edit STRANGLE Strategy\n\n"
        "Select a strategy to edit:",
        reply_markup=get_strategy_list_keyboard(strategies, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def strangle_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle strategy selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_strangle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    await state_manager.set_state(user.id, 'strangle_edit_field')
    
    # Display OTM info
    otm_type = strategy.get('otm_type', 'percentage')
    if otm_type == 'percentage':
        call_otm_display = f"{strategy.get('call_otm_pct', 0)}%"
        put_otm_display = f"{strategy.get('put_otm_pct', 0)}%"
    else:
        call_otm_display = f"{strategy.get('call_otm_num', 0)} strikes"
        put_otm_display = f"{strategy.get('put_otm_num', 0)} strikes"
    
    await query.edit_message_text(
        f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
        f"Current Settings:\n"
        f"• Asset: {strategy.get('asset')}\n"
        f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
        f"• Lot Size: {strategy.get('lot_size', 1)}\n"
        f"• Call OTM: {call_otm_display}\n"
        f"• Put OTM: {put_otm_display}\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_fields_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    field = query.data.split('_')[-1]
    
    await state_manager.set_state_data(user.id, {'editing_field': field})
    data = await state_manager.get_state_data(user.id)
    strategy = data.get('strategy_data', {})
    
    if field == 'name':
        await state_manager.set_state(user.id, 'strangle_edit_name')
        await query.edit_message_text(
            f"📝 Edit Strategy Name\n\n"
            f"Current: {strategy.get('strategy_name')}\n\n"
            f"Enter new name:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'asset':
        await state_manager.set_state(user.id, 'strangle_edit_asset')
        await query.edit_message_text(
            f"📝 Edit Asset\n\n"
            f"Current: {strategy.get('asset')}\n\n"
            f"Select new asset:",
            reply_markup=get_asset_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'expiry':
        await state_manager.set_state(user.id, 'strangle_edit_expiry')
        await query.edit_message_text(
            f"📝 Edit Expiry\n\n"
            f"Current: {strategy.get('expiry', 'daily').capitalize()}\n\n"
            f"Select new expiry:",
            reply_markup=get_expiry_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'lot_size':
        await state_manager.set_state(user.id, 'strangle_edit_lot_size')
        await query.edit_message_text(
            f"📝 Edit Lot Size\n\n"
            f"Current: {strategy.get('lot_size', 1)}\n\n"
            f"Enter new lot size (1-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def strangle_update_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update strategy field (for callbacks like asset, expiry)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('editing_strategy_id')
    editing_field = data.get('editing_field')
    
    new_value = query.data.split('_')[-1]
    
    field_mapping = {
        'asset': 'asset',
        'expiry': 'expiry'
    }
    
    db_field = field_mapping.get(editing_field)
    
    if not db_field:
        await query.edit_message_text(
            "❌ Invalid field selected.",
            reply_markup=get_strangle_menu_keyboard()
        )
        return
    
    update_data = {db_field: new_value}
    result = await update_strangle_strategy(user.id, strategy_id, update_data)
    
    if result:
        log_user_action(user.id, f"Updated STRANGLE strategy {strategy_id} - {db_field}: {new_value}")
        
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
            reply_markup=get_strangle_menu_keyboard()
        )

@error_handler
async def strangle_continue_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continue editing the same strategy."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    strategy_id = query.data.split('_')[-1]
    
    strategy = await get_strangle_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_strangle_menu_keyboard()
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    await state_manager.set_state(user.id, 'strangle_edit_field')
    
    otm_type = strategy.get('otm_type', 'percentage')
    if otm_type == 'percentage':
        call_otm_display = f"{strategy.get('call_otm_pct', 0)}%"
        put_otm_display = f"{strategy.get('put_otm_pct', 0)}%"
    else:
        call_otm_display = f"{strategy.get('call_otm_num', 0)} strikes"
        put_otm_display = f"{strategy.get('put_otm_num', 0)} strikes"
    
    await query.edit_message_text(
        f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
        f"Current Settings:\n"
        f"• Asset: {strategy.get('asset')}\n"
        f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
        f"• Lot Size: {strategy.get('lot_size', 1)}\n"
        f"• Call OTM: {call_otm_display}\n"
        f"• Put OTM: {put_otm_display}\n\n"
        f"What would you like to edit?",
        reply_markup=get_edit_fields_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'strangle_edit_callback',
    'strangle_edit_select_callback',
    'strangle_edit_field_callback',
    'strangle_update_field_callback',
    'strangle_continue_edit_callback',
]
