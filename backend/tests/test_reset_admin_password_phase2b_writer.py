import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.connections.edarsahub_writer_connection as writer_module
import tools.reset_admin_password_phase2b as reset_tool
from core.config.edarsahub_config import (
    EdarsaHubSQLConfig,
    get_edarsahub_sql_config,
)
from core.connections.edarsahub_writer_connection import (
    SQLWriterIdentity,
    validate_writer_identity,
)
from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
)
from tools.reset_admin_password_phase2b import (
    confirm_target,
    update_password_and_audit,
)


class IdentityCursor:
    def __init__(self, row):
        self.row = row

    def execute(self, _sql):
        return None

    def fetchone(self):
        return self.row

    def close(self):
        return None


class IdentityConnection:
    def __init__(self, row):
        self.row = row
        self.close_calls = 0

    def cursor(self):
        return IdentityCursor(self.row)

    def close(self):
        self.close_calls += 1


class RecordingCursor:
    def __init__(self):
        self.calls = []
        self.rowcount = 1

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def close(self):
        return None


class RecordingConnection:
    def __init__(self):
        self.recording_cursor = RecordingCursor()

    def cursor(self):
        return self.recording_cursor


def canonical_config(
    user="HRLectura",
    database="EDARSAHUB",
):
    return EdarsaHubSQLConfig(
        host="sql.internal",
        port=1433,
        database=database,
        user=user,
        password="test-secret",
        profile="default",
    )


def canonical_identity():
    return SQLWriterIdentity(
        database_name="EDARSAHUB",
        login_name="HRLectura",
        user_name="HRLectura",
    )


def test_writer_identity_accepts_canonical_contract():
    conn = IdentityConnection(
        (
            "EDARSAHUB",
            "HRLectura",
            "HRLectura",
        )
    )

    identity = validate_writer_identity(
        conn,
        config=canonical_config(),
    )

    assert identity.database_name == "EDARSAHUB"
    assert identity.login_name == "HRLectura"
    assert identity.user_name == "HRLectura"


def test_writer_config_rejects_noncanonical_login():
    conn = IdentityConnection(
        (
            "EDARSAHUB",
            "OtherLogin",
            "OtherLogin",
        )
    )

    with pytest.raises(
        RuntimeError,
        match="login canonico",
    ):
        validate_writer_identity(
            conn,
            config=canonical_config(
                user="OtherLogin"
            ),
        )


def test_writer_identity_rejects_runtime_mismatch():
    conn = IdentityConnection(
        (
            "EDARSAHUB",
            "UnexpectedLogin",
            "HRLectura",
        )
    )

    with pytest.raises(
        RuntimeError,
        match="login_name",
    ):
        validate_writer_identity(
            conn,
            config=canonical_config(),
        )


def test_target_confirmation_is_exact(monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: "user@example.com",
    )

    confirm_target(
        "user@example.com",
        42,
    )


def test_target_confirmation_rejects_mismatch(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: "other@example.com",
    )

    with pytest.raises(
        RuntimeError,
        match="incorrecta",
    ):
        confirm_target(
            "user@example.com",
            42,
        )


def test_update_and_audit_share_one_connection():
    conn = RecordingConnection()

    update_password_and_audit(
        conn,
        usuario_id=42,
        email="user@example.com",
        password_hash="$2b$12$not-a-real-hash",
        identity=canonical_identity(),
    )

    calls = conn.recording_cursor.calls

    assert len(calls) == 2
    assert (
        "UPDATE dbo.Usuario_Catalogo"
        in calls[0][0]
    )
    assert (
        "INSERT INTO dbo.Usuario_LogRecuperacion"
        in calls[1][0]
    )


def test_update_rejects_zero_rows():
    conn = RecordingConnection()
    conn.recording_cursor.rowcount = 0

    with pytest.raises(
        RuntimeError,
        match="exactamente un usuario activo",
    ):
        update_password_and_audit(
            conn,
            usuario_id=42,
            email="user@example.com",
            password_hash=(
                "$2b$12$not-a-real-hash"
            ),
            identity=canonical_identity(),
        )

    assert len(
        conn.recording_cursor.calls
    ) == 1


def test_config_uses_only_canonical_prefix(
    monkeypatch,
):
    values = {
        "EDARSAHUB_SQL_HOST": "canonical-host",
        "EDARSAHUB_SQL_PORT": "1444",
        "EDARSAHUB_SQL_DATABASE": "EDARSAHUB",
        "EDARSAHUB_SQL_USER": "HRLectura",
        "EDARSAHUB_SQL_PASSWORD": (
            "test-only-password"
        ),
    }

    for name, value in values.items():
        monkeypatch.setenv(name, value)

    cfg = get_edarsahub_sql_config("default")

    assert cfg.profile == "default"
    assert cfg.host == "canonical-host"
    assert cfg.port == 1444
    assert cfg.database == "EDARSAHUB"
    assert cfg.user == "HRLectura"
    assert cfg.password == "test-only-password"

    with pytest.raises(
        ValueError,
        match="no soportado",
    ):
        get_edarsahub_sql_config("writer")


