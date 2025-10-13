"""
CRUD operations for strategy presets (Straddle and Strangle).
Handles creation, retrieval, update, and deletion of strategy configurations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import pytz

from database.connection import get_database
from database.models import (
    StraddleStrategy,
    StrangleStrategy,
    StrategyTypeEnum,
    StopLossTargetConfig
)
from logger import logger, log_function_call


class StrategyOperations:
    """Strategy presets database operations."""
    
    def __init__(self):
        """Initialize strategy operations."""
        self.straddle_collection = "straddle_strategies"
        self.strangle_collection = "strangle_strategies"
    
    @log_function_call
    async def create_straddle_strategy(
        self,
        user_id: int,
        strategy_name: str,
        strategy_description: Optional[str],
        asset: str,
        expiry: str,
        direction: str,
        lot_size: int,
        atm_offset: int,
        stoploss_config: Optional[Dict[str, float]],
        target_config: Optional[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Create a new straddle strategy preset.
        
        Args:
            user_id: Telegram user ID
            strategy_name: Name of the strategy
            strategy_description: Description of the strategy
            asset: Trading asset (BTC/ETH)
            expiry: Expiry notation (D, D+1, W, M, etc.)
            direction: Trade direction (long/short)
            lot_size: Number of lots
            atm_offset: ATM offset in strike increments
            stoploss_config: Stop loss configuration dict
            target_config: Target configuration dict
        
        Returns:
            Dictionary with success status and strategy ID
        """
        try:
            db = await get_database()
            collection = db[self.straddle_collection]
            
            # Check if strategy name already exists
            existing = await collection.find_one({
                "user_id": user_id,
                "strategy_name": strategy_name,
                "is_active": True
            })
            
            if existing:
                logger.warning(
                    f"[StrategyOperations.create_straddle_strategy] Strategy '{strategy_name}' "
                    f"already exists for user {user_id}"
                )
                return {
                    "success": False,
                    "error": f"Strategy name '{strategy_name}' already exists"
                }
            
            # Parse SL/TP configs
            sl_config = None
            if stoploss_config:
                sl_config = StopLossTargetConfig(**stoploss_config)
            
            tp_config = None
            if target_config:
                tp_config = StopLossTargetConfig(**target_config)
            
            # Create strategy document
            strategy = StraddleStrategy(
                user_id=user_id,
                strategy_name=strategy_name,
                strategy_description=strategy_description,
                asset=asset,
                expiry=expiry,
                direction=direction,
                lot_size=lot_size,
                atm_offset=atm_offset,
                stoploss_config=sl_config,
                target_config=tp_config
            )
            
            # Insert into database
            result = await collection.insert_one(strategy.model_dump())
            
            logger.info(
                f"[StrategyOperations.create_straddle_strategy] Straddle strategy "
                f"'{strategy_name}' created for user {user_id}, ID: {result.inserted_id}"
            )
            
            return {
                "success": True,
                "strategy_id": str(result.inserted_id),
                "strategy_name": strategy_name
            }
            
        except Exception as e:
            logger.error(
                f"[StrategyOperations.create_straddle_strategy] Error creating strategy: {e}"
            )
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def create_strangle_strategy(
        self,
        user_id: int,
        strategy_name: str,
        strategy_description: Optional[str],
        asset: str,
        expiry: str,
        direction: str,
        lot_size: int,
        otm_percentage: Optional[float],
        otm_value: Optional[int],
        stoploss_config: Optional[Dict[str, float]],
        target_config: Optional[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Create a new strangle strategy preset.
        
        Args:
            user_id: Telegram user ID
            strategy_name: Name of the strategy
            strategy_description: Description of the strategy
            asset: Trading asset (BTC/ETH)
            expiry: Expiry notation (D, D+1, W, M, etc.)
            direction: Trade direction (long/short)
            lot_size: Number of lots
            otm_percentage: OTM percentage from spot
            otm_value: OTM value from spot
            stoploss_config: Stop loss configuration dict
            target_config: Target configuration dict
        
        Returns:
            Dictionary with success status and strategy ID
        """
        try:
            db = await get_database()
            collection = db[self.strangle_collection]
            
            # Check if strategy name already exists
            existing = await collection.find_one({
                "user_id": user_id,
                "strategy_name": strategy_name,
                "is_active": True
            })
            
            if existing:
                logger.warning(
                    f"[StrategyOperations.create_strangle_strategy] Strategy '{strategy_name}' "
                    f"already exists for user {user_id}"
                )
                return {
                    "success": False,
                    "error": f"Strategy name '{strategy_name}' already exists"
                }
            
            # Validate OTM input
            if not otm_percentage and not otm_value:
                return {
                    "success": False,
                    "error": "Either otm_percentage or otm_value must be provided"
                }
            
            # Parse SL/TP configs
            sl_config = None
            if stoploss_config:
                sl_config = StopLossTargetConfig(**stoploss_config)
            
            tp_config = None
            if target_config:
                tp_config = StopLossTargetConfig(**target_config)
            
            # Create strategy document
            strategy = StrangleStrategy(
                user_id=user_id,
                strategy_name=strategy_name,
                strategy_description=strategy_description,
                asset=asset,
                expiry=expiry,
                direction=direction,
                lot_size=lot_size,
                otm_percentage=otm_percentage,
                otm_value=otm_value,
                stoploss_config=sl_config,
                target_config=tp_config
            )
            
            # Insert into database
            result = await collection.insert_one(strategy.model_dump())
            
            logger.info(
                f"[StrategyOperations.create_strangle_strategy] Strangle strategy "
                f"'{strategy_name}' created for user {user_id}, ID: {result.inserted_id}"
            )
            
            return {
                "success": True,
                "strategy_id": str(result.inserted_id),
                "strategy_name": strategy_name
            }
            
        except Exception as e:
            logger.error(
                f"[StrategyOperations.create_strangle_strategy] Error creating strategy: {e}"
            )
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def get_strategies_by_type(
        self,
        user_id: int,
        strategy_type: StrategyTypeEnum
    ) -> List[Dict[str, Any]]:
        """
        Get all strategies of a specific type for a user.
        
        Args:
            user_id: Telegram user ID
            strategy_type: Type of strategy (straddle/strangle)
        
        Returns:
            List of strategy documents
        """
        try:
            db = await get_database()
            collection_name = (
                self.straddle_collection if strategy_type == StrategyTypeEnum.STRADDLE
                else self.strangle_collection
            )
            collection = db[collection_name]
            
            cursor = collection.find({
                "user_id": user_id,
                "is_active": True
            }).sort("created_at", -1)
            
            strategies = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                strategies.append(doc)
            
            logger.info(
                f"[StrategyOperations.get_strategies_by_type] Retrieved {len(strategies)} "
                f"{strategy_type.value} strategies for user {user_id}"
            )
            
            return strategies
            
        except Exception as e:
            logger.error(
                f"[StrategyOperations.get_strategies_by_type] Error retrieving strategies: {e}"
            )
            return []
    
    @log_function_call
    async def get_strategy_by_name(
        self,
        user_id: int,
        strategy_name: str,
        strategy_type: StrategyTypeEnum
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific strategy by name and type.
        
        Args:
            user_id: Telegram user ID
            strategy_name: Name of the strategy
            strategy_type: Type of strategy (straddle/strangle)
        
        Returns:
            Strategy document or None
        """
        try:
            db = await get_database()
            collection_name = (
                self.straddle_collection if strategy_type == StrategyTypeEnum.STRADDLE
                else self.strangle_collection
            )
            collection = db[collection_name]
            
            strategy = await collection.find_one({
                "user_id": user_id,
                "strategy_name": strategy_name,
                "is_active": True
            })
            
            if strategy:
                strategy['_id'] = str(strategy['_id'])
                logger.info(
                    f"[StrategyOperations.get_strategy_by_name] Retrieved strategy "
                    f"'{strategy_name}' for user {user_id}"
                )
            else:
                logger.warning(
                    f"[StrategyOperations.get_strategy_by_name] Strategy '{strategy_name}' "
                    f"not found for user {user_id}"
                )
            
            return strategy
            
        except Exception as e:
            logger.error(
                f"[StrategyOperations.get_strategy_by_name] Error retrieving strategy: {e}"
            )
            return None
    
    @log_function_call
    async def update_strategy(
        self,
        user_id: int,
        old_strategy_name: str,
        strategy_type: StrategyTypeEnum,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update existing strategy.
        
        Args:
            user_id: Telegram user ID
            old_strategy_name: Current strategy name
            strategy_type: Type of strategy (straddle/strangle)
            update_data: Dictionary of fields to update
        
        Returns:
            Dictionary with success status
        """
        try:
            db = await get_database()
            collection_name = (
                self.straddle_collection if strategy_type == StrategyTypeEnum.STRADDLE
                else self.strangle_collection
            )
            collection = db[collection_name]
            
            # Check if strategy exists
            existing = await collection.find_one({
                "user_id": user_id,
                "strategy_name": old_strategy_name,
                "is_active": True
            })
            
            if not existing:
                return {
                    "success": False,
                    "error": f"Strategy '{old_strategy_name}' not found"
                }
            
            # Check for name conflicts if renaming
            if "strategy_name" in update_data and update_data["strategy_name"] != old_strategy_name:
                name_conflict = await collection.find_one({
                    "user_id": user_id,
                    "strategy_name": update_data["strategy_name"],
                    "_id": {"$ne": existing["_id"]}
                })
                if name_conflict:
                    return {
                        "success": False,
                        "error": f"Strategy name '{update_data['strategy_name']}' already exists"
                    }
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.now(pytz.UTC)
            
            # Update document
            result = await collection.update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[StrategyOperations.update_strategy] Strategy '{old_strategy_name}' "
                    f"updated for user {user_id}"
                )
                return {"success": True, "modified": True}
            else:
                return {"success": True, "modified": False}
            
        except Exception as e:
            logger.error(f"[StrategyOperations.update_strategy] Error updating strategy: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def delete_strategy(
        self,
        user_id: int,
        strategy_name: str,
        strategy_type: StrategyTypeEnum
    ) -> Dict[str, Any]:
        """
        Delete strategy (soft delete by marking inactive).
        
        Args:
            user_id: Telegram user ID
            strategy_name: Strategy name to delete
            strategy_type: Type of strategy (straddle/strangle)
        
        Returns:
            Dictionary with success status
        """
        try:
            db = await get_database()
            collection_name = (
                self.straddle_collection if strategy_type == StrategyTypeEnum.STRADDLE
                else self.strangle_collection
            )
            collection = db[collection_name]
            
            result = await collection.update_one(
                {
                    "user_id": user_id,
                    "strategy_name": strategy_name,
                    "is_active": True
                },
                {"$set": {
                    "is_active": False,
                    "updated_at": datetime.now(pytz.UTC)
                }}
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"[StrategyOperations.delete_strategy] Strategy '{strategy_name}' "
                    f"deleted for user {user_id}"
                )
                return {"success": True}
            else:
                logger.warning(
                    f"[StrategyOperations.delete_strategy] Strategy '{strategy_name}' "
                    f"not found for user {user_id}"
                )
                return {"success": False, "error": "Strategy not found"}
            
        except Exception as e:
            logger.error(f"[StrategyOperations.delete_strategy] Error deleting strategy: {e}")
            return {"success": False, "error": str(e)}
    
    @log_function_call
    async def get_strategy_count(
        self,
        user_id: int,
        strategy_type: Optional[StrategyTypeEnum] = None
    ) -> int:
        """
        Get count of strategies for a user.
        
        Args:
            user_id: Telegram user ID
            strategy_type: Optional strategy type filter
        
        Returns:
            Number of active strategies
        """
        try:
            db = await get_database()
            
            if strategy_type:
                collection_name = (
                    self.straddle_collection if strategy_type == StrategyTypeEnum.STRADDLE
                    else self.strangle_collection
                )
                collection = db[collection_name]
                count = await collection.count_documents({
                    "user_id": user_id,
                    "is_active": True
                })
            else:
                # Count both types
                straddle_count = await db[self.straddle_collection].count_documents({
                    "user_id": user_id,
                    "is_active": True
                })
                strangle_count = await db[self.strangle_collection].count_documents({
                    "user_id": user_id,
                    "is_active": True
                })
                count = straddle_count + strangle_count
            
            return count
            
        except Exception as e:
            logger.error(f"[StrategyOperations.get_strategy_count] Error counting strategies: {e}")
            return 0


if __name__ == "__main__":
    import asyncio
    
    async def test_strategy_operations():
        """Test strategy operations."""
        print("Testing Strategy Operations...")
        
        strategy_ops = StrategyOperations()
        test_user_id = 123456789
        
        # Test create straddle strategy
        straddle_result = await strategy_ops.create_straddle_strategy(
            user_id=test_user_id,
            strategy_name="Test Straddle",
            strategy_description="Test description",
            asset="BTC",
            expiry="D",
            direction="long",
            lot_size=1,
            atm_offset=0,
            stoploss_config={"trigger_percentage": -5.0, "limit_percentage": -5.5},
            target_config={"trigger_percentage": 10.0, "limit_percentage": 9.5}
        )
        print(f"✅ Create Straddle: {straddle_result}")
        
        # Test create strangle strategy
        strangle_result = await strategy_ops.create_strangle_strategy(
            user_id=test_user_id,
            strategy_name="Test Strangle",
            strategy_description="Test description",
            asset="BTC",
            expiry="W",
            direction="long",
            lot_size=1,
            otm_percentage=1.0,
            otm_value=None,
            stoploss_config={"trigger_percentage": -5.0},
            target_config=None
        )
        print(f"✅ Create Strangle: {strangle_result}")
        
        # Test get strategies
        straddle_strategies = await strategy_ops.get_strategies_by_type(
            test_user_id,
            StrategyTypeEnum.STRADDLE
        )
        print(f"✅ Get Straddle Strategies: {len(straddle_strategies)} found")
        
        # Test get specific strategy
        strategy = await strategy_ops.get_strategy_by_name(
            test_user_id,
            "Test Straddle",
            StrategyTypeEnum.STRADDLE
        )
        print(f"✅ Get Strategy by name: {strategy['strategy_name'] if strategy else 'Not found'}")
        
        # Test strategy count
        count = await strategy_ops.get_strategy_count(test_user_id)
        print(f"✅ Strategy Count: {count}")
        
        print("\n✅ Strategy operations test completed!")
    
    asyncio.run(test_strategy_operations())
          
