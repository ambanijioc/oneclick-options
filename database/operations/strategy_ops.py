"""
CRUD operations for strategy presets.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from database.connection import get_database
from database.models.strategy_preset import (
    StrategyPreset,
    StraddlePreset,
    StranglePreset,
    StrategyPresetCreate
)
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_strategy_preset(data: StrategyPresetCreate) -> str:
    """
    Create new strategy preset.
    
    Args:
        data: Strategy preset creation data
    
    Returns:
        Created preset ID
    
    Raises:
        ValueError: If validation fails
    """
    try:
        db = get_database()
        
        # Create appropriate preset model
        if data.strategy_type == "straddle":
            preset = StraddlePreset(
                user_id=data.user_id,
                name=data.name,
                description=data.description,
                asset=data.asset,
                expiry_code=data.expiry_code,
                direction=data.direction,
                lot_size=data.lot_size,
                sl_trigger_pct=data.sl_trigger_pct,
                sl_limit_pct=data.sl_limit_pct,
                target_trigger_pct=data.target_trigger_pct,
                target_limit_pct=data.target_limit_pct,
                atm_offset=data.atm_offset or 0,
                enable_sl_monitor=data.enable_sl_monitor  # ✅ ADD THIS
            )
        else:  # strangle
            if not data.otm_selection:
                raise ValueError("OTM selection is required for strangle strategies")
            
            preset = StranglePreset(
                user_id=data.user_id,
                name=data.name,
                description=data.description,
                asset=data.asset,
                expiry_code=data.expiry_code,
                direction=data.direction,
                lot_size=data.lot_size,
                sl_trigger_pct=data.sl_trigger_pct,
                sl_limit_pct=data.sl_limit_pct,
                target_trigger_pct=data.target_trigger_pct,
                target_limit_pct=data.target_limit_pct,
                otm_selection=data.otm_selection,
                enable_sl_monitor=data.enable_sl_monitor  # ✅ ADD THIS
            )
        
        # Insert to database
        result = await db.strategy_presets.insert_one(preset.to_dict())
        preset_id = str(result.inserted_id)
        
        logger.info(
            f"Created {data.strategy_type} preset: {preset_id} "
            f"for user {data.user_id} (name: {data.name})"
        )
        
        return preset_id
    
    except DuplicateKeyError:
        logger.warning(f"Duplicate strategy name '{data.name}' for user {data.user_id}")
        raise ValueError(f"Strategy name '{data.name}' already exists")
    
    except Exception as e:
        logger.error(f"Failed to create strategy preset: {e}", exc_info=True)
        raise


async def get_strategy_presets(
    user_id: int,
    include_inactive: bool = False
) -> List[StrategyPreset]:
    """
    Get all strategy presets for a user.
    
    Args:
        user_id: User ID
        include_inactive: Include inactive presets
    
    Returns:
        List of strategy presets
    """
    try:
        db = get_database()
        
        # Build query
        query = {"user_id": user_id}
        if not include_inactive:
            query["is_active"] = True
        
        # Fetch presets
        cursor = db.strategy_presets.find(query).sort("created_at", -1)
        presets = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            
            # Create appropriate model based on strategy type
            if doc["strategy_type"] == "straddle":
                presets.append(StraddlePreset(**doc))
            else:
                presets.append(StranglePreset(**doc))
        
        logger.debug(f"Retrieved {len(presets)} strategy preset(s) for user {user_id}")
        
        return presets
    
    except Exception as e:
        logger.error(f"Failed to get strategy presets: {e}", exc_info=True)
        raise


async def get_strategy_presets_by_type(
    user_id: int,
    strategy_type: str,
    include_inactive: bool = False
) -> List[StrategyPreset]:
    """
    Get strategy presets by type for a user.
    
    Args:
        user_id: User ID
        strategy_type: Strategy type (straddle/strangle)
        include_inactive: Include inactive presets
    
    Returns:
        List of strategy presets
    """
    try:
        db = get_database()
        
        # Build query
        query = {
            "user_id": user_id,
            "strategy_type": strategy_type
        }
        if not include_inactive:
            query["is_active"] = True
        
        # Fetch presets
        cursor = db.strategy_presets.find(query).sort("created_at", -1)
        presets = []
        
        async for doc in cursor:
            doc["_id"] = ObjectId(doc["_id"])
            
            if strategy_type == "straddle":
                presets.append(StraddlePreset(**doc))
            else:
                presets.append(StranglePreset(**doc))
        
        logger.debug(
            f"Retrieved {len(presets)} {strategy_type} preset(s) for user {user_id}"
        )
        
        return presets
    
    except Exception as e:
        logger.error(f"Failed to get strategy presets by type: {e}", exc_info=True)
        raise


async def get_strategy_preset_by_id(preset_id: str) -> Optional[StrategyPreset]:
    """
    Get strategy preset by ID.
    
    Args:
        preset_id: Preset ID
    
    Returns:
        Strategy preset or None if not found
    """
    try:
        db = get_database()
        
        # Fetch preset
        doc = await db.strategy_presets.find_one({"_id": ObjectId(preset_id)})
        
        if not doc:
            logger.warning(f"Strategy preset not found: {preset_id}")
            return None
        
        doc["_id"] = ObjectId(doc["_id"])
        
        # Create appropriate model
        if doc["strategy_type"] == "straddle":
            preset = StraddlePreset(**doc)
        else:
            preset = StranglePreset(**doc)
        
        logger.debug(f"Retrieved strategy preset: {preset_id}")
        
        return preset
    
    except Exception as e:
        logger.error(f"Failed to get strategy preset by ID: {e}", exc_info=True)
        raise


async def update_strategy_preset(
    preset_id: str,
    update_data: Dict[str, Any]
) -> bool:
    """
    Update strategy preset.
    
    Args:
        preset_id: Preset ID
        update_data: Data to update
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update document
        result = await db.strategy_presets.update_one(
            {"_id": ObjectId(preset_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated strategy preset: {preset_id}")
            return True
        else:
            logger.warning(f"No changes made to strategy preset: {preset_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to update strategy preset: {e}", exc_info=True)
        raise


async def delete_strategy_preset(preset_id: str) -> bool:
    """
    Delete strategy preset.
    
    Args:
        preset_id: Preset ID
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        db = get_database()
        
        # Delete document
        result = await db.strategy_presets.delete_one({"_id": ObjectId(preset_id)})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted strategy preset: {preset_id}")
            return True
        else:
            logger.warning(f"Strategy preset not found for deletion: {preset_id}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to delete strategy preset: {e}", exc_info=True)
        raise


async def check_strategy_name_exists(user_id: int, name: str) -> bool:
    """
    Check if strategy name already exists for user.
    
    Args:
        user_id: User ID
        name: Strategy name
    
    Returns:
        True if name exists, False otherwise
    """
    try:
        db = get_database()
        
        count = await db.strategy_presets.count_documents({
            "user_id": user_id,
            "name": name
        })
        
        return count > 0
    
    except Exception as e:
        logger.error(f"Failed to check strategy name existence: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio
    from database.models.strategy_preset import OTMSelection
    
    async def test():
        from database.connection import connect_db, close_db
        
        await connect_db()
        
        # Test create straddle
        straddle_data = StrategyPresetCreate(
            user_id=12345,
            strategy_type="straddle",
            name="Test Straddle",
            description="Test straddle strategy",
            asset="BTC",
            expiry_code="W",
            direction="long",
            lot_size=10,
            sl_trigger_pct=50.0,
            sl_limit_pct=55.0,
            target_trigger_pct=100.0,
            target_limit_pct=95.0,
            atm_offset=0
        )
        
        try:
            preset_id = await create_strategy_preset(straddle_data)
            print(f"Created straddle preset: {preset_id}")
            
            # Get preset
            preset = await get_strategy_preset_by_id(preset_id)
            print(f"Retrieved preset: {preset.name}")
            
            # Delete preset
            deleted = await delete_strategy_preset(preset_id)
            print(f"Deleted preset: {deleted}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        await close_db()
    
    asyncio.run(test())
      
