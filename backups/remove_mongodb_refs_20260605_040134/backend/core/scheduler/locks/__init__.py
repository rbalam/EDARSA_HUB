"""
Locks submodule
"""
from .distributed_lock import (
    DistributedLock,
    LockManager,
    LockAcquisitionError,
    get_lock_manager,
)

__all__ = [
    'DistributedLock',
    'LockManager',
    'LockAcquisitionError',
    'get_lock_manager',
]
