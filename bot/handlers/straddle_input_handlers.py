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
        
        # ✅ Convert strikes to dollar offset (BTC = 200, ETH = 50)
        strike_increment = 200 if state_data['asset'] == 'BTC' else 20
        atm_offset = atm_strikes * strike_increment
        
        # ✅ Create StrategyPresetCreate object
        from database.models.strategy_preset import StrategyPresetCreate
        from database.operations.strategy_ops import create_strategy_preset
        from bot.handlers.straddle_strategy_handler import get_straddle_menu_keyboard
       
        preset_data = StrategyPresetCreate(
            user_id=user.id,
            strategy_type='straddle',
            name=state_data['name'],
            description=state_data.get('description', ''),
            asset=state_data['asset'],
            expiry_code=state_data['expiry_code'],
            direction=state_data['direction'],
            lot_size=state_data['lot_size'],
            sl_trigger_pct=state_data['sl_trigger_pct'],
            sl_limit_pct=state_data['sl_limit_pct'],
            target_trigger_pct=state_data.get('target_trigger_pct', 0.0),
            target_limit_pct=state_data.get('target_limit_pct', 0.0),
            atm_offset=atm_offset
        )
        
        # Save to database
        result = await create_strategy_preset(preset_data)
        
        if result:
            target_text = ""
            if state_data.get('target_trigger_pct', 0) > 0:
                target_text = f"Target: <b>{state_data['target_trigger_pct']}% / {state_data['target_limit_pct']}%</b>\n"
            
            await update.message.reply_text(
                f"<b>✅ Straddle Strategy Created</b>\n\n"
                f"Name: <b>{state_data['name']}</b>\n"
                f"Asset: <b>{state_data['asset']}</b>\n"
                f"Expiry: <b>{state_data['expiry_code']}</b>\n"
                f"Direction: <b>{state_data['direction'].title()}</b>\n"
                f"Lot Size: <b>{state_data['lot_size']}</b>\n"
                f"ATM Offset: <b>{atm_strikes:+d} strikes</b> ({atm_offset:+d} USD)\n"
                f"Stop Loss: <b>{state_data['sl_trigger_pct']}% / {state_data['sl_limit_pct']}%</b>\n"
                + target_text,
                reply_markup=get_straddle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create strategy.",
                reply_markup=get_straddle_menu_keyboard()
            )
        
        # Clear state
        await state_manager.clear_state(user.id)
    
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
        [InlineKeyboardButton("🔙 Back", callback_data="straddle_create_cancel")]
    ]
    
    await update.callback_query.edit_message_text(
        "<b>🎯 SL-to-Cost Monitoring</b>\n\n"
        "<b>What it does:</b>\n"
        "• Monitors positions every 5 seconds\n"
        "• When one leg closes (SL hit), moves other leg SL to breakeven\n"
        "• Auto-stops when done\n\n"
        "<b>⚠️ Resource Usage:</b> +10MB RAM per active strategy\n\n"
        "Enable for this preset?",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
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
    from database.operations.strategy_ops import create_strategy_preset
    from datetime import datetime
    
    preset_data = {
        'user_id': update.callback_query.from_user.id,
        'strategy_name': context.user_data.get('strategy_name'),
        'strategy_type': 'straddle',
        'symbol': context.user_data.get('symbol'),
        'entry_time': context.user_data.get('entry_time'),
        # ... other fields from your current implementation ...
        
        # ✅ NEW FIELD
        'enable_sl_monitor': context.user_data.get('enable_sl_monitor', False),
        
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

    result = await create_strategy_preset(preset_data)
    sl_status = "✅ Enabled" if preset_data['enable_sl_monitor'] else "❌ Disabled"
    if result:
        await update.callback_query.edit_message_text(
            f"✅ Preset saved!\n\n"
            f"<b>Name:</b> {preset_data['strategy_name']}\n"
            f"<b>SL Monitor:</b> {sl_status}",
            parse_mode='HTML'
        )
    else:
        await update.callback_query.edit_message_text("❌ Error saving preset.", parse_mode='HTML')
