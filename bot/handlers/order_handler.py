"""
Order management handlers - FIXED VERSION
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # ✅ ADD THIS
import telegram  # ✅ ADD THIS for telegram.error.BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_order, format_error_message
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.order_keyboards import (
    get_order_list_keyboard,
    get_order_action_keyboard,
    get_order_detail_keyboard,
    get_order_cancel_confirmation_keyboard
)
from bot.keyboards.confirmation_keyboards import get_back_keyboard  # ✅ ADD THIS
from database.operations.api_ops import (
    get_api_credentials,
    get_decrypted_api_credential,
    get_api_credential_by_id  # ✅ ADD THIS
)
from services.delta.client import DeltaClient  # ✅ FIXED PATH

logger = setup_logger(__name__)


@error_handler
async def orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle orders menu callback.
    Display API selection for viewing orders.
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
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            "<b>📋 Orders</b>\n\n"
            "❌ No API credentials found.\n"
            "Please add an API first.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Order selection text
    text = (
        "<b>📋 Orders</b>\n\n"
        "Select an API to view orders:"
    )
    
    # Show API selection
    await query.edit_message_text(
        text,
        reply_markup=get_order_list_keyboard(apis),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "orders_menu", "Opened orders menu")


@error_handler
async def order_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle order view callback - show orders for selected API.
    This callback handles the pattern "^order_view_"
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID from callback data (format: order_view_{api_id})
    api_id = query.data.split('_')[-1]
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading orders...</b>\n\n"
        "Fetching order data from Delta Exchange...",
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
            # Fetch open orders
            response = await client.get_open_orders()
            
            if not response.get('success'):
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                keyboard = [
                    [InlineKeyboardButton("🔄 Retry", callback_data=f"order_view_{api_id}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
                ]
                await query.edit_message_text(
                    f"<b>📋 Orders</b>\n\n"
                    f"❌ Failed to fetch orders:\n"
                    f"<code>{error_msg}</code>",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return
            
            orders = response.get('result', [])
            
            # Get API name for display
            api_credential = await get_api_credential_by_id(api_id)
            api_name = api_credential.get('name', 'Unknown API') if api_credential else 'Unknown API'
            
            # Format orders
            if not orders:
                message_text = (
                    f"<b>📋 Orders - {api_name}</b>\n\n"
                    "❌ No open orders found.\n\n"
                    "All orders have been filled or cancelled."
                )
                keyboard = get_back_keyboard("menu_orders")
            else:
                message_text = f"<b>📋 Orders - {api_name}</b>\n\n"
                message_text += f"Open orders: {len(orders)}\n\n"
                
                for order in orders[:10]:  # Show max 10 orders
                    message_text += format_order(order) + "\n\n"
                
                if len(orders) > 10:
                    message_text += f"<i>...and {len(orders) - 10} more orders</i>\n\n"
                
                keyboard = get_order_action_keyboard(api_id, orders)
            
            # ✅ Try-except for duplicate edit protection
            try:
                await query.edit_message_text(
                    message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except telegram.error.BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.debug(f"Orders unchanged for user {user.id}")
                else:
                    raise
            
            log_user_action(user.id, "order_view", f"Viewed {len(orders)} orders for API {api_id}")
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            format_error_message("Failed to fetch orders.", str(e)),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


@error_handler
async def order_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle order detail callback.
    Display detailed information about an order.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID and order ID from callback data
    parts = query.data.split('_')
    api_id = parts[2]
    order_id = parts[3]
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading order details...</b>",
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
            # Fetch order details
            response = await client.get_order(order_id)
            
            if not response.get('success'):
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    format_error_message(f"Failed to fetch order: {error_msg}"),
                    parse_mode='HTML'
                )
                return
            
            order = response.get('result')
            
            if not order:
                await query.edit_message_text(
                    "<b>📋 Order Details</b>\n\n"
                    "❌ Order not found.",
                    parse_mode='HTML'
                )
                return
            
            # Format order details
            order_text = "<b>📋 Order Details</b>\n\n"
            order_text += format_order(order)
            
            # Show order with action keyboard
            await query.edit_message_text(
                order_text,
                reply_markup=get_order_detail_keyboard(api_id, order_id),
                parse_mode='HTML'
            )
            
            log_user_action(user.id, "order_detail", f"Viewed order {order_id}")
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch order details: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to fetch order details.", str(e)),
            parse_mode='HTML'
        )


@error_handler
async def order_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle order cancel callback.
    Show confirmation before cancelling.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID and order ID from callback data
    parts = query.data.split('_')
    api_id = parts[2]
    order_id = parts[3]
    
    # Show confirmation
    text = (
        "<b>⚠️ Cancel Order</b>\n\n"
        f"<b>Order ID:</b> <code>{order_id}</code>\n\n"
        "Are you sure you want to cancel this order?"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_order_cancel_confirmation_keyboard(api_id, order_id),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "order_cancel_request", f"Requested cancel for order {order_id}")


@error_handler
async def order_cancel_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle order cancel confirmation callback.
    Actually cancel the order.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID and order ID from callback data
    parts = query.data.split('_')
    api_id = parts[3]
    order_id = parts[4]
    
    # Show processing message
    await query.edit_message_text(
        "⏳ <b>Cancelling order...</b>",
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
            # Cancel order
            response = await client.cancel_order(order_id)
            
            if response.get('success'):
                await query.edit_message_text(
                    "<b>✅ Order Cancelled</b>\n\n"
                    f"<b>Order ID:</b> <code>{order_id}</code>\n\n"
                    "The order has been successfully cancelled.",
                    parse_mode='HTML'
                )
                
                log_user_action(user.id, "order_cancel_success", f"Cancelled order {order_id}")
            else:
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    format_error_message(f"Failed to cancel order: {error_msg}"),
                    parse_mode='HTML'
                )
                
                log_user_action(user.id, "order_cancel_failed", f"Failed to cancel {order_id}")
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to cancel order.", str(e)),
            parse_mode='HTML'
        )


@error_handler
async def order_cancel_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle cancel all orders callback.
    Show confirmation before cancelling all.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID from callback data
    api_id = query.data.split('_')[-1]
    
    # Show confirmation
    text = (
        "<b>⚠️ Cancel All Orders</b>\n\n"
        "Are you sure you want to cancel <b>ALL</b> open orders?\n\n"
        "<i>This action cannot be undone.</i>"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_order_cancel_confirmation_keyboard(api_id, cancel_all=True),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "order_cancel_all_request", f"Requested cancel all for API {api_id}")


@error_handler
async def order_cancel_all_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle cancel all orders confirmation callback.
    Actually cancel all orders.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract API ID from callback data
    api_id = query.data.split('_')[-1]
    
    # Show processing message
    await query.edit_message_text(
        "⏳ <b>Cancelling all orders...</b>",
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
            # Cancel all orders
            response = await client.cancel_all_orders()
            
            if response.get('success'):
                cancelled_count = len(response.get('result', []))
                
                await query.edit_message_text(
                    "<b>✅ Orders Cancelled</b>\n\n"
                    f"Successfully cancelled <b>{cancelled_count}</b> order(s).",
                    parse_mode='HTML'
                )
                
                log_user_action(
                    user.id,
                    "order_cancel_all_success",
                    f"Cancelled {cancelled_count} orders"
                )
            else:
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    format_error_message(f"Failed to cancel orders: {error_msg}"),
                    parse_mode='HTML'
                )
                
                log_user_action(user.id, "order_cancel_all_failed", "Failed to cancel all orders")
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to cancel all orders: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to cancel all orders.", str(e)),
            parse_mode='HTML'
        )


def register_order_handlers(application: Application):
    """Register order handlers."""
    # Orders menu callback
    application.add_handler(CallbackQueryHandler(
        orders_callback,
        pattern="^menu_orders$"
    ))
    
    # Order view callback
    application.add_handler(CallbackQueryHandler(
        order_view_callback,
        pattern="^order_view_"
    ))
    
    # Order detail callback
    application.add_handler(CallbackQueryHandler(
        order_detail_callback,
        pattern="^order_detail_"
    ))
    
    # Order cancel callback
    application.add_handler(CallbackQueryHandler(
        order_cancel_callback,
        pattern="^order_cancel_(?!confirm|all)"
    ))
    
    # Order cancel confirmation callback
    application.add_handler(CallbackQueryHandler(
        order_cancel_confirm_callback,
        pattern="^order_cancel_confirm_"
    ))
    
    # Cancel all orders callback
    application.add_handler(CallbackQueryHandler(
        order_cancel_all_callback,
        pattern="^order_cancel_all_(?!confirm)"
    ))
    
    # Cancel all confirmation callback
    application.add_handler(CallbackQueryHandler(
        order_cancel_all_confirm_callback,
        pattern="^order_cancel_all_confirm_"
    ))
    
    logger.info("Order handlers registered")


if __name__ == "__main__":
    print("Order handler module loaded")
        
