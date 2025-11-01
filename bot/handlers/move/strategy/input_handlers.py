"""
MOVE Strategy Input Handlers - FIXED & UNIFIED
Handles text input for MOVE strategy creation flows with shorthand support
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
    """
    ✅ RELAXED validation - supports common trading symbols
    Allowed: letters, numbers, spaces, hyphens, underscores, %, @, &, #, :, /, ()
    """
    name = name.strip()
    
    if not name:
        return False, "Name cannot be empty"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    # ✅ RELAXED: Allow these characters
    if not re.match(r"^[a-zA-Z0-9\s\-_#@&:%/.()]+$", name):
        return False, (
            "❌ Invalid characters found!\n\n"
            "✅ Allowed: letters, numbers, spaces,\n"
            "hyphens (-), underscores (_), %, @, &, #, :, /, (), .\n\n"
            "Try: 'BTC 8AM 25%' or 'Morning Move Strategy'"
        )
    
    return True, ""

def validate_lot_size(value: str) -> tuple[bool, str, int]:
    """Validate lot size input"""
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

def validate_percentage(value: str, field_name: str = "Percentage") -> tuple[bool, str, float]:
    """Validate percentage inputs (0-100)"""
    try:
        pct = float(value.strip())
        if pct < 0 or pct > 100:
            return False, f"{field_name} must be between 0 and 100", 0
        return True, "", pct
    except ValueError:
        return False, f"{field_name} must be a number", 0

# ============ STRATEGY NAME INPUT (WITH SHORTHAND PARSER) ============

@error_handler
async def handle_move_strategy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle MOVE strategy name input - Supports both shorthand and regular names
    Shorthand format: "ASSET TIME% PERCENTAGE%" e.g., "BTC 8AM 25%"
    """
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    logger.info(f"📥 Name input: '{text}'")
    
    # ============= PARSE SHORTHAND FORMAT =============
    shorthand_match = re.match(
        r'^([A-Z]+)\s+(\d{1,2}(?:AM|PM)?)\s+(\d+)%$',
        text,
        re.IGNORECASE
    )
    
    if shorthand_match:
        asset, time, percentage = shorthand_match.groups()
        logger.info(f"🔄 Shorthand detected: Asset={asset}, Time={time}, %={percentage}")
        
        try:
            # Parse time
            time_str = time.upper()
            if not time_str.endswith(('AM', 'PM')):
                time_str += 'AM'
            
            # Validate percentage
            sl_percent = float(percentage)
            if sl_percent < 0 or sl_percent > 100:
                raise ValueError("Percentage must be 0-100")
            
            # Save shorthand data - skip to asset selection
            await state_manager.set_state_data(user.id, {
                'asset': asset.upper(),
                'entry_time': time_str,
                'sl_percent': sl_percent,
                'entry_method': 'shorthand'
            })
            
            await state_manager.set_state(user.id, 'move_add_lot_size')
            logger.info("✅ Shorthand parsed, moving to lot size")
            
            await update.message.reply_text(
                f"✅ <b>Parsed Shorthand!</b>\n\n"
                f"🔹 Asset: <code>{asset.upper()}</code>\n"
                f"🔹 Entry Time: <code>{time_str}</code>\n"
                f"🔹 SL%: <code>{sl_percent}%</code>\n\n"
                f"Step 2/7: <b>Lot Size</b>\n"
                f"Enter lot size (1-1000):",
                parse_mode='HTML',
                reply_markup=get_cancel_keyboard()
            )
            return
        
        except Exception as e:
            logger.error(f"❌ Shorthand parse error: {e}")
            await update.message.reply_text(
                "❌ Invalid shorthand format!\n\n"
                "Use: <code>ASSET TIME% PERCENTAGE%</code>\n"
                "Example: <code>BTC 8AM 25%</code>\n\n"
                "Or enter a regular strategy name:",
                parse_mode='HTML',
                reply_markup=get_cancel_keyboard()
            )
            return
    
    # ============= VALIDATE REGULAR NAME =============
    valid, error = validate_strategy_name(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # ============= SAVE NAME & CONTINUE =============
    await state_manager.set_state_data(user.id, {'name': text})
    await state_manager.set_state(user.id, 'move_add_description')
    
    logger.info(f"✅ Name saved: {text}")
    
    await update.message.reply_text(
        f"✅ Strategy name saved: <code>{text}</code>\n\n"
        f"Step 2/7: <b>Description</b>\n"
        f"(Optional) Enter a description:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ LOT SIZE INPUT ============

@error_handler
async def handle_move_lot_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lot size input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, lot_size = validate_lot_size(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nPlease enter a valid lot size (1-1000):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'lot_size': lot_size})
    await state_manager.set_state(user.id, 'move_add_sl_trigger')
    
    log_user_action(user.id, f"Set lot size: {lot_size}")
    
    await update.message.reply_text(
        f"✅ Lot size set: {lot_size}\n\n"
        f"💰 Step 3/7: Stop Loss Setup\n\n"
        f"Enter SL Trigger percentage (0-100):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ ATM OFFSET INPUT ============

@error_handler
async def handle_move_atm_offset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ATM offset input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    valid, error, offset = validate_atm_offset(text)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {error}\n\nPlease enter a valid offset (-10 to +10):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'atm_offset': offset})
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    log_user_action(user.id, f"Set ATM offset: {offset}")
    
    await update.message.reply_text(
        f"✅ ATM offset set: {offset:+d}\n\n"
        f"📊 Step 4/7: Lot Size\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ============ SL INPUTS ============

@error_handler
async def handle_move_sl_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL trigger percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
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
    
    await state_manager.set_state_data(user.id, {'sl_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_sl_limit')
    
    logger.info(f"✅ User {user.id} set SL trigger: {pct}%")
    
    await update.message.reply_text(
        f"✅ SL Trigger: {pct}%\n\n"
        f"Enter SL Limit percentage:\n"
        f"(Usually lower than trigger):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_sl_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL limit percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
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
    
    await state_manager.set_state_data(user.id, {'sl_limit_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_trigger')
    
    await update.message.reply_text(
        f"✅ SL Limit: {pct}%\n\n"
        f"🎯 Target Setup\n\n"
        f"Enter Target Trigger percentage\n"
        f"(or /skip if not needed):",
        reply_markup=get_skip_target_keyboard(),
        parse_mode='HTML'
    )

# ============ TARGET INPUTS ============

@error_handler
async def handle_move_target_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target trigger percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
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
    
    await state_manager.set_state_data(user.id, {'target_trigger_percent': pct})
    await state_manager.set_state(user.id, 'move_add_target_limit')
    
    await update.message.reply_text(
        f"✅ Target Trigger: {pct}%\n\n"
        f"Enter Target Limit percentage:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def handle_move_target_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target limit percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
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
    
    await state_manager.set_state_data(user.id, {'target_limit_percent': pct})
    
    # Import and call confirmation
    from bot.handlers.move.strategy.create import show_move_confirmation
    await show_move_confirmation(update, context)

__all__ = [
    'validate_strategy_name',
    'validate_lot_size',
    'validate_atm_offset',
    'validate_percentage',
    'handle_move_strategy_name',
    'handle_move_lot_size',
    'handle_move_atm_offset',
    'handle_move_sl_trigger',
    'handle_move_sl_limit',
    'handle_move_target_trigger',
    'handle_move_target_limit',
    ]
