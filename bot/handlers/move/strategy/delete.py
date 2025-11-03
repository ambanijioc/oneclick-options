"""
MOVE Strategy Delete Handler

Handles safe deletion of MOVE strategies with confirmation.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    get_move_strategies,
    get_move_strategy,
    delete_move_strategy
)
from bot.keyboards.move_strategy_keyboards import (
    get_delete_list_keyboard,  # ✅ UPDATED
    get_delete_confirmation_keyboard,
    get_move_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of MOVE strategies to delete."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "move_delete_list", "Requested MOVE strategy list for deletion")
    
    strategies = await get_move_strategies(user.id)
    
    if not strategies:
        await query.edit_message_text(
            "📋 <b>No MOVE Strategies Found</b>\n\n"
            "Nothing to delete!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "🗑️ <b>Delete MOVE Strategy</b>\n\n"
        "⚠️ <b>Warning:</b> This action cannot be undone!\n\n"
        "Select a strategy to delete:",
        reply_markup=get_delete_list_keyboard(strategies),  # ✅ UPDATED
        parse_mode='HTML'
    )

@error_handler
async def move_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show confirmation before deleting strategy.
    Callback format: move_delete_{strategy_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract strategy_id from "move_delete_{ID}"
    parts = query.data.split('_')  # ['move', 'delete', 'ID']
    strategy_id = parts[2] if len(parts) >= 3 else None
    
    logger.info(f"DELETE CONFIRM - Raw callback_data: {query.data}")
    logger.info(f"DELETE CONFIRM - Extracted strategy_id: {strategy_id}")
    
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
    
    name = strategy.get('strategy_name', 'Unnamed')
    asset = strategy.get('asset', 'N/A')
    direction = strategy.get('direction', 'unknown').upper()
    expiry = strategy.get('expiry', 'daily').capitalize()
    
    await query.edit_message_text(
        f"🗑️ <b>Delete Strategy Confirmation</b>\n\n"
        f"Are you sure you want to delete:\n\n"
        f"📌 <b>Name:</b> {name}\n"
        f"📊 <b>Asset:</b> {asset}\n"
        f"📅 <b>Expiry:</b> {expiry}\n"
        f"🎯 <b>Direction:</b> {direction}\n\n"
        f"⚠️ <b>This action cannot be undone!</b>",
        reply_markup=get_delete_confirmation_keyboard(strategy_id),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, f"delete_confirm_{strategy_id}", f"Confirming deletion of: {name}")

@error_handler
async def move_delete_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Execute strategy deletion.
    Callback format: move_delete_confirmed_{strategy_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract strategy_id from "move_delete_confirmed_{ID}"
    parts = query.data.split('_')  # ['move', 'delete', 'confirmed', 'ID']
    strategy_id = parts[3] if len(parts) >= 4 else None
    
    logger.info(f"DELETE EXECUTE - Raw callback_data: {query.data}")
    logger.info(f"DELETE EXECUTE - Extracted strategy_id: {strategy_id}")
    
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
            "❌ Strategy not found or already deleted.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    name = strategy.get('strategy_name', 'Unnamed')
    
    result = await delete_move_strategy(user.id, strategy_id)
    
    if result:
        log_user_action(user.id, f"delete_execute_{strategy_id}", f"Deleted MOVE strategy: {name}")
        logger.info(f"✅ DELETE EXECUTE - Successfully deleted strategy: {name} (ID: {strategy_id})")
        
        await query.edit_message_text(
            f"✅ <b>Strategy Deleted!</b>\n\n"
            f"'{name}' has been successfully deleted.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        logger.error(f"❌ DELETE EXECUTE - Failed to delete strategy ID: {strategy_id}")
        await query.edit_message_text(
            "❌ <b>Failed to Delete Strategy</b>\n\n"
            "Please try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )

__all__ = [
    'move_delete_callback',
    'move_delete_confirm_callback',
    'move_delete_execute_callback',
]
