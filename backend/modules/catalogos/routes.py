from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Catálogos Routes
=============================
Endpoints del módulo de catálogos.

ENDPOINTS:
- GET  /catalogos/dominios - Lista todos los dominios y sus catálogos
- GET  /catalogos/tabla/{tabla} - Lista registros de un catálogo
- GET  /catalogos/tabla/{tabla}/{id} - Obtiene un registro específico
- POST /catalogos/tabla/{tabla} - Crea un nuevo registro
- PUT  /catalogos/tabla/{tabla}/{id} - Actualiza un registro
- PUT  /catalogos/tabla/{tabla}/{id}/desactivar - Desactiva un registro
- PUT  /catalogos/tabla/{tabla}/{id}/activar - Reactiva un registro
- GET  /catalogos/estructura/{tabla} - Obtiene estructura de una tabla
- POST /catalogos/admin/crear-tablas - Crea tablas globales nuevas (DDL)
- GET  /catalogos/admin/verificar-tablas - Verifica estado de tablas nuevas
- GET  /catalogos/admin/script-ddl - Obtiene el script DDL

Diciembre 2025
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any

from core.security import get_current_user
from modules.catalogos.service import get_catalogos_service
from modules.catalogos.schemas import (
    CatalogoRegistroCreate,
    CatalogoRegistroUpdate,
)


router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


# ============================================================================
# ENDPOINTS ESPECÍFICOS - SISTEMAS (para combo de Servidores)
# ============================================================================

# Constantes de permisos
PERM_SISTEMAS_SOLICITAR = "CATALOGOS_SISTEMAS_SOLICITAR"
PERM_SISTEMAS_CREAR = "CATALOGOS_SISTEMAS_CREAR"
PERM_SISTEMAS_AUTORIZAR = "CATALOGOS_SISTEMAS_AUTORIZAR"
PERM_SISTEMAS_EDITAR = "CATALOGOS_SISTEMAS_EDITAR"
PERM_SISTEMAS_ACTIVAR = "CATALOGOS_SISTEMAS_ACTIVAR_INACTIVAR"

def _tiene_permiso_sistemas(user: Dict, permiso: str) -> bool:
    """Verifica si el usuario tiene un permiso específico de sistemas."""
    # SuperAdmin y Administrador tienen todos los permisos
    role = user.get('role', '')
    if role in ['Administrador', 'SuperAdministrador']:
        return True
    # Supervisor puede solicitar, crear y editar
    if role == 'Supervisor' and permiso in [PERM_SISTEMAS_SOLICITAR, PERM_SISTEMAS_CREAR, PERM_SISTEMAS_EDITAR]:
        return True
    # Verificar permisos específicos del usuario
    permisos = user.get('permisos', []) or []
    return permiso in permisos


