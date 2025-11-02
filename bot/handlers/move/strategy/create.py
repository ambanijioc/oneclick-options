"""
MOVE Strategy Creation - COMPLETE 7-STEP FLOW WITH INLINE KEYBOARDS
Fixed version with proper registrations
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import create_move_strategy
from bot.keyboards.move_strategy_keyboards import (
    get_cancel_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_direction_keyboard,
    get_confirmation_keyboard,
    get_skip_target_keyboard,
    get_move_menu_keyboard,
    get_description_skip_keyboard
)

logger = setup_logger(__name__)

# ==================== STEP 0: MENU ====================

@error_handler
async def move_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show MOVE strategy menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE strategy menu")
    
    await query.edit_message_text(
        "🎯 MOVE Strategy Management\n\n"
        "Choose an action:",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 1: STRATEGY NAME ====================

@error_handler
async def move_add_new_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1/7: Strategy Name - START"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    await state_manager.set_state(user.id, 'move_add_name')
    
    await query.edit_message_text(
        "📝 <b>Add MOVE Strategy</b>\n\n"
        "Step 1/7: Strategy Name\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "<i>Example: BTC 8AM MOVE, ETH Daily MOVE</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_add_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1 -> Step 2: Save name, show description prompt"""
    user = update.effective_user
    text = update.message.text
    
    # Validate
    if not text or len(text) < 2:
        await update.message.reply_text(
            "❌ Name too short (min 2 characters)\n\nPlease enter a valid name:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'name': text})
    logger.info(f"✅ MOVE name: {text}")
    
    await state_manager.set_state(user.id, 'move_add_description')
    await update.message.reply_text("Step 2/7: Description (Optional)...")
    return  # ✅ CRITICAL: Return to stop execution
    
    await update.message.reply_text(
        f"✅ <b>Name saved</b>\n\n"
        f"<code>{text}</code>\n\n"
        f"<b>Step 2/7: Description (Optional)</b>\n\n"
        f"Enter a description or skip:",
        reply_markup=get_description_skip_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 2: DESCRIPTION ====================

@error_handler
async def handle_move_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2 -> Step 3: Save description (optional), show lot size"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Get saved name
    data = await state_manager.get_state_data(user.id)
    saved_name = data.get('name', '')
    
    # Check if this is a "skip" button or actual text
    if text.upper() in ['SKIP', 'SKIP DESCRIPTION']:
        logger.info(f"⏭️ MOVE description: SKIPPED")
        # Move to next step without saving description
        await state_manager.set_state(user.id, 'move_add_lot_size')
        await update.message.reply_text(
            f"Step 3/7: <b>Lot Size</b>\n"
            f"Name: <code>{saved_name}</code>\n\n"
            f"Enter lot size (1-1000):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # ✅ FIX: Check if description matches name
    if text.lower() == saved_name.lower():
        await update.message.reply_text(
            f"❌ Description cannot be the same as the strategy name!\n\n"
            f"Please enter a different description or skip:",
            reply_markup=get_description_skip_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Validate length
    if len(text) < 2:
        await update.message.reply_text(
            "❌ Description must be at least 2 characters.\n\n"
            "Please enter a valid description or skip:",
            reply_markup=get_description_skip_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save description
    await state_manager.set_state_data(user.id, {'description': text})
    logger.info(f"✅ MOVE description: {text[:50]}")
    
    # Move to next step
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    await update.message.reply_text(
        f"✅ <b>Description saved</b>\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Name: <code>{saved_name}</code>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description button -> Step 3"""
    query = update.callback_query
    await query.answer("⏭️ Skipping...")
    user = query.from_user
    
    await state_manager.set_state_data(user.id, {'description': ''})
    await state_manager.set_state(user.id, 'move_add_lot_size')
    data = await state_manager.get_state_data(user.id)
    
    logger.info(f"⏭️ Description skipped for user {user.id}")
    
    await query.edit_message_text(
        f"⏭️ <b>Description skipped</b>\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Name: <code>{data.get('name')}</code>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 3: LOT SIZE ====================

@error_handler
async def handle_move_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3 -> Step 4: Save lot size, show asset selection"""
    user = update.effective_user
    text = update.message.text
    
    try:
        lot_size = int(text)
        if not (1 <= lot_size <= 1000):
            raise ValueError("Out of range")
        
        await state_manager.set_state_data(user.id, {'lot_size': lot_size})
        logger.info(f"✅ MOVE lot size: {lot_size}")
        
        await state_manager.set_state(user.id, 'move_add_asset')
        
        await update.message.reply_text(
            f"✅ <b>Lot size saved: {lot_size}</b>\n\n"
            f"Step 4/7: <b>Asset Selection</b>\n\n"
            f"Select asset:",
            reply_markup=get_asset_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid lot size\n\n"
            f"Please enter a number between 1-1000:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== STEP 4: ASSET ====================

@error_handler
async def move_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4 -> Step 5: Save asset, show expiry"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract: "move_asset_BTC" -> BTC
    asset = query.data.split('_')[-1]  # Get last part (safer)
    
    await state_manager.set_state_data(user.id, {'asset': asset})
    logger.info(f"✅ MOVE asset: {asset}")
    
    await state_manager.set_state(user.id, 'move_add_expiry')
    
    await query.edit_message_text(
        f"✅ <b>Asset selected: {asset}</b>\n\n"
        f"Step 5/7: <b>Expiry Selection</b>\n\n"
        f"Select expiry type:",
        reply_markup=get_expiry_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 5: EXPIRY ====================

@error_handler
async def move_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5 -> Step 6: Save expiry, show direction"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    expiry = query.data.split('_')[-1]  # "move_expiry_daily" -> "daily"
    
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    logger.info(f"✅ MOVE expiry: {expiry}")
    
    await state_manager.set_state(user.id, 'move_add_direction')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Expiry selected: {expiry.capitalize()}</b>\n\n"
        f"Step 6/7: <b>Direction Selection</b>\n"
        f"Asset: <code>{data.get('asset')}</code>\n\n"
        f"Select direction:",
        reply_markup=get_direction_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 6: DIRECTION ====================

@error_handler
async def move_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6 -> Step 7: Save direction, show ATM offset"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    direction = query.data.split('_')[-1]  # "move_direction_long" -> "long"
    
    await state_manager.set_state_data(user.id, {'direction': direction})
    logger.info(f"✅ MOVE direction: {direction}")
    
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Direction selected: {direction.capitalize()}</b>\n\n"
        f"Step 7/7: <b>ATM Offset & Risk Management</b>\n"
        f"Asset: <code>{data.get('asset')}</code>\n"
        f"Expiry: <code>{data.get('expiry').capitalize()}</code>\n"
        f"Direction: <code>{direction.capitalize()}</code>\n\n"
        f"Enter ATM offset (-10 to +10):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 7: ATM OFFSET & RISK MGMT ====================

@error_handler
async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 7a: Save ATM offset, ask SL trigger"""
    user = update.effective_user
    text = update.message.text
    
    try:
        atm_offset = int(text)
        if not (-10 <= atm_offset <= 10):
            raise ValueError("Out of range")
        
        await state_manager.set_state_data(user.id, {'atm_offset': atm_offset})
        logger.info(f"✅ MOVE ATM: {atm_offset}")
        
        await state_manager.set_state(user.id, 'move_add_sl_trigger')
        
        await update.message.reply_text(
            f"✅ <b>ATM offset saved: {atm_offset:+d}</b>\n\n"
            f"Enter SL Trigger % (e.g., 25):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid offset\n\n"
            f"Please enter a number between -10 and +10:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 7b: Save SL trigger, ask SL limit"""
    user = update.effective_user
    text = update.message.text
    
    try:
        sl_trigger = float(text)
        if not (1 <= sl_trigger <= 200):
            raise ValueError("Out of range")
        
        await state_manager.set_state_data(user.id, {'sl_trigger_percent': sl_trigger})
        logger.info(f"✅ MOVE SL trigger: {sl_trigger}%")
        
        await state_manager.set_state(user.id, 'move_add_sl_limit')
        
        await update.message.reply_text(
            f"✅ <b>SL Trigger saved: {sl_trigger}%</b>\n\n"
            f"Enter SL Limit % (must be >= {sl_trigger}%):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid percentage\n\n"
            f"Please enter a number between 1-200:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 7c: Save SL limit, ask target (optional)"""
    user = update.effective_user
    text = update.message.text
    
    try:
        sl_limit = float(text)
        data = await state_manager.get_state_data(user.id)
        sl_trigger = data.get('sl_trigger_percent', 0)
        
        if not (1 <= sl_limit <= 200):
            raise ValueError("Out of range")
        
        if sl_limit < sl_trigger:
            raise ValueError(f"SL Limit must be >= SL Trigger ({sl_trigger}%)")
        
        await state_manager.set_state_data(user.id, {'sl_limit_percent': sl_limit})
        logger.info(f"✅ MOVE SL limit: {sl_limit}%")
        
        await state_manager.set_state(user.id, 'move_add_target_trigger')
        
        await update.message.reply_text(
            f"✅ <b>SL Limit saved: {sl_limit}%</b>\n\n"
            f"Enter Target Trigger % (optional):",
            reply_markup=get_skip_target_keyboard(),
            parse_mode='HTML'
        )
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n\nPlease enter valid %:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== TARGET (Optional) ====================

@error_handler
async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Target trigger input"""
    user = update.effective_user
    text = update.message.text
    
    try:
        target_trigger = float(text)
        if not (0 <= target_trigger <= 1000):
            raise ValueError("Out of range")
        
        await state_manager.set_state_data(user.id, {'target_trigger_percent': target_trigger})
        logger.info(f"✅ MOVE target trigger: {target_trigger}%")
        
        await state_manager.set_state(user.id, 'move_add_target_limit')
        
        await update.message.reply_text(
            f"✅ <b>Target Trigger saved: {target_trigger}%</b>\n\n"
            f"Enter Target Limit %:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid percentage\n\n"
            f"Please enter a number between 0-1000:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def handle_move_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Target limit input -> CONFIRMATION"""
    user = update.effective_user
    text = update.message.text
    
    try:
        target_limit = float(text)
        data = await state_manager.get_state_data(user.id)
        target_trigger = data.get('target_trigger_percent', 0)
        
        if not (0 <= target_limit <= 1000):
            raise ValueError("Out of range")
        
        if target_limit < target_trigger:
            raise ValueError(f"Target Limit must be >= Target Trigger ({target_trigger}%)")
        
        await state_manager.set_state_data(user.id, {'target_limit_percent': target_limit})
        logger.info(f"✅ MOVE target limit: {target_limit}%")
        
        await show_move_confirmation(update, context)
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n\nPlease enter valid %:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip target -> CONFIRMATION"""
    query = update.callback_query
    await query.answer("⏭️ Skipping target...")
    user = query.from_user
    
    await state_manager.set_state_data(user.id, {
        'target_trigger_percent': None,
        'target_limit_percent': None
    })
    
    logger.info("✅ Target skipped")
    await show_move_confirmation(update, context)

# ==================== CONFIRMATION & SAVE ====================

async def show_move_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation"""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name') or "Unnamed"
    description = data.get('description') or "None"
    asset = data.get('asset') or "N/A"
    expiry = data.get('expiry', 'N/A').capitalize()
    direction = data.get('direction', 'N/A').capitalize()
    atm_offset = data.get('atm_offset', 0)
    sl_trigger = data.get('sl_trigger_percent')
    sl_limit = data.get('sl_limit_percent')
    target_trigger = data.get('target_trigger_percent')
    target_limit = data.get('target_limit_percent')
    
    text = (
        f"✅ <b>MOVE Strategy - Final Confirmation</b>\n\n"
        f"📋 <b>Details:</b>\n"
        f"• Name: <code>{name}</code>\n"
        f"• Description: {description}\n"
        f"• Asset: <code>{asset}</code>\n"
        f"• Expiry: <code>{expiry}</code>\n"
        f"• Direction: <code>{direction}</code>\n"
        f"• ATM Offset: <code>{atm_offset:+d}</code>\n\n"
        f"📊 <b>Risk Management:</b>\n"
        f"• SL Trigger: <code>{sl_trigger}%</code>\n"
        f"• SL Limit: <code>{sl_limit}%</code>\n"
    )
    
    if target_trigger is not None and target_limit is not None:
        text += (
            f"• Target Trigger: <code>{target_trigger}%</code>\n"
            f"• Target Limit: <code>{target_limit}%</code>\n"
        )
    else:
        text += f"• Target: <i>Not set</i>\n"
    
    text += "\n✅ <b>Save this strategy?</b>"
    
    keyboard = get_confirmation_keyboard()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

@error_handler
async def move_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save strategy"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    try:
        strategy_data = {
            'strategy_name': data.get('name'),
            'description': data.get('description', ''),
            'asset': data.get('asset'),
            'expiry': data.get('expiry', 'daily'),
            'direction': data.get('direction'),
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
        log_user_action(user.id, f"Created MOVE: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ <b>MOVE Strategy Created!</b>\n\n"
            f"Name: <code>{data.get('name')}</code>\n"
            f"Asset: <code>{data.get('asset')}</code>\n\n"
            f"Strategy saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"❌ Error saving strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error: {str(e)}\n\nPlease try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel operation"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.clear_state(user.id)
    log_user_action(user.id, "Cancelled MOVE strategy creation")
    
    await query.edit_message_text(
        "❌ Operation Cancelled\n\nReturning to menu...",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'move_add_callback',
    'move_add_new_strategy_callback',
    'handle_move_add_name_input',
    'handle_move_description_input',
    'move_skip_description_callback',
    'handle_move_lot_size_input',
    'move_asset_callback',
    'move_expiry_callback',
    'move_direction_callback',
    'handle_move_atm_offset_input',
    'handle_move_sl_trigger_input',
    'handle_move_sl_limit_input',
    'handle_move_target_trigger_input',
    'handle_move_target_limit_input',
    'move_skip_target_callback',
    'show_move_confirmation',
    'move_confirm_save_callback',
    'move_cancel_callback',
]
