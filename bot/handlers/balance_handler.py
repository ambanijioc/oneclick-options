"""
Balance display handlers.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_balance, format_error_message
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.balance_keyboards import get_balance_keyboard
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from delta.client import DeltaClient

logger = setup_logger(__name__)


@error_handler
async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle balance menu callback.
    Display wallet balance for all configured APIs.
    
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
    
    if not apis:
        await query.edit_message_text(
            "<b>💰 Balance</b>\n\n"
            "❌ No API credentials configured.\n\n"
            "Please add an API credential first.",
            reply_markup=get_balance_keyboard(),
            parse_mode='HTML'
        )
        log_user_action(user.id, "balance_view", "No APIs configured")
        return
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading balances...</b>\n\n"
        "Fetching balance data from Delta Exchange...",
        parse_mode='HTML'
    )
    
    # Fetch balances for all APIs
    balance_messages = []
    total_balance = 0
    total_unrealized_pnl = 0
    
    for api in apis:
        try:
            # Get decrypted credentials
            credentials = await get_decrypted_api_credential(str(api.id))
            if not credentials:
                balance_messages.append(
                    f"<b>❌ {api.api_name}</b>\n"
                    f"Failed to decrypt credentials\n"
                )
                continue
            
            api_key, api_secret = credentials
            
            # Create Delta client
            client = DeltaClient(api_key, api_secret)
            
            try:
                # Fetch balance
                response = await client.get_wallet_balance()
                
                if response.get('success'):
                    result = response.get('result', [])
                    
                    # Find USDT balance (most common quote currency)
                    usdt_balance = None
                    for balance_data in result:
                        if balance_data.get('asset_symbol') == 'USDT':
                            usdt_balance = balance_data
                            break
                    
                    if usdt_balance:
                        # Format balance
                        balance_text = format_balance(usdt_balance, api.api_name)
                        balance_messages.append(balance_text)
                        
                        # Add to totals
                        total_balance += float(usdt_balance.get('balance', 0))
                        total_unrealized_pnl += float(usdt_balance.get('unrealized_pnl', 0))
                    else:
                        balance_messages.append(
                            f"<b>⚠️ {api.api_name}</b>\n"
                            f"No USDT balance found\n"
                        )
                else:
                    error_msg = response.get('error', {}).get('message', 'Unknown error')
                    balance_messages.append(
                        f"<b>❌ {api.api_name}</b>\n"
                        f"Error: {error_msg}\n"
                    )
            
            finally:
                await client.close()
        
        except Exception as e:
            logger.error(f"Failed to fetch balance for API {api.id}: {e}", exc_info=True)
            balance_messages.append(
                f"<b>❌ {api.api_name}</b>\n"
                f"Error: {str(e)[:50]}\n"
            )
    
    # Construct final message
    if balance_messages:
        final_text = "<b>💰 Wallet Balance</b>\n\n"
        final_text += "\n".join(balance_messages)
        
        # Add totals if multiple APIs
        if len(apis) > 1:
            final_text += "\n" + "="*30 + "\n"
            final_text += f"<b>Combined Total:</b> ${total_balance:,.2f}\n"
            final_text += f"<b>Total Unrealized PnL:</b> "
            if total_unrealized_pnl > 0:
                final_text += f"🟢 +${total_unrealized_pnl:,.2f}\n"
            elif total_unrealized_pnl < 0:
                final_text += f"🔴 -${abs(total_unrealized_pnl):,.2f}\n"
            else:
                final_text += f"⚪ ${total_unrealized_pnl:,.2f}\n"
    else:
        final_text = (
            "<b>💰 Balance</b>\n\n"
            "❌ Failed to fetch balance data.\n\n"
            "Please try again later."
        )
    
    # Display balances
    await query.edit_message_text(
        final_text,
        reply_markup=get_balance_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "balance_view", f"Viewed {len(apis)} balance(s)")


@error_handler
async def balance_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle balance refresh callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    # Refresh is the same as viewing balance
    await balance_callback(update, context)
    
    log_user_action(update.callback_query.from_user.id, "balance_refresh", "Refreshed balances")


def register_balance_handlers(application: Application):
    """
    Register balance handlers.
    
    Args:
        application: Bot application instance
    """
    # Balance menu callback
    application.add_handler(CallbackQueryHandler(
        balance_callback,
        pattern="^menu_balance$"
    ))
    
    # Balance refresh callback
    application.add_handler(CallbackQueryHandler(
        balance_refresh_callback,
        pattern="^balance_refresh$"
    ))
    
    logger.info("Balance handlers registered")


if __name__ == "__main__":
    print("Balance handler module loaded")
  
