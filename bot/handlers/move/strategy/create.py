"""
✅ COMPLETE MOVE Strategy Creation - 7-STEP FLOW WITH INLINE KEYBOARDS
Handles: Name → Description → Lot Size → Asset → Expiry → Direction → ATM Offset/Risk Mgmt
All callback handlers included. Production-ready with full validation.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# ==================== STEP 0: START ====================

@error_handler
async def move_add_new_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 0: Start - Strategy Name Prompt"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    log_user_action(user.id, "Started MOVE strategy creation")
    
    # Clear existing state
    await state_manager.clear_state(user.id)
    context.user_data.clear()
    
    # Set initial state
    await state_manager.set_state(user.id, 'move_add_name')
    
    await query.edit_message_text(
        "📝 <b>Add MOVE Strategy</b>\n\n"
        "<b>Step 1/7: Strategy Name</b>\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "<i>Example: BTC 8AM MOVE, ETH Daily MOVE</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 1: STRATEGY NAME ====================

@error_handler
async def handle_move_add_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 1 → Step 2: Save name, show description"""
    user = update.effective_user
    
    # Validate
    if not text or len(text.strip()) < 2:
        await update.message.reply_text(
            "❌ Name too short (minimum 2 characters)",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    if len(text.strip()) > 100:
        await update.message.reply_text(
            "❌ Name too long (maximum 100 characters)",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Store name
    name = text.strip()
    context.user_data['name'] = name
    await state_manager.set_state_data(user.id, {'name': name})
    logger.info(f"✅ MOVE name saved: {name}")
    
    # Move to Step 2
    await state_manager.set_state(user.id, 'move_add_description')
    
    await update.message.reply_text(
        f"✅ <b>Name saved</b>\n\n"
        f"<code>{name}</code>\n\n"
        f"<b>Step 2/7: Description (Optional)</b>\n\n"
        f"Enter a description or click skip:",
        reply_markup=get_description_skip_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 2: DESCRIPTION ====================

@error_handler
async def handle_move_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 2 → Step 3: Save description, show lot size"""
    user = update.effective_user
    
    # Accept any text or empty
    description = text.strip() if text else ""
    context.user_data['description'] = description
    await state_manager.set_state_data(user.id, {'description': description})
    logger.info(f"✅ MOVE description: {description if description else '(empty)'}")
    
    # Move to Step 3
    await state_manager.set_state(user.id, 'move_add_lot_size')
    data = await state_manager.get_state_data(user.id)
    
    await update.message.reply_text(
        f"✅ <b>Description saved</b>\n\n"
        f"<b>Step 3/7: Lot Size</b>\n"
        f"Name: <b>{data.get('name', 'N/A')}</b>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description button"""
    query = update.callback_query
    await query.answer("⏭️ Skipping description...")
    user = query.from_user
    
    context.user_data['description'] = ""
    await state_manager.set_state_data(user.id, {'description': ""})
    logger.info("⏭️ Description skipped")
    
    # Move to Step 3
    await state_manager.set_state(user.id, 'move_add_lot_size')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"⏭️ <b>Description skipped</b>\n\n"
        f"<b>Step 3/7: Lot Size</b>\n"
        f"Name: <b>{data.get('name', 'N/A')}</b>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 3: LOT SIZE ====================

@error_handler
async def handle_move_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 3 → Step 4: Save lot size, show asset selection"""
    user = update.effective_user
    
    try:
        lot_size = int(text.strip())
        if not (1 <= lot_size <= 1000):
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid lot size\n\n"
            "Enter a number between 1-1000:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Store lot size
    context.user_data['lot_size'] = lot_size
    await state_manager.set_state_data(user.id, {'lot_size': lot_size})
    logger.info(f"✅ MOVE lot size: {lot_size}")
    
    # Move to Step 4
    await state_manager.set_state(user.id, 'move_add_asset')
    
    await update.message.reply_text(
        f"✅ <b>Lot size saved</b>\n\n"
        f"Lot Size: <b>{lot_size}</b>\n\n"
        f"<b>Step 4/7: Asset Selection</b>",
        reply_markup=get_asset_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 4: ASSET (CALLBACK) ====================

@error_handler
async def move_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4 → Step 5: Save asset, show expiry"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Parse asset from callback data: move_asset_btc -> btc
    asset = query.data.replace('move_asset_', '').upper()
    
    context.user_data['asset'] = asset
    await state_manager.set_state_data(user.id, {'asset': asset})
    logger.info(f"✅ MOVE asset: {asset}")
    
    # Move to Step 5
    await state_manager.set_state(user.id, 'move_add_expiry')
    
    await query.edit_message_text(
        f"✅ <b>Asset selected</b>\n\n"
        f"Asset: <b>{asset}</b>\n\n"
        f"<b>Step 5/7: Expiry Selection</b>",
        reply_markup=get_expiry_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 5: EXPIRY (CALLBACK) ====================

@error_handler
async def move_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5 → Step 6: Save expiry, show direction"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Parse expiry from callback data: move_expiry_1h -> 1h
    expiry = query.data.replace('move_expiry_', '').upper()
    
    context.user_data['expiry'] = expiry
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    logger.info(f"✅ MOVE expiry: {expiry}")
    
    # Move to Step 6
    await state_manager.set_state(user.id, 'move_add_direction')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Expiry selected</b>\n\n"
        f"Asset: <b>{data.get('asset')}</b>\n"
        f"Expiry: <b>{expiry}</b>\n\n"
        f"<b>Step 6/7: Direction Selection</b>\n\n"
        f"🟢 <b>LONG</b> = Buy MOVE\n"
        f"🔴 <b>SHORT</b> = Sell MOVE",
        reply_markup=get_direction_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 6: DIRECTION (CALLBACK) ====================

@error_handler
async def move_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6 → Step 7: Save direction, show ATM offset"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Parse direction from callback data: move_direction_long -> long
    direction = query.data.replace('move_direction_', '').upper()
    
    context.user_data['direction'] = direction
    await state_manager.set_state_data(user.id, {'direction': direction})
    logger.info(f"✅ MOVE direction: {direction}")
    
    # Move to Step 7
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"✅ <b>Direction selected</b>\n\n"
        f"Asset: <b>{data.get('asset')}</b>\n"
        f"Expiry: <b>{data.get('expiry')}</b>\n"
        f"Direction: <b>{direction}</b>\n\n"
        f"<b>Step 7/7: ATM Offset & Risk Management</b>\n\n"
        f"Enter ATM offset (-10 to +10):\n"
        f"• 0 = ATM (no offset)\n"
        f"• +1 = 1 strike higher\n"
        f"• -1 = 1 strike lower",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 7: ATM OFFSET & RISK MGMT ====================

@error_handler
async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7a: Save ATM offset → Ask SL Trigger %"""
    user = update.effective_user
    
    try:
        atm_offset = int(text.strip())
        if not (-10 <= atm_offset <= 10):
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ATM offset\n\n"
            "Enter -10 to +10:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    context.user_data['atm_offset'] = atm_offset
    await state_manager.set_state_data(user.id, {'atm_offset': atm_offset})
    logger.info(f"✅ MOVE ATM offset: {atm_offset:+d}")
    
    # Next: SL Trigger %
    await state_manager.set_state(user.id, 'move_add_sl_trigger')
    
    await update.message.reply_text(
        f"✅ <b>ATM offset saved</b>\n\n"
        f"ATM Offset: <b>{atm_offset:+d}</b>\n\n"
        f"<b>SL Trigger % (When to exit with loss?)</b>\n\n"
        f"Enter SL trigger % (e.g., 25):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7b: Save SL Trigger % → Ask SL Limit %"""
    user = update.effective_user
    
    try:
        sl_trigger = float(text.strip())
        if not (0 < sl_trigger <= 500):
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid SL trigger\n\n"
            "Enter 0.1 to 500:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    context.user_data['sl_trigger_percent'] = sl_trigger
    await state_manager.set_state_data(user.id, {'sl_trigger_percent': sl_trigger})
    logger.info(f"✅ MOVE SL trigger: {sl_trigger}%")
    
    # Next: SL Limit %
    await state_manager.set_state(user.id, 'move_add_sl_limit')
    
    await update.message.reply_text(
        f"✅ <b>SL Trigger saved</b>\n\n"
        f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
        f"<b>SL Limit % (Max loss allowed?)</b>\n\n"
        f"Enter SL limit % (e.g., 30):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7c: Save SL Limit % → Show Confirmation"""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    try:
        sl_limit = float(text.strip())
        sl_trigger = data.get('sl_trigger_percent', 0)
        
        if not (0 < sl_limit <= 500):
            raise ValueError()
        
        if sl_limit < sl_trigger:
            raise ValueError(f"SL Limit must be >= SL Trigger ({sl_trigger}%)")
    
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n\n"
            f"Enter valid %:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    context.user_data['sl_limit_percent'] = sl_limit
    await state_manager.set_state_data(user.id, {'sl_limit_percent': sl_limit})
    logger.info(f"✅ MOVE SL limit: {sl_limit}%")
    
    # Show confirmation
    await show_move_confirmation(update, context)

# ==================== CONFIRMATION & SAVE ====================

async def show_move_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation before saving"""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name', 'Unnamed')
    description = data.get('description', '')
    asset = data.get('asset', 'N/A')
    expiry = data.get('expiry', 'N/A')
    direction = data.get('direction', 'N/A')
    lot_size = data.get('lot_size', 'N/A')
    atm_offset = data.get('atm_offset', 0)
    sl_trigger = data.get('sl_trigger_percent', 'N/A')
    sl_limit = data.get('sl_limit_percent', 'N/A')
    
    text = (
        f"✅ <b>MOVE Strategy - Final Confirmation</b>\n\n"
        f"📋 <b>Strategy Details:</b>\n"
        f"• <b>Name:</b> {name}\n"
    )
    
    if description:
        text += f"• <b>Description:</b> {description}\n"
    
    text += (
        f"• <b>Asset:</b> {asset}\n"
        f"• <b>Expiry:</b> {expiry}\n"
        f"• <b>Direction:</b> {direction}\n"
        f"• <b>Lot Size:</b> {lot_size}\n"
        f"• <b>ATM Offset:</b> {atm_offset:+d}\n\n"
        f"📊 <b>Risk Management:</b>\n"
        f"• <b>SL Trigger:</b> {sl_trigger}%\n"
        f"• <b>SL Limit:</b> {sl_limit}%\n\n"
        f"<b>✅ Save this strategy?</b>"
    )
    
    keyboard = get_confirmation_keyboard()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

@error_handler
async def move_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save strategy"""
    query = update.callback_query
    await query.answer("💾 Saving strategy...")
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    try:
        # Prepare data for DB
        strategy_data = {
            'strategy_name': data.get('name'),
            'description': data.get('description', ''),
            'asset': data.get('asset'),
            'expiry': data.get('expiry', 'daily'),
            'direction': data.get('direction'),
            'lot_size': data.get('lot_size'),
            'atm_offset': data.get('atm_offset', 0),
            'stop_loss_trigger': data.get('sl_trigger_percent'),
            'stop_loss_limit': data.get('sl_limit_percent'),
        }
        
        # Save to database
        result = await create_move_strategy(user.id, strategy_data)
        
        if not result:
            raise Exception("Failed to create strategy in database")
        
        # Clear state
        await state_manager.clear_state(user.id)
        context.user_data.clear()
        log_user_action(user.id, f"Created MOVE: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ <b>MOVE Strategy Created!</b>\n\n"
            f"<b>{data.get('name')}</b>\n"
            f"Asset: {data.get('asset')}\n"
            f"Direction: {data.get('direction')}\n\n"
            f"Strategy saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        logger.info(f"✅ Strategy saved for user {user.id}: {data.get('name')}")
        
    except Exception as e:
        logger.error(f"❌ Error saving strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error: {str(e)}\n\n"
            f"Please try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel strategy creation"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.clear_state(user.id)
    context.user_data.clear()
    log_user_action(user.id, "Cancelled MOVE creation")
    
    await query.edit_message_text(
        "❌ <b>Operation Cancelled</b>",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )


__all__ = [
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
    'show_move_confirmation',
    'move_confirm_save_callback',
    'move_cancel_callback',
    ]
    
