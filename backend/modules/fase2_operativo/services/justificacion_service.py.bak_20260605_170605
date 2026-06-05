"""
Servicio de Justificaciones de Inventario
CAB-003 | EDARSA HUB - Fase 2A

Encapsula la lógica de negocio para gestión de justificaciones
con modelo híbrido (SIMPLE/COMPLETA según umbral).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from ..repositories.justificacion_repository import JustificacionRepository
from ..repositories.configuracion_repository import ConfiguracionRepository
from ..repositories.detalle_diferencias_repository import DetalleDiferenciasRepository
from ..schemas.enums import TipoJustificacion


class JustificacionServiceError(Exception):
    """Excepción base para errores del servicio de justificaciones."""
    pass


class JustificacionInvalidaError(JustificacionServiceError):
    """La justificación no cumple con los requisitos."""
    pass


class EvidenciaRequeridaError(JustificacionServiceError):
    """Se requiere evidencia documental para justificación COMPLETA."""
    pass


class JustificacionYaExisteError(JustificacionServiceError):
    """Ya existe una justificación para esta diferencia."""
    pass


class JustificacionService:
    """
    Servicio para gestión de justificaciones de inventario.
    
    Implementa el modelo híbrido de justificación:
    - SIMPLE: Solo texto (diferencia <= umbral)
    - COMPLETA: Texto + evidencia obligatoria (diferencia > umbral)
    """
    
    MIN_LONGITUD_TEXTO = 20  # Mínimo de caracteres para el texto
    
    def __init__(self, db):
        """
        Inicializa el servicio con conexión a BD.
        
        Args:
            db: Instancia de la base de datos MongoDB
        """
        self.justificacion_repo = JustificacionRepository(db)
        self.config_repo = ConfiguracionRepository(db)
        self.detalle_repo = DetalleDiferenciasRepository(db)
    
    async def determinar_tipo_justificacion(self, diferencia_valor: float) -> TipoJustificacion:
        """
        Determina el tipo de justificación requerida según el umbral.
        
        Args:
            diferencia_valor: Valor de la diferencia en MXN
            
        Returns:
            TipoJustificacion.SIMPLE o TipoJustificacion.COMPLETA
        """
        umbral = await self.config_repo.get_umbral_justificacion()
        
        if abs(diferencia_valor) <= umbral:
            return TipoJustificacion.SIMPLE
        else:
            return TipoJustificacion.COMPLETA
    
    async def registrar_justificacion(
        self,
        workflow_id: str,
        diferencia_id: str,
        texto_justificacion: str,
        usuario_justificador_id: str,
        evidencia_documental: Optional[Dict[str, Any]] = None,
        forzar_tipo: Optional[TipoJustificacion] = None
    ) -> Dict:
        """
        Registra una justificación para una diferencia.
        
        Args:
            workflow_id: ID del workflow
            diferencia_id: ID de la diferencia
            texto_justificacion: Texto de la justificación
            usuario_justificador_id: ID del usuario que justifica
            evidencia_documental: Evidencia (requerida si es COMPLETA)
            forzar_tipo: Forzar un tipo específico (opcional)
            
        Returns:
            Justificación creada
            
        Raises:
            JustificacionInvalidaError: Si el texto es muy corto
            EvidenciaRequeridaError: Si falta evidencia para COMPLETA
            JustificacionYaExisteError: Si ya existe justificación
        """
        # Validar longitud del texto
        if len(texto_justificacion.strip()) < self.MIN_LONGITUD_TEXTO:
            raise JustificacionInvalidaError(
                f"El texto debe tener al menos {self.MIN_LONGITUD_TEXTO} caracteres"
            )
        
        # Verificar si ya existe justificación
        existe = await self.justificacion_repo.existe_justificacion(workflow_id, diferencia_id)
        if existe:
            raise JustificacionYaExisteError(
                f"Ya existe una justificación para diferencia: {diferencia_id}"
            )
        
        # Obtener umbral actual para snapshot
        umbral = await self.config_repo.get_umbral_justificacion()
        
        # Determinar tipo de justificación
        if forzar_tipo:
            tipo = forzar_tipo
        else:
            # Intentar obtener el valor de la diferencia
            diferencias = await self.detalle_repo.get_by_workflow(workflow_id)
            diferencia = next(
                (d for d in diferencias if d["_id"] == diferencia_id), 
                None
            )
            if diferencia:
                tipo = await self.determinar_tipo_justificacion(
                    diferencia.get("diferencia_valor", 0)
                )
            else:
                # Si no encontramos la diferencia, usar SIMPLE por defecto
                tipo = TipoJustificacion.SIMPLE if not evidencia_documental else TipoJustificacion.COMPLETA
        
        # Validar evidencia si es COMPLETA
        if tipo == TipoJustificacion.COMPLETA and not evidencia_documental:
            raise EvidenciaRequeridaError(
                "Se requiere evidencia documental para justificación COMPLETA"
            )
        
        # Crear justificación
        justificacion_data = {
            "workflow_id": workflow_id,
            "diferencia_id": diferencia_id,
            "tipo_justificacion": tipo.value,
            "texto_justificacion": texto_justificacion.strip(),
            "evidencia_documental": evidencia_documental,
            "umbral_aplicado": umbral,
            "usuario_justificador_id": usuario_justificador_id,
            "fecha_justificacion": datetime.now(timezone.utc)
        }
        
        return await self.justificacion_repo.create(justificacion_data)
    
    async def obtener_justificacion(self, justificacion_id: str) -> Optional[Dict]:
        """
        Obtiene una justificación por su ID.
        
        Args:
            justificacion_id: ID de la justificación
            
        Returns:
            Justificación o None
        """
        return await self.justificacion_repo.get_by_id(justificacion_id)
    
    async def obtener_justificaciones_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las justificaciones de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de justificaciones
        """
        return await self.justificacion_repo.get_by_workflow(workflow_id)
    
    async def obtener_justificaciones_diferencia(self, diferencia_id: str) -> List[Dict]:
        """
        Obtiene justificaciones de una diferencia específica.
        
        Args:
            diferencia_id: ID de la diferencia
            
        Returns:
            Lista de justificaciones
        """
        return await self.justificacion_repo.get_by_diferencia(diferencia_id)
    
    async def validar_si_existe_justificacion(
        self, 
        workflow_id: str, 
        diferencia_id: str
    ) -> bool:
        """
        Verifica si existe una justificación para una diferencia.
        
        Args:
            workflow_id: ID del workflow
            diferencia_id: ID de la diferencia
            
        Returns:
            True si existe, False si no
        """
        return await self.justificacion_repo.existe_justificacion(workflow_id, diferencia_id)
    
    async def verificar_workflow_completamente_justificado(
        self, 
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Verifica si todas las diferencias de un workflow tienen justificación.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Dict con estado de completitud y detalles
        """
        # Obtener diferencias del workflow
        diferencias = await self.detalle_repo.get_by_workflow(workflow_id)
        justificaciones = await self.justificacion_repo.get_by_workflow(workflow_id)
        
        diferencias_justificadas = {j["diferencia_id"] for j in justificaciones}
        
        pendientes = [
            d for d in diferencias 
            if d["_id"] not in diferencias_justificadas
        ]
        
        return {
            "completamente_justificado": len(pendientes) == 0,
            "total_diferencias": len(diferencias),
            "justificadas": len(diferencias_justificadas),
            "pendientes": len(pendientes),
            "diferencias_pendientes": pendientes
        }
    
    async def listar_por_tipo(
        self, 
        tipo: TipoJustificacion, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Lista justificaciones por tipo.
        
        Args:
            tipo: Tipo de justificación (SIMPLE o COMPLETA)
            limit: Límite de resultados
            
        Returns:
            Lista de justificaciones
        """
        return await self.justificacion_repo.get_por_tipo(tipo.value, limit)
    
    async def listar_por_usuario(
        self, 
        usuario_id: str, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Lista justificaciones creadas por un usuario.
        
        Args:
            usuario_id: ID del usuario
            limit: Límite de resultados
            
        Returns:
            Lista de justificaciones
        """
        return await self.justificacion_repo.get_by_usuario(usuario_id, limit)
    
    async def obtener_umbral_actual(self) -> float:
        """
        Obtiene el umbral actual de justificación.
        
        Returns:
            Umbral en MXN
        """
        return await self.config_repo.get_umbral_justificacion()
