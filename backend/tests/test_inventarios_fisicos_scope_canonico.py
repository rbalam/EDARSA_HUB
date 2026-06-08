"""
Regresión P0 (2026-06-08): Inventarios físicos NO-LIVE deben funcionar para AMBOS
sistemas (SoftRestaurant single-tenant y MPRO shared-server) sin romper uno al otro.

CAUSA RAÍZ del bug histórico (se perdía ~4 veces): el endpoint
`/compras/inventarios-fisicos/{server_id}` aplicaba SIEMPRE el filtro por sucursal.
El frontend de SoftRestaurant envía el placeholder `sucursal='SoftRestaurant'`, que NO
existe en `Compras_Inventarios_Fisicos_Sync` (allí la sucursal viene vacía para SR),
así que filtraba a 0 filas → "No hay inventarios disponibles".

FIX CANÓNICO (sistema-agnóstico, sin hardcodear 'MPRO'/'SoftRestaurant'):
    sucursal_filtro = (sucursal_id or sucursal) if _shared_server(server_id) else None
Es decir, el filtro por sucursal SOLO aplica cuando un mismo server_id aloja >1 unidad
(caso MPRO ORIGEN/QRO). Para single-tenant el server_id basta.

Este test BLINDA esa invariante canónica leyendo `Unidades_Negocio` real (EDARSAHUB).
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")


def _get_helpers():
    from core.corporate_filters.request_resolver import _shared_server
    from core.unidades_service import UnidadesService
    return _shared_server, UnidadesService


def test_softrestaurant_servers_no_son_compartidos():
    """Cada server SoftRestaurant aloja exactamente 1 unidad → NO se filtra por sucursal."""
    _shared_server, UnidadesService = _get_helpers()
    unidades = UnidadesService.get_all()
    sr = [u for u in unidades if str(u.get("system_type", "")).upper().startswith("SOFT")]
    assert sr, "Debe haber unidades SoftRestaurant en EDARSAHUB"
    for u in sr:
        sid = u.get("server_id")
        assert _shared_server(sid) is False, (
            f"SoftRestaurant {u.get('codigo')} (server={sid}) NO debe ser shared; "
            f"si lo es, el filtro de sucursal volverá a romper sus inventarios."
        )


def test_mpro_server_es_compartido_origen_y_qro():
    """El server MPRO aloja ORIGEN y 130QRO → SÍ requiere desambiguar por sucursal."""
    _shared_server, UnidadesService = _get_helpers()
    unidades = UnidadesService.get_all()
    mpro = [u for u in unidades if str(u.get("system_type", "")).upper() == "MPRO"]
    assert len(mpro) >= 2, "Deben existir al menos 2 unidades MPRO (ORIGEN y 130QRO)"
    # Todas las MPRO comparten el mismo server_id en este despliegue
    server_ids = {u.get("server_id") for u in mpro}
    for sid in server_ids:
        # Si un server MPRO aloja >1 unidad, debe reportarse como shared
        n = sum(1 for u in unidades if u.get("server_id") == sid)
        if n > 1:
            assert _shared_server(sid) is True, (
                f"server MPRO {sid} aloja {n} unidades y debe ser shared (desambiguación)."
            )


def test_filtro_sucursal_solo_para_shared():
    """Replica la regla del endpoint: sucursal_filtro None para single-tenant."""
    _shared_server, UnidadesService = _get_helpers()
    unidades = UnidadesService.get_all()

    def sucursal_filtro(server_id, sucursal_id, sucursal):
        return (sucursal_id or sucursal) if _shared_server(server_id) else None

    for u in unidades:
        sid = u.get("server_id")
        if str(u.get("system_type", "")).upper().startswith("SOFT"):
            # Aunque llegue el placeholder 'SoftRestaurant', NO debe filtrarse
            assert sucursal_filtro(sid, "", "SoftRestaurant") is None
