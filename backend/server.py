from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

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
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    host: str
    port: int = 1433
    database: str
    username: str
    system_type: str  # "MPRO", "SoftRestaurant", "Otro"
    date_calculation_method: str = "inventory_dates"  # Método para calcular fechas de ventas
    sucursales: List[str] = []  # IDs de sucursales
    # Filtros configurables para consultas
    tipos_movimiento: List[str] = []  # Códigos de tipos de movimiento a incluir
    categorias: List[str] = []  # Códigos de categorías a incluir
    departamentos: List[str] = []  # Códigos de departamentos a incluir
    # Consultas SQL personalizadas para el análisis de inventario
    query_inventario: Optional[Dict] = None  # Consulta para obtener inventarios
    query_ventas: Optional[Dict] = None  # Consulta para obtener ventas
    query_movimientos: Optional[Dict] = None  # Consulta para obtener movimientos/entradas
    queries_configured: bool = False  # Si todas las consultas están configuradas y validadas
    visible_en_operaciones: bool = True  # Si se muestra en dashboards y menús operativos
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

# ============= AUTHENTICATION =============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    payload = verify_token(token)
    user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# ============= SQL SERVER FUNCTIONS =============

def parse_sql_server_host(host: str, default_port: int = 1433) -> tuple:
    """
    Parsea cadenas de conexión SQL Server en varios formatos:
    - hostname
    - hostname,port
    - hostname\instance
    - hostname,port\instance
    - hostname\instance,port
    
    Retorna: (hostname_only, port, instance)
    - hostname_only: solo el hostname sin instancia
    - port: puerto como entero
    - instance: nombre de la instancia o None
    """
    import re
    
    # Remover espacios
    host = host.strip()
    port = default_port
    instance = None
    hostname = host
    
    # Caso 1: hostname,port\instance (ej: server.ddns.net,6669\nationalsoft)
    match = re.match(r'^([^,\\]+),(\d+)\\(.+)$', host)
    if match:
        hostname = match.group(1)
        port = int(match.group(2))
        instance = match.group(3)
        logging.info(f"Parsed DDNS format: hostname={hostname}, port={port}, instance={instance}")
        return (hostname, port, instance)
    
    # Caso 2: hostname\instance,port (ej: server\instance,1433)
    match = re.match(r'^([^,\\]+)\\([^,]+),(\d+)$', host)
    if match:
        hostname = match.group(1)
        instance = match.group(2)
        port = int(match.group(3))
        logging.info(f"Parsed instance,port format: hostname={hostname}, instance={instance}, port={port}")
        return (hostname, port, instance)
    
    # Caso 3: hostname\instance (ej: server\SQLEXPRESS)
    match = re.match(r'^([^,\\]+)\\(.+)$', host)
    if match:
        hostname = match.group(1)
        instance = match.group(2)
        logging.info(f"Parsed instance format: hostname={hostname}, instance={instance}")
        return (hostname, port, instance)
    
    # Caso 4: hostname,port (ej: server.com,1433)
    match = re.match(r'^([^,\\]+),(\d+)$', host)
    if match:
        hostname = match.group(1)
        port = int(match.group(2))
        logging.info(f"Parsed host,port format: hostname={hostname}, port={port}")
        return (hostname, port, None)
    
    # Caso 5: Solo hostname
    logging.info(f"Using simple hostname: {host}")
    return (host, port, None)


def test_sql_connection(host: str, port: int, database: str, username: str, password: str) -> bool:
    """
    Prueba la conexión a SQL Server usando pytds (preferido) con fallback a pymssql.
    """
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.info(f"Testing connection to: hostname={hostname}, port={parsed_port}, instance={instance}, db={database}")
    
    # Primero intentar con pytds (mejor soporte para conexiones complejas)
    try:
        logging.info("Intentando conexión con pytds...")
        conn = pytds.connect(
            server=hostname,
            port=parsed_port,
            database=database,
            user=username,
            password=password,
            timeout=30,
            login_timeout=30
        )
        conn.close()
        logging.info("Conexión exitosa con pytds")
        return True
    except Exception as pytds_error:
        logging.warning(f"pytds falló: {str(pytds_error)}, intentando pymssql...")
    
    # Fallback a pymssql
    try:
        server_string = f"{hostname}\\{instance}" if instance else hostname
        conn = pymssql.connect(
            server=server_string, 
            port=parsed_port, 
            user=username, 
            password=password, 
            database=database
        )
        conn.close()
        logging.info("Conexión exitosa con pymssql")
        return True
    except Exception as pymssql_error:
        logging.error(f"pymssql también falló: {str(pymssql_error)}")
        return False


# Diccionario en memoria para tracking rápido de estado de servidores
_server_status_cache = {}

def mark_server_offline(host: str):
    """Marca un servidor como offline en caché de memoria con backoff exponencial"""
    current = _server_status_cache.get(host, {})
    fail_count = current.get("fail_count", 0) + 1
    
    # Backoff exponencial: 5min, 10min, 20min, 30min máximo
    wait_minutes = min(5 * (2 ** (fail_count - 1)), 30)
    
    _server_status_cache[host] = {
        "is_online": False,
        "last_check": datetime.now(timezone.utc),
        "fail_count": fail_count,
        "wait_minutes": wait_minutes
    }
    logging.info(f"Servidor {host} marcado offline (intento {fail_count}) - próximo reintento en {wait_minutes} min")

def mark_server_online(host: str):
    """Marca un servidor como online en caché de memoria"""
    _server_status_cache[host] = {
        "is_online": True,
        "last_check": datetime.now(timezone.utc),
        "fail_count": 0,
        "wait_minutes": 0
    }

def is_server_offline_in_memory(host: str) -> bool:
    """
    Verifica si un servidor está marcado como offline.
    Usa backoff exponencial para evitar parecer un ataque.
    """
    status = _server_status_cache.get(host)
    if not status:
        return False
    
    if status.get("is_online", True):
        return False
    
    # Verificar si ha pasado suficiente tiempo según el backoff
    last_check = status.get("last_check")
    wait_minutes = status.get("wait_minutes", 5)
    
    if last_check:
        diff = (datetime.now(timezone.utc) - last_check).total_seconds() / 60
        if diff < wait_minutes:
            logging.debug(f"Servidor {host} en cooldown - esperar {wait_minutes - diff:.1f} min más")
            return True
    
    return False

def get_server_cooldown_info(host: str) -> dict:
    """Obtiene información del cooldown de un servidor"""
    status = _server_status_cache.get(host, {})
    if not status or status.get("is_online", True):
        return {"is_offline": False}
    
    last_check = status.get("last_check")
    wait_minutes = status.get("wait_minutes", 5)
    
    if last_check:
        diff = (datetime.now(timezone.utc) - last_check).total_seconds() / 60
        remaining = max(0, wait_minutes - diff)
        return {
            "is_offline": True,
            "fail_count": status.get("fail_count", 0),
            "wait_minutes": wait_minutes,
            "remaining_minutes": round(remaining, 1)
        }
    
    return {"is_offline": True}


def execute_sql_query(host: str, port: int, database: str, username: str, password: str, query: str, timeout_seconds: int = 45) -> List[Dict]:
    """
    Ejecuta una consulta SQL usando pytds (preferido) con fallback a pymssql.
    Incluye verificación de estado offline con backoff exponencial para evitar
    comportamiento de bot/malware.
    """
    # Verificar si el servidor está en cooldown (offline con backoff)
    if is_server_offline_in_memory(host):
        cooldown = get_server_cooldown_info(host)
        logging.info(f"Servidor {host} en cooldown - {cooldown.get('remaining_minutes', 0):.1f} min restantes")
        return []
    
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.info(f"Conectando a SQL Server: hostname={hostname}, port={parsed_port}, db={database}")
    
    # Primero intentar con pytds
    try:
        logging.info("Ejecutando query con pytds...")
        conn = pytds.connect(
            server=hostname,
            port=parsed_port,
            database=database,
            user=username,
            password=password,
            timeout=timeout_seconds,
            login_timeout=15  # Reducido de 30 a 15 segundos
        )
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Obtener nombres de columnas
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convertir datetime a string
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[col] = value
            results.append(row_dict)
        
        conn.close()
        logging.info(f"Query exitosa con pytds: {len(results)} registros")
        mark_server_online(host)  # Marcar como online
        return results
        
    except Exception as pytds_error:
        logging.warning(f"pytds falló: {str(pytds_error)}, intentando pymssql...")
    
    # Fallback a pymssql
    try:
        server_string = f"{hostname}\\{instance}" if instance else hostname
        logging.info(f"Ejecutando query con pymssql en {server_string}:{parsed_port}...")
        conn = pymssql.connect(
            server=server_string, 
            port=parsed_port, 
            user=username, 
            password=password, 
            database=database, 
            timeout=timeout_seconds, 
            login_timeout=15  # Reducido de 30 a 15 segundos
        )
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        # Convertir datetime a string
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        logging.info(f"Query exitosa con pymssql: {len(results)} registros")
        mark_server_online(host)  # Marcar como online
        return results
        
    except Exception as pymssql_error:
        error_msg = f"Error ejecutando consulta. pytds y pymssql fallaron: {str(pymssql_error)}"
        logging.error(error_msg)
        mark_server_offline(host)  # Marcar como offline
        return []  # Devolver lista vacía en lugar de lanzar excepción

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
            except:
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

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Hash password
    hashed_pw = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.model_dump()
    del user_dict['password']
    user = User(**user_dict)
    
    doc = user.model_dump()
    doc['password'] = hashed_pw
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    token = create_token(user.id, user.email, user.role)
    
    return {"token": token, "user": user.model_dump()}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not user.get('active', True):
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    
    token = create_token(user['id'], user['email'], user['role'])
    
    user_response = {k: v for k, v in user.items() if k != 'password'}
    
    return {"token": token, "user": user_response}

