"""
Manual trade execution.
"""

from typing import Dict, Any
from datetime import datetime

from bot.utils.logger import setup_logger, log_trade_execution
from delta.client import DeltaClient
from delta.utils.expiry_parser import parse_expiry_code
from strategies.straddle import StraddleStrategy
from strategies.strangle import StrangleStrategy
from .stoploss_manager import place_stoploss_orders
from .target_manager import place_target_orders
from database.operations.trade_ops import create_trade_history
from database.operations.user_ops import increment_user_trade_count
from database.models.trade_history import TradeHistoryCreate, OrderInfo

logger = setup_logger(__name__)


async def execute_manual_strategy(
    api_key: str,
    api_secret: str,
    preset: Any,
    user_id: int,
    api_id: str
) -> Dict[str, Any]:
    """
    Execute a manual strategy trade.
    
    Args:
        api_key: Delta Exchange API key
        api_secret: Delta Exchange API secret
        preset: Strategy preset
        user_id: User ID
        api_id: API credential ID
    
    Returns:
        Dictionary with execution result
    """
    try:
        logger.info(f"Executing manual strategy: {preset.name} for user {user_id}")
        
        # Create Delta client
        client = DeltaClient(api_key, api_secret)
        
        try:
            # Step 1: Fetch spot price
            spot_price = await client.get_spot_price(preset.asset)
            
            if spot_price == 0:
                return {
                    'success': False,
                    'error': 'Failed to fetch spot price'
                }
            
            # Step 2: Create strategy instance
            if preset.strategy_type == "straddle":
                strategy = StraddleStrategy(preset.asset, preset.direction, preset.lot_size)
                params = {'atm_offset': preset.atm_offset}
            else:
                strategy = StrangleStrategy(preset.asset, preset.direction, preset.lot_size)
                params = {'otm_selection': preset.otm_selection}
            
            # Step 3: Calculate strikes
            strikes = await strategy.calculate_strikes(spot_price, params)
            
            # Step 4: Find products (option contracts)
            expiry_date = parse_expiry_code(preset.expiry_code)
            expiry_str = expiry_date.strftime('%d%b%y').upper()
            
            # Construct option symbols
            call_symbol = f"{preset.asset}USD-{expiry_str}-{strikes['call_strike']}-C"
            put_symbol = f"{preset.asset}USD-{expiry_str}-{strikes['put_strike']}-P"
            
            # Get product IDs
            call_product = await client.get_product(call_symbol)
            put_product = await client.get_product(put_symbol)
            
            if not call_product.get('success') or not put_product.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to find option products'
                }
            
            call_product_id = call_product['result']['id']
            put_product_id = put_product['result']['id']
            
            product_ids = {
                'call': call_product_id,
                'put': put_product_id
            }
            
            # Step 5: Generate orders
            orders = strategy.generate_order_list(strikes, product_ids)
            
            # Step 6: Get market prices for limit orders
            call_ticker = await client.get_ticker(call_symbol)
            put_ticker = await client.get_ticker(put_symbol)
            
            call_price = call_ticker['result'].get('mark_price', 0)
            put_price = put_ticker['result'].get('mark_price', 0)
            
            # Add limit prices to orders
            orders[0]['limit_price'] = str(call_price)
            orders[1]['limit_price'] = str(put_price)
            
            # Step 7: Place main orders
            placed_orders = []
            total_commission = 0
            
            for order_data in orders:
                response = await client.place_order(order_data)
                
                if response.get('success'):
                    order_result = response['result']
                    placed_orders.append(OrderInfo(
                        order_id=str(order_result['id']),
                        symbol=order_result['product']['symbol'],
                        side=order_result['side'],
                        order_type=order_result['order_type'],
                        size=order_result['size'],
                        price=order_result.get('limit_price'),
                        status=order_result['state'],
                        filled_size=order_result.get('filled_size', 0),
                        avg_fill_price=order_result.get('avg_fill_price')
                    ))
                    
                    # Accumulate commission
                    total_commission += float(order_result.get('commission', 0))
                else:
                    # Rollback: cancel already placed orders
                    for placed in placed_orders:
                        try:
                            await client.cancel_order(placed.order_id)
                        except Exception:
                            pass
                    
                    return {
                        'success': False,
                        'error': f"Failed to place order: {response.get('error')}"
                    }
            
            # Calculate average entry price
            entry_price = (call_price + put_price) / 2
            
            # Step 8: Place SL orders
            if preset.sl_trigger_pct > 0:
                sl_result = await place_stoploss_orders(
                    client=client,
                    positions=[{
                        'product_id': call_product_id,
                        'size': preset.lot_size if preset.direction == 'long' else -preset.lot_size,
                        'entry_price': call_price
                    }, {
                        'product_id': put_product_id,
                        'size': preset.lot_size if preset.direction == 'long' else -preset.lot_size,
                        'entry_price': put_price
                    }],
                    sl_trigger_pct=preset.sl_trigger_pct,
                    sl_limit_pct=preset.sl_limit_pct,
                    direction=preset.direction
                )
            
            # Step 9: Place target orders
            if preset.target_trigger_pct > 0:
                target_result = await place_target_orders(
                    client=client,
                    positions=[{
                        'product_id': call_product_id,
                        'size': preset.lot_size if preset.direction == 'long' else -preset.lot_size,
                        'entry_price': call_price
                    }, {
                        'product_id': put_product_id,
                        'size': preset.lot_size if preset.direction == 'long' else -preset.lot_size,
                        'entry_price': put_price
                    }],
                    target_trigger_pct=preset.target_trigger_pct,
                    target_limit_pct=preset.target_limit_pct,
                    direction=preset.direction
                )
            
            # Step 10: Store trade in database
            trade_data = TradeHistoryCreate(
                user_id=user_id,
                api_id=api_id,
                strategy_type=preset.strategy_type,
                strategy_preset_id=str(preset.id) if preset.id else None,
                asset=preset.asset,
                expiry=expiry_str,
                entry_orders=placed_orders,
                entry_price=entry_price,
                lot_size=preset.lot_size,
                commission=total_commission
            )
            
            trade_id = await create_trade_history(trade_data)
            
            # Step 11: Increment user trade count
            await increment_user_trade_count(user_id)
            
            # Log trade execution
            log_trade_execution(
                user_id=user_id,
                api_id=api_id,
                strategy_type=preset.strategy_type,
                asset=preset.asset,
                action='entry',
                details={
                    'trade_id': trade_id,
                    'call_strike': strikes['call_strike'],
                    'put_strike': strikes['put_strike'],
                    'entry_price': entry_price
                }
            )
            
            return {
                'success': True,
                'trade_id': trade_id,
                'message': (
                    f"Trade executed successfully!\n"
                    f"Call Strike: {strikes['call_strike']}\n"
                    f"Put Strike: {strikes['put_strike']}\n"
                    f"Entry Price: ${entry_price:.2f}\n"
                    f"Orders: {len(placed_orders)} placed"
                )
            }
        
        finally:
            await client.close()
    
    except Exception as e:
        logger.error(f"Failed to execute manual strategy: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    print("Manual executor module loaded")
          
