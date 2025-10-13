"""
CRUD operations for trade history.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from database.connection import get_database
from database.models.trade_history import (
    TradeHistory,
    TradeHistoryCreate,
    OrderInfo
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_trade_history(data: TradeHistoryCreate) -> str:
    """
    Create new trade history entry.
    
    Args:
        data: Trade history creation data
    
    Returns:
        Created trade ID
    """
    try:
        db = get_database()
        
        # Create trade document
        trade = TradeHistory(
            user_id=data.user_id,
            api_id=data.api_id,
            strategy_type=data.strategy_type,
            strategy_preset_id=data.strategy_preset_id,
            asset=data.asset,
            expiry=data.expiry,
            entry_orders=data.entry_orders,
            entry_price=data.entry_price,
            lot_size=data.lot_size,
            commission=data.commission
        )
        
        # Insert to database
        result = await db.trade_history.insert_one(trade.to_dict())
        trade_id = str(result.inserted_id)
        
        logger.info(
            f"Created trade history: {trade_id} for user {data.user_id} "
            f"({data.strategy_type} {data.asset})"
        )
        
        return trade_id
    
    except Exception as e:
        logger.error(f"Failed to create trade history: {e}", exc_info=True)
        raise


async def get_trade_history(
    user_id: int,
    status: Optional[str] = None,
    limit: int = 100
) -> List[TradeHistory]:
    """
    Get trade history for a user.
    
    Args:
        user_id: User ID
        status: Filter by status (open/closed)
        limit: Maximum number of trades to return
    
    Returns:
        List of trade history entries
    """
    try:
        db = get_database()
        
        # Build query
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        # Fetch trades
        cursor = db.trade_history.find(query).sort("entry_time", -1).limit(limit)
        trades = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            trades.append(TradeHistory(**doc))
        
        logger.debug(f"Retrieved {len(trades)} trade(s) for user {user_id}")
        
        return trades
    
    except Exception as e:
        logger.error(f"Failed to get trade history: {e}", exc_info=True)
        raise


async def get_recent_trades(
    user_id: int,
    days: int = 3,
    api_id: Optional[str] = None
) -> List[TradeHistory]:
    """
    Get recent closed trades for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        api_id: Optional API ID filter
    
    Returns:
        List of recent trades
    """
    try:
        db = get_database()
        
        # Calculate date threshold
        threshold = datetime.now() - timedelta(days=days)
        
        # Build query
        query = {
            "user_id": user_id,
            "status": "closed",
            "exit_time": {"$gte": threshold}
        }
        
        if api_id:
            query["api_id"] = api_id
        
        # Fetch trades
        cursor = db.trade_history.find(query).sort("exit_time", -1)
        trades = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            trades.append(TradeHistory(**doc))
        
        logger.debug(
            f"Retrieved {len(trades)} recent trade(s) for user {user_id} "
            f"(last {days} days)"
        )
        
        return trades
    
    except Exception as e:
        logger.error(f"Failed to get recent trades: {e}", exc_info=True)
        raise


async def get_trade_by_id(trade_id: str) -> Optional[TradeHistory]:
    """
    Get trade by ID.
    
    Args:
        trade_id: Trade ID
    
    Returns:
        Trade history or None if not found
    """
    try:
        db = get_database()
        
        # Fetch trade
        doc = await db.trade_history.find_one({"_id": ObjectId(trade_id)})
        
        if not doc:
            logger.warning(f"Trade not found: {trade_id}")
            return None
        
        doc["_id"] = ObjectId(doc["_id"])
        trade = TradeHistory(**doc)
        
        logger.debug(f"Retrieved trade: {trade_id}")
        
        return trade
    
    except Exception as e:
        logger.error(f"Failed to get trade by ID: {e}", exc_info=True)
        raise


async def update_trade_history(
    trade_id: str,
    update_data: Dict[str, Any]
) -> bool:
    """
    Update trade history.
    
    Args:
        trade_id: Trade ID
        update_data: Data to update
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update document
        result = await db.trade_history.update_one(
            {"_id": ObjectId(trade_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated trade history: {trade_id}")
            return True
        else:
            logger.warning(f"No changes made to trade history: {trade_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to update trade history: {e}", exc_info=True)
        raise


async def close_trade(
    trade_id: str,
    exit_orders: List[OrderInfo],
    exit_price: float,
    exit_reason: str,
    realized_pnl: float,
    commission: float
) -> bool:
    """
    Close an open trade.
    
    Args:
        trade_id: Trade ID
        exit_orders: Exit order information
        exit_price: Average exit price
        exit_reason: Reason for exit (sl/target/manual)
        realized_pnl: Realized PnL
        commission: Total commission
    
    Returns:
        True if closed successfully, False otherwise
    """
    try:
        # Calculate net PnL
        net_pnl = realized_pnl - commission
        
        update_data = {
            "status": "closed",
            "exit_time": datetime.now(),
            "exit_orders": [order.model_dump() for order in exit_orders],
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "realized_pnl": realized_pnl,
            "commission": commission,
            "net_pnl": net_pnl,
            "updated_at": datetime.now()
        }
        
        result = await update_trade_history(trade_id, update_data)
        
        if result:
            logger.info(
                f"Closed trade: {trade_id} - Reason: {exit_reason}, "
                f"Net PnL: {net_pnl:.2f}"
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to close trade: {e}", exc_info=True)
        raise


async def get_trades_summary(user_id: int, days: int = 3) -> Dict[str, Any]:
    """
    Get trades summary for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
    
    Returns:
        Summary dictionary with trade statistics
    """
    try:
        # Get recent trades
        trades = await get_recent_trades(user_id, days)
        
        # Calculate summary statistics
        total_trades = len(trades)
        total_pnl = sum(trade.realized_pnl or 0 for trade in trades)
        total_commission = sum(trade.commission for trade in trades)
        net_pnl = total_pnl - total_commission
        
        winning_trades = [t for t in trades if (t.realized_pnl or 0) > 0]
        losing_trades = [t for t in trades if (t.realized_pnl or 0) < 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        summary = {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "gross_pnl": round(total_pnl, 2),
            "total_commission": round(total_commission, 2),
            "net_pnl": round(net_pnl, 2),
            "avg_pnl_per_trade": round(net_pnl / total_trades, 2) if total_trades > 0 else 0
        }
        
        logger.debug(f"Generated trades summary for user {user_id}: {summary}")
        
        return summary
    
    except Exception as e:
        logger.error(f"Failed to get trades summary: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio
    
    async def test():
        from database.connection import connect_db, close_db
        
        await connect_db()
        
        # Test create trade
        trade_data = TradeHistoryCreate(
            user_id=12345,
            api_id="507f1f77bcf86cd799439011",
            strategy_type="straddle",
            asset="BTC",
            expiry="2025-10-20",
            entry_orders=[
                OrderInfo(
                    order_id="order_123",
                    symbol="BTCUSD-20OCT25-65000-C",
                    side="buy",
                    order_type="limit",
                    size=10,
                    price=1000.0,
                    status="filled",
                    filled_size=10,
                    avg_fill_price=1000.0
                )
            ],
            entry_price=2000.0,
            lot_size=10,
            commission=5.0
        )
        
        try:
            trade_id = await create_trade_history(trade_data)
            print(f"Created trade: {trade_id}")
            
            # Get trade
            trade = await get_trade_by_id(trade_id)
            print(f"Retrieved trade: {trade.strategy_type} {trade.asset}")
            
            # Get summary
            summary = await get_trades_summary(12345)
            print(f"Summary: {summary}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        await close_db()
    
    asyncio.run(test())
  
