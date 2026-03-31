from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query
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


def execute_sql_query(host: str, port: int, database: str, username: str, password: str, query: str) -> List[Dict]:
    """
    Ejecuta una consulta SQL usando pytds (preferido) con fallback a pymssql.
    """
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    logging.info(f"Conectando a SQL Server: hostname={hostname}, port={parsed_port}, instance={instance}, db={database}")
    
    # Primero intentar con pytds
    try:
        logging.info("Ejecutando query con pytds...")
        conn = pytds.connect(
            server=hostname,
            port=parsed_port,
            database=database,
            user=username,
            password=password,
            timeout=120,
            login_timeout=30
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
            timeout=120, 
            login_timeout=30
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
        return results
        
    except Exception as pymssql_error:
        error_msg = f"Error ejecutando consulta. pytds y pymssql fallaron: {str(pymssql_error)}"
        logging.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

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
            query = "SELECT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre FROM Sucursal WHERE Es_Cve_Estado <> 'BA'"
        elif server['system_type'] == 'SoftRestaurant':
            # SoftRestaurant NO tiene tabla Sucursal - devolvemos una sucursal virtual con el nombre del servidor
            # o podemos devolver los almacenes como "sucursales" virtuales
            return [{"id": "default", "nombre": server.get('name', 'Principal'), "codigo": "default"}]
        else:
            # Query genérica para otros sistemas
            query = "SELECT DISTINCT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre FROM Sucursal"
        
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        # Filtrar por permisos del usuario
        return filter_sucursales_by_permissions(results, current_user, server_id)
    except Exception as e:
        logging.error(f"Error obteniendo sucursales: {str(e)}")
        return []

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
async def get_almacenes_softrestaurant(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de almacenes de SoftRestaurant (no requiere sucursal)"""
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if server['system_type'] != 'SoftRestaurant':
        raise HTTPException(status_code=400, detail="Este endpoint es solo para SoftRestaurant")
    
    try:
        # Query para obtener almacenes de SoftRestaurant incluyendo el tipo
        # TIPO = 1: Almacén de consumo (tiene ventas)
        # TIPO = 2: Almacén de presentaciones (NO tiene ventas)
        query = """
SELECT 
    idalmacen as id, 
    nombre,
    ISNULL(tipo, 1) as tipo
FROM almacen
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
            
            # Calcular fecha de inicio para movimientos/ventas (fecha_ini + 1 día)
            from datetime import datetime, timedelta
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
            
            # 2. Obtener productos del departamento INSUMOS (0007)
            # Solo mostramos productos que:
            # a) Son INSUMOS (Dp_Cve_Departamento = '0007') Y tienen presentaciones
            # b) Son productos de COMPRA que NO están como presentación de ningún insumo
            # NOTA: Usamos GROUP BY y SUM para agrupar inventarios duplicados
            productos_query = f"""
WITH InsumosConPresentaciones AS (
    -- INSUMOS que tienen al menos una presentación
    SELECT DISTINCT P.Pr_Cve_Producto
    FROM Producto P
    INNER JOIN Producto_Presentacion PP ON PP.Pr_Cve_Producto = P.Pr_Cve_Producto
    WHERE P.Dp_Cve_Departamento = '0007'
      AND P.Es_Cve_Estado <> 'BA'
),
ProductosComoPresentacion AS (
    -- Productos que están registrados como presentación de algún insumo
    SELECT DISTINCT Pp_Producto as Pr_Cve_Producto
    FROM Producto_Presentacion
),
InventarioInicial AS (
    -- Sumar inventarios iniciales duplicados por producto (multi-folio, multi-almacén)
    SELECT Pr_Cve_Producto, SUM(Fi_Cantidad_Control_1) as Cantidad
    FROM Fisico
    WHERE Fi_Folio IN ({folios_ini_sql}) AND Al_Cve_Almacen IN ({almacenes_sql})
    GROUP BY Pr_Cve_Producto
),
InventarioFinal AS (
    -- Sumar inventarios finales duplicados por producto (multi-folio, multi-almacén)
    SELECT Pr_Cve_Producto, SUM(Fi_Cantidad_Control_1) as Cantidad
    FROM Fisico
    WHERE Fi_Folio IN ({folios_fin_sql}) AND Al_Cve_Almacen IN ({almacenes_sql})
    GROUP BY Pr_Cve_Producto
)
SELECT TOP 3000
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
        WHEN ICP.Pr_Cve_Producto IS NOT NULL THEN 1
        ELSE 0
    END as Tiene_Presentaciones,
    ISNULL(FI.Cantidad, 0) as Inv_Inicial_Cantidad,
    ISNULL(FF.Cantidad, 0) as Inv_Final_Cantidad
FROM Producto P
INNER JOIN Familia F ON F.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SF ON SF.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
INNER JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
INNER JOIN Departamento D ON D.Dp_Cve_Departamento = P.Dp_Cve_Departamento
LEFT JOIN InsumosConPresentaciones ICP ON ICP.Pr_Cve_Producto = P.Pr_Cve_Producto
LEFT JOIN ProductosComoPresentacion PCP ON PCP.Pr_Cve_Producto = P.Pr_Cve_Producto
LEFT JOIN InventarioInicial FI ON FI.Pr_Cve_Producto = P.Pr_Cve_Producto
LEFT JOIN InventarioFinal FF ON FF.Pr_Cve_Producto = P.Pr_Cve_Producto
WHERE P.Es_Cve_Estado <> 'BA'
    AND (
        -- Caso A: Es un INSUMO con presentaciones
        (P.Dp_Cve_Departamento = '0007' AND ICP.Pr_Cve_Producto IS NOT NULL)
        OR
        -- Caso B: Es un producto de COMPRA que NO está como presentación de ningún insumo
        (P.Dp_Cve_Departamento <> '0007' AND PCP.Pr_Cve_Producto IS NULL)
    )
    {filtro_categorias_p}
    {filtro_familias_p}
    {filtro_subfamilias_p}
ORDER BY F.Fm_Descripcion, SF.Sf_Descripcion, P.Pr_Descripcion
"""
            logging.info("Obteniendo catálogo de productos MPRO (INSUMOS con presentaciones + COMPRAS sin presentación)...")
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
        {"_id": 0, "id": 1, "name": 1, "system_type": 1}
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
ORDER BY INV.fecha DESC
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
    folio_inv_inicial: Optional[str] = None
    fecha_inv_inicial: str
    fecha_auditoria: str  # Fecha del inventario final o actual
    folio_inv_final: Optional[str] = None  # Opcional: si no hay, se captura manual
    folio_requisicion: Optional[str] = None  # Requisición a comparar (una sola)
    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
    inventario_manual: Optional[List[Dict]] = None  # Para captura manual si no hay folio
    inventario_fisico_actual: Optional[List[Dict]] = None  # Captura manual del inv físico del día del pedido
    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones

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
            
            if folios_req:
                folios_sql = ", ".join([f"'{f}'" for f in folios_req])
                # Las órdenes de compra en SoftRestaurant usan códigos que pueden ser presentaciones
                # Intentamos obtener descripción de ambas tablas y el proveedor
                query_requi = f"""
SELECT 
    OCM.idinsumo as codigo, 
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto, 
    SUM(OCM.cantidad) as cantidad_pedido,
    ISNULL(OCM.costo, 0) as costo,
    COALESCE(P.nombre, 'Sin proveedor') as proveedor
FROM ordenescompramov OCM
INNER JOIN ordenescompra OC ON OC.idordencompra = OCM.idordencompra
LEFT JOIN insumos I ON I.idinsumo = OCM.idinsumo
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = OCM.idinsumo
LEFT JOIN proveedores P ON P.idproveedor = OC.idproveedor
WHERE OC.folio IN ({folios_sql})
GROUP BY OCM.idinsumo, I.descripcion, IP.descripcion, OCM.costo, P.nombre
"""
                requi_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_requi
                )
                for r in requi_result:
                    codigo = str(r['codigo']).strip()
                    skus_requisicion.add(codigo)
                    requi_dict[codigo] = {
                        'cantidad': float(r['cantidad_pedido'] or 0),
                        'producto': r['producto'] or '',
                        'costo': float(r.get('costo', 0) or 0),
                        'proveedor': r.get('proveedor', '') or ''
                    }
                logging.info(f"[AUDITORIA] SKUs en requisiciones: {len(skus_requisicion)}")
            
            # PASO 3: Obtener inventario inicial
            # Para BODEGA: usar idpresentacion como código
            # Para CONSUMO: usar idinsumo como código
            inv_ini_dict = {}
            if request.folio_inv_inicial:
                if es_solo_bodega:
                    # Bodega trabaja con presentaciones
                    query_inv_ini = f"""
SELECT 
    RTRIM(INM.idpresentacion) as codigo,
    COALESCE(IP.descripcion, 'Sin descripción') as producto, 
    INM.fisicoalmacen1 as cantidad, 
    ISNULL(INM.costo, 0) as costo
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
WHERE INM.folio = {request.folio_inv_inicial}
"""
                else:
                    # Consumo trabaja con insumos
                    query_inv_ini = f"""
SELECT 
    RTRIM(COALESCE(
        NULLIF(RTRIM(INM.idinsumo), ''),
        IP.idinsumo,
        INM.idpresentacion
    )) as codigo,
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto, 
    INM.fisicoalmacen1 as cantidad, 
    ISNULL(INM.costo, 0) as costo
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
LEFT JOIN insumos I ON I.idinsumo = COALESCE(NULLIF(RTRIM(INM.idinsumo), ''), IP.idinsumo)
WHERE INM.folio = {request.folio_inv_inicial}
"""
                result_ini = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_inv_ini
                )
                inv_ini_dict = {str(r['codigo']).strip(): {
                    "producto": r['producto'], 
                    "cantidad": float(r['cantidad'] or 0),
                    "costo": float(r['costo'] or 0)
                } for r in result_ini}
            
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
                if tipos_entrada_compra:
                    query_mov = f"""
SELECT RTRIM(M.idinsumospresentaciones) as codigo, SUM(M.cantidad) as cantidad
FROM movtosalmacen M
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_entrada_compra])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY RTRIM(M.idinsumospresentaciones)
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
                # Por ahora, usar misma lógica que bodega para presentaciones
                if tipos_entrada_compra:
                    query_mov = f"""
