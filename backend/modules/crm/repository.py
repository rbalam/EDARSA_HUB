"""
EDARSA HUB - CRM Enterprise Repository
=======================================
Operaciones de base de datos SQL Server para el módulo CRM nativo.
Todas las operaciones son contra EDARSAHUB (SQL Server).
"""

import logging
import pymssql
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}

MEXICO_TZ = ZoneInfo("America/Mexico_City")


def get_connection():
    """Obtiene conexión a EDARSAHUB"""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['username'],
        password=EDARSAHUB_CONFIG['password'],
        login_timeout=30,
        timeout=60,
        autocommit=False
    )


def now_mexico() -> datetime:
    """Retorna datetime actual en zona horaria México"""
    return datetime.now(MEXICO_TZ).replace(tzinfo=None)


# ============================================================================
# LEADS REPOSITORY
# ============================================================================

class LeadsRepository:
    """Repositorio para operaciones de Leads"""
    
    @staticmethod
    def generar_folio(cursor, empresa_id) -> str:
        """Genera folio único para Lead: LEAD-YYYYMM-XXXX"""
        prefix = f"LEAD-{now_mexico().strftime('%Y%m')}"
        cursor.execute("""
            SELECT COUNT(*) + 1 as seq 
            FROM CRM_Leads 
            WHERE EmpresaID = %s 
            AND FolioLead LIKE %s
        """, (str(empresa_id), f"{prefix}%"))
        row = cursor.fetchone()
        # cursor es as_dict=True, row es dict
        seq = row.get('seq', 1) if isinstance(row, dict) else (row[0] if row else 1)
        return f"{prefix}-{seq:04d}"
    
    @staticmethod
    def crear(data: Dict[str, Any], user_id) -> Dict[str, Any]:
        """Crea un nuevo Lead"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            empresa_id = data['empresa_id']
            folio = LeadsRepository.generar_folio(cursor, empresa_id)
            now = now_mexico()
            
            # Preparar parámetros con logging
            params = (
                str(empresa_id),
                str(data.get('sucursal_id')) if data.get('sucursal_id') else None,
                folio,
                data['nombre_contacto'],
                data.get('apellido_paterno'),
                data.get('apellido_materno'),
                data.get('nombre_empresa'),
                data.get('puesto'),
                data.get('email'),
                data.get('telefono'),
                data.get('telefono_movil'),
                data.get('origen_lead_id'),
                1,  # EstatusLeadID = NUEVO
                data.get('prioridad_id'),
                str(data.get('ejecutivo_asignado_user_id')) if data.get('ejecutivo_asignado_user_id') else None,
                now if data.get('ejecutivo_asignado_user_id') else None,
                data.get('descripcion'),
                data.get('presupuesto'),
                data.get('fecha_estimada_cierre'),
                str(user_id),
                now,
                now
            )
            
            logger.info(f"[CRM] Creando lead con {len(params)} params, empresa={empresa_id}, user={user_id}")
            
            cursor.execute("""
                INSERT INTO CRM_Leads (
                    EmpresaID, SucursalID, FolioLead,
                    NombreContacto, ApellidoPaterno, ApellidoMaterno,
                    NombreEmpresa, Puesto, Email, Telefono, TelefonoMovil,
                    OrigenLeadID, EstatusLeadID, PrioridadID,
                    EjecutivoAsignadoUserID, FechaAsignacion,
                    Descripcion, Presupuesto, FechaEstimadaCierre,
                    Activo, CreatedBy, CreatedAt, UpdatedAt
                )
                OUTPUT INSERTED.LeadID, INSERTED.FolioLead
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s
                )
            """, params)
            
            result = cursor.fetchone()
            conn.commit()
            
            logger.info(f"[CRM] Lead creado: {folio}")
            return LeadsRepository.obtener_por_id(result['LeadID'])
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando lead: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def obtener_por_id(lead_id) -> Optional[Dict[str, Any]]:
        """Obtiene un Lead por ID con datos expandidos"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT 
                    l.*,
                    o.Nombre as OrigenNombre,
                    e.Nombre as EstatusNombre,
                    e.ColorHex as EstatusColor,
                    p.Nombre as PrioridadNombre,
                    CONCAT(u.Nombre, ' ', u.Apellidos) as EjecutivoNombre
                FROM CRM_Leads l
                LEFT JOIN CRM_Cat_OrigenLead o ON l.OrigenLeadID = o.OrigenID
                LEFT JOIN CRM_Cat_EstatusLead e ON l.EstatusLeadID = e.EstatusID
                LEFT JOIN CRM_Cat_Prioridades p ON l.PrioridadID = p.PrioridadID
                LEFT JOIN Usuario_Catalogo u ON l.EjecutivoAsignadoUserID = u.PublicUUID
                WHERE l.LeadID = %s AND l.Activo = 1
            """, (str(lead_id),))
            
            row = cursor.fetchone()
            if row:
                return LeadsRepository._map_lead(row)
            return None
            
        finally:
            conn.close()
    
    @staticmethod
    def listar(
        empresa_id: UUID,
        estatus_id: Optional[int] = None,
        ejecutivo_id: Optional[UUID] = None,
        origen_id: Optional[int] = None,
        busqueda: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """Lista leads con filtros y paginación"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ["l.EmpresaID = %s", "l.Activo = 1"]
            params = [str(empresa_id)]
            
            if estatus_id:
                where_clauses.append("l.EstatusLeadID = %s")
                params.append(estatus_id)
            
            if ejecutivo_id:
                where_clauses.append("l.EjecutivoAsignadoUserID = %s")
                params.append(str(ejecutivo_id))
            
            if origen_id:
                where_clauses.append("l.OrigenLeadID = %s")
                params.append(origen_id)
            
            if busqueda:
                where_clauses.append("""
                    (l.NombreContacto LIKE %s OR l.NombreEmpresa LIKE %s 
                     OR l.Email LIKE %s OR l.FolioLead LIKE %s)
                """)
                search_param = f"%{busqueda}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            where_sql = " AND ".join(where_clauses)
            
            # Contar total
            cursor.execute(f"SELECT COUNT(*) as total FROM CRM_Leads l WHERE {where_sql}", tuple(params))
            total = cursor.fetchone()['total']
            
            # Obtener página
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT 
                    l.*,
                    o.Nombre as OrigenNombre,
                    e.Nombre as EstatusNombre,
                    e.ColorHex as EstatusColor,
                    p.Nombre as PrioridadNombre,
                    CONCAT(u.Nombre, ' ', u.Apellidos) as EjecutivoNombre
                FROM CRM_Leads l
                LEFT JOIN CRM_Cat_OrigenLead o ON l.OrigenLeadID = o.OrigenID
                LEFT JOIN CRM_Cat_EstatusLead e ON l.EstatusLeadID = e.EstatusID
                LEFT JOIN CRM_Cat_Prioridades p ON l.PrioridadID = p.PrioridadID
                LEFT JOIN Usuario_Catalogo u ON l.EjecutivoAsignadoUserID = u.PublicUUID
                WHERE {where_sql}
                ORDER BY l.CreatedAt DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params) + (offset, page_size))
            
            leads = [LeadsRepository._map_lead(row) for row in cursor.fetchall()]
            return leads, total
            
        finally:
            conn.close()
    
    @staticmethod
    def actualizar(lead_id: UUID, data: Dict[str, Any], user_id: UUID) -> Optional[Dict[str, Any]]:
        """Actualiza un Lead existente"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Construir SET dinámico solo con campos proporcionados
            set_clauses = []
            params = []
            
            field_map = {
                'nombre_contacto': 'NombreContacto',
                'apellido_paterno': 'ApellidoPaterno',
                'apellido_materno': 'ApellidoMaterno',
                'nombre_empresa': 'NombreEmpresa',
                'puesto': 'Puesto',
                'email': 'Email',
                'telefono': 'Telefono',
                'telefono_movil': 'TelefonoMovil',
                'descripcion': 'Descripcion',
                'presupuesto': 'Presupuesto',
                'fecha_estimada_cierre': 'FechaEstimadaCierre',
                'origen_lead_id': 'OrigenLeadID',
                'estatus_lead_id': 'EstatusLeadID',
                'prioridad_id': 'PrioridadID',
            }
            
            for key, column in field_map.items():
                if key in data and data[key] is not None:
                    set_clauses.append(f"{column} = %s")
                    params.append(data[key])
            
            # Manejo especial de ejecutivo (actualiza fecha asignación)
            if 'ejecutivo_asignado_user_id' in data:
                set_clauses.append("EjecutivoAsignadoUserID = %s")
                set_clauses.append("FechaAsignacion = %s")
                params.append(str(data['ejecutivo_asignado_user_id']) if data['ejecutivo_asignado_user_id'] else None)
                params.append(now_mexico() if data['ejecutivo_asignado_user_id'] else None)
            
            if not set_clauses:
                return LeadsRepository.obtener_por_id(lead_id)
            
            set_clauses.append("UpdatedBy = %s")
            set_clauses.append("UpdatedAt = %s")
            params.extend([str(user_id), now_mexico()])
            
            params.append(str(lead_id))
            
            cursor.execute(f"""
                UPDATE CRM_Leads
                SET {', '.join(set_clauses)}
                WHERE LeadID = %s AND Activo = 1
            """, tuple(params))
            
            conn.commit()
            logger.info(f"[CRM] Lead actualizado: {lead_id}")
            return LeadsRepository.obtener_por_id(lead_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error actualizando lead: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def eliminar(lead_id: UUID, user_id: UUID) -> bool:
        """Elimina (soft delete) un Lead"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE CRM_Leads
                SET Activo = 0, DeletedAt = %s, UpdatedBy = %s, UpdatedAt = %s
                WHERE LeadID = %s
            """, (now_mexico(), str(user_id), now_mexico(), str(lead_id)))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error eliminando lead: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def descalificar(lead_id: UUID, motivo_id: int, notas: Optional[str], user_id: UUID) -> Optional[Dict]:
        """Descalifica un Lead"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE CRM_Leads
                SET Descalificado = 1,
                    MotivoDescalificacionID = %s,
                    FechaDescalificacion = %s,
                    NotasDescalificacion = %s,
                    EstatusLeadID = (SELECT EstatusID FROM CRM_Cat_EstatusLead WHERE Codigo = 'DESCALIFICADO'),
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE LeadID = %s AND Activo = 1
            """, (motivo_id, now_mexico(), notas, str(user_id), now_mexico(), str(lead_id)))
            conn.commit()
            return LeadsRepository.obtener_por_id(lead_id)
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error descalificando lead: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def _map_lead(row: Dict) -> Dict[str, Any]:
        """Mapea fila SQL a diccionario de respuesta"""
        return {
            'lead_id': row['LeadID'],
            'empresa_id': row['EmpresaID'],
            'sucursal_id': row.get('SucursalID'),
            'folio_lead': row.get('FolioLead'),
            'nombre_contacto': row['NombreContacto'],
            'apellido_paterno': row.get('ApellidoPaterno'),
            'apellido_materno': row.get('ApellidoMaterno'),
            'nombre_empresa': row.get('NombreEmpresa'),
            'puesto': row.get('Puesto'),
            'email': row.get('Email'),
            'telefono': row.get('Telefono'),
            'telefono_movil': row.get('TelefonoMovil'),
            'descripcion': row.get('Descripcion'),
            'presupuesto': float(row['Presupuesto']) if row.get('Presupuesto') else None,
            'fecha_estimada_cierre': row.get('FechaEstimadaCierre'),
            'origen_lead_id': row.get('OrigenLeadID'),
            'estatus_lead_id': row['EstatusLeadID'],
            'prioridad_id': row.get('PrioridadID'),
            'calificacion_lead_id': row.get('CalificacionLeadID'),
            'ejecutivo_asignado_user_id': row.get('EjecutivoAsignadoUserID'),
            'fecha_asignacion': row.get('FechaAsignacion'),
            'convertido_a_cuenta': bool(row.get('ConvertidoACuenta')),
            'descalificado': bool(row.get('Descalificado')),
            'activo': bool(row.get('Activo', True)),
            'created_at': row['CreatedAt'],
            'updated_at': row['UpdatedAt'],
            # Campos expandidos
            'origen_nombre': row.get('OrigenNombre'),
            'estatus_nombre': row.get('EstatusNombre'),
            'estatus_color': row.get('EstatusColor'),
            'prioridad_nombre': row.get('PrioridadNombre'),
            'ejecutivo_nombre': row.get('EjecutivoNombre'),
        }


# ============================================================================
# OPORTUNIDADES REPOSITORY
# ============================================================================

class OportunidadesRepository:
    """Repositorio para operaciones de Oportunidades"""
    
    @staticmethod
    def generar_folio(cursor, empresa_id) -> str:
        """Genera folio único para Oportunidad: OPP-YYYYMM-XXXX"""
        prefix = f"OPP-{now_mexico().strftime('%Y%m')}"
        cursor.execute("""
            SELECT COUNT(*) + 1 as seq 
            FROM CRM_Oportunidades 
            WHERE EmpresaID = %s 
            AND FolioOportunidad LIKE %s
        """, (str(empresa_id), f"{prefix}%"))
        row = cursor.fetchone()
        # cursor es as_dict=True, row es dict
        seq = row.get('seq', 1) if isinstance(row, dict) else (row[0] if row else 1)
        return f"{prefix}-{seq:04d}"
    
    @staticmethod
    def crear(data: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """Crea una nueva Oportunidad"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            empresa_id = data['empresa_id']
            folio = OportunidadesRepository.generar_folio(cursor, empresa_id)
            now = now_mexico()
            
            # Obtener probabilidad de la etapa inicial
            etapa_id = data.get('etapa_actual_id', 1)
            cursor.execute("""
                SELECT ProbabilidadDefault FROM CRM_Config_PipelineEtapas WHERE EtapaID = %s
            """, (etapa_id,))
            etapa = cursor.fetchone()
            probabilidad = etapa['ProbabilidadDefault'] if etapa else 10
            
            cursor.execute("""
                INSERT INTO CRM_Oportunidades (
                    EmpresaID, SucursalID, FolioOportunidad,
                    CuentaID, ContactoPrincipalID, LeadOrigenID,
                    NombreOportunidad, DescripcionOportunidad,
                    PipelineID, EtapaActualID, ProbabilidadActual,
                    MontoEstimado, MonedaID, FechaEstimadaCierre,
                    FechaApertura, FechaUltimaActividad,
                    EjecutivoResponsableUserID, PreventaResponsableUserID,
                    EstatusOportunidadID, ObservacionesInternas,
                    Activo, CreatedBy, CreatedAt, UpdatedAt
                )
                OUTPUT INSERTED.OportunidadID, INSERTED.FolioOportunidad
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s
                )
            """, (
                str(empresa_id),
                str(data.get('sucursal_id')) if data.get('sucursal_id') else None,
                folio,
                str(data.get('cuenta_id')) if data.get('cuenta_id') else None,
                str(data.get('contacto_principal_id')) if data.get('contacto_principal_id') else None,
                str(data.get('lead_origen_id')) if data.get('lead_origen_id') else None,
                data['nombre_oportunidad'],
                data.get('descripcion_oportunidad'),
                data.get('pipeline_id', 1),
                etapa_id,
                probabilidad,
                data.get('monto_estimado'),
                data.get('moneda_id', 1),
                data.get('fecha_estimada_cierre'),
                now,
                now,
                str(data.get('ejecutivo_responsable_user_id')) if data.get('ejecutivo_responsable_user_id') else None,
                str(data.get('preventa_responsable_user_id')) if data.get('preventa_responsable_user_id') else None,
                1,  # EstatusOportunidadID = ABIERTA
                data.get('observaciones_internas'),
                str(user_id),
                now,
                now
            ))
            
            result = cursor.fetchone()
            opp_id = result['OportunidadID']
            
            # Registrar en historial
            cursor.execute("""
                INSERT INTO CRM_Oportunidades_HistorialEtapas (
                    OportunidadID, EtapaNuevaID, ProbabilidadNueva,
                    MontoNuevo, Comentario, CambiadoPor, FechaCambio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(opp_id), etapa_id, probabilidad,
                data.get('monto_estimado'), 'Oportunidad creada',
                str(user_id), now
            ))
            
            conn.commit()
            logger.info(f"[CRM] Oportunidad creada: {folio}")
            return OportunidadesRepository.obtener_por_id(opp_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando oportunidad: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def obtener_por_id(oportunidad_id: UUID) -> Optional[Dict[str, Any]]:
        """Obtiene una Oportunidad por ID con datos expandidos"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT 
                    o.*,
                    c.RazonSocial as CuentaNombre,
                    NULL as ContactoNombre,
                    p.Nombre as PipelineNombre,
                    e.Nombre as EtapaNombre,
                    e.ColorHex as EtapaColor,
                    eo.Nombre as EstatusNombre,
                    eo.ColorHex as EstatusColor,
                    CONCAT(u.Nombre, ' ', u.Apellidos) as EjecutivoNombre
                FROM CRM_Oportunidades o
                LEFT JOIN Cliente_Catalogo c ON o.CuentaID = c.PublicUUID
                LEFT JOIN CRM_Config_Pipelines p ON o.PipelineID = p.PipelineID
                LEFT JOIN CRM_Config_PipelineEtapas e ON o.EtapaActualID = e.EtapaID
                LEFT JOIN CRM_Cat_EstatusOportunidad eo ON o.EstatusOportunidadID = eo.EstatusID
                LEFT JOIN Usuario_Catalogo u ON o.EjecutivoResponsableUserID = u.PublicUUID
                WHERE o.OportunidadID = %s AND o.Activo = 1
            """, (str(oportunidad_id),))
            
            row = cursor.fetchone()
            if row:
                return OportunidadesRepository._map_oportunidad(row)
            return None
            
        finally:
            conn.close()
    
    @staticmethod
    def listar(
        empresa_id: UUID,
        pipeline_id: Optional[int] = None,
        etapa_id: Optional[int] = None,
        estatus_id: Optional[int] = None,
        ejecutivo_id: Optional[UUID] = None,
        cuenta_id: Optional[UUID] = None,
        busqueda: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """Lista oportunidades con filtros y paginación"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ["o.EmpresaID = %s", "o.Activo = 1"]
            params = [str(empresa_id)]
            
            if pipeline_id:
                where_clauses.append("o.PipelineID = %s")
                params.append(pipeline_id)
            
            if etapa_id:
                where_clauses.append("o.EtapaActualID = %s")
                params.append(etapa_id)
            
            if estatus_id:
                where_clauses.append("o.EstatusOportunidadID = %s")
                params.append(estatus_id)
            
            if ejecutivo_id:
                where_clauses.append("o.EjecutivoResponsableUserID = %s")
                params.append(str(ejecutivo_id))
            
            if cuenta_id:
                where_clauses.append("o.CuentaID = %s")
                params.append(str(cuenta_id))
            
            if busqueda:
                where_clauses.append("""
                    (o.NombreOportunidad LIKE %s OR o.FolioOportunidad LIKE %s)
                """)
                search_param = f"%{busqueda}%"
                params.extend([search_param, search_param])
            
            where_sql = " AND ".join(where_clauses)
            
            # Contar total
            cursor.execute(f"SELECT COUNT(*) as total FROM CRM_Oportunidades o WHERE {where_sql}", tuple(params))
            total = cursor.fetchone()['total']
            
            # Obtener página
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT 
                    o.*,
                    c.RazonSocial as CuentaNombre,
                    p.Nombre as PipelineNombre,
                    e.Nombre as EtapaNombre,
                    e.ColorHex as EtapaColor,
                    eo.Nombre as EstatusNombre,
                    eo.ColorHex as EstatusColor,
                    CONCAT(u.Nombre, ' ', u.Apellidos) as EjecutivoNombre
                FROM CRM_Oportunidades o
                LEFT JOIN Cliente_Catalogo c ON o.CuentaID = c.PublicUUID
                LEFT JOIN CRM_Config_Pipelines p ON o.PipelineID = p.PipelineID
                LEFT JOIN CRM_Config_PipelineEtapas e ON o.EtapaActualID = e.EtapaID
                LEFT JOIN CRM_Cat_EstatusOportunidad eo ON o.EstatusOportunidadID = eo.EstatusID
                LEFT JOIN Usuario_Catalogo u ON o.EjecutivoResponsableUserID = u.PublicUUID
                WHERE {where_sql}
                ORDER BY o.CreatedAt DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params) + (offset, page_size))
            
            opps = [OportunidadesRepository._map_oportunidad(row) for row in cursor.fetchall()]
            return opps, total
            
        finally:
            conn.close()
    
    @staticmethod
    def cambiar_etapa(
        oportunidad_id: UUID,
        etapa_nueva_id: int,
        comentario: Optional[str],
        monto_nuevo: Optional[float],
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Cambia la etapa de una oportunidad y registra en historial"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener estado actual
            cursor.execute("""
                SELECT EtapaActualID, ProbabilidadActual, MontoEstimado, DiasEnEtapaActual
                FROM CRM_Oportunidades WHERE OportunidadID = %s
            """, (str(oportunidad_id),))
            actual = cursor.fetchone()
            if not actual:
                return None
            
            # Obtener probabilidad de nueva etapa
            cursor.execute("""
                SELECT ProbabilidadDefault, EsCierreGanado, EsCierrePerdido
                FROM CRM_Config_PipelineEtapas WHERE EtapaID = %s
            """, (etapa_nueva_id,))
            nueva_etapa = cursor.fetchone()
            if not nueva_etapa:
                raise ValueError(f"Etapa {etapa_nueva_id} no existe")
            
            now = now_mexico()
            nueva_probabilidad = nueva_etapa['ProbabilidadDefault']
            monto_final = monto_nuevo if monto_nuevo is not None else actual['MontoEstimado']
            
            # Actualizar oportunidad
            cursor.execute("""
                UPDATE CRM_Oportunidades
                SET EtapaActualID = %s,
                    ProbabilidadActual = %s,
                    MontoEstimado = %s,
                    DiasEnEtapaActual = 0,
                    FechaUltimaActividad = %s,
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE OportunidadID = %s
            """, (
                etapa_nueva_id, nueva_probabilidad, monto_final,
                now, str(user_id), now, str(oportunidad_id)
            ))
            
            # Registrar en historial
            cursor.execute("""
                INSERT INTO CRM_Oportunidades_HistorialEtapas (
                    OportunidadID, EtapaAnteriorID, EtapaNuevaID,
                    ProbabilidadAnterior, ProbabilidadNueva,
                    MontoAnterior, MontoNuevo, DiasEnEtapaAnterior,
                    Comentario, CambiadoPor, FechaCambio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(oportunidad_id),
                actual['EtapaActualID'], etapa_nueva_id,
                actual['ProbabilidadActual'], nueva_probabilidad,
                actual['MontoEstimado'], monto_final,
                actual['DiasEnEtapaActual'],
                comentario, str(user_id), now
            ))
            
            conn.commit()
            logger.info(f"[CRM] Oportunidad {oportunidad_id} movida a etapa {etapa_nueva_id}")
            return OportunidadesRepository.obtener_por_id(oportunidad_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error cambiando etapa: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def cerrar(
        oportunidad_id: UUID,
        es_ganada: bool,
        motivo_id: Optional[int],
        razon_texto: Optional[str],
        monto_final: Optional[float],
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Cierra una oportunidad como ganada o perdida"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            now = now_mexico()
            
            # Determinar etapa y estatus de cierre
            if es_ganada:
                estatus_codigo = 'GANADA'
                cursor.execute("""
                    SELECT EtapaID FROM CRM_Config_PipelineEtapas 
                    WHERE EsCierreGanado = 1 AND Activo = 1
                """)
            else:
                estatus_codigo = 'PERDIDA'
                cursor.execute("""
                    SELECT EtapaID FROM CRM_Config_PipelineEtapas 
                    WHERE EsCierrePerdido = 1 AND Activo = 1
                """)
            
            etapa_cierre = cursor.fetchone()
            etapa_id = etapa_cierre['EtapaID'] if etapa_cierre else None
            
            cursor.execute("""
                SELECT EstatusID FROM CRM_Cat_EstatusOportunidad WHERE Codigo = %s
            """, (estatus_codigo,))
            estatus = cursor.fetchone()
            estatus_id = estatus['EstatusID'] if estatus else None
            
            # Actualizar oportunidad
            update_fields = {
                'EstatusOportunidadID': estatus_id,
                'EstatusCierreID': estatus_id,
                'FechaRealCierre': now,
                'FechaUltimaActividad': now,
                'UpdatedBy': str(user_id),
                'UpdatedAt': now
            }
            
            if etapa_id:
                update_fields['EtapaActualID'] = etapa_id
                update_fields['ProbabilidadActual'] = 100 if es_ganada else 0
            
            if es_ganada:
                update_fields['MotivoGanadaID'] = motivo_id
            else:
                update_fields['MotivoPerdidaID'] = motivo_id
                update_fields['RazonPerdidaTexto'] = razon_texto
            
            if monto_final is not None:
                update_fields['MontoEstimado'] = monto_final
            
            set_sql = ', '.join([f"{k} = %s" for k in update_fields.keys()])
            params = list(update_fields.values()) + [str(oportunidad_id)]
            
            cursor.execute(f"""
                UPDATE CRM_Oportunidades SET {set_sql} WHERE OportunidadID = %s
            """, tuple(params))
            
            conn.commit()
            logger.info(f"[CRM] Oportunidad {oportunidad_id} cerrada como {'GANADA' if es_ganada else 'PERDIDA'}")
            return OportunidadesRepository.obtener_por_id(oportunidad_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error cerrando oportunidad: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def _map_oportunidad(row: Dict) -> Dict[str, Any]:
        """Mapea fila SQL a diccionario de respuesta"""
        return {
            'oportunidad_id': row['OportunidadID'],
            'empresa_id': row['EmpresaID'],
            'sucursal_id': row.get('SucursalID'),
            'folio_oportunidad': row.get('FolioOportunidad'),
            'cuenta_id': row.get('CuentaID'),
            'contacto_principal_id': row.get('ContactoPrincipalID'),
            'lead_origen_id': row.get('LeadOrigenID'),
            'nombre_oportunidad': row['NombreOportunidad'],
            'descripcion_oportunidad': row.get('DescripcionOportunidad'),
            'pipeline_id': row['PipelineID'],
            'etapa_actual_id': row['EtapaActualID'],
            'probabilidad_actual': row['ProbabilidadActual'],
            'dias_en_etapa_actual': row.get('DiasEnEtapaActual', 0),
            'monto_estimado': float(row['MontoEstimado']) if row.get('MontoEstimado') else None,
            'moneda_id': row.get('MonedaID', 1),
            'fecha_apertura': row['FechaApertura'],
            'fecha_estimada_cierre': row.get('FechaEstimadaCierre'),
            'fecha_real_cierre': row.get('FechaRealCierre'),
            'fecha_ultima_actividad': row.get('FechaUltimaActividad'),
            'fecha_proxima_actividad': row.get('FechaProximaActividad'),
            'ejecutivo_responsable_user_id': row.get('EjecutivoResponsableUserID'),
            'estatus_oportunidad_id': row['EstatusOportunidadID'],
            'observaciones_internas': row.get('ObservacionesInternas'),
            'activo': bool(row.get('Activo', True)),
            'created_at': row['CreatedAt'],
            'updated_at': row['UpdatedAt'],
            # Campos expandidos
            'cuenta_nombre': row.get('CuentaNombre'),
            'contacto_nombre': row.get('ContactoNombre'),
            'pipeline_nombre': row.get('PipelineNombre'),
            'etapa_nombre': row.get('EtapaNombre'),
            'etapa_color': row.get('EtapaColor'),
            'estatus_nombre': row.get('EstatusNombre'),
            'estatus_color': row.get('EstatusColor'),
            'ejecutivo_nombre': row.get('EjecutivoNombre'),
        }


# ============================================================================
# PIPELINE REPOSITORY
# ============================================================================

class PipelineRepository:
    """Repositorio para operaciones de Pipeline"""
    
    @staticmethod
    def obtener_pipelines(empresa_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Obtiene pipelines disponibles con sus etapas"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where = "WHERE p.Activo = 1"
            params = []
            if empresa_id:
                where += " AND (p.EmpresaID = %s OR p.EmpresaID IS NULL)"
                params.append(str(empresa_id))
            
            cursor.execute(f"""
                SELECT p.*, t.Nombre as TipoPipelineNombre
                FROM CRM_Config_Pipelines p
                LEFT JOIN CRM_Cat_TiposPipeline t ON p.TipoPipelineID = t.TipoID
                {where}
                ORDER BY p.EsDefault DESC, p.Orden
            """, tuple(params) if params else None)
            
            pipelines = []
            for row in cursor.fetchall():
                pipeline = {
                    'pipeline_id': row['PipelineID'],
                    'empresa_id': row.get('EmpresaID'),
                    'codigo': row['Codigo'],
                    'nombre': row['Nombre'],
                    'descripcion': row.get('Descripcion'),
                    'tipo_pipeline_id': row.get('TipoPipelineID', 1),
                    'tipo_pipeline_nombre': row.get('TipoPipelineNombre'),
                    'es_default': bool(row.get('EsDefault')),
                    'activo': bool(row.get('Activo', True)),
                    'etapas': []
                }
                
                # Obtener etapas
                cursor.execute("""
                    SELECT * FROM CRM_Config_PipelineEtapas 
                    WHERE PipelineID = %s AND Activo = 1
                    ORDER BY Orden
                """, (row['PipelineID'],))
                
                for etapa in cursor.fetchall():
                    pipeline['etapas'].append({
                        'etapa_id': etapa['EtapaID'],
                        'pipeline_id': etapa['PipelineID'],
                        'codigo': etapa['Codigo'],
                        'nombre': etapa['Nombre'],
                        'descripcion': etapa.get('Descripcion'),
                        'probabilidad_default': etapa['ProbabilidadDefault'],
                        'orden': etapa['Orden'],
                        'color_hex': etapa.get('ColorHex', '#6B7280'),
                        'es_etapa_inicial': bool(etapa.get('EsEtapaInicial')),
                        'es_etapa_cierre': bool(etapa.get('EsEtapaCierre')),
                        'es_cierre_ganado': bool(etapa.get('EsCierreGanado')),
                        'es_cierre_perdido': bool(etapa.get('EsCierrePerdido')),
                        'dias_max_sla': etapa.get('DiasMaxSLA'),
                        'activo': bool(etapa.get('Activo', True))
                    })
                
                pipelines.append(pipeline)
            
            return pipelines
            
        finally:
            conn.close()
    
    @staticmethod
    def obtener_kanban(empresa_id: UUID, pipeline_id: int) -> Dict[str, Any]:
        """Obtiene vista Kanban del pipeline con oportunidades agrupadas por etapa"""
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener pipeline
            cursor.execute("""
                SELECT * FROM CRM_Config_Pipelines WHERE PipelineID = %s AND Activo = 1
            """, (pipeline_id,))
            pipeline_row = cursor.fetchone()
            if not pipeline_row:
                return None
            
            # Obtener etapas
            cursor.execute("""
                SELECT * FROM CRM_Config_PipelineEtapas 
                WHERE PipelineID = %s AND Activo = 1
                ORDER BY Orden
            """, (pipeline_id,))
            etapas = cursor.fetchall()
            
            columnas = []
            total_oportunidades = 0
            total_monto = 0
            monto_ponderado = 0
            
            for etapa in etapas:
                # Obtener oportunidades de esta etapa
                cursor.execute("""
                    SELECT 
                        o.*,
                        c.RazonSocial as CuentaNombre,
                        CONCAT(u.Nombre, ' ', u.Apellidos) as EjecutivoNombre
                    FROM CRM_Oportunidades o
                    LEFT JOIN Cliente_Catalogo c ON o.CuentaID = c.PublicUUID
                    LEFT JOIN Usuario_Catalogo u ON o.EjecutivoResponsableUserID = u.PublicUUID
                    WHERE o.EmpresaID = %s 
                    AND o.PipelineID = %s 
                    AND o.EtapaActualID = %s
                    AND o.Activo = 1
                    AND o.EstatusOportunidadID = 1  -- Solo abiertas
                    ORDER BY o.FechaEstimadaCierre ASC, o.MontoEstimado DESC
                """, (str(empresa_id), pipeline_id, etapa['EtapaID']))
                
                opps = []
                etapa_monto = 0
                for row in cursor.fetchall():
                    opp = OportunidadesRepository._map_oportunidad(row)
                    opps.append(opp)
                    if opp.get('monto_estimado'):
                        etapa_monto += opp['monto_estimado']
                        total_monto += opp['monto_estimado']
                        monto_ponderado += opp['monto_estimado'] * (opp['probabilidad_actual'] / 100)
                
                total_oportunidades += len(opps)
                
                columnas.append({
                    'etapa': {
                        'etapa_id': etapa['EtapaID'],
                        'codigo': etapa['Codigo'],
                        'nombre': etapa['Nombre'],
                        'color_hex': etapa.get('ColorHex', '#6B7280'),
                        'probabilidad_default': etapa['ProbabilidadDefault'],
                        'es_cierre': bool(etapa.get('EsEtapaCierre'))
                    },
                    'oportunidades': opps,
                    'count': len(opps),
                    'total_monto': etapa_monto
                })
            
            return {
                'pipeline': {
                    'pipeline_id': pipeline_row['PipelineID'],
                    'codigo': pipeline_row['Codigo'],
                    'nombre': pipeline_row['Nombre']
                },
                'columnas': columnas,
                'totales': {
                    'total_oportunidades': total_oportunidades,
                    'total_monto': total_monto,
                    'monto_ponderado': round(monto_ponderado, 2)
                }
            }
            
        finally:
            conn.close()


# ============================================================================
# CATÁLOGOS REPOSITORY
# ============================================================================

class CatalogosRepository:
    """Repositorio para catálogos CRM"""
    
    CATALOGOS = {
        'origenes_lead': 'CRM_Cat_OrigenLead',
        'estatus_lead': 'CRM_Cat_EstatusLead',
        'estatus_oportunidad': 'CRM_Cat_EstatusOportunidad',
        'motivos_perdida': 'CRM_Cat_MotivosPerdida',
        'motivos_ganada': 'CRM_Cat_MotivosGanada',
        'prioridades': 'CRM_Cat_Prioridades',
        'sectores': 'CRM_Cat_Sectores',
        'tamanos_cliente': 'CRM_Cat_TamanosCliente',
        'tipos_pipeline': 'CRM_Cat_TiposPipeline',
        'estatus_propuesta': 'CRM_Cat_EstatusPropuesta',
        'estatus_contrato': 'CRM_Cat_EstatusContrato',
    }
    
    # Tablas que NO tienen ColorHex
    TABLAS_SIN_COLOR = {
        'CRM_Cat_MotivosPerdida', 'CRM_Cat_MotivosGanada',
        'CRM_Cat_Sectores', 'CRM_Cat_TamanosCliente', 'CRM_Cat_TiposPipeline'
    }
    
    @staticmethod
    def obtener_catalogo(nombre: str) -> List[Dict[str, Any]]:
        """Obtiene items de un catálogo por nombre"""
        if nombre not in CatalogosRepository.CATALOGOS:
            raise ValueError(f"Catálogo '{nombre}' no existe")
        
        tabla = CatalogosRepository.CATALOGOS[nombre]
        conn = get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Determinar columna ID según tabla
            id_column = 'OrigenID' if 'Origen' in tabla else \
                       'MotivoID' if 'Motivo' in tabla else \
                       'TipoID' if 'Tipo' in tabla else \
                       'TamanoID' if 'Tamano' in tabla else \
                       'SectorID' if 'Sector' in tabla else \
                       'PrioridadID' if 'Prioridad' in tabla else \
                       'EstatusID'
            
            # Algunas tablas no tienen ColorHex
            if tabla in CatalogosRepository.TABLAS_SIN_COLOR:
                cursor.execute(f"""
                    SELECT {id_column} as id, Codigo as codigo, Nombre as nombre,
                           Descripcion as descripcion, Orden as orden,
                           '#6B7280' as color_hex, Activo as activo
                    FROM {tabla}
                    WHERE Activo = 1
                    ORDER BY Orden
                """)
            else:
                cursor.execute(f"""
                    SELECT {id_column} as id, Codigo as codigo, Nombre as nombre,
                           Descripcion as descripcion, Orden as orden,
                           ISNULL(ColorHex, '#6B7280') as color_hex, Activo as activo
                    FROM {tabla}
                    WHERE Activo = 1
                    ORDER BY Orden
                """)
            
            return [dict(row) for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    @staticmethod
    def obtener_todos() -> Dict[str, List[Dict]]:
        """Obtiene todos los catálogos CRM"""
        result = {}
        for nombre in CatalogosRepository.CATALOGOS.keys():
            try:
                result[nombre] = CatalogosRepository.obtener_catalogo(nombre)
            except Exception as e:
                logger.warning(f"[CRM] Error obteniendo catálogo {nombre}: {e}")
                result[nombre] = []
        return result
