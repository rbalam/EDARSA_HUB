"""Pruebas GATE-SQL-GUARD-1: pymssql cursor(as_dict=True) fail-closed y guardrails SQL."""
from __future__ import annotations

import ast
import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ.setdefault("JWT_SECRET", "unit-test-only-signing-material-sql-guard-r1-0001")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "unit-test-only-placeholder")
os.environ.setdefault("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")

import pytest

from core import db as core_db
from core import refresh_tokens as rt
from core import security as sec


# Regex de proyeccion externa sin alias (equivalente al fallo real de pymssql as_dict=True)
_UNNAMED_OUTER_SELECT_RE = re.compile(
    r"(?i)(?<![(\w])SELECT\s+(?:DISTINCT\s+)?(?:TOP\s+\d+\s+)?"
    r"(1|0|COUNT\s*\([^)]*\)|SUM\s*\([^)]*\)|MAX\s*\([^)]*\)|MIN\s*\([^)]*\)|AVG\s*\([^)]*\)|"
    r"GETDATE\s*\(\)|GETUTCDATE\s*\(\)|SCOPE_IDENTITY\s*\(\)|@@\w+)"
    r"(?!\s+AS\b|\s+[A-Za-z_]\w*\s*(?:,|FROM\b|$))"
    r"\s*(?:,|FROM\b|$)"
)


class StrictPyMssqlAsDictError(RuntimeError):
    """Emula pymssql.ColumnsWithoutNamesError cuando as_dict=True recibe columna sin nombre."""


class StrictAsDictCursor:
    """Cursor simulado que replica el rechazo real de pymssql(as_dict=True) ante columnas sin alias."""

    def __init__(
        self,
        *,
        as_dict: bool,
        rows_by_query: Optional[List[Dict[str, Any]]] = None,
        error_to_raise: Optional[Exception] = None,
        seen_queries: Optional[List[str]] = None,
    ) -> None:
        self.as_dict = as_dict
        self._rows = rows_by_query if rows_by_query is not None else []
        self._error = error_to_raise
        self._seen = seen_queries if seen_queries is not None else []
        self.description = None

    def execute(self, query: str, params: Any = None) -> None:
        normalized = " ".join((query or "").split())
        self._seen.append(normalized)
        if self._error is not None:
            raise self._error

        upper = normalized.upper()
        if self.as_dict and _has_unnamed_outer_select(normalized):
            raise StrictPyMssqlAsDictError(
                "Specified as_dict=True and there are columns with no names: [0]"
            )

        if upper.startswith(("INSERT ", "UPDATE ", "DELETE ", "IF NOT EXISTS ")):
            self.description = None
            return

        if self._rows:
            self.description = [(k,) for k in self._rows[0].keys()]
        else:
            self.description = [("existe",)]

    def fetchall(self):
        if self.description is None:
            return []
        if self.as_dict:
            return [dict(r) for r in self._rows]
        return [tuple(r.values()) for r in self._rows]


class StrictAsDictConnection:
    def __init__(
        self,
        *,
        rows: Optional[List[Dict[str, Any]]] = None,
        error_to_raise: Optional[Exception] = None,
        seen_queries: Optional[List[str]] = None,
    ) -> None:
        self._rows = rows
        self._error = error_to_raise
        self._seen = seen_queries if seen_queries is not None else []
        self.closed = False

    def cursor(self, as_dict: bool = False):
        return StrictAsDictCursor(
            as_dict=as_dict,
            rows_by_query=self._rows,
            error_to_raise=self._error,
            seen_queries=self._seen,
        )

    def close(self) -> None:
        self.closed = True


def _has_unnamed_outer_select(sql: str) -> bool:
    for m in _UNNAMED_OUTER_SELECT_RE.finditer(sql):
        prefix = sql[max(0, m.start() - 40) : m.start()].upper()
        if re.search(r"EXISTS\s*\(\s*$", prefix):
            continue
        if re.search(r"\(\s*$", prefix):
            continue
        return True
    return False


