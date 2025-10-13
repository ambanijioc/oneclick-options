"""
Manual trade execution handlers.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_error_message, escape_html, format_number
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.trade_keyboards import (
    get_api_selection_keyboard,
    get_strategy_preset_selection_keyboard,
    # get_strategy_type_keyboard
)
from bot.keyboards.strategy_keyboards import (
    get_strategy_type_keyboard  # Import from here instead
from bot.keyboards.confirmation_keyboards import get_trade_confirmation_keyboard
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from database.operations.strategy_ops import get_strategy_presets_by_type, get_strategy_preset_by_id
from database.operations.user_ops import can_user_trade_today
from delta.client import DeltaClient
from delta.utils.atm_calculator import calculate_atm_strike
from delta.utils.otm_calculator import calculate_otm_strikes

logger = setup_logger(__name__)


@error_handler
async def manual_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle manual trade menu callback.
    Display API selection.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Check trade limit
    can_trade = await can_user_trade_today(user.id)
    if not can_trade:
        await query.edit_message_text(
            "<b>⚡ Manual Trade</b>\n\n"
            "❌ Daily trade limit reached.\n\n"
            "You have reached your maximum number of trades for today. "
            "Please try again tomorrow.",
            parse_mode='HTML'
        )
        return
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    # Manual trade text
    text = (
        "<b>⚡ Manual Options Trade</b>\n\n"
        "Execute trades using your saved strategy presets.\n\n"
        "Select an API to continue:"
    )
    
    # Show API selection
    await query.edit_message_text(
        text,
        reply_markup=get_api_selection_keyboard(apis, action="trade"),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "manual_trade", "Opened manual trade menu")


@error_handler
async def trade_select_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle API selection for trade.
    Show strategy type selection.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID from callback data
    api_id = query.data.split('_')[-1]
    
    # Store API ID in context
    context.user_data['trade_api_id'] = api_id
    
    # Strategy type selection text
    text = (
        "<b>⚡ Manual Trade</b>\n\n"
        "Select strategy type:"
    )
    
    # Show strategy type selection
    await query.edit_message_text(
        text,
        reply_markup=get_strategy_type_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "trade_select_api", f"Selected API: {api_id}")


@error_handler
async def trade_strategy_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle strategy type selection.
    Show available presets.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract strategy type from callback data
    strategy_type = query.data.split('_')[-1]
    
    # Get API ID from context
    api_id = context.user_data.get('trade_api_id')
    if not api_id:
        await query.edit_message_text(
            format_error_message("Session expired. Please start over."),
            parse_mode='HTML'
        )
        return
    
    # Get presets
    presets = await get_strategy_presets_by_type(user.id, strategy_type)
    
    if not presets:
        await query.edit_message_text(
            f"<b>⚡ Manual Trade</b>\n\n"
            f"❌ No {strategy_type} presets found.\n\n"
            f"Please create a strategy preset first.",
            parse_mode='HTML'
        )
        return
    
    # Show preset selection
    text = (
        f"<b>⚡ Manual Trade - {strategy_type.capitalize()}</b>\n\n"
        f"Select a preset to execute:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_strategy_preset_selection_keyboard(presets, api_id, strategy_type),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "trade_strategy_type", f"Selected: {strategy_type}")


@error_handler
async def trade_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle preset selection.
    Calculate strikes and show trade confirmation.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID and preset ID from callback data
    parts = query.data.split('_')
    api_id = parts[2]
    preset_id = parts[3]
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Calculating trade...</b>\n\n"
        "Fetching spot price and calculating strikes...",
        parse_mode='HTML'
    )
    
    try:
        # Get preset
        preset = await get_strategy_preset_by_id(preset_id)
        if not preset:
            await query.edit_message_text(
                format_error_message("Strategy preset not found."),
                parse_mode='HTML'
            )
            return
        
        # Get API credentials
        credentials = await get_decrypted_api_credential(api_id)
        if not credentials:
            await query.edit_message_text(
                format_error_message("Failed to decrypt API credentials."),
                parse_mode='HTML'
            )
            return
        
        api_key, api_secret = credentials
        
        # Create Delta client
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Fetch spot price
            spot_price = await client.get_spot_price(preset.asset)
            
            if spot_price == 0:
                await query.edit_message_text(
                    format_error_message("Failed to fetch spot price."),
                    parse_mode='HTML'
                )
                return
            
            # Calculate strikes based on strategy type
            if preset.strategy_type == "straddle":
                atm_strike = calculate_atm_strike(
                    spot_price,
                    preset.asset,
                    preset.atm_offset
                )
                call_strike = atm_strike
                put_strike = atm_strike
            else:  # strangle
                call_strike, put_strike = calculate_otm_strikes(
                    spot_price,
                    preset.asset,
                    preset.otm_selection['type'],
                    preset.otm_selection['value']
                )
            
            # Format trade confirmation
            text = (
                f"<b>⚡ Trade Confirmation</b>\n\n"
                f"<b>Strategy:</b> {preset.strategy_type.capitalize()}\n"
                f"<b>Asset:</b> {preset.asset}\n"
                f"<b>Direction:</b> {preset.direction.upper()}\n"
                f"<b>Expiry:</b> {preset.expiry_code}\n\n"
                f"<b>Spot Price:</b> ${format_number(spot_price)}\n"
                f"<b>Call Strike:</b> ${call_strike}\n"
                f"<b>Put Strike:</b> ${put_strike}\n\n"
                f"<b>Lot Size:</b> {preset.lot_size}\n"
                f"<b>SL Trigger:</b> {preset.sl_trigger_pct}%\n"
                f"<b>SL Limit:</b> {preset.sl_limit_pct}%\n"
            )
            
            if preset.target_trigger_pct > 0:
                text += f"<b>Target:</b> {preset.target_trigger_pct}%\n"
            else:
                text += f"<b>Target:</b> None\n"
            
            text += (
                f"\n<b>⚠️ Confirm Details</b>\n"
                f"<i>Review carefully before executing</i>"
            )
            
            # Store trade details in context
            context.user_data['trade_details'] = {
                'api_id': api_id,
                'preset_id': preset_id,
                'spot_price': spot_price,
                'call_strike': call_strike,
                'put_strike': put_strike
            }
            
            # Show confirmation
            await query.edit_message_text(
                text,
                reply_markup=get_trade_confirmation_keyboard(
                    {},
                    confirm_callback=f"trade_execute_{api_id}_{preset_id}",
                    cancel_callback="menu_manual_trade"
                ),
                parse_mode='HTML'
            )
            
            log_user_action(
                user.id,
                "trade_preset_selected",
                f"Preset: {preset.name}, Strikes: {call_strike}/{put_strike}"
            )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to calculate trade: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to calculate trade.", str(e)),
            parse_mode='HTML'
        )


def register_manual_trade_handlers(application: Application):
    """
    Register manual trade handlers.
    
    Args:
        application: Bot application instance
    """
    # Manual trade menu callback
    application.add_handler(CallbackQueryHandler(
        manual_trade_callback,
        pattern="^menu_manual_trade$"
    ))
    
    # Trade API selection callback
    application.add_handler(CallbackQueryHandler(
        trade_select_api_callback,
        pattern="^trade_select_api_"
    ))
    
    # Trade strategy type callback
    application.add_handler(CallbackQueryHandler(
        trade_strategy_type_callback,
        pattern="^strategy_type_"
    ))
    
    # Trade preset callback
    application.add_handler(CallbackQueryHandler(
        trade_preset_callback,
        pattern="^trade_preset_"
    ))
    
    logger.info("Manual trade handlers registered")


if __name__ == "__main__":
    print("Manual trade handler module loaded")
          
