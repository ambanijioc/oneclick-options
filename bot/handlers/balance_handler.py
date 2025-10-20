"""
Balance display handlers - SIMPLIFIED VERSION
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.balance_keyboards import get_balance_keyboard
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from services.delta.client import DeltaClient

logger = setup_logger(__name__)


@error_handler
async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle balance menu callback.
    Display wallet balance + unrealized PnL from positions.
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
    total_balance_inr = 0
    total_unrealized_pnl = 0
    
    # Fixed conversion rate: 1 USD = 85 INR
    USD_TO_INR = 85.0
    
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
                # ✅ Fetch wallet balance
                wallet_response = await client.get_wallet_balance()
                
                # ✅ Fetch positions for unrealized PnL
                # Endpoint: GET /v2/positions
                positions_response = await client.get_positions()
                
                if wallet_response.get('success'):
                    result = wallet_response.get('result', [])
                    
                    # Try to find INR balance first (India API)
                    balance_data = None
                    for bal in result:
                        asset = bal.get('asset_symbol', '')
                        if asset in ['INR', 'USDT', 'USD']:
                            balance_data = bal
                            break
                    
                    if balance_data:
                        asset_symbol = balance_data.get('asset_symbol', 'INR')
                        balance = float(balance_data.get('balance', 0))
                        
                        # ✅ Calculate unrealized PnL from ALL positions
                        unrealized_pnl = 0.0
                        if positions_response.get('success'):
                            positions = positions_response.get('result', [])
                            for pos in positions:
                                # Sum unrealized PnL from each position
                                pos_unrealized_pnl = float(pos.get('unrealized_pnl', 0))
                                unrealized_pnl += pos_unrealized_pnl
                        
                        # Convert to INR
                        if asset_symbol == 'INR':
                            balance_inr = balance
                            unrealized_pnl_inr = unrealized_pnl
                        else:  # USD or USDT
                            balance_inr = balance * USD_TO_INR
                            unrealized_pnl_inr = unrealized_pnl * USD_TO_INR
                        
                        # Format balance message
                        balance_text = (
                            f"<b>💼 {api.api_name}</b>\n"
                            f"Balance: ₹{balance_inr:,.2f}\n"
                        )
                        
                        if unrealized_pnl_inr != 0:
                            if unrealized_pnl_inr > 0:
                                balance_text += f"Unrealized PnL: 🟢 +₹{unrealized_pnl_inr:,.2f}\n"
                            else:
                                balance_text += f"Unrealized PnL: 🔴 ₹{unrealized_pnl_inr:,.2f}\n"
                        
                        balance_messages.append(balance_text)
                        
                        # Add to totals
                        total_balance_inr += balance_inr
                        total_unrealized_pnl += unrealized_pnl_inr
                    else:
                        balance_messages.append(
                            f"<b>⚠️ {api.api_name}</b>\n"
                            f"No balance found\n"
                        )
                else:
                    error_msg = wallet_response.get('error', {}).get('message', 'Unknown error')
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
            final_text += f"<b>Combined Total:</b> ₹{total_balance_inr:,.2f}\n"
            final_text += f"<b>Total Unrealized PnL:</b> "
            if total_unrealized_pnl > 0:
                final_text += f"🟢 +₹{total_unrealized_pnl:,.2f}\n"
            elif total_unrealized_pnl < 0:
                final_text += f"🔴 ₹{total_unrealized_pnl:,.2f}\n"
            else:
                final_text += f"⚪ ₹{total_unrealized_pnl:,.2f}\n"
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
    """Handle balance refresh callback."""
    await balance_callback(update, context)
    log_user_action(update.callback_query.from_user.id, "balance_refresh", "Refreshed balances")


def register_balance_handlers(application: Application):
    """Register balance handlers."""
    application.add_handler(CallbackQueryHandler(
        balance_callback,
        pattern="^menu_balance$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        balance_refresh_callback,
        pattern="^balance_refresh$"
    ))
    
    logger.info("Balance handlers registered")
    
