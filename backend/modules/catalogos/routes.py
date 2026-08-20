import os
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
from core.rbac.middleware import require_explicit_permission
from core.rbac_helper_sql import es_admin, es_supervisor_o_superior
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
            VALUES ('{codigo}', '{descripcion.replace("'", "''")}', 0, 'PENDIENTE', '{user_email}', SYSDATETIME())
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
        WHERE Codigo = '{codigo}' OR Descripcion = '{descripcion.replace("'", "''")}'
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
            VALUES ('{codigo}', '{descripcion.replace("'", "''")}', 1, 'ACTIVO', '{user_email}', SYSDATETIME(), '{user_email}', SYSDATETIME())
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
    
    if not es_supervisor_o_superior(current_user):
        raise HTTPException(status_code=403, detail="Sin permisos para editar sistemas")
    
    descripcion = body.datos.get('Descripcion', '').strip()
    
    if not descripcion:
        raise HTTPException(status_code=400, detail="Descripción es obligatoria")
    
    # Verificar duplicados (excepto el actual)
    check_query = f"""
        SELECT COUNT(*) as cnt FROM Sistema_Catalogo 
        WHERE Descripcion = '{descripcion}' AND SistemaID <> {sistema_id}
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
            SET Descripcion = '{descripcion}', FechaActualizacion = SYSDATETIME()
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
    if not es_supervisor_o_superior(current_user):
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
    if not es_supervisor_o_superior(current_user):
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
    if not es_admin(current_user):
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
    if not es_admin(current_user):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden activar registros")
    
    service = get_catalogos_service()
    return await service.activar_registro(tabla, id)


# ============================================================================
# MATRICES DE AUTORIZACION - CONSULTA CANONICA
# ============================================================================

@router.get("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")
async def obtener_matriz_autorizacion(
    tipo_autorizacion_id: int,
    current_user: Dict = Depends(
        require_explicit_permission("SEGURIDAD_CONFIGURAR")
    ),
):
    """
    Consulta la matriz canonica asociada a un tipo de autorizacion.

    Fuente unica:
      dbo.Usuario_TiposAutorizacion
      dbo.Usuario_MatrizAutorizacion
      dbo.Usuario_Roles
      dbo.Usuario_Catalogo

    Este endpoint es deliberadamente read-only en esta fase.
    """
    from core.connections.hrlectura_connection_factory import (
        build_hrlectura_connection_factory,
    )

    conn = build_hrlectura_connection_factory()()
    cur = conn.cursor(as_dict=True)

    try:
        cur.execute(
            """
            SELECT
                TA.TipoAutorizacionID,
                TA.CodigoTipoAutorizacion,
                TA.NombreTipoAutorizacion,
                TA.Descripcion,
                TA.ModuloID,
                TA.AccionID,
                TA.RequiereUnidadNegocio,
                TA.ModoAutorizacion,
                TA.Activo
            FROM dbo.Usuario_TiposAutorizacion AS TA
            WHERE TA.TipoAutorizacionID = %s
            """,
            (tipo_autorizacion_id,),
        )

        tipo = cur.fetchone()

        if not tipo:
            raise HTTPException(
                status_code=404,
                detail="Tipo de autorizacion no encontrado",
            )

        cur.execute(
            """
            SELECT
                MA.MatrizAutorizacionID,
                MA.TipoAutorizacionID,
                MA.NivelAutorizacion,
                MA.RolID,
                R.CodigoRol,
                R.NombreRol,
                MA.UsuarioID,
                U.NombreCompleto AS NombreUsuario,
                U.Email AS EmailUsuario,
                MA.MontoMinimo,
                MA.MontoMaximo,
                MA.Prioridad,
                MA.RequiereTodosLosNiveles,
                MA.Activo,
                MA.FechaAlta,
                MA.FechaModificacion
            FROM dbo.Usuario_MatrizAutorizacion AS MA
            INNER JOIN dbo.Usuario_Roles AS R
                ON R.RolID = MA.RolID
            LEFT JOIN dbo.Usuario_Catalogo AS U
                ON U.UsuarioID = MA.UsuarioID
            WHERE MA.TipoAutorizacionID = %s
            ORDER BY
                MA.NivelAutorizacion,
                MA.Prioridad,
                MA.MatrizAutorizacionID
            """,
            (tipo_autorizacion_id,),
        )

        matriz = cur.fetchall() or []

        return {
            "success": True,
            "tipo": tipo,
            "matriz": matriz,
            "total": len(matriz),
        }

    finally:
        conn.close()


@router.get("/autorizaciones/catalogos")
async def obtener_catalogos_matriz_autorizacion(
    current_user: Dict = Depends(
        require_explicit_permission("SEGURIDAD_CONFIGURAR")
    ),
):
    """
    Catalogos canonicos necesarios para construir selectores de la
    administracion de matrices. No expone IDs para captura manual.
    """
    from core.connections.hrlectura_connection_factory import (
        build_hrlectura_connection_factory,
    )

    conn = build_hrlectura_connection_factory()()
    cur = conn.cursor(as_dict=True)

    try:
        cur.execute(
            """
            SELECT
                RolID,
                CodigoRol,
                NombreRol
            FROM dbo.Usuario_Roles
            WHERE Activo = 1
            ORDER BY NombreRol, RolID
            """
        )
        roles = cur.fetchall() or []

        cur.execute(
            """
            SELECT
                ModuloID,
                CodigoModulo,
                NombreModulo
            FROM dbo.Usuario_Modulos
            WHERE Activo = 1
            ORDER BY NombreModulo, ModuloID
            """
        )
        modulos = cur.fetchall() or []

        cur.execute(
            """
            SELECT
                AccionID,
                CodigoAccion,
                NombreAccion
            FROM dbo.Usuario_Acciones
            WHERE Activo = 1
            ORDER BY NombreAccion, AccionID
            """
        )
        acciones = cur.fetchall() or []

        cur.execute(
            """
            SELECT
                UsuarioID,
                NombreCompleto,
                Email
            FROM dbo.Usuario_Catalogo
            WHERE Activo = 1
            ORDER BY NombreCompleto, UsuarioID
            """
        )
        usuarios = cur.fetchall() or []

        return {
            "success": True,
            "roles": roles,
            "modulos": modulos,
            "acciones": acciones,
            "usuarios": usuarios,
        }

    finally:
        conn.close()



@router.post("/autorizaciones/tipos/{tipo_autorizacion_id}/matriz")
async def crear_fila_matriz_autorizacion(
    tipo_autorizacion_id: int,
    body: Dict[str, Any],
    current_user: Dict = Depends(
        require_explicit_permission("SEGURIDAD_CONFIGURAR")
    ),
):
    """
    Crea una fila de la matriz canonica de autorizacion.

    Validaciones fail-closed:
    - tipo activo
    - rol activo
    - usuario activo cuando se especifica
    - usuario compatible con rol
    - nivel valido
    - prioridad positiva
    - rango monetario valido
    - no duplicidad exacta de nivel/rol
    - no solapamiento de rangos dentro del mismo tipo
    """
    from fastapi import HTTPException
    from core.db import get_edarsahub_pymssql_connection

    nivel = body.get("NivelAutorizacion")
    rol_id = body.get("RolID")
    usuario_id = body.get("UsuarioID")
    monto_minimo = body.get("MontoMinimo")
    monto_maximo = body.get("MontoMaximo")
    prioridad = body.get("Prioridad", 1)
    requiere_todos = bool(body.get("RequiereTodosLosNiveles", False))
    activo = bool(body.get("Activo", True))

    if not isinstance(nivel, int) or nivel <= 0:
        raise HTTPException(
            status_code=400,
            detail="NivelAutorizacion debe ser entero positivo",
        )

    if not isinstance(rol_id, int) or rol_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="RolID requerido",
        )

    if not isinstance(prioridad, int) or prioridad <= 0:
        raise HTTPException(
            status_code=400,
            detail="Prioridad debe ser entero positivo",
        )

    if monto_minimo is not None:
        monto_minimo = float(monto_minimo)

    if monto_maximo is not None:
        monto_maximo = float(monto_maximo)

    if (
        monto_minimo is not None
        and monto_maximo is not None
        and monto_minimo > monto_maximo
    ):
        raise HTTPException(
            status_code=400,
            detail="MontoMinimo no puede ser mayor que MontoMaximo",
        )

    conn = get_edarsahub_pymssql_connection(
        timeout=30,
        login_timeout=10,
    )
    cur = conn.cursor(as_dict=True)

    try:
        cur.execute(
            """
            SELECT
                TipoAutorizacionID,
                ModoAutorizacion
            FROM dbo.Usuario_TiposAutorizacion
            WHERE TipoAutorizacionID = %s
              AND Activo = 1
            """,
            (tipo_autorizacion_id,),
        )
        tipo_row = cur.fetchone()

        if not tipo_row:
            raise HTTPException(
                status_code=404,
                detail="Tipo de autorizacion inexistente o inactivo",
            )

        modo_autorizacion = str(
            tipo_row.get("ModoAutorizacion")
            or "ESCALABLE"
        ).upper()

        if modo_autorizacion not in (
            "ESCALABLE",
            "MANCOMUNADA",
        ):
            raise HTTPException(
                status_code=409,
                detail="Modo de autorizacion canonico invalido",
            )

        if modo_autorizacion == "MANCOMUNADA":
            requiere_todos = True

        cur.execute(
            """
            SELECT RolID
            FROM dbo.Usuario_Roles
            WHERE RolID = %s
              AND Activo = 1
            """,
            (rol_id,),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Rol inexistente o inactivo",
            )

        if usuario_id is not None:
            if not isinstance(usuario_id, int) or usuario_id <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="UsuarioID invalido",
                )

            cur.execute(
                """
                SELECT UsuarioID
                FROM dbo.Usuario_Catalogo
                WHERE UsuarioID = %s
                  AND Activo = 1
                """,
                (usuario_id,),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Usuario inexistente o inactivo",
                )

            cur.execute(
                """
                SELECT TOP 1 1 AS ok
                FROM dbo.Usuario_RolesContexto
                WHERE UsuarioID = %s
                  AND RolID = %s
                  AND Activo = 1
                  AND (
                        FechaBaja IS NULL
                        OR FechaBaja > SYSDATETIME()
                      )
                """,
                (usuario_id, rol_id),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="UsuarioID no tiene el RolID activo indicado",
                )

        cur.execute(
            """
            SELECT TOP 1 MatrizAutorizacionID
            FROM dbo.Usuario_MatrizAutorizacion
            WHERE TipoAutorizacionID = %s
              AND NivelAutorizacion = %s
              AND RolID = %s
              AND Activo = 1
            """,
            (
                tipo_autorizacion_id,
                nivel,
                rol_id,
            ),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Ya existe una fila activa para ese nivel y rol",
            )

        cur.execute(
            """
            SELECT TOP 1
                MatrizAutorizacionID
            FROM dbo.Usuario_MatrizAutorizacion
            WHERE TipoAutorizacionID = %s
              AND Activo = 1
              AND (
                    (
                        %s IS NULL
                        OR MontoMaximo IS NULL
                        OR %s <= MontoMaximo
                    )
                    AND
                    (
                        %s IS NULL
                        OR MontoMinimo IS NULL
                        OR %s >= MontoMinimo
                    )
                  )
            """,
            (
                tipo_autorizacion_id,
                monto_minimo,
                monto_minimo,
                monto_maximo,
                monto_maximo,
            ),
        )
        overlap_row = cur.fetchone()

        if (
            overlap_row
            and modo_autorizacion == "ESCALABLE"
        ):
            raise HTTPException(
                status_code=409,
                detail="El rango monetario se solapa con una fila activa existente",
            )

        cur.execute(
            """
            SELECT ISNULL(MAX(MatrizAutorizacionID), 0) + 1 AS next_id
            FROM dbo.Usuario_MatrizAutorizacion WITH (UPDLOCK, HOLDLOCK)
            """
        )
        next_id = int(cur.fetchone()["next_id"])

        cur.execute(
            """
            INSERT INTO dbo.Usuario_MatrizAutorizacion (
                MatrizAutorizacionID,
                TipoAutorizacionID,
                NivelAutorizacion,
                RolID,
                UsuarioID,
                MontoMinimo,
                MontoMaximo,
                Prioridad,
                RequiereTodosLosNiveles,
                Activo,
                FechaAlta
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                SYSDATETIME()
            )
            """,
            (
                next_id,
                tipo_autorizacion_id,
                nivel,
                rol_id,
                usuario_id,
                monto_minimo,
                monto_maximo,
                prioridad,
                1 if requiere_todos else 0,
                1 if activo else 0,
            ),
        )

        conn.commit()

        return {
            "success": True,
            "MatrizAutorizacionID": next_id,
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creando matriz: {exc}",
        )
    finally:
        conn.close()


@router.put("/autorizaciones/matriz/{matriz_autorizacion_id}")
async def actualizar_fila_matriz_autorizacion(
    matriz_autorizacion_id: int,
    body: Dict[str, Any],
    current_user: Dict = Depends(
        require_explicit_permission("SEGURIDAD_CONFIGURAR")
    ),
):
    """
    Actualiza una fila existente de matriz con las mismas
    validaciones canonicas del alta.
    """
    from fastapi import HTTPException
    from core.db import get_edarsahub_pymssql_connection

    allowed = {
        "NivelAutorizacion",
        "RolID",
        "UsuarioID",
        "MontoMinimo",
        "MontoMaximo",
        "Prioridad",
        "RequiereTodosLosNiveles",
        "Activo",
    }

    payload = {
        key: value
        for key, value in body.items()
        if key in allowed
    }

    if not payload:
        raise HTTPException(
            status_code=400,
            detail="No hay campos validos para actualizar",
        )

    conn = get_edarsahub_pymssql_connection(
        timeout=30,
        login_timeout=10,
    )
    cur = conn.cursor(as_dict=True)

    try:
        cur.execute(
            """
            SELECT
                MA.*,
                TA.ModoAutorizacion
            FROM dbo.Usuario_MatrizAutorizacion AS MA
            INNER JOIN dbo.Usuario_TiposAutorizacion AS TA
                ON TA.TipoAutorizacionID = MA.TipoAutorizacionID
            WHERE MA.MatrizAutorizacionID = %s
            """,
            (matriz_autorizacion_id,),
        )
        current = cur.fetchone()

        if not current:
            raise HTTPException(
                status_code=404,
                detail="Fila de matriz no encontrada",
            )

        modo_autorizacion = str(
            current.get("ModoAutorizacion")
            or "ESCALABLE"
        ).upper()

        if modo_autorizacion not in (
            "ESCALABLE",
            "MANCOMUNADA",
        ):
            raise HTTPException(
                status_code=409,
                detail="Modo de autorizacion canonico invalido",
            )

        nivel = payload.get(
            "NivelAutorizacion",
            current["NivelAutorizacion"],
        )
        rol_id = payload.get(
            "RolID",
            current["RolID"],
        )
        usuario_id = (
            payload["UsuarioID"]
            if "UsuarioID" in payload
            else current["UsuarioID"]
        )
        monto_minimo = (
            payload["MontoMinimo"]
            if "MontoMinimo" in payload
            else current["MontoMinimo"]
        )
        monto_maximo = (
            payload["MontoMaximo"]
            if "MontoMaximo" in payload
            else current["MontoMaximo"]
        )
        prioridad = payload.get(
            "Prioridad",
            current["Prioridad"],
        )
        requiere_todos = payload.get(
            "RequiereTodosLosNiveles",
            current["RequiereTodosLosNiveles"],
        )

        if modo_autorizacion == "MANCOMUNADA":
            requiere_todos = True
        activo = payload.get(
            "Activo",
            current["Activo"],
        )

        if not isinstance(nivel, int) or nivel <= 0:
            raise HTTPException(
                status_code=400,
                detail="NivelAutorizacion debe ser entero positivo",
            )

        if not isinstance(rol_id, int) or rol_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="RolID requerido",
            )

        if not isinstance(prioridad, int) or prioridad <= 0:
            raise HTTPException(
                status_code=400,
                detail="Prioridad debe ser entero positivo",
            )

        if monto_minimo is not None:
            monto_minimo = float(monto_minimo)

        if monto_maximo is not None:
            monto_maximo = float(monto_maximo)

        if (
            monto_minimo is not None
            and monto_maximo is not None
            and monto_minimo > monto_maximo
        ):
            raise HTTPException(
                status_code=400,
                detail="MontoMinimo no puede ser mayor que MontoMaximo",
            )

        cur.execute(
            """
            SELECT RolID
            FROM dbo.Usuario_Roles
            WHERE RolID = %s
              AND Activo = 1
            """,
            (rol_id,),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Rol inexistente o inactivo",
            )

        if usuario_id is not None:
            cur.execute(
                """
                SELECT TOP 1 1 AS ok
                FROM dbo.Usuario_Catalogo u
                INNER JOIN dbo.Usuario_RolesContexto urc
                    ON urc.UsuarioID = u.UsuarioID
                   AND urc.RolID = %s
                   AND urc.Activo = 1
                   AND (
                        urc.FechaBaja IS NULL
                        OR urc.FechaBaja > SYSDATETIME()
                   )
                WHERE u.UsuarioID = %s
                  AND u.Activo = 1
                """,
                (
                    rol_id,
                    usuario_id,
                ),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="UsuarioID no es autorizador activo para el RolID indicado",
                )

        cur.execute(
            """
            SELECT TOP 1 MatrizAutorizacionID
            FROM dbo.Usuario_MatrizAutorizacion
            WHERE TipoAutorizacionID = %s
              AND NivelAutorizacion = %s
              AND RolID = %s
              AND MatrizAutorizacionID <> %s
              AND Activo = 1
            """,
            (
                current["TipoAutorizacionID"],
                nivel,
                rol_id,
                matriz_autorizacion_id,
            ),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Ya existe otra fila activa para ese nivel y rol",
            )

        cur.execute(
            """
            SELECT TOP 1 MatrizAutorizacionID
            FROM dbo.Usuario_MatrizAutorizacion
            WHERE TipoAutorizacionID = %s
              AND MatrizAutorizacionID <> %s
              AND Activo = 1
              AND (
                    (
                        %s IS NULL
                        OR MontoMaximo IS NULL
                        OR %s <= MontoMaximo
                    )
                    AND
                    (
                        %s IS NULL
                        OR MontoMinimo IS NULL
                        OR %s >= MontoMinimo
                    )
                  )
            """,
            (
                current["TipoAutorizacionID"],
                matriz_autorizacion_id,
                monto_minimo,
                monto_minimo,
                monto_maximo,
                monto_maximo,
            ),
        )
        overlap_row = cur.fetchone()

        if (
            overlap_row
            and modo_autorizacion == "ESCALABLE"
        ):
            raise HTTPException(
                status_code=409,
                detail="El rango monetario se solapa con otra fila activa",
            )

        cur.execute(
            """
            UPDATE dbo.Usuario_MatrizAutorizacion
            SET
                NivelAutorizacion = %s,
                RolID = %s,
                UsuarioID = %s,
                MontoMinimo = %s,
                MontoMaximo = %s,
                Prioridad = %s,
                RequiereTodosLosNiveles = %s,
                Activo = %s,
                FechaModificacion = SYSDATETIME()
            WHERE MatrizAutorizacionID = %s
            """,
            (
                nivel,
                rol_id,
                usuario_id,
                monto_minimo,
                monto_maximo,
                prioridad,
                1 if bool(requiere_todos) else 0,
                1 if bool(activo) else 0,
                matriz_autorizacion_id,
            ),
        )

        if cur.rowcount != 1:
            raise RuntimeError(
                f"UPDATE_ROWCOUNT={cur.rowcount}"
            )

        conn.commit()

        return {
            "success": True,
            "MatrizAutorizacionID": matriz_autorizacion_id,
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando matriz: {exc}",
        )
    finally:
        conn.close()



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
    if not es_admin(current_user):
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
    if not es_admin(current_user):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver el script DDL")
    
    service = get_catalogos_service()
    script = await service.obtener_script_ddl()
    return {"success": True, "script": script}
