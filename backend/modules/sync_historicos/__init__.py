"""
EDARSA HUB - Sync Historicos
============================
Modulo de sincronizacion historica.

Los exports legacy se resuelven de forma lazy para que importar submodulos
puros (planner, contratos, validaciones) no inicialice conexiones SQL ni exija
credenciales de runtime durante CI.
"""
from __future__ import annotations

from importlib import import_module

_MODEL_EXPORTS = {
    "SyncVentaHistorica",
    "SyncVentaPorHora",
    "SyncVentaPorDiaSemana",
    "SyncControlEjecucion",
    "SyncRunConfig",
    "SyncRunResult",
}

_LAZY_EXPORTS = {
    "SyncHistoricosRepository": (".repository", "SyncHistoricosRepository"),
    "SyncHistoricosService": (".service", "SyncHistoricosService"),
}

__all__ = [
    "SyncVentaHistorica",
    "SyncVentaPorHora",
    "SyncVentaPorDiaSemana",
    "SyncControlEjecucion",
    "SyncRunConfig",
    "SyncRunResult",
    "SyncHistoricosRepository",
    "SyncHistoricosService",
]


def __getattr__(name: str):
    if name in _MODEL_EXPORTS:
        module = import_module(".models", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value

    lazy = _LAZY_EXPORTS.get(name)
    if lazy:
        module_name, attr_name = lazy
        module = import_module(module_name, __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
