"""
EDARSA HUB - API Administrativa: Calidad de Datos
==================================================
Herramientas para auditar y consolidar datos duplicados o inconsistentes.

CASO ACTUAL: DATA-QUALITY-130MID-001
- Problema: "130° MERIDA" vs "130° MÉRIDA" (con/sin acento)
- Causa: Sincronizaciones históricas usaron nombre con acento
- Solución: Unificar al nombre canónico actual (sin acento)

MÁXIMAS CUMPLIDAS:
- SQL-First: Todo en EDARSAHUB SQL Server
- NO MongoDB
- Trazabilidad: Logs detallados de auditoría
- Idempotente: Scripts generados son seguros de re-ejecutar

NOTA: El usuario HRLectura es de solo lectura.
Los scripts UPDATE deben ejecutarse con credenciales de escritura.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any, List
import logging
import os

from core.security import get_current_user
from core.db import execute_sql_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/data-quality", tags=["Admin - Data Quality"])


# =============================================================================
# CONFIGURACIÓN EDARSAHUB (lectura)
# =============================================================================

def _get_edarsahub_config():
    """Obtiene configuración de EDARSAHUB desde variables de entorno."""
    return {
        'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
        'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        'password': os.environ.get('EDARSAHUB_PASSWORD', '')
    }


def _execute_readonly_query(query: str) -> List[Dict]:
    """Ejecuta query de SOLO LECTURA contra EDARSAHUB."""
    cfg = _get_edarsahub_config()
    try:
        result = execute_sql_query(
            cfg['host'],
            cfg['port'],
            cfg['database'],
            cfg['username'],
            cfg['password'],
            query
        )
        return result or []
    except Exception as e:
        logger.error(f"[DATA-QUALITY] Error ejecutando query: {e}")
        raise HTTPException(status_code=500, detail=f"Error SQL: {str(e)}")


# =============================================================================
# MODELOS
# =============================================================================

class DuplicateAuditResponse(BaseModel):
    """Respuesta de auditoría de duplicados."""
    issue_id: str
    description: str
    affected_table: str
    canonical_value: str
    duplicate_values: List[str]
    summary: Dict[str, Any]
    details: List[Dict[str, Any]]
    consolidation_script: str
    script_notes: str


class ConsolidationPreviewResponse(BaseModel):
    """Vista previa de consolidación."""
    issue_id: str
    records_to_update: int
    preview_sample: List[Dict[str, Any]]
    sql_script: str
    instructions: str


# =============================================================================
# ENDPOINTS: AUDITORÍA DE DUPLICADOS
# =============================================================================

@router.get("/audit/merida-duplicates", response_model=DuplicateAuditResponse)
async def audit_merida_duplicates(
    current_user: dict = Depends(get_current_user)
):
    """
    Audita los duplicados de Mérida por variantes de acento.
    
    Issue: DATA-QUALITY-130MID-001
    Problema: "130° MERIDA" vs "130° MÉRIDA"
    """
    
    # Query para obtener resumen de duplicados
    summary_query = """
    SELECT 
        unidad_negocio_id,
        unidad_negocio_nombre,
        MIN(fecha_operacion) as primera_fecha,
        MAX(fecha_operacion) as ultima_fecha,
        COUNT(*) as total_registros,
        SUM(ventas_total) as total_ventas
    FROM Comercial_KPIs_Diarios_v2 
    WHERE unidad_negocio_id = '130MID'
    GROUP BY unidad_negocio_id, unidad_negocio_nombre
    ORDER BY unidad_negocio_nombre
    """
    
    # Query para obtener el nombre canónico oficial
    canonical_query = """
    SELECT codigo, nombre
    FROM Unidades_Negocio 
    WHERE codigo = '130MID' AND activo = 1
    """
    
    # Ejecutar queries
    summary_results = _execute_readonly_query(summary_query)
    canonical_results = _execute_readonly_query(canonical_query)
    
    if not canonical_results:
        raise HTTPException(status_code=404, detail="No se encontró la unidad canónica 130MID")
    
    canonical_name = canonical_results[0]['nombre']
    
    # Procesar resultados
    duplicate_values = []
    total_to_fix = 0
    details = []
    
    for row in summary_results:
        nombre = row['unidad_negocio_nombre']
        registros = row['total_registros']
        
        # Convertir fecha a string para serialización
        primera = row['primera_fecha']
        ultima = row['ultima_fecha']
        
        detail = {
            'nombre': nombre,
            'es_canonico': nombre == canonical_name,
            'registros': registros,
            'primera_fecha': str(primera) if primera else None,
            'ultima_fecha': str(ultima) if ultima else None,
            'ventas_total': float(row['total_ventas'] or 0)
        }
        details.append(detail)
        
        if nombre != canonical_name:
            duplicate_values.append(nombre)
            total_to_fix += registros
    
    # Generar script de consolidación
    consolidation_script = f"""
-- ===========================================================================
-- SCRIPT DE CONSOLIDACIÓN: DATA-QUALITY-130MID-001
-- ===========================================================================
-- Descripción: Unifica variantes de nombre de Mérida al valor canónico
-- Ejecutar con: Usuario con permisos de escritura en EDARSAHUB
-- ===========================================================================

-- PASO 1: BACKUP (crear tabla temporal con los registros afectados)
SELECT *
INTO #Backup_130MID_PreFix_{datetime.now().strftime('%Y%m%d_%H%M%S')}
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = '130MID'
  AND unidad_negocio_nombre != '{canonical_name}';

