"""
MOVE Edit Text Input Handler

Handles all text input for editing MOVE strategies.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from database.operations.move_strategy_ops import update_move_strategy
from bot.keyboards.move_strategy_keyboards import (
    get_edit_fields_keyboard,
    get_move_menu_keyboard,
    get_cancel_keyboard
)

logger = setup_logger(__name__)


def validate_strategy_name(name: str) -> tuple[bool, str]:
    """Validate strategy name"""
    name = name.strip()
    
    if not name:
        return False, "Name cannot be empty"
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    return True, ""


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


@error_handler
async def handle_move_edit_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle all text input for MOVE strategy editing.
    Routes based on current edit state.
    """
    user = update.effective_user
    text = update.message.text.strip()
    state = await state_manager.get_state(user.id)
    data = await state_manager.get_state_data(user.id)
    
    strategy_id = data.get('editing_strategy_id')
    field = data.get('editing_field')
    
    logger.info("=" * 60)
    logger.info("🔵 MOVE EDIT TEXT INPUT - TRIGGERED")
    logger.info(f"   User: {user.id}, State: {state}")
    logger.info(f"   Field: {field}, Strategy: {strategy_id}")
    logger.info(f"   Input: {text[:50]}..." if len(text) > 50 else f"   Input: {text}")
    
    if not strategy_id or not field:
        logger.warning(f"   ❌ Edit session expired")
        await update.message.reply_text(
            "❌ Edit session expired. Please try again.",
            reply_markup=get_move_menu_keyboard()
        )
        return
    
    try:
        # EDIT NAME
        if state == 'move_edit_name':
            logger.info("   → Processing NAME edit")
            valid, error = validate_strategy_name(text)
            if not valid:
                logger.warning(f"   ❌ Validation failed: {error}")
                await update.message.reply_text(
                    f"❌ {error}\n\nEnter new name:",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'strategy_name': text})
            update_field = 'Name'
            new_value = text
        
        # EDIT DESCRIPTION
        elif state == 'move_edit_description':
            logger.info("   → Processing DESCRIPTION edit")
            if len(text) > 500:
                logger.warning(f"   ❌ Description too long")
                await update.message.reply_text(
                    "❌ Description too long (max 500 characters)\n\nEnter shorter description:",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'description': text})
            update_field = 'Description'
            new_value = text
        
        # EDIT ATM OFFSET
        elif state == 'move_edit_atm_offset':
            logger.info("   → Processing ATM_OFFSET edit")
            valid, error, offset = validate_atm_offset(text)
            if not valid:
                logger.warning(f"   ❌ Validation failed: {error}")
                await update.message.reply_text(
                    f"❌ {error}\n\nEnter ATM offset (-10 to +10):",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'atm_offset': offset})
            update_field = 'ATM Offset'
            new_value = f"{offset:+d}"
        
        # EDIT SL TRIGGER
        elif state == 'move_edit_sl_trigger':
            logger.info("   → Processing SL_TRIGGER edit")
            valid, error, pct = validate_percentage(text, "SL Trigger")
            if not valid:
                logger.warning(f"   ❌ Validation failed: {error}")
                await update.message.reply_text(
                    f"❌ {error}\n\nEnter SL Trigger % (0-100):",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'sl_trigger_percent': pct})
            update_field = 'SL Trigger'
            new_value = f"{pct}%"
        
        # EDIT SL LIMIT
        elif state == 'move_edit_sl_limit':
            logger.info("   → Processing SL_LIMIT edit")
            valid, error, pct = validate_percentage(text, "SL Limit")
            if not valid:
                logger.warning(f"   ❌ Validation failed: {error}")
                await update.message.reply_text(
                    f"❌ {error}\n\nEnter SL Limit % (0-100):",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'sl_limit_percent': pct})
            update_field = 'SL Limit'
            new_value = f"{pct}%"
        
        # EDIT TARGET TRIGGER
        elif state == 'move_edit_target_trigger':
            logger.info("   → Processing TARGET_TRIGGER edit")
            valid, error, pct = validate_percentage(text, "Target Trigger")
            if not valid:
                logger.warning(f"   ❌ Validation failed: {error}")
                await update.message.reply_text(
                    f"❌ {error}\n\nEnter Target Trigger % (0-100):",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'target_trigger_percent': pct})
            update_field = 'Target Trigger'
            new_value = f"{pct}%"
        
        # EDIT TARGET LIMIT
        elif state == 'move_edit_target_limit':
            logger.info("   → Processing TARGET_LIMIT edit")
            valid, error, pct = validate_percentage(text, "Target Limit")
            if not valid:
                logger.warning(f"   ❌ Validation failed: {error}")
                await update.message.reply_text(
                    f"❌ {error}\n\nEnter Target Limit % (0-100):",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            result = await update_move_strategy(user.id, strategy_id, {'target_limit_percent': pct})
            update_field = 'Target Limit'
            new_value = f"{pct}%"
        
        else:
            logger.warning(f"   ❌ Unknown edit state: {state}")
            await update.message.reply_text(
                "❌ Unknown edit state. Please try again.",
                reply_markup=get_move_menu_keyboard()
            )
            return
        
        # Update successful
        if result:
            logger.info(f"   ✅ Update successful")
            log_user_action(user.id, f"move_edit_{field}", f"Updated {field}: {new_value}")
            
            # Clear state
            await state_manager.set_state(user.id, None)
            await state_manager.set_state_data(user.id, {})
            
            await update.message.reply_text(
                f"✅ Strategy Updated!\n\n"
                f"<b>{update_field}</b> changed to: <code>{new_value}</code>\n\n"
                f"What else would you like to edit?",
                reply_markup=get_edit_fields_keyboard(strategy_id),
                parse_mode='HTML'
            )
            logger.info("   ✅ Edit complete, state cleared")
        else:
            logger.warning(f"   ❌ Database update failed")
            await update.message.reply_text(
                "❌ Failed to update strategy. Try again:",
                reply_markup=get_cancel_keyboard(),
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"   ❌ Error in handle_move_edit_text_input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=get_move_menu_keyboard()
        )
    finally:
        logger.info("=" * 60)


__all__ = ['handle_move_edit_text_input']
  
