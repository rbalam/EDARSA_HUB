from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Servicio de Auditoría Financiera
==============================================
Registra todas las acciones financieras sensibles en SQL Server.

NOTA: SQL Server EDARSA HUB es la fuente única para auditoría financiera.
No existe fallback operativo a MongoDB.

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
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
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
# DATACLASS PARA EVENTO DE AUDITORÍA
# ============================================

@dataclass
class AuditoriaParams:
    """
    Parámetros de entrada para registrar auditoría.
    Agrupa los 23 parámetros en una estructura reutilizable.
    
    Uso:
        params = AuditoriaParams(
            modulo=ModuloAuditoria.TESORERIA,
            entidad="cuadre_z",
            accion=AccionAuditoria.CONFIRM,
            registro_id="12345"
        )
        await servicio_auditoria.registrar(params)
    """
    # Usuario (uno de estos debe estar presente)
    usuario: Optional[Dict] = None
    usuario_id: Optional[str] = None
    usuario_email: Optional[str] = None
    session_id: Optional[str] = None
    request: Optional[Any] = None
    ip_origen: Optional[str] = None
    
    # Contexto organizacional
    empresa_id: Optional[str] = None
    sucursal_id: Optional[str] = None
    origen_sistema: OrigenSistema = OrigenSistema.EDARSA_HUB
    
    # Clasificación (obligatorios)
    modulo: ModuloAuditoria = None
    entidad: str = None
    entidad_origen: Optional[str] = None
    accion: AccionAuditoria = None
    registro_id: str = None
    registro_folio: Optional[str] = None
    
    # Cambios
    campo_modificado: Optional[str] = None
    valor_anterior: Optional[Any] = None
    valor_nuevo: Optional[Any] = None
    
    # Resultado
    resultado: ResultadoAuditoria = ResultadoAuditoria.OK
    motivo: Optional[str] = None
    observaciones: Optional[str] = None
    nivel_riesgo: Optional[NivelRiesgo] = None


@dataclass
class EventoAuditoria:
    """Estructura de datos para un evento de auditoría."""
    # Clasificación (obligatorios)
    modulo: str = "SISTEMA"
    entidad: str = "N/A"
    accion: str = "VIEW"
    registro_id: str = "N/A"
    
    # Usuario
    usuario_id: str = "N/A"
    usuario_email: str = "N/A"
    session_id: Optional[str] = None
    ip_origen: Optional[str] = None
    
    # Contexto organizacional
    empresa_id: Optional[str] = None
    sucursal_id: Optional[str] = None
    origen_sistema: str = "EDARSA_HUB"
    entidad_origen: Optional[str] = None
    registro_folio: Optional[str] = None
    
    # Cambios
    campo_modificado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    
    # Resultado
    resultado: str = "OK"
    motivo: Optional[str] = None
    observaciones: Optional[str] = None
    nivel_riesgo: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    _sync_pending: bool = False
    
    def to_sql_params(self) -> list:
        """Retorna los parámetros para INSERT SQL."""
        return [
            self.usuario_id, self.usuario_email, self.session_id, self.ip_origen,
            self.empresa_id, self.sucursal_id, self.origen_sistema,
            self.modulo, self.entidad, self.entidad_origen, self.accion,
            self.registro_id, self.registro_folio,
            self.campo_modificado, self.valor_anterior, self.valor_nuevo,
            self.resultado, self.motivo, self.observaciones, self.nivel_riesgo
        ]
    
    def to_mongo_doc(self) -> dict:
        """Retorna documento para MongoDB."""
        doc = asdict(self)
        doc['_sync_pending'] = True
        return doc


# ============================================
# SERVICIO DE AUDITORÍA
# ============================================