def _patch_pool_and_fallback(
    monkeypatch,
    *,
    rows: Optional[List[Dict[str, Any]]] = None,
    error_to_raise: Optional[Exception] = None,
    seen_queries: Optional[List[str]] = None,
):
    """Parchea core.pool y get_external_sql_connection para pruebas deterministas sin red."""
    core_db.reset_server_cache()
    seen = seen_queries if seen_queries is not None else []

    class _FakePoolMgr:
        def get_pool_driver(self, *args, **kwargs):
            return "pymssql"

    @contextmanager
    def _fake_pooled(*args, **kwargs):
        conn = StrictAsDictConnection(rows=rows, error_to_raise=error_to_raise, seen_queries=seen)
        try:
            yield conn
        finally:
            conn.close()

    def _fake_external(config):
        return StrictAsDictConnection(rows=rows, error_to_raise=error_to_raise, seen_queries=seen)

    monkeypatch.setattr("core.pool.pooled_connection", _fake_pooled)
    monkeypatch.setattr("core.pool.get_pool_manager", lambda: _FakePoolMgr())
    monkeypatch.setattr(core_db, "get_external_sql_connection", _fake_external)
    return seen


# =============================================================================
# 1. core.db: execute_sql_query / execute_sql_query_params (positivo y negativo)
# =============================================================================


def test_execute_sql_query_strict_rejects_unnamed_select_and_accepts_alias(monkeypatch):
    _patch_pool_and_fallback(
        monkeypatch,
        rows=[{"existe": 1, "creado": datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)}],
    )

    # Negativo: SELECT 1 sin alias falla cerrado con raise_on_error=True
    with pytest.raises(StrictPyMssqlAsDictError):
        core_db.execute_sql_query(
            "127.0.0.1", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 FROM dbo.Tabla", raise_on_error=True
        )

    # Compatibilidad legacy: con raise_on_error=False sigue retornando []
    legacy = core_db.execute_sql_query(
        "127.0.0.1", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 FROM dbo.Tabla"
    )
    assert legacy == []

    # Positivo: SELECT 1 AS existe retorna filas normalizadas (datetime -> ISO)
    ok = core_db.execute_sql_query(
        "127.0.0.1", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 AS existe FROM dbo.Tabla", raise_on_error=True
    )
    assert len(ok) == 1
    assert ok[0]["existe"] == 1
    assert ok[0]["creado"].startswith("2026-11-20T12:00:00")


def test_execute_sql_query_params_distinguishes_empty_rows_from_errors_and_cooldown(monkeypatch):
    # 0 filas validas -> [] incluso con raise_on_error=True
    _patch_pool_and_fallback(monkeypatch, rows=[])
    empty = core_db.execute_sql_query_params(
        "127.0.0.1",
        1433,
        "EDARSAHUB",
        "user",
        "pwd",
        "SELECT COUNT(*) AS total FROM dbo.Tabla WHERE id = %s",
        (99,),
        raise_on_error=True,
    )
    assert empty == []

    # Error de conectividad -> propaga con raise_on_error=True y marca cooldown
    _patch_pool_and_fallback(monkeypatch, error_to_raise=RuntimeError("connection timed out"))
    with pytest.raises(RuntimeError, match="connection timed out"):
        core_db.execute_sql_query_params(
            "db-fail.local",
            1433,
            "EDARSAHUB",
            "user",
            "pwd",
            "SELECT 1 AS existe",
            (),
            raise_on_error=True,
        )
    assert core_db.is_server_offline_in_memory("db-fail.local") is True

    # Cooldown activo con raise_on_error=True -> ConnectionError (fail-closed)
    with pytest.raises(ConnectionError, match="cooldown"):
        core_db.execute_sql_query_params(
            "db-fail.local",
            1433,
            "EDARSAHUB",
            "user",
            "pwd",
            "SELECT 1 AS existe",
            (),
            raise_on_error=True,
        )
    # Cooldown activo en modo legacy -> []
    assert (
        core_db.execute_sql_query_params(
            "db-fail.local", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 AS existe", ()
        )
        == []
    )
    core_db.reset_server_cache()


# =============================================================================
# 2. core.db: sql_health_check, test_sql_connection, execute_query_safe,
#    _execute_sql_direct_with_error (eliminacion de rutas fail-open)
# =============================================================================


def test_sql_health_check_and_test_sql_connection_fail_closed_on_error_and_empty(monkeypatch):
    # Positivo: SELECT 1 AS health devuelve fila -> healthy=True
    _patch_pool_and_fallback(monkeypatch, rows=[{"health": 1}])
    ok = core_db.sql_health_check("127.0.0.1", 1433, "EDARSAHUB", "user", "pwd")
    assert ok["healthy"] is True
    assert ok["error"] is None
    assert core_db.test_sql_connection("127.0.0.1", 1433, "EDARSAHUB", "user", "pwd") is True

    # Negativo 1: Error de autenticacion -> healthy=False (antes devolvia True!)
    _patch_pool_and_fallback(monkeypatch, error_to_raise=RuntimeError("Login failed for user 'bad'"))
    auth_fail = core_db.sql_health_check("127.0.0.1", 1433, "EDARSAHUB", "bad", "pwd")
    assert auth_fail["healthy"] is False
    assert auth_fail["error_type"] == "authentication"
    assert "Login failed" in (auth_fail["error"] or "")
    assert core_db.test_sql_connection("127.0.0.1", 1433, "EDARSAHUB", "bad", "pwd") is False

    # Negativo 2: 0 filas en health check -> healthy=False (fail-closed)
    _patch_pool_and_fallback(monkeypatch, rows=[])
    empty_fail = core_db.sql_health_check("127.0.0.1", 1433, "EDARSAHUB", "user", "pwd")
    assert empty_fail["healthy"] is False
    assert empty_fail["error"] is not None


