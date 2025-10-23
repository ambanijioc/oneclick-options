"""
SL Monitor Handler - Track and manage SL-to-Cost monitoring
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.utils.error_handler import error_handler
from bot.utils.logger import log_user_action, setup_logger
from database.operations.strategy_preset import get_all_strategy_presets

logger = setup_logger(__name__)


@error_handler
async def sl_monitor_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show SL monitor menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    try:
        # Get all strategy presets with SL monitoring enabled
        all_presets = await get_all_strategy_presets(user.id)
        
        # Filter for presets with SL monitoring enabled
        monitored_presets = [
            preset for preset in all_presets 
            if preset.get('enable_sl_monitor', False) and preset.get('is_active', True)
        ]
        
        if not monitored_presets:
            keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
            await query.edit_message_text(
                "📊 <b>SL Monitor</b>\n\n"
                "❌ No active strategies with SL monitoring enabled.\n\n"
                "💡 <b>Tip:</b> Enable SL monitoring when creating straddle/strangle strategies "
                "to automatically move your stop loss to cost when you hit 100% profit.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        # Build message with all monitored strategies
        message = "📊 <b>SL Monitor - Active Strategies</b>\n\n"
        message += f"You have <b>{len(monitored_presets)}</b> strateg"
        message += "ies" if len(monitored_presets) > 1 else "y"
        message += " with SL monitoring enabled:\n\n"
        
        keyboard = []
        for idx, preset in enumerate(monitored_presets, 1):
            strategy_type = preset.get('strategy_type', 'unknown').title()
            name = preset.get('name', 'Unnamed')
            asset = preset.get('asset', 'BTC')
            direction = preset.get('direction', 'long').upper()
            
            message += f"{idx}. <b>{name}</b>\n"
            message += f"   📍 Type: {strategy_type}\n"
            message += f"   🪙 Asset: {asset}\n"
            message += f"   📈 Direction: {direction}\n"
            message += f"   ✅ SL Monitor: <code>ACTIVE</code>\n\n"
            
            # Add button to view details
            keyboard.append([
                InlineKeyboardButton(
                    f"📊 {name[:30]}", 
                    callback_data=f"sl_monitor_detail_{preset['_id']}"
                )
            ])
        
        message += "\n💡 <b>How it works:</b>\n"
        message += "When your strategy hits <b>100% profit</b>, the stop loss will automatically "
        message += "move to your entry price (cost), locking in breakeven and protecting your gains."
        
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, "sl_monitor_view", f"Viewed {len(monitored_presets)} monitored strategies")
        
    except Exception as e:
        logger.error(f"Error in sl_monitor_menu_callback: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            "❌ Error loading SL monitors. Please try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


@error_handler
async def sl_monitor_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed view of a specific SL monitor."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract preset ID from callback data
        preset_id = query.data.replace("sl_monitor_detail_", "")
        
        # Get preset details
        from database.operations.strategy_preset import get_strategy_preset_by_id
        preset = await get_strategy_preset_by_id(preset_id)
        
        if not preset:
            keyboard = [[InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitors")]]
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Build detailed message
        message = f"📊 <b>{preset['name']}</b>\n\n"
        message += f"<b>Strategy Details:</b>\n"
        message += f"• Type: {preset['strategy_type'].title()}\n"
        message += f"• Asset: {preset['asset']}\n"
        message += f"• Direction: {preset['direction'].upper()}\n"
        message += f"• Expiry: {preset['expiry_code']}\n"
        message += f"• Lot Size: {preset['lot_size']}\n\n"
        
        message += f"<b>Stop Loss Settings:</b>\n"
        message += f"• Trigger: {preset['sl_trigger_pct']}%\n"
        message += f"• Limit: {preset['sl_limit_pct']}%\n\n"
        
        message += f"<b>SL Monitor:</b>\n"
        message += f"• Status: <code>{'✅ ACTIVE' if preset.get('enable_sl_monitor', False) else '❌ INACTIVE'}</code>\n"
        message += f"• Trigger Point: <b>100% Profit</b>\n"
        message += f"• Action: Move SL to cost (breakeven)\n\n"
        
        message += f"💡 <i>When this strategy reaches 100% profit, "
        message += f"the stop loss will automatically adjust to your entry price, "
        message += f"ensuring you can't lose money even if the market reverses.</i>"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitors")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in sl_monitor_detail_callback: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitors")]]
        await query.edit_message_text(
            "❌ Error loading strategy details. Please try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def register_sl_monitor_handlers(application):
    """Register SL monitor handlers."""
    application.add_handler(CallbackQueryHandler(sl_monitor_menu_callback, pattern="^menu_sl_monitors$"))
    application.add_handler(CallbackQueryHandler(sl_monitor_detail_callback, pattern="^sl_monitor_detail_"))
    logger.info("✓ SL monitor handlers registered")
            
