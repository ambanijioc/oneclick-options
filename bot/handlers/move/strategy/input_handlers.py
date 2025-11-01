"""
MOVE Strategy Input Handlers - FIXED & COMPLETE
Handles text input for MOVE strategy creation flows
Includes state validation in all handlers
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
    get_move_menu_keyboard,
)

logger = setup_logger(__name__)

# ============ VALIDATORS ============

def validate_strategy_name(name: str) -> tuple[bool, str]:
    """Validate strategy name - relaxed rules for trading symbols"""
    name = name.strip()
    
    if not name:
        return False, "Name cannot be empty"
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    if not re.match(r"^[a-zA-Z0-9\s\-_#@&:%/.()]+$", name):
        return False, (
            "❌ Invalid characters found!\n\n"
            "✅ Allowed: letters, numbers, spaces,\n"
            "hyphens (-), underscores (_), %, @, &, #, :, /, (), .\n\n"
            "Try: 'BTC Daily Move' or 'ETH Morning Strategy'"
        )
    return True, ""

def validate_lot_size(value: str) -> tuple[bool, str, int]:
    """Validate lot size (1-1000)"""
    try:
        lot_size = int(value.strip())
        if lot_size < 1 or lot_size > 1000:
            return False, "Lot size must be between 1 and 1000", 0
        return True, "", lot_size
    except ValueError:
        return False, "Lot size must be a whole number", 0

def validate_percentage(value: str, field_name: str = "Value") -> tuple[bool, str, float]:
    """Validate percentage inputs (0-100)"""
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
    """Handle MOVE strategy name input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_name':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    logger.info(f"📥 Strategy name input: '{text}'")
    
    # VALIDATE NAME
    valid, error = validate_strategy_name(text)
    if not valid:
        await update.message.reply_text(
            f"❌ {error}",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO NEXT STATE
    await state_manager.set_state_data(user.id, {'name': text})
    await state_manager.set_state(user.id, 'move_add_description')
    
    logger.info(f"✅ Strategy name saved: {text}")
    
    await update.message.reply_text(
        f"✅ Strategy name saved: <code>{text}</code>\n\n"
        f"Step 2/7: <b>Description (Optional)</b>\n"
        f"Enter a description or skip:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ DESCRIPTION INPUT ============

@error_handler
async def handle_move_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle optional description input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_description':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    # VALIDATE LENGTH
    if len(text) > 500:
        await update.message.reply_text(
            "❌ Description too long (max 500 characters)\n\n"
            "Please enter a shorter description:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO NEXT STATE
    logger.info(f"📥 Description saved: '{text[:50]}'...")
    
    await state_manager.set_state_data(user.id, {'description': text})
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    await update.message.reply_text(
        f"✅ Description saved\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ LOT SIZE INPUT ============

@error_handler
async def handle_move_lot_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lot size input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_lot_size':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, lot_size = validate_lot_size(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nPlease enter lot size (1-1000):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO NEXT STATE
    await state_manager.set_state_data(user.id, {'lot_size': lot_size})
    await state_manager.set_state(user.id, 'move_add_sl_trigger')
    
    log_user_action(user.id, f"Set lot size: {lot_size}")
    logger.info(f"✅ Lot size set: {lot_size}")
    
    await update.message.reply_text(
        f"✅ Lot size: {lot_size}\n\n"
        f"Step 4/7: <b>Stop Loss Trigger %</b>\n"
        f"Enter SL trigger (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ SL INPUTS ============

@error_handler
async def handle_move_sl_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL trigger input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_sl_trigger':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "SL Trigger")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nEnter SL Trigger % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO NEXT STATE
    await state_manager.set_state_data(user.id, {'sl_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_sl_limit')
    
    log_user_action(user.id, f"Set SL trigger: {pct}%")
    logger.info(f"✅ SL trigger: {pct}%")
    
    await update.message.reply_text(
        f"✅ SL Trigger: {pct}%\n\n"
        f"Step 5/7: <b>Stop Loss Limit %</b>\n"
        f"Enter SL limit (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_sl_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL limit input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_sl_limit':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "SL Limit")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nEnter SL Limit % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO NEXT STATE
    await state_manager.set_state_data(user.id, {'sl_limit_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_trigger')
    
    log_user_action(user.id, f"Set SL limit: {pct}%")
    logger.info(f"✅ SL limit: {pct}%")
    
    await update.message.reply_text(
        f"✅ SL Limit: {pct}%\n\n"
        f"Step 6/7: <b>Target Setup (Optional)</b>\n"
        f"Enter target trigger % or skip:",
        reply_markup=get_skip_target_keyboard(),
        parse_mode='HTML'
    )

# ============ TARGET INPUTS ============

@error_handler
async def handle_move_target_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target trigger input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_target_trigger':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "Target Trigger")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nEnter Target Trigger % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO NEXT STATE
    await state_manager.set_state_data(user.id, {'target_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_limit')
    
    log_user_action(user.id, f"Set target trigger: {pct}%")
    logger.info(f"✅ Target trigger: {pct}%")
    
    await update.message.reply_text(
        f"✅ Target Trigger: {pct}%\n\n"
        f"Step 7/7: <b>Target Limit %</b>\n"
        f"Enter target limit (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_target_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target limit input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ STATE VALIDATION
    state = await state_manager.get_state(user.id)
    if state != 'move_add_target_limit':
        return  # Not our state, exit silently
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "Target Limit")
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nEnter Target Limit % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # SAVE & MOVE TO CONFIRMATION
    await state_manager.set_state_data(user.id, {'target_limit_percent': pct})
    
    log_user_action(user.id, f"Set target limit: {pct}%")
    logger.info(f"✅ Target limit: {pct}%")
    
    # Import and show confirmation
    from bot.handlers.move.strategy.create import show_move_confirmation
    await show_move_confirmation(update, context)

__all__ = [
    'validate_strategy_name',
    'validate_lot_size',
    'validate_percentage',
    'handle_move_strategy_name',
    'handle_move_description',
    'handle_move_lot_size',
    'handle_move_sl_trigger',
    'handle_move_sl_limit',
    'handle_move_target_trigger',
    'handle_move_target_limit',
    ]
