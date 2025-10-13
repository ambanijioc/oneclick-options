"""
Position management handler.
Displays open positions and allows setting SL/TP.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.api_operations import APIOperations
from delta.client import DeltaClient
from delta.positions import Positions
from telegram.formatters import format_positions_message
from telegram.keyboards import get_main_menu_keyboard, get_position_list_keyboard, get_api_list_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show positions for all configured APIs.
    
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
        await query.edit_message_text(
            "⏳ Fetching positions...\n\n"
            "Please wait..."
        )
        
        # Fetch positions for each API
        all_positions = []
        
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
                    # Get positions
                    positions_handler = Positions(client)
                    positions = await positions_handler.get_positions()
                    
                    if positions:
                        all_positions.append({
                            'api_name': api_name,
                            'positions': positions
                        })
                    
                finally:
                    await client.close()
                
            except Exception as e:
                logger.error(f"[show_positions] Error fetching positions for {api_name}: {e}")
        
        # Format message
        if not all_positions:
            message = "📊 **Positions**\n\nNo open positions."
        else:
            message = "📊 **Open Positions**\n\n"
            
            total_positions = 0
            for pos_info in all_positions:
                api_name = pos_info.get('api_name')
                positions = pos_info.get('positions', [])
                
                total_positions += len(positions)
                
                message += f"**{api_name}:**\n"
                message += format_positions_message(positions)
                message += "\n" + "─" * 30 + "\n\n"
            
            message += f"\n**Total Open Positions:** {total_positions}"
        
        # Add button to set SL/TP
        keyboard = get_main_menu_keyboard()
        
        if all_positions:
            # Could add a button to select API for SL/TP setting
            pass
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_positions] Displayed positions for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_positions] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error fetching positions.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Position handler module loaded")
  
