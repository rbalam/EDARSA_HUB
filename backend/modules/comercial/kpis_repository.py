from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Repository para KPIs Consolidados (MACROFASE 2)
============================================================

Funciones de acceso a datos para la colección `kpis_comercial`.

REGLAS OBLIGATORIAS:
- Todo UPSERT es idempotente
- No insertar duplicados bajo ninguna condición
- Respetar estados de período (ABIERTO, CERRADO, RECONCILIADO)
- Registrar trazabilidad completa de origen
- Mantener historial embebido limitado (max 10 versiones)

Fecha: 2026-04-22
Versión: 1.0
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
import logging
import hashlib
import json

# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# ============================================================================

_db = None


def init_kpis_repository(database=None) -> None:
    """
    DEPRECADO: MongoDB ya no se usa para KPIs.
    Los KPIs se leen directamente de EDARSAHUB SQL.
    """
    global _db
    _db = database
    import logging
    logging.warning("[COMERCIAL] KPIs repository - MongoDB deprecado")


def get_db():
    """
    DEPRECADO: MongoDB ya no se usa.
    Retorna None - las funciones deben manejar este caso gracefully.
    """
    if _db is None:
        import logging
        logging.debug("[COMERCIAL] KPIs get_db() - MongoDB deprecado, retornando None")
        return None
    return _db


# ============================================================================
# CONSTANTES
# ============================================================================

COLLECTION_NAME = "kpis_comercial"
MAX_EMBEDDED_VERSIONS = 10
CHANGE_THRESHOLD_PCT = 0.01  # 0.01% para considerar cambio significativo

# Estados de período válidos
ESTADO_ABIERTO = "ABIERTO"
ESTADO_CERRADO = "CERRADO"
ESTADO_RECONCILIADO = "RECONCILIADO"

# Transiciones válidas
TRANSICIONES_VALIDAS = {
    ESTADO_ABIERTO: [ESTADO_CERRADO],
    ESTADO_CERRADO: [ESTADO_RECONCILIADO, ESTADO_ABIERTO],
    ESTADO_RECONCILIADO: [ESTADO_CERRADO]  # Solo reapertura manual
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _detect_kpi_changes(old_kpis: dict, new_kpis: dict, threshold_pct: float = CHANGE_THRESHOLD_PCT) -> bool:
    """
    Detecta si hay cambios significativos entre KPIs.
    
    Args:
        old_kpis: KPIs existentes
        new_kpis: KPIs nuevos
        threshold_pct: Porcentaje mínimo para considerar cambio (default 0.01%)
    
    Returns:
        True si hay cambios significativos, False si no
    """
    if not old_kpis:
        return True  # Si no había datos previos, siempre es cambio
    
    for key in new_kpis:
        old_val = old_kpis.get(key, 0) or 0
        new_val = new_kpis.get(key, 0) or 0
        
        # Convertir a float para comparación
        try:
            old_val = float(old_val)
            new_val = float(new_val)
        except (TypeError, ValueError):
            # Si no son numéricos, comparar directamente
            if old_val != new_val:
                return True
            continue
        
        if old_val == 0 and new_val == 0:
            continue
        
        if old_val == 0 and new_val != 0:
            return True  # Cambio de 0 a algo
        
        diff_pct = abs((new_val - old_val) / old_val) * 100
        if diff_pct > threshold_pct:
            return True
    
    return False


def _calculate_diff(old_kpis: dict, new_kpis: dict) -> dict:
    """
    Calcula diferencias entre KPIs para auditoría.
    Solo incluye campos que cambiaron.
    """
    diff = {}
    all_keys = set(old_kpis.keys()) | set(new_kpis.keys())
    
    for key in all_keys:
        old_val = old_kpis.get(key, 0)
        new_val = new_kpis.get(key, 0)
        
        # Convertir a float para comparación numérica
        try:
            old_float = float(old_val or 0)
            new_float = float(new_val or 0)
            if abs(old_float - new_float) > 0.001:  # Pequeña tolerancia
                diff[key] = {"old": old_val, "new": new_val}
        except (TypeError, ValueError):
            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}
    
    return diff


def _build_filter_key(server_id: str, empresa_id: str, sucursal_id: str, fecha: str) -> dict:
    """Construye la clave de filtro para UPSERT."""
    return {
        "server_id": server_id,
        "empresa_id": empresa_id,
        "sucursal_id": str(sucursal_id),
        "fecha": fecha
    }


