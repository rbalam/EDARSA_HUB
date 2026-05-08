"""
EDARSA HUB - Catálogos Service
==============================
Lógica de negocio para el módulo de catálogos.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from modules.catalogos.schemas import (
    DOMINIOS_CATALOGOS,
    ESTRUCTURA_TABLAS,
    CatalogoListResponse,
    CatalogoRegistroResponse,
)
from modules.catalogos import repository

logger = logging.getLogger(__name__)


class CatalogosService:
    """Servicio para gestión de catálogos."""
    
    def __init__(self, db):
        self.db = db
    
    # ========================================================================
    # DOMINIOS Y ESTRUCTURA
    # ========================================================================
    
    async def obtener_dominios(self) -> Dict:
        """Retorna la configuración de todos los dominios y sus catálogos."""
        # Recopilar todas las tablas para una sola consulta
        todas_las_tablas = []
        for dominio_config in DOMINIOS_CATALOGOS.values():
            for catalogo in dominio_config["catalogos"]:
                todas_las_tablas.append(catalogo["tabla"])
        
        # Obtener todos los conteos de una vez
        try:
            conteos = await repository.obtener_conteos_tablas(self.db, todas_las_tablas)
        except Exception as e:
            logger.error(f"Error obteniendo conteos: {e}")
            conteos = {}
        
        # Construir respuesta con conteos
        dominios_con_conteos = {}
        
        for dominio_id, dominio_config in DOMINIOS_CATALOGOS.items():
            catalogos_con_conteo = []
            
            for catalogo in dominio_config["catalogos"]:
                tabla = catalogo["tabla"]
                total = conteos.get(tabla, -1)
                tabla_existe = total >= 0
                total_real = max(0, total)
                
                catalogo_info = {
                    **catalogo,
                    "registros": total_real,
                    "existe": tabla_existe
                }
                catalogos_con_conteo.append(catalogo_info)
            
            dominios_con_conteos[dominio_id] = {
                **dominio_config,
                "catalogos": catalogos_con_conteo
            }
        
        return dominios_con_conteos
    
    async def obtener_estructura_tabla(self, tabla: str) -> Dict:
        """Obtiene la estructura de una tabla."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        estructura_config = ESTRUCTURA_TABLAS[tabla]
        
        # Obtener estructura real de la BD
        try:
            columnas_bd = await repository.obtener_estructura_tabla(self.db, tabla)
        except Exception as e:
            columnas_bd = []
            logger.warning(f"No se pudo obtener estructura de BD para {tabla}: {e}")
        
        return {
            "tabla": tabla,
            "estructura": estructura_config,
            "columnas_bd": columnas_bd
        }
    
    # ========================================================================
    # CRUD GENÉRICO
    # ========================================================================
    
    async def listar_catalogo(
        self,
        tabla: str,
        solo_activos: bool = False,
        buscar: Optional[str] = None,
        limit: int = 500
    ) -> CatalogoListResponse:
        """Lista registros de un catálogo."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        try:
            registros = await repository.listar_registros_catalogo(
                self.db, tabla, solo_activos, buscar, limit
            )
            
            return CatalogoListResponse(
                success=True,
                tabla=tabla,
                registros=registros,
                total=len(registros),
                estructura=ESTRUCTURA_TABLAS[tabla]
            )
        except Exception as e:
            logger.error(f"Error listando catálogo {tabla}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def obtener_registro(self, tabla: str, id_valor: int) -> Dict:
        """Obtiene un registro específico."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        registro = await repository.obtener_registro_catalogo(self.db, tabla, id_valor)
        
        if not registro:
            raise HTTPException(status_code=404, detail=f"Registro {id_valor} no encontrado en {tabla}")
        
        return registro
    
    async def crear_registro(
        self,
        tabla: str,
        datos: Dict[str, Any],
        usuario: str
    ) -> CatalogoRegistroResponse:
        """Crea un nuevo registro en un catálogo."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        try:
            nuevo_id = await repository.crear_registro_catalogo(self.db, tabla, datos, usuario)
            
            return CatalogoRegistroResponse(
                success=True,
                message=f"Registro creado exitosamente en {tabla}",
                id=nuevo_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creando registro en {tabla}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def actualizar_registro(
        self,
        tabla: str,
        id_valor: int,
        datos: Dict[str, Any],
        usuario: str
    ) -> CatalogoRegistroResponse:
        """Actualiza un registro existente."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        # Verificar que existe
        registro = await repository.obtener_registro_catalogo(self.db, tabla, id_valor)
        if not registro:
            raise HTTPException(status_code=404, detail=f"Registro {id_valor} no encontrado")
        
        try:
            await repository.actualizar_registro_catalogo(self.db, tabla, id_valor, datos, usuario)
            
            return CatalogoRegistroResponse(
                success=True,
                message=f"Registro {id_valor} actualizado en {tabla}",
                id=id_valor
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error actualizando registro en {tabla}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def desactivar_registro(self, tabla: str, id_valor: int) -> CatalogoRegistroResponse:
        """Desactiva un registro (soft delete)."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        estructura = ESTRUCTURA_TABLAS[tabla]
        if not estructura.get("campo_activo"):
            raise HTTPException(
                status_code=400, 
                detail=f"La tabla '{tabla}' no soporta desactivación"
            )
        
        try:
            await repository.desactivar_registro_catalogo(self.db, tabla, id_valor)
            
            return CatalogoRegistroResponse(
                success=True,
                message=f"Registro {id_valor} desactivado en {tabla}",
                id=id_valor
            )
        except Exception as e:
            logger.error(f"Error desactivando registro: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def activar_registro(self, tabla: str, id_valor: int) -> CatalogoRegistroResponse:
        """Reactiva un registro."""
        if tabla not in ESTRUCTURA_TABLAS:
            raise HTTPException(status_code=404, detail=f"Tabla '{tabla}' no configurada")
        
        estructura = ESTRUCTURA_TABLAS[tabla]
        if not estructura.get("campo_activo"):
            raise HTTPException(
                status_code=400, 
                detail=f"La tabla '{tabla}' no soporta activación/desactivación"
            )
        
        try:
            await repository.activar_registro_catalogo(self.db, tabla, id_valor)
            
            return CatalogoRegistroResponse(
                success=True,
                message=f"Registro {id_valor} activado en {tabla}",
                id=id_valor
            )
        except Exception as e:
            logger.error(f"Error activando registro: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ========================================================================
    # ADMINISTRACIÓN
    # ========================================================================
    
    async def crear_tablas_nuevas(self) -> Dict:
        """Ejecuta el DDL para crear las tablas globales nuevas."""
        try:
            resultado = await repository.ejecutar_ddl_tablas_nuevas(self.db)
            return {
                "success": True,
                "message": "DDL ejecutado",
                **resultado
            }
        except Exception as e:
            logger.error(f"Error ejecutando DDL: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def verificar_tablas_nuevas(self) -> Dict:
        """Verifica el estado de las tablas nuevas."""
        return await repository.verificar_tablas_nuevas(self.db)
    
    async def obtener_script_ddl(self) -> str:
        """Retorna el script DDL para revisión."""
        return repository.DDL_TABLAS_NUEVAS


# ============================================================================
# INSTANCIA GLOBAL DEL SERVICIO
# ============================================================================

_catalogos_service: CatalogosService = None


def init_catalogos_service(db):
    """Inicializa el servicio de catálogos."""
    global _catalogos_service
    _catalogos_service = CatalogosService(db)


def get_catalogos_service() -> CatalogosService:
    """Obtiene la instancia del servicio."""
    if _catalogos_service is None:
        raise RuntimeError("Servicio de catálogos no inicializado")
    return _catalogos_service
