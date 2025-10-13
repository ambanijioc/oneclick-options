"""
HMAC signature generation for Delta Exchange API authentication.
"""

import hmac
import hashlib
from typing import Optional

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_signature(
    secret: str,
    method: str,
    timestamp: str,
    path: str,
    query_string: str = "",
    payload: str = ""
) -> str:
    """
    Generate HMAC SHA256 signature for Delta Exchange API.
    
    Args:
        secret: API secret key
        method: HTTP method (GET, POST, etc.)
        timestamp: Unix timestamp in milliseconds as string
        path: API endpoint path
        query_string: URL query string (without leading ?)
        payload: Request body JSON string
    
    Returns:
        Hex digest signature
    """
    try:
        # Construct signature data
        # Format: METHOD + TIMESTAMP + PATH + QUERY_STRING + BODY
        signature_data = method + timestamp + path
        
        if query_string:
            signature_data += "?" + query_string
        
        if payload:
            signature_data += payload
        
        # Generate HMAC SHA256 signature
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Generated signature for {method} {path}")
        
        return signature
    
    except Exception as e:
        logger.error(f"Failed to generate signature: {e}", exc_info=True)
        raise


def verify_signature(
    secret: str,
    method: str,
    timestamp: str,
    path: str,
    signature: str,
    query_string: str = "",
    payload: str = ""
) -> bool:
    """
    Verify HMAC signature.
    
    Args:
        secret: API secret key
        method: HTTP method
        timestamp: Unix timestamp
        path: API endpoint path
        signature: Signature to verify
        query_string: URL query string
        payload: Request body
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = generate_signature(
            secret, method, timestamp, path, query_string, payload
        )
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            logger.warning(f"Signature verification failed for {method} {path}")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"Signature verification error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Test signature generation
    test_secret = "test_secret_key_12345"
    test_method = "GET"
    test_timestamp = "1697200000000"
    test_path = "/v2/wallet/balances"
    
    signature = generate_signature(
        test_secret,
        test_method,
        test_timestamp,
        test_path
    )
    
    print(f"Test Signature: {signature}")
    
    # Test verification
    is_valid = verify_signature(
        test_secret,
        test_method,
        test_timestamp,
        test_path,
        signature
    )
    
    print(f"Signature Valid: {is_valid}")
  
