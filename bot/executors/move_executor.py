"""
Universal Move Options Trade Executor - Dynamically executes ANY move strategy.
Fetches strategy, places entry order, and auto-places SL/Target bracket orders.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from bot.utils.logger import setup_logger
from delta.client import DeltaClient

logger = setup_logger(__name__)


class MoveTradeExecutor:
    """
    Universal executor for Move options trades.
    Dynamically executes trades based on strategy configuration.
    """
    
    def __init__(self, client: DeltaClient):
        """
        Initialize executor with Delta client.
        
        Args:
            client: Initialized DeltaClient instance
        """
        self.client = client
        logger.info("MoveTradeExecutor initialized")
    
    async def find_atm_option(
        self,
        asset: str,
        direction: str,
        atm_offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Find ATM option contract dynamically.
        
        Args:
            asset: BTC or ETH
            direction: 'long' or 'short'
            atm_offset: Strike offset from ATM (0 = ATM, +1 = OTM by 1 strike, etc.)
        
        Returns:
            Product dict or None
        """
        try:
            # Get spot price
            spot_price = await self.client.get_spot_price(asset)
            logger.info(f"Current {asset} spot price: ${spot_price:,.2f}")
            
            # Determine option type based on direction
            # For LONG move: Buy CALL (expect upward move)
            # For SHORT move: Buy PUT (expect downward move)
            contract_type = "call_options" if direction.lower() == "long" else "put_options"
            
            # Get all products of this type
            products_response = await self.client.get_products(contract_types=contract_type)
            
            if not products_response.get('success') or not products_response.get('result'):
                logger.error(f"Failed to fetch {contract_type} products")
                return None
            
            products = products_response['result']
            
            # Filter products for the asset
            asset_products = [
                p for p in products
                if p.get('underlying_asset', {}).get('symbol') == asset
                and p.get('contract_type') == contract_type.replace('_options', '')
            ]
            
            if not asset_products:
                logger.error(f"No {contract_type} found for {asset}")
                return None
            
            # Find ATM strike (closest to spot price)
            strikes = []
            for product in asset_products:
                strike = product.get('strike_price')
                if strike:
                    strikes.append((abs(float(strike) - spot_price), product))
            
            if not strikes:
                logger.error("No valid strikes found")
                return None
            
            # Sort by distance from spot price
            strikes.sort(key=lambda x: x[0])
            
            # Apply ATM offset
            offset_index = max(0, min(atm_offset, len(strikes) - 1))
            selected_product = strikes[offset_index][1]
            
            logger.info(
                f"Selected {contract_type} contract: {selected_product.get('symbol')} "
                f"(Strike: ${selected_product.get('strike_price')}, "
                f"Offset: {atm_offset})"
            )
            
            return selected_product
        
        except Exception as e:
            logger.error(f"Error finding ATM option: {e}", exc_info=True)
            return None
    
    async def calculate_sl_target_prices(
        self,
        entry_price: float,
        direction: str,
        stop_loss_trigger: Optional[float],
        target_trigger: Optional[float]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate SL and Target prices based on strategy percentages.
        
        Args:
            entry_price: Entry order price
            direction: 'long' or 'short'
            stop_loss_trigger: SL percentage (e.g., 50 for 50% loss)
            target_trigger: Target percentage (e.g., 100 for 100% profit)
        
        Returns:
            (sl_price, target_price) tuple
        """
        sl_price = None
        target_price = None
        
        if stop_loss_trigger:
            # SL trigger is % of entry price we're willing to lose
            # For long: SL = entry - (entry * sl_pct)
            # For short: SL = entry + (entry * sl_pct)
            sl_pct = stop_loss_trigger / 100.0
            
            if direction.lower() == "long":
                sl_price = entry_price * (1 - sl_pct)
            else:  # short
                sl_price = entry_price * (1 + sl_pct)
        
        if target_trigger:
            # Target trigger is % profit we want
            # For long: Target = entry + (entry * target_pct)
            # For short: Target = entry - (entry * target_pct)
            target_pct = target_trigger / 100.0
            
            if direction.lower() == "long":
                target_price = entry_price * (1 + target_pct)
            else:  # short
                target_price = entry_price * (1 - target_pct)
        
        logger.info(
            f"Calculated prices - Entry: ${entry_price:.2f}, "
            f"SL: ${sl_price:.2f if sl_price else 'None'}, "
            f"Target: ${target_price:.2f if target_price else 'None'}"
        )
        
        return (sl_price, target_price)
    
    async def execute_move_trade(
        self,
        asset: str,
        direction: str,
        lot_size: int,
        atm_offset: int,
        stop_loss_trigger: Optional[float],
        stop_loss_limit: Optional[float],
        target_trigger: Optional[float],
        target_limit: Optional[float]
    ) -> Dict[str, Any]:
        """
        Execute complete move trade with entry + SL + Target orders.
        
        Args:
            asset: BTC or ETH
            direction: 'long' or 'short'
            lot_size: Number of contracts
            atm_offset: ATM strike offset
            stop_loss_trigger: SL trigger percentage
            stop_loss_limit: SL limit percentage
            target_trigger: Target trigger percentage
            target_limit: Target limit percentage
        
        Returns:
            Execution result dict with order details
        """
        try:
            # Step 1: Find ATM option
            product = await self.find_atm_option(asset, direction, atm_offset)
            
            if not product:
                return {
                    'success': False,
                    'error': 'Failed to find suitable option contract'
                }
            
            product_id = product['id']
            product_symbol = product['symbol']
            
            # Step 2: Place entry market order
            logger.info(f"Placing entry order: {direction} {lot_size} contracts of {product_symbol}")
            
            # Delta order side: 'buy' for both long and short (we're opening position)
            entry_order_data = {
                'product_id': product_id,
                'size': lot_size,
                'side': 'buy',  # Always buy for move options
                'order_type': 'market_order',
                'time_in_force': 'ioc'  # Immediate or cancel
            }
            
            entry_response = await self.client.place_order(entry_order_data)
            
            if not entry_response.get('success'):
                return {
                    'success': False,
                    'error': f"Entry order failed: {entry_response.get('error', {}).get('message', 'Unknown error')}"
                }
            
            entry_order = entry_response['result']
            entry_order_id = entry_order['id']
            
            # Get fill price (wait a moment for fill)
            import asyncio
            await asyncio.sleep(1)
            
            # Fetch filled order to get average price
            filled_order_response = await self.client.get_order(entry_order_id)
            filled_order = filled_order_response.get('result', {})
            
            avg_fill_price = float(filled_order.get('average_fill_price', 0))
            
            if avg_fill_price == 0:
                # Fallback to mark price if fill price not available
                ticker_response = await self.client.get_ticker(product_symbol)
                avg_fill_price = float(ticker_response.get('result', {}).get('mark_price', 0))
            
            logger.info(f"✅ Entry order filled! Average price: ${avg_fill_price:.2f}")
            
            # Step 3: Calculate SL and Target prices
            sl_price, target_price = await self.calculate_sl_target_prices(
                avg_fill_price,
                direction,
                stop_loss_trigger,
                target_trigger
            )
            
            # Step 4: Place bracket orders (SL and/or Target)
            sl_order_id = None
            target_order_id = None
            
            # Place Stop Loss order
            if sl_price:
                logger.info(f"Placing Stop Loss order at ${sl_price:.2f}")
                
                sl_order_data = {
                    'product_id': product_id,
                    'size': lot_size,
                    'side': 'sell',  # Close position
                    'order_type': 'stop_market_order',
                    'stop_price': round(sl_price, 2),
                    'time_in_force': 'gtc'  # Good til cancelled
                }
                
                sl_response = await self.client.place_order(sl_order_data)
                
                if sl_response.get('success'):
                    sl_order_id = sl_response['result']['id']
                    logger.info(f"✅ Stop Loss order placed: {sl_order_id}")
                else:
                    logger.warning(f"⚠️ SL order failed: {sl_response.get('error', {}).get('message')}")
            
            # Place Target order
            if target_price:
                logger.info(f"Placing Target order at ${target_price:.2f}")
                
                target_order_data = {
                    'product_id': product_id,
                    'size': lot_size,
                    'side': 'sell',  # Close position
                    'order_type': 'limit_order',
                    'limit_price': round(target_price, 2),
                    'time_in_force': 'gtc'
                }
                
                target_response = await self.client.place_order(target_order_data)
                
                if target_response.get('success'):
                    target_order_id = target_response['result']['id']
                    logger.info(f"✅ Target order placed: {target_order_id}")
                else:
                    logger.warning(f"⚠️ Target order failed: {target_response.get('error', {}).get('message')}")
            
            # Success!
            return {
                'success': True,
                'product': product,
                'entry_order': entry_order,
                'entry_price': avg_fill_price,
                'sl_order_id': sl_order_id,
                'sl_price': sl_price,
                'target_order_id': target_order_id,
                'target_price': target_price
            }
        
        except Exception as e:
            logger.error(f"Error executing move trade: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Execution failed: {str(e)}"
          }
      
