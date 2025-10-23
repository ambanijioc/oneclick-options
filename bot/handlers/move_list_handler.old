"""
Move options list handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.validators.user_validator import check_user_authorization
from database.operations.api_ops import get_api_credentials, get_decrypted_api_credential
from delta.client import DeltaClient

logger = setup_logger(__name__)


def get_move_list_keyboard():
    """Get move list keyboard."""
    keyboard = [
        [InlineKeyboardButton("🟠 BTC Moves", callback_data="move_list_btc")],
        [InlineKeyboardButton("🔵 ETH Moves", callback_data="move_list_eth")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


@error_handler
async def move_list_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display move options list menu."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    await query.edit_message_text(
        "<b>📋 List Move Options</b>\n\n"
        "View available Move options contracts:\n\n"
        "Select asset to view:",
        reply_markup=get_move_list_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "move_list_menu", "Viewed move list menu")


@error_handler
async def move_list_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display move options for selected asset."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    asset = query.data.split('_')[-1].upper()  # BTC or ETH
    
    if not await check_user_authorization(user):
        await query.edit_message_text("❌ Unauthorized access")
        return
    
    # Get user's APIs
    apis = await get_api_credentials(user.id)
    
    if not apis:
        await query.edit_message_text(
            f"<b>📋 {asset} Move Options</b>\n\n"
            "❌ No API credentials configured.",
            reply_markup=get_move_list_keyboard(),
            parse_mode='HTML'
        )
        return
    
    await query.edit_message_text(
        f"⏳ <b>Loading {asset} Move options...</b>",
        parse_mode='HTML'
    )
    
    try:
        # Get first API
        api = apis[0]
        credentials = await get_decrypted_api_credential(str(api.id))
        
        if not credentials:
            await query.edit_message_text(
                "❌ Failed to decrypt credentials",
                reply_markup=get_move_list_keyboard(),
                parse_mode='HTML'
            )
            return
        
        api_key, api_secret = credentials
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Fetch move options
            response = await client.get_products(contract_types='move_options')
            
            if response.get('success'):
                products = response.get('result', [])
                
                # Filter by asset and active
                asset_moves = [
                    p for p in products 
                    if asset in p.get('symbol', '') and p.get('state') == 'live'
                ]
                
                if asset_moves:
                    text = f"<b>📋 {asset} Move Options</b>\n\n"
                    
                    for move in asset_moves[:10]:
                        symbol = move.get('symbol', 'N/A')
                        strike = move.get('strike_price', 'N/A')
                        mark_price = float(move.get('mark_price', 0) or 0)
                        volume = float(move.get('turnover_24h', 0) or 0)
                        
                        text += f"<b>{symbol}</b>\n"
                        text += f"Strike: ${strike}\n"
                        text += f"Mark: ${mark_price:,.2f}\n"
                        text += f"Volume: ${volume:,.0f}\n\n"
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=get_move_list_keyboard(),
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"<b>📋 {asset} Move Options</b>\n\n"
                        f"❌ No active {asset} move options available",
                        reply_markup=get_move_list_keyboard(),
                        parse_mode='HTML'
                    )
            else:
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    f"<b>📋 {asset} Move Options</b>\n\n"
                    f"❌ Error: {error_msg}",
                    reply_markup=get_move_list_keyboard(),
                    parse_mode='HTML'
                )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch move options: {e}", exc_info=True)
        await query.edit_message_text(
            f"<b>📋 {asset} Move Options</b>\n\n"
            f"❌ Error: {str(e)[:100]}",
            reply_markup=get_move_list_keyboard(),
            parse_mode='HTML'
        )
    
    log_user_action(user.id, f"move_list_{asset.lower()}", f"Viewed {asset} move options")


def register_move_list_handlers(application: Application):
    """Register move list handlers."""
    
    application.add_handler(CallbackQueryHandler(
        move_list_menu_callback,
        pattern="^menu_move_list$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        move_list_asset_callback,
        pattern="^move_list_(btc|eth)$"
    ))
    
    logger.info("Move list handlers registered")
  