def test_pymssql_profile_is_keyword_only():
    parameter = inspect.signature(
        get_edarsahub_pymssql_connection
    ).parameters["profile"]

    assert (
        parameter.kind
        is inspect.Parameter.KEYWORD_ONLY
    )


def test_open_writer_uses_canonical_default_profile(
    monkeypatch,
):
    calls = []
    conn = IdentityConnection(
        (
            "EDARSAHUB",
            "HRLectura",
            "HRLectura",
        )
    )

    def fake_config(profile):
        calls.append(("config", profile))
        return canonical_config()

    def fake_connection(*, profile):
        calls.append(("connect", profile))
        return conn

    monkeypatch.setattr(
        writer_module,
        "get_edarsahub_sql_config",
        fake_config,
    )
    monkeypatch.setattr(
        writer_module,
        "get_edarsahub_pymssql_connection",
        fake_connection,
    )

    opened, identity = (
        writer_module.open_validated_writer_connection()
    )

    assert opened is conn
    assert identity.login_name == "HRLectura"
    assert calls == [
        ("config", "default"),
        ("connect", "default"),
    ]


def test_noncanonical_config_rejected_before_open(
    monkeypatch,
):
    opened = []

    monkeypatch.setattr(
        writer_module,
        "get_edarsahub_sql_config",
        lambda profile: canonical_config(
            user="OtherLogin"
        ),
    )
    monkeypatch.setattr(
        writer_module,
        "get_edarsahub_pymssql_connection",
        lambda **kwargs: opened.append(kwargs),
    )

    with pytest.raises(
        RuntimeError,
        match="login canonico",
    ):
        writer_module.open_validated_writer_connection()

    assert opened == []


class TransactionConnection:
    def __init__(self):
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.close_calls += 1


def _main_args(
    skip_validation=True,
):
    return SimpleNamespace(
        email="user@example.com",
        base_url="http://localhost.invalid",
        i_understand_this_updates_sql=True,
        skip_validation=skip_validation,
    )


def _configure_main_happy_path(
    monkeypatch,
    conn,
    *,
    skip_validation=True,
):
    monkeypatch.setattr(
        reset_tool,
        "parse_args",
        lambda: _main_args(
            skip_validation=skip_validation,
        ),
    )

    monkeypatch.setattr(
        reset_tool,
        "open_validated_writer_connection",
        lambda: (
            conn,
            canonical_identity(),
        ),
    )

    monkeypatch.setattr(
        reset_tool,
        "resolve_single_active_user",
        lambda active_conn, email: (
            42,
            [
                {
                    "UsuarioID": 42,
                    "Email": email,
                }
            ],
        ),
    )

    monkeypatch.setattr(
        reset_tool,
        "confirm_target",
        lambda email, usuario_id: None,
    )

    monkeypatch.setattr(
        reset_tool,
        "prompt_new_password",
        lambda email: "TestPassword123",
    )

    monkeypatch.setattr(
        reset_tool,
        "hash_password",
        lambda password: "test-hash",
    )

    monkeypatch.setattr(
        reset_tool,
        "update_password_and_audit",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        reset_tool,
        "fetch_user_metadata",
        lambda active_conn, email: [
            {
                "UsuarioID": 42,
                "Email": email,
            }
        ],
    )

    monkeypatch.setattr(
        reset_tool,
        "write_reset_report",
        lambda *args, **kwargs: Path(
            "/tmp/test-reset-report.md"
        ),
    )


def test_main_commits_writer_transaction_once(
    monkeypatch,
):
    conn = TransactionConnection()
    calls = []

    _configure_main_happy_path(
        monkeypatch,
        conn,
    )

    monkeypatch.setattr(
        reset_tool,
        "update_password_and_audit",
        lambda active_conn,
        usuario_id,
        email,
        password_hash,
        identity: calls.append(
            (
                active_conn,
                usuario_id,
                email,
                password_hash,
                identity,
            )
        ),
    )

    result = reset_tool.main()

    assert result == 0
    assert len(calls) == 1
    assert calls[0][0] is conn
    assert conn.commit_calls == 1
    assert conn.rollback_calls == 0
    assert conn.close_calls == 1


