from core.rbac_sql.service import RBACSQLService

def get_user_access_context_sql(usuario_id):
    return RBACSQLService.build_context(usuario_id)

def can_access_empresa_sql(usuario_id, empresa_id):
    return RBACSQLService.can_access_empresa(usuario_id, empresa_id)

def can_access_unidad_sql(usuario_id, unidad_id):
    return RBACSQLService.can_access_unidad(usuario_id, unidad_id)

def can_access_servidor_sql(usuario_id, servidor_id):
    return RBACSQLService.can_access_servidor(usuario_id, servidor_id)

def can_access_sucursal_sql(usuario_id, servidor_id, sucursal_codigo):
    return RBACSQLService.can_access_sucursal(usuario_id, servidor_id, sucursal_codigo)

def can_access_permission_sql(
    usuario_id,
    permission_code,
):
    return RBACSQLService.can_access_permission(
        usuario_id,
        permission_code,
    )


def get_permission_scope_by_code_sql(
    usuario_id,
    permission_code,
):
    return RBACSQLService.get_permission_scope_by_code(
        usuario_id,
        permission_code,
    )


def get_scope_assignment_state_sql(usuario_id):
    return RBACSQLService.get_scope_assignment_state(
        usuario_id
    )


def can_access_unit_metadata_sql(
    usuario_id,
    permission_code,
    metadata,
):
    return RBACSQLService.can_access_unit_metadata(
        usuario_id,
        permission_code,
        metadata,
    )
