"""
EDARSA HUB - Servicio de Estructura Organizacional (FASE 2)
============================================================

Servicio AISLADO para consulta de estructura organizacional.
- Solo lectura
- No modifica datos funcionales
- No participa en validación de permisos
- Desacoplado del flujo principal

Creado: Diciembre 2025
Fase: FASE 2 - Visualización
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

# Configurar logger para bitácora interna
logger = logging.getLogger("estructura_service")


class EstructuraService:
    """
    Servicio para consultar estructura organizacional.
    Solo lectura - no modifica datos funcionales.
    """
    
    def __init__(self, db):
        self.db = db
    
    async def get_estructura_organizacional(self) -> Dict:
        """
        Obtiene la estructura organizacional completa.
        Retorna empresas con sus unidades y sucursales.
        """
        try:
            # Obtener empresas
            empresas = await self.db.sec_empresas.find(
                {"activo": True},
                {"_id": 0}
            ).to_list(100)
            
            resultado = []
            
            for empresa in empresas:
                empresa_data = {
                    "id": empresa.get("id"),
                    "codigo": empresa.get("codigo"),
                    "nombre": empresa.get("nombre"),
                    "unidades_negocio": []
                }
                
                # Obtener unidades de esta empresa
                unidades = await self.db.sec_unidades_negocio.find(
                    {"empresa_id": empresa.get("id"), "activo": True},
                    {"_id": 0}
                ).to_list(100)
                
                for unidad in unidades:
                    unidad_data = {
                        "id": unidad.get("id"),
                        "codigo": unidad.get("codigo"),
                        "nombre": unidad.get("nombre"),
                        "tipo_unidad": unidad.get("tipo_unidad", "SIN_CLASIFICAR"),
                        "visible_usuario": unidad.get("visible_usuario", True),
                        "sucursales": []
                    }
                    
                    # Obtener sucursales de esta unidad
                    sucursales = await self.db.sec_sucursales.find(
                        {"unidad_negocio_id": unidad.get("id"), "activo": True},
                        {"_id": 0}
                    ).to_list(100)
                    
                    for sucursal in sucursales:
                        unidad_data["sucursales"].append({
                            "id": sucursal.get("id"),
                            "codigo": sucursal.get("codigo"),
                            "nombre": sucursal.get("nombre")
                        })
                    
                    empresa_data["unidades_negocio"].append(unidad_data)
                
                resultado.append(empresa_data)
            
            return {
                "empresas": resultado,
                "total_empresas": len(resultado),
                "fase": "FASE_2",
                "estado": "SOLO_VISUALIZACION"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estructura: {e}")
            return {
                "empresas": [],
                "total_empresas": 0,
                "error": "Error interno",
                "fase": "FASE_2"
            }
    
    async def get_mapeo_servidores(self) -> Dict:
        """
        Obtiene el mapeo entre servidores y sucursales.
        Solo lectura informativa.
        """
        try:
            mapeos = await self.db.sec_mapeo_servidor_sucursal.find(
                {"activo": True},
                {"_id": 0}
            ).to_list(100)
            
            resultado = []
            for mapeo in mapeos:
                resultado.append({
                    "server_id": mapeo.get("server_id"),
                    "server_name": mapeo.get("server_name"),
                    "server_type": mapeo.get("server_type"),
                    "sucursal_id": mapeo.get("sucursal_id"),
                    "unidad_negocio_id": mapeo.get("unidad_negocio_id"),
                    "empresa_id": mapeo.get("empresa_id")
                })
            
            return {
                "mapeos": resultado,
                "total": len(resultado),
                "fase": "FASE_2",
                "nota": "Mapeo informativo - servidor es dimension tecnica"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo mapeos: {e}")
            return {
                "mapeos": [],
                "total": 0,
                "error": "Error interno"
            }
    
    async def get_permisos_catalogo_v2(self) -> Dict:
        """
        Obtiene el catálogo de permisos v2.
        Solo informativo - no reemplaza catálogo legacy.
        """
        try:
            permisos = await self.db.sec_permisos_catalogo.find(
                {"activo": True},
                {"_id": 0}
            ).to_list(500)
            
            # Agrupar por módulo
            por_modulo = {}
            for perm in permisos:
                modulo = perm.get("modulo", "sin_modulo")
                if modulo not in por_modulo:
                    por_modulo[modulo] = []
                por_modulo[modulo].append({
                    "codigo": perm.get("codigo"),
                    "submodulo": perm.get("submodulo"),
                    "accion": perm.get("accion"),
                    "descripcion": perm.get("descripcion")
                })
            
            return {
                "permisos_por_modulo": por_modulo,
                "total_permisos": len(permisos),
                "total_modulos": len(por_modulo),
                "fase": "FASE_2",
                "nota": "Catalogo informativo - no reemplaza permisos actuales"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo permisos: {e}")
            return {
                "permisos_por_modulo": {},
                "total_permisos": 0,
                "error": "Error interno"
            }
    
    async def escribir_bitacora(
        self,
        usuario_id: str,
        usuario_email: str,
        accion: str,
        recurso: str,
        resultado: str = "OK",
        detalles: Dict = None
    ) -> bool:
        """
        Escribe en bitácora de forma DESACOPLADA.
        Si falla, no rompe el flujo principal.
        Registra error internamente pero no lo propaga.
        """
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc),
                "usuario_id": usuario_id,
                "usuario_email": usuario_email,
                "accion": accion,
                "recurso": recurso,
                "resultado": resultado,
                "detalles": detalles or {},
                "fase": "FASE_2"
            }
            await self.db.sec_bitacora_acceso.insert_one(entry)
            return True
        except Exception as e:
            # Log interno - NO propagar error al flujo principal
            logger.warning(f"Bitacora FASE2 fallo (no critico): {e}")
            return False


# Factory function
def get_estructura_service(db) -> EstructuraService:
    """Obtiene instancia del servicio."""
    return EstructuraService(db)


__all__ = ['EstructuraService', 'get_estructura_service']