def _get_utc_now() -> str:
    """Obtiene timestamp UTC en formato ISO."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================


async def _sql_parse_date(fecha: str):
    from datetime import datetime
    return datetime.strptime(str(fecha), "%Y-%m-%d").date()


def _sql_decimal(value, default="0"):
    from decimal import Decimal
    return Decimal(str(value if value is not None else default))


def _sql_int(value, default=0):
    try:
        return int(value if value is not None else default)
    except Exception:
        return default


def _sql_build_hash(server_id: str, sucursal_id: str, fecha: str, kpis: dict) -> str:
    import hashlib
    payload = {
        "server_id": server_id,
        "sucursal_id": str(sucursal_id),
        "fecha": str(fecha),
        "ventas": str(kpis.get("ventas", kpis.get("ventas_total", 0)) or 0),
        "ventas_sin_propina": str(kpis.get("ventas_sin_propina", kpis.get("ventas", 0)) or 0),
        "propinas": str(kpis.get("propinas", kpis.get("propinas_total", 0)) or 0),
        "tickets": str(kpis.get("tickets", kpis.get("cheques", kpis.get("tickets_total", 0))) or 0),
        "pax": str(kpis.get("pax", kpis.get("pax_total", 0)) or 0),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:32]


def _sql_resolve_unidad_pk(server_id: str, empresa_id: str, metadata: Optional[dict]) -> str:
    metadata = metadata or {}
    return (
        metadata.get("unidad_negocio_pk")
        or metadata.get("unidad_negocio_id")
        or empresa_id
        or server_id
    )


def _sql_resolve_sistema(system_type: str):
    from modules.comercial_v2.schemas import SistemaOrigen
    st = (system_type or "").upper()
    if "MPRO" in st or "MANAG" in st:
        return SistemaOrigen.MPRO
    return SistemaOrigen.SOFTRESTAURANT


async def upsert_kpi_comercial(
    server_id: str,
    empresa_id: str,
    sucursal_id: str,
    fecha: str,
    kpis: dict,
    source_info: dict,
    updated_by: str = "scheduler",
    metadata: Optional[dict] = None,
    force_update: bool = False
) -> dict:
    """
    SQL-first wrapper conservando firma legacy.
    Escribe en dbo.Comercial_KPIs_Diarios_v2 mediante Comercial V2.
    No usa MongoDB.
    """
    from modules.comercial_v2.repository_comercial_edarsahub import upsert_kpi_diario
    from modules.comercial_v2.schemas import KPIsDiariosV2, FuenteOriginal

    metadata = metadata or {}
    fecha_op = await _sql_parse_date(fecha)

    unidad_negocio_pk = _sql_resolve_unidad_pk(server_id, empresa_id, metadata)
    unidad_nombre = metadata.get("empresa_nombre") or metadata.get("unidad_negocio_nombre") or unidad_negocio_pk
    sucursal_nombre = metadata.get("sucursal_nombre") or unidad_nombre
    sistema_origen = _sql_resolve_sistema(metadata.get("system_type") or source_info.get("system_type"))

    ventas_total = _sql_decimal(kpis.get("ventas_total", kpis.get("ventas", 0)))
    propinas_total = _sql_decimal(kpis.get("propinas_total", kpis.get("propinas", 0)))
    ventas_sin_propina = _sql_decimal(
        kpis.get("ventas_sin_propina", ventas_total - propinas_total)
    )

    tickets_total = _sql_int(kpis.get("tickets_total", kpis.get("tickets", kpis.get("cheques", 0))))
    pax_total = _sql_int(kpis.get("pax_total", kpis.get("pax", kpis.get("personas", 0))))

    ticket_promedio = ventas_sin_propina / tickets_total if tickets_total > 0 else _sql_decimal(0)
    pax_promedio = ventas_sin_propina / pax_total if pax_total > 0 else _sql_decimal(0)

    sync_run_id = source_info.get("scheduler_job_id") or source_info.get("agent_id") or updated_by
    hash_origen = _sql_build_hash(server_id, sucursal_id, fecha, kpis)

    kpi_v2 = KPIsDiariosV2(
        unidad_negocio_pk=str(unidad_negocio_pk),
        unidad_negocio_nombre=str(unidad_nombre),
        server_id=str(server_id),
        sucursal_id=str(sucursal_id or "DEFAULT"),
        sucursal_nombre=str(sucursal_nombre) if sucursal_nombre else None,
        sistema_origen=sistema_origen,
        fecha_operacion=fecha_op,
        anio=fecha_op.year,
        mes=fecha_op.month,
        dia=fecha_op.day,
        ventas_total=ventas_total,
        ventas_sin_propina=ventas_sin_propina,
        propinas_total=propinas_total,
        tickets_total=tickets_total,
        pax_total=pax_total,
        ticket_promedio=ticket_promedio,
        pax_promedio=pax_promedio,
        ventas_cerradas=_sql_decimal(kpis.get("ventas_cerradas", ventas_total)),
        ventas_abiertas=_sql_decimal(kpis.get("ventas_abiertas", 0)),
        total_estimado_dia=_sql_decimal(kpis.get("total_estimado_dia", ventas_total)),
        es_venta_abierta=False,
        es_corte_cerrado=True,
        es_demo=False,
        activo=True,
        fuente_original=FuenteOriginal.API_LOCAL if source_info.get("type") == "SYNC_AGENT" else FuenteOriginal.SQL_LIVE,
        id_origen=source_info.get("agent_id") or source_info.get("id_origen"),
        hash_origen=hash_origen,
        sync_run_id=str(sync_run_id),
    )

    result = upsert_kpi_diario(kpi_v2)
    action = result.get("action", "SKIP")
    return {
        "action": action,
        "version": result.get("version", 1),
        "id": result.get("id"),
        "source": "SQL_COMERCIAL_KPIS_DIARIOS_V2",
    }


async def cambiar_estado_periodo(
    server_id: str,
    empresa_id: str,
    sucursal_id: str,
    fecha: str,
    nuevo_estado: str,
    motivo: str,
    updated_by: str
) -> Tuple[bool, str]:
    """
    Compatibilidad legacy. Comercial_KPIs_Diarios_v2 no usa estado_periodo documental.
    """
    return False, "Estado de período legacy no aplica en SQL v2"


async def get_kpi_comercial(
    server_id: str,
    empresa_id: str,
    sucursal_id: str,
    fecha: str
) -> Optional[dict]:
    """Lee KPI desde vw_Comercial_KPIs_Diarios_v2_Runtime por server/sucursal/fecha."""
    from modules.comercial_v2.repository_comercial_edarsahub import _execute_query

    safe_server = str(server_id).replace("'", "''")
    safe_sucursal = str(sucursal_id or "DEFAULT").replace("'", "''")
    safe_fecha = str(fecha).replace("'", "''")

    rows = _execute_query(f"""
        SELECT TOP 1 *
        FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
        WHERE server_id = '{safe_server}'
          AND sucursal_id = '{safe_sucursal}'
          AND fecha_operacion = '{safe_fecha}'
          AND activo = 1
    """)
    if not rows:
        return None

    row = rows[0]
    return {
        **row,
        "version": row.get("version", 1),
        "kpis": {
            "ventas": row.get("ventas_sin_propina") or row.get("ventas_total") or 0,
            "ventas_total": row.get("ventas_total") or 0,
            "ventas_sin_propina": row.get("ventas_sin_propina") or 0,
            "propinas_total": row.get("propinas_total") or 0,
            "tickets_total": row.get("tickets_total") or 0,
            "pax_total": row.get("pax_total") or 0,
        },
    }


async def get_kpis_by_empresa_rango(
    empresa_id: str,
    fecha_inicio: str,
    fecha_fin: str,
    excluir_reportes: bool = True
) -> List[dict]:
    """Lee KPIs SQL por unidad_negocio_pk en rango."""
    from modules.comercial_v2.repository_comercial_edarsahub import _execute_query

    safe_empresa = str(empresa_id).replace("'", "''")
    safe_ini = str(fecha_inicio).replace("'", "''")
    safe_fin = str(fecha_fin).replace("'", "''")

    return _execute_query(f"""
        SELECT *
        FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
        WHERE unidad_negocio_pk = '{safe_empresa}'
          AND fecha_operacion BETWEEN '{safe_ini}' AND '{safe_fin}'
          AND activo = 1
        ORDER BY fecha_operacion DESC
    """)


async def get_kpis_by_server_rango(
    server_id: str,
    fecha_inicio: str,
    fecha_fin: str
) -> List[dict]:
    """Lee KPIs SQL por server_id en rango."""
    from modules.comercial_v2.repository_comercial_edarsahub import _execute_query

    safe_server = str(server_id).replace("'", "''")
    safe_ini = str(fecha_inicio).replace("'", "''")
    safe_fin = str(fecha_fin).replace("'", "''")

    return _execute_query(f"""
        SELECT *
        FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
        WHERE server_id = '{safe_server}'
          AND fecha_operacion BETWEEN '{safe_ini}' AND '{safe_fin}'
          AND activo = 1
        ORDER BY fecha_operacion DESC
    """)


async def get_pendientes_reconciliacion(
    fecha_limite: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """
    Compatibilidad legacy. Reconciliación documental no aplica en SQL v2.
    """
    return []


async def cerrar_periodos_anteriores(
    fecha_corte: str,
    updated_by: str = "scheduler_sync_n"
) -> int:
    """
    Compatibilidad legacy. SQL v2 no usa cierre documental de períodos.
    """
    logging.info(f"[KPI-CIERRE] SQL v2 no requiere cierre documental legacy. fecha_corte={fecha_corte}")
    return 0


# ============================================================================
# EXPORTACIONES
# ============================================================================

__all__ = [
    'init_kpis_repository',
    'get_db',
    'COLLECTION_NAME',
    'ESTADO_ABIERTO',
    'ESTADO_CERRADO',
    'ESTADO_RECONCILIADO',
    'upsert_kpi_comercial',
    'cambiar_estado_periodo',
    'get_kpi_comercial',
    'get_kpis_by_empresa_rango',
    'get_kpis_by_server_rango',
    'get_pendientes_reconciliacion',
    'cerrar_periodos_anteriores',
]