@router.get("/sistemas")
async def listar_sistemas(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todos los tipos de sistema (activos, inactivos, pendientes, rechazados).
    
    Usado por: Catálogos > Sistemas
    """
    from core.db import execute_sql_query
    
    query = """
        SELECT SistemaID, Codigo, Descripcion, Activo, Estado,
               SolicitadoPorEmail, AutorizadoPorEmail,
               FechaSolicitud, FechaAutorizacion,
               FechaCreacion, FechaActualizacion
        FROM Sistema_Catalogo
        ORDER BY 
            CASE Estado 
                WHEN 'PENDIENTE' THEN 1 
                WHEN 'ACTIVO' THEN 2 
                WHEN 'INACTIVO' THEN 3 
                ELSE 4 
            END,
            SistemaID
    """
    
    try:
        rows = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            query
        )
        return {"success": True, "data": rows or []}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


@router.get("/sistemas/activos")
async def listar_sistemas_activos(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista solo tipos de sistema activos para poblar combos.
    
    Usado por: Modal Agregar/Editar Servidor
    Filtra: Activo = 1 AND Estado = 'ACTIVO'
    """
    from core.db import execute_sql_query
    
    query = """
        SELECT SistemaID, Codigo, Descripcion
        FROM Sistema_Catalogo
        WHERE Activo = 1 AND Estado = 'ACTIVO'
        ORDER BY Descripcion
    """
    
    try:
        rows = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            query
        )
        
        # Determinar permisos del usuario para mostrar opción "+ Nuevo"
        puede_crear = _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_CREAR)
        puede_solicitar = _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_SOLICITAR)
        
        return {
            "success": True, 
            "data": rows or [],
            "permisos": {
                "puede_crear": puede_crear,
                "puede_solicitar": puede_solicitar,
                "mostrar_nuevo": puede_crear or puede_solicitar
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": [], "permisos": {}}


@router.post("/sistemas/solicitar")
async def solicitar_sistema(
    body: CatalogoRegistroCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Solicita un nuevo tipo de sistema (queda PENDIENTE de autorización).
    
    Requiere: CATALOGOS_SISTEMAS_SOLICITAR
    """
    from fastapi import HTTPException
    from core.db import execute_sql_query
    
    if not _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_SOLICITAR):
        raise HTTPException(status_code=403, detail="Sin permisos para solicitar sistemas")
    
    descripcion = body.datos.get('Descripcion', '').strip()
    
    if not descripcion:
        raise HTTPException(status_code=400, detail="Descripción es obligatoria")
    
    # Generar código automático basado en descripción
    codigo = descripcion.upper().replace(' ', '_')[:20]
    
    # Verificar duplicados
    check_query = f"""
        SELECT COUNT(*) as cnt FROM Sistema_Catalogo 
        WHERE Descripcion = '{Descripcion.replace("'", "''")}'
    """
    try:
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            check_query
        )
        if result and result[0].get('cnt', 0) > 0:
            raise HTTPException(status_code=400, detail="Ya existe un sistema con esa descripción")
        
        user_email = current_user.get('email', 'unknown')
        
        # Insertar como PENDIENTE
        insert_query = f"""
            INSERT INTO Sistema_Catalogo (Codigo, Descripcion, Activo, Estado, SolicitadoPorEmail, FechaSolicitud)
            OUTPUT INSERTED.SistemaID
            VALUES ('{Codigo}', '{Descripcion.replace("'", "''")}', 0, 'PENDIENTE', '{user_email}', SYSDATETIME())
        """
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            insert_query
        )
        nuevo_id = result[0].get('SistemaID') if result else None
        
        return {
            "success": True, 
            "message": "Solicitud enviada para autorización",
            "id": nuevo_id,
            "estado": "PENDIENTE"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sistemas")
async def crear_sistema(
    body: CatalogoRegistroCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo tipo de sistema directamente (ACTIVO).
    
    Requiere: CATALOGOS_SISTEMAS_CREAR
    """
    from fastapi import HTTPException
    from core.db import execute_sql_query
    
    if not _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_CREAR):
        raise HTTPException(status_code=403, detail="Sin permisos para crear sistemas")
    
    codigo = body.datos.get('Codigo', '').strip()
    descripcion = body.datos.get('Descripcion', '').strip()
    
    if not descripcion:
        raise HTTPException(status_code=400, detail="Descripción es obligatoria")
    
    # Si no viene código, generarlo
    if not codigo:
        codigo = descripcion.upper().replace(' ', '_')[:20]
    
    # Verificar duplicados
    check_query = f"""
        SELECT COUNT(*) as cnt FROM Sistema_Catalogo 
        WHERE Codigo = '{Codigo}' OR Descripcion = '{Descripcion.replace("'", "''")}'
    """
    try:
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            check_query
        )
        if result and result[0].get('cnt', 0) > 0:
            raise HTTPException(status_code=400, detail="Ya existe un sistema con ese código o descripción")
        
        user_email = current_user.get('email', 'unknown')
        
        # Insertar como ACTIVO
        insert_query = f"""
            INSERT INTO Sistema_Catalogo (Codigo, Descripcion, Activo, Estado, SolicitadoPorEmail, FechaSolicitud, AutorizadoPorEmail, FechaAutorizacion)
            OUTPUT INSERTED.SistemaID, INSERTED.Codigo, INSERTED.Descripcion
            VALUES ('{Codigo}', '{Descripcion.replace("'", "''")}', 1, 'ACTIVO', '{user_email}', SYSDATETIME(), '{user_email}', SYSDATETIME())
        """
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            insert_query
        )
        
        if result:
            nuevo = result[0]
            return {
                "success": True, 
                "message": "Sistema creado exitosamente",
                "id": nuevo.get('SistemaID'),
                "codigo": nuevo.get('Codigo'),
                "descripcion": nuevo.get('Descripcion'),
                "estado": "ACTIVO"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al crear sistema")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sistemas/{sistema_id}")
async def actualizar_sistema(
    sistema_id: int,
    body: CatalogoRegistroUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un tipo de sistema existente.
    
    Requiere: Administrador
    """
    from fastapi import HTTPException
    from core.db import execute_sql_query
    
    if current_user.get('role') not in ['Administrador', 'Supervisor']:
        raise HTTPException(status_code=403, detail="Sin permisos para editar sistemas")
    
    descripcion = body.datos.get('Descripcion', '').strip()
    
    if not descripcion:
        raise HTTPException(status_code=400, detail="Descripción es obligatoria")
    
    # Verificar duplicados (excepto el actual)
    check_query = f"""
        SELECT COUNT(*) as cnt FROM Sistema_Catalogo 
        WHERE Descripcion = '{Descripcion}' AND SistemaID <> {sistema_id}
    """
    try:
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            check_query
        )
        if result and result[0].get('cnt', 0) > 0:
            raise HTTPException(status_code=400, detail="Ya existe otro sistema con esa descripción")
        
        # Actualizar
        update_query = f"""
            UPDATE Sistema_Catalogo 
            SET Descripcion = '{Descripcion}', FechaActualizacion = SYSDATETIME()
            WHERE SistemaID = {sistema_id}
        """
        execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            update_query
        )
        
        return {"success": True, "message": "Sistema actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sistemas/{sistema_id}/toggle-activo")
async def toggle_sistema_activo(
    sistema_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Activa o inactiva un tipo de sistema.
    
    Requiere: CATALOGOS_SISTEMAS_ACTIVAR_INACTIVAR
    """
    from fastapi import HTTPException
    from core.db import execute_sql_query
    
    if not _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_ACTIVAR):
        raise HTTPException(status_code=403, detail="Sin permisos para activar/inactivar sistemas")
    
    try:
        # Obtener estado actual
        get_query = f"SELECT Activo, Estado FROM Sistema_Catalogo WHERE SistemaID = {sistema_id}"
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            get_query
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Sistema no encontrado")
        
        nuevo_activo = 0 if result[0].get('Activo') else 1
        nuevo_estado = 'ACTIVO' if nuevo_activo else 'INACTIVO'
        
        user_email = current_user.get('email', 'unknown')
        
        # Actualizar
        update_query = f"""
            UPDATE Sistema_Catalogo 
            SET Activo = {nuevo_activo}, 
                Estado = '{nuevo_estado}',
                FechaActualizacion = SYSDATETIME()
            WHERE SistemaID = {sistema_id}
        """
        execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            update_query
        )
        
        estado_texto = "activado" if nuevo_activo else "inactivado"
        return {"success": True, "message": f"Sistema {estado_texto}", "activo": bool(nuevo_activo), "estado": nuevo_estado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sistemas/{sistema_id}/autorizar")
async def autorizar_sistema(
    sistema_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Autoriza una solicitud de sistema pendiente.
    
    Requiere: CATALOGOS_SISTEMAS_AUTORIZAR
    """
    from fastapi import HTTPException
    from core.db import execute_sql_query
    
    if not _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_AUTORIZAR):
        raise HTTPException(status_code=403, detail="Sin permisos para autorizar sistemas")
    
    try:
        # Verificar que existe y está pendiente
        get_query = f"SELECT Estado, Descripcion FROM Sistema_Catalogo WHERE SistemaID = {sistema_id}"
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            get_query
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Sistema no encontrado")
        
        if result[0].get('Estado') != 'PENDIENTE':
            raise HTTPException(status_code=400, detail="Solo se pueden autorizar sistemas pendientes")
        
        user_email = current_user.get('email', 'unknown')
        descripcion = result[0].get('Descripcion', '')
        
        # Autorizar
        update_query = f"""
            UPDATE Sistema_Catalogo 
            SET Activo = 1, 
                Estado = 'ACTIVO',
                AutorizadoPorEmail = '{user_email}',
                FechaAutorizacion = SYSDATETIME(),
                FechaActualizacion = SYSDATETIME()
            WHERE SistemaID = {sistema_id}
        """
        execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            update_query
        )
        
        return {
            "success": True, 
            "message": f"Sistema '{descripcion}' autorizado exitosamente",
            "estado": "ACTIVO"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sistemas/{sistema_id}/rechazar")
async def rechazar_sistema(
    sistema_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Rechaza una solicitud de sistema pendiente.
    
    Requiere: CATALOGOS_SISTEMAS_AUTORIZAR
    """
    from fastapi import HTTPException
    from core.db import execute_sql_query
    
    if not _tiene_permiso_sistemas(current_user, PERM_SISTEMAS_AUTORIZAR):
        raise HTTPException(status_code=403, detail="Sin permisos para rechazar sistemas")
    
    try:
        # Verificar que existe y está pendiente
        get_query = f"SELECT Estado, Descripcion FROM Sistema_Catalogo WHERE SistemaID = {sistema_id}"
        result = execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            get_query
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Sistema no encontrado")
        
        if result[0].get('Estado') != 'PENDIENTE':
            raise HTTPException(status_code=400, detail="Solo se pueden rechazar sistemas pendientes")
        
        user_email = current_user.get('email', 'unknown')
        descripcion = result[0].get('Descripcion', '')
        
        # Rechazar
        update_query = f"""
            UPDATE Sistema_Catalogo 
            SET Activo = 0, 
                Estado = 'RECHAZADO',
                AutorizadoPorEmail = '{user_email}',
                FechaAutorizacion = SYSDATETIME(),
                FechaActualizacion = SYSDATETIME()
            WHERE SistemaID = {sistema_id}
        """
        execute_sql_query(
            os.getenv('EDARSAHUB_SQL_HOST'), 1433, 'EDARSAHUB', os.getenv('EDARSAHUB_SQL_USER'), os.getenv('EDARSAHUB_SQL_PASSWORD'),
            update_query
        )
        
        return {
            "success": True, 
            "message": f"Sistema '{descripcion}' rechazado",
            "estado": "RECHAZADO"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE CONSULTA
# ============================================================================

@router.get("/dominios")
async def listar_dominios(current_user: Dict = Depends(get_current_user)):
    """
    Lista todos los dominios de catálogos con sus catálogos y conteos.
    
    Retorna la estructura completa del módulo de catálogos organizada por dominio
    (Generales, RH, Nómina, Compras, etc.) con información de cada catálogo.
    """
    service = get_catalogos_service()
    dominios = await service.obtener_dominios()
    return {"success": True, "dominios": dominios}


@router.get("/tabla/{tabla}")
async def listar_catalogo(
    tabla: str,
    solo_activos: bool = Query(False, description="Filtrar solo registros activos"),
    buscar: Optional[str] = Query(None, description="Texto de búsqueda"),
    limit: int = Query(500, ge=1, le=2000, description="Máximo de registros"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista registros de un catálogo específico.
    
    Args:
        tabla: Nombre de la tabla del catálogo
        solo_activos: Si True, solo retorna registros activos
        buscar: Texto para filtrar por nombre/descripción
        limit: Máximo de registros a retornar
    """
    service = get_catalogos_service()
    return await service.listar_catalogo(tabla, solo_activos, buscar, limit)


@router.get("/tabla/{tabla}/{id}")
async def obtener_registro(
    tabla: str,
    id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene un registro específico de un catálogo.
    
    Args:
        tabla: Nombre de la tabla
        id: ID del registro
    """
    service = get_catalogos_service()
    registro = await service.obtener_registro(tabla, id)
    return {"success": True, "data": registro}


@router.get("/estructura/{tabla}")
async def obtener_estructura(
    tabla: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene la estructura de una tabla (campos, tipos, etc.).
    
    Útil para generar formularios dinámicos en el frontend.
    """
    service = get_catalogos_service()
    return await service.obtener_estructura_tabla(tabla)


# ============================================================================
# ENDPOINTS DE MODIFICACIÓN
# ============================================================================

@router.post("/tabla/{tabla}")
async def crear_registro(
    tabla: str,
    body: CatalogoRegistroCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo registro en un catálogo.
    
    Args:
        tabla: Nombre de la tabla
        body: Datos del registro a crear
    
    Requiere rol: Administrador o Supervisor
    """
    if current_user.get('role') not in ['Administrador', 'Supervisor']:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos para crear registros")
    
    service = get_catalogos_service()
    return await service.crear_registro(
        tabla, 
        body.datos, 
        current_user.get('email', '')
    )


@router.put("/tabla/{tabla}/{id}")
async def actualizar_registro(
    tabla: str,
    id: int,
    body: CatalogoRegistroUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un registro existente.
    
    Args:
        tabla: Nombre de la tabla
        id: ID del registro
        body: Datos a actualizar
    
    Requiere rol: Administrador o Supervisor
    """
    if current_user.get('role') not in ['Administrador', 'Supervisor']:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos para editar registros")
    
    service = get_catalogos_service()
    return await service.actualizar_registro(
        tabla, 
        id, 
        body.datos,
        current_user.get('email', '')
    )


@router.put("/tabla/{tabla}/{id}/desactivar")
async def desactivar_registro(
    tabla: str,
    id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Desactiva un registro (soft delete).
    
    El registro no se elimina físicamente, solo se marca como inactivo.
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden desactivar registros")
    
    service = get_catalogos_service()
    return await service.desactivar_registro(tabla, id)


@router.put("/tabla/{tabla}/{id}/activar")
async def activar_registro(
    tabla: str,
    id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Reactiva un registro previamente desactivado.
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden activar registros")
    
    service = get_catalogos_service()
    return await service.activar_registro(tabla, id)


# ============================================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================================

@router.post("/admin/crear-tablas")
async def crear_tablas_nuevas(current_user: Dict = Depends(get_current_user)):
    """
    Ejecuta el DDL para crear las tablas globales nuevas.
    
    Crea las siguientes tablas si no existen:
    - Global_Cat_Empresas
    - Global_Cat_Bancos
    - Global_Cat_UnidadesMedida
    - Global_Cat_CentrosCosto
    - Global_Cat_FormaPagoSAT
    - Global_Cat_MetodoPagoSAT
    - Global_Cat_UsoCFDI
    - Global_Cat_RegimenFiscal
    - Finanzas_Cat_CuentasBancarias
    
    También inserta datos iniciales (bancos, formas de pago SAT, etc.)
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear tablas")
    
    service = get_catalogos_service()
    return await service.crear_tablas_nuevas()


@router.get("/admin/verificar-tablas")
async def verificar_tablas_nuevas(current_user: Dict = Depends(get_current_user)):
    """
    Verifica qué tablas globales nuevas existen.
    
    Retorna un diccionario con el estado de cada tabla.
    """
    service = get_catalogos_service()
    estado = await service.verificar_tablas_nuevas()
    return {"success": True, "tablas": estado}


@router.get("/admin/script-ddl")
async def obtener_script_ddl(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el script DDL para revisión antes de ejecutar.
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver el script DDL")
    
    service = get_catalogos_service()
    script = await service.obtener_script_ddl()
    return {"success": True, "script": script}
