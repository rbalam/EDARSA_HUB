"""
Servicio de Cargos Económicos
CAB-003 | EDARSA HUB - Fase 2C.3

Lógica de negocio para la aplicación formal de cargos económicos
derivados de diferencias de inventario dictaminadas.

REGLAS DE NEGOCIO CRÍTICAS:
1. NO se puede crear cargo si existe controversia activa
2. NO se puede crear cargo si existe exoneración
3. NO se puede crear cargo si la responsabilidad no está APROBADA
4. Toda transición genera registro en cargos_economicos_log
5. Reversa requiere motivo detallado y usuario responsable
"""
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
import logging

from ..repositories.cargos_repository import CargosEconomicosRepository, CargosLogRepository
from ..repositories.responsabilidad_repository import ResponsabilidadRepository
from ..repositories.workflow_repository import WorkflowRepository
from ..schemas.cargos_schemas import (
    EstatusCargo,
    AccionCargo,
    OrigenCargo,
    TRANSICIONES_CARGO_VALIDAS,
    CargoEconomicoResponse,
    CargoAccionResponse,
    CargoLogResponse,
    CargoLogListResponse,
    ElegibilidadCargoResponse,
    CargosPendientesResponse,
    CargosAplicadosResponse,
    CargosMetricasResponse,
)
from ..schemas.responsabilidad_schemas import EstadoResponsabilidad

logger = logging.getLogger(__name__)


class CargosServiceError(Exception):
    """Error base del servicio de cargos."""
    pass


class ResponsabilidadNoEncontradaError(CargosServiceError):
    """Responsabilidad no encontrada."""
    pass


class CargoNoEncontradoError(CargosServiceError):
    """Cargo no encontrado."""
    pass


class CargoYaExisteError(CargosServiceError):
    """Ya existe un cargo activo para esta responsabilidad."""
    pass


class NoElegibleParaCargoError(CargosServiceError):
    """La responsabilidad no es elegible para generar cargo."""
    pass


class TransicionInvalidaError(CargosServiceError):
    """Transición de estado no válida."""
    pass


class PermisoInsuficienteError(CargosServiceError):
    """Usuario no tiene permisos suficientes."""
    pass


