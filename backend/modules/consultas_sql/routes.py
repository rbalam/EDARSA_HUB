"""
EDARSA HUB - Consultas SQL: API Routes
======================================
FASE 4: Endpoints /api/consultas-sql/* para exponer módulo SQL-First.
FASE 4B: Endpoints adicionales y blindaje de seguridad.

SEGURIDAD:
- No acepta SQL libre desde frontend (excepto validar-texto para Admin)
- Solo ejecuta consultas del catálogo EDARSAHUB
- Aplica validación con SQLSanitizer
- RBAC: Temporalmente restringido a SuperAdministrador/Administrador
- No expone credenciales ni SQL sensible

ENDPOINTS:
- GET  /catalogo                     - Listar consultas
- GET  /catalogo/{codigo}            - Detalle de consulta
- GET  /catalogo/{codigo}/versiones  - Versiones históricas (FASE 4B)
- GET  /catalogo/{codigo}/servidores - Servidores asociados (FASE 4B)
- POST /validar                      - Validar consulta del catálogo
- POST /validar-texto                - Validar SQL libre (FASE 4B, Admin only)
- POST /ejecutar                     - Ejecutar consulta autorizada (blindado FASE 4B)
- GET  /sistemas                     - Listar sistemas
- GET  /modulos                      - Listar módulos
"""

import logging
import re
import time
from typing import Dict, Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.db import execute_sql_query
from core.server_registry import get_server_connection_info_with_secrets
from core.security import (
    SQLSanitizer, 
    log_blocked_sql,
    verify_token,
)

