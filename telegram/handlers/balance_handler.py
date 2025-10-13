"""
Balance and wallet handler.
Displays account balance and margin information.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.api_operations import APIOperations
from delta.client import DeltaClient
from delta.balance import Balance
from telegram.formatters import format_balance_message
from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show balance for all configured APIs.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        
        # Get all APIs
        api_ops = APIOperations()
        apis = await api_ops.get_all_apis(user_id)
        
        if not apis:
            await query.edit_message_text(
                "❌ No API credentials configured.\n\n"
                "Please add your Delta Exchange API credentials first.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Show loading message
        loading_msg = await query.edit_message_text(
            "⏳ Fetching balance information...\n\n"
            "Please wait..."
        )
        
        # Fetch balance for each API
        all_balances = []
        
        for api in apis:
            try:
                api_name = api.get('api_name')
                
                # Get credentials with secret
                api_creds = await api_ops.get_api_by_name(
                    user_id=user_id,
                    api_name=api_name,
                    include_secret=True
                )
                
                if not api_creds:
                    continue
                
                # Create client
                client = DeltaClient(
                    api_key=api_creds.get('api_key'),
                    api_secret=api_creds.get('api_secret')
                )
                
                try:
                    # Get balance
                    balance_handler = Balance(client)
                    balance_data = await balance_handler.get_margin_info()
                    
                    if balance_data:
                        all_balances.append({
                            'api_name': api_name,
                            'data': balance_data
                        })
                    
                finally:
                    await client.close()
                
            except Exception as e:
                logger.error(f"[show_balance] Error fetching balance for {api_name}: {e}")
                all_balances.append({
                    'api_name': api_name,
                    'error': str(e)
                })
        
        # Format message
        if not all_balances:
            message = "❌ Could not fetch balance information.\n\nPlease check your API credentials."
        else:
            message = "💰 **Account Balances**\n\n"
            
            for balance_info in all_balances:
                api_name = balance_info.get('api_name')
                
                if 'error' in balance_info:
                    message += f"**{api_name}:**\n❌ Error: {balance_info['error']}\n\n"
                else:
                    message += f"**{api_name}:**\n"
                    message += format_balance_message(balance_info.get('data'))
                    message += "\n\n" + "─" * 30 + "\n\n"
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_balance] Displayed balance for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_balance] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error fetching balance information.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Balance handler module loaded")
  