def test_execute_query_safe_distinguishes_no_data_from_sql_and_connectivity_errors(monkeypatch):
    cfg = {
        "host": "127.0.0.1",
        "port": 1433,
        "database": "EDARSAHUB",
        "username": "user",
        "password": "pwd",
        "system_type": "MPRO",
    }

    # Positivo con datos
    _patch_pool_and_fallback(monkeypatch, rows=[{"total": 5}])
    r_ok = core_db.execute_query_safe(cfg, "SELECT COUNT(*) AS total FROM Venta_Encabezado")
    assert r_ok.success is True
    assert r_ok.status == "SUCCESS"
    assert r_ok.rows_affected == 1

    # Positivo 0 filas reales -> NO_DATA
    _patch_pool_and_fallback(monkeypatch, rows=[])
    r_empty = core_db.execute_query_safe(cfg, "SELECT COUNT(*) AS total FROM Venta_Encabezado WHERE 1=0")
    assert r_empty.success is True
    assert r_empty.status == "NO_DATA"

    # Negativo: tabla inexistente -> SCHEMA_MISMATCH (antes devolvia NO_DATA con success=True!)
    _patch_pool_and_fallback(monkeypatch, error_to_raise=RuntimeError("Invalid object name 'NoExiste'"))
    r_schema = core_db.execute_query_safe(cfg, "SELECT 1 AS existe FROM NoExiste")
    assert r_schema.success is False
    assert r_schema.status == "SCHEMA_MISMATCH"
    assert r_schema.error_code == "INVALID_TABLE"

    # Negativo: timeout -> CONNECTION_ERROR
    _patch_pool_and_fallback(monkeypatch, error_to_raise=RuntimeError("Operation timeout expired"))
    r_to = core_db.execute_query_safe(cfg, "SELECT 1 AS existe")
    assert r_to.success is False
    assert r_to.status == "CONNECTION_ERROR"
    assert r_to.error_code == "TIMEOUT"

    # Negativo: columna sin alias en as_dict=True -> QUERY_ERROR (no NO_DATA!)
    _patch_pool_and_fallback(monkeypatch, rows=[{"x": 1}])
    r_unnamed = core_db.execute_query_safe(cfg, "SELECT 1 FROM Venta_Encabezado")
    assert r_unnamed.success is False
    assert r_unnamed.status == "QUERY_ERROR"


@pytest.mark.asyncio
async def test_execute_sql_direct_with_error_distinguishes_empty_from_errors(monkeypatch):
    # 0 filas validas -> ([], None)
    _patch_pool_and_fallback(monkeypatch, rows=[])
    rows, err = await core_db._execute_sql_direct_with_error(
        "127.0.0.1", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 AS existe WHERE 1=0"
    )
    assert rows == []
    assert err is None

    # Error de autenticacion -> ([], mensaje de autenticacion)
    _patch_pool_and_fallback(monkeypatch, error_to_raise=RuntimeError("Login failed for user"))
    rows_e, err_e = await core_db._execute_sql_direct_with_error(
        "127.0.0.1", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 AS existe"
    )
    assert rows_e == []
    assert err_e is not None and "autenticacion" in err_e.lower()

    # Error SQL / columna sin alias -> ([], Error SQL: ...)
    _patch_pool_and_fallback(monkeypatch, rows=[{"x": 1}])
    rows_u, err_u = await core_db._execute_sql_direct_with_error(
        "127.0.0.1", 1433, "EDARSAHUB", "user", "pwd", "SELECT 1 FROM dbo.Tabla"
    )
    assert rows_u == []
    assert err_u is not None and "error sql" in err_u.lower()


# =============================================================================
# 3. core.refresh_tokens: propagacion fail-closed real (sin silenciar errores SQL)
# =============================================================================


