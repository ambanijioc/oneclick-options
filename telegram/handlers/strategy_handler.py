"""
Strategy management handler.
Manages straddle and strangle strategy presets.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.strategy_operations import StrategyOperations
from database.models import StrategyTypeEnum
from telegram.keyboards import get_strategy_list_keyboard, get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_straddle_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show straddle strategy presets.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        # Get strategies
        strategy_ops = StrategyOperations()
        strategies = await strategy_ops.get_strategies_by_type(
            user_id=user_id,
            strategy_type=StrategyTypeEnum.STRADDLE
        )
        
        message = "🎲 **Straddle Strategies**\n\n"
        
        if strategies:
            message += f"You have {len(strategies)} straddle strategy preset(s).\n\n"
            message += "Select an action below:"
        else:
            message += "No straddle strategies configured yet.\n\n"
            message += "Create a straddle strategy preset to get started."
        
        keyboard = get_strategy_list_keyboard(strategies, 'straddle')
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_straddle_strategies] Displayed straddle strategies for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_straddle_strategies] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error loading strategies.",
            reply_markup=get_main_menu_keyboard()
        )


@require_auth
@log_function_call
async def show_strangle_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show strangle strategy presets.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        # Get strategies
        strategy_ops = StrategyOperations()
        strategies = await strategy_ops.get_strategies_by_type(
            user_id=user_id,
            strategy_type=StrategyTypeEnum.STRANGLE
        )
        
        message = "🎯 **Strangle Strategies**\n\n"
        
        if strategies:
            message += f"You have {len(strategies)} strangle strategy preset(s).\n\n"
            message += "Select an action below:"
        else:
            message += "No strangle strategies configured yet.\n\n"
            message += "Create a strangle strategy preset to get started."
        
        keyboard = get_strategy_list_keyboard(strategies, 'strangle')
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_strangle_strategies] Displayed strangle strategies for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_strangle_strategies] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error loading strategies.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Strategy handler module loaded")
  
