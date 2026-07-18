from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "backend/database/migrations"
VALIDATIONS = ROOT / "backend/database/validation"


def _single_file(
    directory: Path,
    marker: str,
) -> Path:
    matches = []

    for path in directory.glob("*.sql"):
        text = path.read_text(
            encoding="utf-8",
            errors="strict",
        )

        if marker in text:
            matches.append(path)

    assert len(matches) == 1, (
        marker,
        [str(path) for path in matches],
    )

    return matches[0]


def test_ia_migration_contract():
    path = _single_file(
        MIGRATIONS,
        "EDARSAHUB:IA_ASSISTANT:SCHEMA_RBAC",
    )

    source = path.read_text(encoding="utf-8")

    required = (
        "SET XACT_ABORT ON",
        "BEGIN TRANSACTION",
        "sp_getapplock",
        "IA_Assistant_Sesiones",
        "IA_Assistant_Mensajes",
        "FK_IA_Assistant_Mensajes_Sesion",
        "mensajes IA huérfanos",
        "IX_IA_Assistant_Sesiones_Usuario_Activo",
        "Usuario_Modulos",
        "Usuario_PermisosRolModulo",
        "IA_ASSISTANT",
        "IA_ASSISTANT_V1",
        "SUPERADMIN",
        "ADMINISTRADOR",
        "Sistema_Modulos",
        "Sistema_ModulosMenus",
        "RequierePermiso",
        "N'/ia'",
        "COMMIT TRANSACTION",
        "ROLLBACK TRANSACTION",
    )

    for token in required:
        assert token in source

    forbidden = (
        r"\bDROP\s+TABLE\b",
        r"\bTRUNCATE\s+TABLE\b",
        r"\bDELETE\s+FROM\b",
        r"\bMERGE\b",
        r"\bGO\b",
    )

    for pattern in forbidden:
        assert not re.search(
            pattern,
            source,
            flags=re.IGNORECASE,
        )


def test_existing_ia_system_module_is_preserved():
    migration = _single_file(
        MIGRATIONS,
        "EDARSAHUB:IA_ASSISTANT:SCHEMA_RBAC",
    ).read_text(encoding="utf-8")

    assert (
        "PRESERVE_EXISTING_IA_SYSTEM_MODULE"
        in migration
    )

    assert not re.search(
        r"UPDATE\s+dbo\.Sistema_Modulos\s+SET",
        migration,
        flags=re.IGNORECASE,
    )

    assert "N'Inteligencia Artificial'" in migration
    assert "N'Asistentes, análisis, automatización'" in migration
    assert "N'Brain'" in migration

    assert (
        "RequierePermiso = N'IA_ASSISTANT'"
        in migration
    )

    assert "IA_ASSISTANT_VER" not in migration


def test_ia_validation_is_read_only():
    path = _single_file(
        VALIDATIONS,
        "IA_ASSISTANT_VALIDATION",
    )

    source = path.read_text(encoding="utf-8")

    assert "DB_NAME()" in source
    assert "SUSER_SNAME()" in source
    assert "USER_NAME()" in source
    assert "mensajes_huerfanos" in source
    assert "IA_ASSISTANT" in source
    assert "RequierePermiso" in source
    assert "ia_assistant_validation" in source

    forbidden = (
        r"\bINSERT\s+INTO\b",
        r"\bUPDATE\s+\S+",
        r"\bDELETE\s+FROM\b",
        r"\bMERGE\b",
        r"\bCREATE\s+TABLE\b",
        r"\bALTER\s+TABLE\b",
        r"\bDROP\s+TABLE\b",
        r"\bTRUNCATE\s+TABLE\b",
    )

    body = re.sub(
        r"/\*.*?\*/",
        "",
        source,
        flags=re.DOTALL,
    )

    for pattern in forbidden:
        assert not re.search(
            pattern,
            body,
            flags=re.IGNORECASE,
        )


def test_ia_validation_batches_are_runner_compatible():
    path = _single_file(
        VALIDATIONS,
        "IA_ASSISTANT_VALIDATION",
    )

    source = path.read_text(encoding="utf-8")

    batches = [
        batch.strip()
        for batch in re.split(
            r"^\s*GO\s*$",
            source,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if batch.strip()
    ]

    assert len(batches) == 8
    assert source.count("\nGO\n") == 7

    assert "database_name" in batches[0]
    assert "foreign_key_name" in batches[2]
    assert "mensajes_huerfanos" in batches[4]
    assert "CodigoRol" in batches[5]
    assert "menu_codigo" in batches[6]

    assert (
        "ia_assistant_validation"
        in batches[7]
    )


def test_repository_matches_migration_tables():
    repository = (
        ROOT
        / "backend/modules/ia_assistant/repository.py"
    ).read_text(encoding="utf-8")

    migration = _single_file(
        MIGRATIONS,
        "EDARSAHUB:IA_ASSISTANT:SCHEMA_RBAC",
    ).read_text(encoding="utf-8")

    for table in (
        "IA_Assistant_Sesiones",
        "IA_Assistant_Mensajes",
    ):
        assert table in repository
        assert table in migration

    assert (
        "FK_IA_Assistant_Mensajes_Sesion"
        in repository
    )
    assert (
        "FK_IA_Assistant_Mensajes_Sesion"
        in migration
    )


def test_permission_is_aligned_across_layers():
    backend_routes = (
        ROOT
        / "backend/modules/ia_assistant/routes.py"
    ).read_text(encoding="utf-8")

    auth_routes = (
        ROOT
        / "backend/modules/auth/routes.py"
    ).read_text(encoding="utf-8")

    migration = _single_file(
        MIGRATIONS,
        "EDARSAHUB:IA_ASSISTANT:SCHEMA_RBAC",
    ).read_text(encoding="utf-8")

    assert 'IA_PERMISSION = "IA_ASSISTANT_VER"' in backend_routes
    assert '"IA_ASSISTANT_VER"' in auth_routes
    assert "IA_ASSISTANT" in migration
    assert "CodigoAccion = N'VER'" in migration
