"""
EDARSA HUB - Automatización Operativa de Compras
================================================
FASE 1: Detección y auditoría automática de pedidos.

Flujo Estados (EXACTO):
1. PEDIDO_DETECTADO
2. PENDIENTE_INVENTARIO_FISICO (si no hay inv. final)
3. AUDITORIA_EN_PROCESO
4. EN_REVISION_GERENCIA
5. PENDIENTE_TESORERIA
6. APROBADO / RECHAZADO

FASE 2: Al llegar a APROBADO/RECHAZADO se genera automáticamente
un Manual Operativo en formato Cienfuegos.
"""

import logging
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
    """Estados EXACTOS del flujo - NO INVENTAR MÁS."""
    PEDIDO_DETECTADO = "PEDIDO_DETECTADO"
    PENDIENTE_INVENTARIO_FISICO = "PENDIENTE_INVENTARIO_FISICO"
    AUDITORIA_EN_PROCESO = "AUDITORIA_EN_PROCESO"
    EN_REVISION_GERENCIA = "EN_REVISION_GERENCIA"
    PENDIENTE_TESORERIA = "PENDIENTE_TESORERIA"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


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
    COLLECTION_BITACORA = "automatizaciones_bitacora"
    COLLECTION_PEDIDOS_PROCESADOS = "pedidos_procesados_automatizacion"
    
    DIAS_PERIODO_ANALISIS = 15  # Ventana fija operativa
    DIAS_PERIODO_CONSUMO_DEFAULT = 15  # Ventana estadística default
    DIAS_OBJETIVO_DEFAULT = 10
    TOLERANCIA_OPTIMO = 0.20   # ±20%
    
    def __init__(self, db):
        self.db = db
        self._is_stub = self._check_is_stub(db)
        self.collection = db[self.COLLECTION]
        self.bitacora = db[self.COLLECTION_BITACORA]
        self.pedidos_procesados = db[self.COLLECTION_PEDIDOS_PROCESADOS]
    
    def _check_is_stub(self, db) -> bool:
        """Verifica si estamos usando StubDatabase."""
        if db is None:
            return True
        try:
            from core.mongo_stub import StubDatabase
            return isinstance(db, StubDatabase)
        except ImportError:
            return False
    
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
        """
        Procesa pedido capturado - FLUJO COMPLETO.
        
        FASE 4.1: Ahora incluye contexto de Unidad de Negocio (empresa)
        
        1. Validar que no esté ya procesado (anti-duplicado)
        2. Determinar ventana 15 días
        3. Buscar inventario inicial más cercano válido
        4. Buscar inventario final del día del pedido
        5. Sin inv. final → PENDIENTE_INVENTARIO_FISICO + notificar + detener
        6. Con inv. final → auditoría + EN_REVISION_GERENCIA
        """
        # CONTROL ANTI-DUPLICADO: Verificar si ya fue procesado
        ya_procesado = self.pedidos_procesados.find_one({
            "server_id": server_id,
            "pedido_folio": pedido_id,
            "origen": origen_sistema
        })
        if ya_procesado:
            # Retornar la automatización existente
            auto_existente = self.collection.find_one(
                {"id": ya_procesado.get("automatizacion_id")},
                {"_id": 0}
            )
            if auto_existente:
                logger.info(f"[{pedido_id}] Ya procesado - retornando existente")
                return auto_existente
        
        now = datetime.now(timezone.utc)
        dias_objetivo = dias_objetivo or self.DIAS_OBJETIVO_DEFAULT
        fecha_pedido = fecha_pedido or now
        
        # Ventana automática 15 días
        fecha_fin_periodo = fecha_pedido
        fecha_inicio_periodo = fecha_pedido - timedelta(days=self.DIAS_PERIODO_ANALISIS)
        
        automatizacion_id = str(uuid.uuid4())
        
        # Registro base - FASE 4.1: Incluye Unidad de Negocio
        # FASE 4.3: Separación periodo operativo vs estadístico
        registro = {
            "id": automatizacion_id,
            "pedido_id": pedido_id,
            "server_id": server_id,
            # FASE 4.1: Contexto de Unidad de Negocio
            "empresa_id": empresa_id,
            "empresa_nombre": empresa_nombre,
            # Ubicación
            "sucursal_id": sucursal_id,
            "sucursal_nombre": sucursal_nombre,
            "almacen_id": almacen_id,
            "almacen_nombre": almacen_nombre,
            # Usuario y origen
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre,
            "origen_sistema": origen_sistema,
            "estado": EstadoAutomatizacion.PEDIDO_DETECTADO.value,
            
            # =========================================================
            # PERIODO OPERATIVO (fechas bloqueadas - no editables)
            # =========================================================
            "fecha_pedido": fecha_pedido.isoformat(),
            "fecha_inicio_periodo": fecha_inicio_periodo.isoformat(),
            "fecha_fin_periodo": fecha_fin_periodo.isoformat(),
            "dias_periodo_analisis": self.DIAS_PERIODO_ANALISIS,
            
            # =========================================================
            # PERIODO ESTADÍSTICO DE CONSUMO (editable por usuario)
            # Separado del periodo operativo para permitir análisis
            # de temporadas comparables (ej: Semana Santa año anterior)
            # =========================================================
            "fecha_consumo_inicio": fecha_inicio_periodo.isoformat(),  # Default = periodo operativo
            "fecha_consumo_fin": fecha_fin_periodo.isoformat(),
            "dias_periodo_consumo": self.DIAS_PERIODO_CONSUMO_DEFAULT,
            
            # =========================================================
            # AJUSTE PORCENTUAL SOBRE CONSUMO
            # Permite ajustar el consumo calculado por factores externos
            # (capacidad diferente, más comensales, etc.)
            # Valor: -100 a +500 (%) - 0 = sin ajuste
            # =========================================================
            "porcentaje_ajuste_consumo": 0.0,
            
            # Inventarios
            "inventario_inicial_id": None,
            "inventario_inicial_fecha": None,
            "inventario_final_id": None,
            "inventario_final_fecha": None,
            "tiene_inventario_final": False,
            # Timestamps
            "fecha_creacion": now.isoformat(),
            "fecha_actualizacion": now.isoformat(),
            # Resultado auditoría
            "resultado": None,
            "detalle_productos": [],
            "recomendacion_general": None,
            "total_productos": len(productos),
            "dias_objetivo": dias_objetivo,
            # Flujo autorización
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
        
        # 1. Buscar inventario inicial más cercano
        inv_inicial = self._buscar_inventario_inicial(
            server_id, almacen_id, fecha_inicio_periodo
        )
        if inv_inicial:
            registro["inventario_inicial_id"] = inv_inicial.get("folio") or inv_inicial.get("id")
            registro["inventario_inicial_fecha"] = inv_inicial.get("fecha")
        
        # 2. Buscar inventario final del día del pedido
        inv_final = self._buscar_inventario_final(
            server_id, almacen_id, fecha_pedido
        )
        
        if not inv_final:
            # SIN INVENTARIO FINAL - DETENER FLUJO
            registro["estado"] = EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value
            registro["tiene_inventario_final"] = False
            registro["resultado"] = {
                "mensaje": "Inventario físico requerido",
                "fecha_requerida": fecha_pedido.strftime("%Y-%m-%d"),
                "almacen": almacen_nombre,
                "accion": "Capturar inventario físico del día del pedido"
            }
            
            self.collection.insert_one(registro)
            self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
            self._notificar_falta_inventario(registro)
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
        
        # 4. Calcular auditoría por producto
        detalle_productos, resumen = self._ejecutar_auditoria(productos, dias_objetivo)
        
        registro["detalle_productos"] = detalle_productos
        registro["resultado"] = resumen
        registro["recomendacion_general"] = self._determinar_recomendacion_general(resumen, len(productos))
        
        # 5. Enviar a EN_REVISION_GERENCIA
        registro["estado"] = EstadoAutomatizacion.EN_REVISION_GERENCIA.value
        registro["fecha_envio_gerencia"] = now.isoformat()
        
        self.collection.insert_one(registro)
        self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
        self._registrar_bitacora(automatizacion_id, "AUDITORIA_COMPLETADA", usuario_id, {
            "recomendacion": registro["recomendacion_general"],
            "criticos": resumen["criticos"],
            "faltantes": resumen["faltantes"]
        })
        self._notificar_gerencia(registro)
        
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
        accion: str,  # "aprobar", "rechazar", "ajuste"
        comentario: str = "",
        nuevo_dias_objetivo: int = None
    ) -> Dict:
        """
        Autorización de Gerencia.
        - aprobar → PENDIENTE_TESORERIA
        - rechazar → RECHAZADO
        - ajuste → recalcular y mantener EN_REVISION_GERENCIA
        """
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
            
            self.collection.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "AUTORIZADO_GERENCIA", usuario_id, {"comentario": comentario})
            self._notificar_tesoreria(registro)
            
            return {"success": True, "estado": EstadoAutomatizacion.PENDIENTE_TESORERIA.value}
        
        elif accion == "rechazar":
            update_data["estado"] = EstadoAutomatizacion.RECHAZADO.value
            update_data["motivo_rechazo"] = comentario
            update_data["rechazado_por"] = usuario_id
            update_data["fecha_rechazo"] = now.isoformat()
            
            self.collection.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "RECHAZADO_GERENCIA", usuario_id, {"motivo": comentario})
            
            return {"success": True, "estado": EstadoAutomatizacion.RECHAZADO.value}
        
        elif accion == "ajuste" and nuevo_dias_objetivo:
            # Recalcular con nuevo días objetivo
            return self.modificar_dias_objetivo(
                automatizacion_id, nuevo_dias_objetivo, usuario_id, usuario_rol, comentario
            )
        
        return {"success": False, "error": "Acción inválida"}
    
    # =========================================================================
    # FLUJO AUTORIZACIÓN TESORERÍA
    # =========================================================================
    
    def autorizar_tesoreria(
        self,
        automatizacion_id: str,
        usuario_id: str,
        usuario_rol: str,
        accion: str,  # "aprobar", "rechazar"
        comentario: str = ""
    ) -> Dict:
        """
        Autorización Final de Tesorería.
        - aprobar → APROBADO
        - rechazar → RECHAZADO
        """
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
            
            self.collection.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "APROBADO_FINAL", usuario_id, {"comentario": comentario})
            
            # TRIGGER: Generar manual operativo al aprobar
            self._generar_manual_operativo(automatizacion_id)
            
            return {"success": True, "estado": EstadoAutomatizacion.APROBADO.value}
        
        elif accion == "rechazar":
            update_data["estado"] = EstadoAutomatizacion.RECHAZADO.value
            update_data["motivo_rechazo"] = comentario
            update_data["rechazado_por"] = usuario_id
            update_data["fecha_rechazo"] = now.isoformat()
            
            self.collection.update_one({"id": automatizacion_id}, {"$set": update_data})
            self._registrar_bitacora(automatizacion_id, "RECHAZADO_TESORERIA", usuario_id, {"motivo": comentario})
            
            # TRIGGER: Generar manual operativo al rechazar
            self._generar_manual_operativo(automatizacion_id)
            
            return {"success": True, "estado": EstadoAutomatizacion.RECHAZADO.value}
        
        return {"success": False, "error": "Acción inválida"}
    
    # =========================================================================
    # MODIFICAR DÍAS OBJETIVO (RECALCULA)
    # =========================================================================
    
    def modificar_dias_objetivo(
        self,
        automatizacion_id: str,
        nuevo_dias_objetivo: int,
        usuario_id: str,
        usuario_rol: str,
        motivo: str = ""
    ) -> Dict:
        """Modifica días objetivo y recalcula todo."""
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
        
        # Recalcular detalle con porcentaje de ajuste existente
        detalle_anterior = registro.get("detalle_productos", [])
        detalle_nuevo = []
        resumen = {"criticos": 0, "faltantes": 0, "optimos": 0, "sobrantes": 0, "total_pedido_optimo": 0}
        
        for prod in detalle_anterior:
            resultado_prod = self._recalcular_producto(prod, nuevo_dias_objetivo, porcentaje_ajuste)
            detalle_nuevo.append(resultado_prod)
            
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
        
        resumen["porcentaje_ajuste_consumo"] = porcentaje_ajuste
        recomendacion_general = self._determinar_recomendacion_general(resumen, len(detalle_nuevo))
        
        now = datetime.now(timezone.utc)
        
        # Bitácora
        self._registrar_bitacora(automatizacion_id, "CAMBIO_DIAS_OBJETIVO", usuario_id, {
            "dias_anterior": dias_anterior,
            "dias_nuevo": nuevo_dias_objetivo,
            "motivo": motivo,
            "recomendacion_anterior": registro.get("recomendacion_general"),
            "recomendacion_nueva": recomendacion_general
        })
        
        # Update
        self.collection.update_one(
            {"id": automatizacion_id},
            {"$set": {
                "dias_objetivo": nuevo_dias_objetivo,
                "detalle_productos": detalle_nuevo,
                "resultado": resumen,
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
    
    def modificar_parametros_consumo(
        self,
        automatizacion_id: str,
        usuario_id: str,
        fecha_consumo_inicio: str = None,
        fecha_consumo_fin: str = None,
        porcentaje_ajuste: float = None,
        motivo: str = ""
    ) -> Dict:
        """
        FASE 4.3: Modifica periodo estadístico y/o ajuste porcentual de consumo.
        
        Permite:
        - Cambiar el periodo estadístico (ej: usar mismo periodo año anterior)
        - Aplicar ajuste porcentual sobre consumo (ej: +10% por mayor capacidad)
        
        Args:
            automatizacion_id: ID de la automatización
            usuario_id: ID del usuario que hace el cambio
            fecha_consumo_inicio: Nueva fecha inicio periodo estadístico (opcional)
            fecha_consumo_fin: Nueva fecha fin periodo estadístico (opcional)
            porcentaje_ajuste: Nuevo porcentaje de ajuste (-100 a +500) (opcional)
            motivo: Motivo del cambio
            
        Returns:
            Dict con resultado y datos recalculados
        """
        registro = self.obtener_automatizacion(automatizacion_id)
        if not registro:
            return {"success": False, "error": "No encontrado"}
        
        # Valores actuales
        ajuste_anterior = registro.get("porcentaje_ajuste_consumo", 0.0)
        fecha_consumo_inicio_anterior = registro.get("fecha_consumo_inicio")
        fecha_consumo_fin_anterior = registro.get("fecha_consumo_fin")
        dias_objetivo = registro.get("dias_objetivo", self.DIAS_OBJETIVO_DEFAULT)
        
        # Determinar nuevos valores
        nuevo_ajuste = porcentaje_ajuste if porcentaje_ajuste is not None else ajuste_anterior
        nueva_fecha_inicio = fecha_consumo_inicio or fecha_consumo_inicio_anterior
        nueva_fecha_fin = fecha_consumo_fin or fecha_consumo_fin_anterior
        
        # Validar porcentaje (-100% a +500%)
        if nuevo_ajuste < -100 or nuevo_ajuste > 500:
            return {
                "success": False,
                "error": "Porcentaje de ajuste debe estar entre -100% y +500%"
            }
        
        # Verificar si hay cambios
        cambio_ajuste = nuevo_ajuste != ajuste_anterior
        cambio_periodo = (
            nueva_fecha_inicio != fecha_consumo_inicio_anterior or
            nueva_fecha_fin != fecha_consumo_fin_anterior
        )
        
        if not cambio_ajuste and not cambio_periodo:
            return {"success": True, "mensaje": "Sin cambios"}
        
        # Recalcular detalle con nuevo ajuste
        detalle_anterior = registro.get("detalle_productos", [])
        detalle_nuevo = []
        resumen = {
            "criticos": 0, "faltantes": 0, "optimos": 0, 
            "sobrantes": 0, "total_pedido_optimo": 0
        }
        
        for prod in detalle_anterior:
            resultado_prod = self._recalcular_producto(prod, dias_objetivo, nuevo_ajuste)
            detalle_nuevo.append(resultado_prod)
            
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
        
        resumen["porcentaje_ajuste_consumo"] = nuevo_ajuste
        recomendacion_general = self._determinar_recomendacion_general(resumen, len(detalle_nuevo))
        
        now = datetime.now(timezone.utc)
        
        # Bitácora
        self._registrar_bitacora(automatizacion_id, "CAMBIO_PARAMETROS_CONSUMO", usuario_id, {
            "cambios": {
                "ajuste": {
                    "anterior": ajuste_anterior,
                    "nuevo": nuevo_ajuste
                } if cambio_ajuste else None,
                "periodo_estadistico": {
                    "fecha_inicio_anterior": fecha_consumo_inicio_anterior,
                    "fecha_fin_anterior": fecha_consumo_fin_anterior,
                    "fecha_inicio_nuevo": nueva_fecha_inicio,
                    "fecha_fin_nuevo": nueva_fecha_fin
                } if cambio_periodo else None
            },
            "motivo": motivo,
            "recomendacion_anterior": registro.get("recomendacion_general"),
            "recomendacion_nueva": recomendacion_general
        })
        
        # Calcular días del periodo estadístico
        dias_periodo = 0
        if nueva_fecha_inicio and nueva_fecha_fin:
            try:
                from datetime import datetime as dt
                f_inicio = dt.fromisoformat(nueva_fecha_inicio.replace('Z', '+00:00'))
                f_fin = dt.fromisoformat(nueva_fecha_fin.replace('Z', '+00:00'))
                dias_periodo = (f_fin - f_inicio).days
            except Exception:
                dias_periodo = self.DIAS_PERIODO_CONSUMO_DEFAULT
        
        # Update
        self.collection.update_one(
            {"id": automatizacion_id},
            {"$set": {
                "fecha_consumo_inicio": nueva_fecha_inicio,
                "fecha_consumo_fin": nueva_fecha_fin,
                "dias_periodo_consumo": dias_periodo,
                "porcentaje_ajuste_consumo": nuevo_ajuste,
                "detalle_productos": detalle_nuevo,
                "resultado": resumen,
                "recomendacion_general": recomendacion_general,
                "fecha_actualizacion": now.isoformat(),
            }}
        )
        
        return {
            "success": True,
            "cambios": {
                "porcentaje_ajuste": {
                    "anterior": ajuste_anterior,
                    "nuevo": nuevo_ajuste
                },
                "periodo_estadistico": {
                    "fecha_inicio": nueva_fecha_inicio,
                    "fecha_fin": nueva_fecha_fin,
                    "dias": dias_periodo
                }
            },
            "resultado": resumen,
            "recomendacion_general": recomendacion_general,
            "recalculado": True
        }
    
    # =========================================================================
    # CÁLCULOS AUDITORÍA
    # =========================================================================
    
    def _ejecutar_auditoria(
        self,
        productos: List[Dict],
        dias_objetivo: int,
        porcentaje_ajuste: float = 0.0
    ) -> tuple:
        """
        Ejecuta auditoría completa por producto.
        
        FASE 4.3: Incluye porcentaje de ajuste sobre consumo
        """
        detalle = []
        resumen = {"criticos": 0, "faltantes": 0, "optimos": 0, "sobrantes": 0, "total_pedido_optimo": 0}
        
        for prod in productos:
            resultado = self._calcular_estado_producto(prod, dias_objetivo, porcentaje_ajuste)
            detalle.append(resultado)
            
            estado = resultado["estado"]
            if estado == EstadoProducto.CRITICO.value:
                resumen["criticos"] += 1
            elif estado == EstadoProducto.FALTANTE.value:
                resumen["faltantes"] += 1
            elif estado == EstadoProducto.OPTIMO.value:
                resumen["optimos"] += 1
            else:
                resumen["sobrantes"] += 1
            resumen["total_pedido_optimo"] += resultado.get("pedido_optimo", 0)
        
        # FASE 4.3: Agregar porcentaje de ajuste al resumen
        resumen["porcentaje_ajuste_consumo"] = porcentaje_ajuste
        
        return detalle, resumen
    
    def _calcular_estado_producto(
        self,
        producto: Dict,
        dias_objetivo: int,
        porcentaje_ajuste: float = 0.0
    ) -> Dict:
        """
        Calcula estado y recomendación por producto.
        
        FASE 4.3: Incluye ajuste porcentual sobre consumo
        
        - consumo_promedio_base: Consumo calculado del periodo estadístico
        - consumo_promedio_ajustado: Consumo base * (1 + porcentaje_ajuste/100)
        - dias_inventario = existencia_fisica / consumo_ajustado
        - pedido_optimo = (dias_objetivo * consumo_ajustado) - existencia_fisica
        """
        existencia = float(producto.get("existencia_fisica", 0) or 0)
        consumo_base = float(producto.get("consumo_promedio", 0) or 0)
        cantidad_pedida = float(producto.get("cantidad_pedida", 0) or 0)
        
        # FASE 4.3: Aplicar ajuste porcentual
        factor_ajuste = 1 + (porcentaje_ajuste / 100.0)
        consumo_ajustado = consumo_base * factor_ajuste
        
        # Días inventario CON consumo ajustado
        if consumo_ajustado > 0:
            dias_inventario = existencia / consumo_ajustado
        else:
            dias_inventario = 999 if existencia > 0 else 0
        
        # Estado
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
        
        # Pedido óptimo CON consumo ajustado
        pedido_optimo = (dias_objetivo * consumo_ajustado) - existencia
        if pedido_optimo < 0:
            pedido_optimo = 0
        
        return {
            "codigo": producto.get("codigo"),
            "nombre": producto.get("nombre"),
            "existencia_fisica": existencia,
            # FASE 4.3: Separar consumo base y ajustado
            "consumo_promedio_base": round(consumo_base, 2),
            "consumo_promedio": round(consumo_ajustado, 2),  # Compatibilidad
            "consumo_promedio_ajustado": round(consumo_ajustado, 2),
            "porcentaje_ajuste_aplicado": porcentaje_ajuste,
            # Indicadores
            "dias_inventario": round(dias_inventario, 1),
            "dias_objetivo": dias_objetivo,
            "estado": estado,
            "recomendacion": recomendacion,
            "cantidad_pedida": cantidad_pedida,
            "pedido_optimo": round(pedido_optimo, 2),
            "diferencia": round(cantidad_pedida - pedido_optimo, 2),
        }
    
    def _recalcular_producto(
        self,
        prod: Dict,
        dias_objetivo: int,
        porcentaje_ajuste: float = 0.0
    ) -> Dict:
        """
        Recalcula con nuevo días objetivo y/o porcentaje de ajuste.
        
        FASE 4.3: Soporta recálculo con ajuste porcentual
        """
        existencia = float(prod.get("existencia_fisica", 0) or 0)
        # Usar consumo base si existe, sino consumo promedio
        consumo_base = float(prod.get("consumo_promedio_base", 0) or prod.get("consumo_promedio", 0) or 0)
        cantidad_pedida = float(prod.get("cantidad_pedida", 0) or 0)
        
        # Aplicar ajuste porcentual
        factor_ajuste = 1 + (porcentaje_ajuste / 100.0)
        consumo_ajustado = consumo_base * factor_ajuste
        
        # Recalcular días inventario
        if consumo_ajustado > 0:
            dias_inventario = existencia / consumo_ajustado
        else:
            dias_inventario = 999 if existencia > 0 else 0
        
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
        
        pedido_optimo = (dias_objetivo * consumo_ajustado) - existencia
        if pedido_optimo < 0:
            pedido_optimo = 0
        
        return {
            "codigo": prod.get("codigo"),
            "nombre": prod.get("nombre"),
            "existencia_fisica": existencia,
            "consumo_promedio_base": round(consumo_base, 2),
            "consumo_promedio": round(consumo_ajustado, 2),
            "consumo_promedio_ajustado": round(consumo_ajustado, 2),
            "porcentaje_ajuste_aplicado": porcentaje_ajuste,
            "dias_inventario": round(dias_inventario, 1),
            "dias_objetivo": dias_objetivo,
            "estado": estado,
            "recomendacion": recomendacion,
            "cantidad_pedida": cantidad_pedida,
            "pedido_optimo": round(pedido_optimo, 2),
            "diferencia": round(cantidad_pedida - pedido_optimo, 2),
        }
    
    def _determinar_recomendacion_general(self, resumen: Dict, total: int) -> str:
        """Determina recomendación general."""
        if resumen["criticos"] > 0:
            return Recomendacion.URGENTE.value
        elif resumen["faltantes"] > 0:
            return Recomendacion.COMPRAR.value
        elif resumen["sobrantes"] > total * 0.5:
            return Recomendacion.REVISAR.value
        return Recomendacion.NO_COMPRAR.value
    
    # =========================================================================
    # BÚSQUEDA INVENTARIOS
    # =========================================================================
    
    def _buscar_inventario_inicial(
        self,
        server_id: str,
        almacen_id: str,
        fecha_inicio_periodo: datetime
    ) -> Optional[Dict]:
        """Busca inventario inicial más cercano (hasta 30 días antes)."""
        if self._is_stub:
            logger.debug("[AUTO_COMPRAS] Modo SQL-only: inventario inicial no disponible")
            return None
        
        fecha_limite = fecha_inicio_periodo - timedelta(days=30)
        
        return self.db.inventarios_fisicos_procesados.find_one(
            {
                "server_id": server_id,
                "almacen_id": almacen_id,
                "fecha": {
                    "$gte": fecha_limite.isoformat(),
                    "$lte": fecha_inicio_periodo.isoformat()
                }
            },
            {"_id": 0},
            sort=[("fecha", -1)]
        )
    
    def _buscar_inventario_final(
        self,
        server_id: str,
        almacen_id: str,
        fecha_pedido: datetime
    ) -> Optional[Dict]:
        """Busca inventario final del día del pedido."""
        if self._is_stub:
            logger.debug("[AUTO_COMPRAS] Modo SQL-only: inventario final no disponible")
            return None
        
        fecha_inicio = fecha_pedido.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = fecha_pedido.replace(hour=23, minute=59, second=59)
        
        return self.db.inventarios_fisicos_procesados.find_one(
            {
                "server_id": server_id,
                "almacen_id": almacen_id,
                "fecha": {
                    "$gte": fecha_inicio.isoformat(),
                    "$lte": fecha_fin.isoformat()
                }
            },
            {"_id": 0},
            sort=[("fecha", -1)]
        )
    
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
        """Lista automatizaciones."""
        filtro = {}
        if server_id:
            filtro["server_id"] = server_id
        if sucursal_id:
            filtro["sucursal_id"] = sucursal_id
        if estado:
            filtro["estado"] = estado
        
        cursor = self.collection.find(filtro, {"_id": 0}).sort("fecha_creacion", -1).limit(limite)
        return list(cursor)
    
    def obtener_automatizacion(self, automatizacion_id: str) -> Optional[Dict]:
        """Obtiene una automatización."""
        return self.collection.find_one({"id": automatizacion_id}, {"_id": 0})
    
    def obtener_kpis(self, server_id: Optional[str] = None) -> Dict:
        """KPIs de automatizaciones."""
        filtro = {"server_id": server_id} if server_id else {}
        
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
            "pendientes_tesoreria": 0,
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
            elif estado == EstadoAutomatizacion.EN_REVISION_GERENCIA.value:
                kpis["pendientes_revision"] = count
            elif estado == EstadoAutomatizacion.PENDIENTE_TESORERIA.value:
                kpis["pendientes_tesoreria"] = count
            elif estado == EstadoAutomatizacion.APROBADO.value:
                kpis["aprobados"] = count
            elif estado == EstadoAutomatizacion.RECHAZADO.value:
                kpis["rechazados"] = count
        
        return kpis
    
    def obtener_bitacora(self, automatizacion_id: str) -> List[Dict]:
        """Obtiene bitácora de cambios."""
        cursor = self.bitacora.find(
            {"automatizacion_id": automatizacion_id},
            {"_id": 0}
        ).sort("fecha", -1)
        return list(cursor)
    
    # =========================================================================
    # AUXILIARES
    # =========================================================================
    
    def _marcar_pedido_procesado(self, server_id: str, pedido_id: str, origen: str, automatizacion_id: str):
        """Marca pedido como procesado."""
        self.pedidos_procesados.update_one(
            {"server_id": server_id, "pedido_folio": pedido_id, "origen": origen},
            {"$set": {
                "automatizacion_id": automatizacion_id,
                "fecha_procesado": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
    
    def _registrar_bitacora(self, automatizacion_id: str, evento: str, usuario_id: str, datos: Dict = None):
        """Registra evento en bitácora."""
        self.bitacora.insert_one({
            "id": str(uuid.uuid4()),
            "automatizacion_id": automatizacion_id,
            "evento": evento,
            "usuario_id": usuario_id,
            "datos": datos or {},
            "fecha": datetime.now(timezone.utc).isoformat()
        })
    
    def _limpiar_respuesta(self, registro: Dict) -> Dict:
        """Limpia _id de MongoDB."""
        if "_id" in registro:
            del registro["_id"]
        return registro
    
    # =========================================================================
    # NOTIFICACIONES (Reutiliza sistema existente)
    # =========================================================================
    
    def _notificar_falta_inventario(self, registro: Dict):
        """Notifica al solicitante que falta inventario."""
        try:
            from modules.fase2_operativo.services.email_service import get_email_service
            service = get_email_service()
            if not service.is_configured():
                return
            
            email = self._obtener_email_usuario(registro["usuario_id"])
            if email:
                service.enviar_email_sync(
                    destinatario=email,
                    asunto="⚠️ Automatización Compras - Inventario Requerido",
                    contenido_html=f"""
                    <h2>Acción Requerida: Inventario Físico</h2>
                    <p>Pedido: <strong>{registro['pedido_id']}</strong></p>
                    <p><strong>Motivo:</strong> No existe inventario físico del día del pedido.</p>
                    <p><strong>Sucursal:</strong> {registro['sucursal_nombre']}</p>
                    <p><strong>Almacén:</strong> {registro['almacen_nombre']}</p>
                    <p>Capture el inventario físico para continuar.</p>
                    """
                )
        except Exception as e:
            logger.error(f"Error notificando falta inventario: {e}")
    
    def _notificar_gerencia(self, registro: Dict):
        """Notifica a Gerencia que hay auditoría lista."""
        try:
            from modules.fase2_operativo.services.email_service import get_email_service
            service = get_email_service()
            if not service.is_configured():
                return
            
            # En modo stub, omitir consultas MongoDB
            if self._is_stub:
                logger.debug("[AUTO_COMPRAS] Modo SQL-only: notificación gerencia omitida")
                return
            
            # Buscar gerentes
            gerentes = list(self.db.users.find(
                {"role": {"$in": ["Gerente", "Director", "Administrador"]}},
                {"_id": 0, "email": 1}
            ))
            
            for g in gerentes[:3]:
                if g.get("email"):
                    service.enviar_email_sync(
                        destinatario=g["email"],
                        asunto=f"Auditoría Compras Lista - {registro['sucursal_nombre']}",
                        contenido_html=self._html_auditoria(registro)
                    )
        except Exception as e:
            logger.error(f"Error notificando gerencia: {e}")
    
    def _notificar_tesoreria(self, registro: Dict):
        """Notifica a Tesorería que Gerencia aprobó."""
        try:
            from modules.fase2_operativo.services.email_service import get_email_service
            service = get_email_service()
            if not service.is_configured():
                return
            
            # En modo stub, omitir consultas MongoDB
            if self._is_stub:
                logger.debug("[AUTO_COMPRAS] Modo SQL-only: notificación tesorería omitida")
                return
            
            # Buscar tesorería
            tesoreros = list(self.db.users.find(
                {"role": {"$in": ["Tesoreria", "Director", "Administrador"]}},
                {"_id": 0, "email": 1}
            ))
            
            for t in tesoreros[:3]:
                if t.get("email"):
                    service.enviar_email_sync(
                        destinatario=t["email"],
                        asunto=f"Compras Autorizada por Gerencia - {registro['sucursal_nombre']}",
                        contenido_html=f"""
                        <h2>Pedido Autorizado por Gerencia</h2>
                        <p>Sucursal: {registro['sucursal_nombre']}</p>
                        <p>Recomendación: <strong>{registro['recomendacion_general']}</strong></p>
                        <p>Requiere autorización final de Tesorería.</p>
                        """
                    )
        except Exception as e:
            logger.error(f"Error notificando tesorería: {e}")
    
    def _html_auditoria(self, registro: Dict) -> str:
        """HTML de auditoría para email."""
        resultado = registro.get("resultado", {})
        return f"""
        <h2>Auditoría Operativa de Compras</h2>
        <p><strong>Sucursal:</strong> {registro['sucursal_nombre']}</p>
        <p><strong>Pedido:</strong> {registro['pedido_id']}</p>
        <p><strong>Recomendación:</strong> <span style="color: red;">{registro['recomendacion_general']}</span></p>
        <h3>Resumen</h3>
        <ul>
            <li>Críticos: {resultado.get('criticos', 0)}</li>
            <li>Faltantes: {resultado.get('faltantes', 0)}</li>
            <li>Óptimos: {resultado.get('optimos', 0)}</li>
            <li>Sobrantes: {resultado.get('sobrantes', 0)}</li>
        </ul>
        <p>Ingrese al sistema para revisar.</p>
        """
    
    def _obtener_email_usuario(self, usuario_id: str) -> str:
        """Obtiene email del usuario."""
        if self._is_stub:
            return ""
        user = self.db.users.find_one({"id": usuario_id}, {"_id": 0, "email": 1})
        return user.get("email", "") if user else ""
    
    def _generar_manual_operativo(self, automatizacion_id: str) -> Optional[str]:
        """
        Genera automáticamente un Manual Operativo (Modelo Cienfuegos)
        cuando el proceso llega a estado final (APROBADO/RECHAZADO).
        
        Returns:
            ID del manual generado o None si error
        """
        if not MANUALES_DISPONIBLE or trigger_generar_manual_sync is None:
            logger.warning("Módulo de manuales operativos no disponible")
            return None
        
        try:
            manual_id = trigger_generar_manual_sync(self.db, automatizacion_id, modulo="compras")
            if manual_id:
                logger.info(f"Manual operativo generado: {manual_id} para automatización {automatizacion_id}")
                # Registrar en bitácora
                self._registrar_bitacora(
                    automatizacion_id, 
                    "MANUAL_GENERADO", 
                    "sistema", 
                    {"manual_id": manual_id, "formato": "cienfuegos"}
                )
            return manual_id
        except Exception as e:
            logger.error(f"Error generando manual operativo: {e}")
            return None


def get_automatizacion_compras_service(db) -> AutomatizacionComprasService:
    """Factory function."""
    return AutomatizacionComprasService(db)
