"""
MOVE Strategy Input Handlers - Complete Implementation
Step 2 (Description) & Step 7 (Target Trigger) are OPTIONAL
If user skips Step 7, Step 8 is automatically skipped too
"""

import re
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization

logger = setup_logger(__name__)

# ============ VALIDATORS ============

def validate_strategy_name(name: str) -> tuple[bool, str]:
    """Validate strategy name"""
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

def validate_atm_offset(value: str) -> tuple[bool, str, int]:
    """Validate ATM offset (-10 to +10)"""
    try:
        offset = int(value.strip())
        if offset < -10 or offset > 10:
            return False, "ATM offset must be between -10 and +10", 0
        return True, "", offset
    except ValueError:
        return False, "ATM offset must be a whole number", 0

def validate_percentage(value: str, field_name: str = "Value") -> tuple[bool, str, float]:
    """Validate percentage inputs (0-100)"""
    try:
        pct = float(value.strip())
        if pct < 0 or pct > 100:
            return False, f"{field_name} must be between 0 and 100", 0
        return True, "", pct
    except ValueError:
        return False, f"{field_name} must be a number", 0

# ============ STEP 1: STRATEGY NAME INPUT ============

@error_handler
async def handle_move_strategy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle MOVE strategy name input - Step 1"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_name':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error = validate_strategy_name(text)
    if not valid:
        await update.message.reply_text(
            f"❌ {error}",
            reply_markup=None,
            parse_mode='HTML'
        )
        return
    
    # Save name to state
    await state_manager.set_state_data(user.id, {'name': text})
    await state_manager.set_state(user.id, 'move_add_description')
    
    log_user_action(user.id, f"Strategy name: {text}")
    logger.info(f"✅ Step 1 complete - Name saved: {text}")
    
    # Move to Step 2: Optional Description
    from bot.keyboards.move_strategy_keyboards import get_skip_description_keyboard
    await update.message.reply_text(
        f"✅ <b>Name saved:</b> <code>{text}</code>\n\n"
        f"<b>Step 2/7: Description (Optional)</b>\n"
        f"Enter description or skip:",
        reply_markup=get_skip_description_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 2: DESCRIPTION INPUT (OPTIONAL) ============

@error_handler
async def handle_move_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle optional description input - Step 2"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_description':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    # ✅ FIXED: No validation comparing description to name!
    
    if len(text) > 500:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            "❌ Description too long (max 500 characters)\n\n"
            "Please enter shorter description:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save description
    await state_manager.set_state_data(user.id, {'description': text})
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    log_user_action(user.id, f"Description: {text[:50]}")
    logger.info(f"✅ Step 2 complete - Description saved")
    
    # Move to Step 3: Lot Size
    from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
    await update.message.reply_text(
        f"✅ <b>Description saved</b>\n\n"
        f"<b>Step 3/7: Lot Size</b>\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 3: LOT SIZE INPUT ============

@error_handler
async def handle_move_lot_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lot size input - Step 3"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_lot_size':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, lot_size = validate_lot_size(text)
    if not valid:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nEnter lot size (1-1000):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save lot size
    await state_manager.set_state_data(user.id, {'lot_size': lot_size})
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    
    log_user_action(user.id, f"Lot size: {lot_size}")
    logger.info(f"✅ Step 3 complete - Lot size: {lot_size}")
    
    # Move to Step 4: ATM Offset
    from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
    await update.message.reply_text(
        f"✅ <b>Lot size:</b> {lot_size}\n\n"
        f"<b>Step 4/7: ATM Offset</b>\n"
        f"Enter ATM offset (-10 to +10):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 4: ATM OFFSET INPUT ============

@error_handler
async def handle_move_atm_offset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ATM offset input - Step 4"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_atm_offset':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, offset = validate_atm_offset(text)
    if not valid:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nEnter ATM offset (-10 to +10):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save ATM offset
    await state_manager.set_state_data(user.id, {'atm_offset': offset})
    await state_manager.set_state(user.id, 'move_add_sl_trigger')
    
    log_user_action(user.id, f"ATM offset: {offset:+d}")
    logger.info(f"✅ Step 4 complete - ATM offset: {offset:+d}")
    
    # Move to Step 5: SL Trigger
    from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
    await update.message.reply_text(
        f"✅ <b>ATM Offset:</b> {offset:+d}\n\n"
        f"<b>Step 5/7: Stop Loss Trigger %</b>\n"
        f"Enter SL trigger (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 5: SL TRIGGER INPUT ============

@error_handler
async def handle_move_sl_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL trigger input - Step 5"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_sl_trigger':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "SL Trigger")
    if not valid:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nEnter SL Trigger % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save SL Trigger
    await state_manager.set_state_data(user.id, {'sl_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_sl_limit')
    
    log_user_action(user.id, f"SL trigger: {pct}%")
    logger.info(f"✅ Step 5 complete - SL trigger: {pct}%")
    
    # Move to Step 6: SL Limit
    from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
    await update.message.reply_text(
        f"✅ <b>SL Trigger:</b> {pct}%\n\n"
        f"<b>Step 6/7: Stop Loss Limit %</b>\n"
        f"Enter SL limit (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 6: SL LIMIT INPUT ============

@error_handler
async def handle_move_sl_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL limit input - Step 6"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_sl_limit':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "SL Limit")
    if not valid:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nEnter SL Limit % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save SL Limit
    await state_manager.set_state_data(user.id, {'sl_limit_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_trigger')
    
    log_user_action(user.id, f"SL limit: {pct}%")
    logger.info(f"✅ Step 6 complete - SL limit: {pct}%")
    
    # Move to Step 7: Target Trigger (Optional)
    from bot.keyboards.move_strategy_keyboards import get_skip_target_keyboard
    await update.message.reply_text(
        f"✅ <b>SL Limit:</b> {pct}%\n\n"
        f"<b>Step 7/7: Target Trigger (Optional)</b>\n"
        f"Enter target trigger % or skip to confirmation:",
        reply_markup=get_skip_target_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 7: TARGET TRIGGER INPUT (OPTIONAL) ============

@error_handler
async def handle_move_target_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target trigger input - Step 7 (Optional)"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_target_trigger':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "Target Trigger")
    if not valid:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nEnter Target Trigger % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # ✅ User entered target trigger, so ask for target limit (Step 8)
    await state_manager.set_state_data(user.id, {'target_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_limit')
    
    log_user_action(user.id, f"Target trigger: {pct}%")
    logger.info(f"✅ Step 7 complete - Target trigger: {pct}%")
    
    # Ask for Step 8: Target Limit
    from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
    await update.message.reply_text(
        f"✅ <b>Target Trigger:</b> {pct}%\n\n"
        f"<b>Step 8/8: Target Limit %</b>\n"
        f"Enter target limit (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ STEP 8: TARGET LIMIT INPUT ============

@error_handler
async def handle_move_target_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target limit input - Step 8 (Only if Step 7 entered)"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_target_limit':
        return
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, pct = validate_percentage(text, "Target Limit")
    if not valid:
        from bot.keyboards.move_strategy_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nEnter Target Limit % (0-100):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Save Target Limit
    await state_manager.set_state_data(user.id, {'target_limit_percent': pct})
    
    log_user_action(user.id, f"Target limit: {pct}%")
    logger.info(f"✅ Step 8 complete - Target limit: {pct}%")
    logger.info(f"✅ All steps complete - Moving to confirmation")
    
    # Show confirmation
    from bot.handlers.move.strategy.create import show_move_confirmation
    await show_move_confirmation(update, context)

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
    ]
    
