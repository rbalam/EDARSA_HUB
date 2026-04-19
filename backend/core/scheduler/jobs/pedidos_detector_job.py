"""
EDARSA HUB - Job de Detección de Pedidos para Automatización Operativa
======================================================================
Job del scheduler para detectar pedidos nuevos en MPro/Soft y disparar
la automatización operativa de compras.

Flujo:
1. Consultar pedidos vigentes de cada servidor activo
2. Comparar contra pedidos ya procesados (EDARSA HUB)
3. Disparar procesar_pedido_operativo() para nuevos
4. Registrar marca de procesamiento (evita duplicados)
5. Registrar bitácora
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

from ..job_logger import get_job_logger

logger = logging.getLogger(__name__)


class PedidosDetectorJob:
    """
    Job para detectar pedidos nuevos y disparar automatización.
    
    Control anti-duplicado:
    - Tabla `pedidos_procesados_automatizacion` en EDARSA HUB
    - Índice único por (server_id, pedido_folio, origen)
    """
    
    COLLECTION_PROCESADOS = "pedidos_procesados_automatizacion"
    
    def __init__(self, db, config: Optional[dict] = None):
        self.db = db
        self.config = config or {}
        self.job_logger = get_job_logger(db)
    
    async def run(self):
        """
        Ejecuta detección de pedidos nuevos.
        """
        # Iniciar log de ejecución
        log_entry = await self.job_logger.start_execution(
            job_name="pedidos_detector",
            metadata={"type": "automatic"}
        )
        
        detectados = 0
        disparados = 0
        fallidos = 0
        ya_procesados = 0
        
        try:
            # Obtener servidores activos
            servidores = await self._obtener_servidores_activos()
            logger.info(f"[PEDIDOS_DETECTOR] Servidores activos: {len(servidores)}")
            
            for server in servidores:
                server_id = server["id"]
                server_name = server.get("name", server_id)
                
                try:
                    # Consultar pedidos vigentes
                    pedidos = await self._consultar_pedidos_vigentes(server)
                    
                    if not pedidos:
                        continue
                    
                    logger.info(f"[PEDIDOS_DETECTOR] {server_name}: {len(pedidos)} pedidos vigentes")
                    
                    for pedido in pedidos:
                        detectados += 1
                        folio = str(pedido.get("folio", pedido.get("Folio", "")))
                        origen = pedido.get("origen", server.get("system_type", "MPRO"))
                        
                        # Verificar si ya fue procesado
                        if await self._ya_procesado(server_id, folio, origen):
                            ya_procesados += 1
                            continue
                        
                        # Disparar automatización
                        try:
                            resultado = await self._disparar_automatizacion(server, pedido)
                            
                            if resultado and resultado.get("estado"):
                                disparados += 1
                                logger.info(
                                    f"[PEDIDOS_DETECTOR] Disparado: {folio} -> {resultado['estado']}"
                                )
                            else:
                                fallidos += 1
                                logger.warning(
                                    f"[PEDIDOS_DETECTOR] Fallo disparar: {folio} - {resultado.get('error') if resultado else 'Sin resultado'}"
                                )
                        except Exception as e:
                            fallidos += 1
                            logger.error(f"[PEDIDOS_DETECTOR] Error disparando {folio}: {e}")
                
                except Exception as e:
                    logger.error(f"[PEDIDOS_DETECTOR] Error servidor {server_name}: {e}")
            
            # Finalizar log
            await self.job_logger.finish_execution(
                log_entry,
                status="success" if fallidos == 0 else "partial",
                processed_count=detectados,
                success_count=disparados,
                failed_count=fallidos,
                message=f"Detectados: {detectados}, Nuevos: {disparados}, Ya procesados: {ya_procesados}, Fallidos: {fallidos}"
            )
            
            logger.info(
                f"[PEDIDOS_DETECTOR] Completado: {detectados} detectados, "
                f"{disparados} nuevos, {ya_procesados} ya procesados, {fallidos} fallidos"
            )
            
        except Exception as e:
            await self.job_logger.finish_execution(
                log_entry,
                status="failed",
                processed_count=detectados,
                success_count=disparados,
                failed_count=fallidos,
                error_detail=str(e),
                message=f"Error: {str(e)}"
            )
            
            logger.error(f"[PEDIDOS_DETECTOR] Error general: {e}")
            raise
    
    async def _obtener_servidores_activos(self) -> List[Dict]:
        """Obtiene servidores activos que pueden tener pedidos."""
        cursor = self.db.servers.find(
            {
                "active": True,
                "system_type": {"$in": ["MPRO", "SoftRestaurant"]}
            },
            {"_id": 0}
        )
        return await cursor.to_list(100)
    
    async def _consultar_pedidos_vigentes(self, server: Dict) -> List[Dict]:
        """Consulta pedidos vigentes de un servidor."""
        try:
            from modules.compras.service import obtener_pedidos_vigentes
            return await obtener_pedidos_vigentes(server["id"])
        except Exception as e:
            logger.warning(f"[PEDIDOS_DETECTOR] Error consultando pedidos {server['id']}: {e}")
            return []
    
    async def _ya_procesado(self, server_id: str, folio: str, origen: str) -> bool:
        """Verifica si el pedido ya fue procesado."""
        existe = await self.db[self.COLLECTION_PROCESADOS].find_one({
            "server_id": server_id,
            "pedido_folio": folio,
            "origen": origen
        })
        return existe is not None
    
    async def _disparar_automatizacion(self, server: Dict, pedido: Dict) -> Dict:
        """Dispara la automatización operativa para un pedido (sync)."""
        # El servicio de automatización usa PyMongo sync
        from modules.fase2_operativo.db_utils import get_database
        from modules.fase2_operativo.services.automatizacion_compras_service import (
            get_automatizacion_compras_service
        )
        
        db_sync = get_database()
        service = get_automatizacion_compras_service(db_sync)
        
        # Construir parámetros
        folio = str(pedido.get("folio", pedido.get("Folio", "")))
        sucursal_id = str(pedido.get("sucursal_id", pedido.get("Sucursal_Id", "")))
        sucursal_nombre = pedido.get("sucursal", pedido.get("Sucursal", ""))
        almacen_id = str(pedido.get("almacen_id", pedido.get("Almacen_Id", "")))
        almacen_nombre = pedido.get("almacen", pedido.get("Almacen", ""))
        origen = pedido.get("origen", server.get("system_type", "MPRO"))
        
        # Obtener detalle de productos del pedido
        productos = await self._obtener_detalle_pedido(server, folio)
        
        if not productos:
            # Sin productos, marcar como procesado para no reintentar
            await self._marcar_procesado(
                server["id"], folio, origen, 
                None, "SIN_PRODUCTOS"
            )
            return {"estado": None, "error": "Pedido sin productos"}
        
        # Disparar procesamiento (sync)
        resultado = service.procesar_pedido_operativo(
            pedido_id=folio,
            server_id=server["id"],
            sucursal_id=sucursal_id,
            sucursal_nombre=sucursal_nombre,
            almacen_id=almacen_id,
            almacen_nombre=almacen_nombre,
            usuario_id="SISTEMA_AUTOMATICO",
            usuario_nombre="Detección Automática",
            productos=productos,
            dias_objetivo=None,  # Usa default
            origen_sistema=origen
        )
        
        return resultado
    
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
    
    async def _marcar_procesado(
        self,
        server_id: str,
        folio: str,
        origen: str,
        automatizacion_id: Optional[str],
        estado: str
    ):
        """Marca pedido como procesado."""
        await self.db[self.COLLECTION_PROCESADOS].update_one(
            {"server_id": server_id, "pedido_folio": folio, "origen": origen},
            {
                "$set": {
                    "automatizacion_id": automatizacion_id,
                    "estado": estado,
                    "fecha_procesado": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )


def create_pedidos_detector_job(db, config: Optional[dict] = None) -> PedidosDetectorJob:
    """Factory para crear el job de detección de pedidos."""
    return PedidosDetectorJob(db, config)