@api_router.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: Dict, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Preparar datos de actualización
    update_data = {}
    if 'name' in user_data:
        update_data['name'] = user_data['name']
    if 'email' in user_data:
        update_data['email'] = user_data['email']
    if 'role' in user_data:
        update_data['role'] = user_data['role']
    if 'sucursales' in user_data:
        update_data['sucursales'] = user_data['sucursales']
    
    # Solo hashear contraseña si se proporciona una nueva
    if 'password' in user_data and user_data['password']:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        update_data['password'] = pwd_context.hash(user_data['password'])
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    return {"message": "Usuario actualizado"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await db.users.update_one({"id": user_id}, {"$set": {"active": False}})
    return {"message": "Usuario desactivado"}

@api_router.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza los permisos de un usuario"""
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {}
    if 'allowed_servers' in permissions:
        update_data['allowed_servers'] = permissions['allowed_servers']
    if 'allowed_sucursales' in permissions:
        update_data['allowed_sucursales'] = permissions['allowed_sucursales']
    if 'allowed_warehouses' in permissions:
        update_data['allowed_warehouses'] = permissions['allowed_warehouses']
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    return {"message": "Permisos actualizados"}

# ============= ROLES CRUD =============

# Módulos disponibles para asignar permisos
MODULOS_DISPONIBLES = [
    {"id": "tablero_ejecutivo", "nombre": "Tablero Ejecutivo", "descripcion": "Vista consolidada de todas las unidades"},
    {"id": "comercial", "nombre": "Comercial", "descripcion": "Dashboard de ventas, ticket perfecto, metas"},
    {"id": "compras", "nombre": "Compras", "descripcion": "Dashboard de compras, autorización, análisis"},
    {"id": "inventarios", "nombre": "Inventarios", "descripcion": "Análisis de inventarios, reportes"},
    {"id": "dashboard_inventarios", "nombre": "Dashboard Inventarios", "descripcion": "Gráficas de diferencias de inventario"},
    {"id": "finanzas", "nombre": "Finanzas", "descripcion": "Libro mayor, cuentas, conciliación"},
    {"id": "produccion", "nombre": "Producción", "descripcion": "Órdenes de producción, BOM"},
    {"id": "recursos_humanos", "nombre": "Recursos Humanos", "descripcion": "Nómina, asistencias"},
    {"id": "reportes_bi", "nombre": "Reportes BI", "descripcion": "Análisis predictivo, KPIs avanzados"},
    {"id": "servidores", "nombre": "Servidores", "descripcion": "Configuración de conexiones a BD"},
    {"id": "catalogo_sql", "nombre": "Catálogo SQL", "descripcion": "Consultas SQL personalizadas"},
    {"id": "explorador_bd", "nombre": "Explorador BD", "descripcion": "Explorar estructura de bases de datos"},
    {"id": "alertas", "nombre": "Alertas", "descripcion": "Configuración de alertas del sistema"},
    {"id": "usuarios", "nombre": "Usuarios", "descripcion": "Gestión de usuarios y roles"},
]

@api_router.get("/roles/modulos")
async def get_modulos_disponibles(current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de módulos disponibles para asignar permisos"""
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    return MODULOS_DISPONIBLES

@api_router.get("/roles")
async def get_roles(current_user: Dict = Depends(get_current_user)):
    """Obtiene todos los roles del sistema"""
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    roles = await db.roles.find({}, {"_id": 0}).to_list(100)
    
    # Si no hay roles, crear los predeterminados
    if not roles:
        default_roles = [
            {
                "id": str(uuid.uuid4()),
                "nombre": "Administrador",
                "descripcion": "Acceso total al sistema",
                "permisos": [m["id"] for m in MODULOS_DISPONIBLES],  # Todos los módulos
                "es_sistema": True,  # No se puede eliminar
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "nombre": "Supervisor",
                "descripcion": "Acceso a módulos operativos y reportes",
                "permisos": ["tablero_ejecutivo", "comercial", "compras", "inventarios", "dashboard_inventarios", "catalogo_sql", "alertas"],
                "es_sistema": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "nombre": "Usuario",
                "descripcion": "Acceso básico de consulta",
                "permisos": ["comercial", "compras", "inventarios", "dashboard_inventarios"],
                "es_sistema": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.roles.insert_many(default_roles)
        roles = default_roles
    
    return roles

@api_router.post("/roles")
async def create_role(role_data: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea un nuevo rol"""
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar que no exista un rol con el mismo nombre
    existing = await db.roles.find_one({"nombre": role_data.get("nombre")})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
    
    new_role = {
        "id": str(uuid.uuid4()),
        "nombre": role_data.get("nombre", ""),
        "descripcion": role_data.get("descripcion", ""),
        "permisos": role_data.get("permisos", []),
        "es_sistema": False,  # Los roles creados por usuario no son de sistema
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.roles.insert_one(new_role)
    if "_id" in new_role:
        del new_role["_id"]
    return new_role

@api_router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza un rol existente"""
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    existing = await db.roles.find_one({"id": role_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Solo permitir cambiar nombre/descripción/permisos en roles de sistema
    update_data = {}
    if "descripcion" in role_data:
        update_data["descripcion"] = role_data["descripcion"]
    if "permisos" in role_data:
        update_data["permisos"] = role_data["permisos"]
    
    # Solo permitir cambiar nombre si no es rol de sistema
    if not existing.get("es_sistema") and "nombre" in role_data:
        # Verificar que el nuevo nombre no exista
        if role_data["nombre"] != existing["nombre"]:
            dup = await db.roles.find_one({"nombre": role_data["nombre"]})
            if dup:
                raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
        update_data["nombre"] = role_data["nombre"]
    
    if update_data:
        await db.roles.update_one({"id": role_id}, {"$set": update_data})
    
    updated = await db.roles.find_one({"id": role_id}, {"_id": 0})
    return updated

@api_router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: Dict = Depends(get_current_user)):
    """Elimina un rol (solo roles no de sistema)"""
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    existing = await db.roles.find_one({"id": role_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    if existing.get("es_sistema"):
        raise HTTPException(status_code=400, detail="No se pueden eliminar roles de sistema")
    
    # Verificar que no haya usuarios con este rol
    users_with_role = await db.users.count_documents({"role": existing["nombre"]})
    if users_with_role > 0:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar: {users_with_role} usuario(s) tienen este rol asignado")
    
    await db.roles.delete_one({"id": role_id})
    return {"message": "Rol eliminado"}

# ============= PERMISSION HELPERS =============

def user_has_server_access(user: Dict, server_id: str) -> bool:
    """Verifica si un usuario tiene acceso a un servidor"""
    if user.get('role') == 'Administrador':
        return True
    allowed = user.get('allowed_servers', [])
    return server_id in allowed if allowed else False

def filter_servers_by_permissions(servers: List[Dict], user: Dict) -> List[Dict]:
    """Filtra servidores según permisos del usuario"""
    role = user.get('role', '')
    logging.info(f"filter_servers: role={role}, total_servers={len(servers)}")
    if role == 'Administrador':
        logging.info("Usuario es Admin, retornando todos los servidores")
        return servers
    allowed = user.get('allowed_servers', [])
    if not allowed:
        logging.info("Usuario sin servidores asignados, retornando lista vacía")
        return []
    filtered = [s for s in servers if s.get('id') in allowed]
    logging.info(f"Filtrado: {len(filtered)} servidores")
    return filtered

def filter_sucursales_by_permissions(sucursales: List[Dict], user: Dict, server_id: str) -> List[Dict]:
    """Filtra sucursales según permisos del usuario"""
    if user.get('role') == 'Administrador':
        return sucursales
    allowed_suc = user.get('allowed_sucursales', {})
    if server_id not in allowed_suc or not allowed_suc[server_id]:
        return sucursales  # Sin restricción = ver todas
    return [s for s in sucursales if s.get('id') in allowed_suc[server_id]]

# ============= SERVERS =============

@api_router.post("/servers")
async def create_server(server_data: ServerCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Test connection
    if not test_sql_connection(server_data.host, server_data.port, server_data.database, server_data.username, server_data.password):
        raise HTTPException(status_code=400, detail="No se pudo conectar al servidor")
    
    server_dict = server_data.model_dump()
    password = server_dict.pop('password')
    
    server = Server(**server_dict)
    doc = server.model_dump()
    doc['password'] = password  # Store encrypted in production
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.servers.insert_one(doc)
    
    return server.model_dump()

@api_router.get("/servers", response_model=List[Server])
async def get_servers(current_user: Dict = Depends(get_current_user)):
    servers = await db.servers.find({"active": True}, {"_id": 0, "password": 0}).to_list(1000)
    # Filtrar según permisos
    return filter_servers_by_permissions(servers, current_user)

@api_router.get("/servers/{server_id}")
async def get_server(server_id: str, current_user: Dict = Depends(get_current_user)):
    # Verificar permiso
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0, "password": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    return server

@api_router.put("/servers/{server_id}")
async def update_server(server_id: str, server_data: Dict, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar que el servidor existe
    existing = await db.servers.find_one({"id": server_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Si no se envía contraseña, mantener la existente
    update_data = {k: v for k, v in server_data.items() if v is not None and v != ''}
    if 'password' not in update_data or not update_data.get('password'):
        update_data.pop('password', None)  # No actualizar la contraseña si está vacía
    
    # Actualizar timestamp
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.servers.update_one({"id": server_id}, {"$set": update_data})
    return {"message": "Servidor actualizado"}

@api_router.delete("/servers/{server_id}")
async def delete_server(server_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await db.servers.update_one({"id": server_id}, {"$set": {"active": False}})
    return {"message": "Servidor desactivado"}


@api_router.get("/servers/{server_id}/ping")
async def ping_server(server_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Prueba la conexión a un servidor SQL Server.
    Retorna información de estado y tiempo de respuesta.
    """
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
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
    """
    query_type = request.get("query_type")  # "inventario", "ventas", "movimientos"
    sql = request.get("sql", "").strip()
    
    if query_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido. Usa: {list(REQUIRED_COLUMNS.keys())}")
    
    if not sql:
        raise HTTPException(status_code=400, detail="La consulta SQL es requerida")
    
    # Obtener servidor
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
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
    """
    if query_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido. Usa: {list(REQUIRED_COLUMNS.keys())}")
    
    sql = request.get("sql", "").strip()
    validated = request.get("validated", False)
    
    if not sql:
        raise HTTPException(status_code=400, detail="La consulta SQL es requerida")
    
    # Verificar que el servidor existe
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Crear objeto de configuración de consulta
    query_config = {
        "sql": sql,
        "validated": validated,
        "last_validated": datetime.now(timezone.utc).isoformat() if validated else None,
        "validation_message": "Validada correctamente" if validated else "Pendiente de validación"
    }
    
    # Actualizar el servidor con la nueva consulta
    field_name = f"query_{query_type}"
    update_result = await db.servers.update_one(
        {"id": server_id},
        {"$set": {field_name: query_config}}
    )
    
    # Verificar si todas las consultas están configuradas
    updated_server = await db.servers.find_one({"id": server_id}, {"_id": 0})
    all_configured = all([
        updated_server.get("query_inventario", {}).get("validated", False),
        updated_server.get("query_ventas", {}).get("validated", False),
        updated_server.get("query_movimientos", {}).get("validated", False)
    ])
    
    await db.servers.update_one(
        {"id": server_id},
        {"$set": {"queries_configured": all_configured}}
    )
    
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
    """
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    return {
        "server_id": server_id,
        "server_name": server.get("name"),
        "system_type": server.get("system_type"),
        "queries_configured": server.get("queries_configured", False),
        "queries": {
            "inventario": {
                "configured": server.get("query_inventario") is not None,
                "validated": server.get("query_inventario", {}).get("validated", False),
                "sql": server.get("query_inventario", {}).get("sql", ""),
                "last_validated": server.get("query_inventario", {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["inventario"]["description"],
                "required_columns": REQUIRED_COLUMNS["inventario"]["required"],
                "optional_columns": REQUIRED_COLUMNS["inventario"]["optional"]
            },
            "ventas": {
                "configured": server.get("query_ventas") is not None,
                "validated": server.get("query_ventas", {}).get("validated", False),
                "sql": server.get("query_ventas", {}).get("sql", ""),
                "last_validated": server.get("query_ventas", {}).get("last_validated"),
                "description": REQUIRED_COLUMNS["ventas"]["description"],
                "required_columns": REQUIRED_COLUMNS["ventas"]["required"],
                "optional_columns": REQUIRED_COLUMNS["ventas"]["optional"]
            },
            "movimientos": {
                "configured": server.get("query_movimientos") is not None,
                "validated": server.get("query_movimientos", {}).get("validated", False),
                "sql": server.get("query_movimientos", {}).get("sql", ""),
                "last_validated": server.get("query_movimientos", {}).get("last_validated"),
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
    """
    if query_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Tipo de consulta inválido")
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    field_name = f"query_{query_type}"
    await db.servers.update_one(
        {"id": server_id},
        {"$set": {field_name: None, "queries_configured": False}}
    )
    
    return {"message": f"Consulta de {query_type} eliminada"}

# ============= REPORTS =============

@api_router.get("/servers/{server_id}/tipos-movimiento")
async def get_tipos_movimiento(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de tipos de movimiento desde SQL Server"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            query = """
                SELECT 
                    Tm_Cve_Tipo_Movimiento as codigo,
                    Tm_Descripcion as descripcion,
                    Tm_Tipo as tipo
                FROM Tipo_Movimiento
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Tm_Cve_Tipo_Movimiento
            """
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant usa tabla 'conceptos' para tipos de movimiento
            query = """
                SELECT 
                    idconcepto as codigo,
                    descripcion,
                    CASE WHEN tipo = 1 THEN 'EN' ELSE 'SA' END as tipo
                FROM conceptos
                ORDER BY idconcepto
            """
        else:
            return []
        
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
        logging.error(f"Error obteniendo tipos de movimiento: {str(e)}")
        return []

@api_router.get("/servers/{server_id}/categorias")
async def get_categorias(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de categorías/grupos desde SQL Server"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            query = """
                SELECT 
                    Ct_Cve_Categoria as codigo,
                    Ct_Descripcion as descripcion
                FROM Categoria
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Ct_Cve_Categoria
            """
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant usa 'gruposi' para categorías de insumos
            query = """
                SELECT 
                    idgruposi as codigo,
                    descripcion
                FROM gruposi
                ORDER BY descripcion
            """
        else:
            return []
        
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
        logging.error(f"Error obteniendo categorías: {str(e)}")
        return []

@api_router.get("/servers/{server_id}/departamentos")
async def get_departamentos(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de departamentos/almacenes desde SQL Server"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            query = """
                SELECT 
                    Dp_Cve_Departamento as codigo,
                    Dp_Descripcion as descripcion
                FROM Departamento
                WHERE Es_Cve_Estado <> 'BA'
                ORDER BY Dp_Cve_Departamento
            """
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant usa 'almacen' como departamentos
            query = """
                SELECT 
                    idalmacen as codigo,
                    nombre as descripcion
                FROM almacen
                ORDER BY idalmacen
            """
        else:
            return []
        
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
        logging.error(f"Error obteniendo departamentos: {str(e)}")
        return []

@api_router.get("/servers/{server_id}/sucursales")
async def get_sucursales(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de sucursales desde SQL Server, filtradas por permisos"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
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
                    return filter_sucursales_by_permissions(results, current_user, server_id)
            except Exception as e:
                logging.warning(f"MPRO Sucursales query failed: {e}")
            
            # Si no hay sucursales en la tabla Sucursal, intentar usar Almacenes
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
                    return filter_sucursales_by_permissions(almacenes, current_user, server_id)
            except Exception as e:
                logging.warning(f"MPRO Almacenes query failed: {e}")
            
            # Si no hay nada, devolver sucursal virtual "Principal"
            return [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
            
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant NO tiene tabla Sucursal - devolvemos una sucursal virtual con el nombre del servidor
            # o podemos devolver los almacenes como "sucursales" virtuales
            return [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
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
                    return filter_sucursales_by_permissions(results, current_user, server_id)
            except:
                pass
            # Fallback: sucursal virtual
            return [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
        
    except Exception as e:
        logging.error(f"Error obteniendo sucursales: {str(e)}")
        # En caso de error, devolver sucursal virtual en lugar de array vacío
        return [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]

@api_router.get("/servers/{server_id}/almacenes")
async def get_almacenes(server_id: str, sucursal_id: Optional[str] = None, sucursal: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de almacenes desde SQL Server"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            if sucursal_id:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = '{sucursal_id}' AND Es_Cve_Estado <> 'BA'"
            else:
                query = "SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Es_Cve_Estado <> 'BA'"
            results = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            return results
        
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant: Usar tabla almacen con estructura diferente
            query = """
SELECT 
    idalmacen as id, 
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
ORDER BY nombre
"""
            results = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            return results
        
        else:
            # Query genérica para otros sistemas
            if sucursal_id:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = '{sucursal_id}'"
            else:
                query = "SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen"
            results = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            return results
    except Exception as e:
        logging.error(f"Error obteniendo almacenes: {str(e)}")
        return []

@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
async def get_almacenes_softrestaurant(
    server_id: str, 
    solo_consumo: bool = False,  # Filtrar solo almacenes de consumo (tipo=1)
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene la lista de almacenes de SoftRestaurant (no requiere sucursal)"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] != 'SoftRestaurant':
        raise HTTPException(status_code=400, detail="Este endpoint es solo para SoftRestaurant")
    
    try:
        # Query para obtener almacenes de SoftRestaurant incluyendo el tipo
        # TIPO = 1: Almacén de consumo (tiene ventas) - Se usa para pendientes de descargar
        # TIPO = 2: Almacén de presentaciones (NO tiene ventas)
        where_clause = "WHERE ISNULL(tipo, 1) = 1" if solo_consumo else ""
        query = f"""
SELECT 
    idalmacen as id, 
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
{where_clause}
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
    """Obtiene la lista de inventarios físicos disponibles con sus fechas"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            where_clause = "WHERE F.Es_Cve_Estado not in ('BA')"
            if sucursal_id:
                where_clause += f" AND F.Sc_Cve_Sucursal = '{sucursal_id}'"
            if almacen_id:
                where_clause += f" AND F.Al_Cve_Almacen = '{almacen_id}'"
            
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
        elif server['system_type'] == 'SoftRestaurant':
            # Query para SoftRestaurant - fecha en formato YYYY-MM-DD HH:MM:SS
            where_clause = "WHERE 1=1"
            if almacen_id:
                where_clause += f" AND INV.idalmacen1 = '{almacen_id}'"
            
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
    - SoftRestaurant: Usa tabla inventariopendiente
    - MPRO: Calcula diferencia entre ventas/consumos y existencias
    """
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    system_type = server.get('system_type', '')
    
    try:
        if system_type == 'SoftRestaurant':
            # Query para SoftRestaurant
            where_clause = "WHERE 1=1"
            if almacen_id:
                where_clause += f" AND ip.idalmacen = '{almacen_id}'"
            
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
            
        elif system_type == 'ManagmentPro':
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
        if system_type == 'ManagmentPro':
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
    server_id = report_params.get('server_id')
    query_type = report_params.get('query_type')  # ventas, movimientos, productos, inventarios
    params = report_params.get('params', {})
    
    # Get server
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
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
    """
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
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
            
        elif server['system_type'] == 'SoftRestaurant':
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
    """
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
    
    # Filtros adicionales del frontend
    filtro_categorias_frontend = report_params.get('categorias', [])
    filtro_familias_frontend = report_params.get('familias', [])
    filtro_subfamilias_frontend = report_params.get('subfamilias', [])
    
    # Opción de agrupación de insumos (por defecto NO agrupar)
    agrupar_insumos = report_params.get('agrupar_insumos', False)
    
    logging.info(f"Filtros recibidos del frontend - Categorias: {filtro_categorias_frontend}, Familias: {filtro_familias_frontend}, SubFamilias: {filtro_subfamilias_frontend}")
    logging.info(f"Agrupar insumos: {agrupar_insumos}")
    
    # Get server
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
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
            
            # Construir condición SQL para múltiples almacenes
            almacenes_like_conditions = " OR ".join([f"A.Al_Descripcion LIKE '%{alm}%'" for alm in lista_almacenes])
            
            almacen_query = f"""
SELECT 
    A.Al_Cve_Almacen as codigo,
    A.Al_Descripcion as nombre,
    A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE ({almacenes_like_conditions})
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
"""
            almacen_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], almacen_query
            )
            if not almacen_result:
                raise HTTPException(status_code=404, detail="Almacén no encontrado")
            
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
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
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
            
            return {"data": results, "count": len(results), "errores_captura": errores_list}
            
        elif server['system_type'] == 'SoftRestaurant':
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
            almacen_query = f"""
SELECT TOP 1 
    idalmacen as codigo,
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
WHERE nombre LIKE '%{almacen}%'
"""
            almacen_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], almacen_query
            )
            if not almacen_result:
                raise HTTPException(status_code=404, detail="Almacén no encontrado")
            
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
  AND AL.nombre LIKE '%{almacen}%'
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
            if tipos_movimiento:
                # Filtrar solo por los conceptos configurados
                conceptos_filter = ", ".join([f"'{t}'" for t in tipos_movimiento])
                filtro_conceptos_insumos = f"AND movsinv.idconcepto IN ({conceptos_filter})"
                filtro_conceptos_presentaciones = f"AND movtosalmacen.idconcepto IN ({conceptos_filter})"
                logging.info(f"Usando tipos de movimiento configurados: {tipos_movimiento}")
            else:
                # Si no hay configuración, excluir solo los vacíos
                filtro_conceptos_insumos = "AND movsinv.idconcepto NOT IN ('')"
                filtro_conceptos_presentaciones = "AND movtosalmacen.idconcepto NOT IN ('')"
                logging.info("No hay tipos de movimiento configurados, usando todos excepto vacíos")
            
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
  AND almacen.nombre LIKE '%{almacen}%'
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
  AND almacen.nombre LIKE '%{almacen}%'
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
  AND AL.nombre LIKE '%{almacen}%'
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
  AND AL.nombre LIKE '%{almacen}%'
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
                        # Obtener info del almacén
                        almacen_id_sr = ""
                        for alm in almacenes:
                            if alm.get('nombre') == almacen or alm.get('id'):
                                almacen_id_sr = alm.get('id', '')
                                break
                        
                        cache_key = {
                            "server_id": server_id,
                            "almacen_id": almacen_id_sr or almacen,
                            "sucursal_id": "",
                            "comentario": "",  # SR no usa comentarios
                            "folio": str(folio_fin)
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
            
            return {"data": results, "count": len(results)}
        
        else:
            raise HTTPException(status_code=400, detail="Sistema no soportado para análisis completo")
        
    except Exception as e:
        logging.error(f"Error en análisis de inventario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando análisis: {str(e)}")

@api_router.post("/reports/movement-details")
async def get_movement_details(params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el detalle de los movimientos para un producto específico.
    Devuelve: folio, fecha, cantidad, tipo de movimiento, descripción.
    """
    server_id = params.get('server_id')
    producto_codigo = params.get('producto_codigo')
    sucursal = params.get('sucursal')
    almacen = params.get('almacen')
    fecha_ini = params.get('fecha_ini')
    fecha_fin = params.get('fecha_fin')
    
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            # MPRO: Movimientos desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
            from datetime import datetime, timedelta
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ini_mov = (fecha_ini_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Obtener código del almacén
            almacen_query = f"""
SELECT TOP 1 A.Al_Cve_Almacen as codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE A.Al_Descripcion LIKE '%{almacen}%'
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
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
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
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
            
        elif server['system_type'] == 'SoftRestaurant':
            # Para SoftRestaurant - detectar si es INSUMO o PRESENTACIÓN
            # PRESENTACIONES: el idinsumospresentaciones ya tiene el código completo (ej: B130009)
            # INSUMOS: el código se genera como prefijo + idinsumo (ej: B + 12345 = B12345)
            
            # Formatear fechas para SQL Server: YYYYMMDD HH:MM:SS
            fecha_ini_fmt = fecha_ini.replace('-', '').replace('T', ' ') if fecha_ini else ''
            fecha_fin_fmt = fecha_fin.replace('-', '').replace('T', ' ') if fecha_fin else ''
            
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
    AND A.nombre LIKE '%{almacen}%'
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
    AND A.nombre LIKE '%{almacen}%'
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
    """
    server_id = params.get('server_id')
    producto_codigo = params.get('producto_codigo')
    sucursal = params.get('sucursal')
    fecha_ini = params.get('fecha_ini')
    fecha_fin = params.get('fecha_fin')
    
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
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
        AND S.Sc_Descripcion LIKE '%{sucursal}%'
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
        AND S.Sc_Descripcion LIKE '%{sucursal}%'
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
            
        elif server['system_type'] == 'SoftRestaurant':
            # Para SoftRestaurant - detalle de ventas usando recetasalmacenes
            # El código puede ser INSUMO (con prefijo) o PRESENTACION (código directo)
            almacen = params.get('almacen', '')
            
            # Formatear fechas para SQL Server: YYYYMMDD HH:MM:SS
            fecha_ini_fmt = fecha_ini.replace('-', '').replace('T', ' ') if fecha_ini else ''
            fecha_fin_fmt = fecha_fin.replace('-', '').replace('T', ' ') if fecha_fin else ''
            
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
  AND AL.nombre LIKE '%{almacen}%'
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
        if server['system_type'] == 'MPRO':
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
            folio = corte['folio']
            
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
        return {
            'almacen_nombre': almacen_nombre,
            'cortes': [{'folio': c['folio'], 'fecha': c['fecha'], 'comentario': c.get('comentario', '')} for c in cortes_result],
            'productos': productos_list,
            'cortes_sin_cache': cortes_sin_cache
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
    """
    server = await db.servers.find_one({"id": request.server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
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
    
    if system_type is None or system_type.upper() == "MPRO":
        result["MPRO"] = {
            nombre: {
                "nombre": consulta["nombre"],
                "descripcion": consulta["descripcion"],
                "parametros": consulta["parametros"]
            }
            for nombre, consulta in CONSULTAS_MPRO.items()
        }
    
    if system_type is None or system_type.upper() == "SOFTRESTAURANT":
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
    
    if system_type is None or system_type.upper() == "MPRO":
        result["MPRO"] = ESTRUCTURA_TABLAS_MPRO
    
    if system_type is None or system_type.upper() == "SOFTRESTAURANT":
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
    """
    server_id = params.get('server_id')
    consulta_nombre = params.get('consulta')
    parametros = params.get('parametros', {})
    
    # Obtener servidor
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Obtener consulta del catálogo según el tipo de sistema
    if server['system_type'] == 'MPRO':
        consultas = CONSULTAS_MPRO
    elif server['system_type'] == 'SoftRestaurant':
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
    
    # Obtener servidor
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        logging.info(f"Ejecutando consulta personalizada")
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
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

@api_router.post("/debug/test-queries")
async def debug_test_queries(params: Dict, current_user: Dict = Depends(get_current_user)):
    """Endpoint de depuración simplificado para probar consultas de un producto."""
    server_id = params.get('server_id')
    sucursal = params.get('sucursal')
    almacen = params.get('almacen', '')  # Nombre del almacén para filtrar
    fecha_ini = params.get('fecha_ini')
    fecha_fin = params.get('fecha_fin')
    producto_codigo = params.get('producto_codigo', '0000000546')
    
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    results = {"parametros": params}
    
    try:
        # Obtener código del almacén si se proporcionó nombre
        almacen_codigo = None
        if almacen:
            almacen_query = f"SELECT TOP 1 Al_Cve_Almacen as codigo FROM Almacen WHERE Al_Descripcion LIKE '%{almacen}%'"
            almacen_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], almacen_query
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
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND E.Pr_Cve_Producto = '{producto_codigo}'
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Tm_Cve_Tipo_Movimiento IN ('050','100','106','108','112','202','400','500','506','508','510','512')
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    {filtro_almacen}
"""
        mov_result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_mov_simple
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
    WHERE sucursal.Sc_Descripcion LIKE '%{sucursal}%'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        AND Producto_Kit.Pk_Producto = '{producto_codigo}'
    
    UNION ALL
    
    -- Ventas DIRECTAS: cuando el producto se vende directamente
    SELECT 
        SUM(venta.Vn_Cantidad_Control_1) as cantidad
    FROM venta
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Descripcion LIKE '%{sucursal}%'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        AND venta.Pr_Cve_Producto = '{producto_codigo}'
) AS VentasCombinadas
"""
        ventas_result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_ventas
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
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND E.Pr_Cve_Producto = '{producto_codigo}'
    AND E.Es_Cve_Estado <> 'CA'
    AND E.Tm_Cve_Tipo_Movimiento IN ('050','100','106','108','112','202','400','500','506','508','510','512')
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY E.Mv_Fecha DESC
"""
        detalle = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_detalle
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
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND V.Es_Cve_Estado <> 'CA'
    AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    AND PK.Pk_Producto = '{producto_codigo}'
ORDER BY V.Vn_Fecha DESC
"""
        detalle_kit = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_detalle_kit
        )
        results["detalle_ventas_kit"] = detalle_kit
        
        # Detalle de ventas directas
        query_detalle_directas = f"""
SELECT TOP 10 V.Vn_Folio, V.Vn_Fecha, V.Pr_Cve_Producto, 
    V.Vn_Cantidad_1, V.Vn_Cantidad_Control_1
FROM venta V
INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND V.Es_Cve_Estado <> 'CA'
    AND V.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    AND V.Pr_Cve_Producto = '{producto_codigo}'
ORDER BY V.Vn_Fecha DESC
"""
        detalle_directas = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query_detalle_directas
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
    """
    try:
        # Si no se especifica servidor, obtener el primero configurado del usuario
        query = {"active": True, "queries_configured": True}
        
        if server_id:
            query["id"] = server_id
        
        server = await db.servers.find_one(query)
        
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
        if server['system_type'] == 'SoftRestaurant':
            query_sql = get_dashboard_inventory_query_softrestaurant(departamentos, categorias)
        elif server['system_type'] == 'MPRO':
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
    Obtiene lista de servidores configurados para el selector del dashboard
    """
    servers = await db.servers.find(
        {"active": True, "queries_configured": True},
        {"_id": 0, "id": 1, "name": 1, "system_type": 1, "visible_en_operaciones": 1}
    ).to_list(100)
    
    return servers


@api_router.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: Dict = Depends(get_current_user)):
    """Métricas básicas para el dashboard - mantenido por compatibilidad"""
    total_servers = await db.servers.count_documents({"active": True})
    total_users = await db.users.count_documents({"active": True})
    total_alerts = await db.alerts.count_documents({"active": True})
    servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
    
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

@api_router.get("/compras/inventarios-fisicos/{server_id}")
async def obtener_inventarios_fisicos(server_id: str, sucursal: str = None, sucursal_id: str = None, almacen: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene la lista de inventarios físicos disponibles para seleccionar, filtrado por almacén y sucursal"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] == 'MPRO':
        # Para MPRO, los almacenes tienen el mismo ID en diferentes sucursales
        # Necesitamos filtrar por la combinación Almacen.Sc_Cve_Sucursal + Almacen.Al_Cve_Almacen
        
        # Filtro por almacén
        almacen_filtro = ""
        if almacen and almacen != "TODOS" and almacen:
            almacen_filtro = f"AND A.Al_Descripcion LIKE '%{almacen}%'"
        
        # Filtro por sucursal - CRÍTICO: usar la clave de sucursal del Almacén
        sucursal_filtro = "1=1"
        if sucursal_id:
            # Filtrar almacenes que pertenecen a esta sucursal específica
            sucursal_filtro = f"A.Sc_Cve_Sucursal = '{sucursal_id}'"
        elif sucursal:
            # Fallback: buscar por nombre de sucursal
            sucursal_filtro = f"S.Sc_Descripcion LIKE '%{sucursal}%'"
        
        query = f"""
SELECT DISTINCT 
    F.Fi_Folio as folio,
    F.Fi_Fecha as fecha,
    A.Al_Descripcion as almacen,
    S.Sc_Descripcion as sucursal,
    A.Sc_Cve_Sucursal as sucursal_id,
    ISNULL(F.Fi_Comentario, '') as comentario,
    COUNT(DISTINCT F.Pr_Cve_Producto) as total_productos
FROM Fisico F
INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE {sucursal_filtro}
    {almacen_filtro}
GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, S.Sc_Descripcion, A.Sc_Cve_Sucursal, F.Fi_Comentario
ORDER BY F.Fi_Folio DESC
"""
        logging.info(f"Inventarios MPRO - Sucursal ID: '{sucursal_id}', Nombre: '{sucursal}', Almacén: '{almacen}'")
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        logging.info(f"Inventarios MPRO - Encontrados: {len(result)}")
        return [{"folio": r['folio'], "fecha": str(r['fecha']), "almacen": r['almacen'], 
                 "sucursal": r.get('sucursal', ''), "sucursal_id": r.get('sucursal_id', ''),
                 "comentario": r['comentario'], "productos": r['total_productos']} for r in result]
    
    elif server['system_type'] == 'SoftRestaurant':
        # SoftRestaurant: Usar tabla invfisico
        almacen_filtro = ""
        if almacen and almacen != "TODOS":
            almacen_filtro = f"AND A.nombre LIKE '%{almacen}%'"
        
        query = f"""
SELECT DISTINCT 
    INV.folio as folio,
    INV.fecha as fecha,
    A.nombre as almacen,
    '' as comentario
FROM invfisico INV
LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
WHERE 1=1
    {almacen_filtro}
ORDER BY INV.folio DESC, INV.fecha DESC
"""
        try:
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            return [{"folio": str(r['folio']), "fecha": str(r['fecha']), "almacen": r['almacen'] or 'Sin almacén', 
                     "comentario": '', "productos": 0} for r in result]
        except Exception as e:
            logging.warning(f"Error obteniendo inventarios físicos SoftRestaurant: {e}")
            return []
    
    return []

@api_router.get("/compras/pedidos-vigentes/{server_id}")
async def obtener_pedidos_vigentes(server_id: str, sucursal: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene la lista de REQUISICIONES de compra SIN AUTORIZAR (estado PXA) para comparar"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] == 'MPRO':
        # REQUISICION_COMPRA es la tabla correcta con estado PXA = Por Autorizar
        query = f"""
SELECT 'REQUI' as tipo, RC.Rc_Folio as folio, RC.Rc_Fecha as fecha, 
       RC.Rc_Comentario as comentario, RC.Es_Cve_Estado as estado,
       CM.Cm_Descripcion as comprador,
       COUNT(RCD.Pr_Cve_Producto) as total_productos,
       SUM(ISNULL(RCD.Rc_Importe, 0)) as importe_total
FROM Requisicion_Compra RC
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = RC.Sc_Cve_Sucursal
LEFT JOIN Comprador CM ON CM.Cm_Cve_Comprador = RC.Cm_Cve_Comprador
LEFT JOIN Requisicion_Compra_Detalle RCD ON RCD.Rc_Folio = RC.Rc_Folio
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND RC.Es_Cve_Estado = 'PXA'
    AND RC.Rc_Fecha >= DATEADD(day, -30, GETDATE())
GROUP BY RC.Rc_Folio, RC.Rc_Fecha, RC.Rc_Comentario, RC.Es_Cve_Estado, CM.Cm_Descripcion
ORDER BY RC.Rc_Fecha DESC
"""
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return [{"tipo": r['tipo'], "folio": r['folio'], "fecha": str(r['fecha']), 
                 "comentario": r['comentario'] or '', "estado": r['estado'],
                 "comprador": r['comprador'] or '',
                 "productos": r['total_productos'], "importe": float(r['importe_total'] or 0)} for r in result]
    
    elif server['system_type'] == 'SoftRestaurant':
        # SoftRestaurant: Usar tabla ordenescompra (órdenes sin aplicar = sin autorizar)
        try:
            query = f"""
SELECT 'ORDEN' as tipo, OC.folio as folio, OC.fechacaptura as fecha,
       '' as comentario, 
       CASE WHEN OC.aplicada = 0 THEN 'PXA' ELSE 'AUT' END as estado,
       PR.nombre as proveedor,
       COUNT(OCM.idinsumo) as total_productos,
       ISNULL(OC.total, 0) as importe_total
FROM ordenescompra OC
LEFT JOIN proveedores PR ON PR.idproveedor = OC.idproveedor
LEFT JOIN ordenescompramov OCM ON OCM.idordencompra = OC.idordencompra
WHERE OC.aplicada = 0
    AND OC.cancelado = 0
    AND OC.fechacaptura >= DATEADD(day, -30, GETDATE())
GROUP BY OC.folio, OC.fechacaptura, OC.aplicada, PR.nombre, OC.total
ORDER BY OC.fechacaptura DESC
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            return [{"tipo": r['tipo'], "folio": str(r['folio']), "fecha": str(r['fecha']), 
                     "comentario": r['comentario'] or '', "estado": r['estado'],
                     "comprador": r['proveedor'] or '',
                     "productos": r['total_productos'], "importe": float(r['importe_total'] or 0)} for r in result]
        except Exception as e:
            logging.warning(f"Error obteniendo pedidos SoftRestaurant: {e}")
            return []
    
    return []

@api_router.get("/compras/detalle-pedido-manual/{server_id}")
async def obtener_detalle_pedido_manual(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el detalle de una requisición por folio manual"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] == 'MPRO':
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
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    almacen_list = almacenes.split(',')
    almacen_codigos_str = ",".join([f"'{a}'" for a in almacen_list])
    
    if server['system_type'] == 'MPRO':
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
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] == 'MPRO':
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
    """Obtiene el detalle de un pedido/orden de compra para comparar"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] == 'MPRO':
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
    """
    verify_token(credentials.credentials)
    
    logging.info(f"[COMPRAS] Iniciando cálculo de pedido - server_id: {request.server_id}")
    
    server = await db.servers.find_one({"id": request.server_id, "active": True})
    if not server:
        logging.error(f"[COMPRAS] Servidor no encontrado: {request.server_id}")
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
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
    
    if server['system_type'] == 'MPRO':
        # Obtener códigos de almacenes
        if "TODOS" in almacenes:
            almacen_query = f"""
SELECT A.Al_Cve_Almacen as codigo, A.Al_Descripcion as nombre, A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal}%' AND A.Es_Cve_Estado <> 'BA'
"""
        else:
            almacen_likes = " OR ".join([f"A.Al_Descripcion LIKE '%{a}%'" for a in almacenes])
            almacen_query = f"""
SELECT A.Al_Cve_Almacen as codigo, A.Al_Descripcion as nombre, A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE S.Sc_Descripcion LIKE '%{sucursal}%' AND ({almacen_likes}) AND A.Es_Cve_Estado <> 'BA'
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
    current_user = await get_current_user(credentials)
    
    server = await db.servers.find_one({"id": request.server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    productos = {}
    
    try:
        if server['system_type'] == 'SoftRestaurant':
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
        
        elif server['system_type'] == 'MPRO':
            # Para MPRO
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
    """
    verify_token(credentials.credentials)
    
    logging.info(f"[AUDITORIA] Iniciando auditoría - server: {request.server_id}, sucursal: {request.sucursal}")
    
    server = await db.servers.find_one({"id": request.server_id, "active": True})
    if not server:
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
    
    sucursal = request.sucursal
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
        if server['system_type'] == 'SoftRestaurant':
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
            tipos_salida_consumo = [t for t in tipos_salida_activos if t in ['SPV', 'SCP', 'SCS']]
            
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
        
        elif server['system_type'] == 'MPRO':
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

@api_router.post("/compras/detalle-movimientos")
async def obtener_detalle_movimientos_post(request: DetalleMovimientosRequest, current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el detalle de movimientos de un producto específico en un período.
    Muestra cada movimiento individual que compone el total.
    """
    server = await db.servers.find_one({"id": request.server_id, "active": True}, {"_id": 0})
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
            if server['system_type'] == 'SoftRestaurant':
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
    server = await db.servers.find_one({"id": request.server_id, "active": True}, {"_id": 0})
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
        if server['system_type'] == 'SoftRestaurant':
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
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
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
        
        if server['system_type'] == 'MPRO':
            # Total compras del período FILTRADO POR SUCURSAL
            query_compras = f"""
SELECT ISNULL(SUM(M.Mv_Costo_Importe), 0) as total
FROM Movimiento M
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE TM.Tm_Tipo = 'E'
    AND (TM.Tm_Descripcion LIKE '%COMP%' OR TM.Tm_Cve_Tipo_Movimiento LIKE '%COMP%')
    AND M.Mv_Fecha >= '{fecha_inicio}'
    AND M.Mv_Fecha < '{fecha_fin}'
    AND ISNULL(M.Es_Cve_Estado, '') <> 'CA'
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
"""
            result_compras = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_compras
            )
            total_compras = float(result_compras[0]['total']) if result_compras else 0
            
            # Requisiciones pendientes FILTRADO POR SUCURSAL
            query_req = f"""
SELECT COUNT(*) as total FROM Requisicion_Compra RC
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = RC.Sc_Cve_Sucursal
WHERE RC.Es_Cve_Estado = 'PXA' AND S.Sc_Descripcion LIKE '%{sucursal}%'
"""
            result_req = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_req
            )
            req_pendientes = result_req[0]['total'] if result_req else 0
            
            # Proveedores activos (con compras en últimos 90 días) FILTRADO POR SUCURSAL
            query_prov = f"""
SELECT COUNT(DISTINCT M.Pv_Cve_Proveedor) as total
FROM Movimiento M
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE M.Mv_Fecha >= DATEADD(day, -90, GETDATE())
    AND M.Pv_Cve_Proveedor IS NOT NULL
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
"""
            result_prov = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_prov
            )
            prov_activos = result_prov[0]['total'] if result_prov else 0
            
            # Top 5 proveedores FILTRADO POR SUCURSAL
            query_top = f"""
SELECT TOP 5 
    P.Pv_Nombre as nombre,
    SUM(M.Mv_Costo_Importe) as total
FROM Movimiento M
INNER JOIN Proveedor P ON P.Pv_Cve_Proveedor = M.Pv_Cve_Proveedor
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE TM.Tm_Tipo = 'E'
    AND M.Mv_Fecha >= '{fecha_inicio}'
    AND M.Mv_Fecha < '{fecha_fin}'
    AND ISNULL(M.Es_Cve_Estado, '') <> 'CA'
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
GROUP BY P.Pv_Nombre
ORDER BY total DESC
"""
            result_top = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_top
            )
            top_proveedores = [{"nombre": r['nombre'], "total": float(r['total'])} for r in result_top]
            
            return {
                "kpis": {
                    "total_compras_mes": total_compras,
                    "requisiciones_pendientes": req_pendientes,
                    "proveedores_activos": prov_activos,
                    "alertas_activas": 0  # TODO: calcular alertas reales
                },
                "alertas": [],
                "top_proveedores": top_proveedores
            }
        
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant - Usando tabla compras del catálogo
            # Usar los parámetros de meses y años del frontend
            
            # Total compras del período seleccionado (usando tabla compras - columna correcta: fechaaplicacion)
            query_compras = f"""
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fechaaplicacion >= '{fecha_inicio}'
  AND c.fechaaplicacion < '{fecha_fin}'
  AND ISNULL(c.cancelado, 0) = 0
"""
            result_compras = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_compras
            )
            total_compras = float(result_compras[0]['Compra_Total'] or 0) if result_compras else 0
            facturas = int(result_compras[0]['Facturas'] or 0) if result_compras else 0
            
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
            
            # Top proveedores usando tabla compras - período seleccionado
            query_top = f"""
SELECT TOP 5 
    ISNULL(p.nombre, 'Sin proveedor') as nombre,
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as total
FROM compras c
LEFT JOIN proveedores p ON p.idproveedor = c.idproveedor
WHERE c.fechaaplicacion >= '{fecha_inicio}'
  AND c.fechaaplicacion < '{fecha_fin}'
  AND ISNULL(c.cancelado, 0) = 0
GROUP BY p.nombre
ORDER BY SUM(c.total) DESC
"""
            result_top = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_top
            )
            top_proveedores = [{"nombre": r['nombre'], "total": float(r['total'] or 0)} for r in (result_top or [])]
            
            return {
                "kpis": {
                    "total_compras_mes": total_compras,
                    "facturas_mes": facturas,
                    "requisiciones_pendientes": 0,  # SoftRestaurant no tiene este concepto
                    "proveedores_activos": prov_activos,
                    "alertas_activas": 0
                },
                "alertas": [],
                "top_proveedores": top_proveedores
            }
        
        return {"kpis": {}, "alertas": [], "top_proveedores": []}
    except Exception as e:
        logging.error(f"Error en dashboard compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/compras/analisis")
async def obtener_analisis_compras(request: AnalisisComprasRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene análisis de compras por proveedor y mes con alertas de desviación"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": request.server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Obtener años (priorizar lista de años sobre año único)
    if request.anios and len(request.anios) > 0:
        anios = [int(a) for a in request.anios]
    elif request.anio:
        anios = [request.anio]
    else:
        anios = [datetime.now().year]
    
    anio_principal = max(anios)  # Usar el año más reciente para la consulta principal
    
    logging.info(f"Análisis compras: {server['name']} - Años: {anios}, Meses: {request.meses}")
    
    try:
        if server['system_type'] == 'MPRO':
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
    AND S.Sc_Descripcion LIKE '%{request.sucursal}%'
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
        
        elif server['system_type'] == 'SoftRestaurant':
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
        
        return {"proveedores": [], "alertas": []}
    except Exception as e:
        logging.error(f"Error en análisis compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/compras/facturas-proveedor/{server_id}")
async def obtener_facturas_proveedor(server_id: str, proveedor_codigo: str, anio: int, meses: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene las facturas/entradas de un proveedor específico"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
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
        
        return []
    except Exception as e:
        logging.error(f"Error obteniendo facturas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/compras/detalle-factura/{server_id}/{folio}")
async def obtener_detalle_factura(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el detalle de productos de una factura/entrada"""
    verify_token(credentials.credentials)
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
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
        
        return []
    except Exception as e:
        logging.error(f"Error obteniendo detalle factura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MÓDULO COMERCIAL - Endpoints de Ventas
# ============================================================================

@api_router.get("/comercial/dashboard/{server_id}")
async def comercial_dashboard(
    server_id: str, 
    sucursal: str = Query(default=""), 
    periodo: str = Query(default="dia"),  # dia, semana, mes
    meses: str = Query(default=""),  # "01,02,03" - Lista de meses separados por coma
    anio: str = Query(default=""),  # "2025" - Año específico (compatibilidad)
    anios: str = Query(default=""),  # "2025,2024" - Múltiples años separados por coma
    tipo_comparacion: str = Query(default="dias_equiv"),  # dias_equiv o mes_completo
    current_user: Dict = Depends(get_current_user)
):
    """
    Dashboard principal de ventas con KPIs y comparativos.
    Soporta SoftRestaurant y MPRO.
    Ahora soporta multiselección de meses y múltiples años.
    tipo_comparacion: 'dias_equiv' compara días 1-N vs días 1-N del período anterior
                      'mes_completo' compara vs el mes completo anterior
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Verificar permisos
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        # Calcular fechas según período
        from datetime import datetime, timedelta
        hoy = datetime.now()
        
        # Obtener lista de años (priorizar 'anios' sobre 'anio')
        if anios:
            lista_anios = [int(a.strip()) for a in anios.split(',') if a.strip()]
        elif anio:
            lista_anios = [int(anio)]
        else:
            lista_anios = [hoy.year]
        
        # Si se proporcionan meses y años específicos, usar esos
        if meses and lista_anios:
            lista_meses = [m.strip() for m in meses.split(',') if m.strip()]
            
            # Usar el año más reciente para la consulta principal
            year = max(lista_anios)
            
            # Para múltiples meses, calcular rango de fechas
            mes_min = min([int(m) for m in lista_meses])
            mes_max = max([int(m) for m in lista_meses])
            
            # Verificar si estamos consultando el mes actual
            es_mes_actual = (year == hoy.year and mes_max == hoy.month and len(lista_meses) == 1)
            
            fecha_ini = f"{year}-{str(mes_min).zfill(2)}-01"
            
            # Para días equivalentes, necesitamos saber el último día con ventas reales
            # Esto se determinará después de consultar la base de datos
            # Por ahora, establecemos fecha_fin provisional
            if es_mes_actual:
                fecha_fin = hoy.strftime('%Y-%m-%d')
                dia_provisional = hoy.day
            else:
                if mes_max == 12:
                    ultimo_dia = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia = datetime(year, mes_max + 1, 1) - timedelta(days=1)
                fecha_fin = ultimo_dia.strftime('%Y-%m-%d')
                dia_provisional = ultimo_dia.day
            
            # NOTA: dia_con_datos se calculará después de consultar la BD
            # y se usará para ajustar los períodos de comparación en modo "dias_equiv"
            
            # Por ahora, establecemos los valores por defecto para mes_completo
            if tipo_comparacion == "mes_completo" or not es_mes_actual:
                # Mes completo: comparar vs mes(es) completo(s) anteriores
                if mes_min == 1:
                    fecha_ini_ant = f"{year - 1}-12-01"
                    fecha_fin_ant = f"{year - 1}-12-31"
                else:
                    mes_ant = mes_min - 1
                    fecha_ini_ant = f"{year}-{str(mes_ant).zfill(2)}-01"
                    if mes_ant == 12:
                        ultimo_dia_ant = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        ultimo_dia_ant = datetime(year, mes_ant + 1, 1) - timedelta(days=1)
                    fecha_fin_ant = ultimo_dia_ant.strftime('%Y-%m-%d')
                
                # Año anterior completo
                fecha_ini_ano_ant = f"{year - 1}-{str(mes_min).zfill(2)}-01"
                if mes_max == 12:
                    ultimo_dia_ano_ant = datetime(year, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia_ano_ant = datetime(year - 1, mes_max + 1, 1) - timedelta(days=1)
                fecha_fin_ano_ant = ultimo_dia_ano_ant.strftime('%Y-%m-%d')
            else:
                # dias_equiv: se calcularán después de obtener el último día con ventas
                # Valores temporales que se actualizarán
                fecha_ini_ant = "PENDIENTE"
                fecha_fin_ant = "PENDIENTE"
                fecha_ini_ano_ant = "PENDIENTE"
                fecha_fin_ano_ant = "PENDIENTE"
            
            logging.info(f"Comercial Dashboard (multiselección): {server['name']} - Meses: {lista_meses} Año: {year} ({fecha_ini} a {fecha_fin}) - Tipo: {tipo_comparacion}")
        elif periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            # Para comparativo: día anterior
            fecha_ini_ant = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
            fecha_fin_ant = fecha_ini_ant
            # Año anterior - mismo día
            try:
                fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
                fecha_fin_ano_ant = fecha_ini_ano_ant
            except ValueError:
                fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
                fecha_fin_ano_ant = fecha_ini_ano_ant
        elif periodo == "semana":
            # Semana actual (lunes a hoy)
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            # Semana anterior
            fecha_ini_ant = (inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
            fecha_fin_ant = (inicio_semana - timedelta(days=1)).strftime('%Y-%m-%d')
            # Año anterior - misma semana aproximada
            try:
                fecha_ini_ano_ant = inicio_semana.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
                fecha_fin_ano_ant = hoy.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
            except ValueError:
                fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-07"
        else:  # mes
            # Mes actual
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            dia_actual = hoy.day  # Día del mes actual (1-31)
            
            # Mes anterior - depende del tipo de comparación
            primer_dia_mes = hoy.replace(day=1)
            ultimo_dia_mes_ant = primer_dia_mes - timedelta(days=1)
            
            if tipo_comparacion == "dias_equiv":
                # Días equivalentes: comparar días 1-N vs días 1-N del mes anterior
                fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                # Usar el mismo número de días (o el máximo del mes anterior si es menor)
                dia_max_mes_ant = ultimo_dia_mes_ant.day
                dia_comparar = min(dia_actual - 1, dia_max_mes_ant)  # -1 porque comparamos hasta ayer equivalente
                if dia_comparar < 1:
                    dia_comparar = 1
                fecha_fin_ant = ultimo_dia_mes_ant.replace(day=dia_comparar).strftime('%Y-%m-%d')
                
                # Año anterior - días equivalentes
                try:
                    fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1, day=1).strftime('%Y-%m-%d')
                    # Para año anterior, usar el mismo día o el máximo del mes
                    ano_ant_ultimo_dia = (datetime(hoy.year - 1, hoy.month + 1, 1) - timedelta(days=1)).day if hoy.month < 12 else 31
                    dia_ano_ant = min(dia_actual - 1, ano_ant_ultimo_dia)
                    if dia_ano_ant < 1:
                        dia_ano_ant = 1
                    fecha_fin_ano_ant = hoy.replace(year=hoy.year - 1, day=dia_ano_ant).strftime('%Y-%m-%d')
                except ValueError:
                    # En caso de día inválido (ej. 31 de feb)
                    fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
            else:
                # Mes completo: comparar vs todo el mes anterior
                fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                fecha_fin_ant = ultimo_dia_mes_ant.strftime('%Y-%m-%d')
                
                # Año anterior - mes completo
                try:
                    fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1, day=1).strftime('%Y-%m-%d')
                    if hoy.month == 12:
                        ultimo_dia_ano_ant = datetime(hoy.year, 1, 1) - timedelta(days=1)
                    else:
                        ultimo_dia_ano_ant = datetime(hoy.year - 1, hoy.month + 1, 1) - timedelta(days=1)
                    fecha_fin_ano_ant = ultimo_dia_ano_ant.strftime('%Y-%m-%d')
                except ValueError:
                    fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
        
        # Logging con tipo de comparación
        logging.info(f"Comercial Dashboard: {server['name']} - Período: {periodo} ({fecha_ini} a {fecha_fin}) - Tipo: {tipo_comparacion}")
        logging.info(f"Comparación mes ant: {fecha_ini_ant} a {fecha_fin_ant}")
        logging.info(f"Comparación año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant}")
        
        if server['system_type'] == 'SoftRestaurant':
            # Formato de fecha compatible con SQL Server en español (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Para días equivalentes: consultar el último día con ventas reales
            if tipo_comparacion == "dias_equiv" and fecha_ini_ant == "PENDIENTE":
                # Query para obtener el último día con ventas en el período actual
                query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, turnos.apertura)) as ultimo_dia_venta
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
"""
                result_ultimo = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia
                )
                
                if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
                    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
                    # Puede venir como string o como date
                    if isinstance(ultimo_dia_venta, str):
                        dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
                    else:
                        dia_con_datos = ultimo_dia_venta.day
                    
                    logging.info(f"SoftRestaurant - Último día con ventas: {ultimo_dia_venta} (día {dia_con_datos})")
                    
                    # Actualizar fecha_fin al último día con ventas
                    f_fin = f"{f_ini[:6]}{str(dia_con_datos).zfill(2)}"
                    
                    # Calcular períodos de comparación basados en días con datos reales
                    # Mes anterior
                    mes_actual = int(f_ini[4:6])
                    anio_actual = int(f_ini[:4])
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    # Calcular máximo día del mes anterior
                    if mes_ant == 12:
                        max_dia_mes_ant = 31
                    elif mes_ant in [4, 6, 9, 11]:
                        max_dia_mes_ant = 30
                    elif mes_ant == 2:
                        max_dia_mes_ant = 29 if (anio_ant % 4 == 0 and (anio_ant % 100 != 0 or anio_ant % 400 == 0)) else 28
                    else:
                        max_dia_mes_ant = 31
                    
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    # Año anterior - mismo mes
                    anio_pasado = anio_actual - 1
                    if mes_actual == 2:
                        max_dia_ano_ant = 29 if (anio_pasado % 4 == 0 and (anio_pasado % 100 != 0 or anio_pasado % 400 == 0)) else 28
                    elif mes_actual in [4, 6, 9, 11]:
                        max_dia_ano_ant = 30
                    else:
                        max_dia_ano_ant = 31
                    
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    logging.info(f"Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant}")
                else:
                    # Si no hay datos, usar valores por defecto
                    dia_con_datos = 1
                    fecha_ini_ant = fecha_ini.replace(f"-{str(mes_max).zfill(2)}-", f"-{str(mes_max-1).zfill(2)}-") if mes_max > 1 else fecha_ini.replace(f"{year}-01-", f"{year-1}-12-")
                    fecha_fin_ant = fecha_ini_ant
                    fecha_ini_ano_ant = fecha_ini.replace(str(year), str(year-1))
                    fecha_fin_ano_ant = fecha_ini_ano_ant
            
            f_ini_ant = fecha_ini_ant.replace('-', '')
            f_fin_ant = fecha_fin_ant.replace('-', '')
            f_ini_ano_ant = fecha_ini_ano_ant.replace('-', '')
            f_fin_ano_ant = fecha_fin_ano_ant.replace('-', '')
            
            logging.info(f"SoftRestaurant Query - Período: {f_ini} a {f_fin}, Mes ant: {f_ini_ant} a {f_fin_ant}, Año ant: {f_ini_ano_ant} a {f_fin_ano_ant}")
            
            # Query principal para KPIs de ventas SoftRestaurant
            # MISMA LÓGICA QUE ANÁLISIS DE INVENTARIOS: usa turnos.apertura
            query_kpis = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques_total,
    SUM(cheques.total) as ventas_periodo,
    AVG(cheques.total) as ticket_promedio,
    ISNULL(SUM(cheques.nopersonas), 0) as pax_total,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as pax_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_kpis
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_total = int(row['cheques_total'] or 0)
                ventas_periodo = float(row['ventas_periodo'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_total = int(row['pax_total'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
            else:
                cheques_total = 0
                ventas_periodo = 0
                ticket_promedio = 0
                pax_total = 0
                pax_promedio = 0
            
            # Estimamos mesas = cheques (cada cheque = una mesa atendida)
            mesas_atendidas = cheques_total
            
            # Calcular rotación de mesas (vueltas promedio por mesa)
            rotacion_mesas = round(cheques_total / mesas_atendidas, 2) if mesas_atendidas > 0 else 0
            
            # Query para período anterior (comparativo) - MISMA LÓGICA
            query_anterior = f"""
SELECT 
    SUM(cheques.total) as ventas_periodo
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_ant} 00:00:00'
  AND turnos.apertura <= '{f_fin_ant} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_ant = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_anterior
            )
            
            ventas_anterior = float(result_ant[0]['ventas_periodo'] or 0) if result_ant and result_ant[0]['ventas_periodo'] else 0
            
            # Calcular variación porcentual
            vs_periodo_anterior = round(((ventas_periodo - ventas_anterior) / ventas_anterior * 100), 1) if ventas_anterior > 0 else 0
            
            # Query para PAX del período anterior
            query_pax_ant = f"""
SELECT ISNULL(SUM(cheques.nopersonas), 0) as pax_total, SUM(cheques.total) as ventas
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_ant} 00:00:00'
  AND turnos.apertura <= '{f_fin_ant} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_pax_ant = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_pax_ant
            )
            
            pax_anterior = int(result_pax_ant[0]['pax_total'] or 0) if result_pax_ant else 0
            ventas_pax_ant = float(result_pax_ant[0]['ventas'] or 0) if result_pax_ant else 0
            pax_promedio_anterior = ventas_pax_ant / pax_anterior if pax_anterior > 0 else 0
            pax_promedio_actual = ventas_periodo / pax_total if pax_total > 0 else 0
            vs_pax_mes_anterior = round(((pax_promedio_actual - pax_promedio_anterior) / pax_promedio_anterior * 100), 1) if pax_promedio_anterior > 0 else 0
            
            # Query para año anterior
            query_ano_ant = f"""
SELECT 
    SUM(cheques.total) as ventas_periodo,
    ISNULL(SUM(cheques.nopersonas), 0) as pax_total
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_ano_ant} 00:00:00'
  AND turnos.apertura <= '{f_fin_ano_ant} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_ano_ant = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ano_ant
            )
            
            ventas_ano_anterior = float(result_ano_ant[0]['ventas_periodo'] or 0) if result_ano_ant and result_ano_ant[0]['ventas_periodo'] else 0
            pax_ano_anterior = int(result_ano_ant[0]['pax_total'] or 0) if result_ano_ant else 0
            
            # Calcular variación vs año anterior
            vs_ano_anterior = round(((ventas_periodo - ventas_ano_anterior) / ventas_ano_anterior * 100), 1) if ventas_ano_anterior > 0 else 0
            pax_vs_ano_anterior = round(((pax_total - pax_ano_anterior) / pax_ano_anterior * 100), 1) if pax_ano_anterior > 0 else 0
            
            # KPIs
            kpis = {
                "ventas_periodo": ventas_periodo,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheques_total": cheques_total,
                "pax_total": pax_total,
                "pax_promedio": round(pax_promedio, 1),
                "consumo_persona": round(ventas_periodo / pax_total, 2) if pax_total > 0 else 0,
                "mesas_atendidas": mesas_atendidas,
                "rotacion_mesas": rotacion_mesas,
                "venta_por_hora": round(ventas_periodo / 12, 2) if ventas_periodo > 0 else 0  # Estimado 12 horas operación
            }
            
            comparativo = {
                "vs_periodo_anterior": vs_periodo_anterior,
                "vs_ano_anterior": vs_ano_anterior,
                "vs_presupuesto": 0,  # TODO: calcular vs meta/presupuesto
                "pax_vs_mes_anterior": vs_pax_mes_anterior,
                "pax_vs_ano_anterior": pax_vs_ano_anterior,
                "tipo_comparacion": tipo_comparacion,
                "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}"
            }
            
            return {
                "kpis": kpis,
                "comparativo": comparativo,
                "alertas": []
            }
        
        elif server['system_type'] == 'MPRO':
            # Para días equivalentes: consultar el último día con ventas reales
            if tipo_comparacion == "dias_equiv" and fecha_ini_ant == "PENDIENTE":
                # Query para MPRO - usar Venta_Encabezado para obtener último día
                sucursal_filter_check = f" AND VE.Sc_Cve_Sucursal IN (SELECT Sc_Cve_Sucursal FROM Sucursal WHERE Sc_Descripcion LIKE '%{sucursal}%')" if sucursal else ""
                
                query_ultimo_dia_mpro = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter_check}
"""
                result_ultimo = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia_mpro
                )
                
                if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
                    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_venta, str):
                        dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
                    else:
                        dia_con_datos = ultimo_dia_venta.day
                    
                    logging.info(f"MPRO - Último día con ventas: {ultimo_dia_venta} (día {dia_con_datos})")
                    
                    # Actualizar fecha_fin al último día con ventas
                    mes_actual = int(fecha_ini[5:7])
                    anio_actual = int(fecha_ini[:4])
                    fecha_fin = f"{anio_actual}-{str(mes_actual).zfill(2)}-{str(dia_con_datos).zfill(2)}"
                    
                    # Calcular períodos de comparación basados en días con datos reales
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    # Calcular máximo día del mes anterior
                    if mes_ant == 12:
                        max_dia_mes_ant = 31
                    elif mes_ant in [4, 6, 9, 11]:
                        max_dia_mes_ant = 30
                    elif mes_ant == 2:
                        max_dia_mes_ant = 29 if (anio_ant % 4 == 0 and (anio_ant % 100 != 0 or anio_ant % 400 == 0)) else 28
                    else:
                        max_dia_mes_ant = 31
                    
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    # Año anterior - mismo mes
                    anio_pasado = anio_actual - 1
                    if mes_actual == 2:
                        max_dia_ano_ant = 29 if (anio_pasado % 4 == 0 and (anio_pasado % 100 != 0 or anio_pasado % 400 == 0)) else 28
                    elif mes_actual in [4, 6, 9, 11]:
                        max_dia_ano_ant = 30
                    else:
                        max_dia_ano_ant = 31
                    
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    logging.info(f"MPRO Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant}")
            
            # Query para MPRO - usar Venta_Encabezado con Comanda para PAX
            sucursal_join = ""
            sucursal_filter = ""
            sucursal_filter_simple = ""
            # No filtrar por sucursal si es "default", "all" o coincide con el nombre del servidor
            nombre_servidor = server.get('name', '').lower()
            sucursal_lower = (sucursal or '').lower()
            skip_sucursal_filter = (
                not sucursal or 
                sucursal == 'all' or 
                sucursal_lower == 'default' or 
                sucursal_lower == nombre_servidor
            )
            
            if not skip_sucursal_filter:
                # Si es un ID de sucursal (formato numérico como "0021"), usar directamente
                # Si es un nombre, usar LIKE
                if sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0'):
                    sucursal_join = ""
                    sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
                    sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # PASO CRÍTICO: Detectar último día con ventas PARA ESTA SUCURSAL ESPECÍFICA
            import calendar
            query_ultimo_dia_suc = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
            try:
                result_ultimo_suc = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia_suc
                )
                if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
                    ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_suc, str):
                        dia_con_datos = int(ultimo_dia_suc.split('-')[2]) if '-' in ultimo_dia_suc else int(ultimo_dia_suc[-2:])
                    else:
                        dia_con_datos = ultimo_dia_suc.day
                    
                    print(f"*** MPRO Dashboard {sucursal} - Ultimo dia con ventas: dia {dia_con_datos} ***")
                    
                    # Actualizar fecha_fin al último día con ventas de esta sucursal
                    mes_actual = int(fecha_ini[5:7])
                    anio_actual = int(fecha_ini[:4])
                    fecha_fin = f"{anio_actual}-{str(mes_actual).zfill(2)}-{str(dia_con_datos).zfill(2)}"
                    
                    # Recalcular fechas de comparación
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    anio_pasado = anio_actual - 1
                    max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_actual)[1]
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    print(f"*** Fechas ajustadas: Actual hasta {fecha_fin}, MesAnt {fecha_ini_ant} a {fecha_fin_ant}, AnoAnt {fecha_ini_ano_ant} a {fecha_fin_ano_ant} ***")
            except Exception as e:
                print(f"Error detectando ultimo dia para sucursal {sucursal}: {e}")
            
            # Query con PAX de tabla Comanda - usar formato YYYYMMDD para MPRO
            fi_mpro = fecha_ini.replace('-', '')
            ff_mpro = fecha_fin.replace('-', '')
            fia_mpro = fecha_ini_ant.replace('-', '')
            ffa_mpro = fecha_fin_ant.replace('-', '')
            fiaa_mpro = fecha_ini_ano_ant.replace('-', '')
            ffaa_mpro = fecha_fin_ano_ant.replace('-', '')
            
            query_kpis = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_periodo,
    ISNULL(SUM(C.Co_Personas), 0) as pax_total
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fi_mpro}'
  AND VE.Vn_Fecha <= '{ff_mpro} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
            print(f"*** MPRO Query sucursal_filter={sucursal_filter}, fi={fi_mpro}, ff={ff_mpro} ***")
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_kpis
            )
            
            if result:
                cheques = int(result[0].get('cheques_total') or 0)
                ventas = float(result[0].get('ventas_periodo') or 0)
                pax = int(result[0].get('pax_total') or 0)
                ticket_promedio = ventas / cheques if cheques > 0 else 0
                consumo_persona = ventas / pax if pax > 0 else 0
                pax_promedio = pax / cheques if cheques > 0 else 0
                
                # Query para período anterior MPRO
                query_pax_ant_mpro = f"""
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fia_mpro}'
  AND VE.Vn_Fecha <= '{ffa_mpro} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
                result_pax_ant = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_pax_ant_mpro
                )
                
                pax_ant = int(result_pax_ant[0]['pax_total'] or 0) if result_pax_ant else 0
                ventas_ant = float(result_pax_ant[0]['ventas'] or 0) if result_pax_ant else 0
                pax_promedio_anterior = ventas_ant / pax_ant if pax_ant > 0 else 0
                pax_promedio_actual = ventas / pax if pax > 0 else 0
                vs_pax_mes_anterior = round(((pax_promedio_actual - pax_promedio_anterior) / pax_promedio_anterior * 100), 1) if pax_promedio_anterior > 0 else 0
                vs_periodo_anterior = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
                
                # Query para año anterior MPRO
                query_ano_ant_mpro = f"""
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fiaa_mpro}'
  AND VE.Vn_Fecha <= '{ffaa_mpro} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
                result_ano_ant = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ano_ant_mpro
                )
                
                pax_ano_ant = int(result_ano_ant[0]['pax_total'] or 0) if result_ano_ant else 0
                ventas_ano_ant = float(result_ano_ant[0]['ventas'] or 0) if result_ano_ant else 0
                vs_ano_anterior = round(((ventas - ventas_ano_ant) / ventas_ano_ant * 100), 1) if ventas_ano_ant > 0 else 0
                pax_vs_ano_anterior = round(((pax - pax_ano_ant) / pax_ano_ant * 100), 1) if pax_ano_ant > 0 else 0
                
                kpis = {
                    "ventas_periodo": round(ventas, 2),
                    "ticket_promedio": round(ticket_promedio, 2),
                    "cheques_total": cheques,
                    "pax_total": pax,
                    "pax_promedio": round(pax_promedio, 2),
                    "consumo_persona": round(consumo_persona, 2),
                    "rotacion_mesas": 0,
                    "mesas_atendidas": 0
                }
                
                # Comparativo para MPRO con PAX y año anterior
                comparativo = {
                    "vs_periodo_anterior": vs_periodo_anterior,
                    "vs_ano_anterior": vs_ano_anterior,
                    "vs_presupuesto": 0,
                    "pax_vs_mes_anterior": vs_pax_mes_anterior,
                    "pax_vs_ano_anterior": pax_vs_ano_anterior,
                    "tipo_comparacion": tipo_comparacion,
                    "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                    "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}"
                }
                
                return {
                    "kpis": kpis,
                    "comparativo": comparativo,
                    "alertas": []
                }
        
        return {"kpis": None, "comparativo": None, "alertas": []}
        
    except Exception as e:
        logging.error(f"Error en comercial dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comercial/ticket-perfecto/{server_id}")
async def comercial_ticket_perfecto(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ticket perfecto y rentabilidad por producto.
    Solo SoftRestaurant tiene los datos necesarios.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        from datetime import datetime, timedelta
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # Análisis de categorías en los tickets (entrada, plato fuerte, postre, etc.)
            # Basado en clasificacionventa de productos
            query_categorias = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as tickets_totales,
    COUNT(DISTINCT CASE WHEN p.clasificacionventa = 1 THEN cheques.folio END) as con_alimentos,
    COUNT(DISTINCT CASE WHEN p.clasificacionventa = 2 THEN cheques.folio END) as con_bebidas
FROM cheques
INNER JOIN cheqdet cd ON cd.foliodet = cheques.folio
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_categorias
            )
            
            tickets_totales = int(result[0]['tickets_totales'] or 0) if result else 0
            con_alimentos = int(result[0]['con_alimentos'] or 0) if result else 0
            con_bebidas = int(result[0]['con_bebidas'] or 0) if result else 0
            
            # Tickets "completos" = tienen alimentos Y bebidas
            tickets_completos = min(con_alimentos, con_bebidas)  # Aproximación
            
            ticket_data = {
                "tickets_totales": tickets_totales,
                "tickets_completos": tickets_completos,
                "pct_completos": round((tickets_completos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "con_entrada": con_alimentos,
                "pct_entrada": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "con_plato_fuerte": con_alimentos,
                "pct_plato_fuerte": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "con_postre": 0,  # Necesita categoría específica
                "pct_postre": 0,
                "con_digestivo": con_bebidas,
                "pct_digestivo": round((con_bebidas / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "oportunidad_perdida": 0
            }
            
            # Top productos por rentabilidad
            query_rentabilidad = f"""
SELECT TOP 20
    p.idproducto as codigo,
    p.descripcion as producto,
    SUM(cd.cantidad * cd.precio) as ventas,
    SUM(cd.cantidad * ISNULL(p.costo, 0)) as costo
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY p.idproducto, p.descripcion
HAVING SUM(cd.cantidad * cd.precio) > 0
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
            result_rent = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rentabilidad
            )
            
            rentabilidad = []
            for r in result_rent:
                ventas = float(r['ventas'] or 0)
                costo = float(r['costo'] or 0)
                margen = round(((ventas - costo) / ventas * 100), 0) if ventas > 0 else 0
                categoria = 'A' if margen >= 60 else ('B' if margen >= 40 else 'C')
                rentabilidad.append({
                    "codigo": str(r['codigo']),
                    "producto": r['producto'],
                    "ventas": ventas,
                    "costo": costo,
                    "margen": margen,
                    "categoria": categoria
                })
            
            return {
                "ticket": ticket_data,
                "rentabilidad": rentabilidad
            }
        
        # Para MPRO devolvemos estructura vacía
        return {
            "ticket": {"tickets_totales": 0, "tickets_completos": 0, "pct_completos": 0},
            "rentabilidad": []
        }
        
    except Exception as e:
        logging.error(f"Error en ticket perfecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comercial/metas/{server_id}")
async def comercial_metas(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Metas de ventas por producto y vendedor.
    Nota: Las metas se configuran externamente, aquí mostramos ventas reales.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        from datetime import datetime
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # Ventas por producto (top 10)
            query_productos = f"""
SELECT TOP 10
    p.descripcion as producto,
    SUM(cd.cantidad * cd.precio) as real_ventas
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY p.descripcion
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
            result_prod = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_productos
            )
            
            metas_producto = []
            for r in result_prod:
                real_ventas = float(r['real_ventas'] or 0)
                # Estimamos meta como 110% del real (sin tabla de metas real)
                meta_estimada = real_ventas * 1.1
                cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                metas_producto.append({
                    "producto": r['producto'],
                    "meta": meta_estimada,
                    "real": real_ventas,
                    "cumplimiento": cumplimiento
                })
            
            # Ventas por mesero/vendedor
            query_vendedor = f"""
SELECT TOP 10
    ISNULL(m.nombre, 'Sin asignar') as vendedor,
    SUM(cheques.total) as real_ventas
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY m.nombre
ORDER BY SUM(cheques.total) DESC
"""
            result_vend = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_vendedor
            )
            
            metas_vendedor = []
            for r in result_vend:
                real_ventas = float(r['real_ventas'] or 0)
                meta_estimada = real_ventas * 1.1
                cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                metas_vendedor.append({
                    "vendedor": r['vendedor'],
                    "meta": meta_estimada,
                    "real": real_ventas,
                    "cumplimiento": cumplimiento
                })
            
            return {
                "por_producto": metas_producto,
                "por_vendedor": metas_vendedor
            }
        
        return {"por_producto": [], "por_vendedor": []}
        
    except Exception as e:
        logging.error(f"Error en metas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comercial/ventas-tiempo/{server_id}")
async def comercial_ventas_tiempo(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Ventas por hora y día de la semana.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        from datetime import datetime, timedelta
        hoy = datetime.now()
        # Última semana
        fecha_ini = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # Ventas por hora
            query_hora = f"""
SELECT 
    DATEPART(HOUR, turnos.apertura) as hora,
    SUM(cheques.total) as ventas,
    SUM(cheques.nopersonas) as pax
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY DATEPART(HOUR, turnos.apertura)
ORDER BY SUM(cheques.total) DESC
"""
            result_hora = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_hora
            )
            
            ventas_por_hora = []
            for r in result_hora[:6]:  # Top 6 horas
                hora_int = int(r['hora'] or 0)
                ventas_por_hora.append({
                    "hora": f"{hora_int:02d}:00",
                    "ventas": float(r['ventas'] or 0),
                    "pax": int(r['pax'] or 0)
                })
            
            # Ventas por día de la semana
            query_dia = f"""
SELECT 
    DATEPART(WEEKDAY, turnos.apertura) as dia_num,
    SUM(cheques.total) as ventas
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY DATEPART(WEEKDAY, turnos.apertura)
ORDER BY DATEPART(WEEKDAY, turnos.apertura)
"""
            result_dia = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_dia
            )
            
            # Mapeo SQL Server DATEPART(WEEKDAY): 1=Domingo, 2=Lunes, ..., 7=Sábado
            # Reordenamos para que sea Lunes a Domingo (2,3,4,5,6,7,1)
            dias_semana = {1: 'Dom', 2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb'}
            orden_dias = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 1: 6}  # Lunes=0, ..., Domingo=6
            
            # Crear diccionario con todos los días inicializados en 0
            ventas_dict = {dia: 0 for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']}
            
            for r in result_dia:
                dia_num = int(r['dia_num'] or 1)
                dia_nombre = dias_semana.get(dia_num, 'Otro')
                if dia_nombre in ventas_dict:
                    ventas_dict[dia_nombre] = float(r['ventas'] or 0)
            
            # Convertir a lista ordenada de Lunes a Domingo
            ventas_por_dia = [{"dia": dia, "ventas": ventas_dict[dia]} for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']]
            
            return {
                "por_hora": ventas_por_hora,
                "por_dia": ventas_por_dia
            }
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO':
            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor_1 = server.get('name', '').lower()
            sucursal_lower_1 = (sucursal or '').lower()
            skip_filter_1 = (not sucursal or sucursal_lower_1 == 'default' or sucursal_lower_1 == nombre_servidor_1)
            if sucursal and not skip_filter_1:
                sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # Ventas por hora para MPRO
            query_hora = f"""
SELECT 
    DATEPART(HOUR, VE.Vn_Fecha) as hora,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
GROUP BY DATEPART(HOUR, VE.Vn_Fecha)
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
            result_hora = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_hora
            )
            
            ventas_por_hora = []
            for r in (result_hora or [])[:6]:  # Top 6 horas
                hora_int = int(r['hora'] or 0)
                ventas_por_hora.append({
                    "hora": f"{hora_int:02d}:00",
                    "ventas": float(r['ventas'] or 0),
                    "pax": int(r['pax'] or 0)
                })
            
            # Ventas por día de la semana para MPRO
            query_dia = f"""
SELECT 
    DATEPART(WEEKDAY, VE.Vn_Fecha) as dia_num,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
GROUP BY DATEPART(WEEKDAY, VE.Vn_Fecha)
ORDER BY DATEPART(WEEKDAY, VE.Vn_Fecha)
"""
            result_dia = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_dia
            )
            
            # Mapeo SQL Server DATEPART(WEEKDAY): 1=Domingo, 2=Lunes, ..., 7=Sábado
            # Reordenamos para que sea Lunes a Domingo
            dias_semana = {1: 'Dom', 2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb'}
            
            # Crear diccionario con todos los días inicializados en 0
            ventas_dict = {dia: 0 for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']}
            
            for r in (result_dia or []):
                dia_num = int(r['dia_num'] or 1)
                dia_nombre = dias_semana.get(dia_num, 'Otro')
                if dia_nombre in ventas_dict:
                    ventas_dict[dia_nombre] = float(r['ventas'] or 0)
            
            # Convertir a lista ordenada de Lunes a Domingo
            ventas_por_dia = [{"dia": dia, "ventas": ventas_dict[dia]} for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']]
            
            return {
                "por_hora": ventas_por_hora,
                "por_dia": ventas_por_dia
            }
        
        return {"por_hora": [], "por_dia": []}
        
    except Exception as e:
        logging.error(f"Error en ventas tiempo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comercial/mesas/{server_id}")
async def comercial_mesas(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de mesas y comensales.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        from datetime import datetime
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # KPIs generales de mesas - sin usar numcuenta que no existe en todas las instalaciones
            query_unidad = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques_mes,
    ISNULL(SUM(cheques.nopersonas), 0) as comensales_mes,
    AVG(cheques.total) as ticket_promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as pax_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_unidad
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_mes = int(row['cheques_mes'] or 0)
                comensales_mes = int(row['comensales_mes'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
                # Estimamos mesas únicas como cheques / 2 (asumiendo 2 servicios por mesa por día en promedio)
                total_mesas = max(1, cheques_mes // max(1, hoy.day * 2))
            else:
                total_mesas = 0
                cheques_mes = 0
                comensales_mes = 0
                ticket_promedio = 0
                pax_promedio = 0
            
            rotacion_promedio = round(cheques_mes / total_mesas, 1) if total_mesas > 0 else 0
            
            # Obtener número de días del mes hasta hoy
            dias_mes = hoy.day
            vueltas_por_dia = round(cheques_mes / dias_mes, 0) if dias_mes > 0 else 0
            
            unidad_data = {
                "nombre": sucursal or server['name'],
                "total_mesas": total_mesas,
                "capacidad_total": total_mesas * 4,  # Estimado 4 personas por mesa
                "mesas_atendidas_mes": cheques_mes,
                "comensales_mes": comensales_mes,
                "rotacion_promedio": rotacion_promedio,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheque_promedio": round(ticket_promedio * pax_promedio, 2) if pax_promedio > 0 else ticket_promedio,
                "pax_promedio": round(pax_promedio, 1),
                "vueltas_por_dia": vueltas_por_dia,
                "vueltas_por_hora_pico": round(vueltas_por_dia / 4, 0)  # Estimado 4 horas pico
            }
            
            # Rotación por hora - más útil sin numcuenta
            query_rotacion = f"""
SELECT TOP 15
    DATEPART(HOUR, turnos.apertura) as hora,
    COUNT(*) as vueltas,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 2) as capacidad_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
GROUP BY DATEPART(HOUR, turnos.apertura)
ORDER BY COUNT(*) DESC
"""
            result_rot = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rotacion
            )
            
            max_vueltas = max([int(r['vueltas'] or 0) for r in result_rot]) if result_rot else 1
            
            rotacion_por_mesa = []
            for r in result_rot:
                vueltas = int(r['vueltas'] or 0)
                ocupacion = round((vueltas / max_vueltas * 100), 0) if max_vueltas > 0 else 0
                hora = int(r['hora'] or 0)
                rotacion_por_mesa.append({
                    "mesa": f"Hora {hora:02d}:00",
                    "capacidad": int(r['capacidad_promedio'] or 2),
                    "vueltas": vueltas,
                    "ocupacion": ocupacion
                })
            
            return {
                "unidad": unidad_data,
                "rotacion": rotacion_por_mesa
            }
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO':
            # Filtro de sucursal para MPRO
            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor_2 = server.get('name', '').lower()
            sucursal_lower_2 = (sucursal or '').lower()
            skip_filter_2 = (not sucursal or sucursal_lower_2 == 'default' or sucursal_lower_2 == nombre_servidor_2)
            if sucursal and not skip_filter_2:
                sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # KPIs generales de mesas para MPRO
            query_unidad = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_mes,
    ISNULL(SUM(C.Co_Personas), 0) as comensales_mes,
    AVG(VE.Vn_Precio_Neto_Importe) as ticket_promedio,
    ISNULL(AVG(CAST(C.Co_Personas as float)), 0) as pax_promedio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_unidad
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_mes = int(row['cheques_mes'] or 0)
                comensales_mes = int(row['comensales_mes'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
                total_mesas = max(1, cheques_mes // max(1, hoy.day * 2))
            else:
                total_mesas = 0
                cheques_mes = 0
                comensales_mes = 0
                ticket_promedio = 0
                pax_promedio = 0
            
            rotacion_promedio = round(cheques_mes / total_mesas, 1) if total_mesas > 0 else 0
            dias_mes = hoy.day
            vueltas_por_dia = round(cheques_mes / dias_mes, 0) if dias_mes > 0 else 0
            
            unidad_data = {
                "nombre": sucursal or server['name'],
                "total_mesas": total_mesas,
                "capacidad_total": total_mesas * 4,
                "mesas_atendidas_mes": cheques_mes,
                "comensales_mes": comensales_mes,
                "rotacion_promedio": rotacion_promedio,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheque_promedio": round(ticket_promedio * pax_promedio, 2) if pax_promedio > 0 else ticket_promedio,
                "pax_promedio": round(pax_promedio, 1),
                "vueltas_por_dia": vueltas_por_dia,
                "vueltas_por_hora_pico": round(vueltas_por_dia / 4, 0)
            }
            
            # Rotación por hora para MPRO
            query_rotacion = f"""
SELECT TOP 15
    DATEPART(HOUR, VE.Vn_Fecha) as hora,
    COUNT(*) as vueltas,
    ISNULL(AVG(CAST(C.Co_Personas as float)), 2) as capacidad_promedio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
GROUP BY DATEPART(HOUR, VE.Vn_Fecha)
ORDER BY COUNT(*) DESC
"""
            result_rotacion = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rotacion
            )
            
            rotacion_por_mesa = []
            for r in (result_rotacion or []):
                hora = int(r['hora'] or 0)
                vueltas = int(r['vueltas'] or 0)
                ocupacion = min(100, round((vueltas / max(1, vueltas_por_dia)) * 100, 1)) if vueltas_por_dia > 0 else 0
                rotacion_por_mesa.append({
                    "mesa": f"Hora {hora:02d}:00",
                    "capacidad": int(r['capacidad_promedio'] or 2),
                    "vueltas": vueltas,
                    "ocupacion": ocupacion
                })
            
            return {
                "unidad": unidad_data,
                "rotacion": rotacion_por_mesa
            }
        
        return {
            "unidad": {"nombre": sucursal, "total_mesas": 0},
            "rotacion": []
        }
        
    except Exception as e:
        logging.error(f"Error en mesas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comercial/detalle-movimientos/{server_id}")
async def comercial_detalle_movimientos(
    server_id: str, 
    sucursal: str = Query(default=""),
    tipo: str = Query(default="ventas"),  # ventas, pax, cheques
    periodo: str = Query(default="mes"),  # dia, semana, mes
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Detalle de movimientos para drill-down en KPIs.
    Devuelve cheques/facturas individuales con su detalle.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        from datetime import datetime, timedelta
        hoy = datetime.now()
        
        # Calcular fechas según período
        if periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        elif periodo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        else:  # mes
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        
        offset = (page - 1) * limit
        
        if server['system_type'] == 'SoftRestaurant':
            # Formato de fecha para SoftRestaurant (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Query para obtener detalle de cheques - Sin columnas opcionales que pueden no existir
            query_detalle = f"""
SELECT 
    cheques.folio,
    turnos.apertura as fecha,
    cheques.total as importe,
    ISNULL(cheques.nopersonas, 0) as pax,
    ISNULL(cheques.descuento, 0) as descuento,
    ISNULL(cheques.propina, 0) as propina,
    'Comedor' as tipo_servicio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
ORDER BY turnos.apertura DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_detalle
            )
            
            # Query para contar total
            query_total = f"""
SELECT COUNT(*) as total
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result_total = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_total
            )
            total = int(result_total[0]['total']) if result_total else 0
            
            movimientos = []
            for row in result or []:
                fecha_val = row.get('fecha')
                fecha_str = fecha_val.strftime('%Y-%m-%d %H:%M') if hasattr(fecha_val, 'strftime') else str(fecha_val) if fecha_val else ''
                movimientos.append({
                    "folio": str(row.get('folio', '')),
                    "fecha": fecha_str,
                    "importe": float(row.get('importe') or 0),
                    "pax": int(row.get('pax') or 0),
                    "descuento": float(row.get('descuento') or 0),
                    "propina": float(row.get('propina') or 0),
                    "tipo_servicio": row.get('tipo_servicio', 'Comedor'),
                    "num_productos": 0
                })
            
            return {
                "movimientos": movimientos,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
                "periodo": {"inicio": fecha_ini, "fin": fecha_fin},
                "servidor": server['name']
            }
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO' or server['system_type'] == 'MPRO':
            # Formato de fecha para MPRO (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Filtro de sucursal si viene - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor = server.get('name', '').lower()
            sucursal_lower = (sucursal or '').lower()
            skip_sucursal_filter = (
                not sucursal or 
                sucursal_lower == 'default' or 
                sucursal_lower == nombre_servidor or
                sucursal_lower == 'managmentpro' or
                sucursal_lower == 'mpro'
            )
            
            if sucursal and not skip_sucursal_filter:
                # Detectar si es un código de sucursal (4 dígitos como "0021") o un nombre
                if len(sucursal) == 4 and sucursal.isdigit():
                    # Es un código de sucursal - buscar por Sc_Cve_Sucursal
                    sucursal_filter = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    # Es un nombre - buscar por descripción parcial
                    sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
            
            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
            query_detalle = f"""
SELECT 
    VE.Vn_Folio as folio,
    VE.Vn_Fecha as fecha,
    VE.Vn_Precio_Neto_Importe as importe,
    ISNULL(C.Co_Personas, 0) as pax,
    'Comedor' as tipo_servicio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{f_ini}'
  AND VE.Vn_Fecha <= '{f_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
ORDER BY VE.Vn_Fecha DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_detalle
            )
            
            # Query para contar total
            query_total = f"""
SELECT COUNT(*) as total
FROM Venta_Encabezado VE
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{f_ini}'
  AND VE.Vn_Fecha <= '{f_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
"""
            result_total = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_total
            )
            total = int(result_total[0]['total']) if result_total else 0
            
            movimientos = []
            for row in result or []:
                fecha_val = row.get('fecha')
                fecha_str = fecha_val.strftime('%Y-%m-%dT%H:%M:%S') if hasattr(fecha_val, 'strftime') else str(fecha_val) if fecha_val else ''
                movimientos.append({
                    "folio": str(row.get('folio', '')),
                    "fecha": fecha_str,
                    "importe": float(row.get('importe') or 0),
                    "pax": int(row.get('pax') or 0),
                    "descuento": 0,
                    "propina": 0,
                    "tipo_servicio": row.get('tipo_servicio', 'Comedor'),
                    "num_productos": 0
                })
            
            return {
                "movimientos": movimientos,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
                "periodo": {"inicio": fecha_ini, "fin": fecha_fin},
                "servidor": server['name']
            }
        
        return {"movimientos": [], "total": 0, "page": 1, "limit": limit, "pages": 0}
        
    except Exception as e:
        logging.error(f"Error en detalle movimientos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comercial/reporte-pax/{server_id}")
async def comercial_reporte_pax(
    server_id: str, 
    sucursal: str = Query(default=""),
    fecha: str = Query(default=""),  # Formato YYYY-MM-DD
    agrupacion: str = Query(default="vendedor"),  # vendedor o ticket
    current_user: Dict = Depends(get_current_user)
):
    """
    Reporte de PAX con drill-down por vendedor o ticket.
    Incluye comparativas vs día/mes/año anterior.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        from datetime import datetime, timedelta
        
        # Fecha seleccionada o hoy
        if fecha:
            fecha_sel = datetime.strptime(fecha, '%Y-%m-%d')
        else:
            fecha_sel = datetime.now()
        
        fecha_str = fecha_sel.strftime('%Y-%m-%d')
        
        # Fechas para comparativos
        fecha_dia_ant = (fecha_sel - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_mes_ant = (fecha_sel.replace(day=1) - timedelta(days=1)).replace(day=min(fecha_sel.day, 28)).strftime('%Y-%m-%d')
        fecha_ano_ant = fecha_sel.replace(year=fecha_sel.year - 1).strftime('%Y-%m-%d')
        
        items = []
        resumen = {"pax_total": 0, "ventas_total": 0, "total_cheques": 0, "pax_promedio": 0, "cheque_promedio": 0}
        comparativo = {"vs_dia_anterior": 0, "vs_mes_anterior": 0, "vs_ano_anterior": 0}
        
        if server['system_type'] == 'SoftRestaurant':
            f_fmt = fecha_str.replace('-', '')
            
            if agrupacion == 'vendedor':
                # Agrupar por vendedor con detalle de cheques
                query = f"""
SELECT 
    ISNULL(emp.nombre, 'Sin Vendedor') as vendedor,
    COUNT(DISTINCT ch.folio) as num_cheques,
    ISNULL(SUM(ch.nopersonas), 0) as pax,
    ISNULL(SUM(ch.total), 0) as total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados emp ON emp.idempleado = ch.idempleado
WHERE t.apertura >= '{f_fmt} 00:00:00'
  AND t.apertura <= '{f_fmt} 23:59:59'
  AND ch.cancelado = 0
  AND ch.total > 0
GROUP BY emp.nombre
ORDER BY SUM(ch.total) DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    vendedor = row.get('vendedor', 'Sin Vendedor')
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    num_cheques = int(row.get('num_cheques') or 0)
                    
                    # Obtener detalle de cheques por vendedor
                    query_detalle = f"""
SELECT 
    ch.folio,
    ISNULL(ch.nopersonas, 0) as pax,
    ch.total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados emp ON emp.idempleado = ch.idempleado
WHERE t.apertura >= '{f_fmt} 00:00:00'
  AND t.apertura <= '{f_fmt} 23:59:59'
  AND ch.cancelado = 0
  AND ch.total > 0
  AND ISNULL(emp.nombre, 'Sin Vendedor') = '{vendedor.replace("'", "''")}'
ORDER BY ch.total DESC
"""
                    detalle_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_detalle
                    )
                    
                    detalle = []
                    for det in detalle_result or []:
                        det_pax = int(det.get('pax') or 0)
                        det_total = float(det.get('total') or 0)
                        detalle.append({
                            "folio": str(det.get('folio', '')),
                            "pax": det_pax,
                            "total": det_total,
                            "pax_promedio": det_total / det_pax if det_pax > 0 else det_total
                        })
                    
                    items.append({
                        "id": f"v_{idx}",
                        "nombre": vendedor,
                        "pax": pax,
                        "total": total,
                        "num_cheques": num_cheques,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": detalle
                    })
            else:
                # Agrupar por ticket/cheque con detalle de vendedor
                query = f"""
SELECT 
    ch.folio,
    ISNULL(emp.nombre, 'Sin Vendedor') as vendedor,
    ISNULL(ch.nopersonas, 0) as pax,
    ch.total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados emp ON emp.idempleado = ch.idempleado
WHERE t.apertura >= '{f_fmt} 00:00:00'
  AND t.apertura <= '{f_fmt} 23:59:59'
  AND ch.cancelado = 0
  AND ch.total > 0
ORDER BY ch.total DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    items.append({
                        "id": f"t_{idx}",
                        "folio": str(row.get('folio', '')),
                        "nombre": str(row.get('folio', '')),
                        "vendedor": row.get('vendedor', 'Sin Vendedor'),
                        "pax": pax,
                        "total": total,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": [{
                            "vendedor": row.get('vendedor', 'Sin Vendedor'),
                            "pax": pax,
                            "total": total,
                            "pax_promedio": total / pax if pax > 0 else total
                        }]
                    })
            
            # Calcular totales
            resumen["pax_total"] = sum(i['pax'] for i in items)
            resumen["ventas_total"] = sum(i['total'] for i in items)
            resumen["total_cheques"] = len(items) if agrupacion == 'ticket' else sum(i.get('num_cheques', 1) for i in items)
            resumen["pax_promedio"] = resumen["ventas_total"] / resumen["pax_total"] if resumen["pax_total"] > 0 else 0
            resumen["cheque_promedio"] = resumen["ventas_total"] / resumen["total_cheques"] if resumen["total_cheques"] > 0 else 0
            
            # Comparativos
            def get_pax_fecha(f):
                f_q = f.replace('-', '')
                q = f"""
SELECT ISNULL(SUM(ch.nopersonas), 0) as pax, ISNULL(SUM(ch.total), 0) as total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
WHERE t.apertura >= '{f_q} 00:00:00' AND t.apertura <= '{f_q} 23:59:59'
  AND ch.cancelado = 0 AND ch.total > 0
"""
                r = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], q)
                return int(r[0]['pax'] or 0) if r else 0, float(r[0]['total'] or 0) if r else 0
            
            pax_ant, total_ant = get_pax_fecha(fecha_dia_ant)
            pax_mes, total_mes = get_pax_fecha(fecha_mes_ant)
            pax_ano, total_ano = get_pax_fecha(fecha_ano_ant)
            
            pax_prom_actual = resumen["pax_promedio"]
            pax_prom_ant = total_ant / pax_ant if pax_ant > 0 else 0
            pax_prom_mes = total_mes / pax_mes if pax_mes > 0 else 0
            pax_prom_ano = total_ano / pax_ano if pax_ano > 0 else 0
            
            comparativo["vs_dia_anterior"] = ((pax_prom_actual - pax_prom_ant) / pax_prom_ant * 100) if pax_prom_ant > 0 else 0
            comparativo["vs_mes_anterior"] = ((pax_prom_actual - pax_prom_mes) / pax_prom_mes * 100) if pax_prom_mes > 0 else 0
            comparativo["vs_ano_anterior"] = ((pax_prom_actual - pax_prom_ano) / pax_prom_ano * 100) if pax_prom_ano > 0 else 0
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO':
            # Implementación para MPRO
            if agrupacion == 'vendedor':
                query = f"""
SELECT 
    ISNULL(E.Em_Nombre, 'Sin Vendedor') as vendedor,
    COUNT(DISTINCT V.Vn_Folio) as num_cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax,
    SUM(V.Vn_Precio_Neto_Importe) as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
LEFT JOIN Empleado E ON E.Em_Cve = V.Em_Cve_Mesero
WHERE V.Vn_Fecha = '{fecha_str}'
  AND V.Vn_Cancelacion = 0
  AND V.Vn_Precio_Neto_Importe > 0
GROUP BY E.Em_Nombre
ORDER BY SUM(V.Vn_Precio_Neto_Importe) DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    vendedor = row.get('vendedor', 'Sin Vendedor')
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    num_cheques = int(row.get('num_cheques') or 0)
                    
                    # Detalle por vendedor
                    query_det = f"""
SELECT V.Vn_Folio as folio, ISNULL(C.Co_Personas, 0) as pax, V.Vn_Precio_Neto_Importe as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
LEFT JOIN Empleado E ON E.Em_Cve = V.Em_Cve_Mesero
WHERE V.Vn_Fecha = '{fecha_str}' AND V.Vn_Cancelacion = 0 AND V.Vn_Precio_Neto_Importe > 0
  AND ISNULL(E.Em_Nombre, 'Sin Vendedor') = '{vendedor.replace("'", "''")}'
ORDER BY V.Vn_Precio_Neto_Importe DESC
"""
                    det_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_det
                    )
                    
                    detalle = []
                    for det in det_result or []:
                        det_pax = int(det.get('pax') or 0)
                        det_total = float(det.get('total') or 0)
                        detalle.append({
                            "folio": str(det.get('folio', '')),
                            "pax": det_pax,
                            "total": det_total,
                            "pax_promedio": det_total / det_pax if det_pax > 0 else det_total
                        })
                    
                    items.append({
                        "id": f"v_{idx}",
                        "nombre": vendedor,
                        "pax": pax,
                        "total": total,
                        "num_cheques": num_cheques,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": detalle
                    })
            else:
                # Por ticket
                query = f"""
SELECT 
    V.Vn_Folio as folio,
    ISNULL(E.Em_Nombre, 'Sin Vendedor') as vendedor,
    ISNULL(C.Co_Personas, 0) as pax,
    V.Vn_Precio_Neto_Importe as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
LEFT JOIN Empleado E ON E.Em_Cve = V.Em_Cve_Mesero
WHERE V.Vn_Fecha = '{fecha_str}'
  AND V.Vn_Cancelacion = 0
  AND V.Vn_Precio_Neto_Importe > 0
ORDER BY V.Vn_Precio_Neto_Importe DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    items.append({
                        "id": f"t_{idx}",
                        "folio": str(row.get('folio', '')),
                        "nombre": str(row.get('folio', '')),
                        "vendedor": row.get('vendedor', 'Sin Vendedor'),
                        "pax": pax,
                        "total": total,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": [{
                            "vendedor": row.get('vendedor', 'Sin Vendedor'),
                            "pax": pax,
                            "total": total,
                            "pax_promedio": total / pax if pax > 0 else total
                        }]
                    })
            
            # Calcular resumen
            resumen["pax_total"] = sum(i['pax'] for i in items)
            resumen["ventas_total"] = sum(i['total'] for i in items)
            resumen["total_cheques"] = len(items) if agrupacion == 'ticket' else sum(i.get('num_cheques', 1) for i in items)
            resumen["pax_promedio"] = resumen["ventas_total"] / resumen["pax_total"] if resumen["pax_total"] > 0 else 0
            resumen["cheque_promedio"] = resumen["ventas_total"] / resumen["total_cheques"] if resumen["total_cheques"] > 0 else 0
            
            # Comparativos para MPRO
            def get_pax_mpro(f):
                q = f"""
SELECT ISNULL(SUM(C.Co_Personas), 0) as pax, SUM(V.Vn_Precio_Neto_Importe) as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
WHERE V.Vn_Fecha = '{f}' AND V.Vn_Cancelacion = 0 AND V.Vn_Precio_Neto_Importe > 0
"""
                r = execute_sql_query(server['host'], server['port'], server['database'],
                                      server['username'], server['password'], q)
                return int(r[0]['pax'] or 0) if r else 0, float(r[0]['total'] or 0) if r else 0
            
            pax_ant, total_ant = get_pax_mpro(fecha_dia_ant)
            pax_mes, total_mes = get_pax_mpro(fecha_mes_ant)
            pax_ano, total_ano = get_pax_mpro(fecha_ano_ant)
            
            pax_prom_actual = resumen["pax_promedio"]
            pax_prom_ant = total_ant / pax_ant if pax_ant > 0 else 0
            pax_prom_mes = total_mes / pax_mes if pax_mes > 0 else 0
            pax_prom_ano = total_ano / pax_ano if pax_ano > 0 else 0
            
            comparativo["vs_dia_anterior"] = ((pax_prom_actual - pax_prom_ant) / pax_prom_ant * 100) if pax_prom_ant > 0 else 0
            comparativo["vs_mes_anterior"] = ((pax_prom_actual - pax_prom_mes) / pax_prom_mes * 100) if pax_prom_mes > 0 else 0
            comparativo["vs_ano_anterior"] = ((pax_prom_actual - pax_prom_ano) / pax_prom_ano * 100) if pax_prom_ano > 0 else 0
        
        return {
            "items": items,
            "resumen": resumen,
            "comparativo": comparativo,
            "fecha": fecha_str,
            "servidor": server['name']
        }
        
    except Exception as e:
        logging.error(f"Error en reporte PAX: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        except:
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

def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
    """Query reutilizable para SoftRestaurant - misma lógica análisis inventarios"""
    import calendar
    
    # Si solo_ventas_dia es True, consultar SOLO tempcheques (ventas sin corte)
    if solo_ventas_dia:
        query_temp = """
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
        try:
            result_temp = execute_sql_query(server['host'], server['port'], server['database'], 
                                            server['username'], server['password'], query_temp)
            if result_temp and len(result_temp) > 0:
                ventas = float(result_temp[0]['ventas'] or 0)
                pax = int(result_temp[0]['pax'] or 0)
                cheques = int(result_temp[0]['cheques'] or 0)
            else:
                ventas, pax, cheques = 0, 0, 0
            
            ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
            cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
            
            return {
                "ventas": ventas,
                "ventas_ant": 0,
                "ventas_año": 0,
                "var_vs_mes_ant": 0,
                "var_vs_año_ant": 0,
                "proyeccion": 0,
                "pax": pax,
                "pax_ant": 0,
                "pax_año": 0,
                "var_pax_mes": 0,
                "var_pax_año": 0,
                "cheques": cheques,
                "cheques_ant": 0,
                "cheques_año": 0,
                "var_cheques_mes": 0,
                "var_cheques_año": 0,
                "ticket_prom": ticket_prom,
                "cheque_prom": cheque_prom,
                "es_ventas_dia": True  # Flag para identificar datos de ventas del día
            }
        except Exception as e:
            logging.warning(f"Error consultando tempcheques {server['name']}: {e}")
            return None
    
    # Usar formato YYYYMMDD sin guiones para evitar problemas de conversión de fecha
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, turnos.apertura)) as ultimo_dia_venta
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fi} 00:00:00'
  AND turnos.apertura <= '{ff} 23:59:59'
  AND cheques.cancelado = 0
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
            else:
                dia_con_datos = ultimo_dia_venta.day
            
            logging.info(f"SoftRestaurant {server['name']} - Último día con ventas: día {dia_con_datos}")
            
            # Actualizar fecha_fin y recalcular días transcurridos
            ff = f"{fi[:6]}{str(dia_con_datos).zfill(2)}"
            dias_transcurridos = dia_con_datos
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = int(fi[4:6])
            anio_actual = int(fi[:4])
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior
            anio_pasado = anio_actual - 1
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_actual)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"Períodos ajustados - Actual: {fi[:4]}-{fi[4:6]}-01 a {fi[:6]}{str(dia_con_datos).zfill(2)}, Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"Error detectando último día: {e}")
        # Si falla, continuar con las fechas originales
    
    # Query principal
    query = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques,
    ISNULL(SUM(cheques.total), 0) as ventas,
    ISNULL(SUM(cheques.nopersonas), 0) as pax
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fi} 00:00:00'
  AND turnos.apertura <= '{ff} 23:59:59'
  AND cheques.cancelado = 0
"""
    try:
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        if result and len(result) > 0:
            ventas = float(result[0]['ventas'] or 0)
            pax = int(result[0]['pax'] or 0)
            cheques = int(result[0]['cheques'] or 0)
        else:
            ventas, pax, cheques = 0, 0, 0
    except Exception as e:
        logging.warning(f"Error consultando {server['name']}: {e}")
        return None
    
    # SUMAR ventas del día sin corte (tempcheques) a las ventas históricas
    try:
        query_temp = """
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
        result_temp = execute_sql_query(server['host'], server['port'], server['database'], 
                                        server['username'], server['password'], query_temp)
        if result_temp and len(result_temp) > 0:
            ventas_temp = float(result_temp[0]['ventas'] or 0)
            pax_temp = int(result_temp[0]['pax'] or 0)
            cheques_temp = int(result_temp[0]['cheques'] or 0)
            # Sumar a los totales
            ventas += ventas_temp
            pax += pax_temp
            cheques += cheques_temp
            logging.info(f"SoftRestaurant {server['name']} - Tempcheques sumados: ventas={ventas_temp}, pax={pax_temp}, cheques={cheques_temp}")
    except Exception as e:
        logging.warning(f"Error consultando tempcheques {server['name']}: {e} - continuando sin ventas del día")
    
    # Mes anterior (mismos días)
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    query_ant = f"""
SELECT ISNULL(SUM(cheques.total), 0) as ventas, ISNULL(SUM(cheques.nopersonas), 0) as pax, COUNT(DISTINCT cheques.folio) as cheques
FROM cheques INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fia} 00:00:00' AND turnos.apertura <= '{ffa} 23:59:59' AND cheques.cancelado = 0
"""
    try:
        r_ant = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_ant)
        ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
        pax_ant = int(r_ant[0]['pax'] or 0) if r_ant else 0
        cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
    except:
        ventas_ant, pax_ant, cheques_ant = 0, 0, 0
    
    # Año anterior (mismos días)
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    query_año = f"""
SELECT ISNULL(SUM(cheques.total), 0) as ventas, ISNULL(SUM(cheques.nopersonas), 0) as pax, COUNT(DISTINCT cheques.folio) as cheques
FROM cheques INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fiaa} 00:00:00' AND turnos.apertura <= '{ffaa} 23:59:59' AND cheques.cancelado = 0
"""
    try:
        r_año = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_año)
        ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
        pax_año = int(r_año[0]['pax'] or 0) if r_año else 0
        cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
    except:
        ventas_año, pax_año, cheques_año = 0, 0, 0
    
    # Cálculos
    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
    
    # Proyección mes completo
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # Variaciones %
    var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
    var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
    var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
    var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
    var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
    
    return {
        "ventas": ventas,
        "ventas_ant": ventas_ant,
        "ventas_año": ventas_año,
        "var_vs_mes_ant": var_vs_mes_ant,
        "var_vs_año_ant": var_vs_año_ant,
        "proyeccion": proyeccion,
        "pax": pax,
        "pax_ant": pax_ant,
        "pax_año": pax_año,
        "var_pax_mes": var_pax_mes,
        "var_pax_año": var_pax_año,
        "cheques": cheques,
        "cheques_ant": cheques_ant,
        "cheques_año": cheques_año,
        "var_cheques_mes": var_cheques_mes,
        "var_cheques_año": var_cheques_año,
        "ticket_prom": ticket_prom,
        "cheque_prom": cheque_prom
    }


