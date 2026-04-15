"""
EDARSA HUB - Servicio de Auditoría Financiera
==============================================
Registra todas las acciones financieras sensibles en SQL Server.

NOTA: Si SQL Server EDARSA HUB no está disponible, los registros se 
guardan temporalmente en MongoDB como fallback y se sincronizan después.

USO:
    from core.auditoria import servicio_auditoria, AccionAuditoria, ModuloAuditoria

    await servicio_auditoria.registrar(
        usuario=current_user,
        request=request,
        modulo=ModuloAuditoria.TESORERIA,
        entidad="cuadre_z",
        accion=AccionAuditoria.CONFIRM,
        registro_id="12345",
        valor_nuevo={"efectivo": 5000, "diferencia": 0}
    )

REGLAS:
- VIEW: Opcional en pantallas de alto volumen
- EDIT, CONFIRM, AUTHORIZE: Obligatorio registrar
- No bloquea operación principal si falla el registro
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum
import json
import logging
import os

logger = logging.getLogger(__name__)


# ============================================
# ENUMS DE CLASIFICACIÓN
# ============================================

class AccionAuditoria(Enum):
    """Tipos de acción auditables"""
    VIEW = "VIEW"           # Consultar / listar / filtrar
    EDIT = "EDIT"           # Modificar registros
    CONFIRM = "CONFIRM"     # Validar / guardar operación propia
    AUTHORIZE = "AUTHORIZE" # Aprobar operación crítica o de otro usuario


class ModuloAuditoria(Enum):
    """Módulos del sistema"""
    TESORERIA = "TESORERIA"
    CXP = "CXP"
    PROPINAS = "PROPINAS"
    PRESUPUESTOS = "PRESUPUESTOS"
    INGRESOS = "INGRESOS"
    CONFIG = "CONFIG"
    USUARIOS = "USUARIOS"
    SISTEMA = "SISTEMA"


class NivelRiesgo(Enum):
    """Niveles de riesgo de la acción"""
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class ResultadoAuditoria(Enum):
    """Resultado de la acción"""
    OK = "OK"
    ERROR = "ERROR"
    RECHAZADO = "RECHAZADO"


class OrigenSistema(Enum):
    """Sistema de origen de los datos"""
    EDARSA_HUB = "EDARSA_HUB"
    SOFT = "SOFT"
    MPRO = "MPRO"


# ============================================
# SERVICIO DE AUDITORÍA
# ============================================

class ServicioAuditoria:
    """
    Servicio centralizado de auditoría financiera.
    Registra en SQL Server EDARSA HUB.
    Fallback a MongoDB si SQL no está disponible.
    """
    
    def __init__(self):
        self._sql_available = None
        self._mongo_db = None
    
    async def _get_mongo_db(self):
        """Obtiene conexión a MongoDB para fallback"""
        if self._mongo_db is None:
            try:
                from motor.motor_asyncio import AsyncIOMotorClient
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                client = AsyncIOMotorClient(mongo_url)
                db_name = os.environ.get('DB_NAME', 'edarsa_hub')
                self._mongo_db = client[db_name]
            except Exception as e:
                logger.error(f"Error conectando a MongoDB: {e}")
                return None
        return self._mongo_db
    
    def _get_sql_connection(self):
        """Obtiene conexión a SQL Server EDARSA HUB"""
        try:
            import pytds
            
            # Verificar si hay configuración de SQL Server
            host = os.environ.get('EDARSA_HUB_SQL_HOST')
            if not host:
                return None
            
            config = {
                'host': host,
                'port': int(os.environ.get('EDARSA_HUB_SQL_PORT', '1433')),
                'database': os.environ.get('EDARSA_HUB_SQL_DB', 'EDARSA_HUB'),
                'user': os.environ.get('EDARSA_HUB_SQL_USER', 'sa'),
                'password': os.environ.get('EDARSA_HUB_SQL_PASS', '')
            }
            
            return pytds.connect(
                server=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                timeout=5,
                login_timeout=5,
                as_dict=True
            )
        except Exception as e:
            logger.debug(f"SQL Server no disponible: {e}")
            return None
    
    def _serialize_value(self, value: Any) -> Optional[str]:
        """Serializa un valor para almacenamiento"""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value)
    
    def _determine_campo_modificado(
        self, 
        valor_anterior: Any, 
        valor_nuevo: Any
    ) -> str:
        """Determina si hay múltiples campos modificados"""
        if isinstance(valor_anterior, dict) and isinstance(valor_nuevo, dict):
            if len(valor_anterior) > 1 or len(valor_nuevo) > 1:
                return "MULTIPLE"
            elif len(valor_nuevo) == 1:
                return list(valor_nuevo.keys())[0]
        return None
    
    async def registrar(
        self,
        # Contexto del usuario (puede ser dict de current_user o valores directos)
        usuario: Optional[Dict] = None,
        usuario_id: Optional[str] = None,
        usuario_email: Optional[str] = None,
        session_id: Optional[str] = None,
        
        # Request para obtener IP
        request: Optional[Any] = None,
        ip_origen: Optional[str] = None,
        
        # Contexto organizacional
        empresa_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        origen_sistema: OrigenSistema = OrigenSistema.EDARSA_HUB,
        
        # Clasificación
        modulo: ModuloAuditoria = None,
        entidad: str = None,
        entidad_origen: Optional[str] = None,
        accion: AccionAuditoria = None,
        
        # Referencia al registro
        registro_id: str = None,
        registro_folio: Optional[str] = None,
        
        # Cambios
        campo_modificado: Optional[str] = None,
        valor_anterior: Optional[Any] = None,
        valor_nuevo: Optional[Any] = None,
        
        # Resultado y contexto
        resultado: ResultadoAuditoria = ResultadoAuditoria.OK,
        motivo: Optional[str] = None,
        observaciones: Optional[str] = None,
        nivel_riesgo: Optional[NivelRiesgo] = None
    ) -> bool:
        """
        Registra un evento de auditoría.
        
        Args:
            usuario: Dict con user_id y email del usuario actual
            request: Request de FastAPI para obtener IP
            modulo: Módulo del sistema (TESORERIA, CXP, etc.)
            entidad: Entidad afectada (cuadre_z, factura, etc.)
            accion: Tipo de acción (VIEW, EDIT, CONFIRM, AUTHORIZE)
            registro_id: ID del registro afectado
            valor_anterior: Valor antes del cambio
            valor_nuevo: Valor después del cambio
            resultado: OK, ERROR o RECHAZADO
            nivel_riesgo: BAJO, MEDIO, ALTO, CRITICO
        
        Returns:
            bool: True si se registró correctamente
        
        Note:
            La auditoría NO bloquea la operación principal si falla.
        """
        try:
            # Extraer datos del usuario
            uid = usuario_id or (usuario.get('user_id') if usuario else None) or (usuario.get('sub') if usuario else None)
            email = usuario_email or (usuario.get('email') if usuario else None)
            sid = session_id or (usuario.get('session_id') if usuario else None)
            
            # Extraer IP del request
            ip = ip_origen
            if not ip and request:
                try:
                    ip = request.client.host if hasattr(request, 'client') else None
                except Exception:
                    pass
            
            # Determinar campo modificado si no se especificó
            campo = campo_modificado
            if not campo and (valor_anterior or valor_nuevo):
                campo = self._determine_campo_modificado(valor_anterior, valor_nuevo)
            
            # Serializar valores
            val_ant = self._serialize_value(valor_anterior)
            val_new = self._serialize_value(valor_nuevo)
            
            # Construir documento de auditoría
            audit_doc = {
                'created_at': datetime.utcnow(),
                'usuario_id': uid or 'N/A',
                'usuario_email': email or 'N/A',
                'session_id': sid,
                'ip_origen': ip,
                'empresa_id': empresa_id,
                'sucursal_id': sucursal_id,
                'origen_sistema': origen_sistema.value if origen_sistema else 'EDARSA_HUB',
                'modulo': modulo.value if modulo else 'SISTEMA',
                'entidad': entidad or 'N/A',
                'entidad_origen': entidad_origen,
                'accion': accion.value if accion else 'VIEW',
                'registro_id': registro_id or 'N/A',
                'registro_folio': registro_folio,
                'campo_modificado': campo,
                'valor_anterior': val_ant,
                'valor_nuevo': val_new,
                'resultado': resultado.value if resultado else 'OK',
                'motivo': motivo,
                'observaciones': observaciones,
                'nivel_riesgo': nivel_riesgo.value if nivel_riesgo else None
            }
            
            # Intentar SQL Server primero
            conn = self._get_sql_connection()
            if conn:
                try:
                    query = """
                    INSERT INTO auditoria_financiera (
                        usuario_id, usuario_email, session_id, ip_origen,
                        empresa_id, sucursal_id, origen_sistema,
                        modulo, entidad, entidad_origen, accion,
                        registro_id, registro_folio,
                        campo_modificado, valor_anterior, valor_nuevo,
                        resultado, motivo, observaciones, nivel_riesgo
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """
                    
                    params = [
                        audit_doc['usuario_id'], audit_doc['usuario_email'], 
                        audit_doc['session_id'], audit_doc['ip_origen'],
                        audit_doc['empresa_id'], audit_doc['sucursal_id'], 
                        audit_doc['origen_sistema'],
                        audit_doc['modulo'], audit_doc['entidad'], 
                        audit_doc['entidad_origen'], audit_doc['accion'],
                        audit_doc['registro_id'], audit_doc['registro_folio'],
                        audit_doc['campo_modificado'], audit_doc['valor_anterior'], 
                        audit_doc['valor_nuevo'],
                        audit_doc['resultado'], audit_doc['motivo'], 
                        audit_doc['observaciones'], audit_doc['nivel_riesgo']
                    ]
                    
                    with conn.cursor() as cursor:
                        cursor.execute(query, params)
                    conn.commit()
                    conn.close()
                    
                    logger.debug(f"[AUDIT-SQL] {audit_doc['modulo']}/{audit_doc['entidad']}/{audit_doc['accion']}")
                    return True
                except Exception as e:
                    logger.warning(f"Error escribiendo a SQL, usando MongoDB fallback: {e}")
                    if conn:
                        conn.close()
            
            # Fallback a MongoDB
            db = await self._get_mongo_db()
            if db is not None:
                try:
                    audit_doc['_sync_pending'] = True  # Marcar para sincronización futura
                    await db.auditoria_financiera.insert_one(audit_doc)
                    logger.debug(f"[AUDIT-MONGO] {audit_doc['modulo']}/{audit_doc['entidad']}/{audit_doc['accion']}")
                    return True
                except Exception as mongo_e:
                    logger.error(f"Error escribiendo auditoría a MongoDB: {mongo_e}")
                    return False
            
            logger.warning("No hay backend de auditoría disponible")
            return False
            
        except Exception as e:
            # La auditoría NO debe bloquear la operación principal
            logger.error(f"Error registrando auditoría: {e}")
            return False
    
    async def consultar_por_registro(
        self,
        registro_id: str,
        limite: int = 100
    ) -> list:
        """Obtiene historial de auditoría de un registro específico."""
        try:
            # Intentar MongoDB primero (más probable que esté disponible)
            db = await self._get_mongo_db()
            if db:
                cursor = db.auditoria_financiera.find(
                    {'registro_id': registro_id},
                    {'_id': 0}
                ).sort('created_at', -1).limit(limite)
                return await cursor.to_list(length=limite)
            return []
        except Exception as e:
            logger.error(f"Error consultando auditoría: {e}")
            return []
    
    async def consultar_por_modulo(
        self,
        modulo: ModuloAuditoria,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        limite: int = 500
    ) -> list:
        """Obtiene historial de auditoría de un módulo."""
        try:
            db = await self._get_mongo_db()
            if db:
                filtro = {'modulo': modulo.value}
                if fecha_inicio:
                    filtro['created_at'] = {'$gte': fecha_inicio}
                if fecha_fin:
                    if 'created_at' in filtro:
                        filtro['created_at']['$lte'] = fecha_fin
                    else:
                        filtro['created_at'] = {'$lte': fecha_fin}
                
                cursor = db.auditoria_financiera.find(
                    filtro,
                    {'_id': 0}
                ).sort('created_at', -1).limit(limite)
                return await cursor.to_list(length=limite)
            return []
        except Exception as e:
            logger.error(f"Error consultando auditoría: {e}")
            return []


# ============================================
# SINGLETON
# ============================================

servicio_auditoria = ServicioAuditoria()


# ============================================
# DECORADOR PARA AUDITORÍA AUTOMÁTICA
# ============================================

def auditar(
    modulo: ModuloAuditoria,
    entidad: str,
    accion: AccionAuditoria,
    nivel_riesgo: NivelRiesgo = None,
    obtener_registro_id: callable = None
):
    """
    Decorador para auditar automáticamente una función.
    
    Uso:
        @auditar(
            modulo=ModuloAuditoria.TESORERIA,
            entidad="cuadre_z",
            accion=AccionAuditoria.CONFIRM,
            nivel_riesgo=NivelRiesgo.ALTO,
            obtener_registro_id=lambda args, kwargs: kwargs.get('corte_id')
        )
        async def guardar_cuadre(corte_id: str, data: dict, current_user: dict):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Obtener usuario y request de kwargs si existen
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            # Obtener registro_id
            reg_id = None
            if obtener_registro_id:
                try:
                    reg_id = obtener_registro_id(args, kwargs)
                except Exception:
                    pass
            
            resultado_audit = ResultadoAuditoria.OK
            error_msg = None
            
            try:
                # Ejecutar función original
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                resultado_audit = ResultadoAuditoria.ERROR
                error_msg = str(e)
                raise
            finally:
                # Registrar auditoría (no bloquea)
                await servicio_auditoria.registrar(
                    usuario=current_user,
                    request=request,
                    modulo=modulo,
                    entidad=entidad,
                    accion=accion,
                    registro_id=str(reg_id) if reg_id else 'N/A',
                    resultado=resultado_audit,
                    motivo=error_msg,
                    nivel_riesgo=nivel_riesgo
                )
        
        return wrapper
    return decorator
