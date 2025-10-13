"""
Delta Exchange positions operations.
Handles fetching and managing open positions.
"""

from typing import Dict, Any, List, Optional

from delta.client import DeltaClient, DeltaAPIError
from database.models import Position
from logger import logger, log_function_call


class Positions:
    """Positions operations for Delta Exchange."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize positions handler.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        logger.debug("[Positions.__init__] Initialized positions handler")
    
    @log_function_call
    async def get_positions(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions or specific product position.
        
        Args:
            product_id: Optional product ID filter
        
        Returns:
            List of position dictionaries
        """
        try:
            params = {}
            if product_id:
                params['product_id'] = product_id
            
            response = await self.client.get("/v2/positions", params=params)
            positions = response.get('result', [])
            
            # Filter out zero-size positions
            active_positions = [p for p in positions if float(p.get('size', 0)) != 0]
            
            logger.info(
                f"[Positions.get_positions] Retrieved {len(active_positions)} active positions"
            )
            
            return active_positions
            
        except DeltaAPIError as e:
            logger.error(f"[Positions.get_positions] Error fetching positions: {e.message}")
            return []
    
    @log_function_call
    async def get_position_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific position.
        
        Args:
            product_id: Product ID
        
        Returns:
            Position details dictionary or None
        """
        try:
            positions = await self.get_positions(product_id)
            
            if positions:
                position = positions[0]
                logger.info(
                    f"[Positions.get_position_details] Retrieved position for "
                    f"product {product_id}: Size={position.get('size')}"
                )
                return position
            else:
                logger.warning(
                    f"[Positions.get_position_details] No position found for "
                    f"product {product_id}"
                )
                return None
            
        except Exception as e:
            logger.error(f"[Positions.get_position_details] Error: {e}")
            return None
    
    @log_function_call
    async def calculate_unrealized_pnl(
        self,
        positions: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate total unrealized PnL across positions.
        
        Args:
            positions: List of position dictionaries
        
        Returns:
            Total unrealized PnL
        """
        try:
            total_pnl = 0.0
            
            for position in positions:
                unrealized_pnl = float(position.get('unrealized_pnl', 0))
                total_pnl += unrealized_pnl
            
            logger.info(
                f"[Positions.calculate_unrealized_pnl] Total unrealized PnL: {total_pnl}"
            )
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"[Positions.calculate_unrealized_pnl] Error: {e}")
            return 0.0
    
    @log_function_call
    async def get_position_margin(self, product_id: int) -> Optional[Dict[str, float]]:
        """
        Get margin information for a position.
        
        Args:
            product_id: Product ID
        
        Returns:
            Dictionary with margin details or None
        """
        try:
            position = await self.get_position_details(product_id)
            
            if position:
                margin_info = {
                    'margin': float(position.get('margin', 0)),
                    'maintenance_margin': float(position.get('maintenance_margin', 0)),
                    'liquidation_price': float(position.get('liquidation_price', 0))
                }
                
                logger.info(
                    f"[Positions.get_position_margin] Margin info for product {product_id}: "
                    f"{margin_info}"
                )
                
                return margin_info
            
            return None
            
        except Exception as e:
            logger.error(f"[Positions.get_position_margin] Error: {e}")
            return None
    
    @log_function_call
    async def parse_positions_to_models(
        self,
        positions: List[Dict[str, Any]]
    ) -> List[Position]:
        """
        Parse API positions to Pydantic Position models.
        
        Args:
            positions: List of position dictionaries from API
        
        Returns:
            List of Position models
        """
        try:
            parsed_positions = []
            
            for pos in positions:
                position_model = Position(
                    product_id=pos.get('product_id'),
                    product_symbol=pos.get('product_symbol', ''),
                    size=float(pos.get('size', 0)),
                    entry_price=float(pos.get('entry_price', 0)),
                    current_price=float(pos.get('mark_price', 0)),
                    unrealized_pnl=float(pos.get('unrealized_pnl', 0)),
                    margin=float(pos.get('margin', 0)),
                    liquidation_price=float(pos.get('liquidation_price', 0))
                )
                parsed_positions.append(position_model)
            
            logger.info(
                f"[Positions.parse_positions_to_models] Parsed {len(parsed_positions)} positions"
            )
            
            return parsed_positions
            
        except Exception as e:
            logger.error(f"[Positions.parse_positions_to_models] Error parsing positions: {e}")
            return []
    
    @log_function_call
    async def get_positions_by_asset(self, asset: str) -> List[Dict[str, Any]]:
        """
        Get positions filtered by underlying asset.
        
        Args:
            asset: Asset symbol (BTC, ETH)
        
        Returns:
            List of positions for the asset
        """
        try:
            all_positions = await self.get_positions()
            
            # Filter by asset in symbol
            asset_positions = [
                p for p in all_positions 
                if asset.upper() in p.get('product_symbol', '').upper()
            ]
            
            logger.info(
                f"[Positions.get_positions_by_asset] Found {len(asset_positions)} "
                f"positions for {asset}"
            )
            
            return asset_positions
            
        except Exception as e:
            logger.error(f"[Positions.get_positions_by_asset] Error: {e}")
            return []


if __name__ == "__main__":
    import asyncio
    
    async def test_positions():
        """Test positions operations."""
        print("Testing Delta Exchange Positions...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        positions = Positions(client)
        
        try:
            # Test get positions
            all_positions = await positions.get_positions()
            print(f"✅ Open positions: {len(all_positions)}")
            
            # Test calculate PnL
            if all_positions:
                total_pnl = await positions.calculate_unrealized_pnl(all_positions)
                print(f"✅ Total unrealized PnL: ${total_pnl}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Positions test completed!")
    
    asyncio.run(test_positions())
              
