"""
Input handlers for straddle strategy creation flow.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from bot.utils.logger import setup_logger
from bot.utils.state_manager import state_manager
from database.operations.strategy_preset import (
    create_strategy_preset,
    get_strategy_preset_by_id,
    update_strategy_preset
)
from database.models.strategy_preset import StrategyPresetUpdate
from bot.keyboards.straddle_strategy_keyboards import get_straddle_menu_keyboard

logger = setup_logger(__name__)


# ============================================================================
# CREATE NEW PRESET INPUT HANDLERS
# ============================================================================

async def handle_straddle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle straddle strategy name input."""
    user = update.effective_user
    
    await state_manager.set_state_data(user.id, {'name': text, 'strategy_type': 'straddle'})
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
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['description'] = text
    await state_manager.set_state_data(user.id, state_data)
    
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
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['lot_size'] = lot_size
        await state_manager.set_state_data(user.id, state_data)
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
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
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
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_limit_pct'] = sl_limit
        await state_manager.set_state_data(user.id, state_data)
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
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger_pct'] = target_trigger
        
        if target_trigger == 0:
            state_data['target_limit_pct'] = 0
            await state_manager.set_state_data(user.id, state_data)
            await state_manager.set_state(user.id, 'straddle_add_atm_offset')
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]]
            
            await update.message.reply_text(
                f"<b>➕ Add Straddle Strategy</b>\n\n"
                f"Enter ATM offset (in strikes):\n\n"
                f"• <code>0</code> = ATM (At The Money)\n"
                f"• <code>+1</code> = 1 strike above ATM (BTC: $200, ETH: $20)\n"
                f"• <code>-1</code> = 1 strike below ATM\n"
                f"• <code>+5</code> = 5 strikes above ATM (BTC: $1000, ETH: $100)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
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
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_limit_pct'] = target_limit
        await state_manager.set_state_data(user.id, state_data)
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
        atm_strikes = int(text)
        state_data = await state_manager.get_state_data(user.id)
        
        strike_increment = 200 if state_data['asset'] == 'BTC' else 20
        atm_offset = atm_strikes * strike_increment
        
        state_data['atm_offset'] = atm_offset
        state_data['atm_strikes'] = atm_strikes
        await state_manager.set_state_data(user.id, state_data)
        
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


# ============================================================================
# SL MONITOR PREFERENCE
# ============================================================================

async def ask_sl_monitor_preference(update, context):
    """Ask if SL monitoring should be enabled."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Enable SL-to-Cost", callback_data="straddle_sl_yes"),
            InlineKeyboardButton("❌ Disable", callback_data="straddle_sl_no")
        ],
        [InlineKeyboardButton("🔙 Cancel", callback_data="straddle_cancel")]
    ]
    
    await update.message.reply_text(
        "<b>🔔 SL-to-Cost Monitoring</b>\n\n"
        "Enable automatic SL-to-cost when trade reaches profit?\n\n"
        "<i>This will move your SL to entry price (cost) when position is in profit.</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_straddle_sl_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL monitor YES selection."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['enable_sl_monitor'] = True
    await state_manager.set_state_data(user.id, state_data)
    
    await save_straddle_preset(update, context)


async def handle_straddle_sl_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SL monitor NO selection."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    state_data = await state_manager.get_state_data(user.id)
    state_data['enable_sl_monitor'] = False
    await state_manager.set_state_data(user.id, state_data)
    
    await save_straddle_preset(update, context)


async def save_straddle_preset(update, context):
    """Save straddle preset to database."""
    if hasattr(update, 'callback_query') and update.callback_query:
        user = update.callback_query.from_user
        is_callback = True
    else:
        user = update.effective_user
        is_callback = False
    
    state_data = await state_manager.get_state_data(user.id)
    
    preset_data = {
        "user_id": user.id,
        "name": state_data['name'],
        "description": state_data.get('description', ''),
        "strategy_type": "straddle",
        "asset": state_data['asset'],
        "expiry_code": state_data['expiry'],
        "direction": state_data['direction'],
        "lot_size": state_data['lot_size'],
        "sl_trigger_pct": state_data['sl_trigger_pct'],
        "sl_limit_pct": state_data['sl_limit_pct'],
        "target_trigger_pct": state_data.get('target_trigger_pct', 0),
        "target_limit_pct": state_data.get('target_limit_pct', 0),
        "atm_offset": state_data['atm_offset'],
        "enable_sl_monitor": state_data.get('enable_sl_monitor', False),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await create_strategy_preset(preset_data)
    
    if result:
        message = (
            "✅ <b>Preset Saved!</b>\n\n"
            f"Name: <b>{state_data['name']}</b>\n"
            f"Asset: <b>{state_data['asset']}</b>\n"
            f"Direction: <b>{state_data['direction'].title()}</b>\n"
            f"SL Monitor: {'✅ <b>Enabled</b>' if state_data.get('enable_sl_monitor', False) else '❌ Disabled'}\n"
        )
        
        if is_callback:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=get_straddle_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=get_straddle_menu_keyboard(),
                parse_mode='HTML'
            )
        
        logger.info(f"Straddle preset saved: {result} | SL monitor: {state_data.get('enable_sl_monitor', False)}")
    else:
        error_msg = "❌ Failed to create strategy."
        if is_callback:
            await update.callback_query.edit_message_text(error_msg, reply_markup=get_straddle_menu_keyboard())
        else:
            await update.message.reply_text(error_msg, reply_markup=get_straddle_menu_keyboard())
    
    await state_manager.clear_state(user.id)


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
    
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text("❌ Strategy not found.")
        await state_manager.clear_state(user.id)
        return
    
    strategy = await get_strategy_preset_by_id(strategy_id)
    if not strategy:
        await update.message.reply_text("❌ Strategy not found.")
        await state_manager.clear_state(user.id)
        return
    
    update_data = StrategyPresetUpdate(name=text)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await update.message.reply_text(
            f"✅ <b>Name Updated!</b>\n\n"
            f"Old: <b>{strategy.name}</b>\n"
            f"New: <b>{text}</b>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Failed to update name.")
    
    await state_manager.clear_state(user.id)


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
    
    state_data = await state_manager.get_state_data(user.id)
    strategy_id = state_data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text("❌ Strategy not found.")
        await state_manager.clear_state(user.id)
        return
    
    update_data = StrategyPresetUpdate(description=text)
    success = await update_strategy_preset(strategy_id, update_data)
    
    if success:
        await update.message.reply_text(
            f"✅ <b>Description Updated!</b>\n\nNew: <i>{text}</i>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Failed to update description.")
    
    await state_manager.clear_state(user.id)


async def handle_straddle_edit_sl_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing SL trigger."""
    user = update.effective_user
    
    try:
        sl_trigger = float(text)
        if sl_trigger < 0 or sl_trigger > 100:
            raise ValueError()
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['sl_trigger_pct'] = sl_trigger
        await state_manager.set_state_data(user.id, state_data)
        await state_manager.set_state(user.id, 'straddle_edit_sl_limit_input')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            f"SL Trigger: <b>{sl_trigger:.1f}%</b>\n\nEnter SL limit %:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        await update.message.reply_text("❌ Invalid percentage (0-100)")


async def handle_straddle_edit_sl_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing SL limit."""
    user = update.effective_user
    
    try:
        sl_limit = float(text)
        if sl_limit < 0 or sl_limit > 100:
            raise ValueError()
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        
        if not strategy_id:
            await update.message.reply_text("❌ Strategy not found.")
            await state_manager.clear_state(user.id)
            return
        
        update_data = StrategyPresetUpdate(
            sl_trigger_pct=state_data.get('sl_trigger_pct'),
            sl_limit_pct=sl_limit
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text("✅ Stop Loss Updated!", parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Failed to update")
        
        await state_manager.clear_state(user.id)
    except:
        await update.message.reply_text("❌ Invalid percentage (0-100)")


async def handle_straddle_edit_target_trigger_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing target trigger percentage."""
    user = update.effective_user
    
    try:
        target_trigger = float(text)
        if target_trigger < 0 or target_trigger > 1000:
            raise ValueError()
        
        if target_trigger == 0:
            state_data = await state_manager.get_state_data(user.id)
            strategy_id = state_data.get('edit_strategy_id')
            
            if not strategy_id:
                await update.message.reply_text("❌ Strategy not found.")
                await state_manager.clear_state(user.id)
                return
            
            update_data = StrategyPresetUpdate(target_trigger_pct=0.0, target_limit_pct=0.0)
            success = await update_strategy_preset(strategy_id, update_data)
            
            if success:
                await update.message.reply_text("✅ <b>Target Disabled</b>", parse_mode='HTML')
            else:
                await update.message.reply_text("❌ Failed to update target.")
            
            await state_manager.clear_state(user.id)
            return
        
        state_data = await state_manager.get_state_data(user.id)
        state_data['target_trigger_pct'] = target_trigger
        await state_manager.set_state_data(user.id, state_data)
        await state_manager.set_state(user.id, 'straddle_edit_target_limit_input')
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="menu_straddle_strategy")]]
        await update.message.reply_text(
            f"Target Trigger: <b>{target_trigger:.1f}%</b>\n\nEnter target limit %:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        await update.message.reply_text("❌ Invalid percentage (0-1000)")


async def handle_straddle_edit_target_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle editing target limit percentage."""
    user = update.effective_user
    
    try:
        target_limit = float(text)
        if target_limit < 0 or target_limit > 1000:
            raise ValueError()
        
        state_data = await state_manager.get_state_data(user.id)
        strategy_id = state_data.get('edit_strategy_id')
        
        if not strategy_id:
            await update.message.reply_text("❌ Strategy not found.")
            await state_manager.clear_state(user.id)
            return
        
        update_data = StrategyPresetUpdate(
            target_trigger_pct=state_data.get('target_trigger_pct'),
            target_limit_pct=target_limit
        )
        success = await update_strategy_preset(strategy_id, update_data)
        
        if success:
            await update.message.reply_text("✅ Target Updated!", parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Failed to update target.")
        
        await state_manager.clear_state(user.id)
    except:
        await update.message.reply_text("❌ Invalid percentage (0-1000)")
