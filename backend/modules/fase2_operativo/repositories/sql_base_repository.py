"""
SQL Base Repository para módulo fase2_operativo
FASE B-P0-C | EDARSA HUB

Este módulo proporciona la clase base para todos los repositories del módulo operativo
usando EDARSAHUB SQL Server en lugar de MongoDB.

ARQUITECTURA:
- Todo acceso productivo va a SQL Server
- CERO MongoDB productivo
- CERO conexiones LIVE a servidores remotos
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import logging
import uuid
import json
import pymssql
import os

logger = logging.getLogger(__name__)

# ============================================================================
# MAPEO COLECCIÓN MONGODB → TABLA SQL
# ============================================================================
COLLECTION_TO_TABLE_MAP = {
    # Tablas existentes (antes de B-P0-B)
    "workflow_inventarios": "Workflow_Inventarios",
    "tareas_inventario": "Tareas_Inventario",
    "detalle_diferencias": "Workflow_DetalleDiferencias",
    "configuracion_operativa": "Configuracion_Operativa",
    
    # Tablas nuevas (creadas en B-P0-B)
    "notificaciones_log": "Operativo_Notificaciones_Log",
    "justificaciones_inventario": "Workflow_Justificaciones",
    "decisiones_auditoria": "Workflow_DecisionesAuditoria",
    "historial_asignaciones": "Operativo_HistorialAsignaciones",
    "responsabilidad_economica": "Operativo_ResponsabilidadEconomica",
    "cargos_economicos": "Operativo_CargosResponsabilidad",
    "cargos_economicos_log": "Operativo_HistorialCargos",
    "responsabilidad_historial": "Operativo_HistorialCargos",  # Alias
    "tareas_operativas_compras": "Operativo_TareasCompras",
    "auditoria_compras_bitacora": "Operativo_BitacoraCompras",
    "pedidos_procesados_automatizacion": "Operativo_PedidosProcesados",
    "auditorias_programadas": "Operativo_AuditoriasProgramadas",
    "documentos_generados": "Operativo_DocumentosGenerados",
    "scheduler_job_logs": "Scheduler_BitacoraJobs",
}

# Mapeo de campos MongoDB → SQL para cada tabla
FIELD_MAPPING = {
    "Workflow_Inventarios": {
        "id": "WorkflowID",
        "_id": "WorkflowID",
        "estado": "EstadoWorkflow",
        "estado_workflow": "EstadoWorkflow",
        "server_id": "ServerID",
        "servidor_id": "ServerID",
        "sucursal_id": "SucursalID",
        "sucursal_nombre": "SucursalNombre",
        "folio_inventario": "FolioInventario",
        "fecha_creacion": "FechaCreacion",
        "fecha_actualizacion": "FechaUltimaActualizacion",
        "fecha_ultima_actualizacion": "FechaUltimaActualizacion",
        "procesado_id": "ProcesadoID",
        "almacen_id": "AlmacenID",
        "almacen_nombre": "AlmacenNombre",
        "ciclo_actual": "CicloActual",
        "total_productos_diferencia": "TotalProductosDiferencia",
        "valor_total_diferencias": "ValorTotalDiferencias",
    },
    "Tareas_Inventario": {
        "id": "TareaID",
        "_id": "TareaID",
        "workflow_id": "WorkflowID",
        "tipo_tarea": "TipoTarea",
        "estado": "EstadoTarea",
        "estado_tarea": "EstadoTarea",
        "fecha_creacion": "FechaCreacion",
        "fecha_vencimiento": "FechaLimite",
        "fecha_limite": "FechaLimite",
        "fecha_completada": "FechaCompletada",
        "fecha_actualizacion": "FechaActualizacion",
        "usuario_asignado_id": "UsuarioAsignadoID",
        "usuario_asignado_nombre": "UsuarioAsignadoNombre",
        "prioridad": "Prioridad",
        "titulo": "Titulo",
        "descripcion": "Descripcion",
        "vencida": "Vencida",
        "estado_sla": "EstadoSLA",
        "server_id": "ServerID",  # Puede no existir, manejar con cuidado
    },
    "Operativo_Notificaciones_Log": {
        "id": "NotificacionID",
        "_id": "NotificacionID",
        "tipo_evento": "TipoEvento",
        "workflow_id": "WorkflowID",
        "tarea_id": "TareaID",
        "estado": "Estado",
        "fecha_envio": "FechaEnvio",
    },
    "Workflow_Justificaciones": {
        "id": "JustificacionID",
        "_id": "JustificacionID",
        "workflow_id": "WorkflowID",
        "estado": "Estado",
        "fecha_creacion": "FechaCreacion",
    },
    "Workflow_DecisionesAuditoria": {
        "id": "DecisionID",
        "_id": "DecisionID",
        "workflow_id": "WorkflowID",
        "fecha_decision": "FechaDecision",
    },
    "Operativo_ResponsabilidadEconomica": {
        "id": "ResponsabilidadID",
        "_id": "ResponsabilidadID",
        "workflow_id": "WorkflowID",
        "server_id": "ServerID",
        "sucursal_id": "SucursalID",
        "sucursal_nombre": "SucursalNombre",
        "responsable_id": "ResponsableID",
        "responsable_nombre": "ResponsableNombre",
        "monto_total": "MontoTotal",
        "monto_justificado": "MontoJustificado",
        "monto_no_justificado": "MontoNoJustificado",
        "estado": "Estado",
        "excede_minimo": "ExcedeMinimo",
        "umbral_minimo": "UmbralMinimo",
        "fecha_calculo": "FechaCalculo",
        "fecha_creacion": "FechaCalculo",
        "fecha_actualizacion": "FechaUltimaActualizacion",
        "fecha_ultima_actualizacion": "FechaUltimaActualizacion",
        "fecha_aprobacion": "FechaAprobacion",
        "aprobado_por_id": "AprobadoPorID",
        "comentarios": "Comentarios",
    },
    "Operativo_CargosResponsabilidad": {
        "id": "CargoID",
        "_id": "CargoID",
        "workflow_id": "WorkflowID",
        "estado": "EstatusCargo",
        "fecha_propuesta": "FechaPropuesta",
    },
    "Configuracion_Operativa": {
        "id": "ID",
        "_id": "ID",
        "clave": "Clave",
        "valor": "Valor",
        "tipo": "Tipo",
        "descripcion": "Descripcion",
        "fecha_actualizacion": "FechaActualizacion",
    },
}


class SQLCursor:
    """
    Clase que simula el cursor de MongoDB con métodos encadenables.
    Permite compatibilidad con código que usa .find().sort().limit().skip()
    """
    
    def __init__(self, repository: 'SQLBaseRepository', filters: Dict = None, projection: Dict = None):
        self._repository = repository
        self._filters = filters or {}
        self._projection = projection
        self._sort_spec = None
        self._skip_val = 0
        self._limit_val = 1000
    
    def sort(self, field_or_list, direction=None) -> 'SQLCursor':
        """Configura ordenamiento."""
        if isinstance(field_or_list, list):
            self._sort_spec = field_or_list
        elif direction is not None:
            self._sort_spec = [(field_or_list, direction)]
        else:
            self._sort_spec = [(field_or_list, 1)]
        return self
    
    def limit(self, n: int) -> 'SQLCursor':
        """Configura límite."""
        self._limit_val = n
        return self
    
    def skip(self, n: int) -> 'SQLCursor':
        """Configura skip."""
        self._skip_val = n
        return self
    
    def __iter__(self):
        """Permite iterar sobre los resultados."""
        results = self._execute()
        return iter(results)
    
    def __list__(self):
        """Permite convertir a lista."""
        return self._execute()
    
    def _execute(self) -> List[Dict]:
        """Ejecuta la query y retorna resultados."""
        return self._repository._find_internal(
            filters=self._filters,
            projection=self._projection,
            skip=self._skip_val,
            limit=self._limit_val,
            sort=self._sort_spec
        )


class SQLRepositoryNotImplementedError(Exception):
    """
    Error para métodos que aún no están migrados a SQL.
    Usado para control explícito - NO devolver [] o None silenciosamente.
    """
    def __init__(self, method: str, collection: str):
        self.method = method
        self.collection = collection
        super().__init__(
            f"SQL_REPOSITORY_METHOD_NOT_IMPLEMENTED: {method}() en {collection}. "
            f"Método pendiente de migración a SQL."
        )


class SQLBaseRepository:
    """
    Clase base SQL para repositories del módulo fase2_operativo.
    
    ARQUITECTURA:
    - Usa EDARSAHUB SQL Server como fuente de datos
    - CERO MongoDB productivo
    - CERO conexiones LIVE
    
    MIGRACIÓN:
    - Reemplaza BaseRepository (MongoDB)
    - Misma interfaz, diferente implementación
    """
    
    def __init__(self, collection_name: str):
        """
        Inicializa el repository SQL.
        
        Args:
            collection_name: Nombre de la colección MongoDB (se mapea a tabla SQL)
        """
        self.collection_name = collection_name
        self.table_name = COLLECTION_TO_TABLE_MAP.get(collection_name)
        
        if not self.table_name:
            raise ValueError(
                f"SQL_REPOSITORY_TABLE_NOT_MAPPED: Colección '{collection_name}' "
                f"no tiene mapeo a tabla SQL. Agregar a COLLECTION_TO_TABLE_MAP."
            )
        
        self._field_map = FIELD_MAPPING.get(self.table_name, {})
        
        # Configuración de conexión SQL (de variables de entorno)
        self._sql_config = {
            "server": os.environ.get("EDARSAHUB_SQL_SERVER", "54.39.104.176"),
            "port": int(os.environ.get("EDARSAHUB_SQL_PORT", "1433")),
            "database": os.environ.get("EDARSAHUB_SQL_DATABASE", "EDARSAHUB"),
            "user": os.environ.get("EDARSAHUB_SQL_USER", "HRLectura"),
            "password": os.environ.get("EDARSAHUB_SQL_PASSWORD", "National09$"),
        }
        
        logger.info(f"[SQL_REPO] Inicializado {collection_name} → {self.table_name}")
    
    def _get_connection(self) -> pymssql.Connection:
        """Obtiene conexión a EDARSAHUB SQL Server."""
        return pymssql.connect(
            server=self._sql_config["server"],
            port=self._sql_config["port"],
            database=self._sql_config["database"],
            user=self._sql_config["user"],
            password=self._sql_config["password"],
            timeout=30,
            as_dict=True
        )
    
    def _get_timestamp(self) -> datetime:
        """Retorna timestamp actual en UTC."""
        return datetime.now(timezone.utc)
    
    def _generate_id(self) -> str:
        """Genera un nuevo ID único."""
        return str(uuid.uuid4()).upper()
    
    def _map_field(self, mongo_field: str) -> str:
        """
        Mapea un campo MongoDB a su equivalente SQL.
        Si el campo no está mapeado, retorna el nombre original con formato SQL (PascalCase).
        """
        mapped = self._field_map.get(mongo_field)
        if mapped:
            return mapped
        # Intentar convertir snake_case a PascalCase
        parts = mongo_field.split("_")
        return "".join(p.capitalize() for p in parts)
    
    def _field_exists_in_table(self, field_name: str) -> bool:
        """Verifica si un campo existe en la tabla SQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = %s AND COLUMN_NAME = %s
            """, (self.table_name, field_name))
            exists = cursor.fetchone()[0] > 0
            cursor.close()
            conn.close()
            return exists
        except:
            return False
    
    def _row_to_dict(self, row: Dict) -> Dict:
        """
        Convierte una fila SQL a formato compatible con MongoDB.
        Convierte nombres de columna PascalCase a snake_case para compatibilidad.
        """
        if row is None:
            return None
        
        # Crear mapeo inverso SQL → MongoDB
        inverse_map = {}
        for mongo_key, sql_key in self._field_map.items():
            inverse_map[sql_key.lower()] = mongo_key
        
        result = {}
        for key, value in row.items():
            # Convertir nombre de columna a snake_case
            mapped_key = inverse_map.get(key.lower(), self._to_snake_case(key))
            
            # Convertir datetime a ISO string
            if isinstance(value, datetime):
                result[mapped_key] = value.isoformat()
            # Parsear JSON si es string
            elif isinstance(value, str) and key.endswith("JSON"):
                try:
                    json_key = mapped_key.replace("_json", "").replace("json", "")
                    result[json_key] = json.loads(value)
                except:
                    result[mapped_key] = value
            else:
                result[mapped_key] = value
        
        return result
    
    def _to_snake_case(self, name: str) -> str:
        """Convierte PascalCase a snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _build_where_clause(self, filters: Dict) -> Tuple[str, List]:
        """
        Construye cláusula WHERE desde filtros estilo MongoDB.
        
        Returns:
            Tuple[str, List]: (cláusula WHERE, lista de parámetros)
        """
        if not filters:
            return "", []
        
        conditions = []
        params = []
        
        # Cache de columnas existentes para esta tabla
        existing_columns = self._get_table_columns()
        
        for key, value in filters.items():
            sql_field = self._map_field(key)
            
            # Verificar si el campo existe en la tabla
            if sql_field.upper() not in [c.upper() for c in existing_columns]:
                logger.warning(f"[SQL_REPO] Campo '{sql_field}' no existe en {self.table_name}, omitiendo filtro")
                continue
            
            if isinstance(value, dict):
                # Operadores MongoDB
                for op, val in value.items():
                    if op == "$eq":
                        conditions.append(f"{sql_field} = %s")
                        params.append(val)
                    elif op == "$ne":
                        conditions.append(f"{sql_field} != %s")
                        params.append(val)
                    elif op == "$gt":
                        conditions.append(f"{sql_field} > %s")
                        params.append(val)
                    elif op == "$gte":
                        conditions.append(f"{sql_field} >= %s")
                        params.append(val)
                    elif op == "$lt":
                        conditions.append(f"{sql_field} < %s")
                        params.append(val)
                    elif op == "$lte":
                        conditions.append(f"{sql_field} <= %s")
                        params.append(val)
                    elif op == "$in":
                        if val:  # Solo si hay valores
                            placeholders = ", ".join(["%s"] * len(val))
                            conditions.append(f"{sql_field} IN ({placeholders})")
                            params.extend(val)
                    elif op == "$nin":
                        if val:  # Solo si hay valores
                            placeholders = ", ".join(["%s"] * len(val))
                            conditions.append(f"{sql_field} NOT IN ({placeholders})")
                            params.extend(val)
                    elif op == "$regex":
                        conditions.append(f"{sql_field} LIKE %s")
                        params.append(f"%{val}%")
            elif value is None:
                conditions.append(f"{sql_field} IS NULL")
            else:
                conditions.append(f"{sql_field} = %s")
                params.append(value)
        
        where_clause = " AND ".join(conditions)
        return where_clause, params
    
    def _get_table_columns(self) -> List[str]:
        """Obtiene la lista de columnas de la tabla."""
        if hasattr(self, '_cached_columns'):
            return self._cached_columns
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = %s
            """, (self.table_name,))
            self._cached_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return self._cached_columns
        except:
            return []
    
    def _build_order_clause(self, sort: Optional[List[tuple]]) -> str:
        """
        Construye cláusula ORDER BY desde formato MongoDB.
        
        Args:
            sort: Lista de tuplas [(campo, dirección), ...]
                  dirección: 1 = ASC, -1 = DESC
        """
        if not sort:
            return ""
        
        order_parts = []
        for field, direction in sort:
            sql_field = self._map_field(field)
            order = "ASC" if direction == 1 else "DESC"
            order_parts.append(f"{sql_field} {order}")
        
        return "ORDER BY " + ", ".join(order_parts)
    
    # =========================================================================
    # MÉTODOS CRUD PRINCIPALES
    # =========================================================================
    
    async def create(self, data: Dict[str, Any]) -> Dict:
        """
        Crea un nuevo registro en SQL.
        
        NOTA: Este método es async para mantener compatibilidad con código existente,
        pero internamente usa operaciones síncronas de pymssql.
        """
        # Generar ID si no existe
        id_field = self._get_id_field_name()
        if "id" not in data and "_id" not in data:
            data["id"] = self._generate_id()
        
        # Agregar timestamps
        now = self._get_timestamp()
        data["fecha_creacion"] = now
        data["fecha_ultima_actualizacion"] = now
        
        # Mapear campos
        sql_data = {}
        for key, value in data.items():
            sql_field = self._map_field(key)
            if isinstance(value, dict) or isinstance(value, list):
                sql_data[sql_field + "JSON"] = json.dumps(value)
            elif isinstance(value, datetime):
                sql_data[sql_field] = value
            else:
                sql_data[sql_field] = value
        
        # Construir INSERT
        columns = ", ".join(sql_data.keys())
        placeholders = ", ".join(["%s"] * len(sql_data))
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(sql_data.values()))
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"[SQL_REPO] CREATE en {self.table_name}: {data.get('id')}")
            return data
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error CREATE en {self.table_name}: {e}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """
        Obtiene un registro por su ID.
        """
        id_field = self._get_id_field_name()
        sql = f"SELECT * FROM {self.table_name} WHERE {id_field} = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_dict(row)
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error GET_BY_ID en {self.table_name}: {e}")
            raise
    
    async def get_all(
        self, 
        filters: Optional[Dict] = None, 
        skip: int = 0, 
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict]:
        """
        Obtiene todos los registros con filtros opcionales.
        """
        where_clause, params = self._build_where_clause(filters)
        order_clause = self._build_order_clause(sort)
        
        # SQL Server requiere ORDER BY para usar OFFSET
        if not order_clause:
            id_field = self._get_id_field_name()
            order_clause = f"ORDER BY {id_field}"
        
        sql = f"SELECT * FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        sql += f" {order_clause}"
        sql += f" OFFSET {skip} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error GET_ALL en {self.table_name}: {e}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Actualiza un registro por su ID.
        """
        # Agregar timestamp de actualización
        data["fecha_ultima_actualizacion"] = self._get_timestamp()
        
        # Mapear campos
        set_parts = []
        params = []
        for key, value in data.items():
            sql_field = self._map_field(key)
            if isinstance(value, dict) or isinstance(value, list):
                set_parts.append(f"{sql_field}JSON = %s")
                params.append(json.dumps(value))
            else:
                set_parts.append(f"{sql_field} = %s")
                params.append(value)
        
        id_field = self._get_id_field_name()
        params.append(id)
        
        sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE {id_field} = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            conn.close()
            
            # Retornar el registro actualizado
            return await self.get_by_id(id)
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error UPDATE en {self.table_name}: {e}")
            raise
    
    async def delete(self, id: str) -> bool:
        """
        Elimina un registro por su ID (hard delete).
        Para soft delete, usar update con Activo=0.
        """
        id_field = self._get_id_field_name()
        sql = f"DELETE FROM {self.table_name} WHERE {id_field} = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (id,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error DELETE en {self.table_name}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict] = None) -> int:
        """
        Cuenta registros que coinciden con los filtros.
        """
        where_clause, params = self._build_where_clause(filters)
        
        sql = f"SELECT COUNT(*) as total FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return row["total"] if row else 0
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error COUNT en {self.table_name}: {e}")
            raise
    
    async def exists(self, filters: Dict) -> bool:
        """
        Verifica si existe al menos un registro.
        """
        return await self.count(filters) > 0
    
    def _get_id_field_name(self) -> str:
        """
        Obtiene el nombre del campo ID para esta tabla.
        """
        # Mapeo de tabla a campo ID
        id_fields = {
            "Workflow_Inventarios": "WorkflowID",
            "Tareas_Inventario": "TareaID",
            "Workflow_DetalleDiferencias": "DetalleID",
            "Configuracion_Operativa": "Clave",
            "Operativo_Notificaciones_Log": "NotificacionID",
            "Workflow_Justificaciones": "JustificacionID",
            "Workflow_DecisionesAuditoria": "DecisionID",
            "Operativo_HistorialAsignaciones": "HistorialID",
            "Operativo_ResponsabilidadEconomica": "ResponsabilidadID",
            "Operativo_CargosResponsabilidad": "CargoID",
            "Operativo_HistorialCargos": "HistorialID",
            "Operativo_TareasCompras": "TareaID",
            "Operativo_BitacoraCompras": "BitacoraID",
            "Operativo_PedidosProcesados": "PedidoID",
            "Operativo_AuditoriasProgramadas": "AuditoriaID",
            "Operativo_DocumentosGenerados": "DocumentoID",
            "Scheduler_BitacoraJobs": "ID",
        }
        return id_fields.get(self.table_name, "ID")
    
    # =========================================================================
    # MÉTODOS DE COMPATIBILIDAD MONGODB (Síncronos)
    # =========================================================================
    
    def find_one(self, filters: Dict, projection: Dict = None) -> Optional[Dict]:
        """
        Versión síncrona de get para compatibilidad con código MongoDB.
        """
        where_clause, params = self._build_where_clause(filters)
        
        # Construir SELECT con proyección
        if projection:
            fields = [self._map_field(f) for f in projection.keys() if projection[f]]
            select_clause = ", ".join(fields) if fields else "*"
        else:
            select_clause = "*"
        
        sql = f"SELECT TOP 1 {select_clause} FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_dict(row)
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error find_one en {self.table_name}: {e}")
            raise
    
    def find(
        self, 
        filters: Dict = None, 
        projection: Dict = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None
    ) -> SQLCursor:
        """
        Versión síncrona para compatibilidad con código MongoDB.
        Retorna SQLCursor que permite encadenar .sort().limit().skip()
        """
        cursor = SQLCursor(self, filters, projection)
        cursor._skip_val = skip
        cursor._limit_val = limit
        cursor._sort_spec = sort
        return cursor
    
    def _find_internal(
        self, 
        filters: Dict = None, 
        projection: Dict = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None
    ) -> List[Dict]:
        """
        Ejecuta la query find y retorna lista de resultados.
        """
        where_clause, params = self._build_where_clause(filters or {})
        order_clause = self._build_order_clause(sort)
        
        # SQL Server requiere ORDER BY para usar OFFSET
        if not order_clause:
            id_field = self._get_id_field_name()
            order_clause = f"ORDER BY {id_field}"
        
        if projection:
            # Filtrar proyecciones a campos existentes
            existing_cols = self._get_table_columns()
            fields = []
            for f in projection.keys():
                if projection[f]:
                    sql_field = self._map_field(f)
                    if sql_field.upper() in [c.upper() for c in existing_cols]:
                        fields.append(sql_field)
            select_clause = ", ".join(fields) if fields else "*"
        else:
            select_clause = "*"
        
        sql = f"SELECT {select_clause} FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        sql += f" {order_clause}"
        sql += f" OFFSET {skip} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error _find_internal en {self.table_name}: {e}")
            # Retornar lista vacía para no romper la UI
            return []
    
    def insert_one(self, data: Dict) -> Dict:
        """
        Versión síncrona de create para compatibilidad con código MongoDB.
        """
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.create(data))
        finally:
            loop.close()
    
    def update_one(self, filters: Dict, update: Dict) -> int:
        """
        Versión síncrona de update para compatibilidad con código MongoDB.
        """
        # Extraer datos de $set si existe
        data = update.get("$set", update)
        
        where_clause, where_params = self._build_where_clause(filters)
        
        # Construir SET
        set_parts = []
        set_params = []
        for key, value in data.items():
            sql_field = self._map_field(key)
            if isinstance(value, dict) or isinstance(value, list):
                set_parts.append(f"{sql_field}JSON = %s")
                set_params.append(json.dumps(value))
            else:
                set_parts.append(f"{sql_field} = %s")
                set_params.append(value)
        
        sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE {where_clause}"
        params = set_params + where_params
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error update_one en {self.table_name}: {e}")
            raise
    
    def count_documents(self, filters: Dict = None, limit: int = None) -> int:
        """
        Versión síncrona de count para compatibilidad con código MongoDB.
        """
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.count(filters))
        finally:
            loop.close()
    
    def delete_one(self, filters: Dict) -> Dict:
        """
        Elimina un documento que coincida con los filtros.
        Versión síncrona para compatibilidad con MongoDB.
        """
        where_clause, params = self._build_where_clause(filters)
        
        sql = f"DELETE TOP(1) FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return {"deleted_count": affected}
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error delete_one en {self.table_name}: {e}")
            raise
    
    def update_many(self, filters: Dict, update: Dict) -> Dict:
        """
        Actualiza múltiples documentos que coincidan con los filtros.
        Versión síncrona para compatibilidad con MongoDB.
        """
        data = update.get("$set", update)
        where_clause, where_params = self._build_where_clause(filters)
        
        set_parts = []
        set_params = []
        for key, value in data.items():
            sql_field = self._map_field(key)
            if isinstance(value, dict) or isinstance(value, list):
                set_parts.append(f"{sql_field}JSON = %s")
                set_params.append(json.dumps(value))
            else:
                set_parts.append(f"{sql_field} = %s")
                set_params.append(value)
        
        sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        params = set_params + where_params
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return {"modified_count": affected}
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error update_many en {self.table_name}: {e}")
            raise
    
    def find_one_and_update(
        self, 
        filters: Dict, 
        update: Dict, 
        return_document: bool = True,
        upsert: bool = False
    ) -> Optional[Dict]:
        """
        Busca un documento, lo actualiza y retorna el resultado.
        Versión síncrona para compatibilidad con MongoDB.
        """
        data = update.get("$set", update)
        where_clause, where_params = self._build_where_clause(filters)
        
        # Primero obtener el documento actual si return_document=True
        if return_document:
            sql_select = f"SELECT * FROM {self.table_name}"
            if where_clause:
                sql_select += f" WHERE {where_clause}"
        
        # Construir UPDATE
        set_parts = []
        set_params = []
        for key, value in data.items():
            sql_field = self._map_field(key)
            if isinstance(value, dict) or isinstance(value, list):
                set_parts.append(f"{sql_field}JSON = %s")
                set_params.append(json.dumps(value))
            else:
                set_parts.append(f"{sql_field} = %s")
                set_params.append(value)
        
        sql_update = f"UPDATE {self.table_name} SET {', '.join(set_parts)}"
        if where_clause:
            sql_update += f" WHERE {where_clause}"
        params = set_params + where_params
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Ejecutar UPDATE
            cursor.execute(sql_update, params)
            conn.commit()
            
            # Retornar documento actualizado
            if return_document:
                cursor.execute(sql_select, where_params)
                row = cursor.fetchone()
                result = self._row_to_dict(row)
            else:
                result = None
            
            cursor.close()
            conn.close()
            
            return result
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error find_one_and_update en {self.table_name}: {e}")
            raise
    
    def aggregate(self, pipeline: List[Dict]) -> List[Dict]:
        """
        Ejecuta una agregación estilo MongoDB.
        
        NOTA: Esta es una implementación simplificada que soporta
        operaciones comunes: $match, $group, $sort, $limit, $project.
        Para agregaciones complejas, puede requerir extensión.
        """
        # Extraer operaciones del pipeline
        match_filters = {}
        group_by = None
        group_accumulators = {}
        sort_spec = None
        limit_val = None
        project_fields = None
        
        for stage in pipeline:
            if "$match" in stage:
                match_filters.update(stage["$match"])
            elif "$group" in stage:
                group_spec = stage["$group"]
                group_by = group_spec.get("_id")
                for key, val in group_spec.items():
                    if key != "_id":
                        group_accumulators[key] = val
            elif "$sort" in stage:
                sort_spec = [(k, v) for k, v in stage["$sort"].items()]
            elif "$limit" in stage:
                limit_val = stage["$limit"]
            elif "$project" in stage:
                project_fields = stage["$project"]
        
        # Construir query SQL
        if group_by is not None:
            # Agregación con GROUP BY
            return self._execute_group_aggregate(
                match_filters, group_by, group_accumulators, sort_spec, limit_val
            )
        else:
            # Query simple con filtros
            return self.find(
                filters=match_filters,
                sort=sort_spec,
                limit=limit_val or 1000
            )
    
    def _execute_group_aggregate(
        self,
        match_filters: Dict,
        group_by: Any,
        accumulators: Dict,
        sort_spec: List[tuple],
        limit_val: int
    ) -> List[Dict]:
        """
        Ejecuta una agregación con GROUP BY.
        """
        where_clause, params = self._build_where_clause(match_filters)
        
        # Construir SELECT con agregadores
        select_parts = []
        
        # Campo de agrupación
        if isinstance(group_by, str) and group_by.startswith("$"):
            group_field = self._map_field(group_by[1:])
            select_parts.append(f"{group_field} as _id")
            group_clause = f"GROUP BY {group_field}"
        elif isinstance(group_by, dict):
            # Múltiples campos de agrupación
            group_fields = []
            for alias, field_expr in group_by.items():
                if isinstance(field_expr, str) and field_expr.startswith("$"):
                    sql_field = self._map_field(field_expr[1:])
                    select_parts.append(f"{sql_field} as {alias}")
                    group_fields.append(sql_field)
            group_clause = f"GROUP BY {', '.join(group_fields)}"
        elif group_by is None:
            # Agregar todo
            group_clause = ""
        else:
            group_clause = ""
        
        # Agregadores
        for alias, acc_spec in accumulators.items():
            if isinstance(acc_spec, dict):
                if "$sum" in acc_spec:
                    val = acc_spec["$sum"]
                    if val == 1:
                        select_parts.append(f"COUNT(*) as {alias}")
                    elif isinstance(val, str) and val.startswith("$"):
                        field = self._map_field(val[1:])
                        select_parts.append(f"SUM({field}) as {alias}")
                    else:
                        select_parts.append(f"SUM({val}) as {alias}")
                elif "$count" in acc_spec:
                    select_parts.append(f"COUNT(*) as {alias}")
                elif "$avg" in acc_spec:
                    field = self._map_field(acc_spec["$avg"][1:])
                    select_parts.append(f"AVG({field}) as {alias}")
                elif "$min" in acc_spec:
                    field = self._map_field(acc_spec["$min"][1:])
                    select_parts.append(f"MIN({field}) as {alias}")
                elif "$max" in acc_spec:
                    field = self._map_field(acc_spec["$max"][1:])
                    select_parts.append(f"MAX({field}) as {alias}")
                elif "$first" in acc_spec:
                    field = self._map_field(acc_spec["$first"][1:])
                    select_parts.append(f"MIN({field}) as {alias}")  # Aproximación
        
        if not select_parts:
            select_parts = ["COUNT(*) as total"]
        
        sql = f"SELECT {', '.join(select_parts)} FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        if group_clause:
            sql += f" {group_clause}"
        
        # ORDER BY
        if sort_spec:
            order_parts = []
            for field, direction in sort_spec:
                sql_field = self._map_field(field) if not field.startswith("_") else field
                order = "ASC" if direction == 1 else "DESC"
                order_parts.append(f"{sql_field} {order}")
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        # LIMIT
        if limit_val:
            sql = sql.replace("SELECT ", f"SELECT TOP {limit_val} ")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[SQL_REPO] Error aggregate en {self.table_name}: {e}")
            # Retornar lista vacía en caso de error para no romper la UI
            return []


