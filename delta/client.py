"""
Delta Exchange API client with async support.
"""

import time
import json
from typing import Dict, Any, Optional, List
import httpx

from config import settings
from .signature import generate_signature
from bot.utils.logger import setup_logger, log_api_call
from bot.utils.error_handler import (
    APIError,
    APINetworkError,
    APITimeoutError,
    APIAuthenticationError,
    APIRateLimitError,
    handle_api_response
)

logger = setup_logger(__name__)


class DeltaClient:
    """
    Async client for Delta Exchange India API.
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: Optional[str] = None
    ):
        """
        Initialize Delta Exchange client.
        
        Args:
            api_key: API key
            api_secret: API secret
            base_url: Base URL for API (defaults to India API)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url or settings.DELTA_BASE_URL
        
        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        logger.info(f"Initialized DeltaClient with base URL: {self.base_url}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.debug("DeltaClient closed")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in milliseconds."""
        return str(int(time.time() * 1000))
    
    def _generate_headers(
        self,
        method: str,
        path: str,
        query_string: str = "",
        payload: str = ""
    ) -> Dict[str, str]:
        """
        Generate request headers with signature.
        
        Args:
            method: HTTP method
            path: API endpoint path
            query_string: URL query string
            payload: Request body
        
        Returns:
            Dictionary of headers
        """
        timestamp = self._get_timestamp()
        
        # Generate signature
        signature = generate_signature(
            self.api_secret,
            method,
            timestamp,
            path,
            query_string,
            payload
        )
        
        headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramTradingBot/1.0'
        }
        
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        authenticated: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Delta Exchange API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: URL query parameters
            data: Request body data
            authenticated: Whether to include authentication
        
        Returns:
            Response data dictionary
        
        Raises:
            APIError: If API returns an error
            APINetworkError: If network error occurs
            APITimeoutError: If request times out
        """
        # Build query string
        query_string = ""
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
        
        # Build payload
        payload = ""
        if data:
            payload = json.dumps(data)
        
        # Generate headers
        if authenticated:
            headers = self._generate_headers(method, endpoint, query_string, payload)
        else:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'TelegramTradingBot/1.0'
            }
        
        # Build full URL
        url = endpoint
        if query_string:
            url += f"?{query_string}"
        
        try:
            # Make request with retry logic
            for attempt in range(settings.MAX_RETRIES):
                try:
                    response = await self.client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        content=payload if payload else None
                    )
                    
                    # Log API call
                    log_api_call(
                        api_id=self.api_key[:8] + "...",
                        endpoint=endpoint,
                        method=method,
                        status_code=response.status_code
                    )
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', settings.RETRY_DELAY))
                        logger.warning(f"Rate limited. Retry after {retry_after}s")
                        
                        if attempt < settings.MAX_RETRIES - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise APIRateLimitError("Rate limit exceeded")
                    
                    # Handle authentication errors
                    if response.status_code == 401:
                        raise APIAuthenticationError("Authentication failed. Check API credentials.")
                    
                    # Parse response
                    response_data = response.json()
                    
                    # Handle API errors
                    if response.status_code >= 400:
                        error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                        log_api_call(
                            api_id=self.api_key[:8] + "...",
                            endpoint=endpoint,
                            method=method,
                            status_code=response.status_code,
                            error=error_msg
                        )
                        raise APIError(f"API error ({response.status_code}): {error_msg}")
                    
                    return response_data
                
                except httpx.TimeoutException:
                    logger.warning(f"Request timeout (attempt {attempt + 1}/{settings.MAX_RETRIES})")
                    if attempt < settings.MAX_RETRIES - 1:
                        await asyncio.sleep(settings.RETRY_DELAY)
                        continue
                    else:
                        raise APITimeoutError("Request timed out")
                
                except httpx.NetworkError as e:
                    logger.warning(f"Network error (attempt {attempt + 1}/{settings.MAX_RETRIES}): {e}")
                    if attempt < settings.MAX_RETRIES - 1:
                        await asyncio.sleep(settings.RETRY_DELAY)
                        continue
                    else:
                        raise APINetworkError(f"Network error: {str(e)}")
        
        except (APIError, APINetworkError, APITimeoutError, APIAuthenticationError, APIRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}", exc_info=True)
            raise APIError(f"Unexpected error: {str(e)}")
    
    # ==================== Wallet / Balance Endpoints ====================
    
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance.
        
        Returns:
            Balance data dictionary
        """
        return await self._request('GET', '/v2/wallet/balances')
    
    async def get_wallet_transactions(
        self,
        asset_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get wallet transaction history.
        
        Args:
            asset_id: Filter by asset ID
            start_time: Start timestamp
            end_time: End timestamp
        
        Returns:
            Transaction data
        """
        params = {}
        if asset_id:
            params['asset_id'] = asset_id
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        
        return await self._request('GET', '/v2/wallet/transactions', params=params)
    
    # ==================== Product Endpoints ====================
    
    async def get_products(self, contract_types: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all products.
        
        Args:
            contract_types: Filter by contract types (e.g., 'call_options,put_options')
        
        Returns:
            Products data
        """
        params = {}
        if contract_types:
            params['contract_types'] = contract_types
        
        return await self._request('GET', '/v2/products', params=params, authenticated=False)
    
    async def get_product(self, symbol: str) -> Dict[str, Any]:
        """
        Get specific product by symbol.
        
        Args:
            symbol: Product symbol
        
        Returns:
            Product data
        """
        return await self._request('GET', f'/v2/products/{symbol}', authenticated=False)
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker data for a symbol.
        
        Args:
            symbol: Product symbol
        
        Returns:
            Ticker data
        """
        return await self._request('GET', f'/v2/tickers/{symbol}', authenticated=False)
    
    async def get_tickers(self) -> Dict[str, Any]:
        """
        Get all tickers.
        
        Returns:
            All tickers data
        """
        return await self._request('GET', '/v2/tickers', authenticated=False)
    
    async def get_l2_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """
        Get L2 orderbook for a symbol.
        
        Args:
            symbol: Product symbol
            depth: Orderbook depth
        
        Returns:
            Orderbook data
        """
        params = {'depth': depth}
        return await self._request('GET', f'/v2/l2orderbook/{symbol}', params=params, authenticated=False)
    
    # ==================== Order Endpoints ====================
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            order_data: Order parameters
        
        Returns:
            Order response data
        """
        return await self._request('POST', '/v2/orders', data=order_data)
    
    async def place_batch_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Place multiple orders in a batch.
        
        Args:
            orders: List of order parameters
        
        Returns:
            Batch order response
        """
        return await self._request('POST', '/v2/orders/batch', data={'orders': orders})
    
    async def place_bracket_order(self, bracket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a bracket order (with stop loss and/or take profit).
        
        Args:
            bracket_data: Bracket order parameters
        
        Returns:
            Bracket order response
        """
        return await self._request('POST', '/v2/orders/bracket', data=bracket_data)
    
    async def get_open_orders(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all open orders.
        
        Args:
            product_id: Filter by product ID
        
        Returns:
            Open orders data
        """
        params = {}
        if product_id:
            params['product_id'] = product_id
        
        return await self._request('GET', '/v2/orders', params=params)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get specific order by ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order data
        """
        return await self._request('GET', f'/v2/orders/{order_id}')
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
        
        Returns:
            Cancellation response
        """
        return await self._request('DELETE', f'/v2/orders/{order_id}')
    
    async def cancel_all_orders(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Cancel all open orders.
        
        Args:
            product_id: Cancel orders for specific product
        
        Returns:
            Cancellation response
        """
        params = {}
        if product_id:
            params['product_id'] = product_id
        
        return await self._request('DELETE', '/v2/orders/all', params=params)
    
    async def edit_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit an existing order.
        
        Args:
            order_id: Order ID
            order_data: Updated order parameters
        
        Returns:
            Updated order data
        """
        return await self._request('PUT', f'/v2/orders/{order_id}', data=order_data)
    
    # ==================== Position Endpoints ====================
    
    async def get_positions(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all positions.
        
        Args:
            product_id: Filter by product ID
        
        Returns:
            Positions data
        """
        params = {}
        if product_id:
            params['product_id'] = product_id
        
        return await self._request('GET', '/v2/positions', params=params)
    
    async def get_position(self, product_id: int) -> Dict[str, Any]:
        """
        Get position for specific product.
        
        Args:
            product_id: Product ID
        
        Returns:
            Position data
        """
        return await self._request('GET', f'/v2/positions/{product_id}')
    
    async def change_position_margin(
        self,
        product_id: int,
        delta_margin: float
    ) -> Dict[str, Any]:
        """
        Change margin for a position.
        
        Args:
            product_id: Product ID
            delta_margin: Margin change amount
        
        Returns:
            Updated position data
        """
        data = {'delta_margin': delta_margin}
        return await self._request('POST', f'/v2/positions/change_margin', data=data)
    
    # ==================== Market Data Endpoints ====================
    
    async def get_ohlc(
        self,
        symbol: str,
        resolution: str,
        start: int,
        end: int
    ) -> Dict[str, Any]:
        """
        Get OHLC candle data.
        
        Args:
            symbol: Product symbol
            resolution: Candle resolution (1m, 5m, 15m, 1h, etc.)
            start: Start timestamp
            end: End timestamp
        
        Returns:
            OHLC data
        """
        params = {
            'resolution': resolution,
            'start': start,
            'end': end
        }
        return await self._request('GET', f'/v2/chart/history', params=params, authenticated=False)
    
    async def get_mark_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current mark price for symbol.
        
        Args:
            symbol: Product symbol
        
        Returns:
            Mark price data
        """
        ticker = await self.get_ticker(symbol)
        return {
            'success': True,
            'result': {
                'symbol': symbol,
                'mark_price': ticker.get('result', {}).get('mark_price', 0)
            }
        }
    
    async def get_index_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current index price.
        
        Args:
            symbol: Index symbol (e.g., '.DEXBTINDEX')
        
        Returns:
            Index price data
        """
        return await self._request('GET', f'/v2/indices/{symbol}', authenticated=False)
    
    async def get_spot_price(self, asset: str = "BTC") -> float:
        """
        Get spot price for asset.
        
        Args:
            asset: Asset symbol (BTC or ETH)
        
        Returns:
            Spot price as float
        """
        # Get index price
        index_symbol = f".DEX{asset}INDEX"
        response = await self.get_index_price(index_symbol)
        
        if response.get('success'):
            return float(response.get('result', {}).get('price', 0))
        
        return 0.0
    
    # ==================== Order History Endpoints ====================
    
    async def get_order_history(
        self,
        product_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get order history.
        
        Args:
            product_id: Filter by product ID
            start_time: Start timestamp
            end_time: End timestamp
            page_size: Number of records per page
        
        Returns:
            Order history data
        """
        params = {'page_size': page_size}
        if product_id:
            params['product_id'] = product_id
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        
        return await self._request('GET', '/v2/orders/history', params=params)
    
    async def get_fills(
        self,
        product_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get fill history (executed trades).
        
        Args:
            product_id: Filter by product ID
            start_time: Start timestamp
            end_time: End timestamp
        
        Returns:
            Fill history data
        """
        params = {}
        if product_id:
            params['product_id'] = product_id
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        
        return await self._request('GET', '/v2/fills', params=params)


# Import asyncio for sleep
import asyncio


if __name__ == "__main__":
    # Test client
    async def test():
        # Note: Use real credentials for testing
        client = DeltaClient("test_api_key", "test_api_secret")
        
        try:
            # Test unauthenticated endpoint
            products = await client.get_products()
            print(f"Products response: {products.get('success')}")
            
            # Test spot price
            btc_price = await client.get_spot_price("BTC")
            print(f"BTC Spot Price: ${btc_price}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await client.close()
    
    asyncio.run(test())
      
