"""
FASE 1C-3I-B v2: Servicio Enterprise de Competidores por Unidad de Negocio

ARQUITECTURA:
- Comercial_CompetidoresCatalogo: Catálogo maestro (datos del competidor)
- Comercial_CompetidoresUnidad: Relación competidor-unidad (prioridad, tipo)
- vw_CompetidoresPorUnidad: Vista consolidada para queries

REGLAS:
- Un competidor puede existir una vez en el catálogo maestro
- El mismo competidor puede relacionarse con múltiples unidades
- Cada unidad tiene su propia prioridad/tipo de relación
- TODAS las consultas DEBEN filtrar por UnidadNegocioID
- RBAC limita qué unidades puede ver el usuario
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
import uuid

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _get_conn() -> Tuple:
    """Retorna parámetros de conexión a EDARSAHUB."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


# =============================================================================
# CATÁLOGO MAESTRO DE COMPETIDORES
# =============================================================================

def crear_competidor_catalogo(
    nombre_competidor: str,
    tipo_restaurante: Optional[str] = None,
    segmento_precio: Optional[str] = None,
    ciudad: Optional[str] = None,
    estado: Optional[str] = None,
    pais: str = "México",
    zona_comercial: Optional[str] = None,
    sitio_web: Optional[str] = None,
    url_menu: Optional[str] = None,
    url_google_maps: Optional[str] = None,
    url_instagram: Optional[str] = None,
    url_facebook: Optional[str] = None,
    url_tripadvisor: Optional[str] = None,
    url_opentable: Optional[str] = None,
    notas: Optional[str] = None,
    usuario: str = "sistema"
) -> Dict[str, Any]:
    """
    Crea un competidor en el catálogo maestro.
    NO lo relaciona con ninguna unidad todavía.
    """
    conn = _get_conn()
    competidor_id = str(uuid.uuid4())
    
    # Construir valores SQL
    def sql_str(val):
        return f"N'{val}'" if val else "NULL"
    
    query = f"""
    INSERT INTO Comercial_CompetidoresCatalogo (
        CompetidorCatalogoID,
        NombreCompetidor,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWeb,
        UrlMenu,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        Notas,
        Activo,
        FechaCreacion,
        UsuarioCreacion
    ) VALUES (
        '{competidor_id}',
        N'{nombre_competidor}',
        {sql_str(tipo_restaurante)},
        {sql_str(segmento_precio)},
        {sql_str(Ciudad)},
        {sql_str(Estado)},
        {sql_str(Pais)},
        {sql_str(zona_comercial)},
        {sql_str(sitio_web)},
        {sql_str(url_menu)},
        {sql_str(url_google_maps)},
        {sql_str(url_instagram)},
        {sql_str(url_facebook)},
        {sql_str(url_tripadvisor)},
        {sql_str(url_opentable)},
        {sql_str(Notas)},
        1,
        GETDATE(),
        N'{usuario}'
    )
    """
    
    execute_sql_query(*conn, query)
    logger.info(f"[COMPETIDOR_CATALOGO] Creado {competidor_id}: {nombre_competidor}")
    
    return {
        "competidor_catalogo_id": competidor_id,
        "nombre_competidor": nombre_competidor,
        "mensaje": "Competidor creado en catálogo maestro. Usar /relacionar para asignarlo a unidades."
    }


