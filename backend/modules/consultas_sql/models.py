"""
EDARSA HUB - Consultas SQL: Modelos Pydantic
============================================
FASE 3: Modelos para el catálogo de consultas SQL-First.

SEGURIDAD:
- No exponer connection strings
- No exponer passwords
- No exponer API keys
- No incluir datos sensibles en serialización

TABLAS ORIGEN:
- ConsultasSQL_Catalogo
- ConsultasSQL_Parametros
- ConsultasSQL_Versiones
- ConsultasSQL_Servidores
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TipoDatoParametro(str, Enum):
    """Tipos de datos permitidos para parámetros."""
    STRING = "STRING"
    DATE = "DATE"
    DATETIME = "DATETIME"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"


class TipoConsulta(str, Enum):
    """Tipos de consulta."""
    CONSULTA = "CONSULTA"
    REPORTE = "REPORTE"
    KPI = "KPI"
    DASHBOARD = "DASHBOARD"


class SeveridadValidacion(str, Enum):
    """Severidad de problemas de validación."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ConsultaSQLParametro:
    """
    Modelo para parámetros de una consulta.
    Tabla origen: ConsultasSQL_Parametros
    """
    parametro_id: int
    consulta_id: int
    nombre_parametro: str
    nombre_mostrar: Optional[str] = None
    tipo_dato: str = "STRING"
    requerido: bool = True
    valor_default: Optional[str] = None
    regex_validacion: Optional[str] = None
    valor_minimo: Optional[str] = None
    valor_maximo: Optional[str] = None
    lista_valores_json: Optional[List[str]] = None
    orden_mostrar: int = 0
    componente_ui: Optional[str] = None
    activo: bool = True

    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> "ConsultaSQLParametro":
        """Crea instancia desde fila de SQL."""
        import json
        lista_valores = None
        if row.get('ListaValoresJSON'):
            try:
                lista_valores = json.loads(row['ListaValoresJSON'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return cls(
            parametro_id=row.get('ParametroID', 0),
            consulta_id=row.get('ConsultaID', 0),
            nombre_parametro=row.get('NombreParametro', ''),
            nombre_mostrar=row.get('NombreMostrar'),
            tipo_dato=row.get('TipoDato', 'STRING'),
            requerido=bool(row.get('Requerido', True)),
            valor_default=row.get('ValorDefault'),
            regex_validacion=row.get('RegexValidacion'),
            valor_minimo=row.get('ValorMinimo'),
            valor_maximo=row.get('ValorMaximo'),
            lista_valores_json=lista_valores,
            orden_mostrar=row.get('OrdenMostrar', 0),
            componente_ui=row.get('ComponenteUI'),
            activo=bool(row.get('Activo', True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            'parametro_id': self.parametro_id,
            'consulta_id': self.consulta_id,
            'nombre_parametro': self.nombre_parametro,
            'nombre_mostrar': self.nombre_mostrar,
            'tipo_dato': self.tipo_dato,
            'requerido': self.requerido,
            'valor_default': self.valor_default,
            'regex_validacion': self.regex_validacion,
            'valor_minimo': self.valor_minimo,
            'valor_maximo': self.valor_maximo,
            'lista_valores_json': self.lista_valores_json,
            'orden_mostrar': self.orden_mostrar,
            'componente_ui': self.componente_ui,
            'activo': self.activo,
        }


@dataclass
class ConsultaSQLVersion:
    """
    Modelo para versiones históricas de una consulta.
    Tabla origen: ConsultasSQL_Versiones
    """
    version_id: int
    consulta_id: int
    version: int
    consulta_sql: str
    parametros_json: Optional[str] = None
    motivo_cambio: Optional[str] = None
    fecha_creacion: Optional[str] = None
    usuario_creacion_id: Optional[str] = None

    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> "ConsultaSQLVersion":
        """Crea instancia desde fila de SQL."""
        fecha = row.get('FechaCreacion')
        if fecha and hasattr(fecha, 'isoformat'):
            fecha = fecha.isoformat()
        
        return cls(
            version_id=row.get('VersionID', 0),
            consulta_id=row.get('ConsultaID', 0),
            version=row.get('Version', 1),
            consulta_sql=row.get('ConsultaSQL', ''),
            parametros_json=row.get('ParametrosJSON'),
            motivo_cambio=row.get('MotivoCambio'),
            fecha_creacion=fecha,
            usuario_creacion_id=row.get('UsuarioCreacionID'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            'version_id': self.version_id,
            'consulta_id': self.consulta_id,
            'version': self.version,
            'consulta_sql': self.consulta_sql,
            'parametros_json': self.parametros_json,
            'motivo_cambio': self.motivo_cambio,
            'fecha_creacion': self.fecha_creacion,
            'usuario_creacion_id': self.usuario_creacion_id,
        }


@dataclass
class ConsultaSQLServidor:
    """
    Modelo para asociaciones consulta-servidor.
    Tabla origen: ConsultasSQL_Servidores
    """
    consulta_servidor_id: int
    consulta_id: int
    servidor_id: str  # UUID como string
    empresa_id: Optional[int] = None
    sucursal_id: Optional[str] = None
    activo: bool = True
    prioridad: int = 0
    fecha_creacion: Optional[str] = None

    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> "ConsultaSQLServidor":
        """Crea instancia desde fila de SQL."""
        fecha = row.get('FechaCreacion')
        if fecha and hasattr(fecha, 'isoformat'):
            fecha = fecha.isoformat()
        
        servidor_id = row.get('ServidorID', '')
        if servidor_id and hasattr(servidor_id, 'lower'):
            # Normalizar UUID a lowercase
            servidor_id = str(servidor_id).lower()
        
        return cls(
            consulta_servidor_id=row.get('ConsultaServidorID', 0),
            consulta_id=row.get('ConsultaID', 0),
            servidor_id=servidor_id,
            empresa_id=row.get('EmpresaID'),
            sucursal_id=row.get('SucursalID'),
            activo=bool(row.get('Activo', True)),
            prioridad=row.get('Prioridad', 0),
            fecha_creacion=fecha,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            'consulta_servidor_id': self.consulta_servidor_id,
            'consulta_id': self.consulta_id,
            'servidor_id': self.servidor_id,
            'empresa_id': self.empresa_id,
            'sucursal_id': self.sucursal_id,
            'activo': self.activo,
            'prioridad': self.prioridad,
            'fecha_creacion': self.fecha_creacion,
        }


@dataclass
class ConsultaSQLCatalogo:
    """
    Modelo principal para consultas del catálogo.
    Tabla origen: ConsultasSQL_Catalogo
    """
    consulta_id: int
    public_uuid: str
    codigo_consulta: str
    nombre_consulta: str
    descripcion: Optional[str] = None
    modulo: str = "General"
    tipo_consulta: str = "CONSULTA"
    sistema_tipo_id: int = 1
    consulta_sql: str = ""
    es_sistema: bool = False
    es_personalizada: bool = False
    es_sincronizable: bool = False
    permite_ejecucion_manual: bool = True
    solo_lectura: bool = True
    requiere_autorizacion: bool = False
    activo: bool = True
    version: int = 1
    config_origen: str = "LEGACY_PYTHON"
    fecha_creacion: Optional[str] = None
    usuario_creacion_id: Optional[str] = None
    fecha_modificacion: Optional[str] = None
    usuario_modificacion_id: Optional[str] = None
    # Relaciones (opcionales, cargadas bajo demanda)
    parametros: List[ConsultaSQLParametro] = field(default_factory=list)

    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> "ConsultaSQLCatalogo":
        """Crea instancia desde fila de SQL."""
        def to_iso(val):
            if val and hasattr(val, 'isoformat'):
                return val.isoformat()
            return val
        
        uuid_val = row.get('PublicUUID', '')
        if uuid_val and hasattr(uuid_val, 'lower'):
            uuid_val = str(uuid_val).lower()
        
        return cls(
            consulta_id=row.get('ConsultaID', 0),
            public_uuid=uuid_val,
            codigo_consulta=row.get('CodigoConsulta', ''),
            nombre_consulta=row.get('NombreConsulta', ''),
            descripcion=row.get('Descripcion'),
            modulo=row.get('Modulo', 'General'),
            tipo_consulta=row.get('TipoConsulta', 'CONSULTA'),
            sistema_tipo_id=row.get('SistemaTipoID', 1),
            consulta_sql=row.get('ConsultaSQL', ''),
            es_sistema=bool(row.get('EsSistema', False)),
            es_personalizada=bool(row.get('EsPersonalizada', False)),
            es_sincronizable=bool(row.get('EsSincronizable', False)),
            permite_ejecucion_manual=bool(row.get('PermiteEjecucionManual', True)),
            solo_lectura=bool(row.get('SoloLectura', True)),
            requiere_autorizacion=bool(row.get('RequiereAutorizacion', False)),
            activo=bool(row.get('Activo', True)),
            version=row.get('Version', 1),
            config_origen=row.get('ConfigOrigen', 'LEGACY_PYTHON'),
            fecha_creacion=to_iso(row.get('FechaCreacion')),
            usuario_creacion_id=row.get('UsuarioCreacionID'),
            fecha_modificacion=to_iso(row.get('FechaModificacion')),
            usuario_modificacion_id=row.get('UsuarioModificacionID'),
        )

    def to_dict(self, include_sql: bool = True) -> Dict[str, Any]:
        """
        Serializa a diccionario.
        
        Args:
            include_sql: Si True, incluye el campo consulta_sql.
                        Si False, lo omite por seguridad.
        """
        result = {
            'consulta_id': self.consulta_id,
            'public_uuid': self.public_uuid,
            'codigo_consulta': self.codigo_consulta,
            'nombre_consulta': self.nombre_consulta,
            'descripcion': self.descripcion,
            'modulo': self.modulo,
            'tipo_consulta': self.tipo_consulta,
            'sistema_tipo_id': self.sistema_tipo_id,
            'es_sistema': self.es_sistema,
            'es_personalizada': self.es_personalizada,
            'es_sincronizable': self.es_sincronizable,
            'permite_ejecucion_manual': self.permite_ejecucion_manual,
            'solo_lectura': self.solo_lectura,
            'requiere_autorizacion': self.requiere_autorizacion,
            'activo': self.activo,
            'version': self.version,
            'config_origen': self.config_origen,
            'fecha_creacion': self.fecha_creacion,
            'usuario_creacion_id': self.usuario_creacion_id,
            'fecha_modificacion': self.fecha_modificacion,
            'usuario_modificacion_id': self.usuario_modificacion_id,
        }
        
        if include_sql:
            result['consulta_sql'] = self.consulta_sql
        
        if self.parametros:
            result['parametros'] = [p.to_dict() for p in self.parametros]
        
        return result

    def get_codigo_sistema(self) -> str:
        """Devuelve el código del sistema basado en sistema_tipo_id."""
        # Mapeo de SistemaTipoID a código
        sistemas = {
            1: "SOFTRESTAURANT",
            2: "MPRO",
            3: "API",
        }
        return sistemas.get(self.sistema_tipo_id, "UNKNOWN")


@dataclass
class ConsultaSQLFilter:
    """Filtros para búsqueda de consultas."""
    sistema_tipo_id: Optional[int] = None
    codigo_sistema: Optional[str] = None  # 'SOFTRESTAURANT', 'MPRO'
    modulo: Optional[str] = None
    activo: Optional[bool] = None
    solo_lectura: Optional[bool] = None
    es_sistema: Optional[bool] = None
    es_personalizada: Optional[bool] = None
    es_sincronizable: Optional[bool] = None
    permite_ejecucion_manual: Optional[bool] = None
    buscar: Optional[str] = None  # Búsqueda en nombre/descripcion
    limit: int = 100


@dataclass
class ConsultaSQLValidationResult:
    """
    Resultado de validación de una consulta SQL.
    """
    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    normalized_sql: Optional[str] = None
    detected_parameters: List[str] = field(default_factory=list)
    validation_timestamp: Optional[str] = None

    def add_error(self, code: str, message: str, severity: str = "ERROR", line: int = None):
        """Agrega un error de validación."""
        self.errors.append({
            'code': code,
            'message': message,
            'severity': severity,
            'line': line,
        })
        self.is_valid = False

    def add_warning(self, code: str, message: str, line: int = None):
        """Agrega un warning de validación."""
        self.warnings.append({
            'code': code,
            'message': message,
            'severity': 'WARNING',
            'line': line,
        })

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'normalized_sql': self.normalized_sql,
            'detected_parameters': self.detected_parameters,
            'validation_timestamp': self.validation_timestamp,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }


__all__ = [
    'TipoDatoParametro',
    'TipoConsulta',
    'SeveridadValidacion',
    'ConsultaSQLParametro',
    'ConsultaSQLVersion',
    'ConsultaSQLServidor',
    'ConsultaSQLCatalogo',
    'ConsultaSQLFilter',
    'ConsultaSQLValidationResult',
]
