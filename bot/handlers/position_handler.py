"""
Position display handlers.
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
from bot.keyboards.position_keyboards import get_position_keyboard
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from delta.client import DeltaClient

logger = setup_logger(__name__)


@error_handler
async def position_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle position view callback.
    Display all open positions for configured APIs.
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
    
    if not apis:
        await query.edit_message_text(
            "<b>📊 Positions</b>\n\n"
            "❌ No API credentials configured.\n\n"
            "Please add an API credential first.",
            reply_markup=get_position_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "position_view", "No APIs configured")
        return
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading positions...</b>\n\n"
        "Fetching position data from Delta Exchange...",
        parse_mode='HTML'
    )
    
    # Fetch positions for all APIs
    position_messages = []
    total_unrealized_pnl = 0
    total_positions = 0
    
    for api in apis:
        try:
            # Get decrypted credentials
            credentials = await get_decrypted_api_credential(str(api.id))
            if not credentials:
                position_messages.append(
                    f"<b>❌ {api.api_name}</b>\n"
                    f"Failed to decrypt credentials\n"
                )
                continue
            
            api_key, api_secret = credentials
            
            # Create Delta client
            client = DeltaClient(api_key, api_secret)
            
            try:
                # Fetch positions with contract types (required for India API)
                response = await client.get_positions()
                
                if response.get('success'):
                    result = response.get('result', [])
                    
                    # Filter only active positions (non-zero size)
                    active_positions = [
                        pos for pos in result 
                        if float(pos.get('size', 0)) != 0
                    ]
                    
                    if active_positions:
                        # Format positions
                        api_position_text = f"<b>📊 {api.api_name}</b>\n\n"
                        
                        for position in active_positions:
                            size = float(position.get('size', 0))
                            entry_price = float(position.get('entry_price', 0))
                            mark_price = float(position.get('mark_price', 0))
                            unrealized_pnl = float(position.get('unrealized_pnl', 0))
                            symbol = position.get('product', {}).get('symbol', 'Unknown')
                            
                            # Position direction
                            direction = "🟢 Long" if size > 0 else "🔴 Short"
                            
                            api_position_text += (
                                f"{direction} {symbol}\n"
                                f"Size: {abs(size)}\n"
                                f"Entry: ${entry_price:,.2f}\n"
                                f"Mark: ${mark_price:,.2f}\n"
                                f"PnL: "
                            )
                            
                            if unrealized_pnl > 0:
                                api_position_text += f"🟢 +${unrealized_pnl:,.2f}\n"
                            elif unrealized_pnl < 0:
                                api_position_text += f"🔴 ${unrealized_pnl:,.2f}\n"
                            else:
                                api_position_text += f"⚪ ${unrealized_pnl:,.2f}\n"
                            
                            api_position_text += "\n"
                            
                            total_unrealized_pnl += unrealized_pnl
                            total_positions += 1
                        
                        position_messages.append(api_position_text)
                    else:
                        position_messages.append(
                            f"<b>📊 {api.api_name}</b>\n"
                            f"No open positions\n"
                        )
                else:
                    error_msg = response.get('error', {}).get('message', 'Unknown error')
                    position_messages.append(
                        f"<b>❌ {api.api_name}</b>\n"
                        f"Error: {error_msg}\n"
                    )
            
            finally:
                await client.close()
        
        except Exception as e:
            logger.error(f"Failed to fetch positions for API {api.id}: {e}", exc_info=True)
            position_messages.append(
                f"<b>❌ {api.api_name}</b>\n"
                f"Error: {str(e)[:80]}\n"
            )
    
    # Construct final message
    if position_messages:
        final_text = "<b>📊 Open Positions</b>\n\n"
        final_text += "\n".join(position_messages)
        
        # Add totals if positions exist
        if total_positions > 0 and len(apis) > 1:
            final_text += "="*30 + "\n"
            final_text += f"<b>Total Positions:</b> {total_positions}\n"
            final_text += f"<b>Total Unrealized PnL:</b> "
            if total_unrealized_pnl > 0:
                final_text += f"🟢 +${total_unrealized_pnl:,.2f}\n"
            elif total_unrealized_pnl < 0:
                final_text += f"🔴 ${total_unrealized_pnl:,.2f}\n"
            else:
                final_text += f"⚪ ${total_unrealized_pnl:,.2f}\n"
    else:
        final_text = (
            "<b>📊 Positions</b>\n\n"
            "❌ Failed to fetch position data.\n\n"
            "Please try again later."
        )
    
    # Display positions
    await query.edit_message_text(
        final_text,
        reply_markup=get_position_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "position_view", f"Viewed positions from {len(apis)} API(s)")


@error_handler
async def position_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle position refresh callback.
    """
    # Refresh is the same as viewing positions
    await position_view_callback(update, context)
    
    log_user_action(update.callback_query.from_user.id, "position_refresh", "Refreshed positions")


def register_position_handlers(application: Application):
    """
    Register position handlers.
    """
    # Position view callback
    application.add_handler(CallbackQueryHandler(
        position_view_callback,
        pattern="^menu_positions$"
    ))
    
    # Position refresh callback
    application.add_handler(CallbackQueryHandler(
        position_refresh_callback,
        pattern="^position_refresh$"
    ))
    
    logger.info("Position handlers registered")


if __name__ == "__main__":
    print("Position handler module loaded")
    
