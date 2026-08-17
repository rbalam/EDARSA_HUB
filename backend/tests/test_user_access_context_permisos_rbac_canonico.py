import ast
from pathlib import Path


BACKEND = Path(__file__).parents[1]

RBAC = (
    BACKEND
    / "core"
    / "rbac_sql"
    / "service.py"
)

CONTEXT = (
    BACKEND
    / "core"
    / "user_access_context.py"
)


def method_source(
    path,
    class_name,
    method_name,
):
    src = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(src)

    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name == class_name
        ):
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef)
                    and item.name == method_name
                ):
                    return (
                        ast.get_source_segment(
                            src,
                            item,
                        )
                        or ""
                    )

    raise AssertionError(
        f"{class_name}.{method_name} missing"
    )


def test_effective_permissions_usa_fuentes_canonicas():
    src = method_source(
        RBAC,
        "RBACSQLService",
        "get_effective_permissions",
    )

    for token in (
        "Usuario_RolesAsignacion",
        "Usuario_Roles",
        "Usuario_PermisosRolModulo",
        "Usuario_Modulos",
        "Usuario_Acciones",
        "Permitido",
    ):
        assert token in src


def test_effective_permissions_sin_role_bypass():
    src = method_source(
        RBAC,
        "RBACSQLService",
        "get_effective_permissions",
    )

    for token in (
        "LEGACY_ROLE_MAPPING",
        "nivel_jerarquia",
        "SUPERADMIN",
        "Administrador",
        "OPERADOR",
        'user.get("role"',
    ):
        assert token not in src


def test_context_usa_permisos_rbac_sql():
    src = CONTEXT.read_text(
        encoding="utf-8"
    )

    assert (
        "RBACSQLService.get_effective_permissions("
        in src
    )


def test_context_permisos_fail_closed():
    src = CONTEXT.read_text(
        encoding="utf-8"
    )

    assert "context.permisos = []" in src


def test_lookup_y_enumerador_comparten_tablas():
    enum_src = method_source(
        RBAC,
        "RBACSQLService",
        "get_effective_permissions",
    )

    lookup_src = method_source(
        RBAC,
        "RBACSQLService",
        "get_permission_scope_by_code",
    )

    for token in (
        "Usuario_RolesAsignacion",
        "Usuario_Roles",
        "Usuario_PermisosRolModulo",
        "Usuario_Modulos",
        "Usuario_Acciones",
    ):
        assert token in enum_src
        assert token in lookup_src


def test_context_enumera_permisos_con_usuario_id_sql():
    src = CONTEXT.read_text(
        encoding="utf-8"
    )

    expected = (
        "RBACSQLService.get_effective_permissions(\n"
        "            usuario_id\n"
        "        )"
    )

    assert expected in src

    forbidden = (
        "RBACSQLService.get_effective_permissions(\n"
        "            context.user_id\n"
        "        )"
    )

    assert forbidden not in src
