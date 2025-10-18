"""
Universal Move Options Trade Executor - For Delta Exchange MOVE contracts.
MOVE contracts are volatility products (straddles: ATM Call + ATM Put at same strike).
"""

from typing import Dict, Any, Optional
from datetime import datetime
from bot.utils.logger import setup_logger
from delta.client import DeltaClient

logger = setup_logger(__name__)


class MoveTradeExecutor:
    """
    Universal executor for Move options trades.
    MOVE contracts are ATM straddles - you profit from volatility magnitude, not direction.
    """
    
    def __init__(self, client: DeltaClient):
        """
        Initialize executor with Delta client.
        
        Args:
            client: Initialized DeltaClient instance
        """
        self.client = client
        logger.info("MoveTradeExecutor initialized for MOVE contracts")
    
    async def find_move_contract(
        self,
        asset: str,
        direction: str,
        atm_offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Find MOVE contract (volatility straddle product).
        
        MOVE contracts are ATM straddles with predetermined strike prices.
        Strike is set at start of measurement period (30min TWAP).
        
        Args:
            asset: BTC or ETH
            direction: 'long' (expect volatility) or 'short' (expect stability)
            atm_offset: Strike offset from ATM (0 = ATM, +1 = one strike higher, etc.)
        
        Returns:
            Product dict or None
        """
        try:
            # Get all MOVE options products
            products_response = await self.client.get_products(contract_types='move_options')
            
            if not products_response.get('success') or not products_response.get('result'):
                logger.error("Failed to fetch MOVE contracts")
                return None
            
            products = products_response['result']
            
            # Filter MOVE contracts for the asset
            asset_moves = [
                p for p in products
                if p.get('underlying_asset', {}).get('symbol') == asset
                and p.get('contract_type') == 'move_options'
                and p.get('state') in ['live', 'auction']  # Include live and auction states
            ]
            
            if not asset_moves:
                logger.error(f"No MOVE contracts found for {asset}")
                return None
            
            # If ATM offset is 0, select nearest expiry with live trading
            if atm_offset == 0:
                # Sort by settlement time (nearest first)
                asset_moves.sort(key=lambda x: x.get('settlement_time', float('inf')))
                
                # Select first live contract (or auction if no live available)
                for product in asset_moves:
                    if product.get('state') == 'live':
                        selected_product = product
                        break
                else:
                    # No live contracts, use first auction
                    selected_product = asset_moves[0]
                    logger.warning(f"Selected MOVE in auction mode: {selected_product.get('symbol')}")
            
            else:
                # ATM offset specified - need to get spot price and find strike
                spot_price = await self.get_spot_price_safe(asset)
                
                if not spot_price:
                    logger.error("Failed to get spot price for ATM offset calculation")
                    # Fallback to nearest expiry
                    asset_moves.sort(key=lambda x: x.get('settlement_time', float('inf')))
                    selected_product = asset_moves[0]
                else:
                    # Calculate target strike with offset
                    # Get strike increment from first contract
                    strike_increment = asset_moves[0].get('strike_price_increment', 100 if asset == 'BTC' else 10)
                    
                    # Round spot to nearest strike
                    atm_strike = round(spot_price / strike_increment) * strike_increment
                    target_strike = atm_strike + (atm_offset * strike_increment)
                    
                    logger.info(f"Spot: ${spot_price:.2f}, ATM: ${atm_strike}, Target: ${target_strike}")
                    
                    # Find MOVE contract with closest strike to target
                    # Filter by nearest expiry first
                    asset_moves.sort(key=lambda x: x.get('settlement_time', float('inf')))
                    nearest_expiry = asset_moves[0].get('settlement_time')
                    
                    same_expiry = [p for p in asset_moves if p.get('settlement_time') == nearest_expiry]
                    
                    # Find closest strike
                    selected_product = min(
                        same_expiry,
                        key=lambda x: abs(x.get('strike_price', 0) - target_strike)
                    )
            
            logger.info(
                f"✅ Selected MOVE contract: {selected_product.get('symbol')} "
                f"Strike: ${selected_product.get('strike_price', 'TBD')}, "
                f"Settlement: {selected_product.get('settlement_time')}, "
                f"Direction: {direction} = {'High Volatility' if direction.lower() == 'long' else 'Low Volatility'}"
            )
            
            return selected_product
        
        except Exception as e:
            logger.error(f"Error finding MOVE contract: {e}", exc_info=True)
            return None
    
    async def get_spot_price_safe(self, asset: str) -> Optional[float]:
        """
        Safely get spot price without failing on API errors.
        
        Args:
            asset: BTC or ETH
        
        Returns:
            Spot price or None
        """
        try:
            return await self.client.get_spot_price(asset)
        except Exception as e:
            logger.warning(f"Could not fetch spot price: {e}")
            return None
    
    async def calculate_sl_target_prices(
        self,
        entry_price: float,
        direction: str,
        stop_loss_trigger: Optional[float],
        stop_loss_limit: Optional[float],
        target_trigger: Optional[float],
        target_limit: Optional[float]
    ) -> Dict[str, Optional[float]]:
        """
        Calculate SL and Target prices for MOVE options with trigger and limit.
    
        For MOVE options:
        - Long MOVE: Profit from high volatility (price rises)
        - Short MOVE: Profit from low volatility (price drops)
    
        Args:
            entry_price: Entry order premium
            direction: 'long' (volatility) or 'short' (stability)
            stop_loss_trigger: SL trigger percentage (e.g., 50 for 50%)
            stop_loss_limit: SL limit percentage (e.g., 55 for 55%)
            target_trigger: Target trigger percentage (e.g., 100 for 100%)
            target_limit: Target limit percentage (e.g., 95 for 95%)
    
        Returns:
            Dict with trigger and limit prices for SL and Target
        """
        result = {
            'sl_trigger': None,
            'sl_limit': None,
            'target_trigger': None,
            'target_limit': None
        }
    
        # Calculate Stop Loss (if configured)
        if stop_loss_trigger is not None and stop_loss_limit is not None:
            sl_trigger_pct = stop_loss_trigger / 100.0
            sl_limit_pct = stop_loss_limit / 100.0
        
            if direction.lower() == "long":
                # Long MOVE: Loss if premium drops (volatility doesn't materialize)
                result['sl_trigger'] = entry_price * (1 - sl_trigger_pct)
                result['sl_limit'] = entry_price * (1 - sl_limit_pct)
            else:  # short
                # Short MOVE: Loss if premium rises (unexpected volatility)
                result['sl_trigger'] = entry_price * (1 + sl_trigger_pct)
                result['sl_limit'] = entry_price * (1 + sl_limit_pct)
        
        # Calculate Target (if configured)
        if target_trigger is not None and target_limit is not None:
            target_trigger_pct = target_trigger / 100.0
            target_limit_pct = target_limit / 100.0
        
            if direction.lower() == "long":
                # Long MOVE: Profit if premium rises (high volatility)
                result['target_trigger'] = entry_price * (1 + target_trigger_pct)
                result['target_limit'] = entry_price * (1 + target_limit_pct)
            else:  # short
                # Short MOVE: Profit if premium drops (low volatility)
                result['target_trigger'] = entry_price * (1 - target_trigger_pct)
                result['target_limit'] = entry_price * (1 - target_limit_pct)
        
        # Safe logging with None handling
        sl_trig_str = f"${result['sl_trigger']:.2f}" if result['sl_trigger'] is not None else 'None'
        sl_lim_str = f"${result['sl_limit']:.2f}" if result['sl_limit'] is not None else 'None'
        tgt_trig_str = f"${result['target_trigger']:.2f}" if result['target_trigger'] is not None else 'None'
        tgt_lim_str = f"${result['target_limit']:.2f}" if result['target_limit'] is not None else 'None'
    
        logger.info(
            f"Calculated prices - Entry: ${entry_price:.2f}, "
            f"SL Trigger: {sl_trig_str}, "
            f"SL Limit: {sl_lim_str}, "
            f"Target Trigger: {tgt_trig_str}, "
            f"Target Limit: {tgt_lim_str}"
        )
    
        return result
    
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
        Execute complete MOVE trade with entry + SL + Target orders.
        
        Args:
            asset: BTC or ETH
            direction: 'long' (volatility) or 'short' (stability)
            lot_size: Number of contracts
            atm_offset: Strike offset from ATM (0 = ATM, +/- for offset)
            stop_loss_trigger: SL trigger percentage
            stop_loss_limit: SL limit percentage
            target_trigger: Target trigger percentage
            target_limit: Target limit percentage
        
        Returns:
            Execution result dict with order details
        """
        try:
            # Step 1: Find MOVE contract with strike selection
            product = await self.find_move_contract(asset, direction, atm_offset)
            
            if not product:
                return {
                    'success': False,
                    'error': 'Failed to find MOVE contract'
                }
            
            product_id = product['id']
            product_symbol = product['symbol']
            
            # Step 2: Determine order side based on direction
            # Long MOVE = Buy (expect volatility)
            # Short MOVE = Sell (expect stability)
            order_side = 'buy' if direction.lower() == 'long' else 'sell'
            
            # Step 3: Place entry market order
            logger.info(f"Placing MOVE entry order: {direction} {lot_size} contracts of {product_symbol}")
            
            entry_order_data = {
                'product_id': product_id,
                'size': lot_size,
                'side': order_side,
                'order_type': 'market_order',
                'time_in_force': 'ioc'
            }
            
            entry_response = await self.client.place_order(entry_order_data)
            
            if not entry_response.get('success'):
                return {
                    'success': False,
                    'error': f"Entry order failed: {entry_response.get('error', {}).get('message', 'Unknown error')}"
                }
            
            entry_order = entry_response['result']
            entry_order_id = entry_order['id']
            
            # Get fill price
            import asyncio
            await asyncio.sleep(1)
            
            filled_order_response = await self.client.get_order(entry_order_id)
            filled_order = filled_order_response.get('result', {})
            
            avg_fill_price = float(filled_order.get('average_fill_price', 0))
            
            if avg_fill_price == 0:
                ticker_response = await self.client.get_ticker(product_symbol)
                avg_fill_price = float(ticker_response.get('result', {}).get('mark_price', 0))
            
            logger.info(f"✅ MOVE entry order filled! Average premium: ${avg_fill_price:.2f}")
            
            # Step 4: Calculate SL and Target prices (trigger + limit)
            prices = await self.calculate_sl_target_prices(
                avg_fill_price,
                direction,
                stop_loss_trigger,
                stop_loss_limit,
                target_trigger,
                target_limit
            )
            
            # Step 5: Place Stop Loss order (with trigger and limit)
            sl_order_id = None
            if prices['sl_trigger'] and prices['sl_limit']:
                logger.info(f"Placing Stop Loss: Trigger=${prices['sl_trigger']:.2f}, Limit=${prices['sl_limit']:.2f}")
                
                # For MOVE: If long, SL sells. If short, SL buys.
                sl_side = 'sell' if direction.lower() == 'long' else 'buy'
                
                sl_order_data = {
                    'product_id': product_id,
                    'size': lot_size,
                    'side': sl_side,
                    'order_type': 'stop_limit_order',
                    'stop_price': round(prices['sl_trigger'], 2),
                    'limit_price': round(prices['sl_limit'], 2),
                    'time_in_force': 'gtc'
                }
                
                sl_response = await self.client.place_order(sl_order_data)
                
                if sl_response.get('success'):
                    sl_order_id = sl_response['result']['id']
                    logger.info(f"✅ Stop Loss order placed: {sl_order_id}")
                else:
                    logger.warning(f"⚠️ SL order failed: {sl_response.get('error', {}).get('message')}")
            
            # Step 6: Place Target order (with trigger and limit)
            target_order_id = None
            if prices['target_trigger'] and prices['target_limit']:
                logger.info(f"Placing Target: Trigger=${prices['target_trigger']:.2f}, Limit=${prices['target_limit']:.2f}")
                
                # For MOVE: If long, Target sells. If short, Target buys.
                target_side = 'sell' if direction.lower() == 'long' else 'buy'
                
                target_order_data = {
                    'product_id': product_id,
                    'size': lot_size,
                    'side': target_side,
                    'order_type': 'stop_limit_order',
                    'stop_price': round(prices['target_trigger'], 2),
                    'limit_price': round(prices['target_limit'], 2),
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
                'sl_trigger': prices['sl_trigger'],
                'sl_limit': prices['sl_limit'],
                'target_order_id': target_order_id,
                'target_trigger': prices['target_trigger'],
                'target_limit': prices['target_limit']
            }
        
        except Exception as e:
            logger.error(f"Error executing MOVE trade: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Execution failed: {str(e)}"
    }
        
