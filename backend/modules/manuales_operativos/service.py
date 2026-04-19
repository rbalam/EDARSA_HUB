"""
Servicio de Manuales Operativos - EDARSA HUB

Genera automáticamente manuales operativos en formato Cienfuegos
basándose en datos reales del proceso y su bitácora de eventos.

PRINCIPIO: EDARSA HUB es el cerebro. La documentación se genera desde
datos reales, NO manuales genéricos.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from .schemas import (
    ModuloOrigen,
    FormatoManual,
    ResponsableManual,
    PasoOperativo,
    EvidenciaGenerada,
    ContenidoManualCienfuegos,
    ManualOperativoCreate,
    ManualOperativoDB,
    ManualOperativoResponse,
    ManualOperativoListResponse,
    EVENTO_A_PASO_OPERATIVO,
)

logger = logging.getLogger(__name__)


class ManualOperativoService:
    """
    Servicio para generar y gestionar manuales operativos.
    
    Responsabilidades:
    - Generar manuales automáticamente al cerrar procesos
    - Convertir eventos de bitácora a pasos operativos
    - Almacenar y consultar manuales
    """
    
    COLLECTION_NAME = "manuales_operativos"
    ESTADOS_TRIGGER = ["COMPLETADA", "CERRADO", "FINALIZADO"]
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[self.COLLECTION_NAME]
    
    async def init_collection(self):
        """Inicializa la colección con índices necesarios."""
        try:
            # Índice por proceso
            await self.collection.create_index("proceso_id", unique=True)
            # Índice por módulo y empresa
            await self.collection.create_index([("modulo", 1), ("empresa_id", 1)])
            # Índice por fecha
            await self.collection.create_index("created_at")
            # Índice para búsqueda por nombre
            await self.collection.create_index("nombre_proceso")
            logger.info(f"Colección {self.COLLECTION_NAME} inicializada con índices")
        except Exception as e:
            logger.warning(f"Error creando índices (pueden ya existir): {e}")
    
    async def generar_manual_auditoria_compras(
        self,
        proceso: Dict[str, Any],
        bitacora: List[Dict[str, Any]],
        usuarios: Dict[str, str] = None
    ) -> Optional[ManualOperativoDB]:
        """
        Genera un manual operativo para Auditoría de Compras.
        
        Args:
            proceso: Documento de automatizaciones_operativas_compras
            bitacora: Lista de eventos de automatizaciones_bitacora
            usuarios: Dict de user_id -> nombre para enriquecer datos
            
        Returns:
            ManualOperativoDB si se generó exitosamente, None si error
        """
        try:
            proceso_id = proceso.get("id")
            estado_final = proceso.get("estado", "DESCONOCIDO")
            
            # Verificar si ya existe manual para este proceso
            existing = await self.collection.find_one({"proceso_id": proceso_id})
            if existing:
                logger.info(f"Manual ya existe para proceso {proceso_id}")
                return ManualOperativoDB(**{**existing, "_id": str(existing["_id"])}) if existing else None
            
            # 1. Construir nombre del proceso
            sucursal = proceso.get("sucursal_nombre", "Sin sucursal")
            almacen = proceso.get("almacen_nombre", "Sin almacén")
            fecha_pedido = proceso.get("fecha_pedido", datetime.now(timezone.utc))
            if isinstance(fecha_pedido, str):
                fecha_pedido = datetime.fromisoformat(fecha_pedido.replace('Z', '+00:00'))
            
            nombre_proceso = f"Auditoría Operativa de Compras - {sucursal} - {almacen}"
            
            # 2. Construir objetivo
            objetivo = (
                f"Validar y auditar el proceso de compras para {sucursal}, "
                f"asegurando la correcta recepción de productos, verificación de inventarios "
                f"y autorización de pagos según las políticas de EDARSA."
            )
            
            # 3. Construir alcance
            fecha_inicio = proceso.get("fecha_inicio_periodo")
            fecha_fin = proceso.get("fecha_fin_periodo")
            alcance = (
                f"Este proceso cubre la auditoría de compras del período "
                f"{self._format_date(fecha_inicio)} al {self._format_date(fecha_fin)} "
                f"para la sucursal {sucursal}, almacén {almacen}. "
                f"Incluye validación de inventarios y autorizaciones requeridas."
            )
            
            # 4. Extraer responsables
            responsables = self._extraer_responsables(proceso, bitacora, usuarios)
            
            # 5. Convertir bitácora a procedimiento paso a paso
            procedimiento = self._bitacora_a_procedimiento(bitacora, usuarios)
            
            # 6. Extraer políticas aplicadas
            politicas = self._extraer_politicas(proceso, bitacora)
            
            # 7. Extraer evidencias
            evidencias = self._extraer_evidencias(proceso)
            
            # 8. Generar observaciones y áreas de mejora
            observaciones, areas_mejora = self._generar_observaciones(proceso, bitacora)
            
            # 9. Calcular métricas
            metricas = self._calcular_metricas(proceso, bitacora)
            
            # Construir contenido estructurado
            contenido = ContenidoManualCienfuegos(
                nombre_proceso=nombre_proceso,
                objetivo=objetivo,
                alcance=alcance,
                responsables=responsables,
                procedimiento=procedimiento,
                politicas=politicas,
                evidencias=evidencias,
                observaciones=observaciones,
                areas_mejora=areas_mejora,
                metricas=metricas
            )
            
            # Crear el manual
            manual_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            manual_doc = {
                "id": manual_id,
                "modulo": ModuloOrigen.COMPRAS.value,
                "proceso_id": proceso_id,
                "proceso_tipo": "auditoria_compras",
                "empresa_id": proceso.get("empresa_id", proceso.get("server_id", "")),
                "empresa_nombre": proceso.get("empresa_nombre", proceso.get("sucursal_nombre", "")),
                "sucursal_id": proceso.get("sucursal_id", ""),
                "sucursal_nombre": sucursal,
                "nombre_proceso": nombre_proceso,
                "formato": FormatoManual.CIENFUEGOS.value,
                "contenido": contenido.model_dump(),
                "estado_proceso_final": estado_final,
                "generado_por": "sistema",
                "created_at": now,
                "updated_at": now,
                "version": 1,
                "activo": True
            }
            
            # Guardar en MongoDB
            await self.collection.insert_one(manual_doc)
            logger.info(f"Manual operativo generado: {manual_id} para proceso {proceso_id}")
            
            return ManualOperativoDB(**manual_doc)
            
        except Exception as e:
            logger.error(f"Error generando manual para proceso {proceso.get('id')}: {e}")
            return None
    
    def _extraer_responsables(
        self,
        proceso: Dict,
        bitacora: List[Dict],
        usuarios: Dict[str, str] = None
    ) -> List[ResponsableManual]:
        """Extrae los responsables del proceso desde la bitácora."""
        responsables = []
        usuarios = usuarios or {}
        
        # Usuario que inició el proceso
        usuario_id = proceso.get("usuario_id")
        if usuario_id:
            responsables.append(ResponsableManual(
                rol="Iniciador del proceso",
                usuario_id=usuario_id,
                usuario_nombre=usuarios.get(usuario_id, proceso.get("usuario_nombre", "Sistema")),
                accion="Creó la auditoría operativa",
                fecha=proceso.get("fecha_creacion")
            ))
        
        # Gerencia
        if proceso.get("autorizado_gerencia"):
            responsables.append(ResponsableManual(
                rol="Gerencia",
                usuario_id=proceso.get("autorizado_por_gerencia"),
                usuario_nombre=usuarios.get(proceso.get("autorizado_por_gerencia"), "Gerencia"),
                accion="Autorizó la auditoría",
                fecha=proceso.get("fecha_autorizacion_gerencia")
            ))
        
        # Tesorería
        if proceso.get("autorizado_tesoreria"):
            responsables.append(ResponsableManual(
                rol="Tesorería",
                usuario_id=proceso.get("autorizado_por_tesoreria"),
                usuario_nombre=usuarios.get(proceso.get("autorizado_por_tesoreria"), "Tesorería"),
                accion="Autorizó el pago",
                fecha=proceso.get("fecha_autorizacion_tesoreria")
            ))
        
        # Extraer responsables únicos de la bitácora
        usuarios_bitacora = set()
        for evento in bitacora:
            uid = evento.get("usuario_id")
            if uid and uid not in usuarios_bitacora and uid != usuario_id:
                usuarios_bitacora.add(uid)
                responsables.append(ResponsableManual(
                    rol="Participante",
                    usuario_id=uid,
                    usuario_nombre=usuarios.get(uid, "Usuario"),
                    accion=f"Ejecutó acción: {evento.get('evento', 'Desconocida')}",
                    fecha=evento.get("fecha")
                ))
        
        return responsables
    
    def _bitacora_a_procedimiento(
        self,
        bitacora: List[Dict],
        usuarios: Dict[str, str] = None
    ) -> List[PasoOperativo]:
        """Convierte eventos de bitácora a pasos operativos."""
        pasos = []
        usuarios = usuarios or {}
        
        # Ordenar bitácora por fecha
        bitacora_ordenada = sorted(
            bitacora,
            key=lambda x: x.get("fecha", datetime.min)
        )
        
        for i, evento in enumerate(bitacora_ordenada, 1):
            evento_tipo = evento.get("evento", "DESCONOCIDO")
            datos = evento.get("datos", {})
            
            # Obtener descripción del paso desde el mapeo
            accion = EVENTO_A_PASO_OPERATIVO.get(
                evento_tipo,
                f"Se ejecutó: {evento_tipo}"
            )
            
            # Enriquecer con datos adicionales si existen
            if datos:
                if "mensaje" in datos:
                    accion = f"{accion}. {datos['mensaje']}"
                if "recomendacion" in datos:
                    accion = f"{accion}. Recomendación: {datos['recomendacion']}"
            
            # Determinar resultado
            resultado = None
            if "criticos" in datos:
                resultado = f"Productos críticos: {datos['criticos']}, Faltantes: {datos.get('faltantes', 0)}"
            elif evento_tipo in ["APROBADA_GERENCIA", "APROBADA_TESORERIA"]:
                resultado = "Autorización concedida"
            elif evento_tipo in ["RECHAZADA_GERENCIA", "RECHAZADA_TESORERIA"]:
                resultado = f"Rechazado: {datos.get('motivo', 'Sin motivo especificado')}"
            elif evento_tipo == "COMPLETADA":
                resultado = "Proceso finalizado exitosamente"
            
            paso = PasoOperativo(
                numero=i,
                accion=accion,
                responsable=usuarios.get(evento.get("usuario_id"), "Sistema"),
                resultado=resultado,
                fecha=evento.get("fecha"),
                evento_origen=evento_tipo
            )
            pasos.append(paso)
        
        return pasos
    
    def _extraer_politicas(self, proceso: Dict, bitacora: List[Dict]) -> List[str]:
        """Extrae las políticas que fueron aplicadas en el proceso."""
        politicas = []
        
        # Política de período de análisis
        dias = proceso.get("dias_periodo_analisis", 15)
        politicas.append(f"Período de análisis de inventarios: {dias} días")
        
        # Política de días objetivo
        dias_obj = proceso.get("dias_objetivo", 10)
        politicas.append(f"Días objetivo de inventario: {dias_obj} días")
        
        # Política de inventario físico
        if proceso.get("tiene_inventario_final"):
            politicas.append("Se requiere inventario físico para validación")
        
        # Política de doble autorización
        if proceso.get("autorizado_gerencia") or proceso.get("autorizado_tesoreria"):
            politicas.append("Doble autorización requerida: Gerencia y Tesorería")
        
        # Extraer políticas de eventos
        for evento in bitacora:
            if evento.get("evento") == "PENDIENTE_INVENTARIO":
                politicas.append("Proceso detenido hasta captura de inventario físico")
        
        return list(set(politicas))  # Eliminar duplicados
    
    def _extraer_evidencias(self, proceso: Dict) -> List[EvidenciaGenerada]:
        """Extrae las evidencias generadas durante el proceso."""
        evidencias = []
        
        # Inventarios
        if proceso.get("inventario_inicial_id"):
            evidencias.append(EvidenciaGenerada(
                tipo="Inventario Inicial",
                descripcion="Inventario físico de inicio de período",
                referencia=proceso.get("inventario_inicial_id"),
                fecha=proceso.get("inventario_inicial_fecha")
            ))
        
        if proceso.get("inventario_final_id"):
            evidencias.append(EvidenciaGenerada(
                tipo="Inventario Final",
                descripcion="Inventario físico de cierre de período",
                referencia=proceso.get("inventario_final_id"),
                fecha=proceso.get("inventario_final_fecha")
            ))
        
        # Reporte de auditoría
        if proceso.get("resultado"):
            evidencias.append(EvidenciaGenerada(
                tipo="Reporte de Auditoría",
                descripcion="Resultado del análisis de auditoría operativa",
                referencia=proceso.get("id"),
                fecha=proceso.get("fecha_actualizacion")
            ))
        
        # Autorizaciones
        if proceso.get("fecha_autorizacion_gerencia"):
            evidencias.append(EvidenciaGenerada(
                tipo="Autorización Gerencia",
                descripcion=f"Aprobación de gerencia. Comentario: {proceso.get('comentario_gerencia', 'N/A')}",
                referencia=proceso.get("autorizado_por_gerencia"),
                fecha=proceso.get("fecha_autorizacion_gerencia")
            ))
        
        if proceso.get("fecha_autorizacion_tesoreria"):
            evidencias.append(EvidenciaGenerada(
                tipo="Autorización Tesorería",
                descripcion=f"Aprobación de tesorería. Comentario: {proceso.get('comentario_tesoreria', 'N/A')}",
                referencia=proceso.get("autorizado_por_tesoreria"),
                fecha=proceso.get("fecha_autorizacion_tesoreria")
            ))
        
        return evidencias
    
    def _generar_observaciones(
        self,
        proceso: Dict,
        bitacora: List[Dict]
    ) -> tuple[List[str], List[str]]:
        """Genera observaciones y áreas de mejora basadas en el proceso."""
        observaciones = []
        areas_mejora = []
        
        # Observaciones basadas en el resultado
        resultado = proceso.get("resultado", {})
        if isinstance(resultado, dict):
            if resultado.get("accion"):
                observaciones.append(f"Acción requerida: {resultado['accion']}")
        
        recomendacion = proceso.get("recomendacion_general")
        if recomendacion:
            observaciones.append(f"Recomendación general: {recomendacion}")
        
        # Productos críticos
        detalle = proceso.get("detalle_productos", [])
        criticos = [p for p in detalle if p.get("criticidad") == "CRITICO"]
        if criticos:
            observaciones.append(f"Se identificaron {len(criticos)} productos en estado crítico")
            areas_mejora.append("Revisar política de stock mínimo para productos críticos")
        
        # Tiempos
        fecha_creacion = proceso.get("fecha_creacion")
        fecha_fin = proceso.get("fecha_actualizacion")
        if fecha_creacion and fecha_fin:
            if isinstance(fecha_creacion, str):
                fecha_creacion = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
            
            dias_proceso = (fecha_fin - fecha_creacion).days
            if dias_proceso > 5:
                areas_mejora.append(f"El proceso tomó {dias_proceso} días. Considerar optimizar tiempos de respuesta")
        
        # Rechazos
        if proceso.get("motivo_rechazo"):
            observaciones.append(f"Motivo de rechazo: {proceso['motivo_rechazo']}")
            areas_mejora.append("Revisar criterios de aprobación para reducir rechazos")
        
        # Eventos de espera
        eventos_espera = [e for e in bitacora if "PENDIENTE" in e.get("evento", "")]
        if len(eventos_espera) > 2:
            areas_mejora.append(f"Proceso tuvo {len(eventos_espera)} estados de espera. Evaluar automatización")
        
        return observaciones, areas_mejora
    
    def _calcular_metricas(self, proceso: Dict, bitacora: List[Dict]) -> Dict[str, Any]:
        """Calcula métricas cuantitativas del proceso."""
        metricas = {}
        
        # Total de productos analizados
        metricas["total_productos"] = proceso.get("total_productos", 0)
        
        # Días de proceso
        fecha_creacion = proceso.get("fecha_creacion")
        fecha_fin = proceso.get("fecha_actualizacion")
        if fecha_creacion and fecha_fin:
            if isinstance(fecha_creacion, str):
                fecha_creacion = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
            metricas["dias_proceso"] = (fecha_fin - fecha_creacion).days
        
        # Total de eventos/pasos
        metricas["total_eventos"] = len(bitacora)
        
        # Productos por criticidad
        detalle = proceso.get("detalle_productos", [])
        metricas["productos_criticos"] = len([p for p in detalle if p.get("criticidad") == "CRITICO"])
        metricas["productos_faltantes"] = len([p for p in detalle if p.get("estado") == "FALTANTE"])
        metricas["productos_ok"] = len([p for p in detalle if p.get("estado") == "OK"])
        
        # Autorizaciones
        metricas["autorizado_gerencia"] = proceso.get("autorizado_gerencia", False)
        metricas["autorizado_tesoreria"] = proceso.get("autorizado_tesoreria", False)
        
        return metricas
    
    def _format_date(self, fecha) -> str:
        """Formatea una fecha para mostrar."""
        if not fecha:
            return "N/A"
        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            except:
                return fecha
        return fecha.strftime("%d/%m/%Y")
    
    # ========== MÉTODOS DE CONSULTA ==========
    
    async def obtener_manual(self, manual_id: str) -> Optional[ManualOperativoResponse]:
        """Obtiene un manual por su ID."""
        doc = await self.collection.find_one({"id": manual_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return ManualOperativoResponse(**doc)
        return None
    
    async def obtener_manual_por_proceso(self, proceso_id: str) -> Optional[ManualOperativoResponse]:
        """Obtiene el manual asociado a un proceso."""
        doc = await self.collection.find_one({"proceso_id": proceso_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return ManualOperativoResponse(**doc)
        return None
    
    async def listar_manuales(
        self,
        modulo: Optional[str] = None,
        empresa_id: Optional[str] = None,
        limite: int = 50,
        skip: int = 0
    ) -> ManualOperativoListResponse:
        """Lista manuales con filtros opcionales."""
        filtro = {"activo": True}
        
        if modulo:
            filtro["modulo"] = modulo
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        
        total = await self.collection.count_documents(filtro)
        cursor = self.collection.find(filtro).sort("created_at", -1).skip(skip).limit(limite)
        
        manuales = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            manuales.append(ManualOperativoResponse(**doc))
        
        return ManualOperativoListResponse(total=total, manuales=manuales)
    
    async def generar_texto_plano(self, manual_id: str) -> Optional[str]:
        """Genera versión en texto plano del manual para exportación."""
        manual = await self.obtener_manual(manual_id)
        if not manual:
            return None
        
        contenido = manual.contenido
        
        texto = f"""
{'='*60}
MANUAL OPERATIVO - MODELO CIENFUEGOS
{'='*60}

