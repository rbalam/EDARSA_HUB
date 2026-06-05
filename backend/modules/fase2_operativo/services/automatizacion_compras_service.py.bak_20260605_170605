"""
EDARSA HUB - Automatización Operativa de Compras
================================================
FASE B-P2-B: Migrado a EDARSAHUB SQL Server

FLUJO ESTADOS:
1. PEDIDO_DETECTADO
2. PENDIENTE_INVENTARIO_FISICO (si no hay inv. final)
3. AUDITORIA_EN_PROCESO
4. EN_REVISION_GERENCIA
5. PENDIENTE_TESORERIA
6. APROBADO / RECHAZADO

TABLAS SQL:
- Operativo_TareasCompras (automatizaciones principales)
- Operativo_BitacoraCompras (bitácora de acciones)
- Operativo_PedidosProcesados (control anti-duplicado)
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from enum import Enum
import uuid

# Import del trigger de manuales operativos
try:
    from modules.manuales_operativos.triggers import trigger_generar_manual_sync
    MANUALES_DISPONIBLE = True
except ImportError:
    MANUALES_DISPONIBLE = False
    trigger_generar_manual_sync = None

logger = logging.getLogger(__name__)


class EstadoAutomatizacion(str, Enum):
    """Estados del flujo de automatización."""
    PEDIDO_DETECTADO = "PEDIDO_DETECTADO"
    PENDIENTE_INVENTARIO_FISICO = "PENDIENTE_INVENTARIO_FISICO"
    AUDITORIA_EN_PROCESO = "AUDITORIA_EN_PROCESO"
    EN_REVISION_GERENCIA = "EN_REVISION_GERENCIA"
    PENDIENTE_TESORERIA = "PENDIENTE_TESORERIA"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class EstadoProducto(str, Enum):
    """Estado de inventario por producto."""
    CRITICO = "CRITICO"
    FALTANTE = "FALTANTE"
    OPTIMO = "OPTIMO"
    SOBRANTE = "SOBRANTE"


class Recomendacion(str, Enum):
    """Recomendación de compra."""
    URGENTE = "URGENTE"
    COMPRAR = "COMPRAR"
    NO_COMPRAR = "NO_COMPRAR"
    REVISAR = "REVISAR"


class AutomatizacionComprasService:
    """
    Servicio de automatización operativa de compras.
    FASE B-P2-B: Migrado a SQL Server EDARSAHUB.
    """
    
    DIAS_PERIODO_ANALISIS = 15
    DIAS_PERIODO_CONSUMO_DEFAULT = 15
    DIAS_OBJETIVO_DEFAULT = 10
    TOLERANCIA_OPTIMO = 0.20
    
    def __init__(self, db=None):
        """
        Inicializa el servicio con repositorios SQL.
        Args:
            db: IGNORADO - Mantenido para compatibilidad. Todo va a SQL.
        """
        self.db = db  # Para compatibilidad
        from ..repositories.sql_base_repository import SQLBaseRepository
        self._repo = SQLBaseRepository("automatizaciones_operativas_compras")
        self._bitacora_repo = SQLBaseRepository("automatizaciones_bitacora")
        self._pedidos_repo = SQLBaseRepository("pedidos_procesados_automatizacion")
        self._inv_repo = SQLBaseRepository("inventarios_fisicos_procesados")
        logger.info("[AUTO_COMPRAS] Inicializado con SQL → Operativo_TareasCompras")
    
    # =========================================================================
    # PROCESAMIENTO PRINCIPAL
    # =========================================================================
    
    def procesar_pedido_operativo(
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
        dias_objetivo: int = None,
        fecha_pedido: datetime = None,
        origen_sistema: str = "MPRO",
        empresa_id: str = None,
        empresa_nombre: str = None
    ) -> Dict:
        """Procesa pedido capturado - FLUJO COMPLETO SQL."""
        # CONTROL ANTI-DUPLICADO
        ya_procesado = self._pedidos_repo.find_one({
            "server_id": server_id,
            "pedido_folio": pedido_id,
            "origen": origen_sistema
        })
        if ya_procesado:
            auto_existente = self._repo.find_one({"id": ya_procesado.get("automatizacion_id")})
            if auto_existente:
                logger.info(f"[{pedido_id}] Ya procesado - retornando existente")
                return self._limpiar_respuesta(auto_existente)
        
        now = datetime.now(timezone.utc)
        dias_objetivo = dias_objetivo or self.DIAS_OBJETIVO_DEFAULT
        fecha_pedido = fecha_pedido or now
        
        fecha_fin_periodo = fecha_pedido
        fecha_inicio_periodo = fecha_pedido - timedelta(days=self.DIAS_PERIODO_ANALISIS)
        
        automatizacion_id = str(uuid.uuid4()).upper()
        
        registro = {
            "id": automatizacion_id,
            "pedido_id": pedido_id,
            "server_id": server_id,
            "empresa_id": empresa_id,
            "empresa_nombre": empresa_nombre,
            "sucursal_id": sucursal_id,
            "sucursal_nombre": sucursal_nombre,
            "almacen_id": almacen_id,
            "almacen_nombre": almacen_nombre,
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre,
            "origen_sistema": origen_sistema,
            "estado": EstadoAutomatizacion.PEDIDO_DETECTADO.value,
            "fecha_pedido": fecha_pedido.isoformat(),
            "fecha_inicio_periodo": fecha_inicio_periodo.isoformat(),
            "fecha_fin_periodo": fecha_fin_periodo.isoformat(),
            "dias_periodo_analisis": self.DIAS_PERIODO_ANALISIS,
            "fecha_consumo_inicio": fecha_inicio_periodo.isoformat(),
            "fecha_consumo_fin": fecha_fin_periodo.isoformat(),
            "dias_periodo_consumo": self.DIAS_PERIODO_CONSUMO_DEFAULT,
            "porcentaje_ajuste_consumo": 0.0,
            "inventario_inicial_id": None,
            "inventario_inicial_fecha": None,
            "inventario_final_id": None,
            "inventario_final_fecha": None,
            "tiene_inventario_final": False,
            "fecha_creacion": now.isoformat(),
            "fecha_actualizacion": now.isoformat(),
            "resultado": None,
            "detalle_productos": productos,
            "recomendacion_general": None,
            "total_productos": len(productos),
            "dias_objetivo": dias_objetivo,
            "fecha_envio_gerencia": None,
            "autorizado_gerencia": False,
            "autorizado_por_gerencia": None,
            "fecha_autorizacion_gerencia": None,
            "comentario_gerencia": None,
            "fecha_envio_tesoreria": None,
            "autorizado_tesoreria": False,
            "autorizado_por_tesoreria": None,
            "fecha_autorizacion_tesoreria": None,
            "comentario_tesoreria": None,
            "motivo_rechazo": None,
            "rechazado_por": None,
            "fecha_rechazo": None,
        }
        
        # 1. Buscar inventario inicial
        inv_inicial = self._buscar_inventario_inicial(server_id, almacen_id, fecha_inicio_periodo)
        if inv_inicial:
            registro["inventario_inicial_id"] = inv_inicial.get("folio") or inv_inicial.get("id")
            registro["inventario_inicial_fecha"] = inv_inicial.get("fecha")
        
        # 2. Buscar inventario final
        inv_final = self._buscar_inventario_final(server_id, almacen_id, fecha_pedido)
        
        if not inv_final:
            # SIN INVENTARIO FINAL - DETENER FLUJO
            registro["estado"] = EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value
            registro["tiene_inventario_final"] = False
            registro["resultado"] = json.dumps({
                "mensaje": "Inventario físico requerido",
                "fecha_requerida": fecha_pedido.strftime("%Y-%m-%d"),
                "almacen": almacen_nombre,
                "accion": "Capturar inventario físico del día del pedido"
            })
            
            self._repo.insert_one(registro)
            self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
            self._registrar_bitacora(automatizacion_id, "PENDIENTE_INVENTARIO", usuario_id, {
                "mensaje": "Flujo detenido - sin inventario final"
            })
            
            logger.info(f"[{automatizacion_id}] PENDIENTE_INVENTARIO_FISICO")
            return self._limpiar_respuesta(registro)
        
        # 3. CON INVENTARIO FINAL - EJECUTAR AUDITORÍA
        registro["inventario_final_id"] = inv_final.get("folio") or inv_final.get("id")
        registro["inventario_final_fecha"] = inv_final.get("fecha")
        registro["tiene_inventario_final"] = True
        registro["estado"] = EstadoAutomatizacion.AUDITORIA_EN_PROCESO.value
        
        # 4. Calcular auditoría
        detalle_productos, resumen = self._ejecutar_auditoria(productos, dias_objetivo)
        
        registro["detalle_productos"] = json.dumps(detalle_productos)
        registro["resultado"] = json.dumps(resumen)
        registro["recomendacion_general"] = self._determinar_recomendacion_general(resumen, len(productos))
        
        # 5. Enviar a EN_REVISION_GERENCIA
        registro["estado"] = EstadoAutomatizacion.EN_REVISION_GERENCIA.value
        registro["fecha_envio_gerencia"] = now.isoformat()
        
        self._repo.insert_one(registro)
        self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
        self._registrar_bitacora(automatizacion_id, "AUDITORIA_COMPLETADA", usuario_id, {
            "recomendacion": registro["recomendacion_general"],
            "criticos": resumen.get("criticos", 0),
            "faltantes": resumen.get("faltantes", 0)
        })
        
        logger.info(f"[{automatizacion_id}] EN_REVISION_GERENCIA - {registro['recomendacion_general']}")
        return self._limpiar_respuesta(registro)
    
    # =========================================================================
    # FLUJO AUTORIZACIÓN GERENCIA
    # =========================================================================
    
    def autorizar_gerencia(
        self,
        automatizacion_id: str,
        usuario_id: str,
        usuario_rol: str,
        accion: str,
        comentario: str = "",
        nuevo_dias_objetivo: int = None
    ) -> Dict:
        """Autorización de Gerencia - SQL."""
        roles_permitidos = ["Gerente", "Director", "Administrador"]
        if usuario_rol not in roles_permitidos:
            return {"success": False, "error": "Solo Gerencia puede autorizar"}
        
        registro = self.obtener_automatizacion(automatizacion_id)
        if not registro:
            return {"success": False, "error": "No encontrado"}
        
        if registro["estado"] != EstadoAutomatizacion.EN_REVISION_GERENCIA.value:
            return {"success": False, "error": f"Estado inválido: {registro['estado']}"}
        
        now = datetime.now(timezone.utc)
        update_data = {"fecha_actualizacion": now.isoformat()}
        
        if accion == "aprobar":
            update_data["estado"] = EstadoAutomatizacion.PENDIENTE_TESORERIA.value
            update_data["autorizado_gerencia"] = True
            update_data["autorizado_por_gerencia"] = usuario_id
            update_data["fecha_autorizacion_gerencia"] = now.isoformat()
            update_data["comentario_gerencia"] = comentario
            update_data["fecha_envio_tesoreria"] = now.isoformat()
            
            self._repo.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "AUTORIZADO_GERENCIA", usuario_id, {"comentario": comentario})
            
            return {"success": True, "estado": EstadoAutomatizacion.PENDIENTE_TESORERIA.value}
        
        elif accion == "rechazar":
            update_data["estado"] = EstadoAutomatizacion.RECHAZADO.value
            update_data["motivo_rechazo"] = comentario
            update_data["rechazado_por"] = usuario_id
            update_data["fecha_rechazo"] = now.isoformat()
            
            self._repo.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "RECHAZADO_GERENCIA", usuario_id, {"motivo": comentario})
            
            return {"success": True, "estado": EstadoAutomatizacion.RECHAZADO.value}
        
        elif accion == "ajuste" and nuevo_dias_objetivo:
            return self.modificar_dias_objetivo(automatizacion_id, nuevo_dias_objetivo, usuario_id, usuario_rol, comentario)
        
        return {"success": False, "error": "Acción inválida"}
    
    # =========================================================================
    # FLUJO AUTORIZACIÓN TESORERÍA
    # =========================================================================
    
    def autorizar_tesoreria(
        self,
        automatizacion_id: str,
        usuario_id: str,
        usuario_rol: str,
        accion: str,
        comentario: str = ""
    ) -> Dict:
        """Autorización Final de Tesorería - SQL."""
        roles_permitidos = ["Tesoreria", "Director", "Administrador"]
        if usuario_rol not in roles_permitidos:
            return {"success": False, "error": "Solo Tesorería puede autorizar"}
        
        registro = self.obtener_automatizacion(automatizacion_id)
        if not registro:
            return {"success": False, "error": "No encontrado"}
        
        if registro["estado"] != EstadoAutomatizacion.PENDIENTE_TESORERIA.value:
            return {"success": False, "error": f"Estado inválido: {registro['estado']}"}
        
        now = datetime.now(timezone.utc)
        update_data = {"fecha_actualizacion": now.isoformat()}
        
        if accion == "aprobar":
            update_data["estado"] = EstadoAutomatizacion.APROBADO.value
            update_data["autorizado_tesoreria"] = True
            update_data["autorizado_por_tesoreria"] = usuario_id
            update_data["fecha_autorizacion_tesoreria"] = now.isoformat()
            update_data["comentario_tesoreria"] = comentario
            
            self._repo.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "APROBADO_FINAL", usuario_id, {"comentario": comentario})
            self._generar_manual_operativo(automatizacion_id)
            
            return {"success": True, "estado": EstadoAutomatizacion.APROBADO.value}
        
        elif accion == "rechazar":
            update_data["estado"] = EstadoAutomatizacion.RECHAZADO.value
            update_data["motivo_rechazo"] = comentario
            update_data["rechazado_por"] = usuario_id
            update_data["fecha_rechazo"] = now.isoformat()
            
            self._repo.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "RECHAZADO_TESORERIA", usuario_id, {"motivo": comentario})
            self._generar_manual_operativo(automatizacion_id)
            
            return {"success": True, "estado": EstadoAutomatizacion.RECHAZADO.value}
        
        return {"success": False, "error": "Acción inválida"}
    
    # =========================================================================
    # MODIFICAR DÍAS OBJETIVO
    # =========================================================================
    
    def modificar_dias_objetivo(
        self,
        automatizacion_id: str,
        nuevo_dias_objetivo: int,
        usuario_id: str,
        usuario_rol: str,
        motivo: str = ""
    ) -> Dict:
        """Modifica días objetivo y recalcula - SQL."""
        roles_permitidos = ["Gerente", "Director", "Administrador"]
        if usuario_rol not in roles_permitidos:
            return {"success": False, "error": "Solo Gerencia puede modificar"}
        
        if nuevo_dias_objetivo < 1 or nuevo_dias_objetivo > 90:
            return {"success": False, "error": "Días objetivo debe estar entre 1 y 90"}
        
        registro = self.obtener_automatizacion(automatizacion_id)
        if not registro:
            return {"success": False, "error": "No encontrado"}
        
        dias_anterior = registro.get("dias_objetivo", self.DIAS_OBJETIVO_DEFAULT)
        porcentaje_ajuste = registro.get("porcentaje_ajuste_consumo", 0.0)
        
        if dias_anterior == nuevo_dias_objetivo:
            return {"success": True, "mensaje": "Sin cambios"}
        
        # Recalcular detalle
        detalle_anterior = registro.get("detalle_productos", [])
        if isinstance(detalle_anterior, str):
            try:
                detalle_anterior = json.loads(detalle_anterior)
            except:
                detalle_anterior = []
        
        detalle_nuevo = []
        resumen = {"criticos": 0, "faltantes": 0, "optimos": 0, "sobrantes": 0, "total_pedido_optimo": 0}
        
        for prod in detalle_anterior:
            resultado_prod = self._recalcular_producto(prod, nuevo_dias_objetivo, porcentaje_ajuste)
            detalle_nuevo.append(resultado_prod)
            
            estado = resultado_prod.get("estado", "")
            if estado == EstadoProducto.CRITICO.value:
                resumen["criticos"] += 1
            elif estado == EstadoProducto.FALTANTE.value:
                resumen["faltantes"] += 1
            elif estado == EstadoProducto.OPTIMO.value:
                resumen["optimos"] += 1
            else:
                resumen["sobrantes"] += 1
            resumen["total_pedido_optimo"] += resultado_prod.get("pedido_optimo", 0)
        
        resumen["porcentaje_ajuste_consumo"] = porcentaje_ajuste
        recomendacion_general = self._determinar_recomendacion_general(resumen, len(detalle_nuevo))
        
        now = datetime.now(timezone.utc)
        
        self._registrar_bitacora(automatizacion_id, "CAMBIO_DIAS_OBJETIVO", usuario_id, {
            "dias_anterior": dias_anterior,
            "dias_nuevo": nuevo_dias_objetivo,
            "motivo": motivo,
            "recomendacion_anterior": registro.get("recomendacion_general"),
            "recomendacion_nueva": recomendacion_general
        })
        
        self._repo.update_one(
            {"id": automatizacion_id},
            {"$set": {
                "dias_objetivo": nuevo_dias_objetivo,
                "detalle_productos": json.dumps(detalle_nuevo),
                "resultado": json.dumps(resumen),
                "recomendacion_general": recomendacion_general,
                "fecha_actualizacion": now.isoformat(),
            }}
        )
        
        return {
            "success": True,
            "dias_objetivo_anterior": dias_anterior,
            "dias_objetivo_nuevo": nuevo_dias_objetivo,
            "resultado": resumen,
            "recomendacion_general": recomendacion_general,
            "recalculado": True
        }
    
    # =========================================================================
    # CONSULTAS SQL
    # =========================================================================
    
    def listar_automatizaciones(
        self,
        server_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        estado: Optional[str] = None,
        limite: int = 50
    ) -> List[Dict]:
        """Lista automatizaciones - SQL."""
        filtro = {}
        if server_id:
            filtro["server_id"] = server_id
        if sucursal_id:
            filtro["sucursal_id"] = sucursal_id
        if estado:
            filtro["estado"] = estado
        
        cursor = self._repo.find(filtro).sort("fecha_creacion", -1).limit(limite)
        return [self._limpiar_respuesta(doc) for doc in cursor]
    
    def obtener_automatizacion(self, automatizacion_id: str) -> Optional[Dict]:
        """Obtiene una automatización - SQL."""
        doc = self._repo.find_one({"id": automatizacion_id})
        return self._limpiar_respuesta(doc) if doc else None
    
    def obtener_kpis(self, server_id: Optional[str] = None) -> Dict:
        """KPIs de automatizaciones - SQL."""
        filtro = {"server_id": server_id} if server_id else {}
        
        pipeline = [
            {"$match": filtro},
            {"$group": {"_id": "$estado", "count": {"$sum": 1}}},
        ]
        
        resultados = list(self._repo.aggregate(pipeline))
        
        kpis = {
            "total": 0,
            "pendientes_inventario": 0,
            "en_proceso": 0,
            "pendientes_revision": 0,
            "pendientes_tesoreria": 0,
            "aprobados": 0,
            "rechazados": 0,
        }
        
        for r in resultados:
            estado = r.get("_id", "")
            count = r.get("count", 0)
            kpis["total"] += count
            
            if estado == EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value:
                kpis["pendientes_inventario"] = count
            elif estado == EstadoAutomatizacion.AUDITORIA_EN_PROCESO.value:
                kpis["en_proceso"] = count
            elif estado == EstadoAutomatizacion.EN_REVISION_GERENCIA.value:
                kpis["pendientes_revision"] = count
            elif estado == EstadoAutomatizacion.PENDIENTE_TESORERIA.value:
                kpis["pendientes_tesoreria"] = count
            elif estado == EstadoAutomatizacion.APROBADO.value:
                kpis["aprobados"] = count
            elif estado == EstadoAutomatizacion.RECHAZADO.value:
                kpis["rechazados"] = count
        
        return kpis
    
    # =========================================================================
    # AUDITORÍA Y CÁLCULOS
    # =========================================================================
    
    def _ejecutar_auditoria(self, productos: List[Dict], dias_objetivo: int) -> tuple:
        """Ejecuta auditoría sobre productos."""
        detalle = []
        resumen = {"criticos": 0, "faltantes": 0, "optimos": 0, "sobrantes": 0, "total_pedido_optimo": 0}
        
        for prod in productos:
            resultado = self._auditar_producto(prod, dias_objetivo)
            detalle.append(resultado)
            
            estado = resultado.get("estado", "")
            if estado == EstadoProducto.CRITICO.value:
                resumen["criticos"] += 1
            elif estado == EstadoProducto.FALTANTE.value:
                resumen["faltantes"] += 1
            elif estado == EstadoProducto.OPTIMO.value:
                resumen["optimos"] += 1
            else:
                resumen["sobrantes"] += 1
            
            resumen["total_pedido_optimo"] += resultado.get("pedido_optimo", 0)
        
        return detalle, resumen
    
    def _auditar_producto(self, producto: Dict, dias_objetivo: int) -> Dict:
        """Audita un producto individual."""
        inv_final = producto.get("inventario_final", 0)
        consumo_diario = producto.get("consumo_diario", 0)
        
        if consumo_diario <= 0:
            dias_inventario = 999
        else:
            dias_inventario = inv_final / consumo_diario
        
        if dias_inventario <= 0:
            estado = EstadoProducto.CRITICO.value
            recomendacion = Recomendacion.URGENTE.value
        elif dias_inventario < dias_objetivo:
            estado = EstadoProducto.FALTANTE.value
            recomendacion = Recomendacion.COMPRAR.value
        elif dias_inventario <= dias_objetivo * (1 + self.TOLERANCIA_OPTIMO):
            estado = EstadoProducto.OPTIMO.value
            recomendacion = Recomendacion.NO_COMPRAR.value
        else:
            estado = EstadoProducto.SOBRANTE.value
            recomendacion = Recomendacion.REVISAR.value
        
        inv_optimo = consumo_diario * dias_objetivo
        pedido_optimo = max(0, inv_optimo - inv_final)
        
        return {
            **producto,
            "dias_inventario": round(dias_inventario, 1),
            "estado": estado,
            "recomendacion": recomendacion,
            "inventario_optimo": round(inv_optimo, 2),
            "pedido_optimo": round(pedido_optimo, 2),
        }
    
    def _recalcular_producto(self, producto: Dict, nuevo_dias_objetivo: int, porcentaje_ajuste: float) -> Dict:
        """Recalcula un producto con nuevos parámetros."""
        consumo_base = producto.get("consumo_diario", 0)
        consumo_ajustado = consumo_base * (1 + porcentaje_ajuste / 100)
        producto_copia = {**producto, "consumo_diario": consumo_ajustado}
        return self._auditar_producto(producto_copia, nuevo_dias_objetivo)
    
    def _determinar_recomendacion_general(self, resumen: Dict, total: int) -> str:
        """Determina recomendación general basada en resumen."""
        if resumen.get("criticos", 0) > 0:
            return Recomendacion.URGENTE.value
        if resumen.get("faltantes", 0) > total * 0.3:
            return Recomendacion.COMPRAR.value
        if resumen.get("sobrantes", 0) > total * 0.5:
            return Recomendacion.REVISAR.value
        return Recomendacion.NO_COMPRAR.value
    
    # =========================================================================
    # INVENTARIOS (SQL)
    # =========================================================================
    
    def _buscar_inventario_inicial(
        self,
        server_id: str,
        almacen_id: str,
        fecha_inicio_periodo: datetime
    ) -> Optional[Dict]:
        """Busca inventario inicial más cercano - SQL."""
        fecha_limite = fecha_inicio_periodo - timedelta(days=30)
        
        return self._inv_repo.find_one({
            "server_id": server_id,
            "almacen_id": almacen_id,
            "fecha": {
                "$gte": fecha_limite.isoformat(),
                "$lte": fecha_inicio_periodo.isoformat()
            }
        })
    
    def _buscar_inventario_final(
        self,
        server_id: str,
        almacen_id: str,
        fecha_pedido: datetime
    ) -> Optional[Dict]:
        """Busca inventario final del día del pedido - SQL."""
        fecha_inicio = fecha_pedido.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = fecha_pedido.replace(hour=23, minute=59, second=59)
        
        return self._inv_repo.find_one({
            "server_id": server_id,
            "almacen_id": almacen_id,
            "fecha": {
                "$gte": fecha_inicio.isoformat(),
                "$lte": fecha_fin.isoformat()
            }
        })
    
    # =========================================================================
    # BITÁCORA Y REGISTRO
    # =========================================================================
    
    def _marcar_pedido_procesado(self, server_id: str, pedido_folio: str, origen: str, automatizacion_id: str):
        """Marca pedido como procesado - SQL."""
        self._pedidos_repo.insert_one({
            "id": str(uuid.uuid4()).upper(),
            "server_id": server_id,
            "pedido_folio": pedido_folio,
            "origen": origen,
            "automatizacion_id": automatizacion_id,
            "fecha_proceso": datetime.now(timezone.utc).isoformat()
        })
    
    def _registrar_bitacora(self, automatizacion_id: str, accion: str, usuario_id: str, detalle: Dict):
        """Registra en bitácora - SQL."""
        self._bitacora_repo.insert_one({
            "id": str(uuid.uuid4()).upper(),
            "automatizacion_id": automatizacion_id,
            "accion": accion,
            "usuario_id": usuario_id,
            "detalle": json.dumps(detalle, ensure_ascii=False),
            "fecha": datetime.now(timezone.utc).isoformat()
        })
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _limpiar_respuesta(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Limpia respuesta para API."""
        if not doc:
            return None
        
        doc.pop("_id", None)
        
        # Deserializar JSON si es necesario
        for field in ["detalle_productos", "resultado"]:
            if field in doc and isinstance(doc[field], str):
                try:
                    doc[field] = json.loads(doc[field])
                except:
                    pass
        
        return doc
    
    def _generar_manual_operativo(self, automatizacion_id: str) -> Optional[str]:
        """Genera Manual Operativo al estado final."""
        if not MANUALES_DISPONIBLE or trigger_generar_manual_sync is None:
            logger.warning("Módulo de manuales operativos no disponible")
            return None
        
        try:
            manual_id = trigger_generar_manual_sync(self.db, automatizacion_id, modulo="compras")
            if manual_id:
                logger.info(f"Manual operativo generado: {manual_id}")
                self._registrar_bitacora(automatizacion_id, "MANUAL_GENERADO", "sistema", {
                    "manual_id": manual_id, "formato": "cienfuegos"
                })
            return manual_id
        except Exception as e:
            logger.error(f"Error generando manual operativo: {e}")
            return None


def get_automatizacion_compras_service(db=None) -> AutomatizacionComprasService:
    """Factory function."""
    return AutomatizacionComprasService(db)