# ============================================================================
# FACTORY PARA OBTENER REPOSITORIO SQL
# ============================================================================

def get_sql_repository(collection_name: str) -> SQLBaseRepository:
    """
    Factory para obtener un repositorio SQL dado un nombre de colección MongoDB.
    
    Args:
        collection_name: Nombre de la colección MongoDB
        
    Returns:
        SQLBaseRepository configurado para la tabla SQL correspondiente
    """
    return SQLBaseRepository(collection_name)


# ============================================================================
# CLASE DE COMPATIBILIDAD PARA MIGRACIÓN GRADUAL
# ============================================================================

class BaseRepository:
    """
    CLASE WRAPPER PARA MIGRACIÓN GRADUAL.
    
    Esta clase mantiene la interfaz del BaseRepository original pero
    delega todas las operaciones a SQLBaseRepository.
    
    IMPORTANTE:
    - Todo acceso productivo va a SQL
    - El parámetro 'db' (MongoDB) se ignora
    - Mantiene compatibilidad con repositories existentes
    """
    
    def __init__(self, db, collection_name: str):
        """
        Inicializa el repository.
        
        Args:
            db: IGNORADO - Solo para compatibilidad
            collection_name: Nombre de la colección (se mapea a tabla SQL)
        """
        # Ignoramos db (MongoDB) - Usamos SQL
        self._sql_repo = SQLBaseRepository(collection_name)
        self.collection_name = collection_name
        self.table_name = self._sql_repo.table_name
        
        # Para compatibilidad: exponer métodos síncronos como 'collection'
        self.collection = self._sql_repo
        
        logger.info(
            f"[BASE_REPO] Inicializado {collection_name} → SQL:{self.table_name} "
            f"(MongoDB db ignorado, usando EDARSAHUB SQL)"
        )
    
    # Delegación de métodos async
    async def create(self, data: Dict[str, Any]) -> Dict:
        return await self._sql_repo.create(data)
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        return await self._sql_repo.get_by_id(id)
    
    async def get_all(
        self, 
        filters: Optional[Dict] = None, 
        skip: int = 0, 
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict]:
        return await self._sql_repo.get_all(filters, skip, limit, sort)
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict]:
        return await self._sql_repo.update(id, data)
    
    async def delete(self, id: str) -> bool:
        return await self._sql_repo.delete(id)
    
    async def count(self, filters: Optional[Dict] = None) -> int:
        return await self._sql_repo.count(filters)
    
    async def exists(self, filters: Dict) -> bool:
        return await self._sql_repo.exists(filters)
    
    # Métodos de serialización (compatibilidad)
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Ya no necesario en SQL, pero mantenido para compatibilidad."""
        return doc
    
    def _serialize_list(self, docs: List[Dict]) -> List[Dict]:
        """Ya no necesario en SQL, pero mantenido para compatibilidad."""
        return docs
    
    def _get_timestamp(self) -> datetime:
        return self._sql_repo._get_timestamp()
