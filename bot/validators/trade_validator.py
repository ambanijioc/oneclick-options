"""
Trade parameter validation.
"""

from typing import Dict, Any, Tuple, Optional

from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_strategy_parameters(strategy_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate strategy preset parameters.
    
    Args:
        strategy_data: Strategy parameters dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = [
        'name', 'asset', 'expiry_code', 'direction', 'lot_size',
        'sl_trigger_pct', 'sl_limit_pct'
    ]
    
    for field in required_fields:
        if field not in strategy_data:
            return False, f"Missing required field: {field}"
    
    # Validate asset
    if strategy_data['asset'] not in ['BTC', 'ETH']:
        return False, "Asset must be BTC or ETH"
    
    # Validate direction
    if strategy_data['direction'] not in ['long', 'short']:
        return False, "Direction must be long or short"
    
    # Validate lot size
    if strategy_data['lot_size'] <= 0:
        return False, "Lot size must be positive"
    
    # Validate percentages
    if strategy_data['sl_trigger_pct'] < 0 or strategy_data['sl_trigger_pct'] > 100:
        return False, "SL trigger percentage must be between 0 and 100"
    
    if strategy_data['sl_limit_pct'] < 0 or strategy_data['sl_limit_pct'] > 100:
        return False, "SL limit percentage must be between 0 and 100"
    
    # Validate target if provided
    target_pct = strategy_data.get('target_trigger_pct', 0)
    if target_pct < 0 or target_pct > 100:
        return False, "Target percentage must be between 0 and 100"
    
    # Strategy-specific validation
    strategy_type = strategy_data.get('strategy_type', 'straddle')
    
    if strategy_type == 'straddle':
        atm_offset = strategy_data.get('atm_offset', 0)
        if abs(atm_offset) > 10:
            return False, "ATM offset must be between -10 and +10"
    
    elif strategy_type == 'strangle':
        if 'otm_selection' not in strategy_data:
            return False, "OTM selection is required for strangle strategies"
        
        otm_selection = strategy_data['otm_selection']
        if otm_selection['type'] not in ['percentage', 'numeral']:
            return False, "OTM selection type must be percentage or numeral"
        
        if otm_selection['value'] <= 0:
            return False, "OTM value must be positive"
    
    return True, None


def validate_strike_price(
    strike: int,
    asset: str,
    spot_price: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate strike price is reasonable.
    
    Args:
        strike: Strike price
        asset: Asset (BTC or ETH)
        spot_price: Current spot price
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check strike increment
    if asset == "BTC":
        if strike % 200 != 0:
            return False, "BTC strike prices must be in 200 increments"
    elif asset == "ETH":
        if strike % 20 != 0:
            return False, "ETH strike prices must be in 20 increments"
    
    # Check strike is within reasonable range (±50% of spot)
    min_strike = spot_price * 0.5
    max_strike = spot_price * 1.5
    
    if strike < min_strike or strike > max_strike:
        return False, f"Strike price too far from spot price (must be between {min_strike:.0f} and {max_strike:.0f})"
    
    return True, None


async def check_sufficient_balance(
    api_id: str,
    required_margin: float
) -> Tuple[bool, Optional[str]]:
    """
    Check if account has sufficient balance for trade.
    
    Args:
        api_id: API credential ID
        required_margin: Required margin for trade
    
    Returns:
        Tuple of (has_sufficient_balance, error_message)
    """
    try:
        # Import here to avoid circular dependency
        from database.operations.api_ops import get_decrypted_api_credential
        from delta.client import DeltaClient
        
        # Get API credentials
        credentials = await get_decrypted_api_credential(api_id)
        if not credentials:
            return False, "API credentials not found"
        
        api_key, api_secret = credentials
        
        # Get wallet balance
        client = DeltaClient(api_key, api_secret)
        balance_response = await client.get_wallet_balance()
        
        if not balance_response.get('success'):
            return False, "Failed to fetch balance"
        
        # Check available balance
        available_balance = balance_response.get('result', {}).get('available_balance', 0)
        
        if available_balance < required_margin:
            return False, f"Insufficient balance. Required: ${required_margin:.2f}, Available: ${available_balance:.2f}"
        
        logger.info(f"Balance check passed: Available ${available_balance:.2f}, Required ${required_margin:.2f}")
        return True, None
    
    except Exception as e:
        logger.error(f"Balance check failed: {e}", exc_info=True)
        return False, f"Balance check failed: {str(e)}"


def validate_trade_request(
    strategy_preset: Dict[str, Any],
    api_id: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate complete trade request.
    
    Args:
        strategy_preset: Strategy preset data
        api_id: API credential ID
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate strategy parameters
    is_valid, error = validate_strategy_parameters(strategy_preset)
    if not is_valid:
        return False, error
    
    # Validate API ID
    if not api_id or len(api_id) < 10:
        return False, "Invalid API credential ID"
    
    # Additional business logic validation
    # (Can be extended based on requirements)
    
    return True, None


if __name__ == "__main__":
    # Test validators
    print("Testing trade validators...\n")
    
    # Test strategy validation
    strategy = {
        'name': 'Test Strategy',
        'asset': 'BTC',
        'expiry_code': 'W',
        'direction': 'long',
        'lot_size': 10,
        'sl_trigger_pct': 50.0,
        'sl_limit_pct': 55.0,
        'target_trigger_pct': 100.0,
        'strategy_type': 'straddle',
        'atm_offset': 0
    }
    
    is_valid, error = validate_strategy_parameters(strategy)
    print(f"Strategy validation: Valid={is_valid}, Error={error}")
    
    # Test strike validation
    is_valid, error = validate_strike_price(65000, "BTC", 65000)
    print(f"\nStrike validation (65000, BTC): Valid={is_valid}, Error={error}")
    
    is_valid, error = validate_strike_price(65100, "BTC", 65000)
    print(f"Strike validation (65100, BTC): Valid={is_valid}, Error={error}")
          
