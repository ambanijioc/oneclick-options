"""
Options listing handlers.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes
)

from bot.utils.logger import setup_logger, log_user_action
from bot.utils.error_handler import error_handler
from bot.utils.message_formatter import format_error_message, escape_html
from bot.validators.user_validator import check_user_authorization
from bot.keyboards.options_keyboards import (
    get_asset_selection_keyboard,
    get_expiry_selection_keyboard
)
from bot.keyboards.expiry_keyboards import get_expiry_list_keyboard
from delta.client import DeltaClient
from delta.utils.expiry_parser import parse_expiry_code, format_expiry_date, get_all_expiry_dates

logger = setup_logger(__name__)


@error_handler
async def list_options_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle list options menu callback.
    Display asset selection (BTC/ETH).
    
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
    
    # Options list text
    text = (
        "<b>📑 List Options</b>\n\n"
        "Select an asset to view available options:"
    )
    
    # Show asset selection
    await query.edit_message_text(
        text,
        reply_markup=get_asset_selection_keyboard(),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "list_options", "Opened options list")


@error_handler
async def asset_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle asset selection callback.
    Display expiry selection for chosen asset.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract asset from callback data
    asset = query.data.split('_')[1]
    
    # Asset info text
    asset_emoji = "₿" if asset == "BTC" else "Ξ"
    text = (
        f"<b>📑 {asset_emoji} {asset} Options</b>\n\n"
        f"Select an expiry to view available strikes:"
    )
    
    # Show expiry selection
    await query.edit_message_text(
        text,
        reply_markup=get_expiry_selection_keyboard(asset),
        parse_mode='HTML'
    )
    
    log_user_action(user.id, "asset_selection", f"Selected asset: {asset}")


@error_handler
async def expiry_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle expiry selection callback.
    Display expiry details and available strikes.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract asset and expiry from callback data
    parts = query.data.split('_')
    asset = parts[1]
    expiry_code = parts[2]
    
    # Show loading message
    await query.edit_message_text(
        f"⏳ <b>Loading {asset} options...</b>\n\n"
        f"Fetching option chain for {expiry_code} expiry...",
        parse_mode='HTML'
    )
    
    try:
        # Parse expiry code to get date
        expiry_date = parse_expiry_code(expiry_code)
        formatted_date = format_expiry_date(expiry_date, '%d %b %Y')
        
        # Create Delta client (unauthenticated call)
        client = DeltaClient("", "")
        
        try:
            # Fetch products (options)
            response = await client.get_products(contract_types='call_options,put_options')
            
            if not response.get('success'):
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                await query.edit_message_text(
                    format_error_message(f"Failed to fetch options: {error_msg}"),
                    parse_mode='HTML'
                )
                return
            
            products = response.get('result', [])
            
            # Filter products by asset and expiry date
            # Note: This is a simplified filter. In production, match exact settlement time
            expiry_str = expiry_date.strftime('%Y-%m-%d')
            
            matching_options = []
            for product in products:
                symbol = product.get('symbol', '')
                if asset in symbol and expiry_str[:7] in product.get('settlement_time', ''):
                    matching_options.append(product)
            
            if not matching_options:
                await query.edit_message_text(
                    f"<b>📑 {asset} Options - {expiry_code}</b>\n\n"
                    f"<b>Expiry:</b> {formatted_date}\n\n"
                    f"❌ No options found for this expiry.\n\n"
                    f"<i>This expiry may not be available yet.</i>",
                    parse_mode='HTML'
                )
                return
            
            # Group by strike
            strikes = set()
            calls = {}
            puts = {}
            
            for option in matching_options:
                strike = option.get('strike_price')
                if strike:
                    strikes.add(strike)
                    
                    if 'C' in option.get('symbol', ''):
                        calls[strike] = option
                    else:
                        puts[strike] = option
            
            # Sort strikes
            sorted_strikes = sorted(strikes)
            
            # Get spot price for reference
            spot_price = 0
            try:
                spot_response = await client.get_spot_price(asset)
                spot_price = spot_response
            except Exception:
                pass
            
            # Format options list
            text = f"<b>📑 {asset} Options - {expiry_code}</b>\n\n"
            text += f"<b>Expiry:</b> {formatted_date}\n"
            text += f"<b>Spot Price:</b> ${spot_price:,.2f}\n"
            text += f"<b>Available Strikes:</b> {len(sorted_strikes)}\n\n"
            
            # Show sample strikes (first 10)
            text += "<b>Sample Strikes:</b>\n"
            for strike in sorted_strikes[:10]:
                has_call = '✅' if strike in calls else '❌'
                has_put = '✅' if strike in puts else '❌'
                
                # Highlight ATM
                atm_indicator = ""
                if spot_price > 0:
                    if abs(strike - spot_price) / spot_price < 0.02:  # Within 2%
                        atm_indicator = " 🎯 ATM"
                
                text += f"  ${strike:,.0f}: Call {has_call} | Put {has_put}{atm_indicator}\n"
            
            if len(sorted_strikes) > 10:
                text += f"\n<i>...and {len(sorted_strikes) - 10} more strikes</i>\n"
            
            text += (
                "\n<i>Use strategy presets to trade these options</i>"
            )
            
            # Show options info
            await query.edit_message_text(
                text,
                parse_mode='HTML'
            )
            
            log_user_action(
                user.id,
                "expiry_selection",
                f"Viewed {asset} {expiry_code}: {len(sorted_strikes)} strikes"
            )
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to fetch options: {e}", exc_info=True)
        await query.edit_message_text(
            format_error_message("Failed to fetch options.", str(e)),
            parse_mode='HTML'
        )


def register_options_list_handlers(application: Application):
    """
    Register options listing handlers.
    
    Args:
        application: Bot application instance
    """
    # List options menu callback
    application.add_handler(CallbackQueryHandler(
        list_options_callback,
        pattern="^menu_list_options$"
    ))
    
    # Asset selection callback
    application.add_handler(CallbackQueryHandler(
        asset_selection_callback,
        pattern="^asset_(BTC|ETH)$"
    ))
    
    # Expiry selection callback
    application.add_handler(CallbackQueryHandler(
        expiry_selection_callback,
        pattern="^expiry_"
    ))
    
    logger.info("Options list handlers registered")


if __name__ == "__main__":
    print("Options list handler module loaded")
  
