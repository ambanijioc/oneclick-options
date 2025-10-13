"""
Delta Exchange orders operations.
Handles order placement, modification, cancellation, and order history.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from delta.client import DeltaClient, DeltaAPIError
from logger import logger, log_function_call


class OrderType(str, Enum):
    """Order types supported by Delta Exchange."""
    MARKET = "market_order"
    LIMIT = "limit_order"
    STOP_MARKET = "stop_market_order"
    STOP_LIMIT = "stop_limit_order"


class OrderSide(str, Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


class TimeInForce(str, Enum):
    """Time in force options."""
    GTC = "gtc"  # Good till cancelled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill


class Orders:
    """Orders operations for Delta Exchange."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize orders handler.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        logger.debug("[Orders.__init__] Initialized orders handler")
    
    @log_function_call
    async def place_order(
        self,
        product_id: int,
        size: float,
        side: str,
        order_type: str = OrderType.MARKET.value,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = TimeInForce.GTC.value,
        post_only: bool = False,
        reduce_only: bool = False,
        bracket_stop_loss_limit_price: Optional[float] = None,
        bracket_stop_loss_price: Optional[float] = None,
        bracket_take_profit_limit_price: Optional[float] = None,
        bracket_take_profit_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a new order.
        
        Args:
            product_id: Product ID to trade
            size: Order size (quantity)
            side: Order side ('buy' or 'sell')
            order_type: Order type (market, limit, stop_market, stop_limit)
            limit_price: Limit price (required for limit orders)
            stop_price: Stop trigger price (required for stop orders)
            time_in_force: Time in force (gtc, ioc, fok)
            post_only: Post only flag
            reduce_only: Reduce only flag
            bracket_stop_loss_limit_price: Bracket order SL limit price
            bracket_stop_loss_price: Bracket order SL trigger price
            bracket_take_profit_limit_price: Bracket order TP limit price
            bracket_take_profit_price: Bracket order TP trigger price
        
        Returns:
            Order response dictionary or None
        """
        try:
            order_data = {
                "product_id": product_id,
                "size": size,
                "side": side,
                "order_type": order_type,
                "time_in_force": time_in_force
            }
            
            # Add optional parameters
            if limit_price is not None:
                order_data["limit_price"] = str(limit_price)
            
            if stop_price is not None:
                order_data["stop_price"] = str(stop_price)
            
            if post_only:
                order_data["post_only"] = True
            
            if reduce_only:
                order_data["reduce_only"] = True
            
            # Bracket order parameters
            if bracket_stop_loss_price is not None:
                order_data["bracket_stop_loss_price"] = str(bracket_stop_loss_price)
            
            if bracket_stop_loss_limit_price is not None:
                order_data["bracket_stop_loss_limit_price"] = str(bracket_stop_loss_limit_price)
            
            if bracket_take_profit_price is not None:
                order_data["bracket_take_profit_price"] = str(bracket_take_profit_price)
            
            if bracket_take_profit_limit_price is not None:
                order_data["bracket_take_profit_limit_price"] = str(bracket_take_profit_limit_price)
            
            # Place order
            response = await self.client.post("/v2/orders", data=order_data)
            
            order = response.get('result')
            if order:
                logger.info(
                    f"[Orders.place_order] Order placed successfully: "
                    f"ID={order.get('id')}, Product={product_id}, "
                    f"Side={side}, Size={size}, Type={order_type}"
                )
            
            return order
            
        except DeltaAPIError as e:
            logger.error(
                f"[Orders.place_order] Error placing order: {e.message} "
                f"(Product: {product_id}, Side: {side}, Size: {size})"
            )
            return None
    
    @log_function_call
    async def place_bracket_order(
        self,
        product_id: int,
        size: float,
        side: str,
        sl_trigger_price: float,
        sl_limit_price: Optional[float] = None,
        tp_trigger_price: Optional[float] = None,
        tp_limit_price: Optional[float] = None,
        limit_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place bracket order with stop loss and/or take profit.
        
        Args:
            product_id: Product ID
            size: Order size
            side: Order side ('buy' or 'sell')
            sl_trigger_price: Stop loss trigger price
            sl_limit_price: Stop loss limit price (optional)
            tp_trigger_price: Take profit trigger price (optional)
            tp_limit_price: Take profit limit price (optional)
            limit_price: Entry limit price (optional, market if not provided)
        
        Returns:
            Order response dictionary or None
        """
        try:
            order_type = OrderType.LIMIT.value if limit_price else OrderType.MARKET.value
            
            return await self.place_order(
                product_id=product_id,
                size=size,
                side=side,
                order_type=order_type,
                limit_price=limit_price,
                bracket_stop_loss_price=sl_trigger_price,
                bracket_stop_loss_limit_price=sl_limit_price,
                bracket_take_profit_price=tp_trigger_price,
                bracket_take_profit_limit_price=tp_limit_price
            )
            
        except Exception as e:
            logger.error(f"[Orders.place_bracket_order] Error: {e}")
            return None
    
    @log_function_call
    async def get_open_orders(
        self,
        product_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Args:
            product_id: Optional product ID filter
        
        Returns:
            List of open order dictionaries
        """
        try:
            params = {"state": "open"}
            if product_id:
                params["product_id"] = product_id
            
            response = await self.client.get("/v2/orders", params=params)
            orders = response.get('result', [])
            
            logger.info(f"[Orders.get_open_orders] Retrieved {len(orders)} open orders")
            
            return orders
            
        except DeltaAPIError as e:
            logger.error(f"[Orders.get_open_orders] Error fetching orders: {e.message}")
            return []
    
    @log_function_call
    async def get_order_history(
        self,
        product_id: Optional[int] = None,
        states: Optional[List[str]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get order history.
        
        Args:
            product_id: Optional product ID filter
            states: Optional order states filter (filled, cancelled, rejected)
            page_size: Number of orders to fetch
        
        Returns:
            List of order dictionaries
        """
        try:
            params = {"page_size": page_size}
            
            if product_id:
                params["product_id"] = product_id
            
            if states:
                params["state"] = ",".join(states)
            
            response = await self.client.get("/v2/orders/history", params=params)
            orders = response.get('result', [])
            
            logger.info(f"[Orders.get_order_history] Retrieved {len(orders)} historical orders")
            
            return orders
            
        except DeltaAPIError as e:
            logger.error(f"[Orders.get_order_history] Error fetching order history: {e.message}")
            return []
    
    @log_function_call
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a specific order.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            response = await self.client.delete(f"/v2/orders/{order_id}")
            
            result = response.get('result')
            if result:
                logger.info(f"[Orders.cancel_order] Order {order_id} cancelled successfully")
                return True
            
            return False
            
        except DeltaAPIError as e:
            logger.error(f"[Orders.cancel_order] Error cancelling order {order_id}: {e.message}")
            return False
    
    @log_function_call
    async def cancel_all_orders(
        self,
        product_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Cancel all open orders.
        
        Args:
            product_id: Optional product ID filter
        
        Returns:
            Cancellation result dictionary
        """
        try:
            data = {}
            if product_id:
                data["product_id"] = product_id
            
            response = await self.client.delete("/v2/orders/all", params=data)
            
            result = response.get('result', {})
            cancelled_count = len(result.get('cancelled', []))
            
            logger.info(
                f"[Orders.cancel_all_orders] Cancelled {cancelled_count} orders"
            )
            
            return result
            
        except DeltaAPIError as e:
            logger.error(f"[Orders.cancel_all_orders] Error: {e.message}")
            return {}
    
    @log_function_call
    async def edit_order(
        self,
        order_id: str,
        size: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Edit an existing order.
        
        Args:
            order_id: Order ID to edit
            size: New order size (optional)
            limit_price: New limit price (optional)
            stop_price: New stop price (optional)
        
        Returns:
            Updated order dictionary or None
        """
        try:
            data = {"id": order_id}
            
            if size is not None:
                data["size"] = size
            
            if limit_price is not None:
                data["limit_price"] = str(limit_price)
            
            if stop_price is not None:
                data["stop_price"] = str(stop_price)
            
            response = await self.client.put("/v2/orders", data=data)
            
            order = response.get('result')
            if order:
                logger.info(f"[Orders.edit_order] Order {order_id} edited successfully")
            
            return order
            
        except DeltaAPIError as e:
            logger.error(f"[Orders.edit_order] Error editing order {order_id}: {e.message}")
            return None
    
    @log_function_call
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific order by ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order dictionary or None
        """
        try:
            response = await self.client.get(f"/v2/orders/{order_id}")
            
            order = response.get('result')
            if order:
                logger.info(f"[Orders.get_order_by_id] Retrieved order {order_id}")
            
            return order
            
        except DeltaAPIError as e:
            logger.error(f"[Orders.get_order_by_id] Error fetching order {order_id}: {e.message}")
            return None


if __name__ == "__main__":
    import asyncio
    
    async def test_orders():
        """Test orders operations."""
        print("Testing Delta Exchange Orders...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        orders = Orders(client)
        
        try:
            # Test get open orders
            open_orders = await orders.get_open_orders()
            print(f"✅ Open orders: {len(open_orders)}")
            
            # Test get order history
            history = await orders.get_order_history(page_size=10)
            print(f"✅ Order history: {len(history)} orders")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Orders test completed!")
    
    asyncio.run(test_orders())
          
