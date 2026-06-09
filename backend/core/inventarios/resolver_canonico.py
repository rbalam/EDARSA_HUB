"""
EDARSA HUB - Resolver Canónico Centralizado (Inventarios / Catálogos)
=====================================================================
Capa COMÚN y reutilizable para resolver identificadores de ORIGEN (POS) hacia
los identificadores CANÓNICOS int de EDARSAHUB. NO vive dentro de ningún job.

REGLAS DE ARQUITECTURA (Ruta B - int estricta):
- Interfaz pública por (unidad_canonica, sistema_origen, codigo_origen).
- ServerID NO es dimensión operativa expuesta: se usa SOLO como llave interna de
  JOIN mientras `Sync_Productos*` no tenga `UnidadNegocioID` poblado.
- NUNCA inventa IDs. Si no resuelve -> None (el llamador lo manda a PENDIENTES;
  descartados = 0).
- SOLO LECTURA. Sin DDL. Sin hardcode de clasificaciones (los tipos de movimiento
  se leen de la tabla canónica `Inventario_TipoMovimiento`).

ESTADO ACTUAL (documentado, ver auditoría):
- El puente POS->ProductoID(int) (`Producto_MapeoOrigen`) NO existe todavía (pendiente
  de aprobación DDL). Mientras no exista, `resolver_producto_id` devuelve None con
  motivo 'BRIDGE_AUSENTE'. La lógica queda lista para activarse cuando el puente exista.
- `resolver_almacen_id` y `resolver_sucursal_id` ya operan contra tablas canónicas
  pobladas (`Inventario_Almacenes`, `Sistema_SucursalServidorMapeo`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Dict

from core.sql_first.db import get_sql_connection
from core.server_registry import get_server_by_unidad_codigo

logger = logging.getLogger(__name__)

# Nombre de la tabla puente propuesta (aún NO creada; pendiente de aprobación DDL).
BRIDGE_TABLE = "Producto_MapeoOrigen"


@dataclass
class ResultadoResolucion:
    """Resultado homologado de una resolución canónica."""
    resuelto: bool
    canonical_id: Optional[int]
    motivo: str  # OK | PENDIENTE_SIN_MAPEO | BRIDGE_AUSENTE | UNIDAD_DESCONOCIDA | SIN_DIMENSION

    @classmethod
    def ok(cls, cid: int) -> "ResultadoResolucion":
        return cls(True, int(cid), "OK")

    @classmethod
    def pendiente(cls, motivo: str) -> "ResultadoResolucion":
        return cls(False, None, motivo)


# ---------------------------------------------------------------------------
# Utilidades internas (cacheadas en proceso)
# ---------------------------------------------------------------------------

def _tabla_existe(nombre: str) -> bool:
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = %s",
        (nombre,),
    )
    return cur.fetchone()[0] > 0


def _server_id_de_unidad(unidad_codigo: str) -> Optional[str]:
    """Traduce la unidad canónica -> ServerID (llave de JOIN interna, no operativa)."""
    if not unidad_codigo:
        return None
    unidad = get_server_by_unidad_codigo(unidad_codigo)
    if not unidad:
        return None
    return unidad.get("server_id") or unidad.get("id")


# ---------------------------------------------------------------------------
# Resolución de PRODUCTO (POS -> ProductoID int)
# ---------------------------------------------------------------------------

def resolver_producto_id(unidad_codigo: str, sistema_origen: str, codigo_origen: str) -> ResultadoResolucion:
    """
    Resuelve el ProductoID canónico (int) a partir de la unidad canónica, el sistema
    de origen y el código de origen del POS.

    Depende del puente `Producto_MapeoOrigen` (ServerID, SystemType, CodigoFuente -> ProductoID).
    Mientras el puente no exista, devuelve PENDIENTE con motivo 'BRIDGE_AUSENTE'.
    """
    server_id = _server_id_de_unidad(unidad_codigo)
    if not server_id:
        return ResultadoResolucion.pendiente("UNIDAD_DESCONOCIDA")

    if not _tabla_existe(BRIDGE_TABLE):
        return ResultadoResolucion.pendiente("BRIDGE_AUSENTE")

    codigo = str(codigo_origen or "").strip()
    if not codigo:
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(
        f"""SELECT TOP 1 ProductoID FROM {BRIDGE_TABLE}
            WHERE ServerID = %s AND SystemType = %s AND CodigoFuente = %s AND Activo = 1""",
        (str(server_id), str(sistema_origen or "").upper(), codigo),
    )
    row = cur.fetchone()
    if row and row[0] is not None:
        return ResultadoResolucion.ok(row[0])
    return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")


# ---------------------------------------------------------------------------
# Resolución de ALMACÉN (POS -> AlmacenID int)
# ---------------------------------------------------------------------------

def resolver_almacen_id(empresa_id: int, sucursal_id: int, codigo_almacen: str) -> ResultadoResolucion:
    """Resuelve AlmacenID canónico desde `Inventario_Almacenes` por código + empresa/sucursal."""
    codigo = str(codigo_almacen or "").strip()
    if not codigo or empresa_id is None or sucursal_id is None:
        return ResultadoResolucion.pendiente("SIN_DIMENSION")

    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT TOP 1 AlmacenID FROM Inventario_Almacenes
           WHERE EmpresaID = %s AND SucursalID = %s AND CodigoAlmacen = %s AND Activo = 1""",
        (int(empresa_id), int(sucursal_id), codigo),
    )
    row = cur.fetchone()
    if row and row[0] is not None:
        return ResultadoResolucion.ok(row[0])
    return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")


