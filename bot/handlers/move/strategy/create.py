"""
MOVE Strategy Creation - COMPLETE 7-STEP FLOW WITH INLINE KEYBOARDS
Based on old code reference but with all new features
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
    
    log_user_action(user.id, "Started MOVE strategy")
    
    # Clear existing state
    await state_manager.clear_state(user.id)
    await state_manager.set_state(user.id, 'move_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'move'})
    
    await query.edit_message_text(
        "📝 Add MOVE Strategy\n\n"
        "Step 1/7: Strategy Name\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "Example: BTC 8AM MOVE, ETH Daily MOVE",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_add_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 1 -> Step 2: Save name, show description prompt"""
    user = update.effective_user
    
    # Store name
    await state_manager.set_state_data(user.id, {'name': text})
    logger.info(f"✅ MOVE name: {text}")
    
    # Move to description
    await state_manager.set_state(user.id, 'move_add_description')
    
    await update.message.reply_text(
        f"✅ <b>Strategy name saved</b>\n\n"
        f"<code>{text}</code>\n\n"
        f"Step 2/7: <b>Description (Optional)</b>\n\n"
        f"Enter a description or skip:",
        reply_markup=get_description_skip_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 2: DESCRIPTION ====================

@error_handler
async def handle_move_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 2 -> Step 3: Save description, show lot size"""
    user = update.effective_user
    
    await state_manager.set_state_data(user.id, {'description': text})
    logger.info(f"✅ MOVE description: {text[:50]}")
    
    await state_manager.set_state(user.id, 'move_add_lot_size')
    data = await state_manager.get_state_data(user.id)
    
    await update.message.reply_text(
        f"✅ <b>Description saved</b>\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Name: {data.get('name')}\n\n"
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
    
    logger.info(f"⏭️ Description skipped")
    
    await query.edit_message_text(
        f"⏭️ <b>Description skipped</b>\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Name: {data.get('name')}\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 3: LOT SIZE ====================

@error_handler
async def handle_move_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 3 -> Step 4: Save lot size, show asset selection"""
    user = update.effective_user
    
    try:
        lot_size = int(text)
        if not (1 <= lot_size <= 1000):
            raise ValueError("1-1000")
        
        await state_manager.set_state_data(user.id, {'lot_size': lot_size})
        logger.info(f"✅ MOVE lot size: {lot_size}")
        
        await state_manager.set_state(user.id, 'move_add_asset')
        
        await update.message.reply_text(
            f"✅ <b>Lot size saved</b>\n\n"
            f"Step 4/7: <b>Asset Selection</b>\n"
            f"Lot Size: {lot_size}\n\n"
            f"Select asset:",
            reply_markup=get_asset_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid lot size\n\n"
            f"Enter a number 1-1000:",
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
    
    asset = query.data.split('_')[2].upper()  # btc -> BTC
    await state_manager.set_state_data(user.id, {'asset': asset})
    logger.info(f"✅ MOVE asset: {asset}")
    
    await state_manager.set_state(user.id, 'move_add_expiry')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Asset selected</b>\n\n"
        f"Step 5/7: <b>Expiry Selection</b>\n"
        f"Asset: {asset}\n\n"
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
    
    expiry = query.data.split('_')[2]
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    logger.info(f"✅ MOVE expiry: {expiry}")
    
    await state_manager.set_state(user.id, 'move_add_direction')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Expiry selected</b>\n\n"
        f"Step 6/7: <b>Direction Selection</b>\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {expiry.capitalize()}\n\n"
        f"Select direction:\n\n"
        f"🟢 Long: Buy MOVE\n"
        f"🔴 Short: Sell MOVE",
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
    
    direction = query.data.split('_')[2]
    await state_manager.set_state_data(user.id, {'direction': direction})
    logger.info(f"✅ MOVE direction: {direction}")
    
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Direction selected</b>\n\n"
        f"Step 7/7: <b>ATM Offset & Risk Mgmt</b>\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {data.get('expiry').capitalize()}\n"
        f"Direction: {direction.capitalize()}\n\n"
        f"Enter ATM offset (-10 to +10):\n"
        f"• 0 = ATM\n"
        f"• 1 = 1 strike ↑\n"
        f"• -1 = 1 strike ↓",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 7: ATM OFFSET & RISK MGMT ====================

@error_handler
async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7a: Save ATM offset, ask SL trigger"""
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        if not (-10 <= atm_offset <= 10):
            raise ValueError("-10 to +10")
        
        await state_manager.set_state_data(user.id, {'atm_offset': atm_offset})
        logger.info(f"✅ MOVE ATM: {atm_offset}")
        
        await state_manager.set_state(user.id, 'move_add_sl_trigger')
        
        await update.message.reply_text(
            f"✅ <b>ATM offset saved</b>\n\n"
            f"ATM Offset: {atm_offset:+d}\n\n"
            f"Enter SL Trigger % (e.g., 25):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Enter -10 to +10:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7b: Save SL trigger, ask SL limit"""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if not (1 <= sl_trigger <= 200):
            raise ValueError("1-200")
        
        await state_manager.set_state_data(user.id, {'sl_trigger_percent': sl_trigger})
        logger.info(f"✅ MOVE SL trigger: {sl_trigger}%")
        
        await state_manager.set_state(user.id, 'move_add_sl_limit')
        
        await update.message.reply_text(
            f"✅ <b>SL Trigger saved</b>\n\n"
            f"SL Trigger: {sl_trigger}%\n\n"
            f"Enter SL Limit % (e.g., 30):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Enter 1-200:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7c: Save SL limit, ask target (optional)"""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        data = await state_manager.get_state_data(user.id)
        sl_trigger = data.get('sl_trigger_percent', 0)
        
        if not (1 <= sl_limit <= 200):
            raise ValueError("1-200")
        
        if sl_limit < sl_trigger:
            raise ValueError(f"must be >= {sl_trigger}%")
        
        await state_manager.set_state_data(user.id, {'sl_limit_percent': sl_limit})
        logger.info(f"✅ MOVE SL limit: {sl_limit}%")
        
        await state_manager.set_state(user.id, 'move_add_target_trigger')
        
        await update.message.reply_text(
            f"✅ <b>SL Limit saved</b>\n\n"
            f"SL Limit: {sl_limit}%\n\n"
            f"Enter Target Trigger % (optional):",
            reply_markup=get_skip_target_keyboard(),
            parse_mode='HTML'
        )
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n\nEnter valid %:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== TARGET (Optional) ====================

@error_handler
async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Target trigger input"""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if not (0 <= target_trigger <= 1000):
            raise ValueError("0-1000")
        
        await state_manager.set_state_data(user.id, {'target_trigger_percent': target_trigger})
        logger.info(f"✅ MOVE target trigger: {target_trigger}%")
        
        await state_manager.set_state(user.id, 'move_add_target_limit')
        
        await update.message.reply_text(
            f"✅ <b>Target Trigger saved</b>\n\n"
            f"Target Trigger: {target_trigger}%\n\n"
            f"Enter Target Limit %:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Enter 0-1000:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def handle_move_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Target limit input -> CONFIRMATION"""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        data = await state_manager.get_state_data(user.id)
        target_trigger = data.get('target_trigger_percent', 0)
        
        if not (0 <= target_limit <= 1000):
            raise ValueError("0-1000")
        
        if target_limit < target_trigger:
            raise ValueError(f"must be >= {target_trigger}%")
        
        await state_manager.set_state_data(user.id, {'target_limit_percent': target_limit})
        logger.info(f"✅ MOVE target limit: {target_limit}%")
        
        await show_move_confirmation(update, context)
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n\nEnter valid %:",
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
    description = data.get('description')
    asset = data.get('asset') or "N/A"
    expiry = data.get('expiry', 'N/A')
    direction = data.get('direction', 'N/A')
    atm_offset = data.get('atm_offset')
    sl_trigger = data.get('sl_trigger_percent')
    sl_limit = data.get('sl_limit_percent')
    target_trigger = data.get('target_trigger_percent')
    target_limit = data.get('target_limit_percent')
    
    text = f"✅ <b>MOVE Strategy - Final Confirmation</b>\n\n📋 <b>Details:</b>\n• Name: {name}\n"
    
    if description:
        text += f"• Description: {description}\n"
    
    text += (
        f"• Asset: {asset}\n"
        f"• Expiry: {expiry.capitalize()}\n"
        f"• Direction: {direction.capitalize()}\n"
        f"• ATM Offset: {atm_offset}\n\n"
        f"📊 <b>Risk Management:</b>\n"
        f"• SL Trigger: {sl_trigger}%\n"
        f"• SL Limit: {sl_limit}%\n"
    )
    
    if target_trigger is not None:
        text += f"• Target Trigger: {target_trigger}%\n• Target Limit: {target_limit}%\n"
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
            raise Exception("Failed to save")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created MOVE: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ <b>MOVE Strategy Created!</b>\n\n"
            f"Name: {data.get('name')}\n"
            f"Asset: {data.get('asset')}\n\n"
            f"Strategy saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
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
    log_user_action(user.id, "Cancelled MOVE")
    
    await query.edit_message_text(
        "❌ Operation Cancelled",
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
    
