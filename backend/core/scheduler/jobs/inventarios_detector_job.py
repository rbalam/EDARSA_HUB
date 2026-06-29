"""
EDARSA HUB - Job de Detección Automática de Inventarios
========================================================
Detecta nuevos inventarios físicos en sistemas origen (SoftRestaurant/MPRO),
dispara análisis automático y crea workflows.

FLUJO COMPLETO:
1. Obtener servidores activos
2. Para cada servidor, consultar inventarios recientes
3. Comparar contra inventarios_procesados_auto (anti-duplicado)
4. Para inventarios nuevos:
   a) Registrar en inventarios_procesados_auto (EN_PROCESO)
   b) Ejecutar análisis de inventario
   c) Disparar orquestación
   d) Actualizar estado (COMPLETADO/ERROR)
5. Registrar bitácora completa

CLAVE DE IDEMPOTENCIA (5 campos):
- sistema_origen
- server_id
- sucursal_id
- almacen_id
- folio_inventario

ESTADOS:
- EN_PROCESO: Siendo procesado
- COMPLETADO: Procesamiento exitoso
- ERROR: Falló después de reintentos

REINTENTOS:
- Máximo 3 intentos automáticos
- Después queda en ERROR permanente

BLINDAJE DE AISLAMIENTO (Abril 2026):
- Validación estricta de system_type antes de queries
- Validación de existencia de tablas requeridas
- try/except con rollback e invalidación de conexión
- Salida controlada si no corresponde ejecutar
- Logs claros de cada decisión

Fecha: Abril 2026
"""

import logging
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
import uuid
from dataclasses import dataclass, asdict

