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
        fingerprint = hashlib.sha256(key.encode()).hexdigest()[:6]
        print(f"[ENCRYPTION] SERVER_SECRET_KEY loaded: true")
        print(f"[ENCRYPTION] Key fingerprint: {fingerprint}")
        return True
    else:
        if is_preview or is_production:
            print("[ENCRYPTION] WARNING: SERVER_SECRET_KEY not configured")
            print("[ENCRYPTION] Encrypted credentials will NOT be decryptable")
            print("[ENCRYPTION] Jobs/syncs that require credentials may fail")
            return False
        else:
            print("[ENCRYPTION] SERVER_SECRET_KEY not configured (development mode)")
            return False

_ENCRYPTION_AVAILABLE = _validate_server_secret_key()

# ==============================================================================
# IMPORTS PRINCIPALES (después de cargar .env)
# ==============================================================================
from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import pymssql
import pytds
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

from catalogo.consultas_mpro import CONSULTAS_MPRO, ESTRUCTURA_TABLAS_MPRO
from catalogo.consultas_softrestaurant import CONSULTAS_SOFTRESTAURANT, ESTRUCTURA_TABLAS_SOFTRESTAURANT
from catalogo.catalogo_consultas import CATALOGO_CONSULTAS, get_consultas_por_categoria as catalogo_get_consultas, get_categorias as catalogo_get_categorias, preparar_sql as catalogo_preparar_sql
from modules.worker_runtime_wake.routes import router as worker_runtime_wake_router

logger = logging.getLogger(__name__)

from core.mongo_stub import get_stub_database
db = get_stub_database()
logger.info("[DB] Sistema funcionando 100% SQL Server - MongoDB ELIMINADO (usando StubDatabase)")

app = FastAPI(title="EDARSA HUB API")
api_router = APIRouter(prefix="/api")
app.include_router(worker_runtime_wake_router, prefix="/api")

STATIC_DIR = ROOT_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

DOWNLOADS_DIR = STATIC_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="api-downloads")

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"[ALERTA CRÍTICA] Fallo no manejado en ruta {request.url.path}: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor. Proceso recuperado automáticamente.", "data": []})

@app.get("/api/health")
async def health_check():
    return {"status": "operativo", "sistema": "EDARSA HUB", "version": "1.0"}