PROCESO: {contenido.nombre_proceso}
FECHA DE GENERACIÓN: {manual.created_at.strftime('%d/%m/%Y %H:%M')}
ESTADO FINAL: {manual.estado_proceso_final}

{'='*60}
1. OBJETIVO
{'='*60}
{contenido.objetivo}

{'='*60}
2. ALCANCE
{'='*60}
{contenido.alcance}

{'='*60}
3. RESPONSABLES
{'='*60}
"""
        for r in contenido.responsables:
            texto += f"- {r.rol}: {r.usuario_nombre or 'N/A'}\n"
            texto += f"  Acción: {r.accion}\n"
            if r.fecha:
                texto += f"  Fecha: {self._format_date(r.fecha)}\n"
            texto += "\n"
        
        texto += f"""
{'='*60}
4. PROCEDIMIENTO PASO A PASO
{'='*60}
"""
        for paso in contenido.procedimiento:
            texto += f"\nPASO {paso.numero}: {paso.accion}\n"
            if paso.responsable:
                texto += f"  Responsable: {paso.responsable}\n"
            if paso.resultado:
                texto += f"  Resultado: {paso.resultado}\n"
            if paso.fecha:
                texto += f"  Fecha: {self._format_date(paso.fecha)}\n"
        
        texto += f"""
{'='*60}
5. POLÍTICAS APLICADAS
{'='*60}
"""
        for i, pol in enumerate(contenido.politicas, 1):
            texto += f"{i}. {pol}\n"
        
        texto += f"""
{'='*60}
6. EVIDENCIA GENERADA
{'='*60}
"""
        for ev in contenido.evidencias:
            texto += f"- {ev.tipo}: {ev.descripcion}\n"
            if ev.referencia:
                texto += f"  Referencia: {ev.referencia}\n"
        
        texto += f"""
{'='*60}
7. OBSERVACIONES
{'='*60}
"""
        for obs in contenido.observaciones:
            texto += f"- {obs}\n"
        
        texto += f"""
{'='*60}
8. ÁREAS DE MEJORA
{'='*60}
"""
        for mejora in contenido.areas_mejora:
            texto += f"- {mejora}\n"
        
        texto += f"""
{'='*60}
MÉTRICAS DEL PROCESO
{'='*60}
"""
        for k, v in contenido.metricas.items():
            texto += f"- {k}: {v}\n"
        
        texto += f"""
{'='*60}
FIN DEL MANUAL
Generado automáticamente por EDARSA HUB
{'='*60}
"""
        return texto


# Instancia global (se inicializa con la DB al importar en server.py)
_service_instance: Optional[ManualOperativoService] = None


def get_manual_service(db: AsyncIOMotorDatabase) -> ManualOperativoService:
    """Obtiene o crea la instancia del servicio."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ManualOperativoService(db)
    return _service_instance


__all__ = ['ManualOperativoService', 'get_manual_service']
