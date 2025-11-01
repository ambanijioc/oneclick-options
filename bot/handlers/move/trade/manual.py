"""
MOVE Manual Trade Execution Handler

Handles manual trade entry, exit, and P&L calculations.
"""

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import get_move_strategy
from database.operations.move_trade_ops import create_move_trade, update_move_trade
from bot.keyboards.move_trade_keyboards import get_trade_menu_keyboard

logger = setup_logger(__name__)


@error_handler
async def move_manual_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start MOVE manual trade entry"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started MOVE manual trade")
    
    # Set initial state
    await state_manager.set_state(user.id, 'move_manual_entry_price')
    
    await query.edit_message_text(
        "📝 Manual MOVE Trade Entry\n\n"
        "Step 1/6: Entry Price\n\n"
        "Enter the entry price:",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_manual_entry_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual trade entry price"""
    user = update.effective_user
    
    # Check if user is in this state
    state = await state_manager.get_state(user.id)
    if state != 'move_manual_entry_price':
        return  # Not for us
    
    text = update.message.text.strip()
    
    try:
        entry_price = float(text)
        if entry_price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, TypeError):
        await update.message.reply_text("❌ Please enter a valid price")
        return
    
    await state_manager.set_state_data(user.id, {'entry_price': entry_price})
    await state_manager.set_state(user.id, 'move_manual_lot_size')
    
    await update.message.reply_text(
        f"✅ Entry Price: {entry_price}\n\n"
        f"Step 2/6: Lot Size\n\n"
        f"Enter lot size (1-1000):",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_manual_lot_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual lot size"""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_manual_lot_size':
        return
    
    text = update.message.text.strip()
    
    try:
        lot_size = int(text)
        if not (1 <= lot_size <= 1000):
            raise ValueError("Lot size out of range")
    except (ValueError, TypeError):
        await update.message.reply_text("❌ Please enter valid lot size (1-1000)")
        return
    
    await state_manager.set_state_data(user.id, {'lot_size': lot_size})
    await state_manager.set_state(user.id, 'move_manual_sl_price')
    
    await update.message.reply_text(
        f"✅ Lot Size: {lot_size}\n\n"
        f"Step 3/6: Stop Loss Price\n\n"
        f"Enter SL price:",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_manual_sl_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL price"""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_manual_sl_price':
        return
    
    text = update.message.text.strip()
    
    try:
        sl_price = float(text)
        if sl_price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, TypeError):
        await update.message.reply_text("❌ Please enter a valid SL price")
        return
    
    await state_manager.set_state_data(user.id, {'sl_price': sl_price})
    await state_manager.set_state(user.id, 'move_manual_target_price')
    
    await update.message.reply_text(
        f"✅ SL Price: {sl_price}\n\n"
        f"Step 4/6: Target Price [Optional]\n\n"
        f"Enter target price or 'skip':",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_manual_target_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target price"""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_manual_target_price':
        return
    
    text = update.message.text.strip()
    
    if text.lower() == 'skip':
        await state_manager.set_state_data(user.id, {'target_price': None})
    else:
        try:
            target_price = float(text)
            if target_price <= 0:
                raise ValueError("Price must be positive")
            await state_manager.set_state_data(user.id, {'target_price': target_price})
        except (ValueError, TypeError):
            await update.message.reply_text("❌ Please enter valid price or 'skip'")
            return
    
    await state_manager.set_state(user.id, 'move_manual_direction')
    
    await update.message.reply_text(
        "✅ Target Price set\n\n"
        "Step 5/6: Trade Direction\n\n"
        "Enter 'BUY' or 'SELL':",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_manual_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trade direction"""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_manual_direction':
        return
    
    text = update.message.text.strip().upper()
    
    if text not in ['BUY', 'SELL']:
        await update.message.reply_text("❌ Please enter 'BUY' or 'SELL'")
        return
    
    await state_manager.set_state_data(user.id, {'direction': text})
    await state_manager.set_state(user.id, 'move_manual_strategy_select')
    
    await update.message.reply_text(
        f"✅ Direction: {text}\n\n"
        f"Step 6/6: Strategy Selection [Optional]\n\n"
        f"Enter strategy name or 'skip' to proceed:",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_manual_strategy_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete manual trade entry"""
    user = update.effective_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_manual_strategy_select':
        return
    
    text = update.message.text.strip()
    data = await state_manager.get_state_data(user.id)
    
    try:
        # ✅ Create manual trade record
        trade_data = {
            'entry_price': data['entry_price'],
            'lot_size': data['lot_size'],
            'sl_price': data['sl_price'],
            'target_price': data.get('target_price'),
            'direction': data['direction'],
            'entry_time': datetime.now().isoformat(),
            'status': 'ACTIVE',
            'pnl': 0,
            'strategy_name': text if text.lower() != 'skip' else 'Manual Trade'
        }
        
        trade_id = await create_move_trade(user.id, trade_data)
        
        if not trade_id:
            raise Exception("Failed to create trade")
        
        # Clear state
        await state_manager.clear_state(user.id)
        
        message = (
            f"✅ Manual Trade Created\n\n"
            f"<b>Trade ID:</b> {trade_id}\n"
            f"<b>Direction:</b> {data['direction']}\n"
            f"<b>Entry Price:</b> {data['entry_price']}\n"
            f"<b>SL Price:</b> {data['sl_price']}\n"
            f"<b>Target Price:</b> {data.get('target_price', 'N/A')}\n"
            f"<b>Lot Size:</b> {data['lot_size']}\n\n"
            f"📊 Monitor your trade in real-time."
        )
        
        await update.message.reply_text(
            message,
            reply_markup=get_trade_menu_keyboard(),
            parse_mode='HTML'
        )
        
        log_user_action(user.id, f"Created manual trade: {trade_id}")
        
    except Exception as e:
        logger.error(f"Manual trade creation failed: {str(e)}")
        await state_manager.clear_state(user.id)
        await update.message.reply_text(
            f"❌ Trade creation failed: {str(e)}",
            reply_markup=get_trade_menu_keyboard()
        )


__all__ = [
    'move_manual_trade_callback',
    'handle_move_manual_entry_price',
    'handle_move_manual_lot_size',
    'handle_move_manual_sl_price',
    'handle_move_manual_target_price',
    'handle_move_manual_direction',
    'handle_move_manual_strategy_select'
]
        
