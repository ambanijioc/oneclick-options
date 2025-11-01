"""
MOVE Trade Preset Creation Handler

Handles creating preset configurations for MOVE strategies.
Presets allow quick application of pre-defined settings to multiple trades.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_preset_ops import create_move_preset
from bot.keyboards.move_preset_keyboards import get_preset_menu_keyboard

logger = setup_logger(__name__)


@error_handler
async def move_create_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start MOVE preset creation flow"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started creating MOVE preset")
    
    await state_manager.set_state(user.id, 'move_create_preset_name')
    await state_manager.set_state_data(user.id, {'preset_data': {}})
    
    await query.edit_message_text(
        "📝 Create MOVE Trade Preset\n\n"
        "Step 1/4: Preset Name\n\n"
        "Enter a unique name for this preset:\n"
        "(e.g., 'Conservative', 'Aggressive')",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_preset_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset name input"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if not await check_user_authorization(user):
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if not text or len(text) < 3 or len(text) > 50:
        await update.message.reply_text(
            "❌ Name must be 3-50 characters long\n\n"
            "Please try again:",
            parse_mode='HTML'
        )
        return
    
    await state_manager.set_state_data(user.id, {'preset_name': text})
    await state_manager.set_state(user.id, 'move_preset_sl_trigger')
    
    await update.message.reply_text(
        f"✅ Preset name: <b>{text}</b>\n\n"
        f"Step 2/4: Stop Loss Trigger (%)\n\n"
        f"Enter the SL trigger percentage (0-100):",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_preset_sl_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL trigger percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    try:
        sl_trigger = float(text)
        if not (0 <= sl_trigger <= 100):
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        await update.message.reply_text(
            "❌ Please enter a valid number (0-100)"
        )
        return
    
    await state_manager.set_state_data(user.id, {'sl_trigger_percent': sl_trigger})
    await state_manager.set_state(user.id, 'move_preset_sl_limit')
    
    await update.message.reply_text(
        f"✅ SL Trigger: <b>{sl_trigger}%</b>\n\n"
        f"Step 3/4: Stop Loss Limit (%)\n\n"
        f"Enter the SL limit percentage (usually lower than trigger):",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_preset_sl_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL limit percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    try:
        sl_limit = float(text)
        if not (0 <= sl_limit <= 100):
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        await update.message.reply_text(
            "❌ Please enter a valid number (0-100)"
        )
        return
    
    await state_manager.set_state_data(user.id, {'sl_limit_percent': sl_limit})
    await state_manager.set_state(user.id, 'move_preset_target')
    
    await update.message.reply_text(
        f"✅ SL Limit: <b>{sl_limit}%</b>\n\n"
        f"Step 4/4: Target Trigger (%) [Optional]\n\n"
        f"Enter target trigger % or type 'skip':",
        parse_mode='HTML'
    )


@error_handler
async def handle_move_preset_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target trigger percentage"""
    user = update.effective_user
    text = update.message.text.strip().lower()
    
    data = await state_manager.get_state_data(user.id)
    
    if text == 'skip':
        result = await create_move_preset(
            user.id,
            data['preset_name'],
            data['sl_trigger_percent'],
            data['sl_limit_percent'],
            None,
            None
        )
        
        if result:
            await update.message.reply_text(
                f"✅ Preset '<b>{data['preset_name']}</b>' created successfully!\n\n"
                f"📊 You can now use this preset for quick trade setup.",
                reply_markup=get_preset_menu_keyboard(),
                parse_mode='HTML'
            )
            log_user_action(user.id, f"Created MOVE preset: {data['preset_name']}")
        else:
            await update.message.reply_text(
                "❌ Failed to create preset",
                reply_markup=get_preset_menu_keyboard()
            )
        
        await state_manager.clear_state(user.id)
        return
    
    try:
        target_trigger = float(text)
        if not (0 <= target_trigger <= 100):
            raise ValueError("Out of range")
        
        data['target_trigger_percent'] = target_trigger
        await state_manager.set_state_data(user.id, data)
        await state_manager.set_state(user.id, 'move_preset_target_limit')
        
        await update.message.reply_text(
            f"✅ Target Trigger: <b>{target_trigger}%</b>\n\n"
            f"Enter target limit percentage:",
            parse_mode='HTML'
        )
        
    except (ValueError, TypeError):
        await update.message.reply_text(
            "❌ Please enter a valid number or 'skip'"
        )


@error_handler
async def handle_move_preset_target_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target limit percentage"""
    user = update.effective_user
    text = update.message.text.strip()
    
    data = await state_manager.get_state_data(user.id)
    
    try:
        target_limit = float(text)
        if not (0 <= target_limit <= 100):
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        await update.message.reply_text(
            "❌ Please enter a valid number"
        )
        return
    
    # Create preset with target
    result = await create_move_preset(
        user.id,
        data['preset_name'],
        data['sl_trigger_percent'],
        data['sl_limit_percent'],
        data['target_trigger_percent'],
        target_limit
    )
    
    if result:
        await update.message.reply_text(
            f"✅ Preset '<b>{data['preset_name']}</b>' created successfully!\n\n"
            f"📊 You can now use this preset for quick trade setup.",
            reply_markup=get_preset_menu_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, f"Created MOVE preset: {data['preset_name']}")
    else:
        await update.message.reply_text(
            "❌ Failed to create preset",
            reply_markup=get_preset_menu_keyboard()
        )
    
    await state_manager.clear_state(user.id)


async def handle_move_preset_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ REQUIRED EXPORT: Main entry point for preset creation
    This function is imported by __init__.py
    """
    if update.callback_query:
        await move_create_preset_callback(update, context)
    else:
        await update.message.reply_text("❌ Invalid request")


def register_move_preset_handlers(application):
    """
    ✅ REQUIRED EXPORT: Register all MOVE preset handlers with the application
    """
    try:
        from telegram.ext import ConversationHandler, MessageFilter, MessageHandler, filters
        
        logger.info("Registering MOVE preset handlers...")
        
        # Conversation handler for preset creation flow
        preset_conversation = ConversationHandler(
            entry_points=[],  # Entry points registered in parent
            states={
                'move_create_preset_name': [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_preset_name)
                ],
                'move_preset_sl_trigger': [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_preset_sl_trigger)
                ],
                'move_preset_sl_limit': [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_preset_sl_limit)
                ],
                'move_preset_target': [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_preset_target)
                ],
                'move_preset_target_limit': [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_move_preset_target_limit)
                ],
            },
            fallbacks=[]
        )
        
        application.add_handler(preset_conversation)
        logger.info("✅ MOVE preset handlers registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registering MOVE preset handlers: {e}")
        return False


# ✅ REQUIRED EXPORTS
__all__ = [
    'handle_move_preset_create',
    'register_move_preset_handlers',
    'move_create_preset_callback',
    'handle_move_preset_name',
    'handle_move_preset_sl_trigger',
    'handle_move_preset_sl_limit',
    'handle_move_preset_target',
    'handle_move_preset_target_limit',
]