SELECT RTRIM(M.idinsumospresentaciones) as codigo, SUM(M.cantidad) as cantidad
FROM movtosalmacen M
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_entrada_compra])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY RTRIM(M.idinsumospresentaciones)
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
                if tipos_salida_traspaso:
                    query_salidas = f"""
SELECT RTRIM(M.idinsumospresentaciones) as codigo, SUM(M.cantidad) as cantidad
FROM movtosalmacen M
WHERE M.idconcepto IN ({", ".join([f"'{t}'" for t in tipos_salida_traspaso])})
    AND M.fecha >= '{fecha_ini_sql}'
    AND M.fecha <= '{fecha_fin_sql} 23:59:59'
GROUP BY RTRIM(M.idinsumospresentaciones)
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
            inv_fin_dict = {}
            if request.inventario_fisico_actual:
                # Captura manual del inventario físico del día del pedido
                inv_fin_dict = {str(item['codigo']).strip(): {
                    "producto": item.get('producto', ''),
                    "cantidad": float(item.get('cantidad', 0)),
                    "costo": float(item.get('costo', 0))
                } for item in request.inventario_fisico_actual}
            elif request.folio_inv_final:
                if es_solo_bodega:
                    # Bodega: usar idpresentacion como código
                    query_inv_fin = f"""
