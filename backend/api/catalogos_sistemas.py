"""
EDARSA HUB - Endpoints de Catálogo de Sistemas y Capacidades
============================================================
FASE 5 del Catálogo Maestro de Sistemas y Capacidades SQL-First.

Endpoints para consultar sistemas, capacidades, variantes y visibilidad
usando SystemCapabilityResolver.

ENDPOINTS:
- GET /api/catalogos/sistemas - Lista todos los sistemas activos
- GET /api/catalogos/sistemas/explorables - Sistemas con EXPLORADOR_BD
- GET /api/catalogos/sistemas/sync-ventas - Sistemas con SYNC_VENTAS_*
- GET /api/catalogos/sistemas/normalizar/{system_type} - Normalizar variante
- GET /api/catalogos/sistemas/diagnostico/{system_type} - Diagnóstico completo
- GET /api/catalogos/sistemas/capacidades/{capacidad} - Sistemas por capacidad
- GET /api/catalogos/sistemas/meta/capacidades-disponibles - Lista capacidades
- GET /api/catalogos/sistemas/meta/modulos-disponibles - Lista módulos
- GET /api/catalogos/sistemas/{codigo_sistema} - Detalle de un sistema
- GET /api/catalogos/sistemas/{codigo_sistema}/capacidades - Capacidades de un sistema

REGLAS:
- EDARSAHUB SQL es la fuente primaria (via SystemCapabilityResolver)
- NO usar MongoDB
- NO exponer secrets (passwords, api_keys, connection strings)
- Autenticación requerida en todos los endpoints

IMPORTANTE: Las rutas con parámetros dinámicos van AL FINAL para evitar
conflictos con rutas fijas como /explorables, /sync-ventas, etc.

Autor: Arquitecto Senior Backend
Fecha: 2025-12-XX
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, List, Any, Optional
import logging

from core.system_capability_resolver import (
    SystemCapabilityResolver,
    Capability,
    Module,
    get_resolver
)
from core.security import verify_token

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Router - NOTA: El prefijo NO incluye /api porque api_router ya lo tiene
router = APIRouter(
    prefix="/catalogos/sistemas-capacidades",
    tags=["Catálogo de Sistemas y Capacidades"]
)


# ============================================================================
# AUTENTICACIÓN
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
        logger.warning(f"[CATALOGOS-SISTEMAS-AUTH] Error verificando token: {e}")
        raise HTTPException(status_code=401, detail="No autenticado")


def check_catalogo_permission(user: Dict) -> bool:
    """
    Verifica permiso para catálogo de sistemas.
    
    FASE 5: Acceso a usuarios autenticados con roles Admin.
    Los datos del catálogo no son sensibles, pero requieren autenticación.
    """
    role = user.get('role', '')
    
    # Roles permitidos (todos los que pueden ver el sistema)
    allowed_roles = ['SuperAdministrador', 'Administrador', 'Gerente', 'Supervisor']
    
    return role in allowed_roles


def require_auth():
    """Dependency para requerir autenticación."""
    async def dependency(user: Dict = Depends(get_current_user_from_token)):
        if not check_catalogo_permission(user):
            logger.warning(
                f"[CATALOGOS-SISTEMAS-RBAC] Acceso denegado. User: {user.get('email')}, "
                f"Role: {user.get('role')}"
            )
            raise HTTPException(
                status_code=403, 
                detail="No tiene permiso para acceder al catálogo de sistemas"
            )
        return user
    return dependency


# ============================================================================
# SCHEMAS DE RESPUESTA
# ============================================================================

def success_response(data: Any, message: str = "OK") -> Dict:
    """Respuesta exitosa estándar."""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message: str, code: str = "ERROR") -> Dict:
    """Respuesta de error estándar."""
    return {
        "success": False,
        "message": message,
        "error_code": code,
        "data": None
    }


# ============================================================================
# ENDPOINTS - RUTAS FIJAS (deben ir PRIMERO)
# ============================================================================

@router.get("")
async def listar_sistemas(
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista todos los sistemas activos.
    
    Retorna:
    - Lista de sistemas con código, nombre y descripción
    - NO incluye passwords ni secrets
    """
    try:
        resolver = get_resolver()
        sistemas = resolver.get_all_systems()
        
        return success_response(
            data=sistemas,
            message=f"{len(sistemas)} sistemas encontrados"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas] Error listando sistemas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo lista de sistemas"
        )


