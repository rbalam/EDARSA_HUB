"""
Repositorio para configuracion_operativa - VERSIÓN SQL
CAB-003 | EDARSA HUB - Fase 2A

FASE B-P1-E: Migrado a EDARSAHUB SQL Server
- CERO MongoDB productivo
- SQL explícito contra Configuracion_Operativa
"""
from typing import Optional, List, Dict

from .sql_base_repository import SQLBaseRepository


class ConfiguracionRepository(SQLBaseRepository):
    """
    Repository para la tabla Configuracion_Operativa.
    Migrado de MongoDB a SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("configuracion_operativa")
    
    async def get_by_clave(self, clave: str) -> Optional[Dict]:
        """
        Obtiene una configuración por su clave.
        """
        doc = self.find_one({"clave": clave})
        return doc
    
    async def get_valor(self, clave: str, default: str = None) -> Optional[str]:
        """
        Obtiene el valor de una configuración.
        """
        doc = await self.get_by_clave(clave)
        return doc["valor"] if doc else default
    
    async def get_valor_int(self, clave: str, default: int = 0) -> int:
        """
        Obtiene el valor de una configuración como entero.
        """
        valor = await self.get_valor(clave)
        try:
            return int(valor) if valor else default
        except ValueError:
            return default
    
    async def get_valor_float(self, clave: str, default: float = 0.0) -> float:
        """
        Obtiene el valor de una configuración como flotante.
        """
        valor = await self.get_valor(clave)
        try:
            return float(valor) if valor else default
        except ValueError:
            return default
    
    async def get_umbral_justificacion(self) -> float:
        """
        Obtiene el umbral para justificación simple.
        Returns:
            Umbral en MXN (default: 500.0)
        """
        return await self.get_valor_float("UMBRAL_JUSTIFICACION_SIMPLE", 500.0)
    
    async def get_dias_limite_tarea(self) -> int:
        """
        Obtiene los días límite por defecto para tareas.
        Returns:
            Días límite (default: 3)
        """
        return await self.get_valor_int("DIAS_LIMITE_TAREA_DEFAULT", 3)
    
    async def get_max_ciclos_reasignacion(self) -> int:
        """
        Obtiene el máximo de ciclos de reasignación.
        Returns:
            Máximo de ciclos (default: 3)
        """
        return await self.get_valor_int("MAX_CICLOS_REASIGNACION", 3)
    
    async def set_valor(self, clave: str, valor: str, descripcion: str = None) -> Dict:
        """
        Establece o actualiza un valor de configuración.
        """
        existente = await self.get_by_clave(clave)
        
        if existente:
            data = {"valor": valor}
            if descripcion:
                data["descripcion"] = descripcion
            return await self.update(existente.get("id") or existente.get("clave"), data)
        else:
            data = {
                "clave": clave,
                "valor": valor,
                "descripcion": descripcion
            }
            return await self.create(data)
    
    async def get_todas(self) -> List[Dict]:
        """
        Obtiene todas las configuraciones.
        """
        return await self.get_all(sort=[("clave", 1)])
    
    # Métodos de compatibilidad
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Compatibilidad - No necesario en SQL."""
        return doc
