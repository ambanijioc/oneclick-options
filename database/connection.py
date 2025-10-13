"""
MongoDB connection management using Motor (async driver).
"""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import settings
from bot.utils.logger import setup_logger, log_to_telegram

logger = setup_logger(__name__)

# Global MongoDB client and database instances
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None


async def connect_db() -> AsyncIOMotorDatabase:
    """
    Connect to MongoDB and return database instance.
    
    Returns:
        MongoDB database instance
    
    Raises:
        ConnectionFailure: If connection fails
    """
    global _mongo_client, _mongo_db
    
    if _mongo_db is not None:
        logger.info("MongoDB already connected")
        return _mongo_db
    
    try:
        logger.info(f"Connecting to MongoDB: {settings.MONGO_DB_NAME}")
        
        # Create MongoDB client
        _mongo_client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            maxPoolSize=10,
            minPoolSize=1
        )
        
        # Get database
        _mongo_db = _mongo_client[settings.MONGO_DB_NAME]
        
        # Test connection
        await _mongo_client.admin.command('ping')
        
        logger.info(f"✓ Connected to MongoDB: {settings.MONGO_DB_NAME}")
        
        # Create indexes
        await _create_indexes()
        
        return _mongo_db
    
    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB connection timeout: {e}")
        await log_to_telegram(
            message="Failed to connect to MongoDB: Timeout",
            level="CRITICAL",
            module="database.connection"
        )
        raise ConnectionFailure(f"MongoDB connection timeout: {e}")
    
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
        await log_to_telegram(
            message=f"Failed to connect to MongoDB: {str(e)}",
            level="CRITICAL",
            module="database.connection",
            error_details=str(e)
        )
        raise


async def close_db():
    """
    Close MongoDB connection.
    """
    global _mongo_client, _mongo_db
    
    if _mongo_client:
        logger.info("Closing MongoDB connection...")
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("✓ MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get current database instance.
    
    Returns:
        MongoDB database instance
    
    Raises:
        RuntimeError: If database is not connected
    """
    if _mongo_db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    
    return _mongo_db


async def _create_indexes():
    """
    Create database indexes for optimal query performance.
    """
    try:
        db = get_database()
        
        logger.info("Creating database indexes...")
        
        # API Credentials indexes
        await db.api_credentials.create_index([("user_id", 1)])
        await db.api_credentials.create_index([("user_id", 1), ("api_name", 1)], unique=True)
        
        # Strategy Presets indexes
        await db.strategy_presets.create_index([("user_id", 1)])
        await db.strategy_presets.create_index([("user_id", 1), ("strategy_type", 1)])
        await db.strategy_presets.create_index([("user_id", 1), ("name", 1)], unique=True)
        
        # Auto Execution indexes
        await db.auto_executions.create_index([("user_id", 1)])
        await db.auto_executions.create_index([("enabled", 1)])
        await db.auto_executions.create_index([("execution_time", 1)])
        
        # Trade History indexes
        await db.trade_history.create_index([("user_id", 1)])
        await db.trade_history.create_index([("user_id", 1), ("entry_time", -1)])
        await db.trade_history.create_index([("api_id", 1)])
        
        # User Settings indexes
        await db.user_settings.create_index([("user_id", 1)], unique=True)
        
        logger.info("✓ Database indexes created successfully")
    
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}", exc_info=True)
        # Don't raise - indexes are optional for functionality


async def test_connection() -> bool:
    """
    Test MongoDB connection.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        db = get_database()
        await db.command('ping')
        logger.info("MongoDB connection test: OK")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    async def test():
        try:
            db = await connect_db()
            print(f"Connected to database: {db.name}")
            
            # Test connection
            is_connected = await test_connection()
            print(f"Connection test: {'PASSED' if is_connected else 'FAILED'}")
            
            await close_db()
            print("Connection closed")
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(test())
  
