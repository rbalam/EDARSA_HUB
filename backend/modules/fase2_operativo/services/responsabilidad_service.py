"""
Servicio de Responsabilidad Económica
CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2

Lógica de negocio para el cálculo de impacto económico
de diferencias de inventario y flujo de aprobaciones.
"""
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
import logging

from ..repositories.responsabilidad_repository import ResponsabilidadRepository
from ..repositories.workflow_repository import WorkflowRepository
from ..repositories.detalle_diferencias_repository import DetalleDiferenciasRepository
from ..repositories.configuracion_repository import ConfiguracionRepository
from ..repositories.historial_responsabilidad_repository import HistorialResponsabilidadRepository
from ..schemas.responsabilidad_schemas import (
    EstadoResponsabilidad,
    AccionResponsabilidad,
    RolAutorizacion,
    ResponsabilidadResponse,
    ResponsabilidadResumenCalculo,
    ResumenFaltantes,
    ResumenSobrantes,
    ToleranciaAplicada,
    ConfiguracionResponsabilidadResponse,
    AccionResponsabilidadResponse,
    HistorialTransicionResponse,
    HistorialListResponse,
    ResponsabilidadPendienteResponse,
    PendientesAprobacionResponse,
    EnDisputaResponse,
    TRANSICIONES_VALIDAS,
)
from ..schemas.enums import EstadoWorkflow

logger = logging.getLogger(__name__)


class ResponsabilidadServiceError(Exception):
    """Error base del servicio de responsabilidad."""
    pass


class WorkflowNoEncontradoError(ResponsabilidadServiceError):
    """Workflow no encontrado."""
    pass


class CalculoYaExisteError(ResponsabilidadServiceError):
    """Ya existe un cálculo para este workflow."""
    pass


class ModuloDesactivadoError(ResponsabilidadServiceError):
    """El módulo de responsabilidad está desactivado."""
    pass


class SinDiferenciasError(ResponsabilidadServiceError):
    """El workflow no tiene diferencias registradas."""
    pass


class AprobacionesDesactivadasError(ResponsabilidadServiceError):
    """Las aprobaciones están desactivadas."""
    pass


class ResponsabilidadNoEncontradaError(ResponsabilidadServiceError):
    """Registro de responsabilidad no encontrado."""
    pass


class TransicionInvalidaError(ResponsabilidadServiceError):
    """Transición de estado no válida."""
    pass


class PermisoInsuficienteError(ResponsabilidadServiceError):
    """Usuario no tiene permisos suficientes para esta acción."""
    pass


# Claves de configuración para responsabilidad
CONFIG_KEYS = {
    "CARGO_MINIMO_MXN": ("50.0", "Monto mínimo en MXN para generar cargo"),
    "TOLERANCIA_UNIDADES": ("2", "Tolerancia absoluta en unidades"),
    "TOLERANCIA_PORCENTAJE_DIFERENCIA": ("1.5", "Tolerancia relativa en porcentaje"),
    "PRECIO_FALTANTE_DEFAULT": ("0.0", "Precio unitario por defecto si no viene del análisis"),
    "MODULO_RESPONSABILIDAD_ACTIVO": ("true", "Módulo de responsabilidad habilitado"),
    "PERMITIR_COMPENSACION_FALTANTES_SOBRANTES": ("false", "Permitir compensación de faltantes con sobrantes"),
    # Fase 2C.2 - Aprobaciones
    "RESPONSABILIDAD_APROBACIONES_HABILITADAS": ("true", "Flujo de aprobaciones habilitado"),
    "RESPONSABILIDAD_UMBRAL_SUPERVISOR": ("500", "Monto máximo para aprobación de supervisor"),
    "RESPONSABILIDAD_UMBRAL_GERENTE": ("2000", "Monto máximo para aprobación de gerente"),
    "RESPONSABILIDAD_UMBRAL_DIRECCION": ("10000", "Monto máximo para aprobación de dirección"),
}