def get_kpis_mpro(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
    """Query reutilizable para MPRO - ventas desde tabla Venta"""
    import calendar
    
    # Formato YYYYMMDD para MPRO
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, Vn_Fecha)) as ultimo_dia_venta
FROM Venta
WHERE Vn_Fecha >= '{fi}' AND Vn_Fecha <= '{ff} 23:59:59'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
            else:
                dia_con_datos = ultimo_dia_venta.day
            
            logging.info(f"MPRO {server['name']} - Último día con ventas: día {dia_con_datos}")
            
            # Actualizar fecha_fin y recalcular días transcurridos
            ff = f"{fi[:6]}{str(dia_con_datos).zfill(2)}"
            dias_transcurridos = dia_con_datos
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = int(fi[4:6])
            anio_actual = int(fi[:4])
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior
            anio_pasado = anio_actual - 1
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_actual)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"MPRO Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"MPRO Error detectando último día: {e}")
    
    # MPRO usa Vn_Folio para identificar tickets y Vn_Precio_Neto_Importe para el monto de venta
    query = f"""
SELECT 
    COUNT(DISTINCT Vn_Folio) as cheques,
    ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta
WHERE Vn_Fecha >= '{fi}' AND Vn_Fecha <= '{ff} 23:59:59'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        if result and len(result) > 0:
            ventas = float(result[0]['ventas'] or 0)
            cheques = int(result[0]['cheques'] or 0)
        else:
            ventas, cheques = 0, 0
        logging.info(f"MPRO {server['name']}: Ventas={ventas}, Cheques={cheques}")
    except Exception as e:
        logging.warning(f"Error consultando MPRO {server['name']}: {e}")
        return None
    
    # MPRO no tiene PAX normalmente, estimamos como cheques
    pax = cheques
    
    # Mes anterior
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    query_ant = f"""
SELECT ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas, COUNT(DISTINCT Vn_Folio) as cheques
FROM Venta WHERE Vn_Fecha >= '{fia}' AND Vn_Fecha <= '{ffa} 23:59:59' AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        r_ant = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_ant)
        ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
        cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
    except:
        ventas_ant, cheques_ant = 0, 0
    pax_ant = cheques_ant
    
    # Año anterior
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    query_año = f"""
SELECT ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas, COUNT(DISTINCT Vn_Folio) as cheques
FROM Venta WHERE Vn_Fecha >= '{fiaa}' AND Vn_Fecha <= '{ffaa} 23:59:59' AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        r_año = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_año)
        ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
        cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
    except:
        ventas_año, cheques_año = 0, 0
    pax_año = cheques_año
    
    # Cálculos
    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # Variaciones %
    var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
    var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
    var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
    var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
    var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
    
    return {
        "ventas": ventas,
        "ventas_ant": ventas_ant,
        "ventas_año": ventas_año,
        "var_vs_mes_ant": var_vs_mes_ant,
        "var_vs_año_ant": var_vs_año_ant,
        "proyeccion": proyeccion,
        "pax": pax,
        "pax_ant": pax_ant,
        "pax_año": pax_año,
        "var_pax_mes": var_pax_mes,
        "var_pax_año": var_pax_año,
        "cheques": cheques,
        "cheques_ant": cheques_ant,
        "cheques_año": cheques_año,
        "var_cheques_mes": var_cheques_mes,
        "var_cheques_año": var_cheques_año,
        "ticket_prom": ticket_prom,
        "cheque_prom": cheque_prom
    }


def get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
    """
    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
    Retorna una lista de unidades, no un solo bloque.
    """
    import calendar
    
    # Formato YYYYMMDD para MPRO (SQL Server con configuración regional español)
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
            else:
                dia_con_datos = ultimo_dia_venta.day
            
            print(f"*** MPRO por sucursal {server['name']} - Ultimo dia con ventas: dia {dia_con_datos} ***")
            
            # Actualizar fecha_fin y recalcular días transcurridos
            ff = f"{fi[:6]}{str(dia_con_datos).zfill(2)}"
            dias_transcurridos = dia_con_datos
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = int(fi[4:6])
            anio_actual = int(fi[:4])
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior
            anio_pasado = anio_actual - 1
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_actual)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"MPRO por sucursal Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"MPRO por sucursal Error detectando último día: {e}")
    
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    
    logging.info(f"MPRO {server['name']}: Consultando ventas del {fi} al {ff}")
    
    # Query principal agrupando por sucursal - INCLUYE PAX desde Comanda
    # IMPORTANTE: Usar formato YYYYMMDD para evitar errores de conversión regional
    query = f"""
