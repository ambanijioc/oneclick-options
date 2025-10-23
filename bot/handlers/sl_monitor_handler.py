"""
SL Monitor Handler - Track and manage SL-to-Cost monitoring
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.error_handler import error_handler
from bot.utils.logger import log_user_action
from database.operations.trades import get_active_trades
from database.operations.strategy_preset import get_strategy_preset_by_id


@error_handler
async def sl_monitor_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show SL monitor menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Get all active trades
    active_trades = await get_active_trades(user.id)
    
    # Filter trades with SL monitoring enabled
    monitored_trades = []
    for trade in active_trades:
        # Get strategy preset
        preset = await get_strategy_preset_by_id(trade['preset_id'])
        if preset and preset.get('enable_sl_monitor', False):
            monitored_trades.append({
                'trade': trade,
                'preset': preset
            })
    
    if not monitored_trades:
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            "📊 <b>SL Monitor</b>\n\n"
            "No active trades with SL monitoring enabled.\n\n"
            "💡 <b>Tip:</b> Enable SL monitoring when creating straddle/strangle strategies.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Build message with all monitored trades
    message = "📊 <b>Active SL Monitors</b>\n\n"
    
    keyboard = []
    for idx, item in enumerate(monitored_trades, 1):
        trade = item['trade']
        preset = item['preset']
        
        # Calculate P&L
        entry_value = trade.get('entry_value', 0)
        current_value = trade.get('current_value', entry_value)
        pnl_pct = ((current_value - entry_value) / entry_value * 100) if entry_value > 0 else 0
        
        # Determine status
        sl_triggered = trade.get('sl_triggered', False)
        status_icon = "🟢" if pnl_pct >= 0 else "🔴"
        sl_status = "✅ Triggered" if sl_triggered else "⏳ Monitoring"
        
        message += f"{idx}. <b>{preset['name']}</b>\n"
        message += f"   {status_icon} P&L: <code>{pnl_pct:+.2f}%</code>\n"
        message += f"   📍 Status: {sl_status}\n"
        message += f"   🎯 Strategy: {preset['strategy_type'].title()}\n\n"
        
        # Add button to view details
        keyboard.append([
            InlineKeyboardButton(
                f"📊 {preset['name']}", 
                callback_data=f"sl_monitor_detail_{trade['_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "sl_monitor_view", f"Viewed {len(monitored_trades)} monitored trades")


@error_handler
async def sl_monitor_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed view of a specific SL monitor."""
    query = update.callback_query
    await query.answer()
    
    # Extract trade ID from callback data
    trade_id = query.data.split("_")[-1]
    
    # TODO: Implement detailed view showing:
    # - Entry price
    # - Current price
    # - SL trigger levels
    # - When SL-to-Cost was triggered (if applicable)
    # - Button to manually disable monitoring
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitors")]]
    
    await query.edit_message_text(
        f"📊 <b>Trade Details</b>\n\n"
        f"Trade ID: <code>{trade_id}</code>\n\n"
        f"(Detailed view coming soon)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
  