def buscar_competidor_catalogo(
    nombre: Optional[str] = None,
    ciudad: Optional[str] = None,
    solo_activos: bool = True,
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    Busca competidores en el catálogo maestro (sin filtrar por unidad).
    Útil para ver qué competidores existen antes de relacionarlos.
    """
    conn = _get_conn()
    
    where_clauses = []
    if solo_activos:
        where_clauses.append("Activo = 1")
    if nombre:
        where_clauses.append(f"NombreCompetidor LIKE N'%{nombre}%'")
    if ciudad:
        where_clauses.append(f"Ciudad LIKE N'%{ciudad}%'")
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Contar total
    count_query = f"SELECT COUNT(*) as total FROM Comercial_CompetidoresCatalogo {where_sql}"
    count_result = execute_sql_query(*conn, count_query)
    total = count_result[0]['total'] if count_result else 0
    
    # Obtener página
    offset = (page - 1) * page_size
    query = f"""
    SELECT 
        CAST(CompetidorCatalogoID AS NVARCHAR(36)) as CompetidorCatalogoID,
        NombreCompetidor,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWeb,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        Notas,
        Activo,
        FechaCreacion
    FROM Comercial_CompetidoresCatalogo
    {where_sql}
    ORDER BY NombreCompetidor
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    result = execute_sql_query(*conn, query)
    
    competidores = []
    for row in result:
        competidores.append({
            "competidor_catalogo_id": row.get('CompetidorCatalogoID'),
            "nombre_competidor": row.get('NombreCompetidor'),
            "tipo_restaurante": row.get('TipoRestaurante'),
            "segmento_precio": row.get('SegmentoPrecio'),
            "ciudad": row.get('Ciudad'),
            "estado": row.get('Estado'),
            "zona_comercial": row.get('ZonaComercial'),
            "activo": bool(row.get('Activo', True))
        })
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "competidores": competidores
    }


# =============================================================================
# RELACIÓN COMPETIDOR-UNIDAD DE NEGOCIO
# =============================================================================

def relacionar_competidor_unidad(
    competidor_catalogo_id: str,
    empresa_id: int,
    unidad_negocio_id: int,
    es_competencia_directa: bool = True,
    es_benchmark_aspiracional: bool = False,
    prioridad: int = 0,
    distancia_km: Optional[float] = None,
    comentarios: Optional[str] = None,
    usuario: str = "sistema"
) -> Dict[str, Any]:
    """
    Relaciona un competidor del catálogo con una unidad de negocio.
    
    REGLA: El mismo competidor puede estar en múltiples unidades con diferentes
    configuraciones (prioridad, tipo de relación, etc.)
    """
    conn = _get_conn()
    
    # Verificar que el competidor existe en el catálogo
    check_query = f"""
    SELECT NombreCompetidor FROM Comercial_CompetidoresCatalogo 
    WHERE CompetidorCatalogoID = '{competidor_catalogo_id}' AND Activo = 1
    """
    check_result = execute_sql_query(*conn, check_query)
    if not check_result:
        return {"error": "COMPETIDOR_NO_EXISTE", "mensaje": "El competidor no existe en el catálogo"}
    
    nombre_competidor = check_result[0]['NombreCompetidor']
    
    # Verificar si ya existe la relación
    existe_query = f"""
    SELECT CompetidorUnidadID FROM Comercial_CompetidoresUnidad
    WHERE CompetidorCatalogoID = '{competidor_catalogo_id}' 
      AND UnidadNegocioID = {UnidadNegocioID}
      AND Activo = 1
    """
    existe_result = execute_sql_query(*conn, existe_query)
    if existe_result:
        return {
            "error": "RELACION_DUPLICADA",
            "mensaje": f"El competidor '{nombre_competidor}' ya está relacionado con la unidad {unidad_negocio_id}"
        }
    
    # Determinar tipo de relación
    tipo_relacion = "BENCHMARK_ASPIRACIONAL" if es_benchmark_aspiracional else "COMPETENCIA_DIRECTA"
    
    relacion_id = str(uuid.uuid4())
    
    distancia_sql = f"{distancia_km}" if distancia_km is not None else "NULL"
    comentarios_sql = f"N'{comentarios}'" if comentarios else "NULL"
    
    insert_query = f"""
    INSERT INTO Comercial_CompetidoresUnidad (
        CompetidorUnidadID,
        CompetidorCatalogoID,
        EmpresaID,
        UnidadNegocioID,
        EsCompetenciaDirecta,
        EsBenchmarkAspiracional,
        TipoRelacion,
        Prioridad,
        DistanciaKm,
        Comentarios,
        Activo,
        FechaCreacion,
        UsuarioCreacion
    ) VALUES (
        '{relacion_id}',
        '{competidor_catalogo_id}',
        {EmpresaID},
        {UnidadNegocioID},
        {1 if es_competencia_directa else 0},
        {1 if es_benchmark_aspiracional else 0},
        '{tipo_relacion}',
        {Prioridad},
        {distancia_sql},
        {comentarios_sql},
        1,
        GETDATE(),
        N'{usuario}'
    )
    """
    
    execute_sql_query(*conn, insert_query)
    logger.info(f"[COMPETIDOR_UNIDAD] Relacionado {nombre_competidor} -> Unidad {unidad_negocio_id}")
    
    return {
        "competidor_unidad_id": relacion_id,
        "competidor_catalogo_id": competidor_catalogo_id,
        "nombre_competidor": nombre_competidor,
        "unidad_negocio_id": unidad_negocio_id,
        "tipo_relacion": tipo_relacion,
        "mensaje": f"Competidor '{nombre_competidor}' relacionado con unidad {unidad_negocio_id}"
    }


