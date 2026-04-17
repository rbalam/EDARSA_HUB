"""
Servicio de Configuración Operativa
CAB-003 | EDARSA HUB - Fase 2A

Encapsula la lógica de negocio para gestión de parámetros de configuración.
"""
from typing import Optional, List, Dict


from ..repositories.configuracion_repository import ConfiguracionRepository


class ConfiguracionServiceError(Exception):
    """Excepción base para errores del servicio de configuración."""
    pass


class ConfiguracionNoEncontradaError(ConfiguracionServiceError):
    """La configuración solicitada no existe."""
    pass


class ValorInvalidoError(ConfiguracionServiceError):
    """El valor de configuración no es válido."""
    pass


class ConfiguracionService:
    """
    Servicio para gestión de configuración operativa.
    
    Proporciona acceso a los parámetros configurables del módulo
    como umbrales, límites de tiempo, etc.
    """
    
    # Claves de configuración conocidas
    CLAVE_UMBRAL_JUSTIFICACION = "UMBRAL_JUSTIFICACION_SIMPLE"
    CLAVE_DIAS_LIMITE_TAREA = "DIAS_LIMITE_TAREA_DEFAULT"
    CLAVE_MAX_CICLOS_REASIGNACION = "MAX_CICLOS_REASIGNACION"
    
    def __init__(self, db):
        """
        Inicializa el servicio con conexión a BD.
        
        Args:
            db: Instancia de la base de datos MongoDB
        """
        self.config_repo = ConfiguracionRepository(db)
    
    async def obtener_valor(
        self, 
        clave: str, 
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtiene el valor de una configuración.
        
        Args:
            clave: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de la configuración o default
        """
        return await self.config_repo.get_valor(clave, default)
    
    async def obtener_valor_int(self, clave: str, default: int = 0) -> int:
        """
        Obtiene el valor de una configuración como entero.
        
        Args:
            clave: Clave de configuración
            default: Valor por defecto
            
        Returns:
            Valor como entero
        """
        return await self.config_repo.get_valor_int(clave, default)
    
    async def obtener_valor_float(self, clave: str, default: float = 0.0) -> float:
        """
        Obtiene el valor de una configuración como flotante.
        
        Args:
            clave: Clave de configuración
            default: Valor por defecto
            
        Returns:
            Valor como flotante
        """
        return await self.config_repo.get_valor_float(clave, default)
    
    async def actualizar_valor(
        self, 
        clave: str, 
        valor: str, 
        descripcion: Optional[str] = None
    ) -> Dict:
        """
        Actualiza o crea un valor de configuración.
        
        Args:
            clave: Clave de configuración
            valor: Nuevo valor
            descripcion: Descripción opcional
            
        Returns:
            Configuración actualizada o creada
            
        Raises:
            ValorInvalidoError: Si el valor está vacío
        """
        if not valor or not valor.strip():
            raise ValorInvalidoError("El valor no puede estar vacío")
        
        return await self.config_repo.set_valor(clave, valor.strip(), descripcion)
    
    async def obtener_configuracion(self, clave: str) -> Optional[Dict]:
        """
        Obtiene una configuración completa por su clave.
        
        Args:
            clave: Clave de configuración
            
        Returns:
            Configuración completa o None
        """
        return await self.config_repo.get_by_clave(clave)
    
    async def listar_todas(self) -> List[Dict]:
        """
        Lista todas las configuraciones.
        
        Returns:
            Lista de configuraciones ordenadas por clave
        """
        return await self.config_repo.get_todas()
    
    # Métodos específicos para configuraciones conocidas
    
    async def obtener_umbral_justificacion(self) -> float:
        """
        Obtiene el umbral para justificación simple.
        
        Returns:
            Umbral en MXN (default: 500.0)
        """
        return await self.config_repo.get_umbral_justificacion()
    
    async def actualizar_umbral_justificacion(self, nuevo_umbral: float) -> Dict:
        """
        Actualiza el umbral de justificación.
        
        Args:
            nuevo_umbral: Nuevo umbral en MXN
            
        Returns:
            Configuración actualizada
            
        Raises:
            ValorInvalidoError: Si el umbral es negativo
        """
        if nuevo_umbral < 0:
            raise ValorInvalidoError("El umbral no puede ser negativo")
        
        return await self.config_repo.set_valor(
            self.CLAVE_UMBRAL_JUSTIFICACION,
            str(nuevo_umbral),
            "Monto máximo en MXN para justificación simple (sin evidencia documental obligatoria)"
        )
    
    async def obtener_dias_limite_tarea(self) -> int:
        """
        Obtiene los días límite por defecto para tareas.
        
        Returns:
            Días límite (default: 3)
        """
        return await self.config_repo.get_dias_limite_tarea()
    
    async def actualizar_dias_limite_tarea(self, dias: int) -> Dict:
        """
        Actualiza los días límite para tareas.
        
        Args:
            dias: Número de días
            
        Returns:
            Configuración actualizada
            
        Raises:
            ValorInvalidoError: Si los días son menores a 1
        """
        if dias < 1:
            raise ValorInvalidoError("Los días límite deben ser al menos 1")
        
        return await self.config_repo.set_valor(
            self.CLAVE_DIAS_LIMITE_TAREA,
            str(dias),
            "Días límite por defecto para completar una tarea asignada"
        )
    
    async def obtener_max_ciclos_reasignacion(self) -> int:
        """
        Obtiene el máximo de ciclos de reasignación.
        
        Returns:
            Máximo de ciclos (default: 3)
        """
        return await self.config_repo.get_max_ciclos_reasignacion()
    
    async def actualizar_max_ciclos_reasignacion(self, max_ciclos: int) -> Dict:
        """
        Actualiza el máximo de ciclos de reasignación.
        
        Args:
            max_ciclos: Máximo de ciclos
            
        Returns:
            Configuración actualizada
            
        Raises:
            ValorInvalidoError: Si el máximo es menor a 1
        """
        if max_ciclos < 1:
            raise ValorInvalidoError("El máximo de ciclos debe ser al menos 1")
        
        return await self.config_repo.set_valor(
            self.CLAVE_MAX_CICLOS_REASIGNACION,
            str(max_ciclos),
            "Número máximo de ciclos de reasignación antes de escalamiento automático"
        )
    
    async def obtener_parametros_operativos(self) -> Dict:
        """
        Obtiene todos los parámetros operativos en un solo llamado.
        
        Returns:
            Diccionario con todos los parámetros
        """
        return {
            "umbral_justificacion": await self.obtener_umbral_justificacion(),
            "dias_limite_tarea": await self.obtener_dias_limite_tarea(),
            "max_ciclos_reasignacion": await self.obtener_max_ciclos_reasignacion()
        }