from .service import ConsultasSQLService, get_service
from .repository import ConsultasSQLRepository, get_repository
from .schemas import (
    CatalogoFiltrosRequest,
    ValidarConsultaRequest,
    EjecutarConsultaRequest,
    ConsultaCatalogoItem,
    ConsultaCatalogoListResponse,
    ConsultaDetalleResponse,
    ParametroDetalle,
    ValidacionResponse,
    EjecucionResponse,
    EjecucionSource,
    SistemasResponse,
    SistemaItem,
    ModulosResponse,
    ModuloItem,
    ErrorResponse,
    # FASE 4B: Nuevos schemas
    ValidarTextoRequest,
    ValidarTextoResponse,
    VersionItem,
    VersionesResponse,
    ServidorAsociadoItem,
    ServidoresAsociadosResponse,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Router con prefix
router = APIRouter(prefix="/consultas-sql", tags=["Consultas SQL - Catálogo"])


# ============================================================================
# HELPERS DE AUTENTICACIÓN Y PERMISOS
# ============================================================================

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """Obtiene usuario actual desde token JWT."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        return payload
    except Exception as e:
        logger.warning(f"[CONSULTAS-SQL-AUTH] Error verificando token: {e}")
        raise HTTPException(status_code=401, detail="No autenticado")


def check_consultas_sql_permission(user: Dict, permission: str = "VER_CATALOGO") -> bool:
    """
    Verifica permiso para consultas SQL.
    
    FASE 4: Temporalmente restringido a SuperAdministrador/Administrador.
    TODO: Implementar RBAC granular en fase futura.
    
    Permisos futuros:
    - CONSULTAS_SQL_VER_CATALOGO
    - CONSULTAS_SQL_VER_DETALLE
    - CONSULTAS_SQL_EJECUTAR
    - CONSULTAS_SQL_VER_SQL
    - CONSULTAS_SQL_ADMINISTRAR
    """
    role = user.get('role', '')
    
    # Temporalmente: Solo SuperAdministrador y Administrador
    allowed_roles = ['SuperAdministrador', 'Administrador']
    
    if role in allowed_roles:
        return True
    
    # En futuro: verificar permiso específico
    # permisos = user.get('permisos', [])
    # return f"CONSULTAS_SQL_{permission}" in permisos
    
    return False


def require_permission(permission: str = "VER_CATALOGO"):
    """Decorator para requerir permiso."""
    async def dependency(user: Dict = Depends(get_current_user_from_token)):
        if not check_consultas_sql_permission(user, permission):
            logger.warning(
                f"[CONSULTAS-SQL-RBAC] Acceso denegado. User: {user.get('email')}, "
                f"Role: {user.get('role')}, Permission: {permission}"
            )
            raise HTTPException(
                status_code=403, 
                detail=f"No tiene permiso para {permission}. Requiere rol Administrador."
            )
        return user
    return dependency


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/catalogo", response_model=ConsultaCatalogoListResponse)
async def listar_catalogo(
    sistema: Optional[str] = Query(None, description="Sistema: SOFTRESTAURANT, MPRO"),
    modulo: Optional[str] = Query(None, description="Módulo"),
    activo: bool = Query(True, description="Solo activas"),
    solo_lectura: bool = Query(True, description="Solo lectura"),
    buscar: Optional[str] = Query(None, max_length=100, description="Búsqueda"),
    limit: int = Query(100, ge=1, le=500, description="Límite"),
    user: Dict = Depends(require_permission("VER_CATALOGO"))
):
    """
    Lista consultas disponibles del catálogo SQL.
    
    SEGURIDAD:
    - Requiere autenticación
    - Requiere rol Administrador/SuperAdministrador
    - No expone SQL completo
    """
    try:
        service = get_service()
        
        consultas = service.listar_consultas(
            sistema=sistema.upper() if sistema else None,
            modulo=modulo,
            solo_activas=activo,
            solo_manuales=False,
            buscar=buscar,
            limit=limit
        )
        
        # Convertir a response items (sin SQL)
        items = []
        for c in consultas:
            params = service._repo.get_parametros(c.consulta_id)
            items.append(ConsultaCatalogoItem(
                consulta_id=c.consulta_id,
                codigo_consulta=c.codigo_consulta,
                nombre=c.nombre_consulta,
                descripcion=c.descripcion,
                sistema=c.get_codigo_sistema(),
                sistema_tipo_id=c.sistema_tipo_id,
                modulo=c.modulo,
                activo=c.activo,
                solo_lectura=c.solo_lectura,
                version=c.version,
                requiere_parametros=len(params) > 0,
                count_parametros=len(params),
                permite_ejecucion_manual=c.permite_ejecucion_manual,
                fecha_actualizacion=c.fecha_modificacion or c.fecha_creacion,
            ))
        
        logger.info(
            f"[CONSULTAS-SQL] Catálogo listado. User: {user.get('email')}, "
            f"Filtros: sistema={sistema}, modulo={modulo}, Total: {len(items)}"
        )
        
        return ConsultaCatalogoListResponse(
            success=True,
            total=len(items),
            consultas=items,
            filtros_aplicados={
                'sistema': sistema,
                'modulo': modulo,
                'activo': activo,
                'solo_lectura': solo_lectura,
                'buscar': buscar,
                'limit': limit,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error listando catálogo: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar catálogo")


@router.get("/catalogo/{codigo_consulta}", response_model=ConsultaDetalleResponse)
async def obtener_detalle_consulta(
    codigo_consulta: str,
    incluir_sql: bool = Query(False, description="Incluir SQL (requiere permiso especial)"),
    user: Dict = Depends(require_permission("VER_DETALLE"))
):
    """
    Obtiene detalle de una consulta por código.
    
    SEGURIDAD:
    - Requiere autenticación
    - SQL solo visible para SuperAdministrador con incluir_sql=True
    - No expone credenciales
    """
    try:
        service = get_service()
        
        # Obtener consulta
        consulta = service.obtener_consulta(codigo=codigo_consulta, include_sql=True)
        if not consulta:
            raise HTTPException(status_code=404, detail=f"Consulta '{codigo_consulta}' no encontrada")
        
        # Verificar que esté activa
        if not consulta.activo:
            raise HTTPException(status_code=400, detail="Consulta inactiva")
        
        # Obtener parámetros
        params = service._repo.get_parametros(consulta.consulta_id)
        
        # Validar consulta
        validation = service.validar_consulta(consulta_id=consulta.consulta_id)
        
        # Determinar si mostrar SQL
        sql_to_show = None
        if incluir_sql:
            # Solo SuperAdministrador puede ver SQL
            if user.get('role') == 'SuperAdministrador':
                sql_to_show = consulta.consulta_sql
            else:
                logger.warning(
                    f"[CONSULTAS-SQL] Intento de ver SQL sin permiso. "
                    f"User: {user.get('email')}, Consulta: {codigo_consulta}"
                )
        
        logger.info(
            f"[CONSULTAS-SQL] Detalle consultado. User: {user.get('email')}, "
            f"Consulta: {codigo_consulta}"
        )
        
        return ConsultaDetalleResponse(
            success=True,
            consulta_id=consulta.consulta_id,
            codigo_consulta=consulta.codigo_consulta,
            nombre=consulta.nombre_consulta,
            descripcion=consulta.descripcion,
            sistema=consulta.get_codigo_sistema(),
            modulo=consulta.modulo,
            activo=consulta.activo,
            solo_lectura=consulta.solo_lectura,
            version=consulta.version,
            parametros=[
                ParametroDetalle(
                    nombre=p.nombre_parametro,
                    nombre_mostrar=p.nombre_mostrar,
                    tipo_dato=p.tipo_dato,
                    requerido=p.requerido,
                    valor_default=p.valor_default,
                    regex_validacion=p.regex_validacion,
                    valor_minimo=p.valor_minimo,
                    valor_maximo=p.valor_maximo,
                    orden=p.orden_mostrar,
                ) for p in params
            ],
            requiere_parametros=len(params) > 0,
            permite_ejecucion_manual=consulta.permite_ejecucion_manual,
            validacion_estado="VALIDA" if validation.is_valid else "INVALIDA",
            sql=sql_to_show,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error obteniendo detalle: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener detalle")


# ============================================================================
# FASE 4B: NUEVOS ENDPOINTS
# ============================================================================

@router.get("/catalogo/{codigo_consulta}/versiones", response_model=VersionesResponse)
async def listar_versiones_consulta(
    codigo_consulta: str,
    incluir_sql: bool = Query(False, description="Incluir SQL (requiere SuperAdmin)"),
    user: Dict = Depends(require_permission("VER_DETALLE"))
):
    """
    Lista versiones históricas de una consulta.
    
    FASE 4B: Endpoint de versiones.
    
    SEGURIDAD:
    - Requiere autenticación
    - SQL de versiones solo visible para SuperAdministrador con incluir_sql=True
    - No ejecuta SQL
    - No expone credenciales
    """
    try:
        service = get_service()
        
        # Obtener consulta
        consulta = service.obtener_consulta(codigo=codigo_consulta, include_sql=False)
        if not consulta:
            raise HTTPException(status_code=404, detail=f"Consulta '{codigo_consulta}' no encontrada")
        
        # Obtener versiones desde ConsultasSQL_Versiones
        versiones_query = f"""
        SELECT 
            VersionID,
            Version,
            ConsultaSQL,
            MotivoCambio,
            FechaCreacion,
            UsuarioCreacionID
        FROM ConsultasSQL_Versiones
        WHERE ConsultaID = {consulta.consulta_id}
        ORDER BY Version DESC
        """
        
        from core.db import execute_sql_query
        from core.server_registry import EDARSAHUB_CONFIG
        versiones_rows = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            versiones_query
        )
        
        # Determinar si mostrar SQL
        puede_ver_sql = incluir_sql and user.get('role') == 'SuperAdministrador'
        
        versiones = []
        for v in versiones_rows:
            versiones.append(VersionItem(
                version_id=v['VersionID'],
                version=v['Version'],
                motivo_cambio=v.get('MotivoCambio'),
                fecha_creacion=str(v['FechaCreacion']) if v.get('FechaCreacion') else None,
                usuario_creacion=v.get('UsuarioCreacionID'),
                sql=v.get('ConsultaSQL') if puede_ver_sql else None
            ))
        
        logger.info(
            f"[CONSULTAS-SQL] Versiones consultadas. User: {user.get('email')}, "
            f"Consulta: {codigo_consulta}, Total: {len(versiones)}"
        )
        
        return VersionesResponse(
            success=True,
            codigo_consulta=codigo_consulta,
            consulta_id=consulta.consulta_id,
            total_versiones=len(versiones),
            versiones=versiones
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error listando versiones: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar versiones")


@router.get("/catalogo/{codigo_consulta}/servidores", response_model=ServidoresAsociadosResponse)
async def listar_servidores_asociados(
    codigo_consulta: str,
    user: Dict = Depends(require_permission("VER_DETALLE"))
):
    """
    Lista servidores asociados a una consulta.
    
    FASE 4B: Endpoint de servidores asociados.
    
    SEGURIDAD:
    - Requiere autenticación
    - NO expone: password, api_key, connection_string, host, usuario
    - Solo metadatos seguros: nombre, sistema, empresa, activo
    - No ejecuta conexión LIVE
    """
    try:
        service = get_service()
        
        # Obtener consulta
        consulta = service.obtener_consulta(codigo=codigo_consulta, include_sql=False)
        if not consulta:
            raise HTTPException(status_code=404, detail=f"Consulta '{codigo_consulta}' no encontrada")
        
        # Obtener servidores asociados - JOIN con Servidores_Conexiones para metadatos seguros
        # IMPORTANTE: NO exponer host, port, username, password, api_key, connection_string
        servidores_query = f"""
        SELECT 
            CS.ConsultaServidorID,
            CAST(CS.ServidorID AS NVARCHAR(36)) as ServidorID,
            SC.Nombre as ServidorNombre,
            CASE SC.SistemaTipoID 
                WHEN 1 THEN 'SOFTRESTAURANT_PRO'
                WHEN 2 THEN 'MPRO'
                WHEN 6 THEN 'ENTERPRISE'
                ELSE 'OTRO'
            END as SistemaTipo,
            E.Nombre as EmpresaNombre,
            CS.Activo,
            ISNULL(CS.Prioridad, 0) as Prioridad
        FROM ConsultasSQL_Servidores CS
        INNER JOIN Servidores_Conexiones SC ON SC.ServidorID = CS.ServidorID
        LEFT JOIN Sistema_Empresas E ON E.EmpresaID = CS.EmpresaID
        WHERE CS.ConsultaID = {consulta.consulta_id}
        ORDER BY CS.Prioridad, SC.Nombre
        """
        
        from core.db import execute_sql_query
        from core.server_registry import EDARSAHUB_CONFIG
        servidores_rows = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            servidores_query
        )
        
        servidores = []
        for s in servidores_rows:
            servidores.append(ServidorAsociadoItem(
                consulta_servidor_id=s['ConsultaServidorID'],
                servidor_id=s['ServidorID'],
                servidor_nombre=s.get('ServidorNombre'),
                sistema_tipo=s.get('SistemaTipo'),
                empresa_nombre=s.get('EmpresaNombre'),
                activo=bool(s.get('Activo', False)),
                prioridad=s.get('Prioridad', 0)
            ))
        
        logger.info(
            f"[CONSULTAS-SQL] Servidores asociados consultados. User: {user.get('email')}, "
            f"Consulta: {codigo_consulta}, Total: {len(servidores)}"
        )
        
        return ServidoresAsociadosResponse(
            success=True,
            codigo_consulta=codigo_consulta,
            consulta_id=consulta.consulta_id,
            total_servidores=len(servidores),
            servidores=servidores
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error listando servidores asociados: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar servidores")


@router.post("/validar-texto", response_model=ValidarTextoResponse)
async def validar_texto_sql(
    request: ValidarTextoRequest,
    user: Dict = Depends(require_permission("VER_CATALOGO"))
):
    """
    Valida texto SQL libre.
    
    FASE 4B: Endpoint de validación de texto SQL.
    
    SEGURIDAD:
    - Requiere autenticación
    - Restringido a Admin/SuperAdministrador
    - Usa SQLSanitizer centralizado
    - NO guarda el SQL
    - NO ejecuta el SQL
    - Registra intentos bloqueados con log_blocked_sql()
    - Responde con errores controlados (sin stacktrace)
    """
    try:
        # Verificar permiso especial para validar texto libre
        role = user.get('role', '')
        if role not in ['SuperAdministrador', 'Administrador']:
            logger.warning(
                f"[CONSULTAS-SQL-SECURITY] Intento no autorizado de validar texto SQL. "
                f"User: {user.get('email')}, Role: {role}"
            )
            raise HTTPException(
                status_code=403,
                detail="Solo Administrador/SuperAdministrador puede validar texto SQL libre"
            )
        
        sql_texto = request.sql_texto.strip()
        
        # Validar con SQLSanitizer
        validation = SQLSanitizer.validate(sql_texto)
        
        errors = []
        warnings = []
        
        if not validation.is_safe:
            # Registrar intento bloqueado
            log_blocked_sql(
                validation,
                endpoint="/api/consultas-sql/validar-texto",
                user_email=user.get('email')
            )
            errors.append({
                "code": "SQL_BLOCKED",
                "message": validation.blocked_reason,
                "severity": "HIGH"
            })
        
        # Detectar parámetros (patrones {nombre})
        import re
        parametros_detectados = list(set(re.findall(r'\{(\w+)\}', sql_texto)))
        
        # Warnings adicionales
        sql_upper = sql_texto.upper()
        if 'SELECT *' in sql_upper:
            warnings.append({
                "code": "SELECT_STAR",
                "message": "Se recomienda especificar columnas en lugar de SELECT *",
                "severity": "LOW"
            })
        
        if 'TOP' not in sql_upper[:50] and sql_upper.startswith('SELECT'):
            warnings.append({
                "code": "NO_LIMIT",
                "message": "Se recomienda usar TOP o LIMIT para evitar resultados masivos",
                "severity": "MEDIUM"
            })
        
        logger.info(
            f"[CONSULTAS-SQL] Validación de texto SQL. User: {user.get('email')}, "
            f"Valid: {validation.is_safe}, Params: {parametros_detectados}"
        )
        
        return ValidarTextoResponse(
            success=True,
            is_valid=validation.is_safe,
            sql_analizado=True,
            errors=errors,
            warnings=warnings,
            parametros_detectados=parametros_detectados,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error validando texto SQL: {e}")
        raise HTTPException(status_code=500, detail="Error interno al validar SQL")
async def validar_consulta(
    request: ValidarConsultaRequest,
    user: Dict = Depends(require_permission("VER_CATALOGO"))
):
    """
    Valida una consulta del catálogo.
    
    SEGURIDAD:
    - No acepta SQL libre
    - Solo valida consultas del catálogo por código o ID
    """
    try:
        service = get_service()
        
        # Debe proporcionar código o ID
        if not request.codigo_consulta and not request.consulta_id:
            raise HTTPException(
                status_code=400, 
                detail="Debe proporcionar codigo_consulta o consulta_id"
            )
        
        # Obtener consulta
        consulta = service.obtener_consulta(
            consulta_id=request.consulta_id,
            codigo=request.codigo_consulta,
            include_sql=True
        )
        if not consulta:
            raise HTTPException(status_code=404, detail="Consulta no encontrada")
        
        # Validar
        validation = service.validar_consulta(consulta_id=consulta.consulta_id)
        
        logger.info(
            f"[CONSULTAS-SQL] Validación ejecutada. User: {user.get('email')}, "
            f"Consulta: {consulta.codigo_consulta}, Valid: {validation.is_valid}"
        )
        
        return ValidacionResponse(
            success=True,
            is_valid=validation.is_valid,
            codigo_consulta=consulta.codigo_consulta,
            consulta_id=consulta.consulta_id,
            errors=validation.errors,
            warnings=validation.warnings,
            parametros_detectados=validation.detected_parameters,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error validando: {e}")
        raise HTTPException(status_code=500, detail="Error interno al validar")


@router.post("/ejecutar", response_model=EjecucionResponse)
async def ejecutar_consulta(
    request: EjecutarConsultaRequest,
    user: Dict = Depends(require_permission("EJECUTAR"))
):
    """
    Ejecuta una consulta autorizada del catálogo.
    
    FASE 4B: BLINDAJE DE SEGURIDAD
    
    SEGURIDAD ESTRICTA:
    1. Solo Admin/SuperAdministrador
    2. No acepta SQL libre
    3. Solo consultas del catálogo EDARSAHUB
    4. Consulta debe tener Activo=1
    5. Consulta debe tener SoloLectura=1
    6. Consulta debe tener PermiteEjecucionManual=1
    7. Valida con SQLSanitizer antes de ejecutar
    8. Parámetros validados contra ConsultasSQL_Parametros
    9. No permite parámetros no declarados
    10. Límite máximo de 5000 filas (reducido por seguridad)
    11. No expone credenciales en logs
    12. Registra intentos bloqueados
    """
    start_time = time.time()
    
    try:
        service = get_service()
        
        # FASE 4B: Verificar rol estricto
        role = user.get('role', '')
        if role not in ['SuperAdministrador', 'Administrador']:
            logger.warning(
                f"[CONSULTAS-SQL-SECURITY] Intento no autorizado de ejecutar. "
                f"User: {user.get('email')}, Role: {role}"
            )
            return EjecucionResponse(
                success=False,
                status="PERMISSION_DENIED",
                errors=["Solo Administrador/SuperAdministrador puede ejecutar consultas"]
            )
        
        # 1. Validar que se proporcione identificador (no SQL libre)
        if not request.codigo_consulta and not request.consulta_id:
            return EjecucionResponse(
                success=False,
                status="VALIDATION_FAILED",
                errors=["Debe proporcionar codigo_consulta o consulta_id. No se acepta SQL libre."]
            )
        
        # 2. Obtener consulta del catálogo
        consulta = service.obtener_consulta(
            consulta_id=request.consulta_id,
            codigo=request.codigo_consulta,
            include_sql=True
        )
        if not consulta:
            return EjecucionResponse(
                success=False,
                status="NOT_FOUND",
                errors=["Consulta no encontrada en catálogo EDARSAHUB"]
            )
        
        # 3. Verificar que esté activa
        if not consulta.activo:
            logger.warning(
                f"[CONSULTAS-SQL-SECURITY] Intento de ejecutar consulta inactiva. "
                f"User: {user.get('email')}, Consulta: {consulta.codigo_consulta}"
            )
            return EjecucionResponse(
                success=False,
                status="INACTIVE",
                errors=["Consulta inactiva - no permitida para ejecución"]
            )
        
        # 4. Verificar SoloLectura=1
        if not consulta.solo_lectura:
            logger.warning(
                f"[CONSULTAS-SQL-SECURITY] Intento de ejecutar consulta no SoloLectura. "
                f"User: {user.get('email')}, Consulta: {consulta.codigo_consulta}"
            )
            return EjecucionResponse(
                success=False,
                status="SECURITY_BLOCKED",
                errors=["Solo se permiten consultas de solo lectura (SoloLectura=1)"]
            )
        
        # FASE 4B: 5. Verificar PermiteEjecucionManual=1
        if not consulta.permite_ejecucion_manual:
            logger.warning(
                f"[CONSULTAS-SQL-SECURITY] Intento de ejecutar consulta no autorizada para ejecución manual. "
                f"User: {user.get('email')}, Consulta: {consulta.codigo_consulta}"
            )
            return EjecucionResponse(
                success=False,
                status="EXECUTION_NOT_ALLOWED",
                errors=["Esta consulta no está autorizada para ejecución manual (PermiteEjecucionManual=0)"]
            )
        
        # 6. Validar SQL con SQLSanitizer
        validation = SQLSanitizer.validate(consulta.consulta_sql)
        if not validation.is_safe:
            log_blocked_sql(
                validation, 
                endpoint="/api/consultas-sql/ejecutar", 
                user_email=user.get('email')
            )
            return EjecucionResponse(
                success=False,
                status="SQL_BLOCKED",
                errors=[f"SQL bloqueado por política de seguridad: {validation.blocked_reason}"]
            )
        
        # 7. Obtener información del servidor
        server_info = get_server_connection_info_with_secrets(request.servidor_id)
        if not server_info:
            return EjecucionResponse(
                success=False,
                status="SERVER_NOT_FOUND",
                errors=["Servidor no encontrado o no autorizado"]
            )
        
        # 8. Verificar que el servidor esté activo
        if not server_info.get('active', True):
            return EjecucionResponse(
                success=False,
                status="SERVER_INACTIVE",
                errors=["Servidor inactivo"]
            )
        
        # 9. Obtener parámetros definidos
        params_definidos = service._repo.get_parametros(consulta.consulta_id)
        params_nombres = {p.nombre_parametro for p in params_definidos}
        
        # 10. Verificar parámetros enviados - NO permitir parámetros no declarados
        params_enviados = request.parametros or {}
        params_extra = set(params_enviados.keys()) - params_nombres
        
        if params_extra:
            logger.warning(
                f"[CONSULTAS-SQL-SECURITY] Parámetros no autorizados detectados. "
                f"User: {user.get('email')}, Consulta: {consulta.codigo_consulta}, "
                f"Params extra: {list(params_extra)}"
            )
            return EjecucionResponse(
                success=False,
                status="INVALID_PARAMS",
                errors=[f"Parámetros no declarados en catálogo: {list(params_extra)}"]
            )
        
        # 11. Verificar parámetros requeridos
        for p in params_definidos:
            if p.requerido and p.nombre_parametro not in params_enviados:
                if p.valor_default is None:
                    return EjecucionResponse(
                        success=False,
                        status="MISSING_PARAMS",
                        errors=[f"Parámetro requerido faltante: {p.nombre_parametro}"]
                    )
        
        # 12. Preparar SQL con parámetros (escapando valores)
        sql_final = consulta.consulta_sql
        for param_name, param_value in params_enviados.items():
            # Escapar valor para prevenir SQL injection
            if param_value is None:
                safe_value = "NULL"
            elif isinstance(param_value, str):
                safe_value = f"'{param_value.replace(chr(39), chr(39)+chr(39))}'"
            elif isinstance(param_value, (int, float)):
                safe_value = str(param_value)
            else:
                safe_value = f"'{str(param_value).replace(chr(39), chr(39)+chr(39))}'"
            
            sql_final = sql_final.replace(f"{{{param_name}}}", safe_value)
        
        # FASE 4B: 13. Aplicar límite máximo reducido (5000 en lugar de 10000)
        MAX_ROWS = 5000
        limit = min(request.limit, MAX_ROWS)
        sql_upper = sql_final.upper().strip()
        if sql_upper.startswith('SELECT') and 'TOP' not in sql_upper[:50]:
            sql_final = sql_final.replace('SELECT', f'SELECT TOP {limit}', 1)
        
        # 14. Ejecutar consulta
        try:
            rows = execute_sql_query(
                host=server_info['host'],
                port=server_info['port'],
                database=server_info['database'],
                username=server_info['username'],
                password=server_info['password'],
                query=sql_final
            )
        except Exception as exec_error:
            # FASE 4B: No loggear detalles de conexión
            logger.error(
                f"[CONSULTAS-SQL] Error ejecutando. User: {user.get('email')}, "
                f"Consulta: {consulta.codigo_consulta}, Error: {str(exec_error)[:100]}"
            )
            return EjecucionResponse(
                success=False,
                status="EXECUTION_ERROR",
                errors=["Error de ejecución - contacte al administrador"]
            )
        
        # 15. Calcular tiempo
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # 16. Obtener columnas
        columns = list(rows[0].keys()) if rows else []
        
        logger.info(
            f"[CONSULTAS-SQL] Ejecución exitosa. User: {user.get('email')}, "
            f"Consulta: {consulta.codigo_consulta}, Server: {request.servidor_id[:8]}..., "
            f"Rows: {len(rows)}, Time: {elapsed_ms}ms"
        )
        
        return EjecucionResponse(
            success=True,
            status="SUCCESS",
            source=EjecucionSource(
                type="EDARSAHUB_SQL_CATALOGO",
                codigo_consulta=consulta.codigo_consulta,
                servidor_id=request.servidor_id,
                system_type=server_info.get('system_type', 'UNKNOWN'),
                generated_at=datetime.now(timezone.utc).isoformat(),
            ),
            columns=columns,
            rows=rows,
            row_count=len(rows),
            elapsed_ms=elapsed_ms,
            warnings=[f"Límite aplicado: {limit} filas máximo"] if len(rows) == limit else [],
            errors=[],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error inesperado: {e}")
        return EjecucionResponse(
            success=False,
            status="ERROR",
            errors=[f"Error interno: {str(e)[:100]}"]
        )


@router.get("/sistemas", response_model=SistemasResponse)
async def listar_sistemas(
    user: Dict = Depends(require_permission("VER_CATALOGO"))
):
    """
    Lista sistemas disponibles para filtros.
    
    Sistemas:
    - SOFTRESTAURANT_PRO (SistemaTipoID=1)
    - MPRO (SistemaTipoID=2)
    - ENTERPRISE (SistemaTipoID=6)
    """
    try:
        repo = get_repository()
        counts = repo.get_counts()
        
        sistemas = [
            SistemaItem(
                sistema_tipo_id=1,
                codigo="SOFTRESTAURANT_PRO",
                nombre="SoftRestaurant Pro",
                count_consultas=counts.get('consultas_softrestaurant', 0)
            ),
            SistemaItem(
                sistema_tipo_id=2,
                codigo="MPRO",
                nombre="ManagementPro",
                count_consultas=counts.get('consultas_mpro', 0)
            ),
        ]
        
        return SistemasResponse(
            success=True,
            sistemas=sistemas
        )
        
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error listando sistemas: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.get("/modulos", response_model=ModulosResponse)
async def listar_modulos(
    user: Dict = Depends(require_permission("VER_CATALOGO"))
):
    """
    Lista módulos/categorías disponibles.
    """
    try:
        repo = get_repository()
        service = get_service()
        
        modulos_nombres = repo.get_modulos()
        
        # Contar consultas por módulo
        modulos = []
        for nombre in modulos_nombres:
            consultas = service.listar_consultas(modulo=nombre, limit=500)
            modulos.append(ModuloItem(
                nombre=nombre,
                count_consultas=len(consultas)
            ))
        
        return ModulosResponse(
            success=True,
            modulos=modulos
        )
        
    except Exception as e:
        logger.error(f"[CONSULTAS-SQL] Error listando módulos: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_consultas_sql_router() -> APIRouter:
    """Retorna el router de consultas SQL."""
    return router
