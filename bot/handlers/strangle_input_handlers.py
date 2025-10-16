"""
Input handlers for strangle strategy creation flow.
Handles text input during strategy creation.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager

logger = setup_logger(__name__)


async def handle_strangle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy name input."""
    user = update.effective_user
    
    # Store strategy name
    await state_manager.set_state_data(user.id, {'name': text, 'strategy_type': 'strangle'})
    
    # Ask for description
    await state_manager.set_state(user.id, 'strangle_add_description')
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Skip Description", callback_data="strangle_skip_description")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]  # ✅ FIXED
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Name: <b>{text}</b>\n\n"
        f"Enter description (optional):",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_strangle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy description input."""
    user = update.effective_user
    
    # Store description
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = text
    await state_manager.set_state_data(user.id, state_data)
    
    # Ask for asset
    keyboard = [
        [InlineKeyboardButton("🟠 BTC", callback_data="strangle_asset_btc")],
        [InlineKeyboardButton("🔵 ETH", callback_data="strangle_asset_eth")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]  # ✅ FIXED
    ]
    
    await update.message.reply_text(
        f"<b>➕ Add Strangle Strategy</b>\n\n"
        f"Name: <b>{state_data['name']}</b>\n"
        f"Description: <i>{text}</i>\n\n"
        f"Select asset:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_strangle_lot_size_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy lot size input."""
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
        await state_manager.set_state(user.id, 'strangle_add_sl_trigger')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]  # ✅ FIXED
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"Lot Size: <b>{lot_size}</b>\n\n"
            f"Enter stop loss trigger percentage:\n\n"
            f"Example: <code>50</code> (for 50% loss)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        await update.message.reply_text(
            "❌ Invalid lot size. Please enter a positive number.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy stop loss trigger input."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 1000:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for stop loss limit percentage
        await state_manager.set_state(user.id, 'strangle_add_sl_limit')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
            f"Enter stop loss limit percentage:\n\n"
            f"Example: <code>55</code> (exit at 55% loss if triggered)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy stop loss limit input."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 1000:
            raise ValueError("Percentage must be between 0 and 100")
        
        # Store SL limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_limit_pct'] = sl_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for target percentage (optional)
        await state_manager.set_state(user.id, 'strangle_add_target_trigger')
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Target (0)", callback_data="strangle_skip_target")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"SL Trigger: <b>{state_data['sl_trigger_pct']}%</b>\n"
            f"SL Limit: <b>{sl_limit}%</b>\n\n"
            f"Enter target trigger percentage (optional):\n\n"
            f"Example: <code>100</code> (for 100% profit)\n"
            f"Or enter <code>0</code> to skip",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 100.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy target trigger input."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Store target trigger
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger_pct'] = target_trigger
        
        if target_trigger == 0:
            # Skip target - go to OTM selection
            state_data['target_limit_pct'] = 0
            await state_manager.set_state_data(user.id, state_data)
            
            keyboard = [
                [InlineKeyboardButton("📊 Percentage (Spot-based)", callback_data="strangle_otm_percentage")],
                [InlineKeyboardButton("🔢 Numeral (ATM-based)", callback_data="strangle_otm_numeral")],
                [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
            ]
            
            await update.message.reply_text(
                f"<b>➕ Add Strangle Strategy</b>\n\n"
                f"Select OTM strike selection method:\n\n"
                f"<b>Percentage:</b> Based on spot price\n"
                f"<i>Example: 1% of $120,000 = $1,200 offset</i>\n\n"
                f"<b>Numeral:</b> Based on strikes from ATM\n"
                f"<i>Example: 4 strikes away from ATM</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            # Ask for target limit
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'strangle_add_target_limit')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Strangle Strategy</b>\n\n"
                f"Target Trigger: <b>{target_trigger}%</b>\n\n"
                f"Enter target limit percentage:\n\n"
                f"Example: <code>105</code> (exit at 105% profit if triggered)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy target limit input."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError("Percentage must be between 0 and 1000")
        
        # Store target limit
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_limit_pct'] = target_limit
        await state_manager.set_state_data(user.id, state_data)
        
        # Ask for OTM method
        keyboard = [
            [InlineKeyboardButton("📊 Percentage (Spot-based)", callback_data="strangle_otm_percentage")],
            [InlineKeyboardButton("🔢 Numeral (ATM-based)", callback_data="strangle_otm_numeral")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]
        ]
        
        await update.message.reply_text(
            f"<b>➕ Add Strangle Strategy</b>\n\n"
            f"Select OTM strike selection method:\n\n"
            f"<b>Percentage:</b> Based on spot price\n"
            f"<i>Example: 1% of $120,000 = $1,200 offset</i>\n\n"
            f"<b>Numeral:</b> Based on strikes from ATM\n"
            f"<i>Example: 4 strikes away from ATM</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        await update.message.reply_text(
            "❌ Invalid percentage. Please enter a number between 0 and 1000.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_strangle_otm_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strangle strategy OTM value input."""
    user = update.effective_user
    
    try:
        otm_value = float(text)
        
        if otm_value <= 0:
            raise ValueError("Value must be positive")
        
        # Get state data
        state_data = await state_manager.get_state_data(user.id)
        otm_type = state_data.get('otm_type', 'percentage')
        
        # Validate based on type
        if otm_type == 'percentage':
            if otm_value > 50:
                raise ValueError("Percentage cannot exceed 50%")
        else:  # numeral
            if otm_value > 100:
                raise ValueError("Strikes cannot exceed 100")
            otm_value = int(otm_value)  # Convert to integer for numeral
        
        # Store OTM selection
        state_data['otm_selection'] = {
            'type': otm_type,
            'value': otm_value
        }
        await state_manager.set_state_data(user.id, state_data)
        
        # ✅ Create StrategyPresetCreate object
        from database.models.strategy_preset import StrategyPresetCreate
        from database.operations.strategy_ops import create_strategy_preset
        from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
        
        preset_data = StrategyPresetCreate(
            user_id=user.id,
            strategy_type='strangle',
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
            otm_selection=state_data['otm_selection']  # Store OTM selection
        )
        
        # Save to database
        result = await create_strategy_preset(preset_data)
        
        if result:
            target_text = ""
            if state_data.get('target_trigger_pct', 0) > 0:
                target_text = f"Target: <b>{state_data['target_trigger_pct']}% / {state_data['target_limit_pct']}%</b>\n"
            
            otm_text = f"{otm_value}%" if otm_type == 'percentage' else f"{int(otm_value)} strikes"
            otm_method = "Spot-based" if otm_type == 'percentage' else "ATM-based"
            
            await update.message.reply_text(
                f"<b>✅ Strangle Strategy Created</b>\n\n"
                f"Name: <b>{state_data['name']}</b>\n"
                f"Asset: <b>{state_data['asset']}</b>\n"
                f"Expiry: <b>{state_data['expiry_code']}</b>\n"
                f"Direction: <b>{state_data['direction'].title()}</b>\n"
                f"Lot Size: <b>{state_data['lot_size']}</b>\n"
                f"OTM: <b>{otm_text}</b> ({otm_method})\n"
                f"Stop Loss: <b>{state_data['sl_trigger_pct']}% / {state_data['sl_limit_pct']}%</b>\n"
                + target_text,
                reply_markup=get_strangle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create strategy.",
                reply_markup=get_strangle_menu_keyboard()
            )
        
        # Clear state
        await state_manager.clear_state(user.id)
    
    except ValueError as e:
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="strangle_cancel")]]
        await update.message.reply_text(
            f"❌ Invalid value. {str(e)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        

# ADD THESE AT THE END OF strangle_input_handlers.py

async def handle_strangle_edit_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strategy name edit input."""
    user = update.effective_user
    
    # Get strategy ID
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text("❌ Strategy not found")
        return
    
    # Update strategy
    from database.models.strategy_preset import StrategyPresetUpdate
    from database.operations.strategy_ops import update_strategy_preset
    from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
    
    update_data = StrategyPresetUpdate(name=text)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await update.message.reply_text(
            f"<b>✅ Name Updated</b>\n\n"
            f"New name: <b>{text}</b>",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update name",
            reply_markup=get_strangle_menu_keyboard()
        )
    
    # Clear state
    await state_manager.clear_state(user.id)


async def handle_strangle_edit_desc_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strategy description edit input."""
    user = update.effective_user
    
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text("❌ Strategy not found")
        return
    
    from database.models.strategy_preset import StrategyPresetUpdate
    from database.operations.strategy_ops import update_strategy_preset
    from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
    
    update_data = StrategyPresetUpdate(description=text)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await update.message.reply_text(
            f"<b>✅ Description Updated</b>\n\n"
            f"New description: <i>{text}</i>",
            reply_markup=get_strangle_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update description",
            reply_markup=get_strangle_menu_keyboard()
        )
    
    await state_manager.clear_state(user.id)


async def handle_strangle_edit_lot_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle strategy lot size edit input."""
    user = update.effective_user
    
    try:
        lot_size = int(text)
        if lot_size <= 0:
            raise ValueError("Lot size must be positive")
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        
        if not strategy_id:
            await update.message.reply_text("❌ Strategy not found")
            return
        
        from database.models.strategy_preset import StrategyPresetUpdate
        from database.operations.strategy_ops import update_strategy_preset
        from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
        
        update_data = StrategyPresetUpdate(lot_size=lot_size)
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text(
                f"<b>✅ Lot Size Updated</b>\n\n"
                f"New lot size: <b>{lot_size}</b>",
                reply_markup=get_strangle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to update lot size",
                reply_markup=get_strangle_menu_keyboard()
            )
        
        await state_manager.clear_state(user.id)
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid lot size. Please enter a positive number."
        )
        

async def handle_strangle_edit_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle SL trigger edit."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 1000:
            raise ValueError("Must be between 0 and 100")
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        
        # Store and ask for limit
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        await state_manager.set_state(user.id, 'strangle_edit_sl_limit_input')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
        
        await update.message.reply_text(
            f"<b>✏️ Edit SL Limit</b>\n\n"
            f"SL Trigger: <b>{sl_trigger}%</b>\n\n"
            f"Enter new SL limit percentage:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid input: {str(e)}")


async def handle_strangle_edit_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle SL limit edit."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 1000:
            raise ValueError("Must be between 0 and 100")
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        sl_trigger = state_data.get('sl_trigger_pct')
        
        from database.models.strategy_preset import StrategyPresetUpdate
        from database.operations.strategy_ops import update_strategy_preset
        from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
        
        update_data = StrategyPresetUpdate(
            sl_trigger_pct=sl_trigger,
            sl_limit_pct=sl_limit
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text(
                f"<b>✅ Stop Loss Updated</b>\n\n"
                f"Trigger: <b>{sl_trigger}%</b>\n"
                f"Limit: <b>{sl_limit}%</b>",
                reply_markup=get_strangle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to update",
                reply_markup=get_strangle_menu_keyboard()
            )
        
        await state_manager.clear_state(user.id)
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid input: {str(e)}")


async def handle_strangle_edit_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target trigger edit."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError("Must be between 0 and 1000")
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        
        if target_trigger == 0:
            # Disable target
            from database.models.strategy_preset import StrategyPresetUpdate
            from database.operations.strategy_ops import update_strategy_preset
            from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
            
            update_data = StrategyPresetUpdate(
                target_trigger_pct=0,
                target_limit_pct=0
            )
            success = await update_strategy_preset(strategy_id, update_data)
            
            if success:
                await update.message.reply_text(
                    "<b>✅ Target Disabled</b>",
                    reply_markup=get_strangle_menu_keyboard(),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("❌ Failed to update")
            
            await state_manager.clear_state(user.id)
        else:
            # Ask for limit
            state_data['target_trigger_pct'] = target_trigger
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'strangle_edit_target_limit_input')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"strangle_edit_{strategy_id}")]]
            
            await update.message.reply_text(
                f"<b>✏️ Edit Target Limit</b>\n\n"
                f"Target Trigger: <b>{target_trigger}%</b>\n\n"
                f"Enter target limit percentage:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid input: {str(e)}")


async def handle_strangle_edit_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle target limit edit."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError("Must be between 0 and 1000")
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        target_trigger = state_data.get('target_trigger_pct')
        
        from database.models.strategy_preset import StrategyPresetUpdate
        from database.operations.strategy_ops import update_strategy_preset
        from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
        
        update_data = StrategyPresetUpdate(
            target_trigger_pct=target_trigger,
            target_limit_pct=target_limit
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text(
                f"<b>✅ Target Updated</b>\n\n"
                f"Trigger: <b>{target_trigger}%</b>\n"
                f"Limit: <b>{target_limit}%</b>",
                reply_markup=get_strangle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to update",
                reply_markup=get_strangle_menu_keyboard()
            )
        
        await state_manager.clear_state(user.id)
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid input: {str(e)}")


async def handle_strangle_edit_otm_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle OTM value edit."""
    user = update.effective_user
    
    try:
        otm_value = float(text)
        if otm_value <= 0:
            raise ValueError("Must be positive")
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        otm_type = state_data.get('otm_type', 'percentage')
        
        if otm_type == 'numeral':
            otm_value = int(otm_value)
        
        from database.models.strategy_preset import StrategyPresetUpdate
        from database.operations.strategy_ops import update_strategy_preset
        from bot.handlers.strangle_strategy_handler import get_strangle_menu_keyboard
        
        update_data = StrategyPresetUpdate(
            otm_selection={'type': otm_type, 'value': otm_value}
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            otm_text = f"{otm_value}%" if otm_type == 'percentage' else f"{int(otm_value)} strikes"
            await update.message.reply_text(
                f"<b>✅ OTM Updated</b>\n\n"
                f"New OTM: <b>{otm_text}</b>",
                reply_markup=get_strangle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to update",
                reply_markup=get_strangle_menu_keyboard()
            )
        
        await state_manager.clear_state(user.id)
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid input: {str(e)}")
        
