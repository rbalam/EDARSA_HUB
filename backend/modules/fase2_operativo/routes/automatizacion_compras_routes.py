from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Routes de Automatización Operativa de Compras
==========================================================
Endpoints para el flujo: Pedido → Gerencia → Tesorería → Aprobado

FASE 4.1 y 4.2 - Diciembre 2025:
- Ejecución automática vía job scheduler
- Ejecución manual para pruebas
- Consulta de tareas operativas
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.rbac.middleware import require_permission, require_explicit_permission
from core.rbac_helper_sql import get_role_code
from ..db_utils import get_database
from modules.fase2_operativo.services.automatizacion_compras_service import (
    get_automatizacion_compras_service,
    EstadoAutomatizacion,
)

router = APIRouter(prefix="/automatizaciones/operativas", tags=["automatizaciones-operativas"])


def _get_authenticated_compras_actor(current_user: Dict) -> tuple[str, str, str]:
    """Deriva identidad real desde JWT/RBAC, no desde body ni rol hardcodeado."""
    usuario_id = str(
        current_user.get("id")
        or current_user.get("user_id")
        or current_user.get("sub")
        or current_user.get("email")
        or ""
    ).strip()
    usuario_nombre = str(current_user.get("email") or usuario_id).strip()
    usuario_rol = get_role_code(current_user)

    if not usuario_id:
        raise HTTPException(
            status_code=403,
            detail="No fue posible resolver identidad RBAC del usuario autenticado"
        )

    return usuario_id, usuario_nombre, usuario_rol


# ============================================================================
# SCHEMAS
# ============================================================================

class ProcesarPedidoRequest(BaseModel):
    pedido_id: str
    server_id: str
    sucursal_id: str
    sucursal_nombre: str
    almacen_id: str
    almacen_nombre: str
    productos: List[Dict]
    dias_objetivo: Optional[int] = 10
    origen_sistema: Optional[str] = "MPRO"


class AccionGerenciaRequest(BaseModel):
    """Acciones: aprobar, rechazar, ajuste"""
    accion: str  # "aprobar", "rechazar", "ajuste"
    comentario: Optional[str] = ""
    dias_objetivo: Optional[int] = None  # Solo para ajuste


class AccionTesoreriaRequest(BaseModel):
    """Acciones: aprobar, rechazar"""
    accion: str  # "aprobar", "rechazar"
    comentario: Optional[str] = ""


class ModificarDiasObjetivoRequest(BaseModel):
    dias_objetivo: int
    motivo: Optional[str] = ""


class ModificarParametrosConsumoRequest(BaseModel):
    """
    FASE 4.3: Modificar periodo estadístico y/o ajuste de consumo.
    
    Permite separar el periodo operativo (bloqueado) del periodo
    estadístico usado para calcular consumo promedio.
    """
    fecha_consumo_inicio: Optional[str] = None  # ISO format
    fecha_consumo_fin: Optional[str] = None     # ISO format
    porcentaje_ajuste: Optional[float] = None   # -100 a +500
    motivo: Optional[str] = ""


class EjecutarDetectorRequest(BaseModel):
    """Request para ejecución manual del detector."""
    empresa_id: Optional[str] = None  # Filtrar por empresa específica


# ============================================================================
# ENDPOINTS FASE 4.1 y 4.2 - DETECTOR DE PEDIDOS
# ============================================================================



# ============================================================================
# SQL-FIRST P2-A: automatización compras sin Mongo runtime
# ============================================================================

def _p2a_conn():
    from modules.compras.sync_service import get_edarsahub_connection
    return get_edarsahub_connection()


def _p2a_rows(sql, params=()):
    conn = _p2a_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        return cur.fetchall() or []
    finally:
        conn.close()


def _p2a_one(sql, params=()):
    rows = _p2a_rows(sql, params)
    return rows[0] if rows else None


