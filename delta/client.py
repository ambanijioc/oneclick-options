"""
Base Delta Exchange API client.
Handles HTTP requests with authentication, retry logic, and error handling.
"""

import asyncio
from typing import Dict, Any, Optional
import httpx
from enum import Enum

from delta.auth import DeltaAuth
from config import config
from logger import logger, log_function_call


class HTTPMethod(str, Enum):
    """HTTP methods enumeration."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class DeltaAPIError(Exception):
    """Custom exception for Delta Exchange API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class DeltaClient:
    """Base client for Delta Exchange API requests."""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Delta Exchange client.
        
        Args:
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret
        """
        self.base_url = config.delta.base_url
        self.auth = DeltaAuth(api_key, api_secret)
        self.timeout = config.delta.timeout
        self.max_retries = config.delta.max_retries
        
        # Create async HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        logger.info(
            f"[DeltaClient.__init__] Initialized client with base URL: {self.base_url}"
        )
    
    @log_function_call
    async def _make_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        query_params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Delta Exchange API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            query_params: Optional query parameters
            body: Optional request body
            retry_count: Current retry attempt
        
        Returns:
            Response data as dictionary
        
        Raises:
            DeltaAPIError: If request fails after all retries
        """
        try:
            # Generate authenticated headers
            headers = self.auth.get_headers(
                method=method.value,
                endpoint=endpoint,
                query_params=query_params,
                body=body
            )
            
            # Build full URL
            url = f"{self.base_url}{endpoint}"
            
            # Make request
            logger.debug(
                f"[DeltaClient._make_request] {method.value} {endpoint} "
                f"(attempt {retry_count + 1}/{self.max_retries + 1})"
            )
            
            response = await self.client.request(
                method=method.value,
                url=url,
                params=query_params,
                json=body,
                headers=headers
            )
            
            # Log response
            logger.debug(
                f"[DeltaClient._make_request] Response status: {response.status_code}"
            )
            
            # Parse response
            response_data = response.json()
            
            # Check for errors
            if response.status_code >= 400:
                error_message = response_data.get('error', {}).get('message', 'Unknown error')
                logger.error(
                    f"[DeltaClient._make_request] API error: {error_message} "
                    f"(status: {response.status_code})"
                )
                
                # Retry on specific errors
                if response.status_code in [429, 500, 502, 503, 504] and retry_count < self.max_retries:
                    wait_time = (retry_count + 1) * 2  # Exponential backoff
                    logger.warning(
                        f"[DeltaClient._make_request] Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                    return await self._make_request(
                        method, endpoint, query_params, body, retry_count + 1
                    )
                
                raise DeltaAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    response_data=response_data
                )
            
            # Check for success
            if not response_data.get('success', False):
                error_message = response_data.get('error', {}).get('message', 'Request failed')
                logger.error(f"[DeltaClient._make_request] Request failed: {error_message}")
                raise DeltaAPIError(
                    message=error_message,
                    response_data=response_data
                )
            
            logger.info(
                f"[DeltaClient._make_request] Request successful: {method.value} {endpoint}"
            )
            
            return response_data
            
        except httpx.TimeoutException as e:
            logger.error(f"[DeltaClient._make_request] Request timeout: {e}")
            
            if retry_count < self.max_retries:
                wait_time = (retry_count + 1) * 2
                logger.warning(f"[DeltaClient._make_request] Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method, endpoint, query_params, body, retry_count + 1
                )
            
            raise DeltaAPIError(f"Request timeout after {self.max_retries} retries")
        
        except httpx.NetworkError as e:
            logger.error(f"[DeltaClient._make_request] Network error: {e}")
            
            if retry_count < self.max_retries:
                wait_time = (retry_count + 1) * 2
                logger.warning(f"[DeltaClient._make_request] Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method, endpoint, query_params, body, retry_count + 1
                )
            
            raise DeltaAPIError(f"Network error after {self.max_retries} retries")
        
        except Exception as e:
            logger.error(f"[DeltaClient._make_request] Unexpected error: {e}")
            raise DeltaAPIError(f"Unexpected error: {str(e)}")
    
    @log_function_call
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GET request.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
        
        Returns:
            Response data
        """
        return await self._make_request(HTTPMethod.GET, endpoint, query_params=params)
    
    @log_function_call
    async def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make POST request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
        
        Returns:
            Response data
        """
        return await self._make_request(HTTPMethod.POST, endpoint, body=data)
    
    @log_function_call
    async def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
        
        Returns:
            Response data
        """
        return await self._make_request(HTTPMethod.PUT, endpoint, body=data)
    
    @log_function_call
    async def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make DELETE request.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
        
        Returns:
            Response data
        """
        return await self._make_request(HTTPMethod.DELETE, endpoint, query_params=params)
    
    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
        logger.info("[DeltaClient.close] Client connection closed")


if __name__ == "__main__":
    import asyncio
    
    async def test_client():
        """Test Delta client."""
        print("Testing Delta Exchange Client...")
        
        # Note: Use real credentials to test actual API calls
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        
        try:
            # Test GET request (fetch products)
            response = await client.get("/v2/products")
            print(f"✅ GET request successful: {len(response.get('result', []))} products")
        except DeltaAPIError as e:
            print(f"⚠️ API Error (expected with test credentials): {e.message}")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Client test completed!")
    
    asyncio.run(test_client())
      
