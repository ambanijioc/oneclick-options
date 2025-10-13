"""
Strangle strategy execution.
Handles OTM strangle trades with call and put at different strikes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from delta.client import DeltaClient
from delta.market_data import MarketData
from delta.products import Products
from delta.orders import Orders
from strategies.calculations import calculate_otm_strikes
from logger import logger, log_function_call
from utils.error_handler import DeltaAPIError, ValidationError


class StrangleStrategy:
    """OTM Strangle strategy implementation."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize strangle strategy.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        self.market_data = MarketData(client)
        self.products = Products(client)
        self.orders = Orders(client)
        logger.debug("[StrangleStrategy.__init__] Initialized strangle strategy")
    
    @log_function_call
    async def execute_strangle(
        self,
        asset: str,
        expiry_date: str,
        direction: str,
        lot_size: int,
        otm_percentage: Optional[float] = None,
        otm_value: Optional[int] = None,
        limit_price_call: Optional[float] = None,
        limit_price_put: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute strangle strategy.
        
        Args:
            asset: Asset symbol (BTC/ETH)
            expiry_date: Expiry date string (YYYY-MM-DD)
            direction: Trade direction ('long' or 'short')
            lot_size: Number of lots
            otm_percentage: OTM percentage from spot
            otm_value: OTM absolute value from spot
            limit_price_call: Optional limit price for call
            limit_price_put: Optional limit price for put
        
        Returns:
            Execution result dictionary
        """
        try:
            logger.info(
                f"[StrangleStrategy.execute_strangle] Executing {direction} strangle: "
                f"{asset}, expiry: {expiry_date}, lots: {lot_size}, "
                f"OTM: {otm_percentage}% or {otm_value}"
            )
            
            # Validate OTM input
            if not otm_percentage and not otm_value:
                raise ValidationError("Either otm_percentage or otm_value must be provided")
            
            # Step 1: Get current spot price
            spot_symbol = f"{asset}USD"
            spot_price = await self.market_data.get_spot_price(spot_symbol)
            
            if not spot_price:
                raise DeltaAPIError("Failed to fetch spot price")
            
            logger.info(f"[StrangleStrategy.execute_strangle] Current spot: {spot_price}")
            
            # Step 2: Calculate OTM strike prices
            call_strike, put_strike = calculate_otm_strikes(
                spot_price=spot_price,
                asset=asset,
                otm_percentage=otm_percentage,
                otm_value=otm_value
            )
            
            logger.info(
                f"[StrangleStrategy.execute_strangle] Calculated strikes: "
                f"Call={call_strike}, Put={put_strike}"
            )
            
            # Step 3: Find option products
            call_option = await self.products.find_option_by_strike(
                asset=asset,
                expiry=expiry_date,
                strike=call_strike,
                option_type='call_options'
            )
            
            put_option = await self.products.find_option_by_strike(
                asset=asset,
                expiry=expiry_date,
                strike=put_strike,
                option_type='put_options'
            )
            
            if not call_option or not put_option:
                raise ValidationError(
                    f"Could not find options for strikes Call={call_strike}, "
                    f"Put={put_strike}, expiry={expiry_date}"
                )
            
            call_product_id = call_option['id']
            put_product_id = put_option['id']
            
            logger.info(
                f"[StrangleStrategy.execute_strangle] Found products: "
                f"Call ID={call_product_id}, Put ID={put_product_id}"
            )
            
            # Step 4: Determine order side
            side = 'buy' if direction.lower() == 'long' else 'sell'
            
            # Step 5: Place orders
            orders_placed = []
            
            # Place call order
            call_order = await self.orders.place_order(
                product_id=call_product_id,
                size=lot_size,
                side=side,
                order_type='limit_order' if limit_price_call else 'market_order',
                limit_price=limit_price_call
            )
            
            if call_order:
                orders_placed.append({
                    'type': 'call',
                    'order_id': call_order.get('id'),
                    'product_id': call_product_id,
                    'strike': call_strike,
                    'status': call_order.get('state')
                })
                logger.info(
                    f"[StrangleStrategy.execute_strangle] Call order placed: "
                    f"ID={call_order.get('id')}"
                )
            else:
                raise DeltaAPIError("Failed to place call order")
            
            # Place put order
            put_order = await self.orders.place_order(
                product_id=put_product_id,
                size=lot_size,
                side=side,
                order_type='limit_order' if limit_price_put else 'market_order',
                limit_price=limit_price_put
            )
            
            if put_order:
                orders_placed.append({
                    'type': 'put',
                    'order_id': put_order.get('id'),
                    'product_id': put_product_id,
                    'strike': put_strike,
                    'status': put_order.get('state')
                })
                logger.info(
                    f"[StrangleStrategy.execute_strangle] Put order placed: "
                    f"ID={put_order.get('id')}"
                )
            else:
                # Cancel call order if put fails
                await self.orders.cancel_order(call_order.get('id'))
                raise DeltaAPIError("Failed to place put order")
            
            # Success response
            result = {
                'success': True,
                'strategy': 'strangle',
                'asset': asset,
                'direction': direction,
                'spot_price': spot_price,
                'call_strike': call_strike,
                'put_strike': put_strike,
                'otm_percentage': otm_percentage,
                'otm_value': otm_value,
                'lot_size': lot_size,
                'expiry': expiry_date,
                'orders': orders_placed,
                'timestamp': datetime.now(pytz.UTC).isoformat()
            }
            
            logger.info(
                f"[StrangleStrategy.execute_strangle] Strangle executed successfully: "
                f"{len(orders_placed)} orders"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[StrangleStrategy.execute_strangle] Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'strategy': 'strangle'
            }
    
    @log_function_call
    async def validate_strangle_params(
        self,
        asset: str,
        expiry_date: str,
        direction: str,
        lot_size: int,
        otm_percentage: Optional[float],
        otm_value: Optional[int]
    ) -> Dict[str, Any]:
        """
        Validate strangle parameters before execution.
        
        Args:
            asset: Asset symbol
            expiry_date: Expiry date
            direction: Trade direction
            lot_size: Lot size
            otm_percentage: OTM percentage
            otm_value: OTM value
        
        Returns:
            Validation result dictionary
        """
        try:
            errors = []
            
            # Validate asset
            if asset.upper() not in ['BTC', 'ETH']:
                errors.append("Asset must be BTC or ETH")
            
            # Validate direction
            if direction.lower() not in ['long', 'short']:
                errors.append("Direction must be 'long' or 'short'")
            
            # Validate lot size
            if lot_size <= 0:
                errors.append("Lot size must be positive")
            
            # Validate OTM input
            if not otm_percentage and not otm_value:
                errors.append("Either OTM percentage or OTM value must be provided")
            
            if otm_percentage and otm_value:
                errors.append("Provide either OTM percentage OR OTM value, not both")
            
            if otm_percentage and (otm_percentage <= 0 or otm_percentage > 50):
                errors.append("OTM percentage must be between 0 and 50")
            
            if otm_value and otm_value <= 0:
                errors.append("OTM value must be positive")
            
            # Validate expiry exists
            available_expiries = await self.products.get_available_expiries(asset)
            if expiry_date not in available_expiries:
                errors.append(f"Expiry {expiry_date} not available")
            
            if errors:
                logger.warning(
                    f"[StrangleStrategy.validate_strangle_params] Validation failed: {errors}"
                )
                return {
                    'valid': False,
                    'errors': errors
                }
            
            logger.info("[StrangleStrategy.validate_strangle_params] Validation passed")
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"[StrangleStrategy.validate_strangle_params] Error: {e}")
            return {
                'valid': False,
                'errors': [str(e)]
            }
    
    @log_function_call
    async def get_strangle_preview(
        self,
        asset: str,
        expiry_date: str,
        direction: str,
        lot_size: int,
        otm_percentage: Optional[float] = None,
        otm_value: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get preview of strangle trade without executing.
        
        Args:
            asset: Asset symbol
            expiry_date: Expiry date
            direction: Trade direction
            lot_size: Lot size
            otm_percentage: OTM percentage
            otm_value: OTM value
        
        Returns:
            Preview information dictionary
        """
        try:
            # Get spot price
            spot_symbol = f"{asset}USD"
            spot_price = await self.market_data.get_spot_price(spot_symbol)
            
            if not spot_price:
                raise DeltaAPIError("Failed to fetch spot price")
            
            # Calculate strikes
            call_strike, put_strike = calculate_otm_strikes(
                spot_price=spot_price,
                asset=asset,
                otm_percentage=otm_percentage,
                otm_value=otm_value
            )
            
            # Find options
            call_option = await self.products.find_option_by_strike(
                asset=asset,
                expiry=expiry_date,
                strike=call_strike,
                option_type='call_options'
            )
            
            put_option = await self.products.find_option_by_strike(
                asset=asset,
                expiry=expiry_date,
                strike=put_strike,
                option_type='put_options'
            )
            
            preview = {
                'strategy': 'strangle',
                'asset': asset,
                'direction': direction,
                'spot_price': spot_price,
                'call_strike': call_strike,
                'put_strike': put_strike,
                'otm_percentage': otm_percentage,
                'otm_value': otm_value,
                'lot_size': lot_size,
                'expiry': expiry_date,
                'call_option': {
                    'symbol': call_option.get('symbol') if call_option else None,
                    'strike': call_strike,
                    'available': call_option is not None
                },
                'put_option': {
                    'symbol': put_option.get('symbol') if put_option else None,
                    'strike': put_strike,
                    'available': put_option is not None
                }
            }
            
            logger.info(
                f"[StrangleStrategy.get_strangle_preview] Preview generated for "
                f"{asset} {direction} strangle"
            )
            
            return preview
            
        except Exception as e:
            logger.error(f"[StrangleStrategy.get_strangle_preview] Error: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    import asyncio
    
    async def test_strangle():
        """Test strangle strategy."""
        print("Testing Strangle Strategy...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        strangle = StrangleStrategy(client)
        
        try:
            # Test preview
            preview = await strangle.get_strangle_preview(
                asset="BTC",
                expiry_date="2025-10-15",
                direction="long",
                lot_size=1,
                otm_percentage=1.0
            )
            print(f"✅ Strangle preview: {preview}")
            
            # Test validation
            validation = await strangle.validate_strangle_params(
                asset="BTC",
                expiry_date="2025-10-15",
                direction="long",
                lot_size=1,
                otm_percentage=1.0,
                otm_value=None
            )
            print(f"✅ Validation: {validation}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Strangle test completed!")
    
    asyncio.run(test_strangle())
  