def _p2a_exec(sql, params=()):
    conn = _p2a_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _p2a_json(obj):
    import json
    return json.dumps(obj or {}, ensure_ascii=False, default=str)


def _p2a_next_id(table, col="ID"):
    conn = _p2a_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(f"SELECT ISNULL(MAX({col}),0)+1 AS NextID FROM dbo.{table} WITH (UPDLOCK,HOLDLOCK)")
        row = cur.fetchone() or {}
        return int(row.get("NextID") or 1)
    finally:
        conn.close()


def _p2a_norm_tarea(r):
    if not r:
        return None
    return {
        **r,
        "id": r.get("TareaID"),
        "tarea_id": r.get("TareaID"),
        "automatizacion_id": r.get("AutomatizacionID"),
        "tipo_tarea": r.get("TipoTarea"),
        "titulo": r.get("Titulo"),
        "descripcion": r.get("Descripcion"),
        "estado": r.get("Estado"),
        "prioridad": r.get("Prioridad"),
        "fecha_creacion": r.get("FechaCreacion"),
        "fecha_limite": r.get("FechaLimite"),
        "fecha_completada": r.get("FechaCompletada"),
        "resultado": r.get("Resultado"),
    }


def _p2a_list_tareas(ctx):
    estado = ctx.get("estado")
    limit = int(ctx.get("limit") or 100)
    where = []
    params = []
    if estado:
        where.append("Estado=%s")
        params.append(estado)
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    rows = _p2a_rows(f"""
        SELECT TOP {limit} *
        FROM dbo.Operativo_TareasCompras
        {sql_where}
        ORDER BY FechaCreacion DESC
    """, tuple(params))
    return [_p2a_norm_tarea(r) for r in rows]


def _p2a_get_tarea(tarea_id):
    return _p2a_norm_tarea(_p2a_one("""
        SELECT TOP 1 * FROM dbo.Operativo_TareasCompras
        WHERE TareaID=%s
    """, (tarea_id,)))


def _p2a_completar_tarea(tarea_id, ctx):
    payload = ctx.get("payload") or ctx.get("body") or {}
    _p2a_exec("""
        UPDATE dbo.Operativo_TareasCompras
        SET Estado='COMPLETADA',
            FechaCompletada=GETUTCDATE(),
            Resultado=%s,
            MetadatosJSON=%s
        WHERE TareaID=%s
    """, (
        payload.get("resultado") or payload.get("comentario") or "Completada",
        _p2a_json(payload),
        tarea_id
    ))


def _p2a_asignar_tarea(tarea_id, ctx):
    target_usuario_id = ctx.get("usuario_id")
    target_usuario_nombre = ctx.get("usuario_nombre") or ctx.get("nombre") or target_usuario_id
    metadata = {
        "usuario_asignado_id": target_usuario_id,
        "usuario_asignado_nombre": target_usuario_nombre
    }
    _p2a_exec("""
        UPDATE dbo.Operativo_TareasCompras
        SET UsuarioAsignadoID=%s,
            UsuarioAsignadoNombre=%s,
            Estado=CASE WHEN Estado IS NULL OR Estado='PENDIENTE' THEN 'ASIGNADA' ELSE Estado END,
            MetadatosJSON=%s
        WHERE TareaID=%s
    """, (
        target_usuario_id,
        target_usuario_nombre,
        _p2a_json(metadata),
        tarea_id
    ))


def _p2a_list_bitacora(ctx):
    limit = int(ctx.get("limit") or 100)
    return _p2a_rows(f"""
        SELECT TOP {limit} *
        FROM dbo.Operativo_BitacoraCompras
        ORDER BY Fecha DESC
    """)


def _p2a_list_pedidos(ctx):
    limit = int(ctx.get("limit") or 100)
    return _p2a_rows(f"""
        SELECT TOP {limit} *
        FROM dbo.Operativo_PedidosProcesados
        ORDER BY FechaProcesamiento DESC
    """)



