"""
Delta Exchange balance and wallet operations.
Handles fetching account balance, margin information, and wallet details.
"""

from typing import Dict, Any, Optional

from delta.client import DeltaClient, DeltaAPIError
from logger import logger, log_function_call


class Balance:
    """Balance and wallet operations for Delta Exchange."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize balance handler.
        
        Args:
            client: DeltaClient instance
        """
        self.client = client
        logger.debug("[Balance.__init__] Initialized balance handler")
    
    @log_function_call
    async def get_wallet_balance(self) -> Optional[Dict[str, Any]]:
        """
        Get wallet balance information.
        
        Returns:
            Wallet balance dictionary or None
        """
        try:
            response = await self.client.get("/v2/wallet/balances")
            
            result = response.get('result', [])
            if result:
                # Delta returns list, get first wallet (usually USDT)
                wallet = result[0]
                
                logger.info(
                    f"[Balance.get_wallet_balance] Retrieved wallet balance: "
                    f"Asset={wallet.get('asset_symbol')}, "
                    f"Balance={wallet.get('balance')}"
                )
                
                return wallet
            
            logger.warning("[Balance.get_wallet_balance] No wallet data found")
            return None
            
        except DeltaAPIError as e:
            logger.error(f"[Balance.get_wallet_balance] Error fetching wallet: {e.message}")
            return None
    
    @log_function_call
    async def get_all_balances(self) -> list[Dict[str, Any]]:
        """
        Get all wallet balances.
        
        Returns:
            List of wallet balance dictionaries
        """
        try:
            response = await self.client.get("/v2/wallet/balances")
            
            balances = response.get('result', [])
            
            logger.info(
                f"[Balance.get_all_balances] Retrieved {len(balances)} wallet balances"
            )
            
            return balances
            
        except DeltaAPIError as e:
            logger.error(f"[Balance.get_all_balances] Error fetching balances: {e.message}")
            return []
    
    @log_function_call
    async def get_margin_info(self) -> Optional[Dict[str, Any]]:
        """
        Get margin and portfolio information.
        
        Returns:
            Dictionary with margin details or None
        """
        try:
            wallet = await self.get_wallet_balance()
            
            if wallet:
                margin_info = {
                    'balance': float(wallet.get('balance', 0)),
                    'available_balance': float(wallet.get('available_balance', 0)),
                    'position_margin': float(wallet.get('position_margin', 0)),
                    'order_margin': float(wallet.get('order_margin', 0)),
                    'commission': float(wallet.get('commission', 0)),
                    'unrealized_pnl': float(wallet.get('unrealized_pnl', 0)),
                    'asset_symbol': wallet.get('asset_symbol', 'USDT')
                }
                
                logger.info(
                    f"[Balance.get_margin_info] Margin info: "
                    f"Available={margin_info['available_balance']}, "
                    f"Used={margin_info['position_margin']}"
                )
                
                return margin_info
            
            return None
            
        except Exception as e:
            logger.error(f"[Balance.get_margin_info] Error calculating margin: {e}")
            return None
    
    @log_function_call
    async def get_available_margin(self) -> float:
        """
        Get available margin for trading.
        
        Returns:
            Available margin as float
        """
        try:
            wallet = await self.get_wallet_balance()
            
            if wallet:
                available_margin = float(wallet.get('available_balance', 0))
                logger.info(
                    f"[Balance.get_available_margin] Available margin: {available_margin}"
                )
                return available_margin
            
            return 0.0
            
        except Exception as e:
            logger.error(f"[Balance.get_available_margin] Error: {e}")
            return 0.0
    
    @log_function_call
    async def get_total_balance(self) -> float:
        """
        Get total wallet balance.
        
        Returns:
            Total balance as float
        """
        try:
            wallet = await self.get_wallet_balance()
            
            if wallet:
                total_balance = float(wallet.get('balance', 0))
                logger.info(f"[Balance.get_total_balance] Total balance: {total_balance}")
                return total_balance
            
            return 0.0
            
        except Exception as e:
            logger.error(f"[Balance.get_total_balance] Error: {e}")
            return 0.0
    
    @log_function_call
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            Dictionary with portfolio statistics
        """
        try:
            wallet = await self.get_wallet_balance()
            
            if not wallet:
                return {}
            
            summary = {
                'total_balance': float(wallet.get('balance', 0)),
                'available_balance': float(wallet.get('available_balance', 0)),
                'position_margin': float(wallet.get('position_margin', 0)),
                'order_margin': float(wallet.get('order_margin', 0)),
                'unrealized_pnl': float(wallet.get('unrealized_pnl', 0)),
                'commission': float(wallet.get('commission', 0)),
                'asset_symbol': wallet.get('asset_symbol', 'USDT'),
                'margin_utilization': 0.0
            }
            
            # Calculate margin utilization percentage
            if summary['total_balance'] > 0:
                used_margin = summary['position_margin'] + summary['order_margin']
                summary['margin_utilization'] = (used_margin / summary['total_balance']) * 100
            
            logger.info(
                f"[Balance.get_portfolio_summary] Portfolio summary: "
                f"Balance={summary['total_balance']}, "
                f"Available={summary['available_balance']}, "
                f"PnL={summary['unrealized_pnl']}"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"[Balance.get_portfolio_summary] Error: {e}")
            return {}
    
    @log_function_call
    async def check_sufficient_margin(self, required_margin: float) -> bool:
        """
        Check if sufficient margin is available for a trade.
        
        Args:
            required_margin: Required margin amount
        
        Returns:
            True if sufficient margin available, False otherwise
        """
        try:
            available = await self.get_available_margin()
            
            is_sufficient = available >= required_margin
            
            logger.info(
                f"[Balance.check_sufficient_margin] Required: {required_margin}, "
                f"Available: {available}, Sufficient: {is_sufficient}"
            )
            
            return is_sufficient
            
        except Exception as e:
            logger.error(f"[Balance.check_sufficient_margin] Error: {e}")
            return False


if __name__ == "__main__":
    import asyncio
    
    async def test_balance():
        """Test balance operations."""
        print("Testing Delta Exchange Balance...")
        
        from delta.client import DeltaClient
        
        test_key = "your_test_api_key"
        test_secret = "your_test_api_secret"
        
        client = DeltaClient(test_key, test_secret)
        balance = Balance(client)
        
        try:
            # Test wallet balance
            wallet = await balance.get_wallet_balance()
            print(f"✅ Wallet balance: {wallet}")
            
            # Test margin info
            margin_info = await balance.get_margin_info()
            print(f"✅ Margin info: {margin_info}")
            
            # Test portfolio summary
            summary = await balance.get_portfolio_summary()
            print(f"✅ Portfolio summary: {summary}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
        
        print("\n✅ Balance test completed!")
    
    asyncio.run(test_balance())
  
