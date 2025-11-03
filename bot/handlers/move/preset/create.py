"""
MOVE Trade Preset - Create Handlers
Handles preset creation flow and callbacks.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_preset_ops import create_move_preset
from bot.keyboards.move_preset_keyboards import (
    get_api_selection_keyboard,
    get_strategy_selection_keyboard,
    get_preset_confirmation_keyboard,
    get_cancel_keyboard,
    get_move_preset_menu_keyboard,
)

logger = setup_logger(__name__)


# ============ ADD PRESET FLOW ============

@error_handler
async def move_preset_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start ADD preset flow - Step 1: Name"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"➕ ADD PRESET STARTED - User {user.id}")
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized")
        return
    
    await state_manager.set_state(user.id, 'move_preset_add_name')
    await state_manager.set_state_data(user.id, {})
    
    log_user_action(user.id, "Started adding MOVE preset")
    
    await query.edit_message_text(
        "📝 <b>Create MOVE Trade Preset</b>\n\n"
        "<b>Step 1/2: Preset Name</b>\n\n"
        "Enter a unique name for this preset:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADD Preset: Show API selection"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"🔌 SELECT API - User {user.id}")
    
    # Check state
    state = await state_manager.get_state(user.id)
    if state != 'move_preset_ready':
        logger.warning(f"Wrong state for API selection: {state}")
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    keyboard = await get_api_selection_keyboard(user.id)
    
    await query.edit_message_text(
        "🔌 <b>Select API</b>\n\n"
        "Choose the API for this preset:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@error_handler
async def move_preset_api_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADD Preset: API selected"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract API ID from callback
    callback = query.data  # "move_preset_api_{api_id}"
    api_id = callback.split('_')[-1]
    
    logger.info(f"✓ API Selected: {api_id}")
    
    data = await state_manager.get_state_data(user.id)
    data['api_id'] = api_id
    await state_manager.set_state_data(user.id, data)
    await state_manager.set_state(user.id, 'move_preset_select_strategy')
    
    # Show strategy selection
    keyboard = await get_strategy_selection_keyboard(user.id)
    
    await query.edit_message_text(
        "✅ <b>API Selected</b>\n\n"
        "📊 <b>Select Strategy</b>\n\n"
        "Choose a strategy for this preset:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@error_handler
async def move_preset_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADD Preset: Strategy selected"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Extract strategy ID from callback
    callback = query.data  # "move_preset_strategy_{strategy_id}"
    strategy_id = callback.split('_')[-1]
    
    logger.info(f"✓ Strategy Selected: {strategy_id}")
    
    data = await state_manager.get_state_data(user.id)
    data['strategy_id'] = strategy_id
    await state_manager.set_state_data(user.id, data)
    
    # Show confirmation
    await query.edit_message_text(
        f"✅ <b>All Details Set!</b>\n\n"
        f"<b>Name:</b> {data['preset_name']}\n"
        f"<b>Description:</b> {data.get('preset_description', 'None')}\n"
        f"<b>API:</b> {data['api_id']}\n"
        f"<b>Strategy:</b> {data['strategy_id']}\n\n"
        f"Ready to save?",
        reply_markup=get_preset_confirmation_keyboard(),
        parse_mode='HTML'
    )


@error_handler
async def move_preset_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADD Preset: Save new preset"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    logger.info(f"💾 SAVE PRESET - User {user.id}")
    
    data = await state_manager.get_state_data(user.id)
    
    # Create preset in database
    result = await create_move_preset(
        user_id=user.id,
        name=data['preset_name'],
        description=data.get('preset_description'),
        api_id=data.get('api_id'),
        strategy_id=data.get('strategy_id'),
        sl_trigger_percent=data.get('sl_trigger_percent'),
        sl_limit_percent=data.get('sl_limit_percent'),
        target_trigger_percent=data.get('target_trigger_percent'),
        target_limit_percent=data.get('target_limit_percent'),
    )
    
    if result:
        logger.info(f"✅ Preset saved successfully: {data['preset_name']}")
        log_user_action(user.id, f"Created preset: {data['preset_name']}")
        
        await query.edit_message_text(
            f"✅ <b>Preset '{data['preset_name']}' created successfully!</b>\n\n"
            f"📊 You can now use this preset for quick trades.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        logger.error(f"❌ Failed to save preset")
        await query.edit_message_text(
            "❌ <b>Failed to save preset</b>\n\n"
            "Please try again.",
            reply_markup=get_move_preset_menu_keyboard(),
            parse_mode='HTML'
        )
    
    await state_manager.clear_state(user.id)


# ============ REGISTRATION ============

def register_create_handlers(application: Application):
    """Register CREATE preset handlers"""
    
    logger.info("📝 Registering CREATE preset handlers...")
    
    try:
        application.add_handler(
            CallbackQueryHandler(move_preset_add_callback, pattern="^move_preset_add$"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_api_selected_callback, pattern="^move_preset_api_.*"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_strategy_callback, pattern="^move_preset_strategy_.*"),
            group=10
        )
        application.add_handler(
            CallbackQueryHandler(move_preset_save_callback, pattern="^move_preset_save$"),
            group=10
        )
        
        logger.info("✅ CREATE preset handlers registered")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering CREATE handlers: {e}", exc_info=True)
        return False


__all__ = [
    'register_create_handlers',
    'move_preset_add_callback',
    'move_preset_api_selected_callback',
    'move_preset_strategy_callback',
    'move_preset_save_callback',
    ]