def _p2a_ultimo_scheduler_log():
    try:
        return _p2a_one("""
            SELECT TOP 1 *
            FROM dbo.Scheduler_BitacoraJobs
            ORDER BY ID DESC
        """) or {}
    except Exception:
        return {}

@router.post("/compras/detector/ejecutar")
async def ejecutar_detector_manual(
    request: EjecutarDetectorRequest = None,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_EJECUTAR"))
):
    """
    FASE 4.1 y 4.2: Ejecuta el detector de pedidos manualmente.
    
    Útil para pruebas y validación. Ejecuta el mismo flujo que el job automático.
    
    - Si se proporciona empresa_id, solo procesa esa empresa
    - Si no, procesa todas las empresas activas
    """
    _get_authenticated_compras_actor(current_user)
    
    # Obtener db async desde el scheduler manager
    from core.scheduler.scheduler_manager import get_scheduler_manager
    from core.scheduler.jobs.pedidos_detector_job import ejecutar_detector_manual as _ejecutar
    
    manager = get_scheduler_manager()
    db_async = manager.db  # Conexión async de MongoDB
    
    empresa_id = request.empresa_id if request else None
    
    try:
        resultado = await _ejecutar(db_async, empresa_id)
        return {
            "success": True,
            "mensaje": "Detector ejecutado correctamente",
            "estadisticas": resultado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compras/detector/estado")
async def obtener_estado_detector(
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """
    Obtiene el estado actual del detector de pedidos.
    
    Incluye última ejecución y próxima programada.
    """
    from core.scheduler.scheduler_manager import get_scheduler_manager
    from ..db_utils import get_database
    
    db = get_database()
    
    # Obtener última ejecución
    ultima = _p2a_ultimo_scheduler_log()
    
    # Obtener estado del job
    try:
        manager = get_scheduler_manager()
        job_info = manager.get_job_info("pedidos_detector")
    except Exception:
        job_info = None
    
    return {
        "ultima_ejecucion": ultima,
        "job_info": job_info,
        "intervalo_segundos": 300  # 5 minutos default
    }


# ============================================================================
# ENDPOINTS FASE 4.2 - TAREAS OPERATIVAS
# ============================================================================

@router.get("/compras/tareas")
async def listar_tareas_operativas(
    empresa_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    limite: int = Query(50, le=200),
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """
    FASE 4.2: Lista tareas operativas de captura de inventario.
    
    Filtrable por empresa y estado.
    """
    db = get_database()
    
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if estado:
        filtro["estado"] = estado
    
    tareas = _p2a_list_tareas(locals())
    
    return {
        "total": len(tareas),
        "tareas": tareas
    }


@router.get("/compras/tareas/{tarea_id}")
async def obtener_tarea_operativa(
    tarea_id: str,
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """Obtiene detalle de una tarea operativa."""
    db = get_database()
    
    tarea = _p2a_get_tarea(tarea_id)
    
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return tarea


@router.post("/compras/tareas/{tarea_id}/completar")
async def completar_tarea_operativa(
    tarea_id: str,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_EJECUTAR"))
):
    """
    FASE 4.2: Marca una tarea operativa como completada.
    
    Esto debería dispararse automáticamente cuando se captura el inventario,
    pero también puede hacerse manualmente.
    """
    usuario_actor_id, usuario_actor_nombre, _usuario_actor_rol = _get_authenticated_compras_actor(current_user)
    payload = {"usuario_id": usuario_actor_id, "usuario_nombre": usuario_actor_nombre, "comentario": "Completada"}
    db = get_database()
    
    from datetime import datetime, timezone
    
    tarea = _p2a_get_tarea(tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if tarea.get("estado") == "COMPLETADA":
        raise HTTPException(status_code=400, detail="Tarea ya completada")
    
    now = datetime.now(timezone.utc).isoformat()
    
    _p2a_completar_tarea(tarea_id, locals())
    
    return {"success": True, "mensaje": "Tarea completada"}


@router.post("/compras/tareas/{tarea_id}/asignar")
async def asignar_tarea_operativa(
    tarea_id: str,
    usuario_id: str = Query(..., description="ID del usuario a asignar"),
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_GESTIONAR"))
):
    """Asigna una tarea operativa a un usuario."""
    _get_authenticated_compras_actor(current_user)
    db = get_database()
    
    from datetime import datetime, timezone
    
    tarea = _p2a_get_tarea(tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    now = datetime.now(timezone.utc).isoformat()
    
    _p2a_asignar_tarea(tarea_id, locals())
    
    return {"success": True, "mensaje": f"Tarea asignada a {usuario_id}"}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/compras/kpis")
async def obtener_kpis(
    server_id: Optional[str] = Query(None),
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """KPIs de automatizaciones operativas."""
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.obtener_kpis(server_id)


@router.get("/compras")
async def listar_automatizaciones(
    server_id: Optional[str] = Query(None),
    sucursal_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    limite: int = Query(50, le=200),
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """Lista automatizaciones."""
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.listar_automatizaciones(server_id, sucursal_id, estado, limite)


# ============================================================================
# BITÁCORA DEL DETECTOR (DEBE IR ANTES DE {automatizacion_id})
# ============================================================================

@router.get("/compras/detector/bitacora")
async def obtener_bitacora_detector(
    limite: int = Query(100, le=500),
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """
    FASE 4.1: Obtiene bitácora de ejecuciones del detector.
    
    Muestra eventos de detección, tareas creadas, auditorías iniciadas.
    """
    db = get_database()
    
    bitacora = _p2a_list_bitacora(locals())
    
    return {
        "total": len(bitacora),
        "eventos": bitacora
    }


@router.get("/compras/pedidos-procesados")
async def listar_pedidos_procesados(
    empresa_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    limite: int = Query(100, le=500),
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """
    FASE 4.1: Lista pedidos que ya fueron procesados.
    
    Útil para verificar anti-duplicados y trazabilidad.
    """
    db = get_database()
    
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if estado:
        filtro["estado"] = estado
    
    pedidos = _p2a_list_pedidos(locals())
    
    return {
        "total": len(pedidos),
        "pedidos": pedidos
    }


# ============================================================================
# ENDPOINTS CON PATH VARIABLE {automatizacion_id}
# ============================================================================

@router.get("/compras/{automatizacion_id}")
async def obtener_automatizacion(
    automatizacion_id: str,
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """Obtiene detalle de una automatización."""
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    registro = service.obtener_automatizacion(automatizacion_id)
    if not registro:
        raise HTTPException(status_code=404, detail="No encontrada")
    
    return registro


@router.post("/compras/procesar")
async def procesar_pedido(
    request: ProcesarPedidoRequest,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_EJECUTAR"))
):
    """
    Procesa pedido capturado.
    Inicia flujo: Detección → Auditoría → EN_REVISION_GERENCIA
    """
    usuario_id, usuario_nombre, _usuario_rol = _get_authenticated_compras_actor(current_user)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = service.procesar_pedido_operativo(
        pedido_id=request.pedido_id,
        server_id=request.server_id,
        sucursal_id=request.sucursal_id,
        sucursal_nombre=request.sucursal_nombre,
        almacen_id=request.almacen_id,
        almacen_nombre=request.almacen_nombre,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        productos=request.productos,
        dias_objetivo=request.dias_objetivo,
        origen_sistema=request.origen_sistema or "MPRO"
    )
    
    return resultado


# ============================================================================
# FLUJO AUTORIZACIÓN GERENCIA
# ============================================================================

@router.post("/compras/{automatizacion_id}/gerencia")
async def autorizar_gerencia(
    automatizacion_id: str,
    request: AccionGerenciaRequest,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_AUTORIZAR"))
):
    """
    Autorización de Gerencia.
    - aprobar → PENDIENTE_TESORERIA
    - rechazar → RECHAZADO
    - ajuste → recalcula y mantiene EN_REVISION_GERENCIA
    """
    usuario_id, _usuario_nombre, usuario_rol = _get_authenticated_compras_actor(current_user)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = service.autorizar_gerencia(
        automatizacion_id=automatizacion_id,
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        accion=request.accion,
        comentario=request.comentario or "",
        nuevo_dias_objetivo=request.dias_objetivo
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# FLUJO AUTORIZACIÓN TESORERÍA
# ============================================================================

@router.post("/compras/{automatizacion_id}/tesoreria")
async def autorizar_tesoreria(
    automatizacion_id: str,
    request: AccionTesoreriaRequest,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_APROBAR"))
):
    """
    Autorización Final de Tesorería.
    - aprobar → APROBADO
    - rechazar → RECHAZADO
    """
    usuario_id, _usuario_nombre, usuario_rol = _get_authenticated_compras_actor(current_user)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = service.autorizar_tesoreria(
        automatizacion_id=automatizacion_id,
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        accion=request.accion,
        comentario=request.comentario or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# MODIFICAR DÍAS OBJETIVO
# ============================================================================

@router.post("/compras/{automatizacion_id}/dias-objetivo")
async def modificar_dias_objetivo(
    automatizacion_id: str,
    request: ModificarDiasObjetivoRequest,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_CONFIGURAR"))
):
    """
    Modifica días objetivo y recalcula.
    Requiere permiso explícito COMPRAS_FACT_CONFIGURAR.
    """
    usuario_id, _usuario_nombre, usuario_rol = _get_authenticated_compras_actor(current_user)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = service.modificar_dias_objetivo(
        automatizacion_id=automatizacion_id,
        nuevo_dias_objetivo=request.dias_objetivo,
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        motivo=request.motivo or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# FASE 4.3: MODIFICAR PERIODO ESTADÍSTICO Y AJUSTE DE CONSUMO
# ============================================================================

@router.post("/compras/{automatizacion_id}/parametros-consumo")
async def modificar_parametros_consumo(
    automatizacion_id: str,
    request: ModificarParametrosConsumoRequest,
    current_user: Dict = Depends(require_explicit_permission("COMPRAS_FACT_CONFIGURAR"))
):
    """
    FASE 4.3: Modifica periodo estadístico y/o ajuste porcentual de consumo.
    
    Permite:
    - Cambiar el periodo estadístico (ej: usar Semana Santa año anterior)
    - Aplicar ajuste porcentual (+10%, -5%, etc.)
    
    El periodo operativo (fecha inventario inicial y fecha pedido) NO se modifica.
    
    Requiere permiso explícito COMPRAS_FACT_CONFIGURAR.
    """
    usuario_id, _usuario_nombre, _usuario_rol = _get_authenticated_compras_actor(current_user)
    db = get_database()
    service = get_automatizacion_compras_service(db)
    
    resultado = service.modificar_parametros_consumo(
        automatizacion_id=automatizacion_id,
        usuario_id=usuario_id,
        fecha_consumo_inicio=request.fecha_consumo_inicio,
        fecha_consumo_fin=request.fecha_consumo_fin,
        porcentaje_ajuste=request.porcentaje_ajuste,
        motivo=request.motivo or ""
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


# ============================================================================
# BITÁCORA
# ============================================================================

@router.get("/compras/{automatizacion_id}/bitacora")
async def obtener_bitacora(
    automatizacion_id: str,
    current_user: Dict = Depends(require_permission("COMPRAS_FACT_VER"))
):
    """Obtiene bitácora de cambios."""
    db = get_database()
    service = get_automatizacion_compras_service(db)
    return service.obtener_bitacora(automatizacion_id)
