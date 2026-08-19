from pathlib import Path


ROOT = Path("/app")
REPOSITORY = ROOT / "backend/modules/auth/repository.py"
SERVICE = ROOT / "backend/modules/auth/service.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_role_save_uses_canonical_sql_catalog():
    text = _text(REPOSITORY)

    assert "dbo.Usuario_Roles" in text
    assert "LOWER(CodigoRol) = LOWER(%s)" in text
    assert "LOWER(NombreRol) = LOWER(%s)" in text
    assert "Activo = 1" in text


def test_role_save_updates_primary_assignment():
    text = _text(REPOSITORY)

    assert "dbo.Usuario_RolesAsignacion" in text
    assert "EsPrincipal = 1" in text
    assert "RolID <> %s" in text
    assert "Invariante de rol principal violada" in text


def test_no_role_hardcode_map_or_fallback():
    text = _text(REPOSITORY)

    assert "ROL_MONGO_TO_SQL" not in text
    assert ".get(update_data['role'], 'USUARIO')" not in text
    assert ".get(update_data[\"role\"], \"USUARIO\")" not in text


def test_role_save_is_transactional_and_fail_closed():
    text = _text(REPOSITORY)

    assert "conn.commit()" in text
    assert "conn.rollback()" in text
    assert "raise ValueError" in text
    assert "raise RuntimeError" in text


def test_role_context_is_not_modified():
    text = _text(REPOSITORY)

    block = text[
        text.index("async def update_user("):
        text.index("async def delete_user(")
    ]

    assert "Usuario_RolesContexto" not in block


def test_service_rejects_false_success():
    text = _text(SERVICE)

    assert "updated = await repo.update_user(user_id, update_data)" in text
    assert "if updated is not True:" in text
    assert "No fue posible persistir la actualización del usuario" in text


def test_same_role_can_be_reused_instead_of_blind_insert():
    text = _text(REPOSITORY)

    assert "reusable_id" in text
    assert "UPDATE dbo.Usuario_RolesAsignacion" in text
    assert "UsuarioRolAsignacionID <> %s" in text