from ..job_logger import get_job_logger
from ..sql_repository import (
    get_active_servers,
    get_server_by_id,
    inventario_existe,
    registrar_inventario_procesando,
    actualizar_inventario_completado,
    actualizar_inventario_error,
    get_inventarios_pendientes_reintento,
    registrar_bitacora_job
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

COLLECTION_PROCESADOS = "inventarios_procesados_auto"
MAX_INTENTOS = 3
ESTADOS = {
    "EN_PROCESO": "EN_PROCESO",
    "COMPLETADO": "COMPLETADO", 
    "ERROR": "ERROR"
}

# Contexto de pool para jobs (aislado de endpoints web)
SQL_CONTEXT_JOBS = "jobs"

# Tablas requeridas por sistema para detección de inventarios
TABLAS_REQUERIDAS = {
    "SoftRestaurant": ["invfisico", "almacen"],
    "MPRO": []  # MPRO no tiene estructura de inventarios compatible
}

# Errores SQL que indican tabla/columna inexistente (requieren invalidar conexión)
ERRORES_ESTRUCTURA_SQL = [
    "nombre de objeto",
    "nombre de columna", 
    "invalid object name",
    "invalid column name",
    "no es válido",
    "does not exist"
]


# =============================================================================
# FUNCIONES DE BLINDAJE Y VALIDACIÓN
# =============================================================================

def _es_error_estructura_sql(error_msg: str) -> bool:
    """
    Detecta si un error SQL indica problema de estructura (tabla/columna inexistente).
    
    Estos errores requieren invalidar la conexión para evitar contaminar el pool.
    """
    error_lower = str(error_msg).lower()
    return any(indicador in error_lower for indicador in ERRORES_ESTRUCTURA_SQL)


def _validar_tabla_existe(servidor: Dict, tabla: str) -> bool:
    """
    Valida que una tabla exista en el servidor antes de ejecutar queries.
    
    AISLAMIENTO (Abril 2026): Usa context="jobs" para no afectar pool web.
    
    Args:
        servidor: Dict con configuración de conexión
        tabla: Nombre de la tabla a validar
        
    Returns:
        True si la tabla existe, False si no existe o hay error
    """
    from core.db import execute_sql_query
    
    try:
        # Query estándar SQL Server para verificar existencia de tabla
        query = f"""
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{tabla}'
        """
        result = execute_sql_query(
            servidor['host'],
            servidor['port'],
            servidor['database'],
            servidor['username'],
            servidor['password'],
            query,
            context=SQL_CONTEXT_JOBS  # AISLAMIENTO: Usar pool de jobs
        )
        existe = result is not None and len(result) > 0
        logger.debug(f"[INVENTARIOS_DETECTOR] Tabla '{tabla}' en {servidor['name']}: {'EXISTE' if existe else 'NO EXISTE'}")
        return existe
        
    except Exception as e:
        logger.warning(f"[INVENTARIOS_DETECTOR] Error verificando tabla '{tabla}' en {servidor['name']}: {e}")
        return False


def _invalidar_conexion_si_error_estructura(servidor: Dict, error: Exception) -> None:
    """
    Si el error indica problema de estructura SQL, invalida la conexión del pool de JOBS.
    
    AISLAMIENTO (Abril 2026): Solo afecta el pool "jobs", NO el pool "web".
    """
    if _es_error_estructura_sql(str(error)):
        try:
            from core.db import parse_sql_server_host
            from core.pool import get_pool_manager
            
            hostname, port, _ = parse_sql_server_host(servidor['host'], servidor['port'])
            pool_manager = get_pool_manager()
            # IMPORTANTE: Solo cerrar pool de jobs, NO el de web
            pool_manager.close_pool(hostname, port, servidor['database'], context=SQL_CONTEXT_JOBS)
            logger.warning(f"[INVENTARIOS_DETECTOR] Pool [jobs] invalidado para {servidor['name']} por error de estructura SQL")
        except Exception as cleanup_error:
            logger.error(f"[INVENTARIOS_DETECTOR] Error invalidando pool [jobs]: {cleanup_error}")


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class ClaveIdempotencia:
    """Clave única para evitar duplicados."""
    sistema_origen: str
    server_id: str
    sucursal_id: str
    almacen_id: str
    folio_inventario: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_query(self) -> Dict:
        """Genera filtro legacy de compatibilidad para buscar por esta clave."""
        return {
            "clave.sistema_origen": self.sistema_origen,
            "clave.server_id": self.server_id,
            "clave.sucursal_id": self.sucursal_id,
            "clave.almacen_id": self.almacen_id,
            "clave.folio_inventario": self.folio_inventario
        }


@dataclass  
class InventarioDetectado:
    """Estructura para inventario detectado."""
    clave: ClaveIdempotencia
    server_name: str
    almacen_nombre: str
    fecha_inventario: str
    folio_inicial: Optional[str]
    fecha_inicial: Optional[str]
    metadata: Dict


# =============================================================================
# JOB PRINCIPAL
# =============================================================================

class InventariosDetectorJob:
    """
    Job para detectar inventarios nuevos y disparar análisis automático.
    
    Control anti-duplicado:
    - Tracking operativo en SQL con compatibilidad legacy
    - Índice único por clave de idempotencia
    """
    
    def __init__(self, db, config: Optional[dict] = None):
        # Asegurar que db nunca sea None - usar StubDatabase
        if db is None:
            from core.mongo_stub import get_stub_database
            db = get_stub_database()
            logger.info("[INVENTARIOS_DETECTOR] Usando StubDatabase")
        
        self.db = db
        self.config = config or {}
        self.job_logger = get_job_logger(db)
        
        # Estadísticas de ejecución
        self.stats = {
            "servidores_escaneados": 0,
            "inventarios_detectados": 0,
            "inventarios_nuevos": 0,
            "inventarios_procesados": 0,
            "inventarios_error": 0,
            "inventarios_duplicados": 0,
            "inventarios_reintentados": 0,
            "errores_servidor": 0
        }
        
        # Límite de procesamiento por ejecución para evitar timeouts
        if config:
            self.max_inventarios_por_ejecucion = getattr(config, 'batch_size', 20)
        else:
            self.max_inventarios_por_ejecucion = 20
    
    def _is_stub_db(self) -> bool:
        """Detecta si self.db es StubDatabase."""
        if self.db is None:
            return True
        return hasattr(self.db, '_collections') and self.db.__class__.__name__ == 'StubDatabase'
    
    async def run(self, manual: bool = False, server_id_filter: str = None):
        """
        Ejecuta detección de inventarios nuevos.
        
        NOTA: Migrado a SQL Server (Mayo 2026).
        El tracking operativo de inventarios es SQL-first.
        
        Args:
            manual: True si es ejecución manual
            server_id_filter: Filtrar por servidor específico (opcional)
        """
        execution_type = "manual" if manual else "automatic"
        started_at = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())[:8]
        
        logger.info(f"[INVENTARIOS_DETECTOR] Iniciando ejecución SQL Server - {started_at.isoformat()}")
        
        # Registrar inicio en bitácora SQL
        await registrar_bitacora_job(
            job_name="inventarios_detector",
            run_id=run_id,
            accion="INICIO",
            detalles={"type": execution_type, "server_filter": server_id_filter}
        )
        
        # Iniciar log de ejecución
        log_entry = await self.job_logger.start_execution(
            job_name="inventarios_detector",
            metadata={
                "type": execution_type,
                "server_filter": server_id_filter
            }
        )
        
        try:
            # 1. Asegurar índice único
            await self._ensure_index()
            
            # 2. Obtener servidores activos
            servidores = await self._obtener_servidores(server_id_filter)
            logger.info(f"[INVENTARIOS_DETECTOR] Servidores a escanear: {len(servidores)}")
            
            # 3. Procesar errores pendientes de reintento
            try:
                await self._procesar_reintentos()
            except Exception as e:
                logger.warning(f"[INVENTARIOS_DETECTOR] Error procesando reintentos: {e}")
            
            # 4. Escanear cada servidor (capturar errores individualmente)
            for servidor in servidores:
                try:
                    await self._escanear_servidor(servidor)
                except Exception as e:
                    logger.error(f"[INVENTARIOS_DETECTOR] Error en servidor {servidor.get('name')}: {e}")
                    self.stats["errores_servidor"] = self.stats.get("errores_servidor", 0) + 1
            
            # 5. Determinar status final
            # success: al menos 1 procesado exitosamente
            # partial: hubo intentos pero todos fallaron
            # error: fallo crítico (no llegó a procesar)
            if self.stats["inventarios_procesados"] > 0:
                final_status = "success"
            elif self.stats["inventarios_detectados"] > 0:
                final_status = "partial"
            else:
                final_status = "success"  # No había nada que procesar
            
            # 6. Finalizar log (SIEMPRE se ejecuta)
            await self.job_logger.finish_execution(
                log_entry=log_entry,
                status=final_status,
                processed_count=self.stats["inventarios_procesados"],
                success_count=self.stats["inventarios_procesados"],
                failed_count=self.stats["inventarios_error"],
                skipped_count=self.stats["inventarios_duplicados"],
                message=self._generar_resumen(),
                extra_metadata={"stats": self.stats}
            )
            
            logger.info(f"[INVENTARIOS_DETECTOR] Finalizado ({final_status}) - {self._generar_resumen()}")
            
            return {
                "status": "SUCCESS",
                "stats": self.stats
            }
            
        except Exception as e:
            logger.error(f"[INVENTARIOS_DETECTOR] ERROR CRÍTICO: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            await self.job_logger.finish_execution(
                log_entry=log_entry,
                status="error",
                processed_count=self.stats["inventarios_procesados"],
                failed_count=self.stats["inventarios_error"],
                error_detail=str(e),
                extra_metadata={"stats": self.stats}
            )
            
            return {
                "status": "ERROR",
                "error": str(e),
                "stats": self.stats
            }
    
    async def _ensure_index(self):
        """Índice ya creado en SQL Server - No es necesario."""
        # La tabla Scheduler_InventariosProcesados ya tiene el UNIQUE constraint
        pass
    
    async def _obtener_servidores(self, server_id_filter: str = None) -> List[Dict]:
        """Obtiene servidores activos desde SQL Server."""
        logger.info("[INVENTARIOS_DETECTOR] _obtener_servidores: Usando SQL Server")
        
        servidores = await get_active_servers(server_id_filter)
        logger.info(f"[INVENTARIOS_DETECTOR] Obtenidos {len(servidores)} servidores de SQL")
        
        # Filtrar solo servidores con system_type compatible
        compatible = []
        for s in servidores:
            st = s.get('system_type', '').lower()
            if st in ['softrestaurant', 'sr', 'mpro']:
                compatible.append(s)
        
        return compatible
    
    async def _procesar_reintentos(self):
        """Procesa inventarios en ERROR que pueden reintentarse."""
        # Limitar reintentos por ejecución
        max_reintentos = 5
        
        # Buscar inventarios en ERROR con intentos < MAX desde SQL
        pendientes = await get_inventarios_pendientes_reintento(
            max_intentos=MAX_INTENTOS,
            limit=max_reintentos
        )
        
        for registro in pendientes:
            # Verificar límite global
            total_procesados = self.stats["inventarios_procesados"] + self.stats["inventarios_error"]
            if total_procesados >= self.max_inventarios_por_ejecucion:
                logger.info("[INVENTARIOS_DETECTOR] Límite alcanzado, saltando reintentos")
                break
            
            self.stats["inventarios_reintentados"] += 1
            logger.info(f"[INVENTARIOS_DETECTOR] Reintentando folio={registro.get('FolioInventario')}")
            
            # Construir registro compatible para procesamiento
            registro_compat = {
                'clave': {
                    'sistema_origen': registro.get('SistemaOrigen'),
                    'server_id': registro.get('ServerID'),
                    'sucursal_id': registro.get('SucursalID'),
                    'almacen_id': registro.get('AlmacenID'),
                    'folio_inventario': registro.get('FolioInventario')
                }
            }
            
            # Intentar procesar
            await self._procesar_inventario_desde_registro(registro_compat)
    
    async def _escanear_servidor(self, servidor: Dict):
        """Escanea un servidor en busca de inventarios nuevos."""
        server_name = servidor.get('name', 'Unknown')
        system_type = servidor.get('system_type', '')
        
        self.stats["servidores_escaneados"] += 1
        logger.info(f"[INVENTARIOS_DETECTOR] Escaneando {server_name} ({system_type})")
        
        try:
            # Detectar inventarios según tipo de sistema
            if system_type == 'SoftRestaurant':
                inventarios = await self._detectar_soft(servidor)
            elif system_type == 'MPRO':
                inventarios = await self._detectar_mpro(servidor)
            else:
                logger.warning(f"[INVENTARIOS_DETECTOR] Tipo de sistema desconocido: {system_type}")
                return
            
            self.stats["inventarios_detectados"] += len(inventarios)
            logger.info(f"[INVENTARIOS_DETECTOR] {server_name}: {len(inventarios)} inventarios detectados")
            
            # Procesar cada inventario detectado
            for inv in inventarios:
                await self._procesar_inventario(inv, servidor)
                
        except Exception as e:
            logger.warning(f"[INVENTARIOS_DETECTOR] {server_name}: Conexión fallida - {e}")
    
    async def _detectar_soft(self, servidor: Dict) -> List[InventarioDetectado]:
        """
        Detecta inventarios en SoftRestaurant.
        
        BLINDAJE (Abril 2026):
        - Valida system_type antes de ejecutar
        - Valida existencia de tabla invfisico
        - try/except con invalidación de conexión si error de estructura
        - Salida controlada si no corresponde
        """
        from core.db import execute_sql_query
        
        inventarios = []
        server_name = servidor.get('name', 'DESCONOCIDO')
        
        # BLINDAJE 1: Validar system_type
        system_type = servidor.get('system_type', '')
        if system_type != 'SoftRestaurant':
            logger.warning(f"[INVENTARIOS_DETECTOR] {server_name}: _detectar_soft llamado con system_type={system_type} (esperado: SoftRestaurant)")
            return inventarios
        
        # BLINDAJE 2: Validar existencia de tabla invfisico
        if not _validar_tabla_existe(servidor, 'invfisico'):
            logger.info(f"[INVENTARIOS_DETECTOR] {server_name}: Tabla 'invfisico' no existe - saltando detección")
            return inventarios
        
        try:
            # Query para obtener inventarios válidos recientes
            query = """
                WITH inventarios_validos AS (
                    SELECT
                        i.folio,
                        i.fecha,
                        i.idalmacen1 AS almacen_id,
                        a.nombre AS almacen_nombre,
                        ROW_NUMBER() OVER (
                            PARTITION BY i.idalmacen1, CONVERT(date, i.fecha)
                            ORDER BY i.folio DESC, i.fecha DESC
                        ) AS rn_dia
                    FROM invfisico i
                    LEFT JOIN almacen a ON a.idalmacen = i.idalmacen1
                    WHERE i.cancelado = 0
                      AND i.fecha >= DATEADD(MONTH, -2, GETDATE())
                )
                SELECT folio, fecha, almacen_id, almacen_nombre
                FROM inventarios_validos
                WHERE rn_dia = 1
                ORDER BY fecha DESC
            """
            
            result = execute_sql_query(
                servidor['host'],
                servidor['port'],
                servidor['database'],
                servidor['username'],
                servidor['password'],
                query,
                context=SQL_CONTEXT_JOBS  # AISLAMIENTO: Usar pool de jobs
            )
            
            if not result:
                logger.debug(f"[INVENTARIOS_DETECTOR] {server_name}: Sin inventarios recientes")
                return inventarios
            
            for row in result:
                folio = str(row['folio'])
                fecha_inv = row['fecha']
                almacen_id = str(row['almacen_id']) if row['almacen_id'] else ''
                almacen_nombre = row.get('almacen_nombre', almacen_id)
                
                # Convertir fecha
                if isinstance(fecha_inv, datetime):
                    fecha_str = fecha_inv.strftime('%Y-%m-%d')
                elif isinstance(fecha_inv, date):
                    fecha_str = fecha_inv.strftime('%Y-%m-%d')
                else:
                    fecha_str = str(fecha_inv)[:10]
                
                # Calcular folio inicial del período
                folio_inicial, fecha_inicial = await self._calcular_folio_inicial_soft(
                    servidor, almacen_id, fecha_str
                )
                
                clave = ClaveIdempotencia(
                    sistema_origen='SOFTRESTAURANT',
                    server_id=servidor['id'],
                    sucursal_id=servidor.get('name', ''),  # En Soft, sucursal = nombre servidor
                    almacen_id=almacen_id,
                    folio_inventario=folio
                )
                
                inventarios.append(InventarioDetectado(
                    clave=clave,
                    server_name=servidor['name'],
                    almacen_nombre=almacen_nombre,
                    fecha_inventario=fecha_str,
                    folio_inicial=folio_inicial,
                    fecha_inicial=fecha_inicial,
                    metadata={
                        "system_type": "SoftRestaurant",
                        "host": servidor['host'],
                        "database": servidor['database']
                    }
                ))
            
        except Exception as e:
            # BLINDAJE: Si es error de estructura SQL, invalidar conexión del pool
            _invalidar_conexion_si_error_estructura(servidor, e)
            logger.error(f"[INVENTARIOS_DETECTOR] Error detectando SOFT en {server_name}: {e}")
        
        return inventarios
    
    async def _detectar_mpro(self, servidor: Dict) -> List[InventarioDetectado]:
        """Detecta inventarios MPRO desde EDARSAHUB Sync (NO-LIVE)."""
        from modules.compras.sync_service import obtener_inventarios_fisicos_sync
        
        inventarios_detectados: List[InventarioDetectado] = []
        server_name = servidor.get('name', 'DESCONOCIDO')
        server_id = servidor.get('id')
        
        try:
            rows = obtener_inventarios_fisicos_sync(
                unidad_negocio_id=None,
                server_id=server_id,
                sucursal=None,
                almacen_id=None,
                almacen=None,
                limit=1000
            )
            
            if not rows:
                logger.info(f"[INVENTARIOS_DETECTOR] MPRO {server_name}: Sin inventarios sync")
                return inventarios_detectados
            
            grupos: Dict[str, List[Dict]] = {}
            for row in rows:
                folio = str(row.get('folio') or '').strip()
                fecha = str(row.get('fecha') or '').strip()
                almacen_id = str(row.get('almacen_id') or '').strip()
                sucursal_id = str(row.get('sucursal_id') or '').strip()
                
                if not folio or not fecha or not almacen_id:
                    continue
                
                key = f"{sucursal_id}|{almacen_id}"
                grupos.setdefault(key, []).append(row)
            
            for _, grupo in grupos.items():
                grupo_ordenado = sorted(
                    grupo,
                    key=lambda r: str(r.get('fecha') or ''),
                    reverse=True
                )
                
                if len(grupo_ordenado) < 2:
                    logger.info(f"[INVENTARIOS_DETECTOR] MPRO {server_name}: Grupo sin par inicial/final")
                    continue
                
                final = grupo_ordenado[0]
                inicial = grupo_ordenado[1]
                
                folio_final = str(final.get('folio') or '').strip()
                folio_inicial = str(inicial.get('folio') or '').strip()
                fecha_final = str(final.get('fecha') or '')[:10]
                fecha_inicial = str(inicial.get('fecha') or '')[:10]
                
                almacen_id = str(final.get('almacen_id') or '').strip()
                almacen_nombre = final.get('almacen') or almacen_id
                sucursal_id = str(final.get('sucursal_id') or final.get('sucursal') or '').strip()
                
                if not folio_final or not folio_inicial or not fecha_final or not fecha_inicial:
                    continue
                
                clave = ClaveIdempotencia(
                    sistema_origen='MPRO',
                    server_id=server_id,
                    sucursal_id=sucursal_id,
                    almacen_id=almacen_id,
                    folio_inventario=folio_final
                )
                
                inventarios_detectados.append(InventarioDetectado(
                    clave=clave,
                    server_name=server_name,
                    almacen_nombre=almacen_nombre,
                    fecha_inventario=fecha_final,
                    folio_inicial=folio_inicial,
                    fecha_inicial=fecha_inicial,
                    metadata={
                        "system_type": "MPRO",
                        "source": "EDARSAHUB_SYNC",
                        "sucursal": final.get('sucursal', ''),
                        "comentario_inicial": inicial.get('comentario', ''),
                        "comentario_final": final.get('comentario', '')
                    }
                ))
            
            logger.info(f"[INVENTARIOS_DETECTOR] MPRO {server_name}: {len(inventarios_detectados)} pares detectados desde Sync")
            
        except Exception as e:
            logger.error(f"[INVENTARIOS_DETECTOR] Error detectando MPRO en {server_name}: {e}")
        
        return inventarios_detectados
    
    async def _calcular_folio_inicial_soft(
        self, 
        servidor: Dict, 
        almacen_id: str, 
        fecha_fin: str
    ) -> tuple:
        """
        Calcula el folio inicial para SoftRestaurant.
        
        BLINDAJE (Abril 2026): 
        - Manejo de errores con invalidación de conexión
        """
        from core.db import execute_sql_query
        server_name = servidor.get('name', 'DESCONOCIDO')
        
        try:
            # Primer día del mes de la fecha final
            fecha_obj = datetime.strptime(fecha_fin, '%Y-%m-%d')
            primer_dia = fecha_obj.replace(day=1).strftime('%Y-%m-%d')
            
            query = f"""
                SELECT TOP 1 folio, fecha
                FROM invfisico
                WHERE cancelado = 0
                  AND idalmacen1 = '{almacen_id}'
                  AND fecha >= '{primer_dia}'
                ORDER BY fecha ASC, folio ASC
            """
            
            result = execute_sql_query(
                servidor['host'],
                servidor['port'],
                servidor['database'],
                servidor['username'],
                servidor['password'],
                query,
                context=SQL_CONTEXT_JOBS  # AISLAMIENTO: Usar pool de jobs
            )
            
            if result and len(result) > 0:
                folio = str(result[0]['folio'])
                fecha = result[0]['fecha']
                if isinstance(fecha, (datetime, date)):
                    fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)[:10]
                else:
                    fecha_str = str(fecha)[:10]
                return folio, fecha_str
            
        except Exception as e:
            # BLINDAJE: Invalidar conexión si error de estructura
            _invalidar_conexion_si_error_estructura(servidor, e)
            logger.warning(f"[INVENTARIOS_DETECTOR] Error calculando folio inicial en {server_name}: {e}")
        
        return None, None
    
    async def _calcular_folio_inicial_mpro(
        self,
        servidor: Dict,
        almacen_id: str,
        sucursal_id: str,
        fecha_fin: str
    ) -> tuple:
        """
        Calcula el folio inicial para MPRO.
        
        BLINDAJE (Abril 2026): MPRO no tiene tabla invfisico.
        Este método no debe ejecutarse - retorna None directamente.
        """
        # BLINDAJE: MPRO no tiene estructura de inventarios compatible
        # NO ejecutar query a tabla inexistente
        logger.debug("[INVENTARIOS_DETECTOR] _calcular_folio_inicial_mpro no implementado para MPRO (tabla invfisico no existe)")
        return None, None
    
    async def _procesar_inventario(self, inv: InventarioDetectado, servidor: Dict):
        """Procesa un inventario detectado."""
        clave = inv.clave
        
        # Verificar límite de procesamiento por ejecución
        total_procesados = self.stats["inventarios_procesados"] + self.stats["inventarios_error"]
        if total_procesados >= self.max_inventarios_por_ejecucion:
            logger.info(f"[INVENTARIOS_DETECTOR] Límite de {self.max_inventarios_por_ejecucion} alcanzado, saltando folio={clave.folio_inventario}")
            return
        
        # Verificar si ya existe (anti-duplicado) - usar SQL
        existe = await inventario_existe(
            sistema_origen=clave.sistema_origen,
            server_id=clave.server_id,
            sucursal_id=clave.sucursal_id,
            almacen_id=clave.almacen_id,
            folio_inventario=clave.folio_inventario
        )
        
        if existe:
            self.stats["inventarios_duplicados"] += 1
            logger.debug(f"[INVENTARIOS_DETECTOR] Duplicado: folio={clave.folio_inventario}")
            return
        
        self.stats["inventarios_nuevos"] += 1
        logger.info(f"[INVENTARIOS_DETECTOR] Nuevo inventario: folio={clave.folio_inventario}, almacen={inv.almacen_nombre}")
        
        # Pre-lock: Insertar registro con estado EN_PROCESO en SQL
        registro_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        registro = {
            "id": registro_id,
            "clave": clave.to_dict(),
            "server_name": inv.server_name,
            "almacen_nombre": inv.almacen_nombre,
            "fecha_inventario": inv.fecha_inventario,
            "folio_inicial": inv.folio_inicial,
            "fecha_inicial": inv.fecha_inicial,
            "estado": ESTADOS["EN_PROCESO"],
            "fecha_deteccion": now,
            "fecha_procesado": None,
            "analisis_resultado": None,
            "workflow_id": None,
            "workflow_creado": False,
            "error": None,
            "intentos": 1,
            "ultimo_intento": now,
            "metadata": inv.metadata
        }
        
        try:
            # Registrar en SQL Server
            success = await registrar_inventario_procesando(
                sistema_origen=clave.sistema_origen,
                server_id=clave.server_id,
                sucursal_id=clave.sucursal_id,
                almacen_id=clave.almacen_id,
                folio_inventario=clave.folio_inventario,
                detalles={
                    "server_name": inv.server_name,
                    "almacen_nombre": inv.almacen_nombre,
                    "folio_inicial": inv.folio_inicial
                }
            )
            if not success:
                # Ya está siendo procesado o error de duplicado
                self.stats["inventarios_duplicados"] += 1
                logger.info(f"[INVENTARIOS_DETECTOR] Ya en proceso: folio={clave.folio_inventario}")
                return
        except Exception as e:
            # DuplicateKeyError - ya está siendo procesado
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                self.stats["inventarios_duplicados"] += 1
                logger.info(f"[INVENTARIOS_DETECTOR] Ya en proceso: folio={clave.folio_inventario}")
                return
            raise
        
        # Ejecutar análisis
        await self._ejecutar_analisis(registro, servidor, inv)
    
    async def _procesar_inventario_desde_registro(self, registro: Dict):
        """Procesa un inventario desde un registro existente (reintento)."""
        # Obtener servidor desde SQL
        servidor = await get_server_by_id(registro["clave"]["server_id"])
        
        if not servidor:
            await self._marcar_error(registro, "Servidor no encontrado")
            return
        
        # Reconstruir InventarioDetectado
        clave = ClaveIdempotencia(**registro["clave"])
        inv = InventarioDetectado(
            clave=clave,
            server_name=registro.get("server_name", servidor.get('name', 'Unknown')),
            almacen_nombre=registro.get("almacen_nombre", ""),
            fecha_inventario=registro.get("fecha_inventario"),
            folio_inicial=registro.get("folio_inicial"),
            fecha_inicial=registro.get("fecha_inicial"),
            metadata=registro.get("metadata", {})
        )
        
        await self._ejecutar_analisis(registro, servidor, inv)
    
    async def _ejecutar_analisis(self, registro: Dict, servidor: Dict, inv: InventarioDetectado):
        """Ejecuta el análisis de inventario y orquestación."""
        clave = inv.clave
        
        try:
            logger.info(f"[INVENTARIOS_DETECTOR] Ejecutando análisis folio={clave.folio_inventario}")
            
            # Validar datos requeridos
            if not inv.folio_inicial:
                raise ValueError("No se encontró folio inicial del período")
            
            # Importar el core de análisis
            from core.inventory_analysis_core import InventoryAnalysisCore, InventoryAnalysisParams
            
            # Preparar parámetros
            params = InventoryAnalysisParams(
                server_id=servidor['id'],
                sucursal=clave.sucursal_id or servidor.get('name', ''),
                almacen=inv.almacen_nombre,
                almacenes=[inv.almacen_nombre],
                fecha_ini=inv.fecha_inicial,
                fecha_fin=inv.fecha_inventario,
                folio_inicial=inv.folio_inicial,
                folio_final=clave.folio_inventario,
                folios_iniciales=[inv.folio_inicial],
                folios_finales=[clave.folio_inventario]
            )
            
            # Ejecutar análisis usando generar_analisis (recibe Pydantic model)
            core = InventoryAnalysisCore(db_client=self.db)
            resultado = await core.generar_analisis(params)
            
            # Verificar resultado
            if resultado.get('error'):
                raise Exception(resultado.get('message', 'Error en análisis'))
            
            results = resultado.get('results', [])
            productos_con_diferencia = [r for r in results if abs(float(r.get('Diferencia_Cantidad', 0) or 0)) > 0.001]
            
            logger.info(f"[INVENTARIOS_DETECTOR] Análisis completado: {len(productos_con_diferencia)} diferencias")
            
            # Si hay diferencias, ejecutar orquestación
            workflow_id = None
            if productos_con_diferencia:
                workflow_id = await self._ejecutar_orquestacion(
                    servidor=servidor,
                    inv=inv,
                    resultados=results,
                    productos_diferencia=productos_con_diferencia
                )
            
            # Calcular métricas
            valor_total = sum(abs(float(p.get('Diferencia_Costo', 0) or 0)) for p in productos_con_diferencia)
            
            # Enviar reporte por email si aplica
            await self._enviar_reporte_analisis_email(
                servidor=servidor,
                inv=inv,
                productos_diferencia=productos_con_diferencia,
                valor_total=valor_total,
                workflow_id=workflow_id
            )
            
            # Actualizar registro como COMPLETADO en SQL
            await actualizar_inventario_completado(
                sistema_origen=clave.sistema_origen,
                server_id=clave.server_id,
                sucursal_id=clave.sucursal_id,
                almacen_id=clave.almacen_id,
                folio_inventario=clave.folio_inventario,
                workflow_id=workflow_id
            )
            
            self.stats["inventarios_procesados"] += 1
            logger.info(f"[INVENTARIOS_DETECTOR] Procesado exitosamente: folio={clave.folio_inventario}, workflow={workflow_id}")
            
        except Exception as e:
            logger.error(f"[INVENTARIOS_DETECTOR] ERROR en análisis folio={clave.folio_inventario}: {e}")
            await self._marcar_error(registro, str(e))
    
    async def _enviar_reporte_analisis_email(
        self,
        servidor: Dict,
        inv: InventarioDetectado,
        productos_diferencia: List[Dict],
        valor_total: float,
        workflow_id: Optional[str]
    ) -> None:
        """Envía reporte automático del análisis de inventario por email."""
        import os
        
        enabled = os.environ.get("SCHEDULER_INVENTARIOS_EMAIL_ENABLED", "false").lower() == "true"
        send_zero = os.environ.get("SCHEDULER_INVENTARIOS_EMAIL_SEND_ZERO", "false").lower() == "true"
        
        if not enabled:
            logger.info("[INVENTARIOS_DETECTOR] Email de análisis deshabilitado")
            return
        
        if not productos_diferencia and not send_zero:
            logger.info("[INVENTARIOS_DETECTOR] Sin diferencias; no se envía email")
            return
        
        try:
            from core.centro_control.email_notifications import send_critical_alert_email
            
            top = sorted(
                productos_diferencia,
                key=lambda r: abs(float(r.get("Diferencia_Costo", 0) or 0)),
                reverse=True
            )[:10]
            
            detalle_lineas = [
                f"Servidor: {servidor.get('name')}",
                f"Almacén: {inv.almacen_nombre}",
                f"Periodo: {inv.fecha_inicial} a {inv.fecha_inventario}",
                f"Folio inicial: {inv.folio_inicial}",
                f"Folio final: {inv.clave.folio_inventario}",
                f"Productos con diferencia: {len(productos_diferencia)}",
                f"Valor absoluto diferencias: ${valor_total:,.2f}",
                f"Workflow: {workflow_id or 'No creado'}",
                "",
                "Top diferencias:"
            ]
            
            for r in top:
                nombre = r.get("Nombre") or r.get("Producto") or r.get("Descripcion") or r.get("Codigo") or "Producto"
                cantidad = r.get("Diferencia_Cantidad", 0)
                costo = r.get("Diferencia_Costo", 0)
                detalle_lineas.append(f"- {nombre}: cantidad {cantidad}, costo ${float(costo or 0):,.2f}")
            
            severidad = "high" if valor_total > 0 else "medium"
            alerta = {
                "id": f"INV-{inv.clave.server_id}-{inv.clave.almacen_id}-{inv.clave.folio_inventario}",
                "titulo": f"Análisis automático de inventario - {inv.almacen_nombre}",
                "severidad": severidad,
                "modulo": "Inventarios",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "detalle": "\n".join(detalle_lineas)
            }
            
            result = await send_critical_alert_email(alerta)
            logger.info(f"[INVENTARIOS_DETECTOR] Email análisis inventario: {result}")
            
        except Exception as e:
            logger.error(f"[INVENTARIOS_DETECTOR] Error enviando email de análisis: {e}")
    
    async def _ejecutar_orquestacion(
        self,
        servidor: Dict,
        inv: InventarioDetectado,
        resultados: List[Dict],
        productos_diferencia: List[Dict]
    ) -> Optional[str]:
        """Ejecuta la orquestación para crear workflow."""
        try:
            from modules.fase2_operativo.services.orquestador_service import OrquestadorService
            
            orquestador = OrquestadorService(self.db)
            
            # Preparar datos completos para el orquestador
            resumen = await orquestador.procesar_analisis(
                server_id=servidor['id'],
                server_name=servidor['name'],
                sucursal_id=inv.clave.sucursal_id or servidor.get('name', ''),
                sucursal_nombre=inv.clave.sucursal_id or servidor.get('name', ''),
                almacen_id=inv.clave.almacen_id,
                almacen_nombre=inv.almacen_nombre,
                resultados_analisis=resultados,
                folios_iniciales=[inv.folio_inicial] if inv.folio_inicial else [],
                folios_finales=[inv.clave.folio_inventario],
                fecha_ini=inv.fecha_inicial or inv.fecha_inventario,
                fecha_fin=inv.fecha_inventario,
                usuario_ejecutor_id="SISTEMA_AUTOMATICO",
                usuario_ejecutor_nombre="Detector Automático",
                # NUEVO: Pasar folio_inventario explícitamente
                folio_inventario=inv.clave.folio_inventario
            )
            
            if resumen.get("workflow_creado"):
                logger.info(f"[INVENTARIOS_DETECTOR] Workflow creado: {resumen.get('workflow_id')}")
                return resumen.get("workflow_id")
            else:
                logger.info(f"[INVENTARIOS_DETECTOR] Workflow no creado: {resumen.get('mensaje', 'Sin detalles')}")
                return None
                
        except Exception as e:
            logger.error(f"[INVENTARIOS_DETECTOR] Error en orquestación: {e}")
            raise
    
    async def _marcar_error(self, registro: Dict, error_msg: str):
        """Marca un registro como ERROR en SQL."""
        clave = registro.get("clave", {})
        intentos = registro.get("intentos", 1)
        
        await actualizar_inventario_error(
            sistema_origen=clave.get("sistema_origen", ""),
            server_id=clave.get("server_id", ""),
            sucursal_id=clave.get("sucursal_id", ""),
            almacen_id=clave.get("almacen_id", ""),
            folio_inventario=clave.get("folio_inventario", ""),
            error_mensaje=error_msg
        )
        
        self.stats["inventarios_error"] += 1
        
        if intentos >= MAX_INTENTOS:
            logger.error(f"[INVENTARIOS_DETECTOR] ERROR CRÍTICO: Máximo de intentos alcanzado - {error_msg}")
        else:
            logger.warning(f"[INVENTARIOS_DETECTOR] Error (intento {intentos}/{MAX_INTENTOS}): {error_msg}")
    
    def _generar_resumen(self) -> str:
        """Genera resumen de la ejecución."""
        return (
            f"Detectados: {self.stats['inventarios_detectados']}, "
            f"Nuevos: {self.stats['inventarios_nuevos']}, "
            f"Procesados: {self.stats['inventarios_procesados']}, "
            f"Errores: {self.stats['inventarios_error']}, "
            f"Duplicados: {self.stats['inventarios_duplicados']}"
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_inventarios_detector_job(db, config: Optional[dict] = None) -> InventariosDetectorJob:
    """Factory function para crear el job."""
    return InventariosDetectorJob(db, config)
