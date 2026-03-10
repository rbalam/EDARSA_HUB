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
    sucursales: List[str] = []  # IDs de sucursales asignadas
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str
    sucursales: List[str] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Server(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    host: str
    port: int = 1433
    database: str
    username: str
    system_type: str  # "MPRO" o "SoftRestaurant"
    date_calculation_method: str = "inventory_dates"  # Método para calcular fechas de ventas
    sucursales: List[str] = []  # IDs de sucursales
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

def test_sql_connection(host: str, port: int, database: str, username: str, password: str) -> bool:
    try:
        conn = pymssql.connect(server=host, port=port, user=username, password=password, database=database)
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error conectando a SQL Server: {str(e)}")
        return False

def execute_sql_query(host: str, port: int, database: str, username: str, password: str, query: str) -> List[Dict]:
    try:
        logging.info(f"Conectando a SQL Server: {host}:{port}/{database}")
        conn = pymssql.connect(server=host, port=port, user=username, password=password, database=database, timeout=120, login_timeout=30)
        cursor = conn.cursor(as_dict=True)
        logging.info("Conexión establecida, ejecutando query...")
        cursor.execute(query)
        logging.info("Query ejecutada, obteniendo resultados...")
        results = cursor.fetchall()
        logging.info(f"Resultados obtenidos: {len(results)} registros")
        conn.close()
        
        # Convert datetime objects to strings
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        return results
    except Exception as e:
        logging.error(f"Error ejecutando query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando consulta: {str(e)}")

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
    return servers

@api_router.get("/servers/{server_id}")
async def get_server(server_id: str, current_user: Dict = Depends(get_current_user)):
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

# ============= REPORTS =============

@api_router.get("/servers/{server_id}/sucursales")
async def get_sucursales(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de sucursales desde SQL Server"""
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
        return results
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
                    CONVERT(varchar, F.fi_fecha, 23) as fecha,
                    CONVERT(varchar, F.fi_fecha, 120) as fecha_completa,
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
        else:
            query = "SELECT Fi_Folio as folio, CONVERT(varchar, fi_fecha, 23) as fecha, CONVERT(varchar, fi_fecha, 120) as fecha_completa FROM Fisico GROUP BY Fi_Folio, fi_fecha ORDER BY fi_fecha DESC"
        
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

@api_router.post("/reports/inventory-analysis")
async def generate_inventory_analysis(report_params: Dict, current_user: Dict = Depends(get_current_user)):
    """
    Genera un análisis completo de inventario con:
    - Inventario Inicial (folio inicial)
    - Ventas (entre fechas)
    - Movimientos (entre fechas)
    - Inventario Final (folio final)
    - Cálculo de diferencias
    """
    server_id = report_params.get('server_id')
    sucursal = report_params.get('sucursal')
    almacen = report_params.get('almacen')
    fecha_ini = report_params.get('fecha_ini')
    fecha_fin = report_params.get('fecha_fin')
    folio_inicial = report_params.get('folio_inicial')
    folio_final = report_params.get('folio_final')
    
    # Get server
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            logging.info(f"Generando análisis de inventario: {sucursal} - {almacen}")
            logging.info(f"Fechas: {fecha_ini} a {fecha_fin}")
            logging.info(f"Folios: {folio_inicial} a {folio_final}")
            
            # Asegurarnos de que las fechas tengan el formato correcto con hora
            if len(fecha_ini) == 10:  # Solo fecha YYYY-MM-DD
                fecha_ini = fecha_ini + ' 00:00:00'
            if len(fecha_fin) == 10:  # Solo fecha YYYY-MM-DD  
                fecha_fin = fecha_fin + ' 23:59:59'
                
            logging.info(f"Fechas con hora: {fecha_ini} a {fecha_fin}")
            
            # Query simplificada con CAST en fechas
            query = f"""
-- Obtener código del almacén
DECLARE @AlmacenCodigo VARCHAR(20)
SELECT TOP 1 @AlmacenCodigo = Al_Cve_Almacen 
FROM Almacen 
WHERE Al_Descripcion LIKE '%{almacen}%'

-- Consulta principal con TOP 2000
SELECT TOP 2000
    P.Pr_Cve_Producto as Codigo,
    P.Pr_Descripcion as Producto,
    F.Fm_Descripcion as Familia,
    SF.Sf_Descripcion as SubFamilia,
    C.Ct_Descripcion as Categoria,
    P.Pr_Unidad_Control_1 as Unidad,
    P.Pr_ultimo_costo as Costo_Unitario,
    
    -- Inventario Inicial
    ISNULL(FI.Fi_Cantidad_Control_1, 0) as Inv_Inicial_Cantidad,
    
    -- Ventas con kits - usando CAST para fechas
    ISNULL((
        SELECT SUM(V.Vn_Cantidad_1 * ISNULL(PK.Pk_Cantidad, 0))
        FROM venta V
        LEFT JOIN producto_kit PK ON PK.Pr_Cve_Producto = V.Pr_Cve_Producto AND PK.Pk_Producto = P.Pr_Cve_Producto
        INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
        WHERE V.Es_Cve_Estado <> 'CA'
            AND V.Al_Cve_Almacen = @AlmacenCodigo
            AND S.Sc_Descripcion LIKE '%{sucursal}%'
            AND CAST(V.Vn_Fecha AS DATE) >= '{fecha_ini}'
            AND CAST(V.Vn_Fecha AS DATE) <= '{fecha_fin}'
    ), 0) as Ventas_Kit,
    
    -- Ventas directas - usando CAST para fechas
    ISNULL((
        SELECT SUM(V.Vn_Cantidad_Control_1)
        FROM venta V
        INNER JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
        WHERE V.Pr_Cve_Producto = P.Pr_Cve_Producto
            AND V.Es_Cve_Estado <> 'CA'
            AND V.Al_Cve_Almacen = @AlmacenCodigo
            AND S.Sc_Descripcion LIKE '%{sucursal}%'
            AND CAST(V.Vn_Fecha AS DATE) >= '{fecha_ini}'
            AND CAST(V.Vn_Fecha AS DATE) <= '{fecha_fin}'
    ), 0) as Ventas_Directas,
    
    -- Movimientos - usando CAST para fechas
    ISNULL((
        SELECT SUM(CASE 
            WHEN TM.Tm_Tipo = '+' THEN M.Mv_Cantidad_Control_1
            WHEN TM.Tm_Tipo = '-' THEN -M.Mv_Cantidad_Control_1
            ELSE 0
        END)
        FROM Movimiento M
        INNER JOIN Tipo_Movimiento TM ON TM.Tm_Cve_Tipo_Movimiento = M.Tm_Cve_Tipo_Movimiento
        INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
        WHERE M.Pr_Cve_Producto = P.Pr_Cve_Producto
            AND M.Es_Cve_Estado <> 'CA'
            AND M.Al_Cve_Almacen = @AlmacenCodigo
            AND S.Sc_Descripcion LIKE '%{sucursal}%'
            AND CAST(M.Mv_Fecha AS DATE) >= '{fecha_ini}'
            AND CAST(M.Mv_Fecha AS DATE) <= '{fecha_fin}'
    ), 0) as Movimientos,
    
    -- Inventario Final
    ISNULL(FF.Fi_Cantidad_Control_1, 0) as Inv_Final_Cantidad
    
FROM Producto P
INNER JOIN Familia F ON F.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SF ON SF.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
INNER JOIN Categoria C ON C.Ct_Cve_Categoria = P.Ct_Cve_Categoria
LEFT JOIN Fisico FI ON FI.Pr_Cve_Producto = P.Pr_Cve_Producto 
    AND FI.Fi_Folio = '{folio_inicial}'
    AND FI.Al_Cve_Almacen = @AlmacenCodigo
LEFT JOIN Fisico FF ON FF.Pr_Cve_Producto = P.Pr_Cve_Producto
    AND FF.Fi_Folio = '{folio_final}'
    AND FF.Al_Cve_Almacen = @AlmacenCodigo

WHERE P.Es_Cve_Estado <> 'BA'
    AND (
        FI.Fi_Cantidad_Control_1 > 0 OR 
        FF.Fi_Cantidad_Control_1 > 0
    )

ORDER BY F.Fm_Descripcion, SF.Sf_Descripcion, P.Pr_Descripcion
            """
            
            logging.info("Ejecutando consulta con CAST en fechas (TOP 2000)...")
            
        else:
            raise HTTPException(status_code=400, detail="Sistema no soportado para análisis completo")
        
        # Execute query
        results = execute_sql_query(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        logging.info(f"Consulta completada. Procesando {len(results)} productos...")
        
        # Log de muestra del primer producto para debugging
        if len(results) > 0:
            logging.info(f"Ejemplo de producto: {results[0]}")
        
        # Procesar resultados y calcular diferencias
        processed_results = []
        for row in results:
            ventas_total = float(row.get('Ventas_Kit', 0) or 0) + float(row.get('Ventas_Directas', 0) or 0)
            movimientos = float(row.get('Movimientos', 0) or 0)
            inv_inicial = float(row.get('Inv_Inicial_Cantidad', 0) or 0)
            inv_final = float(row.get('Inv_Final_Cantidad', 0) or 0)
            costo = float(row.get('Costo_Unitario', 0) or 0)
            
            # Calcular inventario teórico
            inv_teorico = inv_inicial + movimientos - ventas_total
            
            # Calcular diferencias
            diferencia_cantidad = inv_teorico - inv_final
            diferencia_costo = diferencia_cantidad * costo
            diferencia_porcentaje = (diferencia_cantidad / inv_teorico * 100) if inv_teorico > 0 else 0
            
            processed_row = {
                'Categoria': row.get('Categoria'),
                'Familia': row.get('Familia'),
                'SubFamilia': row.get('SubFamilia'),
                'Codigo': row.get('Codigo'),
                'Producto': row.get('Producto'),
                'Unidad': row.get('Unidad'),
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
                'Diferencia_Porcentaje': round(diferencia_porcentaje, 2)
            }
            
            processed_results.append(processed_row)
        
        logging.info(f"Análisis completado: {len(processed_results)} productos procesados")
        
        return {"data": processed_results, "count": len(processed_results)}
        
    except Exception as e:
        logging.error(f"Error en análisis de inventario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando análisis: {str(e)}")

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

# ============= DASHBOARD =============

@api_router.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: Dict = Depends(get_current_user)):
    total_servers = await db.servers.count_documents({"active": True})
    total_users = await db.users.count_documents({"active": True})
    total_alerts = await db.alerts.count_documents({"active": True})
    total_queries = await db.queries.count_documents({})
    
    return {
        "total_servers": total_servers,
        "total_users": total_users,
        "total_alerts": total_alerts,
        "total_queries": total_queries
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
