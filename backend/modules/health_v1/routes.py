import time
import importlib
from typing import Dict, Any, List
from fastapi import APIRouter, Depends

from core.security import get_current_user
from core.sql_first.db import get_sql_connection
from modules.finanzas.health import REQUIRED_TABLES

router = APIRouter(prefix="/health/v1", tags=["Health V1"])


def _now_ms() -> int:
    return int(time.time() * 1000)


def _cursor(conn):
    try:
        return conn.cursor(as_dict=True)
    except TypeError:
        return conn.cursor()


def _rows(cur):
    data = cur.fetchall()
    if not data:
        return []
    if isinstance(data[0], dict):
        return data
    cols = [c[0] for c in cur.description] if cur.description else []
    return [dict(zip(cols, row)) for row in data]


def _one(cur):
    row = cur.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row
    cols = [c[0] for c in cur.description] if cur.description else []
    return dict(zip(cols, row))


def _check_sql_canonic() -> Dict[str, Any]:
    t0 = _now_ms()
    try:
        with get_sql_connection() as conn:
            cur = _cursor(conn)
            cur.execute("SELECT 1 AS ok")
            row = _one(cur)
        return {
            "status": "healthy" if row and row.get("ok") == 1 else "error",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
        }
    except Exception as e:
        return {
            "status": "error",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "error": str(e)[:200],
        }


def _check_tablero_comercial() -> Dict[str, Any]:
    t0 = _now_ms()
    result = {
        "status": "checking",
        "views": {},
        "latency_ms": None,
        "source": "EDARSAHUB_SQL",
    }
    try:
        with get_sql_connection() as conn:
            cur = _cursor(conn)

            expected = [
                "vw_Comercial_KPIs_Diarios_v2_Runtime",
                "vw_Comercial_KPIs_Mensuales_v2_Runtime",
            ]

            for view_name in expected:
                cur.execute("""
                    SELECT COUNT(*) AS total
                    FROM INFORMATION_SCHEMA.VIEWS
                    WHERE TABLE_NAME = %s
                """, (view_name,))
                row = _one(cur)
                exists = bool(row and row.get("total", 0) > 0)
                result["views"][view_name] = {"exists": exists}

                if exists:
                    # Salud estructural = vista CONSULTABLE sin error (independiente de
                    # que tenga filas; una vista vacía para el periodo no es "rota").
                    try:
                        cur.execute(f"SELECT TOP 1 1 AS ok FROM {view_name}")
                        cur.fetchone()
                        result["views"][view_name]["probe_ok"] = True
                    except Exception as pe:
                        result["views"][view_name]["probe_ok"] = False
                        result["views"][view_name]["probe_error"] = str(pe)[:120]
                else:
                    result["views"][view_name]["probe_ok"] = False

            all_ok = all(v["exists"] and v["probe_ok"] for v in result["views"].values())
            result["status"] = "healthy" if all_ok else "degraded"
            result["latency_ms"] = _now_ms() - t0
        return result
    except Exception as e:
        result["status"] = "error"
        result["latency_ms"] = _now_ms() - t0
        result["error"] = str(e)[:200]
        return result


def _check_users_roles() -> Dict[str, Any]:
    t0 = _now_ms()
    try:
        with get_sql_connection() as conn:
            cur = _cursor(conn)

            cur.execute("SELECT COUNT(*) AS total FROM Usuario_Catalogo")
            users = _one(cur)

            cur.execute("SELECT COUNT(*) AS total FROM Usuario_Roles")
            roles = _one(cur)

            cur.execute("SELECT COUNT(*) AS total FROM Usuario_RolesContexto")
            ctx = _one(cur)

        ok = all(x and int(x.get("total", 0)) >= 0 for x in [users, roles, ctx])

        return {
            "status": "healthy" if ok else "degraded",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "counts": {
                "usuarios": int((users or {}).get("total", 0)),
                "roles": int((roles or {}).get("total", 0)),
                "roles_contexto": int((ctx or {}).get("total", 0)),
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "error": str(e)[:200],
        }


def _check_config_operativa() -> Dict[str, Any]:
    t0 = _now_ms()
    try:
        with get_sql_connection() as conn:
            cur = _cursor(conn)
            cur.execute("SELECT COUNT(*) AS total FROM Sistema_TurnosOperativosUnidad")
            turnos = _one(cur)

        total = int((turnos or {}).get("total", 0))
        return {
            "status": "healthy" if total >= 0 else "degraded",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "counts": {"turnos_operativos_unidad": total},
        }
    except Exception as e:
        return {
            "status": "error",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "error": str(e)[:200],
        }


def _check_explorador_bd() -> Dict[str, Any]:
    t0 = _now_ms()
    try:
        mod = importlib.import_module("core.db")
        has_helper = hasattr(mod, "_execute_sql_direct_with_error")
        return {
            "status": "healthy" if has_helper else "degraded",
            "source": "local_code",
            "latency_ms": _now_ms() - t0,
            "helper__execute_sql_direct_with_error": has_helper,
            "note": "Explorador BD sigue siendo herramienta admin/live; aquí solo se valida integridad del helper local.",
        }
    except Exception as e:
        return {
            "status": "error",
            "source": "local_code",
            "latency_ms": _now_ms() - t0,
            "error": str(e)[:200],
        }


def _check_finanzas() -> Dict[str, Any]:
    t0 = _now_ms()
    try:
        required = sorted({t for group in REQUIRED_TABLES.values() for t in group})
        with get_sql_connection() as conn:
            cur = _cursor(conn)
            cur.execute("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME LIKE 'Finanzas%'
            """)
            rows = _rows(cur)

        existing = {r["TABLE_NAME"] for r in rows} if rows else set()
        missing = [t for t in required if t not in existing]

        return {
            "status": "healthy" if len(missing) == 0 else "degraded",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "required_tables": len(required),
            "missing_tables": missing,
            "external_live_is_diagnostic_only": True,
        }
    except Exception as e:
        return {
            "status": "error",
            "source": "EDARSAHUB_SQL",
            "latency_ms": _now_ms() - t0,
            "error": str(e)[:200],
        }


@router.get("")
async def get_health_v1(current_user: Dict = Depends(get_current_user)):
    started = _now_ms()

    checks = {
        "sql_canonic": _check_sql_canonic(),
        "tablero_comercial": _check_tablero_comercial(),
        "users_roles": _check_users_roles(),
        "config_operativa": _check_config_operativa(),
        "explorador_bd": _check_explorador_bd(),
        "finanzas": _check_finanzas(),
    }

    statuses = [v.get("status") for v in checks.values()]

    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "error" for s in statuses):
        overall = "error"
    else:
        overall = "degraded"

    return {
        "name": "EDARSAHUB_V1_HEALTH",
        "version_scope": "v1.0_estabilizada",
        "policy": {
            "sql_first": True,
            "no_mongo_required": True,
            "no_live_in_primary_health": True,
        },
        "overall_status": overall,
        "execution_time_ms": _now_ms() - started,
        "checks": checks,
    }
