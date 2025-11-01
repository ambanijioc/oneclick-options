"""
MOVE Strategy Creation Handler
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_strategy,
    get_move_strategies  # ✅ FIXED: Added missing import
)
from bot.keyboards.move_strategy_keyboards import (
    get_cancel_keyboard,
    get_asset_keyboard,
    get_expiry_keyboard,
    get_direction_keyboard,
    get_confirmation_keyboard,
    get_skip_target_keyboard,
    get_move_menu_keyboard,
    get_description_skip_keyboard
)

logger = setup_logger(__name__)

@error_handler
async def move_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show MOVE strategy menu (called by main menu button)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE strategy menu")

    # ✅ Fetch strategies to get count
    strategies = await get_move_strategies(user.id)
    strategy_count = len(strategies) if strategies else 0
    
    await query.edit_message_text(
        "🎯 MOVE Strategy Management\n\n"
        "Choose an action:",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_add_new_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start MOVE strategy creation flow (called by Add Strategy button)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    log_user_action(user.id, "Started adding MOVE strategy")
    
    # Clear any existing state
    await state_manager.clear_state(user.id)
    
    # Set initial state
    await state_manager.set_state(user.id, 'move_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'move'})
    
    await query.edit_message_text(
        "📝 Add MOVE Strategy\n\n"
        "Step 1/7: Strategy Name\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "Example: BTC 8AM MOVE, ETH Daily MOVE",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def show_description_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show description prompt after name is entered."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    await state_manager.set_state(user.id, 'move_add_description')
    
    await update.message.reply_text(
        f"📝 Add MOVE Strategy\n\n"
        f"Step 2/7: Description\n\n"
        f"Name: {data.get('name')}\n\n"
        f"Enter a description for your strategy (or skip):",
        reply_markup=get_description_skip_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description and move to lot size."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ✅ Save empty description
    await state_manager.set_state_data(user.id, {'description': ''})
    
    # ✅ Get current data
    data = await state_manager.get_state_data(user.id)
    
    # ✅ Move to LOT SIZE (NOT ASSET) - Description is Step 2, Lot Size is Step 3
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    await query.edit_message_text(
        f"✅ Description skipped\n\n"
        f"Step 3/7: <b>Lot Size</b>\n"
        f"Name: {data.get('name')}\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection (BTC/ETH)."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    asset = query.data.split('_')[2]
    await state_manager.set_state_data(user.id, {'asset': asset})
    logger.info(f"✅ MOVE asset selected: {asset}")
    
    await state_manager.set_state(user.id, 'move_add_expiry')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add MOVE Strategy\n\n"
        f"Step 4/7: Expiry Selection\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {asset}\n\n"
        f"Select expiry type:",
        reply_markup=get_expiry_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    expiry = query.data.split('_')[2]
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    logger.info(f"✅ MOVE expiry selected: {expiry}")
    
    await state_manager.set_state(user.id, 'move_add_direction')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add MOVE Strategy\n\n"
        f"Step 5/7: Direction Selection\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {expiry.capitalize()}\n\n"
        f"Select position direction:\n\n"
        f"🟢 Long: Buy MOVE contract\n"
        f"🔴 Short: Sell MOVE contract",
        reply_markup=get_direction_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    direction = query.data.split('_')[2]
    await state_manager.set_state_data(user.id, {'direction': direction})
    logger.info(f"✅ MOVE direction selected: {direction}")
    
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"📝 Add MOVE Strategy\n\n"
        f"Step 6/7: Strike Selection\n\n"
        f"Name: {data.get('name')}\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {data.get('expiry').capitalize()}\n"
        f"Direction: {direction.capitalize()}\n\n"
        f"Enter ATM offset:\n"
        f"• 0 = ATM\n"
        f"• 1 = 1 strike above\n"
        f"• -1 = 1 strike below\n\n"
        f"Range: -10 to +10",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

async def show_move_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name') or "Unnamed"
    description = data.get('description')
    asset = data.get('asset') or "N/A"
    expiry = data.get('expiry')
    direction = data.get('direction')
    atm_offset = data.get('atm_offset')
    sl_trigger = data.get('sl_trigger_percent')
    sl_limit = data.get('sl_limit_percent')
    target_trigger = data.get('target_trigger_percent')
    target_limit = data.get('target_limit_percent')
    
    text = f"✅ MOVE Strategy - Final Confirmation\n\n📋 Details:\n• Name: {name}\n"
    
    if description:
        text += f"• Description: {description}\n"
    
    text += (
        f"• Asset: {asset}\n"
        f"• Expiry: {expiry.capitalize() if expiry else 'N/A'}\n"
        f"• Direction: {direction.capitalize() if direction else 'N/A'}\n"
        f"• ATM Offset: {atm_offset}\n\n"
        f"📊 Risk Management:\n"
        f"• SL Trigger: {sl_trigger}%\n"
        f"• SL Limit: {sl_limit}%\n"
    )
    
    if target_trigger is not None:
        text += f"• Target Trigger: {target_trigger}%\n• Target Limit: {target_limit}%\n"
    
    text += "\nSave this strategy?"
    
    keyboard = get_confirmation_keyboard()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

@error_handler
async def move_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the MOVE strategy."""
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
            'atm_offset': data.get('atm_offset', 0),
            'stop_loss_trigger': data.get('sl_trigger_percent'),
            'stop_loss_limit': data.get('sl_limit_percent'),
            'target_trigger': data.get('target_trigger_percent'),
            'target_limit': data.get('target_limit_percent')
        }
        
        result = await create_move_strategy(user.id, strategy_data)
        
        if not result:
            raise Exception("Failed to save strategy")
        
        await state_manager.clear_state(user.id)
        log_user_action(user.id, f"Created MOVE strategy: {data.get('name')}")
        
        await query.edit_message_text(
            f"✅ MOVE Strategy Created!\n\n"
            f"Name: {data.get('name')}\n"
            f"Asset: {data.get('asset')}\n\n"
            f"Strategy saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating MOVE strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error: {str(e)}\n\nPlease try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip target."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.set_state_data(user.id, {
        'target_trigger_percent': None,
        'target_limit_percent': None
    })
    
    logger.info("✅ User skipped target")
    await show_move_confirmation(update, context)

@error_handler
async def move_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel operation."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    await state_manager.clear_state(user.id)
    log_user_action(user.id, "Cancelled MOVE strategy operation")
    
    await query.edit_message_text(
        "❌ Operation Cancelled",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

# ✅ ADD THIS TO bot/handlers/move/strategy/create.py

@error_handler
async def move_add_new_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Add Strategy' button from MOVE menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    log_user_action(user.id, "Started adding new MOVE strategy")
    
    # Clear any existing state
    await state_manager.clear_state(user.id)
    
    # Set initial state for name input
    await state_manager.set_state(user.id, 'move_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'move'})
    
    await query.edit_message_text(
        "📝 Add MOVE Strategy\n\n"
        "Step 1/7: Strategy Name\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "Example: BTC 8AM MOVE, ETH Daily MOVE",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )
    
__all__ = [
    'move_add_callback',
    'move_add_new_callback',
    'show_description_prompt',
    'move_skip_description_callback',
    'move_asset_callback',
    'move_expiry_callback',
    'move_direction_callback',
    'show_move_confirmation',
    'move_confirm_save_callback',
    'move_skip_target_callback',
    'move_cancel_callback',
]
