"""
MongoDB connection manager using Motor (async driver).
Handles connection pooling, health checks, and graceful shutdown.
"""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from logger import logger, log_function_call
from config import config


class DatabaseManager:
    """Manages MongoDB connection lifecycle."""
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        """Singleton pattern to ensure single database connection."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database manager (only once due to singleton)."""
        if self._client is None:
            logger.info("[DatabaseManager.__init__] Initializing MongoDB connection manager")
    
    @log_function_call
    async def connect(self, max_retries: int = 3, retry_delay: int = 5) -> AsyncIOMotorDatabase:
        """
        Establish connection to MongoDB with retry logic.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between retries in seconds
        
        Returns:
            AsyncIOMotorDatabase instance
        
        Raises:
            ConnectionFailure: If connection fails after all retries
        """
        if self._database is not None:
            logger.info("[DatabaseManager.connect] Using existing database connection")
            return self._database
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"[DatabaseManager.connect] Connection attempt {attempt}/{max_retries}"
                )
                
                # Create MongoDB client
                self._client = AsyncIOMotorClient(
                    config.mongodb.uri,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=20000,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=45000
                )
                
                # Test connection
                await self._client.admin.command('ping')
                
                # Get database
                self._database = self._client[config.mongodb.database_name]
                
                logger.info(
                    f"[DatabaseManager.connect] Successfully connected to MongoDB: "
                    f"{config.mongodb.database_name}"
                )
                
                # Create indexes
                await self._create_indexes()
                
                return self._database
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(
                    f"[DatabaseManager.connect] Connection attempt {attempt} failed: {e}"
                )
                
                if attempt < max_retries:
                    logger.info(f"[DatabaseManager.connect] Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical(
                        f"[DatabaseManager.connect] All connection attempts failed"
                    )
                    raise ConnectionFailure(
                        f"Could not connect to MongoDB after {max_retries} attempts"
                    )
            
            except Exception as e:
                logger.critical(
                    f"[DatabaseManager.connect] Unexpected error during connection: {e}"
                )
                raise
    
    @log_function_call
    async def _create_indexes(self):
        """Create database indexes for optimized queries."""
        try:
            db = self._database
            
            # API Credentials indexes
            await db.api_credentials.create_index("user_id")
            await db.api_credentials.create_index([("user_id", 1), ("api_name", 1)])
            
            # Strategy indexes
            await db.straddle_strategies.create_index("user_id")
            await db.strangle_strategies.create_index("user_id")
            await db.straddle_strategies.create_index([("user_id", 1), ("strategy_name", 1)])
            await db.strangle_strategies.create_index([("user_id", 1), ("strategy_name", 1)])
            
            # Trade history indexes
            await db.trade_history.create_index("user_id")
            await db.trade_history.create_index([("user_id", 1), ("created_at", -1)])
            await db.trade_history.create_index([("user_id", 1), ("api_name", 1)])
            
            # Schedule indexes
            await db.auto_schedules.create_index("user_id")
            await db.auto_schedules.create_index([("user_id", 1), ("is_active", 1)])
            await db.auto_schedules.create_index("execution_time")
            
            logger.info("[DatabaseManager._create_indexes] All indexes created successfully")
            
        except Exception as e:
            logger.warning(f"[DatabaseManager._create_indexes] Index creation warning: {e}")
    
    @log_function_call
    async def health_check(self) -> bool:
        """
        Check MongoDB connection health.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if self._client is None:
                logger.warning("[DatabaseManager.health_check] No active connection")
                return False
            
            await self._client.admin.command('ping')
            logger.debug("[DatabaseManager.health_check] Connection healthy")
            return True
            
        except Exception as e:
            logger.error(f"[DatabaseManager.health_check] Health check failed: {e}")
            return False
    
    @log_function_call
    async def close(self):
        """Gracefully close MongoDB connection."""
        try:
            if self._client is not None:
                self._client.close()
                self._client = None
                self._database = None
                logger.info("[DatabaseManager.close] MongoDB connection closed")
        except Exception as e:
            logger.error(f"[DatabaseManager.close] Error closing connection: {e}")
    
    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """
        Get the current database instance.
        
        Returns:
            AsyncIOMotorDatabase instance or None if not connected
        """
        if self._database is None:
            logger.warning("[DatabaseManager.get_database] Database not initialized")
        return self._database
    
    async def get_collection(self, collection_name: str):
        """
        Get a specific collection from the database.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Collection instance
        """
        if self._database is None:
            await self.connect()
        return self._database[collection_name]


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Helper function to get database instance.
    
    Returns:
        AsyncIOMotorDatabase instance
    """
    if db_manager.get_database() is None:
        await db_manager.connect()
    return db_manager.get_database()


# Graceful shutdown handler
async def shutdown_database():
    """Shutdown database connection gracefully."""
    logger.info("[shutdown_database] Shutting down database connection")
    await db_manager.close()


if __name__ == "__main__":
    # Test database connection
    async def test_connection():
        print("Testing MongoDB connection...")
        
        try:
            db = await get_database()
            print(f"✅ Connected to database: {db.name}")
            
            # Test health check
            is_healthy = await db_manager.health_check()
            print(f"✅ Health check: {'Passed' if is_healthy else 'Failed'}")
            
            # Test collection access
            collection = await db_manager.get_collection('test_collection')
            print(f"✅ Accessed collection: {collection.name}")
            
            # Cleanup
            await db_manager.close()
            print("✅ Connection closed successfully")
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
    
    asyncio.run(test_connection())
      
