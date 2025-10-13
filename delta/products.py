"""
Delta Exchange products operations.
Handles fetching and filtering products, options chains, and expiries.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz

from delta.client import DeltaClient, DeltaAPIError
from logger import logger, log_function_call


class Products:
    """Products operations for Delta Exchange."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize products handler.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        self._products_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache
        logger.debug("[Products.__init__] Initialized products handler")
    
    @log_function_call
    async def get_all_products(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all available products with caching.
        
        Args:
            force_refresh: Force refresh cache
        
        Returns:
            List of product dictionaries
        """
        try:
            # Check cache
            now = datetime.now(pytz.UTC)
            if (not force_refresh and 
                self._products_cache and 
                self._cache_timestamp and
                (now - self._cache_timestamp).total_seconds() < self._cache_ttl):
                logger.debug("[Products.get_all_products] Returning cached products")
                return self._products_cache
            
            # Fetch from API
            response = await self.client.get("/v2/products")
            products = response.get('result', [])
            
            # Update cache
            self._products_cache = products
            self._cache_timestamp = now
            
            logger.info(f"[Products.get_all_products] Retrieved {len(products)} products")
            return products
            
        except DeltaAPIError as e:
            logger.error(f"[Products.get_all_products] Error fetching products: {e.message}")
            return []
    
    @log_function_call
    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific product by ID.
        
        Args:
            product_id: Product ID
        
        Returns:
            Product dictionary or None
        """
        try:
            products = await self.get_all_products()
            product = next((p for p in products if p.get('id') == product_id), None)
            
            if product:
                logger.info(f"[Products.get_product_by_id] Found product {product_id}")
            else:
                logger.warning(f"[Products.get_product_by_id] Product {product_id} not found")
            
            return product
            
        except Exception as e:
            logger.error(f"[Products.get_product_by_id] Error: {e}")
            return None
    
    @log_function_call
    async def get_product_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get specific product by symbol.
        
        Args:
            symbol: Product symbol
        
        Returns:
            Product dictionary or None
        """
        try:
            products = await self.get_all_products()
            product = next((p for p in products if p.get('symbol') == symbol), None)
            
            if product:
                logger.info(f"[Products.get_product_by_symbol] Found product {symbol}")
            else:
                logger.warning(f"[Products.get_product_by_symbol] Product {symbol} not found")
            
            return product
            
        except Exception as e:
            logger.error(f"[Products.get_product_by_symbol] Error: {e}")
            return None
    
    @log_function_call
    async def filter_options(
        self,
        asset: str,
        expiry: Optional[str] = None,
        option_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter options by asset, expiry, and type.
        
        Args:
            asset: Underlying asset (BTC, ETH)
            expiry: Expiry date string (optional)
            option_type: Option type ('call_options' or 'put_options')
        
        Returns:
            List of filtered option products
        """
        try:
            products = await self.get_all_products()
            
            # Filter by product type
            options = [p for p in products if p.get('product_type') in ['call_options', 'put_options']]
            
            # Filter by asset
            if asset:
                options = [p for p in options if asset.upper() in p.get('symbol', '').upper()]
            
            # Filter by expiry
            if expiry:
                options = [p for p in options if p.get('settlement_time', '').startswith(expiry)]
            
            # Filter by option type
            if option_type:
                options = [p for p in options if p.get('product_type') == option_type]
            
            logger.info(
                f"[Products.filter_options] Filtered {len(options)} options "
                f"(asset: {asset}, expiry: {expiry}, type: {option_type})"
            )
            
            return options
            
        except Exception as e:
            logger.error(f"[Products.filter_options] Error filtering options: {e}")
            return []
    
    @log_function_call
    async def get_available_expiries(self, asset: str) -> List[str]:
        """
        Get all available expiry dates for an asset.
        
        Args:
            asset: Underlying asset (BTC, ETH)
        
        Returns:
            List of expiry date strings sorted ascending
        """
        try:
            options = await self.filter_options(asset)
            
            # Extract unique expiries
            expiries = set()
            for option in options:
                settlement_time = option.get('settlement_time')
                if settlement_time:
                    # Extract date part (YYYY-MM-DD)
                    expiry_date = settlement_time.split('T')[0]
                    expiries.add(expiry_date)
            
            # Sort expiries
            sorted_expiries = sorted(list(expiries))
            
            logger.info(
                f"[Products.get_available_expiries] Found {len(sorted_expiries)} "
                f"expiries for {asset}"
            )
            
            return sorted_expiries
            
        except Exception as e:
            logger.error(f"[Products.get_available_expiries] Error: {e}")
            return []
    
    @log_function_call
    async def get_options_chain(
        self,
        asset: str,
        expiry: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get complete options chain for asset and expiry.
        
        Args:
            asset: Underlying asset (BTC, ETH)
            expiry: Expiry date string
        
        Returns:
            Dictionary with 'calls' and 'puts' lists
        """
        try:
            # Get all options for expiry
            options = await self.filter_options(asset, expiry)
            
            # Separate calls and puts
            calls = [o for o in options if o.get('product_type') == 'call_options']
            puts = [o for o in options if o.get('product_type') == 'put_options']
            
            # Sort by strike price
            calls.sort(key=lambda x: float(x.get('strike_price', 0)))
            puts.sort(key=lambda x: float(x.get('strike_price', 0)))
            
            logger.info(
                f"[Products.get_options_chain] Retrieved options chain for {asset} {expiry}: "
                f"{len(calls)} calls, {len(puts)} puts"
            )
            
            return {
                'calls': calls,
                'puts': puts,
                'expiry': expiry,
                'asset': asset
            }
            
        except Exception as e:
            logger.error(f"[Products.get_options_chain] Error: {e}")
            return {'calls': [], 'puts': []}
    
    @log_function_call
    async def find_option_by_strike(
        self,
        asset: str,
        expiry: str,
        strike: float,
        option_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find specific option by strike price and type.
        
        Args:
            asset: Underlying asset (BTC, ETH)
            expiry: Expiry date string
            strike: Strike price
            option_type: 'call_options' or 'put_options'
        
        Returns:
            Option product dictionary or None
        """
        try:
            options = await self.filter_options(asset, expiry, option_type)
            
            option = next(
                (o for o in options if float(o.get('strike_price', 0)) == strike),
                None
            )
            
            if option:
                logger.info(
                    f"[Products.find_option_by_strike] Found {asset} {strike} "
                    f"{option_type} for {expiry}"
                )
            else:
                logger.warning(
                    f"[Products.find_option_by_strike] Option not found: "
                    f"{asset} {strike} {option_type} {expiry}"
                )
            
            return option
            
        except Exception as e:
            logger.error(f"[Products.find_option_by_strike] Error: {e}")
            return None


if __name__ == "__main__":
    import asyncio
    
    async def test_products():
        """Test products operations."""
        print("Testing Delta Exchange Products...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        products = Products(client)
        
        try:
            # Test get all products
            all_products = await products.get_all_products()
            print(f"✅ Total products: {len(all_products)}")
            
            # Test filter options
            btc_options = await products.filter_options("BTC")
            print(f"✅ BTC options: {len(btc_options)}")
            
            # Test available expiries
            expiries = await products.get_available_expiries("BTC")
            print(f"✅ BTC expiries: {len(expiries)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Products test completed!")
    
    asyncio.run(test_products())
          