@router.get("/explorables")
async def listar_sistemas_explorables(
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista sistemas que soportan EXPLORADOR_BD.
    
    Estos sistemas pueden aparecer en el Explorador de Base de Datos.
    
    IMPORTANTE:
    - API_LOCAL (Enterprise) SÍ aparece aquí
    - Basado en capacidad EXPLORADOR_BD activa
    """
    try:
        resolver = get_resolver()
        sistemas = resolver.get_explorable_systems()
        
        return success_response(
            data=sistemas,
            message=f"{len(sistemas)} sistemas explorables"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas/explorables] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo sistemas explorables"
        )


@router.get("/explorables-dinamico")
async def listar_sistemas_explorables_dinamico(
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista proveedores/sistemas DINÁMICAMENTE desde servidores explorables activos.
    
    FIX P0 (May-2026): Este endpoint devuelve los system_type DISTINTOS de los
    servidores explorables, para usar como opciones del primer filtro del Explorador BD.
    
    A diferencia de /explorables que lee de Sistema_Tipos (catálogo cerrado),
    este endpoint lee directamente de Servidores_Conexiones (datos reales).
    
    Ejemplo de respuesta (actualizado Mayo 2026):
    - MPRO: ManagementPro
    - ENTERPRISE: Enterprise
    - SOFTRESTAURANT_PRO: SoftRestaurant Pro
    """
    from modules.comercial.repository import EDARSAHUB_CONFIG
    from core.db import execute_sql_query
    
    try:
        query = """
        SELECT DISTINCT 
            sc.system_type as codigo_sistema,
            CASE 
                WHEN UPPER(sc.system_type) = 'ENTERPRISE' THEN 'Enterprise'
                WHEN UPPER(sc.system_type) = 'SOFRESATAURANT_ENTER' THEN 'Enterprise'
                WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT_PRO' THEN 'SoftRestaurant Pro'
                WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT' THEN 'SoftRestaurant Pro'
                WHEN UPPER(sc.system_type) IN ('SOFT_RESTAURANT', 'SR') THEN 'SoftRestaurant Pro'
                WHEN UPPER(sc.system_type) = 'MPRO' THEN 'ManagementPro'
                WHEN UPPER(sc.system_type) IN ('MANAGEMENTPRO', 'MANAGMENTPRO') THEN 'ManagementPro'
                WHEN UPPER(sc.system_type) IN ('EDARSA_HUB', 'EDARSAHUB', 'EDARSAHUB_SQL') THEN 'EDARSAHUB SQL Server'
                ELSE sc.system_type
            END as nombre_sistema
        FROM Servidores_Conexiones sc
        WHERE sc.activo = 1
          AND (
            sc.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
            OR (sc.tipo_conexion = 'API_LOCAL' AND sc.api_url IS NOT NULL)
            OR sc.tipo_conexion IS NULL
          )
        ORDER BY sc.system_type
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        sistemas = []
        for row in results:
            sistemas.append({
                'codigo_sistema': row.get('codigo_sistema', ''),
                'nombre_sistema': row.get('nombre_sistema', '')
            })
        
        logger.info(f"[catalogos/sistemas/explorables-dinamico] {len(sistemas)} proveedores/sistemas")
        return success_response(
            data=sistemas,
            message=f"{len(sistemas)} proveedores/sistemas explorables"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas/explorables-dinamico] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo proveedores/sistemas explorables"
        )


@router.get("/sync-ventas")
async def listar_sistemas_sync_ventas(
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista sistemas que soportan sincronización de ventas.
    
    Estos sistemas tienen capacidades SYNC_VENTAS_* activas.
    
    IMPORTANTE:
    - API_LOCAL (Enterprise) NO aparece aquí (no tiene query_ventas validada)
    - Solo SOFTRESTAURANT y MPRO actualmente
    - Basado en capacidades SYNC_VENTAS_HISTORICAS, SYNC_VENTAS_POR_HORA, SYNC_VENTAS_DIA_SEMANA
    """
    try:
        resolver = get_resolver()
        sistemas = resolver.get_sync_sales_systems()
        
        return success_response(
            data=sistemas,
            message=f"{len(sistemas)} sistemas con sync de ventas"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas/sync-ventas] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo sistemas con sync de ventas"
        )


