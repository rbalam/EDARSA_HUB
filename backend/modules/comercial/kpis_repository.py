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


def init_kpis_repository(database) -> None:
    """Inicializa el repositorio con la conexión a MongoDB."""
    global _db
    _db = database


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("KPIs repository not initialized. Call init_kpis_repository(db) first.")
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

async def upsert_kpi_comercial(
    server_id: str,
    empresa_id: str,
    sucursal_id: str,
    fecha: str,  # YYYY-MM-DD
    kpis: dict,
    source_info: dict,
    updated_by: str = "scheduler",
    metadata: Optional[dict] = None,
    force_update: bool = False
) -> dict:
    """
    UPSERT idempotente de KPI comercial.
    
    Reglas:
    1. Si no existe: INSERT con version=1, estado=ABIERTO
    2. Si existe y hay cambios: UPDATE con version+1 y guardar snapshot
    3. Si existe y NO hay cambios: NO hacer nada (idempotente)
    4. Si período está RECONCILIADO: Rechazar update (requiere reapertura manual)
    5. Si período está CERRADO y no es SYNC-N: Solo actualizar si force_update=True
    
    Args:
        server_id: UUID del servidor origen
        empresa_id: UUID de la empresa EDARSA
        sucursal_id: Código de sucursal en sistema origen
        fecha: Fecha en formato YYYY-MM-DD
        kpis: Diccionario con KPIs (ventas, pax, cheques, etc.)
        source_info: Información de origen (type, query_timestamp, etc.)
        updated_by: Identificador del proceso que actualiza
        metadata: Datos adicionales (sucursal_nombre, empresa_nombre, etc.)
        force_update: Forzar actualización en estado CERRADO
    
    Returns:
        dict con {
            action: "INSERT" | "UPDATE" | "SKIP" | "REJECTED",
            version: int,
            reason: str (opcional)
        }
    """
    db = get_db()
    now = _get_utc_now()
    
    filter_key = _build_filter_key(server_id, empresa_id, sucursal_id, fecha)
    
    # Buscar documento existente
    existing = await db[COLLECTION_NAME].find_one(filter_key)
    
    # ========================================
    # CASO 1: No existe - INSERT
    # ========================================
    if not existing:
        new_doc = {
            **filter_key,
            # Identificadores auxiliares
            "sucursal_nombre": metadata.get("sucursal_nombre", "") if metadata else "",
            "empresa_nombre": metadata.get("empresa_nombre", "") if metadata else "",
            "unidad_negocio_id": metadata.get("unidad_negocio_id") if metadata else None,
            "system_type": metadata.get("system_type", "") if metadata else "",
            # Estado
            "estado_periodo": ESTADO_ABIERTO,
            "estado_transiciones": [{
                "de": None,
                "a": ESTADO_ABIERTO,
                "timestamp": now,
                "motivo": "Creación inicial"
            }],
            # KPIs
            "kpis": kpis,
            # Origen
            "source": source_info,
            # Auditoría
            "created_at": now,
            "created_by": updated_by,
            "updated_at": now,
            "updated_by": updated_by,
            "version": 1,
            "versions": [],
            # Flags
            "flags": {
                "tiene_corte_z": False,
                "requiere_reconciliacion": False,
                "datos_incompletos": False,
                "excluir_de_reportes": False,
                "alerta_diferencia_mayor_5pct": False
            }
        }
        
        try:
            await db[COLLECTION_NAME].insert_one(new_doc)
            logging.info(f"[KPI-UPSERT] INSERT: {filter_key}")
            return {"action": "INSERT", "version": 1}
        except Exception as e:
            # Posible race condition - intentar update
            if "duplicate key" in str(e).lower():
                logging.warning("[KPI-UPSERT] Race condition detectada, reintentando como UPDATE")
                existing = await db[COLLECTION_NAME].find_one(filter_key)
            else:
                raise
    
    # ========================================
    # CASO 2: Existe pero está RECONCILIADO - RECHAZAR
    # ========================================
    estado_actual = existing.get("estado_periodo", ESTADO_ABIERTO)
    
    if estado_actual == ESTADO_RECONCILIADO:
        logging.warning(
            f"[KPI-UPSERT] REJECTED - Período RECONCILIADO: {filter_key}"
        )
        return {
            "action": "REJECTED", 
            "version": existing.get("version", 1), 
            "reason": "Período RECONCILIADO - requiere reapertura manual"
        }
    
    # ========================================
    # CASO 3: Existe y está CERRADO - Solo SYNC-N o force_update
    # ========================================
    if estado_actual == ESTADO_CERRADO and not force_update:
        # Solo permitir actualización si es SYNC-N explícito
        if updated_by not in ["scheduler_sync_n", "reconciliacion", "admin_manual"]:
            logging.info(
                f"[KPI-UPSERT] SKIP - Período CERRADO y no es SYNC-N: {filter_key}"
            )
            return {
                "action": "SKIP", 
                "version": existing.get("version", 1),
                "reason": "Período CERRADO - solo actualizable por SYNC-N"
            }
    
    # ========================================
    # CASO 4: Verificar si hay cambios significativos
    # ========================================
    existing_kpis = existing.get("kpis", {})
    has_changes = _detect_kpi_changes(existing_kpis, kpis)
    
    if not has_changes:
        logging.debug(f"[KPI-UPSERT] SKIP - Sin cambios significativos: {filter_key}")
        return {"action": "SKIP", "version": existing.get("version", 1)}
    
    # ========================================
    # CASO 5: Hay cambios - UPDATE con historial
    # ========================================
    new_version = existing.get("version", 1) + 1
    diff = _calculate_diff(existing_kpis, kpis)
    
    # Crear snapshot de versión anterior
    version_snapshot = {
        "version": existing.get("version", 1),
        "timestamp": existing.get("updated_at", now),
        "updated_by": existing.get("updated_by", "unknown"),
        "source_type": existing.get("source", {}).get("type", "UNKNOWN"),
        "kpis_snapshot": {k: v for k, v in existing_kpis.items() if k in diff},  # Solo campos que cambiaron
        "reason": f"Actualización por {updated_by}",
        "diff": diff
    }
    
    # Determinar si requiere reconciliación (cambio > 5%)
    requires_reconciliation = False
    ventas_old = existing_kpis.get("ventas", 0) or 0
    ventas_new = kpis.get("ventas", 0) or 0
    if ventas_old > 0:
        ventas_diff_pct = abs((ventas_new - ventas_old) / ventas_old) * 100
        requires_reconciliation = ventas_diff_pct > 5.0
    
    update_doc = {
        "$set": {
            "kpis": kpis,
            "source": source_info,
            "updated_at": now,
            "updated_by": updated_by,
            "version": new_version,
            "flags.requiere_reconciliacion": requires_reconciliation,
            "flags.alerta_diferencia_mayor_5pct": requires_reconciliation
        },
        "$push": {
            "versions": {
                "$each": [version_snapshot],
                "$slice": -MAX_EMBEDDED_VERSIONS  # Mantener últimas N versiones
            }
        }
    }
    
    # Actualizar metadatos si se proporcionan
    if metadata:
        if metadata.get("sucursal_nombre"):
            update_doc["$set"]["sucursal_nombre"] = metadata["sucursal_nombre"]
        if metadata.get("empresa_nombre"):
            update_doc["$set"]["empresa_nombre"] = metadata["empresa_nombre"]
        if metadata.get("system_type"):
            update_doc["$set"]["system_type"] = metadata["system_type"]
    
    await db[COLLECTION_NAME].update_one(filter_key, update_doc)
    
    logging.info(
        f"[KPI-UPSERT] UPDATE v{new_version}: {filter_key}, "
        f"cambios={len(diff)} campos, reconciliacion={requires_reconciliation}"
    )
    
    return {"action": "UPDATE", "version": new_version}


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
    Cambia el estado del período con validaciones.
    
    Args:
        server_id, empresa_id, sucursal_id, fecha: Clave del documento
        nuevo_estado: ABIERTO | CERRADO | RECONCILIADO
        motivo: Razón del cambio
        updated_by: Identificador del proceso
    
    Returns:
        Tuple (success: bool, message: str)
    """
    db = get_db()
    filter_key = _build_filter_key(server_id, empresa_id, sucursal_id, fecha)
    
    existing = await db[COLLECTION_NAME].find_one(filter_key)
    if not existing:
        return False, "Documento no encontrado"
    
    estado_actual = existing.get("estado_periodo", ESTADO_ABIERTO)
    
    # Validar transición permitida
    if nuevo_estado not in TRANSICIONES_VALIDAS.get(estado_actual, []):
        return False, f"Transición no válida: {estado_actual} → {nuevo_estado}"
    
    now = _get_utc_now()
    
    transicion = {
        "de": estado_actual,
        "a": nuevo_estado,
        "timestamp": now,
        "motivo": motivo
    }
    
    await db[COLLECTION_NAME].update_one(
        filter_key,
        {
            "$set": {
                "estado_periodo": nuevo_estado,
                "updated_at": now,
                "updated_by": updated_by
            },
            "$push": {
                "estado_transiciones": transicion
            }
        }
    )
    
    logging.info(f"[KPI-ESTADO] {estado_actual} → {nuevo_estado}: {filter_key}")
    return True, f"Estado cambiado a {nuevo_estado}"


async def get_kpi_comercial(
    server_id: str,
    empresa_id: str,
    sucursal_id: str,
    fecha: str
) -> Optional[dict]:
    """Obtiene un documento KPI por su clave."""
    db = get_db()
    filter_key = _build_filter_key(server_id, empresa_id, sucursal_id, fecha)
    doc = await db[COLLECTION_NAME].find_one(filter_key, {"_id": 0})
    return doc


async def get_kpis_by_empresa_rango(
    empresa_id: str,
    fecha_inicio: str,
    fecha_fin: str,
    excluir_reportes: bool = True
) -> List[dict]:
    """
    Obtiene KPIs de una empresa en un rango de fechas.
    Usado por el Tablero Ejecutivo.
    """
    db = get_db()
    
    query = {
        "empresa_id": empresa_id,
        "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
    }
    
    if excluir_reportes:
        query["flags.excluir_de_reportes"] = {"$ne": True}
    
    cursor = db[COLLECTION_NAME].find(query, {"_id": 0}).sort("fecha", -1)
    return await cursor.to_list(1000)


async def get_kpis_by_server_rango(
    server_id: str,
    fecha_inicio: str,
    fecha_fin: str
) -> List[dict]:
    """
    Obtiene KPIs de un servidor en un rango de fechas.
    Usado por schedulers de sincronización.
    """
    db = get_db()
    
    query = {
        "server_id": server_id,
        "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
    }
    
    cursor = db[COLLECTION_NAME].find(query, {"_id": 0}).sort("fecha", -1)
    return await cursor.to_list(1000)


async def get_pendientes_reconciliacion(
    fecha_limite: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """
    Obtiene documentos pendientes de reconciliación.
    """
    db = get_db()
    
    query = {
        "estado_periodo": ESTADO_CERRADO,
        "flags.requiere_reconciliacion": True
    }
    
    if fecha_limite:
        query["fecha"] = {"$lte": fecha_limite}
    
    cursor = db[COLLECTION_NAME].find(query, {"_id": 0}).sort("fecha", 1).limit(limit)
    return await cursor.to_list(limit)


async def cerrar_periodos_anteriores(
    fecha_corte: str,
    updated_by: str = "scheduler_sync_n"
) -> int:
    """
    Cierra períodos ABIERTOS anteriores a la fecha de corte.
    
    Args:
        fecha_corte: Fecha límite (YYYY-MM-DD), los días anteriores se cierran
        updated_by: Identificador del proceso
    
    Returns:
        Cantidad de documentos actualizados
    """
    db = get_db()
    now = _get_utc_now()
    
    result = await db[COLLECTION_NAME].update_many(
        {
            "estado_periodo": ESTADO_ABIERTO,
            "fecha": {"$lt": fecha_corte}
        },
        {
            "$set": {
                "estado_periodo": ESTADO_CERRADO,
                "updated_at": now,
                "updated_by": updated_by
            },
            "$push": {
                "estado_transiciones": {
                    "de": ESTADO_ABIERTO,
                    "a": ESTADO_CERRADO,
                    "timestamp": now,
                    "motivo": f"Cierre automático por SYNC-N (corte: {fecha_corte})"
                }
            }
        }
    )
    
    if result.modified_count > 0:
        logging.info(f"[KPI-CIERRE] Cerrados {result.modified_count} períodos anteriores a {fecha_corte}")
    
    return result.modified_count


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
