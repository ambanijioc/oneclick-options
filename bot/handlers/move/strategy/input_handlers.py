"""
MOVE Strategy Input Handlers

Handles text input for MOVE strategy creation and editing flows.
Includes lot size validation, SL/Target handling, and percentage inputs.
"""

import re
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import create_move_strategy, update_move_strategy
from bot.keyboards.move_strategy_keyboards import (
    get_skip_target_keyboard,
    get_cancel_keyboard,
    get_move_menu_keyboard
)

logger = setup_logger(__name__)

# ✅ FIX: IMPROVED VALIDATORS
def validate_strategy_name(name: str) -> tuple[bool, str]:
    """Validate strategy name (3-50 chars, alphanumeric + spaces/hyphens)"""
    if not name or len(name) < 3 or len(name) > 50:
        return False, "Name must be 3-50 characters long"
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
        return False, "Name can only contain letters, numbers, spaces, hyphens, underscores"
    return True, ""

def validate_lot_size(value: str) -> tuple[bool, str, int]:
    """
    ✅ FIX: Validate lot size input
    Returns: (is_valid, error_message, lot_size)
    """
    try:
        lot_size = int(value.strip())
        if lot_size < 1 or lot_size > 1000:
            return False, "Lot size must be between 1 and 1000", 0
        return True, "", lot_size
    except ValueError:
        return False, "Lot size must be a whole number", 0

def validate_atm_offset(value: str) -> tuple[bool, str, int]:
    """✅ FIX: Validate ATM offset (-10 to +10)"""
    try:
        offset = int(value.strip())
        if offset < -10 or offset > 10:
            return False, "ATM offset must be between -10 and +10", 0
        return True, "", offset
    except ValueError:
        return False, "ATM offset must be a whole number", 0

def validate_percentage(value: str, field_name: str = "Percentage") -> tuple[bool, str, float]:
    """✅ FIX: Validate percentage inputs (0-100)"""
    try:
        pct = float(value.strip())
        if pct < 0 or pct > 100:
            return False, f"{field_name} must be between 0 and 100", 0
        return True, "", pct
    except ValueError:
        return False, f"{field_name} must be a number", 0

# ============ STRATEGY NAME INPUT ============