@pytest.mark.asyncio
async def test_refresh_tokens_execute_sql_async_propagates_real_sql_errors_and_normalizes_empty(monkeypatch):
    monkeypatch.setattr(
        rt,
        "_sql_config",
        {
            "host": "127.0.0.1",
            "port": 1433,
            "database": "EDARSAHUB",
            "username": "HRLectura",
            "password": "unit-test-only-placeholder",
        },
    )

    # 1. 0 filas -> fetch_one=True devuelve None (nunca []), fetch_all=True devuelve []
    _patch_pool_and_fallback(monkeypatch, rows=[])
    assert await rt._execute_sql_async("SELECT TOP 1 SesionID FROM Sesiones WHERE SesionID = %s", ("x",), fetch_one=True) is None
    assert await rt._execute_sql_async("SELECT SesionID FROM Sesiones WHERE SesionID = %s", ("x",), fetch_all=True) == []

    # 2. Fila valida -> tupla de valores y is_session_active True
    _patch_pool_and_fallback(monkeypatch, rows=[{"SesionID": "sid-ok-123"}])
    assert await rt.is_session_active("sid-ok-123", expected_user_type="interno") is True

    # 3. Fallo real SQL/conectividad -> _execute_sql_async DEBE lanzar (nunca devolver [] silencioso)
    _patch_pool_and_fallback(monkeypatch, error_to_raise=RuntimeError("connection refused by SQL Server"))
    with pytest.raises(RuntimeError, match="connection refused"):
        await rt._execute_sql_async("UPDATE Sesiones SET EstaActiva = 0 WHERE SesionID = %s", ("sid-ok-123",))

    # 4. verify_token_session_active ante fallo SQL -> fail-closed False (HTTP 401)
    assert await sec.verify_token_session_active({"sid": "sid-ok-123"}, expected_user_type="interno") is False


# =============================================================================
# 4. Modulos propietarios corregidos probados con cursor estricto as_dict=True
# =============================================================================


def test_pricing_sugerido_es_producto_vino_usa_alias_compatible_as_dict(monkeypatch):
    from modules.comercial.services import pricing_sugerido_service as ps

    monkeypatch.setattr(ps, "_get_conn", lambda: ("127.0.0.1", 1433, "EDARSAHUB", "user", "pwd"))

    seen_yes = _patch_pool_and_fallback(monkeypatch, rows=[{"existe": 1}])
    assert ps._es_producto_vino("VINO-001", "srv-1") is True
    assert any("SELECT 1 AS existe" in q for q in seen_yes)

    _patch_pool_and_fallback(monkeypatch, rows=[])
    assert ps._es_producto_vino("AGUA-001", "srv-1") is False


def test_sync_ventas_verificar_estado_sync_usa_alias_compatible_as_dict(monkeypatch):
    from modules.sync_historicos import sync_ventas

    seen = _patch_pool_and_fallback(monkeypatch, rows=[{"existe": 1, "total": 10}])
    estado = sync_ventas.verificar_estado_sync()
    assert len(estado["tablas_existentes"]) == 4
    assert estado["tablas_faltantes"] == []
    assert sum("SELECT 1 AS existe FROM INFORMATION_SCHEMA.TABLES" in q for q in seen) == 4


def test_sync_historicos_repository_create_tables_uses_aliased_verification(monkeypatch):
    from modules.sync_historicos.repository import SyncHistoricosRepository

    seen = _patch_pool_and_fallback(monkeypatch, rows=[{"existe": 1}])
    repo = SyncHistoricosRepository(
        {
            "host": "127.0.0.1",
            "port": 1433,
            "database": "EDARSAHUB",
            "username": "user",
            "password": "pwd",
        }
    )
    res = repo.create_tables_if_not_exist()
    assert res == {
        "Sync_Ventas_Historicas": True,
        "Sync_Ventas_PorHora": True,
        "Sync_Ventas_PorDiaSemana": True,
        "Sync_Control_Ejecuciones": True,
    }
    assert sum("SELECT 1 AS existe FROM INFORMATION_SCHEMA.TABLES" in q for q in seen) == 4


@pytest.mark.asyncio
async def test_catalogos_verificar_tablas_nuevas_uses_aliased_query(monkeypatch):
    from modules.catalogos import repository as cat_repo

    seen = _patch_pool_and_fallback(monkeypatch, rows=[{"existe": 1}])
    res = await cat_repo.verificar_tablas_nuevas(db=None)
    assert len(res) == 9
    assert all(res.values())
    assert sum("SELECT 1 AS existe FROM sys.tables" in q for q in seen) == 9


