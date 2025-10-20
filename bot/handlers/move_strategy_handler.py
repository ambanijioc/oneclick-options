"""
MOVE Strategy Management Handler
Handles creation, editing, deletion, and viewing of MOVE option strategies.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.state_manager import state_manager
from bot.validators.user_validator import check_user_authorization
from database.operations.move_strategy_ops import (
    create_move_strategy,
    get_move_strategies,
    get_move_strategy,
    update_move_strategy,
    delete_move_strategy
)

logger = setup_logger(__name__)


def get_move_menu_keyboard():
    """Get MOVE strategy management menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Strategy", callback_data="move_add")],
        [InlineKeyboardButton("✏️ Edit Strategy", callback_data="move_edit_list")],
        [InlineKeyboardButton("🗑️ Delete Strategy", callback_data="move_delete_list")],
        [InlineKeyboardButton("👁️ View Strategies", callback_data="move_view")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_strategy_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main MOVE strategy menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Opened MOVE strategy menu")
    
    await query.edit_message_text(
        "<b>🎯 MOVE Strategy Management</b>\n\n"
        "Manage your MOVE option strategies:\n\n"
        "➕ <b>Add Strategy</b> - Create new MOVE strategy\n"
        "✏️ <b>Edit Strategy</b> - Modify existing strategy\n"
        "🗑️ <b>Delete Strategy</b> - Remove strategy\n"
        "👁️ <b>View Strategies</b> - See all your strategies\n\n"
        "<i>Select an option below:</i>",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )


# ==================== ADD STRATEGY FLOW ====================

@error_handler
async def move_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start MOVE strategy addition flow."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    log_user_action(user.id, "Started adding MOVE strategy")
    
    # Clear any existing state data
    await state_manager.clear_state(user.id)
    
    # Set state to collect name
    await state_manager.set_state(user.id, 'move_add_name')
    await state_manager.set_state_data(user.id, {'strategy_type': 'move'})
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    await query.edit_message_text(
        "<b>📝 Add MOVE Strategy</b>\n\n"
        "<b>Step 1/7: Strategy Name</b>\n\n"
        "Enter a unique name for your MOVE strategy:\n\n"
        "<i>Example: BTC 8AM MOVE, ETH Daily MOVE</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_skip_description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip description and move to asset selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Move to asset selection
    await state_manager.set_state(user.id, 'move_add_asset')
    
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data="move_asset_BTC")],
        [InlineKeyboardButton("Ξ ETH", callback_data="move_asset_ETH")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"<b>📝 Add MOVE Strategy</b>\n\n"
        f"<b>Step 2/7: Asset Selection</b>\n\n"
        f"<b>Name:</b> {data.get('name')}\n\n"
        f"<b>Select underlying asset:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection (BTC/ETH)."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[2]  # move_asset_BTC -> BTC
    
    # Store asset
    await state_manager.set_state_data(user.id, {'asset': asset})
    
    logger.info(f"✅ MOVE asset selected: {asset}")
    
    # Move to expiry selection
    await state_manager.set_state(user.id, 'move_add_expiry')
    
    keyboard = [
        [InlineKeyboardButton("📅 Daily", callback_data="move_expiry_daily")],
        [InlineKeyboardButton("📆 Weekly", callback_data="move_expiry_weekly")],
        [InlineKeyboardButton("📊 Monthly", callback_data="move_expiry_monthly")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"<b>📝 Add MOVE Strategy</b>\n\n"
        f"<b>Step 3/7: Expiry Selection</b>\n\n"
        f"<b>Name:</b> {data.get('name')}\n"
        f"<b>Asset:</b> {asset}\n\n"
        f"<b>Select expiry type:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expiry selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    expiry = query.data.split('_')[2]  # move_expiry_daily -> daily
    
    # Store expiry
    await state_manager.set_state_data(user.id, {'expiry': expiry})
    
    logger.info(f"✅ MOVE expiry selected: {expiry}")
    
    # Move to direction selection
    await state_manager.set_state(user.id, 'move_add_direction')
    
    keyboard = [
        [InlineKeyboardButton("🟢 Long (Buy)", callback_data="move_direction_long")],
        [InlineKeyboardButton("🔴 Short (Sell)", callback_data="move_direction_short")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"<b>📝 Add MOVE Strategy</b>\n\n"
        f"<b>Step 4/7: Direction Selection</b>\n\n"
        f"<b>Name:</b> {data.get('name')}\n"
        f"<b>Asset:</b> {data.get('asset')}\n"
        f"<b>Expiry:</b> {expiry.capitalize()}\n\n"
        f"<b>Select position direction:</b>\n\n"
        f"🟢 <b>Long:</b> Buy MOVE contract (profit from volatility)\n"
        f"🔴 <b>Short:</b> Sell MOVE contract (profit from low volatility)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


@error_handler
async def move_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    direction = query.data.split('_')[2]  # move_direction_long -> long
    
    # Store direction
    await state_manager.set_state_data(user.id, {'direction': direction})
    
    logger.info(f"✅ MOVE direction selected: {direction}")
    
    # Move to ATM offset input
    await state_manager.set_state(user.id, 'move_add_atm_offset')
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    data = await state_manager.get_state_data(user.id)
    
    await query.edit_message_text(
        f"<b>📝 Add MOVE Strategy</b>\n\n"
        f"<b>Step 5/7: Strike Selection</b>\n\n"
        f"<b>Name:</b> {data.get('name')}\n"
        f"<b>Asset:</b> {data.get('asset')}\n"
        f"<b>Expiry:</b> {data.get('expiry').capitalize()}\n"
        f"<b>Direction:</b> {direction.capitalize()}\n\n"
        f"<b>Enter ATM offset</b> (strike selection method):\n\n"
        f"<i>Examples:</i>\n"
        f"• <code>0</code> - Exact ATM\n"
        f"• <code>1</code> - 1 strike above ATM\n"
        f"• <code>-1</code> - 1 strike below ATM\n\n"
        f"<i>Range: -10 to +10</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def show_move_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation before saving."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    
    # ✅ Safe extraction with None guards
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
    
    # ✅ Safe capitalize (prevents None.capitalize() error)
    expiry_display = expiry.capitalize() if expiry else "N/A"
    direction_display = direction.capitalize() if direction else "N/A"
    
    # Build confirmation message
    text = (
        f"<b>✅ MOVE Strategy - Final Confirmation</b>\n\n"
        f"<b>📋 Details:</b>\n"
        f"• <b>Name:</b> {name}\n"
    )
    
    if description:
        text += f"• <b>Description:</b> {description}\n"
    
    text += (
        f"• <b>Asset:</b> {asset}\n"
        f"• <b>Expiry:</b> {expiry_display}\n"
        f"• <b>Direction:</b> {direction_display}\n"
        f"• <b>ATM Offset:</b> {atm_offset}\n\n"
        f"<b>📊 Risk Management:</b>\n"
        f"• <b>SL Trigger:</b> {sl_trigger}%\n"
        f"• <b>SL Limit:</b> {sl_limit}%\n"
    )
    
    if target_trigger is not None:
        text += (
            f"• <b>Target Trigger:</b> {target_trigger}%\n"
            f"• <b>Target Limit:</b> {target_limit}%\n"
        )
    
    text += "\n<b>Save this strategy?</b>"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="move_confirm_save")],
        [InlineKeyboardButton("❌ Cancel", callback_data="move_cancel")]
    ]
    
    # ✅ KEY FIX: Handle both button clicks (callback_query) and text messages
    if update.callback_query:
        # User clicked "Skip Target" button
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        # User entered text input (last step in flow)
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


@error_handler
async def move_confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the MOVE strategy to database."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = await state_manager.get_state_data(user.id)
    
    try:
        # ✅ FIX: Build strategy_data with CORRECT field names matching database
        strategy_data = {
            'strategy_name': data.get('name'),  # ✅ 'strategy_name' NOT 'name'
            'description': data.get('description', ''),
            'asset': data.get('asset'),
            'expiry': data.get('expiry', 'daily'),  # ✅ Add expiry field
            'direction': data.get('direction'),
            'atm_offset': data.get('atm_offset', 0),
            'stop_loss_trigger': data.get('sl_trigger_percent'),  # ✅ Match DB field names
            'stop_loss_limit': data.get('sl_limit_percent'),
            'target_trigger': data.get('target_trigger_percent'),
            'target_limit': data.get('target_limit_percent')
        }
        
        # ✅ FIX: Pass BOTH user.id AND strategy_data
        result = await create_move_strategy(user.id, strategy_data)
        
        if not result:
            raise Exception("Failed to save strategy to database")
        
        # Clear state
        await state_manager.clear_state(user.id)
        
        log_user_action(user.id, f"Created MOVE strategy: {data.get('name')}")
        
        # ✅ FIX: Safe direction display
        direction = data.get('direction')
        direction_display = direction.capitalize() if isinstance(direction, str) and direction else "N/A"
        
        await query.edit_message_text(
            f"<b>✅ MOVE Strategy Created!</b>\n\n"
            f"<b>Name:</b> {data.get('name')}\n"
            f"<b>Asset:</b> {data.get('asset')}\n"
            f"<b>Direction:</b> {direction_display}\n\n"
            f"Strategy has been saved successfully!",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error creating MOVE strategy: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error creating strategy: {str(e)}\n\n"
            f"Please try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def move_skip_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip target and proceed to save."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Set null targets
    await state_manager.set_state_data(user.id, {
        'target_trigger_percent': None,
        'target_limit_percent': None
    })
    
    # Show confirmation
    from .move_input_handlers import handle_move_target_limit_input
    await show_move_confirmation(update, context)


@error_handler
async def move_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel MOVE strategy operation."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Clear state
    await state_manager.clear_state(user.id)
    
    log_user_action(user.id, "Cancelled MOVE strategy operation")
    
    await query.edit_message_text(
        "❌ <b>Operation Cancelled</b>\n\n"
        "MOVE strategy operation has been cancelled.",
        reply_markup=get_move_menu_keyboard(),
        parse_mode='HTML'
    )


# ==================== VIEW STRATEGIES ====================

@error_handler
async def move_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all MOVE strategies for user."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    try:
        # Get all MOVE strategies for user
        strategies = await get_move_strategies(user.id)
        
        if not strategies:
            await query.edit_message_text(
                "<b>📋 MOVE Strategies</b>\n\n"
                "No MOVE strategies found.\n\n"
                "Use <b>➕ Add Strategy</b> to create one!",
                reply_markup=get_move_menu_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Build strategies list
        text = "<b>📋 Your MOVE Strategies</b>\n\n"
        
        for idx, strategy in enumerate(strategies, 1):
            text += f"<b>{idx}. {strategy.get('name')}</b>\n"
            text += f"   • Asset: {strategy.get('asset')}\n"
            # ✅ NEW (safer):
            direction = strategy.get('direction', 'unknown')
            expiry = strategy.get('expiry', 'unknown')  # ✅ CORRECT - matches database field
            text += f"   • Direction: {direction.capitalize() if direction else 'N/A'}\n"
            text += f"   • Expiry: {expiry.capitalize() if expiry else 'N/A'}\n"
            
            if strategy.get('description'):
                desc = strategy.get('description')[:50]
                text += f"   • Description: {desc}...\n" if len(strategy.get('description')) > 50 else f"   • Description: {desc}\n"
            
            text += f"   • SL: {strategy.get('sl_trigger_percent')}% / {strategy.get('sl_limit_percent')}%\n"
            
            if strategy.get('target_trigger_percent'):
                text += f"   • Target: {strategy.get('target_trigger_percent')}% / {strategy.get('target_limit_percent')}%\n"
            
            text += "\n"
        
        text += f"<b>Total:</b> {len(strategies)} strateg{'y' if len(strategies) == 1 else 'ies'}"
        
        log_user_action(user.id, f"Viewed {len(strategies)} MOVE strategies")
        
        await query.edit_message_text(
            text,
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error viewing MOVE strategies: {e}")
        await query.edit_message_text(
            f"❌ Error loading strategies: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


# ==================== EDIT STRATEGY FLOW ====================

@error_handler
async def move_edit_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of MOVE strategies to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    try:
        strategies = await get_move_strategies(user.id)
        
        if not strategies:
            await query.edit_message_text(
                "<b>✏️ Edit MOVE Strategy</b>\n\n"
                "No strategies found to edit.",
                reply_markup=get_move_menu_keyboard(),
                parse_mode='HTML'
            )
            return
        
        keyboard = []
        for strategy in strategies:
            strategy_id = str(strategy.get('_id'))
            name = strategy.get('name')
            asset = strategy.get('asset')
            direction = strategy.get('direction')
            
            button_text = f"{name} ({asset} - {direction.capitalize()})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"move_edit_{strategy_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_menu")])
        
        await query.edit_message_text(
            "<b>✏️ Edit MOVE Strategy</b>\n\n"
            "Select a strategy to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error listing MOVE strategies for edit: {e}")
        await query.edit_message_text(
            f"❌ Error loading strategies: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def move_edit_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle selection of strategy to edit."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[2]  # move_edit_{id}
    
    try:
        strategy = await get_move_strategy(strategy_id)
        
        if not strategy or strategy.get('user_id') != user.id:
            await query.edit_message_text(
                "❌ Strategy not found or access denied.",
                reply_markup=get_move_menu_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Store strategy ID in state
        await state_manager.set_state_data(user.id, {'edit_strategy_id': strategy_id})
        
        # Show edit options
        keyboard = [
            [InlineKeyboardButton("📝 Edit Name", callback_data="move_edit_field_name")],
            [InlineKeyboardButton("📄 Edit Description", callback_data="move_edit_field_description")],
            [InlineKeyboardButton("💰 Edit Asset", callback_data="move_edit_field_asset")],
            [InlineKeyboardButton("📅 Edit Expiry", callback_data="move_edit_field_expiry")],
            [InlineKeyboardButton("🎯 Edit Direction", callback_data="move_edit_field_direction")],
            [InlineKeyboardButton("📊 Edit ATM Offset", callback_data="move_edit_field_atm_offset")],
            [InlineKeyboardButton("🔴 Edit SL Trigger", callback_data="move_edit_field_sl_trigger")],
            [InlineKeyboardButton("🔴 Edit SL Limit", callback_data="move_edit_field_sl_limit")],
            [InlineKeyboardButton("🟢 Edit Target Trigger", callback_data="move_edit_field_target_trigger")],
            [InlineKeyboardButton("🟢 Edit Target Limit", callback_data="move_edit_field_target_limit")],
            [InlineKeyboardButton("🔙 Back", callback_data="move_edit_list")]
        ]
        
        text = (
            f"<b>✏️ Edit: {strategy.get('name')}</b>\n\n"
            f"<b>Current Settings:</b>\n"
            f"• <b>Asset:</b> {strategy.get('asset')}\n"
            f"• <b>Expiry:</b> {strategy.get('expiry_type').capitalize()}\n"
            f"• <b>Direction:</b> {strategy.get('direction').capitalize()}\n"
            f"• <b>ATM Offset:</b> {strategy.get('atm_offset')}\n"
            f"• <b>SL:</b> {strategy.get('sl_trigger_percent')}% / {strategy.get('sl_limit_percent')}%\n"
        )
        
        if strategy.get('target_trigger_percent'):
            text += f"• <b>Target:</b> {strategy.get('target_trigger_percent')}% / {strategy.get('target_limit_percent')}%\n"
        
        text += "\n<b>Select field to edit:</b>"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error selecting MOVE strategy for edit: {e}")
        await query.edit_message_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def move_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit field selection."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    field = '_'.join(query.data.split('_')[3:])  # move_edit_field_name -> name
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('edit_strategy_id')
    
    if not strategy_id:
        await query.edit_message_text(
            "❌ Session expired. Please try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    try:
        strategy = await get_move_strategy(strategy_id)
        
        # Handle different field types
        if field in ['asset', 'expiry', 'direction']:
            # Button-based selection
            if field == 'asset':
                keyboard = [
                    [InlineKeyboardButton("₿ BTC", callback_data=f"move_edit_save_asset_BTC")],
                    [InlineKeyboardButton("Ξ ETH", callback_data=f"move_edit_save_asset_ETH")],
                    [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
                ]
                prompt = "Select new asset:"
            
            elif field == 'expiry':
                keyboard = [
                    [InlineKeyboardButton("📅 Daily", callback_data=f"move_edit_save_expiry_daily")],
                    [InlineKeyboardButton("📆 Weekly", callback_data=f"move_edit_save_expiry_weekly")],
                    [InlineKeyboardButton("📊 Monthly", callback_data=f"move_edit_save_expiry_monthly")],
                    [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
                ]
                prompt = "Select new expiry:"
            
            elif field == 'direction':
                keyboard = [
                    [InlineKeyboardButton("🟢 Long", callback_data=f"move_edit_save_direction_long")],
                    [InlineKeyboardButton("🔴 Short", callback_data=f"move_edit_save_direction_short")],
                    [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
                ]
                prompt = "Select new direction:"
            
            await query.edit_message_text(
                f"<b>✏️ Edit {field.replace('_', ' ').title()}</b>\n\n"
                f"<b>Current:</b> {strategy.get(field if field != 'expiry' else 'expiry_type')}\n\n"
                f"{prompt}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        
        else:
            # Text input fields
            state_map = {
                'name': 'move_edit_name_input',
                'description': 'move_edit_desc_input',
                'atm_offset': 'move_edit_atm_offset_input',
                'sl_trigger': 'move_edit_sl_trigger_input',
                'sl_limit': 'move_edit_sl_limit_input',
                'target_trigger': 'move_edit_target_trigger_input',
                'target_limit': 'move_edit_target_limit_input'
            }
            
            await state_manager.set_state(user.id, state_map.get(field))
            
            keyboard = [
                [InlineKeyboardButton("❌ Cancel", callback_data=f"move_edit_{strategy_id}")]
            ]
            
            field_prompts = {
                'name': f"Current: {strategy.get('name')}\n\nEnter new name:",
                'description': f"Current: {strategy.get('description', 'None')}\n\nEnter new description:",
                'atm_offset': f"Current: {strategy.get('atm_offset')}\n\nEnter new ATM offset (-10 to 10):",
                'sl_trigger': f"Current: {strategy.get('sl_trigger_percent')}%\n\nEnter new SL trigger %:",
                'sl_limit': f"Current: {strategy.get('sl_limit_percent')}%\n\nEnter new SL limit %:",
                'target_trigger': f"Current: {strategy.get('target_trigger_percent')}%\n\nEnter new target trigger %:",
                'target_limit': f"Current: {strategy.get('target_limit_percent')}%\n\nEnter new target limit %:"
            }
            
            await query.edit_message_text(
                f"<b>✏️ Edit {field.replace('_', ' ').title()}</b>\n\n"
                f"{field_prompts.get(field)}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Error editing MOVE field: {e}")
        await query.edit_message_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def move_edit_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button-based edit saves (asset, expiry, direction)."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    parts = query.data.split('_')  # move_edit_save_asset_BTC
    field = parts[3]
    value = parts[4]
    
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('edit_strategy_id')
    
    if not strategy_id:
        await query.edit_message_text(
            "❌ Session expired. Please try again.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    try:
        # Map field names
        field_map = {
            'asset': 'asset',
            'expiry': 'expiry_type',
            'direction': 'direction'
        }
        
        # Update strategy
        update_data = {field_map.get(field): value}
        await update_move_strategy(strategy_id, update_data)
        
        log_user_action(user.id, f"Updated MOVE strategy {field}: {value}")
        
        # Show success and return to strategy edit menu
        strategy = await get_move_strategy(strategy_id)
        
        await query.edit_message_text(
            f"<b>✅ Updated Successfully!</b>\n\n"
            f"<b>{field.title()}:</b> {value}\n\n"
            f"Strategy <b>{strategy.get('name')}</b> has been updated.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Continue Editing", callback_data=f"move_edit_{strategy_id}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="move_menu")]
            ]),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error saving MOVE edit: {e}")
        await query.edit_message_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


async def save_move_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save text-based edit (called from input handlers)."""
    user = update.effective_user
    data = await state_manager.get_state_data(user.id)
    strategy_id = data.get('edit_strategy_id')
    
    if not strategy_id:
        await update.message.reply_text(
            "❌ Session expired. Please try again.",
            parse_mode='HTML'
        )
        return
    
    try:
        # Map edit fields to database fields
        field_map = {
            'edit_name': 'name',
            'edit_description': 'description',
            'edit_atm_offset': 'atm_offset',
            'edit_sl_trigger': 'sl_trigger_percent',
            'edit_sl_limit': 'sl_limit_percent',
            'edit_target_trigger': 'target_trigger_percent',
            'edit_target_limit': 'target_limit_percent'
        }
        
        # Build update data
        update_data = {}
        for edit_key, db_key in field_map.items():
            if edit_key in data:
                update_data[db_key] = data[edit_key]
        
        # Update strategy
        await update_move_strategy(strategy_id, update_data)
        
        # Clear edit data from state
        await state_manager.clear_state(user.id)
        
        strategy = await get_move_strategy(strategy_id)
        
        log_user_action(user.id, f"Updated MOVE strategy: {strategy.get('name')}")
        
        keyboard = [
            [InlineKeyboardButton("✏️ Continue Editing", callback_data=f"move_edit_{strategy_id}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="move_menu")]
        ]
        
        await update.message.reply_text(
            f"<b>✅ Updated Successfully!</b>\n\n"
            f"Strategy <b>{strategy.get('name')}</b> has been updated.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error saving MOVE edit: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            parse_mode='HTML'
            )


# ==================== DELETE STRATEGY FLOW ====================

@error_handler
async def move_delete_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of MOVE strategies to delete."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    try:
        strategies = await get_move_strategies(user.id)
        
        if not strategies:
            await query.edit_message_text(
                "<b>🗑️ Delete MOVE Strategy</b>\n\n"
                "No strategies found to delete.",
                reply_markup=get_move_menu_keyboard(),
                parse_mode='HTML'
            )
            return
        
        keyboard = []
        for strategy in strategies:
            strategy_id = str(strategy.get('_id'))
            name = strategy.get('name')
            asset = strategy.get('asset')
            direction = strategy.get('direction')
            
            button_text = f"❌ {name} ({asset} - {direction.capitalize()})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"move_delete_{strategy_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="move_menu")])
        
        await query.edit_message_text(
            "<b>🗑️ Delete MOVE Strategy</b>\n\n"
            "⚠️ <b>Warning:</b> This action cannot be undone!\n\n"
            "Select a strategy to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error listing MOVE strategies for deletion: {e}")
        await query.edit_message_text(
            f"❌ Error loading strategies: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def move_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm deletion of MOVE strategy."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[2]  # move_delete_{id}
    
    try:
        strategy = await get_move_strategy(strategy_id)
        
        if not strategy or strategy.get('user_id') != user.id:
            await query.edit_message_text(
                "❌ Strategy not found or access denied.",
                reply_markup=get_move_menu_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Show confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"move_delete_confirmed_{strategy_id}")],
            [InlineKeyboardButton("❌ No, Cancel", callback_data="move_delete_list")]
        ]
        
        await query.edit_message_text(
            f"<b>⚠️ Confirm Deletion</b>\n\n"
            f"Are you sure you want to delete this strategy?\n\n"
            f"<b>Name:</b> {strategy.get('name')}\n"
            f"<b>Asset:</b> {strategy.get('asset')}\n"
            f"<b>Direction:</b> {strategy.get('direction').capitalize()}\n\n"
            f"<i>This action cannot be undone!</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error confirming MOVE strategy deletion: {e}")
        await query.edit_message_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


@error_handler
async def move_delete_confirmed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute deletion of MOVE strategy."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    strategy_id = query.data.split('_')[3]  # move_delete_confirmed_{id}
    
    try:
        strategy = await get_move_strategy(strategy_id)
        
        if not strategy or strategy.get('user_id') != user.id:
            await query.edit_message_text(
                "❌ Strategy not found or access denied.",
                reply_markup=get_move_menu_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Delete strategy
        strategy_name = strategy.get('name')
        await delete_move_strategy(strategy_id)
        
        log_user_action(user.id, f"Deleted MOVE strategy: {strategy_name}")
        
        await query.edit_message_text(
            f"<b>✅ Strategy Deleted</b>\n\n"
            f"<b>{strategy_name}</b> has been successfully deleted.",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error deleting MOVE strategy: {e}")
        await query.edit_message_text(
            f"❌ Error deleting strategy: {str(e)}",
            reply_markup=get_move_menu_keyboard(),
            parse_mode='HTML'
        )


# ==================== HANDLER REGISTRATION ====================

def register_move_strategy_handlers(application):
    """Register all MOVE strategy callback handlers."""
    from telegram.ext import CallbackQueryHandler
    
    handlers = [
        # Main menu
        CallbackQueryHandler(move_strategy_menu_callback, pattern="^move_menu$"),
        
        # Add strategy flow
        CallbackQueryHandler(move_add_callback, pattern="^move_add$"),
        CallbackQueryHandler(move_skip_description_callback, pattern="^move_skip_description$"),
        CallbackQueryHandler(move_asset_callback, pattern="^move_asset_"),
        CallbackQueryHandler(move_expiry_callback, pattern="^move_expiry_"),
        CallbackQueryHandler(move_direction_callback, pattern="^move_direction_"),
        CallbackQueryHandler(move_confirm_save_callback, pattern="^move_confirm_save$"),
        CallbackQueryHandler(move_skip_target_callback, pattern="^move_skip_target$"),
        CallbackQueryHandler(move_cancel_callback, pattern="^move_cancel$"),
        
        # View strategies
        CallbackQueryHandler(move_view_callback, pattern="^move_view$"),
        
        # Edit strategy flow
        CallbackQueryHandler(move_edit_list_callback, pattern="^move_edit_list$"),
        CallbackQueryHandler(move_edit_select_callback, pattern="^move_edit_[a-f0-9]{24}$"),
        CallbackQueryHandler(move_edit_field_callback, pattern="^move_edit_field_"),
        CallbackQueryHandler(move_edit_save_callback, pattern="^move_edit_save_"),
        
        # Delete strategy flow
        CallbackQueryHandler(move_delete_list_callback, pattern="^move_delete_list$"),
        CallbackQueryHandler(move_delete_confirm_callback, pattern="^move_delete_[a-f0-9]{24}$"),
        CallbackQueryHandler(move_delete_confirmed_callback, pattern="^move_delete_confirmed_"),
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    logger.info("✅ MOVE strategy handlers registered")
    
