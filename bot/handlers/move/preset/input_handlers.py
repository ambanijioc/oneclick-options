"""
MOVE Preset Input Handlers
Handles all text input for MOVE preset creation and editing.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager
from bot.utils.error_handler import error_handler

logger = setup_logger(__name__)

@error_handler
async def handle_move_preset_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle preset name input."""
    user = update.effective_user
    
    await state_manager.set_state_data(user.id, {'name': text})
    await state_manager.set_state(user.id, 'move_preset_add_entry_lots')
    
    await update.message.reply_text(
        f"✅ Name set: {text}\n\n"
        f"Enter entry lots:"
    )

@error_handler
async def handle_move_preset_entry_lots_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle entry lots input."""
    user = update.effective_user
    
    try:
        entry_lots = int(text)
        if entry_lots < 1:
            raise ValueError("Lots must be at least 1")
        
        await state_manager.set_state_data(user.id, {'entry_lots': entry_lots})
        await state_manager.set_state(user.id, 'move_preset_add_exit_lots')
        
        await update.message.reply_text(
            f"✅ Entry lots set: {entry_lots}\n\n"
            f"Enter exit lots:"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid number.")

@error_handler
async def handle_move_preset_exit_lots_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle exit lots input."""
    user = update.effective_user
    
    try:
        exit_lots = int(text)
        if exit_lots < 1:
            raise ValueError("Lots must be at least 1")
        
        await state_manager.set_state_data(user.id, {'exit_lots': exit_lots})
        
        # Show confirmation
        from .create import show_move_preset_confirmation
        await show_move_preset_confirmation(update, context)
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}\nPlease enter a valid number.")

@error_handler
async def handle_move_preset_edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle edit preset name input."""
    pass

__all__ = [
    'handle_move_preset_name_input',
    'handle_move_preset_entry_lots_input',
    'handle_move_preset_exit_lots_input',
    'handle_move_preset_edit_name_input',
]
