"""
MOVE Trade Database Operations

Handle MOVE trade creation, updates, and retrievals.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_move_trade(
    db: AsyncIOMotorDatabase,
    user_id: int,
    trade_data: dict
) -> str:
    """Create a new MOVE trade"""
    try:
        trade_doc = {
            'user_id': user_id,
            'trade_type': 'MOVE',
            'entry_price': trade_data.get('entry_price'),
            'lot_size': trade_data.get('lot_size'),
            'sl_price': trade_data.get('sl_price'),
            'target_price': trade_data.get('target_price'),
            'direction': trade_data.get('direction'),  # BUY/SELL
            'status': 'ACTIVE',
            'pnl': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        
        result = await db.move_trades.insert_one(trade_doc)
        logger.info(f"✅ MOVE trade created: {result.inserted_id}")
        
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"❌ Error creating MOVE trade: {e}")
        raise


async def update_move_trade(
    db: AsyncIOMotorDatabase,
    trade_id: str,
    updates: dict
) -> bool:
    """Update a MOVE trade"""
    try:
        updates['updated_at'] = datetime.utcnow()
        
        result = await db.move_trades.update_one(
            {'_id': ObjectId(trade_id)},
            {'$set': updates}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ MOVE trade {trade_id} updated")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error updating MOVE trade: {e}")
        raise


async def get_move_trade(
    db: AsyncIOMotorDatabase,
    trade_id: str
) -> dict:
    """Get a MOVE trade by ID"""
    try:
        trade = await db.move_trades.find_one({'_id': ObjectId(trade_id)})
        return trade or {}
    except Exception as e:
        logger.error(f"❌ Error fetching MOVE trade: {e}")
        return {}


async def get_user_move_trades(
    db: AsyncIOMotorDatabase,
    user_id: int
) -> list:
    """Get all MOVE trades for a user"""
    try:
        trades = await db.move_trades.find({'user_id': user_id}).to_list(None)
        return trades or []
    except Exception as e:
        logger.error(f"❌ Error fetching user MOVE trades: {e}")
        return []


async def close_move_trade(
    db: AsyncIOMotorDatabase,
    trade_id: str,
    exit_price: float,
    pnl: float
) -> bool:
    """Close a MOVE trade"""
    try:
        result = await db.move_trades.update_one(
            {'_id': ObjectId(trade_id)},
            {
                '$set': {
                    'status': 'CLOSED',
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ MOVE trade {trade_id} closed | PnL: {pnl}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error closing MOVE trade: {e}")
        raise


__all__ = [
    'create_move_trade',
    'update_move_trade',
    'get_move_trade',
    'get_user_move_trades',
    'close_move_trade',
]
