"""
MOVE Auto Trade Execution Handler

Executes automated MOVE trades based on active strategies.
Handles order placement, SL/target management, and P&L tracking.
"""

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    get_move_strategies,
    get_move_strategy,
    update_move_strategy
)
from database.operations.move_trade_ops import create_move_trade
from bot.keyboards.move_trade_keyboards import get_trade_status_keyboard

logger = setup_logger(__name__)


def get_strategy_selection_keyboard(strategies, mode='auto'):
    """Build strategy selection keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    buttons = []
    for idx, strat in enumerate(strategies):
        strat_name = strat.get('strategy_name', f'Strategy {idx+1}')
        strat_id = str(strat.get('_id', strat.get('id', '')))
        callback = f"move_auto_trade_{strat_id}"
        buttons.append([
            InlineKeyboardButton(f"📊 {strat_name}", callback_data=callback)
        ])
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_trade")])
    return InlineKeyboardMarkup(buttons)


@error_handler
async def move_auto_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start MOVE auto trade execution"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Initiated MOVE auto trade")
    
    strategies = await get_move_strategies(user.id, active_only=True)
    
    if not strategies:
        await query.edit_message_text(
            "❌ No active MOVE strategies found.\n\n"
            "Please create and activate a strategy first.",
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        "📊 Select Strategy for Auto Trade\n\n"
        "Which strategy would you like to trade?",
        reply_markup=get_strategy_selection_keyboard(strategies, mode='auto'),
        parse_mode='HTML'
    )


@error_handler
async def move_auto_execute_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ FIX: Execute auto trade for selected strategy
    Callback format: move_auto_trade_{strategy_id}
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ FIX: Extract strategy_id from "move_auto_trade_{ID}"
    parts = query.data.split('_', 3)  # ['move', 'auto', 'trade', 'ID']
    strategy_id = parts[3] if len(parts) >= 4 else None
    
    logger.info(f"AUTO TRADE - callback_data: {query.data}")
    logger.info(f"AUTO TRADE - Extracted strategy_id: {strategy_id}")
    
    if not strategy_id:
        await query.edit_message_text("❌ Invalid strategy ID.")
        return
    
    strategy = await get_move_strategy(user.id, strategy_id)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Strategy not found.",
            parse_mode='HTML'
        )
        return
    
    # ✅ FIX: Validate strategy has required fields
    required_fields = ['lot_size', 'sl_trigger_percent', 'sl_limit_percent']
    missing = [f for f in required_fields if f not in strategy or strategy[f] is None]
    
    if missing:
        await query.edit_message_text(
            f"❌ Strategy incomplete. Missing: {', '.join(missing)}\n\n"
            f"Please edit strategy before trading.",
            parse_mode='HTML'
        )
        return
    
    # ✅ FIX: Create trade record
    try:
        trade_data = {
            'strategy_id': strategy_id,
            'entry_price': None,
            'entry_time': datetime.now().isoformat(),
            'lot_size': strategy['lot_size'],
            'sl_trigger': strategy['sl_trigger_percent'],
            'sl_limit': strategy['sl_limit_percent'],
            'target_trigger': strategy.get('target_trigger_percent'),
            'target_limit': strategy.get('target_limit_percent'),
            'status': 'PENDING',
            'pnl': 0
        }
        
        trade_id = await create_move_trade(user.id, trade_data)
        
        if not trade_id:
            raise Exception("Failed to create trade record")
        
        # ✅ FIX: Update strategy as trading
        await update_move_strategy(user.id, strategy_id, {
            'last_traded': datetime.now().isoformat(),
            'active_trades': (strategy.get('active_trades', 0) or 0) + 1
        })
        
        strategy_name = strategy.get('strategy_name', 'Unknown')
        
        await query.edit_message_text(
            f"✅ Auto Trade Initiated\n\n"
            f"<b>Strategy:</b> {strategy_name}\n"
            f"<b>Trade ID:</b> {trade_id}\n"
            f"<b>Lot Size:</b> {strategy['lot_size']}\n"
            f"<b>SL Trigger:</b> {strategy['sl_trigger_percent']}%\n\n"
            f"📊 Trade will execute at market open.",
            reply_markup=get_trade_status_keyboard(trade_id),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, f"Executed auto trade for strategy: {strategy_name}")
        
    except Exception as e:
        logger.error(f"Auto trade execution failed: {str(e)}")
        await query.edit_message_text(
            f"❌ Trade execution failed: {str(e)}",
            parse_mode='HTML'
        )


async def register_move_auto_trade_handlers(application):
    """
    ✅ REQUIRED EXPORT: Register all MOVE auto trade handlers
    This is the function imported by __init__.py
    """
    try:
        from telegram.ext import CallbackQueryHandler
        
        logger.info("Registering MOVE auto trade handlers...")
        
        # Register main auto trade callback
        application.add_handler(
            CallbackQueryHandler(move_auto_trade_callback, pattern="^move_auto_trade$")
        )
        
        # Register strategy selection callback
        application.add_handler(
            CallbackQueryHandler(move_auto_execute_trade_callback, pattern="^move_auto_trade_")
        )
        
        logger.info("✅ MOVE auto trade handlers registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering auto trade handlers: {e}")
        return False


# ✅ REQUIRED EXPORTS
__all__ = [
    'register_move_auto_trade_handlers',
    'move_auto_trade_callback',
    'move_auto_execute_trade_callback',
    'get_strategy_selection_keyboard',
]
