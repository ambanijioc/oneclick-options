"""
Order management handler.
Displays open orders and order history.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.api_operations import APIOperations
from delta.client import DeltaClient
from delta.orders import Orders
from telegram.keyboards import get_main_menu_keyboard
from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show open orders for all configured APIs.
    
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
                "❌ No API credentials configured.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Show loading message
        await query.edit_message_text(
            "⏳ Fetching orders...\n\n"
            "Please wait..."
        )
        
        # Fetch orders for each API
        all_orders = []
        
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
                    # Get orders
                    orders_handler = Orders(client)
                    orders = await orders_handler.get_open_orders()
                    
                    if orders:
                        all_orders.append({
                            'api_name': api_name,
                            'orders': orders
                        })
                    
                finally:
                    await client.close()
                
            except Exception as e:
                logger.error(f"[show_orders] Error fetching orders for {api_name}: {e}")
        
        # Format message
        if not all_orders:
            message = "📋 **Orders**\n\nNo open orders."
        else:
            message = "📋 **Open Orders**\n\n"
            
            total_orders = 0
            for order_info in all_orders:
                api_name = order_info.get('api_name')
                orders = order_info.get('orders', [])
                
                total_orders += len(orders)
                
                message += f"**{api_name}:**\n"
                
                for i, order in enumerate(orders[:10], 1):
                    symbol = order.get('product_symbol', 'Unknown')
                    side = order.get('side', 'Unknown')
                    size = order.get('size', 0)
                    order_type = order.get('order_type', 'Unknown')
                    price = order.get('limit_price') or order.get('stop_price', 0)
                    
                    side_emoji = "🟢" if side == 'buy' else "🔴"
                    
                    message += f"{i}. {side_emoji} {side.upper()} {symbol}\n"
                    message += f"   Type: {order_type} | Size: {size}"
                    
                    if price:
                        message += f" | Price: ${price:.2f}"
                    
                    message += "\n\n"
                
                message += "─" * 30 + "\n\n"
            
            message += f"**Total Open Orders:** {total_orders}"
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"[show_orders] Displayed orders for user {user_id}")
        
    except Exception as e:
        logger.error(f"[show_orders] Error: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error fetching orders.",
            reply_markup=get_main_menu_keyboard()
        )


if __name__ == "__main__":
    print("Order handler module loaded")
  
