"""
MOVE Preset Input Handlers
Text input processing for preset creation and editing.
Uses centralized state machine routing.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_preset_ops import create_move_preset, update_move_preset

logger = setup_logger(__name__)


# ============ VALIDATORS ============

def validate_preset_name(name: str) -> tuple[bool, str]:
    """Validate preset name (3-50 chars)"""
    name = name.strip()
    if not name or len(name) < 3 or len(name) > 50:
        return False, "Name must be 3-50 characters"
    return True, ""


def validate_description(desc: str) -> tuple[bool, str]:
    """Validate description (optional, max 200 chars)"""
    desc = desc.strip()
    if len(desc) > 200:
        return False, "Description max 200 characters"
    return True, ""


def validate_percentage(value: str, field_name: str = "Value") -> tuple[bool, str, float]:
    """Validate percentage (0-100)"""
    try:
        pct = float(value.strip())
        if pct < 0 or pct > 100:
            return False, f"{field_name} must be 0-100", 0
        return True, "", pct
    except ValueError:
        return False, f"{field_name} must be a number", 0


# ============ ADD PRESET FLOW ============

@error_handler
async def handle_preset_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add Preset: Name input - Step 1"""
    user = update.effective_user
    text = update.message.text.strip()
    
    logger.info(f"🟢 PRESET NAME INPUT - User {user.id}")
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_add_name':
        return
    
    valid, error = validate_preset_name(text)
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(
            f"❌ {error}\n\nTry again:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'preset_name': text})
    await state_manager.set_state(user.id, 'move_preset_add_description')
    
    logger.info(f"✓ Preset name saved: {text}")
    
    from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
    await update.message.reply_text(
        f"✅ <b>Name:</b> {text}\n\n"
        f"<b>Step 2/2: Description (Optional)</b>\n\n"
        f"Enter description or type 'skip':",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def handle_preset_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add Preset: Description input - Step 2 (Optional)"""
    user = update.effective_user
    text = update.message.text.strip().lower()
    
    logger.info(f"🟠 PRESET DESCRIPTION INPUT - User {user.id}")
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_add_description':
        return
    
    # Skip description
    if text == 'skip':
        logger.info(f"Description skipped")
        await state_manager.set_state_data(user.id, {'preset_description': None})
    else:
        valid, error = validate_description(text)
        if not valid:
            from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
            await update.message.reply_text(
                f"❌ {error}\n\nTry again or type 'skip':",
                reply_markup=get_cancel_keyboard(),
            )
            return
        
        await state_manager.set_state_data(user.id, {'preset_description': text})
    
    # Move to confirmation (API selection happens via callback)
    await state_manager.set_state(user.id, 'move_preset_ready')
    logger.info(f"✓ Preset description saved")
    
    from bot.keyboards.move_preset_keyboards import get_preset_confirmation_keyboard
    await update.message.reply_text(
        "✅ <b>Ready to save preset!</b>\n\n"
        "Confirm to proceed:",
        reply_markup=get_preset_confirmation_keyboard(),
        parse_mode='HTML'
    )


# ============ EDIT PRESET FLOW ============

@error_handler
async def handle_preset_edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit Preset: Name field"""
    user = update.effective_user
    text = update.message.text.strip()
    
    logger.info(f"🟡 EDIT PRESET NAME - User {user.id}")
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_edit_name':
        return
    
    valid, error = validate_preset_name(text)
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(f"❌ {error}", reply_markup=get_cancel_keyboard())
        return
    
    data = await state_manager.get_state_data(user.id)
    data['preset_name'] = text
    await state_manager.set_state_data(user.id, data)
    
    logger.info(f"✓ Preset name updated")
    
    from bot.keyboards.move_preset_keyboards import get_preset_edit_options_keyboard
    await update.message.reply_text(
        f"✅ <b>Name updated:</b> {text}\n\n"
        "Select next field to edit:",
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def handle_preset_edit_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit Preset: Description field"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_edit_description':
        return
    
    valid, error = validate_description(text)
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(f"❌ {error}", reply_markup=get_cancel_keyboard())
        return
    
    data = await state_manager.get_state_data(user.id)
    data['preset_description'] = text
    await state_manager.set_state_data(user.id, data)
    
    from bot.keyboards.move_preset_keyboards import get_preset_edit_options_keyboard
    await update.message.reply_text(
        f"✅ <b>Description updated</b>\n\n"
        "Select next field to edit:",
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def handle_preset_edit_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit Preset: SL Trigger"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_edit_sl_trigger':
        return
    
    valid, error, pct = validate_percentage(text, "SL Trigger")
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(f"❌ {error}", reply_markup=get_cancel_keyboard())
        return
    
    data = await state_manager.get_state_data(user.id)
    data['sl_trigger_percent'] = pct
    await state_manager.set_state_data(user.id, data)
    
    from bot.keyboards.move_preset_keyboards import get_preset_edit_options_keyboard
    await update.message.reply_text(
        f"✅ <b>SL Trigger updated:</b> {pct}%\n\n"
        "Select next field:",
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def handle_preset_edit_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit Preset: SL Limit"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_edit_sl_limit':
        return
    
    valid, error, pct = validate_percentage(text, "SL Limit")
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(f"❌ {error}", reply_markup=get_cancel_keyboard())
        return
    
    data = await state_manager.get_state_data(user.id)
    data['sl_limit_percent'] = pct
    await state_manager.set_state_data(user.id, data)
    
    from bot.keyboards.move_preset_keyboards import get_preset_edit_options_keyboard
    await update.message.reply_text(
        f"✅ <b>SL Limit updated:</b> {pct}%\n\n"
        "Select next field:",
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def handle_preset_edit_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit Preset: Target Trigger"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_edit_target_trigger':
        return
    
    valid, error, pct = validate_percentage(text, "Target Trigger")
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(f"❌ {error}", reply_markup=get_cancel_keyboard())
        return
    
    data = await state_manager.get_state_data(user.id)
    data['target_trigger_percent'] = pct
    await state_manager.set_state_data(user.id, data)
    
    from bot.keyboards.move_preset_keyboards import get_preset_edit_options_keyboard
    await update.message.reply_text(
        f"✅ <b>Target Trigger updated:</b> {pct}%\n\n"
        "Select next field:",
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def handle_preset_edit_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit Preset: Target Limit"""
    user = update.effective_user
    text = update.message.text.strip()
    
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_edit_target_limit':
        return
    
    valid, error, pct = validate_percentage(text, "Target Limit")
    if not valid:
        from bot.keyboards.move_preset_keyboards import get_cancel_keyboard
        await update.message.reply_text(f"❌ {error}", reply_markup=get_cancel_keyboard())
        return
    
    data = await state_manager.get_state_data(user.id)
    data['target_limit_percent'] = pct
    await state_manager.set_state_data(user.id, data)
    
    from bot.keyboards.move_preset_keyboards import get_preset_edit_options_keyboard
    await update.message.reply_text(
        f"✅ <b>Target Limit updated:</b> {pct}%\n\n"
        "Select next field:",
        reply_markup=get_preset_edit_options_keyboard(),
        parse_mode='HTML'
    )


# ============ MESSAGE ROUTER ============

@error_handler
async def route_move_preset_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central router for all MOVE preset text input"""
    
    user = update.effective_user
    current_state = await state_manager.get_state(user.id)
    
    logger.info(f"📨 PRESET ROUTER: User {user.id}, State: {current_state}")
    
    try:
        if current_state == 'move_preset_add_name':
            await handle_preset_name_input(update, context)
        elif current_state == 'move_preset_add_description':
            await handle_preset_description_input(update, context)
        elif current_state == 'move_preset_edit_name':
            await handle_preset_edit_name_input(update, context)
        elif current_state == 'move_preset_edit_description':
            await handle_preset_edit_description_input(update, context)
        elif current_state == 'move_preset_edit_sl_trigger':
            await handle_preset_edit_sl_trigger_input(update, context)
        elif current_state == 'move_preset_edit_sl_limit':
            await handle_preset_edit_sl_limit_input(update, context)
        elif current_state == 'move_preset_edit_target_trigger':
            await handle_preset_edit_target_trigger_input(update, context)
        elif current_state == 'move_preset_edit_target_limit':
            await handle_preset_edit_target_limit_input(update, context)
        else:
            logger.debug(f"⏭️ No routing for preset state: {current_state}")
            
    except Exception as e:
        logger.error(f"❌ Error in preset router: {e}", exc_info=True)
        await update.message.reply_text("❌ Error processing input")


__all__ = [
    'route_move_preset_message',
    'handle_preset_name_input',
    'handle_preset_description_input',
    'handle_preset_edit_name_input',
    'handle_preset_edit_description_input',
    'handle_preset_edit_sl_trigger_input',
    'handle_preset_edit_sl_limit_input',
    'handle_preset_edit_target_trigger_input',
    'handle_preset_edit_target_limit_input',
        ]
