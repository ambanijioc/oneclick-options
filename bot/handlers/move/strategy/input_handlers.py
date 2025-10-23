"""
MOVE Strategy Input Handlers
Handles all text input for MOVE strategy creation and editing.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager
from bot.utils.error_handler import error_handler
from bot.keyboards.move_strategy_keyboards import (
    get_asset_keyboard,
    get_description_skip_keyboard,
    get_skip_target_keyboard,
    get_cancel_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def handle_move_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strategy name input."""
    user = update.effective_user
    
    await state_manager.set_state_data(user.id, {'name': text})
    await state_manager.set_state(user.id, 'move_add_description')
    
    await update.message.reply_text(
        f"✅ Name set: {text}\n\n"
        f"Now enter a description (or /skip):"
    )

@error_handler
async def handle_move_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strategy description input."""
    user = update.effective_user
    
    # Handle /skip command
    if text.lower() == '/skip':
        description = "No description provided"
    else:
        description = text
    
    await state_manager.set_state_data(user.id, {'description': description})
    await state_manager.set_state(user.id, 'move_add_asset')
    
    # Show asset selection keyboard
    await update.message.reply_text(
        f"✅ Description set.\n\n"
        f"Select asset:",
        reply_markup=get_asset_keyboard()
    )

@error_handler
async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle ATM offset input."""
    user = update.effective_user
    
    try:
        atm_offset = float(text)
        
        await state_manager.set_state_data(user.id, {'atm_offset': atm_offset})
        await state_manager.set_state(user.id, 'move_add_sl_trigger')
        
        await update.message.reply_text(
            f"✅ ATM offset set: {atm_offset}\n\n"
            f"Enter Stop Loss trigger percentage:"
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please try again.")
        
@error_handler
async def handle_move_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle lot size input."""
    user = update.effective_user
    
    try:
        lot_size = int(text)
        if lot_size < 1 or lot_size > 100:
            raise ValueError("Lot size must be between 1 and 100")
        
        await state_manager.set_state_data(user.id, {'lot_size': lot_size})
        await state_manager.set_state(user.id, 'move_add_otm_value')
        
        await update.message.reply_text(
            f"✅ Lot size set: {lot_size}\n\n"
            f"Enter OTM offset value:"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid number.")

@error_handler
async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle SL trigger input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        await state_manager.set_state_data(user.id, {'sl_trigger_pct': sl_trigger})
        await state_manager.set_state(user.id, 'move_add_sl_limit')
        
        await update.message.reply_text(
            f"✅ SL Trigger set: {sl_trigger}%\n\n"
            f"Enter Stop Loss limit percentage:"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid percentage.")

@error_handler
async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle SL limit input."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        await state_manager.set_state_data(user.id, {'sl_limit_pct': sl_limit})
        await state_manager.set_state(user.id, 'move_add_target_trigger')
        
        await update.message.reply_text(
            f"✅ SL Limit set: {sl_limit}%\n\n"
            f"Enter Target trigger percentage (or /skip):"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid percentage.")

@error_handler
async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target trigger input."""
    user = update.effective_user
    
    # Handle /skip command
    if text.lower() == '/skip':
        await state_manager.set_state_data(user.id, {
            'target_trigger_pct': None,
            'target_limit_pct': None
        })
        
        # Show confirmation
        from .create import show_move_confirmation
        await show_move_confirmation(update, context)
        return
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        await state_manager.set_state_data(user.id, {'target_trigger_pct': target_trigger})
        await state_manager.set_state(user.id, 'move_add_target_limit')
        
        await update.message.reply_text(
            f"✅ Target Trigger set: {target_trigger}%\n\n"
            f"Enter Target limit percentage:"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid percentage.")

@error_handler
async def handle_move_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target limit input."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        await state_manager.set_state_data(user.id, {'target_limit_pct': target_limit})
        
        # Show confirmation
        from .create import show_move_confirmation
        await show_move_confirmation(update, context)
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid percentage.")

# Edit Handlers
@error_handler
async def handle_move_edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle edit name input."""
    # Implementation similar to create
    pass

@error_handler
async def handle_move_edit_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle edit description input."""
    pass

@error_handler
async def handle_move_edit_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle edit lot size input."""
    pass

__all__ = [
'handle_move_name_input',              # Step 1: Name
    'handle_move_description_input',       # Step 2: Description
    'handle_move_lot_size_input',          # Step 6: Lot Size ✅ KEEP
    'handle_move_atm_offset_input',        # Step 7: ATM Offset ✅ KEEP
    # 'handle_move_otm_value_input',       # ❌ DELETE - Not used in MOVE
    'handle_move_sl_trigger_input',        # Step 8: SL Trigger
    'handle_move_sl_limit_input',          # Step 9: SL Limit  
    'handle_move_target_trigger_input',    # Step 10: Target Trigger
    'handle_move_target_limit_input',      # Step 11: Target Limit
    'handle_move_edit_name_input',         # Edit handlers
    'handle_move_edit_description_input',
    'handle_move_edit_lot_size_input',
]
