"""
SL Monitor Handler - Track and manage SL-to-Cost monitoring
CREATED: 2025-10-24
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, Application
from bot.utils.error_handler import error_handler
from bot.utils.logger import setup_logger
from database.connection import get_database  # ✅ CORRECT
from bson import ObjectId

logger = setup_logger(__name__)


@error_handler
async def sl_monitor_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show SL monitor menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"User {user.id} accessed SL Monitor menu")
    
    try:
        # ✅ FIXED: Use async Motor syntax with await
        db = get_database()
        cursor = db.strategy_presets.find({"user_id": user.id})
        all_presets = await cursor.to_list(length=None)
        
        # Filter for presets with SL monitoring enabled
        monitored_presets = [
            preset for preset in all_presets 
            if preset.get('enable_sl_monitor', False)
        ]
        
        if not monitored_presets:
            keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
            await query.edit_message_text(
                "📊 <b>SL Monitor</b>\n\n"
                "❌ No strategies with SL monitoring enabled.\n\n"
                "💡 <b>How to enable:</b>\n"
                "1. Go to Straddle/Strangle Strategy\n"
                "2. Create or edit a strategy\n"
                "3. When asked \"Enable SL Monitoring?\", select ✅ Yes\n\n"
                "<i>SL Monitoring automatically moves your stop loss to cost "
                "when you hit 100% profit!</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        # Build message with all monitored strategies
        message = "📊 <b>SL Monitor - Active Strategies</b>\n\n"
        message += f"You have <b>{len(monitored_presets)}</b> "
        message += "strateg" + ("ies" if len(monitored_presets) > 1 else "y")
        message += " with SL monitoring enabled:\n\n"
        
        keyboard = []
        for idx, preset in enumerate(monitored_presets, 1):
            strategy_type = preset.get('strategy_type', 'unknown').title()
            name = preset.get('name', 'Unnamed')
            asset = preset.get('asset', 'BTC')
            
            message += f"{idx}. <b>{name}</b>\n"
            message += f"   📍 Type: {strategy_type}\n"
            message += f"   🪙 Asset: {asset}\n"
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
    user = query.from_user
    
    try:
        # Extract preset ID from callback data
        preset_id = query.data.replace("sl_monitor_detail_", "")
        
        logger.info(f"User {user.id} viewing SL monitor details for preset {preset_id}")
        
        # ✅ FIXED: Use async Motor syntax with await
        db = get_database()
        preset = await db.strategy_presets.find_one({"_id": ObjectId(preset_id)})
        
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
        message += f"• Expiry: {preset.get('expiry_code', 'N/A')}\n"
        message += f"• Lot Size: {preset.get('lot_size', 'N/A')}\n\n"
        
        message += f"<b>Stop Loss Settings:</b>\n"
        message += f"• Trigger: {preset.get('sl_trigger_pct', 'N/A')}%\n"
        message += f"• Limit: {preset.get('sl_limit_pct', 'N/A')}%\n\n"
        
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


def register_sl_monitor_handlers(application: Application):
    """Register SL monitor handlers."""
    application.add_handler(CallbackQueryHandler(sl_monitor_menu_callback, pattern="^menu_sl_monitors$"))
    application.add_handler(CallbackQueryHandler(sl_monitor_detail_callback, pattern="^sl_monitor_detail_"))
    logger.info("✓ SL monitor handlers registered")
                                       
