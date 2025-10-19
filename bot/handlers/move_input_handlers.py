"""
Input handlers for MOVE strategy creation/editing flow.
Handles text input during strategy creation with proper state management.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager

logger = setup_logger(__name__)


async def handle_move_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle MOVE strategy name input."""
    user = update.effective_user
    
    # Store strategy name
    await state_manager.set_state_data(user.id, {
        'name': text,
        'strategy_type': 'move'
    })
    
    logger.info(f"✅ MOVE name stored: {text}")
    
    # Move to description state
    await state_manager.set_state(user.id, 'move_add_description')
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="move_skip_description")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    await update.message.reply_text(
        f"<b>📝 Add MOVE Strategy</b>\n\n"
        f"<b>Name:</b> {text}\n\n"
        f"<b>Enter description</b> (optional):",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_move_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle MOVE strategy description input."""
    user = update.effective_user
    
    # Store description
    await state_manager.set_state_data(user.id, {'description': text})
    
    logger.info(f"✅ MOVE description stored: {text[:50]}")
    
    # Move to asset selection state
    await state_manager.set_state(user.id, 'move_add_asset')
    
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_asset_BTC")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_asset_ETH")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    data = await state_manager.get_state_data(user.id)
    
    await update.message.reply_text(
        f"<b>📝 Add MOVE Strategy</b>\n\n"
        f"<b>Name:</b> {data.get('name')}\n"
        f"<b>Description:</b> {text}\n\n"
        f"<b>Select asset:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle ATM offset input (strike selection method)."""
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        
        if not (-10 <= atm_offset <= 10):
            raise ValueError("ATM offset must be between -10 and 10")
        
        # Store ATM offset
        await state_manager.set_state_data(user.id, {'atm_offset': atm_offset})
        
        logger.info(f"✅ MOVE ATM offset stored: {atm_offset}")
        
        # Move to SL trigger state
        await state_manager.set_state(user.id, 'move_add_sl_trigger')
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        data = await state_manager.get_state_data(user.id)
        
        await update.message.reply_text(
            f"<b>📝 Add MOVE Strategy</b>\n\n"
            f"<b>Name:</b> {data.get('name')}\n"
            f"<b>Asset:</b> {data.get('asset')}\n"
            f"<b>Expiry:</b> {data.get('expiry')}\n"
            f"<b>Direction:</b> {data.get('direction')}\n"
            f"<b>ATM Offset:</b> {atm_offset}\n\n"
            f"<b>Enter SL trigger % (e.g., 30 for 30%):</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"❌ Invalid ATM offset: {str(e)}\n\n"
            f"Please enter a number between -10 and 10:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle SL trigger % input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        
        if not (1 <= sl_trigger <= 200):
            raise ValueError("SL trigger must be between 1% and 200%")
        
        # Store SL trigger
        await state_manager.set_state_data(user.id, {'sl_trigger_percent': sl_trigger})
        
        logger.info(f"✅ MOVE SL trigger stored: {sl_trigger}%")
        
        # Move to SL limit state
        await state_manager.set_state(user.id, 'move_add_sl_limit')
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>📝 Add MOVE Strategy</b>\n\n"
            f"<b>SL Trigger:</b> {sl_trigger}%\n\n"
            f"<b>Enter SL limit % (e.g., 35 for 35%):</b>\n\n"
            f"<i>💡 Tip: SL limit should be >= SL trigger</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"❌ Invalid SL trigger: {str(e)}\n\n"
            f"Please enter a number between 1 and 200:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle SL limit % input."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        
        data = await state_manager.get_state_data(user.id)
        sl_trigger = data.get('sl_trigger_percent', 0)
        
        if not (1 <= sl_limit <= 200):
            raise ValueError("SL limit must be between 1% and 200%")
        
        if sl_limit < sl_trigger:
            raise ValueError(f"SL limit ({sl_limit}%) must be >= SL trigger ({sl_trigger}%)")
        
        # Store SL limit
        await state_manager.set_state_data(user.id, {'sl_limit_percent': sl_limit})
        
        logger.info(f"✅ MOVE SL limit stored: {sl_limit}%")
        
        # Move to target trigger state
        await state_manager.set_state(user.id, 'move_add_target_trigger')
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target", callback_data="move_skip_target")],
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>📝 Add MOVE Strategy</b>\n\n"
            f"<b>SL Trigger:</b> {sl_trigger}%\n"
            f"<b>SL Limit:</b> {sl_limit}%\n\n"
            f"<b>Enter target trigger % (optional, e.g., -20 for -20%):</b>\n\n"
            f"<i>💡 Tip: Use negative values for profit targets</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"❌ Invalid SL limit: {str(e)}\n\n"
            f"Please enter a valid number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target trigger % input."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        
        if not (-200 <= target_trigger <= 0):
            raise ValueError("Target trigger must be between -200% and 0%")
        
        # Store target trigger
        await state_manager.set_state_data(user.id, {'target_trigger_percent': target_trigger})
        
        logger.info(f"✅ MOVE target trigger stored: {target_trigger}%")
        
        # Move to target limit state
        await state_manager.set_state(user.id, 'move_add_target_limit')
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>📝 Add MOVE Strategy</b>\n\n"
            f"<b>Target Trigger:</b> {target_trigger}%\n\n"
            f"<b>Enter target limit % (e.g., -25 for -25%):</b>\n\n"
            f"<i>💡 Tip: Target limit should be <= target trigger</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"❌ Invalid target trigger: {str(e)}\n\n"
            f"Please enter a number between -200 and 0:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def handle_move_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target limit % input - FINAL STEP."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        
        data = await state_manager.get_state_data(user.id)
        target_trigger = data.get('target_trigger_percent', 0)
        
        if not (-200 <= target_limit <= 0):
            raise ValueError("Target limit must be between -200% and 0%")
        
        if target_limit > target_trigger:
            raise ValueError(f"Target limit ({target_limit}%) must be <= target trigger ({target_trigger}%)")
        
        # Store target limit
        await state_manager.set_state_data(user.id, {'target_limit_percent': target_limit})
        
        logger.info(f"✅ MOVE target limit stored: {target_limit}%")
        
        # Trigger final confirmation
        from .move_strategy_handler import show_move_confirmation
        await show_move_confirmation(update, context)
    
    except ValueError as e:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"❌ Invalid target limit: {str(e)}\n\n"
            f"Please enter a valid number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


# ==================== EDIT HANDLERS ====================

async def handle_move_edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing MOVE strategy name."""
    user = update.effective_user
    
    # Store new name
    await state_manager.set_state_data(user.id, {'edit_name': text})
    
    logger.info(f"✅ MOVE edit name stored: {text}")
    
    # Trigger save
    from .move_strategy_handler import save_move_edit
    await save_move_edit(update, context)


async def handle_move_edit_desc_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing MOVE strategy description."""
    user = update.effective_user
    
    # Store new description
    await state_manager.set_state_data(user.id, {'edit_description': text})
    
    logger.info(f"✅ MOVE edit description stored")
    
    # Trigger save
    from .move_strategy_handler import save_move_edit
    await save_move_edit(update, context)


async def handle_move_edit_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing ATM offset."""
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        
        if not (-10 <= atm_offset <= 10):
            raise ValueError("ATM offset must be between -10 and 10")
        
        await state_manager.set_state_data(user.id, {'edit_atm_offset': atm_offset})
        
        logger.info(f"✅ MOVE edit ATM offset stored: {atm_offset}")
        
        from .move_strategy_handler import save_move_edit
        await save_move_edit(update, context)
    
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid ATM offset: {str(e)}\n\n"
            f"Please enter a number between -10 and 10:",
            parse_mode='HTML'
        )


async def handle_move_edit_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing SL trigger %."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        
        if not (1 <= sl_trigger <= 200):
            raise ValueError("SL trigger must be between 1% and 200%")
        
        await state_manager.set_state_data(user.id, {'edit_sl_trigger': sl_trigger})
        
        logger.info(f"✅ MOVE edit SL trigger stored: {sl_trigger}%")
        
        from .move_strategy_handler import save_move_edit
        await save_move_edit(update, context)
    
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid SL trigger: {str(e)}\n\n"
            f"Please enter a number between 1 and 200:",
            parse_mode='HTML'
        )


async def handle_move_edit_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing SL limit %."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        
        if not (1 <= sl_limit <= 200):
            raise ValueError("SL limit must be between 1% and 200%")
        
        await state_manager.set_state_data(user.id, {'edit_sl_limit': sl_limit})
        
        logger.info(f"✅ MOVE edit SL limit stored: {sl_limit}%")
        
        from .move_strategy_handler import save_move_edit
        await save_move_edit(update, context)
    
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid SL limit: {str(e)}\n\n"
            f"Please enter a number between 1 and 200:",
            parse_mode='HTML'
        )


async def handle_move_edit_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing target trigger %."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        
        if not (-200 <= target_trigger <= 0):
            raise ValueError("Target trigger must be between -200% and 0%")
        
        await state_manager.set_state_data(user.id, {'edit_target_trigger': target_trigger})
        
        logger.info(f"✅ MOVE edit target trigger stored: {target_trigger}%")
        
        from .move_strategy_handler import save_move_edit
        await save_move_edit(update, context)
    
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid target trigger: {str(e)}\n\n"
            f"Please enter a number between -200 and 0:",
            parse_mode='HTML'
        )


async def handle_move_edit_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing target limit %."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        
        if not (-200 <= target_limit <= 0):
            raise ValueError("Target limit must be between -200% and 0%")
        
        await state_manager.set_state_data(user.id, {'edit_target_limit': target_limit})
        
        logger.info(f"✅ MOVE edit target limit stored: {target_limit}%")
        
        from .move_strategy_handler import save_move_edit
        await save_move_edit(update, context)
    
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid target limit: {str(e)}\n\n"
            f"Please enter a number between -200 and 0:",
            parse_mode='HTML'
    )
    
