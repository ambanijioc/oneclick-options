"""
Leg Protection Service
Monitors straddle/strangle strategies and protects remaining leg when one closes.
Shared by both auto and manual trades.
"""

import asyncio
from typing import Dict
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def start_leg_protection_monitor(strategy_details: Dict, bot_application):
    """
    Start monitoring a strategy for leg protection.
    
    Args:
        strategy_details: Dictionary containing:
            - user_id: User's Telegram ID
            - api_id: API credential ID
            - ce_symbol: CE option symbol
            - pe_symbol: PE option symbol
            - ce_entry_price: CE entry price
            - pe_entry_price: PE entry price
            - ce_sl_order_id: CE stop-loss order ID (optional)
            - pe_sl_order_id: PE stop-loss order ID (optional)
            - direction: 'long' or 'short'
            - lot_size: Lot size
            - strategy_type: 'straddle' or 'strangle'
        bot_application: Telegram bot application instance
    """
    client = None
    try:
        logger.info(f"🔍 Starting leg protection monitor for {strategy_details['ce_symbol']}/{strategy_details['pe_symbol']}")
        
        # Get API credentials
        from database.operations.api_ops import get_decrypted_api_credential
        credentials = await get_decrypted_api_credential(strategy_details['api_id'])
        
        if not credentials:
            logger.error("Failed to get API credentials for monitoring")
            return
        
        api_key, api_secret = credentials
        from delta.client import DeltaClient
        client = DeltaClient(api_key, api_secret)
        
        # Monitor for up to 24 hours (2880 checks at 30sec intervals)
        leg_protection_activated = False
        
        for _ in range(2880):
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # Skip if already protected
            if leg_protection_activated:
                logger.info("Leg protection already activated, stopping monitor")
                break
            
            try:
                # Get current positions
                positions = await client.get_positions()
                
                if not positions.get('success'):
                    continue
                
                positions_data = positions['result']
                
                # Find CE and PE positions
                ce_position = next((p for p in positions_data 
                                  if strategy_details['ce_symbol'] in p.get('product', {}).get('symbol', '')), None)
                pe_position = next((p for p in positions_data 
                                  if strategy_details['pe_symbol'] in p.get('product', {}).get('symbol', '')), None)
                
                # Check if positions exist
                ce_size = int(ce_position.get('size', 0)) if ce_position else 0
                pe_size = int(pe_position.get('size', 0)) if pe_position else 0
                
                # Check if ONE leg is closed
                ce_closed = ce_size == 0
                pe_closed = pe_size == 0
                
                # ONE leg closed, other still open → PROTECT!
                if ce_closed and not pe_closed:
                    logger.info(f"🛡️ CE leg closed, protecting PE leg")
                    await protect_remaining_leg(
                        client=client,
                        strategy=strategy_details,
                        remaining_symbol=strategy_details['pe_symbol'],
                        remaining_entry_price=strategy_details['pe_entry_price'],
                        remaining_sl_order_id=strategy_details.get('pe_sl_order_id'),
                        closed_leg='CE',
                        bot_application=bot_application
                    )
                    leg_protection_activated = True
                    break
                
                elif pe_closed and not ce_closed:
                    logger.info(f"🛡️ PE leg closed, protecting CE leg")
                    await protect_remaining_leg(
                        client=client,
                        strategy=strategy_details,
                        remaining_symbol=strategy_details['ce_symbol'],
                        remaining_entry_price=strategy_details['ce_entry_price'],
                        remaining_sl_order_id=strategy_details.get('ce_sl_order_id'),
                        closed_leg='PE',
                        bot_application=bot_application
                    )
                    leg_protection_activated = True
                    break
                
                # Both legs still open - continue monitoring
                elif not ce_closed and not pe_closed:
                    continue
                
                # Both legs closed - stop monitoring
                else:
                    logger.info("Both legs closed, stopping monitor")
                    break
                    
            except Exception as e:
                logger.error(f"Error checking leg status: {e}")
                continue
        
        logger.info("Leg protection monitoring ended")
        
    except Exception as e:
        logger.error(f"Error in leg protection monitor: {e}", exc_info=True)
    finally:
        if client:
            await client.close()


async def protect_remaining_leg(client, strategy: Dict, remaining_symbol: str, 
                                remaining_entry_price: float, remaining_sl_order_id: str,
                                closed_leg: str, bot_application):
    """
    Move remaining leg's SL to breakeven (entry price).
    STRATEGY: Place new SL first, THEN cancel old one for maximum safety.
    """
    try:
        logger.info(f"🛡️ Protecting remaining leg: {remaining_symbol}")
        
        # Determine order side
        direction = strategy.get('direction', 'long')
        side = 'sell' if direction == 'long' else 'buy'
        
        # Calculate limit price (slightly better execution)
        if side == 'buy':
            # Buying back - limit slightly above stop
            limit_price = round(remaining_entry_price * 1.02, 2)
        else:
            # Selling - limit slightly below stop
            limit_price = round(remaining_entry_price * 0.98, 2)
        
        # ✅ STEP 1: Place NEW breakeven SL FIRST (safety first!)
        logger.info(f"📍 Step 1: Placing new breakeven SL at ${remaining_entry_price:.2f}")
        
        new_sl_order = await client.place_order({
            'product_symbol': remaining_symbol,
            'size': strategy.get('lot_size', 1),
            'side': side,
            'order_type': 'limit_order',
            'stop_order_type': 'stop_loss_order',
            'stop_price': str(round(remaining_entry_price, 2)),
            'limit_price': str(limit_price),
            'reduce_only': True
        })
        
        if not new_sl_order.get('success'):
            error_msg = new_sl_order.get('error', {}).get('message', 'Unknown error')
            logger.error(f"❌ Failed to place new SL: {error_msg}")
            return
        
        new_sl_id = new_sl_order['result']['id']
        logger.info(f"✅ New breakeven SL placed: {new_sl_id} at ${remaining_entry_price:.2f}")
        
        # ✅ STEP 2: Now that we're protected, cancel OLD SL
        logger.info(f"📍 Step 2: Cancelling old SL: {remaining_sl_order_id}")
        
        if remaining_sl_order_id:
            try:
                cancel_result = await client.cancel_order(remaining_sl_order_id)
                if cancel_result.get('success'):
                    logger.info(f"✅ Old SL cancelled: {remaining_sl_order_id}")
                else:
                    logger.info(f"ℹ️ Old SL already executed/closed: {remaining_sl_order_id}")
            except Exception as e:
                logger.info(f"ℹ️ Old SL already executed: {e}")
        
        # ✅ STEP 3: Send notification
        remaining_leg = 'CE' if closed_leg == 'PE' else 'PE'
        message = (
            f"🛡️ **Leg Protection Activated!**\n\n"
            f"🔄 **{closed_leg} leg closed**\n"
            f"🛡️ **{remaining_leg} leg protected**\n\n"
            f"💰 **New SL:** ${remaining_entry_price:.2f} (Breakeven)\n"
            f"📊 **Symbol:** {remaining_symbol}\n"
            f"🆔 **New SL Order:** {new_sl_id}\n\n"
            f"✅ You're now protected from further losses!"
        )
        
        try:
            await bot_application.bot.send_message(
                chat_id=strategy['user_id'],
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Notification sent to user {strategy['user_id']}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
    except Exception as e:
        logger.error(f"Error protecting remaining leg: {e}", exc_info=True)
        
