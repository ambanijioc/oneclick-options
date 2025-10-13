"""
Automated trade execution handler.
Manages scheduled automatic executions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from scheduler.job_scheduler import get_scheduler
from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_auto_trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show auto trade execution menu.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        # Get scheduler
        scheduler = get_scheduler()
        schedules = await scheduler.get_user_schedules(user_id)
        
        message = "⏰ **Auto Trade Execution**\n\n"
        
        if schedules:
            message += f"You have {len(schedules)} active schedule(s):\n\n"
            
            for schedule in schedules[:5]:
                schedule_name = schedule.get('schedule_name', 'Unknown')
                execution_time = schedule.get('execution_time', 'Unknown')
                strategy_name = schedule.get('strategy_name', 'Unknown')
                
                message += f"• **{schedule_name}**\n"
                message += f"  Time: {execution_time}\n"
                message += f"  Strategy: {strategy_name}\n\n"
        else:
            message += "No active schedules.\n\n"
        
        message += "Use the buttons below to manage schedules.\n\n"
        message += "This feature is coming soon!"
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_auto_trade_menu] Displayed auto trade menu for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_auto_trade_menu] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error showing auto trade menu.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Auto trade handler module loaded")
  
