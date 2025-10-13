"""
CRUD operations for trade history.
Handles storing and retrieving trade records with PnL calculations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from database.connection import get_database
from database.models import TradeHistory
from logger import logger, log_function_call


class TradeOperations:
    """Trade history database operations."""
    
    def __init__(self):
        """Initialize trade operations."""
        self.collection_name = "trade_history"
    
    @log_function_call
    async def store_trade(
        self,
        user_id: int,
        api_name: str,
        strategy_type: str,
        strategy_name: str,
        asset: str,
        direction: str,
        entry_time: datetime,
        entry_prices: Dict[str, float],
        lot_size: int,
        positions: List[Dict[str, Any]],
        orders: List[str],
        exit_time: Optional[datetime] = None,
        exit_prices: Optional[Dict[str, float]] = None,
        pnl: Optional[float] = None,
        commission: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Store trade record in database.
        
        Args:
            user_id: Telegram user ID
            api_name: API used for trade
            strategy_type: Type of strategy (straddle/strangle)
            strategy_name: Name of strategy used
            asset: Asset traded (BTC/ETH)
            direction: Trade direction (long/short)
            entry_time: Entry timestamp
            entry_prices: Entry prices for each leg
            lot_size: Lot size
            positions: Position details
            orders: List of order IDs
            exit_time: Exit timestamp (optional)
            exit_prices: Exit prices (optional)
            pnl: Realized PnL (optional)
            commission: Total commission (optional)
        
        Returns:
            Dictionary with success status and trade ID
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Create trade document
            trade = TradeHistory(
                user_id=user_id,
                api_name=api_name,
                strategy_type=strategy_type,
                strategy_name=strategy_name,
                asset=asset,
                direction=direction,
                entry_time=entry_time,
                entry_prices=entry_prices,
                lot_size=lot_size,
                positions=positions,
                orders=orders,
                exit_time=exit_time,
                exit_prices=exit_prices,
                pnl=pnl,
                commission=commission
            )
            
            # Insert into database
            result = await collection.insert_one(trade.model_dump())
            
            logger.info(
                f"[TradeOperations.store_trade] Trade stored for user {user_id}, "
                f"ID: {result.inserted_id}, Strategy: {strategy_name}"
            )
            
            return {
                "success": True,
                "trade_id": str(result.inserted_id)
            }
            
        except Exception as e:
            logger.error(f"[TradeOperations.store_trade] Error storing trade: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def update_trade_exit(
        self,
        trade_id: str,
        exit_time: datetime,
        exit_prices: Dict[str, float],
        pnl: float,
        commission: float
    ) -> Dict[str, Any]:
        """
        Update trade with exit information.
        
        Args:
            trade_id: Trade document ID
            exit_time: Exit timestamp
            exit_prices: Exit prices for each leg
            pnl: Realized PnL
            commission: Total commission
        
        Returns:
            Dictionary with success status
        """
        try:
            from bson import ObjectId
            
            db = await get_database()
            collection = db[self.collection_name]
            
            result = await collection.update_one(
                {"_id": ObjectId(trade_id)},
                {"$set": {
                    "exit_time": exit_time,
                    "exit_prices": exit_prices,
                    "pnl": pnl,
                    "commission": commission
                }}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[TradeOperations.update_trade_exit] Trade {trade_id} "
                    f"updated with exit info, PnL: {pnl}"
                )
                return {"success": True}
            else:
                logger.warning(
                    f"[TradeOperations.update_trade_exit] Trade {trade_id} not found"
                )
                return {"success": False, "error": "Trade not found"}
            
        except Exception as e:
            logger.error(f"[TradeOperations.update_trade_exit] Error updating trade: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def get_trade_history(
        self,
        user_id: int,
        api_name: Optional[str] = None,
        days: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get trade history for a user.
        
        Args:
            user_id: Telegram user ID
            api_name: Optional API name filter
            days: Number of days to look back
        
        Returns:
            List of trade documents
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Calculate date range
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=days)
            
            # Build query
            query = {
                "user_id": user_id,
                "entry_time": {"$gte": start_date, "$lte": end_date}
            }
            
            if api_name:
                query["api_name"] = api_name
            
            # Fetch trades
            cursor = collection.find(query).sort("entry_time", -1)
            
            trades = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                trades.append(doc)
            
            logger.info(
                f"[TradeOperations.get_trade_history] Retrieved {len(trades)} trades "
                f"for user {user_id} (last {days} days)"
            )
            
            return trades
            
        except Exception as e:
            logger.error(f"[TradeOperations.get_trade_history] Error retrieving trades: {e}")
            return []
    
    @log_function_call
    async def get_aggregated_pnl(
        self,
        user_id: int,
        days: int = 3
    ) -> Dict[str, Any]:
        """
        Calculate aggregated PnL statistics across all APIs.
        
        Args:
            user_id: Telegram user ID
            days: Number of days to look back
        
        Returns:
            Dictionary with aggregated statistics
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Calculate date range
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=days)
            
            # Aggregation pipeline
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "entry_time": {"$gte": start_date, "$lte": end_date},
                        "pnl": {"$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_trades": {"$sum": 1},
                        "total_pnl": {"$sum": "$pnl"},
                        "total_commission": {"$sum": "$commission"},
                        "winning_trades": {
                            "$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}
                        },
                        "losing_trades": {
                            "$sum": {"$cond": [{"$lt": ["$pnl", 0]}, 1, 0]}
                        },
                        "avg_pnl": {"$avg": "$pnl"}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                stats = result[0]
                stats.pop('_id', None)
                
                # Calculate net PnL
                stats['net_pnl'] = stats['total_pnl'] - stats.get('total_commission', 0)
                
                # Calculate win rate
                if stats['total_trades'] > 0:
                    stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                else:
                    stats['win_rate'] = 0
                
                logger.info(
                    f"[TradeOperations.get_aggregated_pnl] Calculated stats for user {user_id}: "
                    f"{stats['total_trades']} trades, Net PnL: {stats['net_pnl']}"
                )
                
                return stats
            else:
                logger.info(
                    f"[TradeOperations.get_aggregated_pnl] No trades found for user {user_id}"
                )
                return {
                    "total_trades": 0,
                    "total_pnl": 0.0,
                    "total_commission": 0.0,
                    "net_pnl": 0.0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "avg_pnl": 0.0,
                    "win_rate": 0.0
                }
            
        except Exception as e:
            logger.error(f"[TradeOperations.get_aggregated_pnl] Error calculating PnL: {e}")
            return {"error": str(e)}
    
    @log_function_call
    async def get_trades_by_api(
        self,
        user_id: int,
        days: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get trades grouped by API name.
        
        Args:
            user_id: Telegram user ID
            days: Number of days to look back
        
        Returns:
            Dictionary with API names as keys and trade lists as values
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            # Calculate date range
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=days)
            
            # Fetch all trades
            cursor = collection.find({
                "user_id": user_id,
                "entry_time": {"$gte": start_date, "$lte": end_date}
            }).sort("entry_time", -1)
            
            # Group by API
            trades_by_api = {}
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                api_name = doc.get('api_name', 'Unknown')
                
                if api_name not in trades_by_api:
                    trades_by_api[api_name] = []
                
                trades_by_api[api_name].append(doc)
            
            logger.info(
                f"[TradeOperations.get_trades_by_api] Retrieved trades for "
                f"{len(trades_by_api)} APIs for user {user_id}"
            )
            
            return trades_by_api
            
        except Exception as e:
            logger.error(f"[TradeOperations.get_trades_by_api] Error retrieving trades: {e}")
            return {}
    
    @log_function_call
    async def get_trade_count(
        self,
        user_id: int,
        api_name: Optional[str] = None,
        days: Optional[int] = None
    ) -> int:
        """
        Get count of trades for a user.
        
        Args:
            user_id: Telegram user ID
            api_name: Optional API name filter
            days: Optional number of days to look back
        
        Returns:
            Number of trades
        """
        try:
            db = await get_database()
            collection = db[self.collection_name]
            
            query = {"user_id": user_id}
            
            if api_name:
                query["api_name"] = api_name
            
            if days:
                end_date = datetime.now(pytz.UTC)
                start_date = end_date - timedelta(days=days)
                query["entry_time"] = {"$gte": start_date, "$lte": end_date}
            
            count = await collection.count_documents(query)
            
            return count
            
        except Exception as e:
            logger.error(f"[TradeOperations.get_trade_count] Error counting trades: {e}")
            return 0


if __name__ == "__main__":
    import asyncio
    
    async def test_trade_operations():
        """Test trade operations."""
        print("Testing Trade Operations...")
        
        trade_ops = TradeOperations()
        test_user_id = 123456789
        
        # Test store trade
        result = await trade_ops.store_trade(
            user_id=test_user_id,
            api_name="Test API",
            strategy_type="straddle",
            strategy_name="Test Strategy",
            asset="BTC",
            direction="long",
            entry_time=datetime.now(pytz.UTC),
            entry_prices={"95200_CE": 1200.0, "95200_PE": 1100.0},
            lot_size=1,
            positions=[],
            orders=["order_123", "order_456"],
            pnl=245.50,
            commission=12.50
        )
        print(f"✅ Store Trade: {result}")
        
        # Test get trade history
        trades = await trade_ops.get_trade_history(test_user_id, days=7)
        print(f"✅ Get Trade History: {len(trades)} trades found")
        
        # Test aggregated PnL
        stats = await trade_ops.get_aggregated_pnl(test_user_id, days=7)
        print(f"✅ Aggregated PnL: {stats}")
        
        # Test trades by API
        trades_by_api = await trade_ops.get_trades_by_api(test_user_id, days=7)
        print(f"✅ Trades by API: {len(trades_by_api)} APIs")
        
        # Test trade count
        count = await trade_ops.get_trade_count(test_user_id)
        print(f"✅ Trade Count: {count}")
        
        print("\n✅ Trade operations test completed!")
    
    asyncio.run(test_trade_operations())
      
