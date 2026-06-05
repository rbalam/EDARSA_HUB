"""
CorporateFilterService - Servicio centralizado de filtros corporativos
======================================================================
P1 (2026-06-05): Centraliza toda la lógica de filtrado por unidad de negocio.

REGLAS:
- Siempre usar unidad_negocio_pk (UNIQUEIDENTIFIER) como llave primaria
- El código (130MID, ESTELAR, etc.) es solo para display/legacy
- Todas las queries deben filtrar por PK, no por código

USO:
    from core.corporate_filters import CorporateFilterService
    
    # Obtener todas las unidades
    unidades = CorporateFilterService.get_unidades()
    
    # Resolver una unidad desde cualquier valor
    info = CorporateFilterService.resolver_unidad("130MID")
    # -> {"pk": "uuid...", "codigo": "130MID", "nombre": "130° MERIDA"}
    
    # Construir WHERE para SQL
    where, params = CorporateFilterService.build_where_unidad("k", "ESTELAR")
    # -> " AND k.unidad_negocio_pk = :unidad_pk ", {"unidad_pk": "uuid..."}
"""
from core.unidades_service import UnidadesService
from typing import Optional, Dict, Any, List, Tuple

class CorporateFilterService:
    """Servicio centralizado para filtros corporativos por unidad de negocio."""

    @staticmethod
    def get_unidades() -> List[Dict[str, Any]]:
        """Retorna todas las unidades activas con PK, código y nombre."""
        return UnidadesService.get_all()

    @staticmethod
    def get_unidades_pk() -> List[str]:
        """Retorna lista de PKs (UNIQUEIDENTIFIER como string)."""
        return UnidadesService.get_pks()

    @staticmethod
    def get_unidades_codigos() -> List[str]:
        """Retorna lista de códigos (para compatibilidad legacy)."""
        return UnidadesService.get_codigos()

    @staticmethod
    def resolver_unidad(valor: Any) -> Dict[str, Optional[str]]:
        """
        Resuelve una unidad desde cualquier valor (PK, código o nombre).
        
        Returns:
            {"pk": str|None, "codigo": str|None, "nombre": str|None}
        """
        return {
            "pk": UnidadesService.resolver_pk(valor),
            "codigo": UnidadesService.resolver_codigo(valor),
            "nombre": UnidadesService.get_nombre(valor)
        }

    @staticmethod
    def build_where_unidad(alias: str, valor: Any, param_name: str = "unidad_pk") -> Tuple[str, Dict[str, str]]:
        """
        Construye cláusula WHERE para filtrar por unidad usando PK real.
        
        Args:
            alias: Alias de la tabla (ej: "k")
            valor: Valor a resolver (PK, código o nombre)
            param_name: Nombre del parámetro (default: "unidad_pk")
            
        Returns:
            Tuple[sql_fragment, params_dict]
            
        Example:
            where, params = CorporateFilterService.build_where_unidad("k", "130MID")
            sql = f"SELECT * FROM tabla k WHERE 1=1 {where}"
            # sql = "SELECT * FROM tabla k WHERE 1=1  AND k.unidad_negocio_pk = :unidad_pk "
        """
        pk = UnidadesService.resolver_pk(valor)

        if not pk:
            # Valor no encontrado - retornar condición falsa
            return " AND 1=0 ", {}

        return (
            f" AND {alias}.unidad_negocio_pk = :{param_name} ",
            {param_name: str(pk)}
        )

    @staticmethod
    def build_where_unidades_multiple(alias: str, valores: List[Any], param_prefix: str = "u") -> Tuple[str, Dict[str, str]]:
        """
        Construye cláusula WHERE para filtrar por múltiples unidades usando PKs.
        
        Returns:
            Tuple[sql_fragment, params_dict]
        """
        pks = []
        params = {}
        
        for i, v in enumerate(valores):
            pk = UnidadesService.resolver_pk(v)
            if pk:
                param_name = f"{param_prefix}_{i}"
                pks.append(f":{param_name}")
                params[param_name] = str(pk)
        
        if not pks:
            return " AND 1=0 ", {}
        
        return (
            f" AND {alias}.unidad_negocio_pk IN ({', '.join(pks)}) ",
            params
        )

    @staticmethod
    def validar_acceso_unidad(usuario_unidades: List[str], unidad_solicitada: Any) -> bool:
        """
        Valida si el usuario tiene acceso a la unidad solicitada.
        
        Args:
            usuario_unidades: Lista de códigos/PKs a los que tiene acceso
            unidad_solicitada: Unidad que quiere consultar
            
        Returns:
            True si tiene acceso, False si no
        """
        pk_solicitada = UnidadesService.resolver_pk(unidad_solicitada)
        if not pk_solicitada:
            return False
        
        for u in usuario_unidades:
            if UnidadesService.resolver_pk(u) == pk_solicitada:
                return True
        
        return False