class CargosService:
    """
    Servicio para gestión de cargos económicos.
    
    Implementa el ciclo de vida completo:
    - Evaluación de elegibilidad
    - Creación de propuesta
    - Autorización
    - Aplicación
    - Rechazo
    - Reversa controlada
    """
    
    # Umbrales de autorización por rol
    UMBRAL_SUPERVISOR = 500.0
    UMBRAL_GERENTE = 2000.0
    UMBRAL_DIRECCION = 10000.0
    
    # Jerarquía de roles
    JERARQUIA_ROLES = {
        "AFECTADO": 0,
        "SUPERVISOR": 1,
        "GERENTE_OPS": 2,
        "DIRECCION": 3,
        "ADMIN": 4,
    }
    
    def __init__(self, db):
        self.db = db
        self._is_stub = self._check_is_stub(db)
        self.cargos_repo = CargosEconomicosRepository(db)
        self.log_repo = CargosLogRepository(db)
        self.responsabilidad_repo = ResponsabilidadRepository(db)
        self.workflow_repo = WorkflowRepository(db)
    
    def _check_is_stub(self, db) -> bool:
        """Verifica si estamos usando StubDatabase."""
        if db is None:
            return True
        try:
            from core.mongo_stub import StubDatabase
            return isinstance(db, StubDatabase)
        except ImportError:
            return False
    
    # ==================== ELEGIBILIDAD ====================
    
    async def evaluar_elegibilidad(self, responsabilidad_id: str) -> ElegibilidadCargoResponse:
        """
        Evalúa si una responsabilidad es elegible para generar cargo.
        
        Criterios de elegibilidad:
        1. Responsabilidad existe
        2. Estado = APROBADO
        3. No existe controversia activa (EN_DISPUTA)
        4. No existe exoneración
        5. No existe cargo activo previo
        
        Returns:
            ElegibilidadCargoResponse con el resultado de la evaluación
        """
        # 1. Buscar responsabilidad
        responsabilidad = await self._obtener_responsabilidad(responsabilidad_id)
        if not responsabilidad:
            return ElegibilidadCargoResponse(
                responsabilidad_id=responsabilidad_id,
                es_elegible=False,
                motivo="Responsabilidad no encontrada"
            )
        
        estado = responsabilidad.get("estado", "")
        workflow_id = responsabilidad.get("workflow_id", "")
        monto = responsabilidad.get("monto_propuesto_mxn", 0.0)
        
        # 2. Verificar estado APROBADO
        if estado != EstadoResponsabilidad.APROBADO.value:
            if estado == EstadoResponsabilidad.EN_DISPUTA.value:
                return ElegibilidadCargoResponse(
                    responsabilidad_id=responsabilidad_id,
                    es_elegible=False,
                    motivo="Responsabilidad en disputa activa. Resuelva la controversia primero.",
                    workflow_id=workflow_id,
                    estado_responsabilidad=estado,
                    tiene_controversia_activa=True
                )
            if estado == EstadoResponsabilidad.EXONERADO.value:
                return ElegibilidadCargoResponse(
                    responsabilidad_id=responsabilidad_id,
                    es_elegible=False,
                    motivo="Responsabilidad exonerada. No es posible generar cargo.",
                    workflow_id=workflow_id,
                    estado_responsabilidad=estado,
                    tiene_exoneracion=True
                )
            if estado == EstadoResponsabilidad.RECHAZADO.value:
                return ElegibilidadCargoResponse(
                    responsabilidad_id=responsabilidad_id,
                    es_elegible=False,
                    motivo="Responsabilidad rechazada. El cargo no procedía.",
                    workflow_id=workflow_id,
                    estado_responsabilidad=estado
                )
            # Otros estados (CALCULADO, PROPUESTO)
            return ElegibilidadCargoResponse(
                responsabilidad_id=responsabilidad_id,
                es_elegible=False,
                motivo=f"Responsabilidad en estado {estado}. Debe estar APROBADO para generar cargo.",
                workflow_id=workflow_id,
                estado_responsabilidad=estado
            )
        
        # 3. Verificar que no exista cargo activo previo
        cargo_existente = await self.cargos_repo.get_cargo_activo_por_responsabilidad(responsabilidad_id)
        if cargo_existente:
            return ElegibilidadCargoResponse(
                responsabilidad_id=responsabilidad_id,
                es_elegible=False,
                motivo=f"Ya existe un cargo activo para esta responsabilidad (estatus: {cargo_existente.get('estatus_cargo')})",
                workflow_id=workflow_id,
                estado_responsabilidad=estado,
                tiene_cargo_previo=True,
                cargo_previo_id=cargo_existente.get("id")
            )
        
        # 4. Verificar monto mínimo
        if monto <= 0:
            return ElegibilidadCargoResponse(
                responsabilidad_id=responsabilidad_id,
                es_elegible=False,
                motivo="Monto propuesto es cero o negativo. No es posible generar cargo.",
                workflow_id=workflow_id,
                estado_responsabilidad=estado,
                monto_disponible=monto
            )
        
        # Elegible
        return ElegibilidadCargoResponse(
            responsabilidad_id=responsabilidad_id,
            es_elegible=True,
            motivo="Responsabilidad elegible para generar cargo económico",
            monto_disponible=monto,
            workflow_id=workflow_id,
            estado_responsabilidad=estado,
            tiene_controversia_activa=False,
            tiene_exoneracion=False,
            tiene_cargo_previo=False
        )
    
    # ==================== CREACIÓN DE CARGO ====================
    
    async def crear_propuesta_cargo(
        self,
        responsabilidad_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str
    ) -> CargoAccionResponse:
        """
        Crea una propuesta de cargo económico.
        
        Requiere que la responsabilidad sea elegible.
        Estado inicial: PENDIENTE
        
        Args:
            responsabilidad_id: ID de la responsabilidad origen
            usuario_id: Usuario que crea la propuesta
            usuario_rol: Rol del usuario
            comentario: Justificación
            
        Returns:
            CargoAccionResponse con el resultado
        """
        # Evaluar elegibilidad
        elegibilidad = await self.evaluar_elegibilidad(responsabilidad_id)
        if not elegibilidad.es_elegible:
            raise NoElegibleParaCargoError(elegibilidad.motivo)
        
        # Obtener datos de la responsabilidad
        responsabilidad = await self._obtener_responsabilidad(responsabilidad_id)
        
        now = datetime.now(timezone.utc)
        cargo_id = str(uuid.uuid4())
        
        # Crear el cargo
        datos_cargo = {
            "id": cargo_id,
            "responsabilidad_id": responsabilidad_id,
            "workflow_id": responsabilidad.get("workflow_id", ""),
            "procesado_id": responsabilidad.get("procesado_id", ""),
            "sucursal_id": responsabilidad.get("sucursal_id", ""),
            "responsable_id": responsabilidad.get("calculado_por"),  # El afectado
            "responsable_nombre": None,  # Se puede enriquecer con lookup a usuarios
            "monto_responsabilidad": responsabilidad.get("monto_propuesto_mxn", 0.0),
            "monto_aplicado": 0.0,
            "monto_revertido": 0.0,
            "estatus_cargo": EstatusCargo.PENDIENTE.value,
            "origen": OrigenCargo.RESPONSABILIDAD_ECONOMICA.value,
            "fecha_propuesta": now,
            "propuesto_por": usuario_id,
        }
        
        await self.cargos_repo.crear_cargo(datos_cargo)
        
        # Registrar en log
        log_id = await self.log_repo.registrar_log(
            cargo_id=cargo_id,
            accion=AccionCargo.CREAR.value,
            estatus_anterior="N/A",
            estatus_nuevo=EstatusCargo.PENDIENTE.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto_al_momento=datos_cargo["monto_responsabilidad"]
        )
        
        logger.info(f"Propuesta de cargo creada: {cargo_id} por {usuario_id}")
        
        return CargoAccionResponse(
            success=True,
            cargo_id=cargo_id,
            accion=AccionCargo.CREAR,
            estatus_anterior=EstatusCargo.PENDIENTE,  # N/A en creación
            estatus_nuevo=EstatusCargo.PENDIENTE,
            mensaje=f"Propuesta de cargo creada exitosamente. Monto: ${datos_cargo['monto_responsabilidad']:,.2f} MXN",
            log_id=log_id
        )
    
    # ==================== AUTORIZACIÓN ====================
    
    async def autorizar_cargo(
        self,
        cargo_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> CargoAccionResponse:
        """
        Autoriza un cargo pendiente.
        Transición: PENDIENTE → AUTORIZADO
        """
        cargo = await self._obtener_cargo(cargo_id)
        estatus_actual = cargo.get("estatus_cargo", "")
        
        await self._validar_transicion(estatus_actual, EstatusCargo.AUTORIZADO.value)
        
        monto = cargo.get("monto_responsabilidad", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, "AUTORIZAR")
        
        now = datetime.now(timezone.utc)
        await self.cargos_repo.actualizar_cargo(cargo_id, {
            "estatus_cargo": EstatusCargo.AUTORIZADO.value,
            "fecha_autorizacion": now,
            "autorizado_por": usuario_id,
        })
        
        log_id = await self.log_repo.registrar_log(
            cargo_id=cargo_id,
            accion=AccionCargo.AUTORIZAR.value,
            estatus_anterior=estatus_actual,
            estatus_nuevo=EstatusCargo.AUTORIZADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto_al_momento=monto,
            motivo_codigo=motivo_codigo
        )
        
        logger.info(f"Cargo {cargo_id} autorizado por {usuario_id}")
        
        return CargoAccionResponse(
            success=True,
            cargo_id=cargo_id,
            accion=AccionCargo.AUTORIZAR,
            estatus_anterior=EstatusCargo(estatus_actual),
            estatus_nuevo=EstatusCargo.AUTORIZADO,
            mensaje=f"Cargo autorizado exitosamente. Monto: ${monto:,.2f} MXN. Pendiente aplicación.",
            log_id=log_id
        )
    
    # ==================== APLICACIÓN ====================
    
    async def aplicar_cargo(
        self,
        cargo_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> CargoAccionResponse:
        """
        Aplica formalmente un cargo autorizado.
        Transición: AUTORIZADO → APLICADO
        
        Este es el punto de no retorno. El cargo queda registrado
        para integración con nómina/ERP.
        """
        cargo = await self._obtener_cargo(cargo_id)
        estatus_actual = cargo.get("estatus_cargo", "")
        
        await self._validar_transicion(estatus_actual, EstatusCargo.APLICADO.value)
        
        monto = cargo.get("monto_responsabilidad", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, "APLICAR")
        
        now = datetime.now(timezone.utc)
        await self.cargos_repo.actualizar_cargo(cargo_id, {
            "estatus_cargo": EstatusCargo.APLICADO.value,
            "fecha_aplicacion": now,
            "aplicado_por": usuario_id,
            "monto_aplicado": monto,  # Se registra el monto aplicado
        })
        
        log_id = await self.log_repo.registrar_log(
            cargo_id=cargo_id,
            accion=AccionCargo.APLICAR.value,
            estatus_anterior=estatus_actual,
            estatus_nuevo=EstatusCargo.APLICADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto_al_momento=monto,
            motivo_codigo=motivo_codigo
        )
        
        # Actualizar estado del workflow a CERRADO
        workflow_id = cargo.get("workflow_id")
        if workflow_id:
            await self._cerrar_workflow_si_corresponde(workflow_id, cargo_id)
        
        # NOTIFICACIÓN: Alertar al responsable del cargo aplicado (NO debe romper el flujo)
        await self._notificar_cargo_aplicado(cargo, monto)
        
        logger.info(f"Cargo {cargo_id} APLICADO por {usuario_id}. Monto: ${monto:,.2f}")
        
        return CargoAccionResponse(
            success=True,
            cargo_id=cargo_id,
            accion=AccionCargo.APLICAR,
            estatus_anterior=EstatusCargo(estatus_actual),
            estatus_nuevo=EstatusCargo.APLICADO,
            mensaje=f"Cargo APLICADO formalmente. Monto: ${monto:,.2f} MXN. Listo para integración con nómina.",
            log_id=log_id
        )
    
    # ==================== RECHAZO ====================
    
    async def rechazar_cargo(
        self,
        cargo_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> CargoAccionResponse:
        """
        Rechaza un cargo pendiente.
        Transición: PENDIENTE → RECHAZADO
        
        El cargo no procedía según la evaluación.
        """
        cargo = await self._obtener_cargo(cargo_id)
        estatus_actual = cargo.get("estatus_cargo", "")
        
        await self._validar_transicion(estatus_actual, EstatusCargo.RECHAZADO.value)
        
        monto = cargo.get("monto_responsabilidad", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, "RECHAZAR")
        
        await self.cargos_repo.actualizar_cargo(cargo_id, {
            "estatus_cargo": EstatusCargo.RECHAZADO.value,
        })
        
        log_id = await self.log_repo.registrar_log(
            cargo_id=cargo_id,
            accion=AccionCargo.RECHAZAR.value,
            estatus_anterior=estatus_actual,
            estatus_nuevo=EstatusCargo.RECHAZADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto_al_momento=monto,
            motivo_codigo=motivo_codigo
        )
        
        logger.info(f"Cargo {cargo_id} RECHAZADO por {usuario_id}")
        
        return CargoAccionResponse(
            success=True,
            cargo_id=cargo_id,
            accion=AccionCargo.RECHAZAR,
            estatus_anterior=EstatusCargo(estatus_actual),
            estatus_nuevo=EstatusCargo.RECHAZADO,
            mensaje=f"Cargo RECHAZADO. El cargo de ${monto:,.2f} MXN no procedía.",
            log_id=log_id
        )
    
    # ==================== REVERSA ====================
    
    async def revertir_cargo(
        self,
        cargo_id: str,
        usuario_id: str,
        usuario_rol: str,
        motivo_reversa: str,
        motivo_codigo: Optional[str] = None
    ) -> CargoAccionResponse:
        """
        Revierte un cargo ya aplicado.
        Transición: APLICADO → REVERTIDO
        
        Operación crítica que requiere:
        - Motivo detallado (mínimo 20 caracteres)
        - Rol de autorización suficiente
        - Registro completo de auditoría
        """
        cargo = await self._obtener_cargo(cargo_id)
        estatus_actual = cargo.get("estatus_cargo", "")
        
        await self._validar_transicion(estatus_actual, EstatusCargo.REVERTIDO.value)
        
        monto = cargo.get("monto_aplicado", cargo.get("monto_responsabilidad", 0))
        
        # Reversa siempre requiere nivel alto
        if self.JERARQUIA_ROLES.get(usuario_rol, 0) < self.JERARQUIA_ROLES["GERENTE_OPS"]:
            raise PermisoInsuficienteError(
                f"Reversa de cargo requiere rol GERENTE_OPS o superior. Tu rol: {usuario_rol}"
            )
        
        now = datetime.now(timezone.utc)
        await self.cargos_repo.actualizar_cargo(cargo_id, {
            "estatus_cargo": EstatusCargo.REVERTIDO.value,
            "fecha_reversa": now,
            "revertido_por": usuario_id,
            "monto_revertido": monto,
        })
        
        log_id = await self.log_repo.registrar_log(
            cargo_id=cargo_id,
            accion=AccionCargo.REVERTIR.value,
            estatus_anterior=estatus_actual,
            estatus_nuevo=EstatusCargo.REVERTIDO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=motivo_reversa,
            monto_al_momento=monto,
            motivo_codigo=motivo_codigo
        )
        
        logger.warning(f"REVERSA DE CARGO {cargo_id} por {usuario_id}. Monto: ${monto:,.2f}. Motivo: {motivo_reversa[:50]}...")
        
        return CargoAccionResponse(
            success=True,
            cargo_id=cargo_id,
            accion=AccionCargo.REVERTIR,
            estatus_anterior=EstatusCargo(estatus_actual),
            estatus_nuevo=EstatusCargo.REVERTIDO,
            mensaje=f"Cargo REVERTIDO. Monto revertido: ${monto:,.2f} MXN.",
            log_id=log_id
        )
    
    # ==================== CANCELACIÓN ====================
    
    async def cancelar_cargo(
        self,
        cargo_id: str,
        usuario_id: str,
        usuario_rol: str,
        comentario: str,
        motivo_codigo: Optional[str] = None
    ) -> CargoAccionResponse:
        """
        Cancela un cargo antes de ser aplicado.
        Transiciones válidas: PENDIENTE/AUTORIZADO → CANCELADO
        """
        cargo = await self._obtener_cargo(cargo_id)
        estatus_actual = cargo.get("estatus_cargo", "")
        
        await self._validar_transicion(estatus_actual, EstatusCargo.CANCELADO.value)
        
        monto = cargo.get("monto_responsabilidad", 0)
        await self._validar_permiso_por_monto(monto, usuario_rol, "CANCELAR")
        
        await self.cargos_repo.actualizar_cargo(cargo_id, {
            "estatus_cargo": EstatusCargo.CANCELADO.value,
        })
        
        log_id = await self.log_repo.registrar_log(
            cargo_id=cargo_id,
            accion=AccionCargo.CANCELAR.value,
            estatus_anterior=estatus_actual,
            estatus_nuevo=EstatusCargo.CANCELADO.value,
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            comentario=comentario,
            monto_al_momento=monto,
            motivo_codigo=motivo_codigo
        )
        
        logger.info(f"Cargo {cargo_id} CANCELADO por {usuario_id}")
        
        return CargoAccionResponse(
            success=True,
            cargo_id=cargo_id,
            accion=AccionCargo.CANCELAR,
            estatus_anterior=EstatusCargo(estatus_actual),
            estatus_nuevo=EstatusCargo.CANCELADO,
            mensaje=f"Cargo CANCELADO. El cargo de ${monto:,.2f} MXN no será aplicado.",
            log_id=log_id
        )
    
    # ==================== CONSULTAS ====================
    
    async def obtener_cargo(self, cargo_id: str) -> CargoEconomicoResponse:
        """Obtiene un cargo por su ID."""
        cargo = await self._obtener_cargo(cargo_id)
        return self._mapear_a_response(cargo)
    
    async def obtener_cargo_por_responsabilidad(self, responsabilidad_id: str) -> Optional[CargoEconomicoResponse]:
        """Obtiene el cargo asociado a una responsabilidad."""
        cargo = await self.cargos_repo.get_by_responsabilidad(responsabilidad_id)
        return self._mapear_a_response(cargo) if cargo else None
    
    async def listar_cargos(
        self,
        estatus: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        responsable_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """Lista cargos con filtros."""
        resultado = await self.cargos_repo.listar_con_filtros(
            estatus=estatus,
            sucursal_id=sucursal_id,
            responsable_id=responsable_id,
            workflow_id=workflow_id,
            skip=skip,
            limit=limit
        )
        
        items = [self._mapear_a_response(c) for c in resultado["items"]]
        return {"total": resultado["total"], "items": items}
    
    async def obtener_pendientes_autorizacion(self) -> CargosPendientesResponse:
        """Obtiene cargos pendientes de autorización."""
        resultado = await self.cargos_repo.listar_con_filtros(
            estatus=EstatusCargo.PENDIENTE.value,
            limit=100
        )
        
        monto_total = sum(c.get("monto_responsabilidad", 0) for c in resultado["items"])
        items = [self._mapear_a_response(c) for c in resultado["items"]]
        
        return CargosPendientesResponse(
            total=resultado["total"],
            monto_total_pendiente=round(monto_total, 2),
            items=items
        )
    
    async def obtener_aplicados(self) -> CargosAplicadosResponse:
        """Obtiene cargos aplicados."""
        resultado = await self.cargos_repo.listar_con_filtros(
            estatus=EstatusCargo.APLICADO.value,
            limit=100
        )
        
        monto_total = sum(c.get("monto_aplicado", 0) for c in resultado["items"])
        items = [self._mapear_a_response(c) for c in resultado["items"]]
        
        return CargosAplicadosResponse(
            total=resultado["total"],
            monto_total_aplicado=round(monto_total, 2),
            items=items
        )
    
    async def obtener_log_cargo(self, cargo_id: str) -> CargoLogListResponse:
        """Obtiene el historial de log de un cargo."""
        # Verificar que el cargo existe
        await self._obtener_cargo(cargo_id)
        
        logs = await self.log_repo.get_by_cargo(cargo_id)
        items = [
            CargoLogResponse(
                id=log.get("id", ""),
                cargo_id=log.get("cargo_id", ""),
                accion=log.get("accion", ""),
                estatus_anterior=log.get("estatus_anterior", ""),
                estatus_nuevo=log.get("estatus_nuevo", ""),
                usuario_id=log.get("usuario_id", ""),
                usuario_rol=log.get("usuario_rol"),
                comentario=log.get("comentario", ""),
                motivo_codigo=log.get("motivo_codigo"),
                monto_al_momento=log.get("monto_al_momento", 0),
                fecha=log.get("fecha", datetime.now(timezone.utc)),
                ip_address=log.get("ip_address"),
                user_agent=log.get("user_agent"),
            )
            for log in logs
        ]
        
        return CargoLogListResponse(
            cargo_id=cargo_id,
            total=len(items),
            items=items
        )
    
    async def obtener_metricas(self) -> CargosMetricasResponse:
        """Obtiene métricas agregadas de cargos."""
        metricas_base = await self.cargos_repo.obtener_metricas()
        por_estatus = await self.cargos_repo.contar_por_estatus()
        monto_autorizado = await self.cargos_repo.obtener_monto_autorizado_total()
        
        return CargosMetricasResponse(
            total_cargos=metricas_base.get("total_cargos", 0),
            por_estatus=por_estatus,
            monto_total_propuesto=round(metricas_base.get("monto_total_propuesto", 0), 2),
            monto_total_autorizado=round(monto_autorizado, 2),
            monto_total_aplicado=round(metricas_base.get("monto_total_aplicado", 0), 2),
            monto_total_revertido=round(metricas_base.get("monto_total_revertido", 0), 2),
            promedio_tiempo_autorizacion_horas=None,  # TODO: Calcular
            promedio_tiempo_aplicacion_horas=None,    # TODO: Calcular
        )
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    async def _obtener_responsabilidad(self, responsabilidad_id: str) -> Optional[Dict]:
        """Obtiene un registro de responsabilidad (FASE B-P2: SQL)."""
        registro = await self.responsabilidad_repo.get_by_id(responsabilidad_id)
        if not registro:
            # FASE B-P2: Usar método SQL de repositorio
            registro = self.responsabilidad_repo.find_one({"id": responsabilidad_id})
        return registro
    
    async def _obtener_cargo(self, cargo_id: str) -> Dict:
        """Obtiene un cargo o lanza excepción."""
        cargo = await self.cargos_repo.get_by_id(cargo_id)
        if not cargo:
            raise CargoNoEncontradoError(f"Cargo no encontrado: {cargo_id}")
        return cargo
    
    async def _validar_transicion(self, estatus_actual: str, estatus_nuevo: str):
        """Valida que la transición de estado sea válida."""
        try:
            estatus_actual_enum = EstatusCargo(estatus_actual)
            estatus_nuevo_enum = EstatusCargo(estatus_nuevo)
        except ValueError as e:
            raise TransicionInvalidaError(f"Estado inválido: {e}")
        
        transiciones_permitidas = TRANSICIONES_CARGO_VALIDAS.get(estatus_actual_enum, [])
        if estatus_nuevo_enum not in transiciones_permitidas:
            raise TransicionInvalidaError(
                f"Transición no válida: {estatus_actual} → {estatus_nuevo}. "
                f"Transiciones permitidas: {[t.value for t in transiciones_permitidas]}"
            )
    
    async def _validar_permiso_por_monto(self, monto: float, usuario_rol: str, accion: str):
        """Valida que el usuario tenga permiso según el monto y su rol."""
        if monto <= self.UMBRAL_SUPERVISOR:
            nivel_requerido = "SUPERVISOR"
        elif monto <= self.UMBRAL_GERENTE:
            nivel_requerido = "GERENTE_OPS"
        else:
            nivel_requerido = "DIRECCION"
        
        nivel_usuario = self.JERARQUIA_ROLES.get(usuario_rol, 0)
        nivel_necesario = self.JERARQUIA_ROLES.get(nivel_requerido, 3)
        
        if nivel_usuario < nivel_necesario:
            raise PermisoInsuficienteError(
                f"Permiso insuficiente para {accion}. Monto ${monto:,.2f} requiere rol {nivel_requerido} o superior. "
                f"Tu rol: {usuario_rol}"
            )
    
    async def _cerrar_workflow_si_corresponde(self, workflow_id: str, cargo_id: str):
        """Cierra el workflow si el cargo fue aplicado (FASE B-P2: SQL)."""
        try:
            # FASE B-P2: Usar método SQL de repositorio
            result = self.workflow_repo.find_one_and_update(
                {"id": workflow_id},
                {"$set": {
                    "estado_workflow": "CERRADO",
                    "cerrado_por_cargo": cargo_id,
                    "fecha_ultima_actualizacion": datetime.now(timezone.utc)
                }},
                return_document=True
            )
            if result:
                logger.info(f"Workflow {workflow_id} cerrado tras aplicación de cargo {cargo_id}")
        except Exception as e:
            logger.warning(f"No se pudo cerrar workflow {workflow_id}: {e}")

    async def _notificar_cargo_aplicado(self, cargo: Dict, monto: float):
        """
        Envía notificación de cargo aplicado al responsable.
        
        IMPORTANTE: Esta función NO debe lanzar excepciones.
        El cargo ya fue aplicado, la notificación es complementaria.
        """
        try:
            from .notification_service import get_notification_service
            
            notification_service = get_notification_service(self.db)
            
            # Obtener datos del responsable
            responsable_id = cargo.get("responsable_id")
            if not responsable_id:
                logger.debug("Cargo sin responsable_id, notificación omitida")
                return
            
            # FASE B-P2: En arquitectura SQL-only, notificaciones se basan en datos del cargo
            # No consultamos MongoDB para usuarios/workflows - usamos datos ya disponibles
            logger.debug("[CARGOS] Modo SQL-only: notificación simplificada")
            
            # Obtener nombre de sucursal del cargo si está disponible
            sucursal_nombre = cargo.get("sucursal_nombre", "Sucursal")
            responsable_nombre = cargo.get("responsable_nombre", "Usuario")
            workflow_id = cargo.get("workflow_id", "")
            
            await notification_service.notificar_cargo_aplicado(
                cargo_id=cargo.get("id", ""),
                workflow_id=workflow_id,
                responsable_nombre=responsable_nombre,
                monto_aplicado=monto,
                sucursal_nombre=sucursal_nombre,
                destinatario_email=usuario.get("email"),
                destinatario_nombre=usuario.get("name", "Usuario")
            )
            
            logger.info(f"Notificación de cargo aplicado enviada a {usuario.get('email')}")
            
        except Exception as e:
            # NO romper el flujo si falla la notificación
            logger.error(f"Error enviando notificación de cargo (no crítico): {e}")

    
    def _mapear_a_response(self, cargo: Dict) -> CargoEconomicoResponse:
        """Mapea un documento de BD a CargoEconomicoResponse."""
        return CargoEconomicoResponse(
            id=cargo.get("id", ""),
            responsabilidad_id=cargo.get("responsabilidad_id", ""),
            workflow_id=cargo.get("workflow_id", ""),
            procesado_id=cargo.get("procesado_id", ""),
            sucursal_id=cargo.get("sucursal_id", ""),
            responsable_id=cargo.get("responsable_id"),
            responsable_nombre=cargo.get("responsable_nombre"),
            monto_responsabilidad=cargo.get("monto_responsabilidad", 0),
            monto_aplicado=cargo.get("monto_aplicado", 0),
            monto_revertido=cargo.get("monto_revertido", 0),
            estatus_cargo=EstatusCargo(cargo.get("estatus_cargo", "PENDIENTE")),
            origen=OrigenCargo(cargo.get("origen", "RESPONSABILIDAD_ECONOMICA")),
            fecha_propuesta=cargo.get("fecha_propuesta", datetime.now(timezone.utc)),
            fecha_autorizacion=cargo.get("fecha_autorizacion"),
            fecha_aplicacion=cargo.get("fecha_aplicacion"),
            fecha_reversa=cargo.get("fecha_reversa"),
            propuesto_por=cargo.get("propuesto_por", ""),
            autorizado_por=cargo.get("autorizado_por"),
            aplicado_por=cargo.get("aplicado_por"),
            revertido_por=cargo.get("revertido_por"),
            fecha_creacion=cargo.get("fecha_creacion", datetime.now(timezone.utc)),
            fecha_actualizacion=cargo.get("fecha_actualizacion", datetime.now(timezone.utc)),
        )
