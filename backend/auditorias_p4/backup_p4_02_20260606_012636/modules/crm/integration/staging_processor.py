from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - CRM Staging Processor
==================================
Procesa registros de staging y los mueve a tablas de producción.
Incluye lógica de deduplicación y matching.
"""

import logging
import pymssql
import json
import uuid
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from zoneinfo import ZoneInfo

from .base_connector import SyncStatus

logger = logging.getLogger(__name__)

MEXICO_TZ = ZoneInfo("America/Mexico_City")


class MatchAction(str, Enum):
    """Acción a tomar cuando se encuentra un match"""
    CREAR_NUEVO = "CREAR_NUEVO"
    ACTUALIZAR_EXISTENTE = "ACTUALIZAR_EXISTENTE"
    MARCAR_CONFLICTO = "MARCAR_CONFLICTO"
    OMITIR = "OMITIR"


class MatchType(str, Enum):
    """Tipo de match encontrado"""
    EMAIL_EXACTO = "EMAIL_EXACTO"
    TELEFONO_EXACTO = "TELEFONO_EXACTO"
    NOMBRE_EMPRESA = "NOMBRE_EMPRESA"
    RFC_EXACTO = "RFC_EXACTO"
    RAZON_SOCIAL = "RAZON_SOCIAL"
    SIN_MATCH = "SIN_MATCH"


@dataclass
class MatchResult:
    """Resultado de búsqueda de duplicados"""
    encontrado: bool = False
    tipo_match: MatchType = MatchType.SIN_MATCH
    registro_existente_id: Optional[str] = None
    score_confianza: int = 0  # 0-100
    detalles: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessResult:
    """Resultado del procesamiento de staging"""
    success: bool = True
    total_procesados: int = 0
    creados: int = 0
    actualizados: int = 0
    conflictos: int = 0
    errores: int = 0
    omitidos: int = 0
    mensajes: List[str] = field(default_factory=list)


class StagingProcessor:
    """
    Procesador que mueve registros de staging a producción.
    Implementa deduplicación y matching inteligente.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def _get_connection(self):
        return pymssql.connect(
            server=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password'],
            login_timeout=30,
            timeout=60,
            autocommit=False
        )
    
    def _now(self) -> datetime:
        return datetime.now(MEXICO_TZ).replace(tzinfo=None)
    
    def _generate_uuid(self) -> str:
        return str(uuid.uuid4())
    
    # ============================================================
    # PROCESAMIENTO PRINCIPAL
    # ============================================================
    
    def process_staging(
        self,
        conector_id: int,
        empresa_id: str,
        entidades: List[str] = None,
        accion_duplicados: MatchAction = MatchAction.MARCAR_CONFLICTO,
        limit: int = 100
    ) -> ProcessResult:
        """
        Procesa registros pendientes de staging y los mueve a producción.
        
        Args:
            conector_id: ID del conector
            empresa_id: ID de la empresa destino
            entidades: Lista de entidades a procesar ['leads', 'oportunidades', 'cuentas']
            accion_duplicados: Qué hacer cuando se encuentra un duplicado
            limit: Máximo de registros a procesar por entidad
            
        Returns:
            ProcessResult con estadísticas
        """
        if entidades is None:
            entidades = ['leads', 'cuentas', 'oportunidades']
        
        result = ProcessResult()
        
        for entidad in entidades:
            try:
                if entidad == 'leads':
                    self._process_leads(conector_id, empresa_id, accion_duplicados, limit, result)
                elif entidad == 'cuentas':
                    self._process_cuentas(conector_id, empresa_id, accion_duplicados, limit, result)
                elif entidad == 'oportunidades':
                    self._process_oportunidades(conector_id, empresa_id, accion_duplicados, limit, result)
            except Exception as e:
                logger.error(f"[StagingProcessor] Error procesando {entidad}: {e}")
                result.errores += 1
                result.mensajes.append(f"Error en {entidad}: {str(e)}")
        
        result.success = result.errores == 0
        return result
    
    # ============================================================
    # LEADS
    # ============================================================
    
    def _process_leads(
        self,
        conector_id: int,
        empresa_id: str,
        accion_duplicados: MatchAction,
        limit: int,
        result: ProcessResult
    ):
        """Procesa leads de staging"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener leads pendientes
            cursor.execute("""
                SELECT * FROM CRM_Staging_Leads
                WHERE ConectorID = %s AND EstadoSync = 'PENDIENTE'
                ORDER BY CreatedAt ASC
            """, (conector_id,))
            
            staging_leads = cursor.fetchall()
            
            for staging in staging_leads[:limit]:
                result.total_procesados += 1
                
                try:
                    # Buscar duplicados
                    match = self._find_lead_match(cursor, empresa_id, staging)
                    
                    if match.encontrado:
                        if accion_duplicados == MatchAction.CREAR_NUEVO:
                            # Crear nuevo de todos modos
                            self._create_lead_from_staging(cursor, empresa_id, staging)
                            result.creados += 1
                            self._mark_staging_processed(cursor, 'CRM_Staging_Leads', 
                                staging['StagingID'], None, SyncStatus.SINCRONIZADO)
                            
                        elif accion_duplicados == MatchAction.ACTUALIZAR_EXISTENTE:
                            # Actualizar el existente
                            self._update_lead_from_staging(cursor, match.registro_existente_id, staging)
                            result.actualizados += 1
                            self._mark_staging_processed(cursor, 'CRM_Staging_Leads',
                                staging['StagingID'], match.registro_existente_id, SyncStatus.SINCRONIZADO)
                            
                        elif accion_duplicados == MatchAction.MARCAR_CONFLICTO:
                            # Marcar como conflicto para revisión manual
                            result.conflictos += 1
                            self._mark_staging_conflict(cursor, 'CRM_Staging_Leads',
                                staging['StagingID'], match)
                            
                        else:  # OMITIR
                            result.omitidos += 1
                            self._mark_staging_processed(cursor, 'CRM_Staging_Leads',
                                staging['StagingID'], match.registro_existente_id, SyncStatus.SINCRONIZADO,
                                "Omitido por duplicado")
                    else:
                        # No hay duplicado, crear nuevo
                        new_lead_id = self._create_lead_from_staging(cursor, empresa_id, staging)
                        result.creados += 1
                        self._mark_staging_processed(cursor, 'CRM_Staging_Leads',
                            staging['StagingID'], new_lead_id, SyncStatus.SINCRONIZADO)
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    result.errores += 1
                    logger.error(f"[StagingProcessor] Error procesando lead {staging['StagingID']}: {e}")
                    self._mark_staging_error(conn, 'CRM_Staging_Leads', staging['StagingID'], str(e))
            
            logger.info(f"[StagingProcessor] Leads procesados: {result.total_procesados}")
            
        finally:
            conn.close()
    
    def _find_lead_match(self, cursor, empresa_id: str, staging: Dict) -> MatchResult:
        """Busca duplicados de un lead por email o teléfono"""
        result = MatchResult()
        
        # 1. Match por email (alta confianza)
        if staging.get('Email'):
            cursor.execute("""
                SELECT LeadID, NombreContacto, Email
                FROM CRM_Leads
                WHERE EmpresaID = %s AND Email = %s AND Activo = 1
            """, (empresa_id, staging['Email']))
            
            match = cursor.fetchone()
            if match:
                result.encontrado = True
                result.tipo_match = MatchType.EMAIL_EXACTO
                result.registro_existente_id = str(match['LeadID'])
                result.score_confianza = 95
                result.detalles = {
                    'campo': 'Email',
                    'valor': staging['Email'],
                    'existente': match['NombreContacto']
                }
                return result
        
        # 2. Match por teléfono
        if staging.get('Telefono'):
            cursor.execute("""
                SELECT LeadID, NombreContacto, Telefono
                FROM CRM_Leads
                WHERE EmpresaID = %s AND Telefono = %s AND Activo = 1
            """, (empresa_id, staging['Telefono']))
            
            match = cursor.fetchone()
            if match:
                result.encontrado = True
                result.tipo_match = MatchType.TELEFONO_EXACTO
                result.registro_existente_id = str(match['LeadID'])
                result.score_confianza = 80
                result.detalles = {
                    'campo': 'Telefono',
                    'valor': staging['Telefono'],
                    'existente': match['NombreContacto']
                }
                return result
        
        # 3. Match por nombre de empresa (baja confianza)
        if staging.get('NombreEmpresa'):
            cursor.execute("""
                SELECT LeadID, NombreContacto, NombreEmpresa
                FROM CRM_Leads
                WHERE EmpresaID = %s AND NombreEmpresa = %s AND Activo = 1
            """, (empresa_id, staging['NombreEmpresa']))
            
            match = cursor.fetchone()
            if match:
                result.encontrado = True
                result.tipo_match = MatchType.NOMBRE_EMPRESA
                result.registro_existente_id = str(match['LeadID'])
                result.score_confianza = 60
                result.detalles = {
                    'campo': 'NombreEmpresa',
                    'valor': staging['NombreEmpresa'],
                    'existente': match['NombreContacto']
                }
                return result
        
        return result
    
    def _create_lead_from_staging(self, cursor, empresa_id: str, staging: Dict) -> str:
        """Crea un lead en producción desde staging"""
        lead_id = self._generate_uuid()
        now = self._now()
        
        # Generar folio
        prefix = f"LEAD-{now.strftime('%Y%m')}"
        cursor.execute("""
            SELECT COUNT(*) + 1 as seq FROM CRM_Leads 
            WHERE EmpresaID = %s AND FolioLead LIKE %s
        """, (empresa_id, f"{prefix}%"))
        seq = cursor.fetchone()['seq']
        folio = f"{prefix}-{seq:04d}"
        
        cursor.execute("""
            INSERT INTO CRM_Leads (
                LeadID, EmpresaID, FolioLead, NombreContacto, ApellidoPaterno,
                ApellidoMaterno, NombreEmpresa, Email, Telefono, TelefonoMovil,
                Puesto, Descripcion, EstatusLeadID, Activo, CreatedAt, UpdatedAt
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            lead_id,
            empresa_id,
            folio,
            staging.get('NombreContacto', 'Sin nombre'),
            staging.get('ApellidoPaterno'),
            staging.get('ApellidoMaterno'),
            staging.get('NombreEmpresa'),
            staging.get('Email'),
            staging.get('Telefono'),
            staging.get('TelefonoMovil'),
            staging.get('Puesto'),
            staging.get('Descripcion'),
            1,  # EstatusLeadID = NUEVO
            1,  # Activo
            now,
            now
        ))
        
        logger.debug(f"[StagingProcessor] Lead creado: {folio}")
        return lead_id
    
    def _update_lead_from_staging(self, cursor, lead_id: str, staging: Dict):
        """Actualiza un lead existente desde staging"""
        cursor.execute("""
            UPDATE CRM_Leads SET
                NombreContacto = COALESCE(%s, NombreContacto),
                ApellidoPaterno = COALESCE(%s, ApellidoPaterno),
                NombreEmpresa = COALESCE(%s, NombreEmpresa),
                Telefono = COALESCE(%s, Telefono),
                TelefonoMovil = COALESCE(%s, TelefonoMovil),
                Puesto = COALESCE(%s, Puesto),
                UpdatedAt = %s
            WHERE LeadID = %s
        """, (
            staging.get('NombreContacto'),
            staging.get('ApellidoPaterno'),
            staging.get('NombreEmpresa'),
            staging.get('Telefono'),
            staging.get('TelefonoMovil'),
            staging.get('Puesto'),
            self._now(),
            lead_id
        ))
        
        logger.debug(f"[StagingProcessor] Lead actualizado: {lead_id}")
    
    # ============================================================
    # CUENTAS
    # ============================================================
    
    def _process_cuentas(
        self,
        conector_id: int,
        empresa_id: str,
        accion_duplicados: MatchAction,
        limit: int,
        result: ProcessResult
    ):
        """Procesa cuentas de staging"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT * FROM CRM_Staging_Cuentas
                WHERE ConectorID = %s AND EstadoSync = 'PENDIENTE'
                ORDER BY CreatedAt ASC
            """, (conector_id,))
            
            staging_cuentas = cursor.fetchall()
            
            for staging in staging_cuentas[:limit]:
                result.total_procesados += 1
                
                try:
                    match = self._find_cuenta_match(cursor, empresa_id, staging)
                    
                    if match.encontrado:
                        if accion_duplicados == MatchAction.CREAR_NUEVO:
                            self._create_cuenta_from_staging(cursor, empresa_id, staging)
                            result.creados += 1
                            self._mark_staging_processed(cursor, 'CRM_Staging_Cuentas',
                                staging['StagingID'], None, SyncStatus.SINCRONIZADO)
                            
                        elif accion_duplicados == MatchAction.ACTUALIZAR_EXISTENTE:
                            self._update_cuenta_from_staging(cursor, match.registro_existente_id, staging)
                            result.actualizados += 1
                            self._mark_staging_processed(cursor, 'CRM_Staging_Cuentas',
                                staging['StagingID'], match.registro_existente_id, SyncStatus.SINCRONIZADO)
                            
                        elif accion_duplicados == MatchAction.MARCAR_CONFLICTO:
                            result.conflictos += 1
                            self._mark_staging_conflict(cursor, 'CRM_Staging_Cuentas',
                                staging['StagingID'], match)
                            
                        else:
                            result.omitidos += 1
                            self._mark_staging_processed(cursor, 'CRM_Staging_Cuentas',
                                staging['StagingID'], match.registro_existente_id, SyncStatus.SINCRONIZADO,
                                "Omitido por duplicado")
                    else:
                        new_cuenta_id = self._create_cuenta_from_staging(cursor, empresa_id, staging)
                        result.creados += 1
                        self._mark_staging_processed(cursor, 'CRM_Staging_Cuentas',
                            staging['StagingID'], new_cuenta_id, SyncStatus.SINCRONIZADO)
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    result.errores += 1
                    logger.error(f"[StagingProcessor] Error procesando cuenta {staging['StagingID']}: {e}")
                    self._mark_staging_error(conn, 'CRM_Staging_Cuentas', staging['StagingID'], str(e))
            
            logger.info(f"[StagingProcessor] Cuentas procesadas en este batch")
            
        finally:
            conn.close()
    
    def _find_cuenta_match(self, cursor, empresa_id: str, staging: Dict) -> MatchResult:
        """Busca duplicados de cuenta por RFC o razón social"""
        result = MatchResult()
        
        # 1. Match por RFC (alta confianza)
        if staging.get('RFC'):
            cursor.execute("""
                SELECT ClienteID, RazonSocial, RFC
                FROM Cliente_Catalogo
                WHERE RFC = %s AND Activo = 1
            """, (staging['RFC'],))
            
            match = cursor.fetchone()
            if match:
                result.encontrado = True
                result.tipo_match = MatchType.RFC_EXACTO
                result.registro_existente_id = str(match['ClienteID'])
                result.score_confianza = 98
                result.detalles = {
                    'campo': 'RFC',
                    'valor': staging['RFC'],
                    'existente': match['RazonSocial']
                }
                return result
        
        # 2. Match por razón social exacta
        if staging.get('RazonSocial'):
            cursor.execute("""
                SELECT ClienteID, RazonSocial
                FROM Cliente_Catalogo
                WHERE RazonSocial = %s AND Activo = 1
            """, (staging['RazonSocial'],))
            
            match = cursor.fetchone()
            if match:
                result.encontrado = True
                result.tipo_match = MatchType.RAZON_SOCIAL
                result.registro_existente_id = str(match['ClienteID'])
                result.score_confianza = 85
                result.detalles = {
                    'campo': 'RazonSocial',
                    'valor': staging['RazonSocial'],
                    'existente': match['RazonSocial']
                }
                return result
        
        return result
    
    def _create_cuenta_from_staging(self, cursor, empresa_id: str, staging: Dict) -> str:
        """Crea una cuenta/cliente en producción desde staging"""
        now = self._now()
        public_uuid = self._generate_uuid()
        
        # Generar código de cliente único
        prefix = f"CLI-{now.strftime('%Y%m')}"
        cursor.execute("""
            SELECT COUNT(*) + 1 as seq FROM Cliente_Catalogo
            WHERE CodigoCliente LIKE %s
        """, (f"{prefix}%",))
        seq = cursor.fetchone()['seq']
        codigo_cliente = f"{prefix}-{seq:04d}"
        
        # RFC no puede ser NULL, usar genérico si no hay (único por timestamp)
        rfc = staging.get('RFC')
        if not rfc:
            import random
            rfc = f"XAXX{now.strftime('%d%m%y')}{random.randint(100,999)}"
        
        cursor.execute("""
            INSERT INTO Cliente_Catalogo (
                CodigoCliente, RazonSocial, NombreComercial, RFC, TipoPersona,
                MonedaID, DiasCredito, DescuentoMaximoPorcentaje,
                PortalHabilitado, BloqueadoVenta, Pais,
                SitioWeb, EmailPrincipal, TelefonoPrincipal, Observaciones,
                PublicUUID, Activo, FechaAlta
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            codigo_cliente,
            staging.get('RazonSocial', 'Sin nombre'),
            staging.get('NombreComercial'),
            rfc,
            'M',  # TipoPersona: M=Moral, F=Física
            1,    # MonedaID: 1=MXN
            30,   # DiasCredito default
            0,    # DescuentoMaximoPorcentaje
            0,    # PortalHabilitado
            0,    # BloqueadoVenta
            'México',
            staging.get('SitioWeb'),
            staging.get('EmailPrincipal'),
            staging.get('TelefonoPrincipal'),
            f"Importado de CRM externo. Industria: {staging.get('Industria', 'N/A')} | Dirección: {staging.get('Direccion', 'N/A')}",
            public_uuid,
            1,    # Activo
            now
        ))
        
        logger.debug(f"[StagingProcessor] Cuenta creada: {codigo_cliente} - {staging.get('RazonSocial')}")
        # Retornamos el PublicUUID que es uniqueidentifier, compatible con LocalCuentaID
        return public_uuid
    
    def _update_cuenta_from_staging(self, cursor, cliente_id: str, staging: Dict):
        """Actualiza una cuenta existente desde staging"""
        cursor.execute("""
            UPDATE Cliente_Catalogo SET
                NombreComercial = COALESCE(%s, NombreComercial),
                SitioWeb = COALESCE(%s, SitioWeb),
                EmailPrincipal = COALESCE(%s, EmailPrincipal),
                TelefonoPrincipal = COALESCE(%s, TelefonoPrincipal)
            WHERE ClienteID = %s
        """, (
            staging.get('NombreComercial'),
            staging.get('SitioWeb'),
            staging.get('EmailPrincipal'),
            staging.get('TelefonoPrincipal'),
            cliente_id
        ))
        
        logger.debug(f"[StagingProcessor] Cuenta actualizada: {cliente_id}")
    
    # ============================================================
    # OPORTUNIDADES
    # ============================================================
    
    def _process_oportunidades(
        self,
        conector_id: int,
        empresa_id: str,
        accion_duplicados: MatchAction,
        limit: int,
        result: ProcessResult
    ):
        """Procesa oportunidades de staging"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT * FROM CRM_Staging_Oportunidades
                WHERE ConectorID = %s AND EstadoSync = 'PENDIENTE'
                ORDER BY CreatedAt ASC
            """, (conector_id,))
            
            staging_opps = cursor.fetchall()
            
            for staging in staging_opps[:limit]:
                result.total_procesados += 1
                
                try:
                    # Las oportunidades se crean siempre (raramente hay duplicados)
                    new_opp_id = self._create_oportunidad_from_staging(cursor, empresa_id, staging)
                    result.creados += 1
                    self._mark_staging_processed(cursor, 'CRM_Staging_Oportunidades',
                        staging['StagingID'], new_opp_id, SyncStatus.SINCRONIZADO)
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    result.errores += 1
                    logger.error(f"[StagingProcessor] Error procesando oportunidad {staging['StagingID']}: {e}")
                    self._mark_staging_error(conn, 'CRM_Staging_Oportunidades', staging['StagingID'], str(e))
            
            logger.info(f"[StagingProcessor] Oportunidades procesadas en este batch")
            
        finally:
            conn.close()
    
    def _create_oportunidad_from_staging(self, cursor, empresa_id: str, staging: Dict) -> str:
        """Crea una oportunidad en producción desde staging"""
        opp_id = self._generate_uuid()
        now = self._now()
        
        # Generar folio
        prefix = f"OPP-{now.strftime('%Y%m')}"
        cursor.execute("""
            SELECT COUNT(*) + 1 as seq FROM CRM_Oportunidades
            WHERE EmpresaID = %s AND FolioOportunidad LIKE %s
        """, (empresa_id, f"{prefix}%"))
        seq = cursor.fetchone()['seq']
        folio = f"{prefix}-{seq:04d}"
        
        # Obtener pipeline y etapa por defecto
        cursor.execute("""
            SELECT TOP 1 PipelineID FROM CRM_Config_Pipelines
            WHERE EmpresaID = %s AND EsPrincipal = 1
        """, (empresa_id,))
        pipeline_row = cursor.fetchone()
        pipeline_id = pipeline_row['PipelineID'] if pipeline_row else 1
        
        cursor.execute("""
            SELECT TOP 1 EtapaID FROM CRM_Config_Etapas_Pipeline
            WHERE PipelineID = %s
            ORDER BY OrdenEtapa ASC
        """, (pipeline_id,))
        etapa_row = cursor.fetchone()
        etapa_id = etapa_row['EtapaID'] if etapa_row else 1
        
        cursor.execute("""
            INSERT INTO CRM_Oportunidades (
                OportunidadID, EmpresaID, FolioOportunidad, NombreOportunidad,
                DescripcionOportunidad, PipelineID, EtapaActualID, ProbabilidadActual,
                MontoEstimado, MonedaID, FechaApertura, FechaEstimadaCierre,
                EstatusOportunidadID, Activo, CreatedAt, UpdatedAt
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            opp_id,
            empresa_id,
            folio,
            staging.get('NombreOportunidad', 'Oportunidad importada'),
            staging.get('Descripcion'),
            pipeline_id,
            etapa_id,
            staging.get('Probabilidad', 10),
            staging.get('MontoEstimado', 0),
            1,  # MXN por defecto
            now,
            staging.get('FechaEstimadaCierre'),
            1,  # Estatus: Abierta
            1,  # Activo
            now,
            now
        ))
        
        logger.debug(f"[StagingProcessor] Oportunidad creada: {folio}")
        return opp_id
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _mark_staging_processed(
        self,
        cursor,
        table: str,
        staging_id: int,
        local_id: Optional[str],
        status: SyncStatus,
        error_msg: str = None
    ):
        """Marca un registro de staging como procesado"""
        local_field = {
            'CRM_Staging_Leads': 'LocalLeadID',
            'CRM_Staging_Cuentas': 'LocalCuentaID',
            'CRM_Staging_Oportunidades': 'LocalOportunidadID'
        }.get(table, 'LocalLeadID')
        
        cursor.execute(f"""
            UPDATE {table} SET
                {local_field} = %s,
                EstadoSync = %s,
                FechaProcesado = %s,
                FechaLocal = %s,
                MensajeError = %s,
                Intentos = Intentos + 1,
                UpdatedAt = %s
            WHERE StagingID = %s
        """, (
            local_id,
            status.value,
            self._now(),
            self._now() if status == SyncStatus.SINCRONIZADO else None,
            error_msg,
            self._now(),
            staging_id
        ))
    
    def _mark_staging_conflict(self, cursor, table: str, staging_id: int, match: MatchResult):
        """Marca un registro de staging como conflicto"""
        local_field = {
            'CRM_Staging_Leads': 'LocalLeadID',
            'CRM_Staging_Cuentas': 'LocalCuentaID',
            'CRM_Staging_Oportunidades': 'LocalOportunidadID'
        }.get(table, 'LocalLeadID')
        
        conflict_info = json.dumps({
            'tipo_match': match.tipo_match.value,
            'registro_existente': match.registro_existente_id,
            'score': match.score_confianza,
            'detalles': match.detalles
        })
        
        cursor.execute(f"""
            UPDATE {table} SET
                {local_field} = %s,
                EstadoSync = %s,
                MensajeError = %s,
                Intentos = Intentos + 1,
                UpdatedAt = %s
            WHERE StagingID = %s
        """, (
            match.registro_existente_id,
            SyncStatus.CONFLICTO.value,
            conflict_info,
            self._now(),
            staging_id
        ))
    
    def _mark_staging_error(self, conn, table: str, staging_id: int, error_msg: str):
        """Marca un registro con error"""
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {table} SET
                    EstadoSync = %s,
                    MensajeError = %s,
                    Intentos = Intentos + 1,
                    UpdatedAt = %s
                WHERE StagingID = %s
            """, (
                SyncStatus.ERROR.value,
                error_msg[:500],
                self._now(),
                staging_id
            ))
            conn.commit()
        except:
            pass
    
    # ============================================================
    # RESOLUCIÓN DE CONFLICTOS
    # ============================================================
    
    def get_conflicts(self, conector_id: int, entidad: str = 'leads') -> List[Dict]:
        """Obtiene registros en conflicto"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            table = {
                'leads': 'CRM_Staging_Leads',
                'cuentas': 'CRM_Staging_Cuentas',
                'oportunidades': 'CRM_Staging_Oportunidades'
            }.get(entidad, 'CRM_Staging_Leads')
            
            cursor.execute(f"""
                SELECT * FROM {table}
                WHERE ConectorID = %s AND EstadoSync = 'CONFLICTO'
                ORDER BY CreatedAt DESC
            """, (conector_id,))
            
            conflicts = []
            for row in cursor.fetchall():
                conflict = dict(row)
                # Parsear detalles del conflicto
                if conflict.get('MensajeError'):
                    try:
                        conflict['ConflictDetails'] = json.loads(conflict['MensajeError'])
                    except:
                        pass
                conflicts.append(conflict)
            
            return conflicts
            
        finally:
            conn.close()
    
    def resolve_conflict(
        self,
        staging_id: int,
        entidad: str,
        accion: MatchAction,
        empresa_id: str
    ) -> Dict[str, Any]:
        """
        Resuelve un conflicto específico.
        
        Args:
            staging_id: ID del registro en staging
            entidad: 'leads', 'cuentas' u 'oportunidades'
            accion: CREAR_NUEVO, ACTUALIZAR_EXISTENTE u OMITIR
            empresa_id: ID de empresa destino
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            table = {
                'leads': 'CRM_Staging_Leads',
                'cuentas': 'CRM_Staging_Cuentas',
                'oportunidades': 'CRM_Staging_Oportunidades'
            }.get(entidad)
            
            if not table:
                return {"success": False, "error": "Entidad no válida"}
            
            # Obtener registro
            cursor.execute(f"SELECT * FROM {table} WHERE StagingID = %s", (staging_id,))
            staging = cursor.fetchone()
            
            if not staging:
                return {"success": False, "error": "Registro no encontrado"}
            
            # Obtener ID del registro existente del conflicto
            existing_id = None
            if staging.get('MensajeError'):
                try:
                    conflict_info = json.loads(staging['MensajeError'])
                    existing_id = conflict_info.get('registro_existente')
                except:
                    pass
            
            if accion == MatchAction.CREAR_NUEVO:
                if entidad == 'leads':
                    new_id = self._create_lead_from_staging(cursor, empresa_id, staging)
                elif entidad == 'cuentas':
                    new_id = self._create_cuenta_from_staging(cursor, empresa_id, staging)
                else:
                    new_id = self._create_oportunidad_from_staging(cursor, empresa_id, staging)
                
                self._mark_staging_processed(cursor, table, staging_id, new_id, SyncStatus.SINCRONIZADO)
                conn.commit()
                return {"success": True, "action": "created", "new_id": new_id}
                
            elif accion == MatchAction.ACTUALIZAR_EXISTENTE and existing_id:
                if entidad == 'leads':
                    self._update_lead_from_staging(cursor, existing_id, staging)
                elif entidad == 'cuentas':
                    self._update_cuenta_from_staging(cursor, existing_id, staging)
                
                self._mark_staging_processed(cursor, table, staging_id, existing_id, SyncStatus.SINCRONIZADO)
                conn.commit()
                return {"success": True, "action": "updated", "existing_id": existing_id}
                
            elif accion == MatchAction.OMITIR:
                self._mark_staging_processed(cursor, table, staging_id, existing_id, 
                    SyncStatus.SINCRONIZADO, "Resuelto: Omitido por usuario")
                conn.commit()
                return {"success": True, "action": "skipped"}
            
            return {"success": False, "error": "Acción no válida o registro existente no encontrado"}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
