"""
Position management handlers.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_position, format_error_message
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.position_keyboards import (
    get_position_list_keyboard,
    get_position_action_keyboard,
    get_position_detail_keyboard,
    get_sl_target_type_keyboard
)
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from delta.client import DeltaClient

logger = setup_logger(__name__)


@error_handler
async def positions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle positions menu callback.
    Display API selection for viewing positions.
    
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
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    # Position selection text
    text = (
        "<b>📊 Positions</b>\n\n"
        f"Select an API to view positions:"
    )
    
    # Show API selection
    await query.edit_message_text(
        text,
        reply_markup=get_position_list_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "positions_menu", "Opened positions menu")


@error_handler
async def position_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle position view callback.
    Display positions for selected API.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID from callback data
    api_id = query.data.split('_')[-1]
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading positions...</b>\n\n"
        "Fetching position data from Delta Exchange...",
        parse_mode='HTML'
    )
    
    try:
        # Get API credentials
        credentials = await get_decrypted_api_credential(api_id)
        if not credentials:
            await query.edit_message_text(
                format_error_message(
                    "Failed to decrypt API credentials.",
                    "Please try again or reconfigure the API."
                ),
                parse_mode='HTML'
            )
            return
        
        api_key, api_secret = credentials
        
        # Create Delta client
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Fetch positions
            response = await client.get_positions()
            
            if not response.get('success'):
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    format_error_message(f"Failed to fetch positions: {error_msg}"),
                    parse_mode='HTML'
                )
                return
            
            positions = response.get('result', [])
            
            # Filter out zero positions
            active_positions = [p for p in positions if p.get('size', 0) != 0]
            
            if not active_positions:
                await query.edit_message_text(
                    "<b>📊 Positions</b>\n\n"
                    "❌ No open positions found.\n\n"
                    "All positions are closed or empty.",
                    reply_markup=get_position_detail_keyboard(api_id),
                    parse_mode='HTML'
                )
                log_user_action(user.id, "position_view", f"No positions for API {api_id}")
                return
            
            # Format positions
            position_text = "<b>📊 Open Positions</b>\n\n"
            
            for i, pos in enumerate(active_positions):
                position_text += format_position(pos, i) + "\n\n"
            
            # Show positions with action keyboard
            await query.edit_message_text(
                position_text,
                reply_markup=get_position_detail_keyboard(api_id),
                parse_mode='HTML'
            )
            
            log_user_action(
                user.id,
                "position_view",
                f"Viewed {len(active_positions)} position(s) for API {api_id}"
            )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch positions: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to fetch positions.", str(e)),
            parse_mode='HTML'
        )


@error_handler
async def position_sl_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle position SL/target callback.
    Show position selection for setting SL/target.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID from callback data
    api_id = query.data.split('_')[-1]
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading positions...</b>",
        parse_mode='HTML'
    )
    
    try:
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
            # Fetch positions
            response = await client.get_positions()
            
            if not response.get('success'):
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    format_error_message(f"Failed to fetch positions: {error_msg}"),
                    parse_mode='HTML'
                )
                return
            
            positions = response.get('result', [])
            
            # Filter active positions
            active_positions = [p for p in positions if p.get('size', 0) != 0]
            
            if not active_positions:
                await query.edit_message_text(
                    "<b>🎯 Set Stoploss & Target</b>\n\n"
                    "❌ No open positions found.\n\n"
                    "You need open positions to set stop-loss and target.",
                    parse_mode='HTML'
                )
                return
            
            # Show position selection
            text = (
                "<b>🎯 Set Stoploss & Target</b>\n\n"
                "Select a position to set stop-loss and target:"
            )
            
            await query.edit_message_text(
                text,
                reply_markup=get_position_action_keyboard(api_id, active_positions),
                parse_mode='HTML'
            )
            
            log_user_action(
                user.id,
                "position_sl_target",
                f"Selecting position for SL/target (API {api_id})"
            )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch positions for SL/target: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to fetch positions.", str(e)),
            parse_mode='HTML'
        )


@error_handler
async def position_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle position selection callback.
    Show SL/target type options.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID and position index from callback data
    parts = query.data.split('_')
    api_id = parts[2]
    position_index = int(parts[3])
    
    # Show SL/target type selection
    text = (
        "<b>🎯 Set Stoploss & Target</b>\n\n"
        "Choose how to set stop-loss and target:\n\n"
        "<b>📝 Set Manually:</b> Enter custom SL and target percentages\n\n"
        "<b>💰 SL to Cost:</b> Move stop-loss to breakeven (entry price)"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_sl_target_type_keyboard(api_id, position_index),
        parse_mode='HTML'
    )
    
    log_user_action(
        user.id,
        "position_select",
        f"Selected position {position_index} for SL/target"
    )


def register_position_handlers(application: Application):
    """
    Register position handlers.
    
    Args:
        application: Bot application instance
    """
    # Positions menu callback
    application.add_handler(CallbackQueryHandler(
        positions_callback,
        pattern="^menu_positions$"
    ))
    
    # Position view callback
    application.add_handler(CallbackQueryHandler(
        position_view_callback,
        pattern="^position_view_"
    ))
    
    # Position SL/target callback
    application.add_handler(CallbackQueryHandler(
        position_sl_target_callback,
        pattern="^position_sl_target_"
    ))
    
    # Position selection callback
    application.add_handler(CallbackQueryHandler(
        position_select_callback,
        pattern="^position_select_"
    ))
    
    logger.info("Position handlers registered")


if __name__ == "__main__":
    print("Position handler module loaded")
          
