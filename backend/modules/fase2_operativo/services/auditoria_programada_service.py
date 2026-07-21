from core.unidades_service import UnidadesService
"""
Servicio de Auditorías Programadas (Sync)
EDARSA HUB - Módulo Auditorías Programadas

Usa EDARSAHUB SQL Server; MongoDB queda sustituido por StubDatabase legacy.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import pytz
import logging

from ..access import resolve_unidad_pk
from ..repositories.auditoria_programada_repository import AuditoriaProgramadaRepository
from ..schemas.auditoria_programada_schemas import (
    AuditoriaProgramada,
    AuditoriaProgramadaCreate,
    AuditoriaProgramadaUpdate,
    AuditoriaProgramadaLog,
    FrecuenciaAuditoria,
    EstadoEjecucion,
)

logger = logging.getLogger(__name__)


class AuditoriaProgramadaError(Exception):
    pass

class AuditoriaNoEncontradaError(AuditoriaProgramadaError):
    pass

class EjecucionDuplicadaError(AuditoriaProgramadaError):
    pass

class ConfiguracionInvalidaError(AuditoriaProgramadaError):
    pass


class AuditoriaProgramadaService:
    """
    Servicio para gestión de auditorías programadas (sync).
    
    MIGRACIÓN SQL SERVER (Mayo 2026):
    - Operaciones críticas migradas a SQL
    - MongoDB pasa por StubDatabase
    """
    
    def __init__(self, db):
        self.db = db
        self._is_stub = self._check_is_stub(db)
        self.repo = AuditoriaProgramadaRepository(db)

    def _scope(
        self,
        unidad_negocio_pk: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Optional[List[str]]:
        if unidad_negocio_pk:
            return [unidad_negocio_pk]
        return unidades_permitidas

    def _canonical_fields_from_ref(self, unidad_ref: Optional[str]) -> Dict:
        unidad_pk = resolve_unidad_pk(unidad_ref)
        if not unidad_pk:
            raise ConfiguracionInvalidaError(
                "unidad_negocio_pk canonica requerida o invalida"
            )

        unit = UnidadesService.get_by_pk(unidad_pk)
        if not unit:
            raise ConfiguracionInvalidaError(
                "unidad_negocio_pk canonica requerida o invalida"
            )

        return {
            "unidad_negocio_pk": unidad_pk,
            "unidad_negocio_codigo": unit.get("codigo") or unit.get("unidad_negocio_codigo"),
            "unidad_negocio_nombre": unit.get("nombre") or unit.get("unidad_negocio_nombre"),
            "server_id": unit.get("server_id"),
            "sucursal_id": unit.get("sucursal_origen_id") or unit.get("codigo") or unidad_pk,
            "sucursal_nombre": unit.get("nombre") or unit.get("unidad_negocio_nombre"),
        }
    
    def _check_is_stub(self, db) -> bool:
        """Verifica si estamos usando StubDatabase."""
        if db is None:
            return True
        try:
            from core.mongo_stub import StubDatabase
            return isinstance(db, StubDatabase)
        except ImportError:
            return False
    
    def crear(
        self,
        data: AuditoriaProgramadaCreate,
        unidad_negocio_pk: Optional[str] = None,
    ) -> Dict:
        """Crea una nueva auditoria programada."""
        self._validar_configuracion(data)

        unit_fields = self._canonical_fields_from_ref(
            unidad_negocio_pk
            or data.unidad_negocio_pk
            or data.sucursal_id
            or data.server_id
        )

        proxima = self._calcular_proxima_ejecucion(
            frecuencia=data.frecuencia,
            dia_semana=data.dia_semana,
            dia_mes=data.dia_mes,
            hora=data.hora_ejecucion,
            tz=data.timezone
        )

        auditoria = AuditoriaProgramada(
            nombre=data.nombre,
            descripcion=data.descripcion,
            unidad_negocio_pk=unit_fields["unidad_negocio_pk"],
            server_id=unit_fields["server_id"],
            sucursal_id=unit_fields["sucursal_id"],
            sucursal_nombre=unit_fields["sucursal_nombre"],
            almacenes=data.almacenes,
            tipo_auditoria=data.tipo_auditoria,
            frecuencia=data.frecuencia,
            dia_semana=data.dia_semana,
            dia_mes=data.dia_mes,
            hora_ejecucion=data.hora_ejecucion,
            timezone=data.timezone,
            proxima_ejecucion=proxima,
            usuario_responsable_id=data.usuario_responsable_id,
            rol_responsable=data.rol_responsable,
            observaciones=data.observaciones,
            created_by=data.created_by
        )

        payload = auditoria.model_dump()
        payload.update(unit_fields)
        return self.repo.create(payload)

    def obtener(
        self,
        auditoria_id: str,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Obtiene una auditoria por ID respetando alcance."""
        auditoria = self.repo.get_by_id(auditoria_id, unidades_permitidas)
        if not auditoria:
            raise AuditoriaNoEncontradaError(f"Auditoría no encontrada: {auditoria_id}")
        return auditoria

    def listar(
        self,
        sucursal_id: Optional[str] = None,
        solo_activas: bool = False,
        unidad_negocio_pk: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Lista auditorias programadas respetando alcance."""
        scope = self._scope(unidad_negocio_pk, unidades_permitidas)
        if solo_activas:
            return self.repo.get_activas(scope)
        if sucursal_id:
            return self.repo.get_by_sucursal(sucursal_id, scope)
        return self.repo.get_all(scope)

    def actualizar(
        self,
        auditoria_id: str,
        data: AuditoriaProgramadaUpdate,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Actualiza una auditoria programada respetando alcance."""
        auditoria = self.obtener(auditoria_id, unidades_permitidas)
        update_data = data.model_dump(exclude_unset=True)

        unidad_ref = (
            update_data.get("unidad_negocio_pk")
            or update_data.get("sucursal_id")
            or update_data.get("server_id")
        )
        if unidad_ref:
            update_data.update(self._canonical_fields_from_ref(unidad_ref))

        if any(k in update_data for k in ['frecuencia', 'dia_semana', 'dia_mes', 'hora_ejecucion', 'timezone']):
            frecuencia = update_data.get('frecuencia', auditoria.get('frecuencia'))
            if frecuencia != FrecuenciaAuditoria.MANUAL.value:
                proxima = self._calcular_proxima_ejecucion(
                    frecuencia=frecuencia,
                    dia_semana=update_data.get('dia_semana', auditoria.get('dia_semana')),
                    dia_mes=update_data.get('dia_mes', auditoria.get('dia_mes')),
                    hora=update_data.get('hora_ejecucion', auditoria.get('hora_ejecucion')),
                    tz=update_data.get('timezone', auditoria.get('timezone'))
                )
                update_data['proxima_ejecucion'] = proxima if proxima else None

        update_data['updated_at'] = datetime.now(timezone.utc)
        return self.repo.update(auditoria_id, update_data)

    def eliminar(
        self,
        auditoria_id: str,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> bool:
        """Elimina una auditoria programada respetando alcance."""
        self.obtener(auditoria_id, unidades_permitidas)
        return self.repo.delete(auditoria_id)

    def activar(
        self,
        auditoria_id: str,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Activa una auditoria."""
        auditoria = self.obtener(auditoria_id, unidades_permitidas)

        if auditoria.get('frecuencia') != FrecuenciaAuditoria.MANUAL.value:
            proxima = self._calcular_proxima_ejecucion(
                frecuencia=auditoria.get('frecuencia'),
                dia_semana=auditoria.get('dia_semana'),
                dia_mes=auditoria.get('dia_mes'),
                hora=auditoria.get('hora_ejecucion'),
                tz=auditoria.get('timezone')
            )
            self.repo.update(auditoria_id, {
                'proxima_ejecucion': proxima if proxima else None
            })
        
        self.repo.activar(auditoria_id)
        return self.obtener(auditoria_id, unidades_permitidas)

    def desactivar(
        self,
        auditoria_id: str,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Desactiva una auditoria."""
        self.obtener(auditoria_id, unidades_permitidas)
        self.repo.desactivar(auditoria_id)
        return self.obtener(auditoria_id, unidades_permitidas)

    def ejecutar_manual(
        self,
        auditoria_id: str,
        usuario_id: str,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Ejecuta una auditoria manualmente."""
        auditoria = self.obtener(auditoria_id, unidades_permitidas)
        fecha_programada = datetime.now(timezone.utc)
        
        if self.repo.verificar_ejecucion_duplicada(auditoria_id, fecha_programada, ventana_minutos=30):
            raise EjecucionDuplicadaError("Ya existe una ejecución reciente")
        
        return self._ejecutar_auditoria(auditoria, fecha_programada, usuario_id)
    
    def ejecutar_programada(self, auditoria_id: str, fecha_programada: datetime) -> Dict:
        """Ejecuta una auditoría programada (scheduler)."""
        auditoria = self.obtener(auditoria_id)
        
        if self.repo.verificar_ejecucion_duplicada(auditoria_id, fecha_programada):
            return {"status": "duplicada", "mensaje": "Ejecución ya procesada"}
        
        return self._ejecutar_auditoria(auditoria, fecha_programada, "SCHEDULER")
    
    def _ejecutar_auditoria(self, auditoria: Dict, fecha_programada: datetime, disparado_por: str) -> Dict:
        """Lógica interna de ejecución."""
        inicio = datetime.now(timezone.utc)
        log_data = {
            "auditoria_programada_id": auditoria["id"],
            "fecha_programada": fecha_programada.isoformat(),
            "fecha_ejecucion": inicio.isoformat(),
            "disparado_por": disparado_por,
            "estado": EstadoEjecucion.EN_PROGRESO.value
        }
        
        try:
            workflow_id = self._crear_workflow_inventario(auditoria)
            
            duracion = int((datetime.now(timezone.utc) - inicio).total_seconds() * 1000)
            log_data.update({
                "workflow_id": workflow_id,
                "estado": EstadoEjecucion.COMPLETADA.value,
                "mensaje": f"Workflow creado: {workflow_id}",
                "duracion_ms": duracion
            })
            
            if auditoria.get("frecuencia") != FrecuenciaAuditoria.MANUAL.value:
                proxima = self._calcular_proxima_ejecucion(
                    frecuencia=auditoria.get("frecuencia"),
                    dia_semana=auditoria.get("dia_semana"),
                    dia_mes=auditoria.get("dia_mes"),
                    hora=auditoria.get("hora_ejecucion"),
                    tz=auditoria.get("timezone")
                )
            else:
                proxima = None
            
            self.repo.actualizar_ejecucion(auditoria["id"], EstadoEjecucion.COMPLETADA.value, proxima)
            
        except Exception as e:
            duracion = int((datetime.now(timezone.utc) - inicio).total_seconds() * 1000)
            log_data.update({
                "estado": EstadoEjecucion.FALLIDA.value,
                "error_detalle": str(e),
                "duracion_ms": duracion
            })
            self.repo.actualizar_ejecucion(auditoria["id"], EstadoEjecucion.FALLIDA.value)
            logger.error(f"Error ejecutando auditoría {auditoria['id']}: {e}")
        
        log = AuditoriaProgramadaLog(**log_data)
        self.repo.crear_log(log.model_dump())
        
        return log_data
    
    def _crear_workflow_inventario(self, auditoria: Dict) -> str:
        """Crea workflow de inventario en SQL desde una unidad canonica."""
        from ..schemas.enums import EstadoWorkflow
        import uuid

        now = datetime.now(timezone.utc)

        workflow_data = {
            "id": str(uuid.uuid4()),
            "server_id": auditoria.get("server_id"),
            "sucursal_id": auditoria.get("sucursal_id"),
            "sucursal_nombre": auditoria.get("sucursal_nombre"),
            "estado_workflow": EstadoWorkflow.PENDIENTE_ASIGNACION.value,
            "fecha_creacion": now,
            "fecha_ultima_actualizacion": now,
            "notas": {
                "unidad_negocio_pk": auditoria.get("unidad_negocio_pk"),
                "tipo_origen": f"AUDITORIA_PROGRAMADA:{auditoria['tipo_auditoria']}",
                "auditoria_programada_id": auditoria["id"],
                "almacenes": auditoria.get("almacenes", []),
                "created_by": auditoria.get("created_by", "SCHEDULER"),
                "observaciones": f"Generado automáticamente - {auditoria['nombre']}",
            },
        }
        
        # FASE B-P2: Usar repositorio SQL para crear workflow
        from ..repositories.sql_base_repository import SQLBaseRepository
        workflow_repo = SQLBaseRepository("workflow_inventarios")
        workflow_repo.insert_one(workflow_data)
        logger.info(f"Workflow creado desde auditoría programada: {workflow_data['id']}")
        
        return workflow_data["id"]
    
    def obtener_kpis(
        self,
        unidad_negocio_pk: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Obtiene KPIs de auditorias programadas."""
        ahora = datetime.now(timezone.utc)
        scope = self._scope(unidad_negocio_pk, unidades_permitidas)

        conteo = self.repo.contar_por_estado(scope)

        fin_hoy = ahora.replace(hour=23, minute=59, second=59)
        pendientes_hoy = self.repo.get_pendientes_ejecucion(fin_hoy, scope)

        logs_mes = self.repo.contar_logs_mes(ahora.year, ahora.month, scope)

        proximas = self.repo.get_proximas_24h(scope)
        
        total_logs = sum(logs_mes.values())
        completadas = logs_mes.get("COMPLETADA", 0)
        tasa = (completadas / total_logs * 100) if total_logs > 0 else 100.0
        
        # Contar auditorías en_curso desde logs (EN_PROGRESO)
        en_curso = logs_mes.get("EN_PROGRESO", 0)
        
        return {
            "total_programadas": conteo["activas"] + conteo["inactivas"],
            "activas": conteo["activas"],
            "inactivas": conteo["inactivas"],
            "pendientes_hoy": len(pendientes_hoy),
            "en_curso": en_curso,
            "completadas_mes": logs_mes.get("COMPLETADA", 0),
            "fallidas_mes": logs_mes.get("FALLIDA", 0),
            "tasa_cumplimiento": round(tasa, 1),
            "proximas_24h": [
                {
                    "id": a["id"],
                    "nombre": a["nombre"],
                    "sucursal_nombre": a["sucursal_nombre"],
                    "proxima_ejecucion": a["proxima_ejecucion"]
                }
                for a in proximas[:5]
            ]
        }
    
    def obtener_calendario(
        self,
        anio: int,
        mes: int,
        unidad_negocio_pk: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> Dict:
        """Obtiene vista calendario."""
        scope = self._scope(unidad_negocio_pk, unidades_permitidas)
        auditorias = self.repo.get_calendario(anio, mes, scope)
        
        eventos_por_dia = {}
        for a in auditorias:
            if a.get("proxima_ejecucion"):
                fecha = a["proxima_ejecucion"][:10]
                if fecha not in eventos_por_dia:
                    eventos_por_dia[fecha] = []
                eventos_por_dia[fecha].append({
                    "id": a["id"],
                    "nombre": a["nombre"],
                    "sucursal_nombre": a["sucursal_nombre"],
                    "tipo_auditoria": a["tipo_auditoria"],
                    "hora_ejecucion": a["hora_ejecucion"]
                })
        
        return {
            "eventos": [{"fecha": f, "auditorias": items} for f, items in sorted(eventos_por_dia.items())],
            "mes": mes,
            "anio": anio
        }
    
    def obtener_historial(
        self,
        auditoria_id: Optional[str] = None,
        estado: Optional[str] = None,
        dias: int = 30,
        limit: int = 100,
        unidad_negocio_pk: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene historial de ejecuciones."""
        desde = datetime.now(timezone.utc) - timedelta(days=dias)
        scope = self._scope(unidad_negocio_pk, unidades_permitidas)
        return self.repo.get_logs(
            auditoria_id=auditoria_id,
            estado=estado,
            desde=desde,
            limit=limit,
            unidad_negocio_pks=scope,
        )

    def _validar_configuracion(self, data: AuditoriaProgramadaCreate):
        """Valida configuración según frecuencia."""
        if data.frecuencia == FrecuenciaAuditoria.SEMANAL and data.dia_semana is None:
            raise ConfiguracionInvalidaError("SEMANAL requiere dia_semana")
        if data.frecuencia == FrecuenciaAuditoria.MENSUAL and data.dia_mes is None:
            raise ConfiguracionInvalidaError("MENSUAL requiere dia_mes")
    
    def _calcular_proxima_ejecucion(
        self, frecuencia: str, dia_semana: Optional[int],
        dia_mes: Optional[int], hora: str, tz: str
    ) -> Optional[datetime]:
        """Calcula próxima fecha de ejecución."""
        if frecuencia == FrecuenciaAuditoria.MANUAL.value:
            return None
        
        try:
            zona = pytz.timezone(tz)
        except Exception:
            zona = pytz.timezone("America/Mexico_City")
        
        ahora = datetime.now(zona)
        hora_parts = hora.split(":")
        hora_int, minuto_int = int(hora_parts[0]), int(hora_parts[1])
        
        if frecuencia == FrecuenciaAuditoria.DIARIA.value:
            proxima = ahora.replace(hour=hora_int, minute=minuto_int, second=0, microsecond=0)
            if proxima <= ahora:
                proxima += timedelta(days=1)
        
        elif frecuencia == FrecuenciaAuditoria.SEMANAL.value:
            dias_hasta = (dia_semana - ahora.weekday()) % 7
            if dias_hasta == 0:
                proxima_candidata = ahora.replace(hour=hora_int, minute=minuto_int, second=0, microsecond=0)
                if proxima_candidata <= ahora:
                    dias_hasta = 7
            proxima = ahora + timedelta(days=dias_hasta)
            proxima = proxima.replace(hour=hora_int, minute=minuto_int, second=0, microsecond=0)
        
        elif frecuencia == FrecuenciaAuditoria.QUINCENAL.value:
            if ahora.day < 15:
                proxima = ahora.replace(day=15, hour=hora_int, minute=minuto_int, second=0, microsecond=0)
            else:
                proxima = (ahora + relativedelta(months=1)).replace(day=1, hour=hora_int, minute=minuto_int, second=0, microsecond=0)
            if proxima <= ahora:
                proxima = proxima.replace(day=15) if proxima.day == 1 else (proxima + relativedelta(months=1)).replace(day=1)
        
        elif frecuencia == FrecuenciaAuditoria.MENSUAL.value:
            dia_real = min(dia_mes, 28)
            proxima = ahora.replace(day=dia_real, hour=hora_int, minute=minuto_int, second=0, microsecond=0)
            if proxima <= ahora:
                proxima = proxima + relativedelta(months=1)
        else:
            return None
        
        return proxima.astimezone(timezone.utc)