def desrelacionar_competidor_unidad(
    competidor_catalogo_id: str,
    unidad_negocio_id: int,
    usuario: str = "sistema"
) -> Dict[str, Any]:
    """
    Elimina (soft delete) la relación de un competidor con una unidad.
    El competidor sigue existiendo en el catálogo y en otras unidades.
    """
    conn = _get_conn()
    
    update_query = f"""
    UPDATE Comercial_CompetidoresUnidad
    SET Activo = 0,
        FechaModificacion = GETDATE(),
        UsuarioModificacion = N'{usuario}'
    WHERE CompetidorCatalogoID = '{competidor_catalogo_id}'
      AND UnidadNegocioID = {UnidadNegocioID}
      AND Activo = 1
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[COMPETIDOR_UNIDAD] Desrelacionado {competidor_catalogo_id} de Unidad {unidad_negocio_id}")
    
    return {
        "mensaje": f"Competidor desrelacionado de unidad {unidad_negocio_id}",
        "competidor_catalogo_id": competidor_catalogo_id,
        "unidad_negocio_id": unidad_negocio_id
    }


# =============================================================================
# CONSULTAS POR UNIDAD DE NEGOCIO (OBLIGATORIO FILTRAR)
# =============================================================================

def listar_competidores_por_unidad(
    unidad_negocio_id: int,
    empresa_id: Optional[int] = None,
    solo_competencia_directa: bool = False,
    solo_benchmark: bool = False,
    solo_activos: bool = True,
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    Lista competidores de UNA unidad de negocio específica.
    
    REGLA CRÍTICA: Esta es la función principal para obtener competidores.
    SIEMPRE debe recibir unidad_negocio_id.
    """
    conn = _get_conn()
    
    where_clauses = [f"UnidadNegocioID = {unidad_negocio_id}"]
    
    if empresa_id:
        where_clauses.append(f"EmpresaID = {empresa_id}")
    if solo_activos:
        where_clauses.append("Activo = 1")
    if solo_competencia_directa:
        where_clauses.append("EsCompetenciaDirecta = 1")
    if solo_benchmark:
        where_clauses.append("EsBenchmarkAspiracional = 1")
    
    where_sql = "WHERE " + " AND ".join(where_clauses)
    
    # Contar total
    count_query = f"SELECT COUNT(*) as total FROM vw_CompetidoresPorUnidad {where_sql}"
    count_result = execute_sql_query(*conn, count_query)
    total = count_result[0]['total'] if count_result else 0
    
    # Obtener página
    offset = (page - 1) * page_size
    query = f"""
    SELECT 
        CAST(CompetidorUnidadID AS NVARCHAR(36)) as CompetidorUnidadID,
        CAST(CompetidorCatalogoID AS NVARCHAR(36)) as CompetidorCatalogoID,
        EmpresaID,
        UnidadNegocioID,
        NombreCompetidor,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWeb,
        UrlMenu,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        Notas,
        EsCompetenciaDirecta,
        EsBenchmarkAspiracional,
        TipoRelacion,
        Prioridad,
        DistanciaKm,
        Comentarios,
        Activo
    FROM vw_CompetidoresPorUnidad
    {where_sql}
    ORDER BY Prioridad DESC, NombreCompetidor
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    result = execute_sql_query(*conn, query)
    
    competidores = []
    for row in result:
        competidores.append({
            "competidor_unidad_id": row.get('CompetidorUnidadID'),
            "competidor_catalogo_id": row.get('CompetidorCatalogoID'),
            "empresa_id": row.get('EmpresaID'),
            "unidad_negocio_id": row.get('UnidadNegocioID'),
            "nombre_competidor": row.get('NombreCompetidor'),
            "tipo_restaurante": row.get('TipoRestaurante'),
            "segmento_precio": row.get('SegmentoPrecio'),
            "ciudad": row.get('Ciudad'),
            "zona_comercial": row.get('ZonaComercial'),
            "sitio_web": row.get('SitioWeb'),
            "url_google_maps": row.get('UrlGoogleMaps'),
            "url_instagram": row.get('UrlInstagram'),
            "url_facebook": row.get('UrlFacebook'),
            "url_tripadvisor": row.get('UrlTripAdvisor'),
            "url_opentable": row.get('UrlOpenTable'),
            "notas": row.get('Notas'),
            "es_competencia_directa": bool(row.get('EsCompetenciaDirecta', True)),
            "es_benchmark_aspiracional": bool(row.get('EsBenchmarkAspiracional', False)),
            "tipo_relacion": row.get('TipoRelacion'),
            "prioridad": row.get('Prioridad', 0),
            "distancia_km": float(row.get('DistanciaKm')) if row.get('DistanciaKm') else None,
            "comentarios": row.get('Comentarios'),
            "activo": bool(row.get('Activo', True))
        })
    
    return {
        "total": total,
        "unidad_negocio_id": unidad_negocio_id,
        "page": page,
        "page_size": page_size,
        "competidores": competidores
    }


def obtener_competidor_por_unidad(
    competidor_catalogo_id: str,
    unidad_negocio_id: int
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un competidor específico en el contexto de una unidad.
    Retorna datos del catálogo + datos de la relación con la unidad.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        CAST(CompetidorUnidadID AS NVARCHAR(36)) as CompetidorUnidadID,
        CAST(CompetidorCatalogoID AS NVARCHAR(36)) as CompetidorCatalogoID,
        EmpresaID,
        UnidadNegocioID,
        NombreCompetidor,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWeb,
        UrlMenu,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        Notas,
        EsCompetenciaDirecta,
        EsBenchmarkAspiracional,
        TipoRelacion,
        Prioridad,
        DistanciaKm,
        Comentarios,
        Activo
    FROM vw_CompetidoresPorUnidad
    WHERE CompetidorCatalogoID = '{competidor_catalogo_id}'
      AND UnidadNegocioID = {unidad_negocio_id}
    """
    
    result = execute_sql_query(*conn, query)
    
    if not result:
        return None
    
    row = result[0]
    return {
        "competidor_unidad_id": row.get('CompetidorUnidadID'),
        "competidor_catalogo_id": row.get('CompetidorCatalogoID'),
        "empresa_id": row.get('EmpresaID'),
        "unidad_negocio_id": row.get('UnidadNegocioID'),
        "nombre_competidor": row.get('NombreCompetidor'),
        "tipo_restaurante": row.get('TipoRestaurante'),
        "segmento_precio": row.get('SegmentoPrecio'),
        "ciudad": row.get('Ciudad'),
        "zona_comercial": row.get('ZonaComercial'),
        "es_competencia_directa": bool(row.get('EsCompetenciaDirecta', True)),
        "es_benchmark_aspiracional": bool(row.get('EsBenchmarkAspiracional', False)),
        "tipo_relacion": row.get('TipoRelacion'),
        "prioridad": row.get('Prioridad', 0),
        "distancia_km": float(row.get('DistanciaKm')) if row.get('DistanciaKm') else None,
        "comentarios": row.get('Comentarios')
    }


