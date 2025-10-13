"""
Delta Exchange stop loss and target management.
Handles setting, modifying, and managing SL/TP for positions.
"""

from typing import Dict, Any, Optional

from delta.client import DeltaClient
from delta.orders import Orders, OrderSide
from logger import logger, log_function_call


class StopLossTarget:
    """Stop loss and take profit management for Delta Exchange."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize SL/TP handler.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        self.orders = Orders(client)
        logger.debug("[StopLossTarget.__init__] Initialized SL/TP handler")
    
    @log_function_call
    async def set_bracket_order(
        self,
        position: Dict[str, Any],
        sl_trigger_percentage: float,
        sl_limit_percentage: Optional[float] = None,
        tp_trigger_percentage: Optional[float] = None,
        tp_limit_percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Set bracket order (SL/TP) for a position.
        
        Args:
            position: Position dictionary
            sl_trigger_percentage: Stop loss trigger percentage
            sl_limit_percentage: Stop loss limit percentage (optional)
            tp_trigger_percentage: Take profit trigger percentage (optional)
            tp_limit_percentage: Take profit limit percentage (optional)
        
        Returns:
            Dictionary with order placement results
        """
        try:
            product_id = position.get('product_id')
            size = abs(float(position.get('size', 0)))
            entry_price = float(position.get('entry_price', 0))
            is_long = float(position.get('size', 0)) > 0
            
            # Determine order side (opposite of position)
            side = OrderSide.SELL.value if is_long else OrderSide.BUY.value
            
            # Calculate SL prices
            if is_long:
                sl_trigger = entry_price * (1 + sl_trigger_percentage / 100)
                sl_limit = entry_price * (1 + (sl_limit_percentage or sl_trigger_percentage) / 100)
            else:
                sl_trigger = entry_price * (1 - sl_trigger_percentage / 100)
                sl_limit = entry_price * (1 - (sl_limit_percentage or sl_trigger_percentage) / 100)
            
            # Calculate TP prices if provided
            tp_trigger = None
            tp_limit = None
            if tp_trigger_percentage is not None:
                if is_long:
                    tp_trigger = entry_price * (1 + tp_trigger_percentage / 100)
                    tp_limit = entry_price * (1 + (tp_limit_percentage or tp_trigger_percentage) / 100)
                else:
                    tp_trigger = entry_price * (1 - tp_trigger_percentage / 100)
                    tp_limit = entry_price * (1 - (tp_limit_percentage or tp_trigger_percentage) / 100)
            
            logger.info(
                f"[StopLossTarget.set_bracket_order] Setting bracket order for "
                f"product {product_id}: SL Trigger={sl_trigger}, TP Trigger={tp_trigger}"
            )
            
            # Place bracket order
            order = await self.orders.place_bracket_order(
                product_id=product_id,
                size=size,
                side=side,
                sl_trigger_price=sl_trigger,
                sl_limit_price=sl_limit,
                tp_trigger_price=tp_trigger,
                tp_limit_price=tp_limit
            )
            
            if order:
                return {
                    'success': True,
                    'order_id': order.get('id'),
                    'sl_trigger': sl_trigger,
                    'sl_limit': sl_limit,
                    'tp_trigger': tp_trigger,
                    'tp_limit': tp_limit
                }
            else:
                return {'success': False, 'error': 'Failed to place bracket order'}
            
        except Exception as e:
            logger.error(f"[StopLossTarget.set_bracket_order] Error: {e}")
            return {'success': False, 'error': str(e)}
    
    @log_function_call
    async def set_sl_to_cost(
        self,
        position: Dict[str, Any],
        buffer_percentage: float = 0.2
    ) -> Dict[str, Any]:
        """
        Set stop loss to cost (entry price) with optional buffer.
        
        Args:
            position: Position dictionary
            buffer_percentage: Buffer percentage from entry (default 0.2%)
        
        Returns:
            Dictionary with order placement results
        """
        try:
            product_id = position.get('product_id')
            size = abs(float(position.get('size', 0)))
            entry_price = float(position.get('entry_price', 0))
            is_long = float(position.get('size', 0)) > 0
            
            # Determine order side (opposite of position)
            side = OrderSide.SELL.value if is_long else OrderSide.BUY.value
            
            # Calculate SL at entry price with buffer
            if is_long:
                sl_trigger = entry_price
                sl_limit = entry_price * (1 + buffer_percentage / 100)
            else:
                sl_trigger = entry_price
                sl_limit = entry_price * (1 - buffer_percentage / 100)
            
            logger.info(
                f"[StopLossTarget.set_sl_to_cost] Setting SL to cost for "
                f"product {product_id}: Entry={entry_price}, Buffer={buffer_percentage}%"
            )
            
            # Place bracket order with only SL
            order = await self.orders.place_bracket_order(
                product_id=product_id,
                size=size,
                side=side,
                sl_trigger_price=sl_trigger,
                sl_limit_price=sl_limit
            )
            
            if order:
                return {
                    'success': True,
                    'order_id': order.get('id'),
                    'sl_trigger': sl_trigger,
                    'sl_limit': sl_limit,
                    'entry_price': entry_price
                }
            else:
                return {'success': False, 'error': 'Failed to place SL order'}
            
        except Exception as e:
            logger.error(f"[StopLossTarget.set_sl_to_cost] Error: {e}")
            return {'success': False, 'error': str(e)}
    
    @log_function_call
    async def modify_stoploss(
        self,
        order_id: str,
        new_trigger_price: float,
        new_limit_price: Optional[float] = None
    ) -> bool:
        """
        Modify existing stop loss order.
        
        Args:
            order_id: Order ID to modify
            new_trigger_price: New trigger price
            new_limit_price: New limit price (optional)
        
        Returns:
            True if modified successfully, False otherwise
        """
        try:
            logger.info(
                f"[StopLossTarget.modify_stoploss] Modifying order {order_id}: "
                f"New trigger={new_trigger_price}"
            )
            
            order = await self.orders.edit_order(
                order_id=order_id,
                stop_price=new_trigger_price,
                limit_price=new_limit_price
            )
            
            if order:
                logger.info(f"[StopLossTarget.modify_stoploss] Order {order_id} modified")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[StopLossTarget.modify_stoploss] Error: {e}")
            return False
    
    @log_function_call
    async def validate_order_type_for_position(
        self,
        position: Dict[str, Any],
        order_purpose: str
    ) -> Dict[str, Any]:
        """
        Validate appropriate order type for position direction.
        
        For long positions:
        - Target: Use limit_order (can place limit sell above current price)
        - Stop Loss: Use bracket_order (requires stop order type)
        
        For short positions:
        - Target: Use bracket_order (buying back at lower price)
        - Stop Loss: Use limit_order (can place limit buy above current price)
        
        Args:
            position: Position dictionary
            order_purpose: 'sl' or 'tp'
        
        Returns:
            Dictionary with validation results
        """
        try:
            is_long = float(position.get('size', 0)) > 0
            
            if order_purpose.lower() == 'sl':
                # Stop loss validation
                if is_long:
                    recommended_type = 'bracket_order'
                    reason = 'Long position requires bracket order for stop loss'
                else:
                    recommended_type = 'limit_order'
                    reason = 'Short position can use limit order for stop loss'
            else:  # tp
                # Take profit validation
                if is_long:
                    recommended_type = 'limit_order'
                    reason = 'Long position can use limit order for take profit'
                else:
                    recommended_type = 'bracket_order'
                    reason = 'Short position requires bracket order for take profit'
            
            logger.info(
                f"[StopLossTarget.validate_order_type_for_position] "
                f"Position direction={'long' if is_long else 'short'}, "
                f"Purpose={order_purpose}, Recommended={recommended_type}"
            )
            
            return {
                'is_valid': True,
                'is_long': is_long,
                'order_purpose': order_purpose,
                'recommended_type': recommended_type,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"[StopLossTarget.validate_order_type_for_position] Error: {e}")
            return {'is_valid': False, 'error': str(e)}
    
    @log_function_call
    async def calculate_sl_tp_prices(
        self,
        entry_price: float,
        is_long: bool,
        sl_trigger_pct: float,
        sl_limit_pct: Optional[float] = None,
        tp_trigger_pct: Optional[float] = None,
        tp_limit_pct: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        Calculate SL/TP prices from percentages.
        
        Args:
            entry_price: Entry price
            is_long: True if long position
            sl_trigger_pct: SL trigger percentage
            sl_limit_pct: SL limit percentage (optional)
            tp_trigger_pct: TP trigger percentage (optional)
            tp_limit_pct: TP limit percentage (optional)
        
        Returns:
            Dictionary with calculated prices
        """
        try:
            prices = {}
            
            # Calculate SL prices
            if is_long:
                prices['sl_trigger'] = entry_price * (1 + sl_trigger_pct / 100)
                prices['sl_limit'] = entry_price * (1 + (sl_limit_pct or sl_trigger_pct) / 100)
            else:
                prices['sl_trigger'] = entry_price * (1 - abs(sl_trigger_pct) / 100)
                prices['sl_limit'] = entry_price * (1 - abs(sl_limit_pct or sl_trigger_pct) / 100)
            
            # Calculate TP prices if provided
            if tp_trigger_pct is not None:
                if is_long:
                    prices['tp_trigger'] = entry_price * (1 + tp_trigger_pct / 100)
                    prices['tp_limit'] = entry_price * (1 + (tp_limit_pct or tp_trigger_pct) / 100)
                else:
                    prices['tp_trigger'] = entry_price * (1 - abs(tp_trigger_pct) / 100)
                    prices['tp_limit'] = entry_price * (1 - abs(tp_limit_pct or tp_trigger_pct) / 100)
            else:
                prices['tp_trigger'] = None
                prices['tp_limit'] = None
            
            logger.info(
                f"[StopLossTarget.calculate_sl_tp_prices] Calculated prices: {prices}"
            )
            
            return prices
            
        except Exception as e:
            logger.error(f"[StopLossTarget.calculate_sl_tp_prices] Error: {e}")
            return {}


if __name__ == "__main__":
    import asyncio
    
    async def test_stoploss_target():
        """Test SL/TP operations."""
        print("Testing Delta Exchange StopLoss/Target...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        sl_tp = StopLossTarget(client)
        
        try:
            # Test price calculation
            prices = await sl_tp.calculate_sl_tp_prices(
                entry_price=95000.0,
                is_long=True,
                sl_trigger_pct=-5.0,
                sl_limit_pct=-5.5,
                tp_trigger_pct=10.0,
                tp_limit_pct=9.5
            )
            print(f"✅ Calculated SL/TP prices: {prices}")
            
            # Test validation
            mock_position = {'product_id': 27, 'size': 1.0, 'entry_price': 95000.0}
            validation = await sl_tp.validate_order_type_for_position(mock_position, 'sl')
            print(f"✅ Order type validation: {validation}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ StopLoss/Target test completed!")
    
    asyncio.run(test_stoploss_target())
  
