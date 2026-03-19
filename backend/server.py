from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
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

def generate_excel(data: List[Dict], filename: str = "reporte.xlsx") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Inventario"
    
    if not data:
        return b''
    
    # Headers
    headers = list(data[0].keys())
    ws.append(headers)
    
    # Style headers
    header_fill = PatternFill(start_color="18181b", end_color="18181b", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Data rows
    for row_data in data:
        ws.append(list(row_data.values()))
    
    # Adjust column widths
    for column in ws.columns:
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column[0].column_letter].width = adjusted_width
    
    # Save to bytes
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
    
    await db.users.update_one({"id": user_id}, {"$set": user_data})
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
    
    await db.servers.update_one({"id": server_id}, {"$set": server_data})
    return {"message": "Servidor actualizado"}

@api_router.delete("/servers/{server_id}")
async def delete_server(server_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await db.servers.update_one({"id": server_id}, {"$set": {"active": False}})
    return {"message": "Servidor desactivado"}

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
async def get_almacenes(server_id: str, sucursal_id: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
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
        else:
            # Query genérica para otros sistemas
            if sucursal_id:
                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = '{sucursal_id}'"
            else:
                query = "SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen"
        
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
                    A.Al_Descripcion as almacen
                FROM Fisico F
                INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND F.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
                {where_clause}
                GROUP BY F.Fi_Folio, F.fi_fecha, F.Sc_Cve_Sucursal, S.Sc_Descripcion, F.Al_Cve_Almacen, A.Al_Descripcion
                ORDER BY F.fi_fecha DESC
            """
        elif server['system_type'] == 'SoftRestaurant':
            # Query para SoftRestaurant - fecha en formato YYYY-MM-DD HH:MM:SS
            where_clause = "WHERE INV.cancelado = 0"
            if almacen_id:
                where_clause += f" AND INV.idalmacen1 = '{almacen_id}'"
            
            query = f"""
                SELECT 
                    INV.folio as folio,
                    CONVERT(varchar, INV.fecha, 120) as fecha,
                    INV.idalmacen1 as almacen_id,
                    A.nombre as almacen
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
    fecha_ini = report_params.get('fecha_ini')
    fecha_fin = report_params.get('fecha_fin')
    folio_inicial = report_params.get('folio_inicial')
    folio_final = report_params.get('folio_final')
    
    # Filtros adicionales del frontend
    filtro_categorias_frontend = report_params.get('categorias', [])
    filtro_familias_frontend = report_params.get('familias', [])
    filtro_subfamilias_frontend = report_params.get('subfamilias', [])
    
    logging.info(f"Filtros recibidos del frontend - Categorias: {filtro_categorias_frontend}, Familias: {filtro_familias_frontend}, SubFamilias: {filtro_subfamilias_frontend}")
    
    # Get server
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            logging.info(f"Generando análisis de inventario: {sucursal} - {almacen}")
            logging.info(f"Fechas: {fecha_ini} a {fecha_fin}")
            logging.info(f"Folios: {folio_inicial} a {folio_final}")
            
            # Obtener filtros configurados del servidor
            tipos_movimiento = server.get('tipos_movimiento', [])
            categorias_servidor = server.get('categorias', [])
            departamentos = server.get('departamentos', [])
            
            # PRIORIDAD: Si el frontend envía filtros, usarlos. Si no, usar los del servidor.
            categorias = filtro_categorias_frontend if filtro_categorias_frontend else categorias_servidor
            
            logging.info(f"Filtros finales - Tipos Mov: {len(tipos_movimiento)}, Categorias: {len(categorias)}, Departamentos: {len(departamentos)}")
            
            # Construir filtros SQL dinámicos
            if tipos_movimiento:
                tipos_mov_sql = ",".join([f"'{t}'" for t in tipos_movimiento])
                filtro_tipos_mov = f"AND E.Tm_Cve_Tipo_Movimiento IN ({tipos_mov_sql})"
            else:
                # Si no hay configuración, no filtrar por tipo de movimiento
                filtro_tipos_mov = ""
            
            if categorias:
                categorias_sql = ",".join([f"'{c}'" for c in categorias])
                filtro_categorias = f"AND producto.Ct_Cve_Categoria IN ({categorias_sql})"
                filtro_categorias_p = f"AND P.Ct_Cve_Categoria IN ({categorias_sql})"
            else:
                filtro_categorias = ""
                filtro_categorias_p = ""
            
            if departamentos:
                departamentos_sql = ",".join([f"'{d}'" for d in departamentos])
                filtro_departamentos = f"AND producto.Dp_Cve_Departamento IN ({departamentos_sql})"
                filtro_departamentos_p = f"AND P.Dp_Cve_Departamento IN ({departamentos_sql})"
            else:
                filtro_departamentos = ""
                filtro_departamentos_p = ""
            
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
            
            # ENFOQUE OPTIMIZADO: Ejecutar consultas separadas y combinar en Python
            # Esto es más rápido que CTEs complejas con UNION ALL
            
            # 1. Obtener código del almacén y verificar si tiene ventas
            # En MPRO, un almacén tiene ventas si está relacionado con movimientos de venta en la sucursal
            almacen_query = f"""
SELECT TOP 1 
    A.Al_Cve_Almacen as codigo,
    A.Al_Descripcion as nombre,
    A.Sc_Cve_Sucursal as sucursal_codigo
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
            almacen_nombre = almacen_result[0]['nombre']
            sucursal_codigo = almacen_result[0]['sucursal_codigo']
            
            logging.info(f"Almacén encontrado: {almacen_codigo} - {almacen_nombre} (Sucursal: {sucursal_codigo})")
            
            # Verificar si el almacén tiene ventas (si es almacén de ventas/consumo)
            # Un almacén tiene ventas si tiene movimientos relacionados con ventas
            # Típicamente el almacén "GENERAL" o de "CONSUMO" tiene ventas
            # Los almacenes de BODEGA, PRODUCCIÓN, etc. no tienen ventas directas
            almacen_nombre_upper = almacen_nombre.upper() if almacen_nombre else ''
            es_almacen_ventas = 'GENERAL' in almacen_nombre_upper or 'CONSUMO' in almacen_nombre_upper or 'VENTA' in almacen_nombre_upper
            
            logging.info(f"Código de almacén: {almacen_codigo}, Nombre: {almacen_nombre}, Es almacén de ventas: {es_almacen_ventas}")
            
            # 2. Obtener TODOS los productos que cumplen los filtros de categoría/departamento
            # Luego filtraremos solo los que tienen actividad (inventario, ventas o movimientos)
            productos_query = f"""
SELECT TOP 3000
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    F.Fm_Descripcion as Familia,
    SF.Sf_Descripcion as SubFamilia,
    C.Ct_Descripcion as Categoria,
    P.Pr_Unidad_Control_1 as Unidad,
    P.Pr_ultimo_costo as Costo_Unitario,
    ISNULL(FI.Fi_Cantidad_Control_1, 0) as Inv_Inicial_Cantidad,
    ISNULL(FF.Fi_Cantidad_Control_1, 0) as Inv_Final_Cantidad
FROM Producto P
INNER JOIN Familia F ON F.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SF ON SF.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
INNER JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
LEFT JOIN Fisico FI ON FI.Pr_Cve_Producto = P.Pr_Cve_Producto 
    AND FI.Fi_Folio = '{folio_inicial}'
    AND FI.Al_Cve_Almacen = '{almacen_codigo}'
LEFT JOIN Fisico FF ON FF.Pr_Cve_Producto = P.Pr_Cve_Producto
    AND FF.Fi_Folio = '{folio_final}'
    AND FF.Al_Cve_Almacen = '{almacen_codigo}'
WHERE P.Es_Cve_Estado <> 'BA'
    {filtro_categorias_p}
    {filtro_departamentos_p}
    {filtro_familias_p}
    {filtro_subfamilias_p}
ORDER BY F.Fm_Descripcion, SF.Sf_Descripcion, P.Pr_Descripcion
"""
            logging.info("Obteniendo productos con inventario...")
            productos = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], productos_query
            )
            logging.info(f"Productos obtenidos: {len(productos)}")
            
            # 3. Obtener ventas por producto (combinando kits y directas)
            # IMPORTANTE: Solo los almacenes de ventas/consumo tienen ventas
            # Los almacenes de bodega, producción, etc. NO tienen ventas
            ventas_dict = {}
            
            if es_almacen_ventas:
                ventas_query = f"""
SELECT Producto_Codigo, SUM(Cantidad) as Total_Ventas FROM (
    -- Ventas de productos KIT
    SELECT 
        Producto_Kit.Pk_Producto as Producto_Codigo,
        SUM(venta.Vn_Cantidad_1 * Producto_Kit.Pk_Cantidad) as Cantidad
    FROM venta
    INNER JOIN producto_kit ON Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
    INNER JOIN producto ON producto.Pr_Cve_Producto = Producto_kit.Pk_Producto
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Cve_Sucursal = '{sucursal_codigo}'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        AND producto_kit.Pk_Producto IS NOT NULL
        {filtro_categorias}
        {filtro_departamentos}
    GROUP BY Producto_Kit.Pk_Producto
    
    UNION ALL
    
    -- Ventas DIRECTAS
    SELECT 
        venta.Pr_Cve_Producto as Producto_Codigo,
        SUM(venta.Vn_Cantidad_Control_1) as Cantidad
    FROM venta
    INNER JOIN producto ON producto.Pr_Cve_Producto = venta.Pr_Cve_Producto
    INNER JOIN sucursal ON sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
    WHERE sucursal.Sc_Cve_Sucursal = '{sucursal_codigo}'
        AND venta.Es_Cve_Estado <> 'CA'
        AND venta.Vn_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
        {filtro_categorias}
        {filtro_departamentos}
    GROUP BY venta.Pr_Cve_Producto
) AS VentasCombinadas
GROUP BY Producto_Codigo
"""
                logging.info("Obteniendo ventas (almacén de ventas/consumo)...")
                ventas_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], ventas_query
                )
                ventas_dict = {v['Producto_Codigo']: float(v['Total_Ventas'] or 0) for v in ventas_result}
                logging.info(f"Ventas obtenidas para {len(ventas_dict)} productos")
            else:
                logging.info(f"Almacén '{almacen_nombre}' NO es de ventas/consumo - ventas = 0 para todos los productos")
            
            # 4. Obtener movimientos por producto FILTRADO POR ALMACÉN
            # Los valores de Mv_Cantidad_Control_1 ya incluyen el signo (positivo para entradas, negativo para salidas)
            # Solo sumamos directamente sin aplicar CASE por Tm_Tipo
            movimientos_query = f"""
SELECT 
    E.Pr_Cve_Producto as Producto_Codigo,
    SUM(E.Mv_Cantidad_Control_1) as Total_Movimientos
FROM Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = E.Tm_Cve_Tipo_Movimiento
INNER JOIN Producto P ON P.Pr_Cve_Producto = E.Pr_Cve_Producto
INNER JOIN Familia FM ON FM.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SB ON SB.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'
    AND E.Al_Cve_Almacen = '{almacen_codigo}'
    AND E.Es_Cve_Estado <> 'CA'
    {filtro_tipos_mov}
    AND E.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
GROUP BY E.Pr_Cve_Producto
"""
            logging.info("Obteniendo movimientos...")
            movimientos_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], movimientos_query
            )
            movimientos_dict = {m['Producto_Codigo']: float(m['Total_Movimientos'] or 0) for m in movimientos_result}
            logging.info(f"Movimientos obtenidos para {len(movimientos_dict)} productos")
            
            # 5. Combinar resultados - Solo incluir productos con actividad
            logging.info("Combinando resultados...")
            results = []
            for prod in productos:
                codigo = prod['Codigo']
                ventas_total = ventas_dict.get(codigo, 0)
                movimientos = movimientos_dict.get(codigo, 0)
                inv_inicial = float(prod.get('Inv_Inicial_Cantidad', 0) or 0)
                inv_final = float(prod.get('Inv_Final_Cantidad', 0) or 0)
                costo = float(prod.get('Costo_Unitario', 0) or 0)
                
                # Solo incluir productos con alguna actividad
                if inv_inicial == 0 and inv_final == 0 and ventas_total == 0 and movimientos == 0:
                    continue
                
                # Calcular inventario teórico: Inicial + Movimientos - Ventas
                inv_teorico = inv_inicial + movimientos - ventas_total
                
                # Calcular diferencias: Teórico - Final
                diferencia_cantidad = inv_teorico - inv_final
                diferencia_costo = diferencia_cantidad * costo
                diferencia_porcentaje = (diferencia_cantidad / inv_teorico * 100) if inv_teorico != 0 else 0
                
                # Nuevas columnas solicitadas
                # Valor Real = (Inv_Inicial + Movimientos - Inv_Final) * Costo
                valor_real = (inv_inicial + movimientos - inv_final) * costo
                # Teórico = Ventas * Costo
                teorico_ventas = ventas_total * costo
                
                results.append({
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
            
            logging.info(f"Análisis completado: {len(results)} productos procesados")
            return {"data": results, "count": len(results)}
            
        elif server['system_type'] == 'SoftRestaurant':
            # Análisis de inventario para SoftRestaurant
            logging.info(f"Generando análisis de inventario SoftRestaurant: {almacen}")
            logging.info(f"Folios: {folio_inicial} a {folio_final}")
            logging.info(f"Filtros frontend - Categorias: {filtro_categorias_frontend}, Familias: {filtro_familias_frontend}, SubFamilias: {filtro_subfamilias_frontend}")
            
            # Obtener fechas de los folios de inventario
            fechas_query = f"""
SELECT folio, fecha
FROM invfisico
WHERE folio IN ({folio_inicial}, {folio_final})
ORDER BY folio
"""
            fechas_result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], fechas_query
            )
            
            # Extraer fechas
            fecha_ini = None
            fecha_fin = None
            for row in fechas_result:
                if str(row['folio']) == str(folio_inicial):
                    fecha_ini = str(row['fecha'])[:10]  # Solo fecha YYYY-MM-DD
                elif str(row['folio']) == str(folio_final):
                    fecha_fin = str(row['fecha'])[:10]
            
            if not fecha_ini or not fecha_fin:
                logging.warning(f"No se encontraron fechas para los folios {folio_inicial} y {folio_final}")
                fecha_ini = fecha_ini or "2000-01-01"
                fecha_fin = fecha_fin or "2099-12-31"
            
            logging.info(f"Fechas calculadas de inventarios: {fecha_ini} a {fecha_fin}")
            
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
            
            # 2. Obtener productos (catálogo) con UNION de INSUMOS inventariables + PRESENTACIONES de insumos inventariables
            # Basado en las consultas de Power BI del usuario
            # APLICANDO FILTROS DE CLASIFICACION, GRUPO Y SUBGRUPO
            logging.info("Obteniendo catálogo de productos (INSUMOS inventariables + PRESENTACIONES de insumos inventariables)")
            
            productos_query = f"""
-- INSUMOS inventariables
SELECT 
    'INSUMO' as TABLA,
    GC.descripcion as CATEGORIA,
    GS.descripcion as GRUPO,
    LEFT(GC.descripcion,1) + RTRIM(LTRIM(insumos.idinsumo)) as CODIGO,
    insumos.descripcion as DESCRIPCION,
    insumos.unidad as UM,
    ISNULL((SELECT TOP 1 RENDIMIENTO FROM insumospresentaciones WHERE insumospresentaciones.idinsumo = insumos.idinsumo), 0) as RENDIMIENTO,
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

UNION ALL

-- PRESENTACIONES de insumos inventariables
-- El idinsumospresentaciones YA tiene el prefijo (ej: B130009), no agregar otro
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
        ELSE LEFT(ISNULL(GC_INS.descripcion,'X'),1) + RTRIM(LTRIM(FMOV.idinsumo))
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
WHERE FMOV.folio IN ({folio_inicial}, {folio_final})
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
                    
                if str(inv['folio']) == str(folio_inicial):
                    inv_inicial_dict[codigo] = {
                        'existencia': existencia,
                        'costo': float(inv['costo'] or 0),
                        'tipo': inv['TIPO']
                    }
                elif str(inv['folio']) == str(folio_final):
                    inv_final_dict[codigo] = {
                        'existencia': existencia,
                        'costo': float(inv['costo'] or 0),
                        'tipo': inv['TIPO']
                    }
            
            logging.info(f"Inventario inicial: {len(inv_inicial_dict)} productos, Final: {len(inv_final_dict)} productos")
            
            # 4. Obtener TODOS los códigos que aparecen en inventarios (inicial o final)
            todos_codigos = set(inv_inicial_dict.keys()) | set(inv_final_dict.keys())
            logging.info(f"Total códigos únicos en inventarios: {len(todos_codigos)}")
            
            # 5. Obtener movimientos - UNION de movsinv (INSUMOS) + movtosalmacen (PRESENTACIONES)
            # Las cantidades ya tienen el signo correcto en la BD
            # Formato de fecha: YYYYMMDD HH:MM:SS
            fecha_ini_fmt = fecha_ini.replace('-', '') if fecha_ini else ''
            fecha_fin_fmt = fecha_fin.replace('-', '') if fecha_fin else ''
            logging.info(f"Obteniendo movimientos entre {fecha_ini_fmt} y {fecha_fin_fmt} para almacén {almacen_nombre}")
            
            movimientos_query = f"""
-- MOVIMIENTOS DE INSUMOS (movsinv)
SELECT 
    LEFT(gruposiclasificacion.descripcion,1) + RTRIM(LTRIM(movsinv.idinsumo)) as CODIGO,
    SUM(movsinv.cantidad) as CANTIDAD
FROM movsinv
INNER JOIN insumos ON insumos.idinsumo = movsinv.idinsumo
INNER JOIN gruposi GP ON GP.idgruposi = insumos.idgruposi
INNER JOIN gruposiclasificacion ON gruposiclasificacion.idgruposiclasificacion = GP.idgruposiclasificacion
LEFT JOIN almacen ON almacen.idalmacen = movsinv.idalmacen
WHERE movsinv.idconcepto NOT IN ('')
  AND movsinv.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
  AND almacen.nombre LIKE '%{almacen}%'
GROUP BY LEFT(gruposiclasificacion.descripcion,1) + RTRIM(LTRIM(movsinv.idinsumo))

UNION ALL

-- MOVIMIENTOS DE PRESENTACIONES (movtosalmacen)
-- El idinsumospresentaciones YA tiene el prefijo (ej: B130009), no agregar otro
SELECT 
    RTRIM(LTRIM(movtosalmacen.idinsumospresentaciones)) as CODIGO,
    SUM(movtosalmacen.cantidad) as CANTIDAD
FROM movtosalmacen
INNER JOIN insumospresentaciones ON insumospresentaciones.idinsumospresentaciones = movtosalmacen.idinsumospresentaciones
INNER JOIN gruposi ON gruposi.idgruposi = insumospresentaciones.idgruposi
INNER JOIN gruposiclasificacion ON gruposiclasificacion.idgruposiclasificacion = gruposi.idgruposiclasificacion
LEFT JOIN almacen ON almacen.idalmacen = movtosalmacen.idalmacen
WHERE movtosalmacen.idconcepto NOT IN ('')
  AND movtosalmacen.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
  AND almacen.nombre LIKE '%{almacen}%'
GROUP BY RTRIM(LTRIM(movtosalmacen.idinsumospresentaciones))
"""
            
            try:
                movimientos_result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], movimientos_query
                )
                movimientos_dict = {m['CODIGO']: float(m['CANTIDAD'] or 0) for m in movimientos_result}
                logging.info(f"Movimientos obtenidos para {len(movimientos_dict)} productos")
            except Exception as e:
                logging.warning(f"Error al obtener movimientos: {str(e)}, continuando con movimientos = 0")
                movimientos_dict = {}
            
            # 6. Obtener ventas SOLO si es almacén de consumo (tipo = 1)
            # Basado en la consulta de Power BI que usa recetasalmacenes + costos
            ventas_dict = {}
            if es_almacen_consumo:
                logging.info("Obteniendo ventas (almacén de CONSUMO tipo=1)...")
                ventas_query = f"""
SELECT 
    LEFT(GP.descripcion,1) + RTRIM(LTRIM(receta.idinsumo)) as CODIGO,
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
WHERE turnos.APERTURA BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND AL.nombre LIKE '%{almacen}%'
GROUP BY LEFT(GP.descripcion,1) + RTRIM(LTRIM(receta.idinsumo))
"""
                try:
                    ventas_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], ventas_query
                    )
                    ventas_dict = {v['CODIGO']: float(v['CONSUMIDO'] or 0) for v in ventas_result}
                    logging.info(f"Ventas obtenidas para {len(ventas_dict)} productos")
                except Exception as e:
                    logging.warning(f"Error al obtener ventas: {str(e)}, continuando sin ventas")
                    ventas_dict = {}
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
                
                results.append({
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
            
            # Consulta detalle de movimientos
            query = f"""
SELECT 
    M.Mv_Folio as Folio,
    M.Mv_Fecha as Fecha,
    M.Mv_Cantidad_Control_1 as Cantidad,
    M.Tm_Cve_Tipo_Movimiento as Tipo_Codigo,
    TM.Tm_Descripcion as Tipo_Descripcion,
    TM.Tm_Tipo as Tipo_Movimiento,
    P.Pr_Descripcion as Producto,
    A.Al_Descripcion as Almacen
FROM Movimiento M
INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
INNER JOIN Producto P ON P.Pr_Cve_Producto = M.Pr_Cve_Producto
INNER JOIN Almacen A ON A.Al_Cve_Almacen = M.Al_Cve_Almacen
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
WHERE M.Pr_Cve_Producto = '{producto_codigo}'
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
    AND M.Al_Cve_Almacen = '{almacen_codigo}'
    AND M.Es_Cve_Estado <> 'CA'
    AND M.Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
    {filtro_tipos_mov}
ORDER BY M.Mv_Fecha DESC
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            # Formatear resultados
            movements = []
            for row in result:
                tipo_texto = 'Entrada' if row.get('Tipo_Movimiento') == 'E' else 'Salida'
                movements.append({
                    'folio': row.get('Folio'),
                    'fecha': str(row.get('Fecha'))[:19] if row.get('Fecha') else '',
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
            # Para SoftRestaurant - usando movsinv con tabla conceptos
            # El código tiene prefijo de clasificación (ej: B130009), extraer solo el número
            # Quitar el primer carácter (prefijo de clasificación)
            producto_id = producto_codigo[1:] if producto_codigo and len(producto_codigo) > 1 else producto_codigo
            
            logging.info(f"Detalle movimientos SoftRestaurant - Código original: {producto_codigo}, ID extraído: {producto_id}, Almacén: {almacen}, Fechas: {fecha_ini} a {fecha_fin}")
            
            query = f"""
SELECT 
    COALESCE(M.foliocheque, CAST(M.idcompra AS VARCHAR), CAST(M.traspaso AS VARCHAR), CAST(M.invfisico AS VARCHAR), '') as Folio,
    M.fecha as Fecha,
    CASE WHEN C.tipo = 1 THEN M.cantidad ELSE -M.cantidad END as Cantidad,
    C.idconcepto as Tipo_Codigo,
    C.descripcion as Tipo_Descripcion,
    CASE WHEN C.tipo = 1 THEN 'Entrada' ELSE 'Salida' END as Tipo_Movimiento,
    I.descripcion as Producto,
    A.nombre as Almacen,
    M.costo as Costo,
    M.idconcepto as Concepto_ID
FROM movsinv M
INNER JOIN conceptos C ON C.idconcepto = M.idconcepto
INNER JOIN insumos I ON I.idinsumo = M.idinsumo
LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
WHERE RTRIM(LTRIM(M.idinsumo)) = '{producto_id}'
    AND A.nombre LIKE '%{almacen}%'
    AND M.fecha BETWEEN '{fecha_ini}' AND '{fecha_fin}'
    AND M.idconcepto <> ''
ORDER BY M.fecha DESC
"""
            logging.info(f"Query detalle movimientos: {query[:500]}...")
            
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query
            )
            
            logging.info(f"Movimientos encontrados: {len(result)}")
            
            movements = []
            for row in result:
                movements.append({
                    'folio': row.get('Folio') or '',
                    'fecha': str(row.get('Fecha'))[:19] if row.get('Fecha') else '',
                    'cantidad': float(row.get('Cantidad') or 0),
                    'tipo_codigo': row.get('Tipo_Codigo'),
                    'tipo_descripcion': row.get('Tipo_Descripcion'),
                    'tipo_movimiento': row.get('Tipo_Movimiento', ''),
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
        V.Vn_Precio_Unitario as Precio_Unitario,
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
        V.Vn_Precio_Unitario as Precio_Unitario,
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
            # Para SoftRestaurant
            query = f"""
SELECT 
    VC.idventacuenta as Folio,
    C.fecha as Fecha,
    VC.cantidad as Cantidad,
    'DIRECTA' as Tipo_Venta,
    P.descripcion as Producto,
    VC.precio as Precio_Unitario
FROM ventascuentas VC
INNER JOIN cuentas C ON C.idcuenta = VC.idcuenta
INNER JOIN productos P ON P.idproducto = VC.idproducto
WHERE VC.idproducto IN (
    SELECT idproducto FROM insumos_productos WHERE idinsumo = '{producto_codigo}'
)
AND C.fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'
ORDER BY C.fecha DESC
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
                    'producto': row.get('Producto'),
                    'precio_unitario': float(row.get('Precio_Unitario') or 0),
                    'sucursal': ''
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
    
    excel_bytes = generate_excel(report_data, filename)
    
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