class ServicioAuditoria:
    """
    Servicio centralizado de auditoría financiera.
    Registra en SQL Server EDARSA HUB.
    Fallback a MongoDB si SQL no está disponible.
    """
    
    SQL_INSERT = """
    INSERT INTO auditoria_financiera (
        usuario_id, usuario_email, session_id, ip_origen,
        empresa_id, sucursal_id, origen_sistema,
        modulo, entidad, entidad_origen, accion,
        registro_id, registro_folio,
        campo_modificado, valor_anterior, valor_nuevo,
        resultado, motivo, observaciones, nivel_riesgo
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    
    def __init__(self):
        self._sql_available = None
        self._mongo_db = None
    
    async def _get_mongo_db(self):
        """P5-3D: MongoDB retirado (NO-MONGO). La auditoría persiste en SQL. Retorna None."""
        return None
    
    def _get_sql_connection(self):
        """Obtiene conexión a SQL Server EDARSA HUB"""
        try:
            import pytds
            
            host = os.environ.get('EDARSA_HUB_SQL_HOST')
            if not host:
                return None
            
            return pytds.connect(
                server=host,
                port=int(os.environ.get('EDARSA_HUB_SQL_PORT', '1433')),
                database=os.environ.get('EDARSA_HUB_SQL_DB', 'EDARSA_HUB'),
                user=os.environ.get('EDARSA_HUB_SQL_USER', 'sa'),
                password=os.environ.get('EDARSA_HUB_SQL_PASS', ''),
                timeout=5,
                login_timeout=5,
                as_dict=True
            )
        except Exception as e:
            logger.debug(f"SQL Server no disponible: {e}")
            return None
    
    @staticmethod
    def _serialize_value(value: Any) -> Optional[str]:
        """Serializa un valor para almacenamiento"""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value)
    
    @staticmethod
    def _determine_campo_modificado(valor_anterior: Any, valor_nuevo: Any) -> Optional[str]:
        """Determina si hay múltiples campos modificados"""
        if isinstance(valor_anterior, dict) and isinstance(valor_nuevo, dict):
            if len(valor_anterior) > 1 or len(valor_nuevo) > 1:
                return "MULTIPLE"
            if len(valor_nuevo) == 1:
                return list(valor_nuevo.keys())[0]
        return None
    
    def _extraer_datos_usuario(
        self,
        usuario: Optional[Dict],
        usuario_id: Optional[str],
        usuario_email: Optional[str],
        session_id: Optional[str]
    ) -> tuple:
        """Extrae datos del usuario de múltiples fuentes."""
        uid = usuario_id
        if not uid and usuario:
            uid = usuario.get('user_id') or usuario.get('sub')
        
        email = usuario_email
        if not email and usuario:
            email = usuario.get('email')
        
        sid = session_id
        if not sid and usuario:
            sid = usuario.get('session_id')
        
        return (uid or 'N/A', email or 'N/A', sid)
    
    def _extraer_ip(self, request: Optional[Any], ip_origen: Optional[str]) -> Optional[str]:
        """Extrae IP del request o usa la proporcionada."""
        if ip_origen:
            return ip_origen
        if request:
            try:
                return request.client.host if hasattr(request, 'client') else None
            except Exception:
                pass
        return None
    
    def _crear_evento_from_params(self, p: AuditoriaParams) -> EventoAuditoria:
        """Crea un EventoAuditoria a partir de AuditoriaParams."""
        uid, email, sid = self._extraer_datos_usuario(p.usuario, p.usuario_id, p.usuario_email, p.session_id)
        ip = self._extraer_ip(p.request, p.ip_origen)
        
        # Determinar campo modificado
        campo = p.campo_modificado
        if not campo and (p.valor_anterior or p.valor_nuevo):
            campo = self._determine_campo_modificado(p.valor_anterior, p.valor_nuevo)
        
        return EventoAuditoria(
            usuario_id=uid,
            usuario_email=email,
            session_id=sid,
            ip_origen=ip,
            empresa_id=p.empresa_id,
            sucursal_id=p.sucursal_id,
            origen_sistema=p.origen_sistema.value if p.origen_sistema else 'EDARSA_HUB',
            modulo=p.modulo.value if p.modulo else 'SISTEMA',
            entidad=p.entidad or 'N/A',
            entidad_origen=p.entidad_origen,
            accion=p.accion.value if p.accion else 'VIEW',
            registro_id=p.registro_id or 'N/A',
            registro_folio=p.registro_folio,
            campo_modificado=campo,
            valor_anterior=self._serialize_value(p.valor_anterior),
            valor_nuevo=self._serialize_value(p.valor_nuevo),
            resultado=p.resultado.value if p.resultado else 'OK',
            motivo=p.motivo,
            observaciones=p.observaciones,
            nivel_riesgo=p.nivel_riesgo.value if p.nivel_riesgo else None
        )

    def _crear_evento(
        self,
        usuario: Optional[Dict] = None,
        usuario_id: Optional[str] = None,
        usuario_email: Optional[str] = None,
        session_id: Optional[str] = None,
        request: Optional[Any] = None,
        ip_origen: Optional[str] = None,
        empresa_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        origen_sistema: OrigenSistema = OrigenSistema.EDARSA_HUB,
        modulo: ModuloAuditoria = None,
        entidad: str = None,
        entidad_origen: Optional[str] = None,
        accion: AccionAuditoria = None,
        registro_id: str = None,
        registro_folio: Optional[str] = None,
        campo_modificado: Optional[str] = None,
        valor_anterior: Optional[Any] = None,
        valor_nuevo: Optional[Any] = None,
        resultado: ResultadoAuditoria = ResultadoAuditoria.OK,
        motivo: Optional[str] = None,
        observaciones: Optional[str] = None,
        nivel_riesgo: Optional[NivelRiesgo] = None
    ) -> EventoAuditoria:
        """
        Crea un EventoAuditoria a partir de los parámetros.
        DEPRECATED: Usar _crear_evento_from_params con AuditoriaParams.
        """
        params = AuditoriaParams(
            usuario=usuario, usuario_id=usuario_id, usuario_email=usuario_email,
            session_id=session_id, request=request, ip_origen=ip_origen,
            empresa_id=empresa_id, sucursal_id=sucursal_id, origen_sistema=origen_sistema,
            modulo=modulo, entidad=entidad, entidad_origen=entidad_origen,
            accion=accion, registro_id=registro_id, registro_folio=registro_folio,
            campo_modificado=campo_modificado, valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo, resultado=resultado, motivo=motivo,
            observaciones=observaciones, nivel_riesgo=nivel_riesgo
        )
        return self._crear_evento_from_params(params)
    
    async def _guardar_sql(self, evento: EventoAuditoria) -> bool:
        """Intenta guardar en SQL Server."""
        conn = self._get_sql_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(self.SQL_INSERT, evento.to_sql_params())
            conn.commit()
            logger.debug(f"[AUDIT-SQL] {evento.modulo}/{evento.entidad}/{evento.accion}")
            return True
        except Exception as e:
            logger.warning(f"Error escribiendo a SQL: {e}")
            return False
        finally:
            conn.close()
    
    async def _guardar_mongo(self, evento: EventoAuditoria) -> bool:
        """Compatibilidad legacy desactivada: auditoría opera SQL-only."""
        return False

    async def registrar_params(self, params: AuditoriaParams) -> bool:
        """
        Registra un evento de auditoría usando AuditoriaParams.
        
        Uso:
            params = AuditoriaParams(modulo=ModuloAuditoria.TESORERIA, ...)
            await servicio_auditoria.registrar_params(params)
        """
        try:
            evento = self._crear_evento_from_params(params)
            
            if await self._guardar_sql(evento):
                return True
            
            if await self._guardar_mongo(evento):
                return True
            
            logger.warning("No hay backend de auditoría disponible")
            return False
            
        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")
            return False

    async def registrar(
        self,
        usuario: Optional[Dict] = None,
        usuario_id: Optional[str] = None,
        usuario_email: Optional[str] = None,
        session_id: Optional[str] = None,
        request: Optional[Any] = None,
        ip_origen: Optional[str] = None,
        empresa_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        origen_sistema: OrigenSistema = OrigenSistema.EDARSA_HUB,
        modulo: ModuloAuditoria = None,
        entidad: str = None,
        entidad_origen: Optional[str] = None,
        accion: AccionAuditoria = None,
        registro_id: str = None,
        registro_folio: Optional[str] = None,
        campo_modificado: Optional[str] = None,
        valor_anterior: Optional[Any] = None,
        valor_nuevo: Optional[Any] = None,
        resultado: ResultadoAuditoria = ResultadoAuditoria.OK,
        motivo: Optional[str] = None,
        observaciones: Optional[str] = None,
        nivel_riesgo: Optional[NivelRiesgo] = None
    ) -> bool:
        """
        Registra un evento de auditoría (interfaz legacy con parámetros individuales).
        
        Note:
            La auditoría NO bloquea la operación principal si falla.
            Preferir registrar_params() para nuevo código.
        """
        params = AuditoriaParams(
            usuario=usuario, usuario_id=usuario_id, usuario_email=usuario_email,
            session_id=session_id, request=request, ip_origen=ip_origen,
            empresa_id=empresa_id, sucursal_id=sucursal_id, origen_sistema=origen_sistema,
            modulo=modulo, entidad=entidad, entidad_origen=entidad_origen,
            accion=accion, registro_id=registro_id, registro_folio=registro_folio,
            campo_modificado=campo_modificado, valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo, resultado=resultado, motivo=motivo,
            observaciones=observaciones, nivel_riesgo=nivel_riesgo
        )
        return await self.registrar_params(params)
    
    def _consultar_auditoria_sql(self, predicate, limite: int) -> list:
        """Lee auditoría desde EDARSAHUB SQL (dbo.Finanzas_AuditoriaFinanciera).

        Los eventos viven como JSON en PayloadMongo. Filtra con `predicate(payload)`,
        normaliza created_at a ISO y ordena descendente.
        """
        from datetime import datetime as _dt, timezone as _tz
        from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

        def _ca_dt(payload):
            ca = payload.get('created_at')
            if isinstance(ca, dict):
                ca = ca.get('$date')
            if not ca:
                return None
            try:
                s = ca.replace('Z', '+00:00') if isinstance(ca, str) else ca
                d = _dt.fromisoformat(s)
                return d if d.tzinfo else d.replace(tzinfo=_tz.utc)
            except Exception:
                return None

        try:
            conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=10)
            try:
                cur = conn.cursor(as_dict=True)
                cur.execute(
                    "SELECT PayloadMongo FROM dbo.Finanzas_AuditoriaFinanciera "
                    "WHERE ColeccionOrigen = %s",
                    ('auditoria_financiera',),
                )
                rows = cur.fetchall() or []
            finally:
                conn.close()

            eventos = []
            for r in rows:
                try:
                    p = json.loads(r['PayloadMongo']) if r['PayloadMongo'] else {}
                except Exception:
                    continue
                if not p or not predicate(p, _ca_dt(p)):
                    continue
                p.pop('_id', None)
                ca_dt = _ca_dt(p)
                p['created_at'] = ca_dt.isoformat() if ca_dt else None
                eventos.append((ca_dt or _dt.min.replace(tzinfo=_tz.utc), p))

            eventos.sort(key=lambda x: x[0], reverse=True)
            return [e for _, e in eventos[:limite]]
        except Exception as e:
            logger.error(f"Error consultando auditoría SQL: {e}")
            return []

    async def consultar_por_registro(self, registro_id: str, limite: int = 100) -> list:
        """Obtiene historial de auditoría de un registro específico (SQL-First)."""
        return self._consultar_auditoria_sql(
            lambda p, ca: p.get('registro_id') == registro_id, limite
        )

    async def consultar_por_modulo(
        self,
        modulo: ModuloAuditoria,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        limite: int = 500
    ) -> list:
        """Obtiene historial de auditoría de un módulo (SQL-First)."""
        from datetime import timezone as _tz

        def _aware(dt):
            if dt is None:
                return None
            return dt if dt.tzinfo else dt.replace(tzinfo=_tz.utc)

        fi = _aware(fecha_inicio)
        ff = _aware(fecha_fin)

        def match(p, ca):
            if p.get('modulo') != modulo.value:
                return False
            if fi and (ca is None or ca < fi):
                return False
            if ff and (ca is None or ca > ff):
                return False
            return True

        return self._consultar_auditoria_sql(match, limite)


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



# Exports
__all__ = [
    'AuditoriaParams',
    'EventoAuditoria',
    'AccionAuditoria',
    'ModuloAuditoria',
    'NivelRiesgo',
    'ResultadoAuditoria',
    'OrigenSistema',
    'ServicioAuditoria',
    'servicio_auditoria',
]