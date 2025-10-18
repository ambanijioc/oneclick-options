"""
Universal Move Options Trade Executor - For Delta Exchange MOVE contracts.
COMPLETELY REWRITTEN with proper strike selection, expiry support, and SL/Target fixes.
"""

from typing import Dict, Any, Optional, List, Tuple
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
    
    async def get_available_move_contracts(
        self,
        asset: str,
        expiry: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Get all available MOVE contracts for an asset and expiry type.
        
        Args:
            asset: BTC or ETH
            expiry: "daily", "weekly", or "monthly"
        
        Returns:
            List of MOVE contract dicts
        """
        try:
            # Fetch all MOVE options products
            products_response = await self.client.get_products(contract_types='move_options')
            
            if not products_response.get('success') or not products_response.get('result'):
                logger.error("Failed to fetch MOVE contracts")
                return []
            
            products = products_response['result']
            
            # Filter MOVE contracts for the asset
            asset_moves = [
                p for p in products
                if p.get('underlying_asset', {}).get('symbol') == asset
                and p.get('contract_type') == 'move_options'
                and p.get('state') in ['live', 'auction']
            ]
            
            if not asset_moves:
                logger.warning(f"No MOVE contracts found for {asset}")
                return []
            
            # Filter by expiry type
            filtered_moves = self._filter_by_expiry(asset_moves, expiry)
            
            logger.info(f"Found {len(filtered_moves)} {expiry} MOVE contracts for {asset}")
            
            return filtered_moves
        
        except Exception as e:
            logger.error(f"Error fetching MOVE contracts: {e}", exc_info=True)
            return []
    
    def _filter_by_expiry(
        self,
        contracts: List[Dict[str, Any]],
        expiry_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter contracts by expiry type.
        
        Args:
            contracts: List of MOVE contracts
            expiry_type: "daily", "weekly", or "monthly"
        
        Returns:
            Filtered contracts
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        filtered = []
        
        for contract in contracts:
            settlement_time_str = contract.get('settlement_time')
            
            if not settlement_time_str:
                continue
            
            try:
                settlement_time = datetime.fromisoformat(settlement_time_str.replace('Z', '+00:00'))
                time_diff = settlement_time - now
                
                if expiry_type == "daily":
                    # Daily: Expires within 48 hours
                    if time_diff.total_seconds() <= 48 * 3600:
                        filtered.append(contract)
                
                elif expiry_type == "weekly":
                    # Weekly: Expires between 2-10 days
                    if 2 * 24 * 3600 < time_diff.total_seconds() <= 10 * 24 * 3600:
                        filtered.append(contract)
                
                elif expiry_type == "monthly":
                    # Monthly: Expires between 10-40 days
                    if 10 * 24 * 3600 < time_diff.total_seconds() <= 40 * 24 * 3600:
                        filtered.append(contract)
            
            except Exception as e:
                logger.warning(f"Error parsing settlement time for {contract.get('symbol')}: {e}")
                continue
        
        return filtered
    
    async def find_atm_strike(
        self,
        asset: str,
        expiry: str = "daily"
    ) -> Optional[Tuple[float, List[Dict[str, Any]]]]:
        """
        Find ATM strike price closest to spot price.
        
        Args:
            asset: BTC or ETH
            expiry: "daily", "weekly", or "monthly"
        
        Returns:
            Tuple of (atm_strike, available_contracts) or None
        """
        try:
            # Get spot price
            spot_price = await self.client.get_spot_price(asset)
            
            if not spot_price:
                logger.error(f"Failed to get spot price for {asset}")
                return None
            
            logger.info(f"Current spot price for {asset}: ${spot_price:.2f}")
            
            # Get available contracts
            contracts = await self.get_available_move_contracts(asset, expiry)
            
            if not contracts:
                logger.error(f"No {expiry} MOVE contracts available for {asset}")
                return None
            
            # Extract available strikes
            strikes = sorted(set(float(c.get('strike_price', 0)) for c in contracts if c.get('strike_price')))
            
            if not strikes:
                logger.error("No strikes found in available contracts")
                return None
            
            # Find ATM strike (closest to spot)
            atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
            
            logger.info(f"ATM Strike: ${atm_strike:.2f} (Spot: ${spot_price:.2f})")
            
            return atm_strike, contracts
        
        except Exception as e:
            logger.error(f"Error finding ATM strike: {e}", exc_info=True)
            return None
    
    async def select_move_contract(
        self,
        asset: str,
        expiry: str,
        atm_offset: int = 0,
        fallback_direction: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select MOVE contract with ATM + offset logic.
        
        Args:
            asset: BTC or ETH
            expiry: "daily", "weekly", or "monthly"
            atm_offset: Strike offset from ATM (0 = ATM, +1 = one strike up, -1 = one strike down)
            fallback_direction: "up" or "down" for auto execution if exact strike unavailable
        
        Returns:
            Selected MOVE contract dict or None
        """
        try:
            result = await self.find_atm_strike(asset, expiry)
            
            if not result:
                return None
            
            atm_strike, contracts = result
            
            # Get all available strikes sorted
            strikes = sorted(set(float(c.get('strike_price', 0)) for c in contracts if c.get('strike_price')))
            
            # Calculate target strike with offset
            atm_index = strikes.index(atm_strike)
            target_index = atm_index + atm_offset
            
            # Check if target strike is available
            if 0 <= target_index < len(strikes):
                target_strike = strikes[target_index]
                logger.info(f"Target strike with offset {atm_offset:+d}: ${target_strike:.2f}")
            else:
                # Target strike not available - apply fallback
                if fallback_direction:
                    if fallback_direction == "up" and target_index >= len(strikes):
                        # Use highest available strike
                        target_strike = strikes[-1]
                        logger.warning(f"Target strike unavailable. Fallback to highest: ${target_strike:.2f}")
                    elif fallback_direction == "down" and target_index < 0:
                        # Use lowest available strike
                        target_strike = strikes[0]
                        logger.warning(f"Target strike unavailable. Fallback to lowest: ${target_strike:.2f}")
                    else:
                        # Clamp to available range
                        target_strike = strikes[max(0, min(target_index, len(strikes) - 1))]
                        logger.warning(f"Target strike adjusted to: ${target_strike:.2f}")
                else:
                    # No fallback - return None (manual will ask user)
                    logger.error(f"Target strike with offset {atm_offset:+d} not available")
                    return None
            
            # Find contract with target strike
            selected = next((c for c in contracts if float(c.get('strike_price', 0)) == target_strike), None)
            
            if selected:
                logger.info(f"✅ Selected MOVE contract: {selected['symbol']} (Strike: ${target_strike:.2f})")
            
            return selected
        
        except Exception as e:
            logger.error(f"Error selecting MOVE contract: {e}", exc_info=True)
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
        Calculate SL and Target prices for MOVE options.
        
        Args:
            entry_price: Entry premium
            direction: 'long' or 'short'
            stop_loss_trigger: SL trigger %
            stop_loss_limit: SL limit %
            target_trigger: Target trigger %
            target_limit: Target limit %
        
        Returns:
            Dict with trigger/limit prices
        """
        result = {
            'sl_trigger': None,
            'sl_limit': None,
            'target_trigger': None,
            'target_limit': None
        }
        
        # Calculate Stop Loss
        if stop_loss_trigger is not None and stop_loss_limit is not None:
            sl_trigger_pct = stop_loss_trigger / 100.0
            sl_limit_pct = stop_loss_limit / 100.0
            
            if direction.lower() == "long":
                result['sl_trigger'] = entry_price * (1 - sl_trigger_pct)
                result['sl_limit'] = entry_price * (1 - sl_limit_pct)
            else:  # short
                result['sl_trigger'] = entry_price * (1 + sl_trigger_pct)
                result['sl_limit'] = entry_price * (1 + sl_limit_pct)
        
        # Calculate Target
        if target_trigger is not None and target_limit is not None:
            target_trigger_pct = target_trigger / 100.0
            target_limit_pct = target_limit / 100.0
            
            if direction.lower() == "long":
                result['target_trigger'] = entry_price * (1 + target_trigger_pct)
                result['target_limit'] = entry_price * (1 + target_limit_pct)
            else:  # short
                result['target_trigger'] = entry_price * (1 - target_trigger_pct)
                result['target_limit'] = entry_price * (1 - target_limit_pct)
        
        logger.info(
            f"Calculated prices - Entry: ${entry_price:.2f}, "
            f"SL Trigger: ${result['sl_trigger']:.2f if result['sl_trigger'] else 'None'}, "
            f"Target Trigger: ${result['target_trigger']:.2f if result['target_trigger'] else 'None'}"
        )
        
        return result
    
    async def execute_move_trade(
        self,
        asset: str,
        expiry: str,
        direction: str,
        lot_size: int,
        atm_offset: int,
        stop_loss_trigger: Optional[float],
        stop_loss_limit: Optional[float],
        target_trigger: Optional[float],
        target_limit: Optional[float],
        fallback_direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete MOVE trade with entry + SL + Target.
        
        Args:
            asset: BTC or ETH
            expiry: "daily", "weekly", or "monthly"
            direction: 'long' or 'short'
            lot_size: Number of contracts
            atm_offset: Strike offset from ATM
            stop_loss_trigger: SL trigger %
            stop_loss_limit: SL limit %
            target_trigger: Target trigger %
            target_limit: Target limit %
            fallback_direction: "up" or "down" for auto fallback
        
        Returns:
            Execution result dict
        """
        try:
            # Step 1: Select MOVE contract
            product = await self.select_move_contract(asset, expiry, atm_offset, fallback_direction)
            
            if not product:
                return {
                    'success': False,
                    'error': f'No {expiry} MOVE contract available with offset {atm_offset:+d}'
                }
            
            product_id = product['id']
            product_symbol = product['symbol']
            strike_price = product.get('strike_price', 0)
            
            # Step 2: Place entry order
            order_side = 'buy' if direction.lower() == 'long' else 'sell'
            
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
                    'error': f"Entry order failed: {entry_response.get('error', {}).get('message', 'Unknown')}"
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
            
            logger.info(f"✅ MOVE entry filled! Average premium: ${avg_fill_price:.2f}")
            
            # Step 3: Calculate SL/Target prices
            prices = await self.calculate_sl_target_prices(
                avg_fill_price,
                direction,
                stop_loss_trigger,
                stop_loss_limit,
                target_trigger,
                target_limit
            )
            
            # Step 4: Place Stop Loss
            sl_order_id = None
            if prices['sl_trigger'] and prices['sl_limit']:
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
                    logger.info(f"✅ Stop Loss placed: {sl_order_id}")
            
            # Step 5: Place Target
            target_order_id = None
            if prices['target_trigger'] and prices['target_limit']:
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
                    logger.info(f"✅ Target placed: {target_order_id}")
            
            # Success!
            return {
                'success': True,
                'product': product,
                'strike_price': strike_price,
                'entry_order_id': entry_order_id,
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
                
