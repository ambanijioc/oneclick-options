"""
Delta Exchange API authentication module.
Handles signature generation and request signing per Delta Exchange India spec.
"""

import hmac
import hashlib
import time
from typing import Dict, Optional
from urllib.parse import urlencode

from logger import logger, log_function_call


class DeltaAuth:
    """Handles Delta Exchange API authentication."""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Delta authentication.
        
        Args:
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        logger.debug(f"[DeltaAuth.__init__] Initialized with API key: {api_key[:10]}...")
    
    @log_function_call
    def generate_signature(
        self,
        method: str,
        endpoint: str,
        timestamp: str,
        query_string: str = "",
        body: str = ""
    ) -> str:
        """
        Generate HMAC-SHA256 signature for API request.
        
        Signature format: HMAC-SHA256(method + endpoint + timestamp + query_string + body, secret)
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., /v2/orders)
            timestamp: Unix timestamp in seconds
            query_string: URL query string (without '?')
            body: Request body as JSON string
        
        Returns:
            Hex-encoded signature string
        """
        try:
            # Construct signature payload
            signature_data = method + endpoint + timestamp
            
            if query_string:
                signature_data += query_string
            
            if body:
                signature_data += body
            
            # Generate HMAC-SHA256 signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            logger.debug(
                f"[DeltaAuth.generate_signature] Generated signature for "
                f"{method} {endpoint}"
            )
            
            return signature
            
        except Exception as e:
            logger.error(f"[DeltaAuth.generate_signature] Error generating signature: {e}")
            raise
    
    @log_function_call
    def get_headers(
        self,
        method: str,
        endpoint: str,
        query_params: Optional[Dict] = None,
        body: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate authenticated request headers.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            query_params: Optional query parameters dict
            body: Optional request body dict
        
        Returns:
            Dictionary of headers including signature
        """
        try:
            # Get current timestamp
            timestamp = str(int(time.time()))
            
            # Build query string
            query_string = ""
            if query_params:
                query_string = urlencode(sorted(query_params.items()))
            
            # Convert body to string
            body_string = ""
            if body:
                import json
                body_string = json.dumps(body, separators=(',', ':'))
            
            # Generate signature
            signature = self.generate_signature(
                method=method.upper(),
                endpoint=endpoint,
                timestamp=timestamp,
                query_string=query_string,
                body=body_string
            )
            
            # Build headers
            headers = {
                'api-key': self.api_key,
                'timestamp': timestamp,
                'signature': signature,
                'Content-Type': 'application/json',
                'User-Agent': 'DeltaExchangeTradingBot/1.0'
            }
            
            logger.debug(
                f"[DeltaAuth.get_headers] Generated headers for {method} {endpoint}"
            )
            
            return headers
            
        except Exception as e:
            logger.error(f"[DeltaAuth.get_headers] Error generating headers: {e}")
            raise
    
    @staticmethod
    def validate_credentials(api_key: str, api_secret: str) -> bool:
        """
        Validate API credentials format.
        
        Args:
            api_key: API key to validate
            api_secret: API secret to validate
        
        Returns:
            True if credentials appear valid
        """
        if not api_key or not api_secret:
            logger.warning("[DeltaAuth.validate_credentials] Empty credentials provided")
            return False
        
        if len(api_key) < 10 or len(api_secret) < 10:
            logger.warning("[DeltaAuth.validate_credentials] Credentials too short")
            return False
        
        return True


if __name__ == "__main__":
    # Test authentication
    print("Testing Delta Exchange Authentication...")
    
    # Test credentials (dummy)
    test_key = "test_api_key_12345"
    test_secret = "test_api_secret_67890"
    
    auth = DeltaAuth(test_key, test_secret)
    
    # Test signature generation
    signature = auth.generate_signature(
        method="GET",
        endpoint="/v2/orders",
        timestamp="1697184000",
        query_string="product_id=27",
        body=""
    )
    print(f"✅ Generated signature: {signature[:20]}...")
    
    # Test headers generation
    headers = auth.get_headers(
        method="GET",
        endpoint="/v2/orders",
        query_params={"product_id": 27}
    )
    print(f"✅ Generated headers: {list(headers.keys())}")
    
    # Test validation
    is_valid = DeltaAuth.validate_credentials(test_key, test_secret)
    print(f"✅ Credentials valid: {is_valid}")
    
    print("\n✅ Authentication test completed!")
  
