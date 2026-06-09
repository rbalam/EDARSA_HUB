"""
EDARSA HUB - Servicio de Canonización de Productos (Ruta B - int estricta)
==========================================================================
Capa COMÚN reutilizable. Canoniza productos/insumos de ORIGEN (Sync_Productos*)
hacia el catálogo canónico int `Producto_Catalogo`, generando el puente
`Producto_MapeoOrigen` (ServerID + SystemType + CodigoFuente -> ProductoID).

ESTADO: MODO DRY-RUN OBLIGATORIO (cero escritura). La ejecución real está
bloqueada hasta que el usuario apruebe el DDL del puente + el plan de rollback.

ALCANCE INICIAL (acordado): SOLO insumos inventariables usados por movimientos
(`Sync_Productos_Insumos`), NO el catálogo de venta completo.

REGLAS:
- SOLO LECTURA en dry-run. Sin DDL. Sin hardcode.
- No inventa IDs. No pierde filas: lo no resoluble queda como PENDIENTE.
- descartados = 0.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from core.sql_first.db import get_sql_connection
from core.server_registry import list_unidades_negocio

logger = logging.getLogger(__name__)


@dataclass
class CoberturaUnidad:
    unidad_codigo: str
    unidad_nombre: str
    server_id: str
    system_type: str
    insumos_origen: int = 0          # total leídos (Sync_Productos_Insumos)
    insumos_canonizables: int = 0    # con CodigoFuente no vacío (resolubles a puente)
    insumos_pendientes: int = 0      # sin CodigoFuente (no resolubles)
    almacenes_canonicos: int = 0     # Inventario_Almacenes para su sucursal
    almacenes_pendientes: int = 0    # 0 si hay catálogo; marca hueco si no
    sucursal_resuelta: bool = False
    sucursal_motivo: str = ""
    tipos_canonicos: int = 0
    descartados: int = 0             # SIEMPRE 0 por diseño


def _scalar(cur, q, params=()):
    cur.execute(q, params)
    r = cur.fetchone()
    return r[0] if r else 0


def calcular_cobertura_dry_run() -> Dict:
    """
    Calcula la cobertura de canonización por unidad SIN escribir nada.
    Solo lee de EDARSAHUB (no toca POS).
    """
    conn = get_sql_connection()
    cur = conn.cursor()

    tipos_canonicos = _scalar(cur, "SELECT COUNT(*) FROM Inventario_TipoMovimiento WHERE Activo = 1")
    producto_catalogo_actual = _scalar(cur, "SELECT COUNT(*) FROM Producto_Catalogo")

    unidades = list_unidades_negocio(active_only=True)
    resultados: List[CoberturaUnidad] = []

    for u in unidades:
        codigo = u.get("codigo", "")
        server_id = u.get("server_id") or u.get("id")
        system_type = u.get("system_type", "")

        cov = CoberturaUnidad(
            unidad_codigo=codigo,
            unidad_nombre=u.get("nombre", ""),
            server_id=str(server_id),
            system_type=str(system_type),
            tipos_canonicos=tipos_canonicos,
        )

        # Insumos de origen por ServerID (llave interna de JOIN)
        cov.insumos_origen = _scalar(
            cur, "SELECT COUNT(*) FROM Sync_Productos_Insumos WHERE ServerID = %s", (str(server_id),)
        )
        cov.insumos_canonizables = _scalar(
            cur,
            "SELECT COUNT(*) FROM Sync_Productos_Insumos WHERE ServerID = %s "
            "AND CodigoFuente IS NOT NULL AND LTRIM(RTRIM(CodigoFuente)) <> ''",
            (str(server_id),),
        )
        cov.insumos_pendientes = cov.insumos_origen - cov.insumos_canonizables

        # Sucursal canónica (Sistema_SucursalServidorMapeo)
        cur.execute(
            "SELECT SucursalID, SucursalOrigenID FROM Sistema_SucursalServidorMapeo "
            "WHERE ServidorID = %s AND Activo = 1",
            (str(server_id),),
        )
        filas_suc = cur.fetchall()
        if len(filas_suc) == 1:
            cov.sucursal_resuelta = True
            cov.sucursal_motivo = f"SucursalID={filas_suc[0][0]}"
            suc_id = filas_suc[0][0]
        elif len(filas_suc) > 1:
            cov.sucursal_resuelta = False
            cov.sucursal_motivo = "AMBIGUO_MULTISUCURSAL (SucursalOrigenID NULL en mapeo)"
            suc_id = None
        else:
            cov.sucursal_resuelta = False
            cov.sucursal_motivo = "SIN_MAPEO_SERVIDOR_SUCURSAL"
            suc_id = None

        # Almacenes canónicos para esa sucursal
        if suc_id is not None:
            cov.almacenes_canonicos = _scalar(
                cur, "SELECT COUNT(*) FROM Inventario_Almacenes WHERE SucursalID = %s AND Activo = 1",
                (int(suc_id),),
            )
        cov.almacenes_pendientes = 0 if cov.almacenes_canonicos > 0 else 1  # hueco si no hay catálogo

        resultados.append(cov)

    return {
        "modo": "DRY_RUN (cero escritura)",
        "producto_catalogo_actual": producto_catalogo_actual,
        "tipos_movimiento_canonicos": tipos_canonicos,
        "unidades": [c.__dict__ for c in resultados],
    }


def canonizar_productos(dry_run: bool = True) -> Dict:
    """
    Punto de entrada de canonización. BLOQUEADO en escritura: si dry_run=False
    lanza error hasta que exista el puente aprobado + rollback.
    """
    if not dry_run:
        raise RuntimeError(
            "Canonización en escritura BLOQUEADA: requiere puente 'Producto_MapeoOrigen' "
            "aprobado (DDL + rollback). Ejecutar solo en dry_run hasta autorización."
        )
    return calcular_cobertura_dry_run()


__all__ = ["calcular_cobertura_dry_run", "canonizar_productos", "CoberturaUnidad"]
