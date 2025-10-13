"""
Strategy execution orchestrator.
Handles strategy execution with SL/TP, error handling, and trade recording.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz

from delta.client import DeltaClient
from delta.stoploss_target import StopLossTarget
from delta.positions import Positions
from strategies.straddle import StraddleStrategy
from strategies.strangle import StrangleStrategy
from database.trade_operations import TradeOperations
from database.strategy_operations import StrategyOperations
from database.models import StrategyTypeEnum
from logger import logger, log_function_call
from utils.error_handler import (
    DeltaAPIError,
    ValidationError,
    InsufficientBalanceError,
    format_error_for_user
)
from utils.helpers import parse_expiry_notation


class StrategyExecutor:
    """Orchestrates strategy execution with complete trade lifecycle management."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize strategy executor.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        self.straddle = StraddleStrategy(client)
        self.strangle = StrangleStrategy(client)
        self.sl_tp = StopLossTarget(client)
        self.positions = Positions(client)
        self.trade_ops = TradeOperations()
        self.strategy_ops = StrategyOperations()
        logger.debug("[StrategyExecutor.__init__] Initialized strategy executor")
    
    @log_function_call
    async def execute_strategy_from_preset(
        self,
        user_id: int,
        api_name: str,
        strategy_type: str,
        strategy_name: str
    ) -> Dict[str, Any]:
        """
        Execute strategy from saved preset.
        
        Args:
            user_id: Telegram user ID
            api_name: API name to use
            strategy_type: Strategy type ('straddle' or 'strangle')
            strategy_name: Strategy preset name
        
        Returns:
            Execution result dictionary
        """
        try:
            logger.info(
                f"[StrategyExecutor.execute_strategy_from_preset] Executing {strategy_type} "
                f"strategy '{strategy_name}' for user {user_id} using API '{api_name}'"
            )
            
            # Step 1: Get strategy preset
            strategy_enum = StrategyTypeEnum.STRADDLE if strategy_type.lower() == 'straddle' else StrategyTypeEnum.STRANGLE
            
            strategy_preset = await self.strategy_ops.get_strategy_by_name(
                user_id=user_id,
                strategy_name=strategy_name,
                strategy_type=strategy_enum
            )
            
            if not strategy_preset:
                raise ValidationError(f"Strategy '{strategy_name}' not found")
            
            logger.info(f"[StrategyExecutor.execute_strategy_from_preset] Loaded strategy preset")
            
            # Step 2: Parse expiry notation to actual date
            expiry_notation = strategy_preset.get('expiry')
            expiry_datetime = parse_expiry_notation(expiry_notation)
            
            if not expiry_datetime:
                raise ValidationError(f"Invalid expiry notation: {expiry_notation}")
            
            expiry_date = expiry_datetime.strftime('%Y-%m-%d')
            
            # Step 3: Execute strategy
            if strategy_type.lower() == 'straddle':
                result = await self._execute_straddle_from_preset(
                    strategy_preset=strategy_preset,
                    expiry_date=expiry_date
                )
            else:  # strangle
                result = await self._execute_strangle_from_preset(
                    strategy_preset=strategy_preset,
                    expiry_date=expiry_date
                )
            
            if not result.get('success'):
                return result
            
            # Step 4: Apply SL/TP if configured
            if strategy_preset.get('stoploss_config') or strategy_preset.get('target_config'):
                await self._apply_sl_tp_to_orders(
                    orders=result.get('orders', []),
                    stoploss_config=strategy_preset.get('stoploss_config'),
                    target_config=strategy_preset.get('target_config'),
                    direction=strategy_preset.get('direction')
                )
            
            # Step 5: Record trade
            await self._record_trade(
                user_id=user_id,
                api_name=api_name,
                strategy_type=strategy_type,
                strategy_name=strategy_name,
                execution_result=result,
                strategy_preset=strategy_preset
            )
            
            logger.info(
                f"[StrategyExecutor.execute_strategy_from_preset] Strategy executed successfully"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[StrategyExecutor.execute_strategy_from_preset] Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_message': format_error_for_user(e)
            }
    
    @log_function_call
    async def _execute_straddle_from_preset(
        self,
        strategy_preset: Dict[str, Any],
        expiry_date: str
    ) -> Dict[str, Any]:
        """
        Execute straddle from preset configuration.
        
        Args:
            strategy_preset: Strategy preset dictionary
            expiry_date: Calculated expiry date
        
        Returns:
            Execution result
        """
        try:
            return await self.straddle.execute_straddle(
                asset=strategy_preset.get('asset'),
                expiry_date=expiry_date,
                direction=strategy_preset.get('direction'),
                lot_size=strategy_preset.get('lot_size'),
                atm_offset=strategy_preset.get('atm_offset', 0)
            )
        except Exception as e:
            logger.error(f"[StrategyExecutor._execute_straddle_from_preset] Error: {e}")
            raise
    
    @log_function_call
    async def _execute_strangle_from_preset(
        self,
        strategy_preset: Dict[str, Any],
        expiry_date: str
    ) -> Dict[str, Any]:
        """
        Execute strangle from preset configuration.
        
        Args:
            strategy_preset: Strategy preset dictionary
            expiry_date: Calculated expiry date
        
        Returns:
            Execution result
        """
        try:
            return await self.strangle.execute_strangle(
                asset=strategy_preset.get('asset'),
                expiry_date=expiry_date,
                direction=strategy_preset.get('direction'),
                lot_size=strategy_preset.get('lot_size'),
                otm_percentage=strategy_preset.get('otm_percentage'),
                otm_value=strategy_preset.get('otm_value')
            )
        except Exception as e:
            logger.error(f"[StrategyExecutor._execute_strangle_from_preset] Error: {e}")
            raise
    
    @log_function_call
    async def _apply_sl_tp_to_orders(
        self,
        orders: List[Dict[str, Any]],
        stoploss_config: Optional[Dict[str, float]],
        target_config: Optional[Dict[str, float]],
        direction: str
    ):
        """
        Apply stop loss and take profit to executed orders.
        
        Args:
            orders: List of placed orders
            stoploss_config: Stop loss configuration
            target_config: Target configuration
            direction: Trade direction
        """
        try:
            logger.info(
                f"[StrategyExecutor._apply_sl_tp_to_orders] Applying SL/TP to "
                f"{len(orders)} orders"
            )
            
            # Wait a moment for orders to be filled
            import asyncio
            await asyncio.sleep(2)
            
            # Get current positions
            positions = await self.positions.get_positions()
            
            for order in orders:
                product_id = order.get('product_id')
                
                # Find corresponding position
                position = next(
                    (p for p in positions if p.get('product_id') == product_id),
                    None
                )
                
                if not position:
                    logger.warning(
                        f"[StrategyExecutor._apply_sl_tp_to_orders] No position found "
                        f"for product {product_id}"
                    )
                    continue
                
                # Apply SL/TP
                sl_trigger_pct = None
                sl_limit_pct = None
                tp_trigger_pct = None
                tp_limit_pct = None
                
                if stoploss_config:
                    sl_trigger_pct = stoploss_config.get('trigger_percentage')
                    sl_limit_pct = stoploss_config.get('limit_percentage')
                
                if target_config:
                    tp_trigger_pct = target_config.get('trigger_percentage')
                    tp_limit_pct = target_config.get('limit_percentage')
                
                if sl_trigger_pct:
                    result = await self.sl_tp.set_bracket_order(
                        position=position,
                        sl_trigger_percentage=sl_trigger_pct,
                        sl_limit_percentage=sl_limit_pct,
                        tp_trigger_percentage=tp_trigger_pct,
                        tp_limit_percentage=tp_limit_pct
                    )
                    
                    if result.get('success'):
                        logger.info(
                            f"[StrategyExecutor._apply_sl_tp_to_orders] SL/TP set for "
                            f"product {product_id}"
                        )
                    else:
                        logger.warning(
                            f"[StrategyExecutor._apply_sl_tp_to_orders] Failed to set SL/TP "
                            f"for product {product_id}: {result.get('error')}"
                        )
            
        except Exception as e:
            logger.error(f"[StrategyExecutor._apply_sl_tp_to_orders] Error: {e}")
            # Don't raise - SL/TP failure shouldn't fail entire execution
    
    @log_function_call
    async def _record_trade(
        self,
        user_id: int,
        api_name: str,
        strategy_type: str,
        strategy_name: str,
        execution_result: Dict[str, Any],
        strategy_preset: Dict[str, Any]
    ):
        """
        Record trade in database.
        
        Args:
            user_id: User ID
            api_name: API name
            strategy_type: Strategy type
            strategy_name: Strategy name
            execution_result: Execution result
            strategy_preset: Strategy preset
        """
        try:
            # Extract entry prices from orders
            entry_prices = {}
            order_ids = []
            
            for order in execution_result.get('orders', []):
                order_type = order.get('type')  # 'call' or 'put'
                strike = order.get('strike')
                order_ids.append(order.get('order_id'))
                
                # We'll fetch actual fill prices later, for now use strikes as placeholders
                entry_prices[f"{strike}_{order_type.upper()}"] = strike
            
            # Store trade record
            await self.trade_ops.store_trade(
                user_id=user_id,
                api_name=api_name,
                strategy_type=strategy_type,
                strategy_name=strategy_name,
                asset=execution_result.get('asset'),
                direction=execution_result.get('direction'),
                entry_time=datetime.now(pytz.UTC),
                entry_prices=entry_prices,
                lot_size=strategy_preset.get('lot_size'),
                positions=[],  # Will be populated later
                orders=order_ids
            )
            
            logger.info(
                f"[StrategyExecutor._record_trade] Trade recorded for user {user_id}"
            )
            
        except Exception as e:
            logger.error(f"[StrategyExecutor._record_trade] Error recording trade: {e}")
            # Don't raise - recording failure shouldn't fail execution
    
    @log_function_call
    async def get_execution_preview(
        self,
        user_id: int,
        strategy_type: str,
        strategy_name: str
    ) -> Dict[str, Any]:
        """
        Get preview of strategy execution without actually executing.
        
        Args:
            user_id: User ID
            strategy_type: Strategy type
            strategy_name: Strategy name
        
        Returns:
            Preview information
        """
        try:
            # Get strategy preset
            strategy_enum = StrategyTypeEnum.STRADDLE if strategy_type.lower() == 'straddle' else StrategyTypeEnum.STRANGLE
            
            strategy_preset = await self.strategy_ops.get_strategy_by_name(
                user_id=user_id,
                strategy_name=strategy_name,
                strategy_type=strategy_enum
            )
            
            if not strategy_preset:
                raise ValidationError(f"Strategy '{strategy_name}' not found")
            
            # Parse expiry
            expiry_notation = strategy_preset.get('expiry')
            expiry_datetime = parse_expiry_notation(expiry_notation)
            
            if not expiry_datetime:
                raise ValidationError(f"Invalid expiry notation: {expiry_notation}")
            
            expiry_date = expiry_datetime.strftime('%Y-%m-%d')
            
            # Get preview
            if strategy_type.lower() == 'straddle':
                preview = await self.straddle.get_straddle_preview(
                    asset=strategy_preset.get('asset'),
                    expiry_date=expiry_date,
                    direction=strategy_preset.get('direction'),
                    lot_size=strategy_preset.get('lot_size'),
                    atm_offset=strategy_preset.get('atm_offset', 0)
                )
            else:  # strangle
                preview = await self.strangle.get_strangle_preview(
                    asset=strategy_preset.get('asset'),
                    expiry_date=expiry_date,
                    direction=strategy_preset.get('direction'),
                    lot_size=strategy_preset.get('lot_size'),
                    otm_percentage=strategy_preset.get('otm_percentage'),
                    otm_value=strategy_preset.get('otm_value')
                )
            
            # Add SL/TP info
            preview['stoploss_config'] = strategy_preset.get('stoploss_config')
            preview['target_config'] = strategy_preset.get('target_config')
            
            logger.info(
                f"[StrategyExecutor.get_execution_preview] Generated preview for "
                f"strategy '{strategy_name}'"
            )
            
            return preview
            
        except Exception as e:
            logger.error(f"[StrategyExecutor.get_execution_preview] Error: {e}")
            return {
                'error': str(e),
                'user_message': format_error_for_user(e)
            }
    
    @log_function_call
    async def validate_execution_requirements(
        self,
        user_id: int,
        api_name: str,
        strategy_type: str,
        strategy_name: str
    ) -> Dict[str, Any]:
        """
        Validate all requirements before execution.
        
        Args:
            user_id: User ID
            api_name: API name
            strategy_type: Strategy type
            strategy_name: Strategy name
        
        Returns:
            Validation result
        """
        try:
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check strategy exists
            strategy_enum = StrategyTypeEnum.STRADDLE if strategy_type.lower() == 'straddle' else StrategyTypeEnum.STRANGLE
            
            strategy_preset = await self.strategy_ops.get_strategy_by_name(
                user_id=user_id,
                strategy_name=strategy_name,
                strategy_type=strategy_enum
            )
            
            if not strategy_preset:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Strategy '{strategy_name}' not found")
                return validation_results
            
            # Validate expiry
            expiry_notation = strategy_preset.get('expiry')
            expiry_datetime = parse_expiry_notation(expiry_notation)
            
            if not expiry_datetime:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Invalid expiry notation: {expiry_notation}")
            elif expiry_datetime < datetime.now(pytz.UTC):
                validation_results['valid'] = False
                validation_results['errors'].append(f"Expiry has already passed")
            
            # Check if options are available
            if expiry_datetime:
                expiry_date = expiry_datetime.strftime('%Y-%m-%d')
                
                if strategy_type.lower() == 'straddle':
                    validation = await self.straddle.validate_straddle_params(
                        asset=strategy_preset.get('asset'),
                        expiry_date=expiry_date,
                        direction=strategy_preset.get('direction'),
                        lot_size=strategy_preset.get('lot_size'),
                        atm_offset=strategy_preset.get('atm_offset', 0)
                    )
                else:
                    validation = await self.strangle.validate_strangle_params(
                        asset=strategy_preset.get('asset'),
                        expiry_date=expiry_date,
                        direction=strategy_preset.get('direction'),
                        lot_size=strategy_preset.get('lot_size'),
                        otm_percentage=strategy_preset.get('otm_percentage'),
                        otm_value=strategy_preset.get('otm_value')
                    )
                
                if not validation.get('valid'):
                    validation_results['valid'] = False
                    validation_results['errors'].extend(validation.get('errors', []))
            
            logger.info(
                f"[StrategyExecutor.validate_execution_requirements] Validation result: "
                f"valid={validation_results['valid']}"
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"[StrategyExecutor.validate_execution_requirements] Error: {e}")
            return {
                'valid': False,
                'errors': [str(e)]
            }
    
    @log_function_call
    async def close_strategy_positions(
        self,
        user_id: int,
        product_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Close positions for a strategy.
        
        Args:
            user_id: User ID
            product_ids: List of product IDs to close
        
        Returns:
            Close result
        """
        try:
            from delta.orders import Orders, OrderSide
            
            orders = Orders(self.client)
            closed_positions = []
            
            # Get current positions
            positions = await self.positions.get_positions()
            
            for product_id in product_ids:
                # Find position
                position = next(
                    (p for p in positions if p.get('product_id') == product_id),
                    None
                )
                
                if not position:
                    logger.warning(
                        f"[StrategyExecutor.close_strategy_positions] No position found "
                        f"for product {product_id}"
                    )
                    continue
                
                size = abs(float(position.get('size', 0)))
                is_long = float(position.get('size', 0)) > 0
                
                # Place closing order
                close_side = OrderSide.SELL.value if is_long else OrderSide.BUY.value
                
                order = await orders.place_order(
                    product_id=product_id,
                    size=size,
                    side=close_side,
                    order_type='market_order',
                    reduce_only=True
                )
                
                if order:
                    closed_positions.append({
                        'product_id': product_id,
                        'order_id': order.get('id'),
                        'size': size,
                        'status': 'closed'
                    })
                    logger.info(
                        f"[StrategyExecutor.close_strategy_positions] Closed position "
                        f"for product {product_id}"
                    )
            
            return {
                'success': True,
                'closed_positions': closed_positions,
                'count': len(closed_positions)
            }
            
        except Exception as e:
            logger.error(f"[StrategyExecutor.close_strategy_positions] Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    import asyncio
    
    async def test_executor():
        """Test strategy executor."""
        print("Testing Strategy Executor...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        executor = StrategyExecutor(client)
        
        try:
            # Test validation
            validation = await executor.validate_execution_requirements(
                user_id=123456789,
                api_name="Test API",
                strategy_type="straddle",
                strategy_name="Test Strategy"
            )
            print(f"✅ Validation: {validation}")
            
            # Test preview
            preview = await executor.get_execution_preview(
                user_id=123456789,
                strategy_type="straddle",
                strategy_name="Test Strategy"
            )
            print(f"✅ Preview: {preview}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Executor test completed!")
    
    asyncio.run(test_executor())
