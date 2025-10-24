"""
Input handlers for straddle strategy creation flow.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager  # ✅ Import global instance

logger = setup_logger(__name__)


async def handle_straddle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy name input."""
    user = update.effective_user
    
    # Store strategy name
    await state_manager.set_state_data(user.id, {'name': text, 'strategy_type': 'straddle'})
    
    # Ask for description
    await state_manager.set_state(user.id, 'straddle_add_description')
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="straddle_skip_description")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Enter description (optional):",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_straddle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy description input."""
    user = update.effective_user
    
    # Store description
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data="straddle_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="straddle_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Straddle Strategy</b>\n\n"
        f"Name: <b>{state_data['name']}</b>\n"
        f"Description: <i>{text}</i>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_straddle_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy lot size input."""
    user = update.effective_user
    
    try:
        lot_size = int(text)
        if lot_size <= 0:
            raise ValueError("Lot size must be positive")
        
        # Store lot size
        state_data = await state_manager.get_state_data(user.id)
        state_data['lot_size'] = lot_size
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for stop loss trigger percentage
        await state_manager.set_state(user.id, 'straddle_add_sl_trigger')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"Lot Size: <b>{lot_size}</b>\n\n"
            f"Enter stop loss trigger percentage:\n\n"
            f"Example: <code>50</code> (for 50% loss)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid lot size. Please enter a positive number.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy stop loss trigger input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for stop loss limit percentage
        await state_manager.set_state(user.id, 'straddle_add_sl_limit')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"Example: <code>55</code> (exit at 55% loss if triggered)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy stop loss limit input."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_limit_pct'] = sl_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for target percentage (optional)
        await state_manager.set_state(user.id, 'straddle_add_target_trigger')
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target (0)", callback_data="straddle_skip_target")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"SL Trigger: <b>{state_data['sl_trigger_pct']}%</b>\n"
            f"SL Limit: <b>{sl_limit}%</b>\n\n"
            f"Enter target trigger percentage (optional):\n\n"
            f"Example: <code>100</code> (for 100% profit)\n"
            f"Or enter <code>0</code> to skip",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy target trigger input."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Store target trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger_pct'] = target_trigger
        
        if target_trigger == 0:
            # Skip target - go to ATM offset
            state_data['target_limit_pct'] = 0
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'straddle_add_atm_offset')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Straddle Strategy</b>\n\n"
                    f"Enter ATM offset (in strikes):\n\n"
                    f"• <code>0</code> = ATM (At The Money)\n"
                    f"• <code>+1</code> = 1 strike above ATM (BTC: $200, ETH: $20)\n"  # <-- CHANGED
                    f"• <code>-1</code> = 1 strike below ATM\n"
                    f"• <code>+5</code> = 5 strikes above ATM (BTC: $1000, ETH: $100)",  # <-- CHANGED
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )

        else:
            # Ask for target limit
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'straddle_add_target_limit')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Straddle Strategy</b>\n\n"
                f"Target Trigger: <b>{target_trigger}%</b>\n\n"
                f"Enter target limit percentage:\n\n"
                f"Example: <code>105</code> (exit at 105% profit if triggered)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy target limit input."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Store target limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_limit_pct'] = target_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for ATM offset
        await state_manager.set_state(user.id, 'straddle_add_atm_offset')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Straddle Strategy</b>\n\n"
            f"Enter ATM offset:\n\n"
            f"• <code>0</code> = ATM (At The Money)\n"
            f"• <code>+1000</code> = Strike $1000 above ATM\n"
            f"• <code>-1000</code> = Strike $1000 below ATM",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_atm_offset_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy ATM offset input."""
    user = update.effective_user
    
    try:
        # Parse ATM offset (convert strikes to dollar value)
        atm_strikes = int(text)
        
        # Get state data
        state_data = await state_manager.get_state_data(user.id)
        
        # ✅ Convert strikes to dollar offset (BTC = 200, ETH = 20)
        strike_increment = 200 if state_data['asset'] == 'BTC' else 20
        atm_offset = atm_strikes * strike_increment
        
        # ✅ STORE ATM offset in state (don't save preset yet!)
        state_data['atm_offset'] = atm_offset
        state_data['atm_strikes'] = atm_strikes  # Store for display later
        await state_manager.set_state_data(user.id, state_data)
        
        # ✅ NOW ask about SL monitoring preference
        await ask_sl_monitor_preference(update, context)
        
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
        await update.message.reply_text(
            "❌ Invalid offset. Please enter a whole number.\n\n"
            "Example:\n"
            "• <code>0</code> = ATM\n"
            "• <code>1</code> = 1 strike away (BTC: $200, ETH: $50)\n"
            "• <code>-2</code> = 2 strikes below ATM",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ADD AT THE END OF straddle_input_handlers.py

async def ask_sl_monitor_preference(update, context):
    """
    Ask if SL monitoring should be enabled.
    Step comes AFTER entering all strategy details.
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Enable SL-to-Cost", callback_data="straddle_sl_yes"),
            InlineKeyboardButton("❌ Disable", callback_data="straddle_sl_no")
        ],
        [InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]
    ]
    
    # ✅ FIX: Use update.message.reply_text (NOT callback_query.edit_message_text)
    await update.message.reply_text(
        "<b>🎯 SL-to-Cost Monitoring</b>\n\n"
        "<b>What it does:</b>\n"
        "• Monitors positions every 5 seconds\n"
        "• When one leg closes (hits target), automatically moves other leg's SL to entry price\n"
        "• Protects your profit and prevents losses\n\n"
        "<b>Should this be enabled for this strategy?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def handle_sl_monitor_yes(update, context):
    """User enabled SL monitoring."""
    context.user_data['enable_sl_monitor'] = True
    
    # Continue to save preset
    await save_straddle_preset(update, context)


async def handle_sl_monitor_no(update, context):
    """User disabled SL monitoring."""
    context.user_data['enable_sl_monitor'] = False
    
    # Continue to save preset
    await save_straddle_preset(update, context)


async def save_straddle_preset(update, context):
    """Save the straddle preset with SL preference."""
    from database.models.strategy_preset import StrategyPresetCreate
    from database.operations.strategy_ops import create_strategy_preset
    
    user = update.effective_user
    
    # ✅ Get data from state_manager (NOT context.user_data)
    state_data = await state_manager.get_state_data(user.id)
    
    # ✅ Build preset from state_data
    preset_data = StrategyPresetCreate(
        user_id=user.id,
        name=state_data['name'],
        description=state_data.get('description', ''),
        strategy_type='straddle',
        asset=state_data['asset'],
        expiry_code=state_data['expiry_code'],
        direction=state_data['direction'],
        lot_size=state_data['lot_size'],
        sl_trigger_pct=state_data['sl_trigger_pct'],
        sl_limit_pct=state_data['sl_limit_pct'],
        target_trigger_pct=state_data.get('target_trigger_pct', 0.0),
        target_limit_pct=state_data.get('target_limit_pct', 0.0),
        atm_offset=state_data['atm_offset'],
        enable_sl_monitor=context.user_data.get('enable_sl_monitor', False)  # ✅ From button callback
    )
    
    result = await create_strategy_preset(preset_data)
    
    sl_status = "✅ Enabled" if preset_data.enable_sl_monitor else "❌ Disabled"
    
    if result:
        # ✅ Use update.message (NOT callback_query)
        await update.message.reply_text(
            f"✅ <b>Preset Saved!</b>\n\n"
            f"<b>Name:</b> {preset_data.name}\n"
            f"<b>Asset:</b> {preset_data.asset}\n"
            f"<b>Direction:</b> {preset_data.direction.title()}\n"
            f"<b>SL Monitor:</b> {sl_status}",
            parse_mode='HTML'
        )
        
        await state_manager.clear_state(user.id)
        context.user_data.clear()  # ✅ Clear context too
        log_user_action(user.id, "straddle_save", f"Saved strategy: {preset_data.name}")
    else:
        await update.message.reply_text("❌ Error saving preset.", parse_mode='HTML')

# ============================================================================
# EDIT INPUT HANDLERS
# ============================================================================

async def handle_straddle_edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing strategy name."""
    user = update.effective_user
    
    if len(text) < 3 or len(text) > 50:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Name must be between 3 and 50 characters.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Get strategy ID from state
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text("❌ Strategy not found. Please try again.")
        await state_manager.clear_state(user.id)
        return
    
    # Get existing strategy
    strategy = await get_strategy_preset_by_id(strategy_id)
    if not strategy:
        await update.message.reply_text("❌ Strategy not found.")
        await state_manager.clear_state(user.id)
        return
    
    # Update name
    from database.models.strategy_preset import StrategyPresetUpdate
    update_data = StrategyPresetUpdate(name=text)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await update.message.reply_text(
            f"✅ <b>Name Updated!</b>\n\n"
            f"Old: <b>{strategy.name}</b>\n"
            f"New: <b>{text}</b>",
            parse_mode='HTML'
        )
        log_user_action(user.id, "straddle_edit_name_complete", f"Updated name to: {text}")
    else:
        await update.message.reply_text("❌ Failed to update name.")
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Show updated strategy menu
    await show_strategy_edit_menu(update, strategy_id)


async def handle_straddle_edit_desc_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing strategy description."""
    user = update.effective_user
    
    if len(text) > 200:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Description must be 200 characters or less.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Get strategy ID from state
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text("❌ Strategy not found. Please try again.")
        await state_manager.clear_state(user.id)
        return
    
    # Update description
    from database.models.strategy_preset import StrategyPresetUpdate
    update_data = StrategyPresetUpdate(description=text)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await update.message.reply_text(
            f"✅ <b>Description Updated!</b>\n\n"
            f"New description: <i>{text}</i>",
            parse_mode='HTML'
        )
        log_user_action(user.id, "straddle_edit_desc_complete", f"Updated description")
    else:
        await update.message.reply_text("❌ Failed to update description.")
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    # Show updated strategy menu
    await show_strategy_edit_menu(update, strategy_id)


async def handle_straddle_edit_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing SL trigger percentage."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for stop loss limit percentage
        await state_manager.set_state(user.id, 'straddle_edit_sl_limit_input')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        
        await update.message.reply_text(
            f"<b>✏️ Edit Stop Loss Limit</b>\n\n"
            f"SL Trigger: <b>{sl_trigger:.1f}%</b>\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"Example: <code>51</code> (for 51% loss)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_edit_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing SL limit percentage."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Get state data
        state_data = await state_manager.get_state_data(user.id)
        sl_trigger = state_data.get('sl_trigger_pct')
        strategy_id = state_data.get('edit_strategy_id')
        
        if not strategy_id:
            await update.message.reply_text("❌ Strategy not found.")
            await state_manager.clear_state(user.id)
            return
        
        # Update SL in database
        from database.models.strategy_preset import StrategyPresetUpdate
        update_data = StrategyPresetUpdate(
            sl_trigger_pct=sl_trigger,
            sl_limit_pct=sl_limit
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text(
                f"✅ <b>Stop Loss Updated!</b>\n\n"
                f"SL Trigger: <b>{sl_trigger:.1f}%</b>\n"
                f"SL Limit: <b>{sl_limit:.1f}%</b>",
                parse_mode='HTML'
            )
            log_user_action(user.id, "straddle_edit_sl_complete", f"Updated SL to {sl_trigger}/{sl_limit}")
        else:
            await update.message.reply_text("❌ Failed to update stop loss.")
        
        # Clear state
        await state_manager.clear_state(user.id)
        
        # Show updated strategy menu
        await show_strategy_edit_menu(update, strategy_id)
        
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_edit_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing target trigger percentage."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # If target is 0, disable it and save
        if target_trigger == 0:
            state_data = await state_manager.get_state_data(user.id)
            strategy_id = state_data.get('edit_strategy_id')
            
            if not strategy_id:
                await update.message.reply_text("❌ Strategy not found.")
                await state_manager.clear_state(user.id)
                return
            
            # Update target to 0 (disabled)
            from database.models.strategy_preset import StrategyPresetUpdate
            update_data = StrategyPresetUpdate(
                target_trigger_pct=0.0,
                target_limit_pct=0.0
            )
            success = await update_strategy_preset(strategy_id, update_data)
            
            if success:
                await update.message.reply_text(
                    "✅ <b>Target Disabled</b>\n\n"
                    "Target has been set to 0.",
                    parse_mode='HTML'
                )
                log_user_action(user.id, "straddle_edit_target_complete", "Disabled target")
            else:
                await update.message.reply_text("❌ Failed to update target.")
            
            await state_manager.clear_state(user.id)
            await show_strategy_edit_menu(update, strategy_id)
            return
        
        # Store target trigger and ask for limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger_pct'] = target_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        await state_manager.set_state(user.id, 'straddle_edit_target_limit_input')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        
        await update.message.reply_text(
            f"<b>✏️ Edit Target Limit</b>\n\n"
            f"Target Trigger: <b>{target_trigger:.1f}%</b>\n\n"
            f"Enter target limit percentage:\n\n"
            f"Example: <code>99</code> (for 99% profit)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_straddle_edit_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing target limit percentage."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Get state data
        state_data = await state_manager.get_state_data(user.id)
        target_trigger = state_data.get('target_trigger_pct')
        strategy_id = state_data.get('edit_strategy_id')
        
        if not strategy_id:
            await update.message.reply_text("❌ Strategy not found.")
            await state_manager.clear_state(user.id)
            return
        
        # Update target in database
        from database.models.strategy_preset import StrategyPresetUpdate
        update_data = StrategyPresetUpdate(
            target_trigger_pct=target_trigger,
            target_limit_pct=target_limit
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text(
                f"✅ <b>Target Updated!</b>\n\n"
                f"Target Trigger: <b>{target_trigger:.1f}%</b>\n"
                f"Target Limit: <b>{target_limit:.1f}%</b>",
                parse_mode='HTML'
            )
            log_user_action(user.id, "straddle_edit_target_complete", f"Updated target to {target_trigger}/{target_limit}")
        else:
            await update.message.reply_text("❌ Failed to update target.")
        
        # Clear state
        await state_manager.clear_state(user.id)
        
        # Show updated strategy menu
        await show_strategy_edit_menu(update, strategy_id)
        
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# Helper function to show strategy edit menu after updates
async def show_strategy_edit_menu(update: Update, strategy_id: str):
    """Show the strategy edit menu with updated information."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from database.operations.strategy_ops import get_strategy_preset_by_id
    
    strategy = await get_strategy_preset_by_id(strategy_id)
    
    if not strategy:
        await update.message.reply_text("❌ Strategy not found")
        return
    
    target_text = ""
    if strategy.target_trigger_pct > 0:
        target_text = f"Target: {strategy.target_trigger_pct:.1f}% / {strategy.target_limit_pct:.1f}%\n"
    
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data=f"straddle_edit_name_{strategy_id}")],
        [InlineKeyboardButton("📝 Edit Description", callback_data=f"straddle_edit_desc_{strategy_id}")],
        [InlineKeyboardButton("📝 Edit SL %", callback_data=f"straddle_edit_sl_{strategy_id}")],
        [InlineKeyboardButton("📝 Edit Target %", callback_data=f"straddle_edit_target_{strategy_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="straddle_edit_list")]
    ]
    
    await update.message.reply_text(
        f"<b>✏️ Edit Strategy</b>\n\n"
        f"<b>Current Settings:</b>\n\n"
        f"Name: <b>{strategy.name}</b>\n"
        f"Description: <i>{strategy.description or 'None'}</i>\n"
        f"Asset: {strategy.asset} | Expiry: {strategy.expiry_code}\n"
        f"Direction: {strategy.direction.title()} | Lots: {strategy.lot_size}\n"
        f"ATM Offset: {strategy.atm_offset:+d}\n"
        f"SL: {strategy.sl_trigger_pct:.1f}% / {strategy.sl_limit_pct:.1f}%\n"
        + target_text +
        "\nSelect what you want to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
        )
    