SELECT 
    RTRIM(INM.idpresentacion) as codigo,
    COALESCE(IP.descripcion, 'Sin descripción') as producto, 
    INM.fisicoalmacen1 as cantidad, 
    ISNULL(INM.costo, 0) as costo
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
WHERE INM.folio = {request.folio_inv_final}
"""
                else:
                    # Consumo: usar idinsumo como código
                    query_inv_fin = f"""
SELECT 
    RTRIM(COALESCE(
        NULLIF(RTRIM(INM.idinsumo), ''),
        IP.idinsumo,
        INM.idpresentacion
    )) as codigo,
    COALESCE(I.descripcion, IP.descripcion, 'Sin descripción') as producto,
    INM.fisicoalmacen1 as cantidad, 
    ISNULL(INM.costo, 0) as costo
FROM invfisicomovtos INM
LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = RTRIM(INM.idpresentacion)
LEFT JOIN insumos I ON I.idinsumo = COALESCE(NULLIF(RTRIM(INM.idinsumo), ''), IP.idinsumo)
WHERE INM.folio = {request.folio_inv_final}
"""
                result_fin = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_inv_fin
                )
                inv_fin_dict = {str(r['codigo']).strip(): {
                    "producto": r['producto'],
                    "cantidad": float(r['cantidad'] or 0),
                    "costo": float(r['costo'] or 0)
                } for r in result_fin}
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
            
            # Determinar qué códigos procesar
            if request.solo_skus_requisicion and skus_requisicion:
                # Solo los SKUs que están en las requisiciones seleccionadas
                todos_codigos = skus_requisicion
                logging.info(f"[AUDITORIA] Filtrando solo SKUs de requisición: {len(todos_codigos)}")
            else:
                # Todos los códigos encontrados
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
                
                # ¿Debe comprar?
                debe_comprar = dias_inv < 10  # Umbral de 10 días
                
                # Incluir producto si tiene nombre o está en la requisición
                if producto or codigo in skus_requisicion:
                    resultados.append({
                        "codigo": codigo,
                        "producto": producto or f"SKU: {codigo}",
                        "proveedor": proveedor,
                        "inv_inicial": inv_inicial,
                        "movimientos": movimientos,  # Campo renombrado
                        "entradas": movimientos,  # Mantener compatibilidad
                        "consumos": abs(consumos),  # Mostrar siempre positivo para claridad
                        "existencia_teorica": round(existencia_teorica, 2),
                        "inv_fisico": inv_fisico,
                        "diferencia": round(diferencia, 2),
                        "costo": costo,
                        "importe_diferencia": round(importe_dif, 2),
                        "tipo_diferencia": "favor" if diferencia >= 0 else "contra",
                        "consumo_diario": round(consumo_diario, 2),
                        "dias_inventario": round(dias_inv, 1) if dias_inv < 999 else "N/A",
                        "cantidad_pedido": cantidad_pedido,
                        "debe_comprar": debe_comprar,
                        "recomendacion": "COMPRAR" if debe_comprar and cantidad_pedido > 0 else "OK" if not debe_comprar else "SIN PEDIDO"
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
            
            # Ordenar por importe diferencia (más graves primero)
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


# ============= ANÁLISIS DE COMPRAS - ENDPOINTS =============

class AnalisisComprasRequest(BaseModel):
    server_id: str
    sucursal: str
    anio: int
    meses: List[str]

@api_router.get("/compras/dashboard/{server_id}")
async def obtener_dashboard_compras(
    server_id: str, 
    sucursal: str = None, 
    periodo_mes: str = Query(default="actual"),
    periodo_ano: str = Query(default="actual"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene KPIs y alertas para el dashboard de compras"""
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
            from datetime import datetime, timedelta
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            fecha_ini = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Total compras del mes (usando tabla compras - columna correcta: fechaaplicacion)
            query_compras = f"""
SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fechaaplicacion >= '{fecha_ini}'
  AND c.fechaaplicacion <= '{fecha_fin} 23:59:59'
  AND ISNULL(c.cancelado, 0) = 0
"""
            result_compras = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_compras
            )
            total_compras = float(result_compras[0]['Compra_Total'] or 0) if result_compras else 0
            facturas = int(result_compras[0]['Facturas'] or 0) if result_compras else 0
            
            # Proveedores activos (con compras en últimos 90 días)
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
WHERE c.fechaaplicacion >= '{fecha_ini}'
  AND c.fechaaplicacion <= '{fecha_fin} 23:59:59'
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
    
    try:
        if server['system_type'] == 'MPRO':
            # Construir condición de meses
            meses_cond = " OR ".join([f"MONTH(M.Mv_Fecha) = {int(m)}" for m in request.meses])
            
            query = f"""
SELECT 
    P.Pv_Cve_Proveedor as codigo,
    P.Pv_Nombre as nombre,
    MONTH(M.Mv_Fecha) as mes,
    SUM(M.Mv_Costo_Importe) as total
FROM Movimiento M
INNER JOIN Proveedor P ON P.Pv_Cve_Proveedor = M.Pv_Cve_Proveedor
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE TM.Tm_Tipo = 'E'
    AND YEAR(M.Mv_Fecha) = {request.anio}
    AND ({meses_cond})
    AND S.Sc_Descripcion LIKE '%{request.sucursal}%'
    AND ISNULL(M.Es_Cve_Estado, '') <> 'CA'
GROUP BY P.Pv_Cve_Proveedor, P.Pv_Nombre, MONTH(M.Mv_Fecha)
ORDER BY P.Pv_Nombre, MONTH(M.Mv_Fecha)
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
                    proveedores[codigo][mes_str] = float(row['total'])
                    proveedores[codigo]['total'] += float(row['total'])
            
            # Ordenar por total descendente
            proveedores_list = sorted(proveedores.values(), key=lambda x: x['total'], reverse=True)
            
            return {
                "proveedores": proveedores_list[:50],  # Top 50
                "alertas": []  # TODO: calcular alertas de desviación
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
    current_user: Dict = Depends(get_current_user)
):
    """
    Dashboard principal de ventas con KPIs y comparativos.
    Soporta SoftRestaurant y MPRO.
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
        
        if periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            # Para comparativo: día anterior
            fecha_ini_ant = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
            fecha_fin_ant = fecha_ini_ant
        elif periodo == "semana":
            # Semana actual (lunes a hoy)
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            # Semana anterior
            fecha_ini_ant = (inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
            fecha_fin_ant = (inicio_semana - timedelta(days=1)).strftime('%Y-%m-%d')
        else:  # mes
            # Mes actual
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            # Mes anterior
            primer_dia_mes = hoy.replace(day=1)
            ultimo_dia_mes_ant = primer_dia_mes - timedelta(days=1)
            fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin_ant = ultimo_dia_mes_ant.strftime('%Y-%m-%d')
        
        logging.info(f"Comercial Dashboard: {server['name']} - Período: {periodo} ({fecha_ini} a {fecha_fin})")
        
        if server['system_type'] == 'SoftRestaurant':
            # Formato de fecha compatible con SQL Server en español (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            f_ini_ant = fecha_ini_ant.replace('-', '')
            f_fin_ant = fecha_fin_ant.replace('-', '')
            
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
                "vs_ano_anterior": 0,  # TODO: calcular año anterior
                "vs_presupuesto": 0,  # TODO: calcular vs meta/presupuesto
                "pax_vs_mes_anterior": vs_pax_mes_anterior
            }
            
            return {
                "kpis": kpis,
                "comparativo": comparativo,
                "alertas": []
            }
        
        elif server['system_type'] == 'MPRO':
            # Query para MPRO - usar Venta_Encabezado con Comanda para PAX
            sucursal_join = ""
            sucursal_filter = ""
            if sucursal:
                sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
                sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # Query con PAX de tabla Comanda
            query_kpis = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_periodo,
    ISNULL(SUM(C.Co_Personas), 0) as pax_total
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
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
WHERE VE.Vn_Fecha >= '{fecha_ini_ant}'
  AND VE.Vn_Fecha <= '{fecha_fin_ant} 23:59:59'
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
                
                # Comparativo para MPRO con PAX
                comparativo = {
                    "vs_periodo_anterior": vs_periodo_anterior,
                    "vs_ano_anterior": 0,
                    "vs_presupuesto": 0,
                    "pax_vs_mes_anterior": vs_pax_mes_anterior
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
            # Filtro de sucursal para MPRO
            sucursal_filter = ""
            if sucursal:
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
            sucursal_filter = ""
            if sucursal:
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
            
            # Filtro de sucursal si viene
            sucursal_filter = ""
            if sucursal:
                sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal_filter={sucursal_filter}")
            
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

def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
    """Query reutilizable para SoftRestaurant - misma lógica análisis inventarios"""
    # Usar formato YYYYMMDD sin guiones para evitar problemas de conversión de fecha
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
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
    # Formato YYYYMMDD para MPRO
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
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
    # Formato YYYYMMDD para MPRO (SQL Server con configuración regional español)
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
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
        
        # Query mes anterior para esta sucursal - con PAX (formato YYYYMMDD)
        query_ant = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fia}' AND VE.Vn_Fecha <= '{ffa}'
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
  AND VE.Vn_Fecha >= '{fiaa}' AND VE.Vn_Fecha <= '{ffaa}'
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
    anio: int = Query(default=0),  # 0 = año actual
    current_user: Dict = Depends(get_current_user)
):
    """
    Tablero ejecutivo con KPIs de TODAS las unidades.
    Comparativo vs mes anterior y año anterior (mismos días).
    """
    from datetime import datetime, timedelta
    import calendar
    
    hoy = datetime.now()
    
    # Determinar período
    if anio == 0:
        anio = hoy.year
    if mes == 0:
        mes = hoy.month
    
    # Fechas del período actual
    fecha_ini = f"{anio}-{mes:02d}-01"
    if anio == hoy.year and mes == hoy.month:
        # Mes actual incompleto
        fecha_fin = hoy.strftime('%Y-%m-%d')
        dias_transcurridos = hoy.day
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
    
    logging.info(f"Tablero Ejecutivo: {mes}/{anio} ({fecha_ini} a {fecha_fin}), días: {dias_transcurridos}/{dias_mes}")
    
    # Obtener todos los servidores activos
    servers = await db.servers.find({"active": True}).to_list(100)
    logging.info(f"Servidores encontrados: {len(servers)} - Tipos: {[s['system_type'] for s in servers]}")
    
    # Filtrar por permisos del usuario
    if current_user.get('role') != 'Administrador':
        allowed = current_user.get('allowed_servers', [])
        servers = [s for s in servers if s['id'] in allowed]
    
    resultados = []
    totales = {"ventas": 0, "ventas_ant": 0, "ventas_año": 0, "pax": 0, "pax_ant": 0, "pax_año": 0, 
               "cheques": 0, "cheques_ant": 0, "cheques_año": 0, "proyeccion": 0}
    
    for server in servers:
        logging.info(f"Procesando servidor: {server['name']} - Tipo: {server['system_type']}")
        
        if server['system_type'] == 'SoftRestaurant':
            kpis = get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                           fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes)
            if kpis:
                kpis["unidad"] = server['name']
                kpis["server_id"] = server['id']
                kpis["system_type"] = server['system_type']
                resultados.append(kpis)
                # Acumular totales
                for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                          "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                    totales[k] += kpis.get(k, 0)
        
        elif server['system_type'] == 'MPRO':
            # MPRO: Dividir por sucursal (igual que en Inventarios)
            logging.info(f"Procesando servidor MPRO: {server['name']}")
            try:
                unidades_mpro = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                                           fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes)
                logging.info(f"MPRO {server['name']}: Encontradas {len(unidades_mpro)} unidades")
                for unidad in unidades_mpro:
                    resultados.append(unidad)
                    # Acumular totales
                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                        totales[k] += unidad.get(k, 0)
            except Exception as mpro_error:
                logging.error(f"Error procesando MPRO {server['name']}: {mpro_error}")
    
    # Calcular variaciones de totales
    totales["var_vs_mes_ant"] = round(((totales["ventas"] - totales["ventas_ant"]) / totales["ventas_ant"] * 100), 1) if totales["ventas_ant"] > 0 else 0
    totales["var_vs_año_ant"] = round(((totales["ventas"] - totales["ventas_año"]) / totales["ventas_año"] * 100), 1) if totales["ventas_año"] > 0 else 0
    totales["var_pax_mes"] = round(((totales["pax"] - totales["pax_ant"]) / totales["pax_ant"] * 100), 1) if totales["pax_ant"] > 0 else 0
    totales["var_pax_año"] = round(((totales["pax"] - totales["pax_año"]) / totales["pax_año"] * 100), 1) if totales["pax_año"] > 0 else 0
    totales["var_cheques_mes"] = round(((totales["cheques"] - totales["cheques_ant"]) / totales["cheques_ant"] * 100), 1) if totales["cheques_ant"] > 0 else 0
    totales["var_cheques_año"] = round(((totales["cheques"] - totales["cheques_año"]) / totales["cheques_año"] * 100), 1) if totales["cheques_año"] > 0 else 0
    totales["ticket_prom"] = round(totales["ventas"] / totales["pax"], 2) if totales["pax"] > 0 else 0
    totales["cheque_prom"] = round(totales["ventas"] / totales["cheques"], 2) if totales["cheques"] > 0 else 0
    
    # Proyección vs ventas año anterior (comparar proyección con ventas_año)
    totales["var_proy_vs_año"] = round(((totales["proyeccion"] - totales["ventas_año"]) / totales["ventas_año"] * 100), 1) if totales["ventas_año"] > 0 else 0
    
    # Contar unidades que tenían ventas el año anterior (ventas_año > 0)
    totales["unidades_año_ant"] = sum(1 for u in resultados if u.get("ventas_año", 0) > 0)
    
    # Ordenar unidades de mayor a menor venta
    resultados_ordenados = sorted(resultados, key=lambda x: x.get('ventas', 0), reverse=True)
    
    return {
        "periodo": {"mes": mes, "anio": anio, "dias_transcurridos": dias_transcurridos, "dias_mes": dias_mes},
        "comparativo_con": {"mes_anterior": f"{mes_ant}/{anio_mes_ant}", "año_anterior": f"{mes}/{anio-1}"},
        "unidades": resultados_ordenados,
        "totales": totales
    }


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


# Incluir el router después de definir todos los endpoints
app.include_router(api_router)

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
