from core.rbac_sql.service import RBACSQLService

def build_user_access_context(usuario_id):
    """
    Contexto único SQL-First:
    usuario -> roles -> empresas -> unidades -> sucursales
    """
    return RBACSQLService.build_context(usuario_id)

def can_access_empresa(usuario_id, empresa_id):
    return RBACSQLService.can_access_empresa(usuario_id, empresa_id)

def can_access_unidad(usuario_id, unidad_id):
    return RBACSQLService.can_access_unidad(usuario_id, unidad_id)

def can_access_sucursal(usuario_id, sucursal_id):
    return RBACSQLService.can_access_sucursal(usuario_id, sucursal_id)
