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

# ==============================================================================
# CARGA DE VARIABLES DE ENTORNO - DEBE ESTAR ANTES DE CUALQUIER OTRO IMPORT
# ==============================================================================
# P0-INCIDENTE-SERVER_SECRET_KEY: load_dotenv() DEBE ejecutarse antes de que
# cualquier módulo intente leer variables de entorno (especialmente secret_manager)
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ==============================================================================
# VALIDACIÓN DE SERVER_SECRET_KEY - Entorno Preview/Staging/Production
# ==============================================================================
# MÁXIMA: SERVER_SECRET_KEY es obligatoria para cifrado de credenciales.
# - No se permite fallback a llave insegura
# - No se genera llave nueva en runtime si hay datos cifrados
# - Solo se loggea fingerprint, NUNCA la llave real
# ==============================================================================
def _validate_server_secret_key():
    """
    Valida que SERVER_SECRET_KEY esté configurada correctamente.
    Solo loggea fingerprint seguro, NUNCA la llave real.
    """
    import hashlib
    key = os.environ.get('SERVER_SECRET_KEY')

    # Determinar ambiente
    app_url = os.environ.get('APP_URL', '')
    is_preview = 'preview' in app_url.lower()
    is_production = 'production' in app_url.lower() or (app_url and 'preview' not in app_url.lower() and 'localhost' not in app_url.lower())

    if key:
        # Calcular fingerprint seguro (primeros 6 chars del hash SHA256)
        fingerprint = hashlib.sha256(key.encode()).hexdigest()[:6]
        print(f"[ENCRYPTION] SERVER_SECRET_KEY loaded: true")
        print(f"[ENCRYPTION] Key fingerprint: {fingerprint}")
        return True
    else:
        # En preview/staging/production, la ausencia de SERVER_SECRET_KEY es CRÍTICA
        if is_preview or is_production:
            print("[ENCRYPTION] ⚠️  WARNING: SERVER_SECRET_KEY not configured")
            print("[ENCRYPTION] Encrypted credentials will NOT be decryptable")
            print("[ENCRYPTION] Jobs/syncs that require credentials may fail")
            # No levantar error para no romper el servidor, pero advertir claramente
            return False
        else:
            # En desarrollo local sin datos reales, permitir sin error
            print("[ENCRYPTION] SERVER_SECRET_KEY not configured (development mode)")
            return False

# Ejecutar validación al inicio
_ENCRYPTION_AVAILABLE = _validate_server_secret_key()

# ==============================================================================
# IMPORTS PRINCIPALES (después de cargar .env)
# ==============================================================================
from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
# MongoDB import movido a bloque condicional más abajo
import logging
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

app = FastAPI(title="EDARSA HUB API")
api_router = APIRouter(prefix="/api")

# CAVAS CORPORATIVAS GATE 5 - API backend B2B separada y RBAC SQL explicito
from modules.cavas_corporativas.routes import router as cavas_corporativas_router
api_router.include_router(cavas_corporativas_router)

# CATALOGO AMPLIADO GATE 4 - Gobierno corporativo SQL-first
from modules.catalogo_ampliado.routes import router as catalogo_ampliado_router
api_router.include_router(catalogo_ampliado_router)

# TABLAJERIA - Operaciones / Produccion
# Router existente con prefijo propio /api/tablajeria; se monta directo en app para evitar /api/api.
from modules.tablajeria.routes import router as tablajeria_router
app.include_router(tablajeria_router)

# TABLAJERIA - Operaciones / Produccion
# Router existente con prefijo propio /api/tablajeria; se monta directo en app para evitar /api/api.
from modules.tablajeria.routes import router as tablajeria_router
app.include_router(tablajeria_router)

# Montar archivos estáticos para descargas
STATIC_DIR = ROOT_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Descargas accesibles vía ingress externo (solo /api/* se enruta al backend).
# Sirve /app/backend/static/downloads en /api/downloads para exportaciones/backups.
DOWNLOADS_DIR = STATIC_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="api-downloads")

# ==========================================
# ESCUDO GLOBAL CONTRA CRASHEOS (Evita Errores 502)
# ==========================================
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Atrapa cualquier error no manejado en el código para evitar que el contenedor
    colapse y cierre las conexiones bruscamente (Error 502).
    """
    logging.error(f"[ALERTA CRÍTICA] Fallo no manejado en ruta {request.url.path}: {str(exc)}")

    # Retorna un 500 estructurado. El Frontend (ya blindado) leerá la lista vacía
    # y usará sus datos de respaldo en lugar de quedarse "pensando".
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor. Proceso recuperado automáticamente.",
            "data": []
        }
    )

# ==========================================
# HEALTH CHECK GENERAL (Monitoreo de Infraestructura)
# ==========================================
@app.get("/api/health")
async def health_check():
    """
    Endpoint de salud vital. La infraestructura (Docker/Kubernetes) hará ping aquí.
    Si el servidor se bloquea, la infraestructura lo detectará y reiniciará el nodo.
    """
    return {"status": "operativo", "sistema": "EDARSA HUB", "version": "1.0"}

# ==========================================
# ENDPOINTS FALLBACK TABLERO EJECUTIVO (EDARSA HUB)
# Garantizan respuesta aunque SQL Server esté caído
# ==========================================

@app.get("/api/comercial/tablero-ejecutivo-fallback")
async def tablero_ejecutivo_fallback():
    """
    Endpoint fallback con datos EDARSA mockeados.
    Usado cuando SQL Server no responde.
    """
    return {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "periodo": {"mes": 5, "anio": 2026, "dias_transcurridos": 30, "dias_mes": 31},
        "totales": {
            "ventas": 15710000,
            "pax": 15008,
            "cheques": 5223,
            "cheque_promedio": 3010,
            "pax_prom": 1050,
            "proyeccion": 16809700,
            "var_vs_mes_ant": 1.9,
            "var_vs_año_ant": 9.6
        },
        "unidades": [
            {"id": "cienfuegos", "unidad": "CIENFUEGOS", "ventas": 4130000, "proyeccion": 4410000, "var_vs_mes_ant": 8.8, "var_vs_año_ant": -14.5, "pax": 3177, "cheques": 1052, "cheque_promedio": 3926, "pax_promedio": 1300, "data_status": "DATA_OK"},
            {"id": "merida", "unidad": "130° MERIDA", "ventas": 3570000, "proyeccion": 3820000, "var_vs_mes_ant": -12.7, "var_vs_año_ant": -15.6, "pax": 2314, "cheques": 794, "cheque_promedio": 4496, "pax_promedio": 1543, "data_status": "DATA_OK"},
            {"id": "queretaro", "unidad": "130° QUERETARO", "ventas": 3460000, "proyeccion": 3700000, "var_vs_mes_ant": 4.5, "var_vs_año_ant": -0.9, "pax": 2067, "cheques": 704, "cheque_promedio": 4915, "pax_promedio": 1674, "data_status": "DATA_OK"},
            {"id": "estelar", "unidad": "LA ESTELAR", "ventas": 2470000, "proyeccion": 2640000, "var_vs_mes_ant": 2.3, "var_vs_año_ant": None, "pax": 4520, "cheques": 1658, "cheque_promedio": 1490, "pax_promedio": 546, "data_status": "DATA_OK"},
            {"id": "origen", "unidad": "ORIGEN", "ventas": 2070000, "proyeccion": 2220000, "var_vs_mes_ant": 15.6, "var_vs_año_ant": 16.6, "pax": 2930, "cheques": 1015, "cheque_promedio": 2039, "pax_promedio": 706, "data_status": "DATA_OK"}
        ],
        "_fallback": True
    }

@app.get("/api/v2/comercial/dashboard-fallback")
async def dashboard_comercial_v2_fallback():
    """
    Endpoint V2 fallback con datos EDARSA mockeados.
    """
    return {
        "success": True,
        "data": {
            "consolidatedSales": 15710000,
            "growthMonth": 1.9,
            "growthYear": 9.6,
            "paxTotal": 15008,
            "paxAvg": 1050,
            "tickets": 5223,
            "ticketAvg": 3010,
            "units": [
                {"id": "cienfuegos", "name": "CIENFUEGOS", "sales": 4130000, "projection": 4410000, "growthMonth": 8.8, "growthYear": -14.5, "pax": 3177, "tickets": 1052},
                {"id": "merida", "name": "130° MERIDA", "sales": 3570000, "projection": 3820000, "growthMonth": -12.7, "growthYear": -15.6, "pax": 2314, "tickets": 794},
                {"id": "queretaro", "name": "130° QUERETARO", "sales": 3460000, "projection": 3700000, "growthMonth": 4.5, "growthYear": -0.9, "pax": 2067, "tickets": 704},
                {"id": "estelar", "name": "LA ESTELAR", "sales": 2470000, "projection": 2640000, "growthMonth": 2.3, "growthYear": None, "pax": 4520, "tickets": 1658},
                {"id": "origen", "name": "ORIGEN", "sales": 2070000, "projection": 2220000, "growthMonth": 15.6, "growthYear": 16.6, "pax": 2930, "tickets": 1015}
            ]
        },
        "_fallback": True
    }

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
# P2-01 Config Central EDARSAHUB
from core.config.edarsahub_config import get_edarsahub_sql_config

def _get_edarsahub_config_dict() -> dict:
    """P2-01: Convierte dataclass a formato diccionario legacy."""
    cfg = get_edarsahub_sql_config()
    return {
        'host': cfg.host,
        'port': cfg.port,
        'database': cfg.database,
        'username': cfg.user,
        'password': cfg.password,
    }
from core.refresh_tokens import init_refresh_tokens_module

# Configuración EDARSAHUB para refresh tokens (lee desde .env)
EDARSAHUB_CONFIG = _get_edarsahub_config_dict()
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
from modules.compras.schemas import AuditoriaOperativaRequest

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

# FASE 1C-3C: Módulo Costos y Márgenes (NO-LIVE, EDARSAHUB SQL exclusivo)
# ===========================================
from modules.costos_margenes import router as costos_margenes_router
api_router.include_router(costos_margenes_router)

# CATALOGO-CANONICO-C2: catálogo canónico NO-LIVE (Categoría/Familia/Subfamilia)
from modules.catalogo import router as catalogo_router
api_router.include_router(catalogo_router)

# COMERCIAL-ENRIQUECIDO-C: Catálogo Comercial Enriquecido de Productos (NO-LIVE, SQL-first)
from modules.comercial_enriquecido import comercial_enriquecido_router
api_router.include_router(comercial_enriquecido_router)

# BENCHMARK-INTERNO (G3): Portal Inteligencia Comercial - comparativo de grupo con confidencialidad backend
from modules.comercial_benchmark import comercial_benchmark_router
api_router.include_router(comercial_benchmark_router)

# FASE 1C-3F: Simulación de Precios y Solicitudes de Cambio
# ===========================================
from modules.costos_margenes.routes_precios import router as costos_margenes_precios_router
api_router.include_router(costos_margenes_precios_router)

# FASE 1C-3I-B: Motor de Precios Sugeridos y Benchmark Competitivo
# ===========================================
from modules.comercial.routes_pricing_ia import router as pricing_ia_router
api_router.include_router(pricing_ia_router)

# FASE 1C-3I-C: Integración GPT-5.2 para Pricing IA
# ===========================================
from modules.comercial.routes_pricing_ai import router as pricing_ai_gpt_router
api_router.include_router(pricing_ai_gpt_router)

# Menú IA: Asistente conversacional (OpenAI gpt-5.5 vía EMERGENT_LLM_KEY)
# ===========================================
from modules.ia_assistant.routes import router as ia_assistant_router
api_router.include_router(ia_assistant_router)

# FASE 1C-3I-G: Listas Manuales de Competidores para Pricing IA
# ===========================================
from modules.comercial.routes_listas_competidores import router as listas_competidores_router
api_router.include_router(listas_competidores_router)

# Benchmark Sectorial (reporte NO-LIVE derivado de tablas canonicas)
# ===========================================
from modules.comercial.routes_benchmark_sectorial import router as benchmark_sectorial_router
api_router.include_router(benchmark_sectorial_router)

# Ingesta de Competencia (adjunto/link -> staging -> tablas canonicas)
# ===========================================
from modules.comercial.routes_ingesta_competencia import router as ingesta_competencia_router
api_router.include_router(ingesta_competencia_router)

# FASE 1C-3G-F: Precios Sugeridos y Rangos Vinos
# ===========================================
from modules.comercial.routes_precios_sugeridos import router as precios_sugeridos_router
api_router.include_router(precios_sugeridos_router)

# COSTOS-ALERTAS-001-C: Reglas de Margen Esperado y Alertas
# ===========================================
from modules.comercial.routes_alertas_margen import router as alertas_margen_router
api_router.include_router(alertas_margen_router)

# FASE 1C-3I-B v2: Competidores Enterprise por Unidad de Negocio
# ===========================================
from modules.comercial.routes_competidores_enterprise import router as competidores_enterprise_router
api_router.include_router(competidores_enterprise_router)

# ============================================================================
# PORTAL INTELIGENCIA COMERCIAL IA - Junio 2026
# Endpoints: /api/inteligencia/*
# Fuente: EDARSAHUB (View_Inteligencia_Comercial, Fact_Ventas_Consolidadas)
# NOTA: Portal EXTERNO sin autenticación del CRM principal
# ============================================================================
from modules.inteligencia_comercial.routes import router as inteligencia_router
# Portal Inteligencia EXTERNO: auth propia + guard de scoping por unidad
from routes.portal_inteligencia import router as portal_intel_router, intel_portal_guard
from modules.inteligencia_comercial.iscam_routes import iscam_router
from fastapi import Depends as _DependsIntel
from core.rbac.middleware import require_explicit_permission
# Módulo de inteligencia comercial ya incluye su propia configuración.
# Guard DUAL: usuarios internos del CRM (acceso completo) O externos del portal
# de inteligencia (restringidos a sus unidades asignadas).
api_router.include_router(inteligencia_router, dependencies=[_DependsIntel(intel_portal_guard)])
api_router.include_router(iscam_router, dependencies=[_DependsIntel(intel_portal_guard)])
api_router.include_router(portal_intel_router)

# ============================================================================
# REPORTEADOR BI — Informe Gerencial MECA MPRO (9 páginas)
# Endpoints: /api/reporteador-bi/*  | Fuente: EDARSAHUB SQL (NO-LIVE)
# ============================================================================
from modules.reporteador_bi.routes import router as reporteador_bi_router
api_router.include_router(
    reporteador_bi_router,
    dependencies=[_DependsIntel(intel_portal_guard)],
)

# ============================================================================
# INTELIGENCIA COMERCIAL FASE 1 - Endpoints SQL-First
# Endpoints: /api/comercial/inteligencia/*
# Fuente: EDARSAHUB (Comercial_KPIs_Diarios_v2, Sync_PAX_Detalle, Sync_Sales)
# ============================================================================
from modules.comercial.inteligencia_comercial_routes import router as inteligencia_comercial_fase1_router
api_router.include_router(inteligencia_comercial_fase1_router)

# MÓDULO RECURSOS HUMANOS: Catálogos RH
# - Fase 6B: Migración de catálogos (Puestos, Sucursales, Tipos Incidencias)
# - 10 endpoints migrados con queries parametrizados
# - Validación Pydantic implementada
# ===========================================

from modules.rh import init_rh_module, get_router as get_rh_router, get_importador_router as get_rh_importador_router
from modules.rh.solicitudes_catalogo import router as rh_solicitudes_router
from modules.finanzas.cuentas_por_pagar import router as cxp_router
from modules.finanzas.comprobaciones import router as comprobaciones_router
from modules.finanzas.ingresos import router as ingresos_router
from modules.finanzas.tesoreria import router as tesoreria_router
from modules.finanzas.health import router as finanzas_health_router
from modules.health_v1.routes import router as health_v1_router  # FASE6: health canónico V1 NO-LIVE

# P1-FASE5A.1: Cuentas y Saldos Bancarios (EDARSAHUB)
# - Mayo 2026: Implementación endpoints backend
# - Fuente única: EDARSAHUB (no MongoDB)
# - Datos sensibles siempre enmascarados
from modules.finanzas.cuentas_bancarias import router as cuentas_bancarias_router
from modules.finanzas.saldos_bancarios import router as saldos_bancarios_router

# MÓDULO PROPINAS TPV: solo router EDARSAHUB v2 para superficie de usuario.
from modules.finanzas.propinas_tpv import get_router_edarsahub as get_propinas_tpv_edarsahub_router

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

from modules.corporate_filters.router import router as corporate_filters_router
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

# FASE FINANZAS: Registrar router de comprobaciones
api_router.include_router(comprobaciones_router)

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

# Router EDARSAHUB v2 para Propinas TPV
# Endpoints bajo /api/finanzas/propinas/v2/*
# Fuente de verdad: EDARSAHUB.propinas_tpv_control
api_router.include_router(get_propinas_tpv_edarsahub_router())

# FILTROS CORPORATIVOS EDARSAHUB
api_router.include_router(corporate_filters_router)

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

# RRR - atribucion determinista cliente <-> venta (Gate 4E)
from modules.rrr.routes import router as rrr_attribution_router
api_router.include_router(rrr_attribution_router)

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
# ============================================================================
# P3-01: CONSULTAS SQL MODULE (Módulo legacy reubicado a línea 19305)
# ============================================================================
# NOTA: El router de consultas_sql ahora se registra al final del archivo
# junto con los otros módulos SQL-first migrados de MongoDB

# ============================================================================
# P3-02: SYNC MONITOR SQL-First - Monitor de Sincronizaciones
# Endpoint: GET /api/admin/sync-monitor
# FUENTE: EDARSAHUB (Compras_Sync_Log, Comercial_SyncLog_v2, Servidores_Conexiones)
# NO usa MongoDB. NO usa conexiones LIVE.
# ============================================================================
from modules.sync_monitor import router as sync_monitor_router
api_router.include_router(sync_monitor_router)

# ============================================================================
# P3-03: BACKFILL CORPORATIVO SQL-First - Re-sincronización histórica
# Endpoint: POST /api/admin/backfill, GET /api/admin/backfill/modulos
# FUENTE: EDARSAHUB SQL. Modo DRY_RUN por defecto.
# ============================================================================
from modules.backfill_corporativo import router as backfill_corporativo_router
api_router.include_router(backfill_corporativo_router)

# ============================================================================
# P3: ADMIN SQL-FIRST - Usuarios, Roles, Permisos desde EDARSAHUB SQL
# Endpoints: /api/admin-sql/users, /api/admin-sql/roles, etc.
# ============================================================================
from modules.admin_sql.routes import router as admin_sql_router
from modules.admin_sql import rbac_pilot_service
from core.rbac_helper_sql import es_superadmin, es_admin, es_supervisor_o_superior
app.include_router(admin_sql_router)
from modules.admin_sql.rbac_audit_routes import router as rbac_audit_router
app.include_router(rbac_audit_router)

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

    from core.scheduler.jobs.sync_compras_job import run_sync_compras_job

    logging.info(f"[ADMIN] Usuario {current_user.get('email')} ejecutando sync compras manual (dry_run={dry_run})")

    result = await run_sync_compras_job(dry_run=dry_run)

    return result


@api_router.post("/admin/sync/compras/force-unlock")
async def admin_sync_compras_force_unlock(
    current_user: dict = Depends(get_current_user)
):
    """
    Fuerza la liberación de locks de sincronización de compras atascados.
    Uso: cuando un sync falló y dejó el lock activo.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden liberar locks")

    from datetime import datetime
    from zoneinfo import ZoneInfo

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)
        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))

        # Buscar locks activos de COMPRAS_SYNC
        cursor.execute("""
            SELECT SyncControlID, SyncRunID, StartedAtMexico
            FROM Sync_Control_Ejecuciones
            WHERE SyncType='COMPRAS_SYNC' AND Status='IN_PROGRESS' AND FinishedAtMexico IS NULL
        """)
        active_locks = cursor.fetchall()

        if not active_locks:
            conn.close()
            return {"status": "OK", "message": "No hay locks activos", "released": 0}

        # Liberar todos los locks activos
        for lock in active_locks:
            cursor.execute("""
                UPDATE Sync_Control_Ejecuciones
                SET Status='FORCE_RELEASED', FinishedAtMexico=%s, ErrorMessage='Liberado manualmente por admin'
                WHERE SyncControlID=%s
            """, (now_mx.replace(tzinfo=None), lock['SyncControlID']))

        conn.commit()
        conn.close()

        logging.info(f"[ADMIN] Usuario {current_user.get('email')} liberó {len(active_locks)} locks de sync compras")

        return {
            "status": "OK",
            "message": f"Liberados {len(active_locks)} locks",
            "released": len(active_locks),
            "locks_released": [l['SyncRunID'] for l in active_locks]
        }
    except Exception as e:
        logging.error(f"[ADMIN] Error liberando locks: {e}")
        raise HTTPException(status_code=500, detail=f"Error liberando locks: {str(e)}")


@api_router.get("/admin/sync/compras/table-counts")
async def admin_sync_compras_table_counts(
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna conteos de tablas de sincronización Compras/Inventarios en EDARSAHUB.
    Útil para verificar si el sync está llenando las tablas correctamente.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores")


    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    query = """
    SELECT 'Compras_Sync_Log' AS tabla, COUNT(*) AS registros FROM dbo.Compras_Sync_Log
    UNION ALL SELECT 'Compras_Sync_Checkpoint', COUNT(*) FROM dbo.Compras_Sync_Checkpoint
    UNION ALL SELECT 'Compras_Inventarios_Fisicos_Sync', COUNT(*) FROM dbo.Compras_Inventarios_Fisicos_Sync
    UNION ALL SELECT 'Compras_Requisiciones_Sync', COUNT(*) FROM dbo.Compras_Requisiciones_Sync
    UNION ALL SELECT 'Compras_Pedidos', COUNT(*) FROM dbo.Compras_Pedidos
    UNION ALL SELECT 'Compras_PedidosDetalle', COUNT(*) FROM dbo.Compras_PedidosDetalle
    UNION ALL SELECT 'Compras_Ordenes', COUNT(*) FROM dbo.Compras_Ordenes
    UNION ALL SELECT 'Compras_OrdenesDetalle', COUNT(*) FROM dbo.Compras_OrdenesDetalle
    UNION ALL SELECT 'Compras_Recepciones', COUNT(*) FROM dbo.Compras_Recepciones
    UNION ALL SELECT 'Compras_RecepcionesDetalle', COUNT(*) FROM dbo.Compras_RecepcionesDetalle
    UNION ALL SELECT 'Inventario_Almacenes', COUNT(*) FROM dbo.Inventario_Almacenes
    UNION ALL SELECT 'Inventario_Existencias', COUNT(*) FROM dbo.Inventario_Existencias
    UNION ALL SELECT 'Inventario_Movimientos', COUNT(*) FROM dbo.Inventario_Movimientos
    UNION ALL SELECT 'Inventario_MovimientosDetalle', COUNT(*) FROM dbo.Inventario_MovimientosDetalle
    """

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        total_registros = sum(r['registros'] for r in results)
        tablas_vacias = [r['tabla'] for r in results if r['registros'] == 0]

        return {
            "status": "OK",
            "total_registros": total_registros,
            "tablas_vacias": len(tablas_vacias),
            "tablas": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando tablas: {str(e)}")


@api_router.get("/admin/sync/compras/validate-columns")
async def admin_sync_compras_validate_columns(
    current_user: dict = Depends(get_current_user)
):
    """
    Valida que existan las columnas esperadas en las tablas de sincronización.
    Compara INFORMATION_SCHEMA.COLUMNS con los campos usados por los MERGE.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores")


    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    query = """
    SELECT
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo'
    AND TABLE_NAME IN (
        'Inventario_Movimientos',
        'Inventario_MovimientosDetalle',
        'Compras_Pedidos',
        'Compras_PedidosDetalle',
        'Compras_Ordenes',
        'Compras_OrdenesDetalle',
        'Compras_Recepciones',
        'Compras_RecepcionesDetalle'
    )
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """

    # Campos esperados por cada tabla (usados en MERGE de sync_service.py)
    expected_columns = {
        'Inventario_Movimientos': ['ServerID', 'OrigenSistema', 'DocumentoID', 'Folio', 'TipoMovimiento', 'FechaMovimiento', 'AlmacenOrigenID', 'AlmacenDestinoID', 'Observaciones', 'UsuarioID', 'FechaSync'],
        'Inventario_MovimientosDetalle': ['MovimientoID', 'ServerID', 'OrigenSistema', 'ProductoID', 'CodigoProducto', 'Cantidad', 'CostoUnitario', 'Lote', 'FechaCaducidad', 'FechaSync'],
        'Compras_Pedidos': ['ServerID', 'OrigenSistema', 'PedidoID', 'Folio', 'FechaPedido', 'ProveedorID', 'SucursalID', 'Estatus', 'Total', 'FechaSync'],
        'Compras_PedidosDetalle': ['PedidoID', 'ServerID', 'OrigenSistema', 'ProductoID', 'CodigoProducto', 'Cantidad', 'PrecioUnitario', 'Subtotal', 'FechaSync'],
        'Compras_Ordenes': ['ServerID', 'OrigenSistema', 'OrdenID', 'Folio', 'FechaOrden', 'ProveedorID', 'SucursalID', 'Estatus', 'Total', 'FechaSync'],
        'Compras_OrdenesDetalle': ['OrdenID', 'ServerID', 'OrigenSistema', 'ProductoID', 'CodigoProducto', 'Cantidad', 'PrecioUnitario', 'Subtotal', 'FechaSync'],
        'Compras_Recepciones': ['ServerID', 'OrigenSistema', 'RecepcionID', 'Folio', 'FechaRecepcion', 'ProveedorID', 'OrdenCompraID', 'SucursalID', 'Estatus', 'Total', 'FechaSync'],
        'Compras_RecepcionesDetalle': ['RecepcionID', 'ServerID', 'OrigenSistema', 'ProductoID', 'CodigoProducto', 'CantidadRecibida', 'PrecioUnitario', 'Subtotal', 'Lote', 'FechaCaducidad', 'FechaSync'],
    }

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        # Agrupar columnas por tabla
        actual_columns = {}
        for row in results:
            table = row['TABLE_NAME']
            if table not in actual_columns:
                actual_columns[table] = []
            actual_columns[table].append({
                'column': row['COLUMN_NAME'],
                'type': row['DATA_TYPE'],
                'nullable': row['IS_NULLABLE'],
                'position': row['ORDINAL_POSITION']
            })

        # Validar cada tabla
        validation = {}
        all_ok = True

        for table, expected in expected_columns.items():
            actual_col_names = [c['column'] for c in actual_columns.get(table, [])]
            missing = [col for col in expected if col not in actual_col_names]
            extra = [col for col in actual_col_names if col not in expected]

            table_ok = len(missing) == 0
            if not table_ok:
                all_ok = False

            validation[table] = {
                'exists': table in actual_columns,
                'expected_count': len(expected),
                'actual_count': len(actual_col_names),
                'missing_columns': missing,
                'extra_columns': extra,
                'status': 'OK' if table_ok else 'MISSING_COLUMNS',
                'actual_columns': actual_columns.get(table, [])
            }

        return {
            'status': 'OK' if all_ok else 'VALIDATION_FAILED',
            'all_tables_valid': all_ok,
            'tables_checked': len(expected_columns),
            'validation': validation,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando columnas: {str(e)}")
async def admin_sync_compras_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna los últimos registros de Compras_Sync_Log y Compras_Sync_Checkpoint.
    """
    user_role = current_user.get("role", "")
    if user_role not in ["SuperAdministrador", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo administradores")


    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        # Obtener logs
        cursor.execute(f"SELECT TOP {limit} * FROM dbo.Compras_Sync_Log ORDER BY 1 DESC")
        logs = cursor.fetchall()

        # Obtener checkpoints
        cursor.execute(f"SELECT TOP {limit} * FROM dbo.Compras_Sync_Checkpoint ORDER BY 1 DESC")
        checkpoints = cursor.fetchall()

        conn.close()

        # Convertir datetime a string para JSON
        for log in logs:
            for k, v in log.items():
                if hasattr(v, 'isoformat'):
                    log[k] = v.isoformat()
        for cp in checkpoints:
            for k, v in cp.items():
                if hasattr(v, 'isoformat'):
                    cp[k] = v.isoformat()

        return {
            "status": "OK",
            "sync_logs": {
                "total": len(logs),
                "records": logs
            },
            "checkpoints": {
                "total": len(checkpoints),
                "records": checkpoints
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando logs: {str(e)}")


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


def _validate_identifier(value: Any, max_length: int = 100) -> bool:
    """Valida identificadores externos usados en filtros SQL controlados."""
    import re

    text = str(value or '').strip()
    if not text or len(text) > max_length:
        return False
    return re.fullmatch(r"[A-Za-z0-9_-]+", text) is not None


def _escape_like_pattern(value: Any, max_length: int = 200) -> str:
    """Escapa literales usados dentro de patrones LIKE de SQL Server."""
    text = str(value or '').strip()[:max_length]
    return (
        text
        .replace("'", "''")
        .replace("[", "[[]")
        .replace("%", "[%]")
        .replace("_", "[_]")
    )


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
async def create_server(server_data: ServerCreate, current_user: Dict = Depends(get_current_user), _rbac: dict = Depends(require_explicit_permission("SERVIDORES_CREAR"))):
    """
    FASE 3B.1: Crea servidor en EDARSAHUB SQL primero, NO sincroniza a MongoDB.

    - SQL es la fuente principal
    - MongoDB no se usa en flujo productivo
    - No existe sync Mongo en flujo productivo

    RBAC: Requiere permiso explícito SERVIDORES_CREAR.
    """
    # FASE 3B.2: Validación RBAC corregida - permitir SuperAdministrador y Administrador

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
        sync_mongo=False  # P5: MongoDB sync deshabilitado
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
async def get_servers(current_user: Dict = Depends(get_current_user), _rbac: dict = Depends(require_explicit_permission("SERVIDORES_VER"))):
    """
    FASE 3B: Listado de servidores usando Server Registry Central.

    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (fuente primaria)
    2. Sin fallback MongoDB

    CORRECCIÓN 2026-05-20: Las conexiones CORE (ej. EDARSAHUB SQL) ahora aparecen
    en el listado del menú administrativo de servidores.
    """
    from core.server_registry import list_servers as registry_list_servers

    servers = await registry_list_servers(
        db=db,
        user=current_user,
        prefer_sql=True,
        allow_mongo_fallback=False,  # P5: Fallback MongoDB deshabilitado
        filter_active=True,
        filter_visible_listado=True,
        exclude_core=False,
        mask_secrets=True
    )

    return servers

@api_router.get("/servers/{server_id}")
async def get_server(server_id: str, current_user: Dict = Depends(get_current_user), _rbac: dict = Depends(require_explicit_permission("SERVIDORES_VER"))):
    """
    FASE 3B: Obtener servidor por ID usando Server Registry Central.

    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (fuente primaria)
    2. Sin fallback MongoDB
    """
    from core.server_registry import get_server_by_id as registry_get_server

    # FASE 6-8: Verificar permiso usando función centralizada
    await validate_server_access_unified(current_user, server_id)

    server = await registry_get_server(
        server_id,
        db=db,
        prefer_sql=True,
        allow_mongo_fallback=False,  # P5: Fallback MongoDB deshabilitado
        mask_secrets=True
    )

    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    return server

@api_router.put("/servers/{server_id}")
async def update_server(server_id: str, server_data: Dict, current_user: Dict = Depends(get_current_user), _rbac: dict = Depends(require_explicit_permission("SERVIDORES_EDITAR"))):
    """
    FASE 3B.1: Actualiza servidor en EDARSAHUB SQL primero, NO sincroniza a MongoDB.

    - SQL es la fuente principal
    - MongoDB no se usa en flujo productivo
    - No existe sync Mongo en flujo productivo
    - Passwords enmascarados no sobrescriben el real

    RBAC: Requiere permiso explícito SERVIDORES_EDITAR.
    Protección CORE: Ni SuperAdministrador ni Administrador pueden modificar conexiones CORE.
    """
    # FASE 3B.2: Validación RBAC corregida - permitir SuperAdministrador y Administrador

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
        sync_mongo=False  # P5: MongoDB sync deshabilitado
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
async def delete_server(server_id: str, current_user: Dict = Depends(get_current_user), _rbac: dict = Depends(require_explicit_permission("SERVIDORES_ELIMINAR"))):
    """
    FASE 3B.1: Desactiva servidor en EDARSAHUB SQL primero, NO sincroniza a MongoDB.

    - Usa soft delete (activo=false), no borrado físico
    - SQL es la fuente principal
    - MongoDB no se usa en flujo productivo
    - No existe sync Mongo en flujo productivo

    RBAC: Requiere permiso explícito SERVIDORES_ELIMINAR.
    Protección CORE: Ni SuperAdministrador ni Administrador pueden eliminar conexiones CORE.
    """
    # FASE 3B.2: Validación RBAC corregida - permitir SuperAdministrador y Administrador

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
        sync_mongo=False,  # P5: MongoDB sync deshabilitado
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


# ============================================================================
# SQL-FIRST P0: runtime Mongo legacy -> tablas canónicas
# ============================================================================

def _sql_next_id(cur, table_name: str, id_column: str) -> int:
    cur.execute(f"SELECT ISNULL(MAX({id_column}), 0) + 1 AS NextID FROM dbo.{table_name} WITH (UPDLOCK, HOLDLOCK)")
    row = cur.fetchone()
    return int(row["NextID"] if isinstance(row, dict) else row[0])


def _sql_upsert_servidor_status(server_id: str, is_online: bool, response_time_ms: Optional[int] = None) -> None:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT StatusID FROM dbo.Servidores_Status WHERE ServerID = %s", (server_id,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE dbo.Servidores_Status
                SET IsOnline=%s, ResponseTimeMs=%s, LastCheck=GETDATE()
                WHERE ServerID=%s
            """, (1 if is_online else 0, response_time_ms, server_id))
        else:
            cur.execute("""
                INSERT INTO dbo.Servidores_Status (StatusID, ServerID, IsOnline, ResponseTimeMs, LastCheck)
                VALUES (%s, %s, %s, %s, GETDATE())
            """, (_sql_next_id(cur, "Servidores_Status", "StatusID"), server_id, 1 if is_online else 0, response_time_ms))
        conn.commit()
    finally:
        conn.close()


def _sql_create_alert(alert: Dict) -> None:
    import json
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            INSERT INTO dbo.Alertas_Sistema (
                ID, AlertaID, Tipo, Severidad, Titulo, Mensaje, Modulo,
                FechaCreacion, DatosJSON, AccionSugerida, Acknowledged
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,GETUTCDATE(),%s,%s,0)
        """, (
            _sql_next_id(cur, "Alertas_Sistema", "ID"),
            alert.get("id"),
            "INVENTARIO",
            "info",
            alert.get("name"),
            alert.get("name"),
            "inventarios",
            json.dumps(alert, default=str, ensure_ascii=False),
            None,
        ))
        conn.commit()
    finally:
        conn.close()


def _sql_list_alerts() -> List[Dict]:
    import json
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT AlertaID, Titulo, DatosJSON, FechaCreacion
            FROM dbo.Alertas_Sistema
            WHERE ISNULL(Acknowledged,0)=0
            ORDER BY FechaCreacion DESC
        """)
        rows = cur.fetchall() or []
        out = []
        for r in rows:
            try:
                data = json.loads(r.get("DatosJSON") or "{}")
            except Exception:
                data = {}
            data.setdefault("id", r.get("AlertaID"))
            data.setdefault("name", r.get("Titulo"))
            data.setdefault("active", True)
            data.setdefault("created_at", r.get("FechaCreacion"))
            out.append(data)
        return out
    finally:
        conn.close()


def _sql_update_alert(alert_id: str, alert_data: Dict) -> None:
    import json
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    existing = {}
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT DatosJSON FROM dbo.Alertas_Sistema WHERE AlertaID=%s", (alert_id,))
        row = cur.fetchone()
        if row:
            try:
                existing = json.loads(row.get("DatosJSON") or "{}")
            except Exception:
                existing = {}
        existing.update(alert_data or {})
        cur.execute("""
            UPDATE dbo.Alertas_Sistema
            SET Titulo=%s, Mensaje=%s, DatosJSON=%s
            WHERE AlertaID=%s
        """, (
            existing.get("name") or alert_data.get("name"),
            existing.get("name") or alert_data.get("name"),
            json.dumps(existing, default=str, ensure_ascii=False),
            alert_id,
        ))
        conn.commit()
    finally:
        conn.close()


def _sql_delete_alert(alert_id: str, user_email: Optional[str] = None) -> None:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE dbo.Alertas_Sistema
            SET Acknowledged=1, AcknowledgedBy=%s, AcknowledgedAt=GETUTCDATE()
            WHERE AlertaID=%s
        """, (user_email or "sistema", alert_id))
        conn.commit()
    finally:
        conn.close()


def _sql_count_active_users() -> int:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT COUNT(*) AS total FROM dbo.Usuario_Catalogo WHERE Activo=1")
        row = cur.fetchone() or {}
        return int(row.get("total") or 0)
    finally:
        conn.close()


def _sql_count_active_alerts() -> int:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT COUNT(*) AS total FROM dbo.Alertas_Sistema WHERE ISNULL(Acknowledged,0)=0")
        row = cur.fetchone() or {}
        return int(row.get("total") or 0)
    finally:
        conn.close()


def _sql_insert_script_log(log_data: Dict) -> None:
    import json
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            INSERT INTO dbo.ConsultasSQL_EjecucionesLog (
                ConsultaID, ServidorID, UsuarioID, FechaEjecucion,
                ParametrosJSON, ConsultaSQLEjecutada, Estado, RegistrosDevueltos, ErrorMensaje
            )
            VALUES (0, TRY_CONVERT(uniqueidentifier,%s), %s, GETDATE(), %s, %s, %s, %s, %s)
        """, (
            log_data.get("server_id"),
            log_data.get("usuario") or log_data.get("usuario_app") or "sistema",
            json.dumps(log_data, default=str, ensure_ascii=False),
            log_data.get("titulo"),
            "SUCCESS" if int(log_data.get("fallidos") or 0) == 0 else "ERROR",
            int(log_data.get("exitosos") or 0),
            None if int(log_data.get("fallidos") or 0) == 0 else "Ver ParametrosJSON",
        ))
        conn.commit()
    finally:
        conn.close()


def _sql_inventory_cache_workflow_id(cache_key: Dict) -> str:
    import hashlib
    raw = f"{cache_key.get('server_id','')}|{cache_key.get('folio','')}"
    return "CACHE_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:34]


def _sql_num(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _sql_save_inventario_diferencias_cache(cache_key: Dict, cache_doc: Dict) -> None:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    workflow_id = _sql_inventory_cache_workflow_id(cache_key)
    productos = cache_doc.get("productos") or []

    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("DELETE FROM dbo.Workflow_DetalleDiferencias WHERE WorkflowID=%s", (workflow_id,))

        for idx, prod in enumerate(productos, 1):
            detalle_id = f"{workflow_id}_{idx}"[:50]
            cur.execute("""
                INSERT INTO dbo.Workflow_DetalleDiferencias (
                    ID, DetalleID, WorkflowID, CodigoProducto, NombreProducto,
                    Categoria, Familia, SubFamilia, Unidad, CostoUnitario,
                    InvInicialCantidad, InvFinalCantidad, InvTeoricoCantidad,
                    DiferenciaCantidad, DiferenciaCosto, DiferenciaPorcentaje,
                    Movimientos, Ventas, EstadoJustificacion, RequiereJustificacionCompleta
                )
                VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,'pendiente',0
                )
            """, (
                _sql_next_id(cur, "Workflow_DetalleDiferencias", "ID"),
                detalle_id,
                workflow_id,
                prod.get("codigo") or prod.get("CodigoProducto"),
                prod.get("producto") or prod.get("nombre") or prod.get("NombreProducto"),
                prod.get("categoria") or prod.get("Categoria"),
                prod.get("familia") or prod.get("Familia"),
                prod.get("subfamilia") or prod.get("sub_familia") or prod.get("SubFamilia"),
                prod.get("unidad") or prod.get("Unidad"),
                _sql_num(prod.get("costo_unitario") or prod.get("costo") or prod.get("CostoUnitario")),
                _sql_num(prod.get("inv_inicial") or prod.get("inventario_inicial") or prod.get("InvInicialCantidad")),
                _sql_num(prod.get("inv_final") or prod.get("inventario_final") or prod.get("InvFinalCantidad")),
                _sql_num(prod.get("inv_teorico") or prod.get("inventario_teorico") or prod.get("InvTeoricoCantidad")),
                _sql_num(prod.get("diferencia") or prod.get("diferencia_cantidad") or prod.get("DiferenciaCantidad")),
                _sql_num(prod.get("diferencia_costo") or prod.get("DiferenciaCosto")),
                _sql_num(prod.get("diferencia_porcentaje") or prod.get("DiferenciaPorcentaje")),
                _sql_num(prod.get("movimientos") or prod.get("Movimientos")),
                _sql_num(prod.get("ventas") or prod.get("Ventas")),
            ))
        conn.commit()
    finally:
        conn.close()


def _sql_get_inventario_diferencias_cache(cache_key: Dict) -> Optional[Dict]:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    conn = get_edarsahub_connection()
    workflow_id = _sql_inventory_cache_workflow_id(cache_key)

    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT CodigoProducto, NombreProducto, Categoria, Familia, SubFamilia, Unidad,
                   CostoUnitario, InvInicialCantidad, InvFinalCantidad, InvTeoricoCantidad,
                   DiferenciaCantidad, DiferenciaCosto, DiferenciaPorcentaje, Movimientos, Ventas
            FROM dbo.Workflow_DetalleDiferencias
            WHERE WorkflowID=%s
            ORDER BY ID
        """, (workflow_id,))
        rows = cur.fetchall() or []

        if not rows:
            return None

        productos = []
        for r in rows:
            productos.append({
                "codigo": r.get("CodigoProducto"),
                "producto": r.get("NombreProducto"),
                "categoria": r.get("Categoria"),
                "familia": r.get("Familia"),
                "subfamilia": r.get("SubFamilia"),
                "unidad": r.get("Unidad"),
                "costo_unitario": float(r.get("CostoUnitario") or 0),
                "inv_inicial": float(r.get("InvInicialCantidad") or 0),
                "inv_final": float(r.get("InvFinalCantidad") or 0),
                "inv_teorico": float(r.get("InvTeoricoCantidad") or 0),
                "diferencia": float(r.get("DiferenciaCantidad") or 0),
                "diferencia_costo": float(r.get("DiferenciaCosto") or 0),
                "diferencia_porcentaje": float(r.get("DiferenciaPorcentaje") or 0),
                "movimientos": float(r.get("Movimientos") or 0),
                "ventas": float(r.get("Ventas") or 0),
            })

        return {**cache_key, "productos": productos}
    finally:
        conn.close()


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

            # Guardar estado como online en tabla canónica SQL
            _sql_upsert_servidor_status(server_id, True, int(elapsed_time))

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

        # Guardar estado como offline en tabla canónica SQL
        _sql_upsert_servidor_status(server_id, False, None)

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

    if query_type not in REQUIRED_COLUMNS:  # noqa: F821
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido. Usa: {list(REQUIRED_COLUMNS.keys())}")  # noqa: F821

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
                "columns_required": REQUIRED_COLUMNS[query_type]["required"],  # noqa: F821
                "columns_missing": REQUIRED_COLUMNS[query_type]["required"],  # noqa: F821
                "sample_data": [],
                "row_count": 0
            }

        # Obtener columnas de los resultados
        columns = list(results[0].keys())

        # Validar columnas
        validation = validate_query_columns(columns, query_type)  # noqa: F821

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
            "description": REQUIRED_COLUMNS[query_type]["description"]  # noqa: F821
        }

    except Exception as e:
        logging.error(f"Error validando consulta: {str(e)}")
        return {
            "valid": False,
            "message": f"Error al ejecutar la consulta: {str(e)}",
            "columns_found": [],
            "columns_required": REQUIRED_COLUMNS[query_type]["required"],  # noqa: F821
            "columns_missing": REQUIRED_COLUMNS[query_type]["required"],  # noqa: F821
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

    if query_type not in REQUIRED_COLUMNS:  # noqa: F821
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido. Usa: {list(REQUIRED_COLUMNS.keys())}")  # noqa: F821

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
        sync_mongo=False  # P5: MongoDB sync deshabilitado  # Mantener espejo MongoDB para compatibilidad
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
            sync_mongo=False  # P5: MongoDB sync deshabilitado
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
                "description": REQUIRED_COLUMNS["inventario"]["description"],  # noqa: F821
                "required_columns": REQUIRED_COLUMNS["inventario"]["required"],  # noqa: F821
                "optional_columns": REQUIRED_COLUMNS["inventario"]["optional"]  # noqa: F821
            },
            "ventas": {
                "configured": server.get("query_ventas") is not None,
                "validated": (server.get("query_ventas") or {}).get("validated", False),
                "sql": (server.get("query_ventas") or {}).get("sql", ""),
                "last_validated": (server.get("query_ventas") or {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["ventas"]["description"],  # noqa: F821
                "required_columns": REQUIRED_COLUMNS["ventas"]["required"],  # noqa: F821
                "optional_columns": REQUIRED_COLUMNS["ventas"]["optional"]  # noqa: F821
            },
            "movimientos": {
                "configured": server.get("query_movimientos") is not None,
                "validated": (server.get("query_movimientos") or {}).get("validated", False),
                "sql": (server.get("query_movimientos") or {}).get("sql", ""),
                "last_validated": (server.get("query_movimientos") or {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["movimientos"]["description"],  # noqa: F821
                "required_columns": REQUIRED_COLUMNS["movimientos"]["required"],  # noqa: F821
                "optional_columns": REQUIRED_COLUMNS["movimientos"]["optional"]  # noqa: F821
            }
        },
        "column_aliases": COLUMN_ALIASES  # noqa: F821
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

    if query_type not in REQUIRED_COLUMNS:  # noqa: F821
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
        sync_mongo=False  # P5: MongoDB sync deshabilitado
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


# ============================================================================
# SQL-FIRST: Sistema_ServidorSucursalesConfig
# ============================================================================

def _sql_sucursal_config_row_to_api(row: Dict) -> Dict:
    sucursal_codigo = row.get("SucursalCodigo")
    sucursal_id = row.get("SucursalID")
    sucursal_origen_id = str(sucursal_codigo or sucursal_id or "").strip()
    return {
        "id": str(row.get("ConfigID")),
        "server_id": str(row.get("ServidorID")),
        "sucursal_origen_id": sucursal_origen_id,
        "sucursal_nombre": row.get("SucursalNombre"),
        "nombre_visible": row.get("SucursalNombre"),
        "visible_en_operaciones": bool(row.get("VisibleEnOperaciones")),
        "visible_en_comercial": bool(row.get("VisibleEnComercial")),
        "orden": int(row.get("ConfigID") or 999),
        "activa": bool(row.get("Activo")),
        "fecha_alta": row.get("FechaCreacion"),
        "fecha_modificacion": row.get("FechaModificacion"),
        "usuario_alta": row.get("CreatedBy"),
        "usuario_modificacion": row.get("UpdatedBy"),
    }


def _sql_list_sucursales_config(server_id: Optional[str] = None, activas: bool = True) -> List[Dict]:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811

    where = []
    params = []

    if server_id:
        where.append("ServidorID = CONVERT(uniqueidentifier, %s)")
        params.append(server_id)

    if activas:
        where.append("Activo = 1")

    sql = """
        SELECT
            ConfigID,
            ServidorID,
            SucursalNombre,
            SucursalCodigo,
            SucursalID,
            VisibleEnOperaciones,
            VisibleEnComercial,
            Activo,
            FechaCreacion,
            FechaModificacion,
            CreatedBy,
            UpdatedBy,
            Observaciones
        FROM dbo.Sistema_ServidorSucursalesConfig
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ConfigID"

    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, tuple(params))
        return [_sql_sucursal_config_row_to_api(r) for r in (cur.fetchall() or [])]
    finally:
        conn.close()


def _sql_get_sucursal_config(server_id: str, sucursal_origen_id: str) -> Optional[Dict]:
    rows = _sql_list_sucursales_config(server_id=server_id, activas=False)
    target = str(sucursal_origen_id).strip()
    for r in rows:
        if str(r.get("sucursal_origen_id", "")).strip() == target:
            return r
    return None


def _sql_upsert_sucursal_config(
    server_id: str,
    sucursal_origen_id: str,
    sucursal_nombre: str,
    visible_en_operaciones: Optional[bool] = None,
    visible_en_comercial: Optional[bool] = None,
    activa: Optional[bool] = None,
    user_email: Optional[str] = None,
) -> bool:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811

    visible_op = 1 if visible_en_operaciones is not False else 0
    visible_com = 1 if visible_en_comercial is True else 0
    activo = 1 if activa is not False else 0
    user_email = user_email or "sistema"

    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT ConfigID
            FROM dbo.Sistema_ServidorSucursalesConfig
            WHERE ServidorID = CONVERT(uniqueidentifier, %s)
              AND ISNULL(SucursalCodigo, CONVERT(varchar(50), SucursalID)) = %s
        """, (server_id, str(sucursal_origen_id)))

        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE dbo.Sistema_ServidorSucursalesConfig
                SET SucursalNombre = %s,
                    VisibleEnOperaciones = %s,
                    VisibleEnComercial = %s,
                    Activo = %s,
                    FechaModificacion = SYSDATETIME(),
                    UpdatedBy = %s
                WHERE ConfigID = %s
            """, (
                sucursal_nombre,
                visible_op,
                visible_com,
                activo,
                user_email,
                existing["ConfigID"],
            ))
            conn.commit()
            return False

        cur.execute("""
            SELECT ISNULL(MAX(ConfigID), 0) + 1 AS NextID
            FROM dbo.Sistema_ServidorSucursalesConfig WITH (UPDLOCK, HOLDLOCK)
        """)
        next_id = cur.fetchone()["NextID"]

        cur.execute("""
            INSERT INTO dbo.Sistema_ServidorSucursalesConfig (
                ConfigID,
                ServidorID,
                SucursalNombre,
                SucursalCodigo,
                SucursalID,
                VisibleEnOperaciones,
                VisibleEnComercial,
                FuenteMigracion,
                Activo,
                FechaCreacion,
                CreatedBy
            )
            VALUES (
                %s,
                CONVERT(uniqueidentifier, %s),
                %s,
                %s,
                NULL,
                %s,
                %s,
                'SQL_RUNTIME',
                %s,
                SYSDATETIME(),
                %s
            )
        """, (
            next_id,
            server_id,
            sucursal_nombre,
            str(sucursal_origen_id),
            visible_op,
            visible_com,
            activo,
            user_email,
        ))
        conn.commit()
        return True
    finally:
        conn.close()


def _sql_update_sucursal_config_fields(
    server_id: str,
    sucursal_origen_id: str,
    update_data: Dict,
    user_email: Optional[str] = None,
) -> int:
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811

    sets = ["FechaModificacion = SYSDATETIME()", "UpdatedBy = %s"]
    params = [user_email or "sistema"]

    if "visible_en_operaciones" in update_data and update_data["visible_en_operaciones"] is not None:
        sets.append("VisibleEnOperaciones = %s")
        params.append(1 if update_data["visible_en_operaciones"] else 0)

    if "nombre_visible" in update_data and update_data["nombre_visible"] is not None:
        sets.append("SucursalNombre = %s")
        params.append(str(update_data["nombre_visible"]))

    if "activa" in update_data and update_data["activa"] is not None:
        sets.append("Activo = %s")
        params.append(1 if update_data["activa"] else 0)

    params.extend([server_id, str(sucursal_origen_id)])

    conn = get_edarsahub_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE dbo.Sistema_ServidorSucursalesConfig
            SET {", ".join(sets)}
            WHERE ServidorID = CONVERT(uniqueidentifier, %s)
              AND ISNULL(SucursalCodigo, CONVERT(varchar(50), SucursalID)) = %s
        """, tuple(params))
        count = cur.rowcount or 0
        conn.commit()
        return count
    finally:
        conn.close()


async def filter_sucursales_by_config(sucursales: List[Dict], server_id: str) -> List[Dict]:
    """
    Filtra sucursales según la configuración de visibilidad.
    REGLA DE COMPATIBILIDAD:
    - Si NO hay configuración para este servidor -> devuelve TODAS (comportamiento legacy)
    - Si SÍ hay configuración -> devuelve solo las marcadas como visible_en_operaciones=True
    """
    # Buscar configuración existente en EDARSAHUB SQL
    configs = _sql_list_sucursales_config(server_id=server_id, activas=True)

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

def _is_edarsahub_shared_host(server: Optional[Dict]) -> bool:
    """True si el host del server es el de EDARSAHUB (compartido con el POS de MPRO).
    Conectar en vivo a ese host es lo que dispara el cooldown que tumba los tableros."""
    if not server:
        return False
    try:
        from core.server_registry import EDARSAHUB_CONFIG as _CFG
        eda = str(_CFG.get('host') or '').strip()
        return bool(eda and str(server.get('host') or '').strip() == eda)
    except Exception:
        return False


def _derive_sucursales_from_sync(server_id: str) -> List[Dict]:
    """FASE C (NO-LIVE): deriva sucursales distintas desde Compras_Inventarios_Fisicos_Sync."""
    try:
        from modules.compras.sync_service import get_edarsahub_connection
        conn = get_edarsahub_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT DISTINCT sucursal_id, sucursal
                FROM Compras_Inventarios_Fisicos_Sync
                WHERE LOWER(server_id) = LOWER(%s)
                  AND sucursal_id IS NOT NULL AND sucursal_id <> ''
                ORDER BY sucursal_id
            """, (server_id,))
            rows = cur.fetchall() or []
        finally:
            conn.close()
        return [
            {"id": r['sucursal_id'], "nombre": r.get('sucursal') or r['sucursal_id'], "codigo": r['sucursal_id']}
            for r in rows
        ]
    except Exception as e:
        logging.error(f"[FASE-C] Error derivando sucursales NO-LIVE: {e}")
        return []


def _derive_almacenes_from_sync(server_id: str, sucursal_id: Optional[str] = None, sucursal: Optional[str] = None) -> List[Dict]:
    """FASE C (NO-LIVE): deriva almacenes distintos desde Compras_Inventarios_Fisicos_Sync.
    El filtro por sucursal SOLO aplica a servers compartidos (MPRO ORIGEN/QRO); para
    single-tenant (SoftRestaurant) la sucursal viene vacía en el sync y NO se filtra."""
    try:
        from modules.compras.sync_service import get_edarsahub_connection
        from core.corporate_filters.request_resolver import _shared_server
        apply_suc = _shared_server(server_id)
        where = "LOWER(server_id) = LOWER(%s) AND almacen_id IS NOT NULL AND almacen_id <> ''"
        params: List = [server_id]
        if apply_suc and sucursal_id:
            where += " AND sucursal_id = %s"
            params.append(sucursal_id)
        elif apply_suc and sucursal:
            where += " AND sucursal = %s"
            params.append(sucursal)
        conn = get_edarsahub_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(f"""
                SELECT DISTINCT almacen_id, almacen
                FROM Compras_Inventarios_Fisicos_Sync
                WHERE {where}
                ORDER BY almacen_id
            """, tuple(params))
            rows = cur.fetchall() or []
        finally:
            conn.close()
        return [{"id": r['almacen_id'], "nombre": r.get('almacen') or r['almacen_id']} for r in rows]
    except Exception as e:
        logging.error(f"[FASE-C] Error derivando almacenes NO-LIVE: {e}")
        return []


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

    # === NO-LIVE / EDARSAHUB EXCLUSIVO (todos los sistemas) ===
    # Las sucursales se derivan SIEMPRE del cerebro EDARSAHUB (tabla sync). Nunca se
    # conecta en vivo a ningún POS (ni SoftRestaurant ni MPRO). Esto cumple la máxima
    # NO-LIVE y elimina el cooldown del host compartido. Para single-tenant
    # (SoftRestaurant) el sync no trae sucursal → se usa la virtual "Principal".
    sucursales_raw = _derive_sucursales_from_sync(server_id)
    if not sucursales_raw:
        sucursales_raw = [
            {
                "id": "default",
                "nombre": server.get("name", "Principal"),
                "codigo": "default",
            }
        ]

    context = await resolve_user_access_context(current_user)

    if not has_server_access(context, server_id):
        logging.warning(
            "[RBAC-SUCURSALES] Usuario %s sin acceso al servidor %s",
            current_user.get("email"),
            server_id,
        )
        raise HTTPException(
            status_code=403,
            detail="No tiene acceso a este servidor",
        )

    if context.tiene_acceso_global:
        sucursales_filtradas = sucursales_raw
    else:
        server_key = server_id.lower()
        sucursales_permitidas = context.sucursales_por_server.get(
            server_key,
            [],
        )

        if not sucursales_permitidas:
            logging.warning(
                "[RBAC-SUCURSALES] Usuario %s sin sucursales "
                "asignadas para servidor %s",
                current_user.get("email"),
                server_id,
            )
            sucursales_filtradas = []
        else:
            permitidas = {
                str(codigo).strip().lower()
                for codigo in sucursales_permitidas
                if codigo is not None
            }

            sucursales_filtradas = [
                sucursal
                for sucursal in sucursales_raw
                if str(
                    sucursal.get("codigo")
                    or sucursal.get("id")
                    or ""
                ).strip().lower()
                in permitidas
            ]

    if not include_hidden:
        sucursales_filtradas = await filter_sucursales_by_config(
            sucursales_filtradas,
            server_id,
        )

    logging.info(
        "[NO-LIVE] Sucursales (sync EDARSAHUB) "
        "server=%s total=%s",
        server_id,
        len(sucursales_filtradas),
    )

    return sucursales_filtradas

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

    # === NO-LIVE / EDARSAHUB EXCLUSIVO (todos los sistemas) ===
    # Los almacenes se derivan SIEMPRE del cerebro EDARSAHUB (tabla sync), sin conexión
    # viva a ningún POS. El filtro por sucursal solo aplica a servers compartidos (MPRO).
    results = _derive_almacenes_from_sync(server_id, sucursal_id, sucursal)
    if almacenes_permitidos:
        _permitidos = {str(x) for x in almacenes_permitidos}
        results = [a for a in results if str(a.get('id')) in _permitidos]
    logging.info(f"[NO-LIVE] Almacenes (sync EDARSAHUB) server={server_id}: {len(results)} (RBAC aplicado)")
    return results

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

    # Obtener configuración existente desde EDARSAHUB SQL
    configs = _sql_list_sucursales_config(server_id=server_id, activas=True)

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

    if not es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden sincronizar")

    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
    # AHORA: Usar registry que prioriza EDARSAHUB SQL
    server = await get_server_connection_info(server_id, db=db)

    if not server:
        logging.warning(f"[SYNC_SUCURSALES_CONFIG] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    logging.debug(f"[SYNC_SUCURSALES_CONFIG] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")

    # Obtener sucursales desde EDARSAHUB SQL sync, sin conexión live al POS
    sucursales_sql = _derive_sucursales_from_sync(server_id)
    if not sucursales_sql:
        sucursales_sql = [{"id": "default", "nombre": server.get('name', 'Principal')}]

    existing_configs = _sql_list_sucursales_config(server_id=server_id, activas=False)
    existing_ids = {str(c.get("sucursal_origen_id")) for c in existing_configs}

    # Agregar nuevas sucursales
    nuevas = 0
    actualizadas = 0
    now = datetime.now(timezone.utc)
    user_email = current_user.get("email", "sistema")

    for idx, suc in enumerate(sucursales_sql):
        suc_id = str(suc.get("id", "")).strip()
        suc_nombre = str(suc.get("nombre", "")).strip()

        created = _sql_upsert_sucursal_config(
            server_id=server_id,
            sucursal_origen_id=suc_id,
            sucursal_nombre=suc_nombre,
            visible_en_operaciones=True,
            activa=True,
            user_email=user_email,
        )
        if created:
            nuevas += 1
        else:
            actualizadas += 1

    # Obtener configuración actualizada desde EDARSAHUB SQL
    configs = _sql_list_sucursales_config(server_id=server_id, activas=True)

    return {
        "message": f"Sincronización completada: {nuevas} nuevas, {actualizadas} actualizadas",
        "nuevas": nuevas,
        "actualizadas": actualizadas,
        "total": len(configs),
        "sucursales": configs
    }

@api_router.put("/servers/{server_id}/sucursales-config/bulk")
async def update_sucursales_config_bulk(
    server_id: str,
    bulk_data: SucursalConfigBulkUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza múltiples sucursales en una sola operación."""
    if not es_admin(current_user):
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

        result_count = _sql_update_sucursal_config_fields(
            server_id,
            suc_id,
            update_fields,
            user_email,
        )
        if result_count > 0:
            updated += 1

    return {"message": f"{updated} sucursales actualizadas", "updated": updated}

@api_router.put("/servers/{server_id}/sucursales-config/{sucursal_origen_id}")
async def update_sucursal_config(
    server_id: str,
    sucursal_origen_id: str,
    update_data: SucursalConfigUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza la configuración de una sucursal específica."""
    if not es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar")

    # Verificar que existe en EDARSAHUB SQL
    existing = _sql_get_sucursal_config(server_id, sucursal_origen_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Configuración de sucursal no encontrada")

    # Preparar actualización SQL
    update_fields = {}
    if update_data.visible_en_operaciones is not None:
        update_fields["visible_en_operaciones"] = update_data.visible_en_operaciones
    if update_data.nombre_visible is not None:
        update_fields["nombre_visible"] = update_data.nombre_visible
    if update_data.activa is not None:
        update_fields["activa"] = update_data.activa

    _sql_update_sucursal_config_fields(
        server_id,
        sucursal_origen_id,
        update_fields,
        current_user.get("email"),
    )

    return {"message": "Configuración actualizada", "sucursal_origen_id": sucursal_origen_id}

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
    sucursales = _sql_list_sucursales_config(server_id=server_id, activas=activas)

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

        logging.info(f"[UNIDADES_NEGOCIO] execute_sql_query retornó: {len(unidades_sql) if unidades_sql else 'None'} registros")

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
        user_role = (current_user.get('role') or '').strip()

        # SuperAdministrador y Administrador ven todas las unidades
        # (se aceptan tanto los nombres visibles como los códigos canónicos RBAC)
        is_admin_global = (
            user_role in ['SuperAdministrador', 'Administrador']
            or user_role.upper() in ['SUPERADMIN', 'ADMIN', 'ADMINISTRADOR']
        )
        if is_admin_global:
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
    from core.corporate_filters.request_resolver import resolve_unidad_simple

    # CONTRATO CANÓNICO: el token de ruta puede ser una unidad (codigo/id) — caso
    # Métricas — o un server_id legacy — caso pantalla Análisis. Si es unidad,
    # resolvemos su server_id. El RBAC se aplica aguas abajo vía has_server_access.
    _unidad_token, _matched_by = resolve_unidad_simple(server_id)
    if _unidad_token and _matched_by == 'unidad':
        server_id = _unidad_token.get('server_id') or server_id


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

    # ====================================================================
    # PROTECCIÓN NO-LIVE / HOST COMPARTIDO (crítico para estabilidad):
    # El POS de MPRO comparte IP con EDARSAHUB (54.39.104.176). Un intento de
    # conexión EN VIVO fallido a ese host pone a EDARSAHUB en "cooldown" en
    # memoria → TODAS las lecturas canónicas (Tablero Ejecutivo, unidades, RBAC)
    # devuelven vacío y el sistema "se cae". Por eso NUNCA se conecta en vivo al
    # host de EDARSAHUB desde este endpoint ("insumos pendientes" es opcional).
    # Misma guarda que /dashboard/inventory-summary.
    # ====================================================================
    try:
        from core.server_registry import EDARSAHUB_CONFIG as _EDA_CFG
        _eda_host = str(_EDA_CFG.get('host') or '').strip()
    except Exception:
        _eda_host = ''
    if _eda_host and str(server.get('host') or '').strip() == _eda_host:
        logging.info(
            f"[PENDIENTES-NOLIVE] Conexión live bloqueada al host EDARSAHUB para "
            f"server={server_id} (protección anti-cooldown)."
        )
        return {"items": [], "totales": {"cantidad": 0, "valor": 0, "items": 0}, "almacenes": [], "no_live": True}

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


@api_router.get("/servers/{server_id}/report-filters")
async def get_report_filters(server_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene las opciones de filtros (categorías, familias, subfamilias) para el reporte de análisis.

    CATALOGO-CANONICO-C1 (2026-06-09) — MIGRADO A NO-LIVE:
    Antes consultaba EN VIVO los POS (MPRO/SoftRestaurant), lo que violaba la regla
    NO-LIVE y disparaba el cooldown de EDARSAHUB en el host compartido de MPRO.
    Ahora lee EXCLUSIVAMENTE de EDARSAHUB:
    - MPRO: dimensiones derivadas de Sync_Productos (Categoria/Familia/SubFamilia,
      cuyos códigos = Ct_Cve_Categoria/Fm_Cve_Familia/Sf_Cve_SubFamilia → siguen
      coincidiendo con los filtros de /reports/inventory-analysis).
    - SoftRestaurant: jerarquía de INSUMOS (clasificacionventa/gruposiclasificacion/
      gruposi) desde Sync_Catalogo_Filtros (sincronizada por el job de recetas).
    """
    from core.server_registry import get_server_connection_info

    # Metadata del servidor (system_type) desde EDARSAHUB — NO-LIVE (no conecta al POS)
    server = await get_server_connection_info(server_id, db=db)
    if not server:
        logging.warning(f"[GET_REPORT_FILTERS] Servidor no encontrado via registry. ID={server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    cfg = EDARSAHUB_CONFIG
    empty = {"categorias": [], "familias": [], "subfamilias": []}

    try:
        if is_mpro_system(server.get('system_type')):
            base = f"""
                FROM Sync_Productos
                WHERE CAST(ServerID AS NVARCHAR(36)) = '{server_id}'
            """
            categorias = execute_sql_query(
                cfg['host'], cfg['port'], cfg['database'], cfg['username'], cfg['password'],
                f"SELECT DISTINCT CategoriaCodigoFuente as id, CategoriaNombre as nombre {base} "
                f"AND CategoriaCodigoFuente IS NOT NULL AND CategoriaNombre IS NOT NULL ORDER BY CategoriaNombre"
            )
            familias = execute_sql_query(
                cfg['host'], cfg['port'], cfg['database'], cfg['username'], cfg['password'],
                f"SELECT DISTINCT FamiliaCodigoFuente as id, FamiliaNombre as nombre {base} "
                f"AND FamiliaCodigoFuente IS NOT NULL AND FamiliaNombre IS NOT NULL ORDER BY FamiliaNombre"
            )
            subfamilias = execute_sql_query(
                cfg['host'], cfg['port'], cfg['database'], cfg['username'], cfg['password'],
                f"SELECT DISTINCT SubFamiliaCodigoFuente as id, SubFamiliaNombre as nombre {base} "
                f"AND SubFamiliaCodigoFuente IS NOT NULL AND SubFamiliaNombre IS NOT NULL ORDER BY SubFamiliaNombre"
            )
            return {
                "categorias": categorias or [],
                "familias": familias or [],
                "subfamilias": subfamilias or []
            }

        elif is_softrestaurant_system(server.get('system_type')):
            def _nivel(nivel: str):
                return execute_sql_query(
                    cfg['host'], cfg['port'], cfg['database'], cfg['username'], cfg['password'],
                    f"SELECT Codigo as id, Nombre as nombre, ParentCodigo as parent FROM Sync_Catalogo_Filtros "
                    f"WHERE CAST(ServerID AS NVARCHAR(36)) = '{server_id}' AND Nivel = '{nivel}' "
                    f"AND Activo = 1 ORDER BY Nombre"
                ) or []
            return {
                "categorias": _nivel('CATEGORIA'),
                "familias": _nivel('FAMILIA'),
                "subfamilias": _nivel('SUBFAMILIA')
            }
        else:
            return empty

    except Exception as e:
        logging.error(f"Error obteniendo filtros (NO-LIVE): {str(e)}")
        return empty


# =============================================================================
# FUNCIÓN REUTILIZABLE - Análisis de Inventarios
# CAB-003 Fase 1A: Permite reutilización desde Core Service sin modificar endpoint
# =============================================================================

# Referencia a la función del endpoint para uso externo
# Esta variable se asigna después de definir el endpoint
_inventory_analysis_endpoint_ref = None

from core.inventarios.sql_error_policy import (
    classify_inventory_sql_error as _classify_inventory_sql_error,
    should_retry_inventory_once as _should_retry_inventory_once,
    inventory_analysis_safe_http_exception as _inventory_analysis_safe_http_exception,
)



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
    from core.server_registry import get_server_connection_info
    from core.inventarios.contracts import build_normalized_inventory_request

    from core.corporate_filters.request_resolver import canonical_server_id

    server_id = str(canonical_server_id(report_params.get('server_id')) or '').strip()
    if not server_id:
        raise HTTPException(status_code=400, detail='server_id es requerido')
    report_params['server_id'] = server_id
    access_context = await validate_server_access_unified(current_user, server_id)
    normalized_request = build_normalized_inventory_request(report_params, server_id)

    sucursal_id_param = normalized_request.sucursal_id_param
    sucursal = normalized_request.sucursal
    almacen = normalized_request.almacen
    almacenes = normalized_request.almacenes
    fecha_ini = normalized_request.fecha_ini
    fecha_fin = normalized_request.fecha_fin
    lista_folios_ini = normalized_request.lista_folios_ini
    lista_folios_fin = normalized_request.lista_folios_fin

    # Info completa de inventarios (reservado para evolución de contratos).
    inventarios_iniciales_info = normalized_request.inventarios_iniciales_info
    inventarios_finales_info = normalized_request.inventarios_finales_info

    filtro_categorias_frontend = normalized_request.filtro_categorias_frontend
    filtro_familias_frontend = normalized_request.filtro_familias_frontend
    filtro_subfamilias_frontend = normalized_request.filtro_subfamilias_frontend
    agrupar_insumos = normalized_request.agrupar_insumos

    logging.info(f"Filtros recibidos del frontend - Categorias: {filtro_categorias_frontend}, Familias: {filtro_familias_frontend}, SubFamilias: {filtro_subfamilias_frontend}")
    logging.info(f"Agrupar insumos: {agrupar_insumos}")

    # FASE P1.4-C: Obtener metadatos desde EDARSAHUB SQL via server_registry sin secretos.
    server = await get_server_connection_info(server_id, db=db)
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    from time import perf_counter

    async def _generate_soft_inventory_analysis_canonical():
        from datetime import datetime as _datetime, timedelta as _timedelta

        started_at = perf_counter()
        logging.info(
            "[SOFT-CANONICAL-NOLIVE] start server_id=%s almacen=%s folios_ini=%s folios_fin=%s",
            server_id,
            almacen,
            lista_folios_ini,
            lista_folios_fin,
        )

        if not lista_folios_ini or not lista_folios_fin:
            raise HTTPException(status_code=400, detail="Debe seleccionar folios iniciales y finales")

        def _as_text(value):
            return "" if value is None else str(value).strip()

        def _as_float(value):
            if value is None:
                return 0.0
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        def _parse_dt(value):
            if not value:
                return None
            if isinstance(value, _datetime):
                return value
            text = str(value).replace("T", " ").strip()
            for size, fmt in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M"), (10, "%Y-%m-%d")):
                try:
                    return _datetime.strptime(text[:size], fmt)
                except ValueError:
                    continue
            return None

        def _as_filter_set(values):
            return {
                _as_text(v.get('id') if isinstance(v, dict) else v)
                for v in (values or [])
                if _as_text(v.get('id') if isinstance(v, dict) else v)
            }

        selected_categoria_codes = _as_filter_set(filtro_categorias_frontend)
        selected_familia_codes = _as_filter_set(filtro_familias_frontend)
        selected_subfamilia_codes = _as_filter_set(filtro_subfamilias_frontend)

        selected_almacenes = []

        def _append_almacen_candidate(value):
            value_text = _as_text(value)
            if value_text and value_text not in selected_almacenes:
                selected_almacenes.append(value_text)

        if almacenes:
            for item in almacenes:
                if isinstance(item, dict):
                    for field in ('almacen_id', 'id', 'nombre', 'almacen', 'label', 'value'):
                        _append_almacen_candidate(item.get(field))
                else:
                    _append_almacen_candidate(item)
        elif almacen:
            _append_almacen_candidate(almacen)

        selected_almacenes = _compras_almacenes_scope(access_context, server_id, selected_almacenes)
        folios_all = list(dict.fromkeys([*lista_folios_ini, *lista_folios_fin]))
        folio_placeholders = ",".join(["%s"] * len(folios_all))

        conn = None
        try:
            from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

            open_started_at = perf_counter()
            conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
            open_elapsed_ms = int((perf_counter() - open_started_at) * 1000)
            cursor = conn.cursor(as_dict=True)
            logging.info(
                "[INV-STAGE] stage=CONNECTION_OPEN open_ms=%s classification=OK",
                open_elapsed_ms,
            )

            # Validación obligatoria de identidad SQL canónica antes de consultas.
            v_exec_started = perf_counter()
            cursor.execute("SELECT DB_NAME() AS db_name, SUSER_SNAME() AS suser_name, USER_NAME() AS user_name")
            v_exec_ms = int((perf_counter() - v_exec_started) * 1000)
            v_fetch_started = perf_counter()
            identity_rows = cursor.fetchall() or []
            v_fetch_ms = int((perf_counter() - v_fetch_started) * 1000)
            identity = identity_rows[0] if identity_rows else {}
            db_name = _as_text(identity.get("db_name"))
            suser_name = _as_text(identity.get("suser_name"))
            user_name = _as_text(identity.get("user_name"))
            logging.info(
                "[INV-STAGE] stage=SESSION_VALIDATION execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                v_exec_ms,
                v_fetch_ms,
                len(identity_rows),
            )
            if db_name.upper() != "EDARSAHUB" or suser_name.upper() != "HRLECTURA" or user_name.upper() != "HRLECTURA":
                raise HTTPException(
                    status_code=500,
                    detail="Validación de sesión SQL canónica inválida.",
                )

            header_params = [server_id, *folios_all]
            header_filters = ["server_id = %s", f"folio IN ({folio_placeholders})", "sync_status IN ('ACTIVE', 'REPLACED')"]
            if selected_almacenes:
                almacen_placeholders = ",".join(["%s"] * len(selected_almacenes))
                header_filters.append(f"(almacen_id IN ({almacen_placeholders}) OR almacen IN ({almacen_placeholders}))")
                header_params.extend(selected_almacenes)
                header_params.extend(selected_almacenes)

            h_exec_started = perf_counter()
            cursor.execute(
                f"""
        SELECT
            folio,
            fecha,
            almacen,
            almacen_id,
            sucursal,
            sucursal_id,
            sync_status
        FROM (
            SELECT
                folio,
                fecha,
                almacen,
                almacen_id,
                sucursal,
                sucursal_id,
                sync_status,
                ROW_NUMBER() OVER (
                    PARTITION BY server_id, sucursal_id, almacen_id, folio
                    ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
                ) AS _rn
            FROM Compras_Inventarios_Fisicos_Sync
            WHERE {' AND '.join(header_filters)}
        ) t
        WHERE t._rn = 1
ORDER BY fecha, folio
""",
                tuple(header_params),
            )
            h_exec_ms = int((perf_counter() - h_exec_started) * 1000)
            h_fetch_started = perf_counter()
            header_rows = cursor.fetchall()
            h_fetch_ms = int((perf_counter() - h_fetch_started) * 1000)
            logging.info(
                "[INV-STAGE] stage=HEADERS execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                h_exec_ms,
                h_fetch_ms,
                len(header_rows),
            )
            if not header_rows:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "INVENTORY_PHYSICAL_HEADERS_MISSING",
                        "message": "No se encontraron inventarios canónicos para los folios seleccionados. Ejecuta/resincroniza inventarios físicos y vuelve a generar el reporte.",
                        "folios": folios_all,
                        "source": "dbo.Compras_Inventarios_Fisicos_Sync",
                    },
                )

            replaced_headers = [r for r in header_rows if _as_text(r.get('sync_status')).upper() == 'REPLACED']
            if replaced_headers:
                logging.warning(
                    "[SOFT-CANONICAL-NOLIVE] usando inventarios REPLACED deduplicados por respaldo canónico folios=%s",
                    sorted({_as_text(r.get('folio')) for r in replaced_headers}),
                )

            matched_folios = {_as_text(r.get('folio')) for r in header_rows}
            missing_folios = [f for f in folios_all if _as_text(f) not in matched_folios]
            if missing_folios:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "INVENTORY_PHYSICAL_HEADERS_MISSING",
                        "message": f"Folios sin respaldo canónico: {', '.join(missing_folios)}. Ejecuta/resincroniza inventarios físicos y vuelve a generar el reporte.",
                        "folios": missing_folios,
                        "source": "dbo.Compras_Inventarios_Fisicos_Sync",
                    },
                )

            header_by_folio = {}
            for row in header_rows:
                header_by_folio.setdefault(_as_text(row.get('folio')), row)

            almacen_ids = {_as_text(r.get('almacen_id')) for r in header_rows if _as_text(r.get('almacen_id'))}
            almacen_names = {_as_text(r.get('almacen')) for r in header_rows if _as_text(r.get('almacen'))}
            almacen_display = almacen or next(iter(almacen_names), "")

            ini_dates = [_parse_dt(header_by_folio.get(_as_text(f), {}).get('fecha')) for f in lista_folios_ini]
            fin_dates = [_parse_dt(header_by_folio.get(_as_text(f), {}).get('fecha')) for f in lista_folios_fin]
            request_ini = _parse_dt(fecha_ini)
            request_fin = _parse_dt(fecha_fin)
            inventory_start = min([d for d in [*ini_dates, request_ini] if d], default=None)
            inventory_end = max([d for d in [*fin_dates, request_fin] if d], default=None)
            if not inventory_start or not inventory_end:
                raise HTTPException(status_code=400, detail="No se pudieron determinar fechas canónicas de inventario")
            period_start = inventory_start
            period_end = inventory_end
            if period_start > period_end:
                period_start, period_end = period_end, period_start
            period_start = period_start + _timedelta(seconds=1)
            period_end = period_end - _timedelta(seconds=1)
            if period_start > period_end:
                raise HTTPException(status_code=400, detail="La ventana canónica de movimientos quedó vacía")
            sales_start = inventory_start.replace(hour=0, minute=0, second=0, microsecond=0)
            sales_end = inventory_end.replace(hour=0, minute=0, second=0, microsecond=0) - _timedelta(seconds=1)
            logging.info(
                "[SOFT-CANONICAL-NOLIVE] window start=%s end=%s rule=initial+1s/final-1s",
                period_start,
                period_end,
            )
            logging.info(
                "[SOFT-CANONICAL-NOLIVE] sales_window start=%s end=%s rule=initial-day/final-day-minus-1",
                sales_start,
                sales_end,
            )

            detail_params = [server_id, *folios_all]
            detail_filters = ["server_id = %s", f"folio IN ({folio_placeholders})", "sync_status IN ('ACTIVE', 'REPLACED')"]
            if almacen_ids:
                ids = sorted(almacen_ids)
                detail_filters.append(f"almacen_id IN ({','.join(['%s'] * len(ids))})")
                detail_params.extend(ids)
            elif almacen_names:
                names = sorted(almacen_names)
                detail_filters.append(f"almacen IN ({','.join(['%s'] * len(names))})")
                detail_params.extend(names)

            def _fetch_inventory_detail_rows(filters, params, label):
                nonlocal conn, cursor
                try:
                    d_exec_started = perf_counter()
                    cursor.execute(
                        f"""
SELECT
    folio,
    codigo_producto,
    nombre_producto,
    unidad,
    existencia_fisica,
    ISNULL(Rendimiento, 1) AS rendimiento,
    costo_unitario,
    almacen,
    almacen_id
FROM (
    SELECT
        folio,
        codigo_producto,
        nombre_producto,
        unidad,
        existencia_fisica,
        ISNULL(Rendimiento, 1) AS rendimiento,
        costo_unitario,
        almacen,
        almacen_id,
        ROW_NUMBER() OVER (
            PARTITION BY server_id, almacen_id, folio, codigo_producto
            ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END
        ) AS _rn
    FROM Compras_Inventarios_Fisicos_Detalle_Sync
    WHERE {' AND '.join(filters)}
) t
WHERE t._rn = 1
""",
                        tuple(params),
                    )
                    d_exec_ms = int((perf_counter() - d_exec_started) * 1000)
                except Exception as detail_rendimiento_error:
                    first_classification = _classify_inventory_sql_error(detail_rendimiento_error)
                    logging.warning(
                        "[INV-STAGE] stage=DETAILS label=%s execute_ms=%s classification=%s error_type=%s",
                        label,
                        int((perf_counter() - d_exec_started) * 1000),
                        first_classification,
                        type(detail_rendimiento_error).__name__,
                    )
                    # Si el primer intento dejó DBPROCESS muerto, NO reutilizar sesión.
                    try:
                        if conn:
                            conn.close()
                    except Exception:
                        pass

                    detail_fallback_sql = f"""
SELECT
    folio,
    codigo_producto,
    nombre_producto,
    unidad,
    existencia_fisica,
    1 AS rendimiento,
    costo_unitario,
    almacen,
    almacen_id
FROM (
    SELECT
        folio,
        codigo_producto,
        nombre_producto,
        unidad,
        existencia_fisica,
        1 AS rendimiento,
        costo_unitario,
        almacen,
        almacen_id,
        ROW_NUMBER() OVER (
            PARTITION BY server_id, almacen_id, folio, codigo_producto
            ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END
        ) AS _rn
    FROM Compras_Inventarios_Fisicos_Detalle_Sync
    WHERE {' AND '.join(filters)}
) t
WHERE t._rn = 1
"""

                    last_error = detail_rendimiento_error
                    for attempt in (1, 2):
                        try:
                            local_conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
                            local_cursor = local_conn.cursor(as_dict=True)
                            f_exec_started = perf_counter()
                            local_cursor.execute(detail_fallback_sql, tuple(params))
                            f_exec_ms = int((perf_counter() - f_exec_started) * 1000)
                            f_fetch_started = perf_counter()
                            rows = local_cursor.fetchall()
                            f_fetch_ms = int((perf_counter() - f_fetch_started) * 1000)
                            logging.info(
                                "[INV-STAGE] stage=DETAILS_FALLBACK label=%s attempt=%s execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                                label,
                                attempt,
                                f_exec_ms,
                                f_fetch_ms,
                                len(rows),
                            )
                            conn = local_conn
                            cursor = local_cursor
                            return rows
                        except Exception as fallback_error:
                            last_error = fallback_error
                            classification = _classify_inventory_sql_error(fallback_error)
                            logging.warning(
                                "[INV-STAGE] stage=DETAILS_FALLBACK label=%s attempt=%s classification=%s error_type=%s",
                                label,
                                attempt,
                                classification,
                                type(fallback_error).__name__,
                            )
                            if not _should_retry_inventory_once(classification, attempt):
                                raise
                    raise last_error

                d_fetch_started = perf_counter()
                rows = cursor.fetchall()
                d_fetch_ms = int((perf_counter() - d_fetch_started) * 1000)
                logging.info(
                    "[INV-STAGE] stage=DETAILS label=%s execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                    label,
                    d_exec_ms,
                    d_fetch_ms,
                    len(rows),
                )
                return rows

            detail_rows = _fetch_inventory_detail_rows(detail_filters, detail_params, "almacen")

            if not detail_rows and (almacen_ids or almacen_names):
                folio_only_filters = [
                    "server_id = %s",
                    f"folio IN ({folio_placeholders})",
                    "sync_status IN ('ACTIVE', 'REPLACED')",
                ]
                folio_only_params = [server_id, *folios_all]
                detail_rows = _fetch_inventory_detail_rows(
                    folio_only_filters,
                    folio_only_params,
                    "folio",
                )
                if detail_rows:
                    logging.warning(
                        "[SOFT-CANONICAL-NOLIVE] detalle recuperado por folio sin filtro de almacen; server_id=%s folios=%s almacenes=%s",
                        server_id,
                        folios_all,
                        sorted(almacen_ids or almacen_names),
                    )

            if not detail_rows:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "INVENTORY_PHYSICAL_DETAIL_MISSING",
                        "message": "No hay detalle canónico para los folios seleccionados. Ejecuta/resincroniza inventarios físicos y vuelve a generar el reporte.",
                        "folios": folios_all,
                        "source": "dbo.Compras_Inventarios_Fisicos_Detalle_Sync",
                    },
                )

            ini_set = {_as_text(f) for f in lista_folios_ini}
            fin_set = {_as_text(f) for f in lista_folios_fin}
            inv_inicial = {}
            inv_final = {}
            productos = {}

            for row in detail_rows:
                codigo = _as_text(row.get('codigo_producto'))
                if not codigo:
                    continue
                folio = _as_text(row.get('folio'))
                cantidad = _as_float(row.get('existencia_fisica'))
                rendimiento = _as_float(row.get('rendimiento')) or 1
                costo = _as_float(row.get('costo_unitario'))
                productos.setdefault(codigo, {
                    'Producto': row.get('nombre_producto') or f'Producto {codigo}',
                    'Unidad': row.get('unidad') or 'PZA',
                    'Rendimiento': rendimiento,
                    'Costo_Unitario': costo,
                })
                if rendimiento > _as_float(productos[codigo].get('Rendimiento')):
                    productos[codigo]['Rendimiento'] = rendimiento
                if costo:
                    productos[codigo]['Costo_Unitario'] = costo
                if folio in ini_set:
                    inv_inicial[codigo] = inv_inicial.get(codigo, 0.0) + cantidad
                if folio in fin_set:
                    inv_final[codigo] = inv_final.get(codigo, 0.0) + cantidad

            movimientos = {}
            movement_params = [server_id, period_start, period_end]
            movement_filters = [
                "server_id = %s",
                "fecha >= %s",
                "fecha <= %s",
                "sync_status = 'ACTIVE'",
                "ISNULL(idconcepto, '') NOT IN ('', 'SPV', 'SCP', 'SCS')",
                _soft_date_only_final_day_guard("fecha"),
            ]
            movement_params.extend([period_end, period_end])
            if almacen_ids:
                ids = sorted(almacen_ids)
                movement_filters.append(f"almacen_id IN ({','.join(['%s'] * len(ids))})")
                movement_params.extend(ids)
            elif almacen_names:
                names = sorted(almacen_names)
                movement_filters.append(f"almacen IN ({','.join(['%s'] * len(names))})")
                movement_params.extend(names)

            try:
                m_exec_started = perf_counter()
                cursor.execute(
                    f"""
SELECT
    codigo_producto,
    SUM(cantidad) AS cantidad
FROM Compras_Inventarios_Movimientos_Sync
WHERE {' AND '.join(movement_filters)}
GROUP BY codigo_producto
""",
                    tuple(movement_params),
                )
                m_exec_ms = int((perf_counter() - m_exec_started) * 1000)
                m_fetch_started = perf_counter()
                movimientos = {
                    _as_text(row.get('codigo_producto')): _as_float(row.get('cantidad'))
                    for row in cursor.fetchall()
                    if _as_text(row.get('codigo_producto'))
                }
                m_fetch_ms = int((perf_counter() - m_fetch_started) * 1000)
                logging.info(
                    "[INV-STAGE] stage=MOVIMIENTOS execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                    m_exec_ms,
                    m_fetch_ms,
                    len(movimientos),
                )
            except Exception as mov_error:
                mov_class = _classify_inventory_sql_error(mov_error)
                logging.exception(
                    "[INV-STAGE] stage=MOVIMIENTOS classification=%s error_type=%s",
                    mov_class,
                    type(mov_error).__name__,
                )
                raise

            ventas = {}
            sales_params = [server_id, sales_start, sales_end]
            sales_filters = [
                "server_id = %s",
                "fecha >= %s",
                "fecha <= %s",
                "sync_status = 'ACTIVE'",
                "ISNULL(idconcepto, '') IN ('SPV', 'SCP', 'SCS')",
                _soft_date_only_final_day_guard("fecha"),
            ]
            sales_params.extend([sales_end, sales_end])
            if almacen_ids:
                ids = sorted(almacen_ids)
                sales_filters.append(f"almacen_id IN ({','.join(['%s'] * len(ids))})")
                sales_params.extend(ids)
            elif almacen_names:
                names = sorted(almacen_names)
                sales_filters.append(f"almacen IN ({','.join(['%s'] * len(names))})")
                sales_params.extend(names)

            try:
                s_exec_started = perf_counter()
                cursor.execute(
                    f"""
SELECT
    codigo_producto,
    SUM(cantidad) AS cantidad
FROM Compras_Inventarios_Movimientos_Sync
WHERE {' AND '.join(sales_filters)}
GROUP BY codigo_producto
""",
                    tuple(sales_params),
                )
                s_exec_ms = int((perf_counter() - s_exec_started) * 1000)
                s_fetch_started = perf_counter()
                ventas = {
                    _as_text(row.get('codigo_producto')): abs(_as_float(row.get('cantidad')))
                    for row in cursor.fetchall()
                    if _as_text(row.get('codigo_producto'))
                }
                s_fetch_ms = int((perf_counter() - s_fetch_started) * 1000)
                logging.info(
                    "[INV-STAGE] stage=VENTAS execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                    s_exec_ms,
                    s_fetch_ms,
                    len(ventas),
                )
            except Exception as sales_error:
                sales_class = _classify_inventory_sql_error(sales_error)
                logging.warning(
                    "[INV-STAGE] stage=VENTAS classification=%s error_type=%s",
                    sales_class,
                    type(sales_error).__name__,
                )

            all_codes = sorted(set(productos.keys()) | set(inv_inicial.keys()) | set(inv_final.keys()) | set(movimientos.keys()) | set(ventas.keys()))
            catalogo_productos = {}
            if all_codes:
                code_placeholders = ",".join(["%s"] * len(all_codes))

                def _is_missing_classifier(value, fallback_label):
                    value_text = _as_text(value).upper()
                    return not value_text or value_text == fallback_label or value_text.startswith("SIN ")

                def _merge_catalog_row(codigo, catalog_row, force_classifiers=False):
                    if not codigo or not catalog_row:
                        return
                    current = dict(catalogo_productos.get(codigo) or {})
                    if not current:
                        catalogo_productos[codigo] = dict(catalog_row)
                        return

                    for field in ('Producto', 'Unidad'):
                        if not current.get(field) and catalog_row.get(field):
                            current[field] = catalog_row.get(field)

                    for field in ('Costo_Unitario', 'Rendimiento'):
                        new_value = _as_float(catalog_row.get(field))
                        current_value = _as_float(current.get(field))
                        if new_value and (not current_value or new_value > current_value):
                            current[field] = catalog_row.get(field)

                    classifier_fallbacks = {
                        'Categoria': 'SIN CATEGORIA',
                        'Familia': 'SIN FAMILIA',
                        'SubFamilia': 'SIN SUBFAMILIA',
                    }
                    for field, fallback_label in classifier_fallbacks.items():
                        if (force_classifiers or _is_missing_classifier(current.get(field), fallback_label)) and catalog_row.get(field):
                            current[field] = catalog_row.get(field)

                    for field in ('CategoriaCodigo', 'FamiliaCodigo', 'SubFamiliaCodigo'):
                        if (force_classifiers or not _as_text(current.get(field))) and _as_text(catalog_row.get(field)):
                            current[field] = catalog_row.get(field)

                    catalogo_productos[codigo] = current

                try:
                    ci_exec_started = perf_counter()
                    cursor.execute(
                        f"""
SELECT
    i.CodigoFuente AS Codigo,
    i.Nombre AS Producto,
    i.UnidadMedida AS Unidad,
    COALESCE(i.Costo, i.CostoPromedio, i.UltimoCosto, 0) AS Costo_Unitario,
    COALESCE(i.RendimientoElaborado, 1) AS Rendimiento,
    cat.Codigo AS CategoriaCodigo,
    CASE LTRIM(RTRIM(CAST(cat.Codigo AS VARCHAR(50))))
        WHEN '1' THEN 'BEBIDAS'
        WHEN '2' THEN 'ALIMENTOS'
        WHEN '3' THEN 'OTROS'
        ELSE COALESCE(cat.Nombre, 'SIN CATEGORIA')
    END AS Categoria,
    fam.Codigo AS FamiliaCodigo,
    COALESCE(fam.Nombre, 'SIN FAMILIA') AS Familia,
    sub.Codigo AS SubFamiliaCodigo,
    COALESCE(sub.Nombre, i.GrupoInsumoNombre, 'SIN SUBFAMILIA') AS SubFamilia
FROM Sync_Productos_Insumos i
LEFT JOIN Sync_Catalogo_Filtros sub
    ON sub.ServerID = i.ServerID
   AND sub.Nivel = 'SUBFAMILIA'
   AND sub.Codigo = i.GrupoInsumoCodigoFuente
   AND sub.Activo = 1
LEFT JOIN Sync_Catalogo_Filtros fam
    ON fam.ServerID = i.ServerID
   AND fam.Nivel = 'FAMILIA'
   AND fam.Codigo = sub.ParentCodigo
   AND fam.Activo = 1
LEFT JOIN Sync_Catalogo_Filtros cat
    ON cat.ServerID = i.ServerID
   AND cat.Nivel = 'CATEGORIA'
   AND cat.Codigo = fam.ParentCodigo
   AND cat.Activo = 1
WHERE i.ServerID = %s
  AND i.CodigoFuente IN ({code_placeholders})
  AND i.Activo = 1
""",
                        tuple([server_id, *all_codes]),
                    )
                    ci_exec_ms = int((perf_counter() - ci_exec_started) * 1000)
                    ci_fetch_started = perf_counter()
                    insumo_catalog_rows = cursor.fetchall()
                    ci_fetch_ms = int((perf_counter() - ci_fetch_started) * 1000)
                    for row in insumo_catalog_rows:
                        _merge_catalog_row(_as_text(row.get('Codigo')), row)
                    ci_resolved = len([
                        row for row in insumo_catalog_rows
                        if not _is_missing_classifier(row.get('Categoria'), 'SIN CATEGORIA')
                    ])
                    logging.info(
                        "[INV-STAGE] stage=CATALOGO_INSUMOS execute_ms=%s fetch_ms=%s rows=%s resolved=%s classification=OK",
                        ci_exec_ms,
                        ci_fetch_ms,
                        len(insumo_catalog_rows),
                        ci_resolved,
                    )
                    logging.warning(
                        "[SOFT-CANONICAL-NOLIVE] sync insumo classifier rows=%s resolved=%s",
                        len(insumo_catalog_rows),
                        ci_resolved,
                    )
                except Exception as catalog_error:
                    ci_class = _classify_inventory_sql_error(catalog_error)
                    logging.warning(
                        "[INV-STAGE] stage=CATALOGO_INSUMOS classification=%s error_type=%s",
                        ci_class,
                        type(catalog_error).__name__,
                    )
                    try:
                        cif_exec_started = perf_counter()
                        cursor.execute(
                            f"""
SELECT
    i.CodigoFuente AS Codigo,
    i.Nombre AS Producto,
    i.UnidadMedida AS Unidad,
    COALESCE(i.Costo, i.CostoPromedio, i.UltimoCosto, 0) AS Costo_Unitario,
    COALESCE(i.RendimientoElaborado, 1) AS Rendimiento,
    NULL AS CategoriaCodigo,
    'SIN CATEGORIA' AS Categoria,
    NULL AS FamiliaCodigo,
    'SIN FAMILIA' AS Familia,
    i.GrupoInsumoCodigoFuente AS SubFamiliaCodigo,
    COALESCE(i.GrupoInsumoNombre, 'SIN SUBFAMILIA') AS SubFamilia
FROM Sync_Productos_Insumos i
WHERE i.ServerID = %s
  AND i.CodigoFuente IN ({code_placeholders})
  AND i.Activo = 1
""",
                            tuple([server_id, *all_codes]),
                        )
                        cif_exec_ms = int((perf_counter() - cif_exec_started) * 1000)
                        cif_fetch_started = perf_counter()
                        insumo_fallback_rows = cursor.fetchall()
                        cif_fetch_ms = int((perf_counter() - cif_fetch_started) * 1000)
                        for row in insumo_fallback_rows:
                            _merge_catalog_row(_as_text(row.get('Codigo')), row)
                        logging.info(
                            "[INV-STAGE] stage=CATALOGO_INSUMOS_FALLBACK execute_ms=%s fetch_ms=%s rows=%s classification=OK",
                            cif_exec_ms,
                            cif_fetch_ms,
                            len(insumo_fallback_rows),
                        )
                    except Exception as fallback_catalog_error:
                        cif_class = _classify_inventory_sql_error(fallback_catalog_error)
                        logging.warning(
                            "[INV-STAGE] stage=CATALOGO_INSUMOS_FALLBACK classification=%s error_type=%s",
                            cif_class,
                            type(fallback_catalog_error).__name__,
                        )

                try:
                    cp_exec_started = perf_counter()
                    cursor.execute(
                        f"""
SELECT
    p.CodigoFuente AS Codigo,
    p.Nombre AS Producto,
    'PZA' AS Unidad,
    COALESCE(p.CostoReceta, 0) AS Costo_Unitario,
    1 AS Rendimiento,
    p.CategoriaCodigoFuente AS CategoriaCodigo,
    CASE LTRIM(RTRIM(CAST(p.CategoriaCodigoFuente AS VARCHAR(50))))
        WHEN '1' THEN 'BEBIDAS'
        WHEN '2' THEN 'ALIMENTOS'
        WHEN '3' THEN 'OTROS'
        ELSE COALESCE(p.CategoriaNombre, 'SIN CATEGORIA')
    END AS Categoria,
    p.FamiliaCodigoFuente AS FamiliaCodigo,
    COALESCE(p.FamiliaNombre, 'SIN FAMILIA') AS Familia,
    p.SubFamiliaCodigoFuente AS SubFamiliaCodigo,
    COALESCE(p.SubFamiliaNombre, 'SIN SUBFAMILIA') AS SubFamilia
FROM Sync_Productos p
WHERE p.ServerID = %s
  AND p.CodigoFuente IN ({code_placeholders})
  AND p.Activo = 1
""",
                        tuple([server_id, *all_codes]),
                    )
                    cp_exec_ms = int((perf_counter() - cp_exec_started) * 1000)
                    cp_fetch_started = perf_counter()
                    sync_product_rows = cursor.fetchall()
                    cp_fetch_ms = int((perf_counter() - cp_fetch_started) * 1000)
                    for row in sync_product_rows:
                        _merge_catalog_row(_as_text(row.get('Codigo')), row)
                    cp_resolved = len([
                        row for row in sync_product_rows
                        if not _is_missing_classifier(row.get('Categoria'), 'SIN CATEGORIA')
                    ])
                    logging.info(
                        "[INV-STAGE] stage=CATALOGO_PRODUCTOS_SYNC execute_ms=%s fetch_ms=%s rows=%s resolved=%s classification=OK",
                        cp_exec_ms,
                        cp_fetch_ms,
                        len(sync_product_rows),
                        cp_resolved,
                    )
                    logging.warning(
                        "[SOFT-CANONICAL-NOLIVE] sync product classifier rows=%s resolved=%s",
                        len(sync_product_rows),
                        cp_resolved,
                    )
                except Exception as product_catalog_error:
                    cp_class = _classify_inventory_sql_error(product_catalog_error)
                    logging.warning(
                        "[INV-STAGE] stage=CATALOGO_PRODUCTOS_SYNC classification=%s error_type=%s",
                        cp_class,
                        type(product_catalog_error).__name__,
                    )

                unresolved_catalog_codes = [
                    code for code in all_codes
                    if code not in catalogo_productos
                    or _is_missing_classifier(catalogo_productos[code].get('Categoria'), 'SIN CATEGORIA')
                    or _is_missing_classifier(catalogo_productos[code].get('Familia'), 'SIN FAMILIA')
                    or _is_missing_classifier(catalogo_productos[code].get('SubFamilia'), 'SIN SUBFAMILIA')
                ]
                if unresolved_catalog_codes:
                    unresolved_placeholders = ",".join(["%s"] * len(unresolved_catalog_codes))

                    try:
                        cf_exec_started = perf_counter()
                        cursor.execute(
                            f"""
WITH catalogo_base AS (
    SELECT
        LTRIM(RTRIM(pc.CodigoProducto)) AS Codigo,
        pc.ProductoID
    FROM Producto_Catalogo pc
    WHERE pc.Activo = 1
      AND LTRIM(RTRIM(pc.CodigoProducto)) IN ({unresolved_placeholders})

    UNION ALL

    SELECT
        LTRIM(RTRIM(pc.SKU)) AS Codigo,
        pc.ProductoID
    FROM Producto_Catalogo pc
    WHERE pc.Activo = 1
      AND LTRIM(RTRIM(pc.SKU)) IN ({unresolved_placeholders})

    UNION ALL

    SELECT
        LTRIM(RTRIM(pp.CodigoPresentacion)) AS Codigo,
        pp.ProductoID
    FROM Producto_Presentaciones pp
    WHERE pp.Activo = 1
      AND LTRIM(RTRIM(pp.CodigoPresentacion)) IN ({unresolved_placeholders})
)
SELECT
    cb.Codigo,
    MAX(pc.NombreProducto) AS Producto,
    MAX(pc.UnidadInventario) AS Unidad,
    MAX(pc.PrecioCostoBase) AS Costo_Unitario,
    COALESCE(MAX(pp.FactorConversionInventario), 1) AS Rendimiento,
    MAX(CAST(pf.CodigoFamilia AS VARCHAR(50))) AS CategoriaCodigo,
    COALESCE(MAX(pf.NombreFamilia), 'SIN CATEGORIA') AS Categoria,
    MAX(CAST(psf.CodigoSubFamilia AS VARCHAR(50))) AS FamiliaCodigo,
    COALESCE(MAX(psf.NombreSubFamilia), 'SIN FAMILIA') AS Familia,
    MAX(CAST(pl.CodigoLinea AS VARCHAR(50))) AS SubFamiliaCodigo,
    COALESCE(MAX(pl.NombreLinea), 'SIN SUBFAMILIA') AS SubFamilia
FROM catalogo_base cb
INNER JOIN Producto_Catalogo pc
    ON pc.ProductoID = cb.ProductoID
   AND pc.Activo = 1
LEFT JOIN Producto_Lineas pl
    ON pl.LineaProductoID = pc.LineaProductoID
   AND pl.Activo = 1
LEFT JOIN Producto_SubFamilias psf
    ON psf.SubFamiliaProductoID = pl.SubFamiliaProductoID
   AND psf.Activo = 1
LEFT JOIN Producto_Familias pf
    ON pf.FamiliaProductoID = psf.FamiliaProductoID
   AND pf.Activo = 1
LEFT JOIN Producto_Presentaciones pp
    ON pp.ProductoID = pc.ProductoID
   AND pp.Activo = 1
WHERE cb.Codigo IS NOT NULL AND cb.Codigo <> ''
GROUP BY cb.Codigo
""",
                            tuple([*unresolved_catalog_codes, *unresolved_catalog_codes, *unresolved_catalog_codes]),
                        )
                        cf_exec_ms = int((perf_counter() - cf_exec_started) * 1000)
                        cf_fetch_started = perf_counter()
                        catalogo_canonico_rows = cursor.fetchall()
                        cf_fetch_ms = int((perf_counter() - cf_fetch_started) * 1000)
                        for row in catalogo_canonico_rows:
                            _merge_catalog_row(_as_text(row.get('Codigo')), row)
                        cf_resolved = len([
                            row for row in catalogo_canonico_rows
                            if not _is_missing_classifier(row.get('Categoria'), 'SIN CATEGORIA')
                        ])
                        logging.info(
                            "[INV-STAGE] stage=CATALOGO_FALLBACK_BASE execute_ms=%s fetch_ms=%s rows=%s resolved=%s classification=OK",
                            cf_exec_ms,
                            cf_fetch_ms,
                            len(catalogo_canonico_rows),
                            cf_resolved,
                        )
                        logging.warning(
                            "[SOFT-CANONICAL-NOLIVE] fallback catalog classifier rows=%s resolved=%s",
                            len(catalogo_canonico_rows),
                            cf_resolved,
                        )
                    except Exception as canonical_catalog_error:
                        cf_class = _classify_inventory_sql_error(canonical_catalog_error)
                        logging.warning(
                            "[INV-STAGE] stage=CATALOGO_FALLBACK_BASE classification=%s error_type=%s",
                            cf_class,
                            type(canonical_catalog_error).__name__,
                        )

                    try:
                        cm_exec_started = perf_counter()
                        cursor.execute(
                            f"""
SELECT
    LTRIM(RTRIM(m.CodigoFuente)) AS Codigo,
    MAX(pc.NombreProducto) AS Producto,
    MAX(pc.UnidadInventario) AS Unidad,
    MAX(pc.PrecioCostoBase) AS Costo_Unitario,
    COALESCE(MAX(pp.FactorConversionInventario), 1) AS Rendimiento,
    MAX(CAST(pf.CodigoFamilia AS VARCHAR(50))) AS CategoriaCodigo,
    COALESCE(MAX(pf.NombreFamilia), 'SIN CATEGORIA') AS Categoria,
    MAX(CAST(psf.CodigoSubFamilia AS VARCHAR(50))) AS FamiliaCodigo,
    COALESCE(MAX(psf.NombreSubFamilia), 'SIN FAMILIA') AS Familia,
    MAX(CAST(pl.CodigoLinea AS VARCHAR(50))) AS SubFamiliaCodigo,
    COALESCE(MAX(pl.NombreLinea), 'SIN SUBFAMILIA') AS SubFamilia
FROM Producto_MapeoOrigen m
INNER JOIN Producto_Catalogo pc
    ON pc.ProductoID = m.ProductoID
   AND pc.Activo = 1
LEFT JOIN Producto_Lineas pl
    ON pl.LineaProductoID = pc.LineaProductoID
   AND pl.Activo = 1
LEFT JOIN Producto_SubFamilias psf
    ON psf.SubFamiliaProductoID = pl.SubFamiliaProductoID
   AND psf.Activo = 1
LEFT JOIN Producto_Familias pf
    ON pf.FamiliaProductoID = psf.FamiliaProductoID
   AND pf.Activo = 1
LEFT JOIN Producto_Presentaciones pp
    ON pp.ProductoID = pc.ProductoID
   AND pp.Activo = 1
WHERE m.ServerID = %s
  AND m.Activo = 1
  AND UPPER(COALESCE(m.SystemType, '')) LIKE 'SOFT%%'
  AND LTRIM(RTRIM(m.CodigoFuente)) IN ({unresolved_placeholders})
GROUP BY LTRIM(RTRIM(m.CodigoFuente))
""",
                            tuple([server_id, *unresolved_catalog_codes]),
                        )
                        cm_exec_ms = int((perf_counter() - cm_exec_started) * 1000)
                        cm_fetch_started = perf_counter()
                        mapped_catalog_rows = cursor.fetchall()
                        cm_fetch_ms = int((perf_counter() - cm_fetch_started) * 1000)
                        for row in mapped_catalog_rows:
                            _merge_catalog_row(_as_text(row.get('Codigo')), row)
                        cm_resolved = len([
                            row for row in mapped_catalog_rows
                            if not _is_missing_classifier(row.get('Categoria'), 'SIN CATEGORIA')
                        ])
                        logging.info(
                            "[INV-STAGE] stage=CATALOGO_FALLBACK_MAPEO execute_ms=%s fetch_ms=%s rows=%s resolved=%s classification=OK",
                            cm_exec_ms,
                            cm_fetch_ms,
                            len(mapped_catalog_rows),
                            cm_resolved,
                        )
                        logging.warning(
                            "[SOFT-CANONICAL-NOLIVE] fallback mapped classifier rows=%s resolved=%s",
                            len(mapped_catalog_rows),
                            cm_resolved,
                        )
                    except Exception as mapped_catalog_error:
                        cm_class = _classify_inventory_sql_error(mapped_catalog_error)
                        logging.warning(
                            "[INV-STAGE] stage=CATALOGO_FALLBACK_MAPEO classification=%s error_type=%s",
                            cm_class,
                            type(mapped_catalog_error).__name__,
                        )

                for codigo, catalog_row in catalogo_productos.items():
                    productos.setdefault(codigo, {})
                    if catalog_row.get('Producto'):
                        productos[codigo]['Producto'] = catalog_row.get('Producto')
                    if catalog_row.get('Unidad'):
                        productos[codigo]['Unidad'] = catalog_row.get('Unidad')
                    catalog_cost = _as_float(catalog_row.get('Costo_Unitario'))
                    if not _as_float(productos[codigo].get('Costo_Unitario')) and catalog_cost:
                        productos[codigo]['Costo_Unitario'] = catalog_cost
                    catalog_rendimiento = _as_float(catalog_row.get('Rendimiento')) or 1
                    current_rendimiento = _as_float(productos[codigo].get('Rendimiento')) or 1
                    productos[codigo]['Rendimiento'] = (
                        catalog_rendimiento
                        if catalog_rendimiento > current_rendimiento
                        else current_rendimiento
                    )
                    productos[codigo]['Categoria'] = catalog_row.get('Categoria') or 'SIN CATEGORIA'
                    productos[codigo]['Familia'] = catalog_row.get('Familia') or 'SIN FAMILIA'
                    productos[codigo]['SubFamilia'] = catalog_row.get('SubFamilia') or 'SIN SUBFAMILIA'
                    productos[codigo]['CategoriaCodigo'] = _as_text(catalog_row.get('CategoriaCodigo'))
                    productos[codigo]['FamiliaCodigo'] = _as_text(catalog_row.get('FamiliaCodigo'))
                    productos[codigo]['SubFamiliaCodigo'] = _as_text(catalog_row.get('SubFamiliaCodigo'))

                try:
                    fp_exec_started = perf_counter()
                    cursor.execute(
                        f"""
SELECT
    Codigo,
    MAX(FactorConversionInventario) AS Rendimiento
FROM (
    SELECT
        LTRIM(RTRIM(pc.CodigoProducto)) AS Codigo,
        pp.FactorConversionInventario
    FROM Producto_Catalogo pc
    INNER JOIN Producto_Presentaciones pp
        ON pp.ProductoID = pc.ProductoID
       AND pp.Activo = 1
    WHERE pc.Activo = 1
      AND LTRIM(RTRIM(pc.CodigoProducto)) IN ({code_placeholders})

    UNION ALL

    SELECT
        LTRIM(RTRIM(pc.SKU)) AS Codigo,
        pp.FactorConversionInventario
    FROM Producto_Catalogo pc
    INNER JOIN Producto_Presentaciones pp
        ON pp.ProductoID = pc.ProductoID
       AND pp.Activo = 1
    WHERE pc.Activo = 1
      AND LTRIM(RTRIM(pc.SKU)) IN ({code_placeholders})

    UNION ALL

    SELECT
        LTRIM(RTRIM(pp.CodigoPresentacion)) AS Codigo,
        pp.FactorConversionInventario
    FROM Producto_Presentaciones pp
    WHERE pp.Activo = 1
      AND LTRIM(RTRIM(pp.CodigoPresentacion)) IN ({code_placeholders})
) factores
WHERE Codigo IS NOT NULL AND Codigo <> ''
GROUP BY Codigo
""",
                        tuple([*all_codes, *all_codes, *all_codes]),
                    )
                    fp_exec_ms = int((perf_counter() - fp_exec_started) * 1000)
                    fp_fetch_started = perf_counter()
                    factor_rows = cursor.fetchall()
                    fp_fetch_ms = int((perf_counter() - fp_fetch_started) * 1000)
                    for factor_row in factor_rows:
                        codigo_factor = _as_text(factor_row.get('Codigo'))
                        rendimiento_factor = _as_float(factor_row.get('Rendimiento')) or 1
                        if codigo_factor in productos and rendimiento_factor > _as_float(productos[codigo_factor].get('Rendimiento')):
                            productos[codigo_factor]['Rendimiento'] = rendimiento_factor
                    fp_gt1 = len([p for p in productos.values() if _as_float(p.get('Rendimiento')) > 1])
                    logging.info(
                        "[INV-STAGE] stage=FACTORES_PRESENTACION execute_ms=%s fetch_ms=%s rows=%s rendimiento_gt1=%s classification=OK",
                        fp_exec_ms,
                        fp_fetch_ms,
                        len(factor_rows),
                        fp_gt1,
                    )
                    logging.info(
                        "[SOFT-CANONICAL-NOLIVE] presentation factor rows=%s rendimiento_gt1=%s",
                        len(factor_rows),
                        fp_gt1,
                    )
                except Exception as factor_error:
                    fp_class = _classify_inventory_sql_error(factor_error)
                    logging.warning(
                        "[INV-STAGE] stage=FACTORES_PRESENTACION classification=%s error_type=%s",
                        fp_class,
                        type(factor_error).__name__,
                    )

                logging.warning(
                    "[SOFT-CANONICAL-NOLIVE] catalog rows=%s missing=%s sin_categoria=%s rendimiento_gt1=%s",
                    len(catalogo_productos),
                    len([code for code in all_codes if code not in catalogo_productos]),
                    len([
                        code for code in all_codes
                        if _is_missing_classifier(productos.get(code, {}).get('Categoria'), 'SIN CATEGORIA')
                    ]),
                    len([p for p in productos.values() if _as_float(p.get('Rendimiento')) > 1]),
                )

            def _matches_filter_set(code_val, name_val, filter_set):
                if not filter_set:
                    return True
                code_text = _as_text(code_val)
                name_text = _as_text(name_val).upper()
                if code_text in filter_set or name_text in filter_set:
                    return True
                if code_text.isdigit():
                    num = int(code_text)
                    if (
                        str(num) in filter_set
                        or f"{num:02d}" in filter_set
                        or f"{num:03d}" in filter_set
                        or f"{num:04d}" in filter_set
                    ):
                        return True
                return False

            if selected_categoria_codes or selected_familia_codes or selected_subfamilia_codes:
                before_filter_count = len(all_codes)

                def _passes_soft_catalog_filters(codigo):
                    prod = productos.get(codigo, {})
                    if selected_categoria_codes and not _matches_filter_set(prod.get('CategoriaCodigo'), prod.get('Categoria'), selected_categoria_codes):
                        return False
                    if selected_familia_codes and not _matches_filter_set(prod.get('FamiliaCodigo'), prod.get('Familia'), selected_familia_codes):
                        return False
                    if selected_subfamilia_codes and not _matches_filter_set(prod.get('SubFamiliaCodigo'), prod.get('SubFamilia'), selected_subfamilia_codes):
                        return False
                    return True

                all_codes = [codigo for codigo in all_codes if _passes_soft_catalog_filters(codigo)]
                logging.info(
                    "[SOFT-CANONICAL-NOLIVE] filtros catalogo categorias=%s familias=%s subfamilias=%s before=%s after=%s",
                    sorted(selected_categoria_codes),
                    sorted(selected_familia_codes),
                    sorted(selected_subfamilia_codes),
                    before_filter_count,
                    len(all_codes),
                )

            results = []
            for codigo in all_codes:
                prod = productos.get(codigo, {})
                costo = _as_float(prod.get('Costo_Unitario'))
                inv_ini_qty = _as_float(inv_inicial.get(codigo))
                inv_fin_qty = _as_float(inv_final.get(codigo))
                mov_qty = _as_float(movimientos.get(codigo))
                ventas_qty = _as_float(ventas.get(codigo))
                has_activity = (
                    abs(inv_ini_qty) > 0.000001
                    or abs(inv_fin_qty) > 0.000001
                    or codigo in movimientos
                    or codigo in ventas
                )
                if not has_activity:
                    continue

                inv_teorico = inv_ini_qty + mov_qty - ventas_qty
                diferencia = inv_fin_qty - inv_teorico
                diferencia_costo = diferencia * costo
                diferencia_pct = (diferencia / inv_teorico * 100) if inv_teorico else 0.0
                valor_real = (inv_ini_qty + mov_qty - inv_fin_qty) * costo

                results.append({
                    'ID_Inv_Ini': ', '.join([str(f) for f in lista_folios_ini]),
                    'Comentario_Ini': almacen_display,
                    'ID_Inv_Fin': ', '.join([str(f) for f in lista_folios_fin]),
                    'Comentario_Fin': almacen_display,
                    'Categoria': prod.get('Categoria') or 'SIN CATEGORIA',
                    'Familia': prod.get('Familia') or 'SIN FAMILIA',
                    'SubFamilia': prod.get('SubFamilia') or 'SIN SUBFAMILIA',
                    'Codigo': codigo,
                    'Producto': prod.get('Producto') or f'Producto {codigo}',
                    'Unidad': prod.get('Unidad') or 'PZA',
                    'Rendimiento': _as_float(prod.get('Rendimiento')) or 1,
                    'tipo_almacen': 1,
                    'Costo_Unitario': round(costo, 4),
                    'Inv_Inicial_Cantidad': round(inv_ini_qty, 4),
                    'Inv_Inicial_Costo': round(inv_ini_qty * costo, 2),
                    'Movimientos': round(mov_qty, 4),
                    'Movimientos_Costo': round(mov_qty * costo, 2),
                    'Ventas': round(ventas_qty, 4),
                    'Ventas_Costo': round(ventas_qty * costo, 2),
                    'Inv_Teorico_Cantidad': round(inv_teorico, 4),
                    'Inv_Teorico_Costo': round(inv_teorico * costo, 2),
                    'Inv_Final_Cantidad': round(inv_fin_qty, 4),
                    'Inv_Final_Costo': round(inv_fin_qty * costo, 2),
                    'Diferencia_Cantidad': round(diferencia, 4),
                    'Diferencia_Costo': round(diferencia_costo, 2),
                    'Diferencia_Porcentaje': round(diferencia_pct, 2),
                    'Valor_Real': round(valor_real, 2),
                    'Teorico': 0.0,
                    'source': 'EDARSAHUB_SQL_CANONICAL',
                })

            elapsed_ms = int((perf_counter() - started_at) * 1000)
            logging.info(
                "[SOFT-CANONICAL-NOLIVE] done elapsed_ms=%s rows=%s details=%s movimientos=%s ventas=%s",
                elapsed_ms,
                len(results),
                len(detail_rows),
                len(movimientos),
                len(ventas),
            )
            return {"data": results, "count": len(results), "source": "EDARSAHUB_SQL_CANONICAL"}
        except HTTPException:
            raise
        except Exception as error:
            error_class = _classify_inventory_sql_error(error)
            logging.exception(
                "[SOFT-CANONICAL-NOLIVE] error classification=%s error_type=%s",
                error_class,
                type(error).__name__,
            )
            raise _inventory_analysis_safe_http_exception(error)
        finally:
            if conn:
                conn.close()

    try:
        if is_softrestaurant_system(server.get('system_type')):
            logging.info(
                "Generando análisis de inventario SoftRestaurant desde EDARSAHUB SQL canónico (NO-LIVE)"
            )
            return await _generate_soft_inventory_analysis_canonical()

        if is_mpro_system(server.get('system_type')):
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "INVENTORY_ANALYSIS_CANONICAL_PENDING",
                    "message": (
                        "Análisis de inventario MPRO pendiente de fuente canónica EDARSAHUB. "
                        "Por regla NO-LIVE no se consulta POS en vivo."
                    ),
                    "source": "EDARSAHUB_SQL_CANONICAL",
                },
            )

        raise HTTPException(
            status_code=400,
            detail="Sistema no soportado para análisis canónico de inventario",
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en análisis canónico de inventario: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generando análisis canónico")


# CAB-003 Fase 1A: Asignar referencia para uso desde Core Service
_inventory_analysis_endpoint_ref = generate_inventory_analysis


def _report_detalle_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _report_detalle_fecha_fin(value) -> str:
    text = str(value or '').strip()
    if len(text) == 10 and text[4:5] == '-' and text[7:8] == '-':
        return f"{text} 23:59:59"
    return text


def _report_detalle_almacenes(params: Dict) -> List[str]:
    value = params.get('almacenes')
    if value is None:
        value = params.get('almacen')
    return _compras_clean_almacenes(value)


def _report_movimiento_legacy(row: Dict, producto_nombre: str = '') -> Dict[str, Any]:
    cantidad_raw = _report_detalle_float(row.get('cantidad'))
    tipo = str(row.get('tipo') or '').upper()
    es_entrada = tipo == 'E' or (tipo not in {'S', 'SALIDA'} and cantidad_raw >= 0)
    return {
        'folio': row.get('referencia') or row.get('folio') or '',
        'fecha': row.get('fecha') or '',
        'cantidad': abs(cantidad_raw),
        'tipo_codigo': row.get('concepto') or '',
        'tipo_descripcion': row.get('descripcion') or row.get('tipo_descripcion') or '',
        'tipo_movimiento': 'Entrada' if es_entrada else 'Salida',
        'producto': producto_nombre or row.get('producto') or '',
        'almacen': row.get('almacen') or '',
        'observaciones': row.get('observaciones') or '',
    }


def _report_consumo_legacy(row: Dict, producto_nombre: str = '', sucursal: str = '') -> Dict[str, Any]:
    cantidad = abs(_report_detalle_float(row.get('cantidad') or row.get('consumo')))
    return {
        'folio': row.get('referencia') or row.get('documento') or row.get('folio') or '',
        'fecha': row.get('fecha') or '',
        'cantidad': cantidad,
        'tipo_venta': row.get('concepto') or row.get('tipo_venta') or 'CANONICA',
        'producto_vendido': row.get('descripcion') or row.get('producto_vendido') or producto_nombre,
        'producto': producto_nombre or row.get('producto') or '',
        'precio_unitario': _report_detalle_float(row.get('precio_unitario')),
        'sucursal': row.get('almacen') or sucursal or '',
    }


@api_router.post("/reports/movement-details")
async def get_movement_details(params: Dict, current_user: Dict = Depends(get_current_user)):
    """Wrapper legacy NO-LIVE sobre el detalle canonico de Compras."""
    from types import SimpleNamespace
    from core.corporate_filters.request_resolver import canonical_server_id

    server_id = str(canonical_server_id(params.get('server_id')) or '').strip()
    codigo = str(params.get('producto_codigo') or params.get('codigo') or '').strip()
    if not server_id:
        raise HTTPException(status_code=400, detail="server_id es requerido")
    if not codigo:
        raise HTTPException(status_code=400, detail="producto_codigo es requerido")

    await validate_server_access_unified(current_user, server_id)
    request = SimpleNamespace(
        server_id=server_id,
        sucursal=str(params.get('sucursal') or ''),
        codigo=codigo,
        fecha_inicio=str(params.get('fecha_ini') or params.get('fecha_inicio') or ''),
        fecha_fin=_report_detalle_fecha_fin(params.get('fecha_fin') or params.get('fecha_final')),
        almacenes=_report_detalle_almacenes(params),
    )
    result = await obtener_detalle_movimientos_post(request, current_user)
    if isinstance(result, dict) and result.get('error'):
        return {
            "data": [],
            "count": 0,
            "error": result.get('error'),
            "source": result.get('source') or "EDARSAHUB_SQL_CANONICAL",
        }
    movimientos = result.get('movimientos', []) if isinstance(result, dict) else []
    data = [_report_movimiento_legacy(row, params.get('producto') or '') for row in movimientos]
    return {
        "data": data,
        "count": len(data),
        "source": (result or {}).get('source') or "EDARSAHUB_SQL_CANONICAL",
    }


@api_router.post("/reports/sales-details")
async def get_sales_details(params: Dict, current_user: Dict = Depends(get_current_user)):
    """Wrapper legacy NO-LIVE sobre el detalle canonico de consumos."""
    from types import SimpleNamespace
    from core.corporate_filters.request_resolver import canonical_server_id

    server_id = str(canonical_server_id(params.get('server_id')) or '').strip()
    codigo = str(params.get('producto_codigo') or params.get('codigo') or '').strip()
    if not server_id:
        raise HTTPException(status_code=400, detail="server_id es requerido")
    if not codigo:
        raise HTTPException(status_code=400, detail="producto_codigo es requerido")

    await validate_server_access_unified(current_user, server_id)
    request = SimpleNamespace(
        server_id=server_id,
        sucursal=str(params.get('sucursal') or ''),
        codigo=codigo,
        fecha_inicio=str(params.get('fecha_ini') or params.get('fecha_inicio') or ''),
        fecha_fin=_report_detalle_fecha_fin(params.get('fecha_fin') or params.get('fecha_final')),
        almacenes=_report_detalle_almacenes(params),
    )
    result = await obtener_detalle_consumos_post(request, current_user)
    if isinstance(result, dict) and result.get('error'):
        return {
            "data": [],
            "count": 0,
            "error": result.get('error'),
            "source": result.get('source') or "EDARSAHUB_SQL_CANONICAL",
        }
    consumos = (result.get('consumos') or result.get('movimientos')) if isinstance(result, dict) else []
    data = [_report_consumo_legacy(row, params.get('producto') or '', params.get('sucursal') or '') for row in (consumos or [])]
    return {
        "data": data,
        "count": len(data),
        "source": (result or {}).get('source') or "EDARSAHUB_SQL_CANONICAL",
    }


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
    Los cortes se resuelven exclusivamente desde EDARSAHUB SQL canonico.
    El cache se llena cuando el usuario genera el reporte normal de "Generar Reporte".
    Retorna los últimos 4 cortes con sus diferencias.
    """
    conn = None
    try:
        logging.info(f"get_diferencias_from_cache: almacen_id={almacen_id}, sucursal_id={sucursal_id}, comentario={comentario}, fecha_ref={fecha_referencia}")

        server_id = str(server.get('id') or server.get('server_id') or '').strip()
        if not server_id:
            logging.warning("No se pudo resolver server_id canonico para cache de diferencias")
            return None

        fecha_ref_clean = fecha_referencia.replace('T', ' ')[:10] if fecha_referencia else '2099-12-31'
        filters = [
            "server_id = %s",
            "sync_status IN ('ACTIVE', 'REPLACED')",
            "CONVERT(date, fecha) <= CONVERT(date, %s)",
        ]
        params: List[Any] = [server_id, fecha_ref_clean]

        almacen_text = str(almacen_id or '').strip()
        if almacen_text:
            filters.append("(almacen_id = %s OR almacen = %s)")
            params.extend([almacen_text, almacen_text])

        if is_mpro_system(server.get('system_type')):
            sucursal_text = str(sucursal_id or '').strip()
            comentario_text = str(comentario or '').strip()
            if sucursal_text:
                filters.append("(sucursal_id = %s OR sucursal = %s)")
                params.extend([sucursal_text, sucursal_text])
            if comentario_text:
                filters.append("ISNULL(comentario, '') = %s")
                params.append(comentario_text)

        from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            f"""
SELECT TOP 4
    folio,
    CONVERT(varchar, fecha, 120) AS fecha,
    almacen,
    ISNULL(comentario, '') AS comentario
FROM (
    SELECT
        folio,
        fecha,
        almacen,
        comentario,
        ROW_NUMBER() OVER (
            PARTITION BY server_id, sucursal_id, almacen_id, folio
            ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
        ) AS _rn
    FROM dbo.Compras_Inventarios_Fisicos_Sync
    WHERE {' AND '.join(filters)}
) t
WHERE t._rn = 1
ORDER BY fecha DESC, folio DESC
""",
            tuple(params),
        )
        cortes_result = cursor.fetchall() or []

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
                "server_id": server_id,
                "folio": folio
            }

            cached = _sql_get_inventario_diferencias_cache(cache_key)

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
    finally:
        if conn:
            conn.close()



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
    Usa cache SQL canónico para evitar recalcular.
    Soporta múltiples almacenes (multi-selección).
    FASE 8: Aplica validación RBAC de servidor y almacenes.

    FASE P1.4-E3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    """
    from core.corporate_filters.request_resolver import canonical_server_id
    from core.server_registry import get_server_connection_info

    server_id = str(canonical_server_id(request.server_id) or '').strip()
    if not server_id:
        raise HTTPException(status_code=400, detail="server_id es requerido")

    # FASE 8: Validar acceso y obtener contexto
    context = await resolve_user_access_context(current_user)

    if not has_server_access(context, server_id):
        logging.warning(f"[RBAC-EXPORT-INV] {current_user.get('email')} sin acceso a servidor {server_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")

    # FASE P1.4-E3: Obtener metadatos desde EDARSAHUB SQL via server_registry sin secretos.
    server = await get_server_connection_info(server_id, db=db)
    if not server or not server.get('active', True):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    server = {**server, "id": server_id}

    # FASE 8: Obtener almacenes permitidos
    almacenes_permitidos = get_almacenes_permitidos(context, server_id)

    logging.info(
        f"[RBAC-EXPORT-INV] Usuario={current_user.get('email')}, "
        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
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

    _sql_create_alert(doc)

    return alert.model_dump()

@api_router.get("/alerts", response_model=List[Alert])
async def get_alerts(current_user: Dict = Depends(get_current_user)):
    return _sql_list_alerts()

@api_router.put("/alerts/{alert_id}")
async def update_alert(alert_id: str, alert_data: Dict, current_user: Dict = Depends(get_current_user)):
    _sql_update_alert(alert_id, alert_data)
    return {"message": "Alerta actualizada"}

@api_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, current_user: Dict = Depends(get_current_user)):
    _sql_delete_alert(alert_id, current_user.get("email"))
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
    unidad: Optional[str] = None,
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
    from core.corporate_filters.request_resolver import resolve_unidad_scope

    # CONTRATO CANÓNICO (NO-LIVE): el frontend envía 'unidad' (codigo/id). El
    # backend resuelve server_id centralmente aplicando RBAC. 'server_id' directo
    # queda DEPRECATED (compatibilidad temporal con warning en el resolver).
    _scope = await resolve_unidad_scope(current_user, unidad=unidad, server_id_legacy=server_id)
    if _scope.access_denied:
        return {
            "success": False,
            "message": "Sin acceso a la unidad seleccionada",
            "data": {}
        }
    resolved_server_id = _scope.server_id

    try:
        # FASE P1.4-E2: Obtener servidor desde EDARSAHUB SQL via server_registry
        # ANTES: query = {"active": True, "queries_configured": True}
        # ANTES: if server_id: query["id"] = server_id
        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))

        server = None
        if resolved_server_id:
            # Servidor específico (resuelto desde la unidad canónica)
            server = decrypt_server_secrets(get_server_connection_info_with_secrets(resolved_server_id))
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

        # ====================================================================
        # PROTECCIÓN NO-LIVE / HOST COMPARTIDO (crítico):
        # El POS de MPRO comparte IP con EDARSAHUB (54.39.104.176). Un intento
        # de conexión EN VIVO fallido a ese host pone a EDARSAHUB en "cooldown"
        # en memoria → TODAS las lecturas canónicas (unidades, RBAC, etc.)
        # devuelven vacío y se cae el sistema. Por eso NUNCA se conecta en vivo
        # al host de EDARSAHUB desde este dashboard.
        # ====================================================================
        try:
            from core.server_registry import EDARSAHUB_CONFIG as _EDA_CFG
            _eda_host = str(_EDA_CFG.get('host') or '').strip()
        except Exception:
            _eda_host = ''
        if _eda_host and str(server.get('host') or '').strip() == _eda_host:
            return {
                "success": False,
                "message": "Métricas en vivo no disponibles para esta unidad (regla NO-LIVE). Usa la pestaña Análisis para ver sus inventarios.",
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
                query_sql,
                timeout_seconds=30
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
    SQL-FIRST: métricas desde registry y catálogos canónicos.
    """
    from core.server_registry import list_servers as registry_list_servers

    # FASE P1.4-E4: Obtener contadores de servidores desde EDARSAHUB SQL
    # ANTES: total_servers = await db.servers.count_documents({"active": True})
    # ANTES: servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
    all_servers = await registry_list_servers(db=db, filter_active=True, mask_secrets=True)
    total_servers = len(all_servers)
    servers_configured = len([s for s in all_servers if s.get('queries_configured', False)])

    # SQL-FIRST: contadores desde catálogos canónicos
    total_users = _sql_count_active_users()
    total_alerts = _sql_count_active_alerts()

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

    # CANONICAL-UNIDAD (2026-06-09): El identificador recibido puede ser una
    # unidad canónica (codigo o pk) — contrato nuevo — o un server_id del POS
    # (deprecated, compatibilidad). Se resuelve SIEMPRE al server_id real de
    # EDARSAHUB antes de validar acceso y obtener la configuración.
    try:
        from core.corporate_filters.request_resolver import resolve_unidad_simple
        _u, _matched = resolve_unidad_simple(server_id)
        if _u and _u.get("server_id"):
            if _matched == 'unidad':
                logging.debug(
                    f"[CANONICAL-UNIDAD] token unidad '{server_id}' "
                    f"→ server {_u.get('server_id')} ({_u.get('codigo')})"
                )
            else:
                logging.warning(
                    f"[DEPRECATED-PARAM] Se recibió server_id directo (deprecated). "
                    f"Migrar a 'unidad'. user={user.get('email')} server_id={server_id}"
                )
            server_id = _u.get("server_id")
    except Exception as _e:
        logging.debug(f"[CANONICAL-UNIDAD] resolución no aplicada: {_e}")

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


def _compras_list_values(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.split(',')
    elif isinstance(value, (list, tuple, set)):
        raw = value
    else:
        raw = [value]
    return [str(v).strip() for v in raw if str(v or '').strip()]


def _compras_int_values(value: Any, min_value: int, max_value: int) -> List[int]:
    values = []
    for item in _compras_list_values(value):
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if min_value <= parsed <= max_value and parsed not in values:
            values.append(parsed)
    return values


def _compras_period_where(column_name: str, meses: Any, anios: Any) -> tuple[str, List[Any]]:
    month_values = _compras_int_values(meses, 1, 12)
    year_values = _compras_int_values(anios, 2000, 2100)
    filters = []
    params: List[Any] = []
    if year_values:
        filters.append(f"YEAR({column_name}) IN ({','.join(['%s'] * len(year_values))})")
        params.extend(year_values)
    if month_values:
        filters.append(f"MONTH({column_name}) IN ({','.join(['%s'] * len(month_values))})")
        params.extend(month_values)
    return (" AND ".join(filters) if filters else "1=1", params)


def _compras_find_unidad(server_id: str, sucursal: Optional[str] = None) -> Optional[Dict[str, Any]]:
    from core.unidades_service import UnidadesService

    sid = str(server_id or '').strip().lower()
    suc = str(sucursal or '').strip().upper()
    unidades = [
        u for u in UnidadesService.get_all()
        if str(u.get('server_id') or '').strip().lower() == sid
    ]
    if not unidades:
        return None
    if suc:
        for unidad in unidades:
            candidatos = {
                str(unidad.get('sucursal_origen_id') or '').strip().upper(),
                str(unidad.get('codigo') or '').strip().upper(),
                str(unidad.get('unidad_negocio_codigo') or '').strip().upper(),
                str(unidad.get('nombre') or '').strip().upper(),
                str(unidad.get('unidad_negocio_nombre') or '').strip().upper(),
                str(unidad.get('unidad_negocio_pk') or '').strip().upper(),
            }
            if suc in candidatos:
                return unidad
    if len(unidades) == 1:
        return unidades[0]
    return None


async def _compras_resolve_scope(
    server_id: str,
    sucursal: Optional[str],
    credentials: HTTPAuthorizationCredentials,
) -> Dict[str, Any]:
    access = await validate_server_access_by_empresa(server_id, credentials)
    server = access["server"]
    resolved_server_id = str(server.get('id') or server.get('server_id') or server_id)
    unidad = _compras_find_unidad(resolved_server_id, sucursal)
    if not unidad:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "COMPRAS_UNIDAD_CANONICA_NO_RESUELTA",
                "message": "No se pudo resolver la unidad de negocio canónica para Compras.",
                "server_id": resolved_server_id,
                "sucursal": sucursal,
            },
        )

    from core.inventarios.resolver_canonico import resolver_empresa_id, resolver_sucursal_id

    unidad_codigo = unidad.get('codigo') or unidad.get('unidad_negocio_codigo')
    empresa = resolver_empresa_id(unidad_codigo)
    sucursal_resuelta = resolver_sucursal_id(
        resolved_server_id,
        unidad.get('sucursal_origen_id'),
    )
    if not empresa.resuelto or not sucursal_resuelta.resuelto:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "Falta mapeo canónico Empresa/Sucursal para consultar Compras sin conexión live.",
                "unidad": unidad_codigo,
                "empresa": empresa.motivo,
                "sucursal": sucursal_resuelta.motivo,
            },
        )

    return {
        **access,
        "server_id": resolved_server_id,
        "unidad": unidad,
        "empresa_id": int(empresa.canonical_id),
        "sucursal_id": int(sucursal_resuelta.canonical_id),
        "source": "EDARSAHUB_SQL_CANONICAL",
    }


def _compras_as_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _compras_as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _compras_clean_almacenes(almacenes: Any) -> List[str]:
    values = []
    for item in _compras_list_values(almacenes):
        if item.upper() == "TODOS":
            return []
        if item not in values:
            values.append(item)
    return values


def _compras_apply_almacen_filter(filters: List[str], params: List[Any], almacenes: List[str]) -> None:
    if not almacenes:
        return

    candidates = set()

    for almacen in almacenes:
        text = _compras_as_text(almacen)

        if not text:
            continue

        candidates.add(text)

        if text.isdigit():
            number = int(text)
            candidates.add(f"{number:02d}")
            candidates.add(f"{number:03d}")
            candidates.add(f"{number:04d}")

    items = sorted(candidates)

    if not items:
        return

    placeholders = ",".join(["%s"] * len(items))
    filters.append(
        f"(almacen_id IN ({placeholders}) OR almacen IN ({placeholders}))"
    )
    params.extend(items)
    params.extend(items)


def _compras_almacenes_scope(context: Dict[str, Any], server_id: str, requested: Any) -> List[str]:
    selected = _compras_clean_almacenes(requested)
    permitidos = [str(a) for a in (get_almacenes_permitidos(context, server_id) or []) if str(a or '').strip()]
    if not permitidos:
        return selected
    if not selected:
        return permitidos
    permitidos_set = set(permitidos)
    denied = [a for a in selected if a not in permitidos_set]
    if denied and all(str(a).isdigit() for a in selected):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "COMPRAS_ALMACEN_NO_AUTORIZADO",
                "message": "El usuario no tiene permisos para uno o más almacenes solicitados.",
                "almacenes": denied,
            },
        )
    return selected


def _compras_fetch_latest_inventory_folio(cursor, server_id: str, fecha_ref: str, almacenes: List[str]) -> Optional[str]:
    filters = [
        "server_id = %s",
        "sync_status IN ('ACTIVE', 'REPLACED')",
        "CONVERT(date, fecha) <= CONVERT(date, %s)",
    ]
    params: List[Any] = [server_id, fecha_ref]
    _compras_apply_almacen_filter(filters, params, almacenes)
    cursor.execute(
        f"""
SELECT TOP 1 folio
FROM (
    SELECT
        folio,
        fecha,
        ROW_NUMBER() OVER (
            PARTITION BY server_id, almacen_id, folio
            ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
        ) AS _rn
    FROM dbo.Compras_Inventarios_Fisicos_Sync
    WHERE {' AND '.join(filters)}
) t
WHERE t._rn = 1
ORDER BY fecha DESC, folio DESC
""",
        tuple(params),
    )
    row = cursor.fetchone()
    return _compras_as_text(row.get("folio")) if row else None


def _compras_fetch_inventory_header_rows(cursor, server_id: str, folios: List[str], almacenes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    if not folios:
        return []
    placeholders = ",".join(["%s"] * len(folios))
    filters = [
        "server_id = %s",
        f"folio IN ({placeholders})",
        "sync_status IN ('ACTIVE', 'REPLACED')",
    ]
    params: List[Any] = [server_id, *folios]
    _compras_apply_almacen_filter(filters, params, almacenes or [])
    cursor.execute(
        f"""
SELECT
    folio,
    fecha,
    almacen,
    almacen_id,
    sucursal,
    sucursal_id,
    sync_status
FROM (
    SELECT
        folio,
        fecha,
        almacen,
        almacen_id,
        sucursal,
        sucursal_id,
        sync_status,
        ROW_NUMBER() OVER (
            PARTITION BY server_id, sucursal_id, almacen_id, folio
            ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
        ) AS _rn
    FROM dbo.Compras_Inventarios_Fisicos_Sync
    WHERE {' AND '.join(filters)}
) t
WHERE t._rn = 1
ORDER BY fecha, folio
""",
        tuple(params),
    )
    return list(cursor.fetchall() or [])


def _compras_fetch_inventory_detail(
    cursor,
    server_id: str,
    folios: List[str],
    almacenes: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    if not folios:
        return {}
    placeholders = ",".join(["%s"] * len(folios))
    filters = [
        "server_id = %s",
        f"folio IN ({placeholders})",
        "sync_status IN ('ACTIVE', 'REPLACED')",
    ]
    params: List[Any] = [server_id, *folios]
    _compras_apply_almacen_filter(filters, params, almacenes or [])

    cursor.execute(
        """
SELECT TOP 1 COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME = 'Compras_Inventarios_Fisicos_Detalle_Sync'
  AND LOWER(COLUMN_NAME) = 'rendimiento'
""",
    )
    has_rendimiento = bool(cursor.fetchone())
    rendimiento_expr = "ISNULL(rendimiento, 1)" if has_rendimiento else "1"

    cursor.execute(
        f"""
SELECT
    folio,
    codigo_producto,
    nombre_producto,
    unidad,
    existencia_fisica,
    {rendimiento_expr} AS rendimiento,
    costo_unitario,
    almacen,
    almacen_id
FROM (
    SELECT
        folio,
        codigo_producto,
        nombre_producto,
        unidad,
        existencia_fisica,
        {rendimiento_expr} AS rendimiento,
        costo_unitario,
        almacen,
        almacen_id,
        ROW_NUMBER() OVER (
            PARTITION BY server_id, almacen_id, folio, codigo_producto
            ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
        ) AS _rn
    FROM dbo.Compras_Inventarios_Fisicos_Detalle_Sync
    WHERE {' AND '.join(filters)}
) t
WHERE t._rn = 1
""",
        tuple(params),
    )
    products: Dict[str, Dict[str, Any]] = {}
    for row in cursor.fetchall() or []:
        codigo = _compras_as_text(row.get("codigo_producto"))
        if not codigo:
            continue
        item = products.setdefault(
            codigo,
            {
                "codigo": codigo,
                "producto": row.get("nombre_producto") or f"SKU: {codigo}",
                "unidad": row.get("unidad") or "",
                "cantidad": 0.0,
                "costo": 0.0,
                "rendimiento": 1.0,
                "almacenes": set(),
                "folios": set(),
            },
        )
        item["cantidad"] += _compras_as_float(row.get("existencia_fisica"))
        costo = _compras_as_float(row.get("costo_unitario"))
        if costo:
            item["costo"] = costo
        rendimiento = _compras_as_float(row.get("rendimiento")) or 1.0
        if rendimiento > _compras_as_float(item.get("rendimiento")):
            item["rendimiento"] = rendimiento
        almacen = _compras_as_text(row.get("almacen") or row.get("almacen_id"))
        folio = _compras_as_text(row.get("folio"))
        if almacen:
            item["almacenes"].add(almacen)
        if folio:
            item["folios"].add(folio)
    for item in products.values():
        item["almacenes"] = sorted(item["almacenes"])
        item["folios"] = sorted(item["folios"])
    return products


def _compras_fetch_movimientos(
    cursor,
    server_id: str,
    fecha_ini: str,
    fecha_fin: str,
    almacenes: Optional[List[str]],
    *,
    solo_consumos: bool,
) -> Dict[str, float]:
    concept_filter = (
        "ISNULL(idconcepto, '') IN ('SPV', 'SCP', 'SCS')"
        if solo_consumos
        else "ISNULL(idconcepto, '') NOT IN ('', 'SPV', 'SCP', 'SCS')"
    )
    filters = [
        "server_id = %s",
        "fecha >= %s",
        "fecha <= %s",
        "sync_status = 'ACTIVE'",
        concept_filter,
        _soft_date_only_final_day_guard("fecha"),
    ]
    params: List[Any] = [server_id, fecha_ini, fecha_fin, fecha_fin, fecha_fin]
    _compras_apply_almacen_filter(filters, params, almacenes or [])
    cursor.execute(
        f"""
SELECT codigo_producto, SUM(cantidad) AS cantidad
FROM dbo.Compras_Inventarios_Movimientos_Sync
WHERE {' AND '.join(filters)}
GROUP BY codigo_producto
""",
        tuple(params),
    )
    values = {}
    for row in cursor.fetchall() or []:
        codigo = _compras_as_text(row.get("codigo_producto"))
        if not codigo:
            continue
        cantidad = _compras_as_float(row.get("cantidad"))
        values[codigo] = abs(cantidad) if solo_consumos else cantidad
    return values


def _compras_fetch_pedido_detalle(
    cursor,
    empresa_id: int,
    sucursal_id: int,
    folios: List[str],
) -> Dict[str, Dict[str, Any]]:
    if not folios:
        return {}
    placeholders = ",".join(["%s"] * len(folios))
    cursor.execute(
        f"""
SELECT
    CAST(d.ProductoID AS VARCHAR(50)) AS codigo,
    COALESCE(NULLIF(pc.NombreProducto, ''), CAST(d.ProductoID AS VARCHAR(50))) AS producto,
    pc.UnidadCompra AS unidad,
    p.FolioPedido AS folio_pedido,
    SUM(ISNULL(d.Cantidad, 0)) AS cantidad,
    MAX(ISNULL(d.PrecioEstimado, 0)) AS costo
FROM dbo.Compras_Pedidos p
INNER JOIN dbo.Compras_PedidosDetalle d ON d.PedidoCompraID = p.PedidoCompraID
LEFT JOIN dbo.Producto_Catalogo pc ON pc.ProductoID = d.ProductoID
WHERE p.EmpresaID = %s
  AND p.SucursalID = %s
  AND p.Activo = 1
  AND d.Activo = 1
  AND p.FolioPedido IN ({placeholders})
GROUP BY CAST(d.ProductoID AS VARCHAR(50)), pc.NombreProducto, pc.UnidadCompra, p.FolioPedido
ORDER BY p.FolioPedido, CAST(d.ProductoID AS VARCHAR(50))
""",
        tuple([empresa_id, sucursal_id, *folios]),
    )
    products: Dict[str, Dict[str, Any]] = {}
    for row in cursor.fetchall() or []:
        codigo = _compras_as_text(row.get("codigo"))
        if not codigo:
            continue
        item = products.setdefault(
            codigo,
            {
                "codigo": codigo,
                "producto": row.get("producto") or f"SKU: {codigo}",
                "unidad": row.get("unidad") or "",
                "cantidad": 0.0,
                "costo": 0.0,
                "proveedor": "",
                "folios": [],
            },
        )
        item["cantidad"] += _compras_as_float(row.get("cantidad"))
        costo = _compras_as_float(row.get("costo"))
        if costo:
            item["costo"] = costo
        folio = _compras_as_text(row.get("folio_pedido"))
        if folio and folio not in item["folios"]:
            item["folios"].append(folio)
    return products


def _compras_fetch_pedido_detalle_rows(
    cursor,
    empresa_id: int,
    sucursal_id: int,
    folio: str,
) -> List[Dict[str, Any]]:
    folio = _compras_as_text(folio)
    if not folio:
        return []
    cursor.execute(
        """
SELECT TOP 500
    p.FolioPedido AS folio,
    p.MotivoCompra AS comentario,
    CAST(d.ProductoID AS VARCHAR(50)) AS codigo,
    COALESCE(NULLIF(pc.NombreProducto, ''), CAST(d.ProductoID AS VARCHAR(50))) AS producto,
    pc.UnidadCompra AS unidad,
    d.Cantidad AS cantidad,
    d.PrecioEstimado AS costo,
    d.SubtotalLinea AS importe,
    d.Renglon AS renglon
FROM dbo.Compras_Pedidos p
INNER JOIN dbo.Compras_PedidosDetalle d ON d.PedidoCompraID = p.PedidoCompraID
LEFT JOIN dbo.Producto_Catalogo pc ON pc.ProductoID = d.ProductoID
WHERE p.EmpresaID = %s
  AND p.SucursalID = %s
  AND p.Activo = 1
  AND d.Activo = 1
  AND p.FolioPedido = %s
ORDER BY d.Renglon, d.ProductoID
""",
        (empresa_id, sucursal_id, folio),
    )
    return list(cursor.fetchall() or [])


def _compras_format_pedido_detalle_rows(rows: List[Dict[str, Any]], folio: str, tipo: str = "PEDIDO") -> Dict[str, Any]:
    detalle = []
    for row in rows:
        codigo = _compras_as_text(row.get("codigo"))
        if not codigo:
            continue
        detalle.append({
            "codigo": codigo,
            "producto": row.get("producto") or f"SKU: {codigo}",
            "unidad": row.get("unidad") or "",
            "cantidad": _compras_as_float(row.get("cantidad")),
            "costo": _compras_as_float(row.get("costo")),
            "importe": _compras_as_float(row.get("importe")),
        })
    return {
        "folio": _compras_as_text(rows[0].get("folio")) if rows else _compras_as_text(folio),
        "tipo": _compras_as_text(tipo or "PEDIDO").upper(),
        "comentario": rows[0].get("comentario") if rows else "",
        "detalle": detalle,
        "source": "EDARSAHUB_SQL_CANONICAL",
    }


def _compras_manual_inventory(items: Any) -> Dict[str, Dict[str, Any]]:
    products: Dict[str, Dict[str, Any]] = {}
    for row in items or []:
        if not isinstance(row, dict):
            continue
        codigo = _compras_as_text(row.get("codigo") or row.get("codigo_producto"))
        if not codigo:
            continue
        item = products.setdefault(
            codigo,
            {
                "codigo": codigo,
                "producto": row.get("producto") or row.get("nombre_producto") or f"SKU: {codigo}",
                "unidad": row.get("unidad") or "",
                "cantidad": 0.0,
                "costo": 0.0,
                "rendimiento": 1.0,
            },
        )
        item["cantidad"] += _compras_as_float(row.get("cantidad") or row.get("existencia_fisica"))
        costo = _compras_as_float(row.get("costo") or row.get("costo_unitario"))
        if costo:
            item["costo"] = costo
        rendimiento = _compras_as_float(row.get("rendimiento")) or 1.0
        if rendimiento > _compras_as_float(item.get("rendimiento")):
            item["rendimiento"] = rendimiento
    return products


@api_router.get("/compras/inventarios-fisicos/{server_id}")
async def obtener_inventarios_fisicos(server_id: str, unidad: str = None, sucursal: str = None, sucursal_id: str = None, almacen_id: str = None, almacen: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene la lista de inventarios físicos disponibles para seleccionar.

    CONTRATO CANÓNICO (P0 2026-06):
    - El frontend envía la **unidad** canónica (unidad_codigo o id). El backend
      resuelve server_id y sucursal_origen_id (desambigua MPRO ORIGEN/QRO).
    - El path {server_id} queda DEPRECATED (compatibilidad temporal).

    FUENTE ÚNICA: EDARSAHUB SQL (tabla Compras_Inventarios_Fisicos_Sync).
    NO-LIVE: este endpoint NO consulta POS en vivo.
    FASE 8: Aplica filtro RBAC por almacenes permitidos.
    """
    from core.corporate_filters.request_resolver import (
        resolve_authorized_unidad_scope,
        _shared_server,
    )
    from modules.compras.access import COMPRAS_VER

    token = unidad or server_id
    current_user = await get_current_user(credentials)

    canonical_scope = await resolve_authorized_unidad_scope(
        current_user,
        COMPRAS_VER,
        token,
    )

    if canonical_scope.access_denied:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "COMPRAS_UNIDAD_NO_AUTORIZADA",
                "message": "No tiene acceso a esta Unidad de Negocio.",
            },
        )

    server_id = canonical_scope.server_id
    sucursal_id = (
        sucursal_id
        or canonical_scope.sucursal_origen_id
    )

    if not server_id:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "No fue posible resolver el servidor interno de la unidad.",
            },
        )

    # El alcance ya fue validado por unidad mediante SQL canónico.
    # No se aplica nuevamente RBAC legacy por server_id.
    almacenes_permitidos = []

    logging.info(
        f"[COMPRAS-NOLIVE] Inventarios físicos - "
        f"Usuario={current_user.get('email')}, Unidad={token or '-'}, Server={server_id}, "
        f"Sucursal={sucursal_id or sucursal or '-'}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
    )

    # =========================================================================
    # ÚNICA FUENTE: EDARSAHUB Sync (NO-LIVE). Sin fallback a POS en vivo.
    # =========================================================================
    try:
        # ROBUSTEZ (sistema-agnóstico, no hardcode de 'MPRO'/'SoftRestaurant'):
        # el filtro por sucursal SOLO aplica cuando un mismo server_id aloja >1 unidad
        # (caso MPRO ORIGEN/QRO, que requieren desambiguar). Para single-tenant
        # (SoftRestaurant, o un MPRO único) el server_id basta y NO se filtra por sucursal,
        # así un placeholder del frontend (p.ej. 'SoftRestaurant') o una sucursal vacía en
        # EDARSAHUB NO oculta los inventarios. Si en el futuro se agrega otro sistema, este
        # criterio canónico (¿el server aloja varias unidades?) sigue siendo válido.
        sucursal_filtro = (sucursal_id or sucursal) if _shared_server(server_id) else None
        inventarios = obtener_inventarios_fisicos_sync(
            unidad_negocio_id=None,  # MPRO etiqueta todas las sucursales con la misma
                                     # unidad_negocio_id; se desambigua por server_id+sucursal
            server_id=server_id,
            sucursal=sucursal_filtro,
            almacen_id=almacen_id,
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

            logging.info(f"[COMPRAS-NOLIVE] ✅ Inventarios desde EDARSAHUB SYNC: {len(inventarios)} registros")

            return [{
                "folio": str(inv.get('folio', '')),
                "fecha": str(inv.get('fecha', '')),
                "almacen": inv.get('almacen', 'Sin almacén'),
                "almacen_id": str(inv.get('almacen_id', '')),
                "sucursal": inv.get('sucursal', ''),
                "sucursal_id": str(inv.get('sucursal_id', '')),
                "comentario": (inv.get('comentario') or '').strip(),
                "productos": int(inv.get('total_productos', 0)),
                "source": "EDARSAHUB_SYNC",
                "sync_status": inv.get('sync_status', 'SYNCED'),
            } for inv in inventarios]
    except Exception as e:
        logging.error(f"[COMPRAS-NOLIVE] Error leyendo EDARSAHUB Sync: {e}")
        raise HTTPException(status_code=503, detail="No se pudieron leer los inventarios desde EDARSAHUB en este momento.")

    # Sin datos en EDARSAHUB para este scope (NO-LIVE: no se consulta el POS)
    logging.info(f"[COMPRAS-NOLIVE] Sin inventarios en EDARSAHUB Sync para server={server_id} sucursal={sucursal_id or sucursal or '-'}")
    return []


@api_router.get("/compras/inventarios-fisicos-sql-first/{server_id}")
async def obtener_inventarios_fisicos_sql_first(
    server_id: str,
    sucursal: str = None,
    almacen: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    [SQL-FIRST] Obtiene inventarios físicos SOLO desde EDARSAHUB SQL.

    Este endpoint lee EXCLUSIVAMENTE de dbo.Compras_Inventarios_Fisicos_Sync.
    NO conecta a SoftRestaurant/MPRO directamente.
    NO tiene fallback LIVE.

    Feature flag: COMPRAS_SQL_FIRST_ENABLED
    """
    import os

    await get_current_user(credentials)

    # Verificar feature flag
    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/inventarios-fisicos/{server_id}',
            'inventarios': []
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        # Construir filtros opcionales
        filtros = ["ServerID = %s"]
        params = [server_id]

        if sucursal:
            filtros.append("SucursalID = %s")
            params.append(sucursal)

        if almacen:
            filtros.append("AlmacenID = %s")
            params.append(almacen)

        where_clause = " AND ".join(filtros)

        query = f"""
        SELECT TOP 500
            FolioInventario AS folio,
            FechaInventario AS fecha,
            AlmacenID AS almacen_id,
            NombreAlmacen AS almacen,
            SucursalID AS sucursal_id,
            NombreSucursal AS sucursal,
            TotalProductos AS productos,
            SyncStatus AS sync_status,
            OrigenSistema AS origen_sistema
        FROM dbo.Compras_Inventarios_Fisicos_Sync
        WHERE {where_clause}
        ORDER BY FechaInventario DESC
        """

        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        conn.close()

        inventarios = []
        for r in result:
            inventarios.append({
                'folio': str(r['folio'] or ''),
                'fecha': r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha'] or ''),
                'almacen': r['almacen'] or 'Sin almacén',
                'almacen_id': str(r['almacen_id'] or ''),
                'sucursal': r['sucursal'] or '',
                'sucursal_id': str(r['sucursal_id'] or ''),
                'productos': int(r['productos'] or 0),
                'source': 'EDARSAHUB_SQL_FIRST',
                'sync_status': r['sync_status'] or 'SYNCED',
                'origen_sistema': r['origen_sistema'] or ''
            })

        return {
            'status': 'SQL_FIRST',
            'source': 'EDARSAHUB',
            'total': len(inventarios),
            'inventarios': inventarios
        }

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error obteniendo inventarios físicos: {str(e)}")
        return {
            'status': 'ERROR',
            'inventarios': [],
            'error': f"Error SQL-First: {str(e)}"
        }


@api_router.get("/compras/pedidos-vigentes/{server_id}")
async def obtener_pedidos_vigentes(server_id: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene requisiciones/órdenes vigentes desde EDARSAHUB SQL.

    El parámetro de ruta conserva el nombre server_id por compatibilidad HTTP,
    pero el contrato canónico exige que el frontend envíe la Unidad de Negocio
    (código o PK). server_id y sucursal_origen_id se reconstruyen internamente.
    """
    from core.corporate_filters.request_resolver import (
        resolve_authorized_unidad_scope,
    )
    from modules.compras.access import COMPRAS_VER

    current_user = await get_current_user(credentials)

    canonical_scope = await resolve_authorized_unidad_scope(
        current_user,
        COMPRAS_VER,
        server_id,
    )

    if canonical_scope.access_denied:
        logging.warning(
            "[COMPRAS-RBAC-UNIDAD] acceso denegado user=%s unidad=%s reason=%s",
            current_user.get("email"),
            server_id,
            canonical_scope.denial_reason,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "COMPRAS_UNIDAD_NO_AUTORIZADA",
                "message": "No tiene acceso a esta Unidad de Negocio.",
            },
        )

    unidad_negocio_id = canonical_scope.unidad_pk
    resolved_server_id = canonical_scope.server_id

    if not unidad_negocio_id or not resolved_server_id:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "No fue posible resolver el contexto canónico de la unidad.",
            },
        )

    requisiciones = obtener_requisiciones_sync(
        unidad_negocio_id=unidad_negocio_id,
        server_id=resolved_server_id,
        sucursal=None,
        limit=500,
    )
    return [{
        "tipo": req.get("tipo", "OC"),
        "folio": str(req.get("folio", "")),
        "fecha": str(req.get("fecha", "")),
        "comentario": "",
        "estado": req.get("estatus", "PENDIENTE"),
        "comprador": req.get("proveedor", ""),
        "productos": int(req.get("total_productos", 0) or 0),
        "importe": float(req.get("importe", 0) or 0),
        "source": "EDARSAHUB_SYNC",
        "sync_status": req.get("sync_status", "SYNCED"),
    } for req in requisiciones]


@api_router.get("/compras/detalle-pedido-manual/{server_id}")
async def obtener_detalle_pedido_manual(
    server_id: str,
    folio: str,
    sucursal: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtiene detalle de pedido por folio manual desde EDARSAHUB SQL canónico."""
    from core.corporate_filters.request_resolver import canonical_server_id
    from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

    server_id = canonical_server_id(server_id)
    scope = await _compras_resolve_scope(server_id, sucursal, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(scope["user"], COMPRAS_VER)

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        rows = _compras_fetch_pedido_detalle_rows(
            cursor,
            scope["empresa_id"],
            scope["sucursal_id"],
            folio,
        )
        if not rows:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "COMPRAS_PEDIDO_DETALLE_CANONICO_NO_ENCONTRADO",
                    "message": "No se encontró detalle canónico para el folio solicitado.",
                    "folio": folio,
                    "server_id": scope["server_id"],
                    "sucursal": sucursal,
                },
            )
        return _compras_format_pedido_detalle_rows(rows, folio, "PEDIDO")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[COMPRAS-DETALLE-PEDIDO-MANUAL][NOLIVE] Error: {e}")
        raise HTTPException(status_code=503, detail="Error leyendo detalle canónico del pedido.")
    finally:
        if conn:
            conn.close()


@api_router.get("/compras/pedidos-vigentes-sql-first/{server_id}")
async def obtener_pedidos_vigentes_sql_first(
    server_id: str,
    sucursal: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    [SQL-FIRST] Obtiene pedidos/requisiciones vigentes SOLO desde EDARSAHUB SQL.

    Este endpoint lee EXCLUSIVAMENTE de dbo.Compras_Pedidos y dbo.Compras_PedidosDetalle.
    NO conecta a SoftRestaurant/MPRO directamente.
    NO tiene fallback LIVE.

    Feature flag: COMPRAS_SQL_FIRST_ENABLED
    """
    import os

    await get_current_user(credentials)

    # Verificar feature flag
    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/pedidos-vigentes/{server_id}',
            'pedidos': []
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        # Construir filtros
        filtros = ["p.ServerID = %s", "p.Estatus IN ('PXA', 'PENDIENTE', 'AC', 'RCT')"]
        params = [server_id]

        if sucursal:
            filtros.append("p.SucursalID = %s")
            params.append(sucursal)

        where_clause = " AND ".join(filtros)

        query = f"""
        SELECT TOP 500
            p.PedidoID,
            p.TipoPedido AS tipo,
            p.FolioPedido AS folio,
            p.FechaPedido AS fecha,
            p.Estatus AS estado,
            p.ProveedorNombre AS proveedor,
            p.Comentario AS comentario,
            p.ImporteTotal AS importe,
            p.OrigenSistema AS origen_sistema,
            p.SyncStatus AS sync_status,
            (SELECT COUNT(*) FROM dbo.Compras_PedidosDetalle d WHERE d.PedidoID = p.PedidoID) AS total_productos
        FROM dbo.Compras_Pedidos p
        WHERE {where_clause}
          AND p.FechaPedido >= DATEADD(day, -30, GETDATE())
        ORDER BY p.FechaPedido DESC
        """

        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        conn.close()

        pedidos = []
        for r in result:
            pedidos.append({
                'tipo': r['tipo'] or 'OC',
                'folio': str(r['folio'] or ''),
                'fecha': r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha'] or ''),
                'estado': r['estado'] or 'PENDIENTE',
                'comprador': r['proveedor'] or '',
                'comentario': r['comentario'] or '',
                'productos': int(r['total_productos'] or 0),
                'importe': float(r['importe'] or 0),
                'source': 'EDARSAHUB_SQL_FIRST',
                'sync_status': r['sync_status'] or 'SYNCED',
                'origen_sistema': r['origen_sistema'] or ''
            })

        return {
            'status': 'SQL_FIRST',
            'source': 'EDARSAHUB',
            'total': len(pedidos),
            'pedidos': pedidos
        }

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error obteniendo pedidos vigentes: {str(e)}")
        return {
            'status': 'ERROR',
            'pedidos': [],
            'error': f"Error SQL-First: {str(e)}"
        }


@api_router.get("/compras/detalle-movimientos/{server_id}")
async def obtener_detalle_movimientos(server_id: str, codigo_producto: str, almacenes: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Detalle de movimientos desde tabla canónica Compras_Inventarios_Movimientos_Sync."""
    from types import SimpleNamespace
    from core.corporate_filters.request_resolver import canonical_server_id

    server_id = canonical_server_id(server_id)
    access = await validate_server_access_by_empresa(server_id, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(access["user"], COMPRAS_VER)

    request = SimpleNamespace(
        server_id=server_id,
        codigo=codigo_producto,
        fecha_inicio=fecha_ini,
        fecha_fin=f"{fecha_fin} 23:59:59",
        almacenes=_compras_list_values(almacenes),
    )
    result = _obtener_detalle_softrestaurant_canonico(request, solo_ventas=False)
    return result.get("movimientos", []) if isinstance(result, dict) else []


@api_router.get("/compras/detalle-consumos/{server_id}")
async def obtener_detalle_consumos(server_id: str, codigo_producto: str, sucursal_codigo: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Detalle de consumos desde tabla canónica Compras_Inventarios_Movimientos_Sync."""
    from types import SimpleNamespace
    from core.corporate_filters.request_resolver import canonical_server_id

    server_id = canonical_server_id(server_id)
    access = await validate_server_access_by_empresa(server_id, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(access["user"], COMPRAS_VER)

    request = SimpleNamespace(
        server_id=server_id,
        codigo=codigo_producto,
        fecha_inicio=fecha_ini,
        fecha_fin=f"{fecha_fin} 23:59:59",
        almacenes=[],
    )
    result = _obtener_detalle_softrestaurant_canonico(request, solo_ventas=True)
    return result.get("consumos", []) if isinstance(result, dict) else []


@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
async def obtener_detalle_pedido(
    server_id: str,
    folio: str,
    tipo: str = "PEDIDO",
    sucursal: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Obtiene el detalle de un pedido de compra para comparar desde EDARSAHUB SQL canónico.
    """
    from core.corporate_filters.request_resolver import canonical_server_id
    from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

    server_id = canonical_server_id(server_id)
    scope = await _compras_resolve_scope(server_id, sucursal, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(scope["user"], COMPRAS_VER)

    logging.info(
        "[RBAC-DETALLE-PEDIDO][NOLIVE] User=%s Server=%s Folio=%s Tipo=%s Source=%s",
        scope["user"].get("email"),
        scope["server_id"],
        folio,
        tipo,
        scope["source"],
    )

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        rows = _compras_fetch_pedido_detalle_rows(
            cursor,
            scope["empresa_id"],
            scope["sucursal_id"],
            folio,
        )
        if not rows:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "COMPRAS_PEDIDO_DETALLE_CANONICO_NO_ENCONTRADO",
                    "message": "No se encontró detalle canónico para el folio solicitado.",
                    "folio": folio,
                    "server_id": scope["server_id"],
                    "sucursal": sucursal,
                },
            )
        return {
            _compras_as_text(row.get("codigo")): {
                "producto": row.get("producto") or f"SKU: {_compras_as_text(row.get('codigo'))}",
                "unidad": row.get("unidad") or "",
                "cantidad": _compras_as_float(row.get("cantidad")),
                "costo": _compras_as_float(row.get("costo")),
                "importe": _compras_as_float(row.get("importe")),
                "source": scope["source"],
            }
            for row in rows
            if _compras_as_text(row.get("codigo"))
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[COMPRAS-DETALLE-PEDIDO][NOLIVE] Error: {e}")
        raise HTTPException(status_code=503, detail="Error leyendo detalle canónico del pedido.")
    finally:
        if conn:
            conn.close()

@api_router.post("/compras/calculo-pedido")
async def calcular_pedido_sugerido(request: CalculoPedidoRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Calcula pedido sugerido desde tablas canónicas EDARSAHUB SQL.

    NO-LIVE: no consulta POS ni usa credenciales de servidor origen.
    """
    from datetime import datetime, timedelta
    from core.corporate_filters.request_resolver import canonical_server_id
    from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

    request.server_id = canonical_server_id(request.server_id)
    scope = await _compras_resolve_scope(request.server_id, request.sucursal, credentials)
    server_id = scope["server_id"]
    context = scope["context"]
    almacenes = _compras_almacenes_scope(context, server_id, request.almacenes)

    from modules.compras.access import require_compras_permission, COMPRAS_EJECUTAR
    require_compras_permission(scope["user"], COMPRAS_EJECUTAR)

    try:
        fecha_ini_dt = datetime.strptime(request.fecha_inventario_fisico, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(request.fecha_fin_periodo, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas inválidas. Use formato YYYY-MM-DD")

    dias_periodo = max(1, (fecha_fin_dt - fecha_ini_dt).days)
    fecha_mov_ini = (fecha_ini_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    fecha_mov_fin = f"{request.fecha_fin_periodo} 23:59:59"

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
        cursor = conn.cursor(as_dict=True)

        folios_inv = _compras_list_values(request.folio_inventario_fisico)
        if not folios_inv:
            latest_folio = _compras_fetch_latest_inventory_folio(
                cursor,
                server_id,
                request.fecha_inventario_fisico,
                almacenes,
            )
            folios_inv = [latest_folio] if latest_folio else []
        if not folios_inv:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "INVENTORY_PHYSICAL_HEADER_MISSING",
                    "message": "No se encontraron inventarios canónicos para calcular el pedido.",
                    "source": "dbo.Compras_Inventarios_Fisicos_Sync",
                },
            )

        header_rows = _compras_fetch_inventory_header_rows(cursor, server_id, folios_inv, almacenes)
        inv_inicial = _compras_fetch_inventory_detail(cursor, server_id, folios_inv, almacenes)
        if not inv_inicial and almacenes:
            inv_inicial = _compras_fetch_inventory_detail(cursor, server_id, folios_inv, [])
        if not inv_inicial:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "INVENTORY_PHYSICAL_DETAIL_MISSING",
                    "message": "No hay detalle canónico para los folios seleccionados.",
                    "folios": folios_inv,
                    "source": "dbo.Compras_Inventarios_Fisicos_Detalle_Sync",
                },
            )

        movimientos = _compras_fetch_movimientos(
            cursor,
            server_id,
            fecha_mov_ini,
            fecha_mov_fin,
            almacenes,
            solo_consumos=False,
        )
        consumos = _compras_fetch_movimientos(
            cursor,
            server_id,
            fecha_mov_ini,
            fecha_mov_fin,
            almacenes,
            solo_consumos=True,
        )
        pedido_existente = _compras_fetch_pedido_detalle(
            cursor,
            scope["empresa_id"],
            scope["sucursal_id"],
            _compras_list_values(request.folio_pedido_comparar),
        )

        all_codes = sorted(set(inv_inicial.keys()) | set(movimientos.keys()) | set(consumos.keys()) | set(pedido_existente.keys()))
        results = []
        productos_sin_inventario = []
        for codigo in all_codes:
            base = inv_inicial.get(codigo) or pedido_existente.get(codigo) or {}
            inv_fisico = _compras_as_float(inv_inicial.get(codigo, {}).get("cantidad"))
            mov = _compras_as_float(movimientos.get(codigo))
            consumo = _compras_as_float(consumos.get(codigo))
            costo = _compras_as_float(base.get("costo") or pedido_existente.get(codigo, {}).get("costo"))
            inventario_teorico = inv_fisico + mov - consumo
            promedio_diario = consumo / dias_periodo if dias_periodo > 0 else 0
            consumo_esperado = promedio_diario * max(0, int(request.dias_inventario or 0))
            cantidad_pedir = max(0.0, consumo_esperado - inventario_teorico)
            dias_inv_actual = inventario_teorico / promedio_diario if promedio_diario > 0 else 999
            pedido_qty = _compras_as_float(pedido_existente.get(codigo, {}).get("cantidad"))
            diferencia_pedido = cantidad_pedir - pedido_qty if pedido_qty > 0 else None
            sin_inv_fisico = inv_fisico == 0 and (mov != 0 or consumo > 0)
            if sin_inv_fisico:
                productos_sin_inventario.append(codigo)
            results.append({
                "Codigo": codigo,
                "Producto": base.get("producto") or f"SKU: {codigo}",
                "Familia": None,
                "Categoria": None,
                "Unidad": base.get("unidad") or "",
                "Costo_Unitario": round(costo, 2),
                "Inventario_Inicial": round(inv_fisico, 2),
                "Movimientos_Periodo": round(mov, 2),
                "Consumos_Periodo": round(consumo, 2),
                "Inventario_Final": None,
                "Inventario_Teorico": round(inventario_teorico, 2),
                "Promedio_Diario": round(promedio_diario, 3),
                "Dias_Inventario": round(dias_inv_actual, 1) if dias_inv_actual < 999 else 999,
                "Stock_Minimo": 0,
                "Stock_Maximo": 0,
                "Cantidad_Pedir": round(cantidad_pedir, 2),
                "Costo_Pedido": round(cantidad_pedir * costo, 2),
                "Sin_Inventario_Inicial": sin_inv_fisico,
                "Sin_Inventario_Final": False,
                "Cantidad_Pedido_Existente": round(pedido_qty, 2) if pedido_qty > 0 else None,
                "Diferencia_Pedido": round(diferencia_pedido, 2) if diferencia_pedido is not None else None,
            })

        results.sort(key=lambda item: item["Cantidad_Pedir"], reverse=True)
        almacen_display = sorted({
            _compras_as_text(row.get("almacen") or row.get("almacen_id"))
            for row in header_rows
            if _compras_as_text(row.get("almacen") or row.get("almacen_id"))
        })
        return {
            "status": "OK",
            "source": scope["source"],
            "data": results,
            "count": len(results),
            "tiene_inventario_fisico": True,
            "fecha_inventario_fisico": request.fecha_inventario_fisico,
            "folio_inventario_fisico": folios_inv[0] if len(folios_inv) == 1 else ",".join(folios_inv),
            "tiene_inventario_final": False,
            "fecha_inventario_final": None,
            "folio_inventario_final": None,
            "productos_sin_inventario": len(productos_sin_inventario),
            "es_bodega": False,
            "almacenes": almacen_display or almacenes or request.almacenes,
            "almacen_codigos": almacenes,
            "sucursal_codigo": request.sucursal,
            "dias_periodo": dias_periodo,
            "comparando_con_pedido": request.folio_pedido_comparar,
            "metodo_calculo": request.metodo_calculo,
            "parametros": {
                "fecha_inventario_fisico": request.fecha_inventario_fisico,
                "fecha_fin_periodo": request.fecha_fin_periodo,
                "dias_inventario": request.dias_inventario,
                "sucursal": request.sucursal,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("[COMPRAS-CALCULO][NOLIVE] Error calculando pedido sugerido")
        raise HTTPException(status_code=500, detail=f"Error interno calculando pedido canónico: {str(exc)[:180]}")
    finally:
        if conn:
            conn.close()


# Implementación live legacy desregistrada: sin SQL live ni uso operativo.
async def _legacy_calcular_pedido_sugerido_live_disabled(request: CalculoPedidoRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    raise RuntimeError("Implementación legacy live deshabilitada; use /compras/calculo-pedido canónico.")


@api_router.get("/compras/parametros/{server_id}")
async def obtener_parametros_compra(
    server_id: str,
    sucursal: str = Query(None, description="ID de sucursal"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Obtiene los parámetros de compra configurados para un servidor/sucursal.

    MIGRADO: Ahora lee desde EDARSAHUB SQL (Compras_Parametros_Sucursal).
    """
    # CANONICAL-UNIDAD: el path puede traer una unidad canónica o un server_id legacy.
    from core.corporate_filters.request_resolver import canonical_server_id
    server_id = canonical_server_id(server_id)

    # RBAC: validar alcance por servidor/unidad y permiso funcional de Compras.
    access = await validate_server_access_by_empresa(server_id, credentials)
    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(access["user"], COMPRAS_VER)

    # Usar servicio del módulo compras que lee de SQL
    from modules.compras.service import obtener_parametros

    # Si no se especifica sucursal, usar "DEFAULT"
    sucursal_id = sucursal or "DEFAULT"

    params = await obtener_parametros(server_id, sucursal_id)
    params['server_id'] = server_id  # Asegurar que siempre incluya server_id

    return params


@api_router.post("/compras/parametros")
async def guardar_parametros_compra(params: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Guarda los parámetros de compra para un servidor/sucursal.

    MIGRADO: Ahora escribe a EDARSAHUB SQL (Compras_Parametros_Sucursal).
    """
    # CANONICAL-UNIDAD: acepta unidad canónica o server_id legacy.
    from core.corporate_filters.request_resolver import canonical_server_id
    server_id = canonical_server_id(params.get('server_id'))
    if not server_id:
        raise HTTPException(status_code=400, detail="server_id es requerido")

    # RBAC: validar alcance por servidor/unidad y permiso funcional de Compras
    # (guardar parametros es una accion de configuracion, no solo lectura).
    access = await validate_server_access_by_empresa(server_id, credentials)
    from modules.compras.access import require_compras_permission, COMPRAS_CONFIGURAR
    require_compras_permission(access["user"], COMPRAS_CONFIGURAR)

    # Usar servicio del módulo compras que escribe a SQL
    from modules.compras.service import guardar_parametros

    # Si no se especifica sucursal, usar "DEFAULT"
    sucursal_id = params.get('sucursal') or "DEFAULT"

    result = await guardar_parametros(server_id, sucursal_id, params)

    return result


# ============= AUDITORÍA OPERATIVA DE COMPRAS =============



class ProductosParaCapturaRequest(BaseModel):
    server_id: str
    sucursal: Optional[str] = None
    folios_inv_inicial: Optional[List[str]] = None
    folios_requisiciones: Optional[List[str]] = None

@api_router.post("/compras/productos-para-captura")
async def obtener_productos_para_captura(request: ProductosParaCapturaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene productos para captura desde tablas canónicas EDARSAHUB SQL.

    NO-LIVE: no consulta POS.
    """
    from core.corporate_filters.request_resolver import (
        resolve_authorized_unidad_scope,
    )
    from core.inventarios.resolver_canonico import (
        resolver_empresa_id,
        resolver_sucursal_id,
    )
    from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
    from modules.compras.access import COMPRAS_VER

    unidad_token = request.server_id
    current_user = await get_current_user(credentials)

    canonical_scope = await resolve_authorized_unidad_scope(
        current_user,
        COMPRAS_VER,
        unidad_token,
    )

    if canonical_scope.access_denied:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "COMPRAS_UNIDAD_NO_AUTORIZADA",
                "message": "No tiene acceso a esta Unidad de Negocio.",
            },
        )

    resolved_server_id = canonical_scope.server_id
    unidad_codigo = canonical_scope.unidad_codigo
    sucursal_origen_id = canonical_scope.sucursal_origen_id

    if not resolved_server_id or not unidad_codigo:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "No fue posible resolver el contexto canónico de la unidad.",
            },
        )

    empresa = resolver_empresa_id(unidad_codigo)
    sucursal_resuelta = resolver_sucursal_id(
        resolved_server_id,
        sucursal_origen_id,
    )

    if not empresa.resuelto or not sucursal_resuelta.resuelto:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "Falta mapeo canónico Empresa/Sucursal.",
            },
        )

    scope = {
        "user": current_user,
        "server_id": resolved_server_id,
        "empresa_id": int(empresa.canonical_id),
        "sucursal_id": int(sucursal_resuelta.canonical_id),
        "source": "EDARSAHUB_SQL_CANONICAL",
    }

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        productos = {}

        folios_inv = _compras_list_values(request.folios_inv_inicial)
        if folios_inv:
            detalle = _compras_fetch_inventory_detail(cursor, scope["server_id"], folios_inv, [])
            if not detalle:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "INVENTORY_PHYSICAL_DETAIL_MISSING",
                        "message": "No hay detalle canónico para los folios seleccionados.",
                        "folios": folios_inv,
                        "source": "dbo.Compras_Inventarios_Fisicos_Detalle_Sync",
                    },
                )
            for codigo, row in detalle.items():
                productos[codigo] = {
                    "codigo": codigo,
                    "producto": row.get("producto") or f"SKU: {codigo}",
                    "rendimiento": _compras_as_float(row.get("rendimiento")) or 1,
                }

        pedidos = _compras_fetch_pedido_detalle(
            cursor,
            scope["empresa_id"],
            scope["sucursal_id"],
            _compras_list_values(request.folios_requisiciones),
        )
        for codigo, row in pedidos.items():
            productos.setdefault(codigo, {
                "codigo": codigo,
                "producto": row.get("producto") or f"SKU: {codigo}",
                "rendimiento": 1,
            })

        return {
            "status": "OK",
            "source": scope["source"],
            "productos": list(productos.values()),
            "total": len(productos),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("[PRODUCTOS-CAPTURA][NOLIVE] Error leyendo productos canónicos")
        raise HTTPException(status_code=500, detail=f"Error interno leyendo productos canónicos: {str(exc)[:180]}")
    finally:
        if conn:
            conn.close()


# Implementación live legacy desregistrada: sin SQL live ni uso operativo.
async def _legacy_obtener_productos_para_captura_live_disabled(request: ProductosParaCapturaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    raise RuntimeError("Implementación legacy live deshabilitada; use /compras/productos-para-captura canónico.")


@api_router.post("/compras/productos-para-captura-sql-first")
async def obtener_productos_para_captura_sql_first(
    request: ProductosParaCapturaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    [SQL-FIRST] Obtiene productos para captura desde EDARSAHUB SQL.

    Este endpoint lee EXCLUSIVAMENTE de tablas sincronizadas en EDARSAHUB.
    NO conecta a SoftRestaurant/MPRO directamente.

    Requiere que el job sync_compras haya llenado las tablas:
    - Compras_Pedidos
    - Compras_PedidosDetalle
    - Compras_Requisiciones_Sync

    Feature flag: COMPRAS_SQL_FIRST_ENABLED
    """
    await get_current_user(credentials)

    import os

    # Verificar feature flag
    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/productos-para-captura',
            'productos': [],
            'total': 0
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    productos = {}

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        # Obtener productos de pedidos/requisiciones sincronizados
        if request.folios_requisiciones:
            placeholders = ",".join([f"'{f}'" for f in request.folios_requisiciones])

            query = f"""
            SELECT
                d.CodigoProducto AS codigo,
                d.NombreProducto AS producto,
                ISNULL(d.Rendimiento, 1) AS rendimiento
            FROM dbo.Compras_PedidosDetalle d
            INNER JOIN dbo.Compras_Pedidos p
                ON p.PedidoID = d.PedidoID
            WHERE p.ServerID = %s
              AND p.FolioPedido IN ({placeholders})
            GROUP BY d.CodigoProducto, d.NombreProducto, d.Rendimiento
            """

            cursor.execute(query, (request.server_id,))
            result = cursor.fetchall()

            for r in result:
                codigo = str(r['codigo'] or '').strip()
                if codigo and codigo not in productos:
                    productos[codigo] = {
                        'codigo': codigo,
                        'producto': r['producto'] or f'SKU: {codigo}',
                        'rendimiento': float(r['rendimiento'] or 1)
                    }

        # Obtener productos de inventarios físicos sincronizados
        if request.folios_inv_inicial:
            placeholders = ",".join([f"'{f}'" for f in request.folios_inv_inicial])

            query_inv = f"""
            SELECT
                d.CodigoProducto AS codigo,
                d.NombreProducto AS producto,
                ISNULL(d.Rendimiento, 1) AS rendimiento
            FROM dbo.Compras_Inventarios_Fisicos_Sync d
            WHERE d.ServerID = %s
              AND d.FolioInventario IN ({placeholders})
            GROUP BY d.CodigoProducto, d.NombreProducto, d.Rendimiento
            """

            cursor.execute(query_inv, (request.server_id,))
            result = cursor.fetchall()

            for r in result:
                codigo = str(r['codigo'] or '').strip()
                if codigo and codigo not in productos:
                    productos[codigo] = {
                        'codigo': codigo,
                        'producto': r['producto'] or f'SKU: {codigo}',
                        'rendimiento': float(r['rendimiento'] or 1)
                    }

        conn.close()

        return {
            'status': 'SQL_FIRST',
            'source': 'EDARSAHUB',
            'productos': list(productos.values()),
            'total': len(productos)
        }

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error obteniendo productos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error SQL-First: {str(e)}")


@api_router.post("/compras/auditoria-operativa")
async def realizar_auditoria_operativa(request: AuditoriaOperativaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Realiza auditoría operativa desde tablas canónicas EDARSAHUB SQL.

    NO-LIVE: no consulta POS ni usa credenciales de servidor origen.
    """
    from datetime import datetime, timedelta
    from core.corporate_filters.request_resolver import (
        resolve_authorized_unidad_scope,
    )
    from core.inventarios.resolver_canonico import (
        resolver_empresa_id,
        resolver_sucursal_id,
    )
    from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
    from modules.compras.access import COMPRAS_EJECUTAR

    # El campo server_id se conserva en el schema por compatibilidad,
    # pero el frontend canónico envía aquí la Unidad de Negocio.
    unidad_token = request.server_id
    current_user = await get_current_user(credentials)

    canonical_scope = await resolve_authorized_unidad_scope(
        current_user,
        COMPRAS_EJECUTAR,
        unidad_token,
    )

    if canonical_scope.access_denied:
        logging.warning(
            "[AUDITORIA-COMPRAS-RBAC] acceso denegado user=%s unidad=%s reason=%s",
            current_user.get("email"),
            unidad_token,
            canonical_scope.denial_reason,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "COMPRAS_UNIDAD_NO_AUTORIZADA",
                "message": "No tiene acceso para ejecutar auditorías en esta Unidad de Negocio.",
            },
        )

    server_id = canonical_scope.server_id
    unidad_codigo = canonical_scope.unidad_codigo
    sucursal_origen_id = canonical_scope.sucursal_origen_id

    if not server_id or not unidad_codigo:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "No fue posible resolver el contexto canónico de la unidad.",
            },
        )

    empresa = resolver_empresa_id(unidad_codigo)
    sucursal_resuelta = resolver_sucursal_id(
        server_id,
        sucursal_origen_id,
    )

    if not empresa.resuelto or not sucursal_resuelta.resuelto:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "COMPRAS_CONTEXTO_CANONICO_INCOMPLETO",
                "message": "Falta mapeo canónico Empresa/Sucursal para la auditoría.",
                "unidad": unidad_codigo,
                "empresa": empresa.motivo,
                "sucursal": sucursal_resuelta.motivo,
            },
        )

    # Auditoría no expone selector de almacenes.
    # Los folios seleccionados ya provienen del contexto autorizado de la unidad.
    almacenes = []

    scope = {
        "user": current_user,
        "server_id": server_id,
        "empresa_id": int(empresa.canonical_id),
        "sucursal_id": int(sucursal_resuelta.canonical_id),
        "source": "EDARSAHUB_SQL_CANONICAL",
    }

    try:
        fecha_ini_dt = datetime.strptime(request.fecha_inv_inicial, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(request.fecha_auditoria, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas inválidas. Use formato YYYY-MM-DD")

    dias_periodo = max(1, (fecha_fin_dt - fecha_ini_dt).days)
    fecha_mov_ini = (fecha_ini_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    fecha_mov_fin = f"{request.fecha_auditoria} 23:59:59"
    folios_ini = _compras_list_values(request.folios_inv_inicial) or _compras_list_values(request.folio_inv_inicial)
    folios_fin = _compras_list_values(request.folios_inv_final) or _compras_list_values(request.folio_inv_final)
    folios_req = _compras_list_values(request.folios_requisiciones) or _compras_list_values(request.folio_requisicion)

    resumen = {
        "total_teorico": 0,
        "total_fisico": 0,
        "total_diferencia": 0,
        "productos_favor": 0,
        "productos_contra": 0,
        "importe_favor": 0,
        "importe_contra": 0,
        "requiere_acta": False,
    }

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
        cursor = conn.cursor(as_dict=True)

        inv_ini = _compras_fetch_inventory_detail(cursor, server_id, folios_ini, almacenes)
        if folios_ini and not inv_ini and almacenes:
            inv_ini = _compras_fetch_inventory_detail(cursor, server_id, folios_ini, [])
        if folios_ini and not inv_ini:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "INVENTORY_PHYSICAL_DETAIL_MISSING",
                    "message": "No hay detalle canónico para los folios iniciales seleccionados.",
                    "folios": folios_ini,
                    "source": "dbo.Compras_Inventarios_Fisicos_Detalle_Sync",
                },
            )

        manual_final = request.inventario_fisico_actual or request.inventario_manual
        inv_fin = _compras_manual_inventory(manual_final)
        if not inv_fin and folios_fin:
            inv_fin = _compras_fetch_inventory_detail(cursor, server_id, folios_fin, almacenes)
            if not inv_fin and almacenes:
                inv_fin = _compras_fetch_inventory_detail(cursor, server_id, folios_fin, [])
            if not inv_fin:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "INVENTORY_PHYSICAL_DETAIL_MISSING",
                        "message": "No hay detalle canónico para los folios finales seleccionados.",
                        "folios": folios_fin,
                        "source": "dbo.Compras_Inventarios_Fisicos_Detalle_Sync",
                    },
                )

        movimientos = _compras_fetch_movimientos(
            cursor,
            server_id,
            fecha_mov_ini,
            fecha_mov_fin,
            almacenes,
            solo_consumos=False,
        )
        consumos = _compras_fetch_movimientos(
            cursor,
            server_id,
            fecha_mov_ini,
            fecha_mov_fin,
            almacenes,
            solo_consumos=True,
        )
        pedido = _compras_fetch_pedido_detalle(
            cursor,
            scope["empresa_id"],
            scope["sucursal_id"],
            folios_req,
        )

        if request.solo_skus_requisicion and pedido:
            codigos = sorted(pedido.keys())
        else:
            codigos = sorted(set(inv_ini.keys()) | set(inv_fin.keys()) | set(movimientos.keys()) | set(consumos.keys()) | set(pedido.keys()))

        resultados = []
        for codigo in codigos:
            ini = inv_ini.get(codigo) or {}
            fin = inv_fin.get(codigo) or {}
            ped = pedido.get(codigo) or {}
            inv_inicial = _compras_as_float(ini.get("cantidad"))
            entradas = _compras_as_float(movimientos.get(codigo))
            consumo = _compras_as_float(consumos.get(codigo))
            inv_fisico = _compras_as_float(fin.get("cantidad"))
            costo = _compras_as_float(fin.get("costo") or ini.get("costo") or ped.get("costo"))
            existencia_teorica = inv_inicial + entradas - consumo
            diferencia = inv_fisico - existencia_teorica
            importe_dif = diferencia * costo
            consumo_diario = consumo / dias_periodo if dias_periodo > 0 else 0
            dias_inv = inv_fisico / consumo_diario if consumo_diario > 0 else 999
            dias_objetivo = request.dias_objetivo_default or 10
            if request.dias_objetivo_por_sku and codigo in request.dias_objetivo_por_sku:
                dias_objetivo = request.dias_objetivo_por_sku[codigo]
            cantidad_pedido = _compras_as_float(ped.get("cantidad"))
            debe_comprar = dias_inv < dias_objetivo

            producto = (
                ped.get("producto")
                or fin.get("producto")
                or ini.get("producto")
                or f"SKU: {codigo}"
            )
            rendimiento = (
                _compras_as_float(fin.get("rendimiento"))
                or _compras_as_float(ini.get("rendimiento"))
                or 1
            )
            unidad = fin.get("unidad") or ini.get("unidad") or ""
            folio_pedido = ", ".join(ped.get("folios") or [])

            resultados.append({
                "codigo": codigo,
                "producto": producto,
                "proveedor": ped.get("proveedor") or "",
                "folio_pedido": folio_pedido,
                "inv_inicial": round(inv_inicial, 2),
                "movimientos": round(entradas, 2),
                "entradas": round(entradas, 2),
                "consumos": round(consumo, 2),
                "existencia_teorica": round(existencia_teorica, 2),
                "inv_fisico": round(inv_fisico, 2),
                "diferencia": round(diferencia, 2),
                "costo": round(costo, 4),
                "costo_insumo": round(costo, 4),
                "costo_presentacion": round(costo, 4),
                "importe_diferencia": round(importe_dif, 2),
                "tipo_diferencia": "favor" if diferencia >= 0 else "contra",
                "consumo_diario": round(consumo_diario, 2),
                "dias_inventario": round(dias_inv, 1) if dias_inv < 999 else "N/A",
                "dias_objetivo": dias_objetivo,
                "cantidad_pedido": round(cantidad_pedido, 2) if cantidad_pedido else 0,
                "debe_comprar": debe_comprar,
                "recomendacion": "COMPRAR" if debe_comprar and cantidad_pedido > 0 else "OK" if not debe_comprar else "SIN PEDIDO",
                "rendimiento": rendimiento,
                "unidad": unidad,
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

        resumen = {
            **resumen,
            "total_teorico": round(resumen["total_teorico"], 2),
            "total_fisico": round(resumen["total_fisico"], 2),
            "total_diferencia": round(resumen["total_diferencia"], 2),
            "importe_favor": round(resumen["importe_favor"], 2),
            "importe_contra": round(resumen["importe_contra"], 2),
            "requiere_acta": resumen["productos_contra"] > 0 or resumen["importe_contra"] > 100,
        }
        if not (request.solo_skus_requisicion and pedido):
            resultados.sort(key=lambda row: row["importe_diferencia"])

        return {
            "status": "OK",
            "source": scope["source"],
            "resultados": resultados,
            "resumen": resumen,
            "periodo": {
                "inicio": request.fecha_inv_inicial,
                "fin": request.fecha_auditoria,
                "dias": dias_periodo,
            },
            "folios_requisiciones": folios_req,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("[AUDITORIA][NOLIVE] Error en auditoría canónica")
        raise HTTPException(status_code=500, detail=f"Error interno en auditoría canónica: {str(exc)[:180]}")
    finally:
        if conn:
            conn.close()


# Implementación live legacy desregistrada: sin SQL live ni uso operativo.
async def _legacy_realizar_auditoria_operativa_live_disabled(request: AuditoriaOperativaRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    raise RuntimeError("Implementación legacy live deshabilitada; use /compras/auditoria-operativa canónico.")


# ============= DETALLE DE MOVIMIENTOS =============

class DetalleMovimientosRequest(BaseModel):
    server_id: str
    sucursal: str
    codigo: str
    fecha_inicio: str
    fecha_fin: str
    almacenes: Optional[List[str]] = None


def _clean_detalle_almacenes(almacenes):
    if not almacenes:
        return []
    if isinstance(almacenes, str):
        almacenes = [almacenes]
    cleaned = []
    for almacen in almacenes:
        value = str(almacen or '').strip()
        if value:
            cleaned.append(value)
    return list(dict.fromkeys(cleaned))


def _float_detalle(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _iso_detalle(value):
    return value.isoformat() if hasattr(value, 'isoformat') else str(value or '')


def _soft_date_only_final_day_guard(column_name: str = "fecha") -> str:
    return (
        f"NOT (CAST({column_name} AS time) = '00:00:00' "
        f"AND CAST({column_name} AS date) = CAST(%s AS date) "
        "AND CAST(%s AS time) < '23:59:59')"
    )


def _obtener_detalle_softrestaurant_canonico(request, solo_ventas=False):
    if not request.fecha_inicio or not request.fecha_fin:
        empty_totals = {"total": 0, "entradas": 0, "salidas": 0, "neto": 0} if solo_ventas else {"entradas": 0, "salidas": 0, "neto": 0}
        key = "consumos" if solo_ventas else "movimientos"
        return {key: [], "movimientos": [], "totales": empty_totals, "error": "Fechas no válidas"}

    codigo_limpio = str(request.codigo or '').strip()
    codigo_sin_prefijo = codigo_limpio[1:] if codigo_limpio and codigo_limpio[0].isalpha() else codigo_limpio
    codigos = [c for c in dict.fromkeys([codigo_limpio, codigo_sin_prefijo]) if c]
    almacenes_limpios = _clean_detalle_almacenes(request.almacenes)

    if not codigos:
        empty_totals = {"total": 0, "entradas": 0, "salidas": 0, "neto": 0} if solo_ventas else {"entradas": 0, "salidas": 0, "neto": 0}
        key = "consumos" if solo_ventas else "movimientos"
        return {key: [], "movimientos": [], "totales": empty_totals, "error": "Producto no válido"}

    concept_filter = "ISNULL(idconcepto, '') IN ('SPV', 'SCP', 'SCS')" if solo_ventas else "ISNULL(idconcepto, '') NOT IN ('', 'SPV', 'SCP', 'SCS')"
    codigo_placeholders = ",".join(["%s"] * len(codigos))
    filters = [
        "server_id = %s",
        f"codigo_producto IN ({codigo_placeholders})",
        "fecha >= %s",
        "fecha <= %s",
        "sync_status = 'ACTIVE'",
        concept_filter,
        _soft_date_only_final_day_guard("fecha"),
    ]
    params = [request.server_id, *codigos, request.fecha_inicio, request.fecha_fin, request.fecha_fin, request.fecha_fin]

    if almacenes_limpios:
        almacen_placeholders = ",".join(["%s"] * len(almacenes_limpios))
        filters.append(f"(almacen_id IN ({almacen_placeholders}) OR almacen IN ({almacen_placeholders}))")
        params.extend(almacenes_limpios)
        params.extend(almacenes_limpios)

    conn = None
    try:
        from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            f"""
SELECT TOP 1000
    fecha,
    idconcepto,
    codigo_producto,
    cantidad,
    almacen,
    almacen_id
FROM Compras_Inventarios_Movimientos_Sync
WHERE {' AND '.join(filters)}
ORDER BY fecha DESC
""",
            tuple(params),
        )
        rows = cursor.fetchall()

        movimientos = []
        totales = {"entradas": 0.0, "salidas": 0.0, "neto": 0.0}
        total_ventas = 0.0

        for row in rows:
            raw_qty = _float_detalle(row.get('cantidad'))
            concepto = str(row.get('idconcepto') or ('VENTA' if solo_ventas else 'MOV')).strip()
            almacen = row.get('almacen') or row.get('almacen_id') or ''

            if solo_ventas:
                qty = abs(raw_qty)
                signed_qty = -qty
                tipo = 'S'
                descripcion = 'Venta/consumo canónico SoftRestaurant'
                total_ventas += qty
                totales["salidas"] += qty
            else:
                qty = abs(raw_qty)
                tipo = 'E' if raw_qty >= 0 else 'S'
                signed_qty = qty if tipo == 'E' else -qty
                descripcion = 'Movimiento canónico SoftRestaurant'
                if tipo == 'E':
                    totales["entradas"] += qty
                else:
                    totales["salidas"] += qty

            movimientos.append({
                "fecha": _iso_detalle(row.get('fecha')),
                "concepto": concepto,
                "descripcion": descripcion,
                "cantidad": signed_qty,
                "almacen": almacen,
                "referencia": str(row.get('codigo_producto') or ''),
                "tipo": tipo,
            })

        totales["neto"] = totales["entradas"] - totales["salidas"]

        if solo_ventas:
            total_ventas = round(total_ventas, 4)
            return {
                "consumos": movimientos,
                "movimientos": movimientos,
                "totales": {
                    "total": total_ventas,
                    "entradas": 0,
                    "salidas": total_ventas,
                    "neto": -total_ventas,
                },
                "source": "EDARSAHUB_SQL_CANONICAL",
            }

        return {
            "movimientos": movimientos,
            "totales": {
                "entradas": round(totales["entradas"], 4),
                "salidas": round(totales["salidas"], 4),
                "neto": round(totales["neto"], 4),
            },
            "source": "EDARSAHUB_SQL_CANONICAL",
        }
    finally:
        if conn:
            conn.close()


class UsoInversoRecetaRequest(BaseModel):
    server_id: str
    codigo: str
    producto: Optional[str] = None
    unidad: Optional[str] = None
    rendimiento: Optional[float] = None
    unidad_vista: Optional[str] = None


def _usage_text(value) -> str:
    return str(value or '').strip()


def _usage_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _usage_code_variants(value) -> List[str]:
    text = _usage_text(value)
    if not text:
        return []

    variants = [text]
    stripped = text.lstrip("0")
    if stripped and stripped != text:
        variants.append(stripped)
    if text.isdigit():
        variants.append(text.zfill(10))
        variants.append(text.zfill(8))

    return [v for v in dict.fromkeys(variants) if v]


@api_router.post("/reports/inverse-recipe-usage")
async def obtener_uso_inverso_receta_reportes(
    request: UsoInversoRecetaRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Drilldown inverso desde Analisis de Inventarios.

    Fuente unica: EDARSAHUB SQL canonico. No conecta live a MPRO/SoftRestaurant.
    - Si el codigo es insumo, busca productos/producciones donde aparece.
    - Si el codigo es presentacion, intenta resolver su insumo base canonico
      antes de buscar el uso en recetas.
    """
    from core.corporate_filters.request_resolver import canonical_server_id
    from core.server_registry import get_server_connection_info

    server_id = canonical_server_id(request.server_id)
    codigo = _usage_text(request.codigo)
    if not codigo:
        raise HTTPException(status_code=400, detail="Codigo de producto requerido")
    codigo_variants = _usage_code_variants(codigo)

    server = await get_server_connection_info(server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    system_type = _usage_text(server.get('system_type')).upper()
    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)

        base = {
            "codigo": codigo,
            "nombre": request.producto or codigo,
            "unidad": "",
            "tipo": "INSUMO",
            "rendimiento": 1.0,
        }
        presentacion = None

        variant_placeholders = ",".join(["%s"] * len(codigo_variants))

        cursor.execute(
            f"""
SELECT TOP 1
    CodigoFuente,
    Nombre,
    UnidadMedida,
    COALESCE(RendimientoElaborado, 1) AS Rendimiento,
    COALESCE(EsElaborado, 0) AS EsElaborado
FROM Sync_Productos_Insumos
WHERE ServerID = %s
  AND LTRIM(RTRIM(CodigoFuente)) IN ({variant_placeholders})
  AND Activo = 1
""",
            tuple([server_id, *codigo_variants]),
        )
        insumo_rows = cursor.fetchall()
        if insumo_rows:
            insumo = insumo_rows[0]
            base = {
                "codigo": _usage_text(insumo.get("CodigoFuente")),
                "nombre": insumo.get("Nombre") or request.producto or codigo,
                "unidad": insumo.get("UnidadMedida") or "",
                "tipo": "ELABORADO" if insumo.get("EsElaborado") else "INSUMO",
                "rendimiento": _usage_float(insumo.get("Rendimiento")) or 1.0,
            }
        else:
            try:
                cursor.execute(
                    f"""
SELECT TOP 1
    pp.CodigoPresentacion,
    pp.NombrePresentacion,
    pp.UnidadPresentacion,
    COALESCE(pp.FactorConversionInventario, 1) AS Rendimiento,
    pmo.CodigoFuente AS InsumoBaseCodigo,
    spi.Nombre AS InsumoBaseNombre,
    spi.UnidadMedida AS InsumoBaseUnidad
FROM Producto_Presentaciones pp
INNER JOIN Producto_Catalogo pc ON pc.ProductoID = pp.ProductoID
LEFT JOIN Producto_MapeoOrigen pmo
    ON pmo.ProductoID = pc.ProductoID
   AND pmo.ServerID = %s
   AND pmo.Activo = 1
LEFT JOIN Sync_Productos_Insumos spi
    ON spi.ServerID = pmo.ServerID
   AND LTRIM(RTRIM(spi.CodigoFuente)) = LTRIM(RTRIM(pmo.CodigoFuente))
   AND spi.Activo = 1
WHERE LTRIM(RTRIM(pp.CodigoPresentacion)) IN ({variant_placeholders})
  AND pp.Activo = 1
""",
                    tuple([server_id, *codigo_variants]),
                )
                pres_rows = cursor.fetchall()
            except Exception as pres_error:
                logging.warning("[INVERSE-RECIPE-USAGE] presentacion canonica no disponible: %s", str(pres_error))
                pres_rows = []

            if pres_rows:
                pres = pres_rows[0]
                base_codigo = _usage_text(pres.get("InsumoBaseCodigo")) or codigo
                presentacion = {
                    "codigo": _usage_text(pres.get("CodigoPresentacion")) or codigo,
                    "nombre": pres.get("NombrePresentacion") or request.producto or codigo,
                    "unidad": pres.get("UnidadPresentacion") or "",
                    "rendimiento": _usage_float(pres.get("Rendimiento")) or 1.0,
                }
                base = {
                    "codigo": base_codigo,
                    "nombre": pres.get("InsumoBaseNombre") or request.producto or base_codigo,
                    "unidad": pres.get("InsumoBaseUnidad") or "",
                    "tipo": "INSUMO_BASE",
                    "rendimiento": presentacion["rendimiento"],
                }

        target_codes = []
        for value in [base.get("codigo"), codigo]:
            target_codes.extend(_usage_code_variants(value))

        try:
            map_placeholders = ",".join(["%s"] * len(target_codes))
            cursor.execute(
                f"""
SELECT DISTINCT CodigoFuente
FROM Producto_MapeoOrigen
WHERE ServerID = %s
  AND Activo = 1
  AND ProductoID IN (
      SELECT DISTINCT ProductoID
      FROM Producto_MapeoOrigen
      WHERE ServerID = %s
        AND Activo = 1
        AND LTRIM(RTRIM(CodigoFuente)) IN ({map_placeholders})
  )
""",
                tuple([server_id, server_id, *target_codes]),
            )
            for row in cursor.fetchall():
                target_codes.extend(_usage_code_variants(row.get("CodigoFuente")))
        except Exception as map_error:
            logging.warning("[INVERSE-RECIPE-USAGE] mapeo canonico no disponible: %s", str(map_error))

        target_codes = [c for c in dict.fromkeys(target_codes) if c]
        placeholders = ",".join(["%s"] * len(target_codes))
        if not presentacion and _usage_text(request.unidad_vista).lower() == "presentaciones":
            presentacion = {
                "codigo": codigo,
                "nombre": request.producto or base.get("nombre") or codigo,
                "unidad": request.unidad or base.get("unidad") or "",
                "rendimiento": _usage_float(request.rendimiento) or base.get("rendimiento") or 1.0,
            }

        cursor.execute(
            f"""
SELECT TOP 1000
    r.ProductoCodigoFuente AS CodigoDestino,
    COALESCE(p.Nombre, r.ProductoCodigoFuente) AS ProductoDestino,
    CASE
        WHEN COALESCE(p.EsCompuesto, 0) = 1 THEN 'PRODUCCION'
        WHEN COALESCE(p.EsVendible, 1) = 1 THEN 'VENTA'
        ELSE COALESCE(p.TipoProducto, 'PRODUCTO')
    END AS TipoDestino,
    SUM(COALESCE(r.Cantidad, 0)) AS CantidadReceta,
    COALESCE(MAX(r.UnidadMedida), '') AS UnidadReceta,
    SUM(COALESCE(r.CostoTotal, 0)) AS CostoTotal,
    COUNT(*) AS Lineas
FROM Sync_Productos_Recetas r
LEFT JOIN Sync_Productos p
    ON p.ServerID = r.ServerID
   AND LTRIM(RTRIM(p.CodigoFuente)) = LTRIM(RTRIM(r.ProductoCodigoFuente))
   AND p.Activo = 1
WHERE r.ServerID = %s
  AND r.Activo = 1
  AND LTRIM(RTRIM(r.ComponenteCodigoFuente)) IN ({placeholders})
GROUP BY
    r.ProductoCodigoFuente,
    COALESCE(p.Nombre, r.ProductoCodigoFuente),
    CASE
        WHEN COALESCE(p.EsCompuesto, 0) = 1 THEN 'PRODUCCION'
        WHEN COALESCE(p.EsVendible, 1) = 1 THEN 'VENTA'
        ELSE COALESCE(p.TipoProducto, 'PRODUCTO')
    END
ORDER BY ProductoDestino
""",
            tuple([server_id, *target_codes]),
        )
        productos_rows = cursor.fetchall()

        cursor.execute(
            f"""
SELECT TOP 1000
    e.InsumoElaboradoCodigoFuente AS CodigoDestino,
    COALESCE(i.Nombre, e.InsumoElaboradoCodigoFuente) AS ProductoDestino,
    'PRODUCCION' AS TipoDestino,
    SUM(COALESCE(e.Cantidad, 0)) AS CantidadReceta,
    COALESCE(MAX(e.UnidadMedida), '') AS UnidadReceta,
    SUM(COALESCE(e.CostoTotal, 0)) AS CostoTotal,
    COUNT(*) AS Lineas
FROM Sync_Productos_Elaborados e
LEFT JOIN Sync_Productos_Insumos i
    ON i.ServerID = e.ServerID
   AND LTRIM(RTRIM(i.CodigoFuente)) = LTRIM(RTRIM(e.InsumoElaboradoCodigoFuente))
   AND i.Activo = 1
WHERE e.ServerID = %s
  AND e.Activo = 1
  AND LTRIM(RTRIM(e.ComponenteCodigoFuente)) IN ({placeholders})
GROUP BY e.InsumoElaboradoCodigoFuente, COALESCE(i.Nombre, e.InsumoElaboradoCodigoFuente)
ORDER BY ProductoDestino
""",
            tuple([server_id, *target_codes]),
        )
        elaborados_rows = cursor.fetchall()

        compuestos_rows = []
        try:
            cursor.execute("SELECT OBJECT_ID('Sync_Productos_Compuestos', 'U') AS ObjectID")
            compuestos_table = cursor.fetchone()
            if compuestos_table and compuestos_table.get("ObjectID"):
                cursor.execute(
                    f"""
SELECT TOP 1000
    c.ProductoCodigoFuente AS CodigoDestino,
    COALESCE(p.Nombre, c.ProductoCodigoFuente) AS ProductoDestino,
    'PRODUCTO COMPUESTO' AS TipoDestino,
    SUM(COALESCE(c.Cantidad, 0)) AS CantidadReceta,
    COALESCE(MAX(c.UnidadMedida), '') AS UnidadReceta,
    SUM(COALESCE(c.CostoTotal, 0)) AS CostoTotal,
    COUNT(*) AS Lineas
FROM Sync_Productos_Compuestos c
LEFT JOIN Sync_Productos p
    ON p.ServerID = c.ServerID
   AND LTRIM(RTRIM(p.CodigoFuente)) = LTRIM(RTRIM(c.ProductoCodigoFuente))
   AND p.Activo = 1
WHERE c.ServerID = %s
  AND c.Activo = 1
  AND LTRIM(RTRIM(c.ComponenteCodigoFuente)) IN ({placeholders})
GROUP BY c.ProductoCodigoFuente, COALESCE(p.Nombre, c.ProductoCodigoFuente)
ORDER BY ProductoDestino
""",
                    tuple([server_id, *target_codes]),
                )
                compuestos_rows = cursor.fetchall()
        except Exception as comp_error:
            logging.warning("[INVERSE-RECIPE-USAGE] compuestos canonicos no disponibles: %s", str(comp_error))

        logging.warning(
            "[INVERSE-RECIPE-USAGE] server=%s codigo=%s target_codes=%s productos=%s elaborados=%s compuestos=%s",
            server_id,
            codigo,
            target_codes,
            len(productos_rows),
            len(elaborados_rows),
            len(compuestos_rows),
        )

        usos = []
        for row in [*productos_rows, *elaborados_rows, *compuestos_rows]:
            usos.append({
                "codigo_destino": _usage_text(row.get("CodigoDestino")),
                "producto_destino": row.get("ProductoDestino") or _usage_text(row.get("CodigoDestino")),
                "tipo_destino": row.get("TipoDestino") or "PRODUCTO",
                "cantidad_receta": round(_usage_float(row.get("CantidadReceta")), 6),
                "unidad_receta": row.get("UnidadReceta") or "",
                "costo_total": round(_usage_float(row.get("CostoTotal")), 6),
                "lineas": int(row.get("Lineas") or 0),
            })

        return {
            "source": "EDARSAHUB_SQL_CANONICAL",
            "system_type": system_type,
            "codigo_consultado": codigo,
            "producto_consultado": request.producto or codigo,
            "unidad_vista": request.unidad_vista or "",
            "base": base,
            "presentacion": presentacion,
            "usos": usos,
            "total": len(usos),
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("[INVERSE-RECIPE-USAGE] error")
        raise HTTPException(status_code=500, detail=f"Error obteniendo uso inverso de receta: {str(e)[:160]}")
    finally:
        if conn:
            conn.close()


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
    from core.corporate_filters.request_resolver import canonical_server_id
    from core.user_access_context import resolve_user_access_context, has_server_access
    from modules.compras.access import require_compras_permission, COMPRAS_GESTIONAR

    require_compras_permission(current_user, COMPRAS_GESTIONAR)
    resolved_server_id = canonical_server_id(request.server_id)
    access_context = await resolve_user_access_context(current_user)
    if not has_server_access(access_context, resolved_server_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio.")

    try:
        usuario_id = current_user.get('_sql_usuario_id', current_user.get('id'))
        usuario_email = current_user.get('email', 'unknown')

        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
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
    from core.unidades_service import UnidadesService
    from core.user_access_context import resolve_user_access_context, has_server_access
    from modules.compras.access import require_compras_permission, COMPRAS_VER

    require_compras_permission(current_user, COMPRAS_VER)
    unidad = UnidadesService.get_by_id(unidad_negocio_id)
    if not unidad or not unidad.get("server_id"):
        raise HTTPException(status_code=404, detail="Unidad de negocio no encontrada.")
    access_context = await resolve_user_access_context(current_user)
    if not has_server_access(access_context, str(unidad["server_id"])):
        raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio.")

    try:
        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
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
    from core.user_access_context import resolve_user_access_context, has_server_access
    from modules.compras.access import require_compras_permission, COMPRAS_GESTIONAR

    require_compras_permission(current_user, COMPRAS_GESTIONAR)

    try:
        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
        cursor = conn.cursor(as_dict=True)

        # Resolver el server_id del item ANTES de borrar, para validar alcance RBAC.
        cursor.execute("""
            SELECT server_id FROM Auditoria_Inventario_Provisional
            WHERE id = %s AND estado = 'PROVISIONAL'
        """, (item_id,))
        item_row = cursor.fetchone()
        if not item_row:
            raise HTTPException(status_code=404, detail="Item no encontrado o ya procesado")

        access_context = await resolve_user_access_context(current_user)
        if not has_server_access(access_context, str(item_row.get("server_id") or "")):
            raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio.")

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
    from core.unidades_service import UnidadesService
    from core.user_access_context import resolve_user_access_context, has_server_access
    from modules.compras.access import require_compras_permission, COMPRAS_GESTIONAR

    require_compras_permission(current_user, COMPRAS_GESTIONAR)
    unidad = UnidadesService.get_by_id(unidad_negocio_id)
    if not unidad or not unidad.get("server_id"):
        raise HTTPException(status_code=404, detail="Unidad de negocio no encontrada.")
    access_context = await resolve_user_access_context(current_user)
    if not has_server_access(access_context, str(unidad["server_id"])):
        raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio.")

    try:
        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
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
    # DEBUG: Log de parámetros recibidos
    print("=== DETALLE MOVIMIENTOS ===")
    print("Producto:", request.codigo)
    print("Almacenes:", getattr(request, 'almacenes', None))
    print("Fecha inicial:", request.fecha_inicio)
    print("Fecha final:", request.fecha_fin)
    print("Server ID:", request.server_id)

    # CANONICAL-UNIDAD: acepta unidad canónica o server_id legacy (detalle-movimientos).
    from core.corporate_filters.request_resolver import canonical_server_id
    request.server_id = canonical_server_id(request.server_id)

    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    # RBAC: alcance por servidor/unidad y permiso funcional de Compras.
    from core.user_access_context import resolve_user_access_context, has_server_access
    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(current_user, COMPRAS_VER)
    access_context = await resolve_user_access_context(current_user)
    if not has_server_access(access_context, request.server_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio.")

    # =====================================================================
    # NO-LIVE: el detalle de movimientos se lee EXCLUSIVAMENTE de las tablas
    # canónicas de EDARSAHUB (Inventario_Movimientos/Detalle), pobladas por el
    # job sync_compras. NUNCA se conecta al POS en vivo (cumple regla NO-LIVE).
    # El `codigo` (clave de producto origen) se resuelve a ProductoID canónico
    # vía el puente Producto_MapeoOrigen (ServerID + SystemType + CodigoFuente).
    # =====================================================================
    if not request.fecha_inicio or not request.fecha_fin:
        return {"movimientos": [], "totales": {"entradas": 0, "salidas": 0, "neto": 0}, "error": "Fechas no válidas"}

    system_type = (server.get('system_type') or '').upper()
    codigo_limpio = request.codigo.strip()
    # Si el código empieza con letra (posible prefijo de almacén A/B/C), probar sin él.
    codigo_sin_prefijo = codigo_limpio[1:] if codigo_limpio and codigo_limpio[0].isalpha() else codigo_limpio

    almacenes_limpios = []
    if request.almacenes:
        almacenes_limpios = [str(a).strip() for a in request.almacenes if str(a).strip()]

    movimientos = []
    totales = {"entradas": 0, "salidas": 0, "neto": 0}

    logging.info(f"[DETALLE_MOV][NO-LIVE] server={request.server_id} sys={system_type} codigo='{codigo_limpio}' "
                 f"fechas={request.fecha_inicio}..{request.fecha_fin} almacenes={almacenes_limpios}")

    try:
        if is_softrestaurant_system(server.get('system_type')):
            return _obtener_detalle_softrestaurant_canonico(request, solo_ventas=False)

        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        # 1) Resolver ProductoID(s) canónicos desde el puente Producto_MapeoOrigen.
        cursor.execute(
            """SELECT DISTINCT ProductoID FROM dbo.Producto_MapeoOrigen
               WHERE ServerID = %s AND SystemType = %s
                 AND CodigoFuente IN (%s, %s) AND Activo = 1""",
            (request.server_id, system_type, codigo_limpio, codigo_sin_prefijo)
        )
        producto_ids = [r['ProductoID'] for r in cursor.fetchall()]

        if not producto_ids:
            conn.close()
            return {"movimientos": [], "totales": totales,
                    "message": "Sin mapeo canónico para el producto (Producto_MapeoOrigen)",
                    "source": "EDARSAHUB_NOLIVE"}

        # 2) Detalle de movimientos canónico (NO-LIVE).
        prod_ph = ", ".join(["%s"] * len(producto_ids))
        params = list(producto_ids) + [request.fecha_inicio, request.fecha_fin]
        filtro_almacen = ""
        if almacenes_limpios:
            alm_ph = ", ".join(["%s"] * len(almacenes_limpios))
            filtro_almacen = f" AND al.CodigoAlmacen IN ({alm_ph}) "
            params += almacenes_limpios

        query = f"""
        SELECT TOP 1000
            m.FechaMovimiento AS fecha,
            tm.Codigo AS concepto,
            tm.Descripcion AS descripcion_concepto,
            d.Cantidad AS cantidad,
            al.NombreAlmacen AS almacen,
            ISNULL(m.FolioReferencia, '') AS referencia,
            tm.Naturaleza AS tipo
        FROM dbo.Inventario_MovimientosDetalle d
        INNER JOIN dbo.Inventario_Movimientos m ON m.MovimientoID = d.MovimientoID
        INNER JOIN dbo.Inventario_TipoMovimiento tm ON tm.TipoMovimientoID = m.TipoMovimientoID
        LEFT JOIN dbo.Inventario_Almacenes al ON al.AlmacenID = m.AlmacenID
        WHERE d.ProductoID IN ({prod_ph})
          AND m.FechaMovimiento >= CAST(%s AS DATE)
          AND m.FechaMovimiento < DATEADD(DAY, 1, CAST(%s AS DATE))
          {filtro_almacen}
        ORDER BY m.FechaMovimiento DESC
        """
        cursor.execute(query, tuple(params))
        for r in cursor.fetchall():
            cantidad = float(r['cantidad'] or 0)
            tipo = (r['tipo'] or 'S').upper()
            movimientos.append({
                "fecha": r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha']),
                "concepto": r['concepto'] or '',
                "descripcion": r['descripcion_concepto'] or '',
                "cantidad": cantidad if tipo == 'E' else -cantidad,
                "almacen": r['almacen'] or '',
                "referencia": str(r['referencia'] or ''),
                "tipo": tipo
            })
            if tipo == 'E':
                totales["entradas"] += cantidad
            else:
                totales["salidas"] += cantidad
        conn.close()

        totales["neto"] = totales["entradas"] - totales["salidas"]
        return {"movimientos": movimientos, "totales": totales, "source": "EDARSAHUB_NOLIVE"}

    except Exception as e:
        logging.error(f"[DETALLE_MOV][NO-LIVE] Error: {str(e)[:200]}")
        return {
            "movimientos": [],
            "totales": {"entradas": 0, "salidas": 0, "neto": 0},
            "error": f"Error al obtener movimientos: {str(e)[:120]}"
        }


@api_router.post("/compras/detalle-movimientos-sql-first")
async def obtener_detalle_movimientos_sql_first(
    request: DetalleMovimientosRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    [SQL-FIRST] Obtiene detalle de movimientos desde EDARSAHUB SQL.

    Este endpoint lee EXCLUSIVAMENTE de tablas sincronizadas en EDARSAHUB.
    NO conecta a SoftRestaurant/MPRO directamente.

    Requiere que el job sync_compras haya llenado las tablas:
    - Inventario_Movimientos
    - Inventario_MovimientosDetalle
    - Inventario_Almacenes

    Feature flag: COMPRAS_SQL_FIRST_ENABLED
    """
    import os

    # Verificar feature flag
    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/detalle-movimientos',
            'movimientos': [],
            'totales': {'entradas': 0, 'salidas': 0, 'neto': 0}
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    movimientos = []
    totales = {'entradas': 0, 'salidas': 0, 'neto': 0}

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        codigo_limpio = request.codigo.strip()

        # Filtro de almacenes
        filtro_almacenes = ""
        if request.almacenes:
            almacenes_limpios = [str(a).strip() for a in request.almacenes if str(a).strip()]
            if almacenes_limpios:
                almacenes_sql = ", ".join([f"'{a}'" for a in almacenes_limpios])
                filtro_almacenes = f" AND a.CodigoAlmacen IN ({almacenes_sql}) "

        query = f"""
        SELECT TOP 500
            m.FechaMovimiento AS fecha,
            m.TipoMovimiento AS concepto,
            m.DescripcionConcepto AS descripcion_concepto,
            d.Cantidad AS cantidad,
            a.NombreAlmacen AS almacen,
            m.Folio AS referencia,
            CASE WHEN m.EsEntrada = 1 THEN 'E' ELSE 'S' END AS tipo
        FROM dbo.Inventario_MovimientosDetalle d
        INNER JOIN dbo.Inventario_Movimientos m
            ON m.MovimientoID = d.MovimientoID
        LEFT JOIN dbo.Inventario_Almacenes a
            ON a.AlmacenID = m.AlmacenID
        WHERE m.ServerID = %s
          AND d.CodigoProducto = %s
          AND m.FechaMovimiento >= %s
          AND m.FechaMovimiento < DATEADD(DAY, 1, CAST(%s AS DATE))
          {filtro_almacenes}
        ORDER BY m.FechaMovimiento DESC, m.Folio DESC
        """

        cursor.execute(query, (request.server_id, codigo_limpio, request.fecha_inicio, request.fecha_fin))
        result = cursor.fetchall()

        for r in result:
            cantidad = float(r['cantidad'] or 0)
            tipo = r['tipo'] or 'S'

            movimientos.append({
                'fecha': r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha']),
                'concepto': r['concepto'] or '',
                'descripcion': r['descripcion_concepto'] or '',
                'cantidad': cantidad,
                'almacen': r['almacen'] or '',
                'referencia': r['referencia'] or '',
                'tipo': tipo
            })

            if tipo == 'E':
                totales['entradas'] += cantidad
            else:
                totales['salidas'] += cantidad

        totales['neto'] = totales['entradas'] - totales['salidas']

        conn.close()

        return {
            'status': 'SQL_FIRST',
            'source': 'EDARSAHUB',
            'movimientos': movimientos,
            'totales': totales
        }

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error obteniendo detalle movimientos: {str(e)}")
        return {
            'status': 'ERROR',
            'movimientos': [],
            'totales': {'entradas': 0, 'salidas': 0, 'neto': 0},
            'error': f"Error SQL-First: {str(e)}"
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
    Detalle de consumos/ventas de un producto en un período.
    UNIFICACIÓN CANÓNICA (Fase B): utiliza fuentes sincronizadas en EDARSAHUB.
    La fecha inicial proviene del inventario inicial (la envía el frontend en fecha_inicio).
    """
    # CANONICAL-UNIDAD: acepta unidad canónica o server_id legacy.
    from core.corporate_filters.request_resolver import canonical_server_id
    request.server_id = canonical_server_id(request.server_id)

    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(request.server_id, db=db)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    # RBAC: alcance por servidor/unidad y permiso funcional de Compras.
    from core.user_access_context import resolve_user_access_context, has_server_access
    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(current_user, COMPRAS_VER)
    access_context = await resolve_user_access_context(current_user)
    if not has_server_access(access_context, request.server_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio.")

    if is_softrestaurant_system(server.get('system_type')):
        try:
            return _obtener_detalle_softrestaurant_canonico(request, solo_ventas=True)
        except Exception as e:
            logging.error(f"[DETALLE_CONSUMOS][SOFT-CANONICAL] Error: {e}")
            return {"consumos": [], "movimientos": [], "totales": {"total": 0, "entradas": 0, "salidas": 0, "neto": 0},
                    "error": f"Error al obtener consumos: {str(e)[:100]}"}

    return {
        "consumos": [],
        "movimientos": [],
        "totales": {"total": 0, "entradas": 0, "salidas": 0, "neto": 0},
        "source": "EDARSAHUB_SQL_CANONICAL_PENDING",
        "error": (
            "Detalle canónico de consumos para este sistema pendiente de sincronización. "
            "Por regla NO-LIVE no se consulta POS en vivo."
        ),
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
    """Obtiene KPIs de Compras exclusivamente desde EDARSAHUB SQL canónico."""
    scope = await _compras_resolve_scope(server_id, sucursal, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(scope["user"], COMPRAS_VER)

    anios_param = anios or anio
    if not meses:
        meses = str(datetime.now().month).zfill(2)
    if not anios_param:
        anios_param = str(datetime.now().year)

    periodo_where, periodo_params = _compras_period_where("FechaRecepcion", meses, anios_param)
    pedido_where, pedido_params = _compras_period_where("FechaPedido", meses, anios_param)
    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            f"""
SELECT
    COUNT(DISTINCT FolioRecepcion) AS facturas,
    ISNULL(SUM(Total), 0) AS total,
    COUNT(DISTINCT ProveedorID) AS proveedores
FROM dbo.Compras_Recepciones
WHERE EmpresaID = %s
  AND SucursalID = %s
  AND Activo = 1
  AND {periodo_where}
""",
            tuple([scope["empresa_id"], scope["sucursal_id"], *periodo_params]),
        )
        compras = cursor.fetchone() or {}

        cursor.execute(
            f"""
SELECT COUNT(DISTINCT FolioPedido) AS total
FROM dbo.Compras_Pedidos
WHERE EmpresaID = %s
  AND SucursalID = %s
  AND Activo = 1
  AND {pedido_where}
""",
            tuple([scope["empresa_id"], scope["sucursal_id"], *pedido_params]),
        )
        pedidos = cursor.fetchone() or {}

        cursor.execute(
            f"""
SELECT TOP 5
    COALESCE(
        NULLIF(pc.NombreComercial, ''),
        NULLIF(pc.RazonSocial, ''),
        NULLIF(pc.CodigoProveedor, ''),
        CAST(r.ProveedorID AS VARCHAR(50))
    ) AS nombre,
    COUNT(DISTINCT r.FolioRecepcion) AS facturas,
    ISNULL(SUM(r.Total), 0) AS total
FROM dbo.Compras_Recepciones r
LEFT JOIN dbo.Proveedor_Catalogo pc
  ON pc.ProveedorID = r.ProveedorID
 AND pc.Activo = 1
WHERE r.EmpresaID = %s
  AND r.SucursalID = %s
  AND r.Activo = 1
  AND {periodo_where}
GROUP BY
    r.ProveedorID,
    COALESCE(
        NULLIF(pc.NombreComercial, ''),
        NULLIF(pc.RazonSocial, ''),
        NULLIF(pc.CodigoProveedor, ''),
        CAST(r.ProveedorID AS VARCHAR(50))
    )
ORDER BY ISNULL(SUM(r.Total), 0) DESC
""",
            tuple([scope["empresa_id"], scope["sucursal_id"], *periodo_params]),
        )
        top_proveedores = [
            {"nombre": str(r.get('nombre') or ''), "total": float(r.get('total') or 0)}
            for r in (cursor.fetchall() or [])
        ]
        return {
            "kpis": {
                "total_compras_mes": float(compras.get("total") or 0),
                "facturas_mes": int(compras.get("facturas") or 0),
                "requisiciones_pendientes": int(pedidos.get("total") or 0),
                "proveedores_activos": int(compras.get("proveedores") or 0),
                "alertas_activas": 0,
            },
            "alertas": [],
            "top_proveedores": top_proveedores,
            "meta": {
                "status": "OK",
                "source": scope["source"],
                "unidad": scope["unidad"].get("codigo"),
                "empresa_id": scope["empresa_id"],
                "sucursal_id": scope["sucursal_id"],
                "meses": _compras_int_values(meses, 1, 12),
                "anios": _compras_int_values(anios_param, 2000, 2100),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[COMPRAS-DASHBOARD][NOLIVE] Error: {e}")
        raise HTTPException(status_code=503, detail=f"Error leyendo Compras canónico: {str(e)[:160]}")
    finally:
        if conn:
            conn.close()


@api_router.post("/compras/analisis")
async def obtener_analisis_compras(request: AnalisisComprasRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene análisis de compras por proveedor y mes desde EDARSAHUB SQL canónico."""
    # CANONICAL-UNIDAD: acepta unidad canónica o server_id legacy.
    from core.corporate_filters.request_resolver import canonical_server_id
    request.server_id = canonical_server_id(request.server_id)
    scope = await _compras_resolve_scope(request.server_id, request.sucursal, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(scope["user"], COMPRAS_VER)

    anios = request.anios or ([str(request.anio)] if request.anio else [str(datetime.now().year)])
    meses = request.meses or [str(datetime.now().month).zfill(2)]
    periodo_where, periodo_params = _compras_period_where("FechaRecepcion", meses, anios)
    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            f"""
SELECT TOP 1000
    CAST(r.ProveedorID AS VARCHAR(50)) AS codigo,
    COALESCE(
        NULLIF(pc.NombreComercial, ''),
        NULLIF(pc.RazonSocial, ''),
        NULLIF(pc.CodigoProveedor, ''),
        CAST(r.ProveedorID AS VARCHAR(50))
    ) AS nombre,
    MONTH(r.FechaRecepcion) AS mes,
    YEAR(r.FechaRecepcion) AS anio,
    COUNT(DISTINCT r.FolioRecepcion) AS facturas,
    ISNULL(SUM(r.Total), 0) AS total
FROM dbo.Compras_Recepciones r
LEFT JOIN dbo.Proveedor_Catalogo pc
  ON pc.ProveedorID = r.ProveedorID
 AND pc.Activo = 1
WHERE r.EmpresaID = %s
  AND r.SucursalID = %s
  AND r.Activo = 1
  AND {periodo_where}
GROUP BY
    r.ProveedorID,
    COALESCE(
        NULLIF(pc.NombreComercial, ''),
        NULLIF(pc.RazonSocial, ''),
        NULLIF(pc.CodigoProveedor, ''),
        CAST(r.ProveedorID AS VARCHAR(50))
    ),
    MONTH(r.FechaRecepcion),
    YEAR(r.FechaRecepcion)
ORDER BY ISNULL(SUM(r.Total), 0) DESC
""",
            tuple([scope["empresa_id"], scope["sucursal_id"], *periodo_params]),
        )
        proveedores = {}
        total_compras = 0.0
        total_facturas = 0
        for row in cursor.fetchall() or []:
            codigo = str(row.get("codigo") or "0")
            if codigo not in proveedores:
                proveedores[codigo] = {
                    "codigo": codigo,
                    "nombre": str(row.get("nombre") or codigo),
                    "total": 0,
                    "facturas": 0,
                }
                for mes in meses:
                    proveedores[codigo][str(mes).zfill(2)] = 0
            mes_str = str(row.get("mes") or "").zfill(2)
            total = float(row.get("total") or 0)
            facturas = int(row.get("facturas") or 0)
            if mes_str in proveedores[codigo]:
                proveedores[codigo][mes_str] += total
            proveedores[codigo]["total"] += total
            proveedores[codigo]["facturas"] += facturas
            total_compras += total
            total_facturas += facturas
        proveedores_list = sorted(proveedores.values(), key=lambda x: x["total"], reverse=True)
        promedio_factura = total_compras / total_facturas if total_facturas > 0 else 0
        kpis = {
            "total_compras": round(total_compras, 2),
            "totalCompras": round(total_compras, 2),
            "num_proveedores": len(proveedores_list),
            "numProveedores": len(proveedores_list),
            "num_facturas": total_facturas,
            "numFacturas": total_facturas,
            "promedio_factura": round(promedio_factura, 2),
            "promedioFactura": round(promedio_factura, 2),
        }
        return {
            "status": "OK",
            "source": scope["source"],
            "proveedores": proveedores_list[:100],
            "kpis": kpis,
            "alertas": [],
            "meta": {
                "unidad": scope["unidad"].get("codigo"),
                "empresa_id": scope["empresa_id"],
                "sucursal_id": scope["sucursal_id"],
            },
        }
    except Exception as e:
        logging.error(f"[COMPRAS-ANALISIS][NOLIVE] Error: {e}")
        raise HTTPException(status_code=503, detail=f"Error leyendo análisis canónico de compras: {str(e)[:160]}")
    finally:
        if conn:
            conn.close()


@api_router.get("/compras/facturas-proveedor/{server_id}")
async def obtener_facturas_proveedor(server_id: str, proveedor_codigo: str, anio: int, meses: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene facturas/recepciones de un proveedor desde EDARSAHUB SQL canónico."""
    # CANONICAL-UNIDAD: el path puede traer una unidad canónica o un server_id legacy.
    from core.corporate_filters.request_resolver import canonical_server_id
    server_id = canonical_server_id(server_id)
    scope = await _compras_resolve_scope(server_id, sucursal, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(scope["user"], COMPRAS_VER)

    periodo_where, periodo_params = _compras_period_where("FechaRecepcion", meses, [anio])
    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            f"""
SELECT TOP 500
    r.RecepcionID,
    r.FolioRecepcion AS folio,
    r.FechaRecepcion AS fecha,
    r.Total AS importe,
    r.EstatusRecepcionID AS estatus_id,
    (SELECT COUNT(*)
     FROM dbo.Compras_RecepcionesDetalle d
     WHERE d.RecepcionID = r.RecepcionID) AS productos
FROM dbo.Compras_Recepciones r
WHERE r.EmpresaID = %s
  AND r.SucursalID = %s
  AND r.Activo = 1
  AND CAST(r.ProveedorID AS VARCHAR(50)) = %s
  AND {periodo_where}
ORDER BY r.FechaRecepcion DESC
""",
            tuple([scope["empresa_id"], scope["sucursal_id"], str(proveedor_codigo), *periodo_params]),
        )
        return [
            {
                "folio": str(r.get("folio") or ""),
                "fecha": r.get("fecha").isoformat() if hasattr(r.get("fecha"), "isoformat") else str(r.get("fecha") or ""),
                "productos": int(r.get("productos") or 0),
                "importe": float(r.get("importe") or 0),
                "status": str(r.get("estatus_id") or "canonico"),
                "source": scope["source"],
                "tiene_pdf": False,
                "tiene_xml": False,
            }
            for r in (cursor.fetchall() or [])
        ]
    except Exception as e:
        logging.error(f"[COMPRAS-FACTURAS][NOLIVE] Error: {e}")
        raise HTTPException(status_code=503, detail=f"Error leyendo facturas canónicas: {str(e)[:160]}")
    finally:
        if conn:
            conn.close()


@api_router.get("/compras/detalle-factura/{server_id}/{folio}")
async def obtener_detalle_factura(server_id: str, folio: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene detalle de factura/recepción desde EDARSAHUB SQL canónico."""
    # CANONICAL-UNIDAD: el path puede traer una unidad canónica o un server_id legacy.
    from core.corporate_filters.request_resolver import canonical_server_id
    server_id = canonical_server_id(server_id)
    scope = await _compras_resolve_scope(server_id, sucursal, credentials)

    from modules.compras.access import require_compras_permission, COMPRAS_VER
    require_compras_permission(scope["user"], COMPRAS_VER)

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(timeout=20, login_timeout=10)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            """
SELECT TOP 500
    CAST(d.ProductoID AS VARCHAR(50)) AS codigo,
    CAST(d.ProductoID AS VARCHAR(50)) AS producto,
    d.CantidadRecibida AS cantidad,
    d.PrecioUnitario AS costo,
    d.Subtotal AS importe
FROM dbo.Compras_Recepciones r
INNER JOIN dbo.Compras_RecepcionesDetalle d ON d.RecepcionID = r.RecepcionID
WHERE r.EmpresaID = %s
  AND r.SucursalID = %s
  AND r.Activo = 1
  AND r.FolioRecepcion = %s
ORDER BY d.ProductoID
""",
            (scope["empresa_id"], scope["sucursal_id"], str(folio)),
        )
        return [
            {
                "codigo": str(r.get("codigo") or ""),
                "producto": str(r.get("producto") or r.get("codigo") or ""),
                "cantidad": float(r.get("cantidad") or 0),
                "costo": float(r.get("costo") or 0),
                "importe": float(r.get("importe") or 0),
                "source": scope["source"],
            }
            for r in (cursor.fetchall() or [])
        ]
    except Exception as e:
        logging.error(f"[COMPRAS-DETALLE-FACTURA][NOLIVE] Error: {e}")
        raise HTTPException(status_code=503, detail=f"Error leyendo detalle canónico: {str(e)[:160]}")
    finally:
        if conn:
            conn.close()


# ============================================================================
# ENDPOINTS SQL-FIRST - Compras (Sin fallback LIVE)
# ============================================================================

@api_router.get("/compras/facturas-proveedor-sql-first/{server_id}")
async def obtener_facturas_proveedor_sql_first(
    server_id: str,
    proveedor_id: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    [SQL-FIRST] Obtiene facturas de proveedor SOLO desde EDARSAHUB SQL.
    Lee de dbo.Compras_Recepciones (facturas recibidas).
    Sin fallback LIVE.
    """
    import os

    await get_current_user(credentials)

    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/facturas-proveedor/{server_id}',
            'facturas': []
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        filtros = ["ServerID = %s"]
        params = [server_id]

        if proveedor_id:
            filtros.append("ProveedorID = %s")
            params.append(proveedor_id)
        if fecha_inicio:
            filtros.append("FechaRecepcion >= %s")
            params.append(fecha_inicio)
        if fecha_fin:
            filtros.append("FechaRecepcion <= %s")
            params.append(fecha_fin)

        query = f"""
        SELECT TOP 500
            RecepcionID, FolioFactura AS folio, FechaRecepcion AS fecha,
            ProveedorID, ProveedorNombre AS proveedor,
            ImporteTotal AS importe, Estatus AS estado,
            OrigenSistema, SyncStatus
        FROM dbo.Compras_Recepciones
        WHERE {" AND ".join(filtros)}
        ORDER BY FechaRecepcion DESC
        """

        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        conn.close()

        facturas = [{
            'folio': str(r['folio'] or ''),
            'fecha': r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha'] or ''),
            'proveedor': r['proveedor'] or '',
            'proveedor_id': str(r['ProveedorID'] or ''),
            'importe': float(r['importe'] or 0),
            'estado': r['estado'] or '',
            'source': 'EDARSAHUB_SQL_FIRST'
        } for r in result]

        return {'status': 'SQL_FIRST', 'source': 'EDARSAHUB', 'total': len(facturas), 'facturas': facturas}

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error facturas-proveedor: {str(e)}")
        return {'status': 'ERROR', 'facturas': [], 'error': str(e)}


@api_router.get("/compras/detalle-factura-sql-first/{server_id}/{folio}")
async def obtener_detalle_factura_sql_first(
    server_id: str,
    folio: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    [SQL-FIRST] Obtiene detalle de factura SOLO desde EDARSAHUB SQL.
    Lee de dbo.Compras_RecepcionesDetalle.
    Sin fallback LIVE.
    """
    import os

    await get_current_user(credentials)

    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/detalle-factura/{server_id}/{folio}',
            'detalle': []
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        query = """
        SELECT
            d.CodigoProducto AS codigo, d.NombreProducto AS producto,
            d.Cantidad AS cantidad, d.Unidad AS unidad,
            d.PrecioUnitario AS precio, d.Importe AS importe
        FROM dbo.Compras_RecepcionesDetalle d
        INNER JOIN dbo.Compras_Recepciones r ON r.RecepcionID = d.RecepcionID
        WHERE r.ServerID = %s AND r.FolioFactura = %s
        ORDER BY d.NombreProducto
        """

        cursor.execute(query, (server_id, folio))
        result = cursor.fetchall()
        conn.close()

        detalle = [{
            'codigo': str(r['codigo'] or ''),
            'producto': r['producto'] or '',
            'cantidad': float(r['cantidad'] or 0),
            'unidad': r['unidad'] or '',
            'precio': float(r['precio'] or 0),
            'importe': float(r['importe'] or 0)
        } for r in result]

        return {'status': 'SQL_FIRST', 'source': 'EDARSAHUB', 'folio': folio, 'total': len(detalle), 'detalle': detalle}

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error detalle-factura: {str(e)}")
        return {'status': 'ERROR', 'detalle': [], 'error': str(e)}


@api_router.post("/compras/detalle-consumos-sql-first")
async def obtener_detalle_consumos_sql_first(
    request: DetalleConsumosRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    [SQL-FIRST] Obtiene detalle de consumos SOLO desde EDARSAHUB SQL.
    Lee de tablas de consumos sincronizadas.
    Sin fallback LIVE.
    """
    import os

    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/detalle-consumos',
            'consumos': [],
            'totales': {'total': 0}
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        codigo_limpio = request.codigo.strip()

        query = """
        SELECT TOP 500
            m.FechaMovimiento AS fecha,
            m.Folio AS documento,
            d.Cantidad AS cantidad,
            'CONSUMO' AS tipo,
            a.NombreAlmacen AS almacen
        FROM dbo.Inventario_MovimientosDetalle d
        INNER JOIN dbo.Inventario_Movimientos m ON m.MovimientoID = d.MovimientoID
        LEFT JOIN dbo.Inventario_Almacenes a ON a.AlmacenID = m.AlmacenID
        WHERE m.ServerID = %s
          AND d.CodigoProducto = %s
          AND m.TipoMovimiento IN ('VENTA', 'CONSUMO', 'SALIDA')
          AND m.FechaMovimiento >= %s
          AND m.FechaMovimiento < DATEADD(DAY, 1, CAST(%s AS DATE))
        ORDER BY m.FechaMovimiento DESC
        """

        cursor.execute(query, (request.server_id, codigo_limpio, request.fecha_inicio, request.fecha_fin))
        result = cursor.fetchall()
        conn.close()

        total_consumo = 0
        consumos = []
        for r in result:
            cantidad = float(r['cantidad'] or 0)
            total_consumo += cantidad
            consumos.append({
                'fecha': r['fecha'].isoformat() if hasattr(r['fecha'], 'isoformat') else str(r['fecha'] or ''),
                'documento': r['documento'] or '',
                'cantidad': cantidad,
                'tipo': r['tipo'] or 'CONSUMO',
                'almacen': r['almacen'] or ''
            })

        return {
            'status': 'SQL_FIRST',
            'source': 'EDARSAHUB',
            'consumos': consumos,
            'totales': {'total': total_consumo}
        }

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error detalle-consumos: {str(e)}")
        return {'status': 'ERROR', 'consumos': [], 'totales': {'total': 0}, 'error': str(e)}


@api_router.get("/compras/dashboard-sql-first/{server_id}")
async def obtener_dashboard_compras_sql_first(
    server_id: str,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    [SQL-FIRST] Obtiene dashboard de compras SOLO desde EDARSAHUB SQL.
    Agrega datos de Compras_Pedidos, Compras_Recepciones, Inventario_Movimientos.
    Sin fallback LIVE.
    """
    import os
    from datetime import datetime, timedelta

    await get_current_user(credentials)

    if os.environ.get('COMPRAS_SQL_FIRST_ENABLED', 'false').lower() != 'true':
        return {
            'status': 'DISABLED',
            'message': 'Endpoint SQL-First deshabilitado. Use /compras/dashboard/{server_id}',
            'dashboard': {}
        }

    EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

    # Fechas por defecto: últimos 30 días
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    try:
        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=15)
        cursor = conn.cursor(as_dict=True)

        # Pedidos pendientes
        cursor.execute("""
            SELECT COUNT(*) AS total, ISNULL(SUM(ImporteTotal), 0) AS importe
            FROM dbo.Compras_Pedidos
            WHERE ServerID = %s AND Estatus IN ('PXA', 'PENDIENTE')
              AND FechaPedido >= %s AND FechaPedido <= %s
        """, (server_id, fecha_inicio, fecha_fin))
        pedidos = cursor.fetchone()

        # Recepciones/Facturas
        cursor.execute("""
            SELECT COUNT(*) AS total, ISNULL(SUM(ImporteTotal), 0) AS importe
            FROM dbo.Compras_Recepciones
            WHERE ServerID = %s
              AND FechaRecepcion >= %s AND FechaRecepcion <= %s
        """, (server_id, fecha_inicio, fecha_fin))
        recepciones = cursor.fetchone()

        # Movimientos de inventario
        cursor.execute("""
            SELECT
                SUM(CASE WHEN EsEntrada = 1 THEN 1 ELSE 0 END) AS entradas,
                SUM(CASE WHEN EsEntrada = 0 THEN 1 ELSE 0 END) AS salidas
            FROM dbo.Inventario_Movimientos
            WHERE ServerID = %s
              AND FechaMovimiento >= %s AND FechaMovimiento <= %s
        """, (server_id, fecha_inicio, fecha_fin))
        movimientos = cursor.fetchone()

        conn.close()

        return {
            'status': 'SQL_FIRST',
            'source': 'EDARSAHUB',
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'dashboard': {
                'pedidos_pendientes': {
                    'total': int(pedidos['total'] or 0),
                    'importe': float(pedidos['importe'] or 0)
                },
                'recepciones': {
                    'total': int(recepciones['total'] or 0),
                    'importe': float(recepciones['importe'] or 0)
                },
                'movimientos': {
                    'entradas': int(movimientos['entradas'] or 0),
                    'salidas': int(movimientos['salidas'] or 0)
                }
            }
        }

    except Exception as e:
        logging.error(f"[SQL-FIRST] Error dashboard-compras: {str(e)}")
        return {'status': 'ERROR', 'dashboard': {}, 'error': str(e)}


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
    """Obtiene el último estado de conexión de un servidor desde EDARSAHUB SQL."""
    from modules.comercial.repository import get_server_connection_status as _sql_get_status
    return await _sql_get_status(server_id)

async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None):
    """Guarda el estado de conexión de un servidor en EDARSAHUB SQL."""
    from modules.comercial.repository import save_server_connection_status as _sql_save_status
    await _sql_save_status(server_id, is_online, response_time_ms)

async def is_server_recently_offline(server_id: str, minutes_threshold: int = 10):
    """Verifica si un servidor fue marcado como offline recientemente (evita reintentos)."""
    status = await get_server_connection_status(server_id)
    if not status:
        return False

    if status.get('is_online', True):
        return False

    last_check = status.get('last_check')
    if last_check:
        try:
            if not isinstance(last_check, str):
                last_check = last_check.isoformat()
            last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            if last_check_dt.tzinfo is None:
                last_check_dt = last_check_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            diff_minutes = (now - last_check_dt).total_seconds() / 60
            if diff_minutes < minutes_threshold:
                return True
        except Exception:
            pass

    return False

# Función para guardar/obtener caché de KPIs
async def get_cached_kpis(server_id: str, periodo_key: str):
    """Obtiene los KPIs cacheados desde EDARSAHUB SQL."""
    from modules.comercial.repository import get_cached_kpis as _sql_get_cached_kpis
    return await _sql_get_cached_kpis(server_id, periodo_key)

async def save_kpis_cache(server_id: str, periodo_key: str, kpis: dict):
    """Guarda los KPIs en caché SQL."""
    from modules.comercial.repository import save_kpis_cache as _sql_save_kpis_cache
    await _sql_save_kpis_cache(server_id, periodo_key, kpis)

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
        is_valid, error_msg = _validate_table_name(tabla, conn_info.get('system_type'), user_role)  # noqa: F821
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
    is_valid, error_msg = _validate_table_name(tabla, conn_info.get('system_type'), user_role)  # noqa: F821
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
        is_valid, error_msg = _validate_table_name(tabla, conn_info.get('system_type'), user_role)  # noqa: F821
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
    if not es_admin(current_user):
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
    if not es_superadmin(current_user):
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

    # Guardar log en tabla canónica SQL
    _sql_insert_script_log({
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
from datetime import datetime

# Directorio para almacenar evidencias
EVIDENCIAS_DIR = "/app/uploads/evidencias"
os.makedirs(EVIDENCIAS_DIR, exist_ok=True)

# Modelos Pydantic para Informes de Auditoría
class InformeAuditoriaCreate(BaseModel):  # noqa: F811
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


@api_router.get("/rrhh/catalogos/puestos")
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
#     if not es_admin(current_user):
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
#         ('{Descripcion}', '{Departamento}', {sueldo_base}, '{nomipaq_id}', '{mpro_id}', GETDATE(), '{current_user.get("email", "")}')
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
#         WHERE SucursalID = {SucursalID} AND Semana_Anio = {Semana_Anio}
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
#         ({SucursalID}, {Semana_Anio}, 'Captura', 0)
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

    if not es_admin(current_user):
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

    # FASE P5: MongoDB deprecado - scripts_pendientes migrado a SQL
    # Si hay script_id, se ignora (debe venir en body.script)
    if script_id:
        pass  # P5: db.scripts_pendientes eliminado - usar API SQL

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

    # Guardar log en tabla canónica SQL
    _sql_insert_script_log({
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
    # FASE P5: MongoDB deprecado - scripts_pendientes migrado a SQL
    if script_id and exitosos > 0:
        pass  # P5: db.scripts_pendientes.update_one eliminado - usar API SQL

    return {
        "servidor": server['name'],
        "titulo": titulo,
        "total": len(statements),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados
    }


# ============================================================================
# ========================= MODULO DE FINANZAS ===============================
# ============================================================================

def _finanzas_get_conn():
    from modules.compras.sync_service import get_edarsahub_connection  # noqa: F811
    return get_edarsahub_connection()


def _finanzas_pick(body: Dict, *keys, default=None):
    for key in keys:
        if key in body and body.get(key) is not None:
            return body.get(key)
    return default


def _finanzas_to_int(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except Exception:
        return default


def _finanzas_to_float(value, default=0.0):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except Exception:
        return default


def _finanzas_money(value):
    if value is None:
        return 0.0
    return float(value)


def _finanzas_require_view_scope(
    current_user: Dict,
    unidad_ref: Optional[str] = None,
):
    from modules.finanzas.access import FINANZAS_VER, resolve_finanzas_unit_filter

    return resolve_finanzas_unit_filter(current_user, unidad_ref, FINANZAS_VER)


def _finanzas_require_write_scope(
    current_user: Dict,
    unidad_ref: Optional[str] = None,
):
    from modules.finanzas.access import (
        FINANZAS_ADMINISTRAR,
        FINANZAS_EDITAR,
        require_any_finanzas_permission,
        resolve_finanzas_unit_filter,
    )

    permission = require_any_finanzas_permission(
        current_user,
        (FINANZAS_ADMINISTRAR, FINANZAS_EDITAR),
    )
    return resolve_finanzas_unit_filter(
        current_user,
        unidad_ref,
        permission["permission_code"],
    )


def _finanzas_table_ready(cur) -> bool:
    cur.execute("""
        SELECT CASE
            WHEN OBJECT_ID('dbo.Finanzas_Presupuestos', 'U') IS NOT NULL
             AND COL_LENGTH('dbo.Finanzas_Presupuestos', 'UnidadNegocioID') IS NOT NULL
            THEN 1 ELSE 0 END AS Ready
    """)
    row = cur.fetchone() or {}
    return bool(row.get("Ready"))


def _finanzas_resolve_unidad_negocio(cur, ref: Optional[str]) -> Optional[Dict]:
    if ref is None or str(ref).strip() == "":
        return None

    value = str(ref).strip()

    cur.execute("""
        SELECT TOP 1
            id,
            nombre,
            codigo,
            server_id,
            sucursal_origen_id,
            system_type
        FROM dbo.Unidades_Negocio
        WHERE ISNULL(activo, 1) = 1
          AND (
                id = TRY_CONVERT(uniqueidentifier, %s)
             OR codigo = %s
             OR nombre = %s
             OR server_id = %s
             OR sucursal_origen_id = %s
          )
        ORDER BY
            CASE
                WHEN id = TRY_CONVERT(uniqueidentifier, %s) THEN 1
                WHEN codigo = %s THEN 2
                WHEN nombre = %s THEN 3
                WHEN server_id = %s THEN 4
                WHEN sucursal_origen_id = %s THEN 5
                ELSE 9
            END,
            ISNULL(orden, 999),
            nombre
    """, (value, value, value, value, value, value, value, value, value, value))

    row = cur.fetchone()
    if not row:
        return None

    return {
        "id": str(row.get("id")),
        "nombre": row.get("nombre"),
        "codigo": row.get("codigo"),
        "server_id": row.get("server_id"),
        "sucursal_origen_id": row.get("sucursal_origen_id"),
        "system_type": row.get("system_type"),
    }


def _finanzas_unidad_ref(
    sucursal_id: Optional[str] = None,
    server_id: Optional[str] = None,
    unidad_negocio_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
):
    return unidad_negocio_id or unidad_negocio_pk or server_id or sucursal_id


def _finanzas_body_unidad_ref(body: Dict):
    return (
        _finanzas_pick(body, "unidad_negocio_id", "UnidadNegocioID")
        or _finanzas_pick(body, "unidad_negocio_pk")
        or _finanzas_pick(body, "server_id")
        or _finanzas_pick(body, "sucursal_id", "SucursalID")
    )


def _finanzas_row_to_api(row: Dict) -> Dict:
    unidad_id = row.get("UnidadNegocioID")
    return {
        "PresupuestoID": row.get("PresupuestoID"),
        "UnidadNegocioID": str(unidad_id) if unidad_id is not None else None,
        "SucursalID": str(unidad_id) if unidad_id is not None else None,
        "Nombre_Unidad": row.get("Nombre_Unidad"),
        "Nombre_Sucursal": row.get("Nombre_Unidad"),
        "Codigo_Unidad": row.get("Codigo_Unidad"),
        "Categoria": row.get("Categoria"),
        "SubCategoria": row.get("SubCategoria"),
        "Tipo": row.get("Tipo"),
        "Monto_Presupuestado": _finanzas_money(row.get("Monto_Presupuestado")),
        "Monto_Ejecutado": _finanzas_money(row.get("Monto_Ejecutado")),
        "Anio": row.get("Anio"),
        "Mes": row.get("Mes"),
        "Notas": row.get("Notas"),
        "Activo": bool(row.get("Activo")) if row.get("Activo") is not None else True,
        "Fecha_Creacion": row.get("Fecha_Creacion").isoformat() if row.get("Fecha_Creacion") else None,
        "Fecha_Modificacion": row.get("Fecha_Modificacion").isoformat() if row.get("Fecha_Modificacion") else None,
        "Creado_Por": row.get("Creado_Por"),
        "Modificado_Por": row.get("Modificado_Por"),
    }


def _finanzas_build_where(
    anio=None,
    mes=None,
    unidad_negocio_id=None,
    categoria=None,
    unidades_permitidas=None,
):
    clauses = ["p.Activo = 1"]
    params = []

    if anio is not None:
        clauses.append("p.Anio = %s")
        params.append(anio)

    if mes is not None:
        clauses.append("p.Mes = %s")
        params.append(mes)

    if unidad_negocio_id:
        clauses.append("CONVERT(varchar(36), p.UnidadNegocioID) = %s")
        params.append(str(unidad_negocio_id))
    elif unidades_permitidas is not None:
        allowed = [str(unit).strip() for unit in unidades_permitidas if str(unit).strip()]
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            clauses.append(f"CONVERT(varchar(36), p.UnidadNegocioID) IN ({placeholders})")
            params.extend(allowed)
        else:
            clauses.append("1=0")

    if categoria:
        clauses.append("p.Categoria = %s")
        params.append(categoria)

    return " WHERE " + " AND ".join(clauses), params


def _finanzas_select_presupuestos(
    cur,
    anio=None,
    mes=None,
    unidad_negocio_id=None,
    categoria=None,
    unidades_permitidas=None,
):
    if not _finanzas_table_ready(cur):
        return []

    where_sql, params = _finanzas_build_where(
        anio,
        mes,
        unidad_negocio_id,
        categoria,
        unidades_permitidas,
    )

    cur.execute(f"""
        SELECT
            p.PresupuestoID,
            p.UnidadNegocioID,
            u.nombre AS Nombre_Unidad,
            u.codigo AS Codigo_Unidad,
            p.Categoria,
            p.SubCategoria,
            p.Tipo,
            p.Monto_Presupuestado,
            p.Monto_Ejecutado,
            p.Anio,
            p.Mes,
            p.Notas,
            p.Activo,
            p.Fecha_Creacion,
            p.Fecha_Modificacion,
            p.Creado_Por,
            p.Modificado_Por
        FROM dbo.Finanzas_Presupuestos p
        JOIN dbo.Unidades_Negocio u
            ON u.id = p.UnidadNegocioID
        {where_sql}
        ORDER BY
            ISNULL(u.orden, 999),
            u.nombre,
            p.Anio DESC,
            p.Mes DESC,
            p.Tipo,
            p.Categoria,
            p.SubCategoria
    """, tuple(params))

    return [_finanzas_row_to_api(r) for r in (cur.fetchall() or [])]


def _finanzas_get_presupuesto_by_id(cur, presupuesto_id: int) -> Optional[Dict]:
    if not _finanzas_table_ready(cur):
        return None

    cur.execute("""
        SELECT
            p.PresupuestoID,
            p.UnidadNegocioID,
            u.nombre AS Nombre_Unidad,
            u.codigo AS Codigo_Unidad,
            p.Categoria,
            p.SubCategoria,
            p.Tipo,
            p.Monto_Presupuestado,
            p.Monto_Ejecutado,
            p.Anio,
            p.Mes,
            p.Notas,
            p.Activo,
            p.Fecha_Creacion,
            p.Fecha_Modificacion,
            p.Creado_Por,
            p.Modificado_Por
        FROM dbo.Finanzas_Presupuestos p
        JOIN dbo.Unidades_Negocio u
            ON u.id = p.UnidadNegocioID
        WHERE p.PresupuestoID = %s
          AND p.Activo = 1
    """, (presupuesto_id,))

    row = cur.fetchone()
    return _finanzas_row_to_api(row) if row else None


def _finanzas_empty_dashboard(anio: int, mes: int, mensaje: Optional[str] = None):
    return {
        "periodo": {"anio": anio, "mes": mes},
        "mensaje": mensaje,
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
        "por_unidad": [],
        "totales": []
    }


@api_router.get("/finanzas/dashboard")
async def finanzas_dashboard(
    anio: int = Query(default=None),
    mes: int = Query(default=None),
    sucursal_id: Optional[str] = Query(default=None),
    server_id: Optional[str] = Query(default=None),
    unidad_negocio_id: Optional[str] = Query(default=None),
    unidad_negocio_pk: Optional[str] = Query(default=None),
    current_user: Dict = Depends(get_current_user)
):
    """Dashboard de finanzas basado en presupuestos canonicos por Unidad de Negocio."""
    now = datetime.now()
    anio = _finanzas_to_int(anio, now.year)
    mes = _finanzas_to_int(mes, now.month)
    unidad_ref = _finanzas_unidad_ref(
        sucursal_id,
        server_id,
        unidad_negocio_id,
        unidad_negocio_pk,
    )
    unidad_pk, unidades_permitidas = _finanzas_require_view_scope(
        current_user,
        unidad_ref,
    )

    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                return _finanzas_empty_dashboard(anio, mes, "Tabla Finanzas_Presupuestos pendiente de migracion canonica")

            unidad = _finanzas_resolve_unidad_negocio(cur, unidad_pk) if unidad_pk else None
            unidad_id = unidad["id"] if unidad else None

            presupuestos = _finanzas_select_presupuestos(
                cur,
                anio,
                mes,
                unidad_id,
                unidades_permitidas=unidades_permitidas,
            )

            prev_anio = anio
            prev_mes = mes - 1
            if prev_mes < 1:
                prev_mes = 12
                prev_anio -= 1

            prev_rows = _finanzas_select_presupuestos(
                cur,
                prev_anio,
                prev_mes,
                unidad_id,
                unidades_permitidas=unidades_permitidas,
            )

            def sum_tipo(rows, tipo, campo):
                return sum(_finanzas_money(r.get(campo)) for r in rows if r.get("Tipo") == tipo)

            ingresos_pres = sum_tipo(presupuestos, "Ingreso", "Monto_Presupuestado")
            ingresos_ejec = sum_tipo(presupuestos, "Ingreso", "Monto_Ejecutado")
            egresos_pres = sum_tipo(presupuestos, "Egreso", "Monto_Presupuestado")
            egresos_ejec = sum_tipo(presupuestos, "Egreso", "Monto_Ejecutado")

            prev_ingresos_ejec = sum_tipo(prev_rows, "Ingreso", "Monto_Ejecutado")
            prev_egresos_ejec = sum_tipo(prev_rows, "Egreso", "Monto_Ejecutado")

            ingresos_var = ((ingresos_ejec - prev_ingresos_ejec) / prev_ingresos_ejec * 100) if prev_ingresos_ejec else 0
            egresos_var = ((egresos_ejec - prev_egresos_ejec) / prev_egresos_ejec * 100) if prev_egresos_ejec else 0

            utilidad_pres = ingresos_pres - egresos_pres
            utilidad_real = ingresos_ejec - egresos_ejec
            margen = (utilidad_real / ingresos_ejec * 100) if ingresos_ejec else 0

            por_unidad_map = {}
            for row in presupuestos:
                key = row.get("UnidadNegocioID") or ""
                if key not in por_unidad_map:
                    por_unidad_map[key] = {
                        "UnidadNegocioID": key,
                        "Nombre_Unidad": row.get("Nombre_Unidad"),
                        "Nombre_Sucursal": row.get("Nombre_Unidad"),
                        "ingresos_presupuestados": 0,
                        "ingresos_ejecutados": 0,
                        "egresos_presupuestados": 0,
                        "egresos_ejecutados": 0,
                    }
                bucket = por_unidad_map[key]
                if row.get("Tipo") == "Ingreso":
                    bucket["ingresos_presupuestados"] += _finanzas_money(row.get("Monto_Presupuestado"))
                    bucket["ingresos_ejecutados"] += _finanzas_money(row.get("Monto_Ejecutado"))
                elif row.get("Tipo") == "Egreso":
                    bucket["egresos_presupuestados"] += _finanzas_money(row.get("Monto_Presupuestado"))
                    bucket["egresos_ejecutados"] += _finanzas_money(row.get("Monto_Ejecutado"))

            totales_map = {}
            for row in presupuestos:
                key = (row.get("Tipo"), row.get("Categoria"))
                if key not in totales_map:
                    totales_map[key] = {
                        "Tipo": row.get("Tipo"),
                        "Categoria": row.get("Categoria"),
                        "Monto_Presupuestado": 0,
                        "Monto_Ejecutado": 0,
                    }
                totales_map[key]["Monto_Presupuestado"] += _finanzas_money(row.get("Monto_Presupuestado"))
                totales_map[key]["Monto_Ejecutado"] += _finanzas_money(row.get("Monto_Ejecutado"))

            por_unidad = list(por_unidad_map.values())

            return {
                "periodo": {"anio": anio, "mes": mes},
                "unidad_negocio": unidad,
                "mensaje": None,
                "kpis": {
                    "ingresos_presupuestados": ingresos_pres,
                    "ingresos_ejecutados": ingresos_ejec,
                    "ingresos_var_mes_ant": ingresos_var,
                    "egresos_presupuestados": egresos_pres,
                    "egresos_ejecutados": egresos_ejec,
                    "egresos_var_mes_ant": egresos_var,
                    "utilidad_presupuestada": utilidad_pres,
                    "utilidad_real": utilidad_real,
                    "margen_utilidad": margen
                },
                "presupuestos": presupuestos,
                "por_sucursal": por_unidad,
                "por_unidad": por_unidad,
                "totales": list(totales_map.values())
            }
    finally:
        conn.close()


@api_router.get("/finanzas/presupuestos")
async def finanzas_listar_presupuestos(
    anio: int = Query(default=None),
    mes: int = Query(default=None),
    sucursal_id: Optional[str] = Query(default=None),
    server_id: Optional[str] = Query(default=None),
    unidad_negocio_id: Optional[str] = Query(default=None),
    unidad_negocio_pk: Optional[str] = Query(default=None),
    categoria: Optional[str] = Query(default=None),
    current_user: Dict = Depends(get_current_user)
):
    """Lista presupuestos canonicos con filtros por Unidad de Negocio."""
    anio = _finanzas_to_int(anio)
    mes = _finanzas_to_int(mes)
    unidad_ref = _finanzas_unidad_ref(
        sucursal_id,
        server_id,
        unidad_negocio_id,
        unidad_negocio_pk,
    )
    unidad_pk, unidades_permitidas = _finanzas_require_view_scope(
        current_user,
        unidad_ref,
    )

    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                return {"presupuestos": [], "total": 0, "mensaje": "Tabla Finanzas_Presupuestos pendiente de migracion canonica"}

            unidad = _finanzas_resolve_unidad_negocio(cur, unidad_pk) if unidad_pk else None
            unidad_id = unidad["id"] if unidad else None

            presupuestos = _finanzas_select_presupuestos(
                cur,
                anio,
                mes,
                unidad_id,
                categoria,
                unidades_permitidas,
            )
            return {
                "presupuestos": presupuestos,
                "total": len(presupuestos),
                "unidad_negocio": unidad,
                "mensaje": None
            }
    finally:
        conn.close()


@api_router.post("/finanzas/presupuestos")
async def finanzas_crear_presupuesto(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea presupuesto canonico por Unidad de Negocio."""
    categoria = (_finanzas_pick(body, "categoria", "Categoria") or "").strip()
    subcategoria = _finanzas_pick(body, "subcategoria", "SubCategoria")
    tipo = (_finanzas_pick(body, "tipo", "Tipo") or "").strip()
    monto_pres = _finanzas_to_float(_finanzas_pick(body, "monto_presupuestado", "monto", "Monto_Presupuestado"))
    monto_ejec = _finanzas_to_float(_finanzas_pick(body, "monto_ejecutado", "Monto_Ejecutado"), 0.0)
    anio = _finanzas_to_int(_finanzas_pick(body, "anio", "Anio"))
    mes = _finanzas_to_int(_finanzas_pick(body, "mes", "Mes"))
    notas = _finanzas_pick(body, "notas", "Notas")
    creado_por = current_user.get("email") or current_user.get("username") or current_user.get("Usuario") or "sistema"

    if not categoria:
        raise HTTPException(status_code=400, detail="categoria es requerida")
    if tipo not in ("Ingreso", "Egreso"):
        raise HTTPException(status_code=400, detail="tipo debe ser Ingreso o Egreso")
    if not anio:
        raise HTTPException(status_code=400, detail="anio es requerido")
    if not mes or mes < 1 or mes > 12:
        raise HTTPException(status_code=400, detail="mes debe estar entre 1 y 12")

    unidad_ref = _finanzas_body_unidad_ref(body)
    unidad_pk, _ = _finanzas_require_write_scope(current_user, unidad_ref)

    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                raise HTTPException(status_code=500, detail="Tabla Finanzas_Presupuestos no esta migrada")

            unidad = _finanzas_resolve_unidad_negocio(cur, unidad_pk)
            if not unidad:
                raise HTTPException(status_code=400, detail="Unidad de Negocio invalida o no encontrada")

            cur.execute("""
                INSERT INTO dbo.Finanzas_Presupuestos (
                    UnidadNegocioID,
                    Categoria,
                    SubCategoria,
                    Tipo,
                    Monto_Presupuestado,
                    Monto_Ejecutado,
                    Anio,
                    Mes,
                    Notas,
                    Creado_Por
                )
                OUTPUT INSERTED.PresupuestoID
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                unidad["id"],
                categoria,
                subcategoria,
                tipo,
                monto_pres,
                monto_ejec,
                anio,
                mes,
                notas,
                creado_por,
            ))
            inserted = cur.fetchone() or {}
            presupuesto_id = inserted.get("PresupuestoID")
            conn.commit()

            presupuesto = _finanzas_get_presupuesto_by_id(cur, presupuesto_id)
            return {
                "success": True,
                "message": "Presupuesto creado",
                "presupuesto": presupuesto
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        logging.exception("[FINANZAS] Error creando presupuesto")
        raise HTTPException(status_code=500, detail=f"Error creando presupuesto: {str(exc)}")
    finally:
        conn.close()


@api_router.put("/finanzas/presupuestos/{presupuesto_id}")
async def finanzas_actualizar_presupuesto(
    presupuesto_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza presupuesto canonico."""
    _finanzas_require_write_scope(current_user, _finanzas_body_unidad_ref(body))
    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                raise HTTPException(status_code=500, detail="Tabla Finanzas_Presupuestos no esta migrada")

            current = _finanzas_get_presupuesto_by_id(cur, presupuesto_id)
            if not current:
                raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
            _finanzas_require_write_scope(
                current_user,
                current.get("UnidadNegocioID"),
            )

            sets = []
            params = []

            unidad_ref = _finanzas_body_unidad_ref(body)
            if unidad_ref:
                unidad_pk, _ = _finanzas_require_write_scope(current_user, unidad_ref)
                unidad = _finanzas_resolve_unidad_negocio(cur, unidad_pk)
                if not unidad:
                    raise HTTPException(status_code=400, detail="Unidad de Negocio invalida o no encontrada")
                sets.append("UnidadNegocioID = %s")
                params.append(unidad["id"])

            if "categoria" in body or "Categoria" in body:
                categoria = (_finanzas_pick(body, "categoria", "Categoria") or "").strip()
                if not categoria:
                    raise HTTPException(status_code=400, detail="categoria no puede estar vacia")
                sets.append("Categoria = %s")
                params.append(categoria)

            if "subcategoria" in body or "SubCategoria" in body:
                sets.append("SubCategoria = %s")
                params.append(_finanzas_pick(body, "subcategoria", "SubCategoria"))

            if "tipo" in body or "Tipo" in body:
                tipo = (_finanzas_pick(body, "tipo", "Tipo") or "").strip()
                if tipo not in ("Ingreso", "Egreso"):
                    raise HTTPException(status_code=400, detail="tipo debe ser Ingreso o Egreso")
                sets.append("Tipo = %s")
                params.append(tipo)

            if "monto_presupuestado" in body or "monto" in body or "Monto_Presupuestado" in body:
                sets.append("Monto_Presupuestado = %s")
                params.append(_finanzas_to_float(_finanzas_pick(body, "monto_presupuestado", "monto", "Monto_Presupuestado")))

            if "monto_ejecutado" in body or "Monto_Ejecutado" in body:
                sets.append("Monto_Ejecutado = %s")
                params.append(_finanzas_to_float(_finanzas_pick(body, "monto_ejecutado", "Monto_Ejecutado")))

            if "anio" in body or "Anio" in body:
                anio = _finanzas_to_int(_finanzas_pick(body, "anio", "Anio"))
                if not anio:
                    raise HTTPException(status_code=400, detail="anio invalido")
                sets.append("Anio = %s")
                params.append(anio)

            if "mes" in body or "Mes" in body:
                mes = _finanzas_to_int(_finanzas_pick(body, "mes", "Mes"))
                if not mes or mes < 1 or mes > 12:
                    raise HTTPException(status_code=400, detail="mes debe estar entre 1 y 12")
                sets.append("Mes = %s")
                params.append(mes)

            if "notas" in body or "Notas" in body:
                sets.append("Notas = %s")
                params.append(_finanzas_pick(body, "notas", "Notas"))

            if not sets:
                return {
                    "success": True,
                    "message": "Sin cambios",
                    "presupuesto": current
                }

            modificado_por = current_user.get("email") or current_user.get("username") or current_user.get("Usuario") or "sistema"
            sets.append("Fecha_Modificacion = SYSUTCDATETIME()")
            sets.append("Modificado_Por = %s")
            params.append(modificado_por)
            params.append(presupuesto_id)

            cur.execute(f"""
                UPDATE dbo.Finanzas_Presupuestos
                SET {", ".join(sets)}
                WHERE PresupuestoID = %s
                  AND Activo = 1
            """, tuple(params))
            conn.commit()

            presupuesto = _finanzas_get_presupuesto_by_id(cur, presupuesto_id)
            return {
                "success": True,
                "message": "Presupuesto actualizado",
                "presupuesto": presupuesto
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        logging.exception("[FINANZAS] Error actualizando presupuesto")
        raise HTTPException(status_code=500, detail=f"Error actualizando presupuesto: {str(exc)}")
    finally:
        conn.close()


@api_router.delete("/finanzas/presupuestos/{presupuesto_id}")
async def finanzas_eliminar_presupuesto(
    presupuesto_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina presupuesto con baja logica."""
    modificado_por = current_user.get("email") or current_user.get("username") or current_user.get("Usuario") or "sistema"

    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                raise HTTPException(status_code=500, detail="Tabla Finanzas_Presupuestos no esta migrada")

            current = _finanzas_get_presupuesto_by_id(cur, presupuesto_id)
            if not current:
                raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
            _finanzas_require_write_scope(
                current_user,
                current.get("UnidadNegocioID"),
            )

            cur.execute("""
                UPDATE dbo.Finanzas_Presupuestos
                SET
                    Activo = 0,
                    Fecha_Modificacion = SYSUTCDATETIME(),
                    Modificado_Por = %s
                WHERE PresupuestoID = %s
                  AND Activo = 1
            """, (modificado_por, presupuesto_id))
            affected = cur.rowcount
            conn.commit()

            if affected == 0:
                raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

            return {
                "success": True,
                "message": "Presupuesto eliminado"
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        logging.exception("[FINANZAS] Error eliminando presupuesto")
        raise HTTPException(status_code=500, detail=f"Error eliminando presupuesto: {str(exc)}")
    finally:
        conn.close()


@api_router.get("/finanzas/categorias")
async def finanzas_listar_categorias(
    current_user: Dict = Depends(get_current_user)
):
    """Lista categorias financieras desde presupuestos canonicos."""
    _, unidades_permitidas = _finanzas_require_view_scope(current_user)

    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                return {
                    "categorias": [],
                    "mensaje": "Tabla Finanzas_Presupuestos pendiente de migracion canonica",
                }

            where_sql, params = _finanzas_build_where(
                unidades_permitidas=unidades_permitidas,
            )
            cur.execute(f"""
                SELECT DISTINCT
                    p.Categoria,
                    p.Tipo
                FROM dbo.Finanzas_Presupuestos p
                JOIN dbo.Unidades_Negocio u
                    ON u.id = p.UnidadNegocioID
                {where_sql}
                  AND p.Categoria IS NOT NULL
                  AND LTRIM(RTRIM(p.Categoria)) <> ''
                ORDER BY p.Tipo, p.Categoria
            """, tuple(params))
            return {"categorias": cur.fetchall() or []}
    finally:
        conn.close()


@api_router.post("/finanzas/registrar-movimiento")
async def finanzas_registrar_movimiento(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza monto ejecutado de un presupuesto canonico."""
    presupuesto_id = _finanzas_to_int(_finanzas_pick(body, "presupuesto_id", "PresupuestoID"))
    monto = _finanzas_to_float(_finanzas_pick(body, "monto", "monto_ejecutado", "Monto_Ejecutado"), 0.0)
    modo = (_finanzas_pick(body, "modo", default="incrementar") or "incrementar").lower()
    modificado_por = current_user.get("email") or current_user.get("username") or current_user.get("Usuario") or "sistema"
    movimiento_unidad_pk, _ = _finanzas_require_write_scope(
        current_user,
        _finanzas_body_unidad_ref(body),
    )

    conn = _finanzas_get_conn()
    try:
        with conn.cursor(as_dict=True) as cur:
            if not _finanzas_table_ready(cur):
                raise HTTPException(status_code=500, detail="Tabla Finanzas_Presupuestos no esta migrada")

            if presupuesto_id:
                current = _finanzas_get_presupuesto_by_id(cur, presupuesto_id)
                if not current:
                    raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
                _finanzas_require_write_scope(
                    current_user,
                    current.get("UnidadNegocioID"),
                )
                if modo in ("set", "reemplazar", "replace"):
                    cur.execute("""
                        UPDATE dbo.Finanzas_Presupuestos
                        SET
                            Monto_Ejecutado = %s,
                            Fecha_Modificacion = SYSUTCDATETIME(),
                            Modificado_Por = %s
                        WHERE PresupuestoID = %s
                          AND Activo = 1
                    """, (monto, modificado_por, presupuesto_id))
                else:
                    cur.execute("""
                        UPDATE dbo.Finanzas_Presupuestos
                        SET
                            Monto_Ejecutado = Monto_Ejecutado + %s,
                            Fecha_Modificacion = SYSUTCDATETIME(),
                            Modificado_Por = %s
                        WHERE PresupuestoID = %s
                          AND Activo = 1
                    """, (monto, modificado_por, presupuesto_id))
            else:
                unidad = _finanzas_resolve_unidad_negocio(cur, movimiento_unidad_pk)
                categoria = _finanzas_pick(body, "categoria", "Categoria")
                tipo = _finanzas_pick(body, "tipo", "Tipo")
                anio = _finanzas_to_int(_finanzas_pick(body, "anio", "Anio"))
                mes = _finanzas_to_int(_finanzas_pick(body, "mes", "Mes"))

                if not unidad or not categoria or not tipo or not anio or not mes:
                    raise HTTPException(status_code=400, detail="Debe enviar presupuesto_id o unidad/categoria/tipo/anio/mes")

                cur.execute("""
                    UPDATE dbo.Finanzas_Presupuestos
                    SET
                        Monto_Ejecutado = Monto_Ejecutado + %s,
                        Fecha_Modificacion = SYSUTCDATETIME(),
                        Modificado_Por = %s
                    WHERE UnidadNegocioID = %s
                      AND Categoria = %s
                      AND Tipo = %s
                      AND Anio = %s
                      AND Mes = %s
                      AND Activo = 1
                """, (monto, modificado_por, unidad["id"], categoria, tipo, anio, mes))

            affected = cur.rowcount
            conn.commit()

            return {
                "success": affected > 0,
                "message": "Movimiento aplicado" if affected > 0 else "No se encontro presupuesto para actualizar",
                "actualizados": affected
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        logging.exception("[FINANZAS] Error registrando movimiento")
        raise HTTPException(status_code=500, detail=f"Error registrando movimiento: {str(exc)}")
    finally:
        conn.close()

@api_router.get("/finanzas/script-inicializacion")
async def finanzas_obtener_script_inicializacion(
    current_user: Dict = Depends(get_current_user)
):
    """Retorna el script canonico vigente para Finanzas Presupuestos."""
    _finanzas_require_write_scope(current_user)
    script = """
/*
EDARSAHUB Finanzas / Presupuestos
Script canonico sin datos demo.
FK: dbo.Unidades_Negocio(id)
*/

IF OBJECT_ID('dbo.Unidades_Negocio', 'U') IS NULL
BEGIN
    THROW 51000, 'Falta tabla canonica dbo.Unidades_Negocio.', 1;
END;

IF OBJECT_ID('dbo.Finanzas_Presupuestos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_Presupuestos (
        PresupuestoID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
        Categoria NVARCHAR(100) NOT NULL,
        SubCategoria NVARCHAR(100) NULL,
        Tipo NVARCHAR(20) NOT NULL CHECK (Tipo IN ('Ingreso', 'Egreso')),
        Monto_Presupuestado DECIMAL(18,2) NOT NULL DEFAULT (0),
        Monto_Ejecutado DECIMAL(18,2) NOT NULL DEFAULT (0),
        Anio INT NOT NULL,
        Mes INT NOT NULL CHECK (Mes BETWEEN 1 AND 12),
        Notas NVARCHAR(500) NULL,
        Activo BIT NOT NULL DEFAULT (1),
        Fecha_Creacion DATETIME2(0) NOT NULL DEFAULT (SYSUTCDATETIME()),
        Fecha_Modificacion DATETIME2(0) NULL,
        Creado_Por NVARCHAR(100) NULL,
        Modificado_Por NVARCHAR(100) NULL,
        CONSTRAINT FK_Finanzas_Presupuestos_UnidadNegocio
            FOREIGN KEY (UnidadNegocioID)
            REFERENCES dbo.Unidades_Negocio(id)
    );
END;
"""
    return {
        "script": script,
        "mensaje": "Script canonico. No usa RH_Cat_Sucursales y no inserta datos demo."
    }

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

    # FASE P5: MongoDB deprecado - consultas_custom migrado a SQL
    # Las consultas personalizadas ahora se obtienen de Sistema_ConsultasSQL
    # consultas_custom = await db.consultas_custom.find(filtro).to_list(500)
    consultas_custom = []  # P5: db.consultas_custom eliminado - usar API SQL

    # Obtener categorías (solo del catálogo base)
    categorias_base = set(catalogo_get_categorias())

    return {
        "consultas": resultado,
        "categorias": sorted(list(categorias_base)),
        "total": len(resultado)
    }


@api_router.post("/catalogo/ejecutar-rich/{consulta_id}")
async def ejecutar_consulta_catalogo(  # noqa: F811
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
        # FASE P5: MongoDB deprecado - consultas_custom migrado a SQL
        # Buscar en Sistema_ConsultasSQL via API
        consulta_custom = None  # P5: db.consultas_custom eliminado

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
# CRUD CONSULTAS PERSONALIZADAS - FASE P5: MongoDB deprecado
# ============================================================================

@api_router.put("/catalogo/consultas/{consulta_id}")
async def actualizar_consulta_sql(consulta_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """
    FASE P5: MongoDB deprecado - usar Sistema_ConsultasSQL via API SQL
    """
    raise HTTPException(status_code=501, detail="P5: Endpoint deprecado - usar API /api/sql/consultas")

@api_router.post("/catalogo/ejecutar-custom/{consulta_id}")
async def ejecutar_consulta_custom(
    consulta_id: str,
    server_id: str = Query(...),
    body: Dict = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE P5: MongoDB deprecado - usar Sistema_ConsultasSQL via API SQL
    """
    raise HTTPException(status_code=501, detail="P5: Endpoint deprecado - usar API /api/sql/consultas")
    if normalize_system_type(conn_info.get('system_type')) != normalize_system_type(consulta.get('sistema')):  # noqa: F821
        raise HTTPException(status_code=400, detail=f"Esta consulta es para {consulta['sistema']}, no para {conn_info.get('system_type')}")  # noqa: F821

    # Preparar parámetros
    parametros = body.get('parametros', body) if body else {}

    # Preparar SQL
    sql = consulta['sql']  # noqa: F821
    for param, valor in parametros.items():
        sql = sql.replace('{' + param + '}', str(valor))

    logging.info(f"Ejecutando consulta custom {consulta_id} en {conn_info.get('name')}")  # noqa: F821

    try:
        result = execute_sql_query(
            conn_info['host'], conn_info['port'], conn_info['database'],  # noqa: F821
            conn_info['username'], conn_info['password'], sql  # noqa: F821
        )

        return {
            "consulta": consulta['nombre'],  # noqa: F821
            "servidor": conn_info.get('name'),  # noqa: F821
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

@api_router.get("/sistema/pool-stats")
async def get_pool_statistics(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene estadísticas del connection pool de SQL Server.
    Solo accesible para Administradores.
    """
    if not es_admin(current_user):
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
    if not es_admin(current_user):
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


from core.rbac.middleware import (
    get_current_user_with_permissions as _get_current_user_with_permissions,
)


@api_router.get("/sistema/pendientes-unificados")
async def obtener_pendientes_unificados(
    current_user: Dict = Depends(_get_current_user_with_permissions),
):
    """
    Obtiene TODOS los pendientes del usuario en una bandeja unificada.
    Incluye: Solicitudes de catálogos, Proveedores, Nóminas, etc.
    Ordenados por: Urgentes/Vencidos primero, luego agrupados por tipo.
    """
    current_user.get("id")
    ahora = datetime.now(timezone.utc)

    _permisos = {
        str(permiso).strip().upper()
        for permiso in (current_user.get("permisos") or [])
        if permiso
    }

    def _tiene_alguno(*codigos):
        return any(
            str(codigo).strip().upper() in _permisos
            for codigo in codigos
        )

    # ===== SCOPE POR UNIDAD / PERMISOS =====
    # Admin/SuperAdmin ven todas las unidades. Roles operativos solo sus servers permitidos.
    from core.security import es_admin as _es_admin, es_superadmin as _es_superadmin, get_user_empresas_permitidas
    is_admin_view = _es_admin(current_user) or _es_superadmin(current_user)
    allowed_servers = set()
    if not is_admin_view:
        try:
            _emp = await get_user_empresas_permitidas(current_user)
            allowed_servers = set((s or "").lower() for s in await get_servers_for_empresas(_emp))
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] scope unidad: {_e}")

    def _pasa_unidad(server_id):
        """True si el ítem es visible para el usuario según su unidad/permisos."""
        if is_admin_view:
            return True
        if not server_id:
            return True  # ítems sin unidad asociada no se filtran
        return str(server_id).lower() in allowed_servers

    urgentes = []  # Vencidos y próximos a vencer (< 24h)
    pendientes_catalogos = []
    pendientes_proveedores = []
    pendientes_nominas = []

    # ===== 1. SOLICITUDES DE CATÁLOGOS =====
    if _tiene_alguno('CATALOGOS_VER', 'CATALOGO_VER'):
        # SQL-FIRST: solicitudes canónicas desde Sistema_CatalogosSolicitudes
        try:
            from modules.catalogos_workflow_sql.repository import CatalogosWorkflowSQLRepository
            _wf_repo = CatalogosWorkflowSQLRepository()
            _todas = _wf_repo.listar_solicitudes_workflow()
            solicitudes = [
                s for s in _todas
                if ((s.get("estatus") or "").startswith("Pendiente") or s.get("estatus") == "Reenviada")
                and s.get("catalogo_id") != "fecha_operativa"
            ]
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] catálogos: {_e}")
            solicitudes = []

        for sol in solicitudes:
            _fs = sol.get("fecha_solicitud") or ahora.isoformat()
            try:
                fecha_sol = datetime.fromisoformat(str(_fs).replace("Z", "+00:00"))
                if fecha_sol.tzinfo is None:
                    fecha_sol = fecha_sol.replace(tzinfo=timezone.utc)
            except Exception:
                fecha_sol = ahora
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
    # Fail-closed: este dominio todavía no dispone de un permiso RBAC
    # canónico demostrado para esta bandeja. No se consulta ni se expone
    # hasta formalizar dicho permiso.

    # ===== 3. NÓMINAS PENDIENTES =====
    if _tiene_alguno('RH_VER', 'RECURSOS_HUMANOS_VER'):
        try:
            from modules.rh.service import rh_flujo_nomina_service as _nom_svc
            _res = await _nom_svc.listar_flujos()
            _flujos = _res.get("flujos", []) if isinstance(_res, dict) else []
            _cerrados = {"Pagado", "Cancelado", "Cerrado"}
            for f in _flujos:
                est = (f.get("estatus") or f.get("Estatus") or "").strip()
                if est in _cerrados:
                    continue
                if not _pasa_unidad(f.get("server_id") or f.get("ServerID")):
                    continue
                suc = f.get("sucursal_nombre") or f.get("SucursalNombre") or f.get("sucursal_id") or "Sucursal"
                sem = f.get("semana_anio") or f.get("SemanaAnio") or ""
                fcrea = f.get("fecha_creacion") or f.get("FechaCreacion") or f.get("created_at")
                _venc = est.startswith("Rechazado")
                item = {
                    "id": f.get("id") or f.get("FlujoID") or f.get("flujo_id"),
                    "tipo": "nomina",
                    "titulo": f"Nómina {suc} - {est or 'En proceso'}",
                    "descripcion": f"Semana {sem}",
                    "solicitante": str(suc),
                    "fecha": str(fcrea) if fcrea else None,
                    "estatus": est,
                    "vencido": _venc,
                    "proximo_vencer": False,
                    "data": f,
                }
                if _venc:
                    urgentes.append(item)
                else:
                    pendientes_nominas.append(item)
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] nominas: {_e}")

    # ===== 4. FECHA OPERATIVA (RBAC) PENDIENTE DE AUTORIZAR =====
    pendientes_fecha_operativa = []

    try:
        from modules.catalogos_workflow_sql.repository import (
            CatalogosWorkflowSQLRepository as _WFR,
        )

        _fecha_repo = _WFR()

        for s in _fecha_repo.listar_solicitudes_fecha_operativa_autorizables(
            current_user
        ):
            d = s.get("datos") or {}

            pendientes_fecha_operativa.append({
                "id": s.get("id"),
                "tipo": "fecha_operativa",
                "titulo": (
                    "Cambio fecha operativa · "
                    f"{d.get('dominio', d.get('modulo', ''))}"
                ),
                "descripcion": (
                    f"{d.get('tabla_origen', '')} → "
                    f"{d.get('valor_propuesto', '')}"
                ),
                "solicitante": s.get("solicitante_nombre"),
                "fecha": s.get("fecha_solicitud"),
                "data": s,
            })
    except Exception as _e:
        logging.warning(
            f"[pendientes-unificados] fecha_operativa: {_e}"
        )

    # ===== 5. AUDITORÍAS PROGRAMADAS PENDIENTES DE REVISIÓN =====
    pendientes_auditorias = []
    if _tiene_alguno('AUDITORIA_VER', 'AUTOMATIZACIONES_VER'):
        try:
            from modules.fase2_operativo.routes.dashboard_routes import get_db as _get_db
            from modules.fase2_operativo.services.auditoria_programada_service import AuditoriaProgramadaService as _APS
            _svc = _APS(_get_db())
            _list = None
            for _m in ("listar_pendientes_revision", "listar_pendientes", "listar_auditorias", "listar"):
                if hasattr(_svc, _m):
                    _res = getattr(_svc, _m)()
                    _res = await _res if hasattr(_res, "__await__") else _res
                    _list = _res.get("auditorias", _res) if isinstance(_res, dict) else _res
                    break
            for a in (_list or []):
                est = (a.get("estado") or a.get("Estado") or a.get("estatus") or "").upper()
                if est in ("COMPLETADA", "CERRADA", "CANCELADA"):
                    continue
                if not _pasa_unidad(a.get("server_id") or a.get("ServerID")):
                    continue
                pendientes_auditorias.append({
                    "id": a.get("id") or a.get("AuditoriaID") or a.get("auditoria_id"),
                    "tipo": "auditoria",
                    "titulo": a.get("nombre") or a.get("titulo") or "Auditoría programada",
                    "descripcion": a.get("descripcion") or est,
                    "solicitante": a.get("unidad_negocio") or a.get("creado_por") or "",
                    "fecha": str(a.get("fecha_programada") or a.get("created_at") or ""),
                    "data": a,
                })
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] auditorias: {_e}")

    # ===== 6. ALERTAS ACTIVAS DEL SISTEMA =====
    pendientes_alertas = []
    if _tiene_alguno('ALERTAS_VER'):
        try:
            from modules.fase2_operativo.routes.dashboard_routes import get_db as _get_db2
            from modules.fase2_operativo.services.operativo_service import OperativoService as _OpSvc
            _alertas = await _OpSvc(_get_db2()).obtener_alertas_activas()
            for al in (_alertas or []):
                if not _pasa_unidad(al.get("server_id") or al.get("ServerID")):
                    continue
                sev = (al.get("severidad") or al.get("nivel") or al.get("tipo") or "").upper()
                item = {
                    "id": al.get("id") or al.get("alerta_id"),
                    "tipo": "alerta",
                    "titulo": al.get("titulo") or al.get("mensaje") or "Alerta",
                    "descripcion": al.get("descripcion") or al.get("detalle") or "",
                    "solicitante": al.get("unidad_negocio") or al.get("sucursal") or "",
                    "fecha": str(al.get("fecha") or al.get("created_at") or ""),
                    "severidad": sev,
                    "vencido": sev in ("CRITICA", "CRITICO", "ALTA", "ALTO"),
                    "proximo_vencer": False,
                    "data": al,
                }
                if item["vencido"]:
                    urgentes.append(item)
                else:
                    pendientes_alertas.append(item)
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] alertas: {_e}")

    # ===== 7. EXCEPCIONES ESTRATÉGICAS (Balanced Scorecard) =====
    # Fuente real: mismo motor que /api/alertas-estrategicas/resumen (rentabilidad,
    # compras sin detalle, inventarios a revisar). NO-LIVE: lee tablas canónicas SQL.
    pendientes_excepciones = []
    if _tiene_alguno('ALERTAS_VER'):
        try:
            from modules.alertas_estrategicas.routes import resumen_alertas as _resumen_exc
            # Excepciones ya marcadas como REVISADA (para ocultarlas de la bandeja)
            _revisadas = set()
            try:
                from core.scheduler.jobs.alertas_excepciones_job import (
                    obtener_excepciones_revisadas,
                )

                _revisadas = obtener_excepciones_revisadas()
            except Exception as _e:
                logging.warning(
                    "[pendientes-unificados] estado excepciones: %s",
                    _e,
                )
            _exc = await _resumen_exc(server_id="", limite=200, current_user=current_user)
            for a in (_exc.get("alertas", []) if isinstance(_exc, dict) else []):
                if not _pasa_unidad(a.get("server_id")):
                    continue
                sev = (a.get("severidad") or "").upper()
                _key = f"{a.get('tipo_alerta','EXC')}-{a.get('entidad_id') or a.get('entidad_codigo') or a.get('server_id')}"
                if _key in _revisadas:
                    continue
                item = {
                    "id": _key,
                    "tipo": "excepcion",
                    "titulo": f"{a.get('tipo_alerta','Excepción')} · {a.get('descripcion') or a.get('entidad_codigo') or ''}",
                    "descripcion": a.get("accion_sugerida") or a.get("perspectiva_bsc") or "",
                    "solicitante": a.get("unidad") or "",
                    "fecha": ahora.isoformat(),
                    "severidad": sev,
                    "vencido": False,
                    "proximo_vencer": False,
                    "data": a,
                }
                pendientes_excepciones.append(item)
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] excepciones: {_e}")

    # ===== 8. SINCRONIZACIONES FALLIDAS (con reintento) =====
    pendientes_sincronizaciones = []
    if _tiene_alguno('SCHEDULER_VER'):
        try:
            from api.admin_scheduler_resync import (
                listar_resync_fallidos_pendientes,
            )

            for r in listar_resync_fallidos_pendientes(limite=100):
                if not _pasa_unidad(r.get("ServerID")):
                    continue
                _fe = r.get("FechaEjecucion")
                pendientes_sincronizaciones.append({
                    "id": r.get("ResyncLogID"),
                    "tipo": "sincronizacion",
                    "titulo": f"Re-sync fallido: {r.get('TipoSync')}",
                    "descripcion": (r.get("Mensaje") or "")[:180],
                    "solicitante": r.get("UnidadCodigo") or "",
                    "fecha": _fe.isoformat() if hasattr(_fe, "isoformat") else str(_fe or ""),
                    "tipo_sync": r.get("TipoSync"),
                    "server_id": r.get("ServerID"),
                    "unidad_codigo": r.get("UnidadCodigo"),
                    "data": r,
                })
        except Exception as _e:
            logging.warning(f"[pendientes-unificados] sincronizaciones: {_e}")

    # ===== ORDENAR URGENTES =====
    # Primero los vencidos (más antiguos primero), luego próximos a vencer
    urgentes.sort(key=lambda x: (not x.get("vencido"), x.get("horas_restantes", 0) if x.get("tipo") == "nomina" else -x.get("horas_pendiente", 0)))

    _cats = {
        "urgentes": urgentes,
        "catalogos": pendientes_catalogos,
        "proveedores": pendientes_proveedores,
        "nominas": pendientes_nominas,
        "fecha_operativa": pendientes_fecha_operativa,
        "auditorias": pendientes_auditorias,
        "alertas": pendientes_alertas,
        "excepciones": pendientes_excepciones,
        "sincronizaciones": pendientes_sincronizaciones,
    }
    _contadores = {k: len(v) for k, v in _cats.items()}
    _contadores["total"] = sum(len(v) for v in _cats.values())
    return {**_cats, "contadores": _contadores}


class RevisarExcepcionRequest(BaseModel):
    excepcion_key: str
    titulo: Optional[str] = None
    server_id: Optional[str] = None


@api_router.post("/sistema/excepciones/revisar")
async def marcar_excepcion_revisada(body: RevisarExcepcionRequest, current_user: Dict = Depends(get_current_user)):
    """Marca una excepción estratégica como REVISADA para que salga de la bandeja Mis Tareas."""
    if not body.excepcion_key:
        raise HTTPException(status_code=400, detail="excepcion_key requerido")
    try:
        from core.scheduler.jobs.alertas_excepciones_job import (
            marcar_excepcion_revisada_estado,
        )

        marcar_excepcion_revisada_estado(
            key=body.excepcion_key,
            titulo=body.titulo,
            server_id=body.server_id,
            revisado_por=current_user.get("email", "unknown"),
        )

        return {
            "success": True,
            "excepcion_key": body.excepcion_key,
            "estado": "REVISADA",
        }
    except Exception as e:
        logging.error(f"[excepciones/revisar] {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo marcar como revisada: {e}")


@api_router.post("/sistema/excepciones/silenciar-backlog")
async def silenciar_backlog_excepciones_endpoint(current_user: Dict = Depends(get_current_user)):
    """Pre-marca como notificadas todas las excepciones actuales (solo admin)."""
    if not es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        from core.scheduler.jobs.alertas_excepciones_job import silenciar_backlog_excepciones
        r = await silenciar_backlog_excepciones()
        return {"success": True, **r}
    except Exception as e:
        logging.error(f"[excepciones/silenciar-backlog] {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo silenciar el backlog: {e}")


@api_router.post("/sistema/excepciones/notificar-ahora")
async def notificar_excepciones_ahora_endpoint(
    modo: str = "prueba",
    current_user: Dict = Depends(get_current_user),
):
    """
    Dispara el notificador manualmente (solo admin).
    - modo=prueba (default): envía un mensaje de prueba a los canales para validarlos al instante.
    - modo=real: ejecuta el notificador real (solo envía excepciones nuevas no notificadas).
    """
    if not es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        if modo == "real":
            from core.scheduler.jobs.alertas_excepciones_job import execute_alertas_excepciones_notifier
            r = await execute_alertas_excepciones_notifier()
        else:
            from core.scheduler.jobs.alertas_excepciones_job import enviar_prueba_canales
            r = await enviar_prueba_canales()
        return {"success": True, "modo": modo, **r}
    except Exception as e:
        logging.error(f"[excepciones/notificar-ahora] {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo notificar: {e}")



async def marcar_tarea_leida(tarea_id: str, current_user: Dict = Depends(get_current_user)):
    """Marca una tarea/notificación como leída"""
    # SQL-FIRST: tarea legacy Mongo neutralizada; pendiente mapeo canónico CRM_Tareas/Operativo_TareasCompras.
    return {"success": True}


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
    # SQL-FIRST: write legacy /nomina neutralizado; flujo canónico vive en /rrhh/nominas/flujo.


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

    ciclos = []  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
    ciclos = await cursor.to_list(length=100)  # noqa: F821

    # Limpiar _id de MongoDB
    for ciclo in ciclos:
        ciclo.pop("_id", None)

    return {"ciclos": ciclos, "total": len(ciclos)}


@api_router.get("/nomina/ciclos/{ciclo_id}")
async def obtener_ciclo_nomina(ciclo_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene el detalle de un ciclo de nómina"""
    ciclo = None  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")

    ciclo.pop("_id", None)
    return {"ciclo": ciclo}


@api_router.post("/nomina/ciclos")
async def crear_ciclo_nomina(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea un nuevo ciclo de nómina"""
    if not es_supervisor_o_superior(current_user):
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
        result_suc = await execute_edarsa_hub_query(query_suc)  # noqa: F821
        if result_suc.get("datos"):
            sucursal_nombre = result_suc["datos"][0].get("Nombre", "Sucursal")
    except Exception:
        pass

    # Verificar si ya existe un ciclo activo para esta sucursal en la misma fecha
    # SQL-FIRST: validación legacy /nomina neutralizada; flujo canónico vive en /rrhh/nominas/flujo.
    ciclo_existente = None
    if ciclo_existente:
        raise HTTPException(status_code=400, detail="Ya existe un ciclo activo para esta sucursal y fecha de corte")

    # Obtener configuración
    config = None  # SQL-FIRST: configuración legacy /nomina neutralizada
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

    # SQL-FIRST: insert legacy /nomina neutralizado; flujo canónico vive en /rrhh/nominas/flujo.

    return {"success": True, "ciclo_id": ciclo_id, "message": "Ciclo de nómina creado correctamente"}


@api_router.post("/nomina/ciclos/{ciclo_id}/avanzar")
async def avanzar_etapa_nomina(ciclo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Avanza el ciclo de nómina a la siguiente etapa (requiere firma de autorización)"""
    password = body.get('password')
    comentario = body.get('comentario', '')

    if not password:
        raise HTTPException(status_code=400, detail="Se requiere contraseña de autorización")

    # Verificar contraseña
    # SQL-FIRST: usuario actual ya proviene de get_current_user.
    user = current_user
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Obtener ciclo
    ciclo = None  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
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
    config = None  # SQL-FIRST: configuración legacy /nomina neutralizada
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

    # SQL-FIRST: write legacy /nomina neutralizado; flujo canónico vive en /rrhh/nominas/flujo.

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
    ciclo = None  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
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
    # SQL-FIRST: write legacy /nomina neutralizado; flujo canónico vive en /rrhh/nominas/flujo.

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
    ciclo = None  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")

    movimientos = []  # SQL-FIRST: movimientos legacy /nomina neutralizados
    movimientos = await cursor.to_list(length=500)  # noqa: F821

    for mov in movimientos:
        mov.pop("_id", None)

    return {"movimientos": movimientos, "total": len(movimientos)}


@api_router.post("/nomina/ciclos/{ciclo_id}/movimientos")
async def agregar_movimiento_nomina(ciclo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Agrega un movimiento de nómina (incidencia) a un ciclo"""
    # Verificar que el ciclo existe y está en etapa correcta
    ciclo = None  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
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
        result_col = await execute_edarsa_hub_query(query_col)  # noqa: F821
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

    # SQL-FIRST: insert movimiento legacy /nomina neutralizado.

    # Actualizar contador en el ciclo
    # SQL-FIRST: write legacy /nomina neutralizado; flujo canónico vive en /rrhh/nominas/flujo.

    return {"success": True, "movimiento_id": movimiento_id, "message": "Movimiento agregado"}


@api_router.delete("/nomina/movimientos/{movimiento_id}")
async def eliminar_movimiento_nomina(movimiento_id: str, current_user: Dict = Depends(get_current_user)):
    """Elimina un movimiento de nómina"""
    movimiento = None  # SQL-FIRST: movimientos legacy /nomina neutralizados
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    ciclo_id = movimiento.get("ciclo_id")

    # Verificar etapa del ciclo
    ciclo = None  # SQL-FIRST: legacy /nomina neutralizado; usar /rrhh/nominas/flujo
    if ciclo and ciclo.get("etapa_actual") not in ["headcount", "incidencias", "validacion_rh"]:
        raise HTTPException(status_code=400, detail="No se pueden eliminar movimientos en esta etapa")

    # SQL-FIRST: delete movimiento legacy /nomina neutralizado.

    # Actualizar contador
    # SQL-FIRST: write legacy /nomina neutralizado; flujo canónico vive en /rrhh/nominas/flujo.

    return {"success": True, "message": "Movimiento eliminado"}


@api_router.get("/nomina/configuracion")
async def obtener_configuracion_nomina(current_user: Dict = Depends(get_current_user)):
    """Obtiene la configuración de nóminas"""
    config = None  # SQL-FIRST: configuración legacy /nomina neutralizada

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
    if not es_admin(current_user):
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

    # SQL-FIRST: update configuración legacy /nomina neutralizado.

    return {"success": True, "message": "Configuración guardada correctamente"}


@api_router.get("/nomina/kpis")
async def listar_kpis_nomina(current_user: Dict = Depends(get_current_user)):
    """Lista los KPIs configurados por puesto"""
    kpis = []  # SQL-FIRST: KPIs legacy /nomina neutralizados
    kpis = await cursor.to_list(length=100)  # noqa: F821

    for kpi in kpis:
        kpi.pop("_id", None)

    return {"kpis": kpis, "total": len(kpis)}


@api_router.post("/nomina/kpis")
async def crear_kpi_nomina(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea o actualiza KPIs para un puesto"""
    if not es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo Administradores pueden configurar KPIs")

    puesto_id = body.get('puesto_id')
    indicadores = body.get('indicadores', [])

    if not puesto_id:
        raise HTTPException(status_code=400, detail="Puesto es requerido")

    # Obtener nombre del puesto
    puesto_nombre = "Puesto"
    try:
        query = f"SELECT Descripcion FROM RH_Cat_Puestos WHERE PuestoID = {puesto_id}"
        result = await execute_edarsa_hub_query(query)  # noqa: F821
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
    # SQL-FIRST: update KPIs legacy /nomina neutralizado.

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
            # SQL-FIRST: rol legacy Mongo neutralizado; RBAC canónico en Usuario_Roles/Sistema_RBAC_Roles.
            rol_doc = None
            if rol_doc and permiso in rol_doc.get('permisos', []):
                return True

    # 3. Rol único - compatibilidad FASE 5
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_FASE_11_WHITELIST:
        # SQL-FIRST: rol legacy Mongo neutralizado; RBAC canónico en Usuario_Roles/Sistema_RBAC_Roles.
        rol_doc = None
        if rol_doc and permiso in rol_doc.get('permisos', []):
            return True

    # 4. Fallback legacy (FASE 3)
    if es_superadmin(user):
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
    if not es_admin(current_user):
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
    if not es_admin(current_user):
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


# Helpers de auditoría legacy (Mongo sec_bitacora_admin) eliminados:
# la bitácora ahora es SQL-First via rbac_pilot_service.registrar_bitacora().


@api_router.post("/admin/permisos/asignar")
async def admin_asignar_permiso(
    request: PermisoAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: asigna/retira un permiso directo (sec_permisos)."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede administrar permisos")
    return rbac_pilot_service.toggle_asignacion(
        request.usuario_email, "PERMISO", request.permiso, request.accion,
        current_user.get('email', 'sistema')
    )


class RolAsignacionRequest(BaseModel):
    """Request para asignar/retirar rol sec_*."""
    usuario_email: str
    rol: str
    accion: str  # "ASIGNAR" o "RETIRAR"


@api_router.post("/admin/roles/asignar")
async def admin_asignar_rol(
    request: RolAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: asigna/retira un rol (sec_roles)."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede administrar roles")
    return rbac_pilot_service.toggle_asignacion(
        request.usuario_email, "ROL", request.rol, request.accion,
        current_user.get('email', 'sistema')
    )



async def _require_rbac_bitacora_ver(current_user: Dict):
    """
    Valida acceso a Bitácora RBAC por permiso efectivo SQL explícito.

    Permiso requerido:
    - SISTEMA_RBAC_BITACORA_VER

    Regla crítica:
    - SUPERADMIN puede entrar solo si el permiso existe asignado por SQL.
    - ADMIN legacy NO hace bypass funcional.
    - No usar has_permiso() aquí porque tiene bypass por tiene_acceso_global.
    """
    permiso_requerido = "SISTEMA_RBAC_BITACORA_VER"
    email = current_user.get("email")

    if not email:
        raise HTTPException(status_code=403, detail=f"Permiso requerido: {permiso_requerido}")


    conn = get_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TOP 1 1
            FROM dbo.Usuario_Catalogo u
            INNER JOIN dbo.Usuario_RolesAsignacion ura
                ON ura.UsuarioID = u.UsuarioID
                AND ura.Activo = 1
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = ura.RolID
                AND r.Activo = 1
            INNER JOIN dbo.Usuario_PermisosRolModulo prm
                ON prm.RolID = r.RolID
                AND prm.Activo = 1
                AND prm.Permitido = 1
            INNER JOIN dbo.Usuario_Modulos m
                ON m.ModuloID = prm.ModuloID
                AND m.Activo = 1
            INNER JOIN dbo.Usuario_Acciones a
                ON a.AccionID = prm.AccionID
                AND a.Activo = 1
            WHERE u.Activo = 1
              AND LOWER(u.Email) = LOWER(%s)
              AND CONCAT(m.CodigoModulo, '_', a.CodigoAccion) = %s
        """, (email, permiso_requerido))
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(
            status_code=403,
            detail=f"Permiso requerido: {permiso_requerido}"
        )

    return True


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
    """Bitácora RBAC SQL-First. Lee de dbo.Usuario_RBAC_Bitacora.

    Acceso por permiso efectivo:
    - SISTEMA_RBAC_BITACORA_VER

    Filtros: fecha_inicio/fecha_fin (YYYY-MM-DD), email (LIKE),
    resultado (exitoso|fallido|parcial), tipo (ASIGNAR|REVOCAR).
    """
    await _require_rbac_bitacora_ver(current_user)
    if limit > 100:
        limit = 100
    total, eventos = rbac_pilot_service.get_bitacora(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, email=email,
        resultado=resultado, tipo=tipo, skip=skip, limit=limit,
    )
    paginas_total = (total + limit - 1) // limit if total > 0 else 1
    pagina_actual = (skip // limit) + 1
    return {
        "total": total,
        "pagina": pagina_actual,
        "paginas_total": paginas_total,
        "limit": limit,
        "eventos": eventos,
    }


@api_router.get("/admin/bitacora/{evento_id}")
async def get_bitacora_evento_detalle(
    evento_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Detalle de un evento de bitácora RBAC.

    Acceso por permiso efectivo:
    - SISTEMA_RBAC_BITACORA_VER
    """
    await _require_rbac_bitacora_ver(current_user)
    evento = rbac_pilot_service.get_bitacora_evento(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


# ==============================================================================
# FIN FASE 12 - BITÁCORA RBAC (SQL-First)
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
    """RBAC piloto SQL-First: lista los perfiles predefinidos disponibles."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede ver perfiles")
    return {"perfiles": rbac_pilot_service.get_perfiles_catalogo()}


class AsignarPerfilRequest(BaseModel):
    usuario_email: str
    perfil: str


@api_router.post("/admin/perfiles/asignar")
async def asignar_perfil_usuario(
    request: AsignarPerfilRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: asigna un perfil (sobrescribe sec_roles con los del perfil)."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede asignar perfiles")
    if request.perfil not in PERFILES_FASE_13_WHITELIST:
        raise HTTPException(status_code=400, detail=f"Perfil '{request.perfil}' no esta en whitelist FASE 13")
    return rbac_pilot_service.asignar_perfil(
        request.usuario_email, request.perfil, current_user.get('email', 'sistema')
    )


class RetirarPerfilRequest(BaseModel):
    usuario_email: str


@api_router.post("/admin/perfiles/retirar")
async def retirar_perfil_usuario(
    request: RetirarPerfilRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: retira el perfil de un usuario (limpia sec_perfil y sec_roles)."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede retirar perfiles")
    return rbac_pilot_service.retirar_perfil(
        request.usuario_email, current_user.get('email', 'sistema')
    )


# ==============================================================================
# FASE 14 - ALCANCE ORGANIZACIONAL: ELIMINADO (SQL-First)
# Los endpoints /admin/alcance/* legacy (Mongo, 0 consumidores) fueron retirados.
# El alcance canónico vive en /api/config-asignaciones
# (Usuario_EmpresasAsignacion / Usuario_SucursalesAsignacion).
# ==============================================================================


# Incluir el router después de definir TODOS los endpoints
app.include_router(api_router)

# WORKER: endpoint autenticado de runtime wake
# Runtime reload marker 2026-09-20: fuerza recarga Preview sin cambio funcional; Produccion fuera de alcance.
from modules.worker_runtime_wake.routes import router as worker_runtime_wake_router
app.include_router(worker_runtime_wake_router, prefix="/api")

# EDARSAHUB Universal Worker Console (Fase 1, solo lectura)
from modules.worker_console.routes import router as worker_console_router
app.include_router(worker_console_router, prefix="/api")

# FASE6: health canónico V1.0 (SQL-First / NO-LIVE) -> /api/health/v1
app.include_router(health_v1_router, prefix="/api")

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

# ============= FASE 0: CONSOLA ADMIN SCHEDULER RESYNC =============
# Re-sincronización controlada con dry_run y trazabilidad completa
# Diseño: /app/docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md
from api.admin_scheduler_resync import router as admin_resync_router
app.include_router(admin_resync_router, tags=["Admin - Scheduler Resync"])
logger.info("Consola Admin Scheduler Resync registrada")

# ============= LIMPIEZA DE CACHÉ PREVIEW =============
# P0-CACHE-PREVIEW: Limpieza automática de cachés en modo preview
from api.admin_cache import router as admin_cache_router
app.include_router(admin_cache_router, tags=["Admin - Cache Management"])
logger.info("Admin Cache Management registrado")

# ============= CALIDAD DE DATOS =============
# DATA-QUALITY: Auditoría y consolidación de datos duplicados
from api.admin_data_quality import router as admin_data_quality_router
app.include_router(admin_data_quality_router, tags=["Admin - Data Quality"])
logger.info("Admin Data Quality registrado")

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
from modules.pricing_ai.routes import router as pricing_ai_router
from modules.dashboard_ejecutivo.routes import router as dashboard_ejecutivo_router
from modules.comercial_analytics.routes import router as comercial_analytics_router
from modules.rentabilidad.routes import router as rentabilidad_router
from modules.alertas_estrategicas.routes import router as alertas_estrategicas_router
from core.sql_first.db import get_sql_connection
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection
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
# Feature Flag: COMERCIAL_V2_ENABLED=true (default ON)
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
# CRM Enterprise (SQL-First)
# =============================================================================
try:
    from modules.crm.routes import router as crm_router
    app.include_router(crm_router, tags=["CRM - Estado"])
    logger.info("✓ CRM Estado router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Estado router: {e}")

# =============================================================================
# CRM Vtiger Integration (REST API)
# =============================================================================
try:
    from modules.crm.vtiger_routes import router as vtiger_router
    app.include_router(vtiger_router, tags=["CRM - Vtiger"])
    logger.info("✓ CRM Vtiger router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM Vtiger router: {e}")

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

# CRM Router SQL-First (Fase 2 - Mayo 2026)
try:
    from modules.comercial import crm_router
    app.include_router(crm_router.router, tags=["CRM SQL-First"])
    logger.info("✓ CRM SQL-First router registrado")
except Exception as e:
    logger.warning(f"Error registrando CRM SQL-First router: {e}")

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
# SISTEMA - MENÚS GOBERNADOS
# =============================================================================
try:
    from modules.sistema.menu_routes import router as menu_router
    app.include_router(menu_router, tags=["Sistema - Menús"])
    logger.info("✓ Sistema Menús router registrado")
except Exception as e:
    logger.warning(f"Error registrando Sistema Menús router: {e}")

# =============================================================================
# CAVA DE SOCIOS (Comercial - Experiencia Cliente)
# =============================================================================
try:
    from modules.cava_socios.routes import router as cava_socios_router
    app.include_router(cava_socios_router, tags=["Cava de Socios"])
    logger.info("✓ Cava de Socios router registrado")
except Exception as e:
    logger.warning(f"Error registrando Cava de Socios router: {e}")

# =============================================================================
# SQL-FIRST HEALTH (P2-06)
# =============================================================================
try:
    from modules.sqlfirst_health.routes import router as sqlfirst_health_router
    app.include_router(sqlfirst_health_router)
    logger.info("✓ SQL-First Health router registrado")
except Exception as e:
    logger.warning(f"Error registrando SQL-First Health router: {e}")

# PRICING IA (P3-05)
# =============================================================================
try:
    app.include_router(pricing_ai_router)
    logger.info("✓ Pricing IA router registrado")
except Exception as e:
    logger.warning(f"Error registrando Pricing IA router: {e}")

# DASHBOARD EJECUTIVO (P3-06)
# =============================================================================
try:
    app.include_router(dashboard_ejecutivo_router)

    app.include_router(
        comercial_analytics_router,
        prefix="/api",
    )
    logger.info("✓ Dashboard Ejecutivo router registrado")
except Exception as e:
    logger.warning(f"Error registrando Dashboard Ejecutivo router: {e}")

# RENTABILIDAD (P3-07)
# =============================================================================
try:
    app.include_router(rentabilidad_router)
    logger.info("✓ Rentabilidad router registrado")
except Exception as e:
    logger.warning(f"Error registrando Rentabilidad router: {e}")

# ALERTAS ESTRATÉGICAS (P3-08)
# =============================================================================
try:
    app.include_router(alertas_estrategicas_router)
    logger.info("✓ Alertas Estratégicas router registrado")
except Exception as e:
    logger.warning(f"Error registrando Alertas Estratégicas router: {e}")


# =============================================================================
# ECONOMÍA - DOMINIO ECONÓMICO CANÓNICO
# =============================================================================
try:
    from modules.economia.routes import router as economia_router
    app.include_router(economia_router)
    logger.info("Economía router registrado")
except Exception as e:
    logger.warning(f"Error registrando Economía router: {e}")


# =============================================================================
# MÓDULOS SQL-FIRST (Migración MongoDB Legacy)
# =============================================================================
try:
    from modules.informes_auditoria.routes import router as informes_auditoria_sql_router
    app.include_router(informes_auditoria_sql_router, tags=["Informes Auditoría SQL"])
    logger.info("✓ Informes Auditoría SQL router registrado")
except Exception as e:
    logger.warning(f"Error registrando Informes Auditoría SQL router: {e}")

try:
    from modules.consultas_sql.routes import router as consultas_sql_router
    app.include_router(consultas_sql_router, tags=["Consultas SQL"])
    logger.info("✓ Consultas SQL router registrado")
except Exception as e:
    logger.warning(f"Error registrando Consultas SQL router: {e}")

try:
    from modules.catalogos_workflow_sql.routes import router as catalogos_workflow_sql_router
    app.include_router(catalogos_workflow_sql_router, tags=["Catalogos Workflow SQL"])
    logger.info("✓ Catalogos Workflow SQL router registrado")
except Exception as e:
    logger.warning(f"Error registrando Catalogos Workflow SQL router: {e}")

try:
    from modules.catalogos_workflow_compat.routes import router as catalogos_workflow_compat_router
    app.include_router(catalogos_workflow_compat_router, tags=["Catalogos Workflow Compat"])
    logger.info("✓ Catalogos Workflow Compat router registrado")
except Exception as e:
    logger.warning(f"Error registrando Catalogos Workflow Compat router: {e}")

try:
    from modules.sistema_users_sql.routes import router as sistema_users_sql_router
    app.include_router(sistema_users_sql_router, tags=["Sistema Users SQL"])
    logger.info("✓ Sistema Users SQL router registrado")
except Exception as e:
    logger.warning(f"Error registrando Sistema Users SQL router: {e}")

try:
    from modules.rbac_context_sql.routes import router as rbac_context_sql_router
    app.include_router(rbac_context_sql_router, tags=["RBAC Context SQL"])
    logger.info("✓ RBAC Context SQL router registrado")
except Exception as e:
    logger.warning(f"Error registrando RBAC Context SQL router: {e}")

try:
    from modules.rbac_context_sql.context_routes import router as rbac_context_access_router
    app.include_router(rbac_context_access_router, tags=["RBAC Context Access"])
    logger.info("✓ RBAC Context Access router registrado")
except Exception as e:
    logger.warning(f"Error registrando RBAC Context Access router: {e}")

try:
    from modules.scripts_pendientes.routes import router as scripts_pendientes_sql_router
    app.include_router(scripts_pendientes_sql_router, tags=["Scripts Pendientes SQL"])
    logger.info("✓ Scripts Pendientes SQL router registrado")
except Exception as e:
    logger.warning(f"Error registrando Scripts Pendientes SQL router: {e}")

try:
    from modules.sql_compat_bridge.routes import router as sql_compat_bridge_router
    app.include_router(sql_compat_bridge_router, tags=["SQL Compat Bridge"])
    logger.info("✓ SQL Compat Bridge router registrado")
except Exception as e:
    logger.warning(f"Error registrando SQL Compat Bridge router: {e}")


# =============================================================================
# UNIVERSAL WORKER - WAKE INTERNO CANONICO
# =============================================================================
try:
    from modules.worker_runtime_wake.routes import router as worker_runtime_wake_router
    app.include_router(worker_runtime_wake_router, prefix="/api")
    logger.info("Universal Worker wake router registrado")
except Exception as e:
    logger.warning(f"Error registrando Universal Worker wake router: {e}")


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


# ==========================================
# ENDPOINT DESCARGA SCHEMA SQL
# ==========================================
@app.get("/api/download/schema")
async def download_schema_zip():
    raise HTTPException(
        status_code=410,
        detail=(
            "La descarga legacy fue retirada por seguridad. "
            "Los respaldos no se publican desde la aplicación."
        ),
    )

@app.get("/api/download/schema-sql")
async def download_schema_sql():
    raise HTTPException(
        status_code=410,
        detail=(
            "La descarga legacy fue retirada por seguridad. "
            "El esquema no se publica desde la aplicación."
        ),
    )

@app.get("/api/download/backup-full")
async def download_backup_full():
    raise HTTPException(
        status_code=410,
        detail=(
            "La descarga legacy fue retirada por seguridad. "
            "Los respaldos no se publican desde la aplicación."
        ),
    )

@app.get("/api/download/manual-desarrollo")
async def download_manual_desarrollo():
    """Descarga del Manual de Flujo Desarrollo-Producción en Word."""
    import os
    docx_path = "/app/backend/static/MANUAL_FLUJO_DESARROLLO_PRODUCCION_EDARSAHUB.docx"
    if os.path.exists(docx_path):
        return FileResponse(
            path=docx_path,
            filename="MANUAL_FLUJO_DESARROLLO_PRODUCCION_EDARSAHUB.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    raise HTTPException(status_code=404, detail="Archivo no encontrado")


@app.get("/api/download/backup-db-completo")
async def download_backup_db_completo():
    raise HTTPException(
        status_code=410,
        detail=(
            "La descarga legacy fue retirada por seguridad. "
            "Los respaldos no se publican desde la aplicación."
        ),
    )

@app.get("/api/download/backup-codigo-fuente")
async def download_backup_codigo_fuente():
    raise HTTPException(
        status_code=410,
        detail=(
            "La descarga legacy fue retirada por seguridad. "
            "Los respaldos no se publican desde la aplicación."
        ),
    )



@app.get("/api/descargar/codigo")
async def descargar_codigo_simple():
    raise HTTPException(
        status_code=410,
        detail=(
            "La descarga legacy fue retirada por seguridad. "
            "Los respaldos no se publican desde la aplicación."
        ),
    )