@error_handler
async def handle_move_strategy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle MOVE strategy name input during creation"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error = validate_strategy_name(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Please enter a valid strategy name:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'name': text})
    await state_manager.set_state(user.id, 'move_add_description')
    
    await update.message.reply_text(
        f"✅ Strategy name: {text}\n\n"
        f"📝 Step 2/7: Description (optional)\n\n"
        f"Enter a description or press Skip:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ✅ FIX: handle_move_description function

@error_handler
async def handle_move_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle MOVE strategy description input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Save description
    await state_manager.set_state_data(user.id, {'description': text})
    await state_manager.set_state(user.id, 'move_add_asset')
    
    data = await state_manager.get_state_data(user.id)
    
    # ✅ SEND WITH ASSET KEYBOARD BUTTONS
    await update.message.reply_text(
        f"✅ Description saved\n\n"
        f"📝 Step 3/7: Asset Selection\n\n"
        f"Name: {data.get('name')}\n\n"
        f"Select your asset:",
        reply_markup=get_asset_keyboard(),  # ✅ THIS WAS MISSING!
        parse_mode='HTML'
    )

# ============ LOT SIZE INPUT ============

@error_handler
async def handle_move_lot_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Handle lot size input with improved validation
    """
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, lot_size = validate_lot_size(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Please enter a valid lot size (1-1000):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'lot_size': lot_size})
    await state_manager.set_state(user.id, 'move_add_sl_trigger')
    
    log_user_action(user.id, f"Set lot size: {lot_size}")
    
    await update.message.reply_text(
        f"✅ Lot size set: {lot_size}\n\n"
        f"💰 Step 5/7: Stop Loss Setup\n\n"
        f"Enter SL Trigger percentage (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ ATM OFFSET INPUT ============

@error_handler
async def handle_move_atm_offset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ FIX: Handle ATM offset input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, offset = validate_atm_offset(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Please enter a valid offset (-10 to +10):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'atm_offset': offset})
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    log_user_action(user.id, f"Set ATM offset: {offset}")
    
    await update.message.reply_text(
        f"✅ ATM offset set: {offset:+d}\n\n"
        f"📊 Step 6/7: Lot Size\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ STOP LOSS INPUTS ============

@error_handler
async def handle_move_sl_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ FIX: Handle SL trigger percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "SL Trigger")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Enter SL Trigger % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'sl_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_sl_limit')
    
    logger.info(f"User {user.id} set SL trigger: {pct}%")
    
    await update.message.reply_text(
        f"✅ SL Trigger set: {pct}%\n\n"
        f"Enter SL Limit percentage:\n"
        f"(Usually lower than trigger):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_sl_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ FIX: Handle SL limit percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "SL Limit")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Enter SL Limit % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'sl_limit_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_trigger')
    
    await update.message.reply_text(
        f"✅ SL Limit set: {pct}%\n\n"
        f"🎯 Target Setup\n\n"
        f"Enter Target Trigger percentage\n"
        f"(or Skip if not needed):",
        reply_markup=get_skip_target_keyboard(),
        parse_mode='HTML'
    )

# ============ TARGET INPUTS ============

@error_handler
async def handle_move_target_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ FIX: Handle target trigger percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "Target Trigger")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Enter Target Trigger % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'target_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_limit')
    
    await update.message.reply_text(
        f"✅ Target Trigger set: {pct}%\n\n"
        f"Enter Target Limit percentage:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_target_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ FIX: Handle target limit percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "Target Limit")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"Enter Target Limit % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'target_limit_percent': pct})
    
    # Show confirmation (from create.py)
    from bot.handlers.move.strategy.create import show_move_confirmation
    await show_move_confirmation(update, context)

# ============ EDIT MODE HANDLERS ============

@error_handler
async def handle_move_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name edit input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    valid, error = validate_strategy_name(text)
    if not valid:
        await update.message.reply_text(f"❌ {error}")
        return
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('editing_strategy_id')
    
    result = await update_move_strategy(user.id, strategy_id, {'strategy_name': text})
    
    if result:
        await update.message.reply_text(f"✅ Name updated to: {text}")
        log_user_action(user.id, f"Updated strategy name: {text}")
    else:
        await update.message.reply_text("❌ Failed to update")

@error_handler
async def handle_move_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle description edit input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('editing_strategy_id')
    
    result = await update_move_strategy(user.id, strategy_id, {'description': text})
    
    if result:
        await update.message.reply_text(f"✅ Description updated")
        log_user_action(user.id, "Updated strategy description")
    else:
        await update.message.reply_text("❌ Failed to update")

@error_handler
async def handle_move_edit_atm_offset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ATM offset edit input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    valid, error, offset = validate_atm_offset(text)
    if not valid:
        await update.message.reply_text(f"❌ {error}")
        return
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('editing_strategy_id')
    
    result = await update_move_strategy(user.id, strategy_id, {'atm_offset': offset})
    
    if result:
        await update.message.reply_text(f"✅ ATM offset updated: {offset:+d}")
        log_user_action(user.id, f"Updated ATM offset: {offset:+d}")
    else:
        await update.message.reply_text("❌ Failed to update")

__all__ = [
    'validate_strategy_name',
    'validate_lot_size',
    'validate_atm_offset',
    'validate_percentage',
    'handle_move_strategy_name',
    'handle_move_description',
    'handle_move_lot_size',
    'handle_move_atm_offset',
    'handle_move_sl_trigger',
    'handle_move_sl_limit',
    'handle_move_target_trigger',
    'handle_move_target_limit',
    'handle_move_edit_name',
    'handle_move_edit_description',
    'handle_move_edit_atm_offset',
    ]
