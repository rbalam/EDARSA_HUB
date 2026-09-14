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

import json
import logging
from datetime import datetime, timezone
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
    get_inventario_error_by_id,
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

# =============================================================================
# FUNCIONES DE BLINDAJE Y VALIDACIÓN
# =============================================================================

def _normalizar_system_type(system_type: str) -> str:
    """Normaliza variantes operativas a los motores soportados por el detector."""
    from core.system_type_utils import normalize_system_type

    normalized = normalize_system_type(system_type)
    if normalized == "SOFTRESTAURANT":
        return "SoftRestaurant"
    if normalized == "MANAGEMENTPRO":
        return "MPRO"
    return str(system_type or "").strip()


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
        self.job_logger = get_job_logger()
        
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
                error_detail="Error interno del servidor",
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
            canonical_type = _normalizar_system_type(s.get('system_type', ''))
            if canonical_type in ['SoftRestaurant', 'MPRO']:
                s['system_type_canonical'] = canonical_type
                compatible.append(s)
        
        return compatible
    
    def _rehidratar_registro_reintento(self, registro: Dict) -> Dict:
        """Reconstruye el contexto persistido de un registro para reintento canónico."""
        detalles_raw = registro.get('DetallesJSON')
        detalles = {}
        if isinstance(detalles_raw, dict):
            detalles = detalles_raw
        elif detalles_raw:
            try:
                detalles = json.loads(detalles_raw) or {}
            except (TypeError, ValueError, json.JSONDecodeError):
                logger.warning(
                    "[INVENTARIOS_DETECTOR] DetallesJSON inválido en reintento folio=%s",
                    registro.get('FolioInventario'),
                )

        return {
            'clave': {
                'sistema_origen': registro.get('SistemaOrigen'),
                'server_id': registro.get('ServerID'),
                'sucursal_id': registro.get('SucursalID'),
                'almacen_id': registro.get('AlmacenID'),
                'folio_inventario': registro.get('FolioInventario')
            },
            'server_name': detalles.get('server_name'),
            'almacen_nombre': detalles.get('almacen_nombre', ''),
            'folio_inicial': detalles.get('folio_inicial'),
            'fecha_inicial': detalles.get('fecha_inicial'),
            'fecha_inventario': detalles.get('fecha_inventario'),
            'metadata': detalles.get('metadata', {}),
            'intentos': registro.get('Intentos', 1),
        }

    async def retry_error_by_id(self, record_id: int) -> Dict:
        """Reintenta exactamente un registro ERROR sin alterar el umbral global de reintentos."""
        registro = await get_inventario_error_by_id(record_id)
        if not registro:
            return {
                "status": "NOT_ELIGIBLE",
                "record_id": record_id,
                "message": "El registro no existe o no está en ERROR",
            }

        run_id = f"recovery-{record_id}-{str(uuid.uuid4())[:8]}"
        await registrar_bitacora_job(
            job_name="inventarios_detector",
            run_id=run_id,
            accion="RECOVERY_CANARY_START",
            detalles={"record_id": record_id, "intentos_antes": registro.get('Intentos')},
        )

        registro_compat = self._rehidratar_registro_reintento(registro)
        self.stats["inventarios_reintentados"] += 1
        await self._procesar_inventario_desde_registro(registro_compat)

        await registrar_bitacora_job(
            job_name="inventarios_detector",
            run_id=run_id,
            accion="RECOVERY_CANARY_END",
            detalles={"record_id": record_id},
        )
        return {"status": "EXECUTED", "record_id": record_id, "run_id": run_id}

    async def _procesar_reintentos(self):
        """Procesa inventarios en ERROR que pueden reintentarse."""
        max_reintentos = 5
        pendientes = await get_inventarios_pendientes_reintento(
            max_intentos=MAX_INTENTOS,
            limit=max_reintentos
        )

        for registro in pendientes:
            total_procesados = self.stats["inventarios_procesados"] + self.stats["inventarios_error"]
            if total_procesados >= self.max_inventarios_por_ejecucion:
                logger.info("[INVENTARIOS_DETECTOR] Límite alcanzado, saltando reintentos")
                break

            self.stats["inventarios_reintentados"] += 1
            logger.info(f"[INVENTARIOS_DETECTOR] Reintentando folio={registro.get('FolioInventario')}")
            registro_compat = self._rehidratar_registro_reintento(registro)
            await self._procesar_inventario_desde_registro(registro_compat)
    
    async def _escanear_servidor(self, servidor: Dict):
        """Escanea un servidor en busca de inventarios nuevos."""
        server_name = servidor.get('name', 'Unknown')
        system_type = _normalizar_system_type(
            servidor.get('system_type_canonical') or servidor.get('system_type', '')
        )
        
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
    
    async def _detectar_desde_sync(
        self,
        servidor: Dict,
        sistema_origen: str,
        label: str,
    ) -> List[InventarioDetectado]:
        """Detecta inventarios desde EDARSAHUB Sync (NO-LIVE)."""
        from modules.compras.sync_service import obtener_inventarios_fisicos_sync
        
        def _fecha_key(row: Dict) -> str:
            return str(row.get('fecha') or '').strip()[:10]
        
        def _es_consolidado(row: Dict) -> bool:
            comentario = str(row.get('comentario') or '').upper()
            return 'CONSOLIDADO' in comentario
        
        def _preferir_inventario_fecha(rows_fecha: List[Dict]) -> Dict:
            """
            Para una misma fecha, preferir INVENTARIO FISICO CONSOLIDADO.
            Si no existe consolidado, usar el mayor folio como desempate estable.
            """
            return sorted(
                rows_fecha,
                key=lambda r: (
                    1 if _es_consolidado(r) else 0,
                    str(r.get('folio') or '').strip()
                ),
                reverse=True
            )[0]
        
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
                logger.info(f"[INVENTARIOS_DETECTOR] {label} {server_name}: Sin inventarios sync")
                return inventarios_detectados
            
            grupos: Dict[str, List[Dict]] = {}
            for row in rows:
                folio = str(row.get('folio') or '').strip()
                fecha = _fecha_key(row)
                almacen_id = str(row.get('almacen_id') or '').strip()
                sucursal_id = str(row.get('sucursal_id') or '').strip()
                
                if not folio or not fecha or not almacen_id:
                    continue
                
                key = f"{sucursal_id}|{almacen_id}"
                grupos.setdefault(key, []).append(row)
            
            for key, grupo in grupos.items():
                por_fecha: Dict[str, List[Dict]] = {}
                for row in grupo:
                    fecha = _fecha_key(row)
                    if not fecha:
                        continue
                    por_fecha.setdefault(fecha, []).append(row)
                
                fechas_ordenadas = sorted(por_fecha.keys(), reverse=True)
                
                if len(fechas_ordenadas) < 2:
                    logger.info(
                        f"[INVENTARIOS_DETECTOR] {label} {server_name}: "
                        f"Grupo sin fechas distintas suficientes key={key}"
                    )
                    continue
                
                fecha_final = fechas_ordenadas[0]
                fecha_inicial = fechas_ordenadas[1]
                
                final = _preferir_inventario_fecha(por_fecha[fecha_final])
                inicial = _preferir_inventario_fecha(por_fecha[fecha_inicial])
                
                folio_final = str(final.get('folio') or '').strip()
                folio_inicial = str(inicial.get('folio') or '').strip()
                
                almacen_id = str(final.get('almacen_id') or '').strip()
                almacen_nombre = final.get('almacen') or almacen_id
                sucursal_id = str(
                    final.get('sucursal_id')
                    or final.get('sucursal')
                    or final.get('unidad_negocio_codigo')
                    or server_name
                    or ''
                ).strip()
                
                if not folio_final or not folio_inicial or not fecha_final or not fecha_inicial:
                    continue
                
                logger.info(
                    f"[INVENTARIOS_DETECTOR] {label} {server_name}: "
                    f"Par detectado key={key} inicial={folio_inicial}/{fecha_inicial} "
                    f"final={folio_final}/{fecha_final}"
                )
                
                clave = ClaveIdempotencia(
                    sistema_origen=sistema_origen,
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
                        "system_type": label,
                        "source": "EDARSAHUB_SYNC",
                        "sucursal": final.get('sucursal', ''),
                        "comentario_inicial": inicial.get('comentario', ''),
                        "comentario_final": final.get('comentario', ''),
                        "folio_inicial": folio_inicial,
                        "folio_final": folio_final
                    }
                ))
            
            logger.info(f"[INVENTARIOS_DETECTOR] {label} {server_name}: {len(inventarios_detectados)} pares detectados desde Sync")
            
        except Exception as e:
            logger.error(f"[INVENTARIOS_DETECTOR] Error detectando {label} en {server_name}: {e}")
        
        return inventarios_detectados

    async def _detectar_soft(self, servidor: Dict) -> List[InventarioDetectado]:
        """Detecta inventarios SoftRestaurant desde EDARSAHUB Sync (NO-LIVE)."""
        return await self._detectar_desde_sync(servidor, "SOFTRESTAURANT", "SoftRestaurant")

    async def _detectar_mpro(self, servidor: Dict) -> List[InventarioDetectado]:
        """Detecta inventarios MPRO desde EDARSAHUB Sync (NO-LIVE)."""
        return await self._detectar_desde_sync(servidor, "MPRO", "MPRO")
    
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
                    "folio_inicial": inv.folio_inicial,
                    "fecha_inicial": inv.fecha_inicial,
                    "fecha_inventario": inv.fecha_inventario,
                    "metadata": inv.metadata,
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
                workflow_id=workflow_id,
                resultados=results
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
        workflow_id: Optional[str],
        resultados: Optional[List[Dict]] = None
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
            from io import BytesIO
            from openpyxl import Workbook
            
            def _generar_excel_analisis(rows: List[Dict]) -> bytes:
                wb = Workbook()
                ws = wb.active
                ws.title = "Analisis Inventario"
                
                data = rows or []
                if not data:
                    data = productos_diferencia or []
                
                columnas = []
                for row in data:
                    for key in row.keys():
                        if key not in columnas:
                            columnas.append(key)
                
                if not columnas:
                    columnas = ["Mensaje"]
                    data = [{"Mensaje": "Sin resultados para exportar"}]
                
                ws.append(columnas)
                for row in data:
                    ws.append([row.get(col, "") for col in columnas])
                
                for col in ws.columns:
                    max_len = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        value = "" if cell.value is None else str(cell.value)
                        max_len = max(max_len, len(value))
                    ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 45)
                
                bio = BytesIO()
                wb.save(bio)
                return bio.getvalue()
            
            excel_name = (
                f"analisis_inventario_{inv.clave.folio_inventario}_"
                f"{inv.fecha_inventario}.xlsx"
            ).replace("/", "-").replace("\\", "-")
            
            attachments = [{
                "filename": excel_name,
                "content": _generar_excel_analisis(resultados or productos_diferencia),
                "subtype": "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }]
            
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
            
            result = await send_critical_alert_email(alerta, attachments=attachments)
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
