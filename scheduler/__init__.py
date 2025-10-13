"""
Job scheduler package for automated executions.
"""

from .job_scheduler import init_scheduler, shutdown_scheduler, add_auto_execution_job, remove_auto_execution_job
from .auto_trade_jobs import execute_auto_trade

__all__ = [
    'init_scheduler',
    'shutdown_scheduler',
    'add_auto_execution_job',
    'remove_auto_execution_job',
    'execute_auto_trade'
]