SELECT 
    S.Sc_Cve_Sucursal as sucursal_id,
    S.Sc_Descripcion as sucursal_nombre,
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
GROUP BY S.Sc_Cve_Sucursal, S.Sc_Descripcion
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
    
    try:
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        if not result:
            logging.warning(f"MPRO {server['name']}: No se encontraron sucursales con ventas")
            return []
    except Exception as e:
        logging.warning(f"Error consultando MPRO por sucursal {server['name']}: {e}")
        return []
    
    unidades = []
    
    for row in result:
        sucursal_id = row.get('sucursal_id', '')
        sucursal_nombre = row.get('sucursal_nombre', 'Sin nombre')
        ventas = float(row.get('ventas') or 0)
        cheques = int(row.get('cheques') or 0)
        pax = int(row.get('pax') or 0)  # PAX real desde Comanda.Co_Personas
        
        # Si PAX es 0 pero hay cheques, estimamos PAX = cheques (1 persona por ticket mínimo)
        if pax == 0 and cheques > 0:
            pax = cheques
        
        # PASO 2: Detectar el último día con ventas PARA ESTA SUCURSAL específica
        query_ultimo_dia_suc = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            result_ultimo_suc = execute_sql_query(server['host'], server['port'], server['database'], 
                                                  server['username'], server['password'], query_ultimo_dia_suc)
            if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
                ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
                if isinstance(ultimo_dia_suc, str):
                    dia_suc = int(ultimo_dia_suc.split('-')[2]) if '-' in ultimo_dia_suc else int(ultimo_dia_suc[-2:])
                else:
                    dia_suc = ultimo_dia_suc.day
                
                print(f"*** MPRO {sucursal_nombre} - Ultimo dia con ventas: dia {dia_suc} ***")
                
                # Recalcular fechas de comparación para esta sucursal
                mes_actual = int(fi[4:6])
                anio_actual = int(fi[:4])
                
                # Mes anterior
                if mes_actual == 1:
                    mes_ant = 12
                    anio_ant = anio_actual - 1
                else:
                    mes_ant = mes_actual - 1
                    anio_ant = anio_actual
                
                max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
                dia_comparar = min(dia_suc, max_dia_mes_ant)
                fia_suc = f"{anio_ant}{str(mes_ant).zfill(2)}01"
                ffa_suc = f"{anio_ant}{str(mes_ant).zfill(2)}{str(dia_comparar).zfill(2)}"
                
                # Año anterior
                anio_pasado = anio_actual - 1
                max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_actual)[1]
                dia_ano_ant = min(dia_suc, max_dia_ano_ant)
                fiaa_suc = f"{anio_pasado}{str(mes_actual).zfill(2)}01"
                ffaa_suc = f"{anio_pasado}{str(mes_actual).zfill(2)}{str(dia_ano_ant).zfill(2)}"
            else:
                # Si no hay datos, usar fechas globales
                fia_suc, ffa_suc = fia, ffa
                fiaa_suc, ffaa_suc = fiaa, ffaa
                dia_suc = dias_transcurridos
        except Exception as e:
            print(f"Error detectando ultimo dia para {sucursal_nombre}: {e}")
            fia_suc, ffa_suc = fia, ffa
            fiaa_suc, ffaa_suc = fiaa, ffaa
            dia_suc = dias_transcurridos
        
        # Query mes anterior para esta sucursal - con PAX (formato YYYYMMDD)
        query_ant = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fia_suc}' AND VE.Vn_Fecha <= '{ffa_suc} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            r_ant = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], query_ant)
            ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
            cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
            pax_ant = int(r_ant[0]['pax'] or 0) if r_ant else 0
            if pax_ant == 0 and cheques_ant > 0:
                pax_ant = cheques_ant
        except:
            ventas_ant, cheques_ant, pax_ant = 0, 0, 0
        
        # Query año anterior para esta sucursal - con PAX (formato YYYYMMDD)
        query_año = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fiaa_suc}' AND VE.Vn_Fecha <= '{ffaa_suc} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            r_año = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], query_año)
            ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
            cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
            pax_año = int(r_año[0]['pax'] or 0) if r_año else 0
            if pax_año == 0 and cheques_año > 0:
                pax_año = cheques_año
        except:
            ventas_año, cheques_año, pax_año = 0, 0, 0
        
        # Cálculos
        ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
        cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
        proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
        
        # Variaciones %
        var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
        var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
        
        print(f"MPRO {sucursal_nombre}: Dia={dia_suc}, Actual={ventas:.2f}, MesAnt({fia_suc}-{ffa_suc})={ventas_ant:.2f} -> {var_vs_mes_ant}%, AnoAnt({fiaa_suc}-{ffaa_suc})={ventas_año:.2f} -> {var_vs_año_ant}%")
        var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
        var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
        var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
        var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
        
        unidades.append({
            "unidad": sucursal_nombre,
            "sucursal": sucursal_nombre,  # Para filtrar en endpoints de detalle
            "server_id": server['id'],
            "sucursal_id": sucursal_id,
            "system_type": "MPRO",
            "parent_server": server['name'],
            "ventas": ventas,
            "ventas_ant": ventas_ant,
            "ventas_año": ventas_año,
            "var_vs_mes_ant": var_vs_mes_ant,
            "var_vs_año_ant": var_vs_año_ant,
            "proyeccion": proyeccion,
            "pax": pax,
            "pax_ant": pax_ant,
            "pax_año": pax_año,
            "var_pax_mes": var_pax_mes,
            "var_pax_año": var_pax_año,
            "cheques": cheques,
            "cheques_ant": cheques_ant,
            "cheques_año": cheques_año,
            "var_cheques_mes": var_cheques_mes,
            "var_cheques_año": var_cheques_año,
            "ticket_prom": ticket_prom,
            "cheque_prom": cheque_prom
        })
        
        logging.info(f"MPRO {server['name']} - Sucursal '{sucursal_nombre}': Ventas={ventas}, Cheques={cheques}")
    
    return unidades


