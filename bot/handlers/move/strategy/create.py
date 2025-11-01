"""
MOVE Strategy Creation Handler
Organized in logical flow order (Step 1 → Step 2 → ... → Save)
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_strategy,
    get_move_strategies
)
from bot.keyboards.move_strategy_keyboards import (
    get_cancel_keyboard,
    get_description_skip_keyboard,
    get_confirmation_keyboard,
    get_move_menu_keyboard,
    get_skip_target_keyboard
)

logger = setup_logger(__name__)

# ========================================
# STEP 0: MENU - Show MOVE Strategy Menu
# ========================================

@error_handler
async def move_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🎯 STEP 0: Show MOVE strategy menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE strategy menu")
    strategies = await get_move_strategies(user.id)
    strategy_count = len(strategies) if strategies else 0
    
    await query.edit_message_text(
        "🎯 <b>MOVE Strategy Management</b>\n\n"
        "Choose an action:",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )


# ========================================
# STEP 1: STRATEGY NAME
# ========================================

@error_handler
async def move_add_new_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📝 STEP 1: Start creation - Ask for strategy name."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    log_user_action(user.id, "Started adding new MOVE strategy")
    
    # Clear any existing state
    await state_manager.clear_state(user.id)
    
    # Set initial state
    await state_manager.set_state(user.id, 'move_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'move'})
    
    await query.edit_message_text(
        "📝 <b>Add MOVE Strategy</b>\n\n"
        "Step 1/7: <b>Strategy Name</b>\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "Example: BTC 8AM MOVE, ETH Daily MOVE",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )


# ========================================
# STEP 2: DESCRIPTION (OPTIONAL)
# ========================================

@error_handler
async def show_description_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📝 STEP 2: Ask for description (optional)."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    await state_manager.set_state(user.id, 'move_add_description')
    
    await update.message.reply_text(
        f"✅ <b>Strategy name saved</b>\n\n"
        f"<code>{data.get('name')}</code>\n\n"
        f"Step 2/7: <b>Description (Optional)</b>\n\n"
        f"Enter a description for your strategy or skip:",
        reply_markup=get_description_skip_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⏭️ STEP 2: Skip description button."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_description':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    # Save empty description
    await state_manager.set_state_data(user.id, {'description': ''})
    data = await state_manager.get_state_data(user.id)
    
    # Move to LOT SIZE (Step 3)
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    logger.info(f"⏭️ User {user.id} skipped description")
    
    await query.edit_message_text(
        f"⏭️ <b>Description skipped</b>\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Name: <code>{data.get('name')}</code>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )


# ========================================
# STEPS 3-6: INPUT HANDLERS
# (These are in input_handlers.py)
# Step 3: Lot Size
# Step 4: ATM Offset
# Step 5: SL Trigger
# Step 6: SL Limit
# ========================================

# Called after user enters SL Limit in input_handlers.py
# This shows the Target Trigger prompt


# ========================================
# STEP 7: TARGET TRIGGER (OPTIONAL)
# ========================================

@error_handler
async def move_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⏭️ STEP 7: Skip target setup (auto-skips Step 8 too)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_target_trigger':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    await query.answer("⏭️ Skipping target setup...")
    
    # ✅ Save empty targets and go DIRECTLY to confirmation
    await state_manager.set_state_data(user.id, {
        'target_trigger_percent': None,
        'target_limit_percent': None
    })
    
    logger.info(f"⏭️ User {user.id} skipped target - going to confirmation")
    
    # Go to confirmation (skip Step 8)
    await show_move_confirmation(update, context)


# ========================================
# CONFIRMATION & SAVE
# ========================================

@error_handler
async def show_move_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Show final confirmation before saving."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name') or "Unnamed"
    description = data.get('description', '')
    lot_size = data.get('lot_size')
    atm_offset = data.get('atm_offset')
    sl_trigger = data.get('sl_trigger_percent')
    sl_limit = data.get('sl_limit_percent')
    target_trigger = data.get('target_trigger_percent')
    target_limit = data.get('target_limit_percent')
    
    # Build confirmation text
    text = f"✅ <b>MOVE Strategy - Final Confirmation</b>\n\n"
    text += f"📋 <b>Details:</b>\n"
    text += f"• Name: <code>{name}</code>\n"
    
    if description:
        text += f"• Description: {description}\n"
    
    text += (
        f"• Lot Size: {lot_size}\n"
        f"• ATM Offset: {atm_offset:+d}\n\n"
        f"📊 <b>Risk Management:</b>\n"
        f"• SL Trigger: {sl_trigger}%\n"
        f"• SL Limit: {sl_limit}%\n"
    )
    
    if target_trigger is not None and target_trigger > 0:
        text += (
            f"• Target Trigger: {target_trigger}%\n"
            f"• Target Limit: {target_limit}%\n"
        )
    else:
        text += f"• Target: <i>Not set</i>\n"
    
    text += "\n✅ <b>Save this strategy?</b>"
    
    keyboard = get_confirmation_keyboard()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='HTML'
        )


@error_handler
async def move_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💾 Save the MOVE strategy to database."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    try:
        strategy_data = {
            'strategy_name': data.get('name'),
            'description': data.get('description', ''),
            'lot_size': data.get('lot_size'),
            'atm_offset': data.get('atm_offset', 0),
            'stop_loss_trigger': data.get('sl_trigger_percent'),
            'stop_loss_limit': data.get('sl_limit_percent'),
            'target_trigger': data.get('target_trigger_percent'),
            'target_limit': data.get('target_limit_percent')
        }
        
        result = await create_move_strategy(user.id, strategy_data)
        
        if not result:
            raise Exception("Failed to save strategy")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created MOVE strategy: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ <b>MOVE Strategy Created!</b>\n\n"
            f"📌 Name: <code>{data.get('name')}</code>\n"
            f"📊 Lot Size: {data.get('lot_size')}\n\n"
            f"✅ Strategy saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating MOVE strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ <b>Error saving strategy</b>\n\n"
            f"Error: {str(e)}\n\nPlease try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


# ========================================
# CANCEL OPERATION
# ========================================

@error_handler
async def move_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """❌ Cancel the strategy creation."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.clear_state(user.id)
    log_user_action(user.id, "Cancelled MOVE strategy operation")
    
    await query.edit_message_text(
        "❌ <b>Operation Cancelled</b>",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )


# ========================================
# EXPORTS (All handlers in order)
# ========================================

__all__ = [
    # Step 0: Menu
    'move_add_callback',
    
    # Step 1: Strategy Name
    'move_add_new_strategy_callback',
    
    # Step 2: Description (Optional)
    'show_description_prompt',
    'move_skip_description_callback',
    
    # Steps 3-6: In input_handlers.py
    # - handle_move_lot_size
    # - handle_move_atm_offset
    # - handle_move_sl_trigger
    # - handle_move_sl_limit
    
    # Step 7: Target Trigger (Optional)
    'move_skip_target_callback',
    
    # Confirmation & Save
    'show_move_confirmation',
    'move_confirm_save_callback',
    
    # Cancel
    'move_cancel_callback',
]
