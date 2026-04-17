"""
Servicio de Orquestación para Fase 2A Operativo.
CAB-003 | Fase 2A - Subfase 2A.9

Este servicio conecta el análisis de diferencias de inventario con el módulo operativo:
- Detecta si hay diferencias
- Crea workflow automáticamente
- Crea detalle_diferencias por producto
- Crea tareas iniciales
- Asigna automáticamente por sucursal + almacén
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class OrquestadorService:
    """Servicio que orquesta la creación de workflows desde análisis de inventarios."""
    
    def __init__(self, db):
        self.db = db
    
    async def procesar_analisis(
        self,
        server_id: str,
        server_name: str,
        sucursal_id: str,
        sucursal_nombre: str,
        almacen_id: str,
        almacen_nombre: str,
        resultados_analisis: List[Dict],
        folios_iniciales: List[str],
        folios_finales: List[str],
        fecha_ini: str,
        fecha_fin: str,
        usuario_ejecutor_id: str,
        usuario_ejecutor_nombre: str
    ) -> Dict:
        """
        Procesa los resultados del análisis de inventario y crea workflow si hay diferencias.
        
        Args:
            server_id: ID del servidor
            server_name: Nombre del servidor
            sucursal_id: ID de la sucursal
            sucursal_nombre: Nombre de la sucursal
            almacen_id: ID del almacén
            almacen_nombre: Nombre del almacén
            resultados_analisis: Lista de productos con diferencias calculadas
            folios_iniciales: Lista de folios iniciales
            folios_finales: Lista de folios finales
            fecha_ini: Fecha de inicio del análisis
            fecha_fin: Fecha fin del análisis
            usuario_ejecutor_id: ID del usuario que ejecutó el análisis
            usuario_ejecutor_nombre: Nombre del usuario ejecutor
        
        Returns:
            Resumen de la orquestación con workflow_id, tareas_creadas, etc.
        """
        resumen = {
            "procesado": False,
            "workflow_creado": False,
            "workflow_id": None,
            "detalles_creados": 0,
            "tareas_creadas": 0,
            "productos_con_diferencia": 0,
            "valor_total_diferencias": 0.0,
            "usuario_asignado_id": None,
            "usuario_asignado_nombre": None,
            "mensaje": "",
            "error": None
        }
        
        try:
            # 1. Filtrar productos con diferencia != 0
            productos_con_diferencia = [
                p for p in resultados_analisis 
                if p.get('Diferencia_Cantidad', 0) != 0
            ]
            
            resumen["productos_con_diferencia"] = len(productos_con_diferencia)
            
            # Si no hay diferencias, no crear workflow
            if not productos_con_diferencia:
                resumen["procesado"] = True
                resumen["mensaje"] = "Sin diferencias detectadas, no se crea workflow"
                logger.info(f"Orquestador: Sin diferencias para {sucursal_nombre}/{almacen_nombre}")
                return resumen
            
            # 2. Calcular valor total de diferencias
            valor_total = sum(
                abs(float(p.get('Diferencia_Costo', 0) or 0))
                for p in productos_con_diferencia
            )
            resumen["valor_total_diferencias"] = round(valor_total, 2)
            
            # 3. Generar clave única para validación defensiva de duplicidad
            folio_final_key = ",".join(sorted([str(f) for f in folios_finales]))
            
            # 4. Verificar si ya existe workflow para esta combinación
            workflow_existente = await self._verificar_workflow_existente(
                server_id, sucursal_id, almacen_id, folio_final_key
            )
            
            if workflow_existente:
                resumen["procesado"] = True
                resumen["mensaje"] = f"Ya existe workflow activo: {workflow_existente}"
                resumen["workflow_id"] = workflow_existente
                logger.info(f"Orquestador: Workflow existente {workflow_existente}, omitiendo creación")
                return resumen
            
            # 5. Obtener usuario responsable por sucursal+almacén
            usuario_responsable = await self._obtener_usuario_responsable(
                server_id, sucursal_id, almacen_id, usuario_ejecutor_id
            )
            
            resumen["usuario_asignado_id"] = usuario_responsable["id"]
            resumen["usuario_asignado_nombre"] = usuario_responsable["nombre"]
            
            # 6. Crear Workflow
            workflow_id = await self._crear_workflow(
                server_id=server_id,
                server_name=server_name,
                sucursal_id=sucursal_id,
                sucursal_nombre=sucursal_nombre,
                almacen_id=almacen_id,
                almacen_nombre=almacen_nombre,
                folios_iniciales=folios_iniciales,
                folios_finales=folios_finales,
                folio_final_key=folio_final_key,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                total_productos=len(productos_con_diferencia),
                valor_total_diferencias=valor_total,
                usuario_creador_id=usuario_ejecutor_id
            )
            
            resumen["workflow_id"] = workflow_id
            resumen["workflow_creado"] = True
            
            # 7. Crear Detalle de Diferencias
            detalles_creados = await self._crear_detalles_diferencias(
                workflow_id, productos_con_diferencia
            )
            resumen["detalles_creados"] = detalles_creados
            
            # 8. Crear Tareas iniciales
            tareas_creadas = await self._crear_tareas_iniciales(
                workflow_id=workflow_id,
                sucursal_nombre=sucursal_nombre,
                almacen_nombre=almacen_nombre,
                usuario_responsable=usuario_responsable,
                total_productos=len(productos_con_diferencia),
                valor_total=valor_total
            )
            resumen["tareas_creadas"] = tareas_creadas
            
            resumen["procesado"] = True
            resumen["mensaje"] = f"Workflow creado exitosamente con {detalles_creados} diferencias y {tareas_creadas} tareas"
            
            logger.info(f"Orquestador: ✅ Workflow {workflow_id} creado para {sucursal_nombre}/{almacen_nombre}")
            logger.info(f"  - Productos con diferencia: {len(productos_con_diferencia)}")
            logger.info(f"  - Valor total: ${valor_total:,.2f}")
            logger.info(f"  - Asignado a: {usuario_responsable['nombre']}")
            
            return resumen
            
        except Exception as e:
            resumen["error"] = str(e)
            resumen["mensaje"] = f"Error en orquestación: {str(e)}"
            logger.error(f"Orquestador ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return resumen
    
    async def _verificar_workflow_existente(
        self,
        server_id: str,
        sucursal_id: str,
        almacen_id: str,
        folio_final_key: str
    ) -> Optional[str]:
        """Verifica si ya existe un workflow activo para esta combinación."""
        try:
            workflow = await self.db.workflow_inventarios.find_one({
                "server_id": server_id,
                "sucursal_id": sucursal_id,
                "almacen_id": almacen_id,
                "folio_final_key": folio_final_key,
                "estado": {"$nin": ["completado", "cancelado"]}
            }, {"_id": 0, "id": 1})
            
            return workflow["id"] if workflow else None
            
        except Exception as e:
            logger.warning(f"Error verificando workflow existente: {e}")
            return None
    
    async def _obtener_usuario_responsable(
        self,
        server_id: str,
        sucursal_id: str,
        almacen_id: str,
        usuario_fallback_id: str
    ) -> Dict:
        """Obtiene el usuario responsable o usa fallback."""
        try:
            # Buscar en configuración de sucursales
            config = await self.db.server_sucursales_config.find_one({
                "server_id": server_id,
                "sucursal_origen_id": sucursal_id,
                "activa": True
            }, {"_id": 0, "usuario_responsable_id": 1})
            
            usuario_id = None
            if config and config.get("usuario_responsable_id"):
                usuario_id = config["usuario_responsable_id"]
            else:
                # Fallback: usar el usuario que ejecutó el análisis
                usuario_id = usuario_fallback_id
            
            # Obtener nombre del usuario
            usuario = await self.db.users.find_one(
                {"id": usuario_id},
                {"_id": 0, "id": 1, "name": 1, "email": 1}
            )
            
            if usuario:
                return {
                    "id": usuario["id"],
                    "nombre": usuario.get("name", usuario.get("email", "Usuario"))
                }
            
            # Si no se encuentra el usuario, usar el fallback con datos mínimos
            return {
                "id": usuario_fallback_id,
                "nombre": "Usuario Asignado"
            }
            
        except Exception as e:
            logger.warning(f"Error obteniendo usuario responsable: {e}")
            return {
                "id": usuario_fallback_id,
                "nombre": "Usuario Asignado"
            }
    
    async def _crear_workflow(
        self,
        server_id: str,
        server_name: str,
        sucursal_id: str,
        sucursal_nombre: str,
        almacen_id: str,
        almacen_nombre: str,
        folios_iniciales: List[str],
        folios_finales: List[str],
        folio_final_key: str,
        fecha_ini: str,
        fecha_fin: str,
        total_productos: int,
        valor_total_diferencias: float,
        usuario_creador_id: str
    ) -> str:
        """Crea un nuevo workflow de inventario."""
        workflow_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        workflow_doc = {
            "id": workflow_id,
            "procesado_id": folio_final_key,  # Compatibilidad con schema original
            "server_id": server_id,
            "server_name": server_name,
            "sucursal_id": sucursal_id,
            "sucursal_nombre": sucursal_nombre,
            "almacen_id": almacen_id,
            "almacen_nombre": almacen_nombre,
            "folios_iniciales": folios_iniciales,
            "folios_finales": folios_finales,
            "folio_final_key": folio_final_key,
            "fecha_analisis_ini": fecha_ini,
            "fecha_analisis_fin": fecha_fin,
            "estado_workflow": "PENDIENTE_ASIGNACION",  # Compatibilidad con schema
            "estado": "pendiente",  # Para dashboard
            "ciclo_actual": 1,
            "total_productos_diferencia": total_productos,
            "valor_total_diferencias": round(valor_total_diferencias, 2),
            "fecha_creacion": now,
            "fecha_ultima_actualizacion": now,
            "usuario_creador_id": usuario_creador_id,
            "notas": []
        }
        
        await self.db.workflow_inventarios.insert_one(workflow_doc)
        logger.info(f"Workflow creado: {workflow_id}")
        
        return workflow_id
    
    async def _crear_detalles_diferencias(
        self,
        workflow_id: str,
        productos: List[Dict]
    ) -> int:
        """Crea los detalles de diferencias para cada producto."""
        now = datetime.now(timezone.utc).isoformat()
        detalles = []
        
        for prod in productos:
            detalle_id = str(uuid.uuid4())
            
            detalles.append({
                "id": detalle_id,
                "workflow_id": workflow_id,
                "codigo_producto": prod.get("Codigo", ""),
                "nombre_producto": prod.get("Producto", ""),
                "categoria": prod.get("Categoria", ""),
                "familia": prod.get("Familia", ""),
                "subfamilia": prod.get("SubFamilia", ""),
                "unidad": prod.get("Unidad", ""),
                "costo_unitario": float(prod.get("Costo_Unitario", 0) or 0),
                "inv_inicial_cantidad": float(prod.get("Inv_Inicial_Cantidad", 0) or 0),
                "inv_final_cantidad": float(prod.get("Inv_Final_Cantidad", 0) or 0),
                "inv_teorico_cantidad": float(prod.get("Inv_Teorico_Cantidad", 0) or 0),
                "diferencia_cantidad": float(prod.get("Diferencia_Cantidad", 0) or 0),
                "diferencia_costo": float(prod.get("Diferencia_Costo", 0) or 0),
                "diferencia_porcentaje": float(prod.get("Diferencia_Porcentaje", 0) or 0),
                "movimientos": float(prod.get("Movimientos", 0) or 0),
                "ventas": float(prod.get("Ventas", 0) or 0),
                "estado_justificacion": "pendiente",
                "requiere_justificacion_completa": abs(float(prod.get("Diferencia_Costo", 0) or 0)) > 500,
                "fecha_creacion": now
            })
        
        if detalles:
            await self.db.detalle_diferencias.insert_many(detalles)
        
        logger.info(f"Detalles creados: {len(detalles)} para workflow {workflow_id}")
        return len(detalles)
    
    async def _crear_tareas_iniciales(
        self,
        workflow_id: str,
        sucursal_nombre: str,
        almacen_nombre: str,
        usuario_responsable: Dict,
        total_productos: int,
        valor_total: float
    ) -> int:
        """Crea las tareas iniciales de justificación."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        
        # Obtener días límite de configuración (default 3)
        config = await self.db.configuracion_operativa.find_one(
            {"clave": "DIAS_LIMITE_TAREA_DEFAULT"},
            {"_id": 0, "valor": 1}
        )
        dias_limite = int(config.get("valor", 3)) if config else 3
        fecha_limite = (now + timedelta(days=dias_limite)).isoformat()
        
        # Crear tarea principal de justificación
        tarea_id = str(uuid.uuid4())
        
        tarea_doc = {
            "id": tarea_id,
            "workflow_id": workflow_id,
            "tipo_tarea": "JUSTIFICAR",
            "titulo": f"Justificar diferencias - {sucursal_nombre}/{almacen_nombre}",
            "descripcion": f"Se detectaron {total_productos} productos con diferencias por un valor total de ${valor_total:,.2f}. Favor de revisar y justificar cada diferencia.",
            "estado_tarea": "PENDIENTE",
            "prioridad": "ALTA" if valor_total > 5000 else "MEDIA",
            "usuario_asignado_id": usuario_responsable["id"],
            "usuario_asignado_nombre": usuario_responsable["nombre"],
            "fecha_creacion": now_iso,
            "fecha_asignacion": now_iso,
            "fecha_limite": fecha_limite,
            "fecha_actualizacion": now_iso,
            "ciclo": 1,
            "es_reasignacion": False,
            "vencida": False,
            "notas": []
        }
        
        await self.db.tareas_inventario.insert_one(tarea_doc)
        logger.info(f"Tarea creada: {tarea_id} asignada a {usuario_responsable['nombre']}")
        
        return 1


# Función helper para instanciar el servicio
def get_orquestador_service(db):
    """Factory function para obtener instancia del orquestador."""
    return OrquestadorService(db)
