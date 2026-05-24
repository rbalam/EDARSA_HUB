"""
EDARSA HUB - Job de Detección de Pedidos para Automatización Operativa
======================================================================
FASE 4.1 y 4.2 - Auditoría Operativa de Compras

Job del scheduler para detectar pedidos nuevos en MPro/Soft y disparar
la automatización operativa de compras.

FLUJO COMPLETO:
1. Obtener Unidades de Negocio (empresas) activas
2. Para cada empresa, obtener sus servidores asociados
3. Consultar pedidos vigentes de cada servidor
4. Comparar contra pedidos ya procesados (anti-duplicado)
5. Para pedidos nuevos:
   - FASE 4.1: Crear registro base de auditoría
   - FASE 4.2: Validar inventario
     - Si falta inventario → Crear tarea operativa (PENDIENTE_INVENTARIO)
     - Si hay inventario → Ejecutar auditoría (EN_AUDITORIA)
6. Registrar bitácora completa

EJES FUNCIONALES:
- Unidad de Negocio (empresa) como eje principal
- server_id solo para uso interno (nunca expuesto)
- Anti-duplicados por (empresa_id, pedido_folio, origen)

REGLA ARQUITECTÓNICA OBLIGATORIA:
"Un resultado en cero solo es válido si hubo consulta real exitosa a la fuente correcta.
Si no hubo acceso a la fuente, el resultado no es cero: es fuente no consultada."

"No conviertas limitaciones de infraestructura en datos de negocio."
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict
import uuid
import time

from ..job_logger import get_job_logger
from core.source_resolver import (
    QueryStatus,
    SourceQueryResult,
    AggregatedQueryResult,
    classify_sql_error
)

logger = logging.getLogger(__name__)


class PedidosDetectorJob:
    """
    Job para detectar pedidos nuevos y disparar automatización.
    
    FASE 4.1: Detección automática por Unidad de Negocio
    FASE 4.2: Validación de inventario + tareas operativas
    
    Control anti-duplicado:
    - Colección `pedidos_procesados_automatizacion` en EDARSA HUB
    - Índice único por (empresa_id, pedido_folio, origen)
    
    ESTADOS DE CONSULTA:
    - SUCCESS_WITH_DATA: Consulta exitosa con pedidos encontrados
    - SUCCESS_EMPTY: Consulta exitosa, cero pedidos (resultado real)
    - SOURCE_UNREACHABLE: Fuente no accesible (nunca se devuelve como cero)
    - CONNECTION_COOLDOWN: Servidor en periodo de espera
    - PARTIAL_SUCCESS: Algunas fuentes respondieron, otras no
    """
    
    COLLECTION_PROCESADOS = "pedidos_procesados_automatizacion"
    COLLECTION_TAREAS = "tareas_operativas_compras"
    COLLECTION_BITACORA = "auditoria_compras_bitacora"
    
    def __init__(self, db, config: Optional[dict] = None):
        self.db = db
        self.config = config or {}
        self.job_logger = get_job_logger(db)
    
    def _is_stub_db(self) -> bool:
        """Detecta si self.db es StubDatabase."""
        if self.db is None:
            return True
        return hasattr(self.db, '_collections') and self.db.__class__.__name__ == 'StubDatabase'
    
    async def run(self, manual: bool = False, empresa_id_filter: str = None):
        """
        Ejecuta detección de pedidos nuevos.
        
        FASE 4.1: Resuelve por Unidad de Negocio (empresa)
        FASE 4.2: Valida inventario y crea tareas si falta
        
        REGLA ARQUITECTÓNICA:
        - Cero solo es válido si hubo consulta real exitosa
        - Fuente no consultada NUNCA se reporta como cero
        
        Args:
            manual: True si es ejecución manual (para pruebas)
            empresa_id_filter: Filtrar por empresa específica (opcional)
        """
        execution_type = "manual" if manual else "automatic"
        started_at = datetime.now(timezone.utc)
        
        # MongoDB ELIMINADO - Si db es StubDatabase, saltar ejecución
        if self._is_stub_db():
            logger.info(f"[PEDIDOS_DETECTOR] SKIPPED - MongoDB eliminado, usando StubDatabase")
            await self.job_logger.log_skipped(
                job_name="pedidos_detector",
                reason="MongoDB ELIMINADO - Job deshabilitado (StubDatabase)"
            )
            return
        
        # Iniciar log de ejecución
        log_entry = await self.job_logger.start_execution(
            job_name="pedidos_detector",
            metadata={
                "type": execution_type,
                "empresa_filter": empresa_id_filter
            }
        )
        
        # Contadores con distinción de estados
        stats = {
            "empresas_procesadas": 0,
            "servidores_consultados": 0,
            # Estados de consulta (NUEVOS - distinguen fuente no consultada)
            "servidores_exitosos": 0,        # Consulta exitosa (con o sin datos)
            "servidores_sin_conexion": 0,    # SOURCE_UNREACHABLE / CONNECTION_COOLDOWN
            "servidores_con_error": 0,       # Otros errores
            # Resultados de negocio (solo de consultas exitosas)
            "pedidos_detectados": 0,         # Solo de consultas SUCCESS
            "pedidos_nuevos": 0,
            "ya_procesados": 0,
            "tareas_creadas": 0,
            "auditorias_iniciadas": 0,
            "fallidos": 0,
            # Estado general
            "estado_consulta": "PENDING",    # SUCCESS / PARTIAL / SOURCE_UNREACHABLE / ERROR
            "fuentes_consultadas": [],       # Detalle por servidor
        }
        
        # Resultado agregado para tracking detallado
        aggregated_result = AggregatedQueryResult()
        aggregated_result.started_at = started_at.isoformat()
        
        try:
            # =====================================================
            # FASE 4.1: RESOLVER POR UNIDAD DE NEGOCIO
            # =====================================================
            
            # Obtener empresas activas
            empresas = await self._obtener_empresas_activas(empresa_id_filter)
            logger.info(f"[PEDIDOS_DETECTOR] Empresas activas: {len(empresas)}")
            
            if not empresas:
                stats["estado_consulta"] = "NO_SOURCES"
                await self._registrar_bitacora_job("SIN_EMPRESAS", {
                    "mensaje": "No hay empresas activas configuradas",
                    "estado_consulta": "NO_SOURCES"
                })
                await self.job_logger.finish_execution(
                    log_entry,
                    status="skipped",
                    message="Sin empresas activas"
                )
                return stats
            
            for empresa in empresas:
                empresa_id = empresa["id"]
                empresa_nombre = empresa.get("nombre", empresa_id)
                stats["empresas_procesadas"] += 1
                
                try:
                    # Obtener servidores de esta empresa
                    servidores = await self._obtener_servidores_empresa(empresa_id)
                    
                    if not servidores:
                        logger.debug(f"[PEDIDOS_DETECTOR] {empresa_nombre}: Sin servidores asociados")
                        continue
                    
                    logger.info(f"[PEDIDOS_DETECTOR] {empresa_nombre}: {len(servidores)} servidores")
                    
                    for server in servidores:
                        server_id = server["id"]  # Solo para uso interno
                        server_name = server.get("name", server_id)
                        stats["servidores_consultados"] += 1
                        
                        # =====================================================
                        # CONSULTA CON ENVELOPE DE RESULTADO
                        # =====================================================
                        query_result = await self._consultar_pedidos_con_estado(server)
                        
                        # Agregar al resultado agregado
                        aggregated_result.add_result(query_result)
                        
                        # Registrar estado de la fuente
                        fuente_info = {
                            "server_id": server_id,
                            "server_name": server_name,
                            "empresa_id": empresa_id,
                            "status": query_result.status.value,
                            "query_executed": query_result.query_executed,
                            "row_count": query_result.row_count,
                            "error_message": query_result.error_message
                        }
                        stats["fuentes_consultadas"].append(fuente_info)
                        
                        # =====================================================
                        # CLASIFICAR SEGÚN ESTADO DE CONSULTA
                        # =====================================================
                        if not query_result.query_executed:
                            # FUENTE NO CONSULTADA - NUNCA tratar como cero
                            if query_result.status == QueryStatus.CONNECTION_COOLDOWN:
                                stats["servidores_sin_conexion"] += 1
                                logger.warning(
                                    f"[PEDIDOS_DETECTOR] {server_name}: EN COOLDOWN - "
                                    f"Fuente NO consultada ({query_result.cooldown_remaining_seconds}s restantes)"
                                )
                            elif query_result.status == QueryStatus.SOURCE_UNREACHABLE:
                                stats["servidores_sin_conexion"] += 1
                                logger.warning(
                                    f"[PEDIDOS_DETECTOR] {server_name}: NO ACCESIBLE - "
                                    f"Fuente NO consultada: {query_result.error_message}"
                                )
                            else:
                                stats["servidores_con_error"] += 1
                                logger.error(
                                    f"[PEDIDOS_DETECTOR] {server_name}: ERROR - "
                                    f"{query_result.status.value}: {query_result.error_message}"
                                )
                            
                            # Bitácora: fuente no consultada
                            await self._registrar_bitacora_job("FUENTE_NO_CONSULTADA", {
                                "empresa_id": empresa_id,
                                "empresa_nombre": empresa_nombre,
                                "server_id": server_id,
                                "server_name": server_name,
                                "status": query_result.status.value,
                                "error": query_result.error_message,
                                "query_executed": False,
                                "is_retriable": query_result.is_retriable
                            })
                            continue
                        
                        # =====================================================
                        # CONSULTA EXITOSA - Ahora sí podemos confiar en el resultado
                        # =====================================================
                        stats["servidores_exitosos"] += 1
                        pedidos = query_result.data
                        
                        if not pedidos:
                            # SUCCESS_EMPTY: Consulta exitosa, cero real
                            logger.info(
                                f"[PEDIDOS_DETECTOR] {server_name}: "
                                f"Consulta exitosa - 0 pedidos vigentes (resultado real)"
                            )
                            continue
                        
                        # SUCCESS_WITH_DATA: Hay pedidos para procesar
                        logger.info(
                            f"[PEDIDOS_DETECTOR] {empresa_nombre}/{server_name}: "
                            f"{len(pedidos)} pedidos vigentes detectados"
                        )
                        
                        for pedido in pedidos:
                            stats["pedidos_detectados"] += 1
                            folio = str(pedido.get("folio", pedido.get("Folio", "")))
                            origen = pedido.get("origen", server.get("system_type", "MPRO"))
                            
                            # =====================================================
                            # ANTI-DUPLICADOS: Por empresa_id, no server_id
                            # =====================================================
                            if await self._ya_procesado(empresa_id, folio, origen):
                                stats["ya_procesados"] += 1
                                continue
                            
                            # =====================================================
                            # FASE 4.1: CREAR REGISTRO BASE DE AUDITORÍA
                            # FASE 4.2: VALIDAR INVENTARIO
                            # =====================================================
                            try:
                                resultado = await self._procesar_pedido_nuevo(
                                    empresa=empresa,
                                    server=server,
                                    pedido=pedido
                                )
                                
                                if resultado:
                                    stats["pedidos_nuevos"] += 1
                                    
                                    if resultado.get("tarea_creada"):
                                        stats["tareas_creadas"] += 1
                                        logger.info(
                                            f"[PEDIDOS_DETECTOR] {folio}: "
                                            f"PENDIENTE_INVENTARIO - Tarea creada"
                                        )
                                    elif resultado.get("auditoria_iniciada"):
                                        stats["auditorias_iniciadas"] += 1
                                        logger.info(
                                            f"[PEDIDOS_DETECTOR] {folio}: "
                                            f"EN_AUDITORIA - Auditoría iniciada"
                                        )
                                else:
                                    stats["fallidos"] += 1
                                    
                            except Exception as e:
                                stats["fallidos"] += 1
                                logger.error(
                                    f"[PEDIDOS_DETECTOR] Error procesando {folio}: {e}"
                                )
                                await self._registrar_bitacora_job("ERROR_PEDIDO", {
                                    "empresa_id": empresa_id,
                                    "folio": folio,
                                    "error": str(e)
                                })
                
                except Exception as e:
                    logger.error(
                        f"[PEDIDOS_DETECTOR] Error empresa {empresa_nombre}: {e}"
                    )
                    await self._registrar_bitacora_job("ERROR_EMPRESA", {
                        "empresa_id": empresa_id,
                        "error": str(e)
                    })
            
            # =====================================================
            # DETERMINAR ESTADO GENERAL DE CONSULTA
            # =====================================================
            overall_status = aggregated_result.get_overall_status()
            stats["estado_consulta"] = overall_status.value
            
            # Determinar estado para el log
            if overall_status == QueryStatus.SOURCE_UNREACHABLE:
                status = "source_unreachable"
                message = self._format_stats_message_with_state(stats)
            elif overall_status == QueryStatus.PARTIAL_SUCCESS:
                status = "partial"
                message = self._format_stats_message_with_state(stats)
            elif stats["fallidos"] > 0:
                status = "partial"
                message = self._format_stats_message_with_state(stats)
            elif stats["pedidos_nuevos"] > 0:
                status = "success"
                message = self._format_stats_message_with_state(stats)
            else:
                status = "success"
                message = self._format_stats_message_with_state(stats)
            
            # Completar resultado agregado
            completed_at = datetime.now(timezone.utc)
            aggregated_result.completed_at = completed_at.isoformat()
            aggregated_result.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            # Finalizar log
            await self.job_logger.finish_execution(
                log_entry,
                status=status,
                processed_count=stats["pedidos_detectados"],
                success_count=stats["pedidos_nuevos"],
                failed_count=stats["fallidos"],
                message=message
            )
            
            # Bitácora de ejecución con estados claros
            await self._registrar_bitacora_job("EJECUCION_COMPLETADA", {
                **stats,
                "estado_consulta": overall_status.value,
                "duration_ms": aggregated_result.duration_ms,
                "resumen_fuentes": aggregated_result.to_dict()
            })
            
            logger.info(f"[PEDIDOS_DETECTOR] {message}")
            
            return stats
            
        except Exception as e:
            stats["estado_consulta"] = "ERROR"
            
            await self.job_logger.finish_execution(
                log_entry,
                status="failed",
                processed_count=stats["pedidos_detectados"],
                success_count=stats["pedidos_nuevos"],
                failed_count=stats["fallidos"],
                error_detail=str(e),
                message=f"Error: {str(e)}"
            )
            
            await self._registrar_bitacora_job("ERROR_GENERAL", {
                "error": str(e),
                "stats": stats
            })
            
            logger.error(f"[PEDIDOS_DETECTOR] Error general: {e}")
            raise
    
    def _format_stats_message(self, stats: Dict) -> str:
        """Formatea mensaje de estadísticas (legacy)."""
        return self._format_stats_message_with_state(stats)
    
    def _format_stats_message_with_state(self, stats: Dict) -> str:
        """Formatea mensaje de estadísticas con estado de consulta."""
        estado = stats.get("estado_consulta", "UNKNOWN")
        
        base_msg = (
            f"Estado: {estado} | "
            f"Empresas: {stats['empresas_procesadas']}, "
            f"Servidores: {stats['servidores_consultados']} "
            f"(OK: {stats['servidores_exitosos']}, "
            f"Sin conexión: {stats['servidores_sin_conexion']}, "
            f"Error: {stats['servidores_con_error']})"
        )
        
        if stats['servidores_exitosos'] > 0:
            base_msg += (
                f" | Pedidos detectados: {stats['pedidos_detectados']}, "
                f"Nuevos: {stats['pedidos_nuevos']}, "
                f"Ya procesados: {stats['ya_procesados']}, "
                f"Tareas: {stats['tareas_creadas']}, "
                f"Auditorías: {stats['auditorias_iniciadas']}"
            )
        
        if stats['servidores_sin_conexion'] > 0:
            base_msg += f" | ADVERTENCIA: {stats['servidores_sin_conexion']} fuentes NO consultadas"
        
        return base_msg
    
    # =========================================================================
    # OBTENCIÓN DE EMPRESAS Y SERVIDORES
    # =========================================================================
    
    async def _obtener_empresas_activas(self, empresa_id_filter: str = None) -> List[Dict]:
        """
        Obtiene empresas (Unidades de Negocio) activas.
        
        FASE 4.1: La empresa es el eje funcional, no el servidor.
        """
        filtro = {"activa": True}
        if empresa_id_filter:
            filtro["id"] = empresa_id_filter
        
        cursor = self.db.empresas.find(filtro, {"_id": 0})
        return await cursor.to_list(100)
    
    async def _obtener_servidores_empresa(self, empresa_id: str) -> List[Dict]:
        """
        Obtiene servidores asociados a una empresa vía sucursales.
        
        Flujo: empresa → sucursales → mapeo → servidores
        """
        # Obtener sucursales de la empresa
        sucursales = await self.db.sucursales_catalogo.find(
            {"empresa_id": empresa_id, "activa": True},
            {"id": 1}
        ).to_list(100)
        
        if not sucursales:
            return []
        
        sucursal_ids = [s["id"] for s in sucursales]
        
        # Obtener mapeos a servidores
        mapeos = await self.db.sucursal_servidor_map.find(
            {"sucursal_id": {"$in": sucursal_ids}},
            {"server_id": 1, "sucursal_id": 1, "sucursal_origen_id": 1}
        ).to_list(100)
        
        if not mapeos:
            return []
        
        # Obtener servidores únicos
        server_ids = list(set(m["server_id"] for m in mapeos))
        
        cursor = self.db.servers.find(
            {
                "id": {"$in": server_ids},
                "active": True,
                "system_type": {"$in": ["MPRO", "SoftRestaurant"]}
            },
            {"_id": 0}
        )
        servidores = await cursor.to_list(100)
        
        # Enriquecer servidores con info de mapeo
        for server in servidores:
            server_mapeos = [m for m in mapeos if m["server_id"] == server["id"]]
            server["_mapeos"] = server_mapeos
        
        return servidores
    
    # =========================================================================
    # CONSULTA DE PEDIDOS CON ENVELOPE DE RESULTADO
    # =========================================================================
    
    async def _consultar_pedidos_con_estado(self, server: Dict) -> SourceQueryResult:
        """
        Consulta pedidos vigentes de un servidor con envelope de resultado.
        
        REGLA ARQUITECTÓNICA:
        - NUNCA devuelve lista vacía para ocultar error de conexión
        - Distingue SUCCESS_EMPTY (cero real) de SOURCE_UNREACHABLE (no consultado)
        """
        server_id = server["id"]
        server_name = server.get("name", server_id)
        source_type = server.get("system_type", "MPRO")
        start_time = time.time()
        
        try:
            from modules.compras.service import obtener_pedidos_vigentes
            
            # Intentar consulta real
            pedidos = await obtener_pedidos_vigentes(server_id)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if pedidos and len(pedidos) > 0:
                return SourceQueryResult.success_with_data(
                    data=pedidos,
                    source_type=source_type,
                    source_id=server_id,
                    duration_ms=duration_ms,
                    metadata={"server_name": server_name}
                )
            else:
                # Lista vacía = consulta exitosa sin resultados (cero real)
                return SourceQueryResult.success_empty(
                    source_type=source_type,
                    source_id=server_id,
                    duration_ms=duration_ms,
                    metadata={"server_name": server_name}
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Clasificar el error
            status = classify_sql_error(e)
            
            # Verificar si es cooldown (servidor offline en memoria)
            from core.db import is_server_offline_in_memory, get_server_cooldown_info
            if is_server_offline_in_memory(server.get("host", "")):
                cooldown = get_server_cooldown_info(server.get("host", ""))
                remaining = int(cooldown.get("remaining_seconds", 0))
                return SourceQueryResult.connection_cooldown(
                    source_type=source_type,
                    source_id=server_id,
                    cooldown_remaining_seconds=remaining,
                    metadata={"server_name": server_name, "host": server.get("host")}
                )
            
            # Retornar según clasificación
            if status == QueryStatus.SOURCE_UNREACHABLE:
                return SourceQueryResult.source_unreachable(
                    source_type=source_type,
                    source_id=server_id,
                    error_message=str(e),
                    metadata={"server_name": server_name}
                )
            elif status == QueryStatus.AUTH_ERROR:
                return SourceQueryResult.auth_error(
                    source_type=source_type,
                    source_id=server_id,
                    error_message=str(e),
                    metadata={"server_name": server_name}
                )
            elif status == QueryStatus.QUERY_TIMEOUT:
                return SourceQueryResult.query_timeout(
                    source_type=source_type,
                    source_id=server_id,
                    timeout_seconds=45,
                    metadata={"server_name": server_name}
                )
            else:
                return SourceQueryResult.unknown_error(
                    source_type=source_type,
                    source_id=server_id,
                    error_message=str(e),
                    metadata={"server_name": server_name}
                )
    
    async def _consultar_pedidos_vigentes(self, server: Dict) -> List[Dict]:
        """
        DEPRECATED: Usar _consultar_pedidos_con_estado en su lugar.
        
        Mantener temporalmente para compatibilidad, pero ya no se usa en run().
        """
        result = await self._consultar_pedidos_con_estado(server)
        if result.query_executed and result.status.is_success():
            return result.data
        return []
    
    # =========================================================================
    # ANTI-DUPLICADOS POR UNIDAD DE NEGOCIO
    # =========================================================================
    
    async def _ya_procesado(self, empresa_id: str, folio: str, origen: str) -> bool:
        """
        Verifica si el pedido ya fue procesado para esta empresa.
        
        FASE 4.1: Anti-duplicado por empresa_id (no server_id).
        """
        existe = await self.db[self.COLLECTION_PROCESADOS].find_one({
            "empresa_id": empresa_id,
            "pedido_folio": folio,
            "origen": origen
        })
        return existe is not None
    
    async def _marcar_procesado(
        self,
        empresa_id: str,
        folio: str,
        origen: str,
        automatizacion_id: str,
        estado: str,
        server_id: str = None,
        tarea_id: str = None
    ):
        """
        Marca pedido como procesado.
        
        FASE 4.1: Guarda empresa_id como clave principal.
        """
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db[self.COLLECTION_PROCESADOS].update_one(
            {
                "empresa_id": empresa_id,
                "pedido_folio": folio,
                "origen": origen
            },
            {
                "$set": {
                    "automatizacion_id": automatizacion_id,
                    "estado": estado,
                    "server_id": server_id,  # Solo para trazabilidad interna
                    "tarea_id": tarea_id,
                    "fecha_procesado": now,
                    "fecha_actualizacion": now
                },
                "$setOnInsert": {
                    "fecha_creacion": now
                }
            },
            upsert=True
        )
    
    # =========================================================================
    # FASE 4.1 y 4.2: PROCESAMIENTO DE PEDIDO NUEVO
    # =========================================================================
    
    async def _procesar_pedido_nuevo(
        self,
        empresa: Dict,
        server: Dict,
        pedido: Dict
    ) -> Optional[Dict]:
        """
        Procesa un pedido nuevo detectado.
        
        FASE 4.1: Crea registro base de auditoría
        FASE 4.2: Valida inventario y decide siguiente paso
        
        Returns:
            Dict con resultado: {auditoria_iniciada, tarea_creada, automatizacion_id}
        """
        empresa_id = empresa["id"]
        empresa_nombre = empresa.get("nombre", empresa_id)
        server_id = server["id"]
        
        folio = str(pedido.get("folio", pedido.get("Folio", "")))
        sucursal_id = str(pedido.get("sucursal_id", pedido.get("Sucursal_Id", "")))
        sucursal_nombre = pedido.get("sucursal", pedido.get("Sucursal", ""))
        almacen_id = str(pedido.get("almacen_id", pedido.get("Almacen_Id", "")))
        almacen_nombre = pedido.get("almacen", pedido.get("Almacen", ""))
        origen = pedido.get("origen", server.get("system_type", "MPRO"))
        
        automatizacion_id = str(uuid.uuid4())
        
        # Obtener detalle de productos
        productos = await self._obtener_detalle_pedido(server, folio)
        
        if not productos:
            # Sin productos - marcar como procesado sin tarea
            await self._marcar_procesado(
                empresa_id, folio, origen,
                automatizacion_id, "SIN_PRODUCTOS",
                server_id=server_id
            )
            await self._registrar_bitacora_job("PEDIDO_SIN_PRODUCTOS", {
                "empresa_id": empresa_id,
                "empresa_nombre": empresa_nombre,
                "folio": folio,
                "automatizacion_id": automatizacion_id
            })
            return {"estado": "SIN_PRODUCTOS", "automatizacion_id": automatizacion_id}
        
        # =====================================================
        # FASE 4.2: VALIDAR INVENTARIO
        # =====================================================
        tiene_inventario = await self._validar_inventario_disponible(
            server_id, almacen_id, productos
        )
        
        if not tiene_inventario:
            # =====================================================
            # FALTA INVENTARIO → CREAR TAREA OPERATIVA
            # =====================================================
            tarea_id = await self._crear_tarea_operativa(
                empresa_id=empresa_id,
                empresa_nombre=empresa_nombre,
                automatizacion_id=automatizacion_id,
                folio=folio,
                sucursal_id=sucursal_id,
                sucursal_nombre=sucursal_nombre,
                almacen_id=almacen_id,
                almacen_nombre=almacen_nombre,
                origen=origen,
                productos_count=len(productos)
            )
            
            await self._marcar_procesado(
                empresa_id, folio, origen,
                automatizacion_id, "PENDIENTE_INVENTARIO",
                server_id=server_id,
                tarea_id=tarea_id
            )
            
            await self._registrar_bitacora_job("TAREA_CREADA", {
                "empresa_id": empresa_id,
                "empresa_nombre": empresa_nombre,
                "folio": folio,
                "tarea_id": tarea_id,
                "automatizacion_id": automatizacion_id,
                "motivo": "Falta inventario físico"
            })
            
            return {
                "estado": "PENDIENTE_INVENTARIO",
                "tarea_creada": True,
                "tarea_id": tarea_id,
                "automatizacion_id": automatizacion_id
            }
        
        # =====================================================
        # HAY INVENTARIO → INICIAR AUDITORÍA
        # =====================================================
        resultado = await self._iniciar_auditoria(
            empresa=empresa,
            server=server,
            pedido=pedido,
            productos=productos,
            automatizacion_id=automatizacion_id
        )
        
        await self._marcar_procesado(
            empresa_id, folio, origen,
            automatizacion_id, resultado.get("estado", "EN_AUDITORIA"),
            server_id=server_id
        )
        
        await self._registrar_bitacora_job("AUDITORIA_INICIADA", {
            "empresa_id": empresa_id,
            "empresa_nombre": empresa_nombre,
            "folio": folio,
            "automatizacion_id": automatizacion_id,
            "estado": resultado.get("estado"),
            "recomendacion": resultado.get("recomendacion_general")
        })
        
        return {
            "estado": resultado.get("estado"),
            "auditoria_iniciada": True,
            "automatizacion_id": automatizacion_id,
            "recomendacion": resultado.get("recomendacion_general")
        }
    
    # =========================================================================
    # OBTENCIÓN DE DETALLE DE PEDIDO
    # =========================================================================
    
    async def _obtener_detalle_pedido(self, server: Dict, folio: str) -> List[Dict]:
        """Obtiene detalle de productos del pedido."""
        try:
            if server.get("system_type") == "MPRO":
                from modules.compras.repository import query_detalle_pedido_mpro
                detalle = query_detalle_pedido_mpro(server, folio)
                return [
                    {
                        "codigo": str(p.get("codigo", "")),
                        "nombre": p.get("nombre", p.get("producto", "")),
                        "existencia_fisica": float(p.get("existencia", 0) or 0),
                        "consumo_promedio": float(p.get("consumo_promedio", 0) or 0),
                        "cantidad_pedida": float(p.get("cantidad", 0) or 0),
                    }
                    for p in detalle
                ]
            return []
        except Exception as e:
            logger.warning(f"[PEDIDOS_DETECTOR] Error detalle pedido {folio}: {e}")
            return []
    
    # =========================================================================
    # FASE 4.2: VALIDACIÓN DE INVENTARIO
    # =========================================================================
    
    async def _validar_inventario_disponible(
        self,
        server_id: str,
        almacen_id: str,
        productos: List[Dict]
    ) -> bool:
        """
        Valida si existe inventario físico reciente para el almacén.
        
        FASE 4.2: Determina si podemos proceder con auditoría o necesitamos tarea.
        
        Returns:
            True si hay inventario disponible, False si falta
        """
        from datetime import timedelta
        
        # Buscar inventario físico de los últimos 15 días
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=15)
        
        inventario = await self.db.inventarios_fisicos_procesados.find_one(
            {
                "server_id": server_id,
                "almacen_id": almacen_id,
                "fecha": {"$gte": fecha_limite.isoformat()}
            },
            {"_id": 0, "folio": 1, "fecha": 1}
        )
        
        return inventario is not None
    
    # =========================================================================
    # FASE 4.2: CREACIÓN DE TAREA OPERATIVA
    # =========================================================================
    
    async def _crear_tarea_operativa(
        self,
        empresa_id: str,
        empresa_nombre: str,
        automatizacion_id: str,
        folio: str,
        sucursal_id: str,
        sucursal_nombre: str,
        almacen_id: str,
        almacen_nombre: str,
        origen: str,
        productos_count: int
    ) -> str:
        """
        Crea una tarea operativa cuando falta inventario.
        
        FASE 4.2: Estado PENDIENTE_INVENTARIO hasta que se capture inventario.
        
        Returns:
            ID de la tarea creada
        """
        tarea_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        tarea = {
            "id": tarea_id,
            "tipo": "CAPTURA_INVENTARIO",
            "estado": "PENDIENTE",
            "prioridad": "ALTA",
            # Contexto de negocio (Unidad de Negocio)
            "empresa_id": empresa_id,
            "empresa_nombre": empresa_nombre,
            # Detalle operativo
            "automatizacion_id": automatizacion_id,
            "pedido_folio": folio,
            "sucursal_id": sucursal_id,
            "sucursal_nombre": sucursal_nombre,
            "almacen_id": almacen_id,
            "almacen_nombre": almacen_nombre,
            "origen_sistema": origen,
            "productos_count": productos_count,
            # Descripción para operador
            "titulo": f"Capturar inventario físico - {almacen_nombre}",
            "descripcion": (
                f"Se requiere capturar el inventario físico del almacén {almacen_nombre} "
                f"para continuar con la auditoría del pedido {folio}. "
                f"Unidad de Negocio: {empresa_nombre}."
            ),
            "instrucciones": [
                "1. Realizar conteo físico del inventario del almacén",
                "2. Registrar el inventario en el sistema ERP",
                f"3. Una vez capturado, el pedido {folio} continuará automáticamente"
            ],
            # Timestamps
            "fecha_creacion": now.isoformat(),
            "fecha_actualizacion": now.isoformat(),
            "creado_por": "SISTEMA_AUTOMATICO",
            # Asignación (pendiente)
            "asignado_a": None,
            "fecha_asignacion": None,
            "fecha_vencimiento": None,
            "fecha_completado": None,
            "completado_por": None,
            "notas": []
        }
        
        await self.db[self.COLLECTION_TAREAS].insert_one(tarea)
        
        # Notificar (si está configurado)
        await self._notificar_tarea_creada(tarea)
        
        return tarea_id
    
    async def _notificar_tarea_creada(self, tarea: Dict):
        """Notifica la creación de tarea (opcional)."""
        try:
            # Por ahora solo log, puede extenderse a email/websocket
            logger.info(
                f"[PEDIDOS_DETECTOR] Tarea creada: {tarea['id']} - "
                f"{tarea['titulo']} ({tarea['empresa_nombre']})"
            )
        except Exception as e:
            logger.warning(f"Error notificando tarea: {e}")
    
    # =========================================================================
    # FASE 4.2: INICIAR AUDITORÍA
    # =========================================================================
    
    async def _iniciar_auditoria(
        self,
        empresa: Dict,
        server: Dict,
        pedido: Dict,
        productos: List[Dict],
        automatizacion_id: str
    ) -> Dict:
        """
        Inicia auditoría cuando hay inventario disponible.
        
        FASE 4.2: Ejecuta el servicio de automatización de compras.
        """
        from modules.fase2_operativo.db_utils import get_database
        from modules.fase2_operativo.services.automatizacion_compras_service import (
            get_automatizacion_compras_service
        )
        
        db_sync = get_database()
        service = get_automatizacion_compras_service(db_sync)
        
        folio = str(pedido.get("folio", pedido.get("Folio", "")))
        sucursal_id = str(pedido.get("sucursal_id", pedido.get("Sucursal_Id", "")))
        sucursal_nombre = pedido.get("sucursal", pedido.get("Sucursal", ""))
        almacen_id = str(pedido.get("almacen_id", pedido.get("Almacen_Id", "")))
        almacen_nombre = pedido.get("almacen", pedido.get("Almacen", ""))
        origen = pedido.get("origen", server.get("system_type", "MPRO"))
        
        # Llamar al servicio de automatización con contexto de empresa
        resultado = service.procesar_pedido_operativo(
            pedido_id=folio,
            server_id=server["id"],  # Solo para uso interno
            sucursal_id=sucursal_id,
            sucursal_nombre=sucursal_nombre,
            almacen_id=almacen_id,
            almacen_nombre=almacen_nombre,
            usuario_id="SISTEMA_AUTOMATICO",
            usuario_nombre="Detección Automática",
            productos=productos,
            dias_objetivo=None,
            origen_sistema=origen,
            empresa_id=empresa.get("id"),
            empresa_nombre=empresa.get("nombre")
        )
        
        return resultado
    
    # =========================================================================
    # BITÁCORA DE EVENTOS
    # =========================================================================
    
    async def _registrar_bitacora_job(self, evento: str, datos: Dict):
        """
        Registra evento en bitácora del job.
        
        FASE 4.1: Evidencia clara de cada acción del detector.
        """
        await self.db[self.COLLECTION_BITACORA].insert_one({
            "id": str(uuid.uuid4()),
            "job": "pedidos_detector",
            "evento": evento,
            "datos": datos,
            "fecha": datetime.now(timezone.utc).isoformat()
        })


def create_pedidos_detector_job(db, config: Optional[dict] = None) -> PedidosDetectorJob:
    """Factory para crear el job de detección de pedidos."""
    return PedidosDetectorJob(db, config)


# =========================================================================
# FUNCIÓN PARA EJECUCIÓN MANUAL
# =========================================================================

async def ejecutar_detector_manual(
    db,
    empresa_id: str = None
) -> Dict:
    """
    Ejecuta el detector de pedidos manualmente.
    
    Útil para pruebas y validación de la Fase 4.1 y 4.2.
    
    Args:
        db: Conexión a MongoDB (async)
        empresa_id: Filtrar por empresa específica (opcional)
    
    Returns:
        Estadísticas de la ejecución
    """
    job = create_pedidos_detector_job(db)
    return await job.run(manual=True, empresa_id_filter=empresa_id)