-- Verificar registros a actualizar
SELECT 'Registros a actualizar:' as info, COUNT(*) as total
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = '130MID'
  AND unidad_negocio_nombre != '{canonical_name}';

-- PASO 2: ACTUALIZACIÓN
UPDATE Comercial_KPIs_Diarios_v2
SET 
    unidad_negocio_nombre = '{canonical_name}',
    fecha_ultima_actualizacion = GETDATE(),
    version = ISNULL(version, 0) + 1
WHERE unidad_negocio_id = '130MID'
  AND unidad_negocio_nombre != '{canonical_name}';

-- PASO 3: VERIFICACIÓN
SELECT 
    unidad_negocio_nombre,
    COUNT(*) as registros
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = '130MID'
GROUP BY unidad_negocio_nombre;

-- Si todo está correcto, el resultado debe mostrar SOLO "{canonical_name}"
"""
    
    return DuplicateAuditResponse(
        issue_id="DATA-QUALITY-130MID-001",
        description="Duplicados de Mérida por variantes de acento en unidad_negocio_nombre",
        affected_table="Comercial_KPIs_Diarios_v2",
        canonical_value=canonical_name,
        duplicate_values=duplicate_values,
        summary={
            "total_registros_afectados": total_to_fix,
            "variantes_encontradas": len(duplicate_values),
            "nombre_canonico": canonical_name
        },
        details=details,
        consolidation_script=consolidation_script,
        script_notes=(
            "IMPORTANTE: Este script debe ejecutarse con un usuario que tenga permisos "
            "de escritura en EDARSAHUB (no HRLectura). El script incluye backup automático "
            "y es idempotente (seguro de re-ejecutar)."
        )
    )


@router.get("/audit/generic-duplicates")
async def audit_generic_duplicates(
    column: str = "unidad_negocio_nombre",
    table: str = "Comercial_KPIs_Diarios_v2",
    group_by: str = "unidad_negocio_id",
    current_user: dict = Depends(get_current_user)
):
    """
    Auditoría genérica para encontrar duplicados por variantes de texto.
    Útil para identificar problemas de acentos, mayúsculas, etc.
    """
    
    # Sanitizar inputs (básico)
    allowed_tables = ['Comercial_KPIs_Diarios_v2', 'Unidades_Negocio']
    if table not in allowed_tables:
        raise HTTPException(status_code=400, detail=f"Tabla no permitida: {table}")
    
    query = f"""
    SELECT 
        {group_by},
        {column},
        COUNT(*) as registros
    FROM {table}
    GROUP BY {group_by}, {column}
    HAVING COUNT(*) > 0
    ORDER BY {group_by}, {column}
    """
    
    results = _execute_readonly_query(query)
    
    # Agrupar por ID para detectar variantes
    grouped = {}
    for row in results:
        key = row[group_by]
        if key not in grouped:
            grouped[key] = []
        grouped[key].append({
            'valor': row[column],
            'registros': row['registros']
        })
    
    # Filtrar solo los que tienen múltiples variantes
    duplicates = {k: v for k, v in grouped.items() if len(v) > 1}
    
    return {
        "table": table,
        "column": column,
        "group_by": group_by,
        "total_groups_with_duplicates": len(duplicates),
        "duplicates": duplicates
    }


# =============================================================================
# ENDPOINTS: VERIFICACIÓN POST-FIX
# =============================================================================

@router.get("/verify/merida-consolidation")
async def verify_merida_consolidation(
    current_user: dict = Depends(get_current_user)
):
    """
    Verifica si la consolidación de Mérida se ejecutó correctamente.
    Retorna el estado actual de los datos.
    """
    
    query = """
    SELECT 
        unidad_negocio_id,
        unidad_negocio_nombre,
        COUNT(*) as registros,
        MIN(fecha_operacion) as desde,
        MAX(fecha_operacion) as hasta
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '130MID'
    GROUP BY unidad_negocio_id, unidad_negocio_nombre
    """
    
    results = _execute_readonly_query(query)
    
    # Obtener nombre canónico
    canonical_query = """
    SELECT nombre FROM Unidades_Negocio WHERE codigo = '130MID' AND activo = 1
    """
    canonical_results = _execute_readonly_query(canonical_query)
    canonical_name = canonical_results[0]['nombre'] if canonical_results else 'DESCONOCIDO'
    
    # Evaluar estado
    variantes = len(results)
    is_consolidated = variantes == 1 and results[0]['unidad_negocio_nombre'] == canonical_name
    
    status = "CONSOLIDADO" if is_consolidated else "PENDIENTE"
    
    return {
        "issue_id": "DATA-QUALITY-130MID-001",
        "status": status,
        "canonical_name": canonical_name,
        "current_state": [
            {
                "nombre": r['unidad_negocio_nombre'],
                "registros": r['registros'],
                "desde": str(r['desde']) if r['desde'] else None,
                "hasta": str(r['hasta']) if r['hasta'] else None,
                "es_canonico": r['unidad_negocio_nombre'] == canonical_name
            }
            for r in results
        ],
        "variantes_encontradas": variantes,
        "mensaje": (
            "La consolidación está completa. Todos los registros usan el nombre canónico."
            if is_consolidated else
            f"Aún hay {variantes} variantes. Ejecute el script de consolidación con credenciales de escritura."
        )
    }