@api_router.get("/comercial/tablero-ejecutivo")
async def tablero_ejecutivo(
    mes: int = Query(default=0),  # 0 = mes actual
    anio: int = Query(default=0),  # 0 = año actual, -1 = ventas del día
    current_user: Dict = Depends(get_current_user)
):
    """
    Tablero ejecutivo con KPIs de TODAS las unidades.
    Comparativo vs mes anterior y año anterior (mismos días).
    anio=-1: Modo "Ventas del Día" - solo tempcheques (ventas sin corte) de SoftRestaurant.
    """
    from datetime import datetime, timedelta
    import calendar
    
    hoy = datetime.now()
    
    # Modo especial: Ventas del Día (anio = -1)
    solo_ventas_dia = (anio == -1)
    
    # Determinar período
    if anio == 0:
        anio = hoy.year
    if mes == 0:
        mes = hoy.month
    
    # Fechas del período actual
    fecha_ini = f"{anio}-{mes:02d}-01"
    if anio == hoy.year and mes == hoy.month:
        # Mes actual incompleto - ventas hasta AYER (hoy no se cuenta)
        ayer = hoy - timedelta(days=1)
        fecha_fin = ayer.strftime('%Y-%m-%d')
        dias_transcurridos = ayer.day  # Días hasta ayer, no hasta hoy
    else:
        # Mes completo
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        fecha_fin = f"{anio}-{mes:02d}-{ultimo_dia:02d}"
        dias_transcurridos = ultimo_dia
    
    dias_mes = calendar.monthrange(anio, mes)[1]
    
    # Mes anterior (mismos días para comparar proporcional)
    if mes == 1:
        mes_ant, anio_mes_ant = 12, anio - 1
    else:
        mes_ant, anio_mes_ant = mes - 1, anio
    fecha_ini_ant = f"{anio_mes_ant}-{mes_ant:02d}-01"
    fecha_fin_ant = f"{anio_mes_ant}-{mes_ant:02d}-{min(dias_transcurridos, calendar.monthrange(anio_mes_ant, mes_ant)[1]):02d}"
    
    # Año anterior (mismo mes, mismos días)
    fecha_ini_año_ant = f"{anio-1}-{mes:02d}-01"
    fecha_fin_año_ant = f"{anio-1}-{mes:02d}-{min(dias_transcurridos, calendar.monthrange(anio-1, mes)[1]):02d}"
    
    # Año anterior MES COMPLETO (para comparar proyección vs mes completo)
    ultimo_dia_año_ant = calendar.monthrange(anio-1, mes)[1]
    fecha_fin_año_ant_completo = f"{anio-1}-{mes:02d}-{ultimo_dia_año_ant:02d}"
    
    logging.info(f"Tablero Ejecutivo: {mes}/{anio} ({fecha_ini} a {fecha_fin}), días: {dias_transcurridos}/{dias_mes}")
    
    # Obtener todos los servidores activos Y visibles en operaciones
    servers = await db.servers.find({
        "active": True, 
        "visible_en_operaciones": {"$ne": False}  # Incluye True y documentos sin el campo
    }).to_list(100)
    logging.info(f"Servidores encontrados: {len(servers)} - Tipos: {[s['system_type'] for s in servers]}")
    
    # Filtrar por permisos del usuario
    if current_user.get('role') != 'Administrador':
        allowed = current_user.get('allowed_servers', [])
        servers = [s for s in servers if s['id'] in allowed]
    
    resultados = []
    totales = {"ventas": 0, "ventas_ant": 0, "ventas_año": 0, "ventas_año_completo": 0, "pax": 0, "pax_ant": 0, "pax_año": 0, 
               "cheques": 0, "cheques_ant": 0, "cheques_año": 0, "proyeccion": 0}
    
    periodo_key = f"{anio}-{mes:02d}"
    
    for server in servers:
        logging.info(f"Procesando servidor: {server['name']} - Tipo: {server['system_type']}")
        
        # Verificar si el servidor está offline recientemente (evitar timeouts)
        server_offline = await is_server_recently_offline(server['id'], minutes_threshold=10)
        
        if server['system_type'] == 'SoftRestaurant':
            kpis = None
            
            # Solo intentar conexión si el servidor NO está marcado como offline recientemente
            if not server_offline:
                kpis = get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                               fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia)
                if kpis:
                    # Conexión exitosa - marcar como online
                    await save_server_connection_status(server['id'], True)
                else:
                    # Conexión fallida - marcar como offline
                    await save_server_connection_status(server['id'], False)
            else:
                logging.info(f"Servidor {server['name']} marcado como offline - usando caché")
            
            if kpis:
                # Conexión exitosa - guardar en caché
                kpis["unidad"] = server['name']
                kpis["server_id"] = server['id']
                kpis["system_type"] = server['system_type']
                kpis["status"] = "online"
                kpis["updated_at"] = datetime.now(timezone.utc).isoformat()
                resultados.append(kpis)
                # Guardar en caché
                await save_kpis_cache(server['id'], periodo_key, kpis)
                # Acumular totales
                for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                          "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                    totales[k] += kpis.get(k, 0)
            else:
                # Conexión fallida - buscar en caché
                cached = await get_cached_kpis(server['id'], periodo_key)
                if cached and cached.get('kpis'):
                    kpis = cached['kpis']
                    kpis["status"] = "offline"
                    kpis["updated_at"] = cached.get('updated_at', '')
                    kpis["unidad"] = server['name']
                    kpis["server_id"] = server['id']
                    kpis["system_type"] = server['system_type']
                    resultados.append(kpis)
                    logging.info(f"Usando caché para {server['name']} - última actualización: {cached.get('updated_at')}")
                    # Acumular totales del caché
                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                        totales[k] += kpis.get(k, 0)
                else:
                    logging.warning(f"Sin caché disponible para {server['name']}")
        
        elif server['system_type'] == 'MPRO':
            # MPRO: Dividir por sucursal (igual que en Inventarios)
            logging.info(f"Procesando servidor MPRO: {server['name']}")
            try:
                unidades_mpro = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                                           fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes)
                logging.info(f"MPRO {server['name']}: Encontradas {len(unidades_mpro)} unidades")
                for unidad in unidades_mpro:
                    unidad["status"] = "online"
                    unidad["updated_at"] = datetime.now(timezone.utc).isoformat()
                    resultados.append(unidad)
                    # Guardar en caché cada unidad
                    unidad_key = f"{periodo_key}-{unidad.get('unidad', 'unknown')}"
                    await save_kpis_cache(server['id'], unidad_key, unidad)
                    # Acumular totales
                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                        totales[k] += unidad.get(k, 0)
            except Exception as mpro_error:
                logging.error(f"Error procesando MPRO {server['name']}: {mpro_error}")
                # Buscar en caché para MPRO
                cached_list = await db.kpis_cache.find({
                    "server_id": server['id'],
                    "periodo_key": {"$regex": f"^{periodo_key}"}
                }).to_list(100)
                for cached in cached_list:
                    if cached.get('kpis'):
                        kpis = cached['kpis']
                        kpis["status"] = "offline"
                        kpis["updated_at"] = cached.get('updated_at', '')
                        resultados.append(kpis)
                        for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                  "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                            totales[k] += kpis.get(k, 0)
    
    # Calcular variaciones de totales
    totales["var_vs_mes_ant"] = round(((totales["ventas"] - totales["ventas_ant"]) / totales["ventas_ant"] * 100), 1) if totales["ventas_ant"] > 0 else 0
    totales["var_vs_año_ant"] = round(((totales["ventas"] - totales["ventas_año"]) / totales["ventas_año"] * 100), 1) if totales["ventas_año"] > 0 else 0
    totales["var_pax_mes"] = round(((totales["pax"] - totales["pax_ant"]) / totales["pax_ant"] * 100), 1) if totales["pax_ant"] > 0 else 0
    totales["var_pax_año"] = round(((totales["pax"] - totales["pax_año"]) / totales["pax_año"] * 100), 1) if totales["pax_año"] > 0 else 0
    totales["var_cheques_mes"] = round(((totales["cheques"] - totales["cheques_ant"]) / totales["cheques_ant"] * 100), 1) if totales["cheques_ant"] > 0 else 0
    totales["var_cheques_año"] = round(((totales["cheques"] - totales["cheques_año"]) / totales["cheques_año"] * 100), 1) if totales["cheques_año"] > 0 else 0
    totales["ticket_prom"] = round(totales["ventas"] / totales["pax"], 2) if totales["pax"] > 0 else 0
    totales["cheque_prom"] = round(totales["ventas"] / totales["cheques"], 2) if totales["cheques"] > 0 else 0
    
    # Estimar ventas del año anterior MES COMPLETO (proyección proporcional)
    # Si tenemos 7 días de año anterior con X ventas, el mes completo sería X * (días_mes / días_transcurridos)
    ventas_año_completo_estimado = (totales["ventas_año"] / dias_transcurridos * dias_mes) if dias_transcurridos > 0 and totales["ventas_año"] > 0 else 0
    totales["ventas_año_completo"] = round(ventas_año_completo_estimado, 0)
    
    # Proyección vs ventas año anterior MES COMPLETO (no solo los días equivalentes)
    totales["var_proy_vs_año"] = round(((totales["proyeccion"] - ventas_año_completo_estimado) / ventas_año_completo_estimado * 100), 1) if ventas_año_completo_estimado > 0 else 0
    
    # Contar unidades que tenían ventas el año anterior (ventas_año > 0)
    totales["unidades_año_ant"] = sum(1 for u in resultados if u.get("ventas_año", 0) > 0)
    
    # Ordenar unidades de mayor a menor venta
    resultados_ordenados = sorted(resultados, key=lambda x: x.get('ventas', 0), reverse=True)
    
    # Período para respuesta
    periodo_info = {
        "mes": mes, 
        "anio": anio, 
        "dias_transcurridos": dias_transcurridos, 
        "dias_mes": dias_mes,
        "modo_ventas_dia": solo_ventas_dia
    }
    
    # Si es modo ventas del día, ajustar el período para mostrarlo diferente
    if solo_ventas_dia:
        periodo_info["mes"] = 0
        periodo_info["anio"] = -1
        periodo_info["label"] = "Ventas del Día (sin corte)"
    
    return {
        "periodo": periodo_info,
        "comparativo_con": {"mes_anterior": f"{mes_ant}/{anio_mes_ant}", "año_anterior": f"{mes}/{anio-1}"},
        "unidades": resultados_ordenados,
        "totales": totales
    }



@api_router.get("/comercial/sucursales/{server_id}")
async def obtener_sucursales(
    server_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene las sucursales/empresas de un servidor"""
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        if server['system_type'] == 'MPRO':
            # MPRO: Tabla sucursal (relacionada con venta por Sc_Cve_Sucursal)
            query = """
            SELECT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre 
            FROM sucursal 
            WHERE Es_Cve_Estado = 'AC' 
            ORDER BY Sc_Descripcion
            """
        else:
            # SoftRestaurant: No tiene múltiples sucursales, devolver el servidor como única opción
            return {
                "servidor": server['name'],
                "sucursales": [{
                    "id": "all",
                    "nombre": server['name']
                }]
            }
        
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        ) or []
        
        sucursales = [{"id": r['id'], "nombre": r['nombre']} for r in result]
        
        # Agregar opción "Todas" al inicio
        sucursales.insert(0, {"id": "all", "nombre": "Todas las sucursales"})
        
        return {
            "servidor": server['name'],
            "system_type": server['system_type'],
            "sucursales": sucursales
        }
    except Exception as e:
        logging.error(f"Error obteniendo sucursales: {str(e)}")
        return {
            "servidor": server['name'],
            "sucursales": [{"id": "all", "nombre": server['name']}],
            "error": str(e)
        }



# ============================================================================
# ANÁLISIS DE VENTAS A PRECIOS CONSTANTES (Sin efecto inflación)
# ============================================================================

@api_router.get("/comercial/precios-constantes/{server_id}")
async def ventas_precios_constantes(
    server_id: str,
    periodo_actual: str = Query(..., description="Período actual: YYYY-MM o YYYY-MM,YYYY-MM"),
    periodo_base: str = Query(..., description="Período base para precios: YYYY-MM o YYYY-MM,YYYY-MM"),
    granularidad: str = Query(default="categoria", description="categoria, familia, producto"),
    sucursal: str = Query(default="all", description="ID de sucursal o 'all' para todas"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ventas valuando a precios constantes de un período base.
    Permite comparar ventas eliminando el efecto inflacionario.
    
    - periodo_actual: Mes(es) de ventas a analizar (ej: "2025-03" o "2025-01,2025-02,2025-03")
    - periodo_base: Período de donde tomar los precios de referencia (ej: "2024-03")
    - granularidad: Nivel de detalle (categoria, familia, producto)
    - sucursal: ID de la sucursal a filtrar o 'all' para todas
    
    Productos In/Out:
    - Nuevos (no existían en período base): Usan precio actual
    - Descontinuados (no existen en período actual): Usan último precio conocido
    """
    from datetime import datetime, timedelta
    import calendar
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        # Parsear períodos (pueden ser múltiples meses separados por coma)
        def parse_periodos(periodo_str):
            meses = [m.strip() for m in periodo_str.split(',')]
            fechas = []
            for mes in meses:
                year, month = mes.split('-')
                year, month = int(year), int(month)
                ultimo_dia = calendar.monthrange(year, month)[1]
                fechas.append({
                    'mes': mes,
                    'year': year,
                    'month': month,
                    'fecha_ini': f"{year}-{month:02d}-01",
                    'fecha_fin': f"{year}-{month:02d}-{ultimo_dia:02d}"
                })
            return fechas
        
        periodos_actual = parse_periodos(periodo_actual)
        periodos_base = parse_periodos(periodo_base)
        
        # Fechas consolidadas
        fecha_ini_actual = min(p['fecha_ini'] for p in periodos_actual)
        fecha_fin_actual = max(p['fecha_fin'] for p in periodos_actual)
        fecha_ini_base = min(p['fecha_ini'] for p in periodos_base)
        fecha_fin_base = max(p['fecha_fin'] for p in periodos_base)
        
        logging.info(f"Precios Constantes - Actual: {fecha_ini_actual} a {fecha_fin_actual}, Base: {fecha_ini_base} a {fecha_fin_base}")
        
        if server['system_type'] == 'SoftRestaurant':
            # Formato YYYYMMDD para SoftRestaurant
            f_ini_actual = fecha_ini_actual.replace('-', '')
            f_fin_actual = fecha_fin_actual.replace('-', '')
            f_ini_base = fecha_ini_base.replace('-', '')
            f_fin_base = fecha_fin_base.replace('-', '')
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            query_ventas_reales = f"""
SELECT SUM(cheques.total) as ventas_reales
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_actual} 00:00:00'
  AND turnos.apertura <= '{f_fin_actual} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            # Query para ventas del período ACTUAL con precios actuales
            # Agrupa por producto y calcula precio promedio
            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
            query_ventas_actual = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    'SoftRestaurant' as categoria,
    'Productos' as familia,
    SUM(cd.cantidad) as cantidad,
    SUM(cd.precio * cd.cantidad) as importe_actual,
    AVG(cd.precio) as precio_promedio_actual
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE t.apertura >= '{f_ini_actual} 00:00:00'
  AND t.apertura <= '{f_fin_actual} 23:59:59'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Query para precios del período BASE
            query_precios_base = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    AVG(cd.precio) as precio_promedio_base
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE t.apertura >= '{f_ini_base} 00:00:00'
  AND t.apertura <= '{f_fin_base} 23:59:59'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            # Esto distribuye propinas, impuestos, descuentos proporcionalmente
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            # Procesar resultados aplicando factor de ajuste
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                # Determinar precio a usar para valuación constante
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    # Producto nuevo - usar precio actual
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Buscar productos descontinuados (estaban en base pero no en actual)
            productos_actuales_ids = {str(v['producto_id']) for v in ventas_actual}
            for producto_id, precio_base in precios_base_dict.items():
                if producto_id not in productos_actuales_ids:
                    # Obtener info del producto descontinuado
                    query_info = f"SELECT TOP 1 descripcion FROM productos WHERE idproducto = {producto_id}"
                    info_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_info
                    )
                    nombre_producto = info_result[0]['descripcion'] if info_result else f'Producto {producto_id}'
                    
                    productos_detalle.append({
                        'producto_id': producto_id,
                        'producto': nombre_producto,
                        'categoria': 'Descontinuado',
                        'familia': '-',
                        'cantidad': 0,
                        'precio_actual': 0,
                        'precio_base': precio_base,
                        'importe_actual': 0,
                        'importe_constante': 0,
                        'efecto_precio': 0,
                        'variacion_precio_pct': 0,
                        'es_nuevo': False,
                        'es_descontinuado': True
                    })
            
            # Agrupar según granularidad
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            else:  # producto
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            # Calcular métricas resumen
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        elif server['system_type'] == 'MPRO':
            # Para MPRO - Las ventas están en la tabla 'venta' directamente
            # La sucursal está en la tabla 'sucursal' relacionada por Sc_Cve_Sucursal
            
            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
            filtro_sucursal = f"AND V.Sc_Cve_Sucursal = '{sucursal}'" if sucursal != 'all' else ""
            filtro_sucursal_ve = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'" if sucursal != 'all' else ""
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            query_ventas_reales_mpro = f"""
SELECT ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_reales
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fecha_ini_actual}'
  AND VE.Vn_Fecha <= '{fecha_fin_actual} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {filtro_sucursal_ve}
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales_mpro
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            query_ventas_actual = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    P.Pr_Descripcion as producto,
    ISNULL(S.Sc_Descripcion, 'Sin Sucursal') as categoria,
    'Productos' as familia,
    SUM(V.Vn_Cantidad_Control_1) as cantidad,
    SUM(V.Vn_Precio_Lista * V.Vn_Cantidad_Control_1) as importe_actual,
    AVG(V.Vn_Precio_Lista) as precio_promedio_actual
