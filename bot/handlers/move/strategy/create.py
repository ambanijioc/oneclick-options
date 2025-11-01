"""
MOVE Strategy Creation Handler - COMPLETE WITH ASSET/EXPIRY/DIRECTION
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_strategy,
    get_move_strategies
)
from bot.keyboards.move_strategy_keyboards import (
    get_cancel_keyboard,
    get_move_menu_keyboard,
)

logger = setup_logger(__name__)

# ==================== STEP 0: MENU ====================

@error_handler
async def move_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show MOVE strategy menu."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE strategy menu")
    strategies = await get_move_strategies(user.id)
    
    await query.edit_message_text(
        "🎯 MOVE Strategy Management\n\n"
        "Choose an action:",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 1: STRATEGY NAME ====================

@error_handler
async def move_add_new_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1/9: Start MOVE strategy creation - Ask for strategy name."""
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
        "Step 1/9: Strategy Name\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "Example: BTC 8AM MOVE, ETH Daily MOVE",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 2: DESCRIPTION ====================

@error_handler
async def handle_move_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2/9: User entered description - Save it."""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Store description
    await state_manager.set_state_data(user.id, {'description': text})
    logger.info(f"✅ MOVE description stored: {text[:50]}")
    
    # Move to lot size state (Step 3)
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    data = await state_manager.get_state_data(user.id)
    
    await update.message.reply_text(
        f"✅ <b>Description saved</b>\n\n"
        f"<code>{text}</code>\n\n"
        f"Step 3/9: <b>Lot Size</b>\n"
        f"Name: <code>{data.get('name')}</code>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description and move to lot size - Button callback."""
    query = update.callback_query
    await query.answer("⏭️ Skipping description...")
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_description':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    # Save empty description
    await state_manager.set_state_data(user.id, {'description': ''})
    data = await state_manager.get_state_data(user.id)
    
    # Move to LOT SIZE (Step 3)
    await state_manager.set_state(user.id, 'move_add_lot_size')
    
    logger.info(f"⏭️ User {user.id} skipped description")
    
    await query.edit_message_text(
        f"⏭️ <b>Description skipped</b>\n\n"
        f"Step 3/9: <b>Lot Size</b>\n"
        f"Name: <code>{data.get('name')}</code>\n\n"
        f"Enter lot size (1-1000):",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 3: LOT SIZE ====================

@error_handler
async def handle_move_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 3/9: Handle lot size input."""
    user = update.effective_user
    
    try:
        lot_size = int(text)
        if not (1 <= lot_size <= 1000):
            raise ValueError("Lot size must be between 1 and 1000")
        
        await state_manager.set_state_data(user.id, {'lot_size': lot_size})
        logger.info(f"✅ MOVE lot size stored: {lot_size}")
        
        # Move to ASSET selection (Step 4)
        await state_manager.set_state(user.id, 'move_add_asset')
        
        data = await state_manager.get_state_data(user.id)
        
        keyboard = [
            [
                InlineKeyboardButton("🔵 BTC", callback_data="move_asset_btc"),
                InlineKeyboardButton("🟡 ETH", callback_data="move_asset_eth")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"✅ <b>Lot size saved</b>\n\n"
            f"Step 4/9: <b>Asset Selection</b>\n"
            f"Name: <code>{data.get('name')}</code>\n"
            f"Lot Size: {lot_size}\n\n"
            f"Select asset:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid lot size: {str(e)}\n\n"
            f"Please enter a number between 1 and 1000:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== STEP 4: ASSET SELECTION ====================

@error_handler
async def move_asset_btc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4/9: BTC asset selected."""
    query = update.callback_query
    await query.answer("🔵 BTC selected")
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_asset':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    await state_manager.set_state_data(user.id, {'asset': 'BTC'})
    logger.info(f"✅ MOVE asset selected: BTC")
    
    await _show_expiry_selection(update, context, query)

@error_handler
async def move_asset_eth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4/9: ETH asset selected."""
    query = update.callback_query
    await query.answer("🟡 ETH selected")
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_asset':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    await state_manager.set_state_data(user.id, {'asset': 'ETH'})
    logger.info(f"✅ MOVE asset selected: ETH")
    
    await _show_expiry_selection(update, context, query)

async def _show_expiry_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """Show expiry selection after asset is selected."""
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    # Move to EXPIRY (Step 5)
    await state_manager.set_state(user.id, 'move_add_expiry')
    
    # Expiry options as per Delta Exchange docs
    keyboard = [
        [
            InlineKeyboardButton("📅 D (Daily)", callback_data="move_expiry_d"),
            InlineKeyboardButton("📅 D+1", callback_data="move_expiry_d1")
        ],
        [
            InlineKeyboardButton("📅 W (Weekly)", callback_data="move_expiry_w"),
            InlineKeyboardButton("📅 W1", callback_data="move_expiry_w1")
        ],
        [
            InlineKeyboardButton("📅 M (Monthly)", callback_data="move_expiry_m"),
            InlineKeyboardButton("📅 M1", callback_data="move_expiry_m1")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"✅ <b>Asset selected</b>\n\n"
        f"Step 5/9: <b>Expiry Selection</b>\n"
        f"Asset: {data.get('asset')}\n\n"
        f"Select expiry:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# ==================== STEP 5: EXPIRY SELECTION ====================

async def _handle_expiry_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, expiry_code: str, expiry_label: str):
    """Common handler for expiry selection."""
    query = update.callback_query
    await query.answer(f"📅 {expiry_label} selected")
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_expiry':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    await state_manager.set_state_data(user.id, {'expiry': expiry_code})
    logger.info(f"✅ MOVE expiry selected: {expiry_code}")
    
    await _show_direction_selection(update, context, query)

@error_handler
async def move_expiry_d_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5/9: Daily (D) expiry selected."""
    await _handle_expiry_selection(update, context, 'D', 'Daily')

@error_handler
async def move_expiry_d1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5/9: D+1 expiry selected."""
    await _handle_expiry_selection(update, context, 'D+1', 'D+1')

@error_handler
async def move_expiry_w_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5/9: Weekly (W) expiry selected."""
    await _handle_expiry_selection(update, context, 'W', 'Weekly')

@error_handler
async def move_expiry_w1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5/9: W1 expiry selected."""
    await _handle_expiry_selection(update, context, 'W1', 'W1')

@error_handler
async def move_expiry_m_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5/9: Monthly (M) expiry selected."""
    await _handle_expiry_selection(update, context, 'M', 'Monthly')

@error_handler
async def move_expiry_m1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5/9: M1 expiry selected."""
    await _handle_expiry_selection(update, context, 'M1', 'M1')

async def _show_direction_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """Show direction selection after expiry is selected."""
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    # Move to DIRECTION (Step 6)
    await state_manager.set_state(user.id, 'move_add_direction')
    
    keyboard = [
        [
            InlineKeyboardButton("🟢 Long (Buy)", callback_data="move_direction_long"),
            InlineKeyboardButton("🔴 Short (Sell)", callback_data="move_direction_short")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        f"✅ <b>Expiry selected</b>\n\n"
        f"Step 6/9: <b>Direction Selection</b>\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {data.get('expiry')}\n\n"
        f"Select direction:\n\n"
        f"🟢 <b>Long:</b> Buy MOVE contract (bullish)\n"
        f"🔴 <b>Short:</b> Sell MOVE contract (bearish)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# ==================== STEP 6: DIRECTION SELECTION ====================

async def _handle_direction_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, direction: str, direction_label: str):
    """Common handler for direction selection."""
    query = update.callback_query
    await query.answer(f"{direction_label} selected")
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_direction':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    await state_manager.set_state_data(user.id, {'direction': direction})
    logger.info(f"✅ MOVE direction selected: {direction}")
    
    await _show_atm_offset_prompt(update, context, query)

@error_handler
async def move_direction_long_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6/9: Long direction selected."""
    await _handle_direction_selection(update, context, 'Long', '🟢 Long')

@error_handler
async def move_direction_short_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6/9: Short direction selected."""
    await _handle_direction_selection(update, context, 'Short', '🔴 Short')

async def _show_atm_offset_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """Show ATM offset prompt after direction is selected."""
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    # Move to ATM OFFSET (Step 7)
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    
    await query.edit_message_text(
        f"✅ <b>Direction selected</b>\n\n"
        f"Step 7/9: <b>ATM Offset</b>\n"
        f"Asset: {data.get('asset')}\n"
        f"Expiry: {data.get('expiry')}\n"
        f"Direction: {data.get('direction')}\n\n"
        f"Enter ATM offset (-10 to +10):\n"
        f"• 0 = ATM\n"
        f"• 1 = 1 strike above\n"
        f"• -1 = 1 strike below",
        reply_markup=get_cancel_keyboard(),
        parse_mode='HTML'
    )

# ==================== STEP 7: ATM OFFSET ====================

@error_handler
async def handle_move_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 7/9: Handle ATM offset input."""
    user = update.effective_user
    
    try:
        atm_offset = int(text)
        if not (-10 <= atm_offset <= 10):
            raise ValueError("ATM offset must be between -10 and +10")
        
        await state_manager.set_state_data(user.id, {'atm_offset': atm_offset})
        logger.info(f"✅ MOVE ATM offset stored: {atm_offset}")
        
        # Move to SL trigger (Step 8)
        await state_manager.set_state(user.id, 'move_add_sl_trigger')
        
        await update.message.reply_text(
            f"✅ <b>ATM offset saved</b>\n\n"
            f"Step 8/9: <b>SL Trigger %</b>\n"
            f"ATM Offset: {atm_offset:+d}\n\n"
            f"Enter SL trigger % (e.g., 25 for 25%):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid ATM offset: {str(e)}\n\n"
            f"Please enter a number between -10 and +10:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== STEP 8: SL TRIGGER ====================

@error_handler
async def handle_move_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 8/9: Handle SL trigger % input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if not (1 <= sl_trigger <= 200):
            raise ValueError("SL trigger must be between 1% and 200%")
        
        await state_manager.set_state_data(user.id, {'sl_trigger_percent': sl_trigger})
        logger.info(f"✅ MOVE SL trigger stored: {sl_trigger}%")
        
        # Move to SL limit
        await state_manager.set_state(user.id, 'move_add_sl_limit')
        
        await update.message.reply_text(
            f"✅ <b>SL trigger saved</b>\n\n"
            f"Step 8.5/9: <b>SL Limit %</b>\n"
            f"SL Trigger: {sl_trigger}%\n\n"
            f"Enter SL limit % (e.g., 30 for 30%):\n\n"
            f"💡 Tip: SL limit should be >= SL trigger",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid SL trigger: {str(e)}\n\n"
            f"Please enter a number between 1 and 200:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== STEP 8.5: SL LIMIT ====================

@error_handler
async def handle_move_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 8.5/9: Handle SL limit % input."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        data = await state_manager.get_state_data(user.id)
        sl_trigger = data.get('sl_trigger_percent', 0)
        
        if not (1 <= sl_limit <= 200):
            raise ValueError("SL limit must be between 1% and 200%")
        
        if sl_limit < sl_trigger:
            raise ValueError(f"SL limit ({sl_limit}%) must be >= SL trigger ({sl_trigger}%)")
        
        await state_manager.set_state_data(user.id, {'sl_limit_percent': sl_limit})
        logger.info(f"✅ MOVE SL limit stored: {sl_limit}%")
        
        # Move to target trigger (Step 9)
        await state_manager.set_state(user.id, 'move_add_target_trigger')
        
        # Show skip target button
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target", callback_data="move_skip_target")],
            [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
        ]
        
        await update.message.reply_text(
            f"✅ <b>SL limit saved</b>\n\n"
            f"Step 9/9: <b>Target Trigger % (Optional)</b>\n"
            f"SL Limit: {sl_limit}%\n\n"
            f"Enter target trigger % (e.g., -20 for -20%):\n\n"
            f"💡 Tip: Use negative values for profit targets",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid SL limit: {str(e)}\n\n"
            f"Please enter a valid number:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== STEP 9: TARGET TRIGGER ====================

@error_handler
async def handle_move_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 9: Handle target trigger % input."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if not (0 <= target_trigger <= 1000):
            raise ValueError("Target trigger must be between 0% and 1000%")
        
        await state_manager.set_state_data(user.id, {'target_trigger_percent': target_trigger})
        logger.info(f"✅ MOVE target trigger stored: {target_trigger}%")
        
        # Move to target limit
        await state_manager.set_state(user.id, 'move_add_target_limit')
        
        await update.message.reply_text(
            f"✅ <b>Target trigger saved</b>\n\n"
            f"Step 9.5: <b>Target Limit %</b>\n"
            f"Target Trigger: {target_trigger}%\n\n"
            f"Enter target limit % (e.g., 25 for 25%):",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid target trigger: {str(e)}\n\n"
            f"Please enter a number between 0 and 1000:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== STEP 9.5: TARGET LIMIT ====================

@error_handler
async def handle_move_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Step 9.5: Handle target limit % input - FINAL STEP."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        data = await state_manager.get_state_data(user.id)
        target_trigger = data.get('target_trigger_percent', 0)
        
        if not (0 <= target_limit <= 1000):
            raise ValueError("Target limit must be between 0% and 1000%")
        
        if target_limit < target_trigger:
            raise ValueError(f"Target limit ({target_limit}%) must be >= target trigger ({target_trigger}%)")
        
        await state_manager.set_state_data(user.id, {'target_limit_percent': target_limit})
        logger.info(f"✅ MOVE target limit stored: {target_limit}%")
        
        # Show final confirmation
        await show_move_confirmation(update, context)
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid target limit: {str(e)}\n\n"
            f"Please enter a valid number:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )

# ==================== CONFIRMATION & SAVE ====================

async def show_move_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation before saving."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    name = data.get('name') or "Unnamed"
    description = data.get('description', '')
    lot_size = data.get('lot_size')
    asset = data.get('asset')
    expiry = data.get('expiry')
    direction = data.get('direction')
    atm_offset = data.get('atm_offset')
    sl_trigger = data.get('sl_trigger_percent')
    sl_limit = data.get('sl_limit_percent')
    target_trigger = data.get('target_trigger_percent')
    target_limit = data.get('target_limit_percent')
    
    text = f"✅ <b>MOVE Strategy - Final Confirmation</b>\n\n"
    text += f"📋 <b>Details:</b>\n"
    text += f"• Name: <code>{name}</code>\n"
    
    if description:
        text += f"• Description: {description}\n"
    
    text += (
        f"• Asset: <b>{asset}</b>\n"
        f"• Expiry: <b>{expiry}</b>\n"
        f"• Direction: <b>{direction}</b>\n"
        f"• ATM Offset: {atm_offset:+d}\n"
        f"• Lot Size: {lot_size}\n\n"
        f"📊 <b>Risk Management:</b>\n"
        f"• SL Trigger: {sl_trigger}%\n"
        f"• SL Limit: {sl_limit}%\n"
    )
    
    if target_trigger is not None and target_trigger > 0:
        text += (
            f"• Target Trigger: {target_trigger}%\n"
            f"• Target Limit: {target_limit}%\n"
        )
    else:
        text += f"• Target: <i>Not set</i>\n"
    
    text += "\n✅ <b>Save this strategy?</b>"
    
    keyboard = [
        [InlineKeyboardButton("✅ Save", callback_data="move_confirm_save")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='HTML'
        )

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
            'expiry': data.get('expiry'),
            'direction': data.get('direction'),
            'lot_size': data.get('lot_size'),
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
            f"✅ <b>MOVE Strategy Created!</b>\n\n"
            f"📌 Name: <code>{data.get('name')}</code>\n"
            f"🔵 Asset: {data.get('asset')}\n"
            f"📅 Expiry: {data.get('expiry')}\n"
            f"📊 Direction: {data.get('direction')}\n"
            f"📦 Lot Size: {data.get('lot_size')}\n\n"
            f"✅ Strategy saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating MOVE strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ <b>Error saving strategy</b>\n\n"
            f"Error: {str(e)}\n\nPlease try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )

@error_handler
async def move_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip target setup - Button callback."""
    query = update.callback_query
    await query.answer("⏭️ Skipping target setup...")
    user = query.from_user
    
    state = await state_manager.get_state(user.id)
    if state != 'move_add_target_trigger':
        await query.answer("❌ Invalid state", show_alert=True)
        return
    
    # Save empty targets
    await state_manager.set_state_data(user.id, {
        'target_trigger_percent': None,
        'target_limit_percent': None
    })
    
    logger.info(f"⏭️ User {user.id} skipped target - going to confirmation")
    
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
        "❌ <b>Operation Cancelled</b>",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )


__all__ = [
    'move_add_callback',
    'move_add_new_strategy_callback',
    'handle_move_description_callback',
    'move_skip_description_callback',
    'handle_move_lot_size_input',
    'move_asset_btc_callback',
    'move_asset_eth_callback',
    'move_expiry_d_callback',
    'move_expiry_d1_callback',
    'move_expiry_w_callback',
    'move_expiry_w1_callback',
    'move_expiry_m_callback',
    'move_expiry_m1_callback',
    'move_direction_long_callback',
    'move_direction_short_callback',
    'handle_move_atm_offset_input',
    'handle_move_sl_trigger_input',
    'handle_move_sl_limit_input',
    'handle_move_target_trigger_input',
    'handle_move_target_limit_input',
    'show_move_confirmation',
    'move_confirm_save_callback',
    'move_skip_target_callback',
    'move_cancel_callback',
]
