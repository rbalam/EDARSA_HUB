"""
Endpoints de Configuración
CAB-003 | EDARSA HUB - Fase 2A

Expone la funcionalidad de configuración vía HTTP.
"""
from fastapi import APIRouter, HTTPException
from ..services.configuracion_service import (
    ConfiguracionService,
    ConfiguracionNoEncontradaError,
    ValorInvalidoError
)
from ..api_schemas import ConfiguracionUpdateRequest, OperacionResponse
from ..db_utils import get_database

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


@router.get("")
async def obtener_parametros_operativos():
    """
    Obtiene todos los parámetros operativos del módulo.
    
    Incluye:
    - **umbral_justificacion**: Monto máximo para justificación simple
    - **dias_limite_tarea**: Días por defecto para completar tareas
    - **max_ciclos_reasignacion**: Máximo de ciclos antes de escalar
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        parametros = await config_svc.obtener_parametros_operativos()
        return parametros
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/todas")
async def listar_todas_configuraciones():
    """
    Lista todas las configuraciones del módulo operativo.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        configuraciones = await config_svc.listar_todas()
        return {"items": configuraciones, "total": len(configuraciones)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{clave}")
async def obtener_configuracion(clave: str):
    """
    Obtiene una configuración específica por su clave.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        config = await config_svc.obtener_configuracion(clave)
        if not config:
            raise HTTPException(status_code=404, detail=f"Configuración no encontrada: {clave}")
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{clave}", response_model=OperacionResponse)
async def actualizar_configuracion(clave: str, request: ConfiguracionUpdateRequest):
    """
    Actualiza el valor de una configuración.
    
    Si la configuración no existe, la crea.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        config = await config_svc.actualizar_valor(
            clave=clave,
            valor=request.valor,
            descripcion=request.descripcion
        )
        
        return OperacionResponse(
            success=True,
            message=f"Configuración '{clave}' actualizada",
            data=config
        )
    except ValorInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints específicos para configuraciones conocidas

@router.get("/umbral-justificacion/valor")
async def obtener_umbral_justificacion():
    """
    Obtiene el umbral actual para justificación simple.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        umbral = await config_svc.obtener_umbral_justificacion()
        return {"clave": "UMBRAL_JUSTIFICACION_SIMPLE", "valor": umbral, "moneda": "MXN"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/umbral-justificacion/valor", response_model=OperacionResponse)
async def actualizar_umbral_justificacion(nuevo_umbral: float):
    """
    Actualiza el umbral de justificación.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        config = await config_svc.actualizar_umbral_justificacion(nuevo_umbral)
        
        return OperacionResponse(
            success=True,
            message=f"Umbral actualizado a {nuevo_umbral} MXN",
            data=config
        )
    except ValorInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dias-limite-tarea/valor")
async def obtener_dias_limite_tarea():
    """
    Obtiene los días límite por defecto para tareas.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        dias = await config_svc.obtener_dias_limite_tarea()
        return {"clave": "DIAS_LIMITE_TAREA_DEFAULT", "valor": dias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/dias-limite-tarea/valor", response_model=OperacionResponse)
async def actualizar_dias_limite_tarea(dias: int):
    """
    Actualiza los días límite para tareas.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        config = await config_svc.actualizar_dias_limite_tarea(dias)
        
        return OperacionResponse(
            success=True,
            message=f"Días límite actualizado a {dias}",
            data=config
        )
    except ValorInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/max-ciclos-reasignacion/valor")
async def obtener_max_ciclos_reasignacion():
    """
    Obtiene el máximo de ciclos de reasignación.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        max_ciclos = await config_svc.obtener_max_ciclos_reasignacion()
        return {"clave": "MAX_CICLOS_REASIGNACION", "valor": max_ciclos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/max-ciclos-reasignacion/valor", response_model=OperacionResponse)
async def actualizar_max_ciclos_reasignacion(max_ciclos: int):
    """
    Actualiza el máximo de ciclos de reasignación.
    """
    try:
        db = get_db()
        config_svc = ConfiguracionService(db)
        
        config = await config_svc.actualizar_max_ciclos_reasignacion(max_ciclos)
        
        return OperacionResponse(
            success=True,
            message=f"Máximo ciclos actualizado a {max_ciclos}",
            data=config
        )
    except ValorInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
