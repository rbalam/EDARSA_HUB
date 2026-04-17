"""
Servicio de SLA - Monitoreo de Tiempos y Cumplimiento
CAB-003 | EDARSA HUB - Fase 2B.4 + Subfase 2B.5 Notificaciones WhatsApp

Gestiona el cálculo de métricas SLA para tareas operativas.
Integrado con sistema de notificaciones para alertas automáticas.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EstadoSLA(str, Enum):
    """Estados de SLA para tareas."""
    EN_TIEMPO = "EN_TIEMPO"
    ADVERTENCIA = "ADVERTENCIA"  # 50-74% consumido (Warning)
    URGENTE = "URGENTE"  # 75-99% consumido (Por vencer - 80%)
    VENCIDA = "VENCIDA"  # 100%+ consumido
    ESCALADA = "ESCALADA"  # 150%+ consumido - Subfase 2B.5
    CUMPLIDA_EN_TIEMPO = "CUMPLIDA_EN_TIEMPO"
    CUMPLIDA_FUERA_DE_TIEMPO = "CUMPLIDA_FUERA_DE_TIEMPO"


# Umbrales SLA por defecto (en horas y porcentajes)
UMBRALES_SLA_DEFAULT = {
    "SLA_JUSTIFICACION_SIMPLE_HORAS": 24,
    "SLA_JUSTIFICACION_COMPLETA_HORAS": 48,
    "SLA_REVISION_OPERATIVO_HORAS": 24,
    "SLA_AUDITORIA_HORAS": 72,
    "SLA_UMBRAL_ADVERTENCIA_PORCENTAJE": 50,  # Warning inicial
    "SLA_UMBRAL_URGENTE_PORCENTAJE": 80,  # Por vencer - disparar notificación
    "SLA_UMBRAL_VENCIDO_PORCENTAJE": 100,  # Vencido
    "SLA_UMBRAL_ESCALAMIENTO_PORCENTAJE": 150,  # Escalar a supervisor/gerente
}

# Estados que indican primera acción
ESTADOS_PRIMERA_ACCION = ["EN_PROGRESO", "COMPLETADA"]

# Estados que indican tarea completada
ESTADOS_COMPLETADA = ["COMPLETADA"]

# Estados activos (no finales)
ESTADOS_ACTIVOS = ["PENDIENTE", "EN_PROGRESO"]


class SLAService:
    """
    Servicio para gestión de SLA de tareas operativas.
    
    Calcula métricas de tiempo de respuesta, resolución y cumplimiento.
    Integrado con sistema de notificaciones WhatsApp (Subfase 2B.5).
    """
    
    def __init__(self, db):
        """
        Inicializa el servicio.
        
        Args:
            db: Conexión a la base de datos
        """
        self.db = db
        self._cache_config = None
        self._notification_service = None
    
    def _get_notification_service(self):
        """
        Obtiene el servicio de notificaciones de forma lazy.
        Evita imports circulares y permite operación sin notificaciones.
        """
        if self._notification_service is None:
            try:
                from core.communications.notifications.service import get_notification_orchestrator
                self._notification_service = get_notification_orchestrator(self.db)
            except ImportError:
                logger.warning("Sistema de notificaciones no disponible")
                self._notification_service = None
        return self._notification_service
    
    def _get_configuracion(self) -> Dict[str, Any]:
        """
        Obtiene la configuración SLA desde la BD.
        Usa cache para evitar consultas repetidas.
        """
        if self._cache_config is not None:
            return self._cache_config
        
        config = {}
        
        # Cargar desde configuracion_operativo
        for item in self.db.configuracion_operativo.find({"clave": {"$regex": "^SLA_"}}):
            clave = item.get("clave")
            valor = item.get("valor")
            try:
                config[clave] = int(valor) if valor else UMBRALES_SLA_DEFAULT.get(clave, 24)
            except (ValueError, TypeError):
                config[clave] = UMBRALES_SLA_DEFAULT.get(clave, 24)
        
        # Completar con defaults
        for clave, valor_default in UMBRALES_SLA_DEFAULT.items():
            if clave not in config:
                config[clave] = valor_default
        
        self._cache_config = config
        return config
    
    def invalidar_cache_config(self):
        """Invalida el cache de configuración."""
        self._cache_config = None
    
    def obtener_configuracion(self) -> Dict[str, Any]:
        """
        Obtiene la configuración SLA actual.
        
        Returns:
            Dict con umbrales y porcentajes
        """
        config = self._get_configuracion()
        return {
            "umbrales_horas": {
                "justificacion_simple": config.get("SLA_JUSTIFICACION_SIMPLE_HORAS", 24),
                "justificacion_completa": config.get("SLA_JUSTIFICACION_COMPLETA_HORAS", 48),
                "revision_operativo": config.get("SLA_REVISION_OPERATIVO_HORAS", 24),
                "auditoria": config.get("SLA_AUDITORIA_HORAS", 72),
            },
            "umbrales_porcentaje": {
                "advertencia": config.get("SLA_UMBRAL_ADVERTENCIA_PORCENTAJE", 50),
                "urgente": config.get("SLA_UMBRAL_URGENTE_PORCENTAJE", 75),
            }
        }
    
    async def actualizar_configuracion(self, nuevos_valores: Dict[str, int]) -> Dict[str, Any]:
        """
        Actualiza la configuración SLA.
        
        Args:
            nuevos_valores: Dict con claves y valores a actualizar
            
        Returns:
            Configuración actualizada
        """
        ahora = datetime.now(timezone.utc).isoformat()
        
        for clave, valor in nuevos_valores.items():
            clave_completa = f"SLA_{clave.upper()}" if not clave.startswith("SLA_") else clave.upper()
            
            self.db.configuracion_operativo.update_one(
                {"clave": clave_completa},
                {
                    "$set": {
                        "clave": clave_completa,
                        "valor": str(valor),
                        "tipo": "number",
                        "fecha_actualizacion": ahora
                    }
                },
                upsert=True
            )
        
        self.invalidar_cache_config()
        return self.obtener_configuracion()
    
    def _obtener_limite_horas(self, tipo_tarea: str) -> int:
        """
        Obtiene el límite de horas SLA según el tipo de tarea.
        
        Args:
            tipo_tarea: Tipo de tarea
            
        Returns:
            Horas límite
        """
        config = self._get_configuracion()
        
        mapeo = {
            "JUSTIFICACION_SIMPLE": "SLA_JUSTIFICACION_SIMPLE_HORAS",
            "JUSTIFICACION_COMPLETA": "SLA_JUSTIFICACION_COMPLETA_HORAS",
            "REVISION": "SLA_REVISION_OPERATIVO_HORAS",
            "REVISION_OPERATIVO": "SLA_REVISION_OPERATIVO_HORAS",
            "AUDITORIA": "SLA_AUDITORIA_HORAS",
        }
        
        clave = mapeo.get(tipo_tarea.upper(), "SLA_JUSTIFICACION_SIMPLE_HORAS")
        return config.get(clave, 24)
    
    def _parsear_fecha(self, fecha: Any) -> Optional[datetime]:
        """Parsea una fecha de varios formatos a datetime."""
        if fecha is None:
            return None
        if isinstance(fecha, datetime):
            return fecha
        if isinstance(fecha, str):
            try:
                return datetime.fromisoformat(fecha.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
    
    def calcular_estado_sla(self, tarea: Dict) -> Dict[str, Any]:
        """
        Calcula el estado SLA de una tarea.
        
        Args:
            tarea: Datos de la tarea
            
        Returns:
            Dict con estado_sla y métricas calculadas
        """
        ahora = datetime.now(timezone.utc)
        
        fecha_creacion = self._parsear_fecha(tarea.get("fecha_creacion"))
        fecha_limite = self._parsear_fecha(tarea.get("fecha_limite"))
        fecha_primera_accion = self._parsear_fecha(tarea.get("fecha_primera_accion"))
        fecha_completada = self._parsear_fecha(tarea.get("fecha_completada"))
        estado_tarea = tarea.get("estado_tarea", "PENDIENTE")
        tipo_tarea = tarea.get("tipo_tarea", "JUSTIFICACION_SIMPLE")
        
        # Obtener límite según tipo
        limite_horas = self._obtener_limite_horas(tipo_tarea)
        config = self._get_configuracion()
        umbral_advertencia = config.get("SLA_UMBRAL_ADVERTENCIA_PORCENTAJE", 50)
        umbral_urgente = config.get("SLA_UMBRAL_URGENTE_PORCENTAJE", 75)
        
        resultado = {
            "estado_sla": EstadoSLA.EN_TIEMPO.value,
            "tiempo_respuesta_horas": None,
            "tiempo_resolucion_horas": None,
            "porcentaje_tiempo_consumido": 0,
            "horas_restantes": limite_horas,
            "limite_horas": limite_horas,
            "cumple_sla": None
        }
        
        if not fecha_creacion:
            return resultado
        
        # Calcular tiempo de respuesta si hay primera acción
        if fecha_primera_accion:
            delta_respuesta = fecha_primera_accion - fecha_creacion
            resultado["tiempo_respuesta_horas"] = round(delta_respuesta.total_seconds() / 3600, 2)
        
        # Si la tarea está completada
        if estado_tarea in ESTADOS_COMPLETADA and fecha_completada:
            delta_resolucion = fecha_completada - fecha_creacion
            tiempo_resolucion = delta_resolucion.total_seconds() / 3600
            resultado["tiempo_resolucion_horas"] = round(tiempo_resolucion, 2)
            
            if tiempo_resolucion <= limite_horas:
                resultado["estado_sla"] = EstadoSLA.CUMPLIDA_EN_TIEMPO.value
                resultado["cumple_sla"] = True
            else:
                resultado["estado_sla"] = EstadoSLA.CUMPLIDA_FUERA_DE_TIEMPO.value
                resultado["cumple_sla"] = False
            
            resultado["porcentaje_tiempo_consumido"] = round((tiempo_resolucion / limite_horas) * 100, 1)
            return resultado
        
        # Si la tarea está activa, calcular tiempo consumido
        if estado_tarea in ESTADOS_ACTIVOS:
            # Usar fecha_limite si existe, sino calcular desde fecha_creacion + limite
            if fecha_limite:
                tiempo_total = (fecha_limite - fecha_creacion).total_seconds() / 3600
                tiempo_consumido = (ahora - fecha_creacion).total_seconds() / 3600
            else:
                tiempo_total = limite_horas
                tiempo_consumido = (ahora - fecha_creacion).total_seconds() / 3600
            
            porcentaje = (tiempo_consumido / tiempo_total) * 100 if tiempo_total > 0 else 100
            resultado["porcentaje_tiempo_consumido"] = round(porcentaje, 1)
            resultado["horas_restantes"] = round(max(0, tiempo_total - tiempo_consumido), 2)
            
            # Determinar estado SLA
            if porcentaje >= 100:
                resultado["estado_sla"] = EstadoSLA.VENCIDA.value
            elif porcentaje >= umbral_urgente:
                resultado["estado_sla"] = EstadoSLA.URGENTE.value
            elif porcentaje >= umbral_advertencia:
                resultado["estado_sla"] = EstadoSLA.ADVERTENCIA.value
            else:
                resultado["estado_sla"] = EstadoSLA.EN_TIEMPO.value
        
        return resultado
    
    async def actualizar_estados_sla(self) -> Dict[str, Any]:
        """
        Actualiza los estados SLA de todas las tareas activas.
        Debe ejecutarse periódicamente (cron externo o scheduler).
        
        SUBFASE 2B.5: Ahora también dispara notificaciones automáticas:
        - 80%: notify_sla_warning
        - 100%: notify_sla_expired
        - 150%: notify_sla_escalated
        
        Returns:
            Resumen de actualizaciones
        """
        logger.info("Iniciando actualización de estados SLA")
        
        # Buscar tareas activas
        tareas = list(self.db.tareas_inventario.find(
            {"estado_tarea": {"$in": ESTADOS_ACTIVOS}},
            {"_id": 0}
        ))
        
        config = self._get_configuracion()
        umbral_warning = config.get("SLA_UMBRAL_URGENTE_PORCENTAJE", 80)
        umbral_vencido = config.get("SLA_UMBRAL_VENCIDO_PORCENTAJE", 100)
        umbral_escalado = config.get("SLA_UMBRAL_ESCALAMIENTO_PORCENTAJE", 150)
        
        resultados = {
            "total_procesadas": len(tareas),
            "actualizadas": 0,
            "por_estado": {
                "EN_TIEMPO": 0,
                "ADVERTENCIA": 0,
                "URGENTE": 0,
                "VENCIDA": 0,
                "ESCALADA": 0
            },
            "notificaciones": {
                "warning_enviadas": 0,
                "vencido_enviadas": 0,
                "escalado_enviadas": 0
            },
            "errores": 0
        }
        
        for tarea in tareas:
            try:
                calculo = self.calcular_estado_sla(tarea)
                nuevo_estado = calculo["estado_sla"]
                porcentaje = calculo.get("porcentaje_tiempo_consumido", 0)
                
                # Actualizar solo si cambió o no existe
                estado_actual = tarea.get("estado_sla")
                if estado_actual != nuevo_estado:
                    self.db.tareas_inventario.update_one(
                        {"id": tarea.get("id")},
                        {"$set": {
                            "estado_sla": nuevo_estado,
                            "fecha_actualizacion_sla": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    resultados["actualizadas"] += 1
                
                # ====== SUBFASE 2B.5: NOTIFICACIONES AUTOMÁTICAS ======
                
                # Notificación WARNING (80%) - solo si no se ha enviado antes
                if porcentaje >= umbral_warning and porcentaje < umbral_vencido:
                    if not tarea.get("notificacion_warning_enviada"):
                        sent = await self.notify_sla_warning(tarea)
                        if sent:
                            resultados["notificaciones"]["warning_enviadas"] += 1
                
                # Notificación VENCIDO (100%) - solo si no se ha enviado antes
                elif porcentaje >= umbral_vencido and porcentaje < umbral_escalado:
                    if not tarea.get("notificacion_vencido_enviada"):
                        sent = await self.notify_sla_expired(tarea)
                        if sent:
                            resultados["notificaciones"]["vencido_enviadas"] += 1
                    
                    # También actualizar flag vencida
                    if not tarea.get("vencida"):
                        self.db.tareas_inventario.update_one(
                            {"id": tarea.get("id")},
                            {"$set": {"vencida": True}}
                        )
                
                # Notificación ESCALADO (150%) - solo si no se ha enviado antes
                elif porcentaje >= umbral_escalado:
                    if not tarea.get("notificacion_escalado_enviada"):
                        sent = await self.notify_sla_escalated(tarea)
                        if sent:
                            resultados["notificaciones"]["escalado_enviadas"] += 1
                    
                    nuevo_estado = EstadoSLA.ESCALADA.value
                
                resultados["por_estado"][nuevo_estado] = resultados["por_estado"].get(nuevo_estado, 0) + 1
                
            except Exception as e:
                logger.error(f"Error actualizando SLA de tarea {tarea.get('id')}: {e}")
                resultados["errores"] += 1
        
        logger.info(f"Actualización SLA completada: {resultados}")
        return resultados
    
    async def registrar_primera_accion(self, tarea_id: str) -> bool:
        """
        Registra la fecha de primera acción si no existe.
        Llamar cuando la tarea pasa a EN_PROGRESO o COMPLETADA.
        
        Args:
            tarea_id: ID de la tarea
            
        Returns:
            True si se registró, False si ya existía
        """
        tarea = self.db.tareas_inventario.find_one({"id": tarea_id})
        if not tarea:
            return False
        
        # Solo registrar si no existe
        if tarea.get("fecha_primera_accion"):
            return False
        
        ahora = datetime.now(timezone.utc).isoformat()
        self.db.tareas_inventario.update_one(
            {"id": tarea_id},
            {"$set": {"fecha_primera_accion": ahora}}
        )
        
        logger.info(f"Registrada primera acción para tarea {tarea_id}")
        return True
    
    async def obtener_metricas_globales(self) -> Dict[str, Any]:
        """
        Obtiene métricas globales de cumplimiento SLA.
        
        Returns:
            Dict con métricas de cumplimiento
        """
        # Tareas completadas
        completadas = list(self.db.tareas_inventario.find(
            {"estado_tarea": {"$in": ESTADOS_COMPLETADA}},
            {"_id": 0}
        ))
        
        # Tareas activas
        activas = list(self.db.tareas_inventario.find(
            {"estado_tarea": {"$in": ESTADOS_ACTIVOS}},
            {"_id": 0}
        ))
        
        # Calcular métricas de completadas
        total_completadas = len(completadas)
        cumplidas_en_tiempo = 0
        cumplidas_fuera_tiempo = 0
        tiempos_respuesta = []
        tiempos_resolucion = []
        
        for tarea in completadas:
            calculo = self.calcular_estado_sla(tarea)
            if calculo["cumple_sla"]:
                cumplidas_en_tiempo += 1
            else:
                cumplidas_fuera_tiempo += 1
            
            if calculo["tiempo_respuesta_horas"] is not None:
                tiempos_respuesta.append(calculo["tiempo_respuesta_horas"])
            if calculo["tiempo_resolucion_horas"] is not None:
                tiempos_resolucion.append(calculo["tiempo_resolucion_horas"])
        
        # Calcular métricas de activas
        activas_por_estado = {
            "EN_TIEMPO": 0,
            "ADVERTENCIA": 0,
            "URGENTE": 0,
            "VENCIDA": 0
        }
        
        for tarea in activas:
            calculo = self.calcular_estado_sla(tarea)
            estado = calculo["estado_sla"]
            if estado in activas_por_estado:
                activas_por_estado[estado] += 1
        
        # Calcular porcentaje de cumplimiento
        porcentaje_cumplimiento = 0
        if total_completadas > 0:
            porcentaje_cumplimiento = round((cumplidas_en_tiempo / total_completadas) * 100, 1)
        
        # Calcular promedios
        promedio_respuesta = round(sum(tiempos_respuesta) / len(tiempos_respuesta), 2) if tiempos_respuesta else None
        promedio_resolucion = round(sum(tiempos_resolucion) / len(tiempos_resolucion), 2) if tiempos_resolucion else None
        
        return {
            "cumplimiento": {
                "porcentaje": porcentaje_cumplimiento,
                "total_completadas": total_completadas,
                "cumplidas_en_tiempo": cumplidas_en_tiempo,
                "cumplidas_fuera_tiempo": cumplidas_fuera_tiempo
            },
            "activas": {
                "total": len(activas),
                "por_estado": activas_por_estado
            },
            "tiempos_promedio": {
                "respuesta_horas": promedio_respuesta,
                "resolucion_horas": promedio_resolucion
            },
            "fecha_calculo": datetime.now(timezone.utc).isoformat()
        }
    
    async def obtener_tareas_proximas_vencer(self, limite: int = 20) -> List[Dict]:
        """
        Obtiene tareas próximas a vencer (ADVERTENCIA o URGENTE).
        
        Args:
            limite: Máximo de tareas a retornar
            
        Returns:
            Lista de tareas con sus cálculos SLA
        """
        tareas = list(self.db.tareas_inventario.find(
            {"estado_tarea": {"$in": ESTADOS_ACTIVOS}},
            {"_id": 0}
        ).limit(limite * 2))  # Traer más para filtrar
        
        resultado = []
        for tarea in tareas:
            calculo = self.calcular_estado_sla(tarea)
            if calculo["estado_sla"] in [EstadoSLA.ADVERTENCIA.value, EstadoSLA.URGENTE.value]:
                tarea["sla"] = calculo
                resultado.append(tarea)
        
        # Ordenar por porcentaje (más urgente primero)
        resultado.sort(key=lambda x: x["sla"]["porcentaje_tiempo_consumido"], reverse=True)
        
        return resultado[:limite]
    
    async def obtener_tareas_vencidas(self, limite: int = 50) -> List[Dict]:
        """
        Obtiene tareas vencidas.
        
        Args:
            limite: Máximo de tareas a retornar
            
        Returns:
            Lista de tareas vencidas con sus cálculos SLA
        """
        tareas = list(self.db.tareas_inventario.find(
            {
                "estado_tarea": {"$in": ESTADOS_ACTIVOS},
                "$or": [
                    {"vencida": True},
                    {"estado_sla": EstadoSLA.VENCIDA.value}
                ]
            },
            {"_id": 0}
        ).limit(limite))
        
        resultado = []
        for tarea in tareas:
            calculo = self.calcular_estado_sla(tarea)
            if calculo["estado_sla"] == EstadoSLA.VENCIDA.value:
                tarea["sla"] = calculo
                resultado.append(tarea)
        
        return resultado
    
    # =========================================================================
    # SUBFASE 2B.5: INTEGRACIÓN CON NOTIFICACIONES WHATSAPP
    # =========================================================================
    
    async def notify_sla_warning(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica que un SLA está por vencer (80% consumido).
        
        Args:
            tarea: Datos de la tarea
            workflow: Datos del workflow (opcional)
            
        Returns:
            True si se envió notificación
        """
        notifier = self._get_notification_service()
        if not notifier:
            logger.warning("Notificación SLA_POR_VENCER omitida: servicio no disponible")
            return False
        
        try:
            # Obtener datos del workflow si no se proporcionan
            if not workflow:
                workflow = self.db.workflows_inventario.find_one(
                    {"id": tarea.get("workflow_id")},
                    {"_id": 0}
                )
            
            folio = workflow.get("folio", "N/A") if workflow else tarea.get("folio", "N/A")
            sucursal = workflow.get("sucursal_nombre", "N/A") if workflow else tarea.get("sucursal_nombre", "N/A")
            
            # Calcular SLA para obtener horas restantes
            sla_calc = self.calcular_estado_sla(tarea)
            
            result = await notifier.notify_sla_warning(
                tarea_id=tarea.get("id"),
                workflow_id=tarea.get("workflow_id"),
                responsable_id=tarea.get("responsable_id"),
                folio=folio,
                sucursal=sucursal,
                evento=tarea.get("tipo_tarea", "Justificación"),
                fecha_limite=tarea.get("fecha_limite", "No especificada"),
                horas_restantes=sla_calc.get("horas_restantes", 0)
            )
            
            if result.success:
                # Marcar que se envió notificación de warning
                self.db.tareas_inventario.update_one(
                    {"id": tarea.get("id")},
                    {"$set": {"notificacion_warning_enviada": datetime.now(timezone.utc).isoformat()}}
                )
                logger.info(f"Notificación SLA_POR_VENCER enviada para tarea {tarea.get('id')}")
            
            return result.success
            
        except Exception as e:
            logger.error(f"Error enviando notificación SLA_POR_VENCER: {e}")
            return False
    
    async def notify_sla_expired(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica que un SLA venció (100% consumido).
        
        Args:
            tarea: Datos de la tarea
            workflow: Datos del workflow (opcional)
            
        Returns:
            True si se envió notificación
        """
        notifier = self._get_notification_service()
        if not notifier:
            logger.warning("Notificación SLA_VENCIDO omitida: servicio no disponible")
            return False
        
        try:
            if not workflow:
                workflow = self.db.workflows_inventario.find_one(
                    {"id": tarea.get("workflow_id")},
                    {"_id": 0}
                )
            
            folio = workflow.get("folio", "N/A") if workflow else tarea.get("folio", "N/A")
            sucursal = workflow.get("sucursal_nombre", "N/A") if workflow else tarea.get("sucursal_nombre", "N/A")
            
            result = await notifier.notify_sla_expired(
                tarea_id=tarea.get("id"),
                workflow_id=tarea.get("workflow_id"),
                responsable_id=tarea.get("responsable_id"),
                supervisor_id=tarea.get("supervisor_id"),
                folio=folio,
                sucursal=sucursal,
                evento=tarea.get("tipo_tarea", "Justificación")
            )
            
            if result.success:
                self.db.tareas_inventario.update_one(
                    {"id": tarea.get("id")},
                    {"$set": {"notificacion_vencido_enviada": datetime.now(timezone.utc).isoformat()}}
                )
                logger.info(f"Notificación SLA_VENCIDO enviada para tarea {tarea.get('id')}")
            
            return result.success
            
        except Exception as e:
            logger.error(f"Error enviando notificación SLA_VENCIDO: {e}")
            return False
    
    async def notify_sla_escalated(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica escalamiento de SLA (150% consumido).
        
        Args:
            tarea: Datos de la tarea
            workflow: Datos del workflow (opcional)
            
        Returns:
            True si se envió notificación
        """
        notifier = self._get_notification_service()
        if not notifier:
            logger.warning("Notificación SLA_ESCALADO omitida: servicio no disponible")
            return False
        
        try:
            if not workflow:
                workflow = self.db.workflows_inventario.find_one(
                    {"id": tarea.get("workflow_id")},
                    {"_id": 0}
                )
            
            folio = workflow.get("folio", "N/A") if workflow else tarea.get("folio", "N/A")
            sucursal = workflow.get("sucursal_nombre", "N/A") if workflow else tarea.get("sucursal_nombre", "N/A")
            
            # Calcular porcentaje excedido
            sla_calc = self.calcular_estado_sla(tarea)
            porcentaje = sla_calc.get("porcentaje_tiempo_consumido", 150)
            
            result = await notifier.notify_sla_escalated(
                tarea_id=tarea.get("id"),
                workflow_id=tarea.get("workflow_id"),
                supervisor_id=tarea.get("supervisor_id"),
                gerente_id=tarea.get("gerente_id"),
                folio=folio,
                sucursal=sucursal,
                evento=tarea.get("tipo_tarea", "Justificación"),
                porcentaje_excedido=porcentaje
            )
            
            if result.success:
                self.db.tareas_inventario.update_one(
                    {"id": tarea.get("id")},
                    {"$set": {
                        "notificacion_escalado_enviada": datetime.now(timezone.utc).isoformat(),
                        "estado_sla": EstadoSLA.ESCALADA.value
                    }}
                )
                logger.info(f"Notificación SLA_ESCALADO enviada para tarea {tarea.get('id')}")
            
            return result.success
            
        except Exception as e:
            logger.error(f"Error enviando notificación SLA_ESCALADO: {e}")
            return False


# Singleton del servicio
_sla_service = None


def get_sla_service(db) -> SLAService:
    """
    Obtiene instancia del servicio SLA.
    
    Args:
        db: Conexión a la base de datos
        
    Returns:
        Instancia de SLAService
    """
    global _sla_service
    if _sla_service is None:
        _sla_service = SLAService(db)
    return _sla_service
