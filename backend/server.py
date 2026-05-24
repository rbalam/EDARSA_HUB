# Fix encoding para supervisor - DEBE estar antes de cualquier otro import
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
# MongoDB import movido a bloque condicional más abajo
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import pymssql
import pytds  # Biblioteca alternativa para conexiones SQL Server problemáticas
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment
import base64

# Importar catálogos de consultas
from catalogo.consultas_mpro import CONSULTAS_MPRO, ESTRUCTURA_TABLAS_MPRO
from catalogo.consultas_softrestaurant import CONSULTAS_SOFTRESTAURANT, ESTRUCTURA_TABLAS_SOFTRESTAURANT
from catalogo.catalogo_consultas import CATALOGO_CONSULTAS, get_consultas_por_categoria as catalogo_get_consultas, get_categorias as catalogo_get_categorias, preparar_sql as catalogo_preparar_sql

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logger temprano para mensajes de inicio
logger = logging.getLogger(__name__)

# ============================================================================
# CONEXIÓN A BASE DE DATOS - 100% SQL SERVER
# ============================================================================
# 
# MÁXIMA EDARSAHUB: SQL Server es el cerebro. MongoDB ELIMINADO.
# 
# Todos los módulos funcionan exclusivamente con EDARSAHUB SQL Server.
# Variable 'db' se mantiene como StubDatabase para compatibilidad con código legacy.
# Los accesos a colecciones MongoDB retornan valores vacíos sin fallar.
#
# ============================================================================

# MongoDB ELIMINADO - Usar StubDatabase para evitar errores en código legacy
from core.mongo_stub import get_stub_database
db = get_stub_database()
logger.info("[DB] Sistema funcionando 100% SQL Server - MongoDB ELIMINADO (usando StubDatabase)")

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============= SEGURIDAD Y AUTENTICACIÓN =============
# 
# FASE 2 DEL REFACTOR MODULAR (Diciembre 2025):
# Las funciones de seguridad han sido migradas a /core/security.py
# Este bloque importa y re-exporta para compatibilidad con código existente.
#
# Funciones migradas:
#   - hash_password(), verify_password()
#   - create_token(), verify_token()
#   - get_current_user()
#   - user_has_server_access()
#   - filter_servers_by_permissions()
#   - filter_sucursales_by_permissions()
#   - JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
#   - security (HTTPBearer)
#
# LIMPIEZA FUTURA: Los re-exports pueden eliminarse cuando todos los imports
# en server.py sean actualizados para usar directamente core.security
# =============================================================================

from core.security import (
    # Configuración JWT
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    security,
    # Hashing
    hash_password,
    verify_password,
    # JWT
    create_token,
    verify_token,
    # Dependency
    get_current_user,
    # Permisos - Legacy
    user_has_server_access,
    filter_servers_by_permissions,
    filter_sucursales_by_permissions,
    # Permisos - FASE 3 (nuevo modelo)
    get_user_empresas_permitidas,
    get_servers_for_empresas,
    user_has_empresa_access,
    filter_by_user_context,
    # Inicialización
    init_security,
)

# FASE 6-8: Importar función centralizada de contexto de acceso
from core.user_access_context import (
    resolve_user_access_context,
    has_server_access,
    has_empresa_access,
    has_almacen_access,
    has_permiso,
    UserAccessContext,
    # FASE 8: Enforcement de Almacenes
    get_almacenes_permitidos,
    get_almacenes_sql_filter,
    get_almacenes_sql_filter_like,
    validate_almacen_in_scope,
    filter_results_by_almacen,
)

# Inicializar módulo de seguridad (100% SQL)
init_security(None)  # MongoDB eliminado

# ============================================================================
# FASE 6-8: HELPER DE VALIDACIÓN RBAC CENTRALIZADA
# ============================================================================

async def validate_server_access_unified(current_user: Dict, server_id: str) -> UserAccessContext:
    """
    Validación unificada de acceso a servidor usando resolve_user_access_context().
    
    FASE 6-8: Esta función es la ÚNICA que debe usarse para validar acceso a servidores.
    NUNCA confía en parámetros del frontend.
    
    Args:
        current_user: Usuario autenticado
        server_id: ID del servidor a validar
        
    Returns:
        UserAccessContext si tiene acceso
        
    Raises:
        HTTPException 403 si no tiene acceso
    """
    context = await resolve_user_access_context(current_user)
    
    if has_server_access(context, server_id):
        return context
    
    logging.warning(
        f"[RBAC-DENEGADO] Usuario {current_user.get('email')} "
        f"sin acceso a servidor {server_id}. "
        f"Fuente: {context.fuente_acceso}"
    )
    raise HTTPException(
        status_code=403, 
        detail=f"No tiene acceso a este servidor"
    )


# ============= MÓDULOS (FASE 3) =============
# Inicialización de módulos migrados desde server.py
# 
# MÓDULO AUTH: Autenticación, usuarios y roles
# - Migrado en Fase 3 del refactor modular
# - Endpoints: /auth/*, /users/*, /roles/*
# ===========================================

from modules.auth import get_router as get_auth_router, init_auth_module

# Inicializar módulo auth (100% SQL Server)
init_auth_module(db)  # Pasa StubDatabase para compatibilidad

# Registrar router de auth
api_router.include_router(get_auth_router())

# ============================================================================
# INICIALIZACIÓN REFRESH TOKENS (SQL Server)
# ============================================================================
from core.refresh_tokens import init_refresh_tokens_module

# Configuración EDARSAHUB para refresh tokens
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}
init_refresh_tokens_module(EDARSAHUB_CONFIG)
logger.info("Módulo refresh_tokens inicializado con SQL Server")


# ============================================================================
# FASE 3C.1: HELPER DE DESCIFRADO DE SECRETOS PARA SERVIDORES
# ============================================================================

def decrypt_server_secrets(server: Optional[Dict]) -> Optional[Dict]:
    """
    Descifra los secretos de un servidor obtenido de MongoDB/SQL.
    
    FASE 3C.1: Esta función DEBE usarse después de obtener un servidor
    que se va a usar para conexión SQL/API.
    
    Args:
        server: Diccionario del servidor (puede tener password/api_key cifrados)
        
    Returns:
        Servidor con secrets descifrados para uso interno del backend.
        NUNCA devolver este resultado al frontend.
    """
    if not server:
        return server
    
    try:
        from core.secret_manager import decrypt_secret, is_encrypted_secret
        
        # Descifrar password
        password = server.get('password') or server.get('password_encrypted', '')
        if password and is_encrypted_secret(password):
            server['password'] = decrypt_secret(password)
        elif password:
            # Es legacy plaintext - usar tal cual
            server['password'] = password
        
        # Descifrar api_key si existe
        api_key = server.get('api_key') or server.get('api_key_encrypted', '')
        if api_key and is_encrypted_secret(api_key):
            server['api_key'] = decrypt_secret(api_key)
        elif api_key:
            server['api_key'] = api_key
            
    except Exception as e:
        logging.error(f"[SECRET_DECRYPT_ERROR] Error descifrando secretos de servidor {server.get('id', 'N/A')}: {type(e).__name__}")
    
    return server


# ============================================================================


# MÓDULO COMPRAS: Estado de migración
# - Fase 4B: Los endpoints de compras permanecen en server.py por complejidad
# - La estructura del módulo (schemas, repository, service) está lista
# - Los endpoints se migrarán gradualmente en fases posteriores
# - Por ahora, server.py sigue siendo la fuente de verdad para compras
# ===========================================

from modules.compras import init_compras_module
# FASE P0 SQL-Only: Importar servicio de sincronización para lectura desde EDARSAHUB
from modules.compras.sync_service import (
    obtener_inventarios_fisicos_sync,
    obtener_requisiciones_sync,
)
# FASE 3A.1: Importar utilidades de normalización desde CORE (fuente de verdad)
from core.system_type_utils import (
    normalize_system_type,
    is_mpro_system,
    is_softrestaurant_system,
    is_api_system,
    is_supported_system_type,
    get_unsupported_system_response,
    get_not_available_response,
)
# Importar helpers de logging de compras
from modules.compras.system_type_utils import (
    log_compras_adapter_selected,
    log_compras_query_result,
    log_compras_error,
)

# Inicializar módulo compras (100% SQL Server)
init_compras_module(None)  # MongoDB eliminado

# MÓDULO COMERCIAL: Dashboard comercial, tablero ejecutivo, metas
# - Fase 5B: Migración en progreso
# - Adapters (APIs locales MPRO) migrados a modules/comercial/adapters.py
# - Endpoints permanecen temporalmente en server.py
# ===========================================

from modules.comercial import init_comercial_module
from modules.comercial.adapters import (
    APIS_MPRO_LOCALES,
    query_api_mpro_local,
    obtener_ventas_dia_api_local,
    sumar_ventas_api_local_a_sucursal,
)

# FASE 5B-2: Import de helpers del tablero ejecutivo desde service
from modules.comercial.service import (
    get_kpis_softrestaurant,
    get_kpis_mpro,
    get_kpis_mpro_por_sucursal,
)

# FASE 5B-3: Import del módulo comercial (lazy router)
from modules.comercial import get_router as get_comercial_router

# Inicializar módulo comercial (100% SQL Server)
init_comercial_module(None)  # MongoDB eliminado

# FASE 5B-3: Registrar router de comercial (después de inicializar el módulo)
api_router.include_router(get_comercial_router())

# MÓDULO RECURSOS HUMANOS: Catálogos RH
# - Fase 6B: Migración de catálogos (Puestos, Sucursales, Tipos Incidencias)
# - 10 endpoints migrados con queries parametrizados
# - Validación Pydantic implementada
# ===========================================

from modules.rh import init_rh_module, get_router as get_rh_router, get_importador_router as get_rh_importador_router
from modules.rh.solicitudes_catalogo import router as rh_solicitudes_router
from modules.finanzas.cuentas_por_pagar import router as cxp_router
from modules.finanzas.ingresos import router as ingresos_router
from modules.finanzas.tesoreria import router as tesoreria_router
from modules.finanzas.health import router as finanzas_health_router

# P1-FASE5A.1: Cuentas y Saldos Bancarios (EDARSAHUB)
# - Mayo 2026: Implementación endpoints backend
# - Fuente única: EDARSAHUB (no MongoDB)
# - Datos sensibles siempre enmascarados
from modules.finanzas.cuentas_bancarias import router as cuentas_bancarias_router
from modules.finanzas.saldos_bancarios import router as saldos_bancarios_router

# MÓDULO PROPINAS TPV: Control y cuadre de comisión sobre propinas TPV (2%)
# - CAB Aprobado: 2026-04-14
# - Arquitectura SQL: 2026-04-15 (ARQUITECTURA_PROPINAS_TPV_v3.md)
# - FASE 1 MVP: Solo SoftRestaurant (La Estelar, Cienfuegos, 130 Mérida)
# - FUERA DE ALCANCE: MPRO (pendiente para fase posterior)
# - Documentos: /app/docs/CAB_MODULO_PROPINAS_TPV.md
# - ARQUITECTURA: SQL Server (persistencia) + MongoDB (cache)
# - IMPORTANTE: NO interfiere con /api/finanzas/tesoreria/* (tab Cuadre Z protegido)
from modules.finanzas.propinas_tpv import get_router_sql as get_propinas_tpv_router

# MÓDULO CATÁLOGOS: Módulo maestro centralizado de catálogos
# - Diciembre 2025: Implementación inicial
# - Acceso central y contextual desde módulos
from modules.catalogos import get_router as get_catalogos_router, init_catalogos_module
from modules.catalogos.service import init_catalogos_service

# MÓDULO FINANZAS: Repositorio real de SQL Server
# - Abril 2026: Conexión a tablas reales de Finanzas
from modules.finanzas.repository_real import FinanzasRepositoryReal
from modules.finanzas import ingresos as finanzas_ingresos
from modules.finanzas import cuentas_por_pagar as finanzas_cxp
from modules.finanzas.repository_mpro import FinanzasRepositoryMPRO
from modules.finanzas.repository_softrestaurant import FinanzasRepositorySoftRestaurant

# Módulo de Manuales Operativos (Modelo Cienfuegos)
from modules.manuales_operativos import get_router as get_manuales_router, init_manuales_module
from modules.manuales_operativos.triggers import trigger_generar_manual, ESTADOS_TRIGGER

# Inicializar módulo de Manuales Operativos (100% SQL)
init_manuales_module(None)  # MongoDB eliminado

# Inicializar módulo RH (100% SQL)
init_rh_module(None)  # MongoDB eliminado

# Inicializar módulo de Catálogos (100% SQL)
init_catalogos_module(None)  # MongoDB eliminado
init_catalogos_service(None)  # MongoDB eliminado

# Inicializar repositorios de Finanzas (100% SQL)
_finanzas_repo = FinanzasRepositoryReal(None)  # MongoDB eliminado
finanzas_ingresos.set_finanzas_repository(_finanzas_repo)
finanzas_cxp.set_finanzas_repository(_finanzas_repo)

# MPRO (para cuentas por pagar - fallback)
_mpro_repo = FinanzasRepositoryMPRO(None)  # MongoDB eliminado
finanzas_cxp.set_mpro_repository(_mpro_repo)

# SOFTRESTAURANT (CF, Estelar, 130 Mid - principal para CxP)
_softrest_repo = FinanzasRepositorySoftRestaurant(None)  # MongoDB eliminado
finanzas_cxp.set_softrestaurant_repository(_softrest_repo)

# FASE 6B: Registrar router de RH (catálogos)
api_router.include_router(get_rh_router())

# FASE IMPORTACIÓN: Registrar router de importación RH
api_router.include_router(get_rh_importador_router())

# FASE SOLICITUDES: Registrar router de solicitudes de catálogo
api_router.include_router(rh_solicitudes_router)

# FASE FINANZAS: Registrar router de cuentas por pagar
api_router.include_router(cxp_router)

# FASE FINANZAS: Registrar router de ingresos
api_router.include_router(ingresos_router)

# FASE TESORERÍA: Registrar router de tesorería (Cuadre Cortes Z)
api_router.include_router(tesoreria_router)

# FASE DIAGNÓSTICO: Registrar router de health check de Finanzas
api_router.include_router(finanzas_health_router)

# P1-FASE5A.1: Registrar routers de Cuentas y Saldos Bancarios
# Endpoints: /api/v2/finanzas/cuentas-bancarias/*, /api/v2/finanzas/saldos-bancarios/*, /api/v2/finanzas/bancos
# FUENTE: EDARSAHUB (no MongoDB)
# IMPORTANTE: Datos sensibles siempre enmascarados
api_router.include_router(cuentas_bancarias_router)
api_router.include_router(saldos_bancarios_router)

# MÓDULO CATÁLOGOS: Registrar router de catálogos
api_router.include_router(get_catalogos_router())

# ============================================================================
# FASE 5 ARQ: Catálogo Maestro de Sistemas y Capacidades SQL-First
# Endpoints: /api/catalogos/sistemas/*
# FUENTE: EDARSAHUB (Sistema_Tipos, Sistema_Capacidades, etc.)
# NO usa MongoDB
# ============================================================================
from api.catalogos_sistemas import router as catalogos_sistemas_router
api_router.include_router(catalogos_sistemas_router)

# MÓDULO PROPINAS TPV: Registrar router de propinas TPV (FASE 1 MVP - Solo SoftRestaurant)
# Endpoints bajo /api/finanzas/propinas/*
# ARQUITECTURA: SQL Server EDARSA HUB (persistencia) + MongoDB (cache)
# AISLAMIENTO: NO interfiere con /api/finanzas/tesoreria/* (Tab Cuadre Z PROTEGIDO)
api_router.include_router(get_propinas_tpv_router())

# SUBFASE 3.4: Router EDARSAHUB v2 para Propinas TPV
# Endpoints bajo /api/finanzas/propinas/v2/*
# Fuente de verdad: EDARSAHUB.propinas_tpv_control
from modules.finanzas.propinas_tpv import get_router_edarsahub as get_propinas_tpv_edarsahub_router
api_router.include_router(get_propinas_tpv_edarsahub_router())

# Manuales Operativos (Modelo Cienfuegos) - Generación automática de documentación
api_router.include_router(get_manuales_router())

# ============================================================================
# FASE 1 SYNC AGENT - Endpoints para recibir datos de agentes externos
# ============================================================================
from api.sync_receiver import router as sync_receiver_router, init_sync_receiver
from modules.comercial.kpis_repository import init_kpis_repository
init_sync_receiver(None)  # MongoDB eliminado
init_kpis_repository(None)  # MongoDB eliminado
api_router.include_router(sync_receiver_router)

# ============================================================================
# MÓDULO API CONNECTIONS: CRUD de conexiones a APIs locales
# ============================================================================
from modules.api_connections import api_connections_router
from modules.api_connections.repository import init_api_connections_repository
from modules.api_connections.routes import set_verify_token
init_api_connections_repository(None)  # MongoDB eliminado
set_verify_token(verify_token)
api_router.include_router(api_connections_router)

# ============================================================================
# FASE API-UQT1: Universal Query Tester para Conexiones API
# Endpoint AISLADO: /api/api-connections/{connection_id}/universal-query-test
# FUENTE: EDARSAHUB.Servidores_Conexiones (tipo_conexion = 'API_LOCAL')
# NO modifica endpoint SQL existente
# ============================================================================
from modules.api_connections import api_universal_test_router, set_api_uqt_verify_token
set_api_uqt_verify_token(verify_token)
api_router.include_router(api_universal_test_router)

# ============================================================================
# MÓDULO UNIVERSAL QUERY TESTER: Herramienta agnóstica de diagnóstico
# Permite probar consultas SQL/API contra cualquier origen de datos
# NO asume dominio, NO persiste resultados, Solo lectura (SELECT/GET)
# ============================================================================
from modules.universal_query import router as universal_query_router
api_router.include_router(universal_query_router)

# ============================================================================
# FASE 4: Consultas SQL - Endpoints /api/consultas-sql/*
# Expone módulo SQL-First de forma controlada y segura
# ============================================================================
from modules.consultas_sql import get_consultas_sql_router
api_router.include_router(get_consultas_sql_router())

# ============================================================================
# FASE 4E: Cache Management Endpoints (Admin Only)
# ============================================================================
from modules.comercial.cache_service import cleanup_expired_cache, get_cache_stats, init_cache_service

# Cache service (100% SQL - MongoDB eliminado)
init_cache_service(None)

@api_router.get("/admin/cache/stats")
async def admin_cache_stats(current_user: dict = Depends(get_current_user)):
    """
    Obtiene estadísticas del cache comercial.
    Requiere autenticación.
    """
    stats = await get_cache_stats()
    return {"success": True, "stats": stats}

@api_router.post("/admin/cache/cleanup")
async def admin_cache_cleanup(
    max_age_hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """
    Limpia entradas de cache expiradas.
    Solo administradores y supervisores pueden ejecutar esta acción.
    
    Args:
        max_age_hours: Máximo de horas para considerar un cache como expirado (default 24h)
    """
    # Verificar rol de administrador
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador", "Supervisor"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden limpiar cache")
    
    result = await cleanup_expired_cache(max_age_hours)
    return result


@api_router.post("/admin/sync/compras")
async def admin_sync_compras_manual(
    dry_run: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Ejecuta manualmente la sincronización de Compras (Inventarios y Requisiciones).
    
    FASE P0 SQL-ONLY: Este job sincroniza datos desde servidores físicos hacia EDARSAHUB SQL.
    Los endpoints de compras luego leen de las tablas sincronizadas.
    
    Args:
        dry_run: Si True, solo lista servidores sin ejecutar sincronización
    
    Returns:
        Resultado de la sincronización con detalles por servidor
    """
    # Verificar rol de administrador
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar sincronización")
    
    import asyncio
    from core.scheduler.jobs.sync_compras_job import execute_sync_compras
    
    logging.info(f"[ADMIN] Usuario {current_user.get('email')} ejecutando sync compras manual (dry_run={dry_run})")
    
    # Ejecutar en thread separado para no bloquear
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_sync_compras, dry_run)
    
    return result


@api_router.post("/admin/detect/compras")
async def admin_detect_nuevos_manual(
    dry_run: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Ejecuta manualmente la detección de nuevos inventarios/requisiciones.
    
    Este job usa polling incremental con checkpoints para detectar solo
    registros NUEVOS y generar eventos para informes automáticos.
    
    Args:
        dry_run: Si True, solo verifica servidores sin detectar ni generar eventos
    
    Returns:
        Resultado con cantidad de nuevos detectados y eventos generados
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar detección")
    
    import asyncio
    from core.scheduler.jobs.detect_nuevos_compras_job import execute_detect_nuevos
    
    logging.info(f"[ADMIN] Usuario {current_user.get('email')} ejecutando detección manual (dry_run={dry_run})")
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_detect_nuevos, dry_run)
    
    return result


@api_router.get("/admin/compras/checkpoints")
async def get_checkpoints_compras(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el estado actual de los checkpoints de sincronización.
    Muestra el último folio/fecha detectado por servidor.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador", "Supervisor"]:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    
    from modules.compras.eventos_compras import get_checkpoint_manager
    
    checkpoint_mgr = get_checkpoint_manager()
    checkpoints = checkpoint_mgr.get_all_checkpoints()
    
    return {
        "total": len(checkpoints),
        "checkpoints": checkpoints
    }


@api_router.get("/admin/compras/eventos-pendientes")
async def get_eventos_pendientes_compras(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene los eventos de compras pendientes de procesar.
    Útil para monitorear la cola de informes automáticos.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador", "Supervisor"]:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    
    from modules.compras.eventos_compras import get_event_dispatcher
    
    dispatcher = get_event_dispatcher()
    eventos = dispatcher.get_pending_events(limit=limit)
    
    return {
        "total": len(eventos),
        "eventos": eventos
    }


@api_router.post("/admin/compras/procesar-eventos")
async def procesar_eventos_pendientes(
    current_user: dict = Depends(get_current_user)
):
    """
    Procesa manualmente todos los eventos pendientes.
    Dispara los informes automáticos configurados.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden procesar eventos")
    
    from modules.compras.eventos_compras import get_event_dispatcher
    
    logging.info(f"[ADMIN] Usuario {current_user.get('email')} procesando eventos manualmente")
    
    dispatcher = get_event_dispatcher()
    result = dispatcher.process_pending_events()
    
    return result


import requests

# ============= ENDPOINT: Test API Connection =============
class TestApiRequest(BaseModel):
    url: str
    api_key: str

@api_router.post("/test-api-connection")
async def test_api_connection(request: TestApiRequest):
    """
    Prueba la conexión a una API local (SoftRestaurant o MPRO).
    
    CORRECCIÓN P0 - 2026-05-08:
    Usa query universal "SELECT 1 AS test" para validar conectividad SQL
    sin depender de tablas específicas de ningún sistema.
    
    Valida:
    1. Que la API local responde
    2. Que la API key es válida
    3. Que la API puede ejecutar SQL contra SQL Server
    
    NO intenta calcular ventas del día.
    """
    import requests
    
    try:
        # CORRECCIÓN P0: Query universal de conectividad SQL
        # NO usa tablas específicas de MPRO (Comanda) ni SoftRestaurant (cheques)
        test_query = "SELECT 1 AS test"
        
        headers = {"x-api-key": request.api_key}
        params = {"sql": test_query}
        
        response = requests.get(request.url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si hubo error de SQL
            if isinstance(data, dict) and "detail" in data:
                # La API respondió pero hubo error en SQL
                return {
                    "success": True,
                    "sql_connected": False,
                    "sql_error": data.get("detail", "Error desconocido"),
                    "ventas_hoy": 0
                }
            
            # CORRECCIÓN P0: Query universal exitosa = SQL conectado
            # Devolvemos ventas_hoy: 0 para mantener compatibilidad con frontend
            return {
                "success": True,
                "sql_connected": True,
                "ventas_hoy": 0,
                "message": "Conexión exitosa. API y SQL Server operativos."
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout - La API no responde"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Sin conexión - No se puede alcanzar la API"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============= MODELS =============

class UserRole(BaseModel):
    name: str  # "Administrador", "Supervisor", "Usuario"
    permissions: List[str]

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: str
    telefono: Optional[str] = None  # Subfase 2B.5 - Teléfono para WhatsApp (formato E.164)
    sucursales: List[str] = []  # IDs de sucursales asignadas (legacy)
    allowed_servers: List[str] = []  # IDs de servidores permitidos
    allowed_sucursales: Dict[str, List[str]] = {}  # server_id -> [sucursal_ids]
    allowed_warehouses: Dict[str, List[str]] = {}  # server_id -> [warehouse_codes]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str
    sucursales: List[str] = []
    allowed_servers: List[str] = []
    allowed_sucursales: Dict[str, List[str]] = {}
    allowed_warehouses: Dict[str, List[str]] = {}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ServerQueryConfig(BaseModel):
    """Configuración de una consulta SQL para el servidor"""
    sql: str = ""  # La consulta SQL
    validated: bool = False  # Si ha sido validada exitosamente
    last_validated: Optional[datetime] = None  # Última vez que se validó
    validation_message: Optional[str] = None  # Mensaje de validación (error o éxito)

class Server(BaseModel):
    model_config = ConfigDict(extra="allow")  # FASE 3B: Permitir campos adicionales (config_origin, system_type_normalized)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    host: str
    port: int = 1433
    database: str
    username: str
    system_type: str  # "MPRO", "SoftRestaurant", "Otro", "EDARSA_HUB"
    system_type_normalized: Optional[str] = None  # FASE 3B: system_type normalizado
    date_calculation_method: str = "inventory_dates"  # Método para calcular fechas de ventas
    sucursales: List[str] = []  # IDs de sucursales
    # Filtros configurables para consultas
    # FASE P1.4-B (Dic 2025): Corregido para aceptar objetos JSON (EDARSAHUB) o strings (legacy MongoDB)
    tipos_movimiento: Optional[List[Any]] = []  # Códigos o objetos de tipos de movimiento
    categorias: Optional[List[Any]] = []  # Códigos o objetos de categorías
    departamentos: Optional[List[Any]] = []  # Códigos o objetos de departamentos
    # Consultas SQL personalizadas para el análisis de inventario
    query_inventario: Optional[Dict] = None  # Consulta para obtener inventarios
    query_ventas: Optional[Dict] = None  # Consulta para obtener ventas
    query_movimientos: Optional[Dict] = None  # Consulta para obtener movimientos/entradas
    queries_configured: bool = False  # Si todas las consultas están configuradas y validadas
    visible_en_operaciones: bool = True  # Si se muestra en dashboards y menús operativos
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # ============ CLASIFICACIÓN DE CONEXIÓN (2026-04-20) ============
    # Permite separar conexiones CORE (cerebro del sistema) de DATA_SOURCE (fuentes externas)
    tipo_conexion: str = "DATA_SOURCE"  # "DATA_SOURCE" | "CORE"
    visible_en_listado: bool = True  # Si aparece en el menú de servidores de UI
    es_editable_ui: bool = True  # Si se puede editar desde UI estándar
    es_eliminable_ui: bool = True  # Si se puede eliminar desde UI estándar
    uso_sistema: Optional[str] = None  # "CORE_DB" | "RH_INTERNO" | null para fuentes externas
    # ============ FASE 3B: Campos de registro central ============
    config_origin: Optional[str] = None  # "EDARSAHUB_SQL" | "MONGODB_LEGACY"
    password_configured: Optional[bool] = None  # Si tiene password configurado (sin exponer valor)
    api_key_configured: Optional[bool] = None  # Si tiene api_key configurado (sin exponer valor)
    warnings: Optional[List[str]] = None  # Warnings del registro (ej: "Migrar a EDARSAHUB SQL")

class ServerCreate(BaseModel):
    name: str
    host: str
    port: int = 1433
    database: str
    username: str
    password: str
    system_type: str
    date_calculation_method: str = "inventory_dates"
    sucursales: List[str] = []
    tipos_movimiento: List[str] = []
    categorias: List[str] = []
    departamentos: List[str] = []
    visible_en_operaciones: bool = True  # Por defecto visible
    # Consultas SQL opcionales (se pueden configurar después)
    query_inventario: Optional[Dict] = None
    query_ventas: Optional[Dict] = None
    query_movimientos: Optional[Dict] = None


class QueryValidationRequest(BaseModel):
    """Request para validar una consulta SQL"""
    server_id: str
    query_type: str  # "inventario", "ventas", "movimientos"
    sql: str
    
class QueryValidationResponse(BaseModel):
    """Response de validación de consulta"""
    valid: bool
    message: str
    columns_found: List[str] = []
    columns_required: List[str] = []
    columns_missing: List[str] = []
    sample_data: List[Dict] = []
    row_count: int = 0

class QueryTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    system_type: str
    query_type: str  # "ventas", "movimientos", "productos", "inventarios"
    sql_query: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QueryTemplateCreate(BaseModel):
    name: str
    system_type: str
    query_type: str
    sql_query: str
    description: Optional[str] = None

class InventoryReport(BaseModel):
    sucursal: str
    almacen: str
    fecha_inicio: str
    fecha_fin: str
    categoria: Optional[str] = None
    familia: Optional[str] = None

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    product_codes: List[str] = []  # Códigos de productos específicos
    categoria: Optional[str] = None
    familia: Optional[str] = None
    threshold_percentage: float = 5.0  # Porcentaje de diferencia para alertar
    notify_emails: List[str] = []
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlertCreate(BaseModel):
    name: str
    product_codes: List[str] = []
    categoria: Optional[str] = None
    familia: Optional[str] = None
    threshold_percentage: float = 5.0
    notify_emails: List[str] = []

class EmailReportRequest(BaseModel):
    report_data: Dict[str, Any]
    recipient_emails: List[EmailStr]
    subject: str
    format_type: str  # "excel" o "pdf"

# ============= MODELOS DE CONFIGURACIÓN DE SUCURSALES =============

class SucursalConfig(BaseModel):
    """Configuración de visibilidad de una sucursal dentro de un servidor."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str  # FK a servers.id
    sucursal_origen_id: str  # ID original de SQL Server (Sc_Cve_Sucursal)
    sucursal_nombre: str  # Nombre original de SQL
    nombre_visible: Optional[str] = None  # Nombre personalizado para mostrar
    visible_en_operaciones: bool = True  # BANDERA PRINCIPAL
    orden: int = 0  # Para ordenar en UI
    activa: bool = True  # Soft delete
    fecha_alta: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    usuario_alta: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    usuario_modificacion: Optional[str] = None

class SucursalConfigCreate(BaseModel):
    """Request para crear/actualizar configuración de sucursal."""
    sucursal_origen_id: str
    sucursal_nombre: str
    nombre_visible: Optional[str] = None
    visible_en_operaciones: bool = True
    orden: int = 0

class SucursalConfigUpdate(BaseModel):
    """Request para actualizar visibilidad de sucursal."""
    visible_en_operaciones: Optional[bool] = None
    nombre_visible: Optional[str] = None
    orden: Optional[int] = None
    activa: Optional[bool] = None

class SucursalConfigBulkUpdate(BaseModel):
    """Request para actualizar múltiples sucursales."""
    sucursales: List[Dict[str, Any]]  # [{sucursal_origen_id, visible_en_operaciones, orden}]

# ============= MODELOS DE INFORMES DE AUDITORÍA =============

class EvidenciaAuditoria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre_archivo: str
    tipo_archivo: str  # "image", "pdf", "word", "excel"
    mime_type: str
    tamanio: int  # en bytes
    data_base64: str  # archivo codificado en base64
    fecha_subida: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InformeAuditoriaCreate(BaseModel):
    server_id: str
    sucursal_id: str
    sucursal_nombre: str
    establecimiento: str
    gerente_responsable: str
    auditor: str
    periodo_inicio: str
    periodo_fin: str
    # Datos del reporte de inventario
    datos_inventario: List[Dict[str, Any]] = []
    resumen_situacion: str = ""
    ajustes_tecnicos: str = ""
    # Comparativo 4 cortes (opcional)
    incluir_comparativo: bool = False
    datos_comparativo: List[Dict[str, Any]] = []
    # Campos del auditor
    comentarios: str = ""
    conclusiones: str = ""
    recomendaciones: str = ""
    dictamen_economico: Dict[str, Any] = {}
    # Compromisos
    compromisos_almacen: str = ""
    compromisos_personal: str = ""
    compromisos_gerencia: str = ""

class InformeAuditoriaUpdate(BaseModel):
    establecimiento: Optional[str] = None
    gerente_responsable: Optional[str] = None
    resumen_situacion: Optional[str] = None
    ajustes_tecnicos: Optional[str] = None
    comentarios: Optional[str] = None
    conclusiones: Optional[str] = None
    recomendaciones: Optional[str] = None
    dictamen_economico: Optional[Dict[str, Any]] = None
    compromisos_almacen: Optional[str] = None
    compromisos_personal: Optional[str] = None
    compromisos_gerencia: Optional[str] = None
    incluir_comparativo: Optional[bool] = None
    datos_comparativo: Optional[List[Dict[str, Any]]] = None

class InformeAuditoria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str
    sucursal_id: str
    sucursal_nombre: str
    establecimiento: str
    gerente_responsable: str
    auditor: str
    auditor_id: str
    periodo_inicio: str
    periodo_fin: str
    fecha_emision: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Datos del reporte
    datos_inventario: List[Dict[str, Any]] = []
    resumen_situacion: str = ""
    ajustes_tecnicos: str = ""
    # Comparativo
    incluir_comparativo: bool = False
    datos_comparativo: List[Dict[str, Any]] = []
    # Campos del auditor
    comentarios: str = ""
    conclusiones: str = ""
    recomendaciones: str = ""
    dictamen_economico: Dict[str, Any] = {}
    # Compromisos
    compromisos_almacen: str = ""
    compromisos_personal: str = ""
    compromisos_gerencia: str = ""
    # Evidencias
    evidencias: List[Dict[str, Any]] = []
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estado: str = "borrador"  # borrador, finalizado

# ============= SQL SERVER FUNCTIONS =============
# 
# FASE 1 DEL REFACTOR MODULAR (Diciembre 2025):
# Las funciones de SQL Server han sido migradas a /core/db.py
# Este bloque mantiene imports de compatibilidad para que todo el código
# existente siga funcionando sin cambios.
#
# Funciones migradas:
#   - execute_sql_query()
#   - test_sql_connection()
#   - parse_sql_server_host()
#   - mark_server_offline()
#   - mark_server_online()
#   - is_server_offline_in_memory()
#   - get_server_cooldown_info()
#   - _server_status_cache (variable global)
#
# LIMPIEZA FUTURA: Este bloque puede eliminarse cuando todos los imports
# en server.py sean actualizados para usar directamente core.db
# =============================================================================

from core.db import (
    execute_sql_query,
    test_sql_connection,
    parse_sql_server_host,
    mark_server_offline,
    mark_server_online,
    is_server_offline_in_memory,
    get_server_cooldown_info,
)

# Re-exportar para compatibilidad con código que importa desde server.py
# Nota: _server_status_cache ya no está disponible directamente, usar funciones
# get_server_cache_status() y reset_server_cache() de core.db si es necesario

# ============= EXPORT FUNCTIONS =============

def generate_excel(data: List[Dict], filename: str = "reporte.xlsx", metadata: Dict = None) -> bytes:
    """
    Genera archivo Excel con formato profesional para el reporte de inventario.
    Incluye encabezados con información del servidor, fechas y KPIs visuales.
    Los datos se ordenan por Diferencia_Costo de mayor negativa a mayor positiva.
    """
    from openpyxl.styles import Border, Side, NamedStyle
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.utils import get_column_letter
    from datetime import datetime
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Inventario"
    
    if not data:
        return b''
    
    # ==================== ORDENAR DATOS ====================
    # Ordenar por Diferencia_Costo de mayor negativa a mayor positiva
    try:
        data = sorted(data, key=lambda x: float(x.get('Diferencia_Costo', 0) or 0))
    except (ValueError, TypeError):
        pass  # Si falla, mantener orden original
    
    # Metadata del reporte
    meta = metadata or {}
    servidor_nombre = meta.get('servidor_nombre', 'N/A')
    sucursal = meta.get('sucursal', 'N/A')
    almacen = meta.get('almacen', 'N/A')
    fecha_inicio = meta.get('fecha_inicio', 'N/A')
    fecha_fin = meta.get('fecha_fin', 'N/A')
    fecha_elaboracion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Estilos
    titulo_font = Font(size=14, bold=True, color="18181b")
    header_fill = PatternFill(start_color="18181b", end_color="18181b", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=10)
    label_font = Font(bold=True, size=10)
    value_font = Font(size=10)
    
    # Colores para KPI de diferencias
    verde_fill = PatternFill(start_color="22c55e", end_color="22c55e", fill_type="solid")  # Positivo
    rojo_fill = PatternFill(start_color="ef4444", end_color="ef4444", fill_type="solid")    # Negativo
    amarillo_fill = PatternFill(start_color="eab308", end_color="eab308", fill_type="solid") # Cero
    
    thin_border = Border(
        left=Side(style='thin', color='d4d4d8'),
        right=Side(style='thin', color='d4d4d8'),
        top=Side(style='thin', color='d4d4d8'),
        bottom=Side(style='thin', color='d4d4d8')
    )
    
    # ==================== ENCABEZADO DEL REPORTE ====================
    row_num = 1
    
    # Título principal
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=6)
    ws.cell(row=row_num, column=1, value="REPORTE DE ANÁLISIS DE INVENTARIO").font = titulo_font
    ws.cell(row=row_num, column=1).alignment = Alignment(horizontal="center")
    row_num += 2
    
    # Información del reporte (2 columnas)
    info_data = [
        ("Servidor:", servidor_nombre),
        ("Sucursal:", sucursal),
        ("Almacén:", almacen),
        ("Período:", f"Del {fecha_inicio} al {fecha_fin}"),
        ("Fecha de Elaboración:", fecha_elaboracion)
    ]
    
    for label, value in info_data:
        ws.cell(row=row_num, column=1, value=label).font = label_font
        ws.cell(row=row_num, column=2, value=value).font = value_font
        row_num += 1
    
    row_num += 1  # Espacio antes de la tabla
    
    # ==================== RESUMEN / KPIs ====================
    # Calcular totales
    total_sobrante = sum(float(row.get('Diferencia_Costo', 0) or 0) for row in data if float(row.get('Diferencia_Costo', 0) or 0) > 0)
    total_faltante = sum(float(row.get('Diferencia_Costo', 0) or 0) for row in data if float(row.get('Diferencia_Costo', 0) or 0) < 0)
    total_neto = total_sobrante + total_faltante
    
    ws.cell(row=row_num, column=1, value="RESUMEN:").font = label_font
    row_num += 1
    
    # Sobrante (verde)
    ws.cell(row=row_num, column=1, value="Sobrante:").font = label_font
    cell_sobrante = ws.cell(row=row_num, column=2, value=f"$ {total_sobrante:,.2f}")
    cell_sobrante.fill = verde_fill
    cell_sobrante.font = Font(bold=True, color="FFFFFF")
    row_num += 1
    
    # Faltante (rojo)
    ws.cell(row=row_num, column=1, value="Faltante:").font = label_font
    cell_faltante = ws.cell(row=row_num, column=2, value=f"-$ {abs(total_faltante):,.2f}")
    cell_faltante.fill = rojo_fill
    cell_faltante.font = Font(bold=True, color="FFFFFF")
    row_num += 1
    
    # Neto
    ws.cell(row=row_num, column=1, value="Neto:").font = label_font
    cell_neto = ws.cell(row=row_num, column=2, value=f"$ {total_neto:,.2f}")
    if total_neto > 0:
        cell_neto.fill = verde_fill
        cell_neto.font = Font(bold=True, color="FFFFFF")
    elif total_neto < 0:
        cell_neto.fill = rojo_fill
        cell_neto.font = Font(bold=True, color="FFFFFF")
    else:
        cell_neto.fill = amarillo_fill
        cell_neto.font = Font(bold=True)
    row_num += 2
    
    # ==================== TABLA DE DATOS ====================
    # Headers de la tabla
    headers = list(data[0].keys())
    header_row = row_num
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=row_num, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    
    row_num += 1
    
    # Filas de datos con KPI de colores para diferencias
    diferencia_cols = []
    for idx, header in enumerate(headers):
        if 'diferencia' in header.lower():
            diferencia_cols.append(idx + 1)
    
    for row_data in data:
        values = list(row_data.values())
        for col_num, value in enumerate(values, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if isinstance(value, (int, float)) else "left")
            
            # Aplicar color KPI a columnas de diferencia
            if col_num in diferencia_cols:
                try:
                    num_value = float(value) if value is not None else 0
                    if num_value > 0:
                        cell.fill = verde_fill
                        cell.font = Font(bold=True, color="FFFFFF")
                    elif num_value < 0:
                        cell.fill = rojo_fill
                        cell.font = Font(bold=True, color="FFFFFF")
                    else:
                        cell.fill = amarillo_fill
                        cell.font = Font(bold=True)
                except (ValueError, TypeError):
                    pass
        row_num += 1
    
    # ==================== FORMATO DE TABLA CON FILTROS ====================
    # Aplicar autofiltro a la tabla de datos
    last_col_letter = get_column_letter(len(headers))
    ws.auto_filter.ref = f"A{header_row}:{last_col_letter}{row_num - 1}"
    
    # Ajustar ancho de columnas (evitar celdas mezcladas)
    for col_idx in range(1, len(headers) + 1):
        max_length = 0
        col_letter = get_column_letter(col_idx)
        for row in range(header_row, row_num):
            cell = ws.cell(row=row, column=col_idx)
            try:
                if cell.value and not isinstance(cell, type(None)):
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            except Exception:
                pass
        adjusted_width = min(max_length + 2, 50)  # Max 50 caracteres
        if adjusted_width > 0:
            ws.column_dimensions[col_letter].width = adjusted_width
    
    # Congelar paneles (encabezado de tabla visible al hacer scroll)
    ws.freeze_panes = f"A{header_row + 1}"
    
    # Guardar
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

def generate_pdf(data: List[Dict], filename: str = "reporte.pdf") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    if not data:
        return b''
    
    # Create table data
    headers = list(data[0].keys())
    table_data = [headers]
    
    for row in data:
        table_data.append(list(row.values()))
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e4e4e7'))
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

async def send_email_with_attachment(recipient_emails: List[str], subject: str, body: str, attachment_data: bytes, attachment_filename: str):
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    sender_email = os.environ.get('SENDER_EMAIL')
    
    if not sendgrid_api_key or not sender_email:
        raise HTTPException(status_code=500, detail="SendGrid no configurado")
    
    message = Mail(
        from_email=sender_email,
        to_emails=recipient_emails,
        subject=subject,
        html_content=body
    )
    
    # Attach file
    encoded_file = base64.b64encode(attachment_data).decode()
    attachment = Attachment(
        file_content=encoded_file,
        file_name=attachment_filename,
        file_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if attachment_filename.endswith('.xlsx') else 'application/pdf',
        disposition='attachment'
    )
    message.attachment = attachment
    
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        logging.error(f"Error enviando email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")

# ============= ROUTES =============
# 
# NOTA FASE 3: Las rutas de auth/users/roles han sido migradas a:
# - modules/auth/routes.py
# 
# Endpoints migrados:
# - POST /auth/register
# - POST /auth/login  
# - GET /auth/me
# - GET /users
# - PUT /users/{user_id}
# - DELETE /users/{user_id}
# - PUT /users/{user_id}/permissions
# - GET /roles/modulos
# - GET /roles
# - POST /roles
# - PUT /roles/{role_id}
# - DELETE /roles/{role_id}
#
# LIMPIEZA FUTURA: Este comentario puede eliminarse cuando se complete el refactor
# =============================================================================

# ============= SERVERS =============

@api_router.post("/servers")
async def create_server(server_data: ServerCreate, current_user: Dict = Depends(get_current_user)):
    """
    FASE 3B.1: Crea servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.
    
    - SQL es la fuente principal
    - MongoDB queda como espejo legacy
    - Si MongoDB sync falla, devuelve PARTIAL_SYNC
    
    RBAC: Solo SuperAdministrador o Administrador pueden crear servidores.
    """
    # FASE 3B.2: Validación RBAC corregida - permitir SuperAdministrador y Administrador
    if current_user['role'] not in ['SuperAdministrador', 'Administrador']:
        raise HTTPException(status_code=403, detail="No autorizado. Requiere rol SuperAdministrador o Administrador.")
    
    from core.server_registry import create_server as registry_create_server
    
    # FASE 3B.2: Test connection opcional para servidores de prueba
    # Si host es 127.0.0.1 o TEST_*, saltar validación de conexión
    skip_connection_test = (
        server_data.host in ['127.0.0.1', 'localhost', '0.0.0.0'] or
        server_data.name.startswith('TEST_')
    )
    
    if not skip_connection_test:
        if not test_sql_connection(server_data.host, server_data.port, server_data.database, server_data.username, server_data.password):
            raise HTTPException(status_code=400, detail="No se pudo conectar al servidor")
    
    # Preparar payload
    payload = server_data.model_dump()
    
    # Crear usando registry (SQL-first)
    result = await registry_create_server(
        payload=payload,
        db=db,
        user=current_user,
        sync_mongo=True
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=400, 
            detail=result.get('error', 'Error al crear servidor')
        )
    
    # Respuesta compatible con frontend
    return {
        'id': result['id'],
        'name': result['name'],
        'system_type': result['system_type'],
        'system_type_normalized': result.get('system_type_normalized'),
        'config_origin': result['config_origin'],
        'sync_status': result['sync_status'],
        'warnings': result.get('warnings', []),
        'message': 'Servidor creado exitosamente'
    }

@api_router.get("/servers", response_model=List[Server])
async def get_servers(current_user: Dict = Depends(get_current_user)):
    """
    FASE 3B: Listado de servidores usando Server Registry Central.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (fuente primaria)
    2. MongoDB (fallback legacy)
    
    CORRECCIÓN 2026-05-20: Las conexiones CORE (ej. EDARSAHUB SQL) ahora aparecen
    en el listado del menú administrativo de servidores.
    """
    from core.server_registry import list_servers as registry_list_servers
    
    servers = await registry_list_servers(
        db=db,
        user=current_user,
        prefer_sql=True,
        allow_mongo_fallback=True,
        filter_active=True,
        filter_visible_listado=True,
        exclude_core=False,
        mask_secrets=True
    )
    
    return servers

@api_router.get("/servers/{server_id}")
async def get_server(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    FASE 3B: Obtener servidor por ID usando Server Registry Central.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (fuente primaria)
    2. MongoDB (fallback legacy)
    """
    from core.server_registry import get_server_by_id as registry_get_server
    
    # FASE 6-8: Verificar permiso usando función centralizada
    await validate_server_access_unified(current_user, server_id)
    
    server = await registry_get_server(
        server_id,
        db=db,
        prefer_sql=True,
        allow_mongo_fallback=True,
        mask_secrets=True
    )
    
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    return server

@api_router.put("/servers/{server_id}")
async def update_server(server_id: str, server_data: Dict, current_user: Dict = Depends(get_current_user)):
    """
    FASE 3B.1: Actualiza servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.
    
    - SQL es la fuente principal
    - MongoDB queda como espejo legacy
    - Si MongoDB sync falla, devuelve PARTIAL_SYNC
    - Passwords enmascarados no sobrescriben el real
    
    RBAC: Solo SuperAdministrador o Administrador pueden actualizar servidores.
    Protección CORE: Ni SuperAdministrador ni Administrador pueden modificar conexiones CORE.
    """
    # FASE 3B.2: Validación RBAC corregida - permitir SuperAdministrador y Administrador
    if current_user['role'] not in ['SuperAdministrador', 'Administrador']:
        raise HTTPException(status_code=403, detail="No autorizado. Requiere rol SuperAdministrador o Administrador.")
    
    from core.server_registry import update_server as registry_update_server, get_server_by_id
    
    # Verificar que el servidor existe (también verifica protección CORE via registry)
    existing = await get_server_by_id(server_id, db=db, mask_secrets=False)
    if not existing:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Protección CORE
    if existing.get("tipo_conexion") == "CORE" or existing.get("es_editable_ui") == False:
        raise HTTPException(
            status_code=403, 
            detail="Esta conexión es del sistema central (CORE) y no puede ser modificada desde la interfaz"
        )
    
    # Prevenir que desde UI se cambie a tipo CORE
    if server_data.get("tipo_conexion") == "CORE":
        raise HTTPException(status_code=403, detail="No se puede cambiar el tipo de conexión a CORE desde UI")
    
    # Actualizar usando registry (SQL-first)
    result = await registry_update_server(
        server_id=server_id,
        payload=server_data,
        db=db,
        user=current_user,
        sync_mongo=True
    )
    
    if not result.get('success'):
        status_code = 404 if result.get('sync_status') == 'NOT_FOUND' else 400
        raise HTTPException(
            status_code=status_code,
            detail=result.get('error', 'Error al actualizar servidor')
        )
    
    return {
        'message': result.get('message', 'Servidor actualizado'),
        'config_origin': result['config_origin'],
        'sync_status': result['sync_status'],
        'warnings': result.get('warnings', [])
    }

@api_router.delete("/servers/{server_id}")
async def delete_server(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    FASE 3B.1: Desactiva servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.
    
    - Usa soft delete (activo=false), no borrado físico
    - SQL es la fuente principal
    - MongoDB queda como espejo legacy
    - Si MongoDB sync falla, devuelve PARTIAL_SYNC
    
    RBAC: Solo SuperAdministrador o Administrador pueden eliminar servidores.
    Protección CORE: Ni SuperAdministrador ni Administrador pueden eliminar conexiones CORE.
    """
    # FASE 3B.2: Validación RBAC corregida - permitir SuperAdministrador y Administrador
    if current_user['role'] not in ['SuperAdministrador', 'Administrador']:
        raise HTTPException(status_code=403, detail="No autorizado. Requiere rol SuperAdministrador o Administrador.")
    
    from core.server_registry import delete_server as registry_delete_server, get_server_by_id
    
    # Verificar que existe y obtener datos para validación CORE
    existing = await get_server_by_id(server_id, db=db, mask_secrets=True)
    if not existing:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Protección CORE
    if existing.get("tipo_conexion") == "CORE" or existing.get("es_eliminable_ui") == False:
        raise HTTPException(
            status_code=403, 
            detail="Esta conexión es del sistema central (CORE) y no puede ser eliminada desde la interfaz"
        )
    
    # Eliminar usando registry (SQL-first, soft delete)
    result = await registry_delete_server(
        server_id=server_id,
        db=db,
        user=current_user,
        sync_mongo=True,
        soft_delete=True  # Mantener soft delete como comportamiento actual
    )
    
    if not result.get('success'):
        status_code = 404 if result.get('sync_status') == 'NOT_FOUND' else 400
        raise HTTPException(
            status_code=status_code,
            detail=result.get('error', 'Error al eliminar servidor')
        )
    
    return {
        'message': result.get('message', 'Servidor desactivado'),
        'config_origin': result['config_origin'],
        'sync_status': result['sync_status'],
        'warnings': result.get('warnings', [])
    }


@api_router.get("/servers/{server_id}/ping")
async def ping_server(server_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Prueba la conexión a un servidor SQL Server.
    Retorna información de estado y tiempo de respuesta.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 2:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    verify_token(credentials.credentials)
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[PING_SERVER] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[PING_SERVER] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    import time
    start_time = time.time()
    
    try:
        # Intentar conexión
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'],
            "SELECT 1 as ping, GETDATE() as server_time, @@VERSION as version"
        )
        
        elapsed_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        if result and len(result) > 0:
            server_time = result[0].get('server_time', '')
            version = result[0].get('version', '')[:100]  # Primeros 100 chars
            
            # Guardar estado como online
            await db.server_status.update_one(
                {"server_id": server_id},
                {"$set": {"server_id": server_id, "is_online": True, "response_time_ms": elapsed_time, "last_check": datetime.now(timezone.utc).isoformat()}},
                upsert=True
            )
            
            return {
                "status": "connected",
                "server_name": server['name'],
                "response_time_ms": elapsed_time,
                "server_time": str(server_time) if server_time else None,
                "version": version,
                "message": f"Conexión exitosa en {elapsed_time}ms"
            }
        else:
            return {
                "status": "connected",
                "server_name": server['name'],
                "response_time_ms": elapsed_time,
                "message": "Conexión exitosa (sin datos)"
            }
            
    except Exception as e:
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        error_msg = str(e)
        
        # Guardar estado como offline
        await db.server_status.update_one(
            {"server_id": server_id},
            {"$set": {"server_id": server_id, "is_online": False, "last_check": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        
        # Determinar tipo de error
        if "Unable to connect" in error_msg or "unavailable" in error_msg.lower():
            status = "unreachable"
        elif "Login failed" in error_msg or "authentication" in error_msg.lower():
            status = "auth_error"
        else:
            status = "error"
        
        return {
            "status": status,
            "server_name": server['name'],
            "response_time_ms": elapsed_time,
            "message": error_msg[:200]
        }

# ============= QUERIES =============

@api_router.post("/queries")
async def create_query(query_data: QueryTemplateCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    query = QueryTemplate(**query_data.model_dump())
    doc = query.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.queries.insert_one(doc)
    
    return query.model_dump()

@api_router.get("/queries", response_model=List[QueryTemplate])
async def get_queries(system_type: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    filter_query = {}
    if system_type:
        filter_query['system_type'] = system_type
    
    queries = await db.queries.find(filter_query, {"_id": 0}).to_list(1000)
    return queries

@api_router.put("/queries/{query_id}")
async def update_query(query_id: str, query_data: Dict, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await db.queries.update_one({"id": query_id}, {"$set": query_data})
    return {"message": "Consulta actualizada"}

@api_router.delete("/queries/{query_id}")
async def delete_query(query_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await db.queries.delete_one({"id": query_id})
    return {"message": "Consulta eliminada"}

# ============= SERVER QUERY CONFIGURATION =============

# Columnas requeridas para cada tipo de consulta
REQUIRED_COLUMNS = {
    "inventario": {
        "required": ["codigo", "descripcion", "cantidad"],
        "optional": ["fecha", "sucursal", "almacen", "costo", "unidad", "grupo", "categoria"],
        "description": "Consulta de inventarios (inicial y final). Obtiene el stock de productos en una fecha determinada."
    },
    "ventas": {
        "required": ["codigo", "descripcion", "cantidad"],
        "optional": ["fecha", "precio", "importe", "sucursal", "almacen", "folio"],
        "description": "Consulta de ventas del período. Obtiene los productos vendidos entre dos fechas."
    },
    "movimientos": {
        "required": ["codigo", "descripcion", "cantidad"],
        "optional": ["fecha", "tipo_movimiento", "sucursal", "almacen", "referencia", "costo"],
        "description": "Consulta de movimientos (entradas, compras, traspasos, ajustes). Obtiene las entradas de productos al inventario."
    }
}

# Mapeo de alias de columnas (para flexibilidad)
COLUMN_ALIASES = {
    "codigo": ["codigo", "clave", "code", "producto_codigo", "codigo_producto", "idinsumo", "idproducto", "sku", "cve_producto", "pr_cve_producto"],
    "cantidad": ["cantidad", "qty", "quantity", "existencia", "stock", "unidades", "cant", "movimiento_neto"],
    "descripcion": ["descripcion", "description", "nombre", "name", "producto", "producto_nombre"],
    "fecha": ["fecha", "date", "fecha_movimiento", "fecha_venta", "fecha_inventario"],
    "sucursal": ["sucursal", "branch", "tienda", "sucursal_id", "idsucursal"],
    "almacen": ["almacen", "warehouse", "bodega", "almacen_id", "idalmacen"],
    "costo": ["costo", "cost", "precio_costo", "costo_unitario", "costo_promedio"],
    "precio": ["precio", "price", "precio_venta", "precio_unitario"],
    "importe": ["importe", "total", "importe_total", "monto"],
    "tipo_movimiento": ["tipo_movimiento", "tipo", "movement_type", "concepto", "idconcepto"],
    "unidad": ["unidad", "unit", "unidad_medida"],
    "referencia": ["referencia", "reference", "documento", "folio"],
    "grupo": ["grupo", "group", "categoria", "category", "idgrupo"],
    "categoria": ["categoria", "category", "familia", "family"]
}


def normalize_column_name(column: str) -> str:
    """Normaliza el nombre de una columna buscando en los alias conocidos"""
    column_lower = column.lower().strip()
    for standard_name, aliases in COLUMN_ALIASES.items():
        if column_lower in [a.lower() for a in aliases]:
            return standard_name
    return column_lower


def validate_query_columns(columns: List[str], query_type: str) -> Dict:
    """
    Valida que las columnas de una consulta cumplan con los requisitos.
    Retorna información sobre columnas encontradas, faltantes, etc.
    """
    required = REQUIRED_COLUMNS.get(query_type, {}).get("required", [])
    optional = REQUIRED_COLUMNS.get(query_type, {}).get("optional", [])
    
    # Normalizar columnas encontradas
    normalized_columns = {normalize_column_name(col): col for col in columns}
    found_normalized = set(normalized_columns.keys())
    
    # Verificar columnas requeridas
    columns_found = []
    columns_missing = []
    
    for req_col in required:
        if req_col in found_normalized:
            columns_found.append({"standard": req_col, "actual": normalized_columns[req_col], "required": True})
        else:
            columns_missing.append(req_col)
    
    # Verificar columnas opcionales encontradas
    for opt_col in optional:
        if opt_col in found_normalized:
            columns_found.append({"standard": opt_col, "actual": normalized_columns[opt_col], "required": False})
    
    return {
        "valid": len(columns_missing) == 0,
        "columns_found": columns_found,
        "columns_missing": columns_missing,
        "columns_required": required,
        "columns_optional": optional,
        "all_columns": columns
    }


@api_router.post("/servers/{server_id}/queries/validate")
async def validate_server_query(
    server_id: str, 
    request: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Valida una consulta SQL para un servidor.
    Ejecuta la consulta y verifica que devuelva las columnas necesarias.
    
    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    
    FASE 1B: Sanitización SQL - Validación obligatoria antes de ejecución.
    """
    from core.server_registry import get_server_connection_info_with_secrets
    from core.security import SQLSanitizer, log_blocked_sql
    
    query_type = request.get("query_type")  # "inventario", "ventas", "movimientos"
    sql = request.get("sql", "").strip()
    
    if query_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido. Usa: {list(REQUIRED_COLUMNS.keys())}")
    
    if not sql:
        raise HTTPException(status_code=400, detail="La consulta SQL es requerida")
    
    # FASE 1B: Validar SQL antes de ejecutar
    validation = SQLSanitizer.validate_for_catalog(sql)
    if not validation.is_safe:
        log_blocked_sql(validation, endpoint="/servers/queries/validate", user_email=current_user.get('email'))
        raise HTTPException(status_code=400, detail=f"SQL bloqueado: {validation.blocked_reason}")
    
    # FASE P1.4-B: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        # Ejecutar consulta con límite para validación
        # Agregar TOP 10 si no existe para evitar traer muchos datos
        sql_test = sql
        if "TOP" not in sql.upper() and "LIMIT" not in sql.upper():
            # Insertar TOP 10 después de SELECT
            sql_test = sql.replace("SELECT", "SELECT TOP 10", 1).replace("select", "SELECT TOP 10", 1)
        
        logging.info(f"Validando consulta tipo '{query_type}' para servidor {server_id}")
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            sql_test
        )
        
        if not results:
            return {
                "valid": False,
                "message": "La consulta no devolvió resultados. Verifica que haya datos en las tablas.",
                "columns_found": [],
                "columns_required": REQUIRED_COLUMNS[query_type]["required"],
                "columns_missing": REQUIRED_COLUMNS[query_type]["required"],
                "sample_data": [],
                "row_count": 0
            }
        
        # Obtener columnas de los resultados
        columns = list(results[0].keys())
        
        # Validar columnas
        validation = validate_query_columns(columns, query_type)
        
        if validation["valid"]:
            message = f"✅ Consulta válida. Se encontraron todas las columnas requeridas."
        else:
            missing = ", ".join(validation["columns_missing"])
            message = f"❌ Faltan columnas requeridas: {missing}. Revisa los alias permitidos en la documentación."
        
        return {
            "valid": validation["valid"],
            "message": message,
            "columns_found": [c["actual"] for c in validation["columns_found"]],
            "columns_mapping": validation["columns_found"],
            "columns_required": validation["columns_required"],
            "columns_missing": validation["columns_missing"],
            "sample_data": results[:5],  # Solo muestra 5 registros de ejemplo
            "row_count": len(results),
            "description": REQUIRED_COLUMNS[query_type]["description"]
        }
        
    except Exception as e:
        logging.error(f"Error validando consulta: {str(e)}")
        return {
            "valid": False,
            "message": f"Error al ejecutar la consulta: {str(e)}",
            "columns_found": [],
            "columns_required": REQUIRED_COLUMNS[query_type]["required"],
            "columns_missing": REQUIRED_COLUMNS[query_type]["required"],
            "sample_data": [],
            "row_count": 0
        }


@api_router.put("/servers/{server_id}/queries/{query_type}")
async def save_server_query(
    server_id: str,
    query_type: str,
    request: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Guarda una consulta SQL validada para un servidor.
    
    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server, get_server_by_id
    
    if query_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido. Usa: {list(REQUIRED_COLUMNS.keys())}")
    
    sql = request.get("sql", "").strip()
    validated = request.get("validated", False)
    
    if not sql:
        raise HTTPException(status_code=400, detail="La consulta SQL es requerida")
    
    # FASE P1.4-B: Verificar que el servidor existe via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    server = get_server_connection_info_with_secrets(server_id)
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Crear objeto de configuración de consulta
    query_config = {
        "sql": sql,
        "validated": validated,
        "last_validated": datetime.now(timezone.utc).isoformat() if validated else None,
        "validation_message": "Validada correctamente" if validated else "Pendiente de validación"
    }
    
    # FASE P1.4-B: Actualizar el servidor via server_registry (SQL-first)
    field_name = f"query_{query_type}"
    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: query_config}})
    result = await registry_update_server(
        server_id=server_id,
        payload={field_name: query_config},
        db=db,
        user=current_user,
        sync_mongo=True  # Mantener espejo MongoDB para compatibilidad
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Error al guardar query'))
    
    # FASE P1.4-B: Verificar si todas las consultas están configuradas
    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
    updated_server = await get_server_by_id(server_id, db=db, mask_secrets=True)
    if updated_server:
        all_configured = all([
            (updated_server.get("query_inventario") or {}).get("validated", False),
            (updated_server.get("query_ventas") or {}).get("validated", False),
            (updated_server.get("query_movimientos") or {}).get("validated", False)
        ])
        
        # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {"queries_configured": all_configured}})
        await registry_update_server(
            server_id=server_id,
            payload={"queries_configured": all_configured},
            db=db,
            user=current_user,
            sync_mongo=True
        )
    else:
        all_configured = False
    
    return {
        "message": f"Consulta de {query_type} guardada exitosamente",
        "query_type": query_type,
        "validated": validated,
        "all_queries_configured": all_configured
    }


@api_router.get("/servers/{server_id}/queries")
async def get_server_queries(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el estado de configuración de consultas de un servidor.
    
    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_by_id
    
    # FASE P1.4-B: Obtener servidor desde EDARSAHUB SQL
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    server = await get_server_by_id(server_id, db=db, mask_secrets=True)
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    return {
        "server_id": server_id,
        "server_name": server.get("name"),
        "system_type": server.get("system_type"),
        "queries_configured": server.get("queries_configured", False),
        "queries": {
            "inventario": {
                "configured": server.get("query_inventario") is not None,
                "validated": (server.get("query_inventario") or {}).get("validated", False),
                "sql": (server.get("query_inventario") or {}).get("sql", ""),
                "last_validated": (server.get("query_inventario") or {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["inventario"]["description"],
                "required_columns": REQUIRED_COLUMNS["inventario"]["required"],
                "optional_columns": REQUIRED_COLUMNS["inventario"]["optional"]
            },
            "ventas": {
                "configured": server.get("query_ventas") is not None,
                "validated": (server.get("query_ventas") or {}).get("validated", False),
                "sql": (server.get("query_ventas") or {}).get("sql", ""),
                "last_validated": (server.get("query_ventas") or {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["ventas"]["description"],
                "required_columns": REQUIRED_COLUMNS["ventas"]["required"],
                "optional_columns": REQUIRED_COLUMNS["ventas"]["optional"]
            },
            "movimientos": {
                "configured": server.get("query_movimientos") is not None,
                "validated": (server.get("query_movimientos") or {}).get("validated", False),
                "sql": (server.get("query_movimientos") or {}).get("sql", ""),
                "last_validated": (server.get("query_movimientos") or {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["movimientos"]["description"],
                "required_columns": REQUIRED_COLUMNS["movimientos"]["required"],
                "optional_columns": REQUIRED_COLUMNS["movimientos"]["optional"]
            }
        },
        "column_aliases": COLUMN_ALIASES
    }


@api_router.delete("/servers/{server_id}/queries/{query_type}")
async def delete_server_query(
    server_id: str,
    query_type: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Elimina una consulta configurada de un servidor.
    
    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server
    
    if query_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido")
    
    # FASE P1.4-B: Verificar que el servidor existe via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    server = get_server_connection_info_with_secrets(server_id)
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE P1.4-B: Actualizar via server_registry (SQL-first)
    field_name = f"query_{query_type}"
    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: None, "queries_configured": False}})
    result = await registry_update_server(
        server_id=server_id,
        payload={field_name: None, "queries_configured": False},
        db=db,
        user=current_user,
        sync_mongo=True
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Error al eliminar query'))
    
    return {"message": f"Consulta de {query_type} eliminada"}

# ============= REPORTS =============

@api_router.get("/servers/{server_id}/tipos-movimiento")
async def get_tipos_movimiento(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la lista de tipos de movimiento.
    
    FASE T3.4-B4/MODAL: EDARSAHUB-FIRST.
    
    ESTRATEGIA:
    1. PRIMERO: Leer tipos_movimiento desde EDARSAHUB/server_registry
    2. Si existen tipos en EDARSAHUB → devolverlos directamente (sin conexión viva obligatoria)
    3. La conexión viva queda para refresh/sincronización/diagnóstico futuro
    
    MÁXIMAS:
    - EDARSAHUB es el cerebro del sistema
    - No usar MongoDB
    - No depender de conexión viva para cargar el modal
    - Mantener contrato API compatible con frontend
    
    Returns:
        Lista de objetos [{codigo, descripcion, tipo}] compatibles con frontend
    """
    from core.server_registry import get_server_connection_info
    
    # Obtener servidor desde registry (EDARSAHUB-first)
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_TIPOS_MOVIMIENTO] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.info(f"[GET_TIPOS_MOVIMIENTO] Servidor obtenido. Origin={server.get('config_origin', 'UNKNOWN')}, Name={server.get('name', 'N/A')}")
    
    # EDARSAHUB-FIRST: Leer tipos_movimiento desde EDARSAHUB
    tipos_edarsahub = server.get('tipos_movimiento', [])
    
    if tipos_edarsahub:
        # Hay tipos configurados en EDARSAHUB → devolverlos directamente
        result = _build_tipos_from_edarsahub(server)
        logging.info(f"[GET_TIPOS_MOVIMIENTO] EDARSAHUB-FIRST: {len(result)} tipos. Server={server.get('name', 'N/A')}")
        return result
    
    # No hay tipos en EDARSAHUB → retornar lista vacía
    # (La conexión viva queda para sincronización/diagnóstico, no para carga obligatoria del modal)
    logging.info(f"[GET_TIPOS_MOVIMIENTO] Sin tipos en EDARSAHUB. Server={server.get('name', 'N/A')}")
    return []


def _build_tipos_from_edarsahub(server: dict) -> list:
    """
    FASE T3.4-B4 / P1: Construye lista de tipos de movimiento desde EDARSAHUB.
    
    Soporta dos formatos en tipos_movimiento:
    A) Lista de strings: ["ECA", "EDE"] → convierte a objetos
    B) Lista de objetos: [{"codigo":"ECA","descripcion":"...","tipo":"EN"}] → devuelve directo
    
    El frontend espera: [{codigo, descripcion, tipo}]
    
    Args:
        server: Dict con datos del servidor (debe tener 'tipos_movimiento')
    
    Returns:
        Lista de tipos en formato compatible con frontend
    """
    tipos_data = server.get('tipos_movimiento', [])
    
    if not tipos_data:
        return []
    
    # Si ya son objetos enriquecidos, devolverlos directamente
    if tipos_data and isinstance(tipos_data[0], dict):
        return tipos_data
    
    # Son códigos simples, convertir a objetos
    is_mpro = is_mpro_system(server.get('system_type', ''))
    
    result = []
    for codigo in tipos_data:
        if codigo:
            codigo_str = str(codigo)
            result.append({
                'codigo': codigo_str,
                'descripcion': codigo_str,  # Fallback: descripcion = codigo
                'tipo': _infer_tipo_from_codigo(codigo_str, is_mpro)
            })
    
    return result


def _infer_tipo_from_codigo(codigo: str, is_mpro: bool = False) -> str:
    """
    Infiere si un tipo de movimiento es entrada, salida u otro.
    
    Reglas de inferencia:
    - SoftRestaurant: E* = EN (entrada), S* = SA (salida)
    - MPRO: 0* = EN (entrada), 4* = SA (salida) (según configuración validada)
    - Si no se puede inferir: otro
    
    Returns:
        'EN' (entrada), 'SA' (salida) o 'otro' - Compatible con frontend
    
    Frontend espera: tipo === '+' || tipo === 'EN' → verde (Entrada)
                    otro → rojo (Salida)
    """
    if not codigo:
        return 'otro'
    
    codigo_str = str(codigo).strip()
    
    if not codigo_str:
        return 'otro'
    
    primer_char = codigo_str[0].upper()
    
    # SoftRestaurant: E* = EN (entrada), S* = SA (salida)
    if primer_char == 'E':
        return 'EN'
    elif primer_char == 'S':
        return 'SA'
    
    # MPRO: 0* = EN (entrada), 4* = SA (salida)
    if is_mpro:
        if primer_char == '0':
            return 'EN'
        elif primer_char == '4':
            return 'SA'
    
    # No se puede inferir con seguridad
    return 'otro'

@api_router.get("/servers/{server_id}/categorias")
async def get_categorias(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la lista de categorías/grupos.
    
    P0 CATÁLOGOS EDARSAHUB-FIRST:
    Lee categorías desde EDARSAHUB.Servidores_Conexiones.categorias
    NO consulta BD viva del restaurante.
    NO consulta MongoDB.
    
    MÁXIMA: EDARSAHUB es el cerebro del sistema.
    El modal no debe depender de conexión viva.
    
    Returns:
        Lista de objetos [{codigo, descripcion}] o [] si no hay datos
    """
    from core.server_registry import get_server_by_id
    
    # Obtener servidor desde EDARSAHUB
    server = await get_server_by_id(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_CATEGORIAS] Servidor no encontrado. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # P0: Leer categorías desde EDARSAHUB
    categorias = server.get('categorias', [])
    
    if categorias:
        logging.info(f"[GET_CATEGORIAS] EDARSAHUB-FIRST: {len(categorias)} categorías. Server={server.get('name', 'N/A')}")
        return categorias
    
    # Sin datos en EDARSAHUB
    logging.info(f"[GET_CATEGORIAS] Sin categorías en EDARSAHUB (pendiente sync). Server={server.get('name', 'N/A')}")
    return []


@api_router.get("/servers/{server_id}/departamentos")
async def get_departamentos(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la lista de departamentos/almacenes.
    
    P0 CATÁLOGOS EDARSAHUB-FIRST:
    Lee departamentos desde EDARSAHUB.Servidores_Conexiones.departamentos
    NO consulta BD viva del restaurante.
    NO consulta MongoDB.
    
    MÁXIMA: EDARSAHUB es el cerebro del sistema.
    El modal no debe depender de conexión viva.
    
    Returns:
        Lista de objetos [{codigo, descripcion}] o [] si no hay datos
    """
    from core.server_registry import get_server_by_id
    
    # Obtener servidor desde EDARSAHUB
    server = await get_server_by_id(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_DEPARTAMENTOS] Servidor no encontrado. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # P0: Leer departamentos desde EDARSAHUB
    departamentos_raw = server.get('departamentos', [])
    
    if departamentos_raw:
        # BUG-RBAC-PERM-001: Normalizar formato de respuesta
        # Frontend espera [{codigo, descripcion}] pero EDARSAHUB puede tener strings o dicts
        departamentos = []
        for dep in departamentos_raw:
            if isinstance(dep, dict):
                # Ya es objeto: preservar estructura
                departamentos.append({
                    'codigo': dep.get('codigo') or dep.get('Codigo') or str(dep),
                    'descripcion': dep.get('descripcion') or dep.get('Descripcion') or dep.get('nombre') or dep.get('Nombre') or dep.get('codigo') or str(dep)
                })
            elif isinstance(dep, str):
                # Es string puro: convertir a objeto
                departamentos.append({
                    'codigo': dep,
                    'descripcion': dep  # Usar código como descripción si no hay más datos
                })
            else:
                # Tipo desconocido: convertir a string
                departamentos.append({
                    'codigo': str(dep),
                    'descripcion': str(dep)
                })
        
        logging.info(f"[GET_DEPARTAMENTOS] EDARSAHUB-FIRST: {len(departamentos)} departamentos. Server={server.get('name', 'N/A')}")
        return departamentos
    
    # Sin datos en EDARSAHUB
    logging.info(f"[GET_DEPARTAMENTOS] Sin departamentos en EDARSAHUB (pendiente sync). Server={server.get('name', 'N/A')}")
    return []

async def filter_sucursales_by_config(sucursales: List[Dict], server_id: str) -> List[Dict]:
    """
    Filtra sucursales según la configuración de visibilidad.
    REGLA DE COMPATIBILIDAD:
    - Si NO hay configuración para este servidor -> devuelve TODAS (comportamiento legacy)
    - Si SÍ hay configuración -> devuelve solo las marcadas como visible_en_operaciones=True
    """
    # Buscar configuración existente
    configs = await db.server_sucursales_config.find(
        {"server_id": server_id, "activa": True}
    ).to_list(500)
    
    # Si no hay configuración, devolver todas (backward compatible)
    if not configs or len(configs) == 0:
        return sucursales
    
    # Crear set de IDs visibles
    visibles_ids = {
        str(c.get("sucursal_origen_id")).strip() 
        for c in configs 
        if c.get("visible_en_operaciones", True)
    }
    
    # Si todas están ocultas, devolver todas (safety)
    if not visibles_ids:
        logging.warning(f"Todas las sucursales de {server_id} están ocultas, mostrando todas por seguridad")
        return sucursales
    
    # Filtrar y ordenar
    orden_map = {str(c.get("sucursal_origen_id")).strip(): c.get("orden", 999) for c in configs}
    nombre_map = {str(c.get("sucursal_origen_id")).strip(): c.get("nombre_visible") for c in configs}
    
    resultado = []
    for suc in sucursales:
        suc_id = str(suc.get("id", "")).strip()
        if suc_id in visibles_ids:
            # Aplicar nombre visible si existe
            if nombre_map.get(suc_id):
                suc = {**suc, "nombre_visible": nombre_map[suc_id]}
            suc["_orden"] = orden_map.get(suc_id, 999)
            resultado.append(suc)
    
    # Ordenar por orden configurado
    resultado.sort(key=lambda x: x.get("_orden", 999))
    
    # Limpiar campo temporal
    for r in resultado:
        r.pop("_orden", None)
    
    return resultado

@api_router.get("/servers/{server_id}/sucursales")
async def get_sucursales(server_id: str, include_hidden: bool = False, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la lista de sucursales desde SQL Server, filtradas por permisos y configuración.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 1:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    
    Args:
        include_hidden: Si True, devuelve todas sin filtrar por configuración (para admin UI)
    """
    from core.server_registry import get_server_connection_info
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_SUCURSALES] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_SUCURSALES] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    try:
        sucursales_raw = []
        
        if is_mpro_system(server.get('system_type')):
            # Intentar obtener sucursales de MPRO
            query = "SELECT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre FROM Sucursal WHERE Es_Cve_Estado <> 'BA'"
            try:
                logging.info(f"[MPRO Sucursales] Consultando sucursales para {server['name']}...")
                results = execute_sql_query(
                    server['host'],
                    server['port'],
                    server['database'],
                    server['username'],
                    server['password'],
                    query
                )
                logging.info(f"[MPRO Sucursales] Resultado: {len(results) if results else 0} sucursales")
                if results and len(results) > 0:
                    sucursales_raw = results
            except Exception as e:
                logging.warning(f"MPRO Sucursales query failed: {e}")
            
            # Si no hay sucursales en la tabla Sucursal, intentar usar Almacenes
            if not sucursales_raw:
                try:
                    query_almacen = "SELECT DISTINCT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Es_Cve_Estado <> 'BA'"
                    almacenes = execute_sql_query(
                        server['host'],
                        server['port'],
                        server['database'],
                        server['username'],
                        server['password'],
                        query_almacen
                    )
                    if almacenes and len(almacenes) > 0:
                        sucursales_raw = almacenes
                except Exception as e:
                    logging.warning(f"MPRO Almacenes query failed: {e}")
            
            # Si no hay nada, devolver sucursal virtual "Principal"
            if not sucursales_raw:
                sucursales_raw = [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
            
        elif is_softrestaurant_system(server.get('system_type')):
            # SoftRestaurant NO tiene tabla Sucursal - devolvemos una sucursal virtual con el nombre del servidor
            sucursales_raw = [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
        else:
            # Query genérica para otros sistemas - también con fallback
            try:
                query = "SELECT DISTINCT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre FROM Sucursal"
                results = execute_sql_query(
                    server['host'],
                    server['port'],
                    server['database'],
                    server['username'],
                    server['password'],
                    query
                )
                if results and len(results) > 0:
                    sucursales_raw = results
            except Exception:
                pass
            # Fallback: sucursal virtual
            if not sucursales_raw:
                sucursales_raw = [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
        
        # Aplicar filtro de permisos de usuario
        sucursales_filtradas = filter_sucursales_by_permissions(sucursales_raw, current_user, server_id)
        
        # Aplicar filtro de configuración de visibilidad (si no se pide include_hidden)
        if not include_hidden:
            sucursales_filtradas = await filter_sucursales_by_config(sucursales_filtradas, server_id)
        
        return sucursales_filtradas
        
    except Exception as e:
        logging.error(f"Error obteniendo sucursales: {str(e)}")
        # En caso de error, devolver sucursal virtual en lugar de array vacío
        return [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]

@api_router.get("/servers/{server_id}/almacenes")
async def get_almacenes(server_id: str, sucursal_id: Optional[str] = None, sucursal: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la lista de almacenes desde SQL Server.
    FASE 8: Aplica filtro RBAC por almacenes permitidos.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 1:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # FASE 8: Validar acceso y obtener contexto
    context = await resolve_user_access_context(current_user)
    
    if not has_server_access(context, server_id):
        logging.warning(f"[RBAC-ALMACENES] {current_user.get('email')} sin acceso a servidor {server_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_ALMACENES] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_ALMACENES] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
    
    logging.info(
        f"[RBAC-ALMACENES] Usuario={current_user.get('email')}, "
        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    try:
        # FASE 1B: Importar execute_sql_query_params para parametrización segura
        from core.db import execute_sql_query_params
        
        # FASE 1B: Validar sucursal_id si se proporciona
        if sucursal_id:
            if not _validate_identifier(sucursal_id, max_length=50):
                logging.warning(f"[A01-SANITIZADO] sucursal_id inválido rechazado: {sucursal_id[:50]}")
                raise HTTPException(status_code=400, detail="sucursal_id contiene caracteres no permitidos")
        
        if is_mpro_system(server.get('system_type')):
            # FASE 8: Filtro por almacenes permitidos
            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
            
            # FASE 1B: Parametrización segura de sucursal_id
            if sucursal_id:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = %s AND Es_Cve_Estado <> 'BA'{almacen_filter}"
                results = execute_sql_query_params(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query, (sucursal_id,)
                )
            else:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Es_Cve_Estado <> 'BA'{almacen_filter}"
                results = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
            logging.info(f"[RBAC-ALMACENES] MPRO devolvió {len(results)} almacenes (filtrado RBAC)")
            return results
        
        elif is_softrestaurant_system(server.get('system_type')):
            # FASE 8: Filtro por almacenes permitidos (usa ID numérico)
            almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
            
            query = f"""
SELECT 
    idalmacen as id, 
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
WHERE 1=1{almacen_filter}
ORDER BY nombre
"""
            results = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            logging.info(f"[RBAC-ALMACENES] SoftRestaurant devolvió {len(results)} almacenes (filtrado RBAC)")
            return results
        
        else:
            # Query genérica para otros sistemas con filtro RBAC
            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
            # FASE 1B: Parametrización segura de sucursal_id
            if sucursal_id:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = %s{almacen_filter}"
                results = execute_sql_query_params(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query, (sucursal_id,)
                )
            else:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE 1=1{almacen_filter}"
                results = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
            return results
    except Exception as e:
        logging.error(f"Error obteniendo almacenes: {str(e)}")
        return []

# ============= ENDPOINTS DE CONFIGURACIÓN DE SUCURSALES =============

@api_router.get("/servers/{server_id}/sucursales-config")
async def get_sucursales_config(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la configuración de visibilidad de sucursales para un servidor.
    Retorna lista vacía si no hay configuración (comportamiento legacy).
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 2:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_SUCURSALES_CONFIG] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_SUCURSALES_CONFIG] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # Obtener configuración existente
    configs = await db.server_sucursales_config.find(
        {"server_id": server_id, "activa": True},
        {"_id": 0}
    ).sort("orden", 1).to_list(500)
    
    return {
        "server_id": server_id,
        "server_name": server.get("name"),
        "tiene_configuracion": len(configs) > 0,
        "sucursales": configs
    }

@api_router.post("/servers/{server_id}/sucursales-config/sync")
async def sync_sucursales_config(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Sincroniza las sucursales desde SQL Server con la configuración local.
    - Detecta nuevas sucursales y las agrega como visibles por defecto
    - NO elimina configuraciones existentes (soft delete)
    - Mantiene configuración de sucursales ya existentes
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 2:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden sincronizar")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[SYNC_SUCURSALES_CONFIG] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[SYNC_SUCURSALES_CONFIG] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # Obtener sucursales desde SQL Server
    try:
        sucursales_sql = []
        if is_mpro_system(server.get('system_type')):
            query = "SELECT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre FROM Sucursal WHERE Es_Cve_Estado <> 'BA'"
            sucursales_sql = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            ) or []
        elif is_softrestaurant_system(server.get('system_type')):
            # SoftRestaurant no tiene tabla Sucursal, crear virtual
            sucursales_sql = [{"id": "default", "nombre": server.get('name', 'Principal')}]
        
        if not sucursales_sql:
            sucursales_sql = [{"id": "default", "nombre": server.get('name', 'Principal')}]
    except Exception as e:
        logging.error(f"Error consultando sucursales SQL: {e}")
        sucursales_sql = [{"id": "default", "nombre": server.get('name', 'Principal')}]
    
    # Obtener configuración existente
    existing_configs = await db.server_sucursales_config.find(
        {"server_id": server_id}
    ).to_list(500)
    existing_ids = {c.get("sucursal_origen_id") for c in existing_configs}
    
    # Agregar nuevas sucursales
    nuevas = 0
    actualizadas = 0
    now = datetime.now(timezone.utc)
    user_email = current_user.get("email", "sistema")
    
    for idx, suc in enumerate(sucursales_sql):
        suc_id = str(suc.get("id", "")).strip()
        suc_nombre = str(suc.get("nombre", "")).strip()
        
        if suc_id in existing_ids:
            # Ya existe - actualizar nombre si cambió (reactivar si estaba inactiva)
            await db.server_sucursales_config.update_one(
                {"server_id": server_id, "sucursal_origen_id": suc_id},
                {"$set": {
                    "sucursal_nombre": suc_nombre,
                    "activa": True,
                    "fecha_modificacion": now,
                    "usuario_modificacion": user_email
                }}
            )
            actualizadas += 1
        else:
            # Nueva sucursal - agregar como visible por defecto
            new_config = {
                "id": str(uuid.uuid4()),
                "server_id": server_id,
                "sucursal_origen_id": suc_id,
                "sucursal_nombre": suc_nombre,
                "nombre_visible": None,
                "visible_en_operaciones": True,  # VISIBLE POR DEFECTO
                "orden": idx,
                "activa": True,
                "fecha_alta": now,
                "usuario_alta": user_email,
                "fecha_modificacion": None,
                "usuario_modificacion": None
            }
            await db.server_sucursales_config.insert_one(new_config)
            nuevas += 1
    
    # Obtener configuración actualizada
    configs = await db.server_sucursales_config.find(
        {"server_id": server_id, "activa": True},
        {"_id": 0}
    ).sort("orden", 1).to_list(500)
    
    return {
        "message": f"Sincronización completada: {nuevas} nuevas, {actualizadas} actualizadas",
        "nuevas": nuevas,
        "actualizadas": actualizadas,
        "total": len(configs),
        "sucursales": configs
    }

@api_router.put("/servers/{server_id}/sucursales-config/{sucursal_origen_id}")
async def update_sucursal_config(
    server_id: str, 
    sucursal_origen_id: str, 
    update_data: SucursalConfigUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza la configuración de una sucursal específica."""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar")
    
    # Verificar que existe
    existing = await db.server_sucursales_config.find_one({
        "server_id": server_id,
        "sucursal_origen_id": sucursal_origen_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Configuración de sucursal no encontrada")
    
    # Preparar actualización
    update_fields = {"fecha_modificacion": datetime.now(timezone.utc), "usuario_modificacion": current_user.get("email")}
    if update_data.visible_en_operaciones is not None:
        update_fields["visible_en_operaciones"] = update_data.visible_en_operaciones
    if update_data.nombre_visible is not None:
        update_fields["nombre_visible"] = update_data.nombre_visible
    if update_data.orden is not None:
        update_fields["orden"] = update_data.orden
    if update_data.activa is not None:
        update_fields["activa"] = update_data.activa
    
    await db.server_sucursales_config.update_one(
        {"server_id": server_id, "sucursal_origen_id": sucursal_origen_id},
        {"$set": update_fields}
    )
    
    return {"message": "Configuración actualizada", "sucursal_origen_id": sucursal_origen_id}

@api_router.put("/servers/{server_id}/sucursales-config/bulk")
async def update_sucursales_config_bulk(
    server_id: str, 
    bulk_data: SucursalConfigBulkUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza múltiples sucursales en una sola operación."""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar")
    
    now = datetime.now(timezone.utc)
    user_email = current_user.get("email")
    updated = 0
    
    for suc in bulk_data.sucursales:
        suc_id = suc.get("sucursal_origen_id")
        if not suc_id:
            continue
        
        update_fields = {"fecha_modificacion": now, "usuario_modificacion": user_email}
        if "visible_en_operaciones" in suc:
            update_fields["visible_en_operaciones"] = suc["visible_en_operaciones"]
        if "orden" in suc:
            update_fields["orden"] = suc["orden"]
        if "nombre_visible" in suc:
            update_fields["nombre_visible"] = suc["nombre_visible"]
        
        result = await db.server_sucursales_config.update_one(
            {"server_id": server_id, "sucursal_origen_id": suc_id},
            {"$set": update_fields}
        )
        if result.modified_count > 0:
            updated += 1
    
    return {"message": f"{updated} sucursales actualizadas", "updated": updated}

# ============= FIN ENDPOINTS DE CONFIGURACIÓN DE SUCURSALES =============

# ============= ENDPOINT GLOBAL DE SUCURSALES (para componentes que no tienen server_id) =============
@api_router.get("/sucursales")
async def get_all_sucursales(
    server_id: Optional[str] = Query(None),
    activas: bool = Query(True),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene todas las sucursales configuradas.
    Endpoint global para componentes que necesitan listar sucursales sin conocer el server_id.
    
    Migrado de db.servers.find() a server_registry.list_servers()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 5
    """
    filtro = {}
    if server_id:
        filtro["server_id"] = server_id
    if activas:
        filtro["activa"] = True
    
    cursor = db.server_sucursales_config.find(filtro, {"_id": 0})
    sucursales = await cursor.to_list(500)
    
    # Enriquecer con nombre de servidor usando registry
    # ANTES: server_cursor = db.servers.find({"id": {"$in": server_ids}}, {"_id": 0, "id": 1, "name": 1})
    from core.server_registry import list_servers
    server_ids = list(set(s.get("server_id") for s in sucursales if s.get("server_id")))
    servers = {}
    if server_ids:
        all_servers = await list_servers(db=db, prefer_sql=True)
        for srv in all_servers:
            if srv.get("id") in server_ids:
                servers[srv["id"]] = srv.get("name", srv["id"])
    
    for suc in sucursales:
        suc["server_nombre"] = servers.get(suc.get("server_id"), "")
    
    return sucursales
# ============= FIN ENDPOINT GLOBAL DE SUCURSALES =============

# ============= ENDPOINT UNIDADES DE NEGOCIO (FASE 3.2) =============
# Reemplaza el selector "Servidor" por "Unidad de Negocio" en módulos de negocio
# El backend traduce unidad → server_id internamente
# ==================================================================

@api_router.get("/unidades-negocio")
async def get_unidades_negocio(
    current_user: Dict = Depends(get_current_user)
):
    """
    ============================================================================
    CORRECCIÓN AUDITORIA-UNIDADES-NEGOCIO-01 (2026-04-29):
    
    MANDATO ARQUITECTÓNICO: EDARSAHUB SQL es la ÚNICA fuente maestra de verdad
    para la resolución de unidades de negocio, servidores, empresas y sucursales.
    
    MongoDB NO se usa como fuente, ni como fallback, ni como respaldo.
    Si EDARSAHUB SQL no tiene el dato, retornamos error controlado.
    
    TABLA FUENTE: EDARSAHUB.dbo.Unidades_Negocio
    ============================================================================
    
    Returns:
        Lista de unidades con:
        - id: ID de la unidad de negocio (UUID)
        - codigo: Código corto (130MID, 130QRO, etc.)
        - nombre: Nombre visible ("130° MERIDA", "130° QUERETARO", etc.)
        - server_id: ID técnico del servidor
        - system_type: Tipo de sistema (MPRO, SoftRestaurant)
        - sucursal_origen_id: Código de sucursal en sistema externo (solo MPRO)
        - connection_type: SQL_SERVER | API
    """
    from core.server_registry import EDARSAHUB_CONFIG
    from core.db import execute_sql_query
    
    try:
        # ============================================================================
        # FUENTE ÚNICA: EDARSAHUB SQL
        # ============================================================================
        query = """
        SELECT 
            CAST(un.id AS VARCHAR(50)) as id,
            un.nombre,
            un.codigo,
            CAST(un.server_id AS VARCHAR(50)) as server_id,
            un.sucursal_origen_id,
            un.system_type,
            un.activo,
            un.orden,
            -- Datos del servidor relacionado
            sc.nombre as server_nombre,
            sc.host as server_host,
            sc.database_name as database_name,
            sc.tipo_conexion as connection_type
        FROM Unidades_Negocio un
        INNER JOIN Servidores_Conexiones sc ON CAST(un.server_id AS VARCHAR(50)) = CAST(sc.id AS VARCHAR(50))
        WHERE un.activo = 1
          AND sc.activo = 1
        ORDER BY un.orden, un.nombre
        """
        
        unidades_sql = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if unidades_sql is None:
            logging.error("[UNIDADES_NEGOCIO] EDARSAHUB_SQL_ERROR: Sin respuesta de la base de datos")
            raise HTTPException(
                status_code=503,
                detail="Error de conexión con la base de datos central. No se usa fallback por política arquitectónica."
            )
        
        logging.info(f"[UNIDADES_NEGOCIO] Obtenidas {len(unidades_sql)} unidades desde EDARSAHUB SQL")
        
        # ============================================================================
        # APLICAR RBAC: Filtrar por permisos del usuario
        # ============================================================================
        user_role = current_user.get('role', '')
        
        # SuperAdministrador y Administrador ven todas las unidades
        if user_role in ['SuperAdministrador', 'Administrador']:
            unidades_filtradas = unidades_sql
        else:
            # Otros roles: filtrar por empresas permitidas
            empresas_permitidas = await get_user_empresas_permitidas(current_user)
            allowed_servers = set(current_user.get('allowed_servers', []))
            
            # Filtrar unidades cuyos server_id estén en allowed_servers
            # o cuyo ID esté en empresas_permitidas (para compatibilidad)
            unidades_filtradas = [
                u for u in unidades_sql 
                if u.get('server_id') in allowed_servers or u.get('id') in empresas_permitidas
            ]
            
            if not unidades_filtradas:
                logging.warning(f"[UNIDADES_NEGOCIO] Usuario {current_user.get('email')} sin unidades permitidas")
        
        # ============================================================================
        # CONSTRUIR RESPUESTA
        # ============================================================================
        resultado = []
        for u in unidades_filtradas:
            sucursal_origen_id = u.get('sucursal_origen_id')
            system_type = u.get('system_type', '')
            
            # Para SoftRestaurant (single-tenant), sucursal_origen_id debe ser null
            if system_type == 'SoftRestaurant' and sucursal_origen_id:
                logging.warning(
                    f"[UNIDADES_NEGOCIO] Inconsistencia: {u['nombre']} es SoftRestaurant pero tiene sucursal_origen_id={sucursal_origen_id}"
                )
                sucursal_origen_id = None  # Forzar null para SR
            
            resultado.append({
                "id": u['id'],
                "codigo": u.get('codigo', ''),
                "nombre": u.get('nombre', ''),
                "server_id": u.get('server_id'),
                "server_nombre": u.get('server_nombre', ''),
                "system_type": system_type,
                "connection_type": u.get('connection_type', 'SQL_SERVER'),
                "database_name": u.get('database_name', ''),
                "sucursal_origen_id": sucursal_origen_id,
                # Sucursal en formato legacy para compatibilidad frontend
                "sucursales": [{
                    "id": sucursal_origen_id or u.get('codigo'),
                    "nombre": u.get('nombre')
                }],
                # Metadatos
                "config_origin": "EDARSAHUB_SQL",
                "orden": u.get('orden', 999)
            })
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[UNIDADES_NEGOCIO] Error crítico: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo unidades de negocio desde EDARSAHUB SQL: {str(e)}"
        )

# ============= FIN ENDPOINT UNIDADES DE NEGOCIO =============

@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
async def get_almacenes_softrestaurant(
    server_id: str, 
    solo_consumo: bool = False,  # Filtrar solo almacenes de consumo (tipo=1)
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene la lista de almacenes de SoftRestaurant (no requiere sucursal).
    FASE 8: Aplica filtro RBAC por almacenes permitidos.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 3:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # FASE 8: Validar acceso y obtener contexto
    context = await resolve_user_access_context(current_user)
    
    if not has_server_access(context, server_id):
        logging.warning(f"[RBAC-ALMACENES-SR] {current_user.get('email')} sin acceso a servidor {server_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_ALMACENES_SR] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_ALMACENES_SR] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    if not is_softrestaurant_system(server.get('system_type')):
        raise HTTPException(status_code=400, detail="Este endpoint es solo para SoftRestaurant")
    
    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
    almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
    
    logging.info(
        f"[RBAC-ALMACENES-SR] Usuario={current_user.get('email')}, "
        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    try:
        # Query para obtener almacenes de SoftRestaurant incluyendo el tipo
        # TIPO = 1: Almacén de consumo (tiene ventas) - Se usa para pendientes de descargar
        # TIPO = 2: Almacén de presentaciones (NO tiene ventas)
        where_clause = "WHERE ISNULL(tipo, 1) = 1" if solo_consumo else "WHERE 1=1"
        query = f"""
SELECT 
    idalmacen as id, 
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
{where_clause}{almacen_filter}
ORDER BY nombre
"""
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        logging.info(f"[RBAC-ALMACENES-SR] Devolvió {len(results)} almacenes (filtrado RBAC)")
        return results
    except Exception as e:
        logging.error(f"Error obteniendo almacenes SoftRestaurant: {str(e)}")
        return []

@api_router.get("/servers/{server_id}/inventarios")
async def get_inventarios_list(
    server_id: str, 
    sucursal_id: Optional[str] = None,
    almacen_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene la lista de inventarios físicos disponibles con sus fechas.
    FASE 8: Aplica filtro RBAC por almacenes permitidos.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 3:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # FASE 8: Validar acceso y obtener contexto
    context = await resolve_user_access_context(current_user)
    
    if not has_server_access(context, server_id):
        logging.warning(f"[RBAC-INVENTARIOS-LIST] {current_user.get('email')} sin acceso a servidor {server_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_INVENTARIOS_LIST] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_INVENTARIOS_LIST] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
    
    logging.info(
        f"[RBAC-INVENTARIOS-LIST] Usuario={current_user.get('email')}, "
        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    try:
        if is_mpro_system(server.get('system_type')):
            # FASE 8: Filtro RBAC
            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "F.Al_Cve_Almacen")
            
            where_clause = "WHERE F.Es_Cve_Estado not in ('BA')"
            if sucursal_id:
                where_clause += f" AND F.Sc_Cve_Sucursal = '{sucursal_id}'"
            if almacen_id:
                where_clause += f" AND F.Al_Cve_Almacen = '{almacen_id}'"
            # FASE 8: Agregar filtro RBAC
            where_clause += almacen_rbac_filter
            
            query = f"""
                SELECT 
                    F.Fi_Folio as folio,
                    CONVERT(varchar, F.fi_fecha, 120) as fecha,
                    F.Sc_Cve_Sucursal as sucursal_id,
                    S.Sc_Descripcion as sucursal,
                    F.Al_Cve_Almacen as almacen_id,
                    A.Al_Descripcion as almacen,
                    ISNULL(F.Fi_Comentario, '') as comentario
                FROM Fisico F
                INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND F.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
                {where_clause}
                GROUP BY F.Fi_Folio, F.fi_fecha, F.Sc_Cve_Sucursal, S.Sc_Descripcion, F.Al_Cve_Almacen, A.Al_Descripcion, F.Fi_Comentario
                ORDER BY F.fi_fecha DESC
            """
            logging.info(f"[RBAC-INVENTARIOS-LIST] MPRO Query con filtro RBAC aplicado")
        elif is_softrestaurant_system(server.get('system_type')):
            # FASE 8: Filtro RBAC para SoftRestaurant
            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "INV.idalmacen1")
            
            # Query para SoftRestaurant - fecha en formato YYYY-MM-DD HH:MM:SS
            where_clause = "WHERE 1=1"
            if almacen_id:
                where_clause += f" AND INV.idalmacen1 = '{almacen_id}'"
            # FASE 8: Agregar filtro RBAC
            where_clause += almacen_rbac_filter
            
            query = f"""
                SELECT 
                    INV.folio as folio,
                    CONVERT(varchar, INV.fecha, 120) as fecha,
                    INV.idalmacen1 as almacen_id,
                    A.nombre as almacen,
                    '' as comentario
                FROM invfisico INV
                LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
                {where_clause}
                ORDER BY INV.fecha DESC
            """
            logging.info(f"[RBAC-INVENTARIOS-LIST] SR Query con filtro RBAC aplicado")
        else:
            query = "SELECT Fi_Folio as folio, CONVERT(varchar, fi_fecha, 120) as fecha FROM Fisico GROUP BY Fi_Folio, fi_fecha ORDER BY fi_fecha DESC"
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        return results
    except Exception as e:
        logging.error(f"Error obteniendo inventarios: {str(e)}")
        return []


# ============================================================================
# INSUMOS PENDIENTES DE DESCARGAR (SoftRestaurant)
# ============================================================================
@api_router.get("/inventarios/pendientes/{server_id}")
async def get_insumos_pendientes(
    server_id: str,
    almacen_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene los insumos pendientes de descargar.
    FASE 8: Aplica filtro RBAC por almacenes permitidos.
    - SoftRestaurant: Usa tabla inventariopendiente
    - MPRO: Calcula diferencia entre ventas/consumos y existencias
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 3:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # FASE 8: Validar acceso y obtener contexto
    context = await resolve_user_access_context(current_user)
    
    if not has_server_access(context, server_id):
        logging.warning(f"[RBAC-PENDIENTES] {current_user.get('email')} sin acceso a servidor {server_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_PENDIENTES_DESCARGAR] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_PENDIENTES_DESCARGAR] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # FASE 8: Validar que si se solicita un almacén específico, esté en el alcance
    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
    if almacen_id and almacenes_permitidos and almacen_id not in almacenes_permitidos:
        logging.warning(
            f"[RBAC-PENDIENTES-403] Usuario={current_user.get('email')}, "
            f"Almacén solicitado={almacen_id}, Permitidos={almacenes_permitidos}"
        )
        raise HTTPException(status_code=403, detail="No tiene acceso a este almacén")
    
    system_type = server.get('system_type', '')
    
    logging.info(
        f"[RBAC-PENDIENTES] Usuario={current_user.get('email')}, "
        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    try:
        if is_softrestaurant_system(system_type):
            # FASE 8: Filtro RBAC
            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "ip.idalmacen")
            
            # Query para SoftRestaurant
            where_clause = "WHERE 1=1"
            if almacen_id:
                where_clause += f" AND ip.idalmacen = '{almacen_id}'"
            # FASE 8: Agregar filtro RBAC
            where_clause += almacen_rbac_filter
            
            query = f"""
                SELECT 
                    ip.fecha,
                    ip.idinsumo as codigo,
                    i.descripcion as insumo,
                    ISNULL(g.descripcion, 'SIN GRUPO') as grupo,
                    ip.costo,
                    ip.cantidad,
                    ISNULL(i.unidad, 'PZ') as unidad,
                    ip.idalmacen as almacen,
                    ip.idturno,
                    ABS(ip.costo * ip.cantidad) as total
                FROM inventariopendiente ip
                LEFT JOIN insumos i ON ip.idinsumo = i.idinsumo
                LEFT JOIN gruposi g ON i.idgruposi = g.idgruposi
                {where_clause}
                ORDER BY ABS(ip.costo * ip.cantidad) DESC
            """
            
        elif is_mpro_system(system_type):
            # Query para MPRO - Insumos vendidos sin existencia suficiente
            # Obtener nombre de sucursal desde el servidor
            sucursal_nombre = server.get('name', '').split(' ')[0]  # Tomar primera palabra del nombre
            
            almacen_filter = f"AND venta.Al_Cve_Almacen = '{almacen_id}'" if almacen_id else ""
            
            query = f"""
                DECLARE @sucursal NVARCHAR(50) = '{sucursal_nombre}'
                DECLARE @fecha_ini NVARCHAR(12) = (SELECT TOP 1 CONVERT(DATETIME, DATEFROMPARTS(YEAR(Pr_Fecha_Inicial), MONTH(Pr_Fecha_Inicial), 1), 103) FROM Periodo_Operativo WHERE Pr_Compras = 'NO' ORDER BY Pr_Fecha_final ASC)
                DECLARE @fecha_fin NVARCHAR(12) = (SELECT TOP 1 Pr_Fecha_final FROM Periodo_Operativo WHERE Pr_Compras = 'NO' ORDER BY Pr_Fecha_final DESC)
                
                SELECT  
                    venta.Al_Cve_Almacen AS almacen,
                    Producto_Kit.Pk_Producto AS codigo,
                    categoria.Ct_Descripcion AS categoria,
                    familia.Fm_Descripcion AS grupo,
                    producto.Pr_Descripcion AS insumo,
                    Producto_Kit.Un_Cve_Unidad AS unidad,
                    ROUND(SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad), 3) AS cantidad_vendida,
                    ROUND(MOV.CANT, 3) AS existencia,
                    ROUND(SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) - MOV.CANT, 3) AS diferencia,
                    ISNULL(producto.Pr_Precio_Lista, 0) AS costo,
                    ROUND((SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) - MOV.CANT) * ISNULL(producto.Pr_Precio_Lista, 0), 2) AS total
                FROM venta 
                LEFT JOIN producto_kit ON Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
                LEFT JOIN producto ON producto.Pr_Cve_Producto = Producto_kit.Pk_Producto
                INNER JOIN Categoria ON categoria.Ct_Cve_Categoria = producto.Ct_Cve_Categoria
                INNER JOIN Familia ON familia.Fm_Cve_Familia = Producto.Fm_Cve_Familia
                INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
                INNER JOIN (
                    SELECT  
                        Pr_Cve_Producto,
                        SUM(Mv_Cantidad_Control_1) CANT
                    FROM Movimiento 
                    INNER JOIN Sucursal ON SUCURSAL.Sc_Cve_Sucursal = MOVIMIENTO.Sc_Cve_Sucursal
                    WHERE MV_FECHA <= @fecha_fin 
                    AND SUCURSAL.Sc_Descripcion LIKE '%' + @sucursal + '%'
                    AND Movimiento.Al_Cve_Almacen = '0001'
                    GROUP BY MOVIMIENTO.Pr_Cve_Producto
                ) MOV ON MOV.Pr_Cve_Producto = Producto_Kit.Pk_Producto
                WHERE sucursal.Sc_Descripcion LIKE '%' + @sucursal + '%'
                AND venta.Es_Cve_Estado <> 'CA' 
                AND venta.Vn_Fecha BETWEEN @fecha_ini AND @fecha_fin
                AND producto.Ct_Cve_Categoria IN ('0001','0002','0004')
                AND producto.Dp_Cve_Departamento IN ('0003','0004','0007','0002')
                {almacen_filter}
                GROUP BY 
                    MOV.CANT,
                    Producto_Kit.Pk_Producto,
                    producto.Pr_Descripcion,
                    Producto_Kit.Un_Cve_Unidad,
                    categoria.Ct_Descripcion,
                    familia.Fm_Descripcion,
                    venta.Al_Cve_Almacen,
                    producto.Pr_Precio_Lista
                HAVING (SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) - MOV.CANT) > 0 
                ORDER BY categoria.Ct_Descripcion, familia.Fm_Descripcion, diferencia DESC
            """
        else:
            return {
                "items": [],
                "totales": {"cantidad": 0, "valor": 0, "items": 0},
                "mensaje": f"Este reporte no está disponible para {system_type}"
            }
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        if not results:
            return {
                "items": [],
                "totales": {"cantidad": 0, "valor": 0, "items": 0},
                "almacenes": []
            }
        
        # Procesar resultados según el tipo de sistema
        if is_mpro_system(system_type):
            # Para MPRO, usar 'diferencia' como cantidad y 'total' como valor
            total_cantidad = sum(abs(float(r.get('diferencia') or 0)) for r in results)
            total_valor = sum(abs(float(r.get('total') or 0)) for r in results)
            
            items_con_pareto = []
            acumulado = 0
            for idx, item in enumerate(results):
                total_item = abs(float(item.get('total') or 0))
                acumulado += total_item
                porcentaje_acumulado = (acumulado / total_valor * 100) if total_valor > 0 else 0
                
                items_con_pareto.append({
                    "no": idx + 1,
                    "codigo": str(item.get('codigo', '')).strip(),
                    "insumo": item.get('insumo', ''),
                    "grupo": item.get('grupo', 'SIN GRUPO'),
                    "categoria": item.get('categoria', ''),
                    "cantidad": abs(float(item.get('diferencia') or 0)),
                    "existencia": float(item.get('existencia') or 0),
                    "cantidad_vendida": float(item.get('cantidad_vendida') or 0),
                    "unidad": str(item.get('unidad', 'PZ')).strip(),
                    "costo": float(item.get('costo') or 0),
                    "total": total_item,
                    "almacen": str(item.get('almacen', '')).strip(),
                    "pareto": round(porcentaje_acumulado, 0)
                })
        else:
            # Para SoftRestaurant
            total_cantidad = sum(abs(float(r.get('cantidad') or 0)) for r in results)
            total_valor = sum(float(r.get('total') or 0) for r in results)
            
            items_con_pareto = []
            acumulado = 0
            for idx, item in enumerate(results):
                total_item = float(item.get('total') or 0)
                acumulado += total_item
                porcentaje_acumulado = (acumulado / total_valor * 100) if total_valor > 0 else 0
                
                items_con_pareto.append({
                    "no": idx + 1,
                    "fecha": str(item.get('fecha', ''))[:19] if item.get('fecha') else '',
                    "codigo": item.get('codigo', ''),
                    "insumo": item.get('insumo', ''),
                    "grupo": item.get('grupo', 'SIN GRUPO'),
                    "cantidad": abs(float(item.get('cantidad') or 0)),
                    "unidad": item.get('unidad', 'PZ').strip() if item.get('unidad') else 'PZ',
                    "costo": float(item.get('costo') or 0),
                    "total": total_item,
                    "almacen": str(item.get('almacen', '')).strip(),
                    "idturno": item.get('idturno'),
                    "pareto": round(porcentaje_acumulado, 0)
                })
        
        # Obtener lista de almacenes únicos
        almacenes_unicos = list(set(str(item.get('almacen', '')).strip() for item in results if item.get('almacen')))
        almacenes_unicos.sort()
        
        return {
            "items": items_con_pareto,
            "totales": {
                "cantidad": round(total_cantidad, 2),
                "valor": round(total_valor, 2),
                "items": len(results)
            },
            "almacenes": almacenes_unicos,
            "system_type": system_type
        }
        
    except Exception as e:
        logging.error(f"Error obteniendo insumos pendientes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@api_router.post("/reports/inventory")
async def generate_inventory_report(report_params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Genera un reporte de inventario usando queries predefinidas.
    
    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    server_id = report_params.get('server_id')
    query_type = report_params.get('query_type')  # ventas, movimientos, productos, inventarios
    params = report_params.get('params', {})
    
    # FASE P1.4-C: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Get query template
    query_template = await db.queries.find_one({
        "system_type": server['system_type'],
        "query_type": query_type
    }, {"_id": 0})
    
    if not query_template:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    # Replace parameters in query
    sql_query = query_template['sql_query']
    for key, value in params.items():
        sql_query = sql_query.replace(f"@{key}", f"'{value}'")
    
    # Execute query
    results = execute_sql_query(
        server['host'],
        server['port'],
        server['database'],
        server['username'],
        server['password'],
        sql_query
    )
    
    return {"data": results, "count": len(results)}

@api_router.get("/servers/{server_id}/report-filters")
async def get_report_filters(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene las opciones de filtros (categorías, familias, subfamilias) para el reporte de análisis.
    Soporta MPRO y SoftRestaurant con equivalencias:
    - MPRO: Categoria, Familia, SubFamilia
    - SoftRestaurant: clasificacionventa (CATEGORIA), gruposiclasificacion (FAMILIA), gruposi (SUBFAMILIA)
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 3:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[GET_REPORT_FILTERS] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[GET_REPORT_FILTERS] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    try:
        if is_mpro_system(server.get('system_type')):
            # Obtener categorías
            categorias_query = """
                SELECT DISTINCT Ct_Cve_Categoria as id, Ct_Descripcion as nombre 
                FROM Categoria 
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Ct_Descripcion
            """
            categorias = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], categorias_query
            )
            
            # Obtener familias
            familias_query = """
                SELECT DISTINCT Fm_Cve_Familia as id, Fm_Descripcion as nombre 
                FROM Familia 
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Fm_Descripcion
            """
            familias = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], familias_query
            )
            
            # Obtener subfamilias
            subfamilias_query = """
                SELECT DISTINCT Sf_Cve_SubFamilia as id, Sf_Descripcion as nombre 
                FROM SubFamilia 
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Sf_Descripcion
            """
            subfamilias = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], subfamilias_query
            )
            
            return {
                "categorias": categorias or [],
                "familias": familias or [],
                "subfamilias": subfamilias or []
            }
            
        elif is_softrestaurant_system(server.get('system_type')):
            # Para SoftRestaurant:
            # clasificacionventa (1=ALIMENTOS, 2=BEBIDAS, 3=OTROS) = CATEGORIA
            # gruposiclasificacion = FAMILIA
            # gruposi = SUBFAMILIA
            
            # Categorías fijas según clasificacionventa
            categorias = [
                {"id": "1", "nombre": "ALIMENTOS"},
                {"id": "2", "nombre": "BEBIDAS"},
                {"id": "3", "nombre": "OTROS"}
            ]
            
            # Obtener familias (gruposiclasificacion)
            familias_query = """
                SELECT DISTINCT 
                    CAST(idgruposiclasificacion as VARCHAR) as id, 
                    descripcion as nombre 
                FROM gruposiclasificacion
                ORDER BY descripcion
            """
            familias = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], familias_query
            )
            
            # Obtener subfamilias (gruposi)
            subfamilias_query = """
                SELECT DISTINCT 
                    CAST(idgruposi as VARCHAR) as id, 
                    descripcion as nombre 
                FROM gruposi
                ORDER BY descripcion
            """
            subfamilias = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], subfamilias_query
            )
            
            return {
                "categorias": categorias,
                "familias": familias or [],
                "subfamilias": subfamilias or []
            }
        else:
            return {"categorias": [], "familias": [], "subfamilias": []}
            
    except Exception as e:
        logging.error(f"Error obteniendo filtros: {str(e)}")
        return {"categorias": [], "familias": [], "subfamilias": []}


# =============================================================================
# FUNCIÓN REUTILIZABLE - Análisis de Inventarios
# CAB-003 Fase 1A: Permite reutilización desde Core Service sin modificar endpoint
# =============================================================================

# Referencia a la función del endpoint para uso externo
# Esta variable se asigna después de definir el endpoint
_inventory_analysis_endpoint_ref = None



@api_router.post("/reports/inventory-analysis")
async def generate_inventory_analysis(report_params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Genera un análisis completo de inventario con:
    - Inventario Inicial (folio inicial)
    - Ventas (entre fechas) - Usando consulta original con UNION ALL
    - Movimientos (entre fechas) - Con lógica especial de fechas para tipos 508/108
    - Inventario Final (folio final)
    - Cálculo de diferencias
    Usa filtros configurables por servidor (tipos_movimiento, categorias, departamentos)
    Acepta filtros adicionales del frontend (categorias, familias, subfamilias)
    
    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    server_id = report_params.get('server_id')
    sucursal = report_params.get('sucursal')
    almacen = report_params.get('almacen')
    almacenes = report_params.get('almacenes', [])  # Multi-almacén
    fecha_ini = report_params.get('fecha_ini')
    fecha_fin = report_params.get('fecha_fin')
    folio_inicial = report_params.get('folio_inicial')
    folio_final = report_params.get('folio_final')
    
    # Multi-folios (nuevo)
    folios_iniciales = report_params.get('folios_iniciales', [])
    folios_finales = report_params.get('folios_finales', [])
    
    # Info completa de inventarios (folio + comentario) para MPRO
    inventarios_iniciales_info = report_params.get('inventarios_iniciales_info', [])
    inventarios_finales_info = report_params.get('inventarios_finales_info', [])
    
    # Normalizar a listas - si hay multi-folios, usarlos; si no, usar el individual
    if folios_iniciales:
        lista_folios_ini = folios_iniciales
    elif folio_inicial:
        lista_folios_ini = [folio_inicial]
    else:
        lista_folios_ini = []
    
    if folios_finales:
        lista_folios_fin = folios_finales
    elif folio_final:
        lista_folios_fin = [folio_final]
    else:
        lista_folios_fin = []
    
    # FASE 1B: Validar y sanitizar folios para prevenir SQL Injection
    MAX_FOLIOS = 50  # Límite máximo de folios por solicitud
    
    def _sanitize_folio_list(folios: list, max_count: int = MAX_FOLIOS) -> list:
        """Valida y sanitiza una lista de folios."""
        if not folios:
            return []
        sanitized = []
        for f in folios[:max_count]:
            if f and isinstance(f, str):
                # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
                if _validate_identifier(str(f), max_length=50):
                    # Escapar comillas simples
                    sanitized.append(str(f).replace("'", "''"))
                else:
                    logging.warning(f"[A04-SANITIZADO] Folio inválido rechazado: {str(f)[:20]}")
        return sanitized
    
    # Aplicar sanitización a las listas de folios
    lista_folios_ini = _sanitize_folio_list(lista_folios_ini)
    lista_folios_fin = _sanitize_folio_list(lista_folios_fin)
    
    # Filtros adicionales del frontend
    filtro_categorias_frontend = report_params.get('categorias', [])
    filtro_familias_frontend = report_params.get('familias', [])
    filtro_subfamilias_frontend = report_params.get('subfamilias', [])
    
    # Opción de agrupación de insumos (por defecto NO agrupar)
    agrupar_insumos = report_params.get('agrupar_insumos', False)
    
    logging.info(f"Filtros recibidos del frontend - Categorias: {filtro_categorias_frontend}, Familias: {filtro_familias_frontend}, SubFamilias: {filtro_subfamilias_frontend}")
    logging.info(f"Agrupar insumos: {agrupar_insumos}")
    
    # FASE P1.4-C: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if is_mpro_system(server.get('system_type')):
            logging.info(f"Generando análisis de inventario MPRO: {sucursal} - {almacen}")
            logging.info(f"Fechas: {fecha_ini} a {fecha_fin}")
            logging.info(f"Folios iniciales: {lista_folios_ini}, finales: {lista_folios_fin}")
            
            # Generar cadenas SQL para folios múltiples
            folios_ini_sql = ",".join([f"'{f}'" for f in lista_folios_ini]) if lista_folios_ini else "''"
            folios_fin_sql = ",".join([f"'{f}'" for f in lista_folios_fin]) if lista_folios_fin else "''"
            
            # Obtener filtros configurados del servidor
            tipos_movimiento = server.get('tipos_movimiento', [])
            categorias_servidor = server.get('categorias', [])
            
            # PRIORIDAD: Si el frontend envía filtros, usarlos. Si no, usar los del servidor.
            categorias = filtro_categorias_frontend if filtro_categorias_frontend else categorias_servidor
            
            logging.info(f"Filtros finales - Tipos Mov: {len(tipos_movimiento)}, Categorias: {len(categorias)}")
            
            # Construir filtros SQL dinámicos
            if tipos_movimiento:
                tipos_mov_sql = ",".join([f"'{t}'" for t in tipos_movimiento])
                filtro_tipos_mov = f"AND E.Tm_Cve_Tipo_Movimiento IN ({tipos_mov_sql})"
            else:
                filtro_tipos_mov = ""
            
            if categorias:
                categorias_sql = ",".join([f"'{c}'" for c in categorias])
                filtro_categorias_p = f"AND P.Ct_Cve_Categoria IN ({categorias_sql})"
            else:
                filtro_categorias_p = ""
            
            # Filtros de familia y subfamilia del frontend
            if filtro_familias_frontend:
                familias_sql = ",".join([f"'{f}'" for f in filtro_familias_frontend])
                filtro_familias_p = f"AND P.Fm_Cve_Familia IN ({familias_sql})"
            else:
                filtro_familias_p = ""
            
            if filtro_subfamilias_frontend:
                subfamilias_sql = ",".join([f"'{s}'" for s in filtro_subfamilias_frontend])
                filtro_subfamilias_p = f"AND P.Sf_Cve_SubFamilia IN ({subfamilias_sql})"
            else:
                filtro_subfamilias_p = ""
            
            # ==================== LÓGICA MPRO CORREGIDA ====================
            # El reporte muestra productos del departamento '0007' (INSUMOS)
            # - Si el INSUMO tiene presentaciones (en Producto_Presentacion) → mostrar el INSUMO
            # - Si NO tiene presentaciones → mostrar la clave de COMPRA
            # - Las ventas se calculan usando Producto_Kit (recetas)
            # 
            # FECHAS MPRO:
            # - Movimientos y Ventas: desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
            # - Ejemplo: Si inventario inicial es 28-Feb-2026, movimientos/ventas desde 01-Mar-2026
            # ===============================================================
            
            # Obtener fechas de los inventarios si no se proporcionan explícitamente
            from datetime import datetime, timedelta
            
            # Si no hay fecha_ini, intentar obtenerla de inventarios_iniciales_info o del folio
            if not fecha_ini:
                if inventarios_iniciales_info and inventarios_iniciales_info[0].get('fecha'):
                    fecha_ini = inventarios_iniciales_info[0]['fecha'][:10]  # YYYY-MM-DD
                elif lista_folios_ini:
                    # Obtener fecha del primer folio inicial
                    fecha_folio_query = f"SELECT TOP 1 CONVERT(varchar, Fi_Fecha, 120) as fecha FROM Fisico WHERE Fi_Folio = '{lista_folios_ini[0]}'"
                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
                    if fecha_result:
                        fecha_ini = fecha_result[0]['fecha'][:10]
                    else:
                        raise HTTPException(status_code=400, detail="No se pudo determinar la fecha inicial")
                else:
                    raise HTTPException(status_code=400, detail="Se requiere fecha_ini o inventarios_iniciales_info")
            
            if not fecha_fin:
                if inventarios_finales_info and inventarios_finales_info[0].get('fecha'):
                    fecha_fin = inventarios_finales_info[0]['fecha'][:10]
                elif lista_folios_fin:
                    fecha_folio_query = f"SELECT TOP 1 CONVERT(varchar, Fi_Fecha, 120) as fecha FROM Fisico WHERE Fi_Folio = '{lista_folios_fin[0]}'"
                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
                    if fecha_result:
                        fecha_fin = fecha_result[0]['fecha'][:10]
                    else:
                        raise HTTPException(status_code=400, detail="No se pudo determinar la fecha final")
                else:
                    raise HTTPException(status_code=400, detail="Se requiere fecha_fin o inventarios_finales_info")
            
            # Calcular fecha de inicio para movimientos/ventas (fecha_ini + 1 día)
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ini_mov = (fecha_ini_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            logging.info(f"MPRO - Fecha movimientos/ventas: {fecha_ini_mov} a {fecha_fin}")
            
            # 1. Obtener códigos de TODOS los almacenes seleccionados
            # Si hay almacenes múltiples, usarlos; si no, usar el almacén simple
            lista_almacenes = almacenes if almacenes else [almacen] if almacen else []
            
            if not lista_almacenes:
                raise HTTPException(status_code=400, detail="Debe seleccionar al menos un almacén")
            
            # FASE 1B: Escapar caracteres especiales de LIKE para prevenir SQL Injection
            almacenes_like_conditions = " OR ".join([f"A.Al_Descripcion LIKE '%{_escape_like_pattern(alm)}%'" for alm in lista_almacenes])
            sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
            
            almacen_query = f"""
SELECT 
    A.Al_Cve_Almacen as codigo,
    A.Al_Descripcion as nombre,
    A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE ({almacenes_like_conditions})
    AND S.Sc_Descripcion LIKE '%{sucursal_safe}%'
"""
            almacen_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], almacen_query
            )
            if not almacen_result:
                logging.error(f"Almacén(es) no encontrado(s) en MPRO - Sucursal: '{sucursal}', Almacenes: {lista_almacenes}, Servidor: {server.get('name', server_id)}")
                raise HTTPException(status_code=404, detail=f"Almacén no encontrado en sucursal '{sucursal}'. Verifique la conexión al servidor SQL o que el almacén exista.")
            
            # Lista de códigos de almacén
            almacenes_codigos = [r['codigo'] for r in almacen_result]
            almacenes_nombres = [r['nombre'] for r in almacen_result]
            sucursal_codigo = almacen_result[0]['sucursal_codigo']
            
            # Para compatibilidad: usar el primer almacén como principal
            almacen_codigo = almacenes_codigos[0]
            almacen_nombre = almacenes_nombres[0]
            
            # Construir SQL IN clause para múltiples almacenes
            almacenes_sql = ",".join([f"'{c}'" for c in almacenes_codigos])
            
            # MPRO: Detectar si ALGÚN almacén es tipo BODEGA
            es_almacen_bodega = any('BODEGA' in (n.upper() if n else '') for n in almacenes_nombres)
            
            logging.info(f"Almacenes encontrados: {almacenes_codigos} - {almacenes_nombres} (Sucursal: {sucursal_codigo})")
            logging.info(f"MPRO - Incluye almacén BODEGA: {es_almacen_bodega}")
            
            # 2. Obtener productos que se controlan en inventario:
            # a) INSUMOS (Dp_Cve_Departamento = '0007') que tienen presentaciones configuradas
            # b) Productos de COMPRA (cualquier depto != 0007) que NO están como presentación de ningún insumo
            # NOTA: Traemos productos que tengan inventario físico O movimientos O ventas en el período
            productos_query = f"""
SELECT DISTINCT
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    F.Fm_Descripcion as Familia,
    SF.Sf_Descripcion as SubFamilia,
    C.Ct_Descripcion as Categoria,
    P.Pr_Unidad_Control_1 as Unidad,
    P.Pr_ultimo_costo as Costo_Unitario,
    D.Dp_Descripcion as Departamento,
    CASE 
        WHEN P.Dp_Cve_Departamento = '0007' THEN 'INSUMO'
        ELSE 'COMPRA'
    END as Tipo_Producto,
    CASE 
        WHEN EXISTS (SELECT 1 FROM Producto_Presentacion PP WHERE PP.Pr_Cve_Producto = P.Pr_Cve_Producto) THEN 1
        ELSE 0
    END as Tiene_Presentaciones
FROM Producto P
INNER JOIN Familia F ON F.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SF ON SF.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
INNER JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
INNER JOIN Departamento D ON D.Dp_Cve_Departamento = P.Dp_Cve_Departamento
WHERE P.Es_Cve_Estado <> 'BA'
    AND (
        -- Caso A: Es un INSUMO (depto 0007) que tiene presentaciones configuradas
        (P.Dp_Cve_Departamento = '0007' AND EXISTS (SELECT 1 FROM Producto_Presentacion PP WHERE PP.Pr_Cve_Producto = P.Pr_Cve_Producto))
        OR
        -- Caso B: Es un producto de COMPRA (depto != 0007) que NO está registrado como presentación de otro producto
        (P.Dp_Cve_Departamento <> '0007' AND NOT EXISTS (SELECT 1 FROM Producto_Presentacion PP WHERE PP.Pp_Producto = P.Pr_Cve_Producto))
    )
    {filtro_categorias_p}
    {filtro_familias_p}
    {filtro_subfamilias_p}
    -- Productos que tienen: inventario físico O movimientos en el período
    AND (
        -- Tiene inventario físico capturado
        EXISTS (
            SELECT 1 FROM Fisico FIS 
            WHERE FIS.Pr_Cve_Producto = P.Pr_Cve_Producto 
            AND FIS.Fi_Folio IN ({folios_ini_sql}, {folios_fin_sql})
            AND FIS.Al_Cve_Almacen IN ({almacenes_sql})
        )
        OR
        -- Tiene movimientos en el período (entradas/salidas/traspasos)
        EXISTS (
            SELECT 1 FROM Movimiento MOV
            WHERE MOV.Pr_Cve_Producto = P.Pr_Cve_Producto
            AND MOV.Sc_Cve_Sucursal = '{sucursal_codigo}'
            AND MOV.Al_Cve_Almacen IN ({almacenes_sql})
            AND MOV.Es_Cve_Estado <> 'CA'
            AND MOV.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        )
    )
ORDER BY F.Fm_Descripcion, SF.Sf_Descripcion, P.Pr_Descripcion
"""
            logging.info("Obteniendo catalogo de productos MPRO (INSUMOS con presentaciones + COMPRAS sin presentacion)...")
            productos = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], productos_query
            )
            logging.info(f"Productos obtenidos: {len(productos)}")
            
            # 3. Obtener ventas - UNION ALL de ventas KIT + ventas DIRECTAS
            # Consulta proporcionada por el usuario para MPRO
            # MPRO: Ventas desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
            # NOTA: Los almacenes tipo BODEGA no tienen ventas
            ventas_dict = {}
            
            if not es_almacen_bodega:
                ventas_query = f"""
SELECT Producto_Codigo, SUM(cantidad) as Total_Ventas FROM (
    -- Ventas de productos KIT (usando recetas de Producto_Kit)
    SELECT 
        Producto_Kit.Pk_Producto as Producto_Codigo,
        SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) as cantidad
    FROM venta 
    LEFT JOIN producto_kit ON Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
    LEFT JOIN producto ON producto.Pr_Cve_Producto = Producto_kit.Pk_Producto
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Cve_Sucursal = '{sucursal_codigo}'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini_mov}' AND '{fecha_fin} 23:59:59'
        AND producto_kit.Pk_Producto IS NOT NULL
    GROUP BY Producto_Kit.Pk_Producto

    UNION ALL

    -- Ventas DIRECTAS (productos vendidos directamente sin receta)
    SELECT 
        venta.Pr_Cve_Producto as Producto_Codigo,
        SUM(venta.Vn_Cantidad_Control_1) as cantidad
    FROM venta 
    INNER JOIN producto ON producto.Pr_Cve_Producto = venta.Pr_Cve_Producto 
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Cve_Sucursal = '{sucursal_codigo}'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini_mov}' AND '{fecha_fin} 23:59:59'
    GROUP BY venta.Pr_Cve_Producto
) AS VentasCombinadas
GROUP BY Producto_Codigo
"""
                logging.info("Obteniendo ventas (KIT + DIRECTAS)...")
                ventas_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], ventas_query
                )
                ventas_dict = {v['Producto_Codigo']: float(v['Total_Ventas'] or 0) for v in ventas_result}
                logging.info(f"Ventas obtenidas para {len(ventas_dict)} productos")
            else:
                logging.info(f"MPRO - Almacén BODEGA '{almacen_nombre}' - Ventas = 0 para todos los productos")
            
            # 4. Obtener movimientos por producto FILTRADO POR ALMACÉN
            # Consulta proporcionada por el usuario para MPRO
            # Lógica especial de fecha para tipos '508' y '108':
            # - Si Mv_Tabla = 'CONVERSION_PRODUCTO' → usa Mv_Fecha
            # - Si no → busca la fecha en la tabla Compra a través de Conversion_Producto
            # MPRO: Movimientos desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
            movimientos_query = f"""
SELECT 
    E.Pr_Cve_Producto as Producto_Codigo,
    SUM(E.Mv_Cantidad_Control_1) as Total_Movimientos
FROM Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
INNER JOIN Producto P ON P.Pr_Cve_Producto = E.Pr_Cve_Producto
WHERE S.Sc_Descripcion LIKE '%{_escape_like_pattern(sucursal) if sucursal else ""}%'
    AND E.Al_Cve_Almacen IN ({almacenes_sql})
    AND E.Es_Cve_Estado <> 'CA'
    {filtro_tipos_mov}
    AND (
        CASE   
            WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
            THEN 
                CASE WHEN E.Mv_Tabla = 'CONVERSION_PRODUCTO' THEN E.Mv_Fecha 
                ELSE (
                    SELECT TOP 1 C.Co_Fecha FROM Conversion_Producto CN
                    INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
                    WHERE CN.Cp_Folio = E.Mv_Documento
                )
                END
            ELSE E.Mv_Fecha
        END
    ) BETWEEN '{fecha_ini_mov}' AND '{fecha_fin} 23:59:59'
GROUP BY E.Pr_Cve_Producto
"""
            logging.info("Obteniendo movimientos (con lógica especial de fechas para tipos 508/108)...")
            movimientos_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], movimientos_query
            )
            movimientos_dict = {m['Producto_Codigo']: float(m['Total_Movimientos'] or 0) for m in movimientos_result}
            logging.info(f"Movimientos obtenidos para {len(movimientos_dict)} productos")
            
            # 5. Detectar errores de captura de inventario
            # Si un producto está en Producto_Presentacion como Pp_Producto (es una presentación)
            # Y también fue capturado en inventario físico, es un ERROR
            errores_captura_query = f"""
SELECT DISTINCT 
    PP.Pp_Producto as Codigo_Presentacion,
    P_PRES.Pr_Descripcion as Descripcion_Presentacion,
    PP.Pr_Cve_Producto as Codigo_Insumo,
    P_INS.Pr_Descripcion as Descripcion_Insumo
FROM Producto_Presentacion PP
INNER JOIN Producto P_PRES ON P_PRES.Pr_Cve_Producto = PP.Pp_Producto
INNER JOIN Producto P_INS ON P_INS.Pr_Cve_Producto = PP.Pr_Cve_Producto
INNER JOIN Fisico F ON F.Pr_Cve_Producto = PP.Pp_Producto
    AND F.Al_Cve_Almacen IN ({almacenes_sql})
    AND F.Fi_Folio IN ({folios_ini_sql}, {folios_fin_sql})
WHERE P_INS.Dp_Cve_Departamento = '0007'
"""
            errores_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], errores_captura_query
            )
            if errores_result:
                logging.warning(f"ERRORES DE CAPTURA DETECTADOS: {len(errores_result)} presentaciones capturadas incorrectamente")
                for err in errores_result:
                    logging.warning(f"  - Presentación {err['Codigo_Presentacion']} ({err['Descripcion_Presentacion']}) capturada en inventario, pero debería capturarse como INSUMO {err['Codigo_Insumo']} ({err['Descripcion_Insumo']})")
            
            # 6. Combinar resultados
            logging.info("Combinando resultados...")
            logging.info(f"Modo de agrupación: {'AGRUPADO' if agrupar_insumos else 'SIN AGRUPAR'}")
            results = []
            errores_list = []
            
            if agrupar_insumos:
                # MODO AGRUPADO: Una fila por producto (comportamiento original)
                for prod in productos:
                    codigo = prod['Codigo']
                    ventas_total = ventas_dict.get(codigo, 0)
                    movimientos = movimientos_dict.get(codigo, 0)
                    inv_inicial = float(prod.get('Inv_Inicial_Cantidad', 0) or 0)
                    inv_final = float(prod.get('Inv_Final_Cantidad', 0) or 0)
                    costo = float(prod.get('Costo_Unitario', 0) or 0)
                    tipo_producto = prod.get('Tipo_Producto', 'COMPRA')
                    
                    # Solo incluir productos con alguna actividad
                    if inv_inicial == 0 and inv_final == 0 and ventas_total == 0 and movimientos == 0:
                        continue
                    
                    # Calcular inventario teórico: Inicial + Movimientos - Ventas
                    inv_teorico = inv_inicial + movimientos - ventas_total
                    
                    # Calcular diferencias
                    diferencia_cantidad = inv_final - inv_teorico
                    diferencia_costo = diferencia_cantidad * costo
                    diferencia_porcentaje = (diferencia_cantidad / inv_teorico * 100) if inv_teorico != 0 else 0
                    valor_real = diferencia_cantidad * costo
                    teorico_ventas = ventas_total * costo
                    
                    # Construir strings de folios y comentarios (agrupados)
                    folios_ini_str = ', '.join([i.get('folio', '') for i in inventarios_iniciales_info]) if inventarios_iniciales_info else ', '.join(lista_folios_ini)
                    folios_fin_str = ', '.join([i.get('folio', '') for i in inventarios_finales_info]) if inventarios_finales_info else ', '.join(lista_folios_fin)
                    comentarios_ini_str = ', '.join([i.get('comentario', '') for i in inventarios_iniciales_info if i.get('comentario')]) if inventarios_iniciales_info else ''
                    comentarios_fin_str = ', '.join([i.get('comentario', '') for i in inventarios_finales_info if i.get('comentario')]) if inventarios_finales_info else ''
                    
                    results.append({
                        'ID_Inv_Ini': folios_ini_str,
                        'Comentario_Ini': comentarios_ini_str,
                        'ID_Inv_Fin': folios_fin_str,
                        'Comentario_Fin': comentarios_fin_str,
                        'Tipo': tipo_producto,
                        'Categoria': prod.get('Categoria'),
                        'Familia': prod.get('Familia'),
                        'SubFamilia': prod.get('SubFamilia'),
                        'Codigo': codigo,
                        'Producto': prod.get('Producto'),
                        'Unidad': prod.get('Unidad'),
                        'Costo_Unitario': round(costo, 2),
                        'Inv_Inicial_Cantidad': round(inv_inicial, 2),
                        'Inv_Inicial_Costo': round(inv_inicial * costo, 2),
                        'Movimientos': round(movimientos, 2),
                        'Movimientos_Costo': round(movimientos * costo, 2),
                        'Ventas': round(ventas_total, 2),
                        'Ventas_Costo': round(ventas_total * costo, 2),
                        'Inv_Teorico_Cantidad': round(inv_teorico, 2),
                        'Inv_Teorico_Costo': round(inv_teorico * costo, 2),
                        'Inv_Final_Cantidad': round(inv_final, 2),
                        'Inv_Final_Costo': round(inv_final * costo, 2),
                        'Diferencia_Cantidad': round(diferencia_cantidad, 2),
                        'Diferencia_Costo': round(diferencia_costo, 2),
                        'Diferencia_Porcentaje': round(diferencia_porcentaje, 2),
                        'Valor_Real': round(valor_real, 2),
                        'Teorico': round(teorico_ventas, 2)
                    })
            else:
                # MODO SIN AGRUPAR: Una fila por cada combinación producto + inventario
                # Obtener inventarios detallados por folio, incluyendo el código de almacén
                inv_detalle_query = f"""
SELECT 
    F.Fi_Folio as Folio,
    F.Pr_Cve_Producto as Codigo,
    F.Fi_Cantidad_Control_1 as Cantidad,
    F.Al_Cve_Almacen as Almacen_Codigo,
    ISNULL(F.Fi_Comentario, '') as Comentario
FROM Fisico F
WHERE F.Fi_Folio IN ({folios_ini_sql}, {folios_fin_sql}) 
    AND F.Al_Cve_Almacen IN ({almacenes_sql})
ORDER BY F.Pr_Cve_Producto, F.Fi_Folio
"""
                inv_detalle = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], inv_detalle_query
                )
                
                # Crear diccionarios de folios iniciales y finales
                folios_ini_set = set(lista_folios_ini)
                folios_fin_set = set(lista_folios_fin)
                
                # Mapear folio -> almacén para obtener movimientos específicos
                folio_almacen_map = {}
                for row in inv_detalle:
                    folio_almacen_map[row['Folio']] = row['Almacen_Codigo']
                
                # Organizar inventarios por código y folio
                inv_por_codigo = {}
                for row in inv_detalle:
                    codigo = row['Codigo']
                    folio = row['Folio']
                    cantidad = float(row['Cantidad'] or 0)
                    comentario = row['Comentario'] or ''
                    almacen_cod = row['Almacen_Codigo']
                    
                    if codigo not in inv_por_codigo:
                        inv_por_codigo[codigo] = {'ini': {}, 'fin': {}}
                    
                    if folio in folios_ini_set:
                        inv_por_codigo[codigo]['ini'][folio] = {'cantidad': cantidad, 'comentario': comentario, 'almacen': almacen_cod}
                    elif folio in folios_fin_set:
                        inv_por_codigo[codigo]['fin'][folio] = {'cantidad': cantidad, 'comentario': comentario, 'almacen': almacen_cod}
                
                # Procesar productos con inventarios detallados
                for prod in productos:
                    codigo = prod['Codigo']
                    costo = float(prod.get('Costo_Unitario', 0) or 0)
                    tipo_producto = prod.get('Tipo_Producto', 'COMPRA')
                    
                    inv_data = inv_por_codigo.get(codigo, {'ini': {}, 'fin': {}})
                    
                    # Si no hay inventarios, omitir
                    if not inv_data['ini'] and not inv_data['fin']:
                        continue
                    
                    # Crear filas por cada combinación de folios
                    # Emparejar por orden de selección
                    folios_ini_list = list(inv_data['ini'].keys()) if inv_data['ini'] else ['']
                    folios_fin_list = list(inv_data['fin'].keys()) if inv_data['fin'] else ['']
                    
                    # Generar tantas filas como sea necesario (máximo entre ini y fin)
                    max_filas = max(len(folios_ini_list), len(folios_fin_list), 1)
                    
                    for idx in range(max_filas):
                        folio_ini = folios_ini_list[idx] if idx < len(folios_ini_list) else ''
                        folio_fin = folios_fin_list[idx] if idx < len(folios_fin_list) else ''
                        
                        inv_inicial = inv_data['ini'].get(folio_ini, {}).get('cantidad', 0) if folio_ini else 0
                        inv_final = inv_data['fin'].get(folio_fin, {}).get('cantidad', 0) if folio_fin else 0
                        comentario_ini = inv_data['ini'].get(folio_ini, {}).get('comentario', '') if folio_ini else ''
                        comentario_fin = inv_data['fin'].get(folio_fin, {}).get('comentario', '') if folio_fin else ''
                        
                        # Movimientos y ventas totales del producto (no se dividen, aplican al consolidado)
                        # En modo sin agrupar, cada fila representa un almacén diferente
                        # Los movimientos y ventas son globales del producto
                        mov_fila = movimientos_dict.get(codigo, 0)
                        ven_fila = ventas_dict.get(codigo, 0)
                        
                        # Solo incluir si hay actividad
                        if inv_inicial == 0 and inv_final == 0:
                            continue
                        
                        # Calcular inventario teórico: Inicial + Movimientos - Ventas
                        inv_teorico = inv_inicial + mov_fila - ven_fila
                        
                        # Calcular diferencias
                        diferencia_cantidad = inv_final - inv_teorico
                        diferencia_costo = diferencia_cantidad * costo
                        diferencia_porcentaje = (diferencia_cantidad / inv_teorico * 100) if inv_teorico != 0 else 0
                        valor_real = diferencia_cantidad * costo
                        teorico_ventas = ven_fila * costo
                        
                        results.append({
                            'ID_Inv_Ini': folio_ini,
                            'Comentario_Ini': comentario_ini,
                            'ID_Inv_Fin': folio_fin,
                            'Comentario_Fin': comentario_fin,
                            'Tipo': tipo_producto,
                            'Categoria': prod.get('Categoria'),
                            'Familia': prod.get('Familia'),
                            'SubFamilia': prod.get('SubFamilia'),
                            'Codigo': codigo,
                            'Producto': prod.get('Producto'),
                            'Unidad': prod.get('Unidad'),
                            'Costo_Unitario': round(costo, 2),
                            'Inv_Inicial_Cantidad': round(inv_inicial, 2),
                            'Inv_Inicial_Costo': round(inv_inicial * costo, 2),
                            'Movimientos': round(mov_fila, 2),
                            'Movimientos_Costo': round(mov_fila * costo, 2),
                            'Ventas': round(ven_fila, 2),
                            'Ventas_Costo': round(ven_fila * costo, 2),
                            'Inv_Teorico_Cantidad': round(inv_teorico, 2),
                            'Inv_Teorico_Costo': round(inv_teorico * costo, 2),
                            'Inv_Final_Cantidad': round(inv_final, 2),
                            'Inv_Final_Costo': round(inv_final * costo, 2),
                            'Diferencia_Cantidad': round(diferencia_cantidad, 2),
                            'Diferencia_Costo': round(diferencia_costo, 2),
                            'Diferencia_Porcentaje': round(diferencia_porcentaje, 2),
                            'Valor_Real': round(valor_real, 2),
                            'Teorico': round(teorico_ventas, 2)
                        })
            
            # Agregar errores de captura al resultado si existen
            for err in errores_result:
                errores_list.append({
                    'tipo': 'ERROR_CAPTURA',
                    'mensaje': f"Presentación '{err['Descripcion_Presentacion']}' ({err['Codigo_Presentacion']}) capturada en inventario. Debería capturarse como INSUMO '{err['Descripcion_Insumo']}' ({err['Codigo_Insumo']})"
                })
            
            logging.info(f"Análisis MPRO completado: {len(results)} productos procesados, {len(errores_list)} errores de captura")
            
            # ===== GUARDAR DIFERENCIAS EN CACHE PARA COMPARATIVO DE 4 CORTES =====
            try:
                # Extraer info de los inventarios FINALES para el cache
                # El comparativo requiere las diferencias del inventario FINAL (físico vs teórico)
                logging.info(f"CACHE: Procesando {len(inventarios_finales_info)} inventarios finales para cache")
                
                for inv_info in inventarios_finales_info:
                    folio_cache = inv_info.get('folio', '')
                    comentario_cache = inv_info.get('comentario', '')
                    almacen_id_cache = inv_info.get('almacen_id', '') or almacen_codigo
                    fecha_cache = inv_info.get('fecha', '')
                    
                    if not folio_cache:
                        logging.warning(f"CACHE: Inventario sin folio, saltando")
                        continue
                    
                    logging.info(f"CACHE: Procesando folio {folio_cache}, comentario: {comentario_cache}, almacen_id: {almacen_id_cache}")
                    
                    # Guardar TODOS los productos con diferencia != 0
                    productos_cache = []
                    for r in results:
                        dif = r.get('Diferencia_Cantidad', 0)
                        if dif != 0:
                            productos_cache.append({
                                'codigo': r.get('Codigo', ''),
                                'producto': r.get('Producto', ''),
                                'diferencia_cantidad': round(dif, 2),
                                'diferencia_costo': round(r.get('Diferencia_Costo', 0), 2)
                            })
                    
                    logging.info(f"CACHE: {len(productos_cache)} productos con diferencia para folio {folio_cache}")
                    
                    if productos_cache:
                        cache_key = {
                            "server_id": server_id,
                            "almacen_id": almacen_id_cache,
                            "sucursal_id": sucursal_codigo or "",
                            "comentario": comentario_cache or "",
                            "folio": folio_cache
                        }
                        
                        cache_doc = {
                            **cache_key,
                            "fecha_inventario": fecha_cache,
                            "fecha_cache": datetime.now(timezone.utc).isoformat(),
                            "productos": productos_cache
                        }
                        
                        await db.inventario_diferencias_detalle.update_one(
                            cache_key,
                            {"$set": cache_doc},
                            upsert=True
                        )
                        logging.info(f"CACHE: ✅ Guardado folio {folio_cache} ({comentario_cache}): {len(productos_cache)} productos")
                    else:
                        logging.info(f"CACHE: ⚠️ Folio {folio_cache} sin productos con diferencia, no se guarda")
            except Exception as cache_error:
                logging.error(f"CACHE ERROR: {str(cache_error)}")
                import traceback
                logging.error(traceback.format_exc())
            # ===== FIN CACHE =====
            
            # ===== ORQUESTACIÓN FASE 2A: Crear workflow automático si hay diferencias =====
            try:
                from modules.fase2_operativo.services.orquestador_service import get_orquestador_service
                
                # Determinar folio_inventario principal (el folio final más relevante)
                folio_inventario_principal = lista_folios_fin[0] if lista_folios_fin else None
                
                orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase
                orq_resultado = await orquestador.procesar_analisis(
                    server_id=server_id,
                    server_name=server.get('name', ''),
                    sucursal_id=sucursal or "",
                    sucursal_nombre=sucursal or "",
                    almacen_id=almacen or "",
                    almacen_nombre=almacen or "",
                    resultados_analisis=results,
                    folios_iniciales=lista_folios_ini,
                    folios_finales=lista_folios_fin,
                    fecha_ini=fecha_ini or "",
                    fecha_fin=fecha_fin or "",
                    usuario_ejecutor_id=current_user.get('id', ''),
                    usuario_ejecutor_nombre=current_user.get('name', ''),
                    folio_inventario=folio_inventario_principal  # NUEVO: Pasar folio explícito
                )
                
                if orq_resultado.get('workflow_creado'):
                    logging.info(f"ORQUESTADOR: ✅ Workflow {orq_resultado.get('workflow_id')} creado automáticamente")
                else:
                    logging.info(f"ORQUESTADOR: {orq_resultado.get('mensaje', 'Sin acción')}")
                    
            except Exception as orq_error:
                # NO romper el flujo principal si falla la orquestación
                logging.error(f"ORQUESTADOR ERROR (no crítico): {str(orq_error)}")
                import traceback
                logging.error(traceback.format_exc())
            # ===== FIN ORQUESTACIÓN =====
            
            return {"data": results, "count": len(results), "errores_captura": errores_list}
            
        elif is_softrestaurant_system(server.get('system_type')):
            # Análisis de inventario para SoftRestaurant
            logging.info(f"Generando análisis de inventario SoftRestaurant: {almacen}")
            logging.info(f"Folios iniciales: {lista_folios_ini}, finales: {lista_folios_fin}")
            logging.info(f"Filtros frontend - Categorias: {filtro_categorias_frontend}, Familias: {filtro_familias_frontend}, SubFamilias: {filtro_subfamilias_frontend}")
            
            # Generar cadenas SQL para folios múltiples
            folios_ini_sql_sr = ",".join([str(f) for f in lista_folios_ini]) if lista_folios_ini else "0"
            folios_fin_sql_sr = ",".join([str(f) for f in lista_folios_fin]) if lista_folios_fin else "0"
            all_folios_sql = f"{folios_ini_sql_sr},{folios_fin_sql_sr}"
            
            # Obtener fechas de los folios de inventario
            fechas_query = f"""
SELECT folio, fecha
FROM invfisico
WHERE folio IN ({all_folios_sql})
ORDER BY folio
"""
            fechas_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], fechas_query
            )
            
            # Extraer fechas con hora completa (usar primera y última)
            fecha_ini = None
            fecha_fin = None
            folios_ini_set = set(str(f) for f in lista_folios_ini)
            folios_fin_set = set(str(f) for f in lista_folios_fin)
            for row in fechas_result:
                folio_str = str(row['folio'])
                fecha_str = str(row['fecha'])[:19].replace('T', ' ')  # Normalizar formato
                if folio_str in folios_ini_set:
                    if not fecha_ini or fecha_str < fecha_ini:
                        fecha_ini = fecha_str
                elif folio_str in folios_fin_set:
                    if not fecha_fin or fecha_str > fecha_fin:
                        fecha_fin = fecha_str
            
            if not fecha_ini or not fecha_fin:
                logging.warning(f"No se encontraron fechas para los folios {lista_folios_ini} y {lista_folios_fin}")
                fecha_ini = fecha_ini or "2000-01-01 00:00:00"
                fecha_fin = fecha_fin or "2099-12-31 23:59:59"
            
            logging.info(f"Fechas de inventarios: ini={fecha_ini}, fin={fecha_fin}")
            
            # Ajustar fechas: +1 segundo al inicio, -1 segundo al final
            # para no incluir el momento exacto del inventario
            try:
                from datetime import datetime, timedelta
                dt_ini = datetime.strptime(fecha_ini, "%Y-%m-%d %H:%M:%S")
                dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d %H:%M:%S")
                
                logging.info(f"Fechas ANTES de verificación: ini={dt_ini}, fin={dt_fin}")
                
                # IMPORTANTE: Si las fechas están invertidas, intercambiarlas
                # Esto pasa cuando el usuario selecciona el inventario inicial con fecha más reciente
                if dt_ini > dt_fin:
                    logging.info(f"Fechas invertidas detectadas. Intercambiando...")
                    dt_ini, dt_fin = dt_fin, dt_ini
                    logging.info(f"Fechas DESPUÉS de intercambio: ini={dt_ini}, fin={dt_fin}")
                else:
                    logging.info(f"Fechas en orden correcto (ini <= fin)")
                
                dt_ini = dt_ini + timedelta(seconds=1)
                dt_fin = dt_fin - timedelta(seconds=1)
                fecha_ini = dt_ini.strftime("%Y-%m-%d %H:%M:%S")
                fecha_fin = dt_fin.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logging.warning(f"Error ajustando fechas: {e}")
            
            logging.info(f"Fechas calculadas de inventarios (con hora): {fecha_ini} a {fecha_fin}")
            
            # 1. Obtener información del almacén incluyendo el TIPO
            # TIPO = 1: Almacén de consumo (tiene ventas)
            # TIPO = 2: Almacén de presentaciones (NO tiene ventas)
            # FASE 1B: Escapar caracteres especiales de LIKE
            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
            almacen_query = f"""
SELECT TOP 1 
    idalmacen as codigo,
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
WHERE nombre LIKE '%{almacen_safe}%'
"""
            almacen_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], almacen_query
            )
            if not almacen_result:
                logging.error(f"Almacén '{almacen}' no encontrado en servidor {server.get('name', server_id)} ({server['host']})")
                raise HTTPException(status_code=404, detail=f"Almacén '{almacen}' no encontrado. Verifique la conexión al servidor SQL o que el almacén exista en la base de datos.")
            
            almacen_id = almacen_result[0]['codigo']
            almacen_nombre = almacen_result[0]['nombre']
            almacen_tipo = almacen_result[0]['tipo']
            
            # Determinar si el almacén tiene ventas
            es_almacen_consumo = (almacen_tipo == 1)
            logging.info(f"Almacén: {almacen_nombre}, ID: {almacen_id}, Tipo: {almacen_tipo}, Es Consumo (tiene ventas): {es_almacen_consumo}")
            
            # Construir filtros SQL para SoftRestaurant
            # Categoría = clasificacionventa (1=ALIMENTOS, 2=BEBIDAS, 3=OTROS) en tabla gruposiclasificacion
            # Familia = idgruposiclasificacion en tabla gruposiclasificacion
            # SubFamilia = idgruposi en tabla gruposi
            
            # Construir valores SQL para los filtros
            cats_sql = ",".join([f"'{c}'" for c in filtro_categorias_frontend]) if filtro_categorias_frontend else ""
            fams_sql = ",".join([f"'{f}'" for f in filtro_familias_frontend]) if filtro_familias_frontend else ""
            sfs_sql = ",".join([f"'{s}'" for s in filtro_subfamilias_frontend]) if filtro_subfamilias_frontend else ""
            
            # Filtros para INSUMOS (usa GC para gruposiclasificacion, GS para gruposi)
            filtro_categoria_insumos = f"AND GC.clasificacionventa IN ({cats_sql})" if cats_sql else ""
            filtro_familia_insumos = f"AND GC.idgruposiclasificacion IN ({fams_sql})" if fams_sql else ""
            filtro_subfamilia_insumos = f"AND GS.idgruposi IN ({sfs_sql})" if sfs_sql else ""
            
            # Filtros para PRESENTACIONES (usa GC para gruposiclasificacion, GP para gruposi)
            filtro_categoria_pres = f"AND GC.clasificacionventa IN ({cats_sql})" if cats_sql else ""
            filtro_familia_pres = f"AND GC.idgruposiclasificacion IN ({fams_sql})" if fams_sql else ""
            filtro_subfamilia_pres = f"AND GP.idgruposi IN ({sfs_sql})" if sfs_sql else ""
            
            logging.info(f"Filtros construidos - Categorias: {cats_sql}, Familias: {fams_sql}, SubFamilias: {sfs_sql}")
            
            # 2. Obtener productos (catálogo) según el tipo de almacén
            # - Almacén CONSUMO (tipo 1): Usa INSUMOS (tabla insumos)
            # - Almacén BODEGA/PRESENTACIONES (tipo 2): Usa PRESENTACIONES (tabla insumospresentaciones)
            
            if es_almacen_consumo:
                # ALMACÉN DE CONSUMO: Solo INSUMOS
                logging.info("Obteniendo catálogo de productos: INSUMOS (almacén de consumo)")
                
                productos_query = f"""
SELECT 
    'INSUMO' as TABLA,
    GC.descripcion as CATEGORIA,
    GS.descripcion as GRUPO,
    RTRIM(LTRIM(insumos.idinsumo)) as CODIGO,
    insumos.descripcion as DESCRIPCION,
    insumos.unidad as UM,
    1 as RENDIMIENTO,
    IDET.costo as COSTO
FROM insumos
INNER JOIN insumosdetalle IDET ON IDET.idinsumo = insumos.idinsumo
INNER JOIN gruposi GS ON GS.idgruposi = insumos.idgruposi
INNER JOIN gruposiclasificacion GC ON GC.idgruposiclasificacion = GS.idgruposiclasificacion
WHERE LEFT(insumos.descripcion, 3) <> 'zzz'
  AND IDET.inventariable = 1
  {filtro_categoria_insumos}
  {filtro_familia_insumos}
  {filtro_subfamilia_insumos}
"""
            else:
                # ALMACÉN DE BODEGA/PRESENTACIONES: Solo PRESENTACIONES
                logging.info("Obteniendo catálogo de productos: PRESENTACIONES (almacén de bodega)")
                
                productos_query = f"""
SELECT 
    'PRESENTACION' as TABLA,
    GC.descripcion as CATEGORIA,
    GP.descripcion as GRUPO,
    RTRIM(LTRIM(INPRE.idinsumospresentaciones)) as CODIGO,
    INPRE.descripcion as DESCRIPCION,
    INSUMOS.unidad as UM,
    ISNULL(INPRE.rendimiento, 0) as RENDIMIENTO,
    INPRED.costo as COSTO
FROM insumospresentaciones INPRE
INNER JOIN gruposi GP ON GP.idgruposi = INPRE.idgruposi
INNER JOIN insumospresentacionesdetalle INPRED ON INPRED.idinsumospresentaciones = INPRE.idinsumospresentaciones
INNER JOIN insumos INSUMOS ON INSUMOS.idinsumo = INPRE.idinsumo
INNER JOIN insumosdetalle IDET_PRES ON IDET_PRES.idinsumo = INPRE.idinsumo
INNER JOIN gruposiclasificacion GC ON GC.idgruposiclasificacion = GP.idgruposiclasificacion
WHERE LEFT(INPRE.descripcion, 3) <> 'zzz'
  AND IDET_PRES.inventariable = 1
  {filtro_categoria_pres}
  {filtro_familia_pres}
  {filtro_subfamilia_pres}
"""
            
            productos_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], productos_query
            )
            # Crear diccionario de productos por código
            productos_dict = {p['CODIGO']: p for p in productos_result}
            logging.info(f"Productos en catálogo: {len(productos_dict)}")
            
            # DEBUG: Mostrar códigos de presentaciones para verificar
            codigos_130009 = [c for c in productos_dict.keys() if '130009' in str(c)]
            if codigos_130009:
                logging.info(f"DEBUG Códigos con 130009 en CATALOGO: {codigos_130009}")
            
            # 3. Obtener inventarios (inicial y final) de invfisicomovtos
            # La consulta maneja AMBOS tipos: si idinsumo='' usa idpresentacion, sino usa idinsumo
            logging.info(f"Obteniendo inventarios de folios {folio_inicial} y {folio_final}")
            
            inventarios_query = f"""
SELECT 
    FMOV.folio,
    CASE WHEN RTRIM(ISNULL(FMOV.idinsumo,'')) = '' THEN 'PRESENTACION' ELSE 'INSUMO' END as TIPO,
    CASE 
        WHEN RTRIM(ISNULL(FMOV.idinsumo,'')) = '' 
        THEN RTRIM(LTRIM(FMOV.idpresentacion))
        ELSE RTRIM(LTRIM(FMOV.idinsumo))
    END as CODIGO,
    FMOV.costo,
    FMOV.fisicoalmacen1 as EXISTENCIA,
    CASE WHEN RTRIM(ISNULL(FMOV.idinsumo,'')) = '' THEN ISNULL(IP.rendimiento, 1) ELSE 1 END as RENDIMIENTO,
    CASE WHEN RTRIM(ISNULL(FMOV.idinsumo,'')) = '' THEN I_PRES.unidad ELSE I_INS.unidad END as UNIDAD
FROM invfisicomovtos FMOV
INNER JOIN invfisico FISICO ON FISICO.folio = FMOV.folio
INNER JOIN almacen AL ON AL.idalmacen = FISICO.idalmacen1
-- JOINs para PRESENTACIONES (cuando idinsumo está vacío)
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = FMOV.idpresentacion
LEFT JOIN gruposi GP_PRES ON GP_PRES.idgruposi = IP.idgruposi
LEFT JOIN gruposiclasificacion GC_PRES ON GC_PRES.idgruposiclasificacion = GP_PRES.idgruposiclasificacion
LEFT JOIN insumos I_PRES ON I_PRES.idinsumo = IP.idinsumo
-- JOINs para INSUMOS (cuando idinsumo NO está vacío)
LEFT JOIN insumos I_INS ON I_INS.idinsumo = FMOV.idinsumo
LEFT JOIN gruposi GP_INS ON GP_INS.idgruposi = I_INS.idgruposi
LEFT JOIN gruposiclasificacion GC_INS ON GC_INS.idgruposiclasificacion = GP_INS.idgruposiclasificacion
WHERE FMOV.folio IN ({all_folios_sql})
  AND AL.nombre LIKE '%{almacen_safe}%'
ORDER BY FMOV.folio, CODIGO
"""
            
            inventarios_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], inventarios_query
            )
            
            # Separar inventarios inicial y final - SOLO productos con existencia != 0
            inv_inicial_dict = {}
            inv_final_dict = {}
            for inv in inventarios_result:
                codigo = inv['CODIGO']
                existencia = float(inv['EXISTENCIA'] or 0)
                
                # Solo incluir si tiene existencia != 0
                if existencia == 0:
                    continue
                
                folio_str = str(inv['folio'])
                
                # Acumular inventarios iniciales
                if folio_str in folios_ini_set:
                    if codigo not in inv_inicial_dict:
                        inv_inicial_dict[codigo] = {
                            'existencia': 0,
                            'costo': float(inv['costo'] or 0),
                            'tipo': inv['TIPO']
                        }
                    inv_inicial_dict[codigo]['existencia'] += existencia
                # Acumular inventarios finales
                elif folio_str in folios_fin_set:
                    if codigo not in inv_final_dict:
                        inv_final_dict[codigo] = {
                            'existencia': 0,
                            'costo': float(inv['costo'] or 0),
                            'tipo': inv['TIPO']
                        }
                    inv_final_dict[codigo]['existencia'] += existencia
            
            logging.info(f"Inventario inicial: {len(inv_inicial_dict)} productos, Final: {len(inv_final_dict)} productos")
            
            # DEBUG: Mostrar códigos de inventarios para verificar
            inv_130009 = [c for c in inv_inicial_dict.keys() if '130009' in str(c)]
            if inv_130009:
                logging.info(f"DEBUG Códigos con 130009 en INVENTARIOS: {inv_130009}")
            
            # 4. Obtener TODOS los códigos que aparecen en inventarios (inicial o final)
            todos_codigos = set(inv_inicial_dict.keys()) | set(inv_final_dict.keys())
            logging.info(f"Total códigos únicos en inventarios: {len(todos_codigos)}")
            
            # 5. Obtener movimientos - UNION de movsinv (INSUMOS) + movtosalmacen (PRESENTACIONES)
            # Usar los tipos de movimiento configurados en el servidor
            # Formato de fecha: YYYYMMDD HH:MM:SS (sin guiones, con espacio)
            fecha_ini_fmt = fecha_ini.replace('-', '').replace('T', ' ') if fecha_ini else ''
            fecha_fin_fmt = fecha_fin.replace('-', '').replace('T', ' ') if fecha_fin else ''
            logging.info(f"DEBUG fechas originales: fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
            logging.info(f"Obteniendo movimientos entre {fecha_ini_fmt} y {fecha_fin_fmt} para almacén {almacen_nombre}")
            
            # Obtener tipos de movimiento configurados en el servidor
            tipos_movimiento = server.get('tipos_movimiento', [])
            
            # CORRECCIÓN: Excluir tipos de VENTA de la columna MOVIMIENTOS
            # Las ventas (SPV, SCP, SCS) se muestran en la columna VENTAS por separado
            tipos_venta = ['SPV', 'SCP', 'SCS']
            
            if tipos_movimiento:
                # Filtrar tipos de movimiento EXCLUYENDO los de venta
                tipos_mov_sin_ventas = [t for t in tipos_movimiento if t not in tipos_venta]
                if tipos_mov_sin_ventas:
                    conceptos_filter = ", ".join([f"'{t}'" for t in tipos_mov_sin_ventas])
                    filtro_conceptos_insumos = f"AND movsinv.idconcepto IN ({conceptos_filter})"
                    filtro_conceptos_presentaciones = f"AND movtosalmacen.idconcepto IN ({conceptos_filter})"
                else:
                    # Si solo hay tipos de venta, no hay movimientos (evitar query vacía)
                    filtro_conceptos_insumos = "AND 1=0"  # No devuelve nada
                    filtro_conceptos_presentaciones = "AND 1=0"
                logging.info(f"Tipos de movimiento configurados: {tipos_movimiento}")
                logging.info(f"Tipos de movimiento para columna MOVIMIENTOS (sin ventas): {tipos_mov_sin_ventas}")
            else:
                # Si no hay configuración, excluir vacíos Y tipos de venta
                filtro_conceptos_insumos = f"AND movsinv.idconcepto NOT IN ('', 'SPV', 'SCP', 'SCS')"
                filtro_conceptos_presentaciones = f"AND movtosalmacen.idconcepto NOT IN ('', 'SPV', 'SCP', 'SCS')"
                logging.info("No hay tipos de movimiento configurados, usando todos excepto vacíos y ventas")
            
            movimientos_query = f"""
-- MOVIMIENTOS DE INSUMOS (movsinv) - usar código natural (ya incluye prefijo)
SELECT 
    RTRIM(LTRIM(movsinv.idinsumo)) as CODIGO,
    SUM(movsinv.cantidad) as CANTIDAD
FROM movsinv
INNER JOIN insumos ON insumos.idinsumo = movsinv.idinsumo
INNER JOIN gruposi GP ON GP.idgruposi = insumos.idgruposi
INNER JOIN gruposiclasificacion ON gruposiclasificacion.idgruposiclasificacion = GP.idgruposiclasificacion
LEFT JOIN almacen ON almacen.idalmacen = movsinv.idalmacen
WHERE movsinv.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
  AND almacen.nombre LIKE '%{almacen_safe}%'
  {filtro_conceptos_insumos}
GROUP BY RTRIM(LTRIM(movsinv.idinsumo))

UNION ALL

-- MOVIMIENTOS DE PRESENTACIONES (movtosalmacen)
SELECT 
    RTRIM(LTRIM(movtosalmacen.idinsumospresentaciones)) as CODIGO,
    SUM(movtosalmacen.cantidad) as CANTIDAD
FROM movtosalmacen
INNER JOIN insumospresentaciones ON insumospresentaciones.idinsumospresentaciones = movtosalmacen.idinsumospresentaciones
INNER JOIN gruposi ON gruposi.idgruposi = insumospresentaciones.idgruposi
INNER JOIN gruposiclasificacion ON gruposiclasificacion.idgruposiclasificacion = gruposi.idgruposiclasificacion
LEFT JOIN almacen ON almacen.idalmacen = movtosalmacen.idalmacen
WHERE movtosalmacen.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
  AND almacen.nombre LIKE '%{almacen_safe}%'
  {filtro_conceptos_presentaciones}
GROUP BY RTRIM(LTRIM(movtosalmacen.idinsumospresentaciones))
"""
            
            try:
                movimientos_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], movimientos_query
                )
                movimientos_dict = {m['CODIGO']: float(m['CANTIDAD'] or 0) for m in movimientos_result}
                logging.info(f"Movimientos obtenidos para {len(movimientos_dict)} productos")
                # DEBUG: Mostrar el valor de B130009
                if 'B130009' in movimientos_dict:
                    logging.info(f"DEBUG B130009 movimientos: {movimientos_dict['B130009']}")
            except Exception as e:
                logging.warning(f"Error al obtener movimientos: {str(e)}, continuando con movimientos = 0")
                movimientos_dict = {}
            
            # 6. Obtener ventas SOLO si es almacén de consumo (tipo = 1)
            # Consulta basada en recetasalmacenes + costos + turnos
            ventas_dict = {}
            if es_almacen_consumo:
                logging.info("Obteniendo ventas (almacén de CONSUMO tipo=1)...")
                
                # Calcular fechas para ventas:
                # - fecha_ini: Día del inventario inicial a las 00:00:00
                # - fecha_fin: Día ANTERIOR al inventario final a las 23:59:59
                # Esto asegura incluir TODOS los turnos del período correcto
                try:
                    from datetime import datetime, timedelta
                    dt_ini = datetime.strptime(fecha_ini, "%Y-%m-%d %H:%M:%S")
                    dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d %H:%M:%S")
                    
                    # Fecha inicio: inicio del día del inventario inicial
                    fecha_ini_ventas = dt_ini.replace(hour=0, minute=0, second=0)
                    
                    # Fecha fin: final del día ANTERIOR al inventario final (23:59:59)
                    fecha_fin_ventas = (dt_fin - timedelta(days=1)).replace(hour=23, minute=59, second=59)
                    
                    fecha_ini_sql = fecha_ini_ventas.strftime("%d/%m/%Y %H:%M:%S")
                    fecha_fin_sql = fecha_fin_ventas.strftime("%d/%m/%Y %H:%M:%S")
                except Exception as e:
                    logging.warning(f"Error calculando fechas de ventas: {e}")
                    fecha_ini_sql = fecha_ini
                    fecha_fin_sql = fecha_fin
                
                logging.info(f"Fechas para ventas: ini={fecha_ini_sql}, fin={fecha_fin_sql}")
                
                # Ventas de INSUMOS - usando código natural (ya incluye prefijo)
                # El filtro usa el día del inventario inicial hasta el final del día anterior al inventario final
                ventas_insumos_query = f"""
SELECT 
    RTRIM(LTRIM(receta.idinsumo)) as CODIGO,
    SUM(venta.cantidad * COSTOS.cantidad) as CONSUMIDO
FROM cheqdet venta
INNER JOIN cheques ON venta.foliodet = cheques.folio 
INNER JOIN costos ON costos.idproducto = venta.idproducto
INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
    AND RC.idinsumo = COSTOS.idinsumo 
    AND cheques.idarearestaurant = RC.idarearestaurant 
    AND cheques.idempresa = RC.idempresa
INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
INNER JOIN insumos receta ON receta.idinsumo = costos.idinsumo
INNER JOIN gruposi Grupo ON Grupo.idgruposi = receta.idgruposi
INNER JOIN gruposiclasificacion GP ON GP.idgruposiclasificacion = Grupo.idgruposiclasificacion
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.APERTURA BETWEEN CONVERT(datetime, CONVERT(nvarchar(30),'{fecha_ini_sql}',103),103) 
                          AND CONVERT(datetime, CONVERT(nvarchar(30),'{fecha_fin_sql}',103),103)
  AND cheques.cancelado = 0
  AND AL.nombre LIKE '%{almacen_safe}%'
GROUP BY RTRIM(LTRIM(receta.idinsumo))
"""
                try:
                    logging.info(f"Ejecutando consulta ventas INSUMOS para almacén {almacen}")
                    ventas_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], ventas_insumos_query
                    )
                    # Sumar las ventas por código
                    for v in ventas_result:
                        if v['CODIGO']:
                            codigo = v['CODIGO']
                            cantidad = float(v['CONSUMIDO'] or 0)
                            ventas_dict[codigo] = ventas_dict.get(codigo, 0) + cantidad
                    logging.info(f"Ventas cheques cerrados: {len(ventas_result)} registros, {len(ventas_dict)} productos únicos")
                except Exception as e:
                    logging.warning(f"Error al obtener ventas de cheques cerrados: {str(e)}")
                
                # Intentar obtener ventas de tablas temporales (cuentas no cerradas)
                # Estas tablas pueden no existir en todas las instalaciones de SoftRestaurant
                ventas_temp_query = f"""
SELECT 
    RTRIM(LTRIM(receta.idinsumo)) as CODIGO,
    SUM(venta.cantidad * COSTOS.cantidad) as CONSUMIDO
FROM temcheqdet venta
INNER JOIN temcheques cheques ON venta.foliodet = cheques.folio 
INNER JOIN costos ON costos.idproducto = venta.idproducto
INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
    AND RC.idinsumo = COSTOS.idinsumo 
    AND cheques.idarearestaurant = RC.idarearestaurant 
    AND cheques.idempresa = RC.idempresa
INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
INNER JOIN insumos receta ON receta.idinsumo = costos.idinsumo
INNER JOIN gruposi Grupo ON Grupo.idgruposi = receta.idgruposi
INNER JOIN gruposiclasificacion GP ON GP.idgruposiclasificacion = Grupo.idgruposiclasificacion
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.APERTURA BETWEEN CONVERT(datetime, CONVERT(nvarchar(30),'{fecha_ini_sql}',103),103) 
                          AND CONVERT(datetime, CONVERT(nvarchar(30),'{fecha_fin_sql}',103),103)
  AND cheques.cancelado = 0
  AND AL.nombre LIKE '%{almacen_safe}%'
GROUP BY RTRIM(LTRIM(receta.idinsumo))
"""
                try:
                    logging.info("Intentando obtener ventas de cuentas temporales (temcheques/temcheqdet)...")
                    ventas_temp_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], ventas_temp_query
                    )
                    for v in ventas_temp_result:
                        if v['CODIGO']:
                            codigo = v['CODIGO']
                            cantidad = float(v['CONSUMIDO'] or 0)
                            ventas_dict[codigo] = ventas_dict.get(codigo, 0) + cantidad
                    logging.info(f"Ventas temporales: {len(ventas_temp_result)} registros adicionales")
                except Exception as e:
                    # Es normal que falle si las tablas temporales no existen
                    logging.info(f"Tablas temporales no disponibles (esto es normal): {str(e)[:100]}")
                
                # NOTA: La tabla recetasalmacenes solo tiene idinsumo, no tiene idinsumospresentaciones
                # Por lo tanto, las ventas de PRESENTACIONES no se pueden calcular de la misma manera
                # Las presentaciones se descuentan del inventario a través de los INSUMOS que las componen
                logging.info("Ventas de PRESENTACIONES no disponibles - recetasalmacenes solo tiene idinsumo")
                
                logging.info(f"Total ventas obtenidas: {len(ventas_dict)} productos")
            else:
                logging.info(f"Almacén tipo {almacen_tipo} (NO es consumo) - ventas = 0 para todos los productos")
            
            # 7. Combinar resultados - Solo productos que aparecen en inventarios Y están en el catálogo
            # El catálogo ya está filtrado por inventariable = 1 para insumos
            results = []
            for codigo in todos_codigos:
                # Obtener datos del catálogo de productos
                prod_info = productos_dict.get(codigo, None)
                
                # FILTRO IMPORTANTE: Solo incluir productos que están en el catálogo (inventariables)
                if prod_info is None:
                    continue
                
                # Obtener datos de inventarios
                inv_ini = inv_inicial_dict.get(codigo, {'existencia': 0, 'costo': 0, 'tipo': ''})
                inv_fin = inv_final_dict.get(codigo, {'existencia': 0, 'costo': 0, 'tipo': ''})
                
                inv_inicial = inv_ini['existencia']
                inv_final = inv_fin['existencia']
                
                # El costo viene del inventario o del catálogo
                costo = inv_ini['costo'] or inv_fin['costo'] or float(prod_info.get('COSTO', 0) or 0)
                
                # Movimientos y ventas
                movimientos = movimientos_dict.get(codigo, 0)
                ventas_total = ventas_dict.get(codigo, 0)
                
                # Cálculos
                inv_teorico = inv_inicial + movimientos - ventas_total
                diferencia_cantidad = inv_final - inv_teorico
                diferencia_costo = diferencia_cantidad * costo
                diferencia_porcentaje = (diferencia_cantidad / inv_teorico * 100) if inv_teorico != 0 else 0
                valor_real = (inv_inicial + movimientos - inv_final) * costo
                teorico_ventas = ventas_total * costo
                
                # Tipo del producto (INSUMO o PRESENTACION)
                tipo_producto = inv_ini.get('tipo') or inv_fin.get('tipo') or prod_info.get('TABLA', '')
                
                # Construir strings de folios para SoftRestaurant
                # Para Soft, el "comentario" es el nombre del almacén
                folios_ini_str = ', '.join([str(f) for f in lista_folios_ini])
                folios_fin_str = ', '.join([str(f) for f in lista_folios_fin])
                almacen_nombre_soft = almacen or ''  # El almacén viene como nombre en SoftRestaurant
                
                results.append({
                    'ID_Inv_Ini': folios_ini_str,
                    'Comentario_Ini': almacen_nombre_soft,
                    'ID_Inv_Fin': folios_fin_str,
                    'Comentario_Fin': almacen_nombre_soft,
                    'Categoria': prod_info.get('CATEGORIA', 'Sin Categoría'),
                    'Familia': prod_info.get('GRUPO', 'Sin Familia'),
                    'SubFamilia': tipo_producto,  # Mostrar si es INSUMO o PRESENTACION
                    'Codigo': codigo,
                    'Producto': prod_info.get('DESCRIPCION', f'Producto {codigo}'),
                    'Unidad': prod_info.get('UM', 'PZA'),
                    'Costo_Unitario': round(costo, 4),
                    'Inv_Inicial_Cantidad': round(inv_inicial, 4),
                    'Inv_Inicial_Costo': round(inv_inicial * costo, 2),
                    'Movimientos': round(movimientos, 4),
                    'Movimientos_Costo': round(movimientos * costo, 2),
                    'Ventas': round(ventas_total, 4),
                    'Ventas_Costo': round(ventas_total * costo, 2),
                    'Inv_Teorico_Cantidad': round(inv_teorico, 4),
                    'Inv_Teorico_Costo': round(inv_teorico * costo, 2),
                    'Inv_Final_Cantidad': round(inv_final, 4),
                    'Inv_Final_Costo': round(inv_final * costo, 2),
                    'Diferencia_Cantidad': round(diferencia_cantidad, 4),
                    'Diferencia_Costo': round(diferencia_costo, 2),
                    'Diferencia_Porcentaje': round(diferencia_porcentaje, 2),
                    'Valor_Real': round(valor_real, 2),
                    'Teorico': round(teorico_ventas, 2)
                })
            
            # Ordenar por Categoría, Familia, Código
            results.sort(key=lambda x: (x['Categoria'] or '', x['Familia'] or '', x['Codigo'] or ''))
            
            logging.info(f"Reporte SoftRestaurant generado: {len(results)} productos")
            
            # ===== GUARDAR DIFERENCIAS EN CACHE PARA COMPARATIVO DE 4 CORTES (SR) =====
            try:
                # Para SR, guardar por cada folio final
                for folio_fin in lista_folios_fin:
                    productos_cache = []
                    for r in results:
                        dif = r.get('Diferencia_Cantidad', 0)
                        if dif != 0:
                            productos_cache.append({
                                'codigo': r.get('Codigo', ''),
                                'producto': r.get('Producto', ''),
                                'diferencia_cantidad': round(dif, 2),
                                'diferencia_costo': round(r.get('Diferencia_Costo', 0), 2)
                            })
                    
                    if productos_cache:
                        # Obtener info del almacén - manejar tanto strings como diccionarios
                        almacen_id_sr = ""
                        for alm in almacenes:
                            if isinstance(alm, dict):
                                if alm.get('nombre') == almacen or alm.get('id'):
                                    almacen_id_sr = alm.get('id', '')
                                    break
                            elif isinstance(alm, str):
                                # Si es string, usar directamente
                                if alm == almacen:
                                    almacen_id_sr = alm
                                    break
                        
                        # Convertir folio a string (puede venir como Decimal de SQL Server)
                        folio_str = str(int(folio_fin)) if isinstance(folio_fin, (int, float)) else str(folio_fin)
                        
                        cache_key = {
                            "server_id": server_id,
                            "almacen_id": almacen_id_sr or almacen,
                            "sucursal_id": "",
                            "comentario": "",  # SR no usa comentarios
                            "folio": folio_str
                        }
                        
                        cache_doc = {
                            **cache_key,
                            "fecha_inventario": fecha_fin or "",
                            "fecha_cache": datetime.now(timezone.utc).isoformat(),
                            "productos": productos_cache
                        }
                        
                        await db.inventario_diferencias_detalle.update_one(
                            cache_key,
                            {"$set": cache_doc},
                            upsert=True
                        )
                        logging.info(f"Cache SR guardado para folio {folio_fin}: {len(productos_cache)} productos con diferencia")
            except Exception as cache_error:
                logging.warning(f"Error guardando cache SR: {str(cache_error)}")
            # ===== FIN CACHE SR =====
            
            # ===== ORQUESTACIÓN FASE 2A: Crear workflow automático si hay diferencias (SR) =====
            try:
                from modules.fase2_operativo.services.orquestador_service import get_orquestador_service
                
                # Determinar folio_inventario principal para SR
                folio_inventario_principal = lista_folios_fin[0] if lista_folios_fin else None
                
                orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase
                orq_resultado = await orquestador.procesar_analisis(
                    server_id=server_id,
                    server_name=server.get('name', ''),
                    sucursal_id=sucursal or "",
                    sucursal_nombre=sucursal or "",
                    almacen_id=almacen or "",
                    almacen_nombre=almacen or "",
                    resultados_analisis=results,
                    folios_iniciales=lista_folios_ini,
                    folios_finales=lista_folios_fin,
                    fecha_ini=fecha_ini or "",
                    fecha_fin=fecha_fin or "",
                    usuario_ejecutor_id=current_user.get('id', ''),
                    usuario_ejecutor_nombre=current_user.get('name', ''),
                    folio_inventario=folio_inventario_principal  # NUEVO: Pasar folio explícito
                )
                
                if orq_resultado.get('workflow_creado'):
                    logging.info(f"ORQUESTADOR SR: ✅ Workflow {orq_resultado.get('workflow_id')} creado automáticamente")
                else:
                    logging.info(f"ORQUESTADOR SR: {orq_resultado.get('mensaje', 'Sin acción')}")
                    
            except Exception as orq_error:
                # NO romper el flujo principal si falla la orquestación
                logging.error(f"ORQUESTADOR SR ERROR (no crítico): {str(orq_error)}")
                import traceback
                logging.error(traceback.format_exc())
            # ===== FIN ORQUESTACIÓN SR =====
            
            return {"data": results, "count": len(results)}
        
        else:
            raise HTTPException(status_code=400, detail="Sistema no soportado para análisis completo")
        
    except Exception as e:
        logging.error(f"Error en análisis de inventario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando análisis: {str(e)}")


# CAB-003 Fase 1A: Asignar referencia para uso desde Core Service
_inventory_analysis_endpoint_ref = generate_inventory_analysis


@api_router.post("/reports/movement-details")
async def get_movement_details(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el detalle de los movimientos para un producto específico.
    Devuelve: folio, fecha, cantidad, tipo de movimiento, descripción.
    
    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    server_id = params.get('server_id')
    producto_codigo = params.get('producto_codigo')
    sucursal = params.get('sucursal')
    almacen = params.get('almacen')
    fecha_ini = params.get('fecha_ini')
    fecha_fin = params.get('fecha_fin')
    
    # FASE P1.4-C: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if is_mpro_system(server.get('system_type')):
            # MPRO: Movimientos desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
            from datetime import datetime, timedelta
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ini_mov = (fecha_ini_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # FASE 1C: Sanitizar entradas LIKE
            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
            sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
            
            # Obtener código del almacén
            almacen_query = f"""
SELECT TOP 1 A.Al_Cve_Almacen as codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE A.Al_Descripcion LIKE '%{almacen_safe}%'
    AND S.Sc_Descripcion LIKE '%{sucursal_safe}%'
"""
            almacen_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], almacen_query
            )
            if not almacen_result:
                raise HTTPException(status_code=404, detail="Almacén no encontrado")
            almacen_codigo = almacen_result[0]['codigo']
            
            # Obtener filtros de tipos de movimiento configurados
            tipos_movimiento = server.get('tipos_movimiento', [])
            if tipos_movimiento:
                tipos_mov_sql = ",".join([f"'{t}'" for t in tipos_movimiento])
                filtro_tipos_mov = f"AND M.Tm_Cve_Tipo_Movimiento IN ({tipos_mov_sql})"
            else:
                filtro_tipos_mov = ""
            
            # Consulta detalle de movimientos - CON LÓGICA ESPECIAL DE FECHAS PARA TIPOS 508/108
            # La fecha real de los movimientos tipo 508/108 se calcula de Conversion_Producto/Compra
            query = f"""
SELECT 
    M.Mv_Folio as Folio,
    CASE   
        WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
        THEN 
            CASE WHEN M.Mv_Tabla = 'CONVERSION_PRODUCTO' THEN M.Mv_Fecha 
            ELSE ISNULL((
                SELECT TOP 1 C.Co_Fecha FROM Conversion_Producto CN
                INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
                WHERE CN.Cp_Folio = M.Mv_Documento
            ), M.Mv_Fecha)
            END
        ELSE M.Mv_Fecha
    END as Fecha,
    M.Mv_Cantidad_Control_1 as Cantidad,
    M.Tm_Cve_Tipo_Movimiento as Tipo_Codigo,
    TM.Tm_Descripcion as Tipo_Descripcion,
    TM.Tm_Tipo as Tipo_Movimiento,
    P.Pr_Descripcion as Producto,
    A.Al_Descripcion as Almacen,
    M.Mv_Documento as Documento
FROM Movimiento M
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
INNER JOIN Producto P ON P.Pr_Cve_Producto = M.Pr_Cve_Producto
INNER JOIN Almacen A ON A.Al_Cve_Almacen = M.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE M.Pr_Cve_Producto = '{producto_codigo}'
    AND S.Sc_Descripcion LIKE '%{sucursal_safe}%'
    AND M.Al_Cve_Almacen = '{almacen_codigo}'
    AND M.Es_Cve_Estado <> 'CA'
    {filtro_tipos_mov}
    AND (
        CASE   
            WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
            THEN 
                CASE WHEN M.Mv_Tabla = 'CONVERSION_PRODUCTO' THEN M.Mv_Fecha 
                ELSE ISNULL((
                    SELECT TOP 1 C.Co_Fecha FROM Conversion_Producto CN
                    INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
                    WHERE CN.Cp_Folio = M.Mv_Documento
                ), M.Mv_Fecha)
                END
            ELSE M.Mv_Fecha
        END
    ) BETWEEN '{fecha_ini_mov}' AND '{fecha_fin} 23:59:59'
ORDER BY Fecha DESC
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            # Formatear resultados
            movements = []
            for row in result:
                # Usar Tipo_Movimiento de la BD (E=Entrada, S=Salida)
                tipo_bd = row.get('Tipo_Movimiento', '')
                if tipo_bd == 'E':
                    tipo_texto = 'Entrada'
                elif tipo_bd == 'S':
                    tipo_texto = 'Salida'
                else:
                    # Fallback por signo
                    cantidad = float(row.get('Cantidad') or 0)
                    tipo_texto = 'Entrada' if cantidad >= 0 else 'Salida'
                # Formatear fecha sin la "T" (2026-03-21T00:00:00 -> 2026-03-21 00:00:00)
                fecha_str = str(row.get('Fecha'))[:19].replace('T', ' ') if row.get('Fecha') else ''
                movements.append({
                    'folio': row.get('Folio'),
                    'fecha': fecha_str,
                    'cantidad': float(row.get('Cantidad') or 0),
                    'tipo_codigo': row.get('Tipo_Codigo'),
                    'tipo_descripcion': row.get('Tipo_Descripcion'),
                    'tipo_movimiento': tipo_texto,
                    'producto': row.get('Producto'),
                    'almacen': row.get('Almacen'),
                    'observaciones': ''
                })
            
            return {"data": movements, "count": len(movements)}
            
        elif is_softrestaurant_system(server.get('system_type')):
            # Para SoftRestaurant - detectar si es INSUMO o PRESENTACIÓN
            # PRESENTACIONES: el idinsumospresentaciones ya tiene el código completo (ej: B130009)
            # INSUMOS: el código se genera como prefijo + idinsumo (ej: B + 12345 = B12345)
            
            # FASE 1C: Sanitizar entradas LIKE
            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
            
            # Formatear fechas para SQL Server: YYYYMMDD HH:MM:SS
            # Si solo viene fecha (YYYY-MM-DD), agregar hora inicio/fin
            fecha_ini_fmt = fecha_ini.replace('-', '').replace('T', ' ') if fecha_ini else ''
            fecha_fin_fmt = fecha_fin.replace('-', '').replace('T', ' ') if fecha_fin else ''
            
            # Asegurar que tengan hora
            if fecha_ini_fmt and ' ' not in fecha_ini_fmt:
                fecha_ini_fmt = f"{fecha_ini_fmt} 00:00:00"
            if fecha_fin_fmt and ' ' not in fecha_fin_fmt:
                fecha_fin_fmt = f"{fecha_fin_fmt} 23:59:59"
            
            logging.info(f"Detalle movimientos SoftRestaurant - Código: {producto_codigo}, Almacén: {almacen}, Fechas: {fecha_ini_fmt} a {fecha_fin_fmt}")
            
            # Primero intentar buscar en PRESENTACIONES (movtosalmacen)
            query_presentaciones = f"""
SELECT 
    COALESCE(CAST(M.idcompra AS VARCHAR(50)), CAST(M.traspaso AS VARCHAR(50)), CAST(M.invfisico AS VARCHAR(50)), '') as Folio,
    M.fecha as Fecha,
    M.cantidad as Cantidad,
    M.idconcepto as Tipo_Codigo,
    C.descripcion as Tipo_Descripcion,
    CASE WHEN C.tipo = 1 THEN 'Entrada' ELSE 'Salida' END as Tipo_Movimiento,
    IP.descripcion as Producto,
    A.nombre as Almacen,
    M.costo as Costo
FROM movtosalmacen M
INNER JOIN conceptos C ON C.idconcepto = M.idconcepto
INNER JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = M.idinsumospresentaciones
LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
WHERE RTRIM(LTRIM(M.idinsumospresentaciones)) = '{producto_codigo}'
    AND A.nombre LIKE '%{almacen_safe}%'
    AND M.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
    AND M.idconcepto <> ''
ORDER BY M.fecha DESC
"""
            logging.info(f"Query detalle movimientos PRESENTACIONES: {query_presentaciones[:300]}...")
            
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_presentaciones
            )
            
            # Si no hay resultados en presentaciones, buscar en INSUMOS
            if not result:
                # El código ya es el idinsumo completo (incluyendo el prefijo, ej: B130001)
                # No necesitamos quitar ningún carácter
                logging.info(f"No encontrado en presentaciones, buscando en INSUMOS con ID: {producto_codigo}")
                
                query_insumos = f"""
SELECT 
    COALESCE(CAST(M.foliocheque AS VARCHAR(50)), CAST(M.idcompra AS VARCHAR(50)), CAST(M.traspaso AS VARCHAR(50)), CAST(M.invfisico AS VARCHAR(50)), '') as Folio,
    M.fecha as Fecha,
    M.cantidad as Cantidad,
    M.idconcepto as Tipo_Codigo,
    C.descripcion as Tipo_Descripcion,
    CASE WHEN C.tipo = 1 THEN 'Entrada' ELSE 'Salida' END as Tipo_Movimiento,
    I.descripcion as Producto,
    A.nombre as Almacen,
    M.costo as Costo
FROM movsinv M
INNER JOIN conceptos C ON C.idconcepto = M.idconcepto
INNER JOIN insumos I ON I.idinsumo = M.idinsumo
LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
WHERE RTRIM(LTRIM(M.idinsumo)) = '{producto_codigo}'
    AND A.nombre LIKE '%{almacen_safe}%'
    AND M.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
    AND M.idconcepto <> ''
ORDER BY M.fecha DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_insumos
                )
            
            logging.info(f"Movimientos encontrados: {len(result)}")
            
            movements = []
            for row in result:
                # Usar el campo Tipo_Movimiento de la BD (viene del query SQL)
                tipo_movimiento = row.get('Tipo_Movimiento', '')
                if not tipo_movimiento:
                    # Fallback: Si no viene de BD, inferir por el signo
                    cantidad = float(row.get('Cantidad') or 0)
                    tipo_movimiento = 'Entrada' if cantidad >= 0 else 'Salida'
                movements.append({
                    'folio': row.get('Folio') or '',
                    'fecha': str(row.get('Fecha'))[:19] if row.get('Fecha') else '',
                    'cantidad': float(row.get('Cantidad') or 0),
                    'tipo_codigo': row.get('Tipo_Codigo'),
                    'tipo_descripcion': row.get('Tipo_Descripcion'),
                    'tipo_movimiento': tipo_movimiento,
                    'producto': row.get('Producto'),
                    'almacen': row.get('Almacen'),
                    'observaciones': f"Costo: ${row.get('Costo', 0):.2f}" if row.get('Costo') else ''
                })
            
            return {"data": movements, "count": len(movements)}
        else:
            return {"data": [], "count": 0}
            
    except Exception as e:
        logging.error(f"Error obteniendo detalle de movimientos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.post("/reports/sales-details")
async def get_sales_details(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el detalle de las ventas para un producto específico.
    Devuelve: folio, fecha, cantidad, tipo de venta (directa/kit).
    
    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    server_id = params.get('server_id')
    producto_codigo = params.get('producto_codigo')
    sucursal = params.get('sucursal')
    fecha_ini = params.get('fecha_ini')
    fecha_fin = params.get('fecha_fin')
    
    # FASE P1.4-C: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if is_mpro_system(server.get('system_type')):
            # FASE 1C: Sanitizar entradas LIKE
            sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
            
            # Consulta detalle de ventas - combina ventas directas y de kits
            query = f"""
SELECT * FROM (
    -- Ventas de productos KIT
    SELECT 
        V.Vn_Folio as Folio,
        V.Vn_Fecha as Fecha,
        (V.Vn_Cantidad_1 * PK.Pk_Cantidad) as Cantidad,
        'KIT' as Tipo_Venta,
        PV.Pr_Descripcion as Producto_Vendido,
        P.Pr_Descripcion as Producto,
        V.Vn_Precio_Lista as Precio_Unitario,
        S.Sc_Descripcion as Sucursal
    FROM venta V
    INNER JOIN producto_kit PK ON PK.Pr_Cve_Producto = V.Pr_Cve_Producto
    INNER JOIN producto P ON P.Pr_Cve_Producto = PK.Pk_Producto
    INNER JOIN producto PV ON PV.Pr_Cve_Producto = V.Pr_Cve_Producto
    INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
    WHERE PK.Pk_Producto = '{producto_codigo}'
        AND S.Sc_Descripcion LIKE '%{sucursal_safe}%'
        AND V.Es_Cve_Estado <> 'CA'
        AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    
    UNION ALL
    
    -- Ventas DIRECTAS
    SELECT 
        V.Vn_Folio as Folio,
        V.Vn_Fecha as Fecha,
        V.Vn_Cantidad_Control_1 as Cantidad,
        'DIRECTA' as Tipo_Venta,
        P.Pr_Descripcion as Producto_Vendido,
        P.Pr_Descripcion as Producto,
        V.Vn_Precio_Lista as Precio_Unitario,
        S.Sc_Descripcion as Sucursal
    FROM venta V
    INNER JOIN producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
    INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
    WHERE V.Pr_Cve_Producto = '{producto_codigo}'
        AND S.Sc_Descripcion LIKE '%{sucursal_safe}%'
        AND V.Es_Cve_Estado <> 'CA'
        AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
) AS VentasDetalle
ORDER BY Fecha DESC
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            sales = []
            for row in result:
                sales.append({
                    'folio': row.get('Folio'),
                    'fecha': str(row.get('Fecha'))[:19] if row.get('Fecha') else '',
                    'cantidad': float(row.get('Cantidad') or 0),
                    'tipo_venta': row.get('Tipo_Venta'),
                    'producto_vendido': row.get('Producto_Vendido'),
                    'producto': row.get('Producto'),
                    'precio_unitario': float(row.get('Precio_Unitario') or 0),
                    'sucursal': row.get('Sucursal')
                })
            
            return {"data": sales, "count": len(sales)}
            
        elif is_softrestaurant_system(server.get('system_type')):
            # Para SoftRestaurant - detalle de ventas usando recetasalmacenes
            # El código puede ser INSUMO (con prefijo) o PRESENTACION (código directo)
            almacen = params.get('almacen', '')
            
            # FASE 1C: Sanitizar entradas LIKE
            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
            
            # Formatear fechas para SQL Server: YYYYMMDD HH:MM:SS
            fecha_ini_fmt = fecha_ini.replace('-', '').replace('T', ' ') if fecha_ini else ''
            fecha_fin_fmt = fecha_fin.replace('-', '').replace('T', ' ') if fecha_fin else ''
            
            # Asegurar que tengan hora
            if fecha_ini_fmt and ' ' not in fecha_ini_fmt:
                fecha_ini_fmt = f"{fecha_ini_fmt} 00:00:00"
            if fecha_fin_fmt and ' ' not in fecha_fin_fmt:
                fecha_fin_fmt = f"{fecha_fin_fmt} 23:59:59"
            
            logging.info(f"Detalle ventas SoftRestaurant - Código: {producto_codigo}, Almacén: {almacen}, Fechas: {fecha_ini_fmt} a {fecha_fin_fmt}")
            
            # La tabla recetasalmacenes solo tiene idinsumo, no tiene idinsumospresentaciones
            # Por lo tanto, buscamos directamente por el código de INSUMO (que ya incluye el prefijo)
            query_insumos = f"""
SELECT 
    cheques.folio as Folio,
    turnos.APERTURA as Fecha,
    venta.cantidad * COSTOS.cantidad as Cantidad,
    'RECETA' as Tipo_Venta,
    productos.descripcion as Producto_Vendido,
    receta.descripcion as Producto,
    venta.precio as Precio_Unitario,
    AL.nombre as Almacen
FROM cheqdet venta
INNER JOIN cheques ON venta.foliodet = cheques.folio 
INNER JOIN costos ON costos.idproducto = venta.idproducto
INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
    AND RC.idinsumo = COSTOS.idinsumo 
    AND cheques.idarearestaurant = RC.idarearestaurant 
    AND cheques.idempresa = RC.idempresa
INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
INNER JOIN insumos receta ON receta.idinsumo = costos.idinsumo
INNER JOIN productos ON productos.idproducto = venta.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE RTRIM(LTRIM(receta.idinsumo)) = '{producto_codigo}'
  AND turnos.APERTURA BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
  AND cheques.cancelado = 0
  AND AL.nombre LIKE '%{almacen_safe}%'
ORDER BY turnos.APERTURA DESC
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_insumos
            )
            
            logging.info(f"Ventas encontradas: {len(result)}")
            
            sales = []
            for row in result:
                sales.append({
                    'folio': row.get('Folio'),
                    'fecha': str(row.get('Fecha'))[:19] if row.get('Fecha') else '',
                    'cantidad': float(row.get('Cantidad') or 0),
                    'tipo_venta': row.get('Tipo_Venta'),
                    'producto_vendido': row.get('Producto_Vendido'),
                    'producto': row.get('Producto'),
                    'precio_unitario': float(row.get('Precio_Unitario') or 0),
                    'sucursal': row.get('Almacen', '')
                })
            
            return {"data": sales, "count": len(sales)}
        else:
            return {"data": [], "count": 0}
            
    except Exception as e:
        logging.error(f"Error obteniendo detalle de ventas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.post("/reports/export/excel")
async def export_excel(data: Dict, current_user: Dict = Depends(get_current_user)):
    report_data = data.get('data', [])
    filename = data.get('filename', 'reporte_inventario.xlsx')
    
    # Metadatos para el encabezado del reporte
    metadata = {
        'servidor_nombre': data.get('servidor_nombre', 'N/A'),
        'sucursal': data.get('sucursal', 'N/A'),
        'almacen': data.get('almacen', 'N/A'),
        'fecha_inicio': data.get('fecha_inicio', 'N/A'),
        'fecha_fin': data.get('fecha_fin', 'N/A')
    }
    
    excel_bytes = generate_excel(report_data, filename, metadata)
    
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.post("/reports/export/pdf")
async def export_pdf(data: Dict, current_user: Dict = Depends(get_current_user)):
    report_data = data.get('data', [])
    filename = data.get('filename', 'reporte_inventario.pdf')
    
    pdf_bytes = generate_pdf(report_data, filename)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============= REPORTE COMPARATIVO DE 4 ÚLTIMOS INVENTARIOS (AUDITORÍA) =============
class AlmacenComparativo(BaseModel):
    id: str
    nombre: str = ""
    comentario: Optional[str] = None  # Para MPRO

class ComparativoInventariosRequest(BaseModel):
    server_id: str
    sucursal_id: Optional[str] = None
    sucursal_nombre: str = ""
    # Soporta múltiples almacenes (multi-selección)
    almacenes: List[AlmacenComparativo]
    fecha_referencia: str
    categorias: Optional[List[str]] = None
    # Para compatibilidad con versión anterior (single almacén)
    almacen_id: Optional[str] = None
    almacen_nombre: Optional[str] = ""
    comentario: Optional[str] = None


async def get_diferencias_from_cache(
    server: Dict,
    almacen_id: str,
    almacen_nombre: str,
    sucursal_id: Optional[str],
    comentario: Optional[str],
    fecha_referencia: str
) -> Optional[Dict]:
    """
    Lee las diferencias del cache inventario_diferencias_detalle.
    Este cache se llena cuando el usuario genera el reporte normal de "Generar Reporte".
    Retorna los últimos 4 cortes con sus diferencias.
    """
    try:
        logging.info(f"get_diferencias_from_cache: almacen_id={almacen_id}, sucursal_id={sucursal_id}, comentario={comentario}, fecha_ref={fecha_referencia}")
        
        # 1. Obtener los últimos 4 folios de inventario para este almacén/comentario
        if is_mpro_system(server.get('system_type')):
            sucursal_filtro = f"AND F.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
            comentario_filtro = f"AND F.Fi_Comentario = '{comentario.replace(chr(39), chr(39)+chr(39))}'" if comentario else ""
            
            logging.info(f"Filtros: sucursal_filtro=[{sucursal_filtro}], comentario_filtro=[{comentario_filtro}]")
            
            # Asegurar formato de fecha correcto para SQL Server
            # Formato: YYYY-MM-DD o YYYYMMDD
            fecha_ref_clean = fecha_referencia.replace('T', ' ')[:10] if fecha_referencia else '2099-12-31'
            
            query_cortes = f"""
            SELECT TOP 4 
                F.Fi_Folio as folio,
                CONVERT(varchar, F.Fi_Fecha, 120) as fecha,
                A.Al_Descripcion as almacen,
                ISNULL(F.Fi_Comentario, '') as comentario
            FROM Fisico F
            INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
            WHERE A.Al_Cve_Almacen = '{almacen_id}'
                {sucursal_filtro}
                {comentario_filtro}
                AND CONVERT(date, F.Fi_Fecha) <= CONVERT(date, '{fecha_ref_clean}')
            GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, F.Fi_Comentario
            ORDER BY F.Fi_Fecha DESC
            """
            
            logging.info(f"Query SQL para cortes (fecha_ref={fecha_ref_clean}): folios TOP 4...")
        else:  # SoftRestaurant
            # Asegurar formato de fecha correcto para SQL Server
            fecha_ref_clean_sr = fecha_referencia.replace('T', ' ')[:10] if fecha_referencia else '2099-12-31'
            
            query_cortes = f"""
            SELECT TOP 4 
                INV.folio as folio,
                CONVERT(varchar, INV.fecha, 120) as fecha,
                A.nombre as almacen,
                '' as comentario
            FROM invfisico INV
            INNER JOIN almacen A ON A.idalmacen = INV.idalmacen1
            WHERE INV.idalmacen1 = '{almacen_id}'
                AND CONVERT(date, INV.fecha) <= CONVERT(date, '{fecha_ref_clean_sr}')
            GROUP BY INV.folio, INV.fecha, A.nombre
            ORDER BY INV.fecha DESC
            """
        
        cortes_result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_cortes
        )
        
        if not cortes_result:
            logging.warning(f"No se encontraron inventarios para almacén {almacen_id}/{comentario}")
            return None
        
        logging.info(f"Encontrados {len(cortes_result)} cortes para {almacen_id}/{comentario}: {[c['folio'] for c in cortes_result]}")
        
        # 2. Buscar cada folio en el cache de diferencias
        productos_dict = {}
        cortes_con_cache = []
        cortes_sin_cache = []
        
        for idx, corte in enumerate(cortes_result):
            folio_raw = corte['folio']
            # Convertir folio a string (puede venir como Decimal de SQL Server)
            folio = str(int(folio_raw)) if isinstance(folio_raw, (int, float)) or (hasattr(folio_raw, '__float__')) else str(folio_raw)
            
            # Buscar en cache
            cache_key = {
                "server_id": server['id'],
                "folio": folio
            }
            
            cached = await db.inventario_diferencias_detalle.find_one(cache_key, {"_id": 0})
            
            if cached and cached.get('productos'):
                cortes_con_cache.append(folio)
                for prod in cached['productos']:
                    codigo = prod['codigo']
                    if codigo not in productos_dict:
                        productos_dict[codigo] = {
                            'codigo': codigo,
                            'producto': prod.get('producto', ''),
                            'diferencias': [None] * len(cortes_result)
                        }
                    productos_dict[codigo]['diferencias'][idx] = prod.get('diferencia_cantidad', 0)
            else:
                cortes_sin_cache.append(folio)
        
        logging.info(f"Cache HIT: {len(cortes_con_cache)}, Cache MISS: {len(cortes_sin_cache)}")
        
        if cortes_sin_cache:
            logging.warning(f"Folios sin cache (genera el reporte normal primero): {cortes_sin_cache}")
        
        # Aunque no haya productos, retornar el resultado con cortes_sin_cache
        # para que el endpoint pueda mostrar un mensaje descriptivo
        if not productos_dict:
            return {
                'almacen_nombre': almacen_nombre,
                'cortes': [{'folio': c['folio'], 'fecha': c['fecha'], 'comentario': c.get('comentario', '')} for c in cortes_result],
                'productos': [],
                'cortes_sin_cache': cortes_sin_cache
            }
        
        # 3. Calcular totales y patrones
        for codigo, data in productos_dict.items():
            diferencias = data['diferencias']
            difs_validas = [d for d in diferencias if d is not None and d != 0]
            data['total_diferencia'] = round(sum(difs_validas), 2) if difs_validas else 0
            
            # Detectar patrón
            if len(difs_validas) >= 2:
                todos_negativos = all(d < 0 for d in difs_validas if d != 0)
                todos_positivos = all(d > 0 for d in difs_validas if d != 0)
                if todos_negativos:
                    data['patron'] = 'FALTANTE CONSTANTE'
                elif todos_positivos:
                    data['patron'] = 'SOBRANTE CONSTANTE'
                else:
                    data['patron'] = ''
            else:
                data['patron'] = ''
        
        # 4. Filtrar productos sin diferencias
        productos_list = [p for p in productos_dict.values() if any(d is not None and d != 0 for d in p.get('diferencias', []))]
        
        # Siempre retornar el resultado, incluso si productos está vacío
        # El endpoint debe manejar el caso de cortes_sin_cache
        # Convertir folios a string para evitar problemas con Decimal
        def folio_to_str(f):
            return str(int(f)) if isinstance(f, (int, float)) or hasattr(f, '__float__') else str(f)
        
        return {
            'almacen_nombre': almacen_nombre,
            'cortes': [{'folio': folio_to_str(c['folio']), 'fecha': c['fecha'], 'comentario': c.get('comentario', '')} for c in cortes_result],
            'productos': productos_list,
            'cortes_sin_cache': [folio_to_str(f) for f in cortes_sin_cache]
        }
        
    except Exception as e:
        logging.error(f"Error leyendo cache de diferencias: {str(e)}")
        return None



def generate_excel_comparativo_inventarios(data: List[Dict], metadata: Dict) -> bytes:
    """
    Genera Excel comparativo de los últimos 4 cortes de inventario.
    Columnas: Código | Producto | Dif Corte 1 | Dif Corte 2 | Dif Corte 3 | Dif Corte 4 | Total
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from datetime import datetime
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparativo 4 Cortes"
    
    if not data:
        ws.cell(row=1, column=1, value="No hay datos para mostrar")
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    # Estilos
    titulo_font = Font(size=14, bold=True, color="18181b")
    header_fill = PatternFill(start_color="18181b", end_color="18181b", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=10)
    label_font = Font(bold=True, size=10)
    value_font = Font(size=10)
    verde_fill = PatternFill(start_color="22c55e", end_color="22c55e", fill_type="solid")
    rojo_fill = PatternFill(start_color="ef4444", end_color="ef4444", fill_type="solid")
    amarillo_fill = PatternFill(start_color="fbbf24", end_color="fbbf24", fill_type="solid")
    gris_fill = PatternFill(start_color="e4e4e7", end_color="e4e4e7", fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='d4d4d8'),
        right=Side(style='thin', color='d4d4d8'),
        top=Side(style='thin', color='d4d4d8'),
        bottom=Side(style='thin', color='d4d4d8')
    )
    
    row_num = 1
    
    # Título
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=8)
    ws.cell(row=row_num, column=1, value="REPORTE COMPARATIVO DE AUDITORÍA - 4 ÚLTIMOS INVENTARIOS").font = titulo_font
    ws.cell(row=row_num, column=1).alignment = Alignment(horizontal="center")
    row_num += 2
    
    # Metadatos
    info_data = [
        ("Servidor:", metadata.get('servidor_nombre', 'N/A')),
        ("Sucursal:", metadata.get('sucursal_nombre', 'N/A')),
        ("Almacén:", metadata.get('almacen_nombre', 'N/A')),
        ("Comentario/Tipo:", metadata.get('comentario', 'N/A')),
        ("Fecha de Elaboración:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    ]
    
    for label, value in info_data:
        ws.cell(row=row_num, column=1, value=label).font = label_font
        ws.cell(row=row_num, column=2, value=value).font = value_font
        row_num += 1
    
    row_num += 1
    
    # Fechas de los cortes
    cortes = metadata.get('cortes', [])
    ws.cell(row=row_num, column=1, value="FECHAS DE CORTES:").font = label_font
    row_num += 1
    for i, corte in enumerate(cortes, 1):
        ws.cell(row=row_num, column=1, value=f"Corte {i}:").font = label_font
        ws.cell(row=row_num, column=2, value=f"{corte.get('fecha', 'N/A')} (Folio: {corte.get('folio', 'N/A')})").font = value_font
        row_num += 1
    
    row_num += 1
    
    # Headers dinámicos
    headers = ['Código', 'Producto']
    for i, corte in enumerate(cortes, 1):
        fecha_corta = corte.get('fecha', '')[:10] if corte.get('fecha') else f'Corte {i}'
        headers.append(f'Dif {fecha_corta}')
    headers.append('TOTAL DIF')
    headers.append('PATRÓN')
    
    header_row = row_num
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=row_num, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    
    row_num += 1
    
    # Datos ordenados por Total (de mayor faltante a mayor sobrante)
    data_sorted = sorted(data, key=lambda x: float(x.get('total_diferencia', 0) or 0))
    
    for row_data in data_sorted:
        # Código
        cell = ws.cell(row=row_num, column=1, value=row_data.get('codigo', ''))
        cell.border = thin_border
        
        # Producto
        cell = ws.cell(row=row_num, column=2, value=row_data.get('producto', ''))
        cell.border = thin_border
        
        # Diferencias por corte
        diferencias = row_data.get('diferencias', [])
        for i, dif in enumerate(diferencias):
            col = 3 + i
            cell = ws.cell(row=row_num, column=col, value=dif if dif is not None else '-')
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="right")
            
            if dif is not None:
                try:
                    num_val = float(dif)
                    if num_val < 0:
                        cell.fill = rojo_fill
                        cell.font = Font(bold=True, color="FFFFFF")
                    elif num_val > 0:
                        cell.fill = verde_fill
                        cell.font = Font(bold=True, color="FFFFFF")
                except (ValueError, TypeError):
                    pass
        
        # Rellenar columnas faltantes si hay menos de 4 cortes
        for i in range(len(diferencias), 4):
            col = 3 + i
            cell = ws.cell(row=row_num, column=col, value='-')
            cell.border = thin_border
            cell.fill = gris_fill
        
        # Total
        total = row_data.get('total_diferencia', 0)
        col_total = 3 + len(cortes)
        cell = ws.cell(row=row_num, column=col_total, value=total)
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="right")
        cell.font = Font(bold=True)
        
        if total is not None:
            try:
                num_val = float(total)
                if num_val < 0:
                    cell.fill = rojo_fill
                    cell.font = Font(bold=True, color="FFFFFF")
                elif num_val > 0:
                    cell.fill = verde_fill
                    cell.font = Font(bold=True, color="FFFFFF")
            except (ValueError, TypeError):
                pass
        
        # Patrón (si hay faltante constante)
        patron = row_data.get('patron', '')
        col_patron = col_total + 1
        cell = ws.cell(row=row_num, column=col_patron, value=patron)
        cell.border = thin_border
        if 'CONSTANTE' in patron.upper():
            cell.fill = amarillo_fill
            cell.font = Font(bold=True)
        
        row_num += 1
    
    # Autofiltro
    last_col = get_column_letter(len(headers))
    ws.auto_filter.ref = f"A{header_row}:{last_col}{row_num - 1}"
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 40
    for i in range(3, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 15
    
    # Congelar encabezado
    ws.freeze_panes = f"A{header_row + 1}"
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


@api_router.post("/reports/export/comparativo-inventarios")
async def export_comparativo_inventarios(request: ComparativoInventariosRequest, current_user: Dict = Depends(get_current_user)):
    """
    Genera un Excel comparativo con las diferencias de los últimos 4 cortes de inventario.
    Usa cache en MongoDB para evitar recalcular.
    Soporta múltiples almacenes (multi-selección).
    FASE 8: Aplica validación RBAC de servidor y almacenes.
    
    FASE P1.4-E3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    # FASE 8: Validar acceso y obtener contexto
    context = await resolve_user_access_context(current_user)
    
    if not has_server_access(context, request.server_id):
        logging.warning(f"[RBAC-EXPORT-INV] {current_user.get('email')} sin acceso a servidor {request.server_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    
    # FASE P1.4-E3: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
    
    logging.info(
        f"[RBAC-EXPORT-INV] Usuario={current_user.get('email')}, "
        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    try:
        # Construir lista de almacenes a procesar
        almacenes_a_procesar = []
        
        # Soportar nuevo formato (lista de almacenes) y formato anterior (single almacén)
        if request.almacenes and len(request.almacenes) > 0:
            almacenes_a_procesar = request.almacenes
        elif request.almacen_id:
            # Compatibilidad con versión anterior
            almacenes_a_procesar = [AlmacenComparativo(
                id=request.almacen_id,
                nombre=request.almacen_nombre or '',
                comentario=request.comentario
            )]
        
        if not almacenes_a_procesar:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un almacén")
        
        # FASE 8: Validar que todos los almacenes solicitados estén en el alcance
        if almacenes_permitidos:
            for almacen in almacenes_a_procesar:
                if almacen.id not in almacenes_permitidos:
                    logging.warning(
                        f"[RBAC-EXPORT-INV-403] Usuario={current_user.get('email')}, "
                        f"Almacén fuera de alcance: {almacen.id}"
                    )
                    raise HTTPException(
                        status_code=403, 
                        detail=f"No tiene acceso al almacén {almacen.nombre or almacen.id}"
                    )
        
        # Procesar cada almacén usando cache
        all_productos = []
        all_cortes = []
        almacenes_procesados = []
        folios_sin_cache = []
        
        for almacen in almacenes_a_procesar:
            cache_result = await get_diferencias_from_cache(
                server=server,
                almacen_id=almacen.id,
                almacen_nombre=almacen.nombre,
                sucursal_id=request.sucursal_id,
                comentario=almacen.comentario,
                fecha_referencia=request.fecha_referencia
            )
            
            if cache_result:
                # Verificar si hay folios sin cache
                if cache_result.get('cortes_sin_cache'):
                    folios_sin_cache.extend(cache_result.get('cortes_sin_cache', []))
                
                # Agregar prefijo de almacén/comentario a los productos si hay múltiples
                productos = cache_result.get('productos', [])
                
                # Solo procesar si hay productos
                if productos:
                    if len(almacenes_a_procesar) > 1:
                        prefijo = f"{almacen.nombre}"
                        if almacen.comentario:
                            prefijo += f" ({almacen.comentario})"
                        for prod in productos:
                            prod['almacen_comentario'] = prefijo
                    
                    all_productos.extend(productos)
                
                # Guardar info de cortes (solo del primer almacén para simplificar)
                if not all_cortes:
                    all_cortes = cache_result.get('cortes', [])
                
                if productos:
                    almacenes_procesados.append({
                        'nombre': almacen.nombre,
                        'comentario': almacen.comentario or '',
                        'productos_count': len(productos)
                    })
        
        if not all_productos:
            # Mensaje más descriptivo si faltan reportes en cache
            logging.info(f"all_productos vacío. folios_sin_cache: {folios_sin_cache}")
            if folios_sin_cache:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No hay datos en cache. Primero genera el reporte normal 'Generar Reporte' para los siguientes folios: {', '.join(folios_sin_cache[:4])}"
                )
            raise HTTPException(status_code=404, detail="No se encontraron diferencias de inventario para los almacenes seleccionados")
        
        # Preparar metadata para el Excel
        if len(almacenes_procesados) == 1:
            almacen_info = almacenes_procesados[0]['nombre']
            comentario_info = almacenes_procesados[0]['comentario'] or 'TODOS'
        else:
            almacen_info = f"{len(almacenes_procesados)} almacenes"
            comentario_info = ', '.join([f"{a['nombre']}({a['comentario']})" if a['comentario'] else a['nombre'] for a in almacenes_procesados])
        
        metadata = {
            'servidor_nombre': server.get('name', 'N/A'),
            'sucursal_nombre': request.sucursal_nombre or 'N/A',
            'almacen_nombre': almacen_info,
            'comentario': comentario_info,
            'cortes': all_cortes,
            'desde_cache': True
        }
        
        # Generar Excel
        excel_bytes = generate_excel_comparativo_inventarios(all_productos, metadata)
        
        # Nombre del archivo
        if len(almacenes_procesados) == 1:
            nombre_archivo = almacenes_procesados[0]['nombre']
            if almacenes_procesados[0]['comentario']:
                nombre_archivo += f"_{almacenes_procesados[0]['comentario']}"
        else:
            nombre_archivo = f"{len(almacenes_procesados)}_almacenes"
        
        filename = f"comparativo_inventarios_{nombre_archivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generando comparativo de inventarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")

@api_router.post("/reports/email")
async def email_report(request: EmailReportRequest, background_tasks: BackgroundTasks, current_user: Dict = Depends(get_current_user)):
    report_data = request.report_data.get('data', [])
    
    if request.format_type == 'excel':
        attachment_data = generate_excel(report_data)
        filename = 'reporte_inventario.xlsx'
    else:
        attachment_data = generate_pdf(report_data)
        filename = 'reporte_inventario.pdf'
    
    body = f"""
    <html>
        <body>
            <h2>Reporte de Inventario</h2>
            <p>Se adjunta el reporte solicitado.</p>
            <p><strong>Total de registros:</strong> {len(report_data)}</p>
        </body>
    </html>
    """
    
    background_tasks.add_task(
        send_email_with_attachment,
        request.recipient_emails,
        request.subject,
        body,
        attachment_data,
        filename
    )
    
    return {"message": "Reporte enviado por correo"}

# ============= ALERTS =============

@api_router.post("/alerts")
async def create_alert(alert_data: AlertCreate, current_user: Dict = Depends(get_current_user)):
    alert = Alert(**alert_data.model_dump())
    doc = alert.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.alerts.insert_one(doc)
    
    return alert.model_dump()

@api_router.get("/alerts", response_model=List[Alert])
async def get_alerts(current_user: Dict = Depends(get_current_user)):
    alerts = await db.alerts.find({"active": True}, {"_id": 0}).to_list(1000)
    return alerts

@api_router.put("/alerts/{alert_id}")
async def update_alert(alert_id: str, alert_data: Dict, current_user: Dict = Depends(get_current_user)):
    await db.alerts.update_one({"id": alert_id}, {"$set": alert_data})
    return {"message": "Alerta actualizada"}

@api_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, current_user: Dict = Depends(get_current_user)):
    await db.alerts.update_one({"id": alert_id}, {"$set": {"active": False}})
    return {"message": "Alerta desactivada"}

# ============= CATÁLOGO DE CONSULTAS =============

@api_router.get("/catalogo/consultas")
async def get_catalogo_consultas(system_type: str = None, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el catálogo completo de consultas disponibles.
    Puede filtrar por tipo de sistema (MPRO o SoftRestaurant).
    """
    result = {}
    
    if system_type is None or is_mpro_system(system_type):
        result["MPRO"] = {
            nombre: {
                "nombre": consulta["nombre"],
                "descripcion": consulta["descripcion"],
                "parametros": consulta["parametros"]
            }
            for nombre, consulta in CONSULTAS_MPRO.items()
        }
    
    if system_type is None or is_softrestaurant_system(system_type):
        result["SoftRestaurant"] = {
            nombre: {
                "nombre": consulta["nombre"],
                "descripcion": consulta["descripcion"],
                "parametros": consulta["parametros"]
            }
            for nombre, consulta in CONSULTAS_SOFTRESTAURANT.items()
        }
    
    return result

@api_router.get("/catalogo/estructura-tablas")
async def get_estructura_tablas(system_type: str = None, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene la estructura de las tablas principales.
    Útil para entender la base de datos y crear consultas personalizadas.
    """
    result = {}
    
    if system_type is None or is_mpro_system(system_type):
        result["MPRO"] = ESTRUCTURA_TABLAS_MPRO
    
    if system_type is None or is_softrestaurant_system(system_type):
        result["SoftRestaurant"] = ESTRUCTURA_TABLAS_SOFTRESTAURANT
    
    return result

@api_router.post("/catalogo/ejecutar-consulta")
async def ejecutar_consulta_catalogo(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Ejecuta una consulta del catálogo en un servidor específico.
    
    Parámetros:
    - server_id: ID del servidor donde ejecutar
    - consulta: Nombre de la consulta del catálogo (ej: "ventas", "productos", "proveedores")
    - parametros: Diccionario con los parámetros requeridos por la consulta
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 3:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    server_id = params.get('server_id')
    consulta_nombre = params.get('consulta')
    parametros = params.get('parametros', {})
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[EJECUTAR_CONSULTA_CATALOGO] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[EJECUTAR_CONSULTA_CATALOGO] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # Obtener consulta del catálogo según el tipo de sistema
    if is_mpro_system(server.get('system_type')):
        consultas = CONSULTAS_MPRO
    elif is_softrestaurant_system(server.get('system_type')):
        consultas = CONSULTAS_SOFTRESTAURANT
    else:
        raise HTTPException(status_code=400, detail="Tipo de sistema no soportado")
    
    if consulta_nombre not in consultas:
        raise HTTPException(status_code=404, detail=f"Consulta '{consulta_nombre}' no encontrada en el catálogo")
    
    consulta = consultas[consulta_nombre]
    
    try:
        # Formatear la consulta con los parámetros
        sql = consulta["sql"].format(**parametros)
        
        logging.info(f"Ejecutando consulta: {consulta_nombre}")
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            sql
        )
        
        return {
            "consulta": consulta_nombre,
            "descripcion": consulta["descripcion"],
            "count": len(results),
            "data": results
        }
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Parámetro requerido faltante: {str(e)}")
    except Exception as e:
        logging.error(f"Error ejecutando consulta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando consulta: {str(e)}")

@api_router.post("/catalogo/consulta-personalizada")
async def ejecutar_consulta_personalizada(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Ejecuta una consulta SQL personalizada en un servidor específico.
    Solo para usuarios administradores.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 5
    
    SEGURIDAD: Mantiene validación de rol Admin/Administrador.
    
    Parámetros:
    - server_id: ID del servidor donde ejecutar
    - sql: Consulta SQL a ejecutar
    """
    user_role = current_user.get('role', '').lower()
    if user_role not in ['admin', 'administrador']:
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar consultas personalizadas")
    
    server_id = params.get('server_id')
    sql = params.get('sql')
    
    if not sql:
        raise HTTPException(status_code=400, detail="SQL es requerido")
    
    # Obtener servidor usando registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    from core.server_registry import get_server_connection_info
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    try:
        logging.info(f"Ejecutando consulta personalizada")
        
        results = execute_sql_query(
            conn_info['host'],
            conn_info['port'],
            conn_info['database'],
            conn_info['username'],
            conn_info['password'],
            sql
        )
        
        return {
            "count": len(results),
            "data": results
        }
        
    except Exception as e:
        logging.error(f"Error ejecutando consulta personalizada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============= DEBUG ENDPOINT =============

@api_router.post("/debug/test-connection")
async def debug_test_connection(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Endpoint de depuración para probar conexiones a servidores SQL directamente.
    Permite probar cadenas de conexión especiales (DDNS, instancias, etc.)
    """
    host = params.get('host')
    port = params.get('port', 1433)
    database = params.get('database')
    username = params.get('username')
    password = params.get('password')
    query = params.get('query', 'SELECT 1 AS test')
    
    if not all([host, database, username, password]):
        raise HTTPException(status_code=400, detail="host, database, username y password son requeridos")
    
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    parsed_info = {
        "hostname": hostname,
        "port": parsed_port,
        "instance": instance,
        "original_host": host
    }
    
    try:
        logging.info(f"DEBUG: Probando conexión a {host}")
        results = execute_sql_query(host, port, database, username, password, query)
        return {
            "success": True,
            "message": f"Conexión exitosa. {len(results)} registros obtenidos.",
            "parsed_info": parsed_info,
            "data": results[:10] if results else []  # Solo primeros 10 registros
        }
    except Exception as e:
        logging.error(f"DEBUG: Error en conexión: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "parsed_info": parsed_info,
            "data": []
        }

# ============= ENDPOINT TEMPORAL: Diagnóstico tipos_movimiento =============
# FASE T3.4-B4 DIAGNÓSTICO - Este endpoint es TEMPORAL y debe eliminarse después
@api_router.get("/debug/tipos-movimiento-live/{server_id}")
async def debug_tipos_movimiento_live(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    TEMPORAL: Obtiene tipos de movimiento con descripción desde BD viva.
    Para diagnóstico de enriquecimiento de datos en EDARSAHUB.
    """
    from core.server_registry import get_server_connection_info
    
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if is_mpro_system(server.get('system_type')):
            query = """
                SELECT 
                    Tm_Cve_Tipo_Movimiento as codigo,
                    Tm_Descripcion as descripcion,
                    Tm_Tipo as tipo
                FROM Tipo_Movimiento
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Tm_Cve_Tipo_Movimiento
            """
        elif is_softrestaurant_system(server.get('system_type')):
            query = """
                SELECT 
                    idconcepto as codigo,
                    descripcion,
                    CASE WHEN tipo = 1 THEN 'EN' ELSE 'SA' END as tipo
                FROM conceptos
                ORDER BY idconcepto
            """
        else:
            return {"error": "Sistema no soportado", "system_type": server.get('system_type')}
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        return {
            "server_name": server.get('name'),
            "system_type": server.get('system_type'),
            "source": "BD_VIVA",
            "total": len(results),
            "tipos": results
        }
    except Exception as e:
        return {
            "server_name": server.get('name'),
            "error": str(e)[:500],
            "source": "BD_VIVA_ERROR"
        }

@api_router.post("/debug/test-queries")
async def debug_test_queries(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Endpoint de depuración simplificado para probar consultas de un producto.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    """
    server_id = params.get('server_id')
    sucursal = params.get('sucursal')
    almacen = params.get('almacen', '')  # Nombre del almacén para filtrar
    fecha_ini = params.get('fecha_ini')
    fecha_fin = params.get('fecha_fin')
    producto_codigo = params.get('producto_codigo', '0000000546')
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
    from core.server_registry import get_server_connection_info
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    results = {"parametros": params}
    
    try:
        # FASE 1C: Sanitizar entradas LIKE
        sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
        almacen_safe = _escape_like_pattern(almacen) if almacen else ""
        
        # Obtener código del almacén si se proporcionó nombre
        almacen_codigo = None
        if almacen:
            almacen_query = f"SELECT TOP 1 Al_Cve_Almacen as codigo FROM Almacen WHERE Al_Descripcion LIKE '%{almacen_safe}%'"
            almacen_result = execute_sql_query(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], almacen_query
            )
            if almacen_result:
                almacen_codigo = almacen_result[0]['codigo']
                results["almacen_codigo"] = almacen_codigo
        
        # Consulta de movimientos CON filtro de almacén si se proporciona
        filtro_almacen = f"AND E.Al_Cve_Almacen = '{almacen_codigo}'" if almacen_codigo else ""
        
        query_mov_simple = f"""
SELECT 
    COUNT(*) as Total_Registros,
    SUM(E.Mv_Cantidad_Control_1) as Movimientos_Neto
FROM Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%'
    AND E.Pr_Cve_Producto = '{producto_codigo}'
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Tm_Cve_Tipo_Movimiento IN ('050','100','106','108','112','202','400','500','506','508','510','512')
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    {filtro_almacen}
"""
        mov_result = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query_mov_simple
        )
        results["movimientos_simple"] = mov_result
        
        # Consulta de ventas combinada - Exacta a la original de Power Query
        # IMPORTANTE: La consulta original NO filtra por categorías/departamentos específicamente
        # sino que suma todas las ventas donde el producto aparece (ya sea como kit o directo)
        query_ventas = f"""
SELECT SUM(cantidad) as Total_Ventas FROM (
    -- Ventas de productos KIT: cuando el producto es componente de otro
    SELECT 
        SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) as cantidad
    FROM venta
    INNER JOIN producto_kit ON Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Descripcion LIKE '%{sucursal_safe}%'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        AND Producto_Kit.Pk_Producto = '{producto_codigo}'
    
    UNION ALL
    
    -- Ventas DIRECTAS: cuando el producto se vende directamente
    SELECT 
        SUM(venta.Vn_Cantidad_Control_1) as cantidad
    FROM venta
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Descripcion LIKE '%{sucursal_safe}%'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        AND venta.Pr_Cve_Producto = '{producto_codigo}'
) AS VentasCombinadas
"""
        ventas_result = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query_ventas
        )
        results["ventas"] = ventas_result
        
        # Detalle de movimientos CON ALMACÉN
        query_detalle = f"""
SELECT TOP 10
    E.Mv_Fecha,
    TM.Tm_Cve_Tipo_Movimiento as Codigo,
    TM.Tm_Descripcion as Movimiento,
    TM.Tm_Tipo,
    E.Mv_Cantidad_Control_1 as Cantidad,
    A.Al_Descripcion as Almacen,
    E.Al_Cve_Almacen as Almacen_Codigo
FROM Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%'
    AND E.Pr_Cve_Producto = '{producto_codigo}'
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Tm_Cve_Tipo_Movimiento IN ('050','100','106','108','112','202','400','500','506','508','510','512')
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY E.Mv_Fecha DESC
"""
        detalle = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query_detalle
        )
        results["detalle_movimientos"] = detalle
        
        # Detalle de ventas Kit
        query_detalle_kit = f"""
SELECT TOP 10 V.Vn_Folio, V.Vn_Fecha, V.Pr_Cve_Producto as Producto_Vendido, 
    PK.Pk_Producto as Producto_Componente, V.Vn_Cantidad_1 as Qty_Venta, 
    PK.Pk_Cantidad as Qty_Kit, V.Vn_Cantidad_1 * PK.Pk_Cantidad as Cantidad_Total
FROM venta V
INNER JOIN producto_kit PK ON PK.Pr_Cve_Producto = V.Pr_Cve_Producto
INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%'
    AND V.Es_Cve_Estado <> 'CA'
    AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    AND PK.Pk_Producto = '{producto_codigo}'
ORDER BY V.Vn_Fecha DESC
"""
        detalle_kit = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query_detalle_kit
        )
        results["detalle_ventas_kit"] = detalle_kit
        
        # Detalle de ventas directas
        query_detalle_directas = f"""
SELECT TOP 10 V.Vn_Folio, V.Vn_Fecha, V.Pr_Cve_Producto, 
    V.Vn_Cantidad_1, V.Vn_Cantidad_Control_1
FROM venta V
INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%'
    AND V.Es_Cve_Estado <> 'CA'
    AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    AND V.Pr_Cve_Producto = '{producto_codigo}'
ORDER BY V.Vn_Fecha DESC
"""
        detalle_directas = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query_detalle_directas
        )
        results["detalle_ventas_directas"] = detalle_directas
        
        return results
        
    except Exception as e:
        logging.error(f"Error en debug: {str(e)}")
        results["error"] = str(e)
        return results

# ============= DASHBOARD =============

def get_dashboard_inventory_query_softrestaurant(departamentos=None, categorias=None):
    """
    Consulta para obtener datos de inventario físico de SoftRestaurant
    para el dashboard con análisis de diferencias.
    Aplica filtros de departamentos (almacenes) y categorías (gruposi).
    Solo incluye productos inventariables.
    """
    # Construir filtros
    filtro_almacen = ""
    if departamentos and len(departamentos) > 0:
        almacenes_sql = ",".join([f"'{d}'" for d in departamentos])
        filtro_almacen = f"AND INV.idalmacen1 IN ({almacenes_sql})"
    
    filtro_categoria = ""
    if categorias and len(categorias) > 0:
        categorias_sql = ",".join([f"'{c}'" for c in categorias])
        filtro_categoria = f"AND COALESCE(IP.idgruposi, I.idgruposi) IN ({categorias_sql})"
    
    return f"""
    WITH InventariosMes AS (
        SELECT 
            idalmacen1 as idalmacen,
            MIN(folio) as primer_folio,
            MAX(folio) as ultimo_folio,
            MIN(fecha) as primera_fecha,
            MAX(fecha) as ultima_fecha
        FROM invfisico
        WHERE cancelado = 0
            AND MONTH(fecha) = MONTH(GETDATE())
            AND YEAR(fecha) = YEAR(GETDATE())
            {filtro_almacen.replace('INV.', '')}
        GROUP BY idalmacen1
    )
    SELECT 
        INV.folio,
        INV.fecha,
        INV.idalmacen1 as idalmacen,
        ALM.nombre as almacen_nombre,
        DET.idpresentacion as codigo,
        COALESCE(IP.descripcion, I.descripcion, DET.idpresentacion) as descripcion,
        COALESCE(GS.descripcion, 'Sin Grupo') as grupo,
        DET.costo as costo_unitario,
        DET.existenciaalmacen1 as existencia_teorica,
        DET.fisicoalmacen1 as existencia_fisica,
        DET.diferenciaalmacen1 as diferencia,
        (DET.diferenciaalmacen1 * DET.costo) as costo_diferencia,
        CASE 
            WHEN INV.folio = IM.primer_folio THEN 'INICIAL'
            WHEN INV.folio = IM.ultimo_folio THEN 'FINAL'
            ELSE 'INTERMEDIO'
        END as tipo_inventario
    FROM invfisico INV
    INNER JOIN invfisicomovtos DET ON DET.folio = INV.folio
    INNER JOIN InventariosMes IM ON IM.idalmacen = INV.idalmacen1 
        AND (INV.folio = IM.primer_folio OR INV.folio = IM.ultimo_folio)
    LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = DET.idpresentacion
    LEFT JOIN insumos I ON I.idinsumo = RTRIM(DET.idinsumo)
    LEFT JOIN gruposi GS ON GS.idgruposi = COALESCE(IP.idgruposi, I.idgruposi)
    LEFT JOIN almacen ALM ON ALM.idalmacen = INV.idalmacen1
    WHERE INV.cancelado = 0
    {filtro_almacen}
    {filtro_categoria}
    ORDER BY INV.idalmacen1, INV.folio, DET.idpresentacion
    """


def get_dashboard_inventory_query_mpro(departamentos=None, categorias=None):
    """
    Consulta para obtener datos de inventario físico de MPRO
    para el dashboard con análisis de diferencias.
    - Inventario inicial = último inventario del mes ANTERIOR
    - Inventario final = último inventario del mes ACTUAL
    """
    # Construir filtros
    filtro_departamento = ""
    if departamentos and len(departamentos) > 0:
        dept_sql = ",".join([f"'{d}'" for d in departamentos])
        filtro_departamento = f"AND P.Dp_Cve_Departamento IN ({dept_sql})"
    
    filtro_categoria = ""
    if categorias and len(categorias) > 0:
        cat_sql = ",".join([f"'{c}'" for c in categorias])
        filtro_categoria = f"AND P.Ct_Cve_Categoria IN ({cat_sql})"
    
    return f"""
    WITH InventarioMesAnterior AS (
        -- Último inventario del mes anterior (INICIAL)
        SELECT 
            Al_Cve_Almacen as almacen,
            MAX(Fi_Folio) as folio_inicial
        FROM Fisico
        WHERE Es_Cve_Estado <> 'CA'
            AND MONTH(Fi_Fecha) = MONTH(DATEADD(MONTH, -1, GETDATE()))
            AND YEAR(Fi_Fecha) = YEAR(DATEADD(MONTH, -1, GETDATE()))
        GROUP BY Al_Cve_Almacen
    ),
    InventarioMesActual AS (
        -- Último inventario del mes actual (FINAL)
        SELECT 
            Al_Cve_Almacen as almacen,
            MAX(Fi_Folio) as folio_final
        FROM Fisico
        WHERE Es_Cve_Estado <> 'CA'
            AND MONTH(Fi_Fecha) = MONTH(GETDATE())
            AND YEAR(Fi_Fecha) = YEAR(GETDATE())
        GROUP BY Al_Cve_Almacen
    )
    SELECT TOP 5000
        F.Fi_Folio as folio,
        F.Fi_Fecha as fecha,
        F.Al_Cve_Almacen as idalmacen,
        A.Al_Descripcion as almacen_nombre,
        F.Pr_Cve_Producto as codigo,
        P.Pr_Descripcion as descripcion,
        COALESCE(C.Ct_Descripcion, 'Sin Categoría') as grupo,
        F.Fi_Costo as costo_unitario,
        F.Fi_Cantidad_1 as existencia_teorica,
        F.Fi_Cantidad_Control_1 as existencia_fisica,
        (F.Fi_Cantidad_Control_1 - F.Fi_Cantidad_1) as diferencia,
        ((F.Fi_Cantidad_Control_1 - F.Fi_Cantidad_1) * F.Fi_Costo) as costo_diferencia,
        CASE 
            WHEN F.Fi_Folio = IMA.folio_inicial THEN 'INICIAL'
            WHEN F.Fi_Folio = IMC.folio_final THEN 'FINAL'
            ELSE 'INTERMEDIO'
        END as tipo_inventario
    FROM Fisico F
    LEFT JOIN InventarioMesAnterior IMA ON IMA.almacen = F.Al_Cve_Almacen
    LEFT JOIN InventarioMesActual IMC ON IMC.almacen = F.Al_Cve_Almacen
    INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen
    INNER JOIN Producto P ON P.Pr_Cve_Producto = F.Pr_Cve_Producto
    LEFT JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
    WHERE F.Es_Cve_Estado <> 'CA'
        AND (F.Fi_Folio = IMA.folio_inicial OR F.Fi_Folio = IMC.folio_final)
    {filtro_departamento}
    {filtro_categoria}
    ORDER BY F.Al_Cve_Almacen, F.Fi_Folio, F.Pr_Cve_Producto
    """


@api_router.get("/dashboard/inventory-summary")
async def get_dashboard_inventory_summary(
    server_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene resumen de inventarios para el dashboard.
    Incluye datos para gráficos de diferencias, top faltantes, etc.
    Aplica los filtros configurados en el servidor (departamentos, categorías).
    
    FASE P1.4-E2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets, list_servers as registry_list_servers
    
    try:
        # FASE P1.4-E2: Obtener servidor desde EDARSAHUB SQL via server_registry
        # ANTES: query = {"active": True, "queries_configured": True}
        # ANTES: if server_id: query["id"] = server_id
        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))
        
        server = None
        if server_id:
            # Servidor específico
            server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
            if server and (not server.get('active', True) or not server.get('queries_configured', False)):
                server = None
        else:
            # Buscar primer servidor configurado con queries
            all_servers = await registry_list_servers(db=db, filter_active=True, mask_secrets=False)
            for s in all_servers:
                if s.get('active', True) and s.get('queries_configured', False):
                    server = decrypt_server_secrets(s)
                    break
        
        if not server:
            return {
                "success": False,
                "message": "No hay servidores configurados con consultas SQL",
                "data": {}
            }
        
        # Obtener filtros configurados
        departamentos = server.get('departamentos', [])
        categorias = server.get('categorias', [])
        
        logging.info(f"Dashboard - Servidor: {server['name']}, Sistema: {server['system_type']}")
        logging.info(f"Filtros - Departamentos: {departamentos}, Categorías: {categorias}")
        
        # Ejecutar consulta según el tipo de sistema con filtros
        if is_softrestaurant_system(server.get('system_type')):
            query_sql = get_dashboard_inventory_query_softrestaurant(departamentos, categorias)
        elif is_mpro_system(server.get('system_type')):
            query_sql = get_dashboard_inventory_query_mpro(departamentos, categorias)
        else:
            return {
                "success": False,
                "message": f"Dashboard no implementado para {server['system_type']}",
                "data": {}
            }
        
        try:
            results = execute_sql_query(
                server['host'],
                server['port'],
                server['database'],
                server['username'],
                server['password'],
                query_sql
            )
        except Exception as query_error:
            logging.error(f"Error en consulta dashboard: {str(query_error)}")
            return {
                "success": False,
                "message": f"Error ejecutando consulta: {str(query_error)[:200]}",
                "data": {
                    "server_name": server['name'],
                    "almacenes": [],
                    "top_faltantes_costo": [],
                    "top_faltantes_cantidad": [],
                    "resumen_por_almacen": [],
                    "resumen_por_grupo": [],
                    "kpis": {}
                }
            }
        
        if not results:
            return {
                "success": True,
                "message": "No hay datos de inventario para el mes actual",
                "data": {
                    "server_name": server['name'],
                    "almacenes": [],
                    "top_faltantes_costo": [],
                    "top_faltantes_cantidad": [],
                    "resumen_por_almacen": [],
                    "resumen_por_grupo": [],
                    "kpis": {}
                }
            }
        
        import pandas as pd
        from decimal import Decimal
        
        # Convertir a DataFrame para análisis
        df = pd.DataFrame(results)
        
        # Convertir Decimal a float
        numeric_cols = ['costo_unitario', 'existencia_teorica', 'existencia_fisica', 'diferencia', 'costo_diferencia']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
        
        # Separar inventarios inicial y final
        df_inicial = df[df['tipo_inventario'] == 'INICIAL'].copy()
        df_final = df[df['tipo_inventario'] == 'FINAL'].copy()
        
        # KPIs generales (basados en inventario final)
        total_diferencia_costo = df_final['costo_diferencia'].sum() if 'costo_diferencia' in df_final.columns else 0
        total_items_con_diferencia = len(df_final[df_final['diferencia'] != 0])
        total_items = len(df_final)
        precision = ((total_items - total_items_con_diferencia) / total_items * 100) if total_items > 0 else 0
        
        # Top 10 faltantes por costo (diferencia negativa = faltante)
        df_faltantes = df_final[df_final['diferencia'] < 0].copy()
        top_faltantes_costo = df_faltantes.nsmallest(10, 'costo_diferencia')[
            ['codigo', 'descripcion', 'almacen_nombre', 'diferencia', 'costo_unitario', 'costo_diferencia']
        ].to_dict('records')
        
        # Top 10 faltantes por cantidad
        top_faltantes_cantidad = df_faltantes.nsmallest(10, 'diferencia')[
            ['codigo', 'descripcion', 'almacen_nombre', 'diferencia', 'costo_unitario', 'costo_diferencia']
        ].to_dict('records')
        
        # Resumen por almacén
        resumen_almacen = df_final.groupby(['idalmacen', 'almacen_nombre']).agg({
            'diferencia': 'sum',
            'costo_diferencia': 'sum',
            'codigo': 'count'
        }).reset_index()
        resumen_almacen.columns = ['idalmacen', 'almacen', 'total_diferencia', 'total_costo_diferencia', 'total_items']
        resumen_almacen = resumen_almacen.to_dict('records')
        
        # Resumen por grupo/categoría
        resumen_grupo = df_final.groupby('grupo').agg({
            'diferencia': 'sum',
            'costo_diferencia': 'sum',
            'codigo': 'count'
        }).reset_index()
        resumen_grupo.columns = ['grupo', 'total_diferencia', 'total_costo_diferencia', 'total_items']
        resumen_grupo = resumen_grupo.nsmallest(15, 'total_costo_diferencia').to_dict('records')
        
        # Comparativo inicial vs final por almacén
        comparativo_almacen = []
        almacenes = df['idalmacen'].unique()
        for alm in almacenes:
            df_alm_ini = df_inicial[df_inicial['idalmacen'] == alm]
            df_alm_fin = df_final[df_final['idalmacen'] == alm]
            
            if len(df_alm_ini) > 0 or len(df_alm_fin) > 0:
                alm_nombre = df_alm_fin['almacen_nombre'].iloc[0] if len(df_alm_fin) > 0 else df_alm_ini['almacen_nombre'].iloc[0]
                comparativo_almacen.append({
                    'almacen': alm,
                    'almacen_nombre': alm_nombre,
                    'diferencia_inicial': float(df_alm_ini['costo_diferencia'].sum()) if len(df_alm_ini) > 0 else 0,
                    'diferencia_final': float(df_alm_fin['costo_diferencia'].sum()) if len(df_alm_fin) > 0 else 0,
                    'items_inicial': len(df_alm_ini),
                    'items_final': len(df_alm_fin),
                    'fecha_inicial': str(df_alm_ini['fecha'].iloc[0]) if len(df_alm_ini) > 0 else None,
                    'fecha_final': str(df_alm_fin['fecha'].iloc[0]) if len(df_alm_fin) > 0 else None
                })
        
        # Obtener lista de almacenes únicos
        almacenes_list = df[['idalmacen', 'almacen_nombre']].drop_duplicates().to_dict('records')
        
        return {
            "success": True,
            "message": "Datos obtenidos correctamente",
            "data": {
                "server_id": server['id'],
                "server_name": server['name'],
                "system_type": server['system_type'],
                "almacenes": almacenes_list,
                "kpis": {
                    "total_diferencia_costo": round(total_diferencia_costo, 2),
                    "total_items_con_diferencia": total_items_con_diferencia,
                    "total_items": total_items,
                    "precision_inventario": round(precision, 2),
                    "total_faltantes": len(df_faltantes),
                    "total_sobrantes": len(df_final[df_final['diferencia'] > 0])
                },
                "top_faltantes_costo": top_faltantes_costo,
                "top_faltantes_cantidad": top_faltantes_cantidad,
                "resumen_por_almacen": resumen_almacen,
                "resumen_por_grupo": resumen_grupo,
                "comparativo_almacen": comparativo_almacen
            }
        }
        
    except Exception as e:
        logging.error(f"Error en dashboard inventory summary: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": {}
        }


@api_router.get("/dashboard/servers-configured")
async def get_dashboard_servers(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene lista de servidores configurados para el selector del dashboard.
    
    Migrado de db.servers.find() a server_registry.list_servers()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 5
    """
    # ANTES: servers = await db.servers.find({"active": True, "queries_configured": True}, {...}).to_list(100)
    from core.server_registry import list_servers
    all_servers = await list_servers(db=db, prefer_sql=True)
    
    # Filtrar solo los activos y con queries configuradas
    servers = []
    for s in all_servers:
        if s.get("active", True) and s.get("queries_configured", False):
            servers.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "system_type": s.get("system_type"),
                "visible_en_operaciones": s.get("visible_en_operaciones", True),
                "config_origin": s.get("config_origin", "Unknown")
            })
    
    return servers


@api_router.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: Dict = Depends(get_current_user)):
    """
    Métricas básicas para el dashboard - mantenido por compatibilidad
    
    FASE P1.4-E4 (Dic 2025): Parcialmente migrado a server_registry.
    NOTA: db.users y db.alerts aún usan MongoDB (fuera del alcance de P1.4-E4).
    """
    from core.server_registry import list_servers as registry_list_servers
    
    # FASE P1.4-E4: Obtener contadores de servidores desde EDARSAHUB SQL
    # ANTES: total_servers = await db.servers.count_documents({"active": True})
    # ANTES: servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
    all_servers = await registry_list_servers(db=db, filter_active=True, mask_secrets=True)
    total_servers = len(all_servers)
    servers_configured = len([s for s in all_servers if s.get('queries_configured', False)])
    
    # NOTA: db.users y db.alerts aún usan MongoDB (migración en Fase 2)
    total_users = await db.users.count_documents({"active": True})
    total_alerts = await db.alerts.count_documents({"active": True})
    
    return {
        "total_servers": total_servers,
        "total_users": total_users,
        "total_alerts": total_alerts,
        "servers_configured": servers_configured
    }

# ============= MÓDULO DE COMPRAS - MODELOS =============

class ParametrosCompra(BaseModel):
    dias_inventario: int = 10  # Días de inventario a comprar
    excluir_domingos: bool = True
    dias_inhabiles: List[str] = []  # Lista de fechas YYYY-MM-DD
    dias_transito_proveedor: int = 2  # Días que tarda en llegar el producto

class CalculoPedidoRequest(BaseModel):
    server_id: str
    sucursal: str
    almacenes: List[str]  # Puede ser uno, varios, o "TODOS"
    fecha_inventario_fisico: str  # Fecha del inventario físico inicial
    fecha_fin_periodo: str  # Fecha fin del período de análisis
    dias_inventario: int = 10  # Días de inventario a comprar
    metodo_calculo: str = "consumo"  # "consumo" (promedio) o "stock" (min/max)
    folio_inventario_fisico: Optional[str] = None
    categorias: Optional[List[str]] = None
    familias: Optional[List[str]] = None
    folio_pedido_comparar: Optional[str] = None  # Para comparar con pedido existente

# ============= MÓDULO DE COMPRAS - ENDPOINTS =============
#
# FASE 4B DEL REFACTOR MODULAR (Diciembre 2025):
# 
# ESTADO ACTUAL:
# - La estructura modular está creada (schemas, repository, service)
# - Los ENDPOINTS permanecen aquí por su complejidad (~2000 líneas de lógica)
# - Se migrarán gradualmente en fases posteriores
#
# ENDPOINTS EN ESTE ARCHIVO:
# - GET /compras/inventarios-fisicos/{server_id}
# - GET /compras/pedidos-vigentes/{server_id}  
# - GET /compras/parametros/{server_id}
# - POST /compras/parametros
# - GET /compras/detalle-pedido/{server_id}/{folio}
# - GET /compras/detalle-pedido-manual/{server_id}
# - GET /compras/detalle-movimientos/{server_id}
# - GET /compras/detalle-consumos/{server_id}
# - POST /compras/calculo-pedido (~420 líneas)
# - POST /compras/productos-para-captura
# - POST /compras/auditoria-operativa (~710 líneas)
# - POST /compras/detalle-movimientos
# - POST /compras/detalle-consumos
# - GET /compras/dashboard/{server_id}
# - POST /compras/analisis
# - GET /compras/facturas-proveedor/{server_id}
# - GET /compras/detalle-factura/{server_id}/{folio}
#
# JUSTIFICACIÓN:
# Estos endpoints contienen lógica de negocio crítica para:
# - Cálculo de pedidos sugeridos
# - Auditoría operativa
# - Dashboard de compras
# - Análisis de compras
# La migración debe hacerse con cuidado para no romper funcionalidad.
# =============================================================================

# =============================================================================
# FASE 3.1: VALIDACIÓN DE ACCESO POR EMPRESA (Compras)
# =============================================================================

async def validate_server_access_by_empresa(server_id: str, credentials: HTTPAuthorizationCredentials) -> dict:
    """
    FASE 6-8: Valida acceso al servidor usando resolve_user_access_context().
    
    Esta función reemplaza la lógica dispersa de validación por la función centralizada.
    NUNCA confía en parámetros del frontend.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 1:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    
    FASE 2-G FIX: Usar get_current_user que busca en SQL en lugar de db.users (MongoDB)
    
    Returns:
        dict con usuario, servidor y contexto de acceso
    
    Raises:
        HTTPException 403 si no tiene acceso
        HTTPException 404 si servidor no existe
    """
    from core.server_registry import get_server_connection_info
    
    # FASE 2-G FIX: Usar get_current_user (SQL-only) en lugar de db.users (MongoDB)
    user = await get_current_user(credentials)
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)
    
    if not server:
        logging.warning(f"[VALIDATE_SERVER_ACCESS] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    logging.debug(f"[VALIDATE_SERVER_ACCESS] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
    
    # FASE 6-8: Validar acceso usando función centralizada
    context = await resolve_user_access_context(user)
    
    if not has_server_access(context, server_id):
        logging.warning(
            f"[RBAC-DENEGADO] Usuario {user.get('email')} "
            f"sin acceso a servidor {server_id}. "
            f"Fuente: {context.fuente_acceso}, Servidores: {context.servers_ids}"
        )
        raise HTTPException(
            status_code=403, 
            detail="No tiene acceso a este servidor"
        )
    
    return {"user": user, "server": server, "context": context}

@api_router.get("/compras/inventarios-fisicos/{server_id}")
async def obtener_inventarios_fisicos(server_id: str, sucursal: str = None, sucursal_id: str = None, almacen: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene la lista de inventarios físicos disponibles para seleccionar.
    
    ESTRATEGIA HÍBRIDA:
    1. Primero intenta leer de EDARSAHUB (tabla Compras_Inventarios_Fisicos_Sync)
    2. Si Sync está vacío, hace fallback a consulta LIVE al servidor físico
    
    FASE 8: Aplica filtro RBAC por almacenes permitidos.
    """
    # FASE 3.1: Validar acceso por empresa
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    context = access["context"]  # FASE 8: Obtener contexto RBAC
    
    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
    
    logging.info(
        f"[COMPRAS-HIBRIDO] Inventarios físicos - "
        f"Usuario={access['user'].get('email')}, Server={server_id}, "
        f"AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    # =========================================================================
    # PASO 1: Intentar leer de EDARSAHUB Sync
    # =========================================================================
    try:
        unidad_negocio_id = None
        try:
            from core.unidades_registry import get_unidad_by_server_id
            unidad_info = get_unidad_by_server_id(server_id)
            if unidad_info:
                unidad_negocio_id = unidad_info.id
        except Exception:
            pass
        
        inventarios = obtener_inventarios_fisicos_sync(
            unidad_negocio_id=unidad_negocio_id,
            server_id=server_id,
            sucursal=sucursal or sucursal_id,
            almacen=almacen,
            limit=500
        )
        
        if inventarios and len(inventarios) > 0:
            # Aplicar filtro RBAC
            if almacenes_permitidos:
                inventarios = [
                    inv for inv in inventarios 
                    if inv.get('almacen_id') in almacenes_permitidos 
                    or not almacenes_permitidos
                ]
            
            logging.info(f"[COMPRAS-HIBRIDO] ✅ Inventarios desde SYNC: {len(inventarios)} registros")
            
            return [{
                "folio": str(inv.get('folio', '')),
                "fecha": str(inv.get('fecha', '')),
                "almacen": inv.get('almacen', 'Sin almacén'),
                "almacen_id": str(inv.get('almacen_id', '')),
                "sucursal": inv.get('sucursal', ''),
                "sucursal_id": str(inv.get('sucursal_id', '')),
                "comentario": '',
                "productos": int(inv.get('total_productos', 0)),
                "source": "EDARSAHUB_SYNC",
                "sync_status": inv.get('sync_status', 'SYNCED'),
            } for inv in inventarios]
    except Exception as e:
        logging.warning(f"[COMPRAS-HIBRIDO] Error leyendo Sync, intentando LIVE: {e}")
    
    # =========================================================================
    # PASO 2: Fallback a consulta LIVE (si Sync está vacío o falló)
    # =========================================================================
    logging.info(f"[COMPRAS-HIBRIDO] Sync vacío/fallido, consultando LIVE: {server.get('name')}")
    
    if is_mpro_system(server.get('system_type')):
        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.Al_Cve_Almacen")
        almacen_safe = _escape_like_pattern(almacen) if almacen else ""
        sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
        
        almacen_filtro = ""
        if almacen and almacen != "TODOS":
            almacen_filtro = f"AND A.Al_Descripcion LIKE '%{almacen_safe}%'"
        
        sucursal_filtro = "1=1"
        if sucursal_id:
            sucursal_filtro = f"A.Sc_Cve_Sucursal = '{sucursal_id}'"
        elif sucursal:
            if sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0'):
                sucursal_filtro = f"A.Sc_Cve_Sucursal = '{sucursal}'"
            else:
                sucursal_filtro = f"S.Sc_Descripcion LIKE '%{sucursal_safe}%'"
        
        query = f"""
SELECT DISTINCT 
    F.Fi_Folio as folio, F.Fi_Fecha as fecha,
    A.Al_Descripcion as almacen, A.Al_Cve_Almacen as almacen_id,
    S.Sc_Descripcion as sucursal, A.Sc_Cve_Sucursal as sucursal_id,
    ISNULL(F.Fi_Comentario, '') as comentario,
    COUNT(DISTINCT F.Pr_Cve_Producto) as total_productos
FROM Fisico F
INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE {sucursal_filtro} {almacen_filtro} {almacen_rbac_filter}
GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, A.Al_Cve_Almacen, S.Sc_Descripcion, A.Sc_Cve_Sucursal, F.Fi_Comentario
ORDER BY F.Fi_Folio DESC
"""
        try:
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query, timeout=30
            )
            logging.info(f"[COMPRAS-HIBRIDO] ✅ MPRO LIVE: {len(result)} inventarios")
            return [{"folio": r['folio'], "fecha": str(r['fecha']), "almacen": r['almacen'], 
                     "almacen_id": r.get('almacen_id', ''), "sucursal": r.get('sucursal', ''),
                     "sucursal_id": r.get('sucursal_id', ''), "comentario": r['comentario'],
                     "productos": r['total_productos'], "source": "LIVE"} for r in result]
        except Exception as e:
            error_msg = str(e)
            log_compras_error("inventarios-fisicos", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
            if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower():
                raise HTTPException(status_code=503, detail=f"Servidor temporalmente inaccesible: {server['host']}")
            raise HTTPException(status_code=500, detail=f"Error consultando inventarios: {error_msg[:200]}")
    
    elif is_softrestaurant_system(server.get('system_type')):
        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.idalmacen")
        almacen_safe = _escape_like_pattern(almacen) if almacen else ""
        
        almacen_filtro = ""
        if almacen and almacen != "TODOS":
            almacen_filtro = f"AND A.nombre LIKE '%{almacen_safe}%'"
        
        query = f"""
SELECT DISTINCT 
    INV.folio as folio, INV.fecha as fecha,
    A.nombre as almacen, A.idalmacen as almacen_id, '' as comentario
FROM invfisico INV
LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
WHERE 1=1 {almacen_filtro} {almacen_rbac_filter}
ORDER BY INV.folio DESC, INV.fecha DESC
"""
        try:
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            logging.info(f"[COMPRAS-HIBRIDO] ✅ SoftRestaurant LIVE: {len(result)} inventarios")
            return [{"folio": str(r['folio']), "fecha": str(r['fecha']), 
                     "almacen": r['almacen'] or 'Sin almacén', "almacen_id": str(r.get('almacen_id', '')),
                     "comentario": '', "productos": 0, "source": "LIVE"} for r in result]
        except Exception as e:
            log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), server.get('system_type'))
            raise HTTPException(status_code=500, detail=f"Error consultando inventarios: {str(e)[:200]}")
    
    system_type = server.get('system_type', 'UNKNOWN')
    normalized = normalize_system_type(system_type)
    log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
    raise HTTPException(status_code=400, detail=f"Sistema '{system_type}' (normalizado: {normalized}) no soportado")

@api_router.get("/compras/pedidos-vigentes/{server_id}")
async def obtener_pedidos_vigentes(server_id: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene la lista de REQUISICIONES de compra SIN AUTORIZAR (estado PXA) para comparar.
    
    ESTRATEGIA HÍBRIDA:
    1. Primero intenta leer de EDARSAHUB (tabla Compras_Requisiciones_Sync)
    2. Si Sync está vacío, hace fallback a consulta LIVE al servidor físico
    """
    # FASE 3.1: Validar acceso por empresa
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    
    logging.info(
        f"[COMPRAS-HIBRIDO] Requisiciones - "
        f"Usuario={access['user'].get('email')}, Server={server_id}"
    )
    
    # =========================================================================
    # PASO 1: Intentar leer de EDARSAHUB Sync
    # =========================================================================
    try:
        unidad_negocio_id = None
        try:
            from core.unidades_registry import get_unidad_by_server_id
            unidad_info = get_unidad_by_server_id(server_id)
            if unidad_info:
                unidad_negocio_id = unidad_info.id
        except Exception:
            pass
        
        requisiciones = obtener_requisiciones_sync(
            unidad_negocio_id=unidad_negocio_id,
            server_id=server_id,
            sucursal=sucursal,
            limit=500
        )
        
        if requisiciones and len(requisiciones) > 0:
            logging.info(f"[COMPRAS-HIBRIDO] ✅ Requisiciones desde SYNC: {len(requisiciones)} registros")
            
            return [{
                "tipo": req.get('tipo', 'OC'),
                "folio": str(req.get('folio', '')),
                "fecha": str(req.get('fecha', '')),
                "comentario": '',
                "estado": req.get('estatus', 'PENDIENTE'),
                "comprador": req.get('proveedor', ''),
                "productos": int(req.get('total_productos', 0)),
                "importe": float(req.get('importe', 0) or 0),
                "source": "EDARSAHUB_SYNC",
                "sync_status": req.get('sync_status', 'SYNCED'),
            } for req in requisiciones]
    except Exception as e:
        logging.warning(f"[COMPRAS-HIBRIDO] Error leyendo Sync requisiciones, intentando LIVE: {e}")
    
    # =========================================================================
    # PASO 2: Fallback a consulta LIVE (si Sync está vacío o falló)
    # =========================================================================
    logging.info(f"[COMPRAS-HIBRIDO] Sync vacío/fallido, consultando LIVE: {server.get('name')}")
    
    if is_mpro_system(server.get('system_type')):
        sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
        
        sucursal_filtro = "1=1"
        if sucursal:
            sucursal_filtro = f"(S.Sc_Cve_Sucursal = '{sucursal}' OR S.Sc_Descripcion LIKE '%{sucursal_safe}%')"
        
        query = f"""
SELECT 'OC' as tipo, OC.Oc_Folio as folio, OC.Oc_Fecha as fecha, 
       OC.Oc_Comentario as comentario, OC.Es_Cve_Estado as estado,
       P.Pv_Descripcion as proveedor,
       COUNT(OC.Pr_Cve_Producto) as total_productos,
       0 as importe_total
FROM Orden_Compra OC
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = OC.Sc_Cve_Sucursal
LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = OC.Pv_Cve_Proveedor
WHERE {sucursal_filtro}
    AND OC.Es_Cve_Estado IN ('PXA', 'AC', 'RCT')
    AND OC.Oc_Fecha >= DATEADD(day, -30, GETDATE())
GROUP BY OC.Oc_Folio, OC.Oc_Fecha, OC.Oc_Comentario, OC.Es_Cve_Estado, P.Pv_Descripcion
ORDER BY OC.Oc_Fecha DESC
"""
        try:
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query, timeout=30
            )
            logging.info(f"[COMPRAS-HIBRIDO] ✅ MPRO LIVE: {len(result)} requisiciones")
            return [{"tipo": r['tipo'], "folio": r['folio'], "fecha": str(r['fecha']), 
                     "comentario": r['comentario'] or '', "estado": r['estado'],
                     "comprador": r['proveedor'] or '', "productos": r['total_productos'],
                     "importe": float(r['importe_total'] or 0), "source": "LIVE"} for r in result]
        except Exception as e:
            error_msg = str(e)
            log_compras_error("pedidos-vigentes", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
            if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower():
                raise HTTPException(status_code=503, detail=f"Servidor temporalmente inaccesible: {server['host']}")
            raise HTTPException(status_code=500, detail=f"Error consultando requisiciones: {error_msg[:200]}")
    
    elif is_softrestaurant_system(server.get('system_type')):
        query = """
SELECT 'ORDEN' as tipo, OC.folio as folio, OC.fechacaptura as fecha,
       '' as comentario, 
       CASE WHEN OC.aplicada = 0 THEN 'PXA' ELSE 'AUT' END as estado,
       PR.nombre as proveedor,
       COUNT(OCM.idinsumo) as total_productos,
       ISNULL(OC.total, 0) as importe_total
FROM ordenescompra OC
LEFT JOIN proveedores PR ON PR.idproveedor = OC.idproveedor
LEFT JOIN ordenescompramov OCM ON OCM.idordencompra = OC.idordencompra
WHERE OC.aplicada = 0 AND OC.cancelado = 0
    AND OC.fechacaptura >= DATEADD(day, -30, GETDATE())
GROUP BY OC.folio, OC.fechacaptura, OC.aplicada, PR.nombre, OC.total
ORDER BY OC.fechacaptura DESC
"""
        try:
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            logging.info(f"[COMPRAS-HIBRIDO] ✅ SoftRestaurant LIVE: {len(result)} requisiciones")
            return [{"tipo": r['tipo'], "folio": str(r['folio']), "fecha": str(r['fecha']), 
                     "comentario": r['comentario'] or '', "estado": r['estado'],
                     "comprador": r['proveedor'] or '', "productos": r['total_productos'],
                     "importe": float(r['importe_total'] or 0), "source": "LIVE"} for r in result]
        except Exception as e:
            logging.warning(f"Error obteniendo pedidos SoftRestaurant: {e}")
            return []
    
    return []

@api_router.get("/compras/detalle-pedido-manual/{server_id}")
async def obtener_detalle_pedido_manual(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el detalle de una requisición por folio manual"""
    # FASE 3.1: Validar acceso por empresa
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    
    if is_mpro_system(server.get('system_type')):
        # Buscar primero en REQUISICION_COMPRA_DETALLE (tabla principal)
        query = f"""
SELECT 'REQUI' as tipo, RCD.Pr_Cve_Producto as codigo, P.Pr_Descripcion as producto,
       RCD.Rc_Cantidad as cantidad, RCD.Rc_Costo as costo,
       RC.Rc_Comentario as comentario
FROM Requisicion_Compra_Detalle RCD
INNER JOIN Producto P ON P.Pr_Cve_Producto = RCD.Pr_Cve_Producto
INNER JOIN Requisicion_Compra RC ON RC.Rc_Folio = RCD.Rc_Folio
WHERE RCD.Rc_Folio = '{folio}'
"""
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        if result:
            return {"folio": folio, "tipo": result[0]['tipo'], "comentario": result[0].get('comentario', ''), "detalle": [
                {"codigo": r['codigo'], "producto": r['producto'], "cantidad": float(r['cantidad'] or 0), "costo": float(r['costo'] or 0)}
                for r in result
            ]}
        
        # Si no encuentra en requisición, buscar en pedido/orden (legacy)
        query_legacy = f"""
SELECT 'PEDIDO' as tipo, PDD.Pr_Cve_Producto as codigo, P.Pr_Descripcion as producto,
       PDD.Pd_Cantidad as cantidad, PDD.Pd_Costo as costo
FROM Pedido_Detalle PDD
INNER JOIN Producto P ON P.Pr_Cve_Producto = PDD.Pr_Cve_Producto
WHERE PDD.Pd_Folio = '{folio}'
UNION ALL
SELECT 'ORDEN' as tipo, OCD.Pr_Cve_Producto as codigo, P.Pr_Descripcion as producto,
       OCD.Oc_Cantidad as cantidad, OCD.Oc_Costo as costo
FROM Orden_Compra_Detalle OCD
INNER JOIN Producto P ON P.Pr_Cve_Producto = OCD.Pr_Cve_Producto
WHERE OCD.Oc_Folio = '{folio}'
"""
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_legacy
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"No se encontró el folio '{folio}'")
        return {"folio": folio, "tipo": result[0]['tipo'], "comentario": '', "detalle": [
            {"codigo": r['codigo'], "producto": r['producto'], "cantidad": float(r['cantidad'] or 0), "costo": float(r['costo'] or 0)}
            for r in result
        ]}
    
    return {"detail": "Sistema no soportado"}

@api_router.get("/compras/detalle-movimientos/{server_id}")
async def obtener_detalle_movimientos(server_id: str, codigo_producto: str, almacenes: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el detalle de movimientos de un producto para mostrar en popup"""
    # FASE 3.1: Validar acceso por empresa
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    
    almacen_list = almacenes.split(',')
    almacen_codigos_str = ",".join([f"'{a}'" for a in almacen_list])
    
    if is_mpro_system(server.get('system_type')):
        query = f"""
SELECT 
    E.Mv_Fecha as fecha,
    E.Mv_Documento as documento,
    TM.Tm_Descripcion as tipo_movimiento,
    TM.Tm_Tipo as tipo,
    E.Mv_Cantidad_Control_1 as cantidad,
    A.Al_Descripcion as almacen
FROM Movimiento E
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen
WHERE E.Pr_Cve_Producto = '{codigo_producto}'
    AND E.Al_Cve_Almacen IN ({almacen_codigos_str})
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY E.Mv_Fecha
"""
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return [{"fecha": str(r['fecha']), "documento": r['documento'], "tipo": r['tipo_movimiento'],
                 "entrada_salida": r['tipo'], "cantidad": float(r['cantidad'] or 0), "almacen": r['almacen']} for r in result]
    
    return []

@api_router.get("/compras/detalle-consumos/{server_id}")
async def obtener_detalle_consumos(server_id: str, codigo_producto: str, sucursal_codigo: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el detalle de consumos/ventas de un producto para mostrar en popup"""
    # FASE 3.1: Validar acceso por empresa
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    
    if is_mpro_system(server.get('system_type')):
        query = f"""
SELECT 
    V.Vn_Fecha as fecha,
    V.Vn_Documento as documento,
    P_VENTA.Pr_Descripcion as producto_vendido,
    PK.Pk_Cantidad as cantidad_receta,
    V.Vn_Cantidad_1 as cantidad_vendida,
    (V.Vn_Cantidad_1 * PK.Pk_Cantidad) as consumo_insumo
FROM Venta V
INNER JOIN Producto_Kit PK ON PK.Pr_Cve_Producto = V.Pr_Cve_Producto
INNER JOIN Producto P_VENTA ON P_VENTA.Pr_Cve_Producto = V.Pr_Cve_Producto
WHERE PK.Pk_Producto = '{codigo_producto}'
    AND V.Sc_Cve_Sucursal = '{sucursal_codigo}'
    AND V.Es_Cve_Estado <> 'CA'
    AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY V.Vn_Fecha
"""
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return [{"fecha": str(r['fecha']), "documento": r['documento'], "producto_vendido": r['producto_vendido'],
                 "cantidad_receta": float(r['cantidad_receta'] or 0), "cantidad_vendida": float(r['cantidad_vendida'] or 0),
                 "consumo": float(r['consumo_insumo'] or 0)} for r in result]
    
    return []

@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
async def obtener_detalle_pedido(server_id: str, folio: str, tipo: str = "PEDIDO", credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene el detalle de un pedido/orden de compra para comparar.
    FASE 8: Aplica validación RBAC de servidor.
    """
    # FASE 8: Validar acceso por empresa y servidor
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    access["context"]
    
    logging.info(
        f"[RBAC-DETALLE-PEDIDO] Usuario={access['user'].get('email')}, "
        f"Server={server_id}, Folio={folio}, Tipo={tipo}"
    )
    
    if is_mpro_system(server.get('system_type')):
        if tipo == "PEDIDO":
            query = f"""
SELECT 
    PDD.Pr_Cve_Producto as codigo,
    P.Pr_Descripcion as producto,
    PDD.Pd_Cantidad as cantidad,
    PDD.Pd_Costo as costo,
    PDD.Pd_Importe as importe
FROM Pedido_Detalle PDD
INNER JOIN Producto P ON P.Pr_Cve_Producto = PDD.Pr_Cve_Producto
WHERE PDD.Pd_Folio = '{folio}'
"""
        else:
            query = f"""
SELECT 
    OCD.Pr_Cve_Producto as codigo,
    P.Pr_Descripcion as producto,
    OCD.Oc_Cantidad as cantidad,
    OCD.Oc_Costo as costo,
    OCD.Oc_Importe as importe
FROM Orden_Compra_Detalle OCD
INNER JOIN Producto P ON P.Pr_Cve_Producto = OCD.Pr_Cve_Producto
WHERE OCD.Oc_Folio = '{folio}'
"""
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return {r['codigo']: {"cantidad": float(r['cantidad'] or 0), "costo": float(r['costo'] or 0)} for r in result}

@api_router.post("/compras/calculo-pedido")
async def calcular_pedido_sugerido(request: CalculoPedidoRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Calcula el pedido sugerido basándose en:
    1. Inventario inicial (físico capturado en fecha_inventario_fisico)
    2. + Compras del período (movimientos tipo entrada)
    3. - Consumos/Ventas del período
    4. = Inventario Teórico Actual
    5. Cantidad a pedir según método:
       - consumo: (Promedio Diario × Días Inventario) - Disponible
       - stock: Stock Máximo - Disponible
    FASE 8: Aplica validación RBAC de servidor y almacenes.
    """
    # FASE 8: Validar acceso por empresa y servidor
    access = await validate_server_access_by_empresa(request.server_id, credentials)
    server = access["server"]
    context = access["context"]
    
    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
    
    logging.info(
        f"[RBAC-CALCULO-PEDIDO] Usuario={access['user'].get('email')}, "
        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )
    
    sucursal = request.sucursal
    almacenes = request.almacenes  # Lista de almacenes o ["TODOS"]
    fecha_inv_fisico = request.fecha_inventario_fisico
    fecha_fin = request.fecha_fin_periodo
    dias_inventario = request.dias_inventario
    metodo = request.metodo_calculo  # "consumo" o "stock"
    folio_inv = request.folio_inventario_fisico
    
    # Calcular días del período para promedio
    from datetime import datetime, timedelta
    fecha_ini_dt = datetime.strptime(fecha_inv_fisico, '%Y-%m-%d')
    fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
    dias_periodo = (fecha_fin_dt - fecha_ini_dt).days
    if dias_periodo <= 0:
        dias_periodo = 1
    
    # Para movimientos: desde fecha_inv_fisico + 1 día
    fecha_mov_ini = (fecha_ini_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    
    logging.info(f"[COMPRAS] Parámetros: sucursal={sucursal}, almacenes={almacenes}")
    logging.info(f"[COMPRAS] Período: {fecha_inv_fisico} al {fecha_fin} ({dias_periodo} días)")
    logging.info(f"[COMPRAS] Método: {metodo}, Días inventario: {dias_inventario}")
    
    if is_mpro_system(server.get('system_type')):
        # FASE 8: Agregar filtro RBAC a la query de almacenes
        almacen_rbac_filter = get_almacenes_sql_filter(context, request.server_id, "A.Al_Cve_Almacen")
        
        # FASE 1C: Sanitizar entradas LIKE
        sucursal_safe = _escape_like_pattern(sucursal) if sucursal else ""
        
        # Obtener códigos de almacenes
        if "TODOS" in almacenes:
            almacen_query = f"""
SELECT A.Al_Cve_Almacen as codigo, A.Al_Descripcion as nombre, A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%' AND A.Es_Cve_Estado <> 'BA'{almacen_rbac_filter}
"""
        else:
            # FASE 1C: Sanitizar cada almacén de la lista
            almacen_likes = " OR ".join([f"A.Al_Descripcion LIKE '%{_escape_like_pattern(a)}%'" for a in almacenes])
            almacen_query = f"""
SELECT A.Al_Cve_Almacen as codigo, A.Al_Descripcion as nombre, A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%' AND ({almacen_likes}) AND A.Es_Cve_Estado <> 'BA'{almacen_rbac_filter}
"""
        
        almacen_result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], almacen_query
        )
        if not almacen_result:
            raise HTTPException(status_code=404, detail=f"No se encontraron almacenes para sucursal '{sucursal}'")
        
        almacen_codigos = [a['codigo'] for a in almacen_result]
        almacen_nombres = [a['nombre'] for a in almacen_result]
        sucursal_codigo = almacen_result[0]['sucursal_codigo']
        # Solo es bodega si TODOS los almacenes seleccionados son bodegas (no solo algunos)
        es_bodega = all('BODEGA' in (a['nombre'] or '').upper() for a in almacen_result)
        
        almacen_codigos_str = ",".join([f"'{c}'" for c in almacen_codigos])
        
        logging.info(f"[COMPRAS] Almacenes encontrados: {almacen_nombres}")
        
        # Construir filtros
        filtro_categorias = ""
        if request.categorias:
            cats = ",".join([f"'{c}'" for c in request.categorias])
            filtro_categorias = f"AND P.Ct_Cve_Categoria IN ({cats})"
        
        filtro_familias = ""
        if request.familias:
            fams = ",".join([f"'{f}'" for f in request.familias])
            filtro_familias = f"AND P.Fm_Cve_Familia IN ({fams})"
        
        # Verificar folio de inventario físico
        if folio_inv:
            folio_inventario = folio_inv
            fecha_inventario = fecha_inv_fisico
            tiene_inventario_fisico = True
        else:
            # Buscar el más reciente
            inv_query = f"""
SELECT TOP 1 Fi_Folio as folio, Fi_Fecha as fecha
FROM Fisico WHERE Al_Cve_Almacen IN ({almacen_codigos_str})
ORDER BY Fi_Fecha DESC
"""
            inv_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], inv_query
            )
            tiene_inventario_fisico = len(inv_result) > 0
            folio_inventario = inv_result[0]['folio'] if tiene_inventario_fisico else None
            fecha_inventario = inv_result[0]['fecha'] if tiene_inventario_fisico else None
        
        logging.info(f"[COMPRAS] Inventario físico: folio={folio_inventario}, fecha={fecha_inventario}")
        
        # 1. Obtener catálogo de productos - MISMA LÓGICA DEL REPORTE DE INVENTARIOS
        productos_query = f"""
WITH InsumosConPresentaciones AS (
    SELECT DISTINCT P.Pr_Cve_Producto
    FROM Producto P
    INNER JOIN Producto_Presentacion PP ON PP.Pr_Cve_Producto = P.Pr_Cve_Producto
    WHERE P.Dp_Cve_Departamento = '0007' AND P.Es_Cve_Estado <> 'BA'
),
ProductosComoPresentacion AS (
    SELECT DISTINCT Pp_Producto as Pr_Cve_Producto FROM Producto_Presentacion
)
SELECT 
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    F.Fm_Descripcion as Familia,
    C.Ct_Descripcion as Categoria,
    P.Pr_Unidad_Control_1 as Unidad,
    P.Pr_ultimo_costo as Costo_Unitario,
    CASE WHEN ICP.Pr_Cve_Producto IS NOT NULL THEN 1 ELSE 0 END as Tiene_Presentaciones
FROM Producto P
INNER JOIN Familia F ON F.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
LEFT JOIN InsumosConPresentaciones ICP ON ICP.Pr_Cve_Producto = P.Pr_Cve_Producto
LEFT JOIN ProductosComoPresentacion PCP ON PCP.Pr_Cve_Producto = P.Pr_Cve_Producto
WHERE P.Es_Cve_Estado <> 'BA'
    AND (
        (P.Dp_Cve_Departamento = '0007' AND ICP.Pr_Cve_Producto IS NOT NULL)
        OR
        (P.Dp_Cve_Departamento <> '0007' AND PCP.Pr_Cve_Producto IS NULL)
    )
    {filtro_categorias}
    {filtro_familias}
"""
        productos = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], productos_query
        )
        logging.info(f"[COMPRAS] Productos obtenidos: {len(productos)}")
        
        # 2. Obtener inventario físico
        inventario_dict = {}
        if tiene_inventario_fisico:
            inv_detalle_query = f"""
SELECT Pr_Cve_Producto as Codigo, SUM(Fi_Cantidad_Control_1) as Cantidad
FROM Fisico
WHERE Al_Cve_Almacen IN ({almacen_codigos_str}) AND Fi_Folio = '{folio_inventario}'
GROUP BY Pr_Cve_Producto
"""
            inv_detalle = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], inv_detalle_query
            )
            inventario_dict = {i['Codigo']: float(i['Cantidad'] or 0) for i in inv_detalle}
            logging.info(f"[COMPRAS] Inventario físico: {len(inventario_dict)} productos")
        
        # 3. Obtener movimientos (entradas = compras) del período
        # Usa la misma lógica de fechas del reporte de inventarios: desde fecha_inv + 1
        movimientos_query = f"""
SELECT E.Pr_Cve_Producto as Codigo, SUM(E.Mv_Cantidad_Control_1) as Total_Mov
FROM Movimiento E
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
WHERE E.Al_Cve_Almacen IN ({almacen_codigos_str})
    AND E.Es_Cve_Estado <> 'CA'
    AND TM.Tm_Cve_Tipo_Movimiento IN ('050','100','106','108','112','202','400','500','506','508','510','512')
    AND (
        CASE   
            WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
            THEN CASE WHEN E.Mv_Tabla = 'CONVERSION_PRODUCTO' THEN E.Mv_Fecha 
                 ELSE (SELECT TOP 1 C.Co_Fecha FROM Conversion_Producto CN
                       INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
                       WHERE CN.Cp_Folio = E.Mv_Documento) END
            ELSE E.Mv_Fecha
        END
    ) BETWEEN '{fecha_mov_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY E.Pr_Cve_Producto
"""
        mov_result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], movimientos_query
        )
        movimientos_dict = {m['Codigo']: float(m['Total_Mov'] or 0) for m in mov_result}
        logging.info(f"[COMPRAS] Movimientos obtenidos: {len(movimientos_dict)} productos")
        
        # 4. Obtener consumos/ventas del período - MISMA LÓGICA DEL REPORTE
        consumos_dict = {}
        if not es_bodega:
            ventas_query = f"""
SELECT Producto_Codigo, SUM(cantidad) as Total_Consumo FROM (
    SELECT Producto_Kit.Pk_Producto as Producto_Codigo,
           SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) as cantidad
    FROM venta 
    LEFT JOIN producto_kit ON Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
    LEFT JOIN producto ON producto.Pr_Cve_Producto = Producto_kit.Pk_Producto
    WHERE venta.Sc_Cve_Sucursal = '{sucursal_codigo}'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_mov_ini}' AND '{fecha_fin} 23:59:59'
        AND producto_kit.Pk_Producto IS NOT NULL
    GROUP BY Producto_Kit.Pk_Producto
    UNION ALL
    SELECT venta.Pr_Cve_Producto as Producto_Codigo,
           SUM(venta.Vn_Cantidad_Control_1) as cantidad
    FROM venta 
    INNER JOIN producto ON producto.Pr_Cve_Producto = venta.Pr_Cve_Producto 
    WHERE venta.Sc_Cve_Sucursal = '{sucursal_codigo}'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_mov_ini}' AND '{fecha_fin} 23:59:59'
    GROUP BY venta.Pr_Cve_Producto
) AS ConsumosCombinados
GROUP BY Producto_Codigo
"""
            ventas_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], ventas_query
            )
            consumos_dict = {v['Producto_Codigo']: float(v['Total_Consumo'] or 0) for v in ventas_result}
            logging.info(f"[COMPRAS] Consumos obtenidos: {len(consumos_dict)} productos")
        else:
            # Para bodegas: salidas como consumo
            salidas_query = f"""
SELECT M.Pr_Cve_Producto as Codigo, SUM(ABS(M.Mv_Cantidad_Control_1)) as Total
FROM Movimiento M
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
WHERE M.Al_Cve_Almacen IN ({almacen_codigos_str}) AND TM.Tm_Tipo = 'S'
    AND M.Mv_Fecha BETWEEN '{fecha_mov_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY M.Pr_Cve_Producto
"""
            salidas_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], salidas_query
            )
            consumos_dict = {s['Codigo']: float(s['Total'] or 0) for s in salidas_result}
            logging.info(f"[COMPRAS] Salidas (bodega): {len(consumos_dict)} productos")
        
        # 5. Obtener inventario físico FINAL (si existe folio en fecha_fin)
        inv_final_dict = {}
        folio_inv_final = None
        fecha_inv_final = None
        inv_final_query = f"""
SELECT TOP 1 Fi_Folio as folio, Fi_Fecha as fecha
FROM Fisico 
WHERE Al_Cve_Almacen IN ({almacen_codigos_str})
    AND CONVERT(date, Fi_Fecha) = CONVERT(date, '{fecha_fin}')
ORDER BY Fi_Fecha DESC
"""
        inv_final_result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], inv_final_query
        )
        if inv_final_result:
            folio_inv_final = inv_final_result[0]['folio']
            fecha_inv_final = inv_final_result[0]['fecha']
            # Obtener detalle del inventario final
            inv_final_detalle_query = f"""
SELECT Pr_Cve_Producto as Codigo, SUM(Fi_Cantidad_Control_1) as Cantidad
FROM Fisico
WHERE Al_Cve_Almacen IN ({almacen_codigos_str}) AND Fi_Folio = '{folio_inv_final}'
GROUP BY Pr_Cve_Producto
"""
            inv_final_detalle = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], inv_final_detalle_query
            )
            inv_final_dict = {i['Codigo']: float(i['Cantidad'] or 0) for i in inv_final_detalle}
            logging.info(f"[COMPRAS] Inventario FINAL encontrado: folio={folio_inv_final}, {len(inv_final_dict)} productos")
        else:
            logging.info(f"[COMPRAS] No hay inventario físico en fecha fin {fecha_fin}")
        
        # 6. Obtener pedido existente para comparar (si se especificó)
        pedido_existente = {}
        productos_pedido = set()  # Para filtrar 1:1
        if request.folio_pedido_comparar:
            # Buscar primero en REQUISICION_COMPRA_DETALLE
            ped_query = f"""
SELECT RCD.Pr_Cve_Producto as codigo, RCD.Rc_Cantidad as cantidad
FROM Requisicion_Compra_Detalle RCD WHERE RCD.Rc_Folio = '{request.folio_pedido_comparar}'
"""
            ped_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], ped_query
            )
            
            # Si no encuentra en requisición, buscar en pedido/orden (legacy)
            if not ped_result:
                ped_query_legacy = f"""
SELECT PDD.Pr_Cve_Producto as codigo, PDD.Pd_Cantidad as cantidad
FROM Pedido_Detalle PDD WHERE PDD.Pd_Folio = '{request.folio_pedido_comparar}'
UNION ALL
SELECT OCD.Pr_Cve_Producto as codigo, OCD.Oc_Cantidad as cantidad
FROM Orden_Compra_Detalle OCD WHERE OCD.Oc_Folio = '{request.folio_pedido_comparar}'
"""
                ped_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], ped_query_legacy
                )
            
            pedido_existente = {p['codigo']: float(p['cantidad'] or 0) for p in ped_result}
            productos_pedido = set(pedido_existente.keys())
            logging.info(f"[COMPRAS] Pedido a comparar: {len(pedido_existente)} productos")
        
        # 7. Calcular pedido sugerido
        results = []
        productos_sin_inventario = []
        
        for prod in productos:
            codigo = prod['Codigo']
            
            # FILTRO 1:1: Si se está comparando con un pedido, SOLO incluir productos de ese pedido
            if productos_pedido and codigo not in productos_pedido:
                continue
            
            inv_fisico = inventario_dict.get(codigo, 0)
            movimientos = movimientos_dict.get(codigo, 0)
            consumos = consumos_dict.get(codigo, 0)
            inv_final = inv_final_dict.get(codigo, None)  # None si no hay folio final
            costo = float(prod.get('Costo_Unitario', 0) or 0)
            # Stock min/max no disponible en esta versión
            stock_min = 0
            stock_max = 0
            
            # Inventario Teórico = Inv. Físico + Movimientos - Consumos
            inventario_teorico = inv_fisico + movimientos - consumos
            
            # Promedio diario de consumo
            promedio_diario = consumos / dias_periodo if dias_periodo > 0 else 0
            
            # Cantidad a pedir según método
            if metodo == "stock" and stock_max > 0:
                # Método stock: pedir hasta llegar al máximo
                cantidad_pedir = max(0, stock_max - inventario_teorico)
            else:
                # Método consumo: pedir para cubrir X días
                consumo_esperado = promedio_diario * dias_inventario
                cantidad_pedir = max(0, consumo_esperado - inventario_teorico)
            
            # Días de inventario actual
            dias_inv_actual = inventario_teorico / promedio_diario if promedio_diario > 0 else 999
            
            # Flag sin inventario físico inicial
            sin_inv_fisico_ini = inv_fisico == 0 and (movimientos != 0 or consumos > 0)
            # Flag sin inventario final (existe folio pero el producto no está)
            sin_inv_final = folio_inv_final is not None and inv_final is None and (inv_fisico > 0 or movimientos != 0 or consumos > 0)
            
            # Cantidad en pedido existente
            cant_pedido_exist = pedido_existente.get(codigo, 0)
            diferencia_pedido = cantidad_pedir - cant_pedido_exist if cant_pedido_exist > 0 else None
            
            # Solo incluir productos con actividad
            if inv_fisico > 0 or movimientos != 0 or consumos > 0 or cant_pedido_exist > 0 or (inv_final is not None and inv_final > 0):
                item = {
                    'Codigo': codigo,
                    'Producto': prod.get('Producto'),
                    'Familia': prod.get('Familia'),
                    'Categoria': prod.get('Categoria'),
                    'Unidad': prod.get('Unidad'),
                    'Costo_Unitario': round(costo, 2),
                    'Inventario_Inicial': round(inv_fisico, 2),
                    'Movimientos_Periodo': round(movimientos, 2),
                    'Consumos_Periodo': round(consumos, 2),
                    'Inventario_Final': round(inv_final, 2) if inv_final is not None else None,
                    'Inventario_Teorico': round(inventario_teorico, 2),
                    'Promedio_Diario': round(promedio_diario, 3),
                    'Dias_Inventario': round(dias_inv_actual, 1) if dias_inv_actual < 999 else 999,
                    'Stock_Minimo': round(stock_min, 2),
                    'Stock_Maximo': round(stock_max, 2),
                    'Cantidad_Pedir': round(cantidad_pedir, 2),
                    'Costo_Pedido': round(cantidad_pedir * costo, 2),
                    'Sin_Inventario_Inicial': sin_inv_fisico_ini,
                    'Sin_Inventario_Final': sin_inv_final,
                    'Cantidad_Pedido_Existente': round(cant_pedido_exist, 2) if cant_pedido_exist > 0 else None,
                    'Diferencia_Pedido': round(diferencia_pedido, 2) if diferencia_pedido is not None else None
                }
                results.append(item)
                
                if sin_inv_fisico_ini:
                    productos_sin_inventario.append(codigo)
        
        # Ordenar por cantidad a pedir (mayor primero)
        results.sort(key=lambda x: x['Cantidad_Pedir'], reverse=True)
        
        logging.info(f"[COMPRAS] Cálculo completado: {len(results)} productos")
        
        return {
            "data": results,
            "count": len(results),
            "tiene_inventario_fisico": tiene_inventario_fisico,
            "fecha_inventario_fisico": str(fecha_inventario) if fecha_inventario else fecha_inv_fisico,
            "folio_inventario_fisico": folio_inventario,
            "tiene_inventario_final": folio_inv_final is not None,
            "fecha_inventario_final": str(fecha_inv_final) if fecha_inv_final else None,
            "folio_inventario_final": folio_inv_final,
            "productos_sin_inventario": len(productos_sin_inventario),
            "es_bodega": es_bodega,
            "almacenes": almacen_nombres,
            "almacen_codigos": almacen_codigos,
            "sucursal_codigo": sucursal_codigo,
            "dias_periodo": dias_periodo,
            "comparando_con_pedido": request.folio_pedido_comparar,
            "metodo_calculo": metodo,
            "parametros": {
                "fecha_inventario_fisico": fecha_inv_fisico,
                "fecha_fin_periodo": fecha_fin,
                "dias_inventario": dias_inventario,
                "sucursal": sucursal
            }
        }
    
    # SoftRestaurant - Por implementar
    return {"detail": "SoftRestaurant no implementado aún", "data": [], "count": 0}


@api_router.get("/compras/parametros/{server_id}")
async def obtener_parametros_compra(server_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene los parámetros de compra configurados para un servidor"""
    verify_token(credentials.credentials)
    
    params = await db.parametros_compra.find_one({"server_id": server_id})
    if not params:
        # Retornar valores por defecto
        return {
            "server_id": server_id,
            "dias_inventario": 10,
            "excluir_domingos": True,
            "dias_inhabiles": [],
            "dias_transito_proveedor": 2
        }
    
    # Excluir _id de MongoDB
    params.pop('_id', None)
    return params


@api_router.post("/compras/parametros")
async def guardar_parametros_compra(params: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Guarda los parámetros de compra para un servidor"""
    verify_token(credentials.credentials)
    
    server_id = params.get('server_id')
    if not server_id:
        raise HTTPException(status_code=400, detail="server_id es requerido")
    
    await db.parametros_compra.update_one(
        {"server_id": server_id},
        {"$set": params},
        upsert=True
    )
    
    return {"message": "Parámetros guardados correctamente"}


# ============= AUDITORÍA OPERATIVA DE COMPRAS =============

class AuditoriaOperativaRequest(BaseModel):
    server_id: str
    sucursal: str
    almacenes: List[str]
    folio_inv_inicial: Optional[str] = None  # Legacy: un solo folio
    folios_inv_inicial: Optional[List[str]] = None  # Nuevo: múltiples folios
    fecha_inv_inicial: str
    fecha_auditoria: str  # Fecha del inventario final o actual
    folio_inv_final: Optional[str] = None  # Legacy: un solo folio
    folios_inv_final: Optional[List[str]] = None  # Nuevo: múltiples folios
    folio_requisicion: Optional[str] = None  # Requisición a comparar (una sola)
    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
    inventario_manual: Optional[List[Dict]] = None  # Para captura manual si no hay folio
    inventario_fisico_actual: Optional[List[Dict]] = None  # Captura manual del inv físico del día del pedido
    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones
    dias_objetivo_default: int = 10  # Días de inventario objetivo por defecto
    dias_objetivo_por_sku: Optional[Dict[str, int]] = None  # Días personalizados por SKU {codigo: dias}


class ProductosParaCapturaRequest(BaseModel):
    server_id: str
    folios_inv_inicial: Optional[List[str]] = None
    folios_requisiciones: Optional[List[str]] = None

@api_router.post("/compras/productos-para-captura")
async def obtener_productos_para_captura(request: ProductosParaCapturaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene la lista de productos de los inventarios iniciales y/o requisiciones
    para inicializar la captura manual de inventario físico.
    """
    await get_current_user(credentials)
    
    # FASE T3.3: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    productos = {}
    
    try:
        if is_softrestaurant_system(server.get('system_type')):
            # Obtener productos de inventarios iniciales
            if request.folios_inv_inicial:
                for folio in request.folios_inv_inicial:
                    query = f"""
SELECT 
    RTRIM(COALESCE(
        NULLIF(RTRIM(IP.idinsumo), ''),
        NULLIF(RTRIM(INM.idinsumo), ''),
        INM.idpresentacion
    )) as codigo,
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto,
    ISNULL(IP.rendimiento, 1) as rendimiento
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
LEFT JOIN insumos I ON I.idinsumo = COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), NULLIF(RTRIM(INM.idinsumo), ''))
WHERE INM.folio = {folio}
"""
                    result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query
                    )
                    for r in result:
                        codigo = str(r['codigo'] or '').strip()
                        if codigo and codigo not in productos:
                            productos[codigo] = {
                                'codigo': codigo,
                                'producto': r['producto'] or f'SKU: {codigo}',
                                'rendimiento': float(r['rendimiento'] or 1)
                            }
            
            # Obtener productos de requisiciones
            if request.folios_requisiciones:
                folios_sql = ", ".join([f"'{f}'" for f in request.folios_requisiciones])
                query_requi = f"""
SELECT 
    RTRIM(OCM.idinsumo) as codigo,
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto,
    ISNULL(IP.rendimiento, 1) as rendimiento
FROM ordenescompramov OCM
INNER JOIN ordenescompra OC ON OC.idordencompra = OCM.idordencompra
LEFT JOIN insumos I ON I.idinsumo = OCM.idinsumo
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = OCM.idinsumo
WHERE OC.folio IN ({folios_sql})
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_requi
                )
                for r in result:
                    codigo = str(r['codigo'] or '').strip()
                    if codigo and codigo not in productos:
                        productos[codigo] = {
                            'codigo': codigo,
                            'producto': r['producto'] or f'SKU: {codigo}',
                            'rendimiento': float(r['rendimiento'] or 1)
                        }
        
        elif is_mpro_system(server.get('system_type')):
            # Para MPRO - Obtener productos de inventarios iniciales
            if request.folios_inv_inicial:
                for folio in request.folios_inv_inicial:
                    query = f"""
SELECT 
    P.Pr_Clave as codigo,
    P.Pr_Descripcion as producto,
    1 as rendimiento
FROM Fi_Detalle D
INNER JOIN Producto P ON P.Pr_Clave = D.Fi_Producto
WHERE D.Fi_Folio = '{folio}'
"""
                    result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query
                    )
                    for r in result:
                        codigo = str(r['codigo'] or '').strip()
                        if codigo and codigo not in productos:
                            productos[codigo] = {
                                'codigo': codigo,
                                'producto': r['producto'] or f'SKU: {codigo}',
                                'rendimiento': 1
                            }
            
            # MPRO - Obtener productos de requisiciones/órdenes de compra
            if request.folios_requisiciones:
                folios_sql = ", ".join([f"'{f}'" for f in request.folios_requisiciones])
                
                # En algunos esquemas MPRO, los productos están directamente en Orden_Compra
                # (no en una tabla separada de detalle)
                query_oc_direct = f"""
SELECT DISTINCT
    OC.Pr_Cve_Producto as codigo,
    P.Pr_Descripcion as producto,
    1 as rendimiento
FROM Orden_Compra OC
INNER JOIN Producto P ON P.Pr_Cve_Producto = OC.Pr_Cve_Producto
WHERE OC.Oc_Folio IN ({folios_sql})
"""
                try:
                    result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_oc_direct
                    )
                    for r in result:
                        codigo = str(r['codigo'] or '').strip()
                        if codigo and codigo not in productos:
                            productos[codigo] = {
                                'codigo': codigo,
                                'producto': r['producto'] or f'SKU: {codigo}',
                                'rendimiento': 1
                            }
                except Exception as e:
                    logging.warning(f"[MPRO] Error en Orden_Compra directa: {e}")
                
                # Si no encontró productos, intentar con Orden_Compra_Detalle (esquema alternativo)
                if len(productos) == 0:
                    query_oc_detail = f"""
SELECT DISTINCT
    OCD.Pr_Cve_Producto as codigo,
    P.Pr_Descripcion as producto,
    1 as rendimiento
FROM Orden_Compra_Detalle OCD
INNER JOIN Producto P ON P.Pr_Cve_Producto = OCD.Pr_Cve_Producto
WHERE OCD.Oc_Folio IN ({folios_sql})
"""
                    try:
                        result = execute_sql_query(
                            server['host'], server['port'], server['database'],
                            server['username'], server['password'], query_oc_detail
                        )
                        for r in result:
                            codigo = str(r['codigo'] or '').strip()
                            if codigo and codigo not in productos:
                                productos[codigo] = {
                                    'codigo': codigo,
                                    'producto': r['producto'] or f'SKU: {codigo}',
                                    'rendimiento': 1
                                }
                    except Exception as e:
                        logging.warning(f"[MPRO] Error en Orden_Compra_Detalle (esperado si no existe): {e}")
                
                # Último intento: Requisicion_Compra_Detalle
                if len(productos) == 0:
                    query_requi = f"""
SELECT DISTINCT
    RCD.Pr_Cve_Producto as codigo,
    P.Pr_Descripcion as producto,
    1 as rendimiento
FROM Requisicion_Compra_Detalle RCD
INNER JOIN Producto P ON P.Pr_Cve_Producto = RCD.Pr_Cve_Producto
WHERE RCD.Rc_Folio IN ({folios_sql})
"""
                    try:
                        result = execute_sql_query(
                            server['host'], server['port'], server['database'],
                            server['username'], server['password'], query_requi
                        )
                        for r in result:
                            codigo = str(r['codigo'] or '').strip()
                            if codigo and codigo not in productos:
                                productos[codigo] = {
                                    'codigo': codigo,
                                    'producto': r['producto'] or f'SKU: {codigo}',
                                    'rendimiento': 1
                                }
                    except Exception as e:
                        logging.warning(f"[MPRO] Error en Requisicion_Compra_Detalle (esperado si no existe): {e}")
        
        return {
            'productos': list(productos.values()),
            'total': len(productos)
        }
        
    except Exception as e:
        logging.error(f"Error obteniendo productos para captura: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/compras/auditoria-operativa")
async def realizar_auditoria_operativa(request: AuditoriaOperativaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Realiza Auditoría Operativa:
    1. Inventario Inicial + Compras - Consumos = Existencia Teórica
    2. Compara vs Inventario Físico (folio o captura manual)
    3. Calcula diferencias (favor +, en contra -)
    4. Genera acta de auditoría si hay diferencias en contra
    5. Calcula días de consumo y compara vs requisición
    
    FASE P1.4-E1 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones (incluye tipos_movimiento)
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    verify_token(credentials.credentials)
    
    logging.info(f"[AUDITORIA] Iniciando auditoría - server: {request.server_id}, sucursal: {request.sucursal}")
    
    # FASE P1.4-E1: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Probar conexión primero
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            test_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'],
                "SELECT 1 as test"
            )
            if test_result:
                logging.info(f"[AUDITORIA] Conexión verificada en intento {attempt + 1}")
                break
        except Exception as e:
            logging.warning(f"[AUDITORIA] Intento {attempt + 1} fallido: {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, detail=f"No se puede conectar al servidor después de {max_retries} intentos. Por favor intente de nuevo.")
            time.sleep(2)  # Esperar antes de reintentar
    
    fecha_ini = request.fecha_inv_inicial
    fecha_fin = request.fecha_auditoria
    
    # Convertir fechas a formato YYYYMMDD para pytds (evita error de conversión datetime)
    fecha_ini_sql = fecha_ini.replace('-', '')
    fecha_fin_sql = fecha_fin.replace('-', '')
    
    resultados = []
    resumen = {
        "total_teorico": 0,
        "total_fisico": 0,
        "total_diferencia": 0,
        "productos_favor": 0,
        "productos_contra": 0,
        "importe_favor": 0,
        "importe_contra": 0,
        "requiere_acta": False
    }
    
    try:
        if is_softrestaurant_system(server.get('system_type')):
            # PASO 1: Determinar tipo de almacenes seleccionados
            # tipo=1: Consumo (INSUMOS) - Barra, Cava, Producción
            # tipo=2: Bodega (PRESENTACIONES) - Bodega, Congelador
            almacenes_str = ", ".join([f"'{a}'" for a in request.almacenes])
            query_tipos_alm = f"""
SELECT idalmacen, nombre, ISNULL(tipo, 1) as tipo
FROM almacen
WHERE nombre IN ({almacenes_str}) OR idalmacen IN ({almacenes_str})
"""
            tipos_alm_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_tipos_alm
            )
            
            almacenes_bodega = [a['idalmacen'] for a in tipos_alm_result if a['tipo'] == 2]
            almacenes_consumo = [a['idalmacen'] for a in tipos_alm_result if a['tipo'] == 1]
            
            es_solo_bodega = len(almacenes_bodega) > 0 and len(almacenes_consumo) == 0
            es_solo_consumo = len(almacenes_consumo) > 0 and len(almacenes_bodega) == 0
            es_mixto = len(almacenes_bodega) > 0 and len(almacenes_consumo) > 0
            
            logging.info(f"[AUDITORIA] Almacenes - Bodega: {almacenes_bodega}, Consumo: {almacenes_consumo}")
            logging.info(f"[AUDITORIA] Tipo: solo_bodega={es_solo_bodega}, solo_consumo={es_solo_consumo}, mixto={es_mixto}")
            
            # PASO 2: Obtener SKUs de las requisiciones seleccionadas (para filtrar)
            folios_req = request.folios_requisiciones if request.folios_requisiciones else ([request.folio_requisicion] if request.folio_requisicion else [])
            
            skus_requisicion = set()
            requi_dict = {}
            requi_list = []  # Lista para mantener el orden por proveedor-pedido
            
            if folios_req:
                folios_sql = ", ".join([f"'{f}'" for f in folios_req])
                # Las órdenes de compra en SoftRestaurant usan códigos que pueden ser presentaciones
                # Obtener cada línea de pedido con su folio y proveedor
                query_requi = f"""
SELECT 
    OCM.idinsumo as codigo, 
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto, 
    OCM.cantidad as cantidad_pedido,
    ISNULL(OCM.costo, 0) as costo,
    ISNULL(ID.costo, 0) as costo_insumo,
    ISNULL(IPD.costo, ISNULL(OCM.costo, 0)) as costo_presentacion,
    COALESCE(P.nombre, 'Sin proveedor') as proveedor,
    OC.folio as folio_pedido,
    ISNULL(IP.rendimiento, 1) as rendimiento,
    COALESCE(I.unidad, IP.unidad, '') as unidad
FROM ordenescompramov OCM
INNER JOIN ordenescompra OC ON OC.idordencompra = OCM.idordencompra
LEFT JOIN insumos I ON I.idinsumo = OCM.idinsumo
LEFT JOIN insumosdetalle ID ON ID.idinsumo = OCM.idinsumo
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = OCM.idinsumo
LEFT JOIN insumospresentacionesdetalle IPD ON IPD.idinsumospresentaciones = OCM.idinsumo
LEFT JOIN proveedores P ON P.idproveedor = OC.idproveedor
WHERE OC.folio IN ({folios_sql})
ORDER BY P.nombre, OC.folio, OCM.idinsumo
"""
                requi_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_requi
                )
                for r in requi_result:
                    codigo = str(r['codigo']).strip()
                    skus_requisicion.add(codigo)
                    
                    # Guardar en lista para mantener orden por proveedor-pedido
                    requi_list.append({
                        'codigo': codigo,
                        'cantidad': float(r['cantidad_pedido'] or 0),
                        'producto': r['producto'] or '',
                        'costo': float(r.get('costo', 0) or 0),
                        'costo_insumo': float(r.get('costo_insumo', 0) or 0),
                        'costo_presentacion': float(r.get('costo_presentacion', 0) or r.get('costo', 0) or 0),
                        'proveedor': r.get('proveedor', '') or '',
                        'folio_pedido': str(r.get('folio_pedido', '')).strip(),
                        'rendimiento': float(r.get('rendimiento', 1) or 1),
                        'unidad': r.get('unidad', '') or ''
                    })
                    
                    # También mantener dict para lookup rápido
                    if codigo not in requi_dict:
                        requi_dict[codigo] = {
                            'cantidad': float(r['cantidad_pedido'] or 0),
                            'producto': r['producto'] or '',
                            'costo': float(r.get('costo', 0) or 0),
                            'costo_insumo': float(r.get('costo_insumo', 0) or 0),
                            'costo_presentacion': float(r.get('costo_presentacion', 0) or r.get('costo', 0) or 0),
                            'proveedor': r.get('proveedor', '') or '',
                            'folio_pedido': str(r.get('folio_pedido', '')).strip(),
                            'rendimiento': float(r.get('rendimiento', 1) or 1),
                            'unidad': r.get('unidad', '') or ''
                        }
                logging.info(f"[AUDITORIA] SKUs en requisiciones: {len(skus_requisicion)}, Líneas de pedido: {len(requi_list)}")
            
            # PASO 3: Obtener inventario inicial
            # Para BODEGA: usar idpresentacion como código
            # Para CONSUMO: usar idinsumo como código
            # NUEVO: Procesar múltiples folios y normalizar TODO a INSUMOS
            inv_ini_dict = {}
            
            # Combinar folios (legacy + nuevo formato)
            folios_iniciales = []
            if request.folios_inv_inicial:
                folios_iniciales = request.folios_inv_inicial
            elif request.folio_inv_inicial:
                folios_iniciales = [request.folio_inv_inicial]
            
            if folios_iniciales:
                for folio_inv in folios_iniciales:
                    # Determinar el tipo de almacén de este inventario específico
                    query_tipo_alm = f"""
SELECT A.tipo, A.nombre, INV.idalmacen1
FROM invfisico INV
LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
WHERE INV.folio = {folio_inv}
"""
                    tipo_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_tipo_alm
                    )
                    
                    # tipo=1: Consumo (insumos), tipo=2: Bodega (presentaciones)
                    tipo_almacen = tipo_result[0]['tipo'] if tipo_result else 1
                    es_bodega = tipo_almacen == 2
                    
                    logging.info(f"[AUDITORIA] Procesando inv inicial folio={folio_inv}, tipo_almacen={tipo_almacen}, es_bodega={es_bodega}")
                    
                    # Query para obtener datos del inventario
                    # SIEMPRE traemos el código de insumo para normalizar
                    query_inv_ini = f"""
SELECT 
    RTRIM(COALESCE(
        NULLIF(RTRIM(IP.idinsumo), ''),
        NULLIF(RTRIM(INM.idinsumo), ''),
        INM.idpresentacion
    )) as codigo_insumo,
    RTRIM(INM.idpresentacion) as codigo_presentacion,
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto, 
    INM.fisicoalmacen1 as cantidad,
    ISNULL(ID.costo, 0) as costo_insumo,
    ISNULL(IPD.costo, ISNULL(INM.costo, 0)) as costo_presentacion,
    ISNULL(IP.rendimiento, 1) as rendimiento
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
LEFT JOIN insumos I ON I.idinsumo = COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), NULLIF(RTRIM(INM.idinsumo), ''))
LEFT JOIN insumosdetalle ID ON ID.idinsumo = COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), NULLIF(RTRIM(INM.idinsumo), ''))
LEFT JOIN insumospresentacionesdetalle IPD ON IPD.idinsumospresentaciones = RTRIM(INM.idpresentacion)
WHERE INM.folio = {folio_inv}
"""
                    result_ini = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_inv_ini
                    )
                    
                    for r in result_ini:
                        codigo = str(r['codigo_insumo'] or r['codigo_presentacion'] or '').strip()
                        if not codigo:
                            continue
                        
                        cantidad_raw = float(r['cantidad'] or 0)
                        rendimiento = float(r['rendimiento'] or 1)
                        
                        # NORMALIZAR A INSUMOS:
                        # - Si viene de BODEGA (tipo 2): cantidad está en presentaciones → multiplicar × rendimiento
                        # - Si viene de CONSUMO (tipo 1): cantidad ya está en insumos → mantener
                        if es_bodega:
                            cantidad_en_insumos = cantidad_raw * rendimiento
                        else:
                            cantidad_en_insumos = cantidad_raw
                        
                        # Sumar al diccionario (puede haber mismo producto en múltiples inventarios)
                        if codigo in inv_ini_dict:
                            inv_ini_dict[codigo]['cantidad'] += cantidad_en_insumos
                        else:
                            inv_ini_dict[codigo] = {
                                "producto": r['producto'],
                                "cantidad": cantidad_en_insumos,
                                "costo": float(r['costo_presentacion'] or 0),
                                "costo_insumo": float(r['costo_insumo'] or 0),
                                "costo_presentacion": float(r['costo_presentacion'] or 0),
                                "rendimiento": rendimiento
                            }
                    
                    logging.info(f"[AUDITORIA] Folio {folio_inv}: {len(result_ini)} productos procesados")
            
            # PASO 4: Obtener MOVIMIENTOS según tipo de almacén
            # - Solo Bodega: Movimientos = Entradas activas del filtro en Servidores SQL
            # - Solo Consumo: Movimientos = Traspasos entrada - Traspasos salida del período
            # - Mixto: Compras bodega + Traspasos entrada consumo - Salidas traspasos
            
            # Obtener tipos de movimiento activos del servidor (filtros configurados en Servidores SQL)
            tipos_mov_activos = server.get('tipos_movimiento', [])
            
            # Separar tipos de movimiento por tipo (entrada vs salida)
            # Los que empiezan con 'E' son entradas, los que empiezan con 'S' son salidas
            tipos_entrada_activos = [t for t in tipos_mov_activos if t.startswith('E')]
            tipos_salida_activos = [t for t in tipos_mov_activos if t.startswith('S')]
            
            # Tipos específicos
            tipos_entrada_compra = [t for t in tipos_entrada_activos if t in ['EPC', 'ECS', 'EPB', 'EDE', 'EEH', 'ECO', 'ECA', 'EPL', 'EPR']]
            tipos_entrada_traspaso = [t for t in tipos_entrada_activos if t in ['ETR', 'ETA', 'EAL']]
            tipos_salida_traspaso = [t for t in tipos_salida_activos if t in ['STR', 'STA', 'SAL']]
            [t for t in tipos_salida_activos if t in ['SPV', 'SCP', 'SCS']]
            
            logging.info(f"[AUDITORIA] Tipos entrada activos: {tipos_entrada_activos}")
            logging.info(f"[AUDITORIA] Tipos salida activos: {tipos_salida_activos}")
            
            movimientos_dict = {}
            
            if es_solo_bodega:
                # BODEGA: Solo movimientos de entrada activos (EPC, ECS, etc.)
                # NORMALIZAR A INSUMOS: cantidad × rendimiento
                if tipos_entrada_compra:
                    query_mov = f"""
SELECT 
    COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), RTRIM(M.idinsumospresentaciones)) as codigo, 
    SUM(M.cantidad * ISNULL(IP.rendimiento, 1)) as cantidad
FROM movtosalmacen M
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(M.idinsumospresentaciones)
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_entrada_compra])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), RTRIM(M.idinsumospresentaciones))
"""
                    mov_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_mov
                    )
                    for m in mov_result:
                        codigo = str(m['codigo']).strip()
                        movimientos_dict[codigo] = movimientos_dict.get(codigo, 0) + float(m['cantidad'] or 0)
            
            elif es_solo_consumo:
                # CONSUMO: Traspasos entrada - Traspasos salida del período
                # Entradas por traspaso
                if tipos_entrada_traspaso:
                    query_entrada = f"""
SELECT RTRIM(M.idinsumo) as codigo, SUM(M.cantidad) as cantidad
FROM movsinv M
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_entrada_traspaso])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY RTRIM(M.idinsumo)
"""
                    entrada_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_entrada
                    )
                    for e in entrada_result:
                        codigo = str(e['codigo']).strip()
                        movimientos_dict[codigo] = movimientos_dict.get(codigo, 0) + float(e['cantidad'] or 0)
                
                # Salidas por traspaso (restar)
                if tipos_salida_traspaso:
                    query_salida = f"""
SELECT RTRIM(M.idinsumo) as codigo, SUM(M.cantidad) as cantidad
FROM movsinv M
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_salida_traspaso])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY RTRIM(M.idinsumo)
"""
                    salida_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_salida
                    )
                    for s in salida_result:
                        codigo = str(s['codigo']).strip()
                        # Las salidas restan
                        movimientos_dict[codigo] = movimientos_dict.get(codigo, 0) - float(s['cantidad'] or 0)
            
            else:  # es_mixto
                # MIXTO: Compras bodega + Traspasos entrada consumo
                # NORMALIZAR A INSUMOS: cantidad × rendimiento
                if tipos_entrada_compra:
                    query_mov = f"""
SELECT 
    COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), RTRIM(M.idinsumospresentaciones)) as codigo, 
    SUM(M.cantidad * ISNULL(IP.rendimiento, 1)) as cantidad
FROM movtosalmacen M
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(M.idinsumospresentaciones)
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_entrada_compra])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), RTRIM(M.idinsumospresentaciones))
"""
                    mov_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_mov
                    )
                    for m in mov_result:
                        codigo = str(m['codigo']).strip()
                        movimientos_dict[codigo] = movimientos_dict.get(codigo, 0) + float(m['cantidad'] or 0)
            
            logging.info(f"[AUDITORIA] Movimientos encontrados: {len(movimientos_dict)}")
            
            # PASO 5: Obtener consumos/salidas según tipo de almacén
            # - Solo Bodega: Salidas = Tipos de salida activos en filtros (STR, etc.)
            # - Solo Consumo: Salidas = Ventas (SPV) o tipos de salida consumo activos
            # - Mixto: Ventas (el consumo final)
            
            consumos_dict = {}
            
            if es_solo_bodega:
                # Para bodega, las salidas son traspasos a consumo (usa movtosalmacen)
                # NORMALIZAR A INSUMOS: cantidad × rendimiento
                if tipos_salida_traspaso:
                    query_salidas = f"""
SELECT 
    COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), RTRIM(M.idinsumospresentaciones)) as codigo, 
    SUM(M.cantidad * ISNULL(IP.rendimiento, 1)) as cantidad
FROM movtosalmacen M
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(M.idinsumospresentaciones)
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_salida_traspaso])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), RTRIM(M.idinsumospresentaciones))
"""
                    salidas_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_salidas
                    )
                    for s in salidas_result:
                        codigo = str(s['codigo']).strip()
                        consumos_dict[codigo] = float(s['cantidad'] or 0)
            else:
                # Para consumo o mixto, las salidas son ventas
                query_consumos = f"""
SELECT C.idinsumo as codigo, SUM(CD.cantidad * C.cantidad) as consumo
FROM cheqdet CD
INNER JOIN cheques CH ON CH.folio = CD.foliodet
INNER JOIN turnos T ON T.idturno = CH.idturno
INNER JOIN costos C ON C.idproducto = CD.idproducto
WHERE T.apertura >= '{fecha_ini_sql}'
    AND T.apertura <= '{fecha_fin_sql} 23:59:59'
    AND CH.cancelado = 0
GROUP BY C.idinsumo
"""
                consumos_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_consumos
                )
                for c in consumos_result:
                    codigo = str(c['codigo']).strip()
                    consumos_dict[codigo] = float(c['consumo'] or 0)
            
            logging.info(f"[AUDITORIA] Consumos/Salidas encontradas: {len(consumos_dict)}")
            
            # PASO 6: Obtener inventario final (físico del día del pedido)
            # NUEVO: Procesar múltiples folios y normalizar TODO a INSUMOS
            inv_fin_dict = {}
            if request.inventario_fisico_actual:
                # Captura manual del inventario físico del día del pedido
                inv_fin_dict = {str(item['codigo']).strip(): {
                    "producto": item.get('producto', ''),
                    "cantidad": float(item.get('cantidad', 0)),
                    "costo": float(item.get('costo', 0))
                } for item in request.inventario_fisico_actual}
            else:
                # Combinar folios (legacy + nuevo formato)
                folios_finales = []
                if request.folios_inv_final:
                    folios_finales = request.folios_inv_final
                elif request.folio_inv_final:
                    folios_finales = [request.folio_inv_final]
                
                if folios_finales:
                    for folio_inv in folios_finales:
                        # Determinar el tipo de almacén de este inventario específico
                        query_tipo_alm = f"""
SELECT A.tipo, A.nombre, INV.idalmacen1
FROM invfisico INV
LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
WHERE INV.folio = {folio_inv}
"""
                        tipo_result = execute_sql_query(
                            server['host'], server['port'], server['database'],
                            server['username'], server['password'], query_tipo_alm
                        )
                        
                        tipo_almacen = tipo_result[0]['tipo'] if tipo_result else 1
                        es_bodega = tipo_almacen == 2
                        
                        logging.info(f"[AUDITORIA] Procesando inv final folio={folio_inv}, tipo_almacen={tipo_almacen}, es_bodega={es_bodega}")
                        
                        query_inv_fin = f"""
SELECT 
    RTRIM(COALESCE(
        NULLIF(RTRIM(IP.idinsumo), ''),
        NULLIF(RTRIM(INM.idinsumo), ''),
        INM.idpresentacion
    )) as codigo_insumo,
    RTRIM(INM.idpresentacion) as codigo_presentacion,
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto,
    INM.fisicoalmacen1 as cantidad, 
    ISNULL(ID.costo, 0) as costo_insumo,
    ISNULL(IPD.costo, ISNULL(INM.costo, 0)) as costo_presentacion,
    ISNULL(IP.rendimiento, 1) as rendimiento
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
LEFT JOIN insumos I ON I.idinsumo = COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), NULLIF(RTRIM(INM.idinsumo), ''))
LEFT JOIN insumosdetalle ID ON ID.idinsumo = COALESCE(NULLIF(RTRIM(IP.idinsumo), ''), NULLIF(RTRIM(INM.idinsumo), ''))
LEFT JOIN insumospresentacionesdetalle IPD ON IPD.idinsumospresentaciones = RTRIM(INM.idpresentacion)
WHERE INM.folio = {folio_inv}
"""
                        result_fin = execute_sql_query(
                            server['host'], server['port'], server['database'],
                            server['username'], server['password'], query_inv_fin
                        )
                        
                        for r in result_fin:
                            codigo = str(r['codigo_insumo'] or r['codigo_presentacion'] or '').strip()
                            if not codigo:
                                continue
                            
                            cantidad_raw = float(r['cantidad'] or 0)
                            rendimiento = float(r['rendimiento'] or 1)
                            
                            # NORMALIZAR A INSUMOS
                            if es_bodega:
                                cantidad_en_insumos = cantidad_raw * rendimiento
                            else:
                                cantidad_en_insumos = cantidad_raw
                            
                            if codigo in inv_fin_dict:
                                inv_fin_dict[codigo]['cantidad'] += cantidad_en_insumos
                            else:
                                inv_fin_dict[codigo] = {
                                    "producto": r['producto'],
                                    "cantidad": cantidad_en_insumos,
                                    "costo": float(r['costo_presentacion'] or 0),
                                    "costo_insumo": float(r['costo_insumo'] or 0),
                                    "costo_presentacion": float(r['costo_presentacion'] or 0),
                                    "rendimiento": rendimiento
                                }
                        
                        logging.info(f"[AUDITORIA] Folio final {folio_inv}: {len(result_fin)} productos procesados")
                elif request.inventario_manual:
                    inv_fin_dict = {str(item['codigo']).strip(): {
                        "producto": item.get('producto', ''),
                        "cantidad": float(item.get('cantidad', 0)),
                        "costo": float(item.get('costo', 0))
                    } for item in request.inventario_manual}
            
            # PASO 7: Calcular diferencias y días de consumo
            # FILTRAR SOLO POR SKUs DE LA REQUISICIÓN (si solo_skus_requisicion está activo)
            from datetime import datetime
            dias_periodo = (datetime.strptime(fecha_fin, '%Y-%m-%d') - datetime.strptime(fecha_ini, '%Y-%m-%d')).days
            if dias_periodo <= 0:
                dias_periodo = 1
            
            # Determinar qué procesar: usar requi_list para mantener orden por proveedor-pedido
            if request.solo_skus_requisicion and requi_list:
                # Procesar en orden por proveedor-pedido usando la lista de requisiciones
                logging.info(f"[AUDITORIA] Procesando {len(requi_list)} líneas de pedido por proveedor-pedido")
                
                for item in requi_list:
                    codigo = item['codigo']
                    inv_inicial = inv_ini_dict.get(codigo, {}).get('cantidad', 0)
                    movimientos = movimientos_dict.get(codigo, 0)
                    consumos = consumos_dict.get(codigo, 0)
                    inv_fisico = inv_fin_dict.get(codigo, {}).get('cantidad', 0)
                    costo = inv_ini_dict.get(codigo, {}).get('costo', 0) or inv_fin_dict.get(codigo, {}).get('costo', 0) or item.get('costo', 0)
                    
                    producto = item.get('producto', '')
                    if not producto:
                        producto = inv_ini_dict.get(codigo, {}).get('producto', '') or inv_fin_dict.get(codigo, {}).get('producto', '')
                    
                    cantidad_pedido = item.get('cantidad', 0)
                    proveedor = item.get('proveedor', '')
                    folio_pedido = item.get('folio_pedido', '')
                    rendimiento = item.get('rendimiento', 1)
                    unidad = item.get('unidad', '')
                    
                    # Existencia teórica = inicial + movimientos - consumos
                    existencia_teorica = inv_inicial + movimientos - consumos
                    diferencia = inv_fisico - existencia_teorica
                    importe_dif = diferencia * costo
                    
                    # Consumo diario promedio
                    consumo_diario = abs(consumos) / dias_periodo if dias_periodo > 0 else 0
                    dias_inv = inv_fisico / consumo_diario if consumo_diario > 0 else 999
                    
                    # Días objetivo para este SKU (personalizado o default)
                    dias_objetivo_sku = 10  # Default
                    if request.dias_objetivo_por_sku and codigo in request.dias_objetivo_por_sku:
                        dias_objetivo_sku = request.dias_objetivo_por_sku[codigo]
                    elif hasattr(request, 'dias_objetivo_default') and request.dias_objetivo_default:
                        dias_objetivo_sku = request.dias_objetivo_default
                    
                    debe_comprar = dias_inv < dias_objetivo_sku
                    
                    resultados.append({
                        "codigo": codigo,
                        "producto": producto or f"SKU: {codigo}",
                        "proveedor": proveedor,
                        "folio_pedido": folio_pedido,
                        "inv_inicial": inv_inicial,
                        "movimientos": movimientos,
                        "entradas": movimientos,
                        "consumos": abs(consumos),
                        "existencia_teorica": round(existencia_teorica, 2),
                        "inv_fisico": inv_fisico,
                        "diferencia": round(diferencia, 2),
                        "costo": costo,
                        "costo_insumo": item.get('costo_insumo', 0),
                        "costo_presentacion": item.get('costo_presentacion', costo),
                        "importe_diferencia": round(importe_dif, 2),
                        "tipo_diferencia": "favor" if diferencia >= 0 else "contra",
                        "consumo_diario": round(consumo_diario, 2),
                        "dias_inventario": round(dias_inv, 1) if dias_inv < 999 else "N/A",
                        "dias_objetivo": dias_objetivo_sku,
                        "cantidad_pedido": cantidad_pedido,
                        "debe_comprar": debe_comprar,
                        "recomendacion": "COMPRAR" if debe_comprar and cantidad_pedido > 0 else "OK" if not debe_comprar else "SIN PEDIDO",
                        "rendimiento": rendimiento,
                        "unidad": unidad
                    })
                    
                    resumen["total_teorico"] += existencia_teorica * costo
                    resumen["total_fisico"] += inv_fisico * costo
                    resumen["total_diferencia"] += importe_dif
                    if diferencia >= 0:
                        resumen["productos_favor"] += 1
                        resumen["importe_favor"] += importe_dif
                    else:
                        resumen["productos_contra"] += 1
                        resumen["importe_contra"] += abs(importe_dif)
            else:
                # Todos los códigos encontrados (sin orden específico)
                todos_codigos = set(inv_ini_dict.keys()) | set(movimientos_dict.keys()) | set(consumos_dict.keys()) | set(inv_fin_dict.keys())
                
                for codigo in todos_codigos:
                    inv_inicial = inv_ini_dict.get(codigo, {}).get('cantidad', 0)
                    movimientos = movimientos_dict.get(codigo, 0)  # Entradas según tipo de almacén
                    consumos = consumos_dict.get(codigo, 0)
                    inv_fisico = inv_fin_dict.get(codigo, {}).get('cantidad', 0)
                    costo = inv_ini_dict.get(codigo, {}).get('costo', 0) or inv_fin_dict.get(codigo, {}).get('costo', 0)
                    
                    # Obtener producto desde requisición primero, luego de inventarios
                    producto = requi_dict.get(codigo, {}).get('producto', '') if isinstance(requi_dict.get(codigo), dict) else ''
                    if not producto:
                        producto = inv_ini_dict.get(codigo, {}).get('producto', '') or inv_fin_dict.get(codigo, {}).get('producto', '')
                    
                    cantidad_pedido = requi_dict.get(codigo, {}).get('cantidad', 0) if isinstance(requi_dict.get(codigo), dict) else requi_dict.get(codigo, 0)
                    
                    # Obtener proveedor de la requisición
                    proveedor = requi_dict.get(codigo, {}).get('proveedor', '') if isinstance(requi_dict.get(codigo), dict) else ''
                    
                    # Existencia teórica = inicial + movimientos - consumos
                    existencia_teorica = inv_inicial + movimientos - consumos
                    
                    # Diferencia = físico - teórico
                    diferencia = inv_fisico - existencia_teorica
                    importe_dif = diferencia * costo
                    
                    # Consumo diario promedio
                    consumo_diario = abs(consumos) / dias_periodo if dias_periodo > 0 else 0
                    
                    # Días de inventario disponible
                    dias_inv = inv_fisico / consumo_diario if consumo_diario > 0 else 999
                    
                    # Días objetivo para este SKU (personalizado o default)
                    dias_objetivo_sku = 10  # Default
                    if request.dias_objetivo_por_sku and codigo in request.dias_objetivo_por_sku:
                        dias_objetivo_sku = request.dias_objetivo_por_sku[codigo]
                    elif hasattr(request, 'dias_objetivo_default') and request.dias_objetivo_default:
                        dias_objetivo_sku = request.dias_objetivo_default
                    
                    # ¿Debe comprar?
                    debe_comprar = dias_inv < dias_objetivo_sku
                    
                    # Obtener rendimiento y unidad de la requisición
                    rendimiento = requi_dict.get(codigo, {}).get('rendimiento', 1) if isinstance(requi_dict.get(codigo), dict) else 1
                    unidad = requi_dict.get(codigo, {}).get('unidad', '') if isinstance(requi_dict.get(codigo), dict) else ''
                    
                    # Incluir producto si tiene nombre o está en la requisición
                    if producto or codigo in skus_requisicion:
                        # Obtener folio_pedido si existe
                        folio_pedido = requi_dict.get(codigo, {}).get('folio_pedido', '') if isinstance(requi_dict.get(codigo), dict) else ''
                        costo_insumo = requi_dict.get(codigo, {}).get('costo_insumo', 0) if isinstance(requi_dict.get(codigo), dict) else 0
                        costo_presentacion = requi_dict.get(codigo, {}).get('costo_presentacion', costo) if isinstance(requi_dict.get(codigo), dict) else costo
                        
                        resultados.append({
                            "codigo": codigo,
                            "producto": producto or f"SKU: {codigo}",
                            "proveedor": proveedor,
                            "folio_pedido": folio_pedido,
                            "inv_inicial": inv_inicial,
                            "movimientos": movimientos,
                            "entradas": movimientos,
                            "consumos": abs(consumos),
                            "existencia_teorica": round(existencia_teorica, 2),
                            "inv_fisico": inv_fisico,
                            "diferencia": round(diferencia, 2),
                            "costo": costo,
                            "costo_insumo": costo_insumo,
                            "costo_presentacion": costo_presentacion,
                            "importe_diferencia": round(importe_dif, 2),
                            "tipo_diferencia": "favor" if diferencia >= 0 else "contra",
                            "consumo_diario": round(consumo_diario, 2),
                            "dias_inventario": round(dias_inv, 1) if dias_inv < 999 else "N/A",
                            "dias_objetivo": dias_objetivo_sku,
                            "cantidad_pedido": cantidad_pedido,
                            "debe_comprar": debe_comprar,
                            "recomendacion": "COMPRAR" if debe_comprar and cantidad_pedido > 0 else "OK" if not debe_comprar else "SIN PEDIDO",
                            "rendimiento": rendimiento,
                            "unidad": unidad
                        })
                        
                        resumen["total_teorico"] += existencia_teorica * costo
                        resumen["total_fisico"] += inv_fisico * costo
                        resumen["total_diferencia"] += importe_dif
                        if diferencia >= 0:
                            resumen["productos_favor"] += 1
                            resumen["importe_favor"] += importe_dif
                        else:
                            resumen["productos_contra"] += 1
                            resumen["importe_contra"] += abs(importe_dif)
            
            resumen["requiere_acta"] = resumen["productos_contra"] > 0 or resumen["importe_contra"] > 100
            
            # Solo ordenar por importe cuando NO se filtra por SKUs de requisición
            # (cuando se filtra, ya viene ordenado por proveedor-pedido)
            if not (request.solo_skus_requisicion and requi_list):
                resultados = sorted(resultados, key=lambda x: x['importe_diferencia'])
        
        elif is_mpro_system(server.get('system_type')):
            # Lógica similar para MPRO
            # TODO: Implementar para MPRO si es necesario
            pass
        
        return {
            "resultados": resultados,
            "resumen": resumen,
            "periodo": {"inicio": fecha_ini, "fin": fecha_fin, "dias": dias_periodo if 'dias_periodo' in dir() else 0},
            "folios_requisiciones": folios_req
        }
        
    except Exception as e:
        logging.error(f"[AUDITORIA] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= DETALLE DE MOVIMIENTOS =============

class DetalleMovimientosRequest(BaseModel):
    server_id: str
    sucursal: str
    codigo: str
    fecha_inicio: str
    fecha_fin: str
    almacenes: Optional[List[str]] = None


# =============================================================================
# INVENTARIOS PROVISIONALES - CAPTURA MANUAL
# Tabla: EDARSAHUB.dbo.Auditoria_Inventario_Provisional
# =============================================================================

class InventarioProvisionalItem(BaseModel):
    codigo_producto: str
    nombre_producto: Optional[str] = None
    cantidad: float
    costo_unitario: Optional[float] = 0
    almacen: Optional[str] = None
    notas: Optional[str] = None

class InventarioProvisionalRequest(BaseModel):
    unidad_negocio_id: str
    unidad_negocio_nombre: Optional[str] = None
    server_id: str
    sucursal: Optional[str] = None
    fecha_auditoria: Optional[str] = None
    items: List[InventarioProvisionalItem]


@api_router.post("/compras/inventarios-provisionales")
async def guardar_inventario_provisional(
    request: InventarioProvisionalRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Guarda inventarios provisionales (captura manual) en EDARSAHUB.
    Permite persistir la captura manual del inventario físico antes de ejecutar la auditoría.
    """
    from modules.comercial.service import EDARSAHUB_TABLERO_CONFIG
    
    try:
        usuario_id = current_user.get('_sql_usuario_id', current_user.get('id'))
        usuario_email = current_user.get('email', 'unknown')
        
        conn = pymssql.connect(
            server=EDARSAHUB_TABLERO_CONFIG['host'],
            user=EDARSAHUB_TABLERO_CONFIG['username'],
            password=EDARSAHUB_TABLERO_CONFIG['password'],
            database=EDARSAHUB_TABLERO_CONFIG['database'],
            port=EDARSAHUB_TABLERO_CONFIG['port'],
            timeout=30
        )
        cursor = conn.cursor()
        
        items_guardados = 0
        for item in request.items:
            total = item.cantidad * (item.costo_unitario or 0)
            cursor.execute("""
                INSERT INTO Auditoria_Inventario_Provisional 
                (unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal, 
                 fecha_auditoria, usuario_id, usuario_email,
                 codigo_producto, nombre_producto, cantidad, costo_unitario, total,
                 almacen, notas, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PROVISIONAL')
            """, (
                request.unidad_negocio_id,
                request.unidad_negocio_nombre,
                request.server_id,
                request.sucursal,
                request.fecha_auditoria,
                usuario_id,
                usuario_email,
                item.codigo_producto,
                item.nombre_producto,
                item.cantidad,
                item.costo_unitario or 0,
                total,
                item.almacen,
                item.notas
            ))
            items_guardados += 1
        
        conn.commit()
        conn.close()
        
        logging.info(f"[INV-PROVISIONAL] Guardados {items_guardados} items por {usuario_email}")
        
        return {
            "success": True,
            "message": f"Guardados {items_guardados} productos provisionales",
            "items_guardados": items_guardados
        }
        
    except Exception as e:
        logging.error(f"[INV-PROVISIONAL] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/compras/inventarios-provisionales/{unidad_negocio_id}")
async def obtener_inventarios_provisionales(
    unidad_negocio_id: str,
    fecha_auditoria: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene inventarios provisionales guardados para una unidad de negocio.
    """
    from modules.comercial.service import EDARSAHUB_TABLERO_CONFIG
    
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_TABLERO_CONFIG['host'],
            user=EDARSAHUB_TABLERO_CONFIG['username'],
            password=EDARSAHUB_TABLERO_CONFIG['password'],
            database=EDARSAHUB_TABLERO_CONFIG['database'],
            port=EDARSAHUB_TABLERO_CONFIG['port'],
            timeout=30
        )
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal,
                   fecha_captura, fecha_auditoria, usuario_email,
                   codigo_producto, nombre_producto, cantidad, costo_unitario, total,
                   almacen, notas, estado, auditoria_ejecutada
            FROM Auditoria_Inventario_Provisional
            WHERE unidad_negocio_id = %s AND estado = 'PROVISIONAL'
        """
        params = [unidad_negocio_id]
        
        if fecha_auditoria:
            query += " AND fecha_auditoria = %s"
            params.append(fecha_auditoria)
        
        query += " ORDER BY fecha_captura DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir datetime a string
        for row in rows:
            if row.get('fecha_captura'):
                row['fecha_captura'] = str(row['fecha_captura'])
            if row.get('fecha_auditoria'):
                row['fecha_auditoria'] = str(row['fecha_auditoria'])
        
        return {
            "success": True,
            "data": rows,
            "total": len(rows)
        }
        
    except Exception as e:
        logging.error(f"[INV-PROVISIONAL] Error obteniendo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/compras/inventarios-provisionales/{item_id}")
async def eliminar_inventario_provisional(
    item_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Elimina un item del inventario provisional.
    """
    from modules.comercial.service import EDARSAHUB_TABLERO_CONFIG
    
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_TABLERO_CONFIG['host'],
            user=EDARSAHUB_TABLERO_CONFIG['username'],
            password=EDARSAHUB_TABLERO_CONFIG['password'],
            database=EDARSAHUB_TABLERO_CONFIG['database'],
            port=EDARSAHUB_TABLERO_CONFIG['port'],
            timeout=30
        )
        cursor = conn.cursor()
        
        # Verificar que existe y está en estado PROVISIONAL
        cursor.execute("""
            DELETE FROM Auditoria_Inventario_Provisional 
            WHERE id = %s AND estado = 'PROVISIONAL'
        """, (item_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            logging.info(f"[INV-PROVISIONAL] Eliminado item {item_id} por {current_user.get('email')}")
            return {"success": True, "message": "Item eliminado correctamente"}
        else:
            raise HTTPException(status_code=404, detail="Item no encontrado o ya procesado")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[INV-PROVISIONAL] Error eliminando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/compras/inventarios-provisionales/limpiar/{unidad_negocio_id}")
async def limpiar_inventarios_provisionales(
    unidad_negocio_id: str,
    fecha_auditoria: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Limpia todos los inventarios provisionales de una unidad (para una fecha específica o todos).
    """
    from modules.comercial.service import EDARSAHUB_TABLERO_CONFIG
    
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_TABLERO_CONFIG['host'],
            user=EDARSAHUB_TABLERO_CONFIG['username'],
            password=EDARSAHUB_TABLERO_CONFIG['password'],
            database=EDARSAHUB_TABLERO_CONFIG['database'],
            port=EDARSAHUB_TABLERO_CONFIG['port'],
            timeout=30
        )
        cursor = conn.cursor()
        
        if fecha_auditoria:
            cursor.execute("""
                DELETE FROM Auditoria_Inventario_Provisional 
                WHERE unidad_negocio_id = %s AND fecha_auditoria = %s AND estado = 'PROVISIONAL'
            """, (unidad_negocio_id, fecha_auditoria))
        else:
            cursor.execute("""
                DELETE FROM Auditoria_Inventario_Provisional 
                WHERE unidad_negocio_id = %s AND estado = 'PROVISIONAL'
            """, (unidad_negocio_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"[INV-PROVISIONAL] Limpiados {rows_affected} items de {unidad_negocio_id} por {current_user.get('email')}")
        
        return {
            "success": True,
            "message": f"Se eliminaron {rows_affected} items provisionales",
            "items_eliminados": rows_affected
        }
        
    except Exception as e:
        logging.error(f"[INV-PROVISIONAL] Error limpiando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/compras/detalle-movimientos")
async def obtener_detalle_movimientos_post(request: DetalleMovimientosRequest, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el detalle de movimientos de un producto específico en un período.
    Muestra cada movimiento individual que compone el total.
    """
    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Formatear fechas para SQL
    fecha_ini = request.fecha_inicio.replace('-', '') if request.fecha_inicio else ''
    fecha_fin = request.fecha_fin.replace('-', '') if request.fecha_fin else ''
    
    if not fecha_ini or not fecha_fin:
        return {"movimientos": [], "totales": {"entradas": 0, "salidas": 0, "neto": 0}, "error": "Fechas no válidas"}
    
    movimientos = []
    totales = {"entradas": 0, "salidas": 0, "neto": 0}
    
    # Reintentos para manejar conexiones inestables
    max_retries = 2
    last_error = None
    
    # Limpiar código de espacios
    codigo_limpio = request.codigo.strip()
    
    # Si el código empieza con letra (posible prefijo de almacén A/B/C), también probar sin él
    codigo_sin_prefijo = codigo_limpio[1:] if codigo_limpio and codigo_limpio[0].isalpha() else codigo_limpio
    
    logging.info(f"[DETALLE_MOV] Buscando movimientos para código: '{codigo_limpio}' (sin prefijo: '{codigo_sin_prefijo}'), fechas: {fecha_ini} a {fecha_fin}")
    
    for retry in range(max_retries):
        try:
            if is_softrestaurant_system(server.get('system_type')):
                # Obtener movimientos de presentaciones (movtosalmacen)
                # Buscar con código completo Y sin prefijo (por si A/B es prefijo de almacén)
                query_pres = f"""
SELECT 
    M.fecha,
    RTRIM(LTRIM(M.idconcepto)) as concepto,
    C.descripcion as descripcion_concepto,
    M.cantidad,
    A.nombre as almacen,
    ISNULL(CAST(M.movto AS VARCHAR(50)), '') as referencia,
    CASE WHEN C.tipo = 1 THEN 'E' ELSE 'S' END as tipo
FROM movtosalmacen M
LEFT JOIN conceptos C ON C.idconcepto = M.idconcepto
LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
WHERE (RTRIM(LTRIM(M.idinsumospresentaciones)) = '{codigo_limpio}' 
    OR RTRIM(LTRIM(M.idinsumospresentaciones)) = '{codigo_sin_prefijo}')
    AND M.fecha >= '{fecha_ini}'
    AND M.fecha <= '{fecha_fin} 23:59:59'
ORDER BY M.fecha DESC
"""
                logging.info(f"[DETALLE_MOV] Query presentaciones: {query_pres[:200]}...")
                result_pres = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_pres
                )
                logging.info(f"[DETALLE_MOV] Resultados presentaciones: {len(result_pres)}")
                
                for m in result_pres:
                    cantidad = float(m.get('cantidad', 0) or 0)
                    tipo = m.get('tipo', 'E')
                    
                    movimientos.append({
                        "fecha": m['fecha'].isoformat() if hasattr(m['fecha'], 'isoformat') else str(m['fecha']),
                        "concepto": m['concepto'],
                        "descripcion": m.get('descripcion_concepto', ''),
                        "cantidad": cantidad if tipo == 'E' else -cantidad,
                        "almacen": m.get('almacen', ''),
                        "referencia": str(m.get('referencia', '')),
                        "tipo": tipo
                    })
                    
                    if tipo == 'E':
                        totales["entradas"] += cantidad
                    else:
                        totales["salidas"] += cantidad
                
                # También buscar en movsinv (para insumos)
                query_ins = f"""
SELECT 
    M.fecha,
    RTRIM(LTRIM(M.idconcepto)) as concepto,
    C.descripcion as descripcion_concepto,
    M.cantidad,
    A.nombre as almacen,
    ISNULL(CAST(M.folio AS VARCHAR(50)), '') as referencia,
    CASE WHEN C.tipo = 1 THEN 'E' ELSE 'S' END as tipo
FROM movsinv M
LEFT JOIN conceptos C ON C.idconcepto = M.idconcepto
LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
WHERE (RTRIM(LTRIM(M.idinsumo)) = '{codigo_limpio}'
    OR RTRIM(LTRIM(M.idinsumo)) = '{codigo_sin_prefijo}')
    AND M.fecha >= '{fecha_ini}'
    AND M.fecha <= '{fecha_fin} 23:59:59'
ORDER BY M.fecha DESC
"""
                logging.info(f"[DETALLE_MOV] Query insumos: {query_ins[:200]}...")
                result_ins = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ins
                )
                logging.info(f"[DETALLE_MOV] Resultados insumos: {len(result_ins)}")
                
                for m in result_ins:
                    cantidad = float(m.get('cantidad', 0) or 0)
                    tipo = m.get('tipo', 'E')
                    
                    movimientos.append({
                        "fecha": m['fecha'].isoformat() if hasattr(m['fecha'], 'isoformat') else str(m['fecha']),
                        "concepto": m['concepto'],
                        "descripcion": m.get('descripcion_concepto', ''),
                        "cantidad": cantidad if tipo == 'E' else -cantidad,
                        "almacen": m.get('almacen', ''),
                        "referencia": str(m.get('referencia', '')),
                        "tipo": tipo
                    })
                    
                    if tipo == 'E':
                        totales["entradas"] += cantidad
                    else:
                        totales["salidas"] += cantidad
                
                # Ordenar por fecha
                movimientos.sort(key=lambda x: x['fecha'], reverse=True)
                
                totales["neto"] = totales["entradas"] - totales["salidas"]
                
                return {
                    "movimientos": movimientos,
                    "totales": totales
                }
            else:
                # Para otros sistemas (MPRO, etc.), retornar vacío por ahora
                return {
                    "movimientos": [],
                    "totales": {"entradas": 0, "salidas": 0, "neto": 0},
                    "error": f"Sistema {server['system_type']} no soportado para detalle de movimientos"
                }
            
        except Exception as e:
            last_error = str(e)
            logging.warning(f"[DETALLE_MOV] Intento {retry + 1}/{max_retries} falló: {e}")
            if retry < max_retries - 1:
                import asyncio
                await asyncio.sleep(1)  # Esperar 1 segundo antes de reintentar
            continue
    
    # Si llegamos aquí, todos los reintentos fallaron
    logging.error(f"[DETALLE_MOV] Todos los reintentos fallaron: {last_error}")
    
    # Devolver respuesta con error pero sin hacer crash
    if "unavailable" in str(last_error).lower() or "timeout" in str(last_error).lower():
        return {
            "movimientos": [],
            "totales": {"entradas": 0, "salidas": 0, "neto": 0},
            "error": "El servidor externo no está disponible. Intente nuevamente en unos momentos."
        }
    
    return {
        "movimientos": [],
        "totales": {"entradas": 0, "salidas": 0, "neto": 0},
        "error": f"Error al obtener movimientos: {last_error[:100]}"
    }


class DetalleConsumosRequest(BaseModel):
    server_id: str
    sucursal: str
    codigo: str
    fecha_inicio: str
    fecha_fin: str
    almacenes: Optional[List[str]] = None

@api_router.post("/compras/detalle-consumos")
async def obtener_detalle_consumos_post(request: DetalleConsumosRequest, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el detalle de consumos/ventas de un producto específico en un período.
    Para SoftRestaurant: ventas directas o a través de recetas.
    """
    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Formatear fechas para SQL
    fecha_ini = request.fecha_inicio.replace('-', '') if request.fecha_inicio else ''
    fecha_fin = request.fecha_fin.replace('-', '') if request.fecha_fin else ''
    
    if not fecha_ini or not fecha_fin:
        return {"consumos": [], "totales": {"total": 0}, "error": "Fechas no válidas"}
    
    # Limpiar código de espacios y posibles prefijos
    codigo_limpio = request.codigo.strip()
    codigo_sin_prefijo = codigo_limpio[1:] if codigo_limpio and codigo_limpio[0].isalpha() else codigo_limpio
    
    consumos = []
    total_consumo = 0
    
    try:
        if is_softrestaurant_system(server.get('system_type')):
            logging.info(f"[DETALLE_CONSUMOS] Buscando consumos para código: '{codigo_limpio}' (sin prefijo: '{codigo_sin_prefijo}'), fechas: {fecha_ini} a {fecha_fin}")
            
            # Buscar ventas donde este insumo está en la receta de un producto vendido
            # cheqdet tiene los productos vendidos
            # recetasalmacenes tiene la receta (qué insumos usa cada producto)
            # Consumo = cantidad vendida × cantidad del insumo en la receta
            query_ventas = f"""
SELECT 
    C.fecha,
    C.folio as documento,
    P.descripcion as producto_vendido,
    CD.cantidad as cantidad_vendida,
    R.cantidad as cantidad_receta,
    (CD.cantidad * R.cantidad) as consumo_total,
    A.nombre as almacen
FROM cheques C
INNER JOIN cheqdet CD ON CD.foliodet = C.folio
INNER JOIN productos P ON P.idproducto = CD.idproducto
INNER JOIN recetasalmacenes R ON R.idproducto = CD.idproducto
LEFT JOIN almacen A ON A.idalmacen = R.idalmacen
WHERE (RTRIM(LTRIM(R.idinsumo)) = '{codigo_limpio}' OR RTRIM(LTRIM(R.idinsumo)) = '{codigo_sin_prefijo}')
    AND C.fecha >= '{fecha_ini}'
    AND C.fecha <= '{fecha_fin} 23:59:59'
    AND C.statusfactura <> 'CA'
ORDER BY C.fecha DESC
"""
            logging.info(f"[DETALLE_CONSUMOS] Query: {query_ventas[:200]}...")
            result_ventas = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas
            )
            logging.info(f"[DETALLE_CONSUMOS] Resultados: {len(result_ventas)}")
            
            for r in result_ventas:
                consumo = float(r.get('consumo_total', 0) or 0)
                consumos.append({
                    "fecha": r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha']),
                    "documento": str(r.get('documento', '')),
                    "producto_vendido": r.get('producto_vendido', ''),
                    "cantidad_vendida": float(r.get('cantidad_vendida', 0) or 0),
                    "cantidad_receta": float(r.get('cantidad_receta', 0) or 0),
                    "consumo": consumo,
                    "almacen": r.get('almacen', '')
                })
                total_consumo += consumo
            
            return {
                "consumos": consumos,
                "totales": {"total": round(total_consumo, 4)}
            }
        
        return {
            "consumos": [],
            "totales": {"total": 0},
            "error": f"Sistema {server['system_type']} no soportado para detalle de consumos"
        }
        
    except Exception as e:
        logging.error(f"[DETALLE_CONSUMOS] Error: {str(e)}")
        if "unavailable" in str(e).lower() or "timeout" in str(e).lower():
            return {
                "consumos": [],
                "totales": {"total": 0},
                "error": "El servidor externo no está disponible. Intente nuevamente en unos momentos."
            }
        return {
            "consumos": [],
            "totales": {"total": 0},
            "error": f"Error al obtener consumos: {str(e)[:100]}"
        }


# ============= ANÁLISIS DE COMPRAS - ENDPOINTS =============

class AnalisisComprasRequest(BaseModel):
    server_id: str
    sucursal: str
    anio: Optional[int] = None  # Mantener para compatibilidad
    anios: Optional[List[str]] = None  # Nuevo: múltiples años
    meses: List[str]

@api_router.get("/compras/dashboard/{server_id}")
async def obtener_dashboard_compras(
    server_id: str, 
    sucursal: str = None, 
    meses: str = Query(default=""),  # "01,02,03" - Lista de meses separados por coma
    anio: str = Query(default=""),  # "2025" - Año específico (compatibilidad)
    anios: str = Query(default=""),  # "2025,2024" - Múltiples años
    periodo_mes: str = Query(default="actual"),  # Mantener para compatibilidad
    periodo_ano: str = Query(default="actual"),  # Mantener para compatibilidad
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene KPIs y alertas para el dashboard de compras. Soporta multiselección de meses y años."""
    # FASE 3.1: Validar acceso por empresa
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    
    if not sucursal:
        return {"kpis": {"total_compras_mes": 0, "requisiciones_pendientes": 0, "proveedores_activos": 0, "alertas_activas": 0}, "alertas": [], "top_proveedores": []}
    
    try:
        # Calcular fechas según período seleccionado
        from datetime import datetime
        now = datetime.now()
        
        # Obtener lista de años (priorizar 'anios' sobre 'anio')
        if anios:
            lista_anios = [int(a.strip()) for a in anios.split(',') if a.strip()]
        elif anio:
            lista_anios = [int(anio)]
        else:
            lista_anios = None
        
        # Nueva lógica: meses y años específicos
        if meses and lista_anios:
            lista_meses = [m.strip() for m in meses.split(',') if m.strip()]
            year = max(lista_anios)  # Usar el año más reciente
            
            mes_min = min([int(m) for m in lista_meses])
            mes_max = max([int(m) for m in lista_meses])
            
            fecha_inicio = f"{year}-{str(mes_min).zfill(2)}-01"
            
            # Último día del mes máximo + 1 para el filtro < fecha_fin
            if mes_max == 12:
                fecha_fin = f"{year + 1}-01-01"
            else:
                fecha_fin = f"{year}-{str(mes_max + 1).zfill(2)}-01"
            
            logging.info(f"Dashboard Compras (multiselección): Meses: {lista_meses} Año: {year} ({fecha_inicio} a {fecha_fin})")
        else:
            # Lógica antigua para compatibilidad
            # Determinar el año
            if periodo_ano == "anterior":
                year = now.year - 1
            else:
                year = now.year
            
            # Determinar el mes
            if periodo_mes == "anterior":
                if now.month == 1:
                    month = 12
                    year = year - 1
                else:
                    month = now.month - 1
            else:
                month = now.month
            
            # Calcular fecha inicio y fin del período
            fecha_inicio = f"{year}-{month:02d}-01"
            # Calcular último día del mes
            if month == 12:
                next_month_year = year + 1
                next_month = 1
            else:
                next_month_year = year
                next_month = month + 1
            fecha_fin = f"{next_month_year}-{next_month:02d}-01"
            
            logging.info(f"Dashboard Compras: período {fecha_inicio} a {fecha_fin}")
        
        if is_mpro_system(server.get('system_type')):
            # ============================================================================
            # CORRECCIÓN AUDITORIA-COMPRAS-DASHBOARD-MPRO-01 (2026-04-29):
            # 
            # PROBLEMAS CORREGIDOS:
            # 1. Tm_Tipo = 'E' incorrecto -> debe ser 'EN' para entradas en MPRO
            # 2. Filtro LIKE '%sucursal%' impreciso -> usar Sc_Cve_Sucursal exacto
            # 3. Tabla Movimiento no refleja compras reales -> usar Compra_Encabezado
            # 
            # VALIDACIÓN SQL DIRECTA (2026-04-29):
            # - 130 QRO (0021): 398 facturas, $2,911,864.47 (Compra_Encabezado)
            # - ORIGEN (0023): 377 facturas, $2,006,042.58 (Compra_Encabezado)
            # ============================================================================
            
            # Determinar sucursal_origen_id (código exacto MPRO)
            # El parámetro 'sucursal' puede venir como código o nombre
            # Intentar resolver a código exacto
            sucursal_codigo = sucursal
            
            # Total compras del período usando Compra_Encabezado (fuente correcta)
            # Filtro por Sc_Cve_Sucursal exacto, no LIKE
            query_compras = f"""
SELECT 
    COUNT(DISTINCT Co.Co_Folio) as total_facturas,
    ISNULL(SUM(Co.Co_Precio_Neto_Importe), 0) as total
FROM Compra_Encabezado Co
WHERE Co.Co_Fecha >= '{fecha_inicio}'
    AND Co.Co_Fecha < '{fecha_fin}'
    AND ISNULL(Co.Es_Cve_Estado, '') <> 'CA'
    AND Co.Sc_Cve_Sucursal = '{sucursal_codigo}'
"""
            logging.info(f"[COMPRAS_DASHBOARD_MPRO] Sucursal={sucursal_codigo}, Período={fecha_inicio} a {fecha_fin}")
            
            result_compras = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_compras
            )
            
            # TAREA 7: Prohibir ceros silenciosos - verificar respuesta real
            if not result_compras:
                logging.error(f"[COMPRAS_DASHBOARD_MPRO] COMPRAS_QUERY_ERROR: Sin respuesta para sucursal {sucursal_codigo}")
                return {
                    "kpis": {"total_compras_mes": 0, "facturas_mes": 0, "requisiciones_pendientes": 0, "proveedores_activos": 0, "alertas_activas": 0},
                    "alertas": [{"tipo": "error", "mensaje": "Error en consulta de compras"}],
                    "top_proveedores": [],
                    "meta": {"status": "COMPRAS_QUERY_ERROR", "sucursal": sucursal_codigo, "mensaje": "La consulta no retornó datos"}
                }
            
            total_compras = float(result_compras[0]['total'] or 0)
            total_facturas = int(result_compras[0]['total_facturas'] or 0)
            
            # Requisiciones pendientes FILTRADO POR SUCURSAL EXACTA
            query_req = f"""
SELECT COUNT(*) as total FROM Requisicion_Compra RC
WHERE RC.Es_Cve_Estado = 'PXA' 
    AND RC.Sc_Cve_Sucursal = '{sucursal_codigo}'
"""
            result_req = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_req
            )
            req_pendientes = result_req[0]['total'] if result_req else 0
            
            # Proveedores activos (con compras en últimos 90 días) FILTRADO POR SUCURSAL EXACTA
            query_prov = f"""
SELECT COUNT(DISTINCT Co.Pv_Cve_Proveedor) as total
FROM Compra_Encabezado Co
WHERE Co.Co_Fecha >= DATEADD(day, -90, GETDATE())
    AND Co.Pv_Cve_Proveedor IS NOT NULL
    AND ISNULL(Co.Es_Cve_Estado, '') <> 'CA'
    AND Co.Sc_Cve_Sucursal = '{sucursal_codigo}'
"""
            result_prov = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_prov
            )
            prov_activos = result_prov[0]['total'] if result_prov else 0
            
            # Top 5 proveedores usando Compra_Encabezado
            query_top = f"""
SELECT TOP 5 
    ISNULL(P.Pv_Nombre, 'Sin proveedor') as nombre,
    COUNT(DISTINCT Co.Co_Folio) as facturas,
    ISNULL(SUM(Co.Co_Precio_Neto_Importe), 0) as total
FROM Compra_Encabezado Co
LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = Co.Pv_Cve_Proveedor
WHERE Co.Co_Fecha >= '{fecha_inicio}'
    AND Co.Co_Fecha < '{fecha_fin}'
    AND ISNULL(Co.Es_Cve_Estado, '') <> 'CA'
    AND Co.Sc_Cve_Sucursal = '{sucursal_codigo}'
GROUP BY P.Pv_Nombre
ORDER BY SUM(Co.Co_Precio_Neto_Importe) DESC
"""
            result_top = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_top
            )
            top_proveedores = [{"nombre": r['nombre'], "total": float(r['total'] or 0)} for r in (result_top or [])]
            
            logging.info(f"[COMPRAS_DASHBOARD_MPRO] Resultado: {total_facturas} facturas, ${total_compras:,.2f}, {prov_activos} proveedores")
            
            return {
                "kpis": {
                    "total_compras_mes": total_compras,
                    "facturas_mes": total_facturas,
                    "requisiciones_pendientes": req_pendientes,
                    "proveedores_activos": prov_activos,
                    "alertas_activas": 0
                },
                "alertas": [],
                "top_proveedores": top_proveedores,
                "meta": {
                    "status": "OK",
                    "source": "Compra_Encabezado",
                    "sucursal_codigo": sucursal_codigo,
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "system_type": "MPRO"
                }
            }
        
        elif is_softrestaurant_system(server.get('system_type')):
            # ============================================================================
            # CORRECCIÓN AUDITORIA-COMPRAS-DASHBOARD-SR-01 (2026-04-29):
            # 
            # SoftRestaurant - Usando tabla compras del catálogo
            # Base single-tenant: no requiere filtro por sucursal
            #
            # VALIDACIÓN SQL DIRECTA (2026-04-29):
            # - 130 MID: 452 facturas, $2,738,483.56 (Abril 2026)
            # ============================================================================
            
            # CORRECCIÓN AUDITORIA-COMPRAS-DASHBOARD-VS-ANALISIS-01:
            # Usar MONTH()/YEAR() en lugar de rangos de fecha para consistencia con /api/compras/analisis
            meses_cond = " OR ".join([f"MONTH(c.fechaaplicacion) = {int(m)}" for m in lista_meses]) if meses and lista_meses else f"MONTH(c.fechaaplicacion) = {now.month}"
            anios_cond = " OR ".join([f"YEAR(c.fechaaplicacion) = {a}" for a in lista_anios]) if lista_anios else f"YEAR(c.fechaaplicacion) = {now.year}"
            
            logging.info(f"[COMPRAS_DASHBOARD_SR] Database={server.get('database')}, Filtros: ({anios_cond}) AND ({meses_cond})")
            
            # Total compras del período seleccionado
            query_compras = f"""
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE ({anios_cond})
    AND ({meses_cond})
    AND ISNULL(c.cancelado, 0) = 0
"""
            result_compras = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_compras
            )
            
            # TAREA 7: Prohibir ceros silenciosos - usar estados específicos
            if not result_compras:
                # Registrar el error con detalle para diagnóstico
                logging.error(f"[COMPRAS_DASHBOARD_SR] COMPRAS_QUERY_ERROR: Sin respuesta para {server.get('database')} (host={server.get('host')})")
                
                return {
                    "kpis": {"total_compras_mes": 0, "facturas_mes": 0, "requisiciones_pendientes": 0, "proveedores_activos": 0, "alertas_activas": 0},
                    "alertas": [{"tipo": "error", "mensaje": "No fue posible conectar con el servidor SQL configurado"}],
                    "top_proveedores": [],
                    "meta": {
                        "status": "SERVER_UNREACHABLE",
                        "database": server.get('database'),
                        "host": server.get('host'),
                        "server_id": server_id,
                        "config_origin": "EDARSAHUB_SQL",
                        "mensaje": "No fue posible conectar con el servidor SQL configurado para esta unidad",
                        "zero_confirmed": False
                    }
                }
            
            total_compras = float(result_compras[0]['Compra_Total'] or 0)
            facturas = int(result_compras[0]['Facturas'] or 0)
            
            # Proveedores activos (con compras en últimos 90 días desde hoy)
            from datetime import datetime, timedelta
            fecha_90 = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            query_prov = f"""
SELECT COUNT(DISTINCT c.idproveedor) as total
FROM compras c
WHERE c.fechaaplicacion >= '{fecha_90}'
  AND c.idproveedor IS NOT NULL
  AND ISNULL(c.cancelado, 0) = 0
"""
            result_prov = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_prov
            )
            prov_activos = result_prov[0]['total'] if result_prov else 0
            
            # Top proveedores usando tabla compras
            query_top = f"""
SELECT TOP 5 
    ISNULL(p.nombre, 'Sin proveedor') as nombre,
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as total
FROM compras c
LEFT JOIN proveedores p ON p.idproveedor = c.idproveedor
WHERE ({anios_cond})
    AND ({meses_cond})
    AND ISNULL(c.cancelado, 0) = 0
GROUP BY p.nombre
ORDER BY SUM(c.total) DESC
"""
            result_top = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_top
            )
            top_proveedores = [{"nombre": r['nombre'], "total": float(r['total'] or 0)} for r in (result_top or [])]
            
            logging.info(f"[COMPRAS_DASHBOARD_SR] Resultado: {facturas} facturas, ${total_compras:,.2f}, {prov_activos} proveedores")
            
            return {
                "kpis": {
                    "total_compras_mes": total_compras,
                    "facturas_mes": facturas,
                    "requisiciones_pendientes": 0,  # SoftRestaurant no tiene este concepto
                    "proveedores_activos": prov_activos,
                    "alertas_activas": 0
                },
                "alertas": [],
                "top_proveedores": top_proveedores,
                "meta": {
                    "status": "OK",
                    "source": "compras",
                    "database": server.get('database'),
                    "anios": lista_anios,
                    "meses": lista_meses if meses else [now.month],
                    "system_type": "SoftRestaurant"
                }
            }
        
        return {"kpis": {}, "alertas": [], "top_proveedores": []}
    except Exception as e:
        logging.error(f"Error en dashboard compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/compras/analisis")
async def obtener_analisis_compras(request: AnalisisComprasRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene análisis de compras por proveedor y mes con alertas de desviación"""
    verify_token(credentials.credentials)
    
    # FASE T3.3: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Obtener años (priorizar lista de años sobre año único)
    if request.anios and len(request.anios) > 0:
        anios = [int(a) for a in request.anios]
    elif request.anio:
        anios = [request.anio]
    else:
        anios = [datetime.now().year]
    
    max(anios)  # Usar el año más reciente para la consulta principal
    
    logging.info(f"Análisis compras: {server['name']} - Años: {anios}, Meses: {request.meses}")
    
    try:
        if is_mpro_system(server.get('system_type')):
            # FASE 1C: Sanitizar entradas LIKE
            sucursal_safe = _escape_like_pattern(request.sucursal) if request.sucursal else ""
            
            # Construir condición de meses
            meses_cond = " OR ".join([f"MONTH(M.Mv_Fecha) = {int(m)}" for m in request.meses])
            # Construir condición de años
            anios_cond = " OR ".join([f"YEAR(M.Mv_Fecha) = {a}" for a in anios])
            
            query = f"""
SELECT 
    P.Pv_Cve_Proveedor as codigo,
    P.Pv_Nombre as nombre,
    MONTH(M.Mv_Fecha) as mes,
    YEAR(M.Mv_Fecha) as anio,
    SUM(M.Mv_Costo_Importe) as total
FROM Movimiento M
INNER JOIN Proveedor P ON P.Pv_Cve_Proveedor = M.Pv_Cve_Proveedor
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE TM.Tm_Tipo = 'E'
    AND ({anios_cond})
    AND ({meses_cond})
    AND S.Sc_Descripcion LIKE '%{sucursal_safe}%'
    AND ISNULL(M.Es_Cve_Estado, '') <> 'CA'
GROUP BY P.Pv_Cve_Proveedor, P.Pv_Nombre, MONTH(M.Mv_Fecha), YEAR(M.Mv_Fecha)
ORDER BY P.Pv_Nombre, YEAR(M.Mv_Fecha), MONTH(M.Mv_Fecha)
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            # Pivot por proveedor y mes
            proveedores = {}
            for row in result:
                codigo = row['codigo']
                if codigo not in proveedores:
                    proveedores[codigo] = {
                        'codigo': codigo,
                        'nombre': row['nombre'],
                        'total': 0
                    }
                    for m in request.meses:
                        proveedores[codigo][m] = 0
                
                mes_str = str(row['mes']).zfill(2)
                if mes_str in request.meses:
                    proveedores[codigo][mes_str] += float(row['total'] or 0)
                    proveedores[codigo]['total'] += float(row['total'] or 0)
            
            # Ordenar por total descendente
            proveedores_list = sorted(proveedores.values(), key=lambda x: x['total'], reverse=True)
            
            return {
                "proveedores": proveedores_list[:100],  # Top 100
                "alertas": []
            }
        
        elif is_softrestaurant_system(server.get('system_type')):
            # SoftRestaurant - Compras por proveedor usando tabla compras
            meses_cond = " OR ".join([f"MONTH(c.fechaaplicacion) = {int(m)}" for m in request.meses])
            anios_cond = " OR ".join([f"YEAR(c.fechaaplicacion) = {a}" for a in anios])
            
            query = f"""
SELECT 
    ISNULL(p.idproveedor, 0) as codigo,
    ISNULL(p.nombre, 'Sin proveedor') as nombre,
    MONTH(c.fechaaplicacion) as mes,
    YEAR(c.fechaaplicacion) as anio,
    SUM(c.total) as total
FROM compras c
LEFT JOIN proveedores p ON p.idproveedor = c.idproveedor
WHERE ({anios_cond})
    AND ({meses_cond})
    AND ISNULL(c.cancelado, 0) = 0
GROUP BY p.idproveedor, p.nombre, MONTH(c.fechaaplicacion), YEAR(c.fechaaplicacion)
ORDER BY p.nombre, YEAR(c.fechaaplicacion), MONTH(c.fechaaplicacion)
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            if not result:
                return {"proveedores": [], "alertas": []}
            
            # Pivot por proveedor y mes
            proveedores = {}
            for row in result:
                codigo = str(row['codigo'])
                if codigo not in proveedores:
                    proveedores[codigo] = {
                        'codigo': codigo,
                        'nombre': row['nombre'],
                        'total': 0
                    }
                    for m in request.meses:
                        proveedores[codigo][m] = 0
                
                mes_str = str(row['mes']).zfill(2)
                if mes_str in request.meses:
                    proveedores[codigo][mes_str] += float(row['total'] or 0)
                    proveedores[codigo]['total'] += float(row['total'] or 0)
            
            # Ordenar por total descendente
            proveedores_list = sorted(proveedores.values(), key=lambda x: x['total'], reverse=True)
            
            return {
                "proveedores": proveedores_list[:100],  # Top 100
                "alertas": []
            }
        
        # FASE 3A: Blindaje - sistema no soportado
        system_type = server.get('system_type', 'UNKNOWN')
        normalize_system_type(system_type)
        log_compras_error("analisis", request.server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
        return {
            "status": "UNSUPPORTED_SYSTEM_TYPE",
            "proveedores": [],
            "alertas": [],
            "error": f"El tipo de sistema '{system_type}' no está soportado para análisis de compras"
        }
    except Exception as e:
        logging.error(f"Error en análisis compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/compras/facturas-proveedor/{server_id}")
async def obtener_facturas_proveedor(server_id: str, proveedor_codigo: str, anio: int, meses: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene las facturas/entradas de un proveedor específico"""
    verify_token(credentials.credentials)
    
    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    system_type = server.get('system_type', 'UNKNOWN')
    
    try:
        # FASE 3A: Usar normalización de system_type
        if is_mpro_system(system_type):
            log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "MPRO_ADAPTER")
            meses_list = meses.split(',')
            meses_cond = " OR ".join([f"MONTH(M.Mv_Fecha) = {int(m)}" for m in meses_list])
            
            query = f"""
SELECT 
    M.Mv_Documento as folio,
    M.Mv_Fecha as fecha,
    COUNT(DISTINCT MD.Pr_Cve_Producto) as productos,
    SUM(MD.Md_Importe) as importe,
    CASE WHEN M.Es_Cve_Estado = 'PA' THEN 'pagada' ELSE 'pendiente' END as status
FROM Movimiento M
INNER JOIN Movimiento_Detalle MD ON MD.Mv_Folio = M.Mv_Folio
WHERE M.Pv_Cve_Proveedor = '{proveedor_codigo}'
    AND YEAR(M.Mv_Fecha) = {anio}
    AND ({meses_cond})
    AND M.Es_Cve_Estado <> 'CA'
GROUP BY M.Mv_Documento, M.Mv_Fecha, M.Es_Cve_Estado
ORDER BY M.Mv_Fecha DESC
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            return [
                {
                    "folio": r['folio'],
                    "fecha": str(r['fecha']),
                    "productos": r['productos'],
                    "importe": float(r['importe'] or 0),
                    "status": r['status'],
                    "tiene_pdf": False,  # TODO: verificar si existe archivo
                    "tiene_xml": False
                }
                for r in result
            ]
        
        # FASE 3A: Blindaje - funcionalidad solo disponible en MPRO
        system_type = server.get('system_type', 'UNKNOWN')
        log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "NO_ADAPTER_AVAILABLE")
        return {
            "status": "NOT_AVAILABLE_FOR_SYSTEM",
            "data": [],
            "message": f"Las facturas de proveedor solo están disponibles para sistemas MPRO. Sistema actual: {system_type}"
        }
    except Exception as e:
        logging.error(f"Error obteniendo facturas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/compras/detalle-factura/{server_id}/{folio}")
async def obtener_detalle_factura(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el detalle de productos de una factura/entrada"""
    verify_token(credentials.credentials)
    
    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if is_mpro_system(server.get('system_type')):
            query = f"""
SELECT 
    MD.Pr_Cve_Producto as codigo,
    P.Pr_Descripcion as producto,
    MD.Md_Cantidad as cantidad,
    MD.Md_Costo as costo,
    MD.Md_Importe as importe
FROM Movimiento_Detalle MD
INNER JOIN Movimiento M ON M.Mv_Folio = MD.Mv_Folio
INNER JOIN Producto P ON P.Pr_Cve_Producto = MD.Pr_Cve_Producto
WHERE M.Mv_Documento = '{folio}'
ORDER BY P.Pr_Descripcion
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            return [
                {
                    "codigo": r['codigo'],
                    "producto": r['producto'],
                    "cantidad": float(r['cantidad'] or 0),
                    "costo": float(r['costo'] or 0),
                    "importe": float(r['importe'] or 0)
                }
                for r in result
            ]
        
        # FASE 3A: Blindaje - funcionalidad solo disponible en MPRO
        system_type = server.get('system_type', 'UNKNOWN')
        log_compras_adapter_selected("detalle-factura", server_id, system_type, "NO_ADAPTER_AVAILABLE")
        return {
            "status": "NOT_AVAILABLE_FOR_SYSTEM",
            "data": [],
            "message": f"El detalle de factura solo está disponible para sistemas MPRO. Sistema actual: {system_type}"
        }
    except Exception as e:
        logging.error(f"Error obteniendo detalle factura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MÓDULO COMERCIAL - Endpoints de Ventas
# ============================================================================

# ============================================================================
# ENDPOINT /comercial/dashboard - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-5B (Abril 2026): Migrado a modules/comercial/routes.py
# CIERRE DE FASE 5B - MÓDULO COMERCIAL 100% MIGRADO
# ============================================================================


# ============================================================================
# ENDPOINT /comercial/ticket-perfecto - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4C (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================


# ============================================================================
# ENDPOINT /comercial/metas - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4A (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================


# ============================================================================
# ENDPOINT /comercial/ventas-tiempo - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4C (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================

# ============================================================================
# ENDPOINT /comercial/mesas - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4E (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================

# ============================================================================
# ENDPOINT /comercial/detalle-movimientos - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4E (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================

# ============================================================================
# ENDPOINT /comercial/reporte-pax - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4H (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================


# ============================================================================
# TABLERO EJECUTIVO - Multi-Unidad (Socios/Accionistas)
# ============================================================================

# Función para guardar/obtener estado de conexión de servidores
async def get_server_connection_status(server_id: str):
    """Obtiene el último estado de conexión de un servidor"""
    status = await db.server_status.find_one({"server_id": server_id})
    return status

async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None):
    """Guarda el estado de conexión de un servidor"""
    await db.server_status.update_one(
        {"server_id": server_id},
        {
            "$set": {
                "server_id": server_id,
                "is_online": is_online,
                "response_time_ms": response_time_ms,
                "last_check": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )

async def is_server_recently_offline(server_id: str, minutes_threshold: int = 10):
    """Verifica si un servidor fue marcado como offline recientemente (evita reintentos)"""
    status = await get_server_connection_status(server_id)
    if not status:
        return False  # Sin registro, intentar conectar
    
    if status.get('is_online', True):
        return False  # Estaba online, intentar conectar
    
    # Verificar si el último chequeo fue hace menos de X minutos
    last_check = status.get('last_check')
    if last_check:
        try:
            last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff_minutes = (now - last_check_dt).total_seconds() / 60
            if diff_minutes < minutes_threshold:
                return True  # Offline recientemente, no reintentar
        except Exception:
            pass
    
    return False

# Función para guardar/obtener caché de KPIs
async def get_cached_kpis(server_id: str, periodo_key: str):
    """Obtiene los KPIs cacheados de un servidor"""
    cache = await db.kpis_cache.find_one({
        "server_id": server_id,
        "periodo_key": periodo_key
    })
    return cache

async def save_kpis_cache(server_id: str, periodo_key: str, kpis: dict):
    """Guarda los KPIs en caché"""
    await db.kpis_cache.update_one(
        {"server_id": server_id, "periodo_key": periodo_key},
        {
            "$set": {
                "server_id": server_id,
                "periodo_key": periodo_key,
                "kpis": kpis,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "status": "online"
            }
        },
        upsert=True
    )

# ============================================================================
# HELPERS DEL TABLERO EJECUTIVO - MIGRADOS A modules/comercial/service.py
# ============================================================================
# FASE 5B-2 (Abril 2026): Las siguientes funciones fueron migradas:
# - get_kpis_softrestaurant() -> modules/comercial/service.py
# - get_kpis_mpro() -> modules/comercial/service.py
# - get_kpis_mpro_por_sucursal() -> modules/comercial/service.py
# 
# Ahora se importan directamente desde el módulo.
# Ver línea ~125 donde se hace el import.
# ============================================================================

# ============================================================================
# ENDPOINT TABLERO EJECUTIVO - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-3 (Abril 2026): El endpoint fue migrado:
# - GET /comercial/tablero-ejecutivo -> modules/comercial/routes.py
#
# El router está incluido en api_router (ver línea ~105).
# ============================================================================


# ============================================================================
# ENDPOINT /comercial/sucursales - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4A (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================



# ============================================================================
# ENDPOINT /comercial/precios-constantes - MIGRADO A modules/comercial/routes.py
# ============================================================================
# FASE 5B-4G (Abril 2026): Migrado a modules/comercial/routes.py
# ============================================================================


# ============================================================================
# EXPLORADOR DE BASE DE DATOS - Ver tablas y estructuras
# ============================================================================

@api_router.get("/explorador/conexiones-explorables")
async def listar_conexiones_explorables(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todas las conexiones explorables activas desde EDARSAHUB SQL.
    
    CORRECCIÓN P1 (2026-05-15): 
    - No usa MongoDB
    - No está hardcodeado a SoftRestaurant/MPRO
    - Incluye todos los tipos de conexión explorables (SQL_SERVER, API_LOCAL con /query)
    - Respeta permisos RBAC del usuario
    
    Returns:
        Lista de conexiones explorables con:
        - id: ID de la conexión
        - nombre: Nombre visible
        - sistema_codigo: Código del sistema (MPRO, SOFTRESTAURANT, etc.)
        - sistema_descripcion: Descripción legible del sistema
        - tipo_conexion: SQL_SERVER, API_LOCAL, DATA_SOURCE
        - host: Host (sin credenciales)
        - database: Nombre de la base de datos
        - activo: Boolean
        - explorable: Boolean derivado
    """
    from modules.comercial.repository import EDARSAHUB_CONFIG
    from core.db import execute_sql_query
    
    try:
        # Query para obtener conexiones explorables con su tipo de sistema
        # FIX P0 (May-2026): Separar claramente proveedor/sistema vs tipo de conexión
        #   - grupo_explorador_codigo: system_type RAW = proveedor/sistema (SOFRESATAURANT_ENTER)
        #   - grupo_explorador_nombre: label amigable del proveedor (Sofrestaurant Enterprise)
        #   - tipo_conexion: conexión técnica (API_LOCAL, SQL_SERVER)
        #   - sistema_codigo/sistema_codigo_raw: para matching en Catálogo SQL
        query = """
        SELECT 
            sc.id,
            sc.nombre,
            sc.tipo_conexion,
            sc.system_type,
            sc.host,
            sc.port,
            sc.database_name,
            sc.activo,
            sc.visible_en_operaciones,
            sc.api_url,
            sc.system_type as sistema_codigo_raw,
            -- Para grupo del Explorador BD: usar system_type RAW como proveedor
            sc.system_type as grupo_explorador_codigo,
            -- Label amigable del proveedor (actualizado Mayo 2026)
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
            END as grupo_explorador_nombre,
            -- Para compatibilidad con código anterior (normalizado = tipo conexión técnica)
            COALESCE(st.CodigoSistema, sc.system_type) as sistema_codigo_normalizado,
            COALESCE(st.NombreSistema, sc.system_type) as sistema_nombre
        FROM Servidores_Conexiones sc
        LEFT JOIN Sistema_TiposVariantes sv 
            ON UPPER(sc.system_type) = UPPER(sv.VarianteNombre) 
            AND sv.Activo = 1
        LEFT JOIN Sistema_Tipos st 
            ON sv.SistemaTipoID = st.SistemaTipoID 
            AND st.Activo = 1
        WHERE sc.activo = 1
          AND (
            sc.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
            OR (sc.tipo_conexion = 'API_LOCAL' AND sc.api_url IS NOT NULL)
            OR sc.tipo_conexion IS NULL
          )
        ORDER BY sc.nombre
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        # Construir respuesta sin exponer secrets
        conexiones = []
        for row in results:
            conexion = {
                'id': row.get('id'),
                'nombre': row.get('nombre', ''),
                # FIX P0 (May-2026): Campos para Catálogo SQL (matching por RAW)
                'sistema_codigo': row.get('sistema_codigo_raw', row.get('system_type', '')),
                'sistema_codigo_raw': row.get('sistema_codigo_raw', row.get('system_type', '')),
                # FIX P0 (May-2026): Campos para Explorador BD (grupo por proveedor/sistema)
                'grupo_explorador_codigo': row.get('grupo_explorador_codigo', row.get('system_type', '')),
                'grupo_explorador_nombre': row.get('grupo_explorador_nombre', row.get('system_type', '')),
                # Campos de compatibilidad (normalizado = tipo conexión técnica, NO usar para grupo visual)
                'sistema_codigo_normalizado': row.get('sistema_codigo_normalizado', row.get('system_type', '')),
                'sistema_nombre': row.get('sistema_nombre', row.get('system_type', '')),
                'sistema_descripcion': row.get('grupo_explorador_nombre', row.get('system_type', '')),
                # Tipo de conexión técnica
                'tipo_conexion': row.get('tipo_conexion', 'SQL_SERVER'),
                'host': row.get('host', ''),
                'database': row.get('database_name', ''),
                'activo': bool(row.get('activo', 0)),
                'visible_en_operaciones': bool(row.get('visible_en_operaciones', 0)),
                # Derivar si es explorable técnicamente
                'explorable': _es_conexion_explorable(row)
            }
            conexiones.append(conexion)
        
        logging.info(f"[EXPLORADOR] Listadas {len(conexiones)} conexiones explorables")
        return {
            "success": True,
            "data": conexiones,
            "total": len(conexiones)
        }
        
    except Exception as e:
        logging.error(f"[EXPLORADOR] Error listando conexiones explorables: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo conexiones: {str(e)}")


def _es_conexion_explorable(row: Dict) -> bool:
    """
    Determina si una conexión es técnicamente explorable.
    
    FASE 6 - Integración Catálogo Maestro:
    Ahora usa SystemCapabilityResolver para validar si el sistema
    tiene capacidad EXPLORADOR_BD activa en SQL.
    
    Reglas:
    1. Validar técnicamente (host/database o api_url configurados)
    2. Validar por capacidad (sistema tiene EXPLORADOR_BD activo)
    
    Fallback: Si el resolver falla, usa solo validación técnica (permisivo)
    """
    # Validación técnica básica
    tipo = row.get('tipo_conexion', '')
    
    if tipo in ('SQL_SERVER', 'DATA_SOURCE'):
        tech_valid = bool(row.get('host')) and bool(row.get('database_name'))
    elif tipo == 'API_LOCAL':
        tech_valid = bool(row.get('api_url'))
    else:
        tech_valid = False
    
    if not tech_valid:
        return False
    
    # FASE 6: Validar capacidad EXPLORADOR_BD via Catálogo Maestro
    try:
        from core.system_capability_integration import is_system_explorable
        
        system_type = row.get('sistema_codigo') or row.get('system_type') or ''
        
        if not system_type:
            # Sin system_type, permitir por compatibilidad
            logging.debug(f"[EXPLORADOR] Conexión sin system_type, permitiendo por compatibilidad")
            return True
        
        # Consultar resolver - es permisivo si hay errores
        is_explorable = is_system_explorable(system_type)
        
        logging.debug(
            f"[EXPLORADOR-CAPACIDAD] {system_type}: "
            f"explorable={is_explorable} (via Catálogo Maestro)"
        )
        
        return is_explorable
        
    except Exception as e:
        # Fallback: Si el resolver falla, usar solo validación técnica
        logging.warning(
            f"[EXPLORADOR] Error consultando Catálogo Maestro: {e}. "
            f"Usando validación técnica solamente."
        )
        return True  # Permisivo para no romper funcionalidad


@api_router.get("/explorador/tablas/{server_id}")
async def listar_tablas(
    server_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todas las tablas de la base de datos del servidor.
    
    CORRECCIÓN P1 (2026-05-15): Soporte Multi-Sistema
    - SQL_SERVER / DATA_SOURCE: Usa metadata SQL Server (INFORMATION_SCHEMA)
    - API_LOCAL: Usa endpoint /query con SELECT readonly
    
    No limitado a SoftRestaurant. Soporta MPRO, Enterprise, NOMIPAQ, EDARSAHUB, etc.
    """
    from core.server_registry import get_server_connection_info
    from modules.api_connections.repository import get_api_connection_by_id_full
    
    # Determinar tipo de conexión
    tipo_conexion = None
    conn_info = None
    api_conn = None
    
    # Primero intentar como API_LOCAL
    try:
        api_conn = await get_api_connection_by_id_full(server_id)
        if api_conn and api_conn.get('tipo_conexion') == 'API_LOCAL':
            tipo_conexion = 'API_LOCAL'
    except Exception as e:
        logging.debug(f"[EXPLORADOR] {server_id} no es API_LOCAL: {e}")
    
    # Si no es API_LOCAL, buscar como SQL_SERVER/DATA_SOURCE
    if tipo_conexion != 'API_LOCAL':
        conn_info = await get_server_connection_info(server_id, db=db)
        if conn_info:
            tipo_conexion = conn_info.get('tipo_conexion', 'DATA_SOURCE')
    
    if not api_conn and not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    # FASE 6-8: Validar acceso
    await validate_server_access_unified(current_user, server_id)
    
    # === CASO 1: API_LOCAL (MPRO, Enterprise, etc. via API /query) ===
    if tipo_conexion == 'API_LOCAL' and api_conn:
        return await _cargar_tablas_api_local(api_conn, server_id)
    
    # === CASO 2: SQL_SERVER / DATA_SOURCE (conexión directa SQL) ===
    if conn_info:
        return await _cargar_tablas_sql_server(conn_info)
    
    raise HTTPException(status_code=400, detail="Tipo de conexión no soportado para exploración")


async def _cargar_tablas_api_local(api_conn: Dict, server_id: str) -> Dict:
    """
    Carga tablas desde una conexión API_LOCAL usando endpoint /query.
    
    CORRECCIÓN P1 (2026-05-16): Reutiliza execute_test_query que ya funciona
    para APIs Enterprise (CHAPUR NORTE, etc.) en lugar de httpx directo.
    
    Usa INFORMATION_SCHEMA.TABLES que es más compatible que sys.tables.
    TOP 500 para obtener todas las tablas de la base de datos.
    """
    from modules.api_connections.repository import execute_test_query
    
    nombre = api_conn.get('nombre', api_conn.get('name', 'API'))
    sistema = api_conn.get('tipo', api_conn.get('system_type', 'UNKNOWN'))
    api_url = api_conn.get('url', api_conn.get('api_url', ''))
    
    if not api_url:
        return {
            "servidor": nombre,
            "sistema": sistema,
            "database": "API",
            "tablas": [],
            "error": "URL de API no configurada",
            "tipo_conexion": "API_LOCAL"
        }
    
    # Query compatible con Enterprise y SoftRestaurant - TOP 500 para metadata completa
    metadata_query = """
SELECT TOP 500 TABLE_NAME as tabla 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE' 
ORDER BY TABLE_NAME
"""
    
    try:
        # Usar la función ya probada que funciona con CHAPUR NORTE
        # CORRECCIÓN P1 (2026-05-16): limit=None para obtener TODAS las tablas
        result = await execute_test_query(
            api_id=server_id,
            sql_query=metadata_query.strip(),
            timeout=60,  # Más tiempo para queries de metadata grandes
            limit=None  # Sin límite para obtener todas las tablas de metadata
        )
        
        if result.get('success') and result.get('status_code') == 200:
            # Extraer tablas de la respuesta
            preview_data = result.get('preview_data', result.get('data', []))
            tablas = []
            
            if isinstance(preview_data, list):
                for row in preview_data:
                    if isinstance(row, dict):
                        tabla_name = row.get('tabla', row.get('TABLE_NAME', row.get('name', '')))
                        if tabla_name:
                            tablas.append({"tabla": tabla_name, "tipo": "TABLE"})
            
            logging.info(f"[EXPLORADOR][API_LOCAL] {nombre}: {len(tablas)} tablas obtenidas via test_query")
            return {
                "servidor": nombre,
                "sistema": sistema,
                "database": api_conn.get('sucursal_destino', 'API'),
                "tablas": tablas,
                "tipo_conexion": "API_LOCAL"
            }
        else:
            error_msg = result.get('error', result.get('message', 'Error desconocido'))
            logging.warning(f"[EXPLORADOR][API_LOCAL] {nombre}: {error_msg}")
            return {
                "servidor": nombre,
                "sistema": sistema,
                "database": "API",
                "tablas": [],
                "error": f"Error de API: {error_msg[:100]}",
                "tipo_conexion": "API_LOCAL"
            }
            
    except Exception as e:
        logging.error(f"[EXPLORADOR][API_LOCAL] {nombre}: {e}")
        return {
            "servidor": nombre,
            "sistema": sistema,
            "database": "API",
            "tablas": [],
            "error": f"Error: {str(e)[:100]}",
            "tipo_conexion": "API_LOCAL"
        }


async def _cargar_tablas_sql_server(conn_info: Dict) -> Dict:
    """
    Carga tablas desde una conexión SQL Server directa.
    
    Funciona para SoftRestaurant, NOMIPAQ, EDARSAHUB, cualquier SQL Server.
    
    CORRECCIÓN P1 (2026-05-16): Mejor manejo de errores para mostrar
    mensaje claro cuando hay problemas de conexión o permisos.
    """
    query = """
SELECT 
    TABLE_NAME as tabla,
    TABLE_TYPE as tipo
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME
"""
    nombre = conn_info.get('name', 'Unknown')
    sistema = conn_info.get('system_type', 'Unknown')
    database = conn_info.get('database', '')
    host = conn_info.get('host', '')
    tipo_conexion = conn_info.get('tipo_conexion', 'SQL_SERVER')
    
    # Verificar que hay credenciales SQL
    if not host or not database:
        return {
            "servidor": nombre,
            "sistema": sistema,
            "database": database or "N/A",
            "tablas": [],
            "error": "Configuración SQL incompleta (falta host o database)",
            "tipo_conexion": tipo_conexion
        }
    
    try:
        # Usar conexión directa con mejor manejo de errores
        from core.db import _execute_sql_direct_with_error
        
        result, error_msg = await _execute_sql_direct_with_error(
            host,
            conn_info.get('port', 1433),
            database,
            conn_info.get('username', ''),
            conn_info.get('password', ''),
            query
        )
        
        if error_msg:
            logging.warning(f"[EXPLORADOR][SQL] {nombre}: {error_msg}")
            # Sanitizar mensaje de error (no exponer credenciales)
            safe_error = _sanitize_error_message(error_msg)
            return {
                "servidor": nombre,
                "sistema": sistema,
                "database": database,
                "tablas": [],
                "error": safe_error,
                "tipo_conexion": tipo_conexion
            }
        
        logging.info(f"[EXPLORADOR][SQL] {nombre}: {len(result)} tablas")
        return {
            "servidor": nombre,
            "sistema": sistema,
            "database": database,
            "tablas": result,
            "tipo_conexion": tipo_conexion
        }
        
    except Exception as e:
        logging.error(f"[EXPLORADOR][SQL] {nombre}: {e}")
        safe_error = _sanitize_error_message(str(e))
        return {
            "servidor": nombre,
            "sistema": sistema,
            "database": database,
            "tablas": [],
            "error": safe_error,
            "tipo_conexion": tipo_conexion
        }


def _sanitize_error_message(error: str) -> str:
    """
    Sanitiza mensajes de error para no exponer información sensible.
    """
    # Patrones a ocultar
    sensitive_patterns = [
        (r"password[=:]\s*\S+", "password=***"),
        (r"pwd[=:]\s*\S+", "pwd=***"),
        (r"user[=:]\s*\S+", "user=***"),
        (r"uid[=:]\s*\S+", "uid=***"),
    ]
    
    import re
    result = error
    for pattern, replacement in sensitive_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # Truncar si es muy largo
    if len(result) > 200:
        result = result[:200] + "..."
    
    return result


@api_router.get("/explorador/columnas/{server_id}/{tabla}")
async def listar_columnas(
    server_id: str,
    tabla: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista las columnas de una tabla específica.
    
    CORRECCIÓN P1 (2026-05-16): Soporte Multi-Tipo de Conexión
    - DATA_SOURCE: Usa INFORMATION_SCHEMA.COLUMNS con SQL directo
    - API_LOCAL: Usa execute_test_query para consultar via API remota
    
    La whitelist solo aplica para DATA_SOURCE (tablas conocidas del sistema).
    Para API_LOCAL las tablas son dinámicas del servidor remoto.
    """
    from core.server_registry import get_server_connection_info
    from core.db import execute_sql_query_params
    from modules.api_connections.repository import get_api_connection_by_id_full, execute_test_query
    
    # Determinar tipo de conexión
    tipo_conexion = None
    conn_info = None
    api_conn = None
    
    # Primero intentar como API_LOCAL
    try:
        api_conn = await get_api_connection_by_id_full(server_id)
        if api_conn and api_conn.get('tipo_conexion') == 'API_LOCAL':
            tipo_conexion = 'API_LOCAL'
    except Exception as e:
        logging.debug(f"[EXPLORADOR][COLUMNAS] {server_id} no es API_LOCAL: {e}")
    
    # Si no es API_LOCAL, buscar como SQL_SERVER/DATA_SOURCE
    if tipo_conexion != 'API_LOCAL':
        conn_info = await get_server_connection_info(server_id, db=db)
        if conn_info:
            tipo_conexion = conn_info.get('tipo_conexion', 'DATA_SOURCE')
    
    if not api_conn and not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    # Validar acceso
    await validate_server_access_unified(current_user, server_id)
    
    # === CASO 1: API_LOCAL ===
    if tipo_conexion == 'API_LOCAL' and api_conn:
        nombre = api_conn.get('nombre', api_conn.get('name', 'API'))
        
        # Query para obtener columnas de la tabla via API remota
        # Usamos comillas simples escapadas en la query para el nombre de tabla
        tabla_escaped = tabla.replace("'", "''")
        columns_query = f"""
SELECT 
    COLUMN_NAME as columna,
    DATA_TYPE as tipo,
    CHARACTER_MAXIMUM_LENGTH as longitud,
    IS_NULLABLE as nullable,
    COLUMN_DEFAULT as default_value
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla_escaped}'
ORDER BY ORDINAL_POSITION
"""
        try:
            result = await execute_test_query(
                api_id=server_id,
                sql_query=columns_query.strip(),
                timeout=30,
                limit=None  # Sin límite para metadata
            )
            
            if result.get('success') and result.get('status_code') == 200:
                columnas = result.get('preview_data', result.get('data', []))
                return {
                    "tabla": tabla,
                    "servidor": nombre,
                    "columnas": columnas,
                    "tipo_conexion": "API_LOCAL"
                }
            else:
                error_msg = result.get('error', 'Error desconocido')
                raise HTTPException(status_code=500, detail=f"Error API: {error_msg}")
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[EXPLORADOR][COLUMNAS][API_LOCAL] {nombre}: {e}")
            raise HTTPException(status_code=500, detail=f"Error consultando columnas: {str(e)[:100]}")
    
    # === CASO 2: DATA_SOURCE (SQL directo) ===
    if conn_info:
        # Validar tabla contra whitelist (superadmin bypasea whitelist)
        user_role = current_user.get('role', current_user.get('rol', 'visor'))
        is_valid, error_msg = _validate_table_name(tabla, conn_info.get('system_type'), user_role)
        if not is_valid:
            logging.warning(f"[A03-SANITIZADO] Tabla rechazada por whitelist: {tabla[:50]} (rol={user_role})")
            raise HTTPException(status_code=400, detail=error_msg)
        
        query = """
SELECT 
    COLUMN_NAME as columna,
    DATA_TYPE as tipo,
    CHARACTER_MAXIMUM_LENGTH as longitud,
    IS_NULLABLE as nullable,
    COLUMN_DEFAULT as default_value
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = %s
ORDER BY ORDINAL_POSITION
"""
        try:
            result = execute_sql_query_params(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], query, (tabla,)
            )
            return {
                "tabla": tabla,
                "servidor": conn_info['name'],
                "columnas": result,
                "tipo_conexion": "DATA_SOURCE"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/explorador/relaciones/{server_id}/{tabla}")
async def listar_relaciones(
    server_id: str,
    tabla: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista las relaciones (foreign keys) de una tabla.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    FASE 1B: Whitelist de tablas + parametrización
    """
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info
    from core.db import execute_sql_query_params
    
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    # FASE 6-8: Validar acceso usando función centralizada
    await validate_server_access_unified(current_user, server_id)
    
    # FASE 1B: Validar tabla contra whitelist (superadmin bypasea)
    user_role = current_user.get('role', current_user.get('rol', 'visor'))
    is_valid, error_msg = _validate_table_name(tabla, conn_info.get('system_type'), user_role)
    if not is_valid:
        logging.warning(f"[A03-SANITIZADO] Tabla rechazada por whitelist: {tabla[:50]} (rol={user_role})")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # FASE 1B: Usar parametrización segura (tabla pasada 2 veces)
    query = """
SELECT 
    fk.name as nombre_fk,
    tp.name as tabla_padre,
    cp.name as columna_padre,
    tr.name as tabla_referenciada,
    cr.name as columna_referenciada
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
INNER JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
INNER JOIN sys.columns cp ON cp.object_id = fk.parent_object_id AND cp.column_id = fkc.parent_column_id
INNER JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
INNER JOIN sys.columns cr ON cr.object_id = fk.referenced_object_id AND cr.column_id = fkc.referenced_column_id
WHERE tp.name = %s OR tr.name = %s
ORDER BY fk.name
"""
    try:
        result = execute_sql_query_params(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query, (tabla, tabla)
        )
        return {
            "tabla": tabla,
            "servidor": conn_info['name'],
            "relaciones": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/explorador/preview/{server_id}/{tabla}")
async def preview_tabla(
    server_id: str,
    tabla: str,
    limite: int = Query(default=10, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """
    Muestra las primeras N filas de una tabla.
    
    CORRECCIÓN P1 (2026-05-16): Soporte Multi-Tipo de Conexión
    - DATA_SOURCE: Usa SELECT TOP N directo con SQL Server
    - API_LOCAL: Usa execute_test_query para consultar via API remota
    
    La whitelist solo aplica para DATA_SOURCE (tablas conocidas del sistema).
    Para API_LOCAL las tablas son dinámicas del servidor remoto.
    """
    from core.server_registry import get_server_connection_info
    from modules.api_connections.repository import get_api_connection_by_id_full, execute_test_query
    
    # Determinar tipo de conexión
    tipo_conexion = None
    conn_info = None
    api_conn = None
    
    # Primero intentar como API_LOCAL
    try:
        api_conn = await get_api_connection_by_id_full(server_id)
        if api_conn and api_conn.get('tipo_conexion') == 'API_LOCAL':
            tipo_conexion = 'API_LOCAL'
    except Exception as e:
        logging.debug(f"[EXPLORADOR][PREVIEW] {server_id} no es API_LOCAL: {e}")
    
    # Si no es API_LOCAL, buscar como SQL_SERVER/DATA_SOURCE
    if tipo_conexion != 'API_LOCAL':
        conn_info = await get_server_connection_info(server_id, db=db)
        if conn_info:
            tipo_conexion = conn_info.get('tipo_conexion', 'DATA_SOURCE')
    
    if not api_conn and not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    # Validar acceso
    await validate_server_access_unified(current_user, server_id)
    
    # === CASO 1: API_LOCAL ===
    if tipo_conexion == 'API_LOCAL' and api_conn:
        nombre = api_conn.get('nombre', api_conn.get('name', 'API'))
        
        # Query para preview de datos via API remota
        # Usamos brackets para identificador seguro
        tabla_safe = tabla.replace("]", "]]")  # Escapar corchetes
        preview_query = f"SELECT TOP {limite} * FROM [{tabla_safe}]"
        
        try:
            result = await execute_test_query(
                api_id=server_id,
                sql_query=preview_query.strip(),
                timeout=30,
                limit=limite  # Aplicar límite también a la respuesta
            )
            
            if result.get('success') and result.get('status_code') == 200:
                datos = result.get('preview_data', result.get('data', []))
                return {
                    "tabla": tabla,
                    "servidor": nombre,
                    "registros": len(datos),
                    "datos": datos,
                    "tipo_conexion": "API_LOCAL"
                }
            else:
                error_msg = result.get('error', 'Error desconocido')
                raise HTTPException(status_code=500, detail=f"Error API: {error_msg}")
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[EXPLORADOR][PREVIEW][API_LOCAL] {nombre}: {e}")
            raise HTTPException(status_code=500, detail=f"Error consultando datos: {str(e)[:100]}")
    
    # === CASO 2: DATA_SOURCE (SQL directo) ===
    if conn_info:
        # Validar tabla contra whitelist (superadmin bypasea whitelist)
        user_role = current_user.get('role', current_user.get('rol', 'visor'))
        is_valid, error_msg = _validate_table_name(tabla, conn_info.get('system_type'), user_role)
        if not is_valid:
            logging.warning(f"[A03-SANITIZADO] Tabla rechazada por whitelist: {tabla[:50]} (rol={user_role})")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Tabla validada, usar brackets para identificador seguro
        query = f"SELECT TOP {limite} * FROM [{tabla}]"
        
        try:
            result = execute_sql_query(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], query
            )
            return {
                "tabla": tabla,
                "servidor": conn_info['name'],
                "registros": len(result),
                "datos": result,
                "tipo_conexion": "DATA_SOURCE"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/explorador/query/{server_id}")
async def ejecutar_query_libre(
    server_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta una query SQL personalizada (solo SELECT).
    Solo para administradores.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    
    FASE 1B: Sanitización SQL completa con SQLSanitizer.
    SEGURIDAD: Validación estricta de rol Administrador + bloqueo de SQL peligroso.
    """
    # FASE 1B: Validación de rol
    if current_user.get('role') not in ['Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar queries libres")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info
    from core.security import SQLSanitizer, log_blocked_sql
    
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    query = body.get('query', '').strip()
    
    # FASE 1B: Validación SQL completa con sanitizador centralizado
    validation = SQLSanitizer.validate_for_explorer(query, user_role=current_user.get('role'))
    if not validation.is_safe:
        log_blocked_sql(validation, endpoint="/explorador/query", user_email=current_user.get('email'))
        raise HTTPException(status_code=400, detail=f"SQL bloqueado: {validation.blocked_reason}")
    
    try:
        result = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], query
        )
        return {
            "servidor": conn_info['name'],
            "query": query,
            "registros": len(result),
            "datos": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/explorador/ejecutar-script/{server_id}")
async def ejecutar_script_sql(
    server_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta un script SQL completo (CREATE, INSERT, UPDATE, DELETE, etc.).
    SOLO SUPERADMINISTRADOR - ENDPOINT ALTAMENTE RESTRINGIDO.
    
    FASE 1B: BLOQUEADO por defecto. Solo SuperAdministrador puede usar.
    Este endpoint permite DDL/DML y es extremadamente peligroso.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    """
    # FASE 1B: Solo SuperAdministrador puede ejecutar scripts SQL completos
    # Este endpoint permite DDL/DML, es extremadamente peligroso
    if current_user.get('role') != 'SuperAdministrador':
        logging.warning(
            f"[SQL-SCRIPT-BLOCKED] User {current_user.get('email')} intentó ejecutar script SQL. "
            f"Rol: {current_user.get('role')}. Solo SuperAdministrador permitido."
        )
        raise HTTPException(
            status_code=403, 
            detail="Solo SuperAdministrador puede ejecutar scripts SQL completos. "
                   "Este es un endpoint de alto riesgo."
        )
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    script = body.get('script', '').strip()
    titulo = body.get('titulo', '').strip() or 'Script sin título'
    
    if not script:
        raise HTTPException(status_code=400, detail="El script está vacío")
    
    # FASE 1B: Log de auditoría para scripts SQL (sin exponer el script completo)
    logging.warning(
        f"[SQL-SCRIPT-AUDIT] SuperAdmin {current_user.get('email')} ejecutando script. "
        f"Server: {server_id}, Titulo: {titulo}, Length: {len(script)} chars"
    )
    
    # Parsear el script en statements individuales
    # Dividir por GO (batch separator de SQL Server) o por punto y coma
    import re
    
    # Reemplazar GO como separador de batch
    script_normalizado = re.sub(r'\bGO\b', ';', script, flags=re.IGNORECASE)
    
    # Dividir por punto y coma, pero ignorar los que están dentro de strings
    statements = []
    current_statement = []
    in_string = False
    string_char = None
    
    for char in script_normalizado:
        if char in ("'", '"') and not in_string:
            in_string = True
            string_char = char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
        
        if char == ';' and not in_string:
            stmt = ''.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []
        else:
            current_statement.append(char)
    
    # Agregar el último statement si no termina en ;
    final_stmt = ''.join(current_statement).strip()
    if final_stmt:
        statements.append(final_stmt)
    
    # Filtrar statements vacíos y comentarios puros
    statements = [s for s in statements if s and not s.startswith('--')]
    
    if not statements:
        raise HTTPException(status_code=400, detail="No se encontraron comandos SQL válidos")
    
    logging.info(f"[SCRIPT SQL] Usuario {current_user.get('email')} ejecutando {len(statements)} comandos en {conn_info['name']}")
    
    resultados = []
    exitosos = 0
    fallidos = 0
    
    # Ejecutar cada statement
    import pytds
    
    try:
        # Parsear host y puerto
        host_str = conn_info['host']
        port = conn_info.get('port', 1433)
        
        if ',' in host_str:
            parts = host_str.split(',')
            host = parts[0].strip()
            try:
                port = int(parts[1].strip().split('\\')[0])
            except Exception:
                pass
            if '\\' in host_str:
                host = host_str.split(',')[0].strip()
        else:
            host = host_str
        
        with pytds.connect(
            server=host,
            port=port,
            database=conn_info['database'],
            user=conn_info['username'],
            password=conn_info['password'],
            timeout=60,
            login_timeout=30,
            autocommit=True  # Importante para DDL
        ) as conn:
            cursor = conn.cursor()
            
            for idx, stmt in enumerate(statements):
                stmt_tipo = stmt.split()[0].upper() if stmt.split() else 'UNKNOWN'
                
                try:
                    cursor.execute(stmt)
                    
                    # Si es SELECT, obtener resultados
                    if stmt_tipo == 'SELECT':
                        try:
                            rows = cursor.fetchall()
                            resultados.append({
                                "exito": True,
                                "tipo": stmt_tipo,
                                "mensaje": f"Retornó {len(rows)} filas",
                                "filas_afectadas": len(rows)
                            })
                        except Exception:
                            resultados.append({
                                "exito": True,
                                "tipo": stmt_tipo,
                                "mensaje": "Ejecutado correctamente"
                            })
                    else:
                        # Para DDL/DML, mostrar filas afectadas
                        filas = cursor.rowcount if cursor.rowcount >= 0 else 0
                        resultados.append({
                            "exito": True,
                            "tipo": stmt_tipo,
                            "mensaje": f"{filas} filas afectadas" if filas > 0 else "Ejecutado correctamente",
                            "filas_afectadas": filas
                        })
                    
                    exitosos += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    resultados.append({
                        "exito": False,
                        "tipo": stmt_tipo,
                        "error": error_msg,
                        "statement": stmt[:100] + '...' if len(stmt) > 100 else stmt
                    })
                    fallidos += 1
                    logging.warning(f"[SCRIPT SQL] Error en statement {idx+1}: {error_msg}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
    
    # Guardar log en MongoDB
    await db.script_logs.insert_one({
        "server_id": server_id,
        "server_name": conn_info['name'],
        "titulo": titulo,
        "usuario": current_user.get('email'),
        "fecha": datetime.now(timezone.utc),
        "total_statements": len(statements),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados
    })
    
    return {
        "servidor": conn_info['name'],
        "titulo": titulo,
        "total": len(statements),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados
    }



# ============================================================================
# MÓDULO DE INFORMES DE AUDITORÍA
# Sistema completo para generar, guardar y gestionar informes profesionales
# ============================================================================

import os
import uuid
from datetime import datetime, timezone

# Directorio para almacenar evidencias
EVIDENCIAS_DIR = "/app/uploads/evidencias"
os.makedirs(EVIDENCIAS_DIR, exist_ok=True)

# Modelos Pydantic para Informes de Auditoría
class InformeAuditoriaCreate(BaseModel):
    """Modelo para crear un nuevo informe de auditoría"""
    sucursal_id: str
    sucursal_nombre: str
    almacen_id: str
    almacen_nombre: str
    servidor_id: str
    servidor_nombre: str
    
    # Periodo del análisis
    inventario_inicial_id: str
    inventario_inicial_fecha: str
    inventario_final_id: str
    inventario_final_fecha: str
    fecha_inicio_movimientos: Optional[str] = None
    fecha_fin_movimientos: Optional[str] = None
    
    # Resumen del análisis
    total_productos: int = 0
    productos_con_diferencia: int = 0
    valor_total_diferencias: float = 0
    porcentaje_precision: float = 0
    
    # Contenido del informe
    comentarios: str = ""
    conclusiones: str = ""
    recomendaciones: str = ""
    
    # Opciones
    incluir_comparativo_4_cortes: bool = False
    datos_comparativo: Optional[List[Dict]] = None
    
    # Datos del reporte (productos con diferencias)
    productos_diferencias: Optional[List[Dict]] = None
    
    # Metadatos
    auditor: str = ""
    cargo_auditor: str = ""

class InformeAuditoriaResponse(BaseModel):
    """Modelo de respuesta para informes"""
    id: str
    fecha_creacion: str
    sucursal_nombre: str
    almacen_nombre: str
    periodo: str
    auditor: str
    total_productos: int
    valor_diferencias: float
    tiene_evidencias: bool
    estatus: str


@api_router.post("/auditoria/informes")
async def crear_informe_auditoria(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo informe de auditoría y lo guarda en MongoDB"""
    try:
        informe_id = str(uuid.uuid4())
        ahora = datetime.now(timezone.utc)
        
        # Construir documento del informe
        informe_doc = {
            "id": informe_id,
            "fecha_creacion": ahora.isoformat(),
            "fecha_actualizacion": ahora.isoformat(),
            "estatus": "borrador",
            
            # Ubicación
            "sucursal_id": body.get("sucursal_id"),
            "sucursal_nombre": body.get("sucursal_nombre"),
            "almacen_id": body.get("almacen_id"),
            "almacen_nombre": body.get("almacen_nombre"),
            "servidor_id": body.get("servidor_id"),
            "servidor_nombre": body.get("servidor_nombre"),
            
            # Periodo
            "inventario_inicial_id": body.get("inventario_inicial_id"),
            "inventario_inicial_fecha": body.get("inventario_inicial_fecha"),
            "inventario_final_id": body.get("inventario_final_id"),
            "inventario_final_fecha": body.get("inventario_final_fecha"),
            "fecha_inicio_movimientos": body.get("fecha_inicio_movimientos"),
            "fecha_fin_movimientos": body.get("fecha_fin_movimientos"),
            
            # Resumen numérico
            "total_productos": body.get("total_productos", 0),
            "productos_con_diferencia": body.get("productos_con_diferencia", 0),
            "valor_total_diferencias": body.get("valor_total_diferencias", 0),
            "porcentaje_precision": body.get("porcentaje_precision", 0),
            
            # Contenido textual
            "comentarios": body.get("comentarios", ""),
            "conclusiones": body.get("conclusiones", ""),
            "recomendaciones": body.get("recomendaciones", ""),
            
            # Datos del reporte
            "incluir_comparativo_4_cortes": body.get("incluir_comparativo_4_cortes", False),
            "datos_comparativo": body.get("datos_comparativo"),
            "productos_diferencias": body.get("productos_diferencias"),
            "errores_captura": body.get("errores_captura", []),
            
            # Auditor
            "auditor": body.get("auditor") or current_user.get("name", ""),
            "cargo_auditor": body.get("cargo_auditor", ""),
            "usuario_id": current_user.get("id"),
            
            # Evidencias (se agregan después)
            "evidencias": []
        }
        
        # Guardar en MongoDB
        result = await db.informes_auditoria.insert_one(informe_doc)
        
        return {
            "success": True,
            "message": "Informe creado exitosamente",
            "informe_id": informe_id,
            "mongo_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logging.error(f"Error creando informe de auditoría: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auditoria/informes")
async def listar_informes_auditoria(
    sucursal_id: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    estatus: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """Lista informes de auditoría con filtros opcionales"""
    try:
        # Construir filtro
        filtro = {}
        if sucursal_id:
            filtro["sucursal_id"] = sucursal_id
        if estatus:
            filtro["estatus"] = estatus
        if fecha_desde:
            filtro["fecha_creacion"] = {"$gte": fecha_desde}
        if fecha_hasta:
            if "fecha_creacion" in filtro:
                filtro["fecha_creacion"]["$lte"] = fecha_hasta
            else:
                filtro["fecha_creacion"] = {"$lte": fecha_hasta}
        
        # Contar total
        total = await db.informes_auditoria.count_documents(filtro)
        
        # Obtener informes paginados
        skip = (page - 1) * limit
        cursor = db.informes_auditoria.find(
            filtro,
            {"_id": 0}  # Excluir _id de MongoDB
        ).sort("fecha_creacion", -1).skip(skip).limit(limit)
        
        informes = await cursor.to_list(length=limit)
        
        # Formatear respuesta
        informes_response = []
        for inf in informes:
            informes_response.append({
                "id": inf.get("id"),
                "fecha_creacion": inf.get("fecha_creacion"),
                "sucursal_nombre": inf.get("sucursal_nombre"),
                "almacen_nombre": inf.get("almacen_nombre"),
                "periodo": f"{inf.get('inventario_inicial_fecha', '')} - {inf.get('inventario_final_fecha', '')}",
                "auditor": inf.get("auditor"),
                "total_productos": inf.get("total_productos", 0),
                "productos_con_diferencia": inf.get("productos_con_diferencia", 0),
                "valor_diferencias": inf.get("valor_total_diferencias", 0),
                "tiene_evidencias": len(inf.get("evidencias", [])) > 0,
                "num_evidencias": len(inf.get("evidencias", [])),
                "num_errores_captura": len(inf.get("errores_captura", [])),
                "estatus": inf.get("estatus", "borrador")
            })
        
        return {
            "informes": informes_response,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total > 0 else 1
        }
        
    except Exception as e:
        logging.error(f"Error listando informes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auditoria/informes/{informe_id}")
async def obtener_informe_auditoria(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un informe de auditoría completo por su ID"""
    try:
        informe = await db.informes_auditoria.find_one(
            {"id": informe_id},
            {"_id": 0}
        )
        
        if not informe:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        return informe
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error obteniendo informe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/auditoria/informes/{informe_id}")
async def actualizar_informe_auditoria(
    informe_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un informe de auditoría existente"""
    try:
        # Campos actualizables
        update_fields = {
            "fecha_actualizacion": datetime.now(timezone.utc).isoformat()
        }
        
        campos_permitidos = [
            "comentarios", "conclusiones", "recomendaciones",
            "auditor", "cargo_auditor", "estatus"
        ]
        
        for campo in campos_permitidos:
            if campo in body:
                update_fields[campo] = body[campo]
        
        result = await db.informes_auditoria.update_one(
            {"id": informe_id},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        return {"success": True, "message": "Informe actualizado"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error actualizando informe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/auditoria/informes/{informe_id}")
async def eliminar_informe_auditoria(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un informe de auditoría"""
    try:
        # Primero obtener el informe para eliminar evidencias
        informe = await db.informes_auditoria.find_one({"id": informe_id})
        
        if not informe:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        # Eliminar archivos de evidencias
        for evidencia in informe.get("evidencias", []):
            filepath = evidencia.get("filepath")
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
        
        # Eliminar de MongoDB
        await db.informes_auditoria.delete_one({"id": informe_id})
        
        return {"success": True, "message": "Informe eliminado"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error eliminando informe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auditoria/informes/{informe_id}/evidencias")
async def subir_evidencia(
    informe_id: str,
    file: UploadFile = File(...),
    descripcion: str = Form(""),
    current_user: Dict = Depends(get_current_user)
):
    """Sube una evidencia (foto, PDF, documento) a un informe"""
    try:
        # Verificar que el informe existe
        informe = await db.informes_auditoria.find_one({"id": informe_id})
        if not informe:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        # Validar tipo de archivo
        allowed_types = [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de archivo no permitido: {file.content_type}"
            )
        
        # Generar nombre único para el archivo
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{informe_id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(EVIDENCIAS_DIR, unique_filename)
        
        # Guardar archivo
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Crear registro de evidencia
        evidencia = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "filepath": filepath,
            "content_type": file.content_type,
            "size": len(content),
            "descripcion": descripcion,
            "fecha_subida": datetime.now(timezone.utc).isoformat()
        }
        
        # Agregar al informe
        await db.informes_auditoria.update_one(
            {"id": informe_id},
            {
                "$push": {"evidencias": evidencia},
                "$set": {"fecha_actualizacion": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return {
            "success": True,
            "message": "Evidencia subida exitosamente",
            "evidencia": {
                "id": evidencia["id"],
                "filename": evidencia["filename"],
                "size": evidencia["size"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error subiendo evidencia: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/auditoria/informes/{informe_id}/evidencias/{evidencia_id}")
async def eliminar_evidencia(
    informe_id: str,
    evidencia_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina una evidencia de un informe"""
    try:
        # Obtener informe
        informe = await db.informes_auditoria.find_one({"id": informe_id})
        if not informe:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        # Buscar evidencia
        evidencia_encontrada = None
        for ev in informe.get("evidencias", []):
            if ev.get("id") == evidencia_id:
                evidencia_encontrada = ev
                break
        
        if not evidencia_encontrada:
            raise HTTPException(status_code=404, detail="Evidencia no encontrada")
        
        # Eliminar archivo físico
        filepath = evidencia_encontrada.get("filepath")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        # Eliminar de MongoDB
        await db.informes_auditoria.update_one(
            {"id": informe_id},
            {
                "$pull": {"evidencias": {"id": evidencia_id}},
                "$set": {"fecha_actualizacion": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return {"success": True, "message": "Evidencia eliminada"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error eliminando evidencia: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/auditoria/informes/{informe_id}/finalizar")
async def finalizar_informe(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Marca un informe como finalizado"""
    try:
        result = await db.informes_auditoria.update_one(
            {"id": informe_id},
            {
                "$set": {
                    "estatus": "finalizado",
                    "fecha_finalizacion": datetime.now(timezone.utc).isoformat(),
                    "finalizado_por": current_user.get("name", "")
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        return {"success": True, "message": "Informe finalizado"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error finalizando informe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auditoria/informes/{informe_id}/pdf")
async def generar_pdf_informe(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Genera un PDF profesional del informe de auditoría"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from io import BytesIO
    
    try:
        # Obtener informe
        informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
        if not informe:
            raise HTTPException(status_code=404, detail="Informe no encontrado")
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='TitleCustom',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a1a1a')
        ))
        
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontSize=13,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor('#2563eb'),
            borderColor=colors.HexColor('#2563eb'),
            borderWidth=0,
            borderPadding=0
        ))
        
        styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='SmallGray',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666')
        ))
        
        # Contenido del PDF
        elements = []
        
        # === ENCABEZADO ===
        elements.append(Paragraph("INFORME DE AUDITORÍA DE INVENTARIOS", styles['TitleCustom']))
        elements.append(Paragraph("EDARSA HUB - Sistema de Gestión", styles['Subtitle']))
        elements.append(Spacer(1, 20))
        
        # === DATOS GENERALES ===
        fecha_creacion = informe.get('fecha_creacion', '')[:10] if informe.get('fecha_creacion') else ''
        
        datos_generales = [
            ['INFORMACIÓN GENERAL', ''],
            ['Sucursal:', informe.get('sucursal_nombre', 'N/A')],
            ['Almacén:', informe.get('almacen_nombre', 'N/A')],
            ['Fecha del Informe:', fecha_creacion],
            ['Auditor:', informe.get('auditor', 'N/A')],
            ['Cargo:', informe.get('cargo_auditor', 'N/A')],
        ]
        
        table_datos = Table(datos_generales, colWidths=[2*inch, 4.5*inch])
        table_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table_datos)
        elements.append(Spacer(1, 15))
        
        # === PERIODO ANALIZADO ===
        periodo_data = [
            ['PERIODO ANALIZADO', ''],
            ['Inventario Inicial:', f"{informe.get('inventario_inicial_fecha', 'N/A')}"],
            ['Inventario Final:', f"{informe.get('inventario_final_fecha', 'N/A')}"],
            ['Inicio Movimientos:', f"{informe.get('fecha_inicio_movimientos', 'N/A')}"],
            ['Fin Movimientos:', f"{informe.get('fecha_fin_movimientos', 'N/A')}"],
        ]
        
        table_periodo = Table(periodo_data, colWidths=[2*inch, 4.5*inch])
        table_periodo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_periodo)
        elements.append(Spacer(1, 15))
        
        # === RESUMEN EJECUTIVO ===
        total_prod = informe.get('total_productos', 0)
        prod_dif = informe.get('productos_con_diferencia', 0)
        valor_dif = informe.get('valor_total_diferencias', 0)
        precision = informe.get('porcentaje_precision', 0)
        
        resumen_data = [
            ['RESUMEN EJECUTIVO', '', '', ''],
            ['Total Productos', 'Con Diferencia', 'Valor Diferencias', '% Precisión'],
            [str(total_prod), str(prod_dif), f"${valor_dif:,.2f}", f"{precision:.1f}%"],
        ]
        
        table_resumen = Table(resumen_data, colWidths=[1.625*inch]*4)
        table_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('FONTSIZE', (0, 2), (-1, 2), 14),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e9ecef')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table_resumen)
        elements.append(Spacer(1, 20))
        
        # === COMENTARIOS ===
        if informe.get('comentarios'):
            elements.append(Paragraph("COMENTARIOS DEL AUDITOR", styles['SectionTitle']))
            elements.append(Paragraph(informe.get('comentarios', ''), styles['BodyJustified']))
            elements.append(Spacer(1, 10))
        
        # === CONCLUSIONES ===
        if informe.get('conclusiones'):
            elements.append(Paragraph("CONCLUSIONES", styles['SectionTitle']))
            elements.append(Paragraph(informe.get('conclusiones', ''), styles['BodyJustified']))
            elements.append(Spacer(1, 10))
        
        # === RECOMENDACIONES ===
        if informe.get('recomendaciones'):
            elements.append(Paragraph("RECOMENDACIONES", styles['SectionTitle']))
            elements.append(Paragraph(informe.get('recomendaciones', ''), styles['BodyJustified']))
            elements.append(Spacer(1, 10))
        
        # === PRODUCTOS CON DIFERENCIAS (Top 20) ===
        productos = informe.get('productos_diferencias', [])
        if productos and len(productos) > 0:
            elements.append(PageBreak())
            elements.append(Paragraph("DETALLE DE PRODUCTOS CON DIFERENCIAS", styles['SectionTitle']))
            elements.append(Paragraph(f"Mostrando los primeros {min(20, len(productos))} productos con mayor diferencia", styles['SmallGray']))
            elements.append(Spacer(1, 10))
            
            # Encabezados de tabla
            prod_headers = ['Código', 'Producto', 'Inv. Ini', 'Inv. Fin', 'Diferencia', 'Valor']
            prod_data = [prod_headers]
            
            # Top 20 productos
            for prod in productos[:20]:
                prod_data.append([
                    str(prod.get('codigo', ''))[:10],
                    str(prod.get('producto', ''))[:25],
                    str(prod.get('inv_inicial', 0)),
                    str(prod.get('inv_final', 0)),
                    str(prod.get('diferencia', 0)),
                    f"${prod.get('valor_diferencia', 0):,.2f}"
                ])
            
            col_widths = [0.8*inch, 2.5*inch, 0.7*inch, 0.7*inch, 0.8*inch, 1*inch]
            table_prod = Table(prod_data, colWidths=col_widths)
            table_prod.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            elements.append(table_prod)
        
        # === ERRORES DE CAPTURA DE INVENTARIO ===
        errores_captura = informe.get('errores_captura', [])
        if errores_captura and len(errores_captura) > 0:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(
                f"ERRORES DE CAPTURA DE INVENTARIO ({len(errores_captura)} detectados)", 
                styles['SectionTitle']
            ))
            
            # Encabezados
            err_headers = ['Código', 'Producto', 'Tipo Error', 'Cantidad', 'Detalle']
            err_data = [err_headers]
            
            # Mostrar hasta 15 errores
            for err in errores_captura[:15]:
                err_data.append([
                    str(err.get('codigo', ''))[:12],
                    str(err.get('producto', ''))[:30],
                    str(err.get('tipo_error', 'Error'))[:15],
                    str(err.get('inv_capturado', '')),
                    str(err.get('detalle', ''))[:25]
                ])
            
            err_col_widths = [0.9*inch, 2.2*inch, 1*inch, 0.7*inch, 1.7*inch]
            table_err = Table(err_data, colWidths=err_col_widths)
            table_err.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f5c6cb')),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(table_err)
            
            if len(errores_captura) > 15:
                elements.append(Paragraph(
                    f"... y {len(errores_captura) - 15} errores adicionales no mostrados en este documento.",
                    styles['SmallGray']
                ))
        
        # === EVIDENCIAS ===
        evidencias = informe.get('evidencias', [])
        if evidencias:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("EVIDENCIAS ADJUNTAS", styles['SectionTitle']))
            
            ev_data = [['#', 'Archivo', 'Descripción', 'Fecha']]
            for i, ev in enumerate(evidencias, 1):
                fecha_ev = ev.get('fecha_subida', '')[:10] if ev.get('fecha_subida') else ''
                ev_data.append([
                    str(i),
                    ev.get('filename', '')[:30],
                    ev.get('descripcion', '')[:40],
                    fecha_ev
                ])
            
            table_ev = Table(ev_data, colWidths=[0.4*inch, 2.5*inch, 2.5*inch, 1.1*inch])
            table_ev.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table_ev)
        
        # === PIE DE PÁGINA ===
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("_" * 80, styles['SmallGray']))
        elements.append(Paragraph(
            f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | EDARSA HUB | Confidencial",
            styles['SmallGray']
        ))
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar respuesta
        buffer.seek(0)
        filename = f"Informe_Auditoria_{informe.get('sucursal_nombre', 'X')}_{fecha_creacion}.pdf"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# MÓDULO DE RECURSOS HUMANOS - Endpoints
# Conecta con tablas RH_* en EDARSAHUB SQL Server
# ============================================================================

# ID del servidor EDARSA HUB
EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

async def execute_edarsa_hub_query(query: str):
    """
    Helper para ejecutar queries en EDARSA HUB.
    
    CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C / LOTE 1:
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    para usar EDARSAHUB SQL como fuente primaria.
    """
    from core.server_registry import get_server_connection_info
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    conn_info = await get_server_connection_info(EDARSA_HUB_SERVER_ID, db=db)
    
    if not conn_info:
        logging.error(f"[EDARSA_HUB_QUERY] Servidor EDARSA HUB no encontrado via registry. ID={EDARSA_HUB_SERVER_ID}")
        raise HTTPException(status_code=404, detail="Servidor EDARSA HUB no configurado")
    
    logging.debug(f"[EDARSA_HUB_QUERY] Conexión obtenida via registry. Origin={conn_info.get('config_origin', 'UNKNOWN')}")
    
    try:
        result = execute_sql_query(
            conn_info['host'], 
            conn_info['port'], 
            conn_info['database'], 
            conn_info['username'], 
            conn_info['password'], 
            query
        )
        return {"datos": result, "registros": len(result)}
    except Exception as e:
        logging.error(f"Error en query EDARSA HUB: {e}")
        raise HTTPException(status_code=500, detail=f"Error en consulta: {str(e)}")


# ------------ CATÁLOGOS RH - MIGRADO A modules/rh/ ------------
# FASE 6B (Diciembre 2025): Los siguientes 10 endpoints fueron migrados a modules/rh/
# con queries parametrizados y validación Pydantic:
# - GET    /rrhh/catalogos/puestos -> modules/rh/routes.py
# - POST   /rrhh/catalogos/puestos -> modules/rh/routes.py
# - PUT    /rrhh/catalogos/puestos/{id} -> modules/rh/routes.py
# - DELETE /rrhh/catalogos/puestos/{id} -> modules/rh/routes.py
# - GET    /rrhh/catalogos/sucursales -> modules/rh/routes.py
# - GET    /rrhh/catalogos/tipos-incidencias -> modules/rh/routes.py
# - POST   /rrhh/catalogos/tipos-incidencias -> modules/rh/routes.py
# - PUT    /rrhh/catalogos/tipos-incidencias/{id} -> modules/rh/routes.py
# - DELETE /rrhh/catalogos/tipos-incidencias/{id} -> modules/rh/routes.py
# - GET    /rrhh/catalogos/script-inicializacion -> modules/rh/routes.py

# ENDPOINT /rrhh/catalogos/puestos - MIGRADO A modules/rh/routes.py
# @api_router.get("/rrhh/catalogos/puestos")
# async def rrhh_listar_puestos(current_user: Dict = Depends(get_current_user)):
#     """Lista catálogo de puestos desde RH_Cat_Puestos"""
#     query = """
#         SELECT 
#             PuestoID,
#             Descripcion,
#             Departamento,
#             Sueldo_Base_Seman_SBC
#         FROM RH_Cat_Puestos
#         ORDER BY Departamento, Descripcion
#     """
#     result = await execute_edarsa_hub_query(query)
#     return {"puestos": result.get("datos", []), "total": result.get("registros", 0)}


# ENDPOINT /rrhh/catalogos/sucursales - MIGRADO A modules/rh/routes.py
# @api_router.get("/rrhh/catalogos/sucursales")
# async def rrhh_listar_sucursales(current_user: Dict = Depends(get_current_user)):
#     """Lista catálogo de sucursales desde RH_Cat_Sucursales"""
#     query = """
#         SELECT 
#             s.SucursalID,
#             s.Nombre_Sucursal,
#             s.Ciudad,
#             s.Activa,
#             sf.RFC,
#             sf.RazonSocial
#         FROM RH_Cat_Sucursales s
#         LEFT JOIN RH_Cat_SucursalesFiscal sf ON s.SucursalID = sf.SucursalID AND sf.Activo = 1
#         ORDER BY s.Nombre_Sucursal
#     """
#     result = await execute_edarsa_hub_query(query)
#     return {"sucursales": result.get("datos", []), "total": result.get("registros", 0)}


# ------------ CATÁLOGOS CRUD (ADMIN ONLY) - MIGRADO A modules/rh/ ------------
# FASE 6B: La función check_admin_role está replicada en modules/rh/service.py

# def check_admin_role(current_user: Dict):
#     """Verifica que el usuario tenga rol de Administrador"""
#     if current_user.get('role') != 'Administrador':
#         raise HTTPException(status_code=403, detail="Solo administradores pueden realizar esta acción")


# ENDPOINT POST /rrhh/catalogos/puestos - MIGRADO A modules/rh/routes.py
# @api_router.post("/rrhh/catalogos/puestos")
# async def rrhh_crear_puesto(
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Crea un nuevo puesto en el catálogo (Solo Administrador)"""
#     check_admin_role(current_user)
#     
#     descripcion = body.get('descripcion', '').strip()
#     departamento = body.get('departamento', '').strip()
#     sueldo_base = body.get('sueldo_base', 0)
#     nomipaq_id = body.get('nomipaq_id', '')  # ID para mapeo con NomiPAQ
#     mpro_id = body.get('mpro_id', '')  # ID para mapeo con MPRO
#     
#     if not descripcion:
#         raise HTTPException(status_code=400, detail="La descripción del puesto es requerida")
#     
#     # VULNERABILIDAD SQL INJECTION - CORREGIDA EN modules/rh/repository.py
#     query = f"""
#         INSERT INTO RH_Cat_Puestos 
#         (Descripcion, Departamento, Sueldo_Base_Seman_SBC, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
#         OUTPUT INSERTED.PuestoID
#         VALUES 
#         ('{descripcion}', '{departamento}', {sueldo_base}, '{nomipaq_id}', '{mpro_id}', GETDATE(), '{current_user.get("email", "")}')
#     """
#     
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Puesto creado"}


# ENDPOINT PUT /rrhh/catalogos/puestos/{puesto_id} - MIGRADO A modules/rh/routes.py
# @api_router.put("/rrhh/catalogos/puestos/{puesto_id}")
# async def rrhh_actualizar_puesto(
#     puesto_id: int,
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Actualiza un puesto existente (Solo Administrador)"""
#     check_admin_role(current_user)
#     
#     updates = []
#     if 'descripcion' in body:
#         updates.append(f"Descripcion = '{body['descripcion']}'")
#     if 'departamento' in body:
#         updates.append(f"Departamento = '{body['departamento']}'")
#     if 'sueldo_base' in body:
#         updates.append(f"Sueldo_Base_Seman_SBC = {body['sueldo_base']}")
#     if 'nomipaq_id' in body:
#         updates.append(f"NomiPAQ_ID = '{body['nomipaq_id']}'")
#     if 'mpro_id' in body:
#         updates.append(f"MPRO_ID = '{body['mpro_id']}'")
#     
#     if not updates:
#         raise HTTPException(status_code=400, detail="No hay campos para actualizar")
#     
#     # VULNERABILIDAD SQL INJECTION - CORREGIDA EN modules/rh/repository.py
#     query = f"""
#         UPDATE RH_Cat_Puestos
#         SET {', '.join(updates)}, Fecha_Modificacion = GETDATE()
#         WHERE PuestoID = {puesto_id}
#     """
#     
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Puesto actualizado"}


# ENDPOINT DELETE /rrhh/catalogos/puestos/{puesto_id} - MIGRADO A modules/rh/routes.py
# @api_router.delete("/rrhh/catalogos/puestos/{puesto_id}")
# async def rrhh_eliminar_puesto(
#     puesto_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Elimina un puesto del catálogo (Solo Administrador)"""
#     check_admin_role(current_user)
#     
#     # Verificar si hay colaboradores con este puesto
#     query_check = f"SELECT COUNT(*) as total FROM RH_Colaboradores_Expediente WHERE PuestoID = {puesto_id}"
#     result = await execute_edarsa_hub_query(query_check)
#     if result.get('datos', [{}])[0].get('total', 0) > 0:
#         raise HTTPException(status_code=400, detail="No se puede eliminar: hay colaboradores asignados a este puesto")
#     
#     query = f"DELETE FROM RH_Cat_Puestos WHERE PuestoID = {puesto_id}"
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Puesto eliminado"}


# ------------ CATÁLOGO DE TIPOS DE INCIDENCIAS - MIGRADO A modules/rh/ ------------

# ENDPOINT GET /rrhh/catalogos/tipos-incidencias - MIGRADO A modules/rh/routes.py
# @api_router.get("/rrhh/catalogos/tipos-incidencias")
# async def rrhh_listar_tipos_incidencias(current_user: Dict = Depends(get_current_user)):
#     """Lista catálogo de tipos de incidencias"""
#     query = """
#         SELECT 
#             TipoIncidenciaID,
#             Codigo,
#             Descripcion,
#             Categoria,
#             Afectacion,
#             Calculo_Monto,
#             Activo,
#             NomiPAQ_ID,
#             MPRO_ID
#         FROM RH_Cat_Tipos_Incidencias
#         WHERE Activo = 1
#         ORDER BY Categoria, Descripcion
#     """
#     try:
#         result = await execute_edarsa_hub_query(query)
#         return {"tipos_incidencias": result.get("datos", []), "total": result.get("registros", 0)}
#     except Exception:
#         # Si la tabla no existe, retornar tipos por defecto
#         tipos_default = [
#             {"TipoIncidenciaID": 1, "Codigo": "BON", "Descripcion": "Bono", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
#             {"TipoIncidenciaID": 2, "Codigo": "HEX", "Descripcion": "Horas Extra", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
#             {"TipoIncidenciaID": 3, "Codigo": "COM", "Descripcion": "Comisión", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
#             {"TipoIncidenciaID": 4, "Codigo": "FAL", "Descripcion": "Falta", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
#             {"TipoIncidenciaID": 5, "Codigo": "RET", "Descripcion": "Retardo", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
#             {"TipoIncidenciaID": 6, "Codigo": "DES", "Descripcion": "Descuento", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
#         ]
#         return {"tipos_incidencias": tipos_default, "total": len(tipos_default), "nota": "Usando tipos por defecto - Ejecute script SQL"}


# ENDPOINT POST /rrhh/catalogos/tipos-incidencias - MIGRADO A modules/rh/routes.py
# @api_router.post("/rrhh/catalogos/tipos-incidencias")
# async def rrhh_crear_tipo_incidencia(
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Crea un nuevo tipo de incidencia (Solo Administrador)"""
#     check_admin_role(current_user)
#     
#     codigo = body.get('codigo', '').strip().upper()
#     descripcion = body.get('descripcion', '').strip()
#     categoria = body.get('categoria', 'Descuento')  # Ingreso o Descuento
#     afectacion = 1 if categoria == 'Ingreso' else -1
#     calculo_monto = body.get('calculo_monto', 'Manual')  # Manual, Porcentaje, Formula
#     nomipaq_id = body.get('nomipaq_id', '')
#     mpro_id = body.get('mpro_id', '')
#     
#     if not codigo or not descripcion:
#         raise HTTPException(status_code=400, detail="Código y descripción son requeridos")
#     
#     # VULNERABILIDAD SQL INJECTION - CORREGIDA EN modules/rh/repository.py
#     query = f"""
#         INSERT INTO RH_Cat_Tipos_Incidencias 
#         (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto, Activo, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
#         VALUES 
#         ('{codigo}', '{descripcion}', '{categoria}', {afectacion}, '{calculo_monto}', 1, '{nomipaq_id}', '{mpro_id}', GETDATE(), '{current_user.get("email", "")}')
#     """
#     
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Tipo de incidencia creado"}


# ENDPOINT PUT /rrhh/catalogos/tipos-incidencias/{tipo_id} - MIGRADO A modules/rh/routes.py
# @api_router.put("/rrhh/catalogos/tipos-incidencias/{tipo_id}")
# async def rrhh_actualizar_tipo_incidencia(
#     tipo_id: int,
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Actualiza un tipo de incidencia (Solo Administrador)"""
#     check_admin_role(current_user)
#     
#     updates = []
#     if 'codigo' in body:
#         updates.append(f"Codigo = '{body['codigo'].upper()}'")
#     if 'descripcion' in body:
#         updates.append(f"Descripcion = '{body['descripcion']}'")
#     if 'categoria' in body:
#         updates.append(f"Categoria = '{body['categoria']}'")
#         updates.append(f"Afectacion = {1 if body['categoria'] == 'Ingreso' else -1}")
#     if 'calculo_monto' in body:
#         updates.append(f"Calculo_Monto = '{body['calculo_monto']}'")
#     if 'activo' in body:
#         updates.append(f"Activo = {1 if body['activo'] else 0}")
#     if 'nomipaq_id' in body:
#         updates.append(f"NomiPAQ_ID = '{body['nomipaq_id']}'")
#     if 'mpro_id' in body:
#         updates.append(f"MPRO_ID = '{body['mpro_id']}'")
#     
#     if not updates:
#         raise HTTPException(status_code=400, detail="No hay campos para actualizar")
#     
#     # VULNERABILIDAD SQL INJECTION - CORREGIDA EN modules/rh/repository.py
#     query = f"""
#         UPDATE RH_Cat_Tipos_Incidencias
#         SET {', '.join(updates)}, Fecha_Modificacion = GETDATE()
#         WHERE TipoIncidenciaID = {tipo_id}
#     """
#     
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Tipo de incidencia actualizado"}


# ENDPOINT DELETE /rrhh/catalogos/tipos-incidencias/{tipo_id} - MIGRADO A modules/rh/routes.py
# @api_router.delete("/rrhh/catalogos/tipos-incidencias/{tipo_id}")
# async def rrhh_eliminar_tipo_incidencia(
#     tipo_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Desactiva un tipo de incidencia (Solo Administrador) - No elimina para mantener histórico"""
#     check_admin_role(current_user)
#     
#     query = f"UPDATE RH_Cat_Tipos_Incidencias SET Activo = 0, Fecha_Modificacion = GETDATE() WHERE TipoIncidenciaID = {tipo_id}"
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Tipo de incidencia desactivado"}


# ------------ SCRIPT INICIALIZACIÓN CATÁLOGOS RRHH - MIGRADO A modules/rh/ ------------

# ENDPOINT GET /rrhh/catalogos/script-inicializacion - MIGRADO A modules/rh/routes.py
# El script SQL completo está ahora en modules/rh/service.py (SCRIPT_INICIALIZACION_SQL)
# @api_router.get("/rrhh/catalogos/script-inicializacion")
# async def rrhh_catalogos_script(current_user: Dict = Depends(get_current_user)):
#     """Retorna el script SQL para crear/actualizar las tablas de catálogos RRHH"""
#     return {...}


# ------------ COLABORADORES - MIGRADO A modules/rh/ ------------
# FASE 6C-B (Diciembre 2025): Los siguientes 5 endpoints fueron migrados a modules/rh/
# con queries parametrizados nativos y validación Pydantic (CURP, RFC, CLABE):
# - GET    /rrhh/colaboradores -> modules/rh/routes.py
# - GET    /rrhh/colaboradores/{colaborador_id} -> modules/rh/routes.py
# - POST   /rrhh/colaboradores -> modules/rh/routes.py
# - PUT    /rrhh/colaboradores/{colaborador_id} -> modules/rh/routes.py
# - DELETE /rrhh/colaboradores/{colaborador_id} -> modules/rh/routes.py

# ENDPOINT /rrhh/colaboradores - MIGRADO
# @api_router.get("/rrhh/colaboradores")
# async def rrhh_listar_colaboradores(...):
#     """Lista colaboradores con filtros opcionales"""
#     # VULNERABILIDAD SQL INJECTION CORREGIDA: Queries ahora usan parámetros nativos
#     # y escape_sql_string() solo para búsqueda LIKE
#     pass

# ENDPOINT /rrhh/colaboradores/{colaborador_id} - MIGRADO
# @api_router.get("/rrhh/colaboradores/{colaborador_id}")
# async def rrhh_obtener_colaborador(...):
#     """Obtiene detalle de un colaborador con incidencias y asistencias"""
#     # VULNERABILIDAD SQL INJECTION CORREGIDA: Queries ahora usan parámetros nativos
#     pass

# ENDPOINT POST /rrhh/colaboradores - MIGRADO
# @api_router.post("/rrhh/colaboradores")
# async def rrhh_crear_colaborador(...):
#     """Crea un nuevo colaborador"""
#     # VULNERABILIDAD SQL INJECTION CORREGIDA: Queries ahora usan parámetros nativos
#     # VALIDACIÓN AGREGADA: Pydantic valida CURP, RFC, CLABE
#     pass

# ENDPOINT PUT /rrhh/colaboradores/{colaborador_id} - MIGRADO
# @api_router.put("/rrhh/colaboradores/{colaborador_id}")
# async def rrhh_actualizar_colaborador(...):
#     """Actualiza datos de un colaborador"""
#     # VULNERABILIDAD SQL INJECTION CORREGIDA: escape_sql_string() + validación enteros
#     pass

# ENDPOINT DELETE /rrhh/colaboradores/{colaborador_id} - MIGRADO
# @api_router.delete("/rrhh/colaboradores/{colaborador_id}")
# async def rrhh_dar_baja_colaborador(...):
#     """Da de baja lógica a un colaborador"""
#     # VULNERABILIDAD SQL INJECTION CORREGIDA: Queries ahora usan parámetros nativos
#     pass


# ------------ INCIDENCIAS - MIGRADO A modules/rh/ ------------
# FASE 6D-B (Diciembre 2025): Los siguientes 4 endpoints fueron migrados a modules/rh/
# con queries parametrizados y validación contra catálogo RH_Cat_Tipos_Incidencias:
# - GET  /rrhh/incidencias -> modules/rh/routes.py
# - POST /rrhh/incidencias -> modules/rh/routes.py
# - POST /rrhh/incidencias/importar-excel -> modules/rh/routes.py
# - GET  /rrhh/incidencias/plantilla-excel -> modules/rh/routes.py
#
# COMPORTAMIENTO IMPORTACIÓN EXCEL:
# - La importación es PARCIAL, NO transaccional
# - Si una fila falla, las anteriores ya fueron insertadas
# - Documentado en ImportacionExcelResponse
#
# VALIDACIÓN DE TIPOS:
# - Fuente principal: RH_Cat_Tipos_Incidencias (catálogo)
# - Fallback: Lista TIPOS_INCIDENCIA_FALLBACK cuando catálogo no está disponible


# ------------ ASISTENCIA (RELOJ CHECADOR) ------------

# ============================================================================
# ENDPOINTS DE ASISTENCIA - COMENTADOS (FASE 6E-B)
# ============================================================================
# Migrados a: modules/rh/routes.py
# Fecha: Diciembre 2025
#
# IMPORTANTE: No eliminar este código comentado hasta que el usuario lo autorice.
# Los endpoints ahora funcionan desde el módulo modular con:
# - Validación Pydantic (tipo_registro: Entrada/Salida)
# - Queries parametrizados (prevención SQL Injection)
# - Mismos contratos de API
# ============================================================================

# @api_router.get("/rrhh/asistencia")
# async def rrhh_listar_asistencias(
#     colaborador_id: Optional[int] = None,
#     sucursal_id: Optional[int] = None,
#     fecha: Optional[str] = None,
#     fecha_desde: Optional[str] = None,
#     fecha_hasta: Optional[str] = None,
#     page: int = Query(1, ge=1),
#     limit: int = Query(100, ge=1, le=500),
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Lista registros del reloj checador"""
#     
#     conditions = ["1=1"]
#     if colaborador_id:
#         conditions.append(f"r.ColaboradorID = {colaborador_id}")
#     if sucursal_id:
#         conditions.append(f"c.SucursalID = {sucursal_id}")
#     if fecha:
#         conditions.append(f"CAST(r.FechaHora AS DATE) = '{fecha}'")
#     if fecha_desde:
#         conditions.append(f"CAST(r.FechaHora AS DATE) >= '{fecha_desde}'")
#     if fecha_hasta:
#         conditions.append(f"CAST(r.FechaHora AS DATE) <= '{fecha_hasta}'")
#     
#     where_clause = " AND ".join(conditions)
#     offset = (page - 1) * limit
#     
#     query = f"""
#         SELECT 
#             r.CheckID,
#             r.ColaboradorID,
#             c.Nombre_Completo,
#             c.SucursalID,
#             s.Nombre_Sucursal,
#             p.Descripcion as Puesto,
#             r.Tipo_Registro,
#             r.FechaHora,
#             r.Geolocalizacion,
#             r.Validado_Gerencia
#         FROM RH_Reloj_Checador r
#         LEFT JOIN RH_Colaboradores_Expediente c ON r.ColaboradorID = c.ColaboradorID
#         LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
#         LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
#         WHERE {where_clause}
#         ORDER BY r.FechaHora DESC
#         OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
#     """
#     
#     result = await execute_edarsa_hub_query(query)
#     
#     return {
#         "asistencias": result.get("datos", []),
#         "total": result.get("registros", 0),
#         "page": page,
#         "limit": limit
#     }


# @api_router.post("/rrhh/asistencia")
# async def rrhh_registrar_asistencia(
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Registra una entrada o salida"""
#     
#     colaborador_id = body.get('colaborador_id')
#     tipo = body.get('tipo_registro')  # "Entrada" o "Salida"
#     geo = body.get('geolocalizacion')
#     
#     if not colaborador_id or not tipo:
#         raise HTTPException(status_code=400, detail="Colaborador y tipo son requeridos")
#     
#     query = f"""
#         INSERT INTO RH_Reloj_Checador 
#         (ColaboradorID, Tipo_Registro, FechaHora, Geolocalizacion, Validado_Gerencia)
#         OUTPUT INSERTED.CheckID
#         VALUES 
#         ({colaborador_id}, '{tipo}', GETDATE(), {f"'{geo}'" if geo else 'NULL'}, 0)
#     """
#     
#     result = await execute_edarsa_hub_query(query)
#     
#     return {
#         "success": True,
#         "message": "Asistencia registrada",
#         "check_id": result.get("datos", [{}])[0].get("CheckID") if result.get("datos") else None
#     }


# @api_router.put("/rrhh/asistencia/{check_id}/validar")
# async def rrhh_validar_asistencia(
#     check_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Valida un registro de asistencia (gerencia)"""
#     
#     query = f"""
#         UPDATE RH_Reloj_Checador
#         SET Validado_Gerencia = 1
#         WHERE CheckID = {check_id}
#     """
#     
#     await execute_edarsa_hub_query(query)
#     
#     return {"success": True, "message": "Asistencia validada"}


# ------------ FLUJO DE NÓMINA ------------
# ============================================================================
# ENDPOINTS DE FLUJO NÓMINA - COMENTADOS (FASE 6F-B)
# ============================================================================
# Migrados a: modules/rh/routes.py
# Fecha: Diciembre 2025
#
# IMPORTANTE: No eliminar este código comentado hasta que el usuario lo autorice.
# Los endpoints ahora funcionan desde el módulo modular con:
# - Validación Pydantic (sucursal_id, semana_anio, motivo_rechazo)
# - Validación de transiciones de estado (previene saltos absurdos)
# - Queries parametrizados (prevención SQL Injection)
# - Mismos contratos de API
# ============================================================================

# @api_router.get("/rrhh/nominas/flujo")
# async def rrhh_listar_flujos_nomina(
#     sucursal_id: Optional[int] = None,
#     semana_anio: Optional[int] = None,
#     estatus: Optional[str] = None,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Lista flujos de nómina por sucursal"""
#     
#     conditions = ["1=1"]
#     if sucursal_id:
#         conditions.append(f"f.SucursalID = {sucursal_id}")
#     if semana_anio:
#         conditions.append(f"f.Semana_Anio = {semana_anio}")
#     if estatus:
#         conditions.append(f"f.Estatus_Flujo = '{estatus}'")
#     
#     where_clause = " AND ".join(conditions)
#     
#     query = f"""
#         SELECT 
#             f.FlujoID,
#             f.SucursalID,
#             s.Nombre_Sucursal,
#             f.Semana_Anio,
#             f.Estatus_Flujo,
#             f.Hora_Entrega_RH,
#             f.Hora_Validacion_Gerente,
#             f.Hora_Autorizacion_DG,
#             f.Hora_Envio_Tesoreria,
#             f.Hora_Pago_Ejecutado,
#             f.Motivo_Rechazo_Gerente,
#             f.Intentos_Reenvio
#         FROM RH_Flujo_Nomina_Sucursal f
#         LEFT JOIN RH_Cat_Sucursales s ON f.SucursalID = s.SucursalID
#         WHERE {where_clause}
#         ORDER BY f.Semana_Anio DESC, s.Nombre_Sucursal
#     """
#     
#     result = await execute_edarsa_hub_query(query)
#     
#     return {
#         "flujos": result.get("datos", []),
#         "total": result.get("registros", 0)
#     }


# @api_router.post("/rrhh/nominas/flujo")
# async def rrhh_crear_flujo_nomina(
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Crea un nuevo periodo de nómina para una sucursal"""
#     
#     sucursal_id = body.get('sucursal_id')
#     semana_anio = body.get('semana_anio')  # Formato: 202614 (año + semana)
#     
#     if not sucursal_id or not semana_anio:
#         raise HTTPException(status_code=400, detail="Sucursal y semana son requeridos")
#     
#     # Verificar si ya existe
#     check_query = f"""
#         SELECT FlujoID FROM RH_Flujo_Nomina_Sucursal 
#         WHERE SucursalID = {sucursal_id} AND Semana_Anio = {semana_anio}
#     """
#     existing = await execute_edarsa_hub_query(check_query)
#     
#     if existing.get("datos"):
#         raise HTTPException(status_code=400, detail="Ya existe un flujo para esta sucursal y semana")
#     
#     query = f"""
#         INSERT INTO RH_Flujo_Nomina_Sucursal 
#         (SucursalID, Semana_Anio, Estatus_Flujo, Intentos_Reenvio)
#         OUTPUT INSERTED.FlujoID
#         VALUES 
#         ({sucursal_id}, {semana_anio}, 'Captura', 0)
#     """
#     
#     result = await execute_edarsa_hub_query(query)
#     
#     return {
#         "success": True,
#         "message": "Flujo de nómina creado",
#         "flujo_id": result.get("datos", [{}])[0].get("FlujoID") if result.get("datos") else None
#     }


# @api_router.put("/rrhh/nominas/flujo/{flujo_id}/enviar-rh")
# async def rrhh_enviar_nomina_rh(
#     flujo_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Marca la nómina como enviada a RH"""
#     query = f"""
#         UPDATE RH_Flujo_Nomina_Sucursal
#         SET Estatus_Flujo = 'Enviado_RH', Hora_Entrega_RH = GETDATE()
#         WHERE FlujoID = {flujo_id}
#     """
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Nómina enviada a RH"}


# @api_router.put("/rrhh/nominas/flujo/{flujo_id}/validar-gerente")
# async def rrhh_validar_nomina_gerente(
#     flujo_id: int,
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Validación de nómina por gerente"""
#     aprobado = body.get('aprobado', True)
#     motivo = body.get('motivo_rechazo', '')
#     
#     if aprobado:
#         query = f"""
#             UPDATE RH_Flujo_Nomina_Sucursal
#             SET Estatus_Flujo = 'Validacion_Gerente', 
#                 Hora_Validacion_Gerente = GETDATE(),
#                 Motivo_Rechazo_Gerente = NULL
#             WHERE FlujoID = {flujo_id}
#         """
#     else:
#         query = f"""
#             UPDATE RH_Flujo_Nomina_Sucursal
#             SET Estatus_Flujo = 'Rechazado_Gerente', 
#                 Motivo_Rechazo_Gerente = '{motivo or "Sin especificar"}',
#                 Intentos_Reenvio = Intentos_Reenvio + 1
#             WHERE FlujoID = {flujo_id}
#         """
#     
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Nómina validada" if aprobado else "Nómina rechazada"}


# @api_router.put("/rrhh/nominas/flujo/{flujo_id}/autorizar-dg")
# async def rrhh_autorizar_nomina_dg(
#     flujo_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Autorización de nómina por Dirección General"""
#     query = f"""
#         UPDATE RH_Flujo_Nomina_Sucursal
#         SET Estatus_Flujo = 'Autorizacion_DG', Hora_Autorizacion_DG = GETDATE()
#         WHERE FlujoID = {flujo_id}
#     """
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Nómina autorizada por DG"}


# @api_router.put("/rrhh/nominas/flujo/{flujo_id}/enviar-tesoreria")
# async def rrhh_enviar_nomina_tesoreria(
#     flujo_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Envía nómina a tesorería para pago"""
#     query = f"""
#         UPDATE RH_Flujo_Nomina_Sucursal
#         SET Estatus_Flujo = 'Enviado_Tesoreria', Hora_Envio_Tesoreria = GETDATE()
#         WHERE FlujoID = {flujo_id}
#     """
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Nómina enviada a tesorería"}


# @api_router.put("/rrhh/nominas/flujo/{flujo_id}/marcar-pagado")
# async def rrhh_marcar_nomina_pagada(
#     flujo_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Marca la nómina como pagada"""
#     query = f"""
#         UPDATE RH_Flujo_Nomina_Sucursal
#         SET Estatus_Flujo = 'Pagado', Hora_Pago_Ejecutado = GETDATE()
#         WHERE FlujoID = {flujo_id}
#     """
#     await execute_edarsa_hub_query(query)
#     return {"success": True, "message": "Nómina marcada como pagada"}


# ------------ AUDITORÍA FISCAL ------------

# ============================================================================
# ENDPOINTS DE AUDITORÍA FISCAL - COMENTADOS (FASE 6G-B)
# ============================================================================
# Migrados a: modules/rh/routes.py
# Fecha: Diciembre 2025
# ============================================================================

# @api_router.get("/rrhh/auditoria-fiscal")
# async def rrhh_listar_auditoria_fiscal(
#     colaborador_id: Optional[int] = None,
#     semana: Optional[int] = None,
#     solo_alertas: bool = False,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Lista auditoría fiscal de nóminas"""
#     
#     conditions = ["1=1"]
#     if colaborador_id:
#         conditions.append(f"a.ColaboradorID = {colaborador_id}")
#     if semana:
#         conditions.append(f"a.Semana = {semana}")
#     if solo_alertas:
#         conditions.append("a.Alerta_Fraude = 1")
#     
#     where_clause = " AND ".join(conditions)
#     
#     query = f"""
#         SELECT 
#             a.AuditoriaID,
#             a.ColaboradorID,
#             c.Nombre_Completo,
#             c.RFC,
#             s.Nombre_Sucursal,
#             a.Semana,
#             a.Monto_Dispersado_Banco,
#             a.Monto_Timbrado_XML,
#             a.Monto_IMSS_EBA_EMA,
#             a.Diferencia,
#             a.Alerta_Fraude
#         FROM RH_Auditoria_Fiscal a
#         LEFT JOIN RH_Colaboradores_Expediente c ON a.ColaboradorID = c.ColaboradorID
#         LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
#         WHERE {where_clause}
#         ORDER BY a.Alerta_Fraude DESC, a.Semana DESC
#     """
#     
#     result = await execute_edarsa_hub_query(query)
#     alertas = sum(1 for r in result.get("datos", []) if r.get("Alerta_Fraude") == 1)
#     
#     return {
#         "auditoria": result.get("datos", []),
#         "total": result.get("registros", 0),
#         "total_alertas": alertas
#     }


# ============================================================================
# ENDPOINTS DE DASHBOARD RRHH - COMENTADOS (FASE 6G-B)
# ============================================================================

# @api_router.get("/rrhh/dashboard")
# async def rrhh_dashboard(
#     sucursal_id: Optional[int] = None,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Dashboard con métricas de RRHH"""
#     
#     suc_filter = f"AND SucursalID = {sucursal_id}" if sucursal_id else ""
#     suc_filter_c = f"AND c.SucursalID = {sucursal_id}" if sucursal_id else ""
#     
#     # Total colaboradores
#     query_total = f"""
#         SELECT 
#             COUNT(*) as total,
#             SUM(CASE WHEN Colaborador_Activo = 1 THEN 1 ELSE 0 END) as activos,
#             SUM(CASE WHEN Estatus_Laboral = 'Vacaciones' THEN 1 ELSE 0 END) as vacaciones,
#             SUM(CASE WHEN Estatus_Laboral = 'Incapacidad' THEN 1 ELSE 0 END) as incapacidad,
#             SUM(CASE WHEN Colaborador_Activo = 0 THEN 1 ELSE 0 END) as bajas
#         FROM RH_Colaboradores_Expediente
#         WHERE 1=1 {suc_filter}
#     """
#     
#     # Por departamento
#     query_depto = f"""
#         SELECT 
#             ISNULL(p.Departamento, 'Sin asignar') as Departamento,
#             COUNT(*) as total
#         FROM RH_Colaboradores_Expediente c
#         LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
#         WHERE c.Colaborador_Activo = 1 {suc_filter_c}
#         GROUP BY p.Departamento
#         ORDER BY total DESC
#     """
#     
#     # Incidencias del mes
#     query_incidencias = f"""
#         SELECT 
#             Tipo_Incidencia,
#             COUNT(*) as cantidad,
#             SUM(ISNULL(Monto, 0)) as monto_total
#         FROM RH_Incidencias_Nomina i
#         LEFT JOIN RH_Colaboradores_Expediente c ON i.ColaboradorID = c.ColaboradorID
#         WHERE MONTH(Fecha_Incidencia) = MONTH(GETDATE()) 
#           AND YEAR(Fecha_Incidencia) = YEAR(GETDATE())
#           {suc_filter_c}
#         GROUP BY Tipo_Incidencia
#     """
#     
#     # Flujos pendientes
#     query_flujos = f"""
#         SELECT 
#             Estatus_Flujo,
#             COUNT(*) as cantidad
#         FROM RH_Flujo_Nomina_Sucursal
#         WHERE Estatus_Flujo NOT IN ('Pagado')
#           {suc_filter}
#         GROUP BY Estatus_Flujo
#     """
#     
#     # Alertas fraude
#     query_alertas = f"""
#         SELECT COUNT(*) as alertas
#         FROM RH_Auditoria_Fiscal a
#         LEFT JOIN RH_Colaboradores_Expediente c ON a.ColaboradorID = c.ColaboradorID
#         WHERE a.Alerta_Fraude = 1 {suc_filter_c}
#     """
#     
#     result_total = await execute_edarsa_hub_query(query_total)
#     result_depto = await execute_edarsa_hub_query(query_depto)
#     result_incidencias = await execute_edarsa_hub_query(query_incidencias)
#     result_flujos = await execute_edarsa_hub_query(query_flujos)
#     result_alertas = await execute_edarsa_hub_query(query_alertas)
#     
#     return {
#         "resumen": result_total.get("datos", [{}])[0] if result_total.get("datos") else {},
#         "por_departamento": result_depto.get("datos", []),
#         "incidencias_mes": result_incidencias.get("datos", []),
#         "flujos_pendientes": result_flujos.get("datos", []),
#         "alertas_fraude": result_alertas.get("datos", [{}])[0].get("alertas", 0) if result_alertas.get("datos") else 0
#     }



# ============ SCRIPTS PENDIENTES (STAND-BY) ============

@api_router.post("/explorador/guardar-script/{server_id}")
async def guardar_script_pendiente(
    server_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Guarda un script SQL en stand-by para ejecución posterior.
    Permite que un administrador de BD lo ejecute con sus credenciales.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 6
    
    NOTA: La escritura del script pendiente permanece en MongoDB como documento
    operativo temporal (cola/workflow), NO como catálogo maestro.
    El documento NO contiene credenciales, solo referencia al server_id y nombre.
    """
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden guardar scripts")
    
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    script = body.get('script', '').strip()
    titulo = body.get('titulo', '').strip()
    
    if not script:
        raise HTTPException(status_code=400, detail="El script está vacío")
    if not titulo:
        raise HTTPException(status_code=400, detail="El título es requerido")
    
    # Contar statements
    import re
    script_normalizado = re.sub(r'\bGO\b', ';', script, flags=re.IGNORECASE)
    statements = [s.strip() for s in script_normalizado.split(';') if s.strip() and not s.strip().startswith('--')]
    
    # Guardar en MongoDB como documento operativo temporal
    # IMPORTANTE: No incluir credenciales, solo server_id y nombre para referencia
    result = await db.scripts_pendientes.insert_one({
        "server_id": server_id,
        "server_name": conn_info.get('name'),  # Solo nombre, sin credenciales
        "titulo": titulo,
        "script": script,
        "num_statements": len(statements),
        "creado_por": current_user.get('email'),
        "fecha_creacion": datetime.now(timezone.utc),
        "estado": "pendiente"
    })
    
    return {"message": "Script guardado en stand-by", "id": str(result.inserted_id)}


@api_router.get("/explorador/scripts-pendientes/{server_id}")
async def listar_scripts_pendientes(
    server_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Lista los scripts pendientes de ejecución para un servidor."""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver scripts pendientes")
    
    scripts = await db.scripts_pendientes.find(
        {"server_id": server_id, "estado": "pendiente"},
        {"_id": 1, "titulo": 1, "script": 1, "num_statements": 1, "creado_por": 1, "fecha_creacion": 1}
    ).sort("fecha_creacion", -1).to_list(100)
    
    # Convertir ObjectId a string
    for s in scripts:
        s['_id'] = str(s['_id'])
    
    return scripts


@api_router.delete("/explorador/script-pendiente/{script_id}")
async def eliminar_script_pendiente(
    script_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un script pendiente."""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar scripts")
    
    from bson import ObjectId
    result = await db.scripts_pendientes.delete_one({"_id": ObjectId(script_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Script no encontrado")
    
    return {"message": "Script eliminado"}


@api_router.put("/explorador/script-pendiente/{script_id}")
async def actualizar_script_pendiente(
    script_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un script pendiente (título y/o contenido)."""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar scripts")
    
    titulo = body.get('titulo', '').strip()
    script = body.get('script', '').strip()
    
    if not titulo:
        raise HTTPException(status_code=400, detail="El título es requerido")
    if not script:
        raise HTTPException(status_code=400, detail="El script no puede estar vacío")
    
    # Contar statements actualizados
    import re
    script_normalizado = re.sub(r'\bGO\b', ';', script, flags=re.IGNORECASE)
    statements = [s.strip() for s in script_normalizado.split(';') if s.strip() and not s.strip().startswith('--')]
    
    from bson import ObjectId
    result = await db.scripts_pendientes.update_one(
        {"_id": ObjectId(script_id)},
        {"$set": {
            "titulo": titulo,
            "script": script,
            "num_statements": len(statements),
            "modificado_por": current_user.get('email'),
            "fecha_modificacion": datetime.now(timezone.utc)
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Script no encontrado")
    
    return {"message": "Script actualizado", "num_statements": len(statements)}


@api_router.post("/explorador/ejecutar-con-credenciales/{server_id}")
async def ejecutar_script_con_credenciales(
    server_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta un script SQL usando credenciales de administrador proporcionadas.
    Las credenciales se usan solo para esta ejecución (no se guardan).
    
    FASE P1.4-E4 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.server_registry import get_server_connection_info_with_secrets
    
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar scripts")
    
    # FASE P1.4-E4: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    script_id = body.get('script_id')
    script = body.get('script', '').strip()
    titulo = body.get('titulo', 'Script sin título')
    admin_username = body.get('admin_username', '').strip()
    admin_password = body.get('admin_password', '')
    
    if not admin_username or not admin_password:
        raise HTTPException(status_code=400, detail="Credenciales de administrador requeridas")
    
    # Si hay script_id, cargar el script de MongoDB
    if script_id:
        from bson import ObjectId
        script_doc = await db.scripts_pendientes.find_one({"_id": ObjectId(script_id)})
        if script_doc:
            script = script_doc.get('script', '')
            titulo = script_doc.get('titulo', titulo)
    
    if not script:
        raise HTTPException(status_code=400, detail="El script está vacío")
    
    # Parsear statements
    import re
    script_normalizado = re.sub(r'\bGO\b', ';', script, flags=re.IGNORECASE)
    statements = []
    current_statement = []
    in_string = False
    string_char = None
    
    for char in script_normalizado:
        if char in ("'", '"') and not in_string:
            in_string = True
            string_char = char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
        
        if char == ';' and not in_string:
            stmt = ''.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []
        else:
            current_statement.append(char)
    
    final_stmt = ''.join(current_statement).strip()
    if final_stmt:
        statements.append(final_stmt)
    
    statements = [s for s in statements if s and not s.startswith('--')]
    
    if not statements:
        raise HTTPException(status_code=400, detail="No se encontraron comandos SQL válidos")
    
    logging.info(f"[SCRIPT CON CREDS] Usuario {current_user.get('email')} ejecutando {len(statements)} comandos en {server['name']} con credenciales de {admin_username}")
    
    resultados = []
    exitosos = 0
    fallidos = 0
    
    import pytds
    
    try:
        host_str = server['host']
        port = server.get('port', 1433)
        
        if ',' in host_str:
            parts = host_str.split(',')
            host = parts[0].strip()
            try:
                port = int(parts[1].strip().split('\\')[0])
            except Exception:
                pass
        else:
            host = host_str
        
        with pytds.connect(
            server=host,
            port=port,
            database=server['database'],
            user=admin_username,  # Usar credenciales proporcionadas
            password=admin_password,
            timeout=60,
            login_timeout=30,
            autocommit=True
        ) as conn:
            cursor = conn.cursor()
            
            for idx, stmt in enumerate(statements):
                stmt_tipo = stmt.split()[0].upper() if stmt.split() else 'UNKNOWN'
                
                try:
                    cursor.execute(stmt)
                    
                    if stmt_tipo == 'SELECT':
                        try:
                            rows = cursor.fetchall()
                            resultados.append({
                                "exito": True,
                                "tipo": stmt_tipo,
                                "mensaje": f"Retornó {len(rows)} filas",
                                "filas_afectadas": len(rows)
                            })
                        except Exception:
                            resultados.append({
                                "exito": True,
                                "tipo": stmt_tipo,
                                "mensaje": "Ejecutado correctamente"
                            })
                    else:
                        filas = cursor.rowcount if cursor.rowcount >= 0 else 0
                        resultados.append({
                            "exito": True,
                            "tipo": stmt_tipo,
                            "mensaje": f"{filas} filas afectadas" if filas > 0 else "Ejecutado correctamente",
                            "filas_afectadas": filas
                        })
                    
                    exitosos += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    resultados.append({
                        "exito": False,
                        "tipo": stmt_tipo,
                        "error": error_msg,
                        "statement": stmt[:100] + '...' if len(stmt) > 100 else stmt
                    })
                    fallidos += 1
                    logging.warning(f"[SCRIPT CON CREDS] Error en statement {idx+1}: {error_msg}")
    
    except pytds.LoginError:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: Usuario o contraseña incorrectos")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
    
    # Guardar log
    await db.script_logs.insert_one({
        "server_id": server_id,
        "server_name": server['name'],
        "titulo": titulo,
        "usuario_app": current_user.get('email'),
        "usuario_sql": admin_username,
        "fecha": datetime.now(timezone.utc),
        "total_statements": len(statements),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados,
        "tipo": "ejecutado_con_credenciales"
    })
    
    # Si se ejecutó exitosamente y era un script pendiente, marcarlo como ejecutado
    if script_id and exitosos > 0:
        from bson import ObjectId
        await db.scripts_pendientes.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": {
                "estado": "ejecutado",
                "fecha_ejecucion": datetime.now(timezone.utc),
                "ejecutado_por": current_user.get('email'),
                "resultado": {"exitosos": exitosos, "fallidos": fallidos}
            }}
        )
    
    return {
        "servidor": server['name'],
        "titulo": titulo,
        "total": len(statements),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados
    }


# ============================================================================
# ========================= MÓDULO DE FINANZAS ===============================
# ============================================================================

@api_router.get("/finanzas/dashboard")
async def finanzas_dashboard(
    anio: int = Query(default=None),
    mes: int = Query(default=None),
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Dashboard general de finanzas con KPIs y comparativos"""
    from datetime import datetime
    
    if not anio:
        anio = datetime.now().year
    if not mes:
        mes = datetime.now().month
    
    # NOTA: La tabla Finanzas_Presupuestos no existe actualmente en EDARSA HUB
    # Retornar estructura vacía para evitar corrupción del pool de conexiones
    return {
        "periodo": {"anio": anio, "mes": mes},
        "mensaje": "Dashboard de presupuestos no disponible - tabla Finanzas_Presupuestos pendiente de creación",
        "kpis": {
            "ingresos_presupuestados": 0,
            "ingresos_ejecutados": 0,
            "ingresos_var_mes_ant": 0,
            "egresos_presupuestados": 0,
            "egresos_ejecutados": 0,
            "egresos_var_mes_ant": 0,
            "utilidad_presupuestada": 0,
            "utilidad_real": 0,
            "margen_utilidad": 0
        },
        "presupuestos": [],
        "por_sucursal": [],
        "totales": []
    }


@api_router.get("/finanzas/presupuestos")
async def finanzas_listar_presupuestos(
    anio: int = Query(default=None),
    mes: int = Query(default=None),
    sucursal_id: Optional[int] = None,
    categoria: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista presupuestos con filtros - TABLA NO DISPONIBLE"""
    # NOTA: La tabla Finanzas_Presupuestos no existe actualmente
    return {"presupuestos": [], "total": 0, "mensaje": "Tabla Finanzas_Presupuestos pendiente de creación"}


@api_router.post("/finanzas/presupuestos")
async def finanzas_crear_presupuesto(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo presupuesto - TABLA NO DISPONIBLE"""
    return {"success": False, "message": "Tabla Finanzas_Presupuestos pendiente de creación"}


@api_router.put("/finanzas/presupuestos/{presupuesto_id}")
async def finanzas_actualizar_presupuesto(
    presupuesto_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un presupuesto existente - TABLA NO DISPONIBLE"""
    return {"success": False, "message": "Tabla Finanzas_Presupuestos pendiente de creación"}


@api_router.delete("/finanzas/presupuestos/{presupuesto_id}")
async def finanzas_eliminar_presupuesto(
    presupuesto_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un presupuesto - TABLA NO DISPONIBLE"""
    return {"success": False, "message": "Tabla Finanzas_Presupuestos pendiente de creación"}


@api_router.get("/finanzas/categorias")
async def finanzas_listar_categorias(
    current_user: Dict = Depends(get_current_user)
):
    """Lista las categorías únicas de presupuestos - TABLA NO DISPONIBLE"""
    # Categorías por defecto (tabla no existe)
    return {
        "categorias": [
            {"Categoria": "Ventas", "Tipo": "Ingreso"},
            {"Categoria": "Servicios", "Tipo": "Ingreso"},
            {"Categoria": "Otros Ingresos", "Tipo": "Ingreso"},
            {"Categoria": "Nómina", "Tipo": "Egreso"},
            {"Categoria": "Materia Prima", "Tipo": "Egreso"},
            {"Categoria": "Servicios Básicos", "Tipo": "Egreso"},
            {"Categoria": "Renta", "Tipo": "Egreso"},
            {"Categoria": "Marketing", "Tipo": "Egreso"},
            {"Categoria": "Mantenimiento", "Tipo": "Egreso"},
            {"Categoria": "Gastos Administrativos", "Tipo": "Egreso"},
        ]
    }


@api_router.post("/finanzas/registrar-movimiento")
async def finanzas_registrar_movimiento(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Registra un movimiento y actualiza el monto ejecutado del presupuesto - TABLA NO DISPONIBLE"""
    return {"success": False, "message": "Tabla Finanzas_Presupuestos pendiente de creación"}


@api_router.get("/finanzas/script-inicializacion")
async def finanzas_obtener_script_inicializacion(
    current_user: Dict = Depends(get_current_user)
):
    """Retorna el script SQL para crear las tablas de finanzas en EDARSA HUB"""
    
    script = """
-- ============================================
-- SCRIPT DE INICIALIZACIÓN - MÓDULO FINANZAS
-- Ejecutar en la base de datos EDARSA HUB
-- ============================================

-- Tabla de Presupuestos
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Finanzas_Presupuestos' AND xtype='U')
BEGIN
    CREATE TABLE Finanzas_Presupuestos (
        PresupuestoID INT IDENTITY(1,1) PRIMARY KEY,
        SucursalID INT NOT NULL,
        Categoria NVARCHAR(100) NOT NULL,
        SubCategoria NVARCHAR(100),
        Tipo NVARCHAR(20) NOT NULL CHECK (Tipo IN ('Ingreso', 'Egreso')),
        Monto_Presupuestado DECIMAL(18,2) DEFAULT 0,
        Monto_Ejecutado DECIMAL(18,2) DEFAULT 0,
        Anio INT NOT NULL,
        Mes INT NOT NULL CHECK (Mes BETWEEN 1 AND 12),
        Notas NVARCHAR(500),
        Fecha_Creacion DATETIME DEFAULT GETDATE(),
        Fecha_Modificacion DATETIME,
        Creado_Por NVARCHAR(100),
        
        CONSTRAINT FK_Presupuesto_Sucursal FOREIGN KEY (SucursalID) 
            REFERENCES RH_Cat_Sucursales(SucursalID)
    );
    
    CREATE INDEX IX_Presupuestos_Periodo ON Finanzas_Presupuestos(Anio, Mes);
    CREATE INDEX IX_Presupuestos_Sucursal ON Finanzas_Presupuestos(SucursalID);
    
    PRINT 'Tabla Finanzas_Presupuestos creada exitosamente';
END
ELSE
    PRINT 'Tabla Finanzas_Presupuestos ya existe';
GO

-- Insertar presupuestos de ejemplo para el mes actual
DECLARE @Anio INT = YEAR(GETDATE())
DECLARE @Mes INT = MONTH(GETDATE())

-- Solo insertar si no hay datos del periodo actual
IF NOT EXISTS (SELECT 1 FROM Finanzas_Presupuestos WHERE Anio = @Anio AND Mes = @Mes)
BEGIN
    -- Obtener sucursales activas
    INSERT INTO Finanzas_Presupuestos (SucursalID, Categoria, SubCategoria, Tipo, Monto_Presupuestado, Anio, Mes, Creado_Por)
    SELECT 
        s.SucursalID,
        'Ventas',
        'Ventas Generales',
        'Ingreso',
        100000.00,
        @Anio,
        @Mes,
        'SISTEMA'
    FROM RH_Cat_Sucursales s
    WHERE s.Nombre_Sucursal IS NOT NULL;
    
    INSERT INTO Finanzas_Presupuestos (SucursalID, Categoria, SubCategoria, Tipo, Monto_Presupuestado, Anio, Mes, Creado_Por)
    SELECT 
        s.SucursalID,
        'Nómina',
        'Sueldos y Salarios',
        'Egreso',
        50000.00,
        @Anio,
        @Mes,
        'SISTEMA'
    FROM RH_Cat_Sucursales s
    WHERE s.Nombre_Sucursal IS NOT NULL;
    
    PRINT 'Presupuestos de ejemplo insertados';
END
GO

PRINT '=== Script de inicialización completado ===';
"""
    
    return {
        "script": script,
        "instrucciones": [
            "1. Copia el script SQL",
            "2. Ve a 'Explorador BD' en el menú lateral",
            "3. Selecciona el servidor EDARSA HUB",
            "4. Pega y ejecuta el script con credenciales de administrador",
            "5. Regresa a Finanzas para ver los datos"
        ]
    }


# ============================================================================
# ========================= MÓDULO DE RECLUTAMIENTO ==========================
# ============================================================================

# ============================================================================
# ENDPOINTS DE RECLUTAMIENTO - COMENTADOS (FASE 6H-B)
# ============================================================================
# Migrados a: modules/rh/routes.py
# Fecha: Diciembre 2025
#
# Endpoints migrados:
# - GET    /rrhh/vacantes
# - POST   /rrhh/vacantes
# - PUT    /rrhh/vacantes/{vacante_id}
# - DELETE /rrhh/vacantes/{vacante_id}
# - GET    /rrhh/candidatos
# - POST   /rrhh/candidatos
# - PUT    /rrhh/candidatos/{candidato_id}
# - DELETE /rrhh/candidatos/{candidato_id}
# - GET    /rrhh/reclutamiento/dashboard
# - GET    /rrhh/reclutamiento/script-inicializacion
# ============================================================================

# @api_router.get("/rrhh/vacantes")
# async def rrhh_listar_vacantes(
#     sucursal_id: Optional[int] = None,
#     estatus: Optional[str] = None,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Lista vacantes disponibles"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.post("/rrhh/vacantes")
# async def rrhh_crear_vacante(
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Crea una nueva vacante"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.put("/rrhh/vacantes/{vacante_id}")
# async def rrhh_actualizar_vacante(
#     vacante_id: int,
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Actualiza una vacante"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.delete("/rrhh/vacantes/{vacante_id}")
# async def rrhh_eliminar_vacante(
#     vacante_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Elimina una vacante"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.get("/rrhh/candidatos")
# async def rrhh_listar_candidatos(
#     vacante_id: Optional[int] = None,
#     estatus: Optional[str] = None,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Lista candidatos"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.post("/rrhh/candidatos")
# async def rrhh_crear_candidato(
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Registra un nuevo candidato"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.put("/rrhh/candidatos/{candidato_id}")
# async def rrhh_actualizar_candidato(
#     candidato_id: int,
#     body: Dict,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Actualiza el estatus de un candidato"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.delete("/rrhh/candidatos/{candidato_id}")
# async def rrhh_eliminar_candidato(
#     candidato_id: int,
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Elimina un candidato"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.get("/rrhh/reclutamiento/dashboard")
# async def rrhh_reclutamiento_dashboard(
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Dashboard de reclutamiento con métricas"""
#     ... # Código original comentado - ver modules/rh/routes.py


# @api_router.get("/rrhh/reclutamiento/script-inicializacion")
# async def rrhh_reclutamiento_script(
#     current_user: Dict = Depends(get_current_user)
# ):
#     """Retorna el script SQL para crear las tablas de reclutamiento"""
#     ... # Código original comentado - ver modules/rh/routes.py


def _escape_like_pattern(value: str) -> str:
    """
    Escapa caracteres especiales para LIKE en SQL Server.
    FASE 1A - Sanitización SQL Injection.
    Caracteres escapados: [ ] % _ '
    """
    if not value:
        return value
    # Escapar en orden: primero [ (para no afectar los escapes posteriores)
    result = value.replace('[', '[[]')
    result = result.replace('%', '[%]')
    result = result.replace('_', '[_]')
    result = result.replace("'", "''")
    return result


def _validate_identifier(value: str, max_length: int = 128) -> bool:
    """
    FASE 1B - Valida que un identificador sea seguro para usar en SQL.
    Solo permite caracteres alfanuméricos, guiones bajos y guiones.
    """
    if not value or not isinstance(value, str):
        return False
    if len(value) > max_length:
        return False
    # Solo alfanuméricos, guiones bajos, guiones y puntos (para esquemas)
    import re
    return bool(re.match(r'^[a-zA-Z0-9_\-\.]+$', value))


def _sanitize_identifier(value: str) -> str:
    """
    FASE 1B - Sanitiza un identificador escapando comillas.
    Usar SOLO después de validar con _validate_identifier().
    """
    if not value:
        return value
    return value.replace("'", "''")


# FASE 1B - Whitelist de tablas permitidas para explorador SQL
# Actualizar esta lista según las tablas que deben ser consultables
EXPLORADOR_TABLAS_PERMITIDAS = {
    # SoftRestaurant
    'almacen', 'cheques', 'cheqdet', 'productos', 'categorias', 'turnos',
    'meseros', 'cuentas', 'folios', 'formasdepago', 'movsinventario', 
    'movsalmacen', 'gruposi', 'gruposiclasificacion', 'productosreceta',
    'productosi', 'usuarios', 'tiposdecheques', 'impuestos', 'preciosi',
    # MPRO
    'producto', 'almacen', 'sucursal', 'proveedor', 'movimiento', 
    'entrada', 'salida', 'fisico', 'compras', 'ventas', 'clientes',
    'categoria', 'familia', 'subfamilia', 'unidad', 'tipo_movimiento',
    # Tablas de sistema
    'information_schema.tables', 'information_schema.columns',
}


def _validate_table_name(tabla: str, system_type: str = None, user_role: str = None) -> tuple:
    """
    FASE 1B - Valida nombre de tabla contra whitelist.
    
    Args:
        tabla: Nombre de la tabla
        system_type: Tipo de sistema (SoftRestaurant, MPRO, etc.)
        user_role: Rol del usuario (superadmin bypasea whitelist)
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not tabla:
        return (False, "Nombre de tabla vacío")
    
    tabla_lower = tabla.lower().strip()
    
    # Verificar caracteres básicos primero
    if not _validate_identifier(tabla_lower, max_length=128):
        return (False, f"Nombre de tabla inválido: caracteres no permitidos")
    
    # SUPERADMIN BYPASS: El usuario superadministrador no tiene restricciones
    if user_role and user_role.lower() in ('superadmin', 'superadministrador'):
        return (True, None)
    
    # Verificar contra whitelist
    if tabla_lower in EXPLORADOR_TABLAS_PERMITIDAS:
        return (True, None)
    
    # Verificar prefijos comunes seguros
    safe_prefixes = ('dbo.', 'sys.', 'information_schema.')
    for prefix in safe_prefixes:
        if tabla_lower.startswith(prefix):
            base_table = tabla_lower[len(prefix):]
            if base_table in EXPLORADOR_TABLAS_PERMITIDAS:
                return (True, None)
    
    return (False, f"Tabla '{tabla}' no está en la lista permitida")


def _build_safe_folios_condition(folios: list, column_name: str, max_folios: int = 50) -> tuple:
    """
    FASE 1B - Construye condición IN segura para lista de folios.
    
    Args:
        folios: Lista de folios
        column_name: Nombre de la columna (ya validado)
        max_folios: Máximo de folios permitidos
        
    Returns:
        tuple: (sql_condition: str, params: tuple)
        Si folios vacío, retorna condición que no coincide con nada.
    """
    if not folios:
        return ("1=0", ())  # Condición que nunca se cumple
    
    # Limitar cantidad
    folios_limitados = folios[:max_folios]
    
    # Validar cada folio
    folios_validos = []
    for f in folios_limitados:
        if f and isinstance(f, str) and _validate_identifier(f, max_length=50):
            folios_validos.append(f)
    
    if not folios_validos:
        return ("1=0", ())
    
    # Construir placeholders dinámicos (%s para cada folio)
    placeholders = ", ".join(["%s"] * len(folios_validos))
    sql_condition = f"{column_name} IN ({placeholders})"
    
    return (sql_condition, tuple(folios_validos))


@api_router.get("/explorador/buscar/{server_id}")
async def buscar_en_bd(
    server_id: str,
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    tipo: str = Query(default="todo", description="Tipo: todo, tablas, columnas, datos"),
    tabla: str = Query(default=None, description="Buscar datos solo en esta tabla"),
    limite: int = Query(default=50, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Buscador global de la base de datos.
    Busca en nombres de tablas, columnas y opcionalmente en datos.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    
    FASE 1A: Sanitizado contra SQL Injection usando _escape_like_pattern()
    """
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    # FASE 6-8: Validar acceso usando función centralizada
    await validate_server_access_unified(current_user, server_id)
    
    # FASE 1A: Sanitizar parámetro de búsqueda contra SQL Injection
    q_safe = _escape_like_pattern(q)
    
    resultados = {
        "termino": q,
        "tablas": [],
        "columnas": [],
        "datos": [],
        "total": 0
    }
    
    # FASE 1A: Sanitizar nombre de tabla si se proporciona
    tabla_safe = _escape_like_pattern(tabla) if tabla else None
    
    try:
        # 1. Buscar en nombres de TABLAS
        if tipo in ["todo", "tablas"]:
            query_tablas = f"""
SELECT TABLE_NAME as tabla, TABLE_TYPE as tipo
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_NAME LIKE '%{q_safe}%'
ORDER BY TABLE_NAME
"""
            tablas = execute_sql_query(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], query_tablas
            )
            resultados["tablas"] = tablas or []
        
        # 2. Buscar en nombres de COLUMNAS
        if tipo in ["todo", "columnas"]:
            query_columnas = f"""
SELECT 
    TABLE_NAME as tabla,
    COLUMN_NAME as columna,
    DATA_TYPE as tipo_dato
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%{q_safe}%'
ORDER BY TABLE_NAME, COLUMN_NAME
"""
            columnas = execute_sql_query(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], query_columnas
            )
            resultados["columnas"] = columnas or []
        
        # 3. Buscar en DATOS (opcional, más costoso)
        if tipo in ["todo", "datos"] and tabla:
            # Buscar en una tabla específica
            # Obtener columnas de tipo texto de la tabla
            # FASE 1A: Validar que tabla solo contenga caracteres alfanuméricos y _
            if not tabla.replace('_', '').replace(' ', '').isalnum():
                raise HTTPException(status_code=400, detail="Nombre de tabla inválido")
            query_cols_texto = f"""
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla_safe}'
  AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext')
"""
            cols_texto = execute_sql_query(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], query_cols_texto
            )
            
            if cols_texto:
                # Construir WHERE con OR para cada columna de texto
                # FASE 1A: Usar q_safe para prevenir SQL injection
                condiciones = " OR ".join([f"[{c['COLUMN_NAME']}] LIKE '%{q_safe}%'" for c in cols_texto])
                query_datos = f"""
SELECT TOP {limite} *
FROM [{tabla}]
WHERE {condiciones}
"""
                datos = execute_sql_query(
                    conn_info['host'], conn_info['port'], conn_info['database'],
                    conn_info['username'], conn_info['password'], query_datos
                )
                resultados["datos"] = [{"tabla": tabla, "fila": d} for d in (datos or [])]
        
        elif tipo == "datos" and not tabla:
            # Buscar en todas las tablas principales (limitado por rendimiento)
            # Solo busca en las primeras 5 tablas que contengan columnas de texto
            query_tablas_texto = f"""
SELECT DISTINCT TOP 5 TABLE_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext')
  AND TABLE_NAME NOT LIKE 'sys%'
"""
            tablas_texto = execute_sql_query(
                conn_info['host'], conn_info['port'], conn_info['database'],
                conn_info['username'], conn_info['password'], query_tablas_texto
            )
            
            datos_encontrados = []
            for t in (tablas_texto or [])[:5]:
                tabla_nombre = t['TABLE_NAME']
                # FASE 1A: tabla_nombre viene de INFORMATION_SCHEMA (confiable)
                # pero sanitizamos por seguridad en profundidad
                tabla_nombre_safe = _escape_like_pattern(tabla_nombre)
                # Obtener columnas de texto
                query_cols = f"""
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla_nombre_safe}'
  AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext')
"""
                cols = execute_sql_query(
                    conn_info['host'], conn_info['port'], conn_info['database'],
                    conn_info['username'], conn_info['password'], query_cols
                )
                
                if cols:
                    # FASE 1A: Usar q_safe para prevenir SQL injection
                    condiciones = " OR ".join([f"[{c['COLUMN_NAME']}] LIKE '%{q_safe}%'" for c in cols[:5]])
                    query_datos = f"SELECT TOP 10 * FROM [{tabla_nombre}] WHERE {condiciones}"
                    try:
                        datos = execute_sql_query(
                            conn_info['host'], conn_info['port'], conn_info['database'],
                            conn_info['username'], conn_info['password'], query_datos
                        )
                        for d in (datos or []):
                            datos_encontrados.append({"tabla": tabla_nombre, "fila": d})
                    except Exception:
                        pass  # Ignorar errores en tablas específicas
                
                if len(datos_encontrados) >= limite:
                    break
            
            resultados["datos"] = datos_encontrados[:limite]
        
        resultados["total"] = len(resultados["tablas"]) + len(resultados["columnas"]) + len(resultados["datos"])
        
        return resultados
        
    except Exception as e:
        logging.error(f"Error en búsqueda BD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CATÁLOGO DE CONSULTAS - Para que Rich use sin programador
# ============================================================================

@api_router.get("/catalogo/consultas-rich")
async def listar_consultas_rich(
    sistema: str = Query(default=None),  # SoftRestaurant, MPRO
    categoria: str = Query(default=None),  # Ventas, Compras, Pagos, etc.
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todas las consultas disponibles en el catálogo de Rich.
    Incluye consultas predefinidas y personalizadas (MongoDB).
    Filtrable por sistema y categoría.
    """
    # Consultas predefinidas del catálogo
    consultas = catalogo_get_consultas(sistema, categoria)
    
    # Formato amigable para el frontend
    resultado = []
    for key, c in consultas.items():
        resultado.append({
            "id": key,
            "nombre": c["nombre"],
            "descripcion": c["descripcion"],
            "sistema": c["sistema"],
            "categoria": c["categoria"],
            "parametros": c["parametros"],
            "sql": c["sql"],  # Incluir el SQL para visualización
            "tipo": "predefinida"
        })
    
    # Agregar consultas personalizadas desde MongoDB
    filtro = {"active": True}
    if sistema:
        filtro["sistema"] = sistema
    if categoria:
        filtro["categoria"] = categoria
    
    consultas_custom = await db.consultas_custom.find(filtro).to_list(500)
    for c in consultas_custom:
        resultado.append({
            "id": c["id"],
            "nombre": c["nombre"],
            "descripcion": c["descripcion"],
            "sistema": c["sistema"],
            "categoria": c["categoria"],
            "parametros": c["parametros"],
            "sql": c.get("sql", ""),  # Incluir el SQL
            "tipo": "personalizada",
            "created_by": c.get("created_by"),
            "created_at": c.get("created_at")
        })
    
    # Obtener categorías (incluyendo las de consultas personalizadas)
    categorias_base = set(catalogo_get_categorias())
    for c in consultas_custom:
        categorias_base.add(c.get("categoria", ""))
    
    return {
        "consultas": resultado,
        "categorias": sorted(list(categorias_base)),
        "total": len(resultado)
    }


@api_router.post("/catalogo/ejecutar-rich/{consulta_id}")
async def ejecutar_consulta_catalogo(
    consulta_id: str,
    server_id: str = Query(...),
    limit: int = Query(default=None, description="Límite de registros (para modo test)"),
    body: Dict = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta una consulta del catálogo (predefinida o personalizada) con los parámetros dados.
    Body debe contener: { "fecha_ini": "2026-03-01", "fecha_fin": "2026-03-27" }
    o { "parametros": { "fecha_ini": "...", ... } }
    
    FASE 1B: Validación SQL obligatoria para consultas custom.
    """
    from core.security import SQLSanitizer, log_blocked_sql
    
    # Buscar primero en consultas predefinidas
    consulta = None
    es_custom = False
    
    if consulta_id in CATALOGO_CONSULTAS:
        consulta = CATALOGO_CONSULTAS[consulta_id]
    else:
        # Buscar en consultas personalizadas
        consulta_custom = await db.consultas_custom.find_one({"id": consulta_id})
        if consulta_custom:
            consulta = consulta_custom
            es_custom = True
    
    if not consulta:
        raise HTTPException(status_code=404, detail=f"Consulta '{consulta_id}' no encontrada en el catálogo")
    
    # FASE 1B: Validar SQL de consultas custom antes de ejecutar
    if es_custom:
        sql_to_validate = consulta.get('sql', '')
        validation = SQLSanitizer.validate_for_catalog(sql_to_validate)
        if not validation.is_safe:
            log_blocked_sql(validation, endpoint=f"/catalogo/ejecutar-rich/{consulta_id}", user_email=current_user.get('email'))
            raise HTTPException(
                status_code=400, 
                detail=f"Consulta custom bloqueada: {validation.blocked_reason}. "
                       "Esta consulta contiene SQL no permitido y no puede ejecutarse."
            )
    
    # Extraer parámetros del body (soporta ambos formatos)
    if body and 'parametros' in body:
        parametros = body['parametros']
    else:
        parametros = body or {}
    
    # Verificar servidor
    # FASE P1.4-E4: Obtener servidor desde EDARSAHUB SQL via server_registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info_with_secrets
    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Verificar que el sistema coincida
    sistema_server = server.get('system_type')
    sistema_consulta = consulta.get('sistema')
    
    # Mapeo de tipos para consultas predefinidas
    if not es_custom:
        if is_mpro_system(sistema_server) and not consulta_id.startswith('MPRO_'):
            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para MPRO")
        if is_softrestaurant_system(sistema_server) and not consulta_id.startswith('SR_'):
            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para SoftRestaurant")
    else:
        # Para consultas custom, verificar directamente
        if normalize_system_type(sistema_server) != normalize_system_type(sistema_consulta):
            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para {sistema_server}")
    
    # FASE 6-8: Validar acceso usando función centralizada
    await validate_server_access_unified(current_user, server_id)
    
    # Preparar parámetros
    params = parametros or {}
    
    # Validar parámetros requeridos
    for param in consulta['parametros']:
        if param not in params:
            raise HTTPException(status_code=400, detail=f"Falta parámetro requerido: {param}")
    
    # Preparar SQL
    if es_custom:
        sql = consulta['sql']
        for param, valor in params.items():
            sql = sql.replace('{' + param + '}', str(valor))
    else:
        sql = catalogo_preparar_sql(consulta_id, params)
    
    # Si hay límite (modo test), agregar TOP/LIMIT al SQL
    if limit and limit > 0:
        # Detectar si ya tiene TOP
        sql_upper = sql.upper().strip()
        if sql_upper.startswith('SELECT') and 'TOP ' not in sql_upper[:50]:
            # Insertar TOP después de SELECT
            sql = sql.replace('SELECT', f'SELECT TOP {limit}', 1)
            sql = sql.replace('select', f'SELECT TOP {limit}', 1)
        logging.info(f"Modo TEST con límite de {limit} registros")
    
    logging.info(f"Catálogo - Ejecutando {consulta_id} en {server['name']}")
    
    # Convertir fechas al formato YYYYMMDD sin guiones para compatibilidad con SQL Server
    for key in ['fecha_ini', 'fecha_fin', 'fecha']:
        if key in params and params[key]:
            # Quitar guiones si existen
            params[key] = params[key].replace('-', '')
    
    # Reemplazar los parámetros en el SQL
    sql_final = sql
    for key, val in params.items():
        sql_final = sql_final.replace('{' + key + '}', str(val))
    
    logging.info(f"SQL Final: {sql_final[:200]}...")
    
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], sql_final
        )
        
        return {
            "consulta": consulta['nombre'],
            "servidor": server['name'],
            "parametros": params,
            "registros": len(result),
            "datos": result
        }
        
    except Exception as e:
        logging.error(f"Error ejecutando consulta del catálogo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRUD CONSULTAS PERSONALIZADAS (MongoDB)
# ============================================================================

@api_router.get("/catalogo/consultas-custom")
async def listar_consultas_custom(current_user: Dict = Depends(get_current_user)):
    """Lista todas las consultas personalizadas guardadas en MongoDB"""
    consultas = await db.consultas_custom.find().to_list(1000)
    for c in consultas:
        c['_id'] = str(c['_id'])
    return consultas


@api_router.post("/catalogo/consultas-custom")
async def crear_consulta_custom(body: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Crea una nueva consulta personalizada.
    FASE 1B: Validación SQL obligatoria antes de guardar.
    """
    from core.security import SQLSanitizer, log_blocked_sql
    
    # Solo admin puede crear consultas
    if current_user.get('role') not in ['Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear consultas")
    
    # Validar campos requeridos
    required = ['nombre', 'descripcion', 'sistema', 'categoria', 'parametros', 'sql']
    for field in required:
        if field not in body or not body[field]:
            raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
    
    # FASE 1B: Validar SQL antes de guardar
    sql_to_validate = body['sql']
    validation = SQLSanitizer.validate_for_catalog(sql_to_validate)
    if not validation.is_safe:
        log_blocked_sql(validation, endpoint="/catalogo/consultas-custom", user_email=current_user.get('email'))
        raise HTTPException(
            status_code=400, 
            detail=f"SQL no permitido: {validation.blocked_reason}. Solo se permiten consultas SELECT/WITH."
        )
    
    # Generar ID único
    import uuid
    consulta_id = f"CUSTOM_{body['sistema']}_{uuid.uuid4().hex[:8].upper()}"
    
    consulta = {
        "id": consulta_id,
        "nombre": body['nombre'],
        "descripcion": body['descripcion'],
        "sistema": body['sistema'],
        "categoria": body['categoria'],
        "parametros": body['parametros'] if isinstance(body['parametros'], list) else body['parametros'].split(','),
        "sql": body['sql'],
        "created_by": current_user.get('email'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
        "validated": True,  # FASE 1B: Marcamos como validada
        "validation_timestamp": validation.validation_timestamp
    }
    
    await db.consultas_custom.insert_one(consulta)
    consulta.pop('_id', None)
    
    logging.info(f"[CATALOGO-CUSTOM] Consulta creada: {consulta_id} por {current_user.get('email')}")
    return {"message": "Consulta creada exitosamente", "consulta": consulta}


@api_router.put("/catalogo/consultas-custom/{consulta_id}")
async def actualizar_consulta_custom(consulta_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Actualiza una consulta personalizada.
    FASE 1B: Validación SQL obligatoria si se actualiza el campo sql.
    """
    from core.security import SQLSanitizer, log_blocked_sql
    
    if current_user.get('role') not in ['Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar consultas")
    
    consulta = await db.consultas_custom.find_one({"id": consulta_id})
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    update_data = {}
    for field in ['nombre', 'descripcion', 'categoria', 'parametros', 'sql']:
        if field in body:
            if field == 'parametros' and isinstance(body[field], str):
                update_data[field] = body[field].split(',')
            else:
                update_data[field] = body[field]
    
    # FASE 1B: Si se actualiza el SQL, validarlo
    if 'sql' in update_data:
        validation = SQLSanitizer.validate_for_catalog(update_data['sql'])
        if not validation.is_safe:
            log_blocked_sql(validation, endpoint=f"/catalogo/consultas-custom/{consulta_id}", user_email=current_user.get('email'))
            raise HTTPException(
                status_code=400, 
                detail=f"SQL no permitido: {validation.blocked_reason}. Solo se permiten consultas SELECT/WITH."
            )
        update_data['validated'] = True
        update_data['validation_timestamp'] = validation.validation_timestamp
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['updated_by'] = current_user.get('email')
    
    await db.consultas_custom.update_one({"id": consulta_id}, {"$set": update_data})
    
    logging.info(f"[CATALOGO-CUSTOM] Consulta actualizada: {consulta_id} por {current_user.get('email')}")
    return {"message": "Consulta actualizada"}


@api_router.put("/catalogo/consultas/{consulta_id}")
async def actualizar_consulta_sql(consulta_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Actualiza el SQL de cualquier consulta.
    Para consultas predefinidas, guarda una versión modificada en consultas_custom.
    """
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar consultas")
    
    sql_nuevo = body.get('sql')
    if not sql_nuevo:
        raise HTTPException(status_code=400, detail="Se requiere el campo 'sql'")
    
    # Verificar si es consulta custom
    consulta_custom = await db.consultas_custom.find_one({"id": consulta_id})
    if consulta_custom:
        # Actualizar consulta custom existente
        await db.consultas_custom.update_one(
            {"id": consulta_id},
            {"$set": {
                "sql": sql_nuevo,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user.get('email')
            }}
        )
        return {"message": "Consulta personalizada actualizada"}
    
    # Si es predefinida, verificar que existe y crear versión custom
    if consulta_id in CATALOGO_CONSULTAS:
        original = CATALOGO_CONSULTAS[consulta_id]
        # Guardar como versión modificada
        import uuid
        consulta_mod = {
            "id": f"{consulta_id}_mod_{uuid.uuid4().hex[:6]}",
            "original_id": consulta_id,
            "nombre": f"{original['nombre']} (Modificada)",
            "descripcion": original['descripcion'],
            "sistema": original['sistema'],
            "categoria": original['categoria'],
            "parametros": original['parametros'],
            "sql": sql_nuevo,
            "created_by": current_user.get('email'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
        await db.consultas_custom.insert_one(consulta_mod)
        consulta_mod.pop('_id', None)
        return {"message": "Versión modificada guardada", "consulta": consulta_mod}
    
    raise HTTPException(status_code=404, detail="Consulta no encontrada")


@api_router.delete("/catalogo/consultas-custom/{consulta_id}")
async def eliminar_consulta_custom(consulta_id: str, current_user: Dict = Depends(get_current_user)):
    """Elimina una consulta personalizada"""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar consultas")
    
    result = await db.consultas_custom.delete_one({"id": consulta_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    return {"message": "Consulta eliminada"}


@api_router.post("/catalogo/ejecutar-custom/{consulta_id}")
async def ejecutar_consulta_custom(
    consulta_id: str,
    server_id: str = Query(...),
    body: Dict = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta una consulta personalizada guardada en el catálogo.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 5
    """
    # Buscar consulta en MongoDB
    consulta = await db.consultas_custom.find_one({"id": consulta_id})
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    # Verificar servidor usando registry
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    from core.server_registry import get_server_connection_info
    conn_info = await get_server_connection_info(server_id, db=db)
    if not conn_info:
        raise HTTPException(status_code=404, detail="Servidor no encontrado o sin acceso")
    
    # Verificar que el sistema coincida
    if normalize_system_type(conn_info.get('system_type')) != normalize_system_type(consulta.get('sistema')):
        raise HTTPException(status_code=400, detail=f"Esta consulta es para {consulta['sistema']}, no para {conn_info.get('system_type')}")
    
    # Preparar parámetros
    parametros = body.get('parametros', body) if body else {}
    
    # Preparar SQL
    sql = consulta['sql']
    for param, valor in parametros.items():
        sql = sql.replace('{' + param + '}', str(valor))
    
    logging.info(f"Ejecutando consulta custom {consulta_id} en {conn_info.get('name')}")
    
    try:
        result = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],
            conn_info['username'], conn_info['password'], sql
        )
        
        return {
            "consulta": consulta['nombre'],
            "servidor": conn_info.get('name'),
            "parametros": parametros,
            "registros": len(result),
            "datos": result
        }
    except Exception as e:
        logging.error(f"Error ejecutando consulta custom: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INFORMES DE AUDITORÍA
# ============================================================================

@api_router.post("/informes-auditoria")
async def crear_informe_auditoria(
    informe: InformeAuditoriaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo informe de auditoría"""
    # Verificar rol
    if current_user.get('role') not in ['Administrador', 'Auditor']:
        raise HTTPException(status_code=403, detail="Solo administradores y auditores pueden crear informes")
    
    # Crear documento
    informe_doc = {
        "id": str(uuid.uuid4()),
        "server_id": informe.server_id,
        "sucursal_id": informe.sucursal_id,
        "sucursal_nombre": informe.sucursal_nombre,
        "establecimiento": informe.establecimiento,
        "gerente_responsable": informe.gerente_responsable,
        "auditor": informe.auditor,
        "auditor_id": current_user.get('user_id'),
        "periodo_inicio": informe.periodo_inicio,
        "periodo_fin": informe.periodo_fin,
        "fecha_emision": datetime.now(timezone.utc).isoformat(),
        "datos_inventario": informe.datos_inventario,
        "resumen_situacion": informe.resumen_situacion,
        "ajustes_tecnicos": informe.ajustes_tecnicos,
        "incluir_comparativo": informe.incluir_comparativo,
        "datos_comparativo": informe.datos_comparativo,
        "comentarios": informe.comentarios,
        "conclusiones": informe.conclusiones,
        "recomendaciones": informe.recomendaciones,
        "dictamen_economico": informe.dictamen_economico,
        "compromisos_almacen": informe.compromisos_almacen,
        "compromisos_personal": informe.compromisos_personal,
        "compromisos_gerencia": informe.compromisos_gerencia,
        "evidencias": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "estado": "borrador"
    }
    
    await db.informes_auditoria.insert_one(informe_doc)
    informe_doc.pop('_id', None)
    
    return {"message": "Informe creado exitosamente", "informe": informe_doc}


@api_router.get("/informes-auditoria")
async def listar_informes_auditoria(
    server_id: Optional[str] = None,
    sucursal_id: Optional[str] = None,
    auditor_id: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    estado: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista informes de auditoría con filtros opcionales, agrupados por sucursal"""
    # Verificar rol
    if current_user.get('role') not in ['Administrador', 'Auditor', 'Supervisor']:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver informes")
    
    # Construir filtro
    filtro = {}
    if server_id:
        filtro["server_id"] = server_id
    if sucursal_id:
        filtro["sucursal_id"] = sucursal_id
    if auditor_id:
        filtro["auditor_id"] = auditor_id
    if estado:
        filtro["estado"] = estado
    if fecha_desde:
        filtro["fecha_emision"] = {"$gte": fecha_desde}
    if fecha_hasta:
        if "fecha_emision" in filtro:
            filtro["fecha_emision"]["$lte"] = fecha_hasta
        else:
            filtro["fecha_emision"] = {"$lte": fecha_hasta}
    
    # Obtener informes
    cursor = db.informes_auditoria.find(filtro, {"_id": 0, "datos_inventario": 0, "datos_comparativo": 0, "evidencias": 0}).sort("fecha_emision", -1)
    informes = await cursor.to_list(500)
    
    # Agrupar por sucursal
    por_sucursal = {}
    for inf in informes:
        suc = inf.get('sucursal_nombre', 'Sin Sucursal')
        if suc not in por_sucursal:
            por_sucursal[suc] = []
        por_sucursal[suc].append(inf)
    
    return {
        "total": len(informes),
        "informes": informes,
        "por_sucursal": por_sucursal
    }


@api_router.get("/informes-auditoria/{informe_id}")
async def obtener_informe_auditoria(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un informe de auditoría específico"""
    informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
    if not informe:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    return informe


@api_router.put("/informes-auditoria/{informe_id}")
async def actualizar_informe_auditoria(
    informe_id: str,
    datos: InformeAuditoriaUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un informe de auditoría"""
    # Verificar rol
    if current_user.get('role') not in ['Administrador', 'Auditor']:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar informes")
    
    # Verificar que existe
    informe = await db.informes_auditoria.find_one({"id": informe_id})
    if not informe:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    # Solo el auditor que lo creó o un admin puede editarlo
    if current_user.get('role') != 'Administrador' and informe.get('auditor_id') != current_user.get('user_id'):
        raise HTTPException(status_code=403, detail="Solo puede editar sus propios informes")
    
    # Construir actualización
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field, value in datos.model_dump(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    await db.informes_auditoria.update_one({"id": informe_id}, {"$set": update_data})
    
    # Retornar actualizado
    informe_updated = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
    return {"message": "Informe actualizado", "informe": informe_updated}


@api_router.delete("/informes-auditoria/{informe_id}")
async def eliminar_informe_auditoria(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un informe de auditoría"""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar informes")
    
    result = await db.informes_auditoria.delete_one({"id": informe_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    return {"message": "Informe eliminado"}


@api_router.post("/informes-auditoria/{informe_id}/evidencias")
async def subir_evidencia(
    informe_id: str,
    archivo: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """Sube una evidencia al informe de auditoría"""
    # Verificar rol
    if current_user.get('role') not in ['Administrador', 'Auditor']:
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    # Verificar informe existe
    informe = await db.informes_auditoria.find_one({"id": informe_id})
    if not informe:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    # Verificar cantidad de evidencias (máximo 5)
    if len(informe.get('evidencias', [])) >= 5:
        raise HTTPException(status_code=400, detail="Máximo 5 evidencias por informe")
    
    # Verificar tamaño (máximo 10MB)
    contenido = await archivo.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo excede 10MB")
    
    # Determinar tipo
    extension = archivo.filename.split('.')[-1].lower() if '.' in archivo.filename else ''
    tipo_archivo = "otro"
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        tipo_archivo = "image"
    elif extension == 'pdf':
        tipo_archivo = "pdf"
    elif extension in ['doc', 'docx']:
        tipo_archivo = "word"
    elif extension in ['xls', 'xlsx']:
        tipo_archivo = "excel"
    
    # Crear evidencia
    evidencia = {
        "id": str(uuid.uuid4()),
        "nombre_archivo": archivo.filename,
        "tipo_archivo": tipo_archivo,
        "mime_type": archivo.content_type or "application/octet-stream",
        "tamanio": len(contenido),
        "data_base64": base64.b64encode(contenido).decode('utf-8'),
        "fecha_subida": datetime.now(timezone.utc).isoformat()
    }
    
    # Agregar al informe
    await db.informes_auditoria.update_one(
        {"id": informe_id},
        {
            "$push": {"evidencias": evidencia},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Retornar sin el data_base64 para no sobrecargar
    evidencia_response = {k: v for k, v in evidencia.items() if k != 'data_base64'}
    return {"message": "Evidencia subida", "evidencia": evidencia_response}


@api_router.delete("/informes-auditoria/{informe_id}/evidencias/{evidencia_id}")
async def eliminar_evidencia(
    informe_id: str,
    evidencia_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina una evidencia del informe"""
    if current_user.get('role') not in ['Administrador', 'Auditor']:
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    result = await db.informes_auditoria.update_one(
        {"id": informe_id},
        {
            "$pull": {"evidencias": {"id": evidencia_id}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    
    return {"message": "Evidencia eliminada"}


@api_router.get("/informes-auditoria/{informe_id}/evidencias/{evidencia_id}")
async def descargar_evidencia(
    informe_id: str,
    evidencia_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Descarga una evidencia"""
    informe = await db.informes_auditoria.find_one({"id": informe_id})
    if not informe:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    evidencia = next((e for e in informe.get('evidencias', []) if e['id'] == evidencia_id), None)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    
    contenido = base64.b64decode(evidencia['data_base64'])
    
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type=evidencia['mime_type'],
        headers={"Content-Disposition": f"attachment; filename={evidencia['nombre_archivo']}"}
    )


@api_router.put("/informes-auditoria/{informe_id}/estado")
async def cambiar_estado_informe(
    informe_id: str,
    estado: str = Query(..., regex="^(borrador|finalizado)$"),
    current_user: Dict = Depends(get_current_user)
):
    """Cambia el estado del informe (borrador/finalizado)"""
    if current_user.get('role') not in ['Administrador', 'Auditor']:
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    result = await db.informes_auditoria.update_one(
        {"id": informe_id},
        {"$set": {"estado": estado, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    return {"message": f"Estado cambiado a {estado}"}


@api_router.get("/informes-auditoria/{informe_id}/export-pdf")
async def exportar_informe_pdf(
    informe_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Exporta el informe de auditoría a PDF"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    
    informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
    if not informe:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCustom', fontSize=16, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='Subtitle', fontSize=12, fontName='Helvetica-Bold', spaceAfter=10, spaceBefore=15))
    styles.add(ParagraphStyle(name='BodyCustom', fontSize=10, fontName='Helvetica', alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle(name='SmallText', fontSize=9, fontName='Helvetica', spaceAfter=5))
    
    elements = []
    
    # Título
    elements.append(Paragraph("INFORME DE AUDITORÍA DE INVENTARIO", styles['TitleCustom']))
    elements.append(Paragraph("EDARSA HUB", styles['TitleCustom']))
    elements.append(Spacer(1, 20))
    
    # Información del encabezado
    header_data = [
        ["Establecimiento:", informe.get('establecimiento', '')],
        ["Gerente Responsable:", informe.get('gerente_responsable', '')],
        ["Auditor:", informe.get('auditor', '')],
        ["Fecha de Emisión:", informe.get('fecha_emision', '')[:10] if informe.get('fecha_emision') else ''],
        ["Período:", f"{informe.get('periodo_inicio', '')} a {informe.get('periodo_fin', '')}"],
    ]
    header_table = Table(header_data, colWidths=[4*cm, 12*cm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # 1. Resumen de Situación
    if informe.get('resumen_situacion'):
        elements.append(Paragraph("1. RESUMEN DE SITUACIÓN", styles['Subtitle']))
        elements.append(Paragraph(informe.get('resumen_situacion', '').replace('\n', '<br/>'), styles['BodyCustom']))
        elements.append(Spacer(1, 10))
    
    # 2. Ajustes Técnicos y Operativos
    if informe.get('ajustes_tecnicos'):
        elements.append(Paragraph("2. AJUSTES TÉCNICOS Y OPERATIVOS", styles['Subtitle']))
        elements.append(Paragraph(informe.get('ajustes_tecnicos', '').replace('\n', '<br/>'), styles['BodyCustom']))
        elements.append(Spacer(1, 10))
    
    # 3. Cuadro de Diferencias
    datos_inv = informe.get('datos_inventario', [])
    if datos_inv:
        elements.append(Paragraph("3. CUADRO INFORMATIVO DE DIFERENCIAS", styles['Subtitle']))
        
        # Crear tabla de inventario (simplificada)
        table_data = [["Producto", "Unidad", "Inv.Ini", "Mov", "Ventas", "Teórico", "Final", "Dif", "Importe"]]
        for item in datos_inv[:50]:  # Limitar a 50 productos para no sobrecargar el PDF
            dif = item.get('Diferencia_Cantidad', 0)
            if dif != 0:  # Solo mostrar productos con diferencia
                table_data.append([
                    str(item.get('Producto', ''))[:30],
                    str(item.get('Unidad', ''))[:5],
                    str(round(item.get('Inv_Inicial', 0), 2)),
                    str(round(item.get('Movimientos', 0), 2)),
                    str(round(item.get('Ventas', 0), 2)),
                    str(round(item.get('Inv_Teorico', 0), 2)),
                    str(round(item.get('Inv_Final', 0), 2)),
                    str(round(dif, 2)),
                    f"${round(item.get('Diferencia_Costo', 0), 2)}"
                ])
        
        if len(table_data) > 1:
            inv_table = Table(table_data, colWidths=[4.5*cm, 1.2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.2*cm, 2*cm])
            inv_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(inv_table)
        elements.append(Spacer(1, 10))
    
    # Dictamen Económico
    dictamen = informe.get('dictamen_economico', {})
    if dictamen:
        elements.append(Paragraph("DICTAMEN ECONÓMICO", styles['Subtitle']))
        dictamen_text = f"Total a comandear: ${dictamen.get('total_diferencia', 0):,.2f} MXN"
        if dictamen.get('responsable'):
            dictamen_text += f"<br/>Responsable: {dictamen.get('responsable')}"
        if dictamen.get('observaciones'):
            dictamen_text += f"<br/>Observaciones: {dictamen.get('observaciones')}"
        elements.append(Paragraph(dictamen_text, styles['BodyCustom']))
        elements.append(Spacer(1, 10))
    
    # 4. Comentarios del Auditor
    if informe.get('comentarios'):
        elements.append(Paragraph("4. COMENTARIOS DEL AUDITOR", styles['Subtitle']))
        elements.append(Paragraph(informe.get('comentarios', '').replace('\n', '<br/>'), styles['BodyCustom']))
        elements.append(Spacer(1, 10))
    
    # 5. Conclusiones
    if informe.get('conclusiones'):
        elements.append(Paragraph("5. CONCLUSIONES", styles['Subtitle']))
        elements.append(Paragraph(informe.get('conclusiones', '').replace('\n', '<br/>'), styles['BodyCustom']))
        elements.append(Spacer(1, 10))
    
    # 6. Recomendaciones
    if informe.get('recomendaciones'):
        elements.append(Paragraph("6. RECOMENDACIONES", styles['Subtitle']))
        elements.append(Paragraph(informe.get('recomendaciones', '').replace('\n', '<br/>'), styles['BodyCustom']))
        elements.append(Spacer(1, 10))
    
    # 7. Compromisos
    if informe.get('compromisos_almacen') or informe.get('compromisos_personal') or informe.get('compromisos_gerencia'):
        elements.append(Paragraph("7. COMPROMISOS", styles['Subtitle']))
        if informe.get('compromisos_almacen'):
            elements.append(Paragraph(f"<b>Almacén:</b> {informe.get('compromisos_almacen')}", styles['SmallText']))
        if informe.get('compromisos_personal'):
            elements.append(Paragraph(f"<b>Personal de Barra:</b> {informe.get('compromisos_personal')}", styles['SmallText']))
        if informe.get('compromisos_gerencia'):
            elements.append(Paragraph(f"<b>Gerencia:</b> {informe.get('compromisos_gerencia')}", styles['SmallText']))
        elements.append(Spacer(1, 10))
    
    # Comparativo 4 Cortes
    if informe.get('incluir_comparativo') and informe.get('datos_comparativo'):
        elements.append(Paragraph("ANEXO: COMPARATIVO DE 4 CORTES", styles['Subtitle']))
        comp_data = informe.get('datos_comparativo', [])
        if comp_data:
            # Simplificar para el PDF
            comp_table_data = [["Producto", "Corte 1", "Corte 2", "Corte 3", "Corte 4", "Total"]]
            for item in comp_data[:30]:
                comp_table_data.append([
                    str(item.get('Producto', ''))[:25],
                    str(item.get('corte_1', 0)),
                    str(item.get('corte_2', 0)),
                    str(item.get('corte_3', 0)),
                    str(item.get('corte_4', 0)),
                    str(item.get('total', 0))
                ])
            if len(comp_table_data) > 1:
                comp_table = Table(comp_table_data, colWidths=[5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d4a6f')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(comp_table)
    
    # Firma
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_" * 40, styles['BodyCustom']))
    elements.append(Paragraph(f"{informe.get('auditor', '')}<br/>Auditor EDARSA HUB", styles['SmallText']))
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"Informe_Auditoria_{informe.get('sucursal_nombre', 'SN').replace(' ', '_')}_{informe.get('periodo_fin', 'fecha')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# SISTEMA DE SOLICITUDES Y TAREAS
# ============================================================================

# Lista de catálogos del sistema disponibles para solicitudes
# niveles_aprobacion: 1 = Solo Supervisor/Admin, 2 = Supervisor + Admin, etc.
CATALOGOS_SISTEMA = [
    {"id": "puestos", "nombre": "Puestos", "modulo": "RRHH", "tabla": "RH_Cat_Puestos", "niveles_aprobacion": 1},
    {"id": "tipos_incidencias", "nombre": "Tipos de Incidencias", "modulo": "RRHH", "tabla": "RH_Cat_Tipos_Incidencias", "niveles_aprobacion": 1},
    {"id": "sucursales", "nombre": "Sucursales", "modulo": "RRHH", "tabla": "RH_Cat_Sucursales", "niveles_aprobacion": 2},
    {"id": "departamentos", "nombre": "Departamentos", "modulo": "RRHH", "tabla": "RH_Cat_Departamentos", "niveles_aprobacion": 1},
    {"id": "proveedores", "nombre": "Proveedores", "modulo": "Compras", "tabla": "Proveedores", "niveles_aprobacion": 2},
    {"id": "categorias_presupuesto", "nombre": "Categorías Presupuesto", "modulo": "Finanzas", "tabla": "Finanzas_Categorias", "niveles_aprobacion": 2},
    {"id": "almacenes", "nombre": "Almacenes", "modulo": "Inventarios", "tabla": "Almacenes", "niveles_aprobacion": 1},
    {"id": "familias", "nombre": "Familias de Productos", "modulo": "Inventarios", "tabla": "Familias", "niveles_aprobacion": 1},
    {"id": "categorias", "nombre": "Categorías de Productos", "modulo": "Inventarios", "tabla": "Categorias", "niveles_aprobacion": 1},
]

# Función para agregar evento al historial de una solicitud
async def agregar_evento_historial(solicitud_id: str, evento: Dict):
    """Agrega un evento al historial de trazabilidad de una solicitud"""
    evento["id"] = str(uuid.uuid4())
    evento["timestamp"] = datetime.now(timezone.utc).isoformat()
    await db.solicitudes_catalogos.update_one(
        {"id": solicitud_id},
        {"$push": {"historial": evento}}
    )

# ============= ENDPOINTS DE DIAGNÓSTICO DEL SISTEMA =============
# Añadidos en Prioridad 1 - Connection Pooling (Abril 2026)

@api_router.get("/sistema/pool-stats")
async def get_pool_statistics(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene estadísticas del connection pool de SQL Server.
    Solo accesible para Administradores.
    """
    if current_user.get("role") != "Administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver estadísticas del pool")
    
    try:
        from core.pool import get_pool_statistics, get_pool_manager
        from core.db import get_server_cache_status
        
        stats = get_pool_statistics()
        server_cache = get_server_cache_status()
        
        return {
            "pool_stats": stats,
            "server_cooldown_cache": server_cache,
            "mensaje": "Connection pooling activo - reduce overhead de conexiones SQL"
        }
    except Exception as e:
        return {
            "pool_stats": {"error": str(e)},
            "server_cooldown_cache": {},
            "mensaje": "Error obteniendo estadísticas"
        }

@api_router.post("/sistema/pool-reset")
async def reset_pool_connections(current_user: Dict = Depends(get_current_user)):
    """
    Resetea todos los pools de conexiones SQL Server.
    Solo accesible para Administradores. Usar con precaución.
    """
    if current_user.get("role") != "Administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden resetear pools")
    
    try:
        from core.pool import close_all_pools
        from core.db import reset_server_cache
        
        close_all_pools()
        reset_server_cache()
        
        return {
            "success": True,
            "mensaje": "Todos los pools de conexiones han sido reseteados"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# ENDPOINT SQL HEALTH CHECK (Abril 2026)
# =============================================================================

EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

@api_router.get("/sistema/sql-health")
async def sql_server_health_check(
    server_id: str = Query(default=None, description="ID del servidor. Si no se especifica, usa EDARSA HUB"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Realiza un health check de conexión a SQL Server con diagnóstico detallado.
    
    INTEGRACIÓN RESILIENTE (Abril 2026):
    - Prueba conectividad al servidor SQL remoto
    - Retorna latencia, estado y recomendaciones
    - Detecta tipo de error: red, auth, timeout, conexión muerta
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    
    Args:
        server_id: ID del servidor a probar (default: EDARSA HUB)
    
    Returns:
        Dict con diagnóstico completo incluyendo:
        - healthy: bool
        - server: string con host:port
        - database: nombre de la BD
        - latency_ms: latencia en milisegundos
        - error: mensaje de error si falla
        - error_type: tipo de error (network, auth, timeout, dead_connection, cooldown)
        - driver_used: pytds o pymssql
        - config: configuración de timeouts actual
        - recommendations: lista de recomendaciones
    """
    from core.db import sql_health_check, ResilientConfig
    from core.server_registry import get_server_connection_info
    
    # Obtener servidor
    target_server_id = server_id or EDARSA_HUB_SERVER_ID
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
    conn_info = await get_server_connection_info(target_server_id, db=db)
    
    if not conn_info:
        return {
            "healthy": False,
            "error": f"Servidor con ID '{target_server_id}' no encontrado o inactivo",
            "error_type": "configuration",
            "recommendations": [
                "Verificar que el ID del servidor es correcto",
                "Verificar que el servidor está marcado como activo en la configuración"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Ejecutar health check
    result = sql_health_check(
        host=conn_info['host'],
        port=conn_info['port'],
        database=conn_info['database'],
        username=conn_info['username'],
        password=conn_info['password']
    )
    
    # Agregar metadata del servidor
    result["server_id"] = target_server_id
    result["server_name"] = conn_info.get('name', 'Unknown')
    result["system_type"] = conn_info.get('system_type', 'Unknown')
    result["config_origin"] = conn_info.get('config_origin', 'Unknown')
    
    return result


@api_router.post("/sistema/sql-health/test-query")
async def sql_server_test_query(
    server_id: str = Query(default=None, description="ID del servidor"),
    tabla: str = Query(default="sys.tables", description="Tabla para probar"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta una query de prueba sobre SQL Server para validar conectividad real.
    
    Usa la lógica resiliente con reintentos automáticos.
    
    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
    CONEXIONES-SQL-EDARSAHUB-01 / LOTE 4
    
    Args:
        server_id: ID del servidor (default: EDARSA HUB)
        tabla: Tabla a consultar (default: sys.tables)
    
    Returns:
        Dict con resultado de la query de prueba
    """
    from core.db import execute_sql_query, ResilientConfig
    from core.server_registry import get_server_connection_info
    
    target_server_id = server_id or EDARSA_HUB_SERVER_ID
    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
    conn_info = await get_server_connection_info(target_server_id, db=db)
    
    if not conn_info:
        return {
            "success": False,
            "error": f"Servidor '{target_server_id}' no encontrado",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Query de prueba simple - usar * para compatibilidad con todas las tablas
    query = f"SELECT TOP 5 * FROM {tabla}"
    
    import time
    start = time.time()
    
    results = execute_sql_query(
        host=conn_info['host'],
        port=conn_info['port'],
        database=conn_info['database'],
        username=conn_info['username'],
        password=conn_info['password'],
        query=query,
        timeout_seconds=ResilientConfig.QUERY_TIMEOUT
    )
    
    elapsed = (time.time() - start) * 1000
    
    if results:
        return {
            "success": True,
            "tabla": tabla,
            "registros": len(results),
            "sample": results[:3] if len(results) > 3 else results,
            "latency_ms": round(elapsed, 2),
            "config": {
                "login_timeout": ResilientConfig.LOGIN_TIMEOUT,
                "query_timeout": ResilientConfig.QUERY_TIMEOUT,
                "max_retries": ResilientConfig.MAX_RETRIES
            },
            "config_origin": conn_info.get('config_origin', 'Unknown'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    else:
        return {
            "success": False,
            "error": "Query no retornó resultados o falló",
            "latency_ms": round(elapsed, 2),
            "recommendations": [
                "Verificar que la tabla existe",
                "Verificar permisos de lectura",
                "Revisar logs del backend para más detalles"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@api_router.get("/sistema/catalogos-disponibles")
async def listar_catalogos_sistema(current_user: Dict = Depends(get_current_user)):
    """Lista todos los catálogos del sistema disponibles para solicitudes"""
    # Obtener configuración personalizada de niveles desde MongoDB
    config = await db.config_catalogos.find_one({"tipo": "niveles_aprobacion"})
    config_niveles = config.get("niveles", {}) if config else {}
    
    catalogos_con_config = []
    for cat in CATALOGOS_SISTEMA:
        cat_copy = cat.copy()
        # Usar configuración personalizada si existe, sino usar el default
        cat_copy["niveles_aprobacion"] = config_niveles.get(cat["id"], cat.get("niveles_aprobacion", 1))
        catalogos_con_config.append(cat_copy)
    
    return {"catalogos": catalogos_con_config}


@api_router.put("/sistema/catalogos/{catalogo_id}/niveles")
async def configurar_niveles_catalogo(catalogo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Configura los niveles de aprobación de un catálogo (Solo Admin)"""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo Administradores pueden configurar niveles")
    
    niveles = body.get("niveles_aprobacion", 1)
    if niveles < 1 or niveles > 3:
        raise HTTPException(status_code=400, detail="Niveles debe ser entre 1 y 3")
    
    # Guardar/actualizar configuración
    await db.config_catalogos.update_one(
        {"tipo": "niveles_aprobacion"},
        {"$set": {f"niveles.{catalogo_id}": niveles}},
        upsert=True
    )
    
    # Registrar en log
    await agregar_evento_historial("CONFIG", {
        "accion": "CONFIGURACION_NIVELES",
        "usuario_id": current_user.get("id"),
        "usuario_email": current_user.get("email"),
        "catalogo_id": catalogo_id,
        "niveles_nuevos": niveles,
        "descripcion": f"Configuración de {niveles} nivel(es) de aprobación para {catalogo_id}"
    })
    
    return {"success": True, "message": f"Niveles de aprobación actualizados a {niveles}"}


@api_router.get("/sistema/permisos-catalogos/{user_id}")
async def obtener_permisos_catalogos_usuario(user_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene los permisos de catálogos de un usuario específico"""
    # Solo Supervisor o Administrador pueden ver permisos
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
    if not permisos:
        return {"user_id": user_id, "catalogos_permitidos": [], "puede_solicitar": False}
    
    return {
        "user_id": user_id,
        "catalogos_permitidos": permisos.get("catalogos_permitidos", []),
        "puede_solicitar": permisos.get("puede_solicitar", False),
        "asignado_por": permisos.get("asignado_por"),
        "fecha_asignacion": permisos.get("fecha_asignacion")
    }


@api_router.post("/sistema/permisos-catalogos")
async def asignar_permisos_catalogos(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Asigna permisos de catálogos a un usuario (Solo Supervisor, Admin o SuperAdmin)"""
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="Solo Supervisores o Administradores pueden asignar permisos")
    
    user_id = body.get("user_id")
    catalogos_permitidos = body.get("catalogos_permitidos", [])
    puede_solicitar = body.get("puede_solicitar", False)
    puede_autorizar = body.get("puede_autorizar", False)
    puede_liberar = body.get("puede_liberar", False)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id es requerido")
    
    # Verificar que el usuario existe
    usuario = await db.users.find_one({"id": user_id})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Guardar o actualizar permisos en colección permisos_catalogos
    await db.permisos_catalogos.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "catalogos_permitidos": catalogos_permitidos,
            "puede_solicitar": puede_solicitar,
            "puede_autorizar": puede_autorizar,
            "puede_liberar": puede_liberar,
            "asignado_por": current_user.get("email"),
            "fecha_asignacion": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # También actualizar en el documento del usuario para consulta rápida
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "permisos_catalogos": catalogos_permitidos,
            "puede_solicitar": puede_solicitar,
            "puede_autorizar": puede_autorizar,
            "puede_liberar": puede_liberar
        }}
    )
    
    return {"success": True, "message": "Permisos asignados correctamente"}


@api_router.get("/sistema/mis-permisos-catalogos")
async def obtener_mis_permisos_catalogos(current_user: Dict = Depends(get_current_user)):
    """Obtiene los permisos de catálogos del usuario actual"""
    user_id = current_user.get("id")
    
    # Administradores tienen todos los permisos
    if current_user.get('role') == 'Administrador':
        return {
            "puede_solicitar": True,
            "puede_aprobar": True,
            "catalogos_permitidos": [c["id"] for c in CATALOGOS_SISTEMA]
        }
    
    # Supervisores pueden aprobar
    puede_aprobar = current_user.get('role') == 'Supervisor'
    
    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
    if not permisos:
        return {"puede_solicitar": False, "puede_aprobar": puede_aprobar, "catalogos_permitidos": []}
    
    return {
        "puede_solicitar": permisos.get("puede_solicitar", False),
        "puede_aprobar": puede_aprobar,
        "catalogos_permitidos": permisos.get("catalogos_permitidos", [])
    }


@api_router.post("/sistema/solicitudes")
async def crear_solicitud_catalogo(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea una nueva solicitud de alta en catálogo"""
    catalogo_id = body.get("catalogo_id")
    datos = body.get("datos", {})
    notas = body.get("notas", "")
    
    if not catalogo_id or not datos:
        raise HTTPException(status_code=400, detail="catalogo_id y datos son requeridos")
    
    # Verificar permisos del usuario
    user_id = current_user.get("id")
    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
    
    # Administradores siempre pueden
    if current_user.get('role') != 'Administrador':
        if not permisos or not permisos.get("puede_solicitar"):
            raise HTTPException(status_code=403, detail="No tiene permiso para solicitar altas")
        
        if catalogo_id not in permisos.get("catalogos_permitidos", []):
            raise HTTPException(status_code=403, detail=f"No tiene permiso para solicitar altas en el catálogo: {catalogo_id}")
    
    # Obtener info del catálogo incluyendo niveles configurados
    catalogo_info = next((c for c in CATALOGOS_SISTEMA if c["id"] == catalogo_id), None)
    if not catalogo_info:
        raise HTTPException(status_code=400, detail="Catálogo no válido")
    
    # Obtener configuración de niveles personalizada
    config = await db.config_catalogos.find_one({"tipo": "niveles_aprobacion"})
    niveles_requeridos = config.get("niveles", {}).get(catalogo_id, catalogo_info.get("niveles_aprobacion", 1)) if config else catalogo_info.get("niveles_aprobacion", 1)
    
    solicitud_id = str(uuid.uuid4())
    ahora = datetime.now(timezone.utc).isoformat()
    
    # Evento inicial del historial
    evento_creacion = {
        "id": str(uuid.uuid4()),
        "timestamp": ahora,
        "accion": "CREACION",
        "usuario_id": user_id,
        "usuario_email": current_user.get("email"),
        "usuario_nombre": current_user.get("name", current_user.get("email")),
        "descripcion": "Solicitud creada",
        "datos_snapshot": datos.copy(),
        "estatus_anterior": None,
        "estatus_nuevo": "Pendiente Nivel 1"
    }
    
    solicitud = {
        "id": solicitud_id,
        "catalogo_id": catalogo_id,
        "catalogo_nombre": catalogo_info["nombre"],
        "modulo": catalogo_info["modulo"],
        "datos": datos,
        "notas": notas,
        "version": 1,  # Versión de la solicitud (incrementa con correcciones)
        "estatus": "Pendiente Nivel 1",
        "nivel_actual": 1,
        "niveles_requeridos": niveles_requeridos,
        "aprobaciones": [],  # Lista de aprobaciones por nivel
        "solicitante_id": user_id,
        "solicitante_email": current_user.get("email"),
        "solicitante_nombre": current_user.get("name", current_user.get("email")),
        "fecha_solicitud": ahora,
        "fecha_ultima_modificacion": ahora,
        "aprobador_final_id": None,
        "aprobador_final_email": None,
        "fecha_aprobacion_final": None,
        "motivo_rechazo": None,
        "historial": [evento_creacion]
    }
    
    await db.solicitudes_catalogos.insert_one(solicitud)
    
    # Crear tarea para supervisores/admins
    tarea = {
        "id": str(uuid.uuid4()),
        "tipo": "aprobacion_catalogo",
        "titulo": f"Aprobar alta en {catalogo_info['nombre']} (Nivel 1/{niveles_requeridos})",
        "descripcion": f"Solicitud de {current_user.get('name', current_user.get('email'))} para agregar elemento al catálogo {catalogo_info['nombre']}",
        "solicitud_id": solicitud_id,
        "nivel_aprobacion": 1,
        "estatus": "Pendiente",
        "prioridad": "Normal",
        "asignado_a_roles": ["Supervisor", "Administrador"],
        "creado_por": user_id,
        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
        "fecha_limite": None
    }
    await db.tareas_sistema.insert_one(tarea)
    
    return {"success": True, "solicitud_id": solicitud_id, "message": "Solicitud creada correctamente"}


@api_router.get("/sistema/solicitudes")
async def listar_solicitudes(
    estatus: str = None,
    catalogo_id: str = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista solicitudes de catálogos"""
    filtro = {}
    
    # Usuarios normales solo ven sus propias solicitudes
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        filtro["solicitante_id"] = current_user.get("id")
    
    if estatus:
        filtro["estatus"] = estatus
    if catalogo_id:
        filtro["catalogo_id"] = catalogo_id
    
    solicitudes = await db.solicitudes_catalogos.find(filtro, {"_id": 0}).sort("fecha_solicitud", -1).to_list(100)
    
    return {"solicitudes": solicitudes, "total": len(solicitudes)}


@api_router.get("/sistema/solicitudes/{solicitud_id}")
async def obtener_solicitud(solicitud_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene detalle de una solicitud"""
    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id}, {"_id": 0})
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Verificar acceso
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        if solicitud.get("solicitante_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")
    
    return solicitud


@api_router.post("/sistema/solicitudes/{solicitud_id}/aprobar")
async def aprobar_solicitud(solicitud_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Aprueba una solicitud con firma (contraseña del aprobador) - Soporta múltiples niveles"""
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="Solo Supervisores o Administradores pueden aprobar")
    
    password = body.get("password")
    comentario = body.get("comentario", "")
    if not password:
        raise HTTPException(status_code=400, detail="Contraseña de autorización requerida")
    
    # Verificar password
    if not verify_password(password, current_user.get("password")):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    # Obtener solicitud
    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    estatus_actual = solicitud.get("estatus", "")
    if "Pendiente" not in estatus_actual and estatus_actual != "Reenviada":
        raise HTTPException(status_code=400, detail="La solicitud no está pendiente de aprobación")
    
    ahora = datetime.now(timezone.utc).isoformat()
    nivel_actual = solicitud.get("nivel_actual", 1)
    niveles_requeridos = solicitud.get("niveles_requeridos", 1)
    aprobaciones = solicitud.get("aprobaciones", [])
    
    # Verificar que no haya aprobado ya este nivel
    ya_aprobo = any(a.get("aprobador_id") == current_user.get("id") and a.get("nivel") == nivel_actual for a in aprobaciones)
    if ya_aprobo:
        raise HTTPException(status_code=400, detail="Ya aprobó este nivel")
    
    # Restricción: Supervisores solo pueden aprobar nivel 1, Admins pueden aprobar cualquier nivel
    if current_user.get('role') == 'Supervisor' and nivel_actual > 1:
        raise HTTPException(status_code=403, detail="Solo Administradores pueden aprobar niveles superiores al 1")
    
    # Registrar aprobación de este nivel
    aprobacion = {
        "nivel": nivel_actual,
        "aprobador_id": current_user.get("id"),
        "aprobador_email": current_user.get("email"),
        "aprobador_nombre": current_user.get("name", current_user.get("email")),
        "fecha": ahora,
        "comentario": comentario
    }
    aprobaciones.append(aprobacion)
    
    estatus_anterior = estatus_actual
    
    # Determinar si ya completó todos los niveles
    if nivel_actual >= niveles_requeridos:
        # Aprobación final
        nuevo_estatus = "Aprobada"
        nuevo_nivel = nivel_actual
        
        # Insertar en SQL
        catalogo_id = solicitud.get("catalogo_id")
        datos = solicitud.get("datos", {})
        
        try:
            if catalogo_id == "puestos":
                query = f"""
                    INSERT INTO RH_Cat_Puestos (Descripcion, Departamento, Sueldo_Base_Seman_SBC, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
                    VALUES ('{datos.get("descripcion", "")}', '{datos.get("departamento", "")}', {datos.get("sueldo_base", 0)}, 
                            '{datos.get("nomipaq_id", "")}', '{datos.get("mpro_id", "")}', GETDATE(), '{current_user.get("email")}')
                """
                await execute_edarsa_hub_query(query)
            
            elif catalogo_id == "tipos_incidencias":
                categoria = datos.get("categoria", "Descuento")
                afectacion = 1 if categoria == "Ingreso" else -1
                query = f"""
                    INSERT INTO RH_Cat_Tipos_Incidencias (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto, Activo, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
                    VALUES ('{datos.get("codigo", "").upper()}', '{datos.get("descripcion", "")}', '{categoria}', {afectacion},
                            '{datos.get("calculo_monto", "Manual")}', 1, '{datos.get("nomipaq_id", "")}', '{datos.get("mpro_id", "")}', 
                            GETDATE(), '{current_user.get("email")}')
                """
                await execute_edarsa_hub_query(query)
        except Exception as e:
            print(f"Error insertando en SQL: {e}")
        
        # Actualizar solicitud como aprobada final
        await db.solicitudes_catalogos.update_one(
            {"id": solicitud_id},
            {"$set": {
                "estatus": nuevo_estatus,
                "nivel_actual": nuevo_nivel,
                "aprobaciones": aprobaciones,
                "aprobador_final_id": current_user.get("id"),
                "aprobador_final_email": current_user.get("email"),
                "fecha_aprobacion_final": ahora,
                "fecha_ultima_modificacion": ahora
            },
            "$push": {"historial": {
                "id": str(uuid.uuid4()),
                "timestamp": ahora,
                "accion": "APROBACION_FINAL",
                "usuario_id": current_user.get("id"),
                "usuario_email": current_user.get("email"),
                "usuario_nombre": current_user.get("name", current_user.get("email")),
                "descripcion": f"Aprobación final (Nivel {nivel_actual}/{niveles_requeridos})",
                "comentario": comentario,
                "estatus_anterior": estatus_anterior,
                "estatus_nuevo": nuevo_estatus
            }}}
        )
        
        # Notificar al solicitante
        notificacion = {
            "id": str(uuid.uuid4()),
            "tipo": "notificacion",
            "titulo": f"Tu solicitud fue APROBADA",
            "descripcion": f"La solicitud de alta en {solicitud.get('catalogo_nombre')} fue aprobada y registrada en el sistema.",
            "solicitud_id": solicitud_id,
            "estatus": "Pendiente",
            "prioridad": "Normal",
            "asignado_a_usuario": solicitud.get("solicitante_id"),
            "creado_por": current_user.get("id"),
            "fecha_creacion": ahora
        }
        await db.tareas_sistema.insert_one(notificacion)
        
        mensaje = "Solicitud aprobada e insertada en el catálogo"
    else:
        # Pasar al siguiente nivel
        nuevo_nivel = nivel_actual + 1
        nuevo_estatus = f"Pendiente Nivel {nuevo_nivel}"
        
        await db.solicitudes_catalogos.update_one(
            {"id": solicitud_id},
            {"$set": {
                "estatus": nuevo_estatus,
                "nivel_actual": nuevo_nivel,
                "aprobaciones": aprobaciones,
                "fecha_ultima_modificacion": ahora
            },
            "$push": {"historial": {
                "id": str(uuid.uuid4()),
                "timestamp": ahora,
                "accion": "APROBACION_NIVEL",
                "usuario_id": current_user.get("id"),
                "usuario_email": current_user.get("email"),
                "usuario_nombre": current_user.get("name", current_user.get("email")),
                "descripcion": f"Aprobación de Nivel {nivel_actual}/{niveles_requeridos}",
                "comentario": comentario,
                "estatus_anterior": estatus_anterior,
                "estatus_nuevo": nuevo_estatus
            }}}
        )
        
        # Crear tarea para el siguiente nivel (solo Admins si nivel > 1)
        tarea = {
            "id": str(uuid.uuid4()),
            "tipo": "aprobacion_catalogo",
            "titulo": f"Aprobar alta en {solicitud.get('catalogo_nombre')} (Nivel {nuevo_nivel}/{niveles_requeridos})",
            "descripcion": f"Solicitud requiere aprobación de Nivel {nuevo_nivel}",
            "solicitud_id": solicitud_id,
            "nivel_aprobacion": nuevo_nivel,
            "estatus": "Pendiente",
            "prioridad": "Alta",
            "asignado_a_roles": ["Administrador"] if nuevo_nivel > 1 else ["Supervisor", "Administrador"],
            "creado_por": current_user.get("id"),
            "fecha_creacion": ahora
        }
        await db.tareas_sistema.insert_one(tarea)
        
        mensaje = f"Nivel {nivel_actual} aprobado. Pendiente aprobación de Nivel {nuevo_nivel}"
    
    # Actualizar tareas anteriores como completadas
    await db.tareas_sistema.update_many(
        {"solicitud_id": solicitud_id, "nivel_aprobacion": nivel_actual},
        {"$set": {"estatus": "Completada", "completado_por": current_user.get("id"), "fecha_completado": ahora}}
    )
    
    return {"success": True, "message": mensaje, "estatus": nuevo_estatus if nivel_actual < niveles_requeridos else "Aprobada"}


@api_router.post("/sistema/solicitudes/{solicitud_id}/rechazar")
async def rechazar_solicitud(solicitud_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Rechaza una solicitud - El solicitante podrá corregir y reenviar"""
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        raise HTTPException(status_code=403, detail="Solo Supervisores o Administradores pueden rechazar")
    
    motivo = body.get("motivo", "Sin motivo especificado")
    
    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    estatus_actual = solicitud.get("estatus", "")
    if "Pendiente" not in estatus_actual and estatus_actual != "Reenviada":
        raise HTTPException(status_code=400, detail="La solicitud no está pendiente de revisión")
    
    ahora = datetime.now(timezone.utc).isoformat()
    
    # Actualizar solicitud - queda en estado "Rechazada - Pendiente Corrección"
    await db.solicitudes_catalogos.update_one(
        {"id": solicitud_id},
        {"$set": {
            "estatus": "Rechazada - Pendiente Corrección",
            "motivo_rechazo": motivo,
            "rechazado_por_id": current_user.get("id"),
            "rechazado_por_email": current_user.get("email"),
            "fecha_rechazo": ahora,
            "fecha_ultima_modificacion": ahora
        },
        "$push": {"historial": {
            "id": str(uuid.uuid4()),
            "timestamp": ahora,
            "accion": "RECHAZO",
            "usuario_id": current_user.get("id"),
            "usuario_email": current_user.get("email"),
            "usuario_nombre": current_user.get("name", current_user.get("email")),
            "descripcion": f"Solicitud rechazada",
            "motivo": motivo,
            "estatus_anterior": estatus_actual,
            "estatus_nuevo": "Rechazada - Pendiente Corrección"
        }}}
    )
    
    # Actualizar tareas relacionadas
    await db.tareas_sistema.update_many(
        {"solicitud_id": solicitud_id, "estatus": "Pendiente"},
        {"$set": {"estatus": "Rechazada", "completado_por": current_user.get("id"), "fecha_completado": ahora}}
    )
    
    # Notificar al solicitante que puede corregir
    notificacion = {
        "id": str(uuid.uuid4()),
        "tipo": "notificacion_correccion",
        "titulo": f"Solicitud rechazada - Puede corregir y reenviar",
        "descripcion": f"La solicitud de alta en {solicitud.get('catalogo_nombre')} requiere correcciones. Motivo: {motivo}",
        "solicitud_id": solicitud_id,
        "estatus": "Pendiente",
        "prioridad": "Alta",
        "asignado_a_usuario": solicitud.get("solicitante_id"),
        "creado_por": current_user.get("id"),
        "fecha_creacion": ahora,
        "permite_correccion": True
    }
    await db.tareas_sistema.insert_one(notificacion)
    
    return {"success": True, "message": "Solicitud rechazada. El solicitante podrá corregir y reenviar."}


@api_router.put("/sistema/solicitudes/{solicitud_id}/corregir")
async def corregir_solicitud(solicitud_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Permite al solicitante corregir una solicitud rechazada y reenviarla"""
    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Verificar que sea el solicitante original
    if solicitud.get("solicitante_id") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Solo el solicitante original puede corregir")
    
    # Verificar que esté en estado de corrección
    if solicitud.get("estatus") != "Rechazada - Pendiente Corrección":
        raise HTTPException(status_code=400, detail="La solicitud no está pendiente de corrección")
    
    nuevos_datos = body.get("datos")
    nuevas_notas = body.get("notas", solicitud.get("notas", ""))
    
    if not nuevos_datos:
        raise HTTPException(status_code=400, detail="Debe proporcionar los datos corregidos")
    
    ahora = datetime.now(timezone.utc).isoformat()
    version_anterior = solicitud.get("version", 1)
    nueva_version = version_anterior + 1
    
    # Actualizar solicitud con datos corregidos
    await db.solicitudes_catalogos.update_one(
        {"id": solicitud_id},
        {"$set": {
            "datos": nuevos_datos,
            "notas": nuevas_notas,
            "version": nueva_version,
            "estatus": "Reenviada",
            "nivel_actual": 1,  # Vuelve al nivel 1
            "aprobaciones": [],  # Limpiar aprobaciones anteriores
            "motivo_rechazo": None,
            "fecha_ultima_modificacion": ahora
        },
        "$push": {"historial": {
            "id": str(uuid.uuid4()),
            "timestamp": ahora,
            "accion": "CORRECCION",
            "usuario_id": current_user.get("id"),
            "usuario_email": current_user.get("email"),
            "usuario_nombre": current_user.get("name", current_user.get("email")),
            "descripcion": f"Solicitud corregida y reenviada (v{nueva_version})",
            "datos_anteriores": solicitud.get("datos"),
            "datos_nuevos": nuevos_datos,
            "estatus_anterior": "Rechazada - Pendiente Corrección",
            "estatus_nuevo": "Reenviada"
        }}}
    )
    
    # Crear nueva tarea para aprobadores
    niveles_requeridos = solicitud.get("niveles_requeridos", 1)
    tarea = {
        "id": str(uuid.uuid4()),
        "tipo": "aprobacion_catalogo",
        "titulo": f"Revisar corrección: {solicitud.get('catalogo_nombre')} (v{nueva_version})",
        "descripcion": f"Solicitud corregida por {current_user.get('name', current_user.get('email'))} - Nivel 1/{niveles_requeridos}",
        "solicitud_id": solicitud_id,
        "nivel_aprobacion": 1,
        "estatus": "Pendiente",
        "prioridad": "Alta",
        "asignado_a_roles": ["Supervisor", "Administrador"],
        "creado_por": current_user.get("id"),
        "fecha_creacion": ahora
    }
    await db.tareas_sistema.insert_one(tarea)
    
    return {"success": True, "message": f"Solicitud corregida y reenviada (versión {nueva_version})"}


@api_router.get("/sistema/solicitudes/{solicitud_id}/historial")
async def obtener_historial_solicitud(solicitud_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene el historial completo de trazabilidad de una solicitud"""
    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id}, {"_id": 0})
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Verificar acceso
    if current_user.get('role') not in ['Supervisor', 'Administrador', 'SuperAdministrador']:
        if solicitud.get("solicitante_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")
    
    historial = solicitud.get("historial", [])
    aprobaciones = solicitud.get("aprobaciones", [])
    
    return {
        "solicitud_id": solicitud_id,
        "catalogo": solicitud.get("catalogo_nombre"),
        "version_actual": solicitud.get("version", 1),
        "estatus_actual": solicitud.get("estatus"),
        "nivel_actual": solicitud.get("nivel_actual", 1),
        "niveles_requeridos": solicitud.get("niveles_requeridos", 1),
        "solicitante": {
            "id": solicitud.get("solicitante_id"),
            "email": solicitud.get("solicitante_email"),
            "nombre": solicitud.get("solicitante_nombre")
        },
        "aprobaciones": aprobaciones,
        "historial": sorted(historial, key=lambda x: x.get("timestamp", ""), reverse=True),
        "total_eventos": len(historial)
    }


@api_router.get("/sistema/mis-tareas")
async def obtener_mis_tareas(current_user: Dict = Depends(get_current_user)):
    """Obtiene las tareas asignadas al usuario actual"""
    user_id = current_user.get("id")
    user_role = current_user.get("role")
    
    # Tareas asignadas directamente al usuario
    filtro_usuario = {"asignado_a_usuario": user_id}
    
    # Tareas asignadas por rol
    filtro_rol = {"asignado_a_roles": user_role}
    
    # Combinar ambos filtros
    tareas = await db.tareas_sistema.find(
        {"$or": [filtro_usuario, filtro_rol]},
        {"_id": 0}
    ).sort("fecha_creacion", -1).to_list(100)
    
    # Separar por estatus
    pendientes = [t for t in tareas if t.get("estatus") == "Pendiente"]
    en_proceso = [t for t in tareas if t.get("estatus") == "En Proceso"]
    completadas = [t for t in tareas if t.get("estatus") in ["Completada", "Rechazada", "Leida"]]
    
    # Contar solicitudes pendientes de aprobar (para badge)
    solicitudes_pendientes = await db.solicitudes_catalogos.count_documents({"estatus": "Pendiente"}) if user_role in ['Supervisor', 'Administrador'] else 0
    
    return {
        "pendientes": pendientes,
        "en_proceso": en_proceso,
        "completadas": completadas[:20],  # Limitar historial
        "total_pendientes": len(pendientes),
        "total_en_proceso": len(en_proceso),
        "solicitudes_pendientes_aprobar": solicitudes_pendientes
    }


@api_router.get("/sistema/pendientes-unificados")
async def obtener_pendientes_unificados(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene TODOS los pendientes del usuario en una bandeja unificada.
    Incluye: Solicitudes de catálogos, Proveedores, Nóminas, etc.
    Ordenados por: Urgentes/Vencidos primero, luego agrupados por tipo.
    """
    current_user.get("id")
    user_role = current_user.get("role")
    ahora = datetime.now(timezone.utc)
    
    urgentes = []  # Vencidos y próximos a vencer (< 24h)
    pendientes_catalogos = []
    pendientes_proveedores = []
    pendientes_nominas = []
    
    # ===== 1. SOLICITUDES DE CATÁLOGOS =====
    if user_role in ['Supervisor', 'Administrador']:
        solicitudes = await db.solicitudes_catalogos.find(
            {"estatus": "Pendiente"},
            {"_id": 0}
        ).sort("fecha_solicitud", -1).to_list(100)
        
        for sol in solicitudes:
            fecha_sol = datetime.fromisoformat(sol.get("fecha_solicitud", ahora.isoformat()).replace("Z", "+00:00"))
            horas_pendiente = (ahora - fecha_sol).total_seconds() / 3600
            
            item = {
                "id": sol.get("id"),
                "tipo": "catalogo",
                "titulo": f"Solicitud de {sol.get('catalogo_nombre', 'Catálogo')}",
                "descripcion": sol.get("notas", "Sin descripción"),
                "solicitante": sol.get("solicitante_nombre", "Usuario"),
                "fecha": sol.get("fecha_solicitud"),
                "horas_pendiente": round(horas_pendiente, 1),
                "vencido": horas_pendiente > 48,  # Más de 48h = vencido
                "proximo_vencer": 24 < horas_pendiente <= 48,
                "data": sol
            }
            
            if item["vencido"] or item["proximo_vencer"]:
                urgentes.append(item)
            else:
                pendientes_catalogos.append(item)
    
    # ===== 2. PROVEEDORES PENDIENTES DE APROBAR =====
    if user_role in ['Supervisor', 'Administrador']:
        proveedores = await db.portal_proveedores.find(
            {"status": "pending"},
            {"_id": 0}
        ).sort("fecha_registro", -1).to_list(100)
        
        for prov in proveedores:
            fecha_reg = prov.get("fecha_registro")
            if fecha_reg:
                try:
                    fecha_prov = datetime.fromisoformat(fecha_reg.replace("Z", "+00:00"))
                    horas_pendiente = (ahora - fecha_prov).total_seconds() / 3600
                except Exception:
                    horas_pendiente = 0
            else:
                horas_pendiente = 0
            
            item = {
                "id": prov.get("id"),
                "tipo": "proveedor",
                "titulo": f"Proveedor: {prov.get('razon_social', 'Sin nombre')}",
                "descripcion": f"RFC: {prov.get('rfc', 'N/A')} - {prov.get('email', '')}",
                "solicitante": prov.get("razon_social"),
                "fecha": fecha_reg,
                "horas_pendiente": round(horas_pendiente, 1),
                "vencido": horas_pendiente > 72,  # Más de 72h = vencido
                "proximo_vencer": 48 < horas_pendiente <= 72,
                "data": prov
            }
            
            if item["vencido"] or item["proximo_vencer"]:
                urgentes.append(item)
            else:
                pendientes_proveedores.append(item)
    
    # ===== 3. NÓMINAS PENDIENTES POR ROL =====
    # Mapeo de etapas a roles
    etapas_por_rol = {
        "Administrador": ["headcount", "incidencias", "validacion_rh", "maquilador", "autorizacion", "tesoreria"],
        "Supervisor": ["headcount", "incidencias", "validacion_rh", "autorizacion"],
        "Gerente": ["headcount", "incidencias", "autorizacion"],
        "Maquilador": ["maquilador"],
        "Tesoreria": ["tesoreria"],
        "RH": ["validacion_rh"]
    }
    
    etapas_usuario = etapas_por_rol.get(user_role, [])
    
    if etapas_usuario:
        ciclos = await db.nomina_ciclos.find(
            {"etapa_actual": {"$in": etapas_usuario}, "estatus": {"$ne": "cancelado"}},
            {"_id": 0}
        ).to_list(100)
        
        # Obtener configuración para calcular vencimientos
        config = await db.nomina_configuracion.find_one({}, {"_id": 0})
        {
            "headcount": config.get("horario_headcount", "10:00") if config else "10:00",
            "incidencias": config.get("horario_headcount", "10:00") if config else "10:00",
            "validacion_rh": config.get("horario_autorizacion", "11:00") if config else "11:00",
            "autorizacion": config.get("horario_autorizacion", "11:00") if config else "11:00",
            "maquilador": config.get("horario_maquilador", "12:00") if config else "12:00",
            "tesoreria": config.get("horario_tesoreria", "14:00") if config else "14:00"
        }
        
        etapa_nombres = {
            "headcount": "Headcount",
            "incidencias": "Incidencias",
            "validacion_rh": "Validación RH",
            "maquilador": "Maquilador",
            "autorizacion": "Autorización",
            "tesoreria": "Tesorería"
        }
        
        for ciclo in ciclos:
            etapa = ciclo.get("etapa_actual", "")
            fecha_corte = ciclo.get("fecha_corte", "")
            sucursal = ciclo.get("sucursal_nombre", "Sucursal")
            
            # Calcular si está vencido basado en deadline
            try:
                deadline_str = ciclo.get(f"deadline_{etapa}")
                if deadline_str:
                    deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    horas_restantes = (deadline - ahora).total_seconds() / 3600
                    vencido = horas_restantes < 0
                    proximo_vencer = 0 <= horas_restantes < 24
                else:
                    horas_restantes = 0
                    vencido = True
                    proximo_vencer = False
            except Exception:
                horas_restantes = 0
                vencido = True
                proximo_vencer = False
            
            item = {
                "id": ciclo.get("id"),
                "tipo": "nomina",
                "subtipo": etapa,
                "titulo": f"Nómina {sucursal} - {etapa_nombres.get(etapa, etapa)}",
                "descripcion": f"Corte: {fecha_corte} | {ciclo.get('tipo_nomina', 'Quincenal')}",
                "solicitante": sucursal,
                "fecha": ciclo.get("fecha_creacion"),
                "deadline": ciclo.get(f"deadline_{etapa}"),
                "horas_restantes": round(horas_restantes, 1),
                "vencido": vencido,
                "proximo_vencer": proximo_vencer,
                "data": ciclo
            }
            
            if item["vencido"] or item["proximo_vencer"]:
                urgentes.append(item)
            else:
                pendientes_nominas.append(item)
    
    # ===== ORDENAR URGENTES =====
    # Primero los vencidos (más antiguos primero), luego próximos a vencer
    urgentes.sort(key=lambda x: (not x["vencido"], x.get("horas_restantes", 0) if x["tipo"] == "nomina" else -x.get("horas_pendiente", 0)))
    
    return {
        "urgentes": urgentes,
        "catalogos": pendientes_catalogos,
        "proveedores": pendientes_proveedores,
        "nominas": pendientes_nominas,
        "contadores": {
            "urgentes": len(urgentes),
            "catalogos": len(pendientes_catalogos),
            "proveedores": len(pendientes_proveedores),
            "nominas": len(pendientes_nominas),
            "total": len(urgentes) + len(pendientes_catalogos) + len(pendientes_proveedores) + len(pendientes_nominas)
        }
    }
async def marcar_tarea_leida(tarea_id: str, current_user: Dict = Depends(get_current_user)):
    """Marca una tarea/notificación como leída"""
    await db.tareas_sistema.update_one(
        {"id": tarea_id},
        {"$set": {"estatus": "Leida", "fecha_leida": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True}


@api_router.get("/sistema/usuarios-asignables")
async def listar_usuarios_asignables(current_user: Dict = Depends(get_current_user)):
    """Lista usuarios que pueden recibir permisos de catálogos (para roles con permiso 'usuarios')"""
    # Verificar permisos dinámicamente basado en el rol del usuario
    user_role = current_user.get('role', '')
    
    # Roles de sistema con acceso directo
    allowed_base_roles = ['Supervisor', 'Administrador']
    
    # Verificar si el rol tiene permiso 'usuarios' en la BD
    has_access = user_role in allowed_base_roles
    if not has_access:
        role_doc = await db.roles.find_one({"nombre": user_role}, {"_id": 0, "permisos": 1})
        if role_doc and "usuarios" in role_doc.get("permisos", []):
            has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener usuarios activos
    usuarios = await db.users.find(
        {"active": True},
        {"_id": 0, "id": 1, "email": 1, "name": 1, "role": 1}
    ).to_list(500)
    
    # Agregar info de permisos actuales
    for u in usuarios:
        permisos = await db.permisos_catalogos.find_one({"user_id": u["id"]})
        u["permisos_catalogos"] = permisos.get("catalogos_permitidos", []) if permisos else []
        u["puede_solicitar"] = permisos.get("puede_solicitar", False) if permisos else False
    
    return {"usuarios": usuarios}


# Script SQL para crear tablas de sistema en EDARSA HUB (si se requiere)
@api_router.get("/sistema/script-tareas")
async def obtener_script_tareas(current_user: Dict = Depends(get_current_user)):
    """Retorna script SQL para crear tablas de tareas en EDARSA HUB (opcional)"""
    script = """
-- ============================================
-- SCRIPT DE INICIALIZACIÓN - SISTEMA DE TAREAS
-- Base de datos: EDARSA HUB (Opcional - Las tareas se guardan en MongoDB)
-- ============================================

-- Esta tabla es OPCIONAL si desea mantener un log en SQL Server
-- El sistema principal usa MongoDB para las tareas

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Sistema_Log_Solicitudes' AND xtype='U')
BEGIN
    CREATE TABLE Sistema_Log_Solicitudes (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        SolicitudID NVARCHAR(50) NOT NULL,
        CatalogoID NVARCHAR(50) NOT NULL,
        CatalogoNombre NVARCHAR(100),
        Datos NVARCHAR(MAX),  -- JSON con los datos de la solicitud
        Estatus NVARCHAR(20) NOT NULL,  -- Pendiente, Aprobada, Rechazada
        SolicitanteEmail NVARCHAR(100),
        AprobadorEmail NVARCHAR(100),
        FechaSolicitud DATETIME DEFAULT GETDATE(),
        FechaResolucion DATETIME,
        MotivoRechazo NVARCHAR(500)
    );
    
    CREATE INDEX IX_LogSolicitudes_Estatus ON Sistema_Log_Solicitudes(Estatus);
    CREATE INDEX IX_LogSolicitudes_Fecha ON Sistema_Log_Solicitudes(FechaSolicitud);
    
    PRINT 'Tabla Sistema_Log_Solicitudes creada exitosamente';
END
GO
"""
    return {
        "script": script,
        "nota": "Este script es OPCIONAL. El sistema de tareas funciona con MongoDB. Use este script solo si desea mantener un log adicional en SQL Server."
    }


# ============================================================================
# MÓDULO DE NÓMINAS - GESTIÓN DE CICLOS
# ============================================================================

# Etapas del flujo de nómina
ETAPAS_NOMINA = [
    {"id": "headcount", "nombre": "Headcount", "responsable": "Gerencia", "orden": 1},
    {"id": "incidencias", "nombre": "Incidencias", "responsable": "Gerencia", "orden": 2},
    {"id": "validacion_rh", "nombre": "Validación RH", "responsable": "RH", "orden": 3},
    {"id": "maquilador", "nombre": "Maquilador", "responsable": "Maquilador", "orden": 4},
    {"id": "autorizacion", "nombre": "Autorización", "responsable": "Gerencia", "orden": 5},
    {"id": "tesoreria", "nombre": "Tesorería", "responsable": "Tesorería", "orden": 6},
    {"id": "pagada", "nombre": "Pagada", "responsable": "Sistema", "orden": 7}
]

# Mapeo de roles permitidos por responsable
ROLES_NOMINA = {
    "Gerencia": ["Administrador", "Supervisor"],
    "RH": ["Administrador", "Supervisor"],
    "Maquilador": ["Administrador", "Supervisor", "Maquilador"],
    "Tesorería": ["Administrador", "Tesoreria"],
    "Sistema": ["Administrador"]
}


async def agregar_evento_nomina(ciclo_id: str, evento: Dict):
    """Agrega un evento al historial de trazabilidad de un ciclo de nómina"""
    evento["id"] = str(uuid.uuid4())
    evento["timestamp"] = datetime.now(timezone.utc).isoformat()
    await db.nomina_ciclos.update_one(
        {"id": ciclo_id},
        {"$push": {"historial": evento}}
    )


def calcular_deadline(fecha_base: datetime, horario: str, dia_objetivo: int = None) -> datetime:
    """Calcula el deadline basado en la configuración"""
    hora, minuto = map(int, horario.split(':'))
    deadline = fecha_base.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    if dia_objetivo is not None:
        dias_adelante = (dia_objetivo - fecha_base.weekday()) % 7
        if dias_adelante == 0 and fecha_base.hour >= hora:
            dias_adelante = 7
        deadline = deadline + timedelta(days=dias_adelante)
    return deadline


@api_router.get("/nomina/ciclos")
async def listar_ciclos_nomina(
    sucursal_id: str = Query(default=None),
    periodo: str = Query(default="actual"),
    current_user: Dict = Depends(get_current_user)
):
    """Lista los ciclos de nómina con filtros opcionales"""
    filtro = {}
    
    if sucursal_id:
        filtro["sucursal_id"] = sucursal_id
    
    # Filtrar por periodo
    ahora = datetime.now(timezone.utc)
    if periodo == "actual":
        # Últimos 30 días
        fecha_inicio = ahora - timedelta(days=30)
        filtro["fecha_creacion"] = {"$gte": fecha_inicio.isoformat()}
    elif periodo == "anterior":
        fecha_inicio = ahora - timedelta(days=60)
        fecha_fin = ahora - timedelta(days=30)
        filtro["fecha_creacion"] = {"$gte": fecha_inicio.isoformat(), "$lt": fecha_fin.isoformat()}
    
    cursor = db.nomina_ciclos.find(filtro).sort("fecha_creacion", -1)
    ciclos = await cursor.to_list(length=100)
    
    # Limpiar _id de MongoDB
    for ciclo in ciclos:
        ciclo.pop("_id", None)
    
    return {"ciclos": ciclos, "total": len(ciclos)}


@api_router.get("/nomina/ciclos/{ciclo_id}")
async def obtener_ciclo_nomina(ciclo_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene el detalle de un ciclo de nómina"""
    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")
    
    ciclo.pop("_id", None)
    return {"ciclo": ciclo}


@api_router.post("/nomina/ciclos")
async def crear_ciclo_nomina(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea un nuevo ciclo de nómina"""
    if current_user.get('role') not in ['Administrador', 'Supervisor']:
        raise HTTPException(status_code=403, detail="No autorizado para crear ciclos de nómina")
    
    sucursal_id = body.get('sucursal_id')
    fecha_corte = body.get('fecha_corte')
    tipo_nomina = body.get('tipo_nomina', 'quincenal')
    notas = body.get('notas', '')
    
    if not sucursal_id or not fecha_corte:
        raise HTTPException(status_code=400, detail="Sucursal y fecha de corte son requeridos")
    
    # Obtener nombre de sucursal
    sucursal_nombre = "Sucursal"
    try:
        query_suc = f"SELECT Nombre FROM RH_Cat_Sucursales WHERE SucursalID = {sucursal_id}"
        result_suc = await execute_edarsa_hub_query(query_suc)
        if result_suc.get("datos"):
            sucursal_nombre = result_suc["datos"][0].get("Nombre", "Sucursal")
    except Exception:
        pass
    
    # Verificar si ya existe un ciclo activo para esta sucursal en la misma fecha
    ciclo_existente = await db.nomina_ciclos.find_one({
        "sucursal_id": sucursal_id,
        "fecha_corte": fecha_corte,
        "etapa_actual": {"$ne": "pagada"}
    })
    if ciclo_existente:
        raise HTTPException(status_code=400, detail="Ya existe un ciclo activo para esta sucursal y fecha de corte")
    
    # Obtener configuración
    config = await db.nomina_configuracion.find_one({"tipo": "general"})
    config = config or {}
    
    ahora = datetime.now(timezone.utc)
    
    # Calcular deadline inicial (para headcount)
    horario_headcount = config.get('horario_headcount', '10:00')
    deadline_inicial = calcular_deadline(ahora, horario_headcount)
    
    ciclo_id = str(uuid.uuid4())
    ciclo = {
        "id": ciclo_id,
        "sucursal_id": sucursal_id,
        "sucursal_nombre": sucursal_nombre,
        "fecha_corte": fecha_corte,
        "tipo_nomina": tipo_nomina,
        "notas": notas,
        "etapa_actual": "headcount",
        "deadline_actual": deadline_inicial.isoformat(),
        "total_colaboradores": 0,
        "total_movimientos": 0,
        "fecha_creacion": ahora.isoformat(),
        "creado_por_id": current_user.get("id"),
        "creado_por_email": current_user.get("email"),
        "historial": [{
            "id": str(uuid.uuid4()),
            "tipo": "creacion",
            "accion": "CICLO_CREADO",
            "descripcion": f"Ciclo de nómina {tipo_nomina} creado para {sucursal_nombre}",
            "usuario_id": current_user.get("id"),
            "usuario_email": current_user.get("email"),
            "usuario_nombre": current_user.get("name"),
            "timestamp": ahora.isoformat()
        }]
    }
    
    await db.nomina_ciclos.insert_one(ciclo)
    
    return {"success": True, "ciclo_id": ciclo_id, "message": "Ciclo de nómina creado correctamente"}


@api_router.post("/nomina/ciclos/{ciclo_id}/avanzar")
async def avanzar_etapa_nomina(ciclo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Avanza el ciclo de nómina a la siguiente etapa (requiere firma de autorización)"""
    password = body.get('password')
    comentario = body.get('comentario', '')
    
    if not password:
        raise HTTPException(status_code=400, detail="Se requiere contraseña de autorización")
    
    # Verificar contraseña
    user = await db.users.find_one({"id": current_user.get("id")})
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    # Obtener ciclo
    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")
    
    etapa_actual = ciclo.get("etapa_actual")
    if etapa_actual == "pagada":
        raise HTTPException(status_code=400, detail="El ciclo ya está finalizado")
    
    # Verificar permisos para la etapa actual
    etapa_info = next((e for e in ETAPAS_NOMINA if e["id"] == etapa_actual), None)
    if not etapa_info:
        raise HTTPException(status_code=400, detail="Etapa no válida")
    
    roles_permitidos = ROLES_NOMINA.get(etapa_info["responsable"], [])
    if current_user.get("role") not in roles_permitidos:
        raise HTTPException(status_code=403, detail=f"No tiene permisos para actuar en la etapa {etapa_info['nombre']}")
    
    # Determinar siguiente etapa
    idx_actual = next((i for i, e in enumerate(ETAPAS_NOMINA) if e["id"] == etapa_actual), -1)
    if idx_actual == -1 or idx_actual >= len(ETAPAS_NOMINA) - 1:
        raise HTTPException(status_code=400, detail="No hay siguiente etapa")
    
    siguiente_etapa = ETAPAS_NOMINA[idx_actual + 1]
    
    # Obtener configuración para calcular nuevo deadline
    config = await db.nomina_configuracion.find_one({"tipo": "general"})
    config = config or {}
    
    ahora = datetime.now(timezone.utc)
    nuevo_deadline = None
    
    # Calcular deadline según la etapa
    if siguiente_etapa["id"] == "incidencias":
        nuevo_deadline = calcular_deadline(ahora, config.get('horario_headcount', '10:00'))
    elif siguiente_etapa["id"] == "validacion_rh":
        nuevo_deadline = calcular_deadline(ahora, config.get('horario_maquilador', '12:00'))
    elif siguiente_etapa["id"] == "maquilador":
        nuevo_deadline = calcular_deadline(ahora, config.get('horario_maquilador', '12:00'))
    elif siguiente_etapa["id"] == "autorizacion":
        nuevo_deadline = calcular_deadline(ahora, config.get('horario_maquilador', '12:00'))
    elif siguiente_etapa["id"] == "tesoreria":
        nuevo_deadline = calcular_deadline(ahora, config.get('horario_tesoreria', '14:00'))
    
    # Actualizar ciclo
    update_data = {
        "etapa_actual": siguiente_etapa["id"],
        "fecha_ultima_actualizacion": ahora.isoformat()
    }
    if nuevo_deadline:
        update_data["deadline_actual"] = nuevo_deadline.isoformat()
    
    await db.nomina_ciclos.update_one(
        {"id": ciclo_id},
        {"$set": update_data}
    )
    
    # Registrar evento
    await agregar_evento_nomina(ciclo_id, {
        "tipo": "avance",
        "accion": "ETAPA_AVANZADA",
        "descripcion": f"Avance de '{etapa_info['nombre']}' a '{siguiente_etapa['nombre']}'",
        "etapa_anterior": etapa_actual,
        "etapa_nueva": siguiente_etapa["id"],
        "usuario_id": current_user.get("id"),
        "usuario_email": current_user.get("email"),
        "usuario_nombre": current_user.get("name"),
        "comentario": comentario
    })
    
    return {
        "success": True, 
        "message": f"Nómina avanzada a etapa: {siguiente_etapa['nombre']}",
        "etapa_anterior": etapa_actual,
        "etapa_nueva": siguiente_etapa["id"]
    }


@api_router.post("/nomina/ciclos/{ciclo_id}/rechazar")
async def rechazar_ciclo_nomina(ciclo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Rechaza/devuelve el ciclo de nómina a la etapa de validación RH"""
    motivo = body.get('motivo', '')
    
    if not motivo:
        raise HTTPException(status_code=400, detail="Se requiere motivo del rechazo")
    
    # Obtener ciclo
    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")
    
    etapa_actual = ciclo.get("etapa_actual")
    
    # Solo se puede rechazar desde autorizacion
    if etapa_actual not in ["autorizacion", "maquilador"]:
        raise HTTPException(status_code=400, detail="Solo se puede devolver desde las etapas de Autorización o Maquilador")
    
    # Verificar permisos
    etapa_info = next((e for e in ETAPAS_NOMINA if e["id"] == etapa_actual), None)
    roles_permitidos = ROLES_NOMINA.get(etapa_info["responsable"], [])
    if current_user.get("role") not in roles_permitidos:
        raise HTTPException(status_code=403, detail="No tiene permisos para rechazar en esta etapa")
    
    ahora = datetime.now(timezone.utc)
    
    # Devolver a validación RH
    await db.nomina_ciclos.update_one(
        {"id": ciclo_id},
        {"$set": {
            "etapa_actual": "validacion_rh",
            "fecha_ultima_actualizacion": ahora.isoformat()
        }}
    )
    
    # Registrar evento
    await agregar_evento_nomina(ciclo_id, {
        "tipo": "rechazo",
        "accion": "NOMINA_DEVUELTA",
        "descripcion": f"Nómina devuelta para corrección desde '{etapa_info['nombre']}' a 'Validación RH'",
        "etapa_anterior": etapa_actual,
        "etapa_nueva": "validacion_rh",
        "motivo": motivo,
        "usuario_id": current_user.get("id"),
        "usuario_email": current_user.get("email"),
        "usuario_nombre": current_user.get("name")
    })
    
    return {"success": True, "message": "Nómina devuelta para corrección"}


@api_router.get("/nomina/ciclos/{ciclo_id}/movimientos")
async def listar_movimientos_nomina(ciclo_id: str, current_user: Dict = Depends(get_current_user)):
    """Lista los movimientos de un ciclo de nómina"""
    # Verificar que el ciclo existe
    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")
    
    cursor = db.nomina_movimientos.find({"ciclo_id": ciclo_id}).sort("fecha_registro", -1)
    movimientos = await cursor.to_list(length=500)
    
    for mov in movimientos:
        mov.pop("_id", None)
    
    return {"movimientos": movimientos, "total": len(movimientos)}


@api_router.post("/nomina/ciclos/{ciclo_id}/movimientos")
async def agregar_movimiento_nomina(ciclo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Agrega un movimiento de nómina (incidencia) a un ciclo"""
    # Verificar que el ciclo existe y está en etapa correcta
    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")
    
    etapa_actual = ciclo.get("etapa_actual")
    if etapa_actual not in ["headcount", "incidencias", "validacion_rh"]:
        raise HTTPException(status_code=400, detail="No se pueden agregar movimientos en esta etapa")
    
    colaborador_id = body.get('colaborador_id')
    tipo_incidencia = body.get('tipo_incidencia')
    monto = body.get('monto', 0)
    unidades = body.get('unidades', 0)
    notas = body.get('notas', '')
    
    if not colaborador_id or not tipo_incidencia:
        raise HTTPException(status_code=400, detail="Colaborador y tipo de incidencia son requeridos")
    
    # Obtener nombre del colaborador
    colaborador_nombre = "Colaborador"
    try:
        query_col = f"SELECT NombreCompleto FROM RH_Colaboradores_Expediente WHERE ColaboradorID = {colaborador_id}"
        result_col = await execute_edarsa_hub_query(query_col)
        if result_col.get("datos"):
            colaborador_nombre = result_col["datos"][0].get("NombreCompleto", "Colaborador")
    except Exception:
        pass
    
    ahora = datetime.now(timezone.utc)
    movimiento_id = str(uuid.uuid4())
    
    movimiento = {
        "id": movimiento_id,
        "ciclo_id": ciclo_id,
        "colaborador_id": str(colaborador_id),
        "colaborador_nombre": colaborador_nombre,
        "tipo_incidencia": tipo_incidencia,
        "categoria": "Ingreso" if tipo_incidencia in ["BON", "HEX", "COM", "Bono", "Horas Extra", "Comisión"] else "Descuento",
        "monto": float(monto),
        "unidades": float(unidades),
        "notas": notas,
        "fecha_registro": ahora.isoformat(),
        "registrado_por_id": current_user.get("id"),
        "registrado_por": current_user.get("email")
    }
    
    await db.nomina_movimientos.insert_one(movimiento)
    
    # Actualizar contador en el ciclo
    await db.nomina_ciclos.update_one(
        {"id": ciclo_id},
        {"$inc": {"total_movimientos": 1}}
    )
    
    return {"success": True, "movimiento_id": movimiento_id, "message": "Movimiento agregado"}


@api_router.delete("/nomina/movimientos/{movimiento_id}")
async def eliminar_movimiento_nomina(movimiento_id: str, current_user: Dict = Depends(get_current_user)):
    """Elimina un movimiento de nómina"""
    movimiento = await db.nomina_movimientos.find_one({"id": movimiento_id})
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    
    ciclo_id = movimiento.get("ciclo_id")
    
    # Verificar etapa del ciclo
    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
    if ciclo and ciclo.get("etapa_actual") not in ["headcount", "incidencias", "validacion_rh"]:
        raise HTTPException(status_code=400, detail="No se pueden eliminar movimientos en esta etapa")
    
    await db.nomina_movimientos.delete_one({"id": movimiento_id})
    
    # Actualizar contador
    await db.nomina_ciclos.update_one(
        {"id": ciclo_id},
        {"$inc": {"total_movimientos": -1}}
    )
    
    return {"success": True, "message": "Movimiento eliminado"}


@api_router.get("/nomina/configuracion")
async def obtener_configuracion_nomina(current_user: Dict = Depends(get_current_user)):
    """Obtiene la configuración de nóminas"""
    config = await db.nomina_configuracion.find_one({"tipo": "general"})
    
    if not config:
        # Configuración por defecto
        config = {
            "tipo": "general",
            "dia_corte": 0,  # Domingo
            "dia_pago": 1,  # Lunes
            "dias_inhabiles": [],
            "horario_headcount": "10:00",
            "horario_autorizacion": "11:00",
            "horario_maquilador": "12:00",
            "horario_tesoreria": "14:00"
        }
    
    config.pop("_id", None)
    return {"configuracion": config}


@api_router.post("/nomina/configuracion")
async def guardar_configuracion_nomina(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Guarda la configuración de nóminas (Solo Admin)"""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo Administradores pueden configurar nóminas")
    
    config = {
        "tipo": "general",
        "dia_corte": body.get('dia_corte', 0),
        "dia_pago": body.get('dia_pago', 1),
        "dias_inhabiles": body.get('dias_inhabiles', []),
        "horario_headcount": body.get('horario_headcount', '10:00'),
        "horario_autorizacion": body.get('horario_autorizacion', '11:00'),
        "horario_maquilador": body.get('horario_maquilador', '12:00'),
        "horario_tesoreria": body.get('horario_tesoreria', '14:00'),
        "actualizado_por": current_user.get("email"),
        "fecha_actualizacion": datetime.now(timezone.utc).isoformat()
    }
    
    await db.nomina_configuracion.update_one(
        {"tipo": "general"},
        {"$set": config},
        upsert=True
    )
    
    return {"success": True, "message": "Configuración guardada correctamente"}


@api_router.get("/nomina/kpis")
async def listar_kpis_nomina(current_user: Dict = Depends(get_current_user)):
    """Lista los KPIs configurados por puesto"""
    cursor = db.nomina_kpis_puestos.find({})
    kpis = await cursor.to_list(length=100)
    
    for kpi in kpis:
        kpi.pop("_id", None)
    
    return {"kpis": kpis, "total": len(kpis)}


@api_router.post("/nomina/kpis")
async def crear_kpi_nomina(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea o actualiza KPIs para un puesto"""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo Administradores pueden configurar KPIs")
    
    puesto_id = body.get('puesto_id')
    indicadores = body.get('indicadores', [])
    
    if not puesto_id:
        raise HTTPException(status_code=400, detail="Puesto es requerido")
    
    # Obtener nombre del puesto
    puesto_nombre = "Puesto"
    try:
        query = f"SELECT Descripcion FROM RH_Cat_Puestos WHERE PuestoID = {puesto_id}"
        result = await execute_edarsa_hub_query(query)
        if result.get("datos"):
            puesto_nombre = result["datos"][0].get("Descripcion", "Puesto")
    except Exception:
        pass
    
    kpi_id = str(uuid.uuid4())
    kpi = {
        "id": kpi_id,
        "puesto_id": str(puesto_id),
        "puesto_nombre": puesto_nombre,
        "indicadores": indicadores,
        "actualizado_por": current_user.get("email"),
        "fecha_actualizacion": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert por puesto
    await db.nomina_kpis_puestos.update_one(
        {"puesto_id": str(puesto_id)},
        {"$set": kpi},
        upsert=True
    )
    
    return {"success": True, "message": "KPIs guardados correctamente"}


@api_router.get("/nomina/script-tablas")
async def obtener_script_tablas_nomina(current_user: Dict = Depends(get_current_user)):
    """Retorna el script SQL para crear tablas de nómina en EDARSA HUB"""
    script = """
-- ============================================
-- SCRIPT DE TABLAS - MÓDULO DE NÓMINAS
-- Base de datos: EDARSA HUB (SQL Server)
-- NOTA: Las tablas principales se manejan en MongoDB.
-- Este script es para tablas auxiliares opcionales.
-- ============================================

-- ========== TABLA DE CONCEPTOS DE NÓMINA ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Nomina_Cat_Conceptos' AND xtype='U')
BEGIN
    CREATE TABLE Nomina_Cat_Conceptos (
        ConceptoID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL UNIQUE,
        Descripcion NVARCHAR(200) NOT NULL,
        Tipo NVARCHAR(50) NOT NULL, -- 'Percepcion', 'Deduccion', 'Obligacion'
        Categoria NVARCHAR(100), -- 'Legal', 'Empresa', 'Sindical'
        Afectacion INT DEFAULT 1, -- 1 = Suma, -1 = Resta
        Formula NVARCHAR(500), -- Fórmula de cálculo si aplica
        NomiPAQ_ID NVARCHAR(50),
        MPRO_ID NVARCHAR(50),
        Activo BIT DEFAULT 1,
        Fecha_Creacion DATETIME DEFAULT GETDATE()
    );
    
    -- Conceptos base
    INSERT INTO Nomina_Cat_Conceptos (Codigo, Descripcion, Tipo, Categoria, Afectacion) VALUES
    ('SUELDO', 'Sueldo Base', 'Percepcion', 'Empresa', 1),
    ('BONO', 'Bono', 'Percepcion', 'Empresa', 1),
    ('COMISION', 'Comisión', 'Percepcion', 'Empresa', 1),
    ('HEXTRA', 'Horas Extra', 'Percepcion', 'Legal', 1),
    ('AGUINALDO', 'Aguinaldo', 'Percepcion', 'Legal', 1),
    ('VACACIONES', 'Prima Vacacional', 'Percepcion', 'Legal', 1),
    ('ISR', 'ISR', 'Deduccion', 'Legal', -1),
    ('IMSS', 'IMSS Trabajador', 'Deduccion', 'Legal', -1),
    ('INFONAVIT', 'INFONAVIT', 'Deduccion', 'Legal', -1),
    ('FONACOT', 'FONACOT', 'Deduccion', 'Legal', -1),
    ('PENSION', 'Pensión Alimenticia', 'Deduccion', 'Legal', -1),
    ('FALTA', 'Descuento por Falta', 'Deduccion', 'Empresa', -1),
    ('RETARDO', 'Descuento por Retardo', 'Deduccion', 'Empresa', -1),
    ('PRESTAMO', 'Préstamo Empresa', 'Deduccion', 'Empresa', -1),
    ('UNIFORME', 'Descuento Uniforme', 'Deduccion', 'Empresa', -1);
    
    PRINT 'Tabla Nomina_Cat_Conceptos creada';
END
GO

-- ========== TABLA DE PERIODOS DE NÓMINA ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Nomina_Periodos' AND xtype='U')
BEGIN
    CREATE TABLE Nomina_Periodos (
        PeriodoID INT IDENTITY(1,1) PRIMARY KEY,
        Año INT NOT NULL,
        Numero INT NOT NULL, -- Número de periodo en el año
        Tipo NVARCHAR(20) NOT NULL, -- 'Semanal', 'Quincenal', 'Mensual'
        Fecha_Inicio DATE NOT NULL,
        Fecha_Fin DATE NOT NULL,
        Fecha_Pago DATE,
        Estatus NVARCHAR(20) DEFAULT 'Abierto', -- 'Abierto', 'Cerrado', 'Pagado'
        CONSTRAINT UQ_Periodo UNIQUE (Año, Numero, Tipo)
    );
    
    CREATE INDEX IX_Periodos_Año ON Nomina_Periodos(Año);
    PRINT 'Tabla Nomina_Periodos creada';
END
GO

-- ========== TABLA DE RESUMEN DE NÓMINA ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Nomina_Resumen' AND xtype='U')
BEGIN
    CREATE TABLE Nomina_Resumen (
        ResumenID INT IDENTITY(1,1) PRIMARY KEY,
        CicloID NVARCHAR(50) NOT NULL, -- ID del ciclo en MongoDB
        SucursalID INT NOT NULL,
        PeriodoID INT,
        Total_Percepciones DECIMAL(18,2) DEFAULT 0,
        Total_Deducciones DECIMAL(18,2) DEFAULT 0,
        Total_Neto DECIMAL(18,2) DEFAULT 0,
        Total_Colaboradores INT DEFAULT 0,
        Fecha_Calculo DATETIME DEFAULT GETDATE(),
        Calculado_Por NVARCHAR(100)
    );
    
    CREATE INDEX IX_Resumen_Ciclo ON Nomina_Resumen(CicloID);
    PRINT 'Tabla Nomina_Resumen creada';
END
GO

PRINT 'Script de nóminas ejecutado correctamente';
"""
    return {
        "script": script,
        "nota": "Este script es OPCIONAL. El sistema de nóminas funciona principalmente con MongoDB. Use estas tablas para integración con NomiPAQ o reportes SQL."
    }


# ==============================================================================
# FASE 2 - ENDPOINTS DE ESTRUCTURA ORGANIZACIONAL (SOLO LECTURA)
# ==============================================================================
# Estos endpoints son NUEVOS y no modifican lógica existente.
# Solo visualización - no participan en validación de permisos.
# Bitácora desacoplada - si falla, no rompe flujo principal.
# ==============================================================================

from modules.sistema.estructura_service import get_estructura_service


# ==============================================================================
# FASE 3/5/6: VALIDACIÓN DE PERMISO GRANULAR - PILOTO CONTROLADO
# ==============================================================================
# Alcance: Endpoints protegidos por permisos piloto
# FASE 3: Permisos directos + Fallback SuperAdmin
# FASE 5: + Herencia por rol único (sec_rol)
# FASE 6: + Múltiples roles (sec_roles array)
# NO expande a otros endpoints sin aprobación explícita
# ==============================================================================

# Whitelist FASE 11 - Roles permitidos (NO EXPANDIR sin aprobación)
# FASE 6: VISOR_ESTRUCTURA, VISOR_SISTEMA
# FASE 8: + VISOR_ADMIN
# FASE 10: + ADMIN_USUARIOS
# FASE 11: + GESTOR_SISTEMA
ROLES_FASE_11_WHITELIST = ["VISOR_ESTRUCTURA", "VISOR_SISTEMA", "VISOR_ADMIN", "ADMIN_USUARIOS", "GESTOR_SISTEMA"]


async def verificar_permiso_v6(user: dict, permiso: str) -> bool:
    """
    FASE 6: Verifica permiso con múltiples roles.
    Coexiste con legacy - no lo reemplaza.
    
    Orden de resolución (4 capas):
    1. Permisos directos (sec_permisos) → FASE 4
    2. Múltiples roles (sec_roles array) → FASE 6
    3. Rol único (sec_rol string) → FASE 5 (compatibilidad)
    4. Fallback legacy (SuperAdmin) → FASE 3
    """
    # 1. Permisos directos (FASE 4)
    permisos_directos = user.get('sec_permisos', [])
    if permiso in permisos_directos:
        return True
    
    # 2. Múltiples roles (FASE 6)
    sec_roles = user.get('sec_roles', [])
    for rol_codigo in sec_roles:
        if rol_codigo in ROLES_FASE_11_WHITELIST:
            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
            if rol_doc and permiso in rol_doc.get('permisos', []):
                return True
    
    # 3. Rol único - compatibilidad FASE 5
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_FASE_11_WHITELIST:
        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol_doc and permiso in rol_doc.get('permisos', []):
            return True
    
    # 4. Fallback legacy (FASE 3)
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False


async def verificar_permiso_estructura_v6(user: dict) -> bool:
    """Wrapper específico para SISTEMA_ESTRUCTURA_VER."""
    return await verificar_permiso_v6(user, 'SISTEMA_ESTRUCTURA_VER')


@api_router.get("/sistema/estructura-organizacional")
async def get_estructura_organizacional(current_user: Dict = Depends(get_current_user)):
    """
    FASE 6: Obtiene estructura organizacional (solo lectura).
    Protegido por permiso granular SISTEMA_ESTRUCTURA_VER.
    Resolución: permisos directos → múltiples roles → rol único → fallback SuperAdmin.
    """
    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
    
    # FASE 6: Validación de permiso con múltiples roles
    tiene_permiso = await verificar_permiso_estructura_v6(current_user)
    
    if not tiene_permiso:
        # Registrar intento denegado (desacoplado - no bloquea)
        await service.escribir_bitacora(
            usuario_id=current_user.get('id', ''),
            usuario_email=current_user.get('email', ''),
            accion="ACCESO_DENEGADO",
            recurso="/api/sistema/estructura-organizacional",
            resultado="DENEGADO",
            detalles={"permiso_requerido": "SISTEMA_ESTRUCTURA_VER", "fase": "FASE_3"}
        )
        raise HTTPException(
            status_code=403, 
            detail="Permiso requerido: SISTEMA_ESTRUCTURA_VER"
        )
    
    # Registrar acceso permitido
    await service.escribir_bitacora(
        usuario_id=current_user.get('id', ''),
        usuario_email=current_user.get('email', ''),
        accion="VER_ESTRUCTURA",
        recurso="/api/sistema/estructura-organizacional",
        resultado="OK",
        detalles={"permiso_verificado": "SISTEMA_ESTRUCTURA_VER", "fase": "FASE_3"}
    )
    
    return await service.get_estructura_organizacional()


@api_router.get("/sistema/mapeo-servidores")
async def get_mapeo_servidores(current_user: Dict = Depends(get_current_user)):
    """
    FASE 2: Obtiene mapeo servidor-sucursal (solo lectura).
    Informativo - servidor es dimensión técnica.
    """
    if current_user.get('role') not in ['SuperAdministrador', 'Administrador']:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
    
    await service.escribir_bitacora(
        usuario_id=current_user.get('id', ''),
        usuario_email=current_user.get('email', ''),
        accion="VER_MAPEO_SERVIDORES",
        recurso="/api/sistema/mapeo-servidores"
    )
    
    return await service.get_mapeo_servidores()


@api_router.get("/sistema/permisos-catalogo-v2")
async def get_permisos_catalogo_v2(current_user: Dict = Depends(get_current_user)):
    """
    FASE 2: Obtiene catálogo de permisos v2 (solo lectura informativa).
    NO reemplaza catálogo legacy - solo visualización del nuevo modelo.
    """
    if current_user.get('role') not in ['SuperAdministrador', 'Administrador']:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
    
    await service.escribir_bitacora(
        usuario_id=current_user.get('id', ''),
        usuario_email=current_user.get('email', ''),
        accion="VER_PERMISOS_V2",
        recurso="/api/sistema/permisos-catalogo-v2"
    )
    
    return await service.get_permisos_catalogo_v2()

# ==============================================================================
# FIN FASE 2 - ENDPOINTS DE ESTRUCTURA ORGANIZACIONAL
# ==============================================================================


# ==============================================================================
# FASE 4: ADMINISTRACIÓN DE PERMISOS (PILOTO CONTROLADO)
# ==============================================================================
# Alcance: SOLO endpoint de asignación/retiro de permisos
# Whitelist: SOLO SISTEMA_ESTRUCTURA_VER
# Quién administra: SOLO SuperAdministrador
# Auditoría: sec_bitacora_admin
# NO TOCA: get_current_user, Layout.js, auth global, UI, módulos productivos
# ==============================================================================

# Whitelist estricta FASE 10 - NO EXPANDIR sin aprobación
# FASE 4: SISTEMA_ESTRUCTURA_VER
# FASE 8: + SISTEMA_USUARIOS_VER, SISTEMA_ROLES_VER
# FASE 10: + SISTEMA_USUARIOS_EDITAR, SISTEMA_USUARIOS_ELIMINAR, SISTEMA_ROLES_EDITAR, SISTEMA_ROLES_ELIMINAR
PERMISOS_FASE_10_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_USUARIOS_EDITAR",
    "SISTEMA_USUARIOS_ELIMINAR",
    "SISTEMA_ROLES_VER",
    "SISTEMA_ROLES_EDITAR",
    "SISTEMA_ROLES_ELIMINAR"
]


class PermisoAsignacionRequest(BaseModel):
    """Request para asignar/retirar permiso."""
    usuario_email: str
    permiso: str
    accion: str  # "ASIGNAR" o "RETIRAR"


async def registrar_auditoria_admin_fase4(
    tipo_operacion: str,
    administrador: dict,
    usuario_afectado: dict,
    permiso: str,
    accion: str,
    estado_anterior: list,
    estado_nuevo: list,
    resultado: str,
    mensaje: str = None
):
    """
    FASE 4: Registra auditoría de administración de permisos.
    Desacoplado - no bloquea el flujo si falla.
    """
    try:
        await db.sec_bitacora_admin.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "tipo": tipo_operacion,
            "administrador": {
                "id": administrador.get('id', ''),
                "email": administrador.get('email', ''),
                "role": administrador.get('role', '')
            },
            "usuario_afectado": {
                "id": usuario_afectado.get('id', '') if usuario_afectado else '',
                "email": usuario_afectado.get('email', '') if usuario_afectado else ''
            },
            "permiso": permiso,
            "accion": accion,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "resultado": resultado,
            "mensaje": mensaje,
            "origen": "API",
            "fase": "FASE_4"
        })
    except Exception as e:
        logging.warning(f"Error en auditoría admin FASE 4 (no crítico): {e}")


@api_router.post("/admin/permisos/asignar")
async def admin_asignar_permiso(
    request: PermisoAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 4: Asigna o retira un permiso a un usuario.
    
    Restricciones:
    - Solo SuperAdministrador puede ejecutar
    - Solo permisos en whitelist FASE 4
    - Auditoría completa en sec_bitacora_admin
    
    NO TOCA: get_current_user, Layout.js, auth global, roles legacy
    """
    # 1. VALIDAR: Solo SuperAdministrador puede administrar
    if current_user.get('role') != 'SuperAdministrador':
        await registrar_auditoria_admin_fase4(
            tipo_operacion="INTENTO_NO_AUTORIZADO",
            administrador=current_user,
            usuario_afectado=None,
            permiso=request.permiso,
            accion=request.accion,
            estado_anterior=[],
            estado_nuevo=[],
            resultado="RECHAZADO",
            mensaje="Usuario sin privilegios de SuperAdministrador"
        )
        raise HTTPException(
            status_code=403,
            detail="Solo SuperAdministrador puede administrar permisos"
        )
    
    # 2. VALIDAR: Acción válida
    accion_upper = request.accion.upper()
    if accion_upper not in ["ASIGNAR", "RETIRAR"]:
        raise HTTPException(
            status_code=400,
            detail="Acción inválida. Use 'ASIGNAR' o 'RETIRAR'"
        )
    
    # 3. VALIDAR: Permiso en whitelist FASE 4
    if request.permiso not in PERMISOS_FASE_10_WHITELIST:
        await registrar_auditoria_admin_fase4(
            tipo_operacion="PERMISO_FUERA_WHITELIST",
            administrador=current_user,
            usuario_afectado=None,
            permiso=request.permiso,
            accion=accion_upper,
            estado_anterior=[],
            estado_nuevo=[],
            resultado="RECHAZADO",
            mensaje=f"Permiso {request.permiso} no está en whitelist FASE 4"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Permiso '{request.permiso}' no disponible en FASE 10. Whitelist: {PERMISOS_FASE_10_WHITELIST}"
        )
    
    # 4. VALIDAR: Permiso existe en catálogo
    permiso_catalogo = await db.sec_permisos_catalogo.find_one({"codigo": request.permiso})
    if not permiso_catalogo:
        raise HTTPException(
            status_code=400,
            detail=f"Permiso '{request.permiso}' no existe en catálogo sec_permisos_catalogo"
        )
    
    # 5. VALIDAR: Usuario destino existe
    usuario_destino = await db.users.find_one({"email": request.usuario_email})
    if not usuario_destino:
        await registrar_auditoria_admin_fase4(
            tipo_operacion="USUARIO_NO_ENCONTRADO",
            administrador=current_user,
            usuario_afectado={"email": request.usuario_email},
            permiso=request.permiso,
            accion=accion_upper,
            estado_anterior=[],
            estado_nuevo=[],
            resultado="RECHAZADO",
            mensaje=f"Usuario {request.usuario_email} no encontrado"
        )
        raise HTTPException(
            status_code=404,
            detail=f"Usuario '{request.usuario_email}' no encontrado"
        )
    
    # 6. Obtener permisos actuales del usuario
    permisos_actuales = usuario_destino.get('sec_permisos', [])
    estado_anterior = permisos_actuales.copy() if permisos_actuales else []
    
    # 7. Aplicar acción
    cambio_realizado = False
    mensaje_resultado = ""
    
    if accion_upper == "ASIGNAR":
        if request.permiso in permisos_actuales:
            # Permiso ya existe - no es error, pero informar
            mensaje_resultado = f"Permiso {request.permiso} ya estaba asignado a {request.usuario_email}"
        else:
            permisos_actuales.append(request.permiso)
            cambio_realizado = True
            mensaje_resultado = f"Permiso {request.permiso} asignado exitosamente a {request.usuario_email}"
    
    elif accion_upper == "RETIRAR":
        if request.permiso not in permisos_actuales:
            # Permiso no existe - no es error, pero informar
            mensaje_resultado = f"Permiso {request.permiso} no estaba asignado a {request.usuario_email}"
        else:
            permisos_actuales.remove(request.permiso)
            cambio_realizado = True
            mensaje_resultado = f"Permiso {request.permiso} retirado exitosamente de {request.usuario_email}"
    
    estado_nuevo = permisos_actuales.copy()
    
    # 8. Actualizar usuario si hubo cambio
    if cambio_realizado:
        await db.users.update_one(
            {"email": request.usuario_email},
            {"$set": {"sec_permisos": permisos_actuales}}
        )
    
    # 9. Registrar auditoría
    await registrar_auditoria_admin_fase4(
        tipo_operacion=f"{accion_upper}_PERMISO",
        administrador=current_user,
        usuario_afectado=usuario_destino,
        permiso=request.permiso,
        accion=accion_upper,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        resultado="OK" if cambio_realizado else "SIN_CAMBIO",
        mensaje=mensaje_resultado
    )
    
    # 10. Respuesta
    return {
        "success": True,
        "usuario": request.usuario_email,
        "permiso": request.permiso,
        "accion": accion_upper,
        "cambio_realizado": cambio_realizado,
        "mensaje": mensaje_resultado,
        "permisos_actuales": estado_nuevo,
        "fase": "FASE_4"
    }


# ==============================================================================
# FIN FASE 4 - ADMINISTRACIÓN DE PERMISOS
# ==============================================================================


# ==============================================================================
# FASE 5/6: HERENCIA DE PERMISOS POR ROL (PILOTO CONTROLADO)
# ==============================================================================
# FASE 5: Rol único (sec_rol)
# FASE 6: Múltiples roles (sec_roles array)
# Whitelist: ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]
# Quién administra: SOLO SuperAdministrador
# Auditoría: sec_bitacora_admin
# NO TOCA: get_current_user, Layout.js, auth global, UI, roles legacy
# ==============================================================================

class RolAsignacionRequest(BaseModel):
    """Request para asignar/retirar rol sec_*."""
    usuario_email: str
    rol: str
    accion: str  # "ASIGNAR" o "RETIRAR"


async def registrar_auditoria_rol_fase6(
    tipo_operacion: str,
    administrador: dict,
    usuario_afectado: dict,
    rol: str,
    permisos_rol: list,
    accion: str,
    roles_anteriores: list,
    roles_nuevos: list,
    resultado: str,
    mensaje: str = None
):
    """
    FASE 6: Registra auditoría de administración de múltiples roles.
    Reutiliza sec_bitacora_admin.
    Desacoplado - no bloquea el flujo si falla.
    """
    try:
        await db.sec_bitacora_admin.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "tipo": tipo_operacion,
            "administrador": {
                "id": administrador.get('id', ''),
                "email": administrador.get('email', ''),
                "role": administrador.get('role', '')
            },
            "usuario_afectado": {
                "id": usuario_afectado.get('id', '') if usuario_afectado else '',
                "email": usuario_afectado.get('email', '') if usuario_afectado else ''
            },
            "rol": rol,
            "permisos_heredados": permisos_rol,
            "accion": accion,
            "roles_anteriores": roles_anteriores,
            "roles_nuevos": roles_nuevos,
            "resultado": resultado,
            "mensaje": mensaje,
            "origen": "API",
            "fase": "FASE_6"
        })
    except Exception as e:
        logging.warning(f"Error en auditoría rol FASE 6 (no crítico): {e}")


@api_router.post("/admin/roles/asignar")
async def admin_asignar_rol(
    request: RolAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 6: Asigna o retira un rol sec_* a un usuario.
    Soporta múltiples roles en array sec_roles.
    Mantiene compatibilidad con sec_rol de FASE 5.
    
    Restricciones:
    - Solo SuperAdministrador puede ejecutar
    - Solo roles en whitelist FASE 6 (VISOR_ESTRUCTURA, VISOR_SISTEMA)
    - Auditoría completa en sec_bitacora_admin
    
    NO TOCA: get_current_user, Layout.js, auth global, roles legacy
    """
    # 1. VALIDAR: Solo SuperAdministrador puede administrar
    if current_user.get('role') != 'SuperAdministrador':
        await registrar_auditoria_rol_fase6(
            tipo_operacion="INTENTO_NO_AUTORIZADO_ROL",
            administrador=current_user,
            usuario_afectado=None,
            rol=request.rol,
            permisos_rol=[],
            accion=request.accion,
            roles_anteriores=[],
            roles_nuevos=[],
            resultado="RECHAZADO",
            mensaje="Usuario sin privilegios de SuperAdministrador"
        )
        raise HTTPException(
            status_code=403,
            detail="Solo SuperAdministrador puede administrar roles"
        )
    
    # 2. VALIDAR: Acción válida
    accion_upper = request.accion.upper()
    if accion_upper not in ["ASIGNAR", "RETIRAR"]:
        raise HTTPException(
            status_code=400,
            detail="Acción inválida. Use 'ASIGNAR' o 'RETIRAR'"
        )
    
    # 3. VALIDAR: Rol en whitelist FASE 11
    if request.rol not in ROLES_FASE_11_WHITELIST:
        await registrar_auditoria_rol_fase6(
            tipo_operacion="ROL_FUERA_WHITELIST",
            administrador=current_user,
            usuario_afectado=None,
            rol=request.rol,
            permisos_rol=[],
            accion=accion_upper,
            roles_anteriores=[],
            roles_nuevos=[],
            resultado="RECHAZADO",
            mensaje=f"Rol {request.rol} no está en whitelist FASE 11"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Rol '{request.rol}' no disponible en FASE 11. Whitelist: {ROLES_FASE_11_WHITELIST}"
        )
    
    # 4. VALIDAR: Rol existe en sec_roles
    rol_doc = await db.sec_roles.find_one({"codigo": request.rol, "activo": True})
    if not rol_doc:
        raise HTTPException(
            status_code=400,
            detail=f"Rol '{request.rol}' no existe en colección sec_roles"
        )
    
    permisos_del_rol = rol_doc.get('permisos', [])
    
    # 5. VALIDAR: Usuario destino existe
    usuario_destino = await db.users.find_one({"email": request.usuario_email})
    if not usuario_destino:
        await registrar_auditoria_rol_fase6(
            tipo_operacion="USUARIO_NO_ENCONTRADO_ROL",
            administrador=current_user,
            usuario_afectado={"email": request.usuario_email},
            rol=request.rol,
            permisos_rol=permisos_del_rol,
            accion=accion_upper,
            roles_anteriores=[],
            roles_nuevos=[],
            resultado="RECHAZADO",
            mensaje=f"Usuario {request.usuario_email} no encontrado"
        )
        raise HTTPException(
            status_code=404,
            detail=f"Usuario '{request.usuario_email}' no encontrado"
        )
    
    # 6. Obtener roles actuales del usuario (FASE 6: array)
    roles_actuales = usuario_destino.get('sec_roles', [])
    if not isinstance(roles_actuales, list):
        roles_actuales = []
    roles_anteriores = roles_actuales.copy()
    
    # 7. Aplicar acción
    cambio_realizado = False
    mensaje_resultado = ""
    
    if accion_upper == "ASIGNAR":
        if request.rol in roles_actuales:
            mensaje_resultado = f"Rol {request.rol} ya estaba asignado a {request.usuario_email}"
        else:
            roles_actuales.append(request.rol)
            cambio_realizado = True
            mensaje_resultado = f"Rol {request.rol} asignado exitosamente a {request.usuario_email}. Permisos heredados: {permisos_del_rol}"
    
    elif accion_upper == "RETIRAR":
        if request.rol not in roles_actuales:
            mensaje_resultado = f"Rol {request.rol} no estaba asignado a {request.usuario_email}"
        else:
            roles_actuales.remove(request.rol)
            cambio_realizado = True
            mensaje_resultado = f"Rol {request.rol} retirado exitosamente de {request.usuario_email}"
    
    roles_nuevos = roles_actuales.copy()
    
    # 8. Actualizar usuario si hubo cambio
    if cambio_realizado:
        await db.users.update_one(
            {"email": request.usuario_email},
            {"$set": {"sec_roles": roles_actuales}}
        )
    
    # 9. Calcular permisos efectivos de todos los roles
    permisos_efectivos = []
    for rol_codigo in roles_nuevos:
        rol = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
        if rol:
            for p in rol.get('permisos', []):
                if p not in permisos_efectivos:
                    permisos_efectivos.append(p)
    
    # 10. Registrar auditoría
    await registrar_auditoria_rol_fase6(
        tipo_operacion=f"{accion_upper}_ROL_MULTIPLE",
        administrador=current_user,
        usuario_afectado=usuario_destino,
        rol=request.rol,
        permisos_rol=permisos_del_rol,
        accion=accion_upper,
        roles_anteriores=roles_anteriores,
        roles_nuevos=roles_nuevos,
        resultado="OK" if cambio_realizado else "SIN_CAMBIO",
        mensaje=mensaje_resultado
    )
    
    # 11. Respuesta
    return {
        "success": True,
        "usuario": request.usuario_email,
        "rol": request.rol,
        "permisos_heredados_rol": permisos_del_rol,
        "accion": accion_upper,
        "cambio_realizado": cambio_realizado,
        "mensaje": mensaje_resultado,
        "sec_roles_actuales": roles_nuevos,
        "permisos_efectivos_todos_roles": permisos_efectivos,
        "fase": "FASE_6"
    }


# ==============================================================================
# FIN FASE 5/6 - HERENCIA DE PERMISOS POR ROL
# ==============================================================================


# ==============================================================================
# FASE 12: BITÁCORA RBAC DE SOLO LECTURA
# ==============================================================================
# Panel de auditoría visual para consultar sec_bitacora_admin
# Acceso restringido a SuperAdministrador
# Solo lectura - sin edición, borrado ni modificación
# ==============================================================================

@api_router.get("/admin/bitacora")
async def get_bitacora_rbac(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    email: Optional[str] = None,
    resultado: Optional[str] = None,
    tipo: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 12: Endpoint de solo lectura para consultar bitácora RBAC.
    
    Acceso: Solo SuperAdministrador
    
    Filtros:
        - fecha_inicio: YYYY-MM-DD
        - fecha_fin: YYYY-MM-DD
        - email: Email del usuario afectado
        - resultado: OK | RECHAZADO | SIN_CAMBIO
        - tipo: ASIGNAR_PERMISO | ASIGNAR_ROL_MULTIPLE
    
    Paginación:
        - skip: Registros a saltar (default 0)
        - limit: Registros por página (default 50, max 100)
    """
    # Verificar acceso: Solo SuperAdministrador
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(
            status_code=403,
            detail="Solo SuperAdministrador puede acceder a la bitácora RBAC"
        )
    
    # Limitar máximo de registros por consulta
    if limit > 100:
        limit = 100
    
    # Construir filtro
    filtro = {}
    
    if fecha_inicio:
        try:
            fecha_ini = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            filtro["timestamp"] = {"$gte": fecha_ini.isoformat()}
        except ValueError:
            pass  # Ignorar fecha inválida
    
    if fecha_fin:
        try:
            fecha_f = datetime.strptime(fecha_fin, "%Y-%m-%d")
            # Agregar un día para incluir todo el día final
            fecha_f = fecha_f.replace(hour=23, minute=59, second=59)
            if "timestamp" in filtro:
                filtro["timestamp"]["$lte"] = fecha_f.isoformat()
            else:
                filtro["timestamp"] = {"$lte": fecha_f.isoformat()}
        except ValueError:
            pass
    
    if email:
        filtro["usuario_afectado.email"] = {"$regex": email, "$options": "i"}
    
    if resultado:
        filtro["resultado"] = resultado
    
    if tipo:
        filtro["tipo"] = tipo
    
    # Obtener total para paginación
    total = await db.sec_bitacora_admin.count_documents(filtro)
    
    # Obtener eventos con paginación
    eventos_cursor = db.sec_bitacora_admin.find(
        filtro,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit)
    
    eventos = await eventos_cursor.to_list(limit)
    
    # Calcular páginas
    paginas_total = (total + limit - 1) // limit if total > 0 else 1
    pagina_actual = (skip // limit) + 1
    
    return {
        "total": total,
        "pagina": pagina_actual,
        "paginas_total": paginas_total,
        "limit": limit,
        "eventos": eventos
    }


@api_router.get("/admin/bitacora/{evento_id}")
async def get_bitacora_evento_detalle(
    evento_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 12: Obtiene detalle completo de un evento de bitácora.
    
    Acceso: Solo SuperAdministrador
    """
    # Verificar acceso: Solo SuperAdministrador
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(
            status_code=403,
            detail="Solo SuperAdministrador puede acceder a la bitácora RBAC"
        )
    
    evento = await db.sec_bitacora_admin.find_one(
        {"id": evento_id},
        {"_id": 0}
    )
    
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    return evento


# ==============================================================================
# FIN FASE 12 - BITÁCORA RBAC
# ==============================================================================


# ==============================================================================
# FASE 13: PERFILES PREDEFINIDOS RBAC
# ==============================================================================
# Perfiles como metadato y atajo de asignación de roles.
# - sec_roles sigue siendo la fuente de verdad operativa
# - sec_perfil es solo referencia informativa y trazabilidad
# - Asignar perfil = reemplazar sec_roles con los roles del perfil
# - NO modifica rbac_helper.py ni la resolución de permisos
# ==============================================================================

# Whitelist de perfiles permitidos FASE 13 (no expandir sin autorización)
PERFILES_FASE_13_WHITELIST = [
    "PERFIL_VISOR_BASICO",
    "PERFIL_VISOR_SISTEMA",
    "PERFIL_VISOR_COMPLETO",
    "PERFIL_ADMIN_USUARIOS",
    "PERFIL_GESTOR_SISTEMA"
]


@api_router.get("/admin/perfiles")
async def get_perfiles_disponibles(current_user: Dict = Depends(get_current_user)):
    """
    FASE 13: Lista los perfiles predefinidos disponibles.
    
    Acceso: Solo SuperAdministrador
    """
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede ver perfiles")
    
    perfiles = await db.sec_perfiles.find(
        {"activo": True},
        {"_id": 0}
    ).to_list(100)
    
    return {"perfiles": perfiles}


class AsignarPerfilRequest(BaseModel):
    usuario_email: str
    perfil: str


@api_router.post("/admin/perfiles/asignar")
async def asignar_perfil_usuario(
    request: AsignarPerfilRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 13: Asigna un perfil predefinido a un usuario.
    
    Comportamiento:
    - Sobrescribe sec_roles con los roles exactos del perfil
    - Guarda sec_perfil como metadato informativo
    - Registra en sec_bitacora_admin
    
    Acceso: Solo SuperAdministrador
    """
    # 1. Verificar acceso
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede asignar perfiles")
    
    # 2. Validar perfil en whitelist
    if request.perfil not in PERFILES_FASE_13_WHITELIST:
        raise HTTPException(
            status_code=400,
            detail=f"Perfil '{request.perfil}' no está en whitelist FASE 13. Permitidos: {PERFILES_FASE_13_WHITELIST}"
        )
    
    # 3. Obtener perfil de la colección
    perfil_doc = await db.sec_perfiles.find_one({"codigo": request.perfil, "activo": True})
    if not perfil_doc:
        raise HTTPException(status_code=404, detail=f"Perfil {request.perfil} no encontrado o inactivo")
    
    roles_del_perfil = perfil_doc.get("roles", [])
    
    # 4. Buscar usuario
    usuario = await db.users.find_one({"email": request.usuario_email})
    if not usuario:
        # Auditoría de fallo
        await db.sec_bitacora_admin.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tipo": "ASIGNAR_PERFIL",
            "administrador": {
                "id": current_user.get("id"),
                "email": current_user.get("email"),
                "role": current_user.get("role")
            },
            "usuario_afectado": {"id": "", "email": request.usuario_email},
            "perfil": request.perfil,
            "roles_del_perfil": roles_del_perfil,
            "accion": "ASIGNAR",
            "resultado": "RECHAZADO",
            "mensaje": f"Usuario {request.usuario_email} no encontrado",
            "fase": "FASE_13"
        })
        raise HTTPException(status_code=404, detail=f"Usuario {request.usuario_email} no encontrado")
    
    # 5. Obtener estado anterior
    perfil_anterior = usuario.get("sec_perfil")
    roles_anteriores = usuario.get("sec_roles", [])
    
    # 6. Actualizar usuario: sobrescribir sec_roles, sec_perfil y limpiar sec_roles_alcance
    # FASE 14: Al cambiar perfil, los roles cambian, por lo que el alcance anterior no aplica
    await db.users.update_one(
        {"email": request.usuario_email},
        {"$set": {
            "sec_perfil": request.perfil,
            "sec_roles": roles_del_perfil,
            "sec_roles_alcance": {}  # FASE 14: Limpiar alcance al cambiar perfil
        }}
    )
    
    # 7. Auditoría
    await db.sec_bitacora_admin.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": "ASIGNAR_PERFIL",
        "administrador": {
            "id": current_user.get("id"),
            "email": current_user.get("email"),
            "role": current_user.get("role")
        },
        "usuario_afectado": {
            "id": usuario.get("id"),
            "email": request.usuario_email
        },
        "perfil": request.perfil,
        "roles_del_perfil": roles_del_perfil,
        "accion": "ASIGNAR",
        "perfil_anterior": perfil_anterior,
        "roles_anteriores": roles_anteriores,
        "roles_nuevos": roles_del_perfil,
        "resultado": "OK",
        "mensaje": f"Perfil {request.perfil} asignado exitosamente a {request.usuario_email}. Roles aplicados: {roles_del_perfil}",
        "fase": "FASE_13"
    })
    
    return {
        "success": True,
        "usuario": request.usuario_email,
        "perfil": request.perfil,
        "roles_aplicados": roles_del_perfil,
        "perfil_anterior": perfil_anterior,
        "roles_anteriores": roles_anteriores,
        "mensaje": f"Perfil {request.perfil} asignado exitosamente"
    }


class RetirarPerfilRequest(BaseModel):
    usuario_email: str


@api_router.post("/admin/perfiles/retirar")
async def retirar_perfil_usuario(
    request: RetirarPerfilRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 13: Retira el perfil de un usuario.
    
    Comportamiento:
    - Limpia sec_perfil (None)
    - Limpia sec_roles (lista vacía)
    - Registra en sec_bitacora_admin
    
    Acceso: Solo SuperAdministrador
    """
    # 1. Verificar acceso
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede retirar perfiles")
    
    # 2. Buscar usuario
    usuario = await db.users.find_one({"email": request.usuario_email})
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario {request.usuario_email} no encontrado")
    
    # 3. Obtener estado anterior
    perfil_anterior = usuario.get("sec_perfil")
    roles_anteriores = usuario.get("sec_roles", [])
    
    if not perfil_anterior:
        return {
            "success": True,
            "usuario": request.usuario_email,
            "mensaje": "Usuario no tenía perfil asignado",
            "cambio_realizado": False
        }
    
    # 4. Limpiar perfil, roles y alcance
    # FASE 14: Al retirar perfil, también limpiar alcance
    await db.users.update_one(
        {"email": request.usuario_email},
        {"$set": {
            "sec_perfil": None,
            "sec_roles": [],
            "sec_roles_alcance": {}  # FASE 14: Limpiar alcance al retirar perfil
        }}
    )
    
    # 5. Auditoría
    await db.sec_bitacora_admin.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": "RETIRAR_PERFIL",
        "administrador": {
            "id": current_user.get("id"),
            "email": current_user.get("email"),
            "role": current_user.get("role")
        },
        "usuario_afectado": {
            "id": usuario.get("id"),
            "email": request.usuario_email
        },
        "perfil": perfil_anterior,
        "accion": "RETIRAR",
        "perfil_anterior": perfil_anterior,
        "roles_anteriores": roles_anteriores,
        "roles_nuevos": [],
        "resultado": "OK",
        "mensaje": f"Perfil {perfil_anterior} retirado de {request.usuario_email}. Roles limpiados.",
        "fase": "FASE_13"
    })
    
    return {
        "success": True,
        "usuario": request.usuario_email,
        "perfil_retirado": perfil_anterior,
        "roles_eliminados": roles_anteriores,
        "mensaje": f"Perfil {perfil_anterior} retirado exitosamente",
        "cambio_realizado": True
    }


# ==============================================================================
# FIN FASE 13 - PERFILES PREDEFINIDOS
# ==============================================================================


# ==============================================================================
# FASE 14: ALCANCE ORGANIZACIONAL RBAC (METADATO)
# ==============================================================================
# Modelo de alcance organizacional por rol.
# - sec_roles_alcance define alcance por cada rol en sec_roles
# - En esta fase es solo METADATO, no filtrado activo
# - NO modifica rbac_helper.py ni resolución de permisos
# - Sincronización: retirar rol limpia su alcance asociado
# ==============================================================================

# Tipos de alcance permitidos
TIPOS_ALCANCE_PERMITIDOS = ["GLOBAL", "EMPRESA", "UNIDAD", "SUCURSAL", "ALMACEN"]


@api_router.get("/admin/alcance/empresas")
async def get_empresas_alcance(current_user: Dict = Depends(get_current_user)):
    """
    FASE 14: Lista empresas disponibles para asignar alcance.
    
    Acceso: Solo SuperAdministrador
    """
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede consultar alcance")
    
    empresas = await db.sec_empresas.find(
        {},
        {"_id": 0, "id": 1, "codigo": 1, "nombre": 1}
    ).to_list(100)
    
    return {"empresas": empresas}


@api_router.get("/admin/alcance/unidades")
async def get_unidades_alcance(
    empresa_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 14: Lista unidades de negocio disponibles.
    
    Acceso: Solo SuperAdministrador
    """
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede consultar alcance")
    
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    
    unidades = await db.sec_unidades_negocio.find(
        filtro,
        {"_id": 0, "id": 1, "codigo": 1, "nombre": 1, "empresa_id": 1}
    ).to_list(100)
    
    return {"unidades": unidades}


@api_router.get("/admin/alcance/sucursales")
async def get_sucursales_alcance(
    unidad_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 14: Lista sucursales disponibles.
    
    Acceso: Solo SuperAdministrador
    """
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede consultar alcance")
    
    filtro = {}
    if unidad_id:
        filtro["unidad_negocio_id"] = unidad_id
    
    sucursales = await db.sec_sucursales.find(
        filtro,
        {"_id": 0, "id": 1, "codigo": 1, "nombre": 1, "unidad_negocio_id": 1}
    ).to_list(100)
    
    return {"sucursales": sucursales}


class AsignarAlcanceRequest(BaseModel):
    usuario_email: str
    rol: str
    tipo: str  # GLOBAL | EMPRESA | UNIDAD | SUCURSAL | ALMACEN
    empresa_id: Optional[str] = None
    unidades_ids: List[str] = []
    sucursales_ids: List[str] = []
    almacenes_ids: List[str] = []


@api_router.post("/admin/alcance/asignar")
async def asignar_alcance_rol(
    request: AsignarAlcanceRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 14: Asigna alcance organizacional a un rol específico de un usuario.
    
    Comportamiento:
    - Verifica que el usuario tenga el rol en sec_roles
    - Actualiza sec_roles_alcance[rol] con el nuevo alcance
    - Registra auditoría
    
    IMPORTANTE: En esta fase es solo METADATO, no filtrado activo.
    
    Acceso: Solo SuperAdministrador
    """
    # 1. Verificar acceso
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede asignar alcance")
    
    # 2. Validar tipo de alcance
    if request.tipo not in TIPOS_ALCANCE_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de alcance inválido. Permitidos: {TIPOS_ALCANCE_PERMITIDOS}"
        )
    
    # 3. Buscar usuario
    usuario = await db.users.find_one({"email": request.usuario_email})
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario {request.usuario_email} no encontrado")
    
    # 4. Verificar que el usuario tenga el rol
    sec_roles = usuario.get("sec_roles", [])
    if request.rol not in sec_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Usuario no tiene el rol {request.rol}. Roles actuales: {sec_roles}"
        )
    
    # 5. Obtener alcance anterior
    sec_roles_alcance = usuario.get("sec_roles_alcance", {})
    alcance_anterior = sec_roles_alcance.get(request.rol)
    
    # 6. Construir nuevo alcance
    nuevo_alcance = {
        "tipo": request.tipo,
        "empresa_id": request.empresa_id,
        "unidades_ids": request.unidades_ids,
        "sucursales_ids": request.sucursales_ids,
        "almacenes_ids": request.almacenes_ids,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 7. Actualizar sec_roles_alcance
    sec_roles_alcance[request.rol] = nuevo_alcance
    
    await db.users.update_one(
        {"email": request.usuario_email},
        {"$set": {"sec_roles_alcance": sec_roles_alcance}}
    )
    
    # 8. Auditoría
    await db.sec_bitacora_admin.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": "ASIGNAR_ALCANCE",
        "administrador": {
            "id": current_user.get("id"),
            "email": current_user.get("email"),
            "role": current_user.get("role")
        },
        "usuario_afectado": {
            "id": usuario.get("id"),
            "email": request.usuario_email
        },
        "rol": request.rol,
        "alcance_nuevo": nuevo_alcance,
        "alcance_anterior": alcance_anterior,
        "accion": "ASIGNAR",
        "resultado": "OK",
        "mensaje": f"Alcance {request.tipo} asignado a rol {request.rol} de {request.usuario_email}",
        "fase": "FASE_14"
    })
    
    return {
        "success": True,
        "usuario": request.usuario_email,
        "rol": request.rol,
        "alcance": nuevo_alcance,
        "alcance_anterior": alcance_anterior,
        "mensaje": f"Alcance {request.tipo} asignado exitosamente"
    }


class RetirarAlcanceRequest(BaseModel):
    usuario_email: str
    rol: str


@api_router.post("/admin/alcance/retirar")
async def retirar_alcance_rol(
    request: RetirarAlcanceRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 14: Retira el alcance de un rol específico de un usuario.
    
    Comportamiento:
    - Elimina la entrada del rol en sec_roles_alcance
    - Registra auditoría
    
    Acceso: Solo SuperAdministrador
    """
    # 1. Verificar acceso
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede retirar alcance")
    
    # 2. Buscar usuario
    usuario = await db.users.find_one({"email": request.usuario_email})
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario {request.usuario_email} no encontrado")
    
    # 3. Obtener alcance actual
    sec_roles_alcance = usuario.get("sec_roles_alcance", {})
    alcance_anterior = sec_roles_alcance.get(request.rol)
    
    if not alcance_anterior:
        return {
            "success": True,
            "usuario": request.usuario_email,
            "rol": request.rol,
            "mensaje": f"El rol {request.rol} no tenía alcance asignado",
            "cambio_realizado": False
        }
    
    # 4. Eliminar alcance del rol
    del sec_roles_alcance[request.rol]
    
    await db.users.update_one(
        {"email": request.usuario_email},
        {"$set": {"sec_roles_alcance": sec_roles_alcance}}
    )
    
    # 5. Auditoría
    await db.sec_bitacora_admin.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": "RETIRAR_ALCANCE",
        "administrador": {
            "id": current_user.get("id"),
            "email": current_user.get("email"),
            "role": current_user.get("role")
        },
        "usuario_afectado": {
            "id": usuario.get("id"),
            "email": request.usuario_email
        },
        "rol": request.rol,
        "alcance_anterior": alcance_anterior,
        "accion": "RETIRAR",
        "resultado": "OK",
        "mensaje": f"Alcance retirado del rol {request.rol} de {request.usuario_email}",
        "fase": "FASE_14"
    })
    
    return {
        "success": True,
        "usuario": request.usuario_email,
        "rol": request.rol,
        "alcance_retirado": alcance_anterior,
        "mensaje": f"Alcance retirado del rol {request.rol}",
        "cambio_realizado": True
    }


# ==============================================================================
# FIN FASE 14 - ALCANCE ORGANIZACIONAL RBAC
# ==============================================================================


# Incluir el router después de definir TODOS los endpoints
app.include_router(api_router)

# ============================================================================
# PORTAL DE PROVEEDORES (Subproyecto separado)
# ============================================================================
from routes.portal_proveedores import portal_router, init_portal_db
init_portal_db(db, JWT_SECRET, execute_sql_query)
app.include_router(portal_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    # FASE AUTH-SECURITY-01: Para cookies, no se puede usar wildcard con credentials=True
    # Se usan orígenes explícitos. En producción, CORS_ORIGINS debe estar configurado.
    # NOTA: El proxy de Kubernetes/Cloudflare puede sobrescribir estos headers.
    # Si las cookies no funcionan, memoryToken es el fallback para autenticación SPA.
    allow_origins=[
        origin.strip() 
        for origin in os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
        if origin.strip() and origin.strip() != '*'
    ] or ["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    # MongoDB ELIMINADO - Este handler ya no es necesario
    # La variable 'client' ya no existe (era el cliente de MongoDB)
    pass


# === FASE 2 - MÓDULO OPERATIVO (CAB-003) ===
from modules.fase2_operativo.router import router_fase2_operativo
app.include_router(router_fase2_operativo, prefix="/api/v2", tags=["Fase2-Operativo"])

# ============= SUBFASE 2B.5: SISTEMA DE NOTIFICACIONES WHATSAPP =============
# Importar y registrar rutas de notificaciones (core transversal)
from core.communications.routes import router as communications_router, init_notifications_routes
init_notifications_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
app.include_router(communications_router, tags=["Notificaciones"])

# ============= SUBFASE 2B.5.2: SCHEDULER AUTOMÁTICO =============
# Sistema de jobs periódicos para SLA y notificaciones
from core.scheduler.routes import router as scheduler_router, init_scheduler_routes
init_scheduler_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
app.include_router(scheduler_router, tags=["Scheduler"])

# ============= CENTRO DE CONTROL EDARSA =============
# Sistema proactivo de observabilidad y detección de regresiones
# Documentación: /app/docs/CENTRO_CONTROL_EDARSA.md
from core.centro_control import centro_control_router
app.include_router(centro_control_router, tags=["Centro de Control"])
logger.info("Centro de Control EDARSA registrado")

# ============= MÓDULO CONFIGURACIÓN =============
# Gestión de configuraciones maestras (asignaciones, etc.)
from modules.configuracion.routes.config_asignaciones_routes import router as config_asignaciones_router
app.include_router(config_asignaciones_router, tags=["Configuración"])
logger.info("Módulo Configuración registrado")

# ============= FASE 2D: RBAC AVANZADO =============
# Sistema de control de acceso basado en roles
from core.rbac.routes import router as rbac_router
from core.rbac.service import RBACService
# Inicializar RBAC (sembrar permisos y roles si no existen)
try:
    rbac_service = RBACService(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
    rbac_service.ensure_initialized()
    logger.info("RBAC Service inicializado (SQL Server)")
except Exception as e:
    logger.warning(f"Error inicializando RBAC: {e}")
app.include_router(rbac_router, prefix="/api/v2", tags=["RBAC"])

# ============= COMERCIAL V2 - ENDPOINTS AISLADOS =============
# Endpoints que leen SOLO desde EDARSAHUB v2
# NO reemplazan el tablero actual
# Feature Flag: COMERCIAL_V2_ENABLED=false (default OFF)
try:
    from modules.comercial_v2 import get_comercial_v2_router
    comercial_v2_router = get_comercial_v2_router()
    app.include_router(comercial_v2_router, prefix="/api/v2", tags=["Comercial V2"])
    logger.info("Comercial V2 endpoints registrados en /api/v2/comercial/*")
except Exception as e:
    logger.warning(f"Error registrando Comercial V2: {e}")

# =============================================================================
# FASE 4D: Admin CORE Connections Router
# =============================================================================
try:
    from api.admin_core_connections import router as admin_core_router
    from core.security import verify_token as verify_jwt_token
    
    # Middleware para validar SuperAdministrador en rutas CORE admin
    from fastapi import Request
    
    @app.middleware("http")
    async def validate_core_admin_access(request: Request, call_next):
        """
        FASE 4D: Valida que solo SuperAdministrador acceda a /api/admin/core-connections.
        """
        if request.url.path.startswith("/api/admin/core-connections"):
            # Obtener token del header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token de autenticación requerido"}
                )
            
            token = auth_header.replace("Bearer ", "")
            
            try:
                # Verificar token y obtener usuario
                payload = verify_jwt_token(token)
                if not payload:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Token inválido o expirado"}
                    )
                
                # Verificar rol SuperAdministrador
                role = payload.get('role', '').strip()
                role_normalized = role.lower().replace(' ', '').replace('_', '')
                
                if role_normalized not in ['superadministrador', 'superadmin']:
                    logger.warning(
                        f"[CORE_ADMIN][PERMISSION_DENIED] Usuario {payload.get('email')} "
                        f"con rol '{role}' intentó acceder a {request.url.path}"
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Solo SuperAdministrador puede administrar conexiones CORE"}
                    )
                
                # Auditar acceso
                logger.info(f"[CORE_ADMIN][ACCESS] SuperAdministrador {payload.get('email')} accediendo a {request.url.path}")
                
            except Exception as e:
                logger.error(f"[CORE_ADMIN][AUTH_ERROR] {type(e).__name__}: {str(e)[:100]}")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Error de autenticación"}
                )
        
        return await call_next(request)
    
    app.include_router(admin_core_router, prefix="/api", tags=["Admin CORE"])
    logger.info("✓ Admin CORE Connections router registrado")
except Exception as e:
    logger.warning(f"Error registrando Admin CORE router: {e}")

# =============================================================================
# FASE P0D: DBA Credential Endpoint para Diagnóstico Ejecutor B
# =============================================================================
try:
    from api.dba_credential_p0d import router as dba_cred_router
    app.include_router(dba_cred_router, prefix="/api", tags=["Admin DBA P0D"])
    logger.info("✓ DBA Credential P0D router registrado")
except Exception as e:
    logger.warning(f"Error registrando DBA Credential P0D router: {e}")

# =============================================================================
# Configuración Operativa de Unidades (Turnos / Ventas del Día)
# =============================================================================
try:
    from api.configuracion_operativa_unidades import router as config_operativa_router
    app.include_router(config_operativa_router, prefix="/api", tags=["Admin Config Operativa"])
    logger.info("✓ Configuración Operativa Unidades router registrado")
except Exception as e:
    logger.warning(f"Error registrando Configuración Operativa router: {e}")

# =============================================================================
# CRM VTiger Integration
# =============================================================================
try:
    from modules.crm.routes import router as crm_router
    app.include_router(crm_router, tags=["CRM - VTiger"])
    logger.info("✓ CRM VTiger router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM VTiger router: {e}")

# =============================================================================
# CRM Enterprise Native (EDARSAHUB SQL)
# =============================================================================
try:
    from modules.crm.native_routes import router as crm_native_router
    app.include_router(crm_native_router, tags=["CRM - Native (EDARSAHUB SQL)"])
    logger.info("✓ CRM Native router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Native router: {e}")

# =============================================================================
# CRM Integration Framework (Conectores Externos)
# =============================================================================
try:
    from modules.crm.integration_routes import router as crm_integration_router
    app.include_router(crm_integration_router, tags=["CRM - Integration Framework"])
    logger.info("✓ CRM Integration router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Integration router: {e}")

# =============================================================================
# CRM COMERCIAL (Enterprise-Grade - EDARSAHUB SQL)
# =============================================================================
try:
    from modules.crm.comercial_routes import router as crm_comercial_router
    app.include_router(crm_comercial_router, tags=["CRM Comercial"])
    logger.info("✓ CRM Comercial router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Comercial router: {e}")

try:
    from modules.crm.automation_routes import router as crm_automation_router
    app.include_router(crm_automation_router, tags=["CRM - Automatización"])
    logger.info("✓ CRM Automation router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Automation router: {e}")

try:
    from modules.crm.trigger_routes import router as crm_trigger_router
    app.include_router(crm_trigger_router, tags=["CRM - Triggers"])
    logger.info("✓ CRM Triggers router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Triggers router: {e}")

# =============================================================================
# TABLAJERÍA (Operaciones - Producción/Transformación)
# =============================================================================
try:
    from modules.tablajeria.routes import router as tablajeria_router
    app.include_router(tablajeria_router, tags=["Tablajería"])
    logger.info("✓ Tablajería router registrado")
except Exception as e:
    logger.warning(f"Error registrando Tablajería router: {e}")

# =============================================================================
# CAVA DE SOCIOS (Comercial - Experiencia Cliente)
# =============================================================================
try:
    from modules.cava_socios.routes import router as cava_socios_router
    app.include_router(cava_socios_router, tags=["Cava de Socios"])
    logger.info("✓ Cava de Socios router registrado")
except Exception as e:
    logger.warning(f"Error registrando Cava de Socios router: {e}")


# Startup: Iniciar scheduler
@app.on_event("startup")
async def startup_scheduler():
    """Inicia el scheduler de jobs automáticos."""
    try:
        from core.scheduler import start_scheduler
        await start_scheduler(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
        logger.info("Scheduler iniciado correctamente (SQL-only mode)")
    except Exception as e:
        logger.error(f"Error iniciando scheduler: {e}")
        # No fallar el startup por el scheduler

# Shutdown: Detener scheduler
@app.on_event("shutdown")
async def shutdown_scheduler():
    """Detiene el scheduler limpiamente."""
    try:
        from core.scheduler import stop_scheduler
        await stop_scheduler()
        logger.info("Scheduler detenido correctamente")
    except Exception as e:
        logger.error(f"Error deteniendo scheduler: {e}")

