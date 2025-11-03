"""
MOVE Strategy Edit Handler

Handles editing existing MOVE strategies.
"""

from telegram import Update, BadRequest
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application

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
    get_cancel_keyboard,
    get_continue_edit_keyboard,
    get_edit_asset_keyboard,
    get_edit_expiry_keyboard,
    get_edit_direction_keyboard
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
    
    log_user_action(user.id, "move_edit", "Requested MOVE strategy list for editing")
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 No MOVE strategies found.\n\n"
            "Create your first strategy!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "📝 Edit MOVE Strategy\n\n"
        "Select a strategy to edit:",
        reply_markup=get_strategy_list_keyboard(strategies, action='edit'),
        parse_mode='HTML'
    )

@error_handler
async def move_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy selection for editing.
    First call shows list, second call with move_edit_{ID} shows details.
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # CASE 1: Initial move_edit call (show list)
    if query.data == "move_edit":
        return await move_edit_callback(update, context)
    
    # CASE 2: move_edit_{strategy_id} call (select specific strategy)
    parts = query.data.split('_')
    strategy_id = parts[2] if len(parts) >= 3 else None
    
    if not strategy_id:
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_strategy_id': strategy_id,
        'strategy_data': strategy
    })
    
    keyboard = get_edit_fields_keyboard(strategy_id)
    
    try:
        await query.edit_message_text(
            f"📝 Edit Strategy: {strategy.get('strategy_name')}\n\n"
            f"Current Settings:\n"
            f"• Asset: {strategy.get('asset')}\n"
            f"• Expiry: {strategy.get('expiry', 'daily').capitalize()}\n"
            f"• Direction: {strategy.get('direction', 'N/A').capitalize()}\n"
            f"• ATM Offset: {strategy.get('atm_offset', 0)}\n\n"
            f"What would you like to edit?",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.warning("Message not modified")
        else:
            raise

@error_handler
async def move_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle field selection for editing.
    Callback format: move_edit_field_{strategy_id}_{field_name}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract: move_edit_field_{ID}_{field} -> ['move', 'edit', 'field', 'ID', 'field_name']
    parts = query.data.split('_', 4)  # Limit splits to preserve field names
    strategy_id = parts[3] if len(parts) >= 4 else None
    field = parts[4] if len(parts) >= 5 else None
    
    logger.info(f"EDIT FIELD - callback_data: {query.data}")
    logger.info(f"EDIT FIELD - strategy_id: {strategy_id}, field: {field}")
    
    if not strategy_id or not field:
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    await state_manager.set_state_data(user.id, {
        'editing_field': field,
        'editing_strategy_id': strategy_id
    })
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
    
    elif field == 'description':
        await state_manager.set_state(user.id, 'move_edit_description')
        await query.edit_message_text(
            f"📝 Edit Description\n\n"
            f"Current: {strategy.get('description', 'None')}\n\n"
            f"Enter new description:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    elif field == 'asset':
        await query.edit_message_text(
            f"📝 Edit Asset\n\n"
            f"Current: {strategy.get('asset')}\n\n"
            f"Select new asset:",
            reply_markup=get_edit_asset_keyboard(strategy_id),
            parse_mode='HTML'
        )
    
    elif field == 'expiry':
        await query.edit_message_text(
            f"📝 Edit Expiry\n\n"
            f"Current: {strategy.get('expiry', 'daily').capitalize()}\n\n"
            f"Select new expiry:",
            reply_markup=get_edit_expiry_keyboard(strategy_id),
            parse_mode='HTML'
        )
    
    elif field == 'direction':
        await query.edit_message_text(
            f"📝 Edit Direction\n\n"
            f"Current: {strategy.get('direction', 'N/A').capitalize()}\n\n"
            f"Select new direction:",
            reply_markup=get_edit_direction_keyboard(strategy_id),
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
    
    elif field in ['sl_trigger', 'sl_limit', 'target_trigger', 'target_limit']:
        await state_manager.set_state(user.id, f'move_edit_{field}')
        field_display = field.replace('_', ' ').title()
        await query.edit_message_text(
            f"📝 Edit {field_display}\n\n"
            f"Current: {strategy.get(field, 'Not set')}\n\n"
            f"Enter new value (percentage):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_edit_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Save callback-based edits (asset, expiry, direction).
    Format: move_edit_save_{field}_{strategy_id}_{value}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract: move_edit_save_asset_ID_BTC -> ['move', 'edit', 'save', 'asset', 'ID', 'BTC']
    parts = query.data.split('_')
    field = parts[3] if len(parts) >= 4 else None
    strategy_id = parts[4] if len(parts) >= 5 else None
    new_value = parts[5] if len(parts) >= 6 else None
    
    logger.info(f"EDIT SAVE - callback_data: {query.data}")
    logger.info(f"EDIT SAVE - field: {field}, strategy_id: {strategy_id}, value: {new_value}")
    
    if not all([field, strategy_id, new_value]):
        await query.edit_message_text(
            "❌ Invalid request.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    # Map field to database column
    field_mapping = {
        'asset': 'asset',
        'expiry': 'expiry',
        'direction': 'direction'
    }
    
    db_field = field_mapping.get(field)
    
    if not db_field:
        await query.edit_message_text(
            "❌ Invalid field.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    # Update strategy
    update_data = {db_field: new_value}
    result = await update_move_strategy(user.id, strategy_id, update_data)
    
    if result:
        log_user_action(user.id, f"move_edit_save_{field}", f"Updated {field}: {new_value}")
        
        await query.edit_message_text(
            f"✅ Strategy Updated!\n\n"
            f"{field.capitalize()} changed to: {new_value.capitalize()}\n\n"
            f"Continue editing or return to menu?",
            reply_markup=get_continue_edit_keyboard(strategy_id),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "❌ Failed to update strategy.",
            reply_markup=get_move_menu_keyboard()
        )


# ✅ TEXT INPUT HANDLER FOR EDITS
@error_handler
async def move_edit_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ NEW: Handle text input for name, description, atm_offset edits
    """
    user = update.message.from_user
    text = update.message.text
    
    data = await state_manager.get_state_data(user.id)
    state = await state_manager.get_state(user.id)
    strategy_id = data.get('editing_strategy_id')
    field = data.get('editing_field')
    
    if not strategy_id or not field:
        await update.message.reply_text("❌ Edit session expired. Please try again.")
        return
    
    # Map state to field and validate
    if state == 'move_edit_name':
        if len(text) < 3 or len(text) > 100:
            await update.message.reply_text("❌ Name must be 3-100 characters. Try again:")
            return
        update_field = 'strategy_name'
        new_value = text.strip()
        
    elif state == 'move_edit_description':
        if len(text) < 5 or len(text) > 500:
            await update.message.reply_text("❌ Description must be 5-500 characters. Try again:")
            return
        update_field = 'description'
        new_value = text.strip()
        
    elif state == 'move_edit_atm_offset':
        try:
            offset = int(text)
            if not -10 <= offset <= 10:
                await update.message.reply_text("❌ ATM Offset must be between -10 and +10. Try again:")
                return
            update_field = 'atm_offset'
            new_value = offset
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number. Try again:")
            return
    else:
        await update.message.reply_text("❌ Invalid edit state.")
        return
    
    # Update strategy in database
    result = await update_move_strategy(user.id, strategy_id, {update_field: new_value})
    
    if result:
        log_user_action(user.id, f"move_edit_text_{field}", f"Updated {field}: {new_value}")
        
        # Clear state
        await state_manager.set_state(user.id, None)
        await state_manager.set_state_data(user.id, {})
        
        await update.message.reply_text(
            f"✅ Strategy Updated!\n\n"
            f"{field.capitalize()} changed to: <code>{new_value}</code>\n\n"
            f"What else would you like to edit?",
            reply_markup=get_edit_fields_keyboard(strategy_id),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Failed to update strategy. Try again:")


# ✅ REGISTRATION FUNCTION
def register_move_edit_handlers(app: Application):
    """Register MOVE strategy edit handlers"""
    # This handles BOTH "move_edit" (show list) AND "move_edit_{ID}" (select strategy)
    app.add_handler(CallbackQueryHandler(move_edit_select_callback, pattern="^move_edit"))
    
    app.add_handler(CallbackQueryHandler(move_edit_field_callback, pattern="^move_edit_field_"))
    app.add_handler(CallbackQueryHandler(move_edit_save_callback, pattern="^move_edit_save_"))
    
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        move_edit_text_input
    ))
    
    logger.info("✓ MOVE edit handlers registered")

__all__ = [
    'move_edit_callback',
    'move_edit_select_callback',
    'move_edit_field_callback',
    'move_edit_save_callback',
    'move_edit_text_input',
    'register_move_edit_handlers',
            ]