@pytest.mark.asyncio
async def test_comercial_repository_upserts_use_aliased_existence_checks(monkeypatch):
    from modules.comercial import repository as com_repo

    seen_checks: List[str] = []
    seen_writes: List[str] = []

    def _strict_single(query: str, params: tuple = None):
        norm = " ".join((query or "").split())
        seen_checks.append(norm)
        if _has_unnamed_outer_select(norm):
            raise StrictPyMssqlAsDictError("ColumnsWithoutNamesError")
        return {"existe": 1}

    def _fake_insert(query: str, params: tuple = None):
        seen_writes.append(" ".join((query or "").split()))
        return True

    monkeypatch.setattr(com_repo, "execute_hub_query_single", _strict_single)
    monkeypatch.setattr(com_repo, "execute_hub_insert", _fake_insert)

    await com_repo.save_metas_sucursal("srv-1", "Suc1", 11, 2026, {"meta_ventas": 100})
    await com_repo.save_kpis_cache("srv-1", "2026-11", {"ventas_total": 100})
    await com_repo.save_server_connection_status("srv-1", True, 25)
    await com_repo.save_dashboard_cache("srv-1", "2026-11", {"ok": True})

    assert len(seen_checks) == 4
    assert all("SELECT 1 AS existe FROM" in q for q in seen_checks)
    assert len(seen_writes) == 4
    assert all(q.startswith("UPDATE ") for q in seen_writes)


# =============================================================================
# 5. Guardrail estatico AST sobre backend/core y backend/modules
# =============================================================================


def _extract_string_literal(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                parts.append("{EXPR}")
        return "".join(parts)
    return None


def test_no_unnamed_outer_select_in_as_dict_backend_modules():
    """Impide regresiones de columnas sin alias en modulos que usan as_dict=True / execute_sql_query*."""
    backend_root = Path(__file__).resolve().parents[1]
    sql_dict_marker = re.compile(
        r"as_dict\s*=\s*True|execute_sql_query|execute_hub_query|execute_edarsa_query|execute_query_safe"
    )

    # Allowlist verificada exclusivamente para sitios que usan cursor de tuplas conn.cursor() (NO as_dict=True)
    # o strings de valor por defecto no ejecutados con as_dict=True.
    verified_tuple_cursor_allowlist = {
        ("core/inventarios/resolver_canonico.py", "COUNT(*)"),
        ("core/scheduler/jobs/inteligencia_comercial_sync_job.py", "COUNT(*)"),
        ("modules/cavas_corporativas/repository.py", "1"),
        ("modules/compras/sync_service.py", "COUNT(*)"),
        ("modules/consultas_sql/repository.py", "1"),
        ("modules/finanzas/repository_cortes_caja_edarsahub.py", "COUNT(*)"),
        ("modules/finanzas/sync_cortes_mpro.py", "@@IDENTITY"),
        ("modules/finanzas/sync_cortes_softrestaurant.py", "@@IDENTITY"),
        ("modules/finanzas/sync_propinas_mpro.py", "MAX(LOGID)"),
        ("modules/finanzas/sync_propinas_softrestaurant.py", "SCOPE_IDENTITY()"),
        ("modules/finanzas/sync_propinas_softrestaurant.py", "MAX(LOGID)"),
    }

    violations: List[str] = []
    for base in (backend_root / "core", backend_root / "modules"):
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            src = path.read_text(encoding="utf-8", errors="ignore")
            if not sql_dict_marker.search(src):
                continue
            tree = ast.parse(src, filename=str(path))
            rel = str(path.relative_to(backend_root))
            for node in ast.walk(tree):
                s = _extract_string_literal(node)
                if not s or "SELECT" not in s.upper():
                    continue
                for m in _UNNAMED_OUTER_SELECT_RE.finditer(s):
                    prefix = s[max(0, m.start() - 40) : m.start()].upper()
                    if re.search(r"EXISTS\s*\(\s*$", prefix):
                        continue
                    if re.search(r"\(\s*$", prefix):
                        continue
                    expr_key = re.sub(r"\s+", "", m.group(1).upper())
                    if (rel, expr_key) in verified_tuple_cursor_allowlist:
                        continue
                    snippet = " ".join(s[m.start() : min(len(s), m.end() + 70)].split())
                    violations.append(f"{rel}:{node.lineno} [{expr_key}] -> {snippet}")

    assert violations == [], "Proyecciones SQL sin alias incompatibles con pymssql as_dict=True:\n" + "\n".join(violations)
