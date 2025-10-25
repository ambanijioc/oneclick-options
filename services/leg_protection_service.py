"""
Leg Protection Service - FIXED VERSION
Cancels old SL order with BOTH product_id and order_id
"""

import asyncio
from typing import Dict
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def start_leg_protection_monitor(strategy_details: Dict, bot_application):
    """
    Start monitoring a strategy for leg protection.
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
    Protect remaining leg with SMART stop-loss placement.
    
    Strategy:
    1. Get current market price
    2. If current price ≈ entry price → Use dynamic SL (above current price)
    3. If current price < entry price → Use breakeven SL (at entry price)
    4. Place new SL FIRST (safety)
    5. Cancel old SL SECOND (with correct parameters)
    """
    try:
        logger.info(f"🛡️ Protecting remaining leg: {remaining_symbol}")
        
        # ✅ STEP 1: Get product_id for the remaining symbol
        logger.info(f"📍 Fetching product details for {remaining_symbol}")
        
        product_response = await client.get_product(remaining_symbol)
        
        if not product_response.get('success'):
            logger.error(f"❌ Failed to get product for {remaining_symbol}")
            return
        
        product_id = product_response['result']['id']
        logger.info(f"✅ Product ID: {product_id}")
        
        # ✅ STEP 2: Get current market price
        ticker_response = await client.get_ticker(remaining_symbol)
        if not ticker_response.get('success'):
            logger.error("Failed to fetch ticker")
            return
        
        ticker = ticker_response['result']
        current_mark_price = float(ticker.get('mark_price', 0))
        current_last_price = float(ticker.get('close', 0))
        current_price = current_mark_price or current_last_price
        
        logger.info(f"💰 Current market price: ${current_price:.2f}")
        logger.info(f"💰 Original entry price: ${remaining_entry_price:.2f}")
        
        # ✅ STEP 3: SMART SL CALCULATION
        # Check if current price is very close to entry price (within 5%)
        price_diff_pct = abs(current_price - remaining_entry_price) / remaining_entry_price * 100
        
        if price_diff_pct <= 5.0:
            # ⚠️ CASE 1: Price ≈ Entry Price (would trigger immediately)
            # Use DYNAMIC SL above current price to prevent immediate execution
            logger.warning(f"⚠️ Current price (${current_price:.2f}) too close to entry (${remaining_entry_price:.2f})")
            logger.info("📍 Using DYNAMIC SL strategy to prevent immediate execution")
            
            if current_price < 5.0:
                # Very cheap option - add $2 buffer
                sl_price = current_price + 2.0
            elif current_price < 20.0:
                # Mid-priced - add 20% buffer
                sl_price = current_price * 1.20
            else:
                # Higher-priced - add 15% buffer
                sl_price = current_price * 1.15
            
            sl_price = round(sl_price, 2)
            logger.info(f"✅ Dynamic SL: ${sl_price:.2f} (${sl_price - current_price:.2f} above current)")
            
        else:
            # ✅ CASE 2: Price significantly different from entry
            # Use BREAKEVEN SL at entry price
            logger.info("📍 Using BREAKEVEN SL strategy (entry price)")
            sl_price = round(remaining_entry_price, 2)
            logger.info(f"✅ Breakeven SL: ${sl_price:.2f}")
        
        # ✅ STEP 4: Determine order parameters
        direction = strategy.get('direction', 'long')
        side = 'sell' if direction == 'long' else 'buy'
        
        # Calculate limit price (slightly better execution)
        if side == 'buy':
            limit_price = round(sl_price * 1.02, 2)  # 2% slippage
        else:
            limit_price = round(sl_price * 0.98, 2)  # 2% slippage
        
        # ✅ STEP 5: Place NEW protective SL FIRST (safety first!)
        logger.info(f"📍 Step 1: Placing new protective SL at ${sl_price:.2f}")
        
        new_sl_order = await client.place_order({
            'product_id': product_id,
            'size': strategy.get('lot_size', 1),
            'side': side,
            'order_type': 'limit_order',
            'stop_order_type': 'stop_loss_order',
            'stop_price': str(sl_price),
            'limit_price': str(limit_price),
            'reduce_only': True
        })
        
        if not new_sl_order.get('success'):
            error_msg = new_sl_order.get('error', {}).get('message', 'Unknown error')
            logger.error(f"❌ Failed to place new SL: {error_msg}")
            return
        
        new_sl_id = new_sl_order['result']['id']
        logger.info(f"✅ New protective SL placed: {new_sl_id} at ${sl_price:.2f}")
        
        # ✅ STEP 6: Cancel OLD SL with CORRECT parameters (product_id + order_id)
        logger.info(f"📍 Step 2: Cancelling old SL: {remaining_sl_order_id}")
        
        if remaining_sl_order_id:
            try:
                # ✅ FIX: Pass BOTH product_id and order_id
                cancel_result = await client.cancel_order(
                    product_id=product_id,  # ✅ REQUIRED!
                    order_id=remaining_sl_order_id  # ✅ Order ID
                )
                
                if cancel_result.get('success'):
                    logger.info(f"✅ Old SL cancelled: {remaining_sl_order_id}")
                else:
                    error_msg = cancel_result.get('error', {}).get('message', 'Unknown error')
                    logger.warning(f"⚠️ Old SL cancellation failed: {error_msg}")
            
            except Exception as e:
                logger.warning(f"⚠️ Could not cancel old SL: {e}")
        
        # ✅ STEP 7: Send notification
        remaining_leg = 'CE' if closed_leg == 'PE' else 'PE'
        sl_strategy = "Dynamic (prevents immediate trigger)" if price_diff_pct <= 5.0 else "Breakeven (entry price)"
        
        message = (
            f"🛡️ **Leg Protection Activated!**\n\n"
            f"🔄 **{closed_leg} leg closed**\n"
            f"🛡️ **{remaining_leg} leg protected**\n\n"
            f"💰 **Current Price:** ${current_price:.2f}\n"
            f"💰 **Entry Price:** ${remaining_entry_price:.2f}\n"
            f"🎯 **New SL:** ${sl_price:.2f}\n"
            f"📊 **Strategy:** {sl_strategy}\n"
            f"📊 **Symbol:** {remaining_symbol}\n"
            f"🆔 **New SL Order:** `{new_sl_id}`\n"
            f"🗑️ **Old SL Cancelled:** `{remaining_sl_order_id}`\n\n"
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