class ResponsabilidadService:
    """Servicio para cálculo de responsabilidad económica y aprobaciones."""
    
    def __init__(self, db):
        self.db = db
        self.responsabilidad_repo = ResponsabilidadRepository(db)
        self.workflow_repo = WorkflowRepository(db)
        self.diferencias_repo = DetalleDiferenciasRepository(db)
        self.config_repo = ConfiguracionRepository(db)
        self.historial_repo = HistorialResponsabilidadRepository(db)
    
    # ==================== CONFIGURACIÓN ====================
    
    async def obtener_configuracion(self) -> ConfiguracionResponsabilidadResponse:
        """Obtiene la configuración actual de responsabilidad."""
        cargo_minimo = await self.config_repo.get_valor_float("CARGO_MINIMO_MXN", 50.0)
        tolerancia_unidades = await self.config_repo.get_valor_int("TOLERANCIA_UNIDADES", 2)
        tolerancia_porcentaje = await self.config_repo.get_valor_float("TOLERANCIA_PORCENTAJE_DIFERENCIA", 1.5)
        precio_default = await self.config_repo.get_valor_float("PRECIO_FALTANTE_DEFAULT", 0.0)
        
        modulo_activo_str = await self.config_repo.get_valor("MODULO_RESPONSABILIDAD_ACTIVO", "true")
        modulo_activo = modulo_activo_str.lower() == "true"
        
        compensacion_str = await self.config_repo.get_valor("PERMITIR_COMPENSACION_FALTANTES_SOBRANTES", "false")
        compensacion = compensacion_str.lower() == "true"
        
        return ConfiguracionResponsabilidadResponse(
            cargo_minimo_mxn=cargo_minimo,
            tolerancia_unidades=tolerancia_unidades,
            tolerancia_porcentaje_diferencia=tolerancia_porcentaje,
            precio_faltante_default=precio_default,
            modulo_responsabilidad_activo=modulo_activo,
            permitir_compensacion_faltantes_sobrantes=compensacion
        )
    
    async def actualizar_configuracion(
        self,
        cargo_minimo_mxn: Optional[float] = None,
        tolerancia_unidades: Optional[int] = None,
        tolerancia_porcentaje_diferencia: Optional[float] = None,
        precio_faltante_default: Optional[float] = None,
        modulo_responsabilidad_activo: Optional[bool] = None,
        permitir_compensacion_faltantes_sobrantes: Optional[bool] = None
    ) -> ConfiguracionResponsabilidadResponse:
        """Actualiza la configuración de responsabilidad."""
        
        if cargo_minimo_mxn is not None:
            await self.config_repo.set_valor(
                "CARGO_MINIMO_MXN",
                str(cargo_minimo_mxn),
                CONFIG_KEYS["CARGO_MINIMO_MXN"][1]
            )
        
        if tolerancia_unidades is not None:
            await self.config_repo.set_valor(
                "TOLERANCIA_UNIDADES",
                str(tolerancia_unidades),
                CONFIG_KEYS["TOLERANCIA_UNIDADES"][1]
            )
        
        if tolerancia_porcentaje_diferencia is not None:
            await self.config_repo.set_valor(
                "TOLERANCIA_PORCENTAJE_DIFERENCIA",
                str(tolerancia_porcentaje_diferencia),
                CONFIG_KEYS["TOLERANCIA_PORCENTAJE_DIFERENCIA"][1]
            )
        
        if precio_faltante_default is not None:
            await self.config_repo.set_valor(
                "PRECIO_FALTANTE_DEFAULT",
                str(precio_faltante_default),
                CONFIG_KEYS["PRECIO_FALTANTE_DEFAULT"][1]
            )
        
        if modulo_responsabilidad_activo is not None:
            await self.config_repo.set_valor(
                "MODULO_RESPONSABILIDAD_ACTIVO",
                str(modulo_responsabilidad_activo).lower(),
                CONFIG_KEYS["MODULO_RESPONSABILIDAD_ACTIVO"][1]
            )
        
        if permitir_compensacion_faltantes_sobrantes is not None:
            await self.config_repo.set_valor(
                "PERMITIR_COMPENSACION_FALTANTES_SOBRANTES",
                str(permitir_compensacion_faltantes_sobrantes).lower(),
                CONFIG_KEYS["PERMITIR_COMPENSACION_FALTANTES_SOBRANTES"][1]
            )
        
        return await self.obtener_configuracion()
    
    async def inicializar_configuracion(self) -> Dict:
        """Inicializa las claves de configuración si no existen."""
        claves_creadas = []
        
        for clave, (default, descripcion) in CONFIG_KEYS.items():
            existente = await self.config_repo.get_by_clave(clave)
            if not existente:
                await self.config_repo.set_valor(clave, default, descripcion)
                claves_creadas.append(clave)
                logger.info(f"Configuración inicializada: {clave} = {default}")
        
        return {
            "claves_creadas": claves_creadas,
            "total": len(claves_creadas),
            "mensaje": f"Se inicializaron {len(claves_creadas)} claves de configuración"
        }
    
    # ==================== CÁLCULO ====================
    
    async def calcular_responsabilidad(
        self,
        workflow_id: str,
        usuario_id: str,
        forzar_recalculo: bool = False
    ) -> ResponsabilidadResumenCalculo:
        """
        Calcula el impacto económico de un workflow.
        
        Flujo 2C.1:
        1. Valida workflow existe
        2. Verifica módulo activo
        3. Obtiene diferencias
        4. Clasifica faltantes/sobrantes
        5. Aplica tolerancias
        6. Calcula monto propuesto (solo faltantes fuera de tolerancia)
        7. Compara vs cargo mínimo
        8. Persiste con estado CALCULADO
        9. Actualiza workflow a EN_REVISION_FINANCIERA
        10. Retorna resumen
        
        Args:
            workflow_id: ID del workflow
            usuario_id: Usuario que ejecuta el cálculo
            forzar_recalculo: Si True, recalcula aunque exista
            
        Returns:
            Resumen del cálculo
        """
        # 1. Verificar módulo activo
        config = await self.obtener_configuracion()
        if not config.modulo_responsabilidad_activo:
            raise ModuloDesactivadoError("El módulo de responsabilidad económica está desactivado")
        
        # 2. Verificar workflow existe
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            # Intentar buscar por campo 'id' (UUID) si no es ObjectId
            workflow = await self._buscar_workflow_por_uuid(workflow_id)
        if not workflow:
            raise WorkflowNoEncontradoError(f"Workflow no encontrado: {workflow_id}")
        
        # 3. Verificar si ya existe cálculo
        calculo_existente = await self.responsabilidad_repo.get_by_workflow(workflow_id)
        if calculo_existente and not forzar_recalculo:
            raise CalculoYaExisteError(f"Ya existe un cálculo para el workflow {workflow_id}")
        
        # 4. Obtener diferencias
        diferencias = await self.diferencias_repo.get_by_workflow(workflow_id)
        if not diferencias:
            raise SinDiferenciasError(f"El workflow {workflow_id} no tiene diferencias registradas")
        
        # 5. Ejecutar cálculo
        resultado = self._calcular_impacto(diferencias, config)
        
        # 6. Preparar datos para persistir
        now = datetime.now(timezone.utc)
        registro_id = str(uuid.uuid4())
        
        datos_registro = {
            "id": registro_id,
            "workflow_id": workflow_id,
            "tarea_id": None,  # Se puede asociar después si aplica
            "procesado_id": workflow.get("procesado_id", ""),
            "sucursal_id": workflow.get("sucursal_id", self._extraer_sucursal(workflow)),
            
            # Totales
            "total_diferencias": resultado["total_diferencias"],
            
            # Faltantes
            "faltantes_unidades": resultado["faltantes"]["unidades"],
            "faltantes_valor_mxn": resultado["faltantes"]["valor_mxn"],
            "faltantes_cantidad_items": resultado["faltantes"]["cantidad_items"],
            
            # Sobrantes
            "sobrantes_unidades": resultado["sobrantes"]["unidades"],
            "sobrantes_valor_mxn": resultado["sobrantes"]["valor_mxn"],
            "sobrantes_cantidad_items": resultado["sobrantes"]["cantidad_items"],
            
            # Tolerancia
            "tolerancia_aplicada_unidades": config.tolerancia_unidades,
            "tolerancia_aplicada_porcentaje": config.tolerancia_porcentaje_diferencia,
            "diferencias_dentro_tolerancia": resultado["tolerancia"]["dentro"],
            "diferencias_fuera_tolerancia": resultado["tolerancia"]["fuera"],
            "valor_excluido_por_tolerancia_mxn": resultado["tolerancia"]["valor_excluido"],
            
            # Monto propuesto
            "monto_propuesto_mxn": resultado["monto_propuesto"],
            "excede_minimo": resultado["excede_minimo"],
            "cargo_minimo_configurado_mxn": config.cargo_minimo_mxn,
            
            # Estado
            "estado": EstadoResponsabilidad.CALCULADO.value,
            
            # Auditoría
            "fecha_calculo": now,
            "calculado_por": usuario_id,
        }
        
        # 7. Persistir (crear o actualizar)
        if calculo_existente and forzar_recalculo:
            await self.responsabilidad_repo.actualizar_calculo(workflow_id, datos_registro)
            logger.info(f"Recalculada responsabilidad para workflow {workflow_id}")
        else:
            await self.responsabilidad_repo.crear_calculo(datos_registro)
            logger.info(f"Creada responsabilidad para workflow {workflow_id}")
        
        # 8. Actualizar estado del workflow a EN_REVISION_FINANCIERA
        estado_anterior = workflow.get("estado_workflow", "")
        # Usar el método correcto dependiendo de si es ObjectId o UUID
        workflow_actualizado = await self.workflow_repo.update(workflow.get("_id", ""), {
            "estado_workflow": EstadoWorkflow.EN_REVISION_FINANCIERA.value,
        })
        if not workflow_actualizado:
            # Intentar por UUID
            workflow_actualizado = await self._actualizar_workflow_por_uuid(workflow_id, {
                "estado_workflow": EstadoWorkflow.EN_REVISION_FINANCIERA.value,
            })
        logger.info(f"Workflow {workflow_id} actualizado a EN_REVISION_FINANCIERA (anterior: {estado_anterior})")
        
        # 9. Construir resumen
        return ResponsabilidadResumenCalculo(
            id=registro_id,
            workflow_id=workflow_id,
            estado=EstadoResponsabilidad.CALCULADO,
            total_diferencias=resultado["total_diferencias"],
            faltantes_valor_mxn=resultado["faltantes"]["valor_mxn"],
            sobrantes_valor_mxn=resultado["sobrantes"]["valor_mxn"],
            valor_excluido_por_tolerancia_mxn=resultado["tolerancia"]["valor_excluido"],
            monto_propuesto_mxn=resultado["monto_propuesto"],
            excede_minimo=resultado["excede_minimo"],
            workflow_estado_nuevo=EstadoWorkflow.EN_REVISION_FINANCIERA.value,
            mensaje=self._generar_mensaje_resumen(resultado, config)
        )
    
    def _calcular_impacto(self, diferencias: List[Dict], config: ConfiguracionResponsabilidadResponse) -> Dict:
        """
        Ejecuta el cálculo de impacto económico.
        
        Reglas:
        - Faltante = diferencia < 0 (físico < sistema)
        - Sobrante = diferencia > 0 (físico > sistema)
        - Sobrantes NO compensan faltantes (por config)
        - Tolerancia excluye diferencias pequeñas
        - Monto propuesto = solo faltantes fuera de tolerancia
        """
        faltantes = {"unidades": 0, "valor_mxn": 0.0, "cantidad_items": 0}
        sobrantes = {"unidades": 0, "valor_mxn": 0.0, "cantidad_items": 0}
        tolerancia = {"dentro": 0, "fuera": 0, "valor_excluido": 0.0}
        
        precio_default = config.precio_faltante_default
        tol_unidades = config.tolerancia_unidades
        tol_porcentaje = config.tolerancia_porcentaje_diferencia / 100.0  # Convertir a decimal
        
        for dif in diferencias:
            # Extraer valores de la diferencia
            cantidad_dif = dif.get("diferencia_cantidad", dif.get("diferencia", 0))
            # Usar diferencia_costo si diferencia_valor no existe
            valor_dif = dif.get("diferencia_valor") or dif.get("diferencia_costo", 0.0)
            cantidad_esperada = dif.get("cantidad_esperada", dif.get("cantidad_sistema", dif.get("inv_teorico_cantidad", 0)))
            
            # Si no hay valor, calcular con precio default
            if valor_dif == 0 and cantidad_dif != 0 and precio_default > 0:
                valor_dif = abs(cantidad_dif) * precio_default
            
            # Determinar si está dentro de tolerancia
            dentro_tolerancia = self._esta_dentro_tolerancia(
                cantidad_dif, cantidad_esperada, tol_unidades, tol_porcentaje
            )
            
            if cantidad_dif < 0:  # FALTANTE
                faltantes["unidades"] += abs(cantidad_dif)
                faltantes["valor_mxn"] += abs(valor_dif)
                faltantes["cantidad_items"] += 1
                
                if dentro_tolerancia:
                    tolerancia["dentro"] += 1
                    tolerancia["valor_excluido"] += abs(valor_dif)
                else:
                    tolerancia["fuera"] += 1
                    
            elif cantidad_dif > 0:  # SOBRANTE
                sobrantes["unidades"] += cantidad_dif
                sobrantes["valor_mxn"] += valor_dif
                sobrantes["cantidad_items"] += 1
                
                # Sobrantes también se evalúan contra tolerancia para registro
                if dentro_tolerancia:
                    tolerancia["dentro"] += 1
                else:
                    tolerancia["fuera"] += 1
            # diferencia == 0 se ignora (no hay impacto)
        
        # Calcular monto propuesto (solo faltantes fuera de tolerancia)
        # = faltantes_valor - valor_excluido_por_tolerancia
        monto_propuesto = max(0.0, faltantes["valor_mxn"] - tolerancia["valor_excluido"])
        
        # Nota: NO aplicamos compensación aunque esté habilitada (2C.1 no compensa)
        # La compensación será para fases posteriores
        
        excede_minimo = monto_propuesto >= config.cargo_minimo_mxn
        
        return {
            "total_diferencias": len(diferencias),
            "faltantes": faltantes,
            "sobrantes": sobrantes,
            "tolerancia": tolerancia,
            "monto_propuesto": round(monto_propuesto, 2),
            "excede_minimo": excede_minimo
        }
    
    def _esta_dentro_tolerancia(
        self,
        cantidad_diferencia: int,
        cantidad_esperada: int,
        tol_unidades: int,
        tol_porcentaje: float
    ) -> bool:
        """
        Determina si una diferencia está dentro de tolerancia.
        
        Criterio: Dentro de tolerancia si cumple CUALQUIERA:
        - abs(diferencia) <= tolerancia_unidades
        - abs(diferencia) / cantidad_esperada <= tolerancia_porcentaje
        """
        abs_dif = abs(cantidad_diferencia)
        
        # Tolerancia absoluta en unidades
        if abs_dif <= tol_unidades:
            return True
        
        # Tolerancia relativa en porcentaje
        if cantidad_esperada > 0:
            porcentaje_dif = abs_dif / cantidad_esperada
            if porcentaje_dif <= tol_porcentaje:
                return True
        
        return False
    
    def _extraer_sucursal(self, workflow: Dict) -> str:
        """Extrae el ID de sucursal del workflow o sus datos relacionados."""
        # Intentar obtener de campos conocidos
        if "sucursal_id" in workflow:
            return workflow["sucursal_id"]
        if "sucursal" in workflow:
            return workflow["sucursal"]
        # Fallback
        return "DESCONOCIDA"
    
    async def _buscar_workflow_por_uuid(self, workflow_id: str) -> Optional[Dict]:
        """Busca un workflow por su campo 'id' (UUID)."""
        doc = self.workflow_repo.collection.find_one({"id": workflow_id})
        return self.workflow_repo._serialize_id(doc) if doc else None
    
    async def _actualizar_workflow_por_uuid(self, workflow_id: str, data: Dict) -> Optional[Dict]:
        """Actualiza un workflow buscando por su campo 'id' (UUID)."""
        from datetime import datetime, timezone
        data["fecha_ultima_actualizacion"] = datetime.now(timezone.utc)
        result = self.workflow_repo.collection.find_one_and_update(
            {"id": workflow_id},
            {"$set": data},
            return_document=True
        )
        return self.workflow_repo._serialize_id(result) if result else None
    
    def _generar_mensaje_resumen(self, resultado: Dict, config: ConfiguracionResponsabilidadResponse) -> str:
        """Genera un mensaje descriptivo del resultado."""
        monto = resultado["monto_propuesto"]
        excede = resultado["excede_minimo"]
        faltantes_valor = resultado["faltantes"]["valor_mxn"]
        sobrantes_valor = resultado["sobrantes"]["valor_mxn"]
        
        if monto == 0:
            return "No se generó monto propuesto. Todas las diferencias están dentro de tolerancia o no hay faltantes."
        
        if excede:
            return f"Monto propuesto: ${monto:,.2f} MXN (excede mínimo de ${config.cargo_minimo_mxn:,.2f}). Faltantes: ${faltantes_valor:,.2f}, Sobrantes: ${sobrantes_valor:,.2f} (no compensan)."
        else:
            return f"Monto propuesto: ${monto:,.2f} MXN (NO excede mínimo de ${config.cargo_minimo_mxn:,.2f}). El cargo no procede por ser menor al mínimo."
    
    # ==================== CONSULTAS ====================
    
    async def obtener_por_workflow(self, workflow_id: str) -> Optional[ResponsabilidadResponse]:
        """Obtiene el cálculo de responsabilidad de un workflow."""
        registro = await self.responsabilidad_repo.get_by_workflow(workflow_id)
        if not registro:
            return None
        return self._mapear_a_response(registro)
    
    async def listar(
        self,
        sucursal_id: Optional[str] = None,
        estado: Optional[str] = None,
        excede_minimo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """Lista cálculos de responsabilidad con filtros."""
        resultado = await self.responsabilidad_repo.listar_con_filtros(
            sucursal_id=sucursal_id,
            estado=estado,
            excede_minimo=excede_minimo,
            skip=skip,
            limit=limit
        )
        
        items = [self._mapear_a_response(r) for r in resultado["items"]]
        return {"items": items, "total": resultado["total"]}
    
    def _mapear_a_response(self, registro: Dict) -> ResponsabilidadResponse:
        """Mapea un registro de BD a ResponsabilidadResponse."""
        return ResponsabilidadResponse(
            id=registro.get("id", ""),
            workflow_id=registro.get("workflow_id", ""),
            tarea_id=registro.get("tarea_id"),
            procesado_id=registro.get("procesado_id", ""),
            sucursal_id=registro.get("sucursal_id", ""),
            total_diferencias=registro.get("total_diferencias", 0),
            faltantes=ResumenFaltantes(
                unidades=registro.get("faltantes_unidades", 0),
                valor_mxn=registro.get("faltantes_valor_mxn", 0.0),
                cantidad_items=registro.get("faltantes_cantidad_items", 0)
            ),
            sobrantes=ResumenSobrantes(
                unidades=registro.get("sobrantes_unidades", 0),
                valor_mxn=registro.get("sobrantes_valor_mxn", 0.0),
                cantidad_items=registro.get("sobrantes_cantidad_items", 0)
            ),
            tolerancia=ToleranciaAplicada(
                tolerancia_unidades=registro.get("tolerancia_aplicada_unidades", 0),
                tolerancia_porcentaje=registro.get("tolerancia_aplicada_porcentaje", 0.0),
                diferencias_dentro_tolerancia=registro.get("diferencias_dentro_tolerancia", 0),
                diferencias_fuera_tolerancia=registro.get("diferencias_fuera_tolerancia", 0),
                valor_excluido_por_tolerancia_mxn=registro.get("valor_excluido_por_tolerancia_mxn", 0.0)
            ),
            monto_propuesto_mxn=registro.get("monto_propuesto_mxn", 0.0),
            excede_minimo=registro.get("excede_minimo", False),
            cargo_minimo_configurado_mxn=registro.get("cargo_minimo_configurado_mxn", 0.0),
            estado=EstadoResponsabilidad(registro.get("estado", "CALCULADO")),
            fecha_calculo=registro.get("fecha_calculo", datetime.now(timezone.utc)),
            calculado_por=registro.get("calculado_por", ""),
            fecha_creacion=registro.get("fecha_creacion", datetime.now(timezone.utc)),
            fecha_actualizacion=registro.get("fecha_actualizacion", datetime.now(timezone.utc))
        )
    
    # ==================== MÉTRICAS DASHBOARD ====================
    
    async def obtener_metricas_dashboard(self) -> Dict:
        """
        Obtiene métricas agregadas para el dashboard de responsabilidad.
        
        Returns:
            Dict con métricas globales, por sucursal y workflows recientes
        """
        # Métricas globales
        metricas_globales = await self.responsabilidad_repo.obtener_metricas_globales()
        
        # Contar workflows en EN_REVISION_FINANCIERA
        workflows_revision = self.workflow_repo.collection.count_documents({
            "estado_workflow": EstadoWorkflow.EN_REVISION_FINANCIERA.value
        })
        
        # Top sucursales por monto propuesto
        top_sucursales = await self._obtener_top_sucursales(limit=5)
        
        # Últimos cálculos
        resultado_lista = await self.responsabilidad_repo.listar_con_filtros(limit=10)
        ultimos_calculos = [
            {
                "workflow_id": r.get("workflow_id", ""),
                "sucursal_id": r.get("sucursal_id", ""),
                "monto_propuesto_mxn": r.get("monto_propuesto_mxn", 0),
                "excede_minimo": r.get("excede_minimo", False),
                "estado": r.get("estado", "CALCULADO"),
                "fecha_calculo": r.get("fecha_calculo").isoformat() if r.get("fecha_calculo") else None
            }
            for r in resultado_lista.get("items", [])
        ]
        
        return {
            "resumen": {
                "total_calculos": metricas_globales.get("total_calculos", 0),
                "monto_total_propuesto_mxn": round(metricas_globales.get("total_monto_propuesto", 0), 2),
                "total_faltantes_mxn": round(metricas_globales.get("total_faltantes_valor", 0), 2),
                "total_sobrantes_mxn": round(metricas_globales.get("total_sobrantes_valor", 0), 2),
                "calculos_exceden_minimo": metricas_globales.get("calculos_exceden_minimo", 0),
                "workflows_en_revision_financiera": workflows_revision,
            },
            "top_sucursales": top_sucursales,
            "ultimos_calculos": ultimos_calculos
        }
    
    async def _obtener_top_sucursales(self, limit: int = 5) -> list:
        """Obtiene las sucursales con mayor monto propuesto."""
        pipeline = [
            {
                "$group": {
                    "_id": "$sucursal_id",
                    "monto_total": {"$sum": "$monto_propuesto_mxn"},
                    "cantidad_calculos": {"$sum": 1},
                    "calculos_exceden": {
                        "$sum": {"$cond": ["$excede_minimo", 1, 0]}
                    }
                }
            },
            {"$sort": {"monto_total": -1}},
            {"$limit": limit}
        ]
        
        result = list(self.responsabilidad_repo.collection.aggregate(pipeline))
        
        return [
            {
                "sucursal_id": r["_id"],
                "monto_total_mxn": round(r["monto_total"], 2),
                "cantidad_calculos": r["cantidad_calculos"],
                "calculos_exceden_minimo": r["calculos_exceden"]
            }
            for r in result
        ]
    
    # ==================== FASE 2C.2: APROBACIONES ====================
    
    async def _verificar_aprobaciones_habilitadas(self):
        """Verifica si las aprobaciones están habilitadas."""
        habilitadas_str = await self.config_repo.get_valor("RESPONSABILIDAD_APROBACIONES_HABILITADAS", "true")
        if habilitadas_str.lower() != "true":
            raise AprobacionesDesactivadasError("El flujo de aprobaciones está desactivado")
    
    async def _obtener_responsabilidad(self, responsabilidad_id: str) -> Dict:
        """Obtiene un registro de responsabilidad por ID."""
        registro = await self.responsabilidad_repo.get_by_id(responsabilidad_id)
        if not registro:
            # Intentar buscar por campo 'id'
            registro = self.responsabilidad_repo.collection.find_one({"id": responsabilidad_id})
            if registro:
                registro = self.responsabilidad_repo._serialize_id(registro)
        if not registro:
            raise ResponsabilidadNoEncontradaError(f"Responsabilidad no encontrada: {responsabilidad_id}")
        return registro
    
    async def _validar_transicion(self, estado_actual: str, estado_nuevo: str):
        """Valida que la transición de estado sea válida."""
        estado_actual_enum = EstadoResponsabilidad(estado_actual)
        estado_nuevo_enum = EstadoResponsabilidad(estado_nuevo)
        
        transiciones_permitidas = TRANSICIONES_VALIDAS.get(estado_actual_enum, [])
        if estado_nuevo_enum not in transiciones_permitidas:
            raise TransicionInvalidaError(
                f"Transición no válida: {estado_actual} → {estado_nuevo}. "
                f"Transiciones permitidas: {[t.value for t in transiciones_permitidas]}"
            )
    
    async def _validar_permiso_por_monto(self, monto: float, usuario_rol: str, accion: str):
        """Valida que el usuario tenga permiso según el monto y su rol."""
        umbral_supervisor = await self.config_repo.get_valor_float("RESPONSABILIDAD_UMBRAL_SUPERVISOR", 500)
        umbral_gerente = await self.config_repo.get_valor_float("RESPONSABILIDAD_UMBRAL_GERENTE", 2000)
        
        # Determinar nivel requerido según monto
        if monto <= umbral_supervisor:
            nivel_requerido = RolAutorizacion.SUPERVISOR
        elif monto <= umbral_gerente:
            nivel_requerido = RolAutorizacion.GERENTE_OPS
        else:
            nivel_requerido = RolAutorizacion.DIRECCION
        
        # Jerarquía de roles
        jerarquia = {
            RolAutorizacion.AFECTADO.value: 0,
            RolAutorizacion.SUPERVISOR.value: 1,
            RolAutorizacion.GERENTE_OPS.value: 2,
            RolAutorizacion.DIRECCION.value: 3,
        }
        
        nivel_usuario = jerarquia.get(usuario_rol, 0)
        nivel_necesario = jerarquia.get(nivel_requerido.value, 3)
        
        # Exonerar siempre requiere nivel superior
        if accion == AccionResponsabilidad.EXONERAR.value:
            nivel_necesario = max(nivel_necesario, jerarquia[RolAutorizacion.GERENTE_OPS.value])
        
        if nivel_usuario < nivel_necesario:
            raise PermisoInsuficienteError(
                f"Permiso insuficiente. Monto ${monto:,.2f} requiere rol {nivel_requerido.value} o superior. "
                f"Tu rol: {usuario_rol}"
            )
    
    async def _registrar_transicion(
        self,
        responsabilidad_id: str,
        accion: AccionResponsabilidad,
        estado_anterior: str,
        estado_nuevo: str,
        usuario_id: str,
        usuario_rol: Optional[str],
        comentario: str,
        monto: float,
        motivo_codigo: Optional[str] = None
    ) -> str:
        """Registra una transición en el historial."""
        transicion_id = str(uuid.uuid4())
        await self.historial_repo.registrar_transicion(
            transicion_id=transicion_id,
            responsabilidad_id=responsabilidad_id,
            accion=accion.value,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto_al_momento=monto,
            motivo_codigo=motivo_codigo
        )
        return transicion_id
    
    async def _actualizar_estado_responsabilidad(
        self,
        responsabilidad_id: str,
        nuevo_estado: EstadoResponsabilidad
    ):
        """Actualiza el estado de un registro de responsabilidad."""
        now = datetime.now(timezone.utc)
        self.responsabilidad_repo.collection.update_one(
            {"id": responsabilidad_id},
            {"$set": {
                "estado": nuevo_estado.value,
                "fecha_actualizacion": now
            }}
        )
    
    async def _actualizar_estado_workflow_si_corresponde(
        self,
        workflow_id: str,
        estado_responsabilidad: EstadoResponsabilidad
    ) -> str:
        """
        Actualiza el estado del workflow según el estado de responsabilidad.
        
        Reglas:
        - APROBADO: Workflow permanece en EN_REVISION_FINANCIERA
        - RECHAZADO/EXONERADO: Cierra workflow solo si no hay más pendientes
        """
        workflow = await self._buscar_workflow_por_uuid(workflow_id)
        if not workflow:
            return "DESCONOCIDO"
        
        estado_workflow_actual = workflow.get("estado_workflow", "")
        nuevo_estado_workflow = estado_workflow_actual
        
        # RECHAZADO o EXONERADO pueden cerrar el workflow
        if estado_responsabilidad in [EstadoResponsabilidad.RECHAZADO, EstadoResponsabilidad.EXONERADO]:
            # Verificar si hay otros cálculos activos para este workflow
            calculos_activos = self.responsabilidad_repo.collection.count_documents({
                "workflow_id": workflow_id,
                "estado": {"$in": [
                    EstadoResponsabilidad.CALCULADO.value,
                    EstadoResponsabilidad.PROPUESTO.value,
                    EstadoResponsabilidad.EN_DISPUTA.value,
                    EstadoResponsabilidad.APROBADO.value  # Aprobado pero no aplicado
                ]}
            })
            
            if calculos_activos == 0:
                nuevo_estado_workflow = EstadoWorkflow.CERRADO.value
                await self._actualizar_workflow_por_uuid(workflow_id, {
                    "estado_workflow": nuevo_estado_workflow,
                    "cerrado_por_responsabilidad": True
                })
                logger.info(f"Workflow {workflow_id} cerrado tras {estado_responsabilidad.value}")
        
        return nuevo_estado_workflow
    
    async def proponer(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> AccionResponsabilidadResponse:
        """
        Propone formalmente un monto para revisión.
        Transición: CALCULADO → PROPUESTO
        """
        await self._verificar_aprobaciones_habilitadas()
        
        registro = await self._obtener_responsabilidad(responsabilidad_id)
        estado_actual = registro.get("estado", "CALCULADO")
        
        await self._validar_transicion(estado_actual, EstadoResponsabilidad.PROPUESTO.value)
        
        monto = registro.get("monto_propuesto_mxn", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, AccionResponsabilidad.PROPONER.value)
        
        # Registrar transición
        transicion_id = await self._registrar_transicion(
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.PROPONER,
            estado_anterior=estado_actual,
            estado_nuevo=EstadoResponsabilidad.PROPUESTO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto=monto,
            motivo_codigo=motivo_codigo
        )
        
        # Actualizar estado
        await self._actualizar_estado_responsabilidad(responsabilidad_id, EstadoResponsabilidad.PROPUESTO)
        
        workflow_id = registro.get("workflow_id", "")
        workflow_estado = await self._actualizar_estado_workflow_si_corresponde(
            workflow_id, EstadoResponsabilidad.PROPUESTO
        )
        
        return AccionResponsabilidadResponse(
            success=True,
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.PROPONER,
            estado_anterior=EstadoResponsabilidad(estado_actual),
            estado_nuevo=EstadoResponsabilidad.PROPUESTO,
            mensaje=f"Monto ${monto:,.2f} propuesto exitosamente para revisión",
            transicion_id=transicion_id,
            workflow_estado=workflow_estado or EstadoWorkflow.EN_REVISION_FINANCIERA.value
        )
    
    async def aprobar(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> AccionResponsabilidadResponse:
        """
        Aprueba un monto propuesto.
        Transición: PROPUESTO → APROBADO
        """
        await self._verificar_aprobaciones_habilitadas()
        
        registro = await self._obtener_responsabilidad(responsabilidad_id)
        estado_actual = registro.get("estado", "CALCULADO")
        
        await self._validar_transicion(estado_actual, EstadoResponsabilidad.APROBADO.value)
        
        monto = registro.get("monto_propuesto_mxn", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, AccionResponsabilidad.APROBAR.value)
        
        transicion_id = await self._registrar_transicion(
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.APROBAR,
            estado_anterior=estado_actual,
            estado_nuevo=EstadoResponsabilidad.APROBADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto=monto,
            motivo_codigo=motivo_codigo
        )
        
        await self._actualizar_estado_responsabilidad(responsabilidad_id, EstadoResponsabilidad.APROBADO)
        
        # APROBADO NO cierra el workflow
        workflow_id = registro.get("workflow_id", "")
        
        return AccionResponsabilidadResponse(
            success=True,
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.APROBAR,
            estado_anterior=EstadoResponsabilidad(estado_actual),
            estado_nuevo=EstadoResponsabilidad.APROBADO,
            mensaje=f"Monto ${monto:,.2f} aprobado. Pendiente de aplicación (Fase 2C.3)",
            transicion_id=transicion_id,
            workflow_estado=EstadoWorkflow.EN_REVISION_FINANCIERA.value
        )
    
    async def rechazar(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> AccionResponsabilidadResponse:
        """
        Rechaza un cargo propuesto (el monto NO procedía).
        Transición: PROPUESTO/EN_DISPUTA → RECHAZADO
        """
        await self._verificar_aprobaciones_habilitadas()
        
        registro = await self._obtener_responsabilidad(responsabilidad_id)
        estado_actual = registro.get("estado", "CALCULADO")
        
        await self._validar_transicion(estado_actual, EstadoResponsabilidad.RECHAZADO.value)
        
        monto = registro.get("monto_propuesto_mxn", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, AccionResponsabilidad.RECHAZAR.value)
        
        transicion_id = await self._registrar_transicion(
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.RECHAZAR,
            estado_anterior=estado_actual,
            estado_nuevo=EstadoResponsabilidad.RECHAZADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto=monto,
            motivo_codigo=motivo_codigo
        )
        
        await self._actualizar_estado_responsabilidad(responsabilidad_id, EstadoResponsabilidad.RECHAZADO)
        
        workflow_id = registro.get("workflow_id", "")
        workflow_estado = await self._actualizar_estado_workflow_si_corresponde(
            workflow_id, EstadoResponsabilidad.RECHAZADO
        )
        
        return AccionResponsabilidadResponse(
            success=True,
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.RECHAZAR,
            estado_anterior=EstadoResponsabilidad(estado_actual),
            estado_nuevo=EstadoResponsabilidad.RECHAZADO,
            mensaje=f"Cargo de ${monto:,.2f} RECHAZADO. El monto no procedía como fue planteado.",
            transicion_id=transicion_id,
            workflow_estado=workflow_estado
        )
    
    async def exonerar(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> AccionResponsabilidadResponse:
        """
        Exonera al responsable del cargo (había base pero se libera).
        Transición: PROPUESTO/EN_DISPUTA → EXONERADO
        """
        await self._verificar_aprobaciones_habilitadas()
        
        registro = await self._obtener_responsabilidad(responsabilidad_id)
        estado_actual = registro.get("estado", "CALCULADO")
        
        await self._validar_transicion(estado_actual, EstadoResponsabilidad.EXONERADO.value)
        
        monto = registro.get("monto_propuesto_mxn", 0)
        # Exonerar siempre requiere nivel superior
        await self._validar_permiso_por_monto(monto, usuario_rol, AccionResponsabilidad.EXONERAR.value)
        
        transicion_id = await self._registrar_transicion(
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.EXONERAR,
            estado_anterior=estado_actual,
            estado_nuevo=EstadoResponsabilidad.EXONERADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto=monto,
            motivo_codigo=motivo_codigo
        )
        
        await self._actualizar_estado_responsabilidad(responsabilidad_id, EstadoResponsabilidad.EXONERADO)
        
        workflow_id = registro.get("workflow_id", "")
        workflow_estado = await self._actualizar_estado_workflow_si_corresponde(
            workflow_id, EstadoResponsabilidad.EXONERADO
        )
        
        return AccionResponsabilidadResponse(
            success=True,
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.EXONERAR,
            estado_anterior=EstadoResponsabilidad(estado_actual),
            estado_nuevo=EstadoResponsabilidad.EXONERADO,
            mensaje=f"Cargo de ${monto:,.2f} EXONERADO. El responsable ha sido liberado.",
            transicion_id=transicion_id,
            workflow_estado=workflow_estado
        )
    
    async def disputar(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> AccionResponsabilidadResponse:
        """
        Inicia una disputa sobre el monto propuesto.
        Transición: PROPUESTO → EN_DISPUTA
        Solo puede ser iniciada por el afectado o nivel superior.
        """
        await self._verificar_aprobaciones_habilitadas()
        
        registro = await self._obtener_responsabilidad(responsabilidad_id)
        estado_actual = registro.get("estado", "CALCULADO")
        
        await self._validar_transicion(estado_actual, EstadoResponsabilidad.EN_DISPUTA.value)
        
        # Disputa puede ser iniciada por afectado o supervisor+
        roles_permitidos = [
            RolAutorizacion.AFECTADO.value,
            RolAutorizacion.SUPERVISOR.value,
            RolAutorizacion.GERENTE_OPS.value,
            RolAutorizacion.DIRECCION.value
        ]
        if usuario_rol not in roles_permitidos:
            raise PermisoInsuficienteError(
                f"Solo el afectado o un supervisor puede iniciar una disputa. Tu rol: {usuario_rol}"
            )
        
        monto = registro.get("monto_propuesto_mxn", 0)
        
        transicion_id = await self._registrar_transicion(
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.DISPUTAR,
            estado_anterior=estado_actual,
            estado_nuevo=EstadoResponsabilidad.EN_DISPUTA.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto=monto,
            motivo_codigo=motivo_codigo
        )
        
        await self._actualizar_estado_responsabilidad(responsabilidad_id, EstadoResponsabilidad.EN_DISPUTA)
        
        return AccionResponsabilidadResponse(
            success=True,
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.DISPUTAR,
            estado_anterior=EstadoResponsabilidad(estado_actual),
            estado_nuevo=EstadoResponsabilidad.EN_DISPUTA,
            mensaje=f"Disputa iniciada sobre monto ${monto:,.2f}",
            transicion_id=transicion_id,
            workflow_estado=EstadoWorkflow.EN_REVISION_FINANCIERA.value
        )
    
    async def resolver_disputa(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> AccionResponsabilidadResponse:
        """
        Resuelve una disputa, volviendo a estado PROPUESTO.
        Transición: EN_DISPUTA → PROPUESTO
        """
        await self._verificar_aprobaciones_habilitadas()
        
        registro = await self._obtener_responsabilidad(responsabilidad_id)
        estado_actual = registro.get("estado", "CALCULADO")
        
        await self._validar_transicion(estado_actual, EstadoResponsabilidad.PROPUESTO.value)
        
        monto = registro.get("monto_propuesto_mxn", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, AccionResponsabilidad.RESOLVER_DISPUTA.value)
        
        transicion_id = await self._registrar_transicion(
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.RESOLVER_DISPUTA,
            estado_anterior=estado_actual,
            estado_nuevo=EstadoResponsabilidad.PROPUESTO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto=monto,
            motivo_codigo=motivo_codigo
        )
        
        await self._actualizar_estado_responsabilidad(responsabilidad_id, EstadoResponsabilidad.PROPUESTO)
        
        return AccionResponsabilidadResponse(
            success=True,
            responsabilidad_id=responsabilidad_id,
            accion=AccionResponsabilidad.RESOLVER_DISPUTA,
            estado_anterior=EstadoResponsabilidad(estado_actual),
            estado_nuevo=EstadoResponsabilidad.PROPUESTO,
            mensaje=f"Disputa resuelta. Monto ${monto:,.2f} vuelve a estado PROPUESTO para revisión.",
            transicion_id=transicion_id,
            workflow_estado=EstadoWorkflow.EN_REVISION_FINANCIERA.value
        )
    
    # ==================== CONSULTAS 2C.2 ====================
    
    async def obtener_pendientes_aprobacion(self) -> PendientesAprobacionResponse:
        """Obtiene responsabilidades pendientes de aprobación (CALCULADO o PROPUESTO)."""
        estados_pendientes = [
            EstadoResponsabilidad.CALCULADO.value,
            EstadoResponsabilidad.PROPUESTO.value
        ]
        
        registros = list(self.responsabilidad_repo.collection.find({
            "estado": {"$in": estados_pendientes}
        }).sort("fecha_calculo", -1))
        
        now = datetime.now(timezone.utc)
        items = []
        monto_total = 0.0
        
        for r in registros:
            r = self.responsabilidad_repo._serialize_id(r)
            fecha_calculo = r.get("fecha_calculo")
            dias_pendiente = 0
            if fecha_calculo:
                if isinstance(fecha_calculo, str):
                    fecha_calculo = datetime.fromisoformat(fecha_calculo.replace("Z", "+00:00"))
                # Asegurar que ambas fechas tengan timezone
                if fecha_calculo.tzinfo is None:
                    fecha_calculo = fecha_calculo.replace(tzinfo=timezone.utc)
                dias_pendiente = (now - fecha_calculo).days
            
            monto = r.get("monto_propuesto_mxn", 0)
            monto_total += monto
            
            items.append(ResponsabilidadPendienteResponse(
                id=r.get("id", ""),
                workflow_id=r.get("workflow_id", ""),
                sucursal_id=r.get("sucursal_id", ""),
                monto_propuesto_mxn=monto,
                excede_minimo=r.get("excede_minimo", False),
                estado=EstadoResponsabilidad(r.get("estado", "CALCULADO")),
                fecha_calculo=fecha_calculo or now,
                dias_pendiente=dias_pendiente
            ))
        
        return PendientesAprobacionResponse(
            total=len(items),
            monto_total_pendiente=round(monto_total, 2),
            items=items
        )
    
    async def obtener_en_disputa(self) -> EnDisputaResponse:
        """Obtiene responsabilidades en disputa."""
        registros = list(self.responsabilidad_repo.collection.find({
            "estado": EstadoResponsabilidad.EN_DISPUTA.value
        }).sort("fecha_calculo", -1))
        
        now = datetime.now(timezone.utc)
        items = []
        monto_total = 0.0
        
        for r in registros:
            r = self.responsabilidad_repo._serialize_id(r)
            fecha_calculo = r.get("fecha_calculo")
            dias_pendiente = 0
            if fecha_calculo:
                if isinstance(fecha_calculo, str):
                    fecha_calculo = datetime.fromisoformat(fecha_calculo.replace("Z", "+00:00"))
                # Asegurar que ambas fechas tengan timezone
                if fecha_calculo.tzinfo is None:
                    fecha_calculo = fecha_calculo.replace(tzinfo=timezone.utc)
                dias_pendiente = (now - fecha_calculo).days
            
            monto = r.get("monto_propuesto_mxn", 0)
            monto_total += monto
            
            items.append(ResponsabilidadPendienteResponse(
                id=r.get("id", ""),
                workflow_id=r.get("workflow_id", ""),
                sucursal_id=r.get("sucursal_id", ""),
                monto_propuesto_mxn=monto,
                excede_minimo=r.get("excede_minimo", False),
                estado=EstadoResponsabilidad.EN_DISPUTA,
                fecha_calculo=fecha_calculo or now,
                dias_pendiente=dias_pendiente
            ))
        
        return EnDisputaResponse(
            total=len(items),
            monto_total_en_disputa=round(monto_total, 2),
            items=items
        )
    
    async def obtener_historial(self, responsabilidad_id: str) -> HistorialListResponse:
        """Obtiene el historial de transiciones de una responsabilidad."""
        # Verificar que existe
        await self._obtener_responsabilidad(responsabilidad_id)
        
        transiciones = await self.historial_repo.get_by_responsabilidad(responsabilidad_id)
        
        items = [
            HistorialTransicionResponse(
                id=t.get("id", ""),
                responsabilidad_id=t.get("responsabilidad_id", ""),
                accion=t.get("accion", ""),
                estado_anterior=t.get("estado_anterior", ""),
                estado_nuevo=t.get("estado_nuevo", ""),
                usuario_id=t.get("usuario_id", ""),
                usuario_rol=t.get("usuario_rol"),
                comentario=t.get("comentario", ""),
                motivo_codigo=t.get("motivo_codigo"),
                monto_al_momento=t.get("monto_al_momento", 0),
                fecha=t.get("fecha", datetime.now(timezone.utc))
            )
            for t in transiciones
        ]
        
        return HistorialListResponse(
            responsabilidad_id=responsabilidad_id,
            total=len(items),
            items=items
        )