def test_main_rolls_back_when_update_or_audit_fails(
    monkeypatch,
):
    conn = TransactionConnection()

    _configure_main_happy_path(
        monkeypatch,
        conn,
    )

    def fail_update(*args, **kwargs):
        raise RuntimeError(
            "simulated transactional failure"
        )

    monkeypatch.setattr(
        reset_tool,
        "update_password_and_audit",
        fail_update,
    )

    result = reset_tool.main()

    assert result == 1
    assert conn.commit_calls == 0
    assert conn.rollback_calls == 1
    assert conn.close_calls == 1


def test_operational_report_dirs_are_outside_repository():
    expected = Path(
        "/tmp/edarsahub/rbac_phase1"
    )

    assert reset_tool.REPORT_DIR == expected
    assert (
        reset_tool.rbac_validator.REPORT_DIR
        == expected
    )
    assert (
        "docs/reports"
        not in str(reset_tool.REPORT_DIR)
    )


def test_reset_report_records_separate_statuses(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        reset_tool,
        "REPORT_DIR",
        tmp_path,
    )

    report_path = reset_tool.write_reset_report(
        email="user@example.com",
        before_rows=[],
        after_rows=[],
        validation_md=None,
        validation_summary=None,
        rotation_sql_status="COMMITTED",
        post_validation_status="WARN_OR_FAIL",
    )

    report = report_path.read_text(
        encoding="utf-8"
    )

    assert (
        "ROTATION_SQL_STATUS=COMMITTED"
        in report
    )
    assert (
        "POST_VALIDATION_STATUS=WARN_OR_FAIL"
        in report
    )
    assert "REPORT_STATUS=PASS" in report


def test_rotation_validation_does_not_force_global_access(
    monkeypatch,
):
    captured = {}

    def fake_validate_user(
        spec,
        base_url,
        timeout,
    ):
        captured["spec"] = spec
        captured["base_url"] = base_url
        captured["timeout"] = timeout

        return {
            "status": "OK",
        }

    monkeypatch.setattr(
        reset_tool.rbac_validator,
        "validate_user",
        fake_validate_user,
    )

    monkeypatch.setattr(
        reset_tool.rbac_validator,
        "write_reports",
        lambda *args, **kwargs: (
            Path("/tmp/test-rbac.json"),
            Path("/tmp/test-rbac.md"),
        ),
    )

    _, summary = reset_tool.run_rbac_validation(
        "user@example.com",
        "TestPassword123",
        "http://localhost.invalid",
    )

    assert (
        "expect_global_access"
        not in captured["spec"]
    )
    assert (
        captured["spec"]["expected_min_permissions"]
        == 1
    )
    assert summary["ok"] == 1


def test_commit_remains_explicit_when_validation_fails(
    monkeypatch,
    capsys,
):
    conn = TransactionConnection()

    _configure_main_happy_path(
        monkeypatch,
        conn,
        skip_validation=False,
    )

    def fail_validation(*args, **kwargs):
        raise RuntimeError(
            "simulated validation failure"
        )

    monkeypatch.setattr(
        reset_tool,
        "run_rbac_validation",
        fail_validation,
    )

    result = reset_tool.main()
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert result == 1
    assert conn.commit_calls == 1
    assert conn.rollback_calls == 0
    assert conn.close_calls == 1

    assert (
        "ROTATION_SQL_STATUS=COMMITTED"
        in output
    )
    assert (
        "POST_VALIDATION_STATUS=ERROR"
        in output
    )
    assert "REPORT_STATUS=PASS" in output


def test_commit_remains_explicit_when_report_fails(
    monkeypatch,
    capsys,
):
    conn = TransactionConnection()

    _configure_main_happy_path(
        monkeypatch,
        conn,
        skip_validation=True,
    )

    def fail_report(*args, **kwargs):
        raise RuntimeError(
            "simulated report failure"
        )

    monkeypatch.setattr(
        reset_tool,
        "write_reset_report",
        fail_report,
    )

    result = reset_tool.main()
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert result == 1
    assert conn.commit_calls == 1
    assert conn.rollback_calls == 0
    assert conn.close_calls == 1

    assert (
        "ROTATION_SQL_STATUS=COMMITTED"
        in output
    )
    assert (
        "POST_VALIDATION_STATUS=SKIPPED"
        in output
    )
    assert "REPORT_STATUS=ERROR" in output


def test_main_clears_sensitive_local_values():
    source = inspect.getsource(
        reset_tool.main
    )

    final_cleanup = source[
        source.rfind("finally:"):
    ]

    assert 'password = ""' in final_cleanup
    assert 'new_hash = ""' in final_cleanup
