"""
STRADDLE Strategy Creation Handler

Handles the complete flow of creating a new STRADDLE strategy:
- Name & description input
- Asset selection (BTC/ETH)
- Expiry selection (daily/weekly/monthly)
- Direction selection (long/short)
- Lot size & risk management setup

STRADDLE = Buy/Sell Call + Put at the SAME ATM strike
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.straddle_strategy_ops import create_straddle_strategy
from bot.keyboards.straddle_strategy_keyboards import (
    get_cancel_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_direction_keyboard,
    get_confirmation_keyboard,
    get_skip_target_keyboard,
    get_straddle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def straddle_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start STRADDLE strategy creation flow."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started adding STRADDLE strategy")
    
    await state_manager.clear_state(user.id)
    await state_manager.set_state(user.id, 'straddle_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'straddle'})
    
    await query.edit_message_text(
        "📝 Add STRADDLE Strategy\n\n"
        "Step 1/7: Strategy Name\n\n"
        "Enter a unique name for your STRADDLE strategy:\n\n"
        "Example: BTC ATM Straddle, ETH IV Crush",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def straddle_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description and move to asset selection."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.set_state(user.id, 'straddle_add_asset')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRADDLE Strategy\n\n"
        f"Step 2/7: Asset Selection\n\n"
        f"Name: {data.get('name')}\n\n"
        f"Select underlying asset:",
        reply_markup=get_asset_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def straddle_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection (BTC/ETH)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    asset = query.data.split('_')[2]  # straddle_asset_BTC -> BTC
    
    await state_manager.set_state_data(user.id, {'asset': asset})
    logger.info(f"✅ STRADDLE asset selected: {asset}")
    
    await state_manager.set_state(user.id, 'straddle_add_expiry')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRADDLE Strategy\n\n"
        f"Step 3/7: Expiry Selection\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {asset}\n\n"
        f"Select expiry type:",
        reply_markup=get_expiry_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def straddle_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection (daily/weekly/monthly)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    expiry = query.data.split('_')[2]  # straddle_expiry_daily -> daily
    
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    logger.info(f"✅ STRADDLE expiry selected: {expiry}")
    
    await state_manager.set_state(user.id, 'straddle_add_direction')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRADDLE Strategy\n\n"
        f"Step 4/7: Direction Selection\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {expiry.capitalize()}\n\n"
        f"Select trade direction:\n\n"
        f"📈 Long: Buy Call + Put (profit from big moves)\n"
        f"📉 Short: Sell Call + Put (profit from low volatility)",
        reply_markup=get_direction_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def straddle_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection (long/short)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    direction = query.data.split('_')[-1]  # straddle_direction_long -> long
    
    await state_manager.set_state_data(user.id, {'direction': direction})
    logger.info(f"✅ STRADDLE direction selected: {direction}")
    
    await state_manager.set_state(user.id, 'straddle_add_lot_size')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRADDLE Strategy\n\n"
        f"Step 5/7: Lot Size\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {data.get('expiry').capitalize()}\n"
        f"Direction: {direction.capitalize()}\n\n"
        f"Enter lot size (contracts per leg):\n\n"
        f"Range: 1-100",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

async def show_straddle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation before saving."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name') or "Unnamed"
    description = data.get('description')
    asset = data.get('asset') or "N/A"
    expiry = data.get('expiry')
    direction = data.get('direction')
    lot_size = data.get('lot_size', 1)
    sl_trigger = data.get('sl_trigger_pct')
    sl_limit = data.get('sl_limit_pct')
    target_trigger = data.get('target_trigger_pct')
    target_limit = data.get('target_limit_pct')
    
    expiry_display = expiry.capitalize() if expiry else "N/A"
    direction_display = direction.capitalize() if direction else "N/A"
    
    text = (
        f"✅ STRADDLE Strategy - Final Confirmation\n\n"
        f"📋 Details:\n"
        f"• Name: {name}\n"
    )
    
    if description:
        text += f"• Description: {description}\n"
    
    text += (
        f"• Asset: {asset}\n"
        f"• Expiry: {expiry_display}\n"
        f"• Direction: {direction_display}\n"
        f"• Lot Size: {lot_size}\n\n"
        f"📊 Strike: ATM (At-The-Money)\n"
        f"Both Call + Put at same ATM strike\n\n"
        f"📊 Risk Management:\n"
        f"• SL Trigger: {sl_trigger}%\n"
        f"• SL Limit: {sl_limit}%\n"
    )
    
    if target_trigger is not None:
        text += (
            f"• Target Trigger: {target_trigger}%\n"
            f"• Target Limit: {target_limit}%\n"
        )
    
    text += "\nSave this strategy?"
    
    keyboard = get_confirmation_keyboard()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

@error_handler
async def straddle_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the STRADDLE strategy to database."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    data = await state_manager.get_state_data(user.id)
    
    try:
        strategy_data = {
            'strategy_name': data.get('name'),
            'description': data.get('description', ''),
            'asset': data.get('asset'),
            'expiry': data.get('expiry', 'daily'),
            'direction': data.get('direction'),
            'lot_size': data.get('lot_size', 1),
            'stop_loss_trigger': data.get('sl_trigger_pct'),
            'stop_loss_limit': data.get('sl_limit_pct'),
            'target_trigger': data.get('target_trigger_pct'),
            'target_limit': data.get('target_limit_pct')
        }
        
        result = await create_straddle_strategy(user.id, strategy_data)
        
        if not result:
            raise Exception("Failed to save strategy to database")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created STRADDLE strategy: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ STRADDLE Strategy Created!\n\n"
            f"Name: {data.get('name')}\n"
            f"Asset: {data.get('asset')}\n"
            f"Expiry: {data.get('expiry').capitalize()}\n"
            f"Direction: {data.get('direction').capitalize()}\n\n"
            f"Strategy has been saved successfully!",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating STRADDLE strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error creating strategy: {str(e)}\n\n"
            f"Please try again.",
            reply_markup=get_straddle_menu_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def straddle_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip target and proceed to save."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.set_state_data(user.id, {
        'target_trigger_pct': None,
        'target_limit_pct': None
    })
    
    await show_straddle_confirmation(update, context)

@error_handler
async def straddle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel STRADDLE strategy operation."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.clear_state(user.id)
    log_user_action(user.id, "Cancelled STRADDLE strategy operation")
    
    await query.edit_message_text(
        "❌ Operation Cancelled\n\n"
        "STRADDLE strategy operation has been cancelled.",
        reply_markup=get_straddle_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'straddle_add_callback',
    'straddle_skip_description_callback',
    'straddle_asset_callback',
    'straddle_expiry_callback',
    'straddle_direction_callback',
    'show_straddle_confirmation',
    'straddle_confirm_save_callback',
    'straddle_skip_target_callback',
    'straddle_cancel_callback',
]
