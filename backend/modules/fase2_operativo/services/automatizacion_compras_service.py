"""
EDARSA HUB - Automatización Operativa de Compras
================================================
FASE 1: Detección y auditoría automática de pedidos.

Flujo:
1. Pedido capturado → validar inventario físico
2. Sin inventario → PENDIENTE_INVENTARIO_FISICO + notificar
3. Con inventario → ejecutar auditoría operativa
4. Generar clasificación y recomendación
5. Enviar a revisión (Gerente/Tesorería)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class EstadoAutomatizacion(str, Enum):
    """Estados del flujo de automatización operativa."""
    PENDIENTE_INVENTARIO_FISICO = "PENDIENTE_INVENTARIO_FISICO"
    AUDITORIA_EN_PROCESO = "AUDITORIA_EN_PROCESO"
    AUDITADO_PENDIENTE_REVISION = "AUDITADO_PENDIENTE_REVISION"
    EN_REVISION_GERENCIA = "EN_REVISION_GERENCIA"
    EN_REVISION_TESORERIA = "EN_REVISION_TESORERIA"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    ERROR = "ERROR"


class EstadoProducto(str, Enum):
    """Estado de inventario por producto."""
    CRITICO = "CRITICO"      # dias_inv <= 0
    FALTANTE = "FALTANTE"    # dias_inv < objetivo
    OPTIMO = "OPTIMO"        # dias_inv ≈ objetivo (±20%)
    SOBRANTE = "SOBRANTE"    # dias_inv > objetivo


class Recomendacion(str, Enum):
    """Recomendación de compra."""
    URGENTE = "URGENTE"       # Estado CRITICO
    COMPRAR = "COMPRAR"       # Estado FALTANTE
    NO_COMPRAR = "NO_COMPRAR" # Estado OPTIMO
    REVISAR = "REVISAR"       # Estado SOBRANTE


class AutomatizacionComprasService:
    """Servicio de automatización operativa de compras."""
    
    COLLECTION = "automatizaciones_operativas_compras"
    DIAS_INVENTARIO_FISICO_VALIDO = 7  # Inventario físico válido si tiene menos de 7 días
    DIAS_OBJETIVO_DEFAULT = 10
    TOLERANCIA_OPTIMO = 0.20  # ±20% del objetivo se considera óptimo
    
    def __init__(self, db):
        self.db = db
        self.collection = db[self.COLLECTION]
    
    async def procesar_pedido_operativo(
        self,
        pedido_id: str,
        server_id: str,
        sucursal_id: str,
        sucursal_nombre: str,
        almacen_id: str,
        almacen_nombre: str,
        usuario_id: str,
        usuario_nombre: str,
        productos: List[Dict],
        dias_objetivo: int = None
    ) -> Dict:
        """
        Procesa un pedido/requisición capturado.
        
        Flujo:
        1. Validar inventario físico reciente
        2. Si no hay → marcar pendiente y notificar
        3. Si hay → ejecutar auditoría y clasificar
        """
        now = datetime.now(timezone.utc)
        dias_objetivo = dias_objetivo or self.DIAS_OBJETIVO_DEFAULT
        
        # Crear registro base
        automatizacion_id = str(uuid.uuid4())
        registro = {
            "id": automatizacion_id,
            "pedido_id": pedido_id,
            "server_id": server_id,
            "sucursal_id": sucursal_id,
            "sucursal_nombre": sucursal_nombre,
            "almacen_id": almacen_id,
            "almacen_nombre": almacen_nombre,
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre,
            "estado": None,
            "inventario_fisico_id": None,
            "inventario_fisico_fecha": None,
            "fecha_creacion": now.isoformat(),
            "fecha_actualizacion": now.isoformat(),
            "resultado": None,
            "detalle_productos": [],
            "recomendacion_general": None,
            "total_productos": len(productos),
            "dias_objetivo": dias_objetivo,
        }
        
        # 1. Validar inventario físico reciente
        inventario = await self._buscar_inventario_fisico_reciente(
            server_id, sucursal_id, almacen_id
        )
        
        if not inventario:
            # Sin inventario físico válido
            registro["estado"] = EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value
            registro["resultado"] = {
                "mensaje": "No existe inventario físico reciente",
                "dias_requeridos": self.DIAS_INVENTARIO_FISICO_VALIDO,
                "accion_requerida": "Realizar conteo físico de inventario"
            }
            
            # Guardar y notificar
            self.collection.insert_one(registro)
            await self._notificar_falta_inventario(registro)
            
            logger.info(f"Automatización {automatizacion_id}: PENDIENTE_INVENTARIO_FISICO")
            return self._limpiar_respuesta(registro)
        
        # 2. Hay inventario físico - ejecutar auditoría
        registro["inventario_fisico_id"] = inventario.get("folio")
        registro["inventario_fisico_fecha"] = inventario.get("fecha")
        registro["estado"] = EstadoAutomatizacion.AUDITORIA_EN_PROCESO.value
        
        # 3. Ejecutar cálculo por producto
        detalle_productos = []
        resumen = {
            "criticos": 0,
            "faltantes": 0,
            "optimos": 0,
            "sobrantes": 0,
            "total_pedido_optimo": 0
        }
        
        for prod in productos:
            resultado_prod = self._calcular_estado_producto(
                producto=prod,
                dias_objetivo=dias_objetivo
            )
            detalle_productos.append(resultado_prod)
            
            # Actualizar resumen
            estado = resultado_prod["estado"]
            if estado == EstadoProducto.CRITICO.value:
                resumen["criticos"] += 1
            elif estado == EstadoProducto.FALTANTE.value:
                resumen["faltantes"] += 1
            elif estado == EstadoProducto.OPTIMO.value:
                resumen["optimos"] += 1
            else:
                resumen["sobrantes"] += 1
            
            resumen["total_pedido_optimo"] += resultado_prod.get("pedido_optimo", 0)
        
        registro["detalle_productos"] = detalle_productos
        registro["resultado"] = resumen
        
        # 4. Determinar recomendación general
        if resumen["criticos"] > 0:
            registro["recomendacion_general"] = Recomendacion.URGENTE.value
        elif resumen["faltantes"] > 0:
            registro["recomendacion_general"] = Recomendacion.COMPRAR.value
        elif resumen["sobrantes"] > len(productos) * 0.5:
            registro["recomendacion_general"] = Recomendacion.REVISAR.value
        else:
            registro["recomendacion_general"] = Recomendacion.NO_COMPRAR.value
        
        # 5. Actualizar estado a pendiente revisión
        registro["estado"] = EstadoAutomatizacion.AUDITADO_PENDIENTE_REVISION.value
        registro["fecha_actualizacion"] = datetime.now(timezone.utc).isoformat()
        
        # Guardar
        self.collection.insert_one(registro)
        
        # Notificar para revisión
        await self._notificar_listo_revision(registro)
        
        logger.info(f"Automatización {automatizacion_id}: AUDITADO - Recomendación: {registro['recomendacion_general']}")
        return self._limpiar_respuesta(registro)
    
    def _calcular_estado_producto(
        self,
        producto: Dict,
        dias_objetivo: int
    ) -> Dict:
        """
        Calcula estado y recomendación para un producto.
        
        Fórmula:
        dias_inventario = existencia_fisica / consumo_promedio
        pedido_optimo = (dias_objetivo * consumo_promedio) - existencia_fisica
        """
        existencia = float(producto.get("existencia_fisica", 0) or 0)
        consumo = float(producto.get("consumo_promedio", 0) or 0)
        cantidad_pedida = float(producto.get("cantidad_pedida", 0) or 0)
        
        # Calcular días de inventario
        if consumo > 0:
            dias_inventario = existencia / consumo
        else:
            dias_inventario = 999 if existencia > 0 else 0
        
        # Determinar estado
        if dias_inventario <= 0:
            estado = EstadoProducto.CRITICO.value
            recomendacion = Recomendacion.URGENTE.value
        elif dias_inventario < dias_objetivo * (1 - self.TOLERANCIA_OPTIMO):
            estado = EstadoProducto.FALTANTE.value
            recomendacion = Recomendacion.COMPRAR.value
        elif dias_inventario <= dias_objetivo * (1 + self.TOLERANCIA_OPTIMO):
            estado = EstadoProducto.OPTIMO.value
            recomendacion = Recomendacion.NO_COMPRAR.value
        else:
            estado = EstadoProducto.SOBRANTE.value
            recomendacion = Recomendacion.REVISAR.value
        
        # Calcular pedido óptimo
        pedido_optimo = (dias_objetivo * consumo) - existencia
        if pedido_optimo < 0:
            pedido_optimo = 0
        
        # Diferencia vs pedido capturado
        diferencia = cantidad_pedida - pedido_optimo
        
        return {
            "codigo": producto.get("codigo"),
            "nombre": producto.get("nombre"),
            "existencia_fisica": existencia,
            "consumo_promedio": round(consumo, 2),
            "dias_inventario": round(dias_inventario, 1),
            "dias_objetivo": dias_objetivo,
            "estado": estado,
            "recomendacion": recomendacion,
            "cantidad_pedida": cantidad_pedida,
            "pedido_optimo": round(pedido_optimo, 2),
            "diferencia": round(diferencia, 2),
        }
    
    async def _buscar_inventario_fisico_reciente(
        self,
        server_id: str,
        sucursal_id: str,
        almacen_id: str
    ) -> Optional[Dict]:
        """Busca inventario físico de los últimos N días."""
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=self.DIAS_INVENTARIO_FISICO_VALIDO)
        
        # Buscar en colección de inventarios físicos procesados
        inventario = self.db.inventarios_fisicos_procesados.find_one(
            {
                "server_id": server_id,
                "sucursal_id": sucursal_id,
                "almacen_id": almacen_id,
                "fecha": {"$gte": fecha_limite.isoformat()}
            },
            {"_id": 0},
            sort=[("fecha", -1)]
        )
        
        if inventario:
            return inventario
        
        # Si no hay registro local, simular que hay uno para demo
        # En producción, esto consultaría la API de MPRO
        return None
    
    async def _notificar_falta_inventario(self, registro: Dict):
        """Notifica al usuario que falta inventario físico."""
        try:
            from modules.fase2_operativo.services.email_service import get_email_service
            
            service = get_email_service()
            if not service.is_configured():
                logger.debug("Email service no configurado, omitiendo notificación")
                return
            
            await service.enviar_email(
                destinatario=self._obtener_email_usuario(registro["usuario_id"]),
                asunto=f"⚠️ Automatización Compras - Inventario Físico Requerido",
                contenido_html=f"""
                <h2>Acción Requerida: Inventario Físico</h2>
                <p>El pedido <strong>{registro['pedido_id']}</strong> no puede ser auditado automáticamente.</p>
                <p><strong>Motivo:</strong> No existe inventario físico de los últimos {self.DIAS_INVENTARIO_FISICO_VALIDO} días.</p>
                <p><strong>Sucursal:</strong> {registro['sucursal_nombre']}</p>
                <p><strong>Almacén:</strong> {registro['almacen_nombre']}</p>
                <p>Por favor, realice un conteo físico de inventario para continuar con el proceso.</p>
                """
            )
        except Exception as e:
            logger.error(f"Error enviando notificación falta inventario: {e}")
    
    async def _notificar_listo_revision(self, registro: Dict):
        """Notifica que la auditoría está lista para revisión."""
        try:
            from modules.fase2_operativo.services.email_service import get_email_service
            
            service = get_email_service()
            if not service.is_configured():
                logger.debug("Email service no configurado, omitiendo notificación")
                return
            
            recomendacion = registro.get("recomendacion_general", "")
            resultado = registro.get("resultado", {})
            
            # Enviar a Gerencia si hay críticos o urgentes
            if resultado.get("criticos", 0) > 0 or recomendacion == Recomendacion.URGENTE.value:
                # Buscar gerentes
                gerentes = list(self.db.users.find(
                    {"role": {"$in": ["Gerente", "Director", "Administrador"]}},
                    {"_id": 0, "email": 1, "name": 1}
                ))
                
                for gerente in gerentes[:3]:  # Max 3
                    if gerente.get("email"):
                        await service.enviar_email(
                            destinatario=gerente["email"],
                            asunto=f"🔔 Auditoría Compras Lista - {registro['sucursal_nombre']}",
                            contenido_html=self._generar_html_revision(registro)
                        )
        except Exception as e:
            logger.error(f"Error enviando notificación revisión: {e}")
    
    def _generar_html_revision(self, registro: Dict) -> str:
        """Genera HTML para email de revisión."""
        resultado = registro.get("resultado", {})
        return f"""
        <h2>Auditoría Operativa de Compras</h2>
        <p><strong>Sucursal:</strong> {registro['sucursal_nombre']}</p>
        <p><strong>Pedido:</strong> {registro['pedido_id']}</p>
        <p><strong>Recomendación:</strong> <span style="color: {'red' if registro['recomendacion_general'] == 'URGENTE' else 'orange'}">{registro['recomendacion_general']}</span></p>
        
        <h3>Resumen</h3>
        <ul>
            <li>Críticos: {resultado.get('criticos', 0)}</li>
            <li>Faltantes: {resultado.get('faltantes', 0)}</li>
            <li>Óptimos: {resultado.get('optimos', 0)}</li>
            <li>Sobrantes: {resultado.get('sobrantes', 0)}</li>
        </ul>
        
        <p>Ingrese al sistema para revisar el detalle completo.</p>
        """
    
    def _obtener_email_usuario(self, usuario_id: str) -> str:
        """Obtiene email del usuario."""
        user = self.db.users.find_one({"id": usuario_id}, {"_id": 0, "email": 1})
        return user.get("email", "") if user else ""
    
    def _limpiar_respuesta(self, registro: Dict) -> Dict:
        """Limpia el registro para respuesta (sin _id de MongoDB)."""
        if "_id" in registro:
            del registro["_id"]
        return registro
    
    # =========================================================================
    # CONSULTAS
    # =========================================================================
    
    def listar_automatizaciones(
        self,
        server_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        estado: Optional[str] = None,
        limite: int = 50
    ) -> List[Dict]:
        """Lista automatizaciones operativas."""
        filtro = {}
        if server_id:
            filtro["server_id"] = server_id
        if sucursal_id:
            filtro["sucursal_id"] = sucursal_id
        if estado:
            filtro["estado"] = estado
        
        cursor = self.collection.find(
            filtro,
            {"_id": 0}
        ).sort("fecha_creacion", -1).limit(limite)
        
        return list(cursor)
    
    def obtener_automatizacion(self, automatizacion_id: str) -> Optional[Dict]:
        """Obtiene una automatización por ID."""
        registro = self.collection.find_one(
            {"id": automatizacion_id},
            {"_id": 0}
        )
        return registro
    
    def obtener_kpis(self, server_id: Optional[str] = None) -> Dict:
        """Obtiene KPIs de automatizaciones operativas."""
        filtro = {}
        if server_id:
            filtro["server_id"] = server_id
        
        # Contar por estado
        pipeline = [
            {"$match": filtro},
            {"$group": {"_id": "$estado", "count": {"$sum": 1}}},
        ]
        
        resultados = list(self.collection.aggregate(pipeline))
        
        kpis = {
            "total": 0,
            "pendientes_inventario": 0,
            "en_proceso": 0,
            "pendientes_revision": 0,
            "aprobados": 0,
            "rechazados": 0,
        }
        
        for r in resultados:
            estado = r["_id"]
            count = r["count"]
            kpis["total"] += count
            
            if estado == EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value:
                kpis["pendientes_inventario"] = count
            elif estado == EstadoAutomatizacion.AUDITORIA_EN_PROCESO.value:
                kpis["en_proceso"] = count
            elif estado in [
                EstadoAutomatizacion.AUDITADO_PENDIENTE_REVISION.value,
                EstadoAutomatizacion.EN_REVISION_GERENCIA.value,
                EstadoAutomatizacion.EN_REVISION_TESORERIA.value
            ]:
                kpis["pendientes_revision"] += count
            elif estado == EstadoAutomatizacion.APROBADO.value:
                kpis["aprobados"] = count
            elif estado == EstadoAutomatizacion.RECHAZADO.value:
                kpis["rechazados"] = count
        
        return kpis
    
    # =========================================================================
    # ACCIONES DE REVISIÓN
    # =========================================================================
    
    async def enviar_a_revision(
        self,
        automatizacion_id: str,
        tipo_revision: str,  # "gerencia" o "tesoreria"
        usuario_id: str
    ) -> Dict:
        """Envía automatización a revisión."""
        estado_nuevo = (
            EstadoAutomatizacion.EN_REVISION_GERENCIA.value
            if tipo_revision == "gerencia"
            else EstadoAutomatizacion.EN_REVISION_TESORERIA.value
        )
        
        result = self.collection.update_one(
            {"id": automatizacion_id},
            {
                "$set": {
                    "estado": estado_nuevo,
                    "fecha_actualizacion": datetime.now(timezone.utc).isoformat(),
                    "enviado_revision_por": usuario_id,
                    "tipo_revision": tipo_revision,
                }
            }
        )
        
        if result.modified_count == 0:
            return {"success": False, "error": "No encontrado"}
        
        return {"success": True, "estado": estado_nuevo}
    
    async def aprobar(
        self,
        automatizacion_id: str,
        usuario_id: str,
        comentario: str = ""
    ) -> Dict:
        """Aprueba una automatización."""
        result = self.collection.update_one(
            {"id": automatizacion_id},
            {
                "$set": {
                    "estado": EstadoAutomatizacion.APROBADO.value,
                    "fecha_actualizacion": datetime.now(timezone.utc).isoformat(),
                    "aprobado_por": usuario_id,
                    "fecha_aprobacion": datetime.now(timezone.utc).isoformat(),
                    "comentario_aprobacion": comentario,
                }
            }
        )
        
        if result.modified_count == 0:
            return {"success": False, "error": "No encontrado"}
        
        return {"success": True, "estado": EstadoAutomatizacion.APROBADO.value}
    
    async def rechazar(
        self,
        automatizacion_id: str,
        usuario_id: str,
        motivo: str
    ) -> Dict:
        """Rechaza una automatización."""
        result = self.collection.update_one(
            {"id": automatizacion_id},
            {
                "$set": {
                    "estado": EstadoAutomatizacion.RECHAZADO.value,
                    "fecha_actualizacion": datetime.now(timezone.utc).isoformat(),
                    "rechazado_por": usuario_id,
                    "fecha_rechazo": datetime.now(timezone.utc).isoformat(),
                    "motivo_rechazo": motivo,
                }
            }
        )
        
        if result.modified_count == 0:
            return {"success": False, "error": "No encontrado"}
        
        return {"success": True, "estado": EstadoAutomatizacion.RECHAZADO.value}


def get_automatizacion_compras_service(db) -> AutomatizacionComprasService:
    """Factory function."""
    return AutomatizacionComprasService(db)