FROM venta V
INNER JOIN Producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
LEFT JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE V.Vn_Fecha >= '{fecha_ini_actual}'
  AND V.Vn_Fecha <= '{fecha_fin_actual} 23:59:59'
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto, P.Pr_Descripcion, S.Sc_Descripcion
"""
            
            query_precios_base = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    AVG(V.Vn_Precio_Lista) as precio_promedio_base
FROM venta V
WHERE V.Vn_Fecha >= '{fecha_ini_base}'
  AND V.Vn_Fecha <= '{fecha_fin_base} 23:59:59'
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Agrupar según granularidad (mismo código)
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            else:
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Sistema no soportado: {server['system_type']}")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en precios constantes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



# ============================================================================
# EXPLORADOR DE BASE DE DATOS - Ver tablas y estructuras
# ============================================================================

@api_router.get("/explorador/tablas/{server_id}")
async def listar_tablas(
    server_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todas las tablas de la base de datos del servidor.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    
    # Query para listar tablas (SQL Server)
    query = """
SELECT 
    TABLE_NAME as tabla,
    TABLE_TYPE as tipo
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME
"""
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return {
            "servidor": server['name'],
            "sistema": server['system_type'],
            "database": server['database'],
            "tablas": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/explorador/columnas/{server_id}/{tabla}")
async def listar_columnas(
    server_id: str,
    tabla: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista las columnas de una tabla específica.
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    
    query = f"""