def obtener_unidades_del_competidor(competidor_catalogo_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene todas las unidades de negocio donde está relacionado un competidor.
    Útil para saber "¿En qué unidades compite este restaurante?"
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        cu.UnidadNegocioID,
        cu.EmpresaID,
        cu.TipoRelacion,
        cu.Prioridad,
        cu.EsCompetenciaDirecta,
        cu.EsBenchmarkAspiracional,
        cc.NombreCompetidor
    FROM Comercial_CompetidoresUnidad cu
    INNER JOIN Comercial_CompetidoresCatalogo cc 
        ON cu.CompetidorCatalogoID = cc.CompetidorCatalogoID
    WHERE cu.CompetidorCatalogoID = '{competidor_catalogo_id}'
      AND cu.Activo = 1
    ORDER BY cu.Prioridad DESC
    """
    
    result = execute_sql_query(*conn, query)
    
    unidades = []
    for row in result:
        unidades.append({
            "unidad_negocio_id": row.get('UnidadNegocioID'),
            "empresa_id": row.get('EmpresaID'),
            "tipo_relacion": row.get('TipoRelacion'),
            "prioridad": row.get('Prioridad'),
            "es_competencia_directa": bool(row.get('EsCompetenciaDirecta')),
            "es_benchmark_aspiracional": bool(row.get('EsBenchmarkAspiracional'))
        })
    
    return unidades


# =============================================================================
# ESTADÍSTICAS POR UNIDAD
# =============================================================================

def estadisticas_competidores_unidad(unidad_negocio_id: int) -> Dict[str, Any]:
    """
    Estadísticas de competidores para una unidad específica.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        COUNT(*) as total_competidores,
        SUM(CASE WHEN EsCompetenciaDirecta = 1 THEN 1 ELSE 0 END) as competencia_directa,
        SUM(CASE WHEN EsBenchmarkAspiracional = 1 THEN 1 ELSE 0 END) as benchmark_aspiracional,
        COUNT(DISTINCT SegmentoPrecio) as segmentos_precio,
        AVG(CAST(DistanciaKm AS FLOAT)) as distancia_promedio_km
    FROM vw_CompetidoresPorUnidad
    WHERE UnidadNegocioID = {unidad_negocio_id}
      AND Activo = 1
    """
    
    result = execute_sql_query(*conn, query)
    
    if not result:
        return {
            "unidad_negocio_id": unidad_negocio_id,
            "total_competidores": 0,
            "competencia_directa": 0,
            "benchmark_aspiracional": 0
        }
    
    row = result[0]
    return {
        "unidad_negocio_id": unidad_negocio_id,
        "total_competidores": row.get('total_competidores', 0),
        "competencia_directa": row.get('competencia_directa', 0),
        "benchmark_aspiracional": row.get('benchmark_aspiracional', 0),
        "segmentos_precio_distintos": row.get('segmentos_precio', 0),
        "distancia_promedio_km": round(float(row.get('distancia_promedio_km') or 0), 2)
    }


# =============================================================================
# VALIDACIÓN RBAC
# =============================================================================

def validar_acceso_unidad(usuario_id: str, unidad_negocio_id: int, es_superadmin: bool = False) -> bool:
    """
    Valida si el usuario tiene acceso a una unidad de negocio específica.
    
    REGLA: SuperAdmin puede ver todas las unidades.
    Otros usuarios solo pueden ver las unidades asignadas.
    """
    if es_superadmin:
        return True
    
    # TODO: Implementar consulta a tabla de permisos usuario-unidad
    # Por ahora, permitir acceso (implementar cuando exista tabla de permisos)
    logger.warning(f"[RBAC] Validación de acceso pendiente para usuario {usuario_id} -> unidad {unidad_negocio_id}")
    return True


def obtener_unidades_permitidas(usuario_id: str, es_superadmin: bool = False) -> List[int]:
    """
    Obtiene las unidades de negocio a las que tiene acceso el usuario.
    
    REGLA: SuperAdmin ve todas.
    """
    conn = _get_conn()
    
    if es_superadmin:
        query = "SELECT DISTINCT UnidadNegocioID FROM Comercial_CompetidoresUnidad WHERE Activo = 1"
    else:
        # TODO: Consultar tabla de permisos usuario-unidad
        query = "SELECT DISTINCT UnidadNegocioID FROM Comercial_CompetidoresUnidad WHERE Activo = 1"
    
    result = execute_sql_query(*conn, query)
    return [row['UnidadNegocioID'] for row in result]
