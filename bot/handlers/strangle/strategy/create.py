"""
STRANGLE Strategy Creation Handler

Handles the complete flow of creating a new STRANGLE strategy:
- Name & description input
- Asset selection (BTC/ETH)
- Expiry selection (daily/weekly/monthly)
- OTM selection (percentage or numeral based)
- Strike & risk management setup

STRANGLE = Sell Call + Put at different OTM strikes
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.strangle_strategy_ops import create_strangle_strategy
from bot.keyboards.strangle_strategy_keyboards import (
    get_cancel_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_otm_type_keyboard,
    get_confirmation_keyboard,
    get_skip_target_keyboard,
    get_strangle_menu_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def strangle_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start STRANGLE strategy creation flow."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started adding STRANGLE strategy")
    
    await state_manager.clear_state(user.id)
    await state_manager.set_state(user.id, 'strangle_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'strangle'})
    
    await query.edit_message_text(
        "📝 Add STRANGLE Strategy\n\n"
        "Step 1/9: Strategy Name\n\n"
        "Enter a unique name for your STRANGLE strategy:\n\n"
        "Example: BTC Weekly Strangle, ETH High IV",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description and move to asset selection."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.set_state(user.id, 'strangle_add_asset')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRANGLE Strategy\n\n"
        f"Step 2/9: Asset Selection\n\n"
        f"Name: {data.get('name')}\n\n"
        f"Select underlying asset:",
        reply_markup=get_asset_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection (BTC/ETH)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    asset = query.data.split('_')[2]  # strangle_asset_BTC -> BTC
    
    await state_manager.set_state_data(user.id, {'asset': asset})
    logger.info(f"✅ STRANGLE asset selected: {asset}")
    
    await state_manager.set_state(user.id, 'strangle_add_expiry')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRANGLE Strategy\n\n"
        f"Step 3/9: Expiry Selection\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {asset}\n\n"
        f"Select expiry type:",
        reply_markup=get_expiry_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection (daily/weekly/monthly)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    expiry = query.data.split('_')[2]  # strangle_expiry_daily -> daily
    
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    logger.info(f"✅ STRANGLE expiry selected: {expiry}")
    
    await state_manager.set_state(user.id, 'strangle_otm_type')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add STRANGLE Strategy\n\n"
        f"Step 4/9: OTM Selection Method\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {expiry.capitalize()}\n\n"
        f"How would you like to select OTM strikes?\n\n"
        f"🔢 Percentage: e.g., 5% OTM from spot\n"
        f"🎯 Numeral: e.g., 2 strikes away from ATM",
        reply_markup=get_otm_type_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def strangle_otm_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTM type selection (percentage/numeral)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    otm_type = query.data.split('_')[-1]  # strangle_otm_type_percentage -> percentage
    
    await state_manager.set_state_data(user.id, {'otm_type': otm_type})
    logger.info(f"✅ STRANGLE OTM type selected: {otm_type}")
    
    data = await state_manager.get_state_data(user.id)
    
    if otm_type == 'percentage':
        await state_manager.set_state(user.id, 'strangle_add_call_otm_pct')
        await query.edit_message_text(
            f"📝 Add STRANGLE Strategy\n\n"
            f"Step 5/9: Call OTM Percentage\n\n"
            f"Name: {data.get('name')}\n"
            f"Asset: {data.get('asset')}\n"
            f"Expiry: {data.get('expiry').capitalize()}\n\n"
            f"Enter Call OTM percentage above spot price:\n\n"
            f"Examples:\n"
            f"• 5 - 5% above spot\n"
            f"• 10 - 10% above spot\n\n"
            f"Range: 1-50%",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    else:  # numeral
        await state_manager.set_state(user.id, 'strangle_add_call_otm_num')
        await query.edit_message_text(
            f"📝 Add STRANGLE Strategy\n\n"
            f"Step 5/9: Call OTM Strikes\n\n"
            f"Name: {data.get('name')}\n"
            f"Asset: {data.get('asset')}\n"
            f"Expiry: {data.get('expiry').capitalize()}\n\n"
            f"Enter number of strikes above ATM:\n\n"
            f"Examples:\n"
            f"• 1 - 1 strike above ATM\n"
            f"• 2 - 2 strikes above ATM\n\n"
            f"Range: 1-10",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

async def show_strangle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation before saving."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name') or "Unnamed"
    description = data.get('description')
    asset = data.get('asset') or "N/A"
    expiry = data.get('expiry')
    otm_type = data.get('otm_type')
    
    lot_size = data.get('lot_size', 1)
    sl_trigger = data.get('sl_trigger_pct')
    sl_limit = data.get('sl_limit_pct')
    target_trigger = data.get('target_trigger_pct')
    target_limit = data.get('target_limit_pct')
    
    expiry_display = expiry.capitalize() if expiry else "N/A"
    
    text = (
        f"✅ STRANGLE Strategy - Final Confirmation\n\n"
        f"📋 Details:\n"
        f"• Name: {name}\n"
    )
    
    if description:
        text += f"• Description: {description}\n"
    
    text += (
        f"• Asset: {asset}\n"
        f"• Expiry: {expiry_display}\n"
        f"• Lot Size: {lot_size}\n\n"
        f"📊 Strike Selection:\n"
    )
    
    if otm_type == 'percentage':
        call_otm = data.get('call_otm_pct', 0)
        put_otm = data.get('put_otm_pct', 0)
        text += f"• Call OTM: {call_otm}% above spot\n"
        text += f"• Put OTM: {put_otm}% below spot\n"
    else:
        call_otm = data.get('call_otm_num', 0)
        put_otm = data.get('put_otm_num', 0)
        text += f"• Call: {call_otm} strikes above ATM\n"
        text += f"• Put: {put_otm} strikes below ATM\n"
    
    text += f"\n📊 Risk Management:\n"
    text += f"• SL Trigger: {sl_trigger}%\n"
    text += f"• SL Limit: {sl_limit}%\n"
    
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
async def strangle_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the STRANGLE strategy to database."""
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
            'otm_type': data.get('otm_type'),
            'call_otm_pct': data.get('call_otm_pct'),
            'put_otm_pct': data.get('put_otm_pct'),
            'call_otm_num': data.get('call_otm_num'),
            'put_otm_num': data.get('put_otm_num'),
            'lot_size': data.get('lot_size', 1),
            'stop_loss_trigger': data.get('sl_trigger_pct'),
            'stop_loss_limit': data.get('sl_limit_pct'),
            'target_trigger': data.get('target_trigger_pct'),
            'target_limit': data.get('target_limit_pct')
        }
        
        result = await create_strangle_strategy(user.id, strategy_data)
        
        if not result:
            raise Exception("Failed to save strategy to database")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created STRANGLE strategy: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ STRANGLE Strategy Created!\n\n"
            f"Name: {data.get('name')}\n"
            f"Asset: {data.get('asset')}\n"
            f"Expiry: {data.get('expiry').capitalize()}\n\n"
            f"Strategy has been saved successfully!",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating STRANGLE strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error creating strategy: {str(e)}\n\n"
            f"Please try again.",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def strangle_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip target and proceed to save."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.set_state_data(user.id, {
        'target_trigger_pct': None,
        'target_limit_pct': None
    })
    
    await show_strangle_confirmation(update, context)

@error_handler
async def strangle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel STRANGLE strategy operation."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.clear_state(user.id)
    log_user_action(user.id, "Cancelled STRANGLE strategy operation")
    
    await query.edit_message_text(
        "❌ Operation Cancelled\n\n"
        "STRANGLE strategy operation has been cancelled.",
        reply_markup=get_strangle_menu_keyboard(),
        parse_mode='HTML'
    )

__all__ = [
    'strangle_add_callback',
    'strangle_skip_description_callback',
    'strangle_asset_callback',
    'strangle_expiry_callback',
    'strangle_otm_type_callback',
    'show_strangle_confirmation',
    'strangle_confirm_save_callback',
    'strangle_skip_target_callback',
    'strangle_cancel_callback',
      ]
