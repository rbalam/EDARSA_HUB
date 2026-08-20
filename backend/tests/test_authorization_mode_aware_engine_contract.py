from pathlib import Path

ROOT = Path("/app/backend")

MIG = (
    ROOT
    / "database/migrations"
    / "20260819_038_authorization_mode_aware_engine.sql"
)


def source():
    return MIG.read_text(encoding="utf-8")


def test_create_snapshots_authorization_mode():
    src = source()

    assert "@ModoAutorizacion" in src
    assert "ModoAutorizacion" in src
    assert "Usuario_Autorizaciones" in src


def test_engine_supports_both_modes():
    src = source()

    assert "'ESCALABLE'" in src
    assert "'MANCOMUNADA'" in src


def test_scalable_preserves_sequential_resolution():
    src = source()

    assert "ESCALABLE" in src
    assert "@ModoAutorizacion" in src
    assert "MIN(NivelAutorizacion)" in src

    resolver_block = src.split(
        "CREATE OR ALTER PROCEDURE dbo.sp_Usuario_ResolverAutorizacion",
        1,
    )[1]

    assert "IF @ModoAutorizacion" in resolver_block
    assert "MIN(NivelAutorizacion)" in resolver_block


def test_joint_mode_does_not_require_minimum_level_for_user():
    src = source()

    marker = "MANCOMUNADA:"
    assert marker in src

    block = src.split(marker, 1)[1]

    assert (
        "UsuarioAutorizadorID ="
        in block
    )
    assert (
        "Resultado = ''PENDIENTE''"
        in block
    )


def test_any_rejection_closes_request():
    src = source()

    assert (
        "IF @Resultado = ''RECHAZADA''"
        in src
    )
    assert (
        "EstatusAutorizacion = ''RECHAZADA''"
        in src
    )


def test_joint_approval_requires_no_pending_details():
    src = source()

    assert "ELSE IF NOT EXISTS (" in src
    assert "Usuario_AutorizacionesDetalle" in src
    assert "Resultado = ''PENDIENTE''" in src


def test_no_new_parallel_authorization_tables():
    src = source().upper()

    assert "CREATE TABLE" not in src
    assert "MONGODB" not in src


def test_resolver_semantic_modes_without_fragile_whitespace():
    src = source()

    marker = (
        "CREATE OR ALTER PROCEDURE "
        "dbo.sp_Usuario_ResolverAutorizacion"
    )

    assert marker in src

    resolver = src.split(marker, 1)[1]

    scalable_marker = (
        "IF @ModoAutorizacion = "
        "''ESCALABLE''"
    )

    joint_marker = "MANCOMUNADA:"
    rowcount_marker = "IF @@ROWCOUNT <> 1"

    assert scalable_marker in resolver
    assert joint_marker in resolver
    assert rowcount_marker in resolver

    scalable_pos = resolver.index(
        scalable_marker
    )

    joint_pos = resolver.index(
        joint_marker,
        scalable_pos,
    )

    rowcount_pos = resolver.index(
        rowcount_marker,
        joint_pos,
    )

    scalable = resolver[
        scalable_pos:joint_pos
    ]

    joint = resolver[
        joint_pos:rowcount_pos
    ]

    after_resolution = resolver[
        rowcount_pos:
    ]

    assert "MIN(NivelAutorizacion)" in scalable
    assert "@NivelPendiente" in scalable
    assert "NivelAutorizacion =" in scalable

    assert "UsuarioAutorizadorID" in joint
    assert "Resultado = ''PENDIENTE''" in joint

    assert "@NivelPendiente" not in joint
    assert "NivelAutorizacion =" not in joint

    assert (
        "IF @Resultado = ''RECHAZADA''"
        in after_resolution
    )

    assert "RECHAZADA" in after_resolution

    assert (
        "ELSE IF NOT EXISTS ("
        in after_resolution
    )

    assert "AUTORIZADA" in after_resolution
    assert "EN_PROCESO" in after_resolution
