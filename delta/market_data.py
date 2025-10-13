"""
Delta Exchange market data operations.
Handles fetching spot prices, tickers, OHLC data, and live market feeds.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz

from delta.client import DeltaClient, DeltaAPIError
from logger import logger, log_function_call


class MarketData:
    """Market data operations for Delta Exchange."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize market data handler.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        logger.debug("[MarketData.__init__] Initialized market data handler")
    
    @log_function_call
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker data for a symbol.
        
        Args:
            symbol: Product symbol (e.g., 'BTCUSD', 'ETHUSD')
        
        Returns:
            Ticker data dictionary or None
        """
        try:
            response = await self.client.get(
                "/v2/tickers",
                params={"symbol": symbol}
            )
            
            result = response.get('result', [])
            if result:
                ticker = result[0]
                logger.info(
                    f"[MarketData.get_ticker] Retrieved ticker for {symbol}: "
                    f"Mark Price: {ticker.get('mark_price')}"
                )
                return ticker
            
            logger.warning(f"[MarketData.get_ticker] No ticker data found for {symbol}")
            return None
            
        except DeltaAPIError as e:
            logger.error(f"[MarketData.get_ticker] Error fetching ticker: {e.message}")
            return None
    
    @log_function_call
    async def get_spot_price(self, symbol: str) -> Optional[float]:
        """
        Get current spot price for a symbol.
        
        Args:
            symbol: Product symbol (e.g., 'BTCUSD', 'ETHUSD')
        
        Returns:
            Spot price as float or None
        """
        try:
            ticker = await self.get_ticker(symbol)
            if ticker:
                spot_price = float(ticker.get('spot_price', 0))
                logger.info(f"[MarketData.get_spot_price] {symbol} spot price: {spot_price}")
                return spot_price
            return None
            
        except Exception as e:
            logger.error(f"[MarketData.get_spot_price] Error fetching spot price: {e}")
            return None
    
    @log_function_call
    async def get_mark_price(self, product_id: int) -> Optional[float]:
        """
        Get mark price for a product.
        
        Args:
            product_id: Delta Exchange product ID
        
        Returns:
            Mark price as float or None
        """
        try:
            response = await self.client.get(
                "/v2/tickers",
                params={"product_id": product_id}
            )
            
            result = response.get('result', [])
            if result:
                mark_price = float(result[0].get('mark_price', 0))
                logger.info(
                    f"[MarketData.get_mark_price] Product {product_id} mark price: {mark_price}"
                )
                return mark_price
            
            return None
            
        except DeltaAPIError as e:
            logger.error(f"[MarketData.get_mark_price] Error fetching mark price: {e.message}")
            return None
    
    @log_function_call
    async def get_futures_price(self, product_id: int) -> Optional[float]:
        """
        Get futures mark price for a product.
        
        Args:
            product_id: Delta Exchange product ID
        
        Returns:
            Futures mark price as float or None
        """
        return await self.get_mark_price(product_id)
    
    @log_function_call
    async def get_ohlc_data(
        self,
        symbol: str,
        resolution: str,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get OHLC (candlestick) data for a symbol.
        
        Args:
            symbol: Product symbol
            resolution: Time resolution (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 1d, 1w)
            start: Start timestamp (Unix seconds)
            end: End timestamp (Unix seconds)
        
        Returns:
            List of OHLC data dictionaries
        """
        try:
            params = {
                "symbol": symbol,
                "resolution": resolution
            }
            
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            
            response = await self.client.get("/v2/history/candles", params=params)
            
            result = response.get('result', [])
            logger.info(
                f"[MarketData.get_ohlc_data] Retrieved {len(result)} candles "
                f"for {symbol} ({resolution})"
            )
            
            return result
            
        except DeltaAPIError as e:
            logger.error(f"[MarketData.get_ohlc_data] Error fetching OHLC data: {e.message}")
            return []
    
    @log_function_call
    async def get_orderbook(self, product_id: int, depth: int = 20) -> Optional[Dict[str, Any]]:
        """
        Get orderbook for a product.
        
        Args:
            product_id: Delta Exchange product ID
            depth: Orderbook depth (default 20)
        
        Returns:
            Orderbook data dictionary or None
        """
        try:
            response = await self.client.get(
                f"/v2/l2orderbook/{product_id}",
                params={"depth": depth}
            )
            
            orderbook = response.get('result', {})
            logger.info(
                f"[MarketData.get_orderbook] Retrieved orderbook for product {product_id}"
            )
            
            return orderbook
            
        except DeltaAPIError as e:
            logger.error(f"[MarketData.get_orderbook] Error fetching orderbook: {e.message}")
            return None
    
    @log_function_call
    async def get_trades(
        self,
        product_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades for a product.
        
        Args:
            product_id: Delta Exchange product ID
            limit: Number of trades to fetch (default 50)
        
        Returns:
            List of trade dictionaries
        """
        try:
            response = await self.client.get(
                "/v2/trades",
                params={
                    "product_id": product_id,
                    "limit": limit
                }
            )
            
            trades = response.get('result', [])
            logger.info(
                f"[MarketData.get_trades] Retrieved {len(trades)} trades "
                f"for product {product_id}"
            )
            
            return trades
            
        except DeltaAPIError as e:
            logger.error(f"[MarketData.get_trades] Error fetching trades: {e.message}")
            return []
    
    @log_function_call
    async def get_index_price(self, symbol: str) -> Optional[float]:
        """
        Get index price for a symbol.
        
        Args:
            symbol: Index symbol (e.g., '.DEXBTUSDT')
        
        Returns:
            Index price as float or None
        """
        try:
            ticker = await self.get_ticker(symbol)
            if ticker:
                index_price = float(ticker.get('index_price', 0))
                logger.info(f"[MarketData.get_index_price] {symbol} index price: {index_price}")
                return index_price
            return None
            
        except Exception as e:
            logger.error(f"[MarketData.get_index_price] Error fetching index price: {e}")
            return None


if __name__ == "__main__":
    import asyncio
    
    async def test_market_data():
        """Test market data operations."""
        print("Testing Delta Exchange Market Data...")
        
        # Note: Use real credentials for testing
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        market_data = MarketData(client)
        
        try:
            # Test spot price
            spot_price = await market_data.get_spot_price("BTCUSD")
            print(f"✅ BTC Spot Price: ${spot_price}" if spot_price else "⚠️ No spot price")
            
            # Test ticker
            ticker = await market_data.get_ticker("ETHUSD")
            print(f"✅ ETH Ticker: {ticker}" if ticker else "⚠️ No ticker data")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Market data test completed!")
    
    asyncio.run(test_market_data())
      
