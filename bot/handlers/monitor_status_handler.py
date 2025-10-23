"""
bot/handlers/monitor_status_handler.py

Handler for checking SL monitor status.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from services.sl_monitor_service import (
    get_active_monitors,
    get_monitor_status,
    get_all_monitor_details,
    stop_strategy_monitor
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def show_monitor_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active SL monitors."""
    query = update.callback_query
    await query.answer()
    
    active = get_active_monitors()
    details = get_all_monitor_details()
    
    if not active:
        await query.edit_message_text(
            "🔍 <b>SL-to-Cost Monitors</b>\n\n"
            "No active monitors running.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="menu_main")
            ]])
        )
        return
    
    text = f"🔍 <b>Active SL Monitors</b> ({len(active)})\n\n"
    
    for strat_id in active:
        info = details[strat_id]
        
        status_emoji = {
            'running': '🟢',
            'moving_sl': '🟡',
            'completed': '✅',
            'error': '🔴',
            'stopped': '⏸️',
            'both_closed': '⚪'
        }.get(info['status'], '⚫')
        
        runtime = datetime.now() - info['started_at']
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        
        text += (
            f"{status_emoji} <b>{info['strategy_type'].upper()}</b>\n"
            f"├ ID: <code>{strat_id[-8:]}</code>\n"
            f"├ Status: {info['status']}\n"
            f"├ Checks: {info['check_count']}\n"
            f"├ Runtime: {runtime_str}\n"
            f"└ Symbols: {info['call_symbol']} / {info['put_symbol']}\n\n"
        )
    
    # Add buttons to stop individual monitors
    keyboard = []
    for strat_id in active:
        keyboard.append([
            InlineKeyboardButton(
                f"🛑 Stop {strat_id[-8:]}",
                callback_data=f"monitor_stop_{strat_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="monitor_status")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def stop_monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop a specific monitor."""
    query = update.callback_query
    await query.answer()
    
    # Extract strategy_id from callback data
    strategy_id = query.data.replace('monitor_stop_', '')
    
    # Stop the monitor
    stop_strategy_monitor(strategy_id)
    
    await query.answer("🛑 Monitor stopped", show_alert=True)
    
    # Refresh the status display
    await show_monitor_status_callback(update, context)
    
