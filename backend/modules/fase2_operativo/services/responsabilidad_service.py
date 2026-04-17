"""
Servicio de Responsabilidad Económica
CAB-003 | EDARSA HUB - Fase 2C.1

Lógica de negocio para el cálculo de impacto económico
de diferencias de inventario.
"""
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
import logging

from ..repositories.responsabilidad_repository import ResponsabilidadRepository
from ..repositories.workflow_repository import WorkflowRepository
from ..repositories.detalle_diferencias_repository import DetalleDiferenciasRepository
from ..repositories.configuracion_repository import ConfiguracionRepository
from ..schemas.responsabilidad_schemas import (
    EstadoResponsabilidad,
    ResponsabilidadResponse,
    ResponsabilidadResumenCalculo,
    ResumenFaltantes,
    ResumenSobrantes,
    ToleranciaAplicada,
    ConfiguracionResponsabilidadResponse,
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


# Claves de configuración para responsabilidad
CONFIG_KEYS = {
    "CARGO_MINIMO_MXN": ("50.0", "Monto mínimo en MXN para generar cargo"),
    "TOLERANCIA_UNIDADES": ("2", "Tolerancia absoluta en unidades"),
    "TOLERANCIA_PORCENTAJE_DIFERENCIA": ("1.5", "Tolerancia relativa en porcentaje"),
    "PRECIO_FALTANTE_DEFAULT": ("0.0", "Precio unitario por defecto si no viene del análisis"),
    "MODULO_RESPONSABILIDAD_ACTIVO": ("true", "Módulo de responsabilidad habilitado"),
    "PERMITIR_COMPENSACION_FALTANTES_SOBRANTES": ("false", "Permitir compensación de faltantes con sobrantes"),
}


class ResponsabilidadService:
    """Servicio para cálculo de responsabilidad económica."""
    
    def __init__(self, db):
        self.db = db
        self.responsabilidad_repo = ResponsabilidadRepository(db)
        self.workflow_repo = WorkflowRepository(db)
        self.diferencias_repo = DetalleDiferenciasRepository(db)
        self.config_repo = ConfiguracionRepository(db)
    
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
