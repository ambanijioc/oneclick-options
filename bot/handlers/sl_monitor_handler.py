"""
SL Monitor Handler - Track and manage SL-to-Cost monitoring
CREATED: 2025-10-24
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, Application
from bot.utils.error_handler import error_handler
from bot.utils.logger import setup_logger

# ✅ CORRECT IMPORTS - Use existing database operations
from database.connection import get_database
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
        # ✅ Query database directly
        db = get_database()
        
        # Get all strategies with SL monitoring enabled
        straddle_cursor = db.strategy_presets.find({
            'user_id': user.id,
            'strategy_type': 'straddle',
            'enable_sl_monitor': True
        })
        strangle_cursor = db.strategy_presets.find({
            'user_id': user.id,
            'strategy_type': 'strangle',
            'enable_sl_monitor': True
        })
        
        straddle_strategies = await straddle_cursor.to_list(length=100)
        strangle_strategies = await strangle_cursor.to_list(length=100)
        
        monitored_strategies = straddle_strategies + strangle_strategies
        
        if not monitored_strategies:
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
        message += f"You have <b>{len(monitored_strategies)}</b> "
        message += "strateg" + ("ies" if len(monitored_strategies) > 1 else "y")
        message += " with SL monitoring enabled:\n\n"
        
        keyboard = []
        for idx, strategy in enumerate(monitored_strategies, 1):
            strategy_type = strategy.get('strategy_type', 'unknown').title()
            name = strategy.get('name', 'Unnamed')
            asset = strategy.get('asset', 'N/A')
            
            message += f"{idx}. <b>{name}</b>\n"
            message += f"   📍 Type: {strategy_type}\n"
            message += f"   🪙 Asset: {asset}\n"
            message += f"   ✅ Status: <code>ACTIVE</code>\n\n"
            
            # Add button to view details
            keyboard.append([
                InlineKeyboardButton(
                    f"📊 {name[:30]}", 
                    callback_data=f"sl_monitor_detail_{str(strategy['_id'])}"
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
        
        logger.info(f"Displayed {len(monitored_strategies)} monitored strategies to user {user.id}")
        
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
        # Extract strategy ID from callback data
        strategy_id = query.data.replace("sl_monitor_detail_", "")
        
        logger.info(f"User {user.id} viewing SL monitor details for strategy {strategy_id}")
        
        # ✅ Query database directly
        db = get_database()
        strategy = await db.strategy_presets.find_one({'_id': ObjectId(strategy_id)})
        
        if not strategy:
            keyboard = [[InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitor")]]
            await query.edit_message_text(
                "❌ Strategy not found.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Build detailed message
        message = f"📊 <b>{strategy.get('name', 'Unnamed')}</b>\n\n"
        message += f"<b>Strategy Details:</b>\n"
        message += f"• Type: {strategy.get('strategy_type', 'N/A').title()}\n"
        message += f"• Asset: {strategy.get('asset', 'N/A')}\n"
        message += f"• Expiry: {strategy.get('expiry_code', 'N/A')}\n"
        message += f"• Direction: {strategy.get('direction', 'N/A').title()}\n"
        message += f"• Lot Size: {strategy.get('lot_size', 0)}\n\n"
        
        message += f"<b>Stop Loss Settings:</b>\n"
        message += f"• Trigger: {strategy.get('sl_trigger_pct', 0):.1f}%\n"
        message += f"• Limit: {strategy.get('sl_limit_pct', 0):.1f}%\n\n"
        
        if strategy.get('target_trigger_pct', 0) > 0:
            message += f"<b>Target Settings:</b>\n"
            message += f"• Trigger: {strategy.get('target_trigger_pct', 0):.1f}%\n"
            message += f"• Limit: {strategy.get('target_limit_pct', 0):.1f}%\n\n"
        
        message += f"<b>SL Monitor:</b>\n"
        message += f"• Status: <code>{'✅ ACTIVE' if strategy.get('enable_sl_monitor') else '❌ INACTIVE'}</code>\n"
        message += f"• Trigger Point: <b>100% Profit</b>\n"
        message += f"• Action: Move SL to cost (breakeven)\n\n"
        
        message += f"💡 <i>When this strategy reaches 100% profit, "
        message += f"the stop loss will automatically adjust to your entry price, "
        message += f"ensuring you can't lose money even if the market reverses.</i>"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitor")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in sl_monitor_detail_callback: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔙 Back to Monitors", callback_data="menu_sl_monitor")]]
        await query.edit_message_text(
            "❌ Error loading strategy details. Please try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def register_sl_monitor_handlers(application: Application):
    """Register SL monitor handlers."""
    application.add_handler(CallbackQueryHandler(
        sl_monitor_menu_callback, 
        pattern="^menu_sl_monitor$"
    ))
    application.add_handler(CallbackQueryHandler(
        sl_monitor_detail_callback, 
        pattern="^sl_monitor_detail_"
    ))
    logger.info("✓ SL monitor handlers registered")
        