@router.get("/meta/capacidades-disponibles")
async def listar_capacidades_disponibles(
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista todas las capacidades disponibles en el sistema.
    
    Útil para UI de administración.
    """
    capacidades = [
        {"codigo": cap.value, "nombre": cap.name.replace("_", " ").title()}
        for cap in Capability
    ]
    
    return success_response(
        data=capacidades,
        message=f"{len(capacidades)} capacidades disponibles"
    )


@router.get("/meta/modulos-disponibles")
async def listar_modulos_disponibles(
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista todos los módulos disponibles para visibilidad.
    
    Útil para UI de administración.
    """
    modulos = [
        {"codigo": mod.value, "nombre": mod.name.replace("_", " ").title()}
        for mod in Module
    ]
    
    return success_response(
        data=modulos,
        message=f"{len(modulos)} módulos disponibles"
    )


# ============================================================================
# ENDPOINTS - RUTAS CON PARÁMETROS EN SUBRUTAS (van después de las fijas)
# ============================================================================

@router.get("/normalizar/{system_type}")
async def normalizar_system_type(
    system_type: str,
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Normaliza un system_type a su código canónico.
    
    Ejemplos:
    - ManagmentPro -> MPRO
    - SOFRESATAURANT_ENTER -> API_LOCAL
    - SoftRestaurant -> SOFTRESTAURANT
    - SR -> SOFTRESTAURANT
    
    Retorna:
    - codigo_sistema: Código normalizado
    - nombre_sistema: Nombre legible
    - found: True si se encontró en catálogo
    - source: 'sql' si viene de EDARSAHUB, 'fallback_legacy' si usa system_type_utils.py
    """
    try:
        resolver = get_resolver()
        resultado = resolver.normalize_system_type(system_type)
        
        return success_response(
            data=resultado,
            message="Normalización completada"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas/normalizar] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error normalizando system_type"
        )


@router.get("/diagnostico/{system_type}")
async def diagnostico_sistema(
    system_type: str,
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Diagnóstico completo de un sistema.
    
    Incluye:
    - Normalización del system_type
    - Capacidades activas
    - Visibilidad por módulo
    - Indicadores de soporte (explorador, sync ventas)
    - Diagnóstico legible
    
    Útil para debugging y verificación de configuración.
    """
    try:
        resolver = get_resolver()
        resultado = resolver.explain_system(system_type)
        
        return success_response(
            data=resultado,
            message="Diagnóstico completado"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas/diagnostico] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en diagnóstico del sistema"
        )


@router.get("/capacidades/{capacidad}")
async def listar_sistemas_por_capacidad(
    capacidad: str,
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista sistemas que soportan una capacidad específica.
    
    Capacidades disponibles:
    - EXPLORADOR_BD, EXPLORADOR_TABLAS, EXPLORADOR_COLUMNAS, EXPLORADOR_PREVIEW
    - SYNC_VENTAS_HISTORICAS, SYNC_VENTAS_POR_HORA, SYNC_VENTAS_DIA_SEMANA
    - VENTAS_DIA, VENTAS_PERIODO
    - COMPRAS, INVENTARIOS, CORTES_Z, REPORTES
    - CATALOGO_SQL, SUCURSALES_VISIBLES, CUENTAS_POR_PAGAR
    """
    try:
        resolver = get_resolver()
        sistemas = resolver.get_systems_for_capability(capacidad)
        
        if not sistemas:
            return success_response(
                data=[],
                message=f"No hay sistemas con capacidad '{capacidad}'"
            )
        
        return success_response(
            data=sistemas,
            message=f"{len(sistemas)} sistemas con capacidad '{capacidad}'"
        )
    except Exception as e:
        logger.error(f"[catalogos/sistemas/capacidades/{capacidad}] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo sistemas por capacidad"
        )


# ============================================================================
# ENDPOINTS - RUTAS CON PARÁMETROS DINÁMICOS (van AL FINAL)
# ============================================================================

@router.get("/{codigo_sistema}/capacidades")
async def listar_capacidades_sistema(
    codigo_sistema: str,
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Lista capacidades activas de un sistema específico.
    
    Retorna lista de capacidades con:
    - codigo: Código de la capacidad
    - descripcion: Descripción legible
    - requiere_api_local: Si requiere API local
    - requiere_sql_directo: Si requiere conexión SQL directa
    """
    try:
        resolver = get_resolver()
        capacidades = resolver.get_capabilities(codigo_sistema)
        
        if not capacidades:
            # Verificar si el sistema existe
            normalized = resolver.normalize_system_type(codigo_sistema)
            if not normalized.get('found'):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sistema '{codigo_sistema}' no encontrado"
                )
            return success_response(
                data=[],
                message=f"Sistema '{codigo_sistema}' no tiene capacidades configuradas"
            )
        
        return success_response(
            data=capacidades,
            message=f"{len(capacidades)} capacidades para '{codigo_sistema}'"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[catalogos/sistemas/{codigo_sistema}/capacidades] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo capacidades"
        )


@router.get("/{codigo_sistema}")
async def obtener_sistema(
    codigo_sistema: str,
    current_user: Dict = Depends(require_auth())
) -> Dict:
    """
    Obtiene detalle de un sistema específico.
    
    Retorna:
    - Información del sistema
    - Lista de capacidades
    - Visibilidad por módulo
    - Indicadores de soporte
    """
    try:
        resolver = get_resolver()
        
        # Usar explain_system para obtener información completa
        resultado = resolver.explain_system(codigo_sistema)
        
        if not resultado.get('found'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sistema '{codigo_sistema}' no encontrado"
            )
        
        return success_response(
            data=resultado,
            message=f"Sistema '{codigo_sistema}' encontrado"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[catalogos/sistemas/{codigo_sistema}] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo sistema"
        )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['router']