# ---------------------------------------------------------------------------
# Resolución de SUCURSAL (ServerID + sucursal_origen -> SucursalID int)
# ---------------------------------------------------------------------------

def resolver_sucursal_id(servidor_id: str, sucursal_origen_id: Optional[str] = None) -> ResultadoResolucion:
    """
    Resuelve SucursalID canónico desde `Sistema_SucursalServidorMapeo`.
    Si el servidor aloja varias sucursales y no se entrega `sucursal_origen_id`,
    devuelve PENDIENTE (ambiguo) en lugar de adivinar.
    """
    if not servidor_id:
        return ResultadoResolucion.pendiente("SIN_DIMENSION")

    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        """SELECT SucursalID, SucursalOrigenID FROM Sistema_SucursalServidorMapeo
           WHERE ServidorID = %s AND Activo = 1""",
        (str(servidor_id),),
    )
    filas = cur.fetchall()
    if not filas:
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    if sucursal_origen_id:
        for f in filas:
            if str(f.get("SucursalOrigenID") or "") == str(sucursal_origen_id):
                return ResultadoResolucion.ok(f["SucursalID"])
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    if len(filas) == 1:
        return ResultadoResolucion.ok(filas[0]["SucursalID"])

    # Servidor con múltiples sucursales y sin origen: no adivinar.
    return ResultadoResolucion.pendiente("AMBIGUO_MULTISUCURSAL")


# ---------------------------------------------------------------------------
# Resolución de TIPO DE MOVIMIENTO (DB-driven, sin hardcode de clasificación)
# ---------------------------------------------------------------------------

def resolver_tipo_movimiento_por_codigo(codigo_canonico: str) -> ResultadoResolucion:
    """
    Resuelve TipoMovimientoID desde la tabla canónica `Inventario_TipoMovimiento`
    por su Código canónico (p.ej. 'ENTRADA_COMPRA'). DB-driven: cero hardcode.

    NOTA: El puente concepto-POS (EPC/SPC...) -> Código canónico se resolverá en
    Sub-fase B mediante un catálogo DB-driven de conceptos, NO con un dict en código.
    """
    codigo = str(codigo_canonico or "").strip().upper()
    if not codigo:
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 TipoMovimientoID FROM Inventario_TipoMovimiento WHERE Codigo = %s AND Activo = 1",
        (codigo,),
    )
    row = cur.fetchone()
    if row and row[0] is not None:
        return ResultadoResolucion.ok(row[0])
    return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")


__all__ = [
    "ResultadoResolucion",
    "resolver_producto_id",
    "resolver_almacen_id",
    "resolver_sucursal_id",
    "resolver_tipo_movimiento_por_codigo",
    "BRIDGE_TABLE",
]
