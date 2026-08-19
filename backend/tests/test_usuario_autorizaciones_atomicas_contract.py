from pathlib import Path


ROOT = Path("/app")
MIGRATION = ROOT / (
    "backend/database/migrations/"
    "20260819_032_usuario_autorizaciones_atomicas.sql"
)


def _source() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_slice_one_only_replaces_the_two_authorization_procedures():
    source = _source()

    assert source.count("CREATE OR ALTER PROCEDURE") == 2
    assert "dbo.sp_Usuario_CrearAutorizacion" in source
    assert "dbo.sp_Usuario_ResolverAutorizacion" in source
    assert "CREATE TABLE" not in source
    assert "ALTER TABLE" not in source
    assert "GRANT " not in source


def test_create_fails_closed_before_mutation_and_is_atomic():
    source = _source()
    create = source.split(
        "CREATE OR ALTER PROCEDURE dbo.sp_Usuario_ResolverAutorizacion",
        maxsplit=1,
    )[0]

    assert "SET XACT_ABORT ON;" in create
    assert "THROW 51032, 'Usuario solicitante requerido.', 1;" in create
    assert "THROW 51033, 'Usuario solicitante inexistente o inactivo.', 1;" in create
    assert "THROW 51035, 'No existe matriz de autorizacion aplicable.', 1;" in create
    assert "THROW 51036, 'La matriz aplicable no tiene autorizadores activos.', 1;" in create
    assert (
        "THROW 51037, 'La matriz aplicable contiene autorizadores inexistentes o inactivos.', 1;"
        in create
    )
    assert "@AutorizacionID BIGINT OUTPUT" in create
    assert "SELECT TOP 1 URA.UsuarioID" in create
    assert "SET @UsuarioSolicitanteID = 1" not in create
    assert create.index("BEGIN TRANSACTION;") < create.index(
        "INSERT INTO dbo.Usuario_Autorizaciones"
    )
    assert "IF @@TRANCOUNT > 0" in create
    assert "ROLLBACK TRANSACTION;" in create
    assert "EXEC dbo.sp_Usuario_LogActividad" in create


def test_resolve_closes_result_and_concurrency_gaps():
    source = _source()
    resolve = source.split(
        "CREATE OR ALTER PROCEDURE dbo.sp_Usuario_ResolverAutorizacion",
        maxsplit=1,
    )[1]

    assert "SET XACT_ABORT ON;" in resolve
    assert "@Resultado NOT IN ('AUTORIZADA', 'RECHAZADA')" in resolve
    assert "OMITIDA" not in resolve
    assert "Usuario autorizador requerido." in resolve
    assert "Usuario autorizador inexistente o inactivo." in resolve
    assert "SET @UsuarioAutorizadorID = 1" not in resolve
    assert "WITH (UPDLOCK, HOLDLOCK)" in resolve
    assert "SELECT @NivelPendiente = MIN(NivelAutorizacion)" in resolve
    assert "IF @@ROWCOUNT <> 1" in resolve
    assert "THROW 51044, 'No hay autorizacion pendiente para este usuario.', 1;" in resolve
    assert "BEGIN TRANSACTION;" in resolve
    assert "ROLLBACK TRANSACTION;" in resolve
    assert "EstatusAutorizacion = 'RECHAZADA'" in resolve
    assert "EstatusAutorizacion = 'AUTORIZADA'" in resolve
    assert "EstatusAutorizacion = 'EN_PROCESO'" in resolve
    assert "EXEC dbo.sp_Usuario_LogActividad" in resolve
