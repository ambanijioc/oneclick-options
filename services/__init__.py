"""
Shared services for the trading bot.
"""

from .leg_protection_service import start_leg_protection_monitor

__all__ = ['start_leg_protection_monitor']
