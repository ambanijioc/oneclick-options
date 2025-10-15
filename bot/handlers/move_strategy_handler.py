"""
Move options strategy handlers.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from delta.client import DeltaClient

logger = setup_logger(__name__)


def get_move_strategy_keyboard():
    """Get move strategy keyboard."""
    keyboard = [
        [InlineKeyboardButton("📈 Long Move", callback_data="move_long")],
        [InlineKeyboardButton("📉 Short Move", callback_data="move_short")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle move strategy callback.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check authorization
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    await query.edit_message_text(
        "<b>📊 Move Options Strategy</b>\n\n"
        "Move options are volatility products that profit from large price movements in either direction.\n\n"
        "<b>Long Move:</b> Buy when expecting high volatility\n"
        "<b>Short Move:</b> Sell when expecting low volatility\n\n"
        "Select your strategy:",
        reply_markup=get_move_strategy_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_strategy", "Viewed move strategy menu")


@error_handler
async def move_long_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle long move selection.
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
            "<b>📊 Long Move</b>\n\n"
            "❌ No API credentials configured.\n\n"
            "Please add an API credential first.",
            reply_markup=get_move_strategy_keyboard(),
            parse_mode='HTML'
        )
        return
    
    # Show loading message
    await query.edit_message_text(
        "⏳ <b>Loading Move options...</b>\n\n"
        "Fetching available move contracts...",
        parse_mode='HTML'
    )
    
    # Fetch move options
    try:
        # Get first API for fetching options
        api = apis[0]
        credentials = await get_decrypted_api_credential(str(api.id))
        
        if not credentials:
            await query.edit_message_text(
                "❌ Failed to decrypt credentials",
                reply_markup=get_move_strategy_keyboard(),
                parse_mode='HTML'
            )
            return
        
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Fetch move options products
            response = await client.get_products(contract_types='move_options')
            
            if response.get('success'):
                products = response.get('result', [])
                
                # Filter active move options
                active_moves = [
                    p for p in products 
                    if p.get('state') == 'live'
                ]
                
                if active_moves:
                    # Group by underlying asset
                    btc_moves = [m for m in active_moves if 'BTC' in m.get('symbol', '')]
                    eth_moves = [m for m in active_moves if 'ETH' in m.get('symbol', '')]
                    
                    text = "<b>📊 Available Move Options</b>\n\n"
                    
                    if btc_moves:
                        text += "<b>🟠 BTC Move Options:</b>\n"
                        for move in btc_moves[:5]:
                            symbol = move.get('symbol', 'N/A')
                            strike = move.get('strike_price', 'N/A')
                            text += f"• {symbol} (Strike: ${strike})\n"
                        text += "\n"
                    
                    if eth_moves:
                        text += "<b>🔵 ETH Move Options:</b>\n"
                        for move in eth_moves[:5]:
                            symbol = move.get('symbol', 'N/A')
                            strike = move.get('strike_price', 'N/A')
                            text += f"• {symbol} (Strike: ${strike})\n"
                        text += "\n"
                    
                    text += "Use /trade to place orders"
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=get_move_strategy_keyboard(),
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        "<b>📊 Long Move</b>\n\n"
                        "❌ No active move options available",
                        reply_markup=get_move_strategy_keyboard(),
                        parse_mode='HTML'
                    )
            else:
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    f"<b>📊 Long Move</b>\n\n"
                    f"❌ Error: {error_msg}",
                    reply_markup=get_move_strategy_keyboard(),
                    parse_mode='HTML'
                )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch move options: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>📊 Long Move</b>\n\n"
            f"❌ Error: {str(e)[:100]}",
            reply_markup=get_move_strategy_keyboard(),
            parse_mode='HTML'
        )
    
    log_user_action(user.id, "move_long", "Viewed long move options")


@error_handler
async def move_short_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle short move selection.
    """
    # Similar to move_long_callback but for short positions
    await move_long_callback(update, context)  # Reuse the same logic for now
    log_user_action(update.callback_query.from_user.id, "move_short", "Viewed short move options")


def register_move_strategy_handlers(application: Application):
    """
    Register move strategy handlers.
    """
    application.add_handler(CallbackQueryHandler(
        move_strategy_callback,
        pattern="^menu_move_strategy$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_long_callback,
        pattern="^move_long$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_short_callback,
        pattern="^move_short$"
    ))
    
    logger.info("Move strategy handlers registered")


if __name__ == "__main__":
    print("Move strategy handler module loaded")
