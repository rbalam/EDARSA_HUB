"""
EDARSA HUB - Core Scheduler Module
==================================

El paquete raiz evita importar SchedulerManager, rutas y jobs durante
la importacion de submodulos independientes, como la capa de locks.

Los componentes pesados se resuelven de forma diferida mediante
__getattr__.
"""

from importlib import import_module

from .config import JobConfig, SchedulerConfig


_MANAGER_EXPORTS = {
    "SchedulerManager",
    "get_scheduler_manager",
    "start_scheduler",
    "stop_scheduler",
}

_ROUTE_EXPORTS = {
    "scheduler_router",
    "init_scheduler_routes",
}

__all__ = [
    "SchedulerManager",
    "get_scheduler_manager",
    "start_scheduler",
    "stop_scheduler",
    "SchedulerConfig",
    "JobConfig",
    "scheduler_router",
    "init_scheduler_routes",
]


def __getattr__(name):
    """Resuelve componentes pesados solo cuando se solicitan."""
    if name in _MANAGER_EXPORTS:
        module = import_module(".scheduler_manager", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value

    if name in _ROUTE_EXPORTS:
        module = import_module(".routes", __name__)
        attribute = (
            "router"
            if name == "scheduler_router"
            else "init_scheduler_routes"
        )
        value = getattr(module, attribute)
        globals()[name] = value
        return value

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


def __dir__():
    return sorted(set(globals()) | set(__all__))