SELECT 
    COLUMN_NAME as columna,
    DATA_TYPE as tipo,
    CHARACTER_MAXIMUM_LENGTH as longitud,
    IS_NULLABLE as nullable,
    COLUMN_DEFAULT as default_value
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla}'
ORDER BY ORDINAL_POSITION
"""
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return {
            "tabla": tabla,
            "servidor": server['name'],
            "columnas": result
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
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    
    query = f"""
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
WHERE tp.name = '{tabla}' OR tr.name = '{tabla}'
ORDER BY fk.name
"""
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return {
            "tabla": tabla,
            "servidor": server['name'],
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
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    
    # Sanitizar nombre de tabla para evitar SQL injection
    if not tabla.replace('_', '').isalnum():
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")
    
    query = f"SELECT TOP {limite} * FROM [{tabla}]"
    
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return {
            "tabla": tabla,
            "servidor": server['name'],
            "registros": len(result),
            "datos": result
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
    """
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar queries libres")
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    query = body.get('query', '').strip()
    
    # Validar que sea solo SELECT
    if not query.upper().startswith('SELECT'):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT")
    
    # Bloquear palabras peligrosas
    palabras_prohibidas = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC']
    for palabra in palabras_prohibidas:
        if palabra in query.upper():
            raise HTTPException(status_code=400, detail=f"Query contiene operación prohibida: {palabra}")
    
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        )
        return {
            "servidor": server['name'],
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
    SOLO ADMINISTRADORES - USAR CON PRECAUCIÓN.
    Ejecuta cada statement por separado y devuelve el resultado de cada uno.
    """
    # Verificar que sea admin
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar scripts SQL")
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    script = body.get('script', '').strip()
    titulo = body.get('titulo', '').strip() or 'Script sin título'
    
    if not script:
        raise HTTPException(status_code=400, detail="El script está vacío")
    
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
    
    logging.info(f"[SCRIPT SQL] Usuario {current_user.get('email')} ejecutando {len(statements)} comandos en {server['name']}")
    
    resultados = []
    exitosos = 0
    fallidos = 0
    
    # Ejecutar cada statement
    import pytds
    
    try:
        # Parsear host y puerto
        host_str = server['host']
        port = server.get('port', 1433)
        
        if ',' in host_str:
            parts = host_str.split(',')
            host = parts[0].strip()
            try:
                port = int(parts[1].strip().split('\\')[0])
            except:
                pass
            if '\\' in host_str:
                host = host_str.split(',')[0].strip()
        else:
            host = host_str
        
        with pytds.connect(
            server=host,
            port=port,
            database=server['database'],
            user=server['username'],
            password=server['password'],
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
                        except:
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
        "server_name": server['name'],
        "titulo": titulo,
        "usuario": current_user.get('email'),
        "fecha": datetime.now(timezone.utc),
        "total_statements": len(statements),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados
    })
    
    return {
        "servidor": server['name'],
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
                except:
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
    """Helper para ejecutar queries en EDARSA HUB"""
    server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor EDARSA HUB no configurado")
    
    try:
        result = execute_sql_query(
            server['host'], 
            server['port'], 
            server['database'], 
            server['username'], 
            server['password'], 
            query
        )
        return {"datos": result, "registros": len(result)}
    except Exception as e:
        logging.error(f"Error en query EDARSA HUB: {e}")
        raise HTTPException(status_code=500, detail=f"Error en consulta: {str(e)}")


# ------------ CATÁLOGOS ------------

@api_router.get("/rrhh/catalogos/puestos")
async def rrhh_listar_puestos(current_user: Dict = Depends(get_current_user)):
    """Lista catálogo de puestos desde RH_Cat_Puestos"""
    query = """
        SELECT 
            PuestoID,
            Descripcion,
            Departamento,
            Sueldo_Base_Seman_SBC
        FROM RH_Cat_Puestos
        ORDER BY Departamento, Descripcion
    """
    result = await execute_edarsa_hub_query(query)
    return {"puestos": result.get("datos", []), "total": result.get("registros", 0)}


@api_router.get("/rrhh/catalogos/sucursales")
async def rrhh_listar_sucursales(current_user: Dict = Depends(get_current_user)):
    """Lista catálogo de sucursales desde RH_Cat_Sucursales"""
    query = """
        SELECT 
            s.SucursalID,
            s.Nombre_Sucursal,
            s.Ciudad,
            s.Activa,
            sf.RFC,
            sf.RazonSocial
        FROM RH_Cat_Sucursales s
        LEFT JOIN RH_Cat_SucursalesFiscal sf ON s.SucursalID = sf.SucursalID AND sf.Activo = 1
        ORDER BY s.Nombre_Sucursal
    """
    result = await execute_edarsa_hub_query(query)
    return {"sucursales": result.get("datos", []), "total": result.get("registros", 0)}


# ------------ CATÁLOGOS CRUD (ADMIN ONLY) ------------

def check_admin_role(current_user: Dict):
    """Verifica que el usuario tenga rol de Administrador"""
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden realizar esta acción")


@api_router.post("/rrhh/catalogos/puestos")
async def rrhh_crear_puesto(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo puesto en el catálogo (Solo Administrador)"""
    check_admin_role(current_user)
    
    descripcion = body.get('descripcion', '').strip()
    departamento = body.get('departamento', '').strip()
    sueldo_base = body.get('sueldo_base', 0)
    nomipaq_id = body.get('nomipaq_id', '')  # ID para mapeo con NomiPAQ
    mpro_id = body.get('mpro_id', '')  # ID para mapeo con MPRO
    
    if not descripcion:
        raise HTTPException(status_code=400, detail="La descripción del puesto es requerida")
    
    query = f"""
        INSERT INTO RH_Cat_Puestos 
        (Descripcion, Departamento, Sueldo_Base_Seman_SBC, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
        OUTPUT INSERTED.PuestoID
        VALUES 
        ('{descripcion}', '{departamento}', {sueldo_base}, '{nomipaq_id}', '{mpro_id}', GETDATE(), '{current_user.get("email", "")}')
    """
    
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Puesto creado"}


@api_router.put("/rrhh/catalogos/puestos/{puesto_id}")
async def rrhh_actualizar_puesto(
    puesto_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un puesto existente (Solo Administrador)"""
    check_admin_role(current_user)
    
    updates = []
    if 'descripcion' in body:
        updates.append(f"Descripcion = '{body['descripcion']}'")
    if 'departamento' in body:
        updates.append(f"Departamento = '{body['departamento']}'")
    if 'sueldo_base' in body:
        updates.append(f"Sueldo_Base_Seman_SBC = {body['sueldo_base']}")
    if 'nomipaq_id' in body:
        updates.append(f"NomiPAQ_ID = '{body['nomipaq_id']}'")
    if 'mpro_id' in body:
        updates.append(f"MPRO_ID = '{body['mpro_id']}'")
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = f"""
        UPDATE RH_Cat_Puestos
        SET {', '.join(updates)}, Fecha_Modificacion = GETDATE()
        WHERE PuestoID = {puesto_id}
    """
    
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Puesto actualizado"}


@api_router.delete("/rrhh/catalogos/puestos/{puesto_id}")
async def rrhh_eliminar_puesto(
    puesto_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un puesto del catálogo (Solo Administrador)"""
    check_admin_role(current_user)
    
    # Verificar si hay colaboradores con este puesto
    query_check = f"SELECT COUNT(*) as total FROM RH_Colaboradores_Expediente WHERE PuestoID = {puesto_id}"
    result = await execute_edarsa_hub_query(query_check)
    if result.get('datos', [{}])[0].get('total', 0) > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: hay colaboradores asignados a este puesto")
    
    query = f"DELETE FROM RH_Cat_Puestos WHERE PuestoID = {puesto_id}"
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Puesto eliminado"}


# ------------ CATÁLOGO DE TIPOS DE INCIDENCIAS ------------

@api_router.get("/rrhh/catalogos/tipos-incidencias")
async def rrhh_listar_tipos_incidencias(current_user: Dict = Depends(get_current_user)):
    """Lista catálogo de tipos de incidencias"""
    query = """
        SELECT 
            TipoIncidenciaID,
            Codigo,
            Descripcion,
            Categoria,
            Afectacion,
            Calculo_Monto,
            Activo,
            NomiPAQ_ID,
            MPRO_ID
        FROM RH_Cat_Tipos_Incidencias
        WHERE Activo = 1
        ORDER BY Categoria, Descripcion
    """
    try:
        result = await execute_edarsa_hub_query(query)
        return {"tipos_incidencias": result.get("datos", []), "total": result.get("registros", 0)}
    except:
        # Si la tabla no existe, retornar tipos por defecto
        tipos_default = [
            {"TipoIncidenciaID": 1, "Codigo": "BON", "Descripcion": "Bono", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
            {"TipoIncidenciaID": 2, "Codigo": "HEX", "Descripcion": "Horas Extra", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
            {"TipoIncidenciaID": 3, "Codigo": "COM", "Descripcion": "Comisión", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
            {"TipoIncidenciaID": 4, "Codigo": "FAL", "Descripcion": "Falta", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
            {"TipoIncidenciaID": 5, "Codigo": "RET", "Descripcion": "Retardo", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
            {"TipoIncidenciaID": 6, "Codigo": "DES", "Descripcion": "Descuento", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
        ]
        return {"tipos_incidencias": tipos_default, "total": len(tipos_default), "nota": "Usando tipos por defecto - Ejecute script SQL"}


@api_router.post("/rrhh/catalogos/tipos-incidencias")
async def rrhh_crear_tipo_incidencia(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo tipo de incidencia (Solo Administrador)"""
    check_admin_role(current_user)
    
    codigo = body.get('codigo', '').strip().upper()
    descripcion = body.get('descripcion', '').strip()
    categoria = body.get('categoria', 'Descuento')  # Ingreso o Descuento
    afectacion = 1 if categoria == 'Ingreso' else -1
    calculo_monto = body.get('calculo_monto', 'Manual')  # Manual, Porcentaje, Formula
    nomipaq_id = body.get('nomipaq_id', '')
    mpro_id = body.get('mpro_id', '')
    
    if not codigo or not descripcion:
        raise HTTPException(status_code=400, detail="Código y descripción son requeridos")
    
    query = f"""
        INSERT INTO RH_Cat_Tipos_Incidencias 
        (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto, Activo, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
        VALUES 
        ('{codigo}', '{descripcion}', '{categoria}', {afectacion}, '{calculo_monto}', 1, '{nomipaq_id}', '{mpro_id}', GETDATE(), '{current_user.get("email", "")}')
    """
    
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Tipo de incidencia creado"}


@api_router.put("/rrhh/catalogos/tipos-incidencias/{tipo_id}")
async def rrhh_actualizar_tipo_incidencia(
    tipo_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un tipo de incidencia (Solo Administrador)"""
    check_admin_role(current_user)
    
    updates = []
    if 'codigo' in body:
        updates.append(f"Codigo = '{body['codigo'].upper()}'")
    if 'descripcion' in body:
        updates.append(f"Descripcion = '{body['descripcion']}'")
    if 'categoria' in body:
        updates.append(f"Categoria = '{body['categoria']}'")
        updates.append(f"Afectacion = {1 if body['categoria'] == 'Ingreso' else -1}")
    if 'calculo_monto' in body:
        updates.append(f"Calculo_Monto = '{body['calculo_monto']}'")
    if 'activo' in body:
        updates.append(f"Activo = {1 if body['activo'] else 0}")
    if 'nomipaq_id' in body:
        updates.append(f"NomiPAQ_ID = '{body['nomipaq_id']}'")
    if 'mpro_id' in body:
        updates.append(f"MPRO_ID = '{body['mpro_id']}'")
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = f"""
        UPDATE RH_Cat_Tipos_Incidencias
        SET {', '.join(updates)}, Fecha_Modificacion = GETDATE()
        WHERE TipoIncidenciaID = {tipo_id}
    """
    
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Tipo de incidencia actualizado"}


@api_router.delete("/rrhh/catalogos/tipos-incidencias/{tipo_id}")
async def rrhh_eliminar_tipo_incidencia(
    tipo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Desactiva un tipo de incidencia (Solo Administrador) - No elimina para mantener histórico"""
    check_admin_role(current_user)
    
    query = f"UPDATE RH_Cat_Tipos_Incidencias SET Activo = 0, Fecha_Modificacion = GETDATE() WHERE TipoIncidenciaID = {tipo_id}"
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Tipo de incidencia desactivado"}


# ------------ SCRIPT INICIALIZACIÓN CATÁLOGOS RRHH ------------

@api_router.get("/rrhh/catalogos/script-inicializacion")
async def rrhh_catalogos_script(current_user: Dict = Depends(get_current_user)):
    """Retorna el script SQL para crear/actualizar las tablas de catálogos RRHH"""
    
    script = """
-- ============================================
-- SCRIPT DE INICIALIZACIÓN - CATÁLOGOS RRHH
-- Compatible con: NomiPAQ, MPRO, Excel
-- Base de datos: EDARSA HUB
-- ============================================

-- ========== MODIFICAR TABLA PUESTOS ==========
-- Agregar columnas de mapeo si no existen
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'NomiPAQ_ID')
BEGIN
    ALTER TABLE RH_Cat_Puestos ADD NomiPAQ_ID NVARCHAR(50) NULL;
    PRINT 'Columna NomiPAQ_ID agregada a RH_Cat_Puestos';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'MPRO_ID')
BEGIN
    ALTER TABLE RH_Cat_Puestos ADD MPRO_ID NVARCHAR(50) NULL;
    PRINT 'Columna MPRO_ID agregada a RH_Cat_Puestos';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'Fecha_Creacion')
BEGIN
    ALTER TABLE RH_Cat_Puestos ADD Fecha_Creacion DATETIME DEFAULT GETDATE();
    ALTER TABLE RH_Cat_Puestos ADD Fecha_Modificacion DATETIME NULL;
    ALTER TABLE RH_Cat_Puestos ADD Creado_Por NVARCHAR(100) NULL;
    PRINT 'Columnas de auditoría agregadas a RH_Cat_Puestos';
END
GO

-- ========== TABLA TIPOS DE INCIDENCIAS ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Cat_Tipos_Incidencias' AND xtype='U')
BEGIN
    CREATE TABLE RH_Cat_Tipos_Incidencias (
        TipoIncidenciaID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(10) NOT NULL UNIQUE,
        Descripcion NVARCHAR(100) NOT NULL,
        Categoria NVARCHAR(20) NOT NULL CHECK (Categoria IN ('Ingreso', 'Descuento')),
        Afectacion INT NOT NULL DEFAULT -1,  -- 1 = suma, -1 = resta
        Calculo_Monto NVARCHAR(20) DEFAULT 'Manual',  -- Manual, Porcentaje, Formula
        Formula NVARCHAR(500) NULL,  -- Fórmula personalizada si aplica
        Activo BIT DEFAULT 1,
        
        -- Mapeo con sistemas externos
        NomiPAQ_ID NVARCHAR(50) NULL,  -- ID en NomiPAQ
        NomiPAQ_Tipo NVARCHAR(50) NULL,  -- Tipo de concepto en NomiPAQ
        MPRO_ID NVARCHAR(50) NULL,  -- ID en MPRO
        Excel_Columna NVARCHAR(50) NULL,  -- Nombre de columna en Excel
        
        -- Auditoría
        Fecha_Creacion DATETIME DEFAULT GETDATE(),
        Fecha_Modificacion DATETIME NULL,
        Creado_Por NVARCHAR(100) NULL
    );
    
    CREATE INDEX IX_TiposIncidencias_Categoria ON RH_Cat_Tipos_Incidencias(Categoria);
    CREATE INDEX IX_TiposIncidencias_Activo ON RH_Cat_Tipos_Incidencias(Activo);
    
    PRINT 'Tabla RH_Cat_Tipos_Incidencias creada exitosamente';
END
GO

-- ========== INSERTAR TIPOS DE INCIDENCIAS POR DEFECTO ==========
IF NOT EXISTS (SELECT 1 FROM RH_Cat_Tipos_Incidencias)
BEGIN
    -- INGRESOS (+)
    INSERT INTO RH_Cat_Tipos_Incidencias (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto) VALUES
    ('BON', 'Bono', 'Ingreso', 1, 'Manual'),
    ('HEX', 'Horas Extra', 'Ingreso', 1, 'Formula'),
    ('COM', 'Comisión', 'Ingreso', 1, 'Porcentaje'),
    ('INC', 'Incentivo', 'Ingreso', 1, 'Manual'),
    ('GRA', 'Gratificación', 'Ingreso', 1, 'Manual'),
    ('AGU', 'Aguinaldo', 'Ingreso', 1, 'Formula'),
    ('PTU', 'PTU', 'Ingreso', 1, 'Formula'),
    ('PVA', 'Prima Vacacional', 'Ingreso', 1, 'Formula');
    
    -- DESCUENTOS (-)
    INSERT INTO RH_Cat_Tipos_Incidencias (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto) VALUES
    ('FAL', 'Falta', 'Descuento', -1, 'Formula'),
    ('RET', 'Retardo', 'Descuento', -1, 'Manual'),
    ('DES', 'Descuento General', 'Descuento', -1, 'Manual'),
    ('VAC', 'Vacaciones', 'Descuento', -1, 'Formula'),
    ('INA', 'Incapacidad', 'Descuento', -1, 'Formula'),
    ('PER', 'Permiso', 'Descuento', -1, 'Manual'),
    ('PRE', 'Préstamo', 'Descuento', -1, 'Manual'),
    ('INF', 'INFONAVIT', 'Descuento', -1, 'Porcentaje'),
    ('FON', 'FONACOT', 'Descuento', -1, 'Manual'),
    ('ISR', 'ISR', 'Descuento', -1, 'Formula'),
    ('IMSS', 'IMSS', 'Descuento', -1, 'Formula');
    
    PRINT 'Tipos de incidencias por defecto insertados';
END
GO

-- ========== MODIFICAR TABLA INCIDENCIAS NÓMINA ==========
-- Agregar columna para vincular con catálogo de tipos
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Incidencias_Nomina' AND COLUMN_NAME = 'TipoIncidenciaID')
BEGIN
    ALTER TABLE RH_Incidencias_Nomina ADD TipoIncidenciaID INT NULL;
    ALTER TABLE RH_Incidencias_Nomina ADD CONSTRAINT FK_Incidencia_Tipo 
        FOREIGN KEY (TipoIncidenciaID) REFERENCES RH_Cat_Tipos_Incidencias(TipoIncidenciaID);
    PRINT 'Columna TipoIncidenciaID agregada a RH_Incidencias_Nomina';
END

-- Agregar columnas de mapeo externo
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Incidencias_Nomina' AND COLUMN_NAME = 'Origen_Sistema')
BEGIN
    ALTER TABLE RH_Incidencias_Nomina ADD Origen_Sistema NVARCHAR(20) DEFAULT 'EDARSA_HUB';  -- EDARSA_HUB, NomiPAQ, MPRO, Excel
    ALTER TABLE RH_Incidencias_Nomina ADD Origen_ID NVARCHAR(50) NULL;  -- ID en sistema origen
    ALTER TABLE RH_Incidencias_Nomina ADD Fecha_Importacion DATETIME NULL;
    PRINT 'Columnas de origen agregadas a RH_Incidencias_Nomina';
END
GO

-- ========== TABLA DE MAPEO SISTEMAS EXTERNOS ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Mapeo_Sistemas' AND xtype='U')
BEGIN
    CREATE TABLE RH_Mapeo_Sistemas (
        MapeoID INT IDENTITY(1,1) PRIMARY KEY,
        Sistema_Origen NVARCHAR(20) NOT NULL,  -- NomiPAQ, MPRO, Excel
        Tabla_Origen NVARCHAR(100) NOT NULL,
        Campo_Origen NVARCHAR(100) NOT NULL,
        Tabla_Destino NVARCHAR(100) NOT NULL,  -- Tabla en EDARSA HUB
        Campo_Destino NVARCHAR(100) NOT NULL,
        Transformacion NVARCHAR(500) NULL,  -- SQL o fórmula de transformación
        Activo BIT DEFAULT 1,
        Fecha_Creacion DATETIME DEFAULT GETDATE()
    );
    
    PRINT 'Tabla RH_Mapeo_Sistemas creada para configurar importaciones';
END
GO

-- ========== INSERTAR MAPEOS POR DEFECTO PARA NOMIPAQ ==========
IF NOT EXISTS (SELECT 1 FROM RH_Mapeo_Sistemas WHERE Sistema_Origen = 'NomiPAQ')
BEGIN
    INSERT INTO RH_Mapeo_Sistemas (Sistema_Origen, Tabla_Origen, Campo_Origen, Tabla_Destino, Campo_Destino) VALUES
    ('NomiPAQ', 'nom10001', 'numtrab', 'RH_Colaboradores_Expediente', 'NomiPAQ_ID'),
    ('NomiPAQ', 'nom10001', 'nombre', 'RH_Colaboradores_Expediente', 'Nombre_Completo'),
    ('NomiPAQ', 'nom10001', 'rfc', 'RH_Colaboradores_Expediente', 'RFC'),
    ('NomiPAQ', 'nom10001', 'curp', 'RH_Colaboradores_Expediente', 'CURP'),
    ('NomiPAQ', 'nom10003', 'idconcepto', 'RH_Cat_Tipos_Incidencias', 'NomiPAQ_ID'),
    ('NomiPAQ', 'nom10007', 'idmovto', 'RH_Incidencias_Nomina', 'Origen_ID');
    
    PRINT 'Mapeos NomiPAQ insertados';
END
GO

PRINT '=== Script de catálogos RRHH completado ===';
PRINT 'Las tablas están listas para importar datos de NomiPAQ, MPRO o Excel';
"""
    
    return {
        "script": script,
        "instrucciones": [
            "1. Copia el script SQL completo",
            "2. Ve a 'Explorador BD' en el menú lateral",
            "3. Selecciona el servidor EDARSA HUB",
            "4. Ejecuta el script con credenciales de administrador",
            "5. Las tablas quedarán preparadas para:",
            "   - Gestionar catálogos de Puestos e Incidencias",
            "   - Importar datos desde NomiPAQ",
            "   - Importar datos desde MPRO",
            "   - Importar datos desde Excel",
            "   - Migrar a EDARSA HUB sin pérdida de datos"
        ],
        "compatibilidad": {
            "nomipaq": "Mapeo con nom10001 (empleados), nom10003 (conceptos), nom10007 (movimientos)",
            "mpro": "Campos MPRO_ID en todas las tablas para vincular registros",
            "excel": "Campo Excel_Columna para mapear columnas de importación"
        }
    }


# ------------ COLABORADORES ------------

@api_router.get("/rrhh/colaboradores")
async def rrhh_listar_colaboradores(
    sucursal_id: Optional[int] = None,
    puesto_id: Optional[int] = None,
    estatus: Optional[str] = None,
    buscar: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """Lista colaboradores con filtros opcionales"""
    
    conditions = ["1=1"]
    if sucursal_id:
        conditions.append(f"c.SucursalID = {sucursal_id}")
    if puesto_id:
        conditions.append(f"c.PuestoID = {puesto_id}")
    if estatus:
        conditions.append(f"c.Estatus_Laboral = '{estatus}'")
    if buscar:
        conditions.append(f"(c.Nombre_Completo LIKE '%{buscar}%' OR c.RFC LIKE '%{buscar}%' OR c.CURP LIKE '%{buscar}%')")
    
    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit
    
    query = f"""
        SELECT 
            c.ColaboradorID,
            c.Nombre_Completo,
            c.CURP,
            c.RFC,
            c.CLABE_Bancaria,
            c.SucursalID,
            s.Nombre_Sucursal,
            c.PuestoID,
            p.Descripcion as Puesto,
            p.Departamento,
            c.Colaborador_Activo,
            c.Fecha_Alta,
            c.Estatus_Laboral,
            c.Validacion_IA_RFC,
            c.Validacion_IA_CURP,
            c.Validacion_IA_EdoCta,
            c.Validacion_IA_Contrato
        FROM RH_Colaboradores_Expediente c
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE {where_clause}
        ORDER BY c.Nombre_Completo
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    count_query = f"""
        SELECT COUNT(*) as total
        FROM RH_Colaboradores_Expediente c
        WHERE {where_clause}
    """
    
    result = await execute_edarsa_hub_query(query)
    count_result = await execute_edarsa_hub_query(count_query)
    
    total = count_result.get("datos", [{}])[0].get("total", 0) if count_result.get("datos") else 0
    
    return {
        "colaboradores": result.get("datos", []),
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }


@api_router.get("/rrhh/colaboradores/{colaborador_id}")
async def rrhh_obtener_colaborador(
    colaborador_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene detalle de un colaborador con incidencias y asistencias"""
    
    query_colaborador = f"""
        SELECT 
            c.ColaboradorID,
            c.Nombre_Completo,
            c.CURP,
            c.RFC,
            c.CLABE_Bancaria,
            c.SucursalID,
            s.Nombre_Sucursal,
            s.Ciudad,
            c.PuestoID,
            p.Descripcion as Puesto,
            p.Departamento,
            p.Sueldo_Base_Seman_SBC,
            c.Colaborador_Activo,
            c.Fecha_Alta,
            c.Estatus_Laboral,
            c.Validacion_IA_RFC,
            c.Validacion_IA_CURP,
            c.Validacion_IA_EdoCta,
            c.Validacion_IA_Contrato
        FROM RH_Colaboradores_Expediente c
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE c.ColaboradorID = {colaborador_id}
    """
    
    query_incidencias = f"""
        SELECT TOP 20
            IncidenciaID,
            Tipo_Incidencia,
            Monto,
            Unidades,
            Fecha_Incidencia,
            Fecha_Registro
        FROM RH_Incidencias_Nomina
        WHERE ColaboradorID = {colaborador_id}
        ORDER BY Fecha_Incidencia DESC
    """
    
    query_asistencias = f"""
        SELECT TOP 30
            CheckID,
            Tipo_Registro,
            FechaHora,
            Geolocalizacion,
            Validado_Gerencia
        FROM RH_Reloj_Checador
        WHERE ColaboradorID = {colaborador_id}
        ORDER BY FechaHora DESC
    """
    
    query_auditoria = f"""
        SELECT TOP 10
            AuditoriaID,
            Semana,
            Monto_Dispersado_Banco,
            Monto_Timbrado_XML,
            Monto_IMSS_EBA_EMA,
            Diferencia,
            Alerta_Fraude
        FROM RH_Auditoria_Fiscal
        WHERE ColaboradorID = {colaborador_id}
        ORDER BY Semana DESC
    """
    
    result_col = await execute_edarsa_hub_query(query_colaborador)
    result_inc = await execute_edarsa_hub_query(query_incidencias)
    result_asis = await execute_edarsa_hub_query(query_asistencias)
    result_aud = await execute_edarsa_hub_query(query_auditoria)
    
    if not result_col.get("datos"):
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")
    
    return {
        "colaborador": result_col.get("datos", [])[0],
        "incidencias": result_inc.get("datos", []),
        "asistencias": result_asis.get("datos", []),
        "auditoria_fiscal": result_aud.get("datos", [])
    }


@api_router.post("/rrhh/colaboradores")
async def rrhh_crear_colaborador(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo colaborador"""
    
    nombre = body.get('nombre_completo', '').strip()
    curp = body.get('curp')
    rfc = body.get('rfc')
    clabe = body.get('clabe_bancaria')
    sucursal_id = body.get('sucursal_id')
    puesto_id = body.get('puesto_id')
    estatus = body.get('estatus_laboral', 'Activo')
    
    if not nombre or not sucursal_id or not puesto_id:
        raise HTTPException(status_code=400, detail="Nombre, sucursal y puesto son requeridos")
    
    query = f"""
        INSERT INTO RH_Colaboradores_Expediente 
        (Nombre_Completo, CURP, RFC, CLABE_Bancaria, SucursalID, PuestoID, 
         Colaborador_Activo, Fecha_Alta, Estatus_Laboral)
        OUTPUT INSERTED.ColaboradorID
        VALUES 
        ('{nombre}', 
         {f"'{curp}'" if curp else 'NULL'}, 
         {f"'{rfc}'" if rfc else 'NULL'}, 
         {f"'{clabe}'" if clabe else 'NULL'}, 
         {sucursal_id}, 
         {puesto_id}, 
         1, 
         GETDATE(), 
         '{estatus}')
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "success": True,
        "message": "Colaborador creado exitosamente",
        "colaborador_id": result.get("datos", [{}])[0].get("ColaboradorID") if result.get("datos") else None
    }


@api_router.put("/rrhh/colaboradores/{colaborador_id}")
async def rrhh_actualizar_colaborador(
    colaborador_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza datos de un colaborador"""
    
    updates = []
    if body.get('nombre_completo'):
        updates.append(f"Nombre_Completo = '{body['nombre_completo']}'")
    if 'curp' in body:
        updates.append(f"CURP = '{body['curp']}'" if body['curp'] else "CURP = NULL")
    if 'rfc' in body:
        updates.append(f"RFC = '{body['rfc']}'" if body['rfc'] else "RFC = NULL")
    if 'clabe_bancaria' in body:
        updates.append(f"CLABE_Bancaria = '{body['clabe_bancaria']}'" if body['clabe_bancaria'] else "CLABE_Bancaria = NULL")
    if body.get('sucursal_id'):
        updates.append(f"SucursalID = {body['sucursal_id']}")
    if body.get('puesto_id'):
        updates.append(f"PuestoID = {body['puesto_id']}")
    if body.get('estatus_laboral'):
        updates.append(f"Estatus_Laboral = '{body['estatus_laboral']}'")
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    
    query = f"""
        UPDATE RH_Colaboradores_Expediente
        SET {', '.join(updates)}
        WHERE ColaboradorID = {colaborador_id}
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Colaborador actualizado"}


@api_router.delete("/rrhh/colaboradores/{colaborador_id}")
async def rrhh_dar_baja_colaborador(
    colaborador_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Da de baja lógica a un colaborador"""
    
    query = f"""
        UPDATE RH_Colaboradores_Expediente
        SET Colaborador_Activo = 0, Estatus_Laboral = 'Baja'
        WHERE ColaboradorID = {colaborador_id}
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Colaborador dado de baja"}


# ------------ INCIDENCIAS ------------

@api_router.get("/rrhh/incidencias")
async def rrhh_listar_incidencias(
    colaborador_id: Optional[int] = None,
    tipo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """Lista incidencias con filtros"""
    
    conditions = ["1=1"]
    if colaborador_id:
        conditions.append(f"i.ColaboradorID = {colaborador_id}")
    if tipo:
        conditions.append(f"i.Tipo_Incidencia = '{tipo}'")
    if fecha_desde:
        conditions.append(f"i.Fecha_Incidencia >= '{fecha_desde}'")
    if fecha_hasta:
        conditions.append(f"i.Fecha_Incidencia <= '{fecha_hasta}'")
    if sucursal_id:
        conditions.append(f"c.SucursalID = {sucursal_id}")
    
    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit
    
    query = f"""
        SELECT 
            i.IncidenciaID,
            i.ColaboradorID,
            c.Nombre_Completo,
            c.SucursalID,
            s.Nombre_Sucursal,
            i.Tipo_Incidencia,
            i.Monto,
            i.Unidades,
            i.Fecha_Incidencia,
            i.Capturado_Por,
            i.Fecha_Registro
        FROM RH_Incidencias_Nomina i
        LEFT JOIN RH_Colaboradores_Expediente c ON i.ColaboradorID = c.ColaboradorID
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY i.Fecha_Incidencia DESC
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "incidencias": result.get("datos", []),
        "total": result.get("registros", 0),
        "page": page,
        "limit": limit
    }


@api_router.post("/rrhh/incidencias")
async def rrhh_crear_incidencia(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una nueva incidencia"""
    
    colaborador_id = body.get('colaborador_id')
    tipo = body.get('tipo_incidencia')
    monto = body.get('monto', 0)
    unidades = body.get('unidades', 0)
    fecha = body.get('fecha_incidencia')
    
    if not colaborador_id or not tipo or not fecha:
        raise HTTPException(status_code=400, detail="Colaborador, tipo y fecha son requeridos")
    
    query = f"""
        INSERT INTO RH_Incidencias_Nomina 
        (ColaboradorID, Tipo_Incidencia, Monto, Unidades, Fecha_Incidencia, Fecha_Registro)
        OUTPUT INSERTED.IncidenciaID
        VALUES 
        ({colaborador_id}, '{tipo}', {monto}, {unidades}, '{fecha}', GETDATE())
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "success": True,
        "message": "Incidencia registrada",
        "incidencia_id": result.get("datos", [{}])[0].get("IncidenciaID") if result.get("datos") else None
    }


@api_router.post("/rrhh/incidencias/importar-excel")
async def rrhh_importar_incidencias_excel(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Importa incidencias de nómina desde un archivo Excel.
    
    Formato esperado del Excel:
    - Columna A: RFC o ColaboradorID
    - Columna B: Tipo de Incidencia (Falta, Retardo, Bono, Descuento, Horas Extra, Vacaciones, Incapacidad, Permiso, Comision, Otro)
    - Columna C: Fecha (YYYY-MM-DD o DD/MM/YYYY)
    - Columna D: Monto (opcional)
    - Columna E: Unidades (opcional)
    """
    import openpyxl
    from io import BytesIO
    from datetime import datetime
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos Excel (.xlsx, .xls)")
    
    try:
        contents = await file.read()
        wb = openpyxl.load_workbook(BytesIO(contents))
        ws = wb.active
        
        # Obtener mapeo de RFC -> ColaboradorID
        query_colaboradores = """
            SELECT ColaboradorID, RFC, Nombre_Completo 
            FROM RH_Colaboradores_Expediente 
            WHERE Colaborador_Activo = 1
        """
        result_col = await execute_edarsa_hub_query(query_colaboradores)
        colaboradores_map = {}
        for c in result_col.get("datos", []):
            if c.get("RFC"):
                colaboradores_map[c["RFC"].strip().upper()] = c["ColaboradorID"]
            colaboradores_map[str(c["ColaboradorID"])] = c["ColaboradorID"]
        
        tipos_validos = ['Falta', 'Retardo', 'Bono', 'Descuento', 'Horas Extra', 
                        'Vacaciones', 'Incapacidad', 'Permiso', 'Comision', 'Otro']
        
        registros_importados = 0
        errores = []
        
        # Leer filas (empezando en la 2 para saltar encabezado)
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row or not row[0]:  # Fila vacía
                continue
            
            try:
                # Columna A: RFC o ID
                identificador = str(row[0]).strip().upper()
                colaborador_id = colaboradores_map.get(identificador)
                
                if not colaborador_id:
                    errores.append(f"Fila {row_idx}: Colaborador '{row[0]}' no encontrado")
                    continue
                
                # Columna B: Tipo
                tipo = str(row[1]).strip() if row[1] else None
                if not tipo or tipo not in tipos_validos:
                    errores.append(f"Fila {row_idx}: Tipo de incidencia inválido '{tipo}'")
                    continue
                
                # Columna C: Fecha
                fecha_raw = row[2]
                if isinstance(fecha_raw, datetime):
                    fecha = fecha_raw.strftime('%Y-%m-%d')
                elif fecha_raw:
                    # Intentar parsear diferentes formatos
                    fecha_str = str(fecha_raw).strip()
                    try:
                        if '/' in fecha_str:
                            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                        else:
                            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                    except:
                        errores.append(f"Fila {row_idx}: Formato de fecha inválido '{fecha_raw}'")
                        continue
                else:
                    errores.append(f"Fila {row_idx}: Fecha requerida")
                    continue
                
                # Columna D: Monto (opcional)
                monto = float(row[3]) if row[3] and len(row) > 3 else 0
                
                # Columna E: Unidades (opcional)
                unidades = float(row[4]) if len(row) > 4 and row[4] else 0
                
                # Insertar incidencia
                query_insert = f"""
                    INSERT INTO RH_Incidencias_Nomina 
                    (ColaboradorID, Tipo_Incidencia, Monto, Unidades, Fecha_Incidencia, Fecha_Registro)
                    VALUES 
                    ({colaborador_id}, '{tipo}', {monto}, {unidades}, '{fecha}', GETDATE())
                """
                await execute_edarsa_hub_query(query_insert)
                registros_importados += 1
                
            except Exception as e:
                errores.append(f"Fila {row_idx}: Error - {str(e)}")
        
        return {
            "success": True,
            "registros_importados": registros_importados,
            "errores": errores[:20],  # Limitar a 20 errores
            "total_errores": len(errores)
        }
        
    except Exception as e:
        logging.error(f"Error importando Excel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


@api_router.get("/rrhh/incidencias/plantilla-excel")
async def rrhh_descargar_plantilla_excel(
    current_user: Dict = Depends(get_current_user)
):
    """Genera y descarga una plantilla Excel para importar incidencias"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Incidencias"
    
    # Encabezados
    headers = ["RFC/ID Colaborador", "Tipo Incidencia", "Fecha (DD/MM/YYYY)", "Monto", "Unidades"]
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Ejemplos
    ejemplos = [
        ["XAXX010101000", "Falta", "01/04/2026", 0, 1],
        ["XAXX010101001", "Bono", "01/04/2026", 500, 0],
        ["XAXX010101002", "Horas Extra", "01/04/2026", 150, 2],
    ]
    
    for row_idx, ejemplo in enumerate(ejemplos, 2):
        for col_idx, value in enumerate(ejemplo, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    
    # Hoja de tipos válidos
    ws2 = wb.create_sheet(title="Tipos Válidos")
    ws2.cell(row=1, column=1, value="Tipos de Incidencia Válidos")
    ws2.cell(row=1, column=1).font = Font(bold=True)
    
    tipos = ['Falta', 'Retardo', 'Bono', 'Descuento', 'Horas Extra', 
             'Vacaciones', 'Incapacidad', 'Permiso', 'Comision', 'Otro']
    for i, tipo in enumerate(tipos, 2):
        ws2.cell(row=i, column=1, value=tipo)
    
    # Guardar en memoria
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_incidencias.xlsx"}
    )


# ------------ ASISTENCIA (RELOJ CHECADOR) ------------

@api_router.get("/rrhh/asistencia")
async def rrhh_listar_asistencias(
    colaborador_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    fecha: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Lista registros del reloj checador"""
    
    conditions = ["1=1"]
    if colaborador_id:
        conditions.append(f"r.ColaboradorID = {colaborador_id}")
    if sucursal_id:
        conditions.append(f"c.SucursalID = {sucursal_id}")
    if fecha:
        conditions.append(f"CAST(r.FechaHora AS DATE) = '{fecha}'")
    if fecha_desde:
        conditions.append(f"CAST(r.FechaHora AS DATE) >= '{fecha_desde}'")
    if fecha_hasta:
        conditions.append(f"CAST(r.FechaHora AS DATE) <= '{fecha_hasta}'")
    
    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit
    
    query = f"""
        SELECT 
            r.CheckID,
            r.ColaboradorID,
            c.Nombre_Completo,
            c.SucursalID,
            s.Nombre_Sucursal,
            p.Descripcion as Puesto,
            r.Tipo_Registro,
            r.FechaHora,
            r.Geolocalizacion,
            r.Validado_Gerencia
        FROM RH_Reloj_Checador r
        LEFT JOIN RH_Colaboradores_Expediente c ON r.ColaboradorID = c.ColaboradorID
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE {where_clause}
        ORDER BY r.FechaHora DESC
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "asistencias": result.get("datos", []),
        "total": result.get("registros", 0),
        "page": page,
        "limit": limit
    }


@api_router.post("/rrhh/asistencia")
async def rrhh_registrar_asistencia(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Registra una entrada o salida"""
    
    colaborador_id = body.get('colaborador_id')
    tipo = body.get('tipo_registro')  # "Entrada" o "Salida"
    geo = body.get('geolocalizacion')
    
    if not colaborador_id or not tipo:
        raise HTTPException(status_code=400, detail="Colaborador y tipo son requeridos")
    
    query = f"""
        INSERT INTO RH_Reloj_Checador 
        (ColaboradorID, Tipo_Registro, FechaHora, Geolocalizacion, Validado_Gerencia)
        OUTPUT INSERTED.CheckID
        VALUES 
        ({colaborador_id}, '{tipo}', GETDATE(), {f"'{geo}'" if geo else 'NULL'}, 0)
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "success": True,
        "message": "Asistencia registrada",
        "check_id": result.get("datos", [{}])[0].get("CheckID") if result.get("datos") else None
    }


@api_router.put("/rrhh/asistencia/{check_id}/validar")
async def rrhh_validar_asistencia(
    check_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Valida un registro de asistencia (gerencia)"""
    
    query = f"""
        UPDATE RH_Reloj_Checador
        SET Validado_Gerencia = 1
        WHERE CheckID = {check_id}
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Asistencia validada"}


# ------------ FLUJO DE NÓMINA ------------

@api_router.get("/rrhh/nominas/flujo")
async def rrhh_listar_flujos_nomina(
    sucursal_id: Optional[int] = None,
    semana_anio: Optional[int] = None,
    estatus: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista flujos de nómina por sucursal"""
    
    conditions = ["1=1"]
    if sucursal_id:
        conditions.append(f"f.SucursalID = {sucursal_id}")
    if semana_anio:
        conditions.append(f"f.Semana_Anio = {semana_anio}")
    if estatus:
        conditions.append(f"f.Estatus_Flujo = '{estatus}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            f.FlujoID,
            f.SucursalID,
            s.Nombre_Sucursal,
            f.Semana_Anio,
            f.Estatus_Flujo,
            f.Hora_Entrega_RH,
            f.Hora_Validacion_Gerente,
            f.Hora_Autorizacion_DG,
            f.Hora_Envio_Tesoreria,
            f.Hora_Pago_Ejecutado,
            f.Motivo_Rechazo_Gerente,
            f.Intentos_Reenvio
        FROM RH_Flujo_Nomina_Sucursal f
        LEFT JOIN RH_Cat_Sucursales s ON f.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY f.Semana_Anio DESC, s.Nombre_Sucursal
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "flujos": result.get("datos", []),
        "total": result.get("registros", 0)
    }


@api_router.post("/rrhh/nominas/flujo")
async def rrhh_crear_flujo_nomina(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo periodo de nómina para una sucursal"""
    
    sucursal_id = body.get('sucursal_id')
    semana_anio = body.get('semana_anio')  # Formato: 202614 (año + semana)
    
    if not sucursal_id or not semana_anio:
        raise HTTPException(status_code=400, detail="Sucursal y semana son requeridos")
    
    # Verificar si ya existe
    check_query = f"""
        SELECT FlujoID FROM RH_Flujo_Nomina_Sucursal 
        WHERE SucursalID = {sucursal_id} AND Semana_Anio = {semana_anio}
    """
    existing = await execute_edarsa_hub_query(check_query)
    
    if existing.get("datos"):
        raise HTTPException(status_code=400, detail="Ya existe un flujo para esta sucursal y semana")
    
    query = f"""
        INSERT INTO RH_Flujo_Nomina_Sucursal 
        (SucursalID, Semana_Anio, Estatus_Flujo, Intentos_Reenvio)
        OUTPUT INSERTED.FlujoID
        VALUES 
        ({sucursal_id}, {semana_anio}, 'Captura', 0)
    """
    
    result = await execute_edarsa_hub_query(query)
    
    return {
        "success": True,
        "message": "Flujo de nómina creado",
        "flujo_id": result.get("datos", [{}])[0].get("FlujoID") if result.get("datos") else None
    }


@api_router.put("/rrhh/nominas/flujo/{flujo_id}/enviar-rh")
async def rrhh_enviar_nomina_rh(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Marca la nómina como enviada a RH"""
    query = f"""
        UPDATE RH_Flujo_Nomina_Sucursal
        SET Estatus_Flujo = 'Enviado_RH', Hora_Entrega_RH = GETDATE()
        WHERE FlujoID = {flujo_id}
    """
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Nómina enviada a RH"}


@api_router.put("/rrhh/nominas/flujo/{flujo_id}/validar-gerente")
async def rrhh_validar_nomina_gerente(
    flujo_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Validación de nómina por gerente"""
    aprobado = body.get('aprobado', True)
    motivo = body.get('motivo_rechazo', '')
    
    if aprobado:
        query = f"""
            UPDATE RH_Flujo_Nomina_Sucursal
            SET Estatus_Flujo = 'Validacion_Gerente', 
                Hora_Validacion_Gerente = GETDATE(),
                Motivo_Rechazo_Gerente = NULL
            WHERE FlujoID = {flujo_id}
        """
    else:
        query = f"""
            UPDATE RH_Flujo_Nomina_Sucursal
            SET Estatus_Flujo = 'Rechazado_Gerente', 
                Motivo_Rechazo_Gerente = '{motivo or "Sin especificar"}',
                Intentos_Reenvio = Intentos_Reenvio + 1
            WHERE FlujoID = {flujo_id}
        """
    
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Nómina validada" if aprobado else "Nómina rechazada"}


@api_router.put("/rrhh/nominas/flujo/{flujo_id}/autorizar-dg")
async def rrhh_autorizar_nomina_dg(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Autorización de nómina por Dirección General"""
    query = f"""
        UPDATE RH_Flujo_Nomina_Sucursal
        SET Estatus_Flujo = 'Autorizacion_DG', Hora_Autorizacion_DG = GETDATE()
        WHERE FlujoID = {flujo_id}
    """
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Nómina autorizada por DG"}


@api_router.put("/rrhh/nominas/flujo/{flujo_id}/enviar-tesoreria")
async def rrhh_enviar_nomina_tesoreria(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Envía nómina a tesorería para pago"""
    query = f"""
        UPDATE RH_Flujo_Nomina_Sucursal
        SET Estatus_Flujo = 'Enviado_Tesoreria', Hora_Envio_Tesoreria = GETDATE()
        WHERE FlujoID = {flujo_id}
    """
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Nómina enviada a tesorería"}


@api_router.put("/rrhh/nominas/flujo/{flujo_id}/marcar-pagado")
async def rrhh_marcar_nomina_pagada(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Marca la nómina como pagada"""
    query = f"""
        UPDATE RH_Flujo_Nomina_Sucursal
        SET Estatus_Flujo = 'Pagado', Hora_Pago_Ejecutado = GETDATE()
        WHERE FlujoID = {flujo_id}
    """
    await execute_edarsa_hub_query(query)
    return {"success": True, "message": "Nómina marcada como pagada"}


# ------------ AUDITORÍA FISCAL ------------

@api_router.get("/rrhh/auditoria-fiscal")
async def rrhh_listar_auditoria_fiscal(
    colaborador_id: Optional[int] = None,
    semana: Optional[int] = None,
    solo_alertas: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """Lista auditoría fiscal de nóminas"""
    
    conditions = ["1=1"]
    if colaborador_id:
        conditions.append(f"a.ColaboradorID = {colaborador_id}")
    if semana:
        conditions.append(f"a.Semana = {semana}")
    if solo_alertas:
        conditions.append("a.Alerta_Fraude = 1")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            a.AuditoriaID,
            a.ColaboradorID,
            c.Nombre_Completo,
            c.RFC,
            s.Nombre_Sucursal,
            a.Semana,
            a.Monto_Dispersado_Banco,
            a.Monto_Timbrado_XML,
            a.Monto_IMSS_EBA_EMA,
            a.Diferencia,
            a.Alerta_Fraude
        FROM RH_Auditoria_Fiscal a
        LEFT JOIN RH_Colaboradores_Expediente c ON a.ColaboradorID = c.ColaboradorID
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY a.Alerta_Fraude DESC, a.Semana DESC
    """
    
    result = await execute_edarsa_hub_query(query)
    alertas = sum(1 for r in result.get("datos", []) if r.get("Alerta_Fraude") == 1)
    
    return {
        "auditoria": result.get("datos", []),
        "total": result.get("registros", 0),
        "total_alertas": alertas
    }


# ------------ DASHBOARD RRHH ------------

@api_router.get("/rrhh/dashboard")
async def rrhh_dashboard(
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Dashboard con métricas de RRHH"""
    
    suc_filter = f"AND SucursalID = {sucursal_id}" if sucursal_id else ""
    suc_filter_c = f"AND c.SucursalID = {sucursal_id}" if sucursal_id else ""
    
    # Total colaboradores
    query_total = f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN Colaborador_Activo = 1 THEN 1 ELSE 0 END) as activos,
            SUM(CASE WHEN Estatus_Laboral = 'Vacaciones' THEN 1 ELSE 0 END) as vacaciones,
            SUM(CASE WHEN Estatus_Laboral = 'Incapacidad' THEN 1 ELSE 0 END) as incapacidad,
            SUM(CASE WHEN Colaborador_Activo = 0 THEN 1 ELSE 0 END) as bajas
        FROM RH_Colaboradores_Expediente
        WHERE 1=1 {suc_filter}
    """
    
    # Por departamento
    query_depto = f"""
        SELECT 
            ISNULL(p.Departamento, 'Sin asignar') as Departamento,
            COUNT(*) as total
        FROM RH_Colaboradores_Expediente c
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE c.Colaborador_Activo = 1 {suc_filter_c}
        GROUP BY p.Departamento
        ORDER BY total DESC
    """
    
    # Incidencias del mes
    query_incidencias = f"""
        SELECT 
            Tipo_Incidencia,
            COUNT(*) as cantidad,
            SUM(ISNULL(Monto, 0)) as monto_total
        FROM RH_Incidencias_Nomina i
        LEFT JOIN RH_Colaboradores_Expediente c ON i.ColaboradorID = c.ColaboradorID
        WHERE MONTH(Fecha_Incidencia) = MONTH(GETDATE()) 
          AND YEAR(Fecha_Incidencia) = YEAR(GETDATE())
          {suc_filter_c}
        GROUP BY Tipo_Incidencia
    """
    
    # Flujos pendientes
    query_flujos = f"""
        SELECT 
            Estatus_Flujo,
            COUNT(*) as cantidad
        FROM RH_Flujo_Nomina_Sucursal
        WHERE Estatus_Flujo NOT IN ('Pagado')
          {suc_filter}
        GROUP BY Estatus_Flujo
    """
    
    # Alertas fraude
    query_alertas = f"""
        SELECT COUNT(*) as alertas
        FROM RH_Auditoria_Fiscal a
        LEFT JOIN RH_Colaboradores_Expediente c ON a.ColaboradorID = c.ColaboradorID
        WHERE a.Alerta_Fraude = 1 {suc_filter_c}
    """
    
    result_total = await execute_edarsa_hub_query(query_total)
    result_depto = await execute_edarsa_hub_query(query_depto)
    result_incidencias = await execute_edarsa_hub_query(query_incidencias)
    result_flujos = await execute_edarsa_hub_query(query_flujos)
    result_alertas = await execute_edarsa_hub_query(query_alertas)
    
    return {
        "resumen": result_total.get("datos", [{}])[0] if result_total.get("datos") else {},
        "por_departamento": result_depto.get("datos", []),
        "incidencias_mes": result_incidencias.get("datos", []),
        "flujos_pendientes": result_flujos.get("datos", []),
        "alertas_fraude": result_alertas.get("datos", [{}])[0].get("alertas", 0) if result_alertas.get("datos") else 0
    }



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
    """
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden guardar scripts")
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
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
    
    # Guardar en MongoDB
    result = await db.scripts_pendientes.insert_one({
        "server_id": server_id,
        "server_name": server['name'],
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
    """
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar scripts")
    
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
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
            except:
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
                        except:
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
    
    except pytds.LoginError as e:
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
    
    suc_filter = f"AND p.SucursalID = {sucursal_id}" if sucursal_id else ""
    
    # Obtener presupuestos del periodo
    query_presupuestos = f"""
        SELECT 
            p.PresupuestoID,
            p.SucursalID,
            s.Nombre_Sucursal,
            p.Categoria,
            p.SubCategoria,
            p.Tipo,
            p.Monto_Presupuestado,
            p.Monto_Ejecutado,
            p.Anio,
            p.Mes,
            CASE 
                WHEN p.Monto_Presupuestado > 0 
                THEN ROUND((p.Monto_Ejecutado / p.Monto_Presupuestado) * 100, 2)
                ELSE 0 
            END as Porcentaje_Ejecucion
        FROM Finanzas_Presupuestos p
        LEFT JOIN RH_Cat_Sucursales s ON p.SucursalID = s.SucursalID
        WHERE p.Anio = {anio} AND p.Mes = {mes} {suc_filter}
        ORDER BY s.Nombre_Sucursal, p.Categoria
    """
    
    # Totales por tipo (Ingreso/Egreso)
    query_totales = f"""
        SELECT 
            Tipo,
            SUM(Monto_Presupuestado) as Total_Presupuestado,
            SUM(Monto_Ejecutado) as Total_Ejecutado
        FROM Finanzas_Presupuestos
        WHERE Anio = {anio} AND Mes = {mes} {suc_filter.replace('p.', '')}
        GROUP BY Tipo
    """
    
    # Comparativo mes anterior
    mes_ant = mes - 1 if mes > 1 else 12
    anio_ant = anio if mes > 1 else anio - 1
    
    query_comparativo = f"""
        SELECT 
            Tipo,
            SUM(Monto_Ejecutado) as Total_Ejecutado
        FROM Finanzas_Presupuestos
        WHERE Anio = {anio_ant} AND Mes = {mes_ant} {suc_filter.replace('p.', '')}
        GROUP BY Tipo
    """
    
    # Por sucursal
    query_por_sucursal = f"""
        SELECT 
            p.SucursalID,
            s.Nombre_Sucursal,
            SUM(CASE WHEN p.Tipo = 'Ingreso' THEN p.Monto_Ejecutado ELSE 0 END) as Ingresos,
            SUM(CASE WHEN p.Tipo = 'Egreso' THEN p.Monto_Ejecutado ELSE 0 END) as Egresos,
            SUM(CASE WHEN p.Tipo = 'Ingreso' THEN p.Monto_Presupuestado ELSE 0 END) as Ingresos_Pres,
            SUM(CASE WHEN p.Tipo = 'Egreso' THEN p.Monto_Presupuestado ELSE 0 END) as Egresos_Pres
        FROM Finanzas_Presupuestos p
        LEFT JOIN RH_Cat_Sucursales s ON p.SucursalID = s.SucursalID
        WHERE p.Anio = {anio} AND p.Mes = {mes}
        GROUP BY p.SucursalID, s.Nombre_Sucursal
        ORDER BY s.Nombre_Sucursal
    """
    
    try:
        result_pres = await execute_edarsa_hub_query(query_presupuestos)
        result_totales = await execute_edarsa_hub_query(query_totales)
        result_comp = await execute_edarsa_hub_query(query_comparativo)
        result_suc = await execute_edarsa_hub_query(query_por_sucursal)
        
        # Calcular KPIs
        totales_dict = {r['Tipo']: r for r in result_totales.get('datos', [])}
        comp_dict = {r['Tipo']: r for r in result_comp.get('datos', [])}
        
        ingresos_pres = totales_dict.get('Ingreso', {}).get('Total_Presupuestado', 0) or 0
        ingresos_real = totales_dict.get('Ingreso', {}).get('Total_Ejecutado', 0) or 0
        egresos_pres = totales_dict.get('Egreso', {}).get('Total_Presupuestado', 0) or 0
        egresos_real = totales_dict.get('Egreso', {}).get('Total_Ejecutado', 0) or 0
        
        ingresos_ant = comp_dict.get('Ingreso', {}).get('Total_Ejecutado', 0) or 0
        egresos_ant = comp_dict.get('Egreso', {}).get('Total_Ejecutado', 0) or 0
        
        return {
            "periodo": {"anio": anio, "mes": mes},
            "kpis": {
                "ingresos_presupuestados": ingresos_pres,
                "ingresos_ejecutados": ingresos_real,
                "ingresos_var_mes_ant": round(((ingresos_real - ingresos_ant) / ingresos_ant * 100) if ingresos_ant > 0 else 0, 2),
                "egresos_presupuestados": egresos_pres,
                "egresos_ejecutados": egresos_real,
                "egresos_var_mes_ant": round(((egresos_real - egresos_ant) / egresos_ant * 100) if egresos_ant > 0 else 0, 2),
                "utilidad_presupuestada": ingresos_pres - egresos_pres,
                "utilidad_real": ingresos_real - egresos_real,
                "margen_utilidad": round(((ingresos_real - egresos_real) / ingresos_real * 100) if ingresos_real > 0 else 0, 2)
            },
            "presupuestos": result_pres.get('datos', []),
            "por_sucursal": result_suc.get('datos', []),
            "totales": result_totales.get('datos', [])
        }
    except Exception as e:
        logging.error(f"Error en dashboard finanzas: {str(e)}")
        # Retornar estructura vacía si las tablas no existen
        return {
            "periodo": {"anio": anio, "mes": mes},
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
            "totales": [],
            "nota": "Las tablas de finanzas aún no han sido creadas. Ejecute el script de inicialización."
        }


@api_router.get("/finanzas/presupuestos")
async def finanzas_listar_presupuestos(
    anio: int = Query(default=None),
    mes: int = Query(default=None),
    sucursal_id: Optional[int] = None,
    categoria: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista presupuestos con filtros"""
    from datetime import datetime
    
    if not anio:
        anio = datetime.now().year
    
    conditions = [f"p.Anio = {anio}"]
    if mes:
        conditions.append(f"p.Mes = {mes}")
    if sucursal_id:
        conditions.append(f"p.SucursalID = {sucursal_id}")
    if categoria:
        conditions.append(f"p.Categoria = '{categoria}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            p.PresupuestoID,
            p.SucursalID,
            s.Nombre_Sucursal,
            p.Categoria,
            p.SubCategoria,
            p.Tipo,
            p.Monto_Presupuestado,
            p.Monto_Ejecutado,
            p.Anio,
            p.Mes,
            p.Notas,
            p.Fecha_Creacion,
            p.Creado_Por
        FROM Finanzas_Presupuestos p
        LEFT JOIN RH_Cat_Sucursales s ON p.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY p.Mes, s.Nombre_Sucursal, p.Categoria
    """
    
    try:
        result = await execute_edarsa_hub_query(query)
        return {
            "presupuestos": result.get('datos', []),
            "total": result.get('registros', 0)
        }
    except:
        return {"presupuestos": [], "total": 0, "nota": "Tablas no disponibles"}


@api_router.post("/finanzas/presupuestos")
async def finanzas_crear_presupuesto(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un nuevo presupuesto"""
    
    sucursal_id = body.get('sucursal_id')
    categoria = body.get('categoria', '').strip()
    subcategoria = body.get('subcategoria', '').strip()
    tipo = body.get('tipo', 'Egreso')  # Ingreso o Egreso
    monto = body.get('monto', 0)
    anio = body.get('anio')
    mes = body.get('mes')
    notas = body.get('notas', '').strip()
    
    if not sucursal_id or not categoria or not anio or not mes:
        raise HTTPException(status_code=400, detail="Sucursal, categoría, año y mes son requeridos")
    
    if tipo not in ['Ingreso', 'Egreso']:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'Ingreso' o 'Egreso'")
    
    query = f"""
        INSERT INTO Finanzas_Presupuestos 
        (SucursalID, Categoria, SubCategoria, Tipo, Monto_Presupuestado, Monto_Ejecutado, Anio, Mes, Notas, Fecha_Creacion, Creado_Por)
        VALUES 
        ({sucursal_id}, '{categoria}', '{subcategoria}', '{tipo}', {monto}, 0, {anio}, {mes}, '{notas}', GETDATE(), '{current_user.get("email", "")}')
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Presupuesto creado"}


@api_router.put("/finanzas/presupuestos/{presupuesto_id}")
async def finanzas_actualizar_presupuesto(
    presupuesto_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un presupuesto existente"""
    
    updates = []
    
    if 'monto_presupuestado' in body:
        updates.append(f"Monto_Presupuestado = {body['monto_presupuestado']}")
    if 'monto_ejecutado' in body:
        updates.append(f"Monto_Ejecutado = {body['monto_ejecutado']}")
    if 'categoria' in body:
        updates.append(f"Categoria = '{body['categoria']}'")
    if 'subcategoria' in body:
        updates.append(f"SubCategoria = '{body['subcategoria']}'")
    if 'notas' in body:
        updates.append(f"Notas = '{body['notas']}'")
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = f"""
        UPDATE Finanzas_Presupuestos
        SET {', '.join(updates)}, Fecha_Modificacion = GETDATE()
        WHERE PresupuestoID = {presupuesto_id}
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Presupuesto actualizado"}


@api_router.delete("/finanzas/presupuestos/{presupuesto_id}")
async def finanzas_eliminar_presupuesto(
    presupuesto_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un presupuesto"""
    
    query = f"DELETE FROM Finanzas_Presupuestos WHERE PresupuestoID = {presupuesto_id}"
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Presupuesto eliminado"}


@api_router.get("/finanzas/categorias")
async def finanzas_listar_categorias(
    current_user: Dict = Depends(get_current_user)
):
    """Lista las categorías únicas de presupuestos"""
    
    query = """
        SELECT DISTINCT Categoria, Tipo
        FROM Finanzas_Presupuestos
        ORDER BY Tipo, Categoria
    """
    
    try:
        result = await execute_edarsa_hub_query(query)
        return {"categorias": result.get('datos', [])}
    except:
        # Categorías por defecto si no existe la tabla
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
    """Registra un movimiento y actualiza el monto ejecutado del presupuesto"""
    
    presupuesto_id = body.get('presupuesto_id')
    monto = body.get('monto', 0)
    descripcion = body.get('descripcion', '').strip()
    
    if not presupuesto_id or monto == 0:
        raise HTTPException(status_code=400, detail="Presupuesto y monto son requeridos")
    
    # Actualizar monto ejecutado
    query_update = f"""
        UPDATE Finanzas_Presupuestos
        SET Monto_Ejecutado = Monto_Ejecutado + {monto}
        WHERE PresupuestoID = {presupuesto_id}
    """
    
    await execute_edarsa_hub_query(query_update)
    
    return {"success": True, "message": "Movimiento registrado"}


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

@api_router.get("/rrhh/vacantes")
async def rrhh_listar_vacantes(
    sucursal_id: Optional[int] = None,
    estatus: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista vacantes disponibles"""
    
    conditions = ["1=1"]
    if sucursal_id:
        conditions.append(f"v.SucursalID = {sucursal_id}")
    if estatus:
        conditions.append(f"v.Estatus = '{estatus}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            v.VacanteID,
            v.SucursalID,
            s.Nombre_Sucursal,
            v.PuestoID,
            p.Nombre_Puesto,
            p.Departamento,
            v.Titulo,
            v.Descripcion,
            v.Requisitos,
            v.Salario_Min,
            v.Salario_Max,
            v.Tipo_Contrato,
            v.Estatus,
            v.Fecha_Publicacion,
            v.Fecha_Cierre,
            v.Creado_Por,
            (SELECT COUNT(*) FROM RH_Candidatos c WHERE c.VacanteID = v.VacanteID) as Total_Candidatos
        FROM RH_Vacantes v
        LEFT JOIN RH_Cat_Sucursales s ON v.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON v.PuestoID = p.PuestoID
        WHERE {where_clause}
        ORDER BY v.Fecha_Publicacion DESC
    """
    
    try:
        result = await execute_edarsa_hub_query(query)
        return {
            "vacantes": result.get('datos', []),
            "total": result.get('registros', 0)
        }
    except:
        return {"vacantes": [], "total": 0, "nota": "Tablas no disponibles"}


@api_router.post("/rrhh/vacantes")
async def rrhh_crear_vacante(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una nueva vacante"""
    
    sucursal_id = body.get('sucursal_id')
    puesto_id = body.get('puesto_id')
    titulo = body.get('titulo', '').strip()
    descripcion = body.get('descripcion', '').strip()
    requisitos = body.get('requisitos', '').strip()
    salario_min = body.get('salario_min', 0)
    salario_max = body.get('salario_max', 0)
    tipo_contrato = body.get('tipo_contrato', 'Tiempo Completo')
    
    if not sucursal_id or not puesto_id or not titulo:
        raise HTTPException(status_code=400, detail="Sucursal, puesto y título son requeridos")
    
    query = f"""
        INSERT INTO RH_Vacantes 
        (SucursalID, PuestoID, Titulo, Descripcion, Requisitos, Salario_Min, Salario_Max, Tipo_Contrato, Estatus, Fecha_Publicacion, Creado_Por)
        VALUES 
        ({sucursal_id}, {puesto_id}, '{titulo}', '{descripcion}', '{requisitos}', {salario_min}, {salario_max}, '{tipo_contrato}', 'Abierta', GETDATE(), '{current_user.get("email", "")}')
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Vacante creada"}


@api_router.put("/rrhh/vacantes/{vacante_id}")
async def rrhh_actualizar_vacante(
    vacante_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza una vacante"""
    
    updates = []
    
    if 'titulo' in body:
        updates.append(f"Titulo = '{body['titulo']}'")
    if 'descripcion' in body:
        updates.append(f"Descripcion = '{body['descripcion']}'")
    if 'requisitos' in body:
        updates.append(f"Requisitos = '{body['requisitos']}'")
    if 'salario_min' in body:
        updates.append(f"Salario_Min = {body['salario_min']}")
    if 'salario_max' in body:
        updates.append(f"Salario_Max = {body['salario_max']}")
    if 'estatus' in body:
        updates.append(f"Estatus = '{body['estatus']}'")
        if body['estatus'] == 'Cerrada':
            updates.append("Fecha_Cierre = GETDATE()")
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = f"""
        UPDATE RH_Vacantes
        SET {', '.join(updates)}
        WHERE VacanteID = {vacante_id}
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Vacante actualizada"}


@api_router.delete("/rrhh/vacantes/{vacante_id}")
async def rrhh_eliminar_vacante(
    vacante_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina una vacante"""
    
    # Primero eliminar candidatos asociados
    await execute_edarsa_hub_query(f"DELETE FROM RH_Candidatos WHERE VacanteID = {vacante_id}")
    await execute_edarsa_hub_query(f"DELETE FROM RH_Vacantes WHERE VacanteID = {vacante_id}")
    
    return {"success": True, "message": "Vacante eliminada"}


@api_router.get("/rrhh/candidatos")
async def rrhh_listar_candidatos(
    vacante_id: Optional[int] = None,
    estatus: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista candidatos"""
    
    conditions = ["1=1"]
    if vacante_id:
        conditions.append(f"c.VacanteID = {vacante_id}")
    if estatus:
        conditions.append(f"c.Estatus = '{estatus}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            c.CandidatoID,
            c.VacanteID,
            v.Titulo as Vacante_Titulo,
            s.Nombre_Sucursal,
            c.Nombre_Completo,
            c.Email,
            c.Telefono,
            c.CV_URL,
            c.Estatus,
            c.Puntuacion,
            c.Notas,
            c.Fecha_Aplicacion,
            c.Fecha_Entrevista,
            c.Entrevistador
        FROM RH_Candidatos c
        LEFT JOIN RH_Vacantes v ON c.VacanteID = v.VacanteID
        LEFT JOIN RH_Cat_Sucursales s ON v.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY c.Fecha_Aplicacion DESC
    """
    
    try:
        result = await execute_edarsa_hub_query(query)
        return {
            "candidatos": result.get('datos', []),
            "total": result.get('registros', 0)
        }
    except:
        return {"candidatos": [], "total": 0, "nota": "Tablas no disponibles"}


@api_router.post("/rrhh/candidatos")
async def rrhh_crear_candidato(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Registra un nuevo candidato"""
    
    vacante_id = body.get('vacante_id')
    nombre = body.get('nombre', '').strip()
    email = body.get('email', '').strip()
    telefono = body.get('telefono', '').strip()
    cv_url = body.get('cv_url', '').strip()
    
    if not vacante_id or not nombre or not email:
        raise HTTPException(status_code=400, detail="Vacante, nombre y email son requeridos")
    
    query = f"""
        INSERT INTO RH_Candidatos 
        (VacanteID, Nombre_Completo, Email, Telefono, CV_URL, Estatus, Fecha_Aplicacion)
        VALUES 
        ({vacante_id}, '{nombre}', '{email}', '{telefono}', '{cv_url}', 'Recibido', GETDATE())
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Candidato registrado"}


@api_router.put("/rrhh/candidatos/{candidato_id}")
async def rrhh_actualizar_candidato(
    candidato_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza el estatus de un candidato"""
    
    updates = []
    
    if 'estatus' in body:
        updates.append(f"Estatus = '{body['estatus']}'")
    if 'puntuacion' in body:
        updates.append(f"Puntuacion = {body['puntuacion']}")
    if 'notas' in body:
        updates.append(f"Notas = '{body['notas']}'")
    if 'fecha_entrevista' in body:
        updates.append(f"Fecha_Entrevista = '{body['fecha_entrevista']}'")
    if 'entrevistador' in body:
        updates.append(f"Entrevistador = '{body['entrevistador']}'")
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = f"""
        UPDATE RH_Candidatos
        SET {', '.join(updates)}
        WHERE CandidatoID = {candidato_id}
    """
    
    await execute_edarsa_hub_query(query)
    
    return {"success": True, "message": "Candidato actualizado"}


@api_router.delete("/rrhh/candidatos/{candidato_id}")
async def rrhh_eliminar_candidato(
    candidato_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un candidato"""
    
    await execute_edarsa_hub_query(f"DELETE FROM RH_Candidatos WHERE CandidatoID = {candidato_id}")
    
    return {"success": True, "message": "Candidato eliminado"}


@api_router.get("/rrhh/reclutamiento/dashboard")
async def rrhh_reclutamiento_dashboard(
    current_user: Dict = Depends(get_current_user)
):
    """Dashboard de reclutamiento con métricas"""
    
    try:
        # Vacantes por estatus
        query_vacantes = """
            SELECT 
                Estatus,
                COUNT(*) as cantidad
            FROM RH_Vacantes
            GROUP BY Estatus
        """
        
        # Candidatos por estatus
        query_candidatos = """
            SELECT 
                Estatus,
                COUNT(*) as cantidad
            FROM RH_Candidatos
            GROUP BY Estatus
        """
        
        # Candidatos por vacante (top 5)
        query_top = """
            SELECT TOP 5
                v.Titulo,
                COUNT(c.CandidatoID) as Total_Candidatos
            FROM RH_Vacantes v
            LEFT JOIN RH_Candidatos c ON v.VacanteID = c.VacanteID
            WHERE v.Estatus = 'Abierta'
            GROUP BY v.VacanteID, v.Titulo
            ORDER BY Total_Candidatos DESC
        """
        
        result_vac = await execute_edarsa_hub_query(query_vacantes)
        result_cand = await execute_edarsa_hub_query(query_candidatos)
        result_top = await execute_edarsa_hub_query(query_top)
        
        return {
            "vacantes_por_estatus": result_vac.get('datos', []),
            "candidatos_por_estatus": result_cand.get('datos', []),
            "top_vacantes": result_top.get('datos', [])
        }
    except:
        return {
            "vacantes_por_estatus": [],
            "candidatos_por_estatus": [],
            "top_vacantes": [],
            "nota": "Tablas no disponibles"
        }


@api_router.get("/rrhh/reclutamiento/script-inicializacion")
async def rrhh_reclutamiento_script(
    current_user: Dict = Depends(get_current_user)
):
    """Retorna el script SQL para crear las tablas de reclutamiento"""
    
    script = """
-- ============================================
-- SCRIPT DE INICIALIZACIÓN - MÓDULO RECLUTAMIENTO
-- Ejecutar en la base de datos EDARSA HUB
-- ============================================

-- Tabla de Vacantes
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Vacantes' AND xtype='U')
BEGIN
    CREATE TABLE RH_Vacantes (
        VacanteID INT IDENTITY(1,1) PRIMARY KEY,
        SucursalID INT NOT NULL,
        PuestoID INT NOT NULL,
        Titulo NVARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(MAX),
        Requisitos NVARCHAR(MAX),
        Salario_Min DECIMAL(18,2) DEFAULT 0,
        Salario_Max DECIMAL(18,2) DEFAULT 0,
        Tipo_Contrato NVARCHAR(50) DEFAULT 'Tiempo Completo',
        Estatus NVARCHAR(20) DEFAULT 'Abierta' CHECK (Estatus IN ('Abierta', 'En Proceso', 'Cerrada', 'Cancelada')),
        Fecha_Publicacion DATETIME DEFAULT GETDATE(),
        Fecha_Cierre DATETIME,
        Creado_Por NVARCHAR(100),
        
        CONSTRAINT FK_Vacante_Sucursal FOREIGN KEY (SucursalID) 
            REFERENCES RH_Cat_Sucursales(SucursalID),
        CONSTRAINT FK_Vacante_Puesto FOREIGN KEY (PuestoID) 
            REFERENCES RH_Cat_Puestos(PuestoID)
    );
    
    CREATE INDEX IX_Vacantes_Estatus ON RH_Vacantes(Estatus);
    CREATE INDEX IX_Vacantes_Sucursal ON RH_Vacantes(SucursalID);
    
    PRINT 'Tabla RH_Vacantes creada exitosamente';
END
ELSE
    PRINT 'Tabla RH_Vacantes ya existe';
GO

-- Tabla de Candidatos
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Candidatos' AND xtype='U')
BEGIN
    CREATE TABLE RH_Candidatos (
        CandidatoID INT IDENTITY(1,1) PRIMARY KEY,
        VacanteID INT NOT NULL,
        Nombre_Completo NVARCHAR(200) NOT NULL,
        Email NVARCHAR(100) NOT NULL,
        Telefono NVARCHAR(20),
        CV_URL NVARCHAR(500),
        Estatus NVARCHAR(30) DEFAULT 'Recibido' CHECK (Estatus IN ('Recibido', 'En Revision', 'Entrevista Programada', 'Entrevistado', 'Seleccionado', 'Rechazado', 'Contratado')),
        Puntuacion INT CHECK (Puntuacion BETWEEN 0 AND 100),
        Notas NVARCHAR(MAX),
        Fecha_Aplicacion DATETIME DEFAULT GETDATE(),
        Fecha_Entrevista DATETIME,
        Entrevistador NVARCHAR(100),
        
        CONSTRAINT FK_Candidato_Vacante FOREIGN KEY (VacanteID) 
            REFERENCES RH_Vacantes(VacanteID)
    );
    
    CREATE INDEX IX_Candidatos_Vacante ON RH_Candidatos(VacanteID);
    CREATE INDEX IX_Candidatos_Estatus ON RH_Candidatos(Estatus);
    
    PRINT 'Tabla RH_Candidatos creada exitosamente';
END
ELSE
    PRINT 'Tabla RH_Candidatos ya existe';
GO

PRINT '=== Script de reclutamiento completado ===';
"""
    
    return {
        "script": script,
        "instrucciones": [
            "1. Copia el script SQL",
            "2. Ve a 'Explorador BD' en el menú lateral",
            "3. Selecciona el servidor EDARSA HUB",
            "4. Pega y ejecuta el script con credenciales de administrador",
            "5. Regresa a Recursos Humanos > Reclutamiento"
        ]
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
    """
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    
    resultados = {
        "termino": q,
        "tablas": [],
        "columnas": [],
        "datos": [],
        "total": 0
    }
    
    try:
        # 1. Buscar en nombres de TABLAS
        if tipo in ["todo", "tablas"]:
            query_tablas = f"""
SELECT TABLE_NAME as tabla, TABLE_TYPE as tipo
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_NAME LIKE '%{q}%'
ORDER BY TABLE_NAME
"""
            tablas = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_tablas
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
WHERE COLUMN_NAME LIKE '%{q}%'
ORDER BY TABLE_NAME, COLUMN_NAME
"""
            columnas = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_columnas
            )
            resultados["columnas"] = columnas or []
        
        # 3. Buscar en DATOS (opcional, más costoso)
        if tipo in ["todo", "datos"] and tabla:
            # Buscar en una tabla específica
            # Obtener columnas de tipo texto de la tabla
            query_cols_texto = f"""
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla}'
  AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext')
"""
            cols_texto = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_cols_texto
            )
            
            if cols_texto:
                # Construir WHERE con OR para cada columna de texto
                condiciones = " OR ".join([f"[{c['COLUMN_NAME']}] LIKE '%{q}%'" for c in cols_texto])
                query_datos = f"""
SELECT TOP {limite} *
FROM [{tabla}]
WHERE {condiciones}
"""
                datos = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_datos
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
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_tablas_texto
            )
            
            datos_encontrados = []
            for t in (tablas_texto or [])[:5]:
                tabla_nombre = t['TABLE_NAME']
                # Obtener columnas de texto
                query_cols = f"""
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla_nombre}'
  AND DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext')
"""
                cols = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_cols
                )
                
                if cols:
                    condiciones = " OR ".join([f"[{c['COLUMN_NAME']}] LIKE '%{q}%'" for c in cols[:5]])
                    query_datos = f"SELECT TOP 10 * FROM [{tabla_nombre}] WHERE {condiciones}"
                    try:
                        datos = execute_sql_query(
                            server['host'], server['port'], server['database'],
                            server['username'], server['password'], query_datos
                        )
                        for d in (datos or []):
                            datos_encontrados.append({"tabla": tabla_nombre, "fila": d})
                    except:
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
    """
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
    
    # Extraer parámetros del body (soporta ambos formatos)
    if body and 'parametros' in body:
        parametros = body['parametros']
    else:
        parametros = body or {}
    
    # Verificar servidor
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Verificar que el sistema coincida
    sistema_server = server['system_type']
    sistema_consulta = consulta['sistema']
    
    # Mapeo de tipos para consultas predefinidas
    if not es_custom:
        if sistema_server == 'MPRO' and not consulta_id.startswith('MPRO_'):
            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para MPRO")
        if sistema_server == 'SoftRestaurant' and not consulta_id.startswith('SR_'):
            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para SoftRestaurant")
    else:
        # Para consultas custom, verificar directamente
        if sistema_server != sistema_consulta:
            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para {sistema_server}")
    
    # Verificar permisos
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
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
    """Crea una nueva consulta personalizada"""
    # Solo admin puede crear consultas
    if current_user.get('role') != 'Administrador':
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear consultas")
    
    # Validar campos requeridos
    required = ['nombre', 'descripcion', 'sistema', 'categoria', 'parametros', 'sql']
    for field in required:
        if field not in body or not body[field]:
            raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
    
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
        "active": True
    }
    
    await db.consultas_custom.insert_one(consulta)
    consulta.pop('_id', None)
    
    return {"message": "Consulta creada exitosamente", "consulta": consulta}


@api_router.put("/catalogo/consultas-custom/{consulta_id}")
async def actualizar_consulta_custom(consulta_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza una consulta personalizada"""
    if current_user.get('role') != 'Administrador':
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
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['updated_by'] = current_user.get('email')
    
    await db.consultas_custom.update_one({"id": consulta_id}, {"$set": update_data})
    
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
    """Ejecuta una consulta personalizada"""
    # Buscar consulta en MongoDB
    consulta = await db.consultas_custom.find_one({"id": consulta_id})
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    # Verificar servidor
    server = await db.servers.find_one({"id": server_id, "active": True})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Verificar que el sistema coincida
    if server['system_type'] != consulta['sistema']:
        raise HTTPException(status_code=400, detail=f"Esta consulta es para {consulta['sistema']}, no para {server['system_type']}")
    
    # Preparar parámetros
    parametros = body.get('parametros', body) if body else {}
    
    # Preparar SQL
    sql = consulta['sql']
    for param, valor in parametros.items():
        sql = sql.replace('{' + param + '}', str(valor))
    
    logging.info(f"Ejecutando consulta custom {consulta_id} en {server['name']}")
    
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], sql
        )
        
        return {
            "consulta": consulta['nombre'],
            "servidor": server['name'],
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
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
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
    """Asigna permisos de catálogos a un usuario (Solo Supervisor o Admin)"""
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
        raise HTTPException(status_code=403, detail="Solo Supervisores o Administradores pueden asignar permisos")
    
    user_id = body.get("user_id")
    catalogos_permitidos = body.get("catalogos_permitidos", [])
    puede_solicitar = body.get("puede_solicitar", True)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id es requerido")
    
    # Verificar que el usuario existe
    usuario = await db.users.find_one({"id": user_id})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Guardar o actualizar permisos
    await db.permisos_catalogos.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "catalogos_permitidos": catalogos_permitidos,
            "puede_solicitar": puede_solicitar,
            "asignado_por": current_user.get("email"),
            "fecha_asignacion": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
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
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
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
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
        if solicitud.get("solicitante_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")
    
    return solicitud


@api_router.post("/sistema/solicitudes/{solicitud_id}/aprobar")
async def aprobar_solicitud(solicitud_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Aprueba una solicitud con firma (contraseña del aprobador) - Soporta múltiples niveles"""
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
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
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
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
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
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
    user_id = current_user.get("id")
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
                except:
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
        horarios = {
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
            except:
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
    """Lista usuarios que pueden recibir permisos de catálogos (para Supervisores/Admin)"""
    if current_user.get('role') not in ['Supervisor', 'Administrador']:
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
    except:
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
    except:
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
    except:
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
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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
    client.close()
