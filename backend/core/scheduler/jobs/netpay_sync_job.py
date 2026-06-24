"""
EDARSA HUB - NetPay Sync Scheduler Job

Ejecuta los dos reportes NetPay soportados por el robot:
- DETALLE_TRANSACCIONES
- DETALLE_DEPOSITOS_MOVIMIENTOS
"""
from __future__ import annotations

import asyncio
import os
import shlex
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


REPORT_TYPES = (
    "DETALLE_TRANSACCIONES",
    "DETALLE_DEPOSITOS_MOVIMIENTOS",
)


def _default_date_range() -> tuple[date, date]:
    # Diario automatico: reprocesa el dia anterior completo.
    yesterday = date.today() - timedelta(days=1)
    return yesterday, yesterday


def _validate_range(date_from: date, date_to: date, max_days: int = 31) -> None:
    if date_to < date_from:
        raise ValueError("date_to no puede ser menor que date_from")
    if date_to > date.today():
        raise ValueError("date_to no puede ser una fecha futura")
    days = (date_to - date_from).days + 1
    if days > max_days:
        raise ValueError(f"Rango NetPay excede maximo permitido de {max_days} dias: {days}")


def _read_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = raw_value.strip()
        if value and value[0] in {'"', "'"}:
            try:
                parsed = shlex.split(value, comments=False, posix=True)
                value = parsed[0] if parsed else ""
            except ValueError:
                value = value.strip("'\"")
        values[key] = value
    return values


def _build_robot_env(robot_root: Path) -> Dict[str, str]:
    env = os.environ.copy()

    backend_env = _read_env_file(Path("/app/backend/.env"))
    robot_env = _read_env_file(robot_root / ".env")

    for key, value in backend_env.items():
        if key.startswith("EDARSAHUB_SQL_") and value:
            env[key] = value

    for key, value in robot_env.items():
        if (key.startswith("NETPAY_") or key == "SERVER_SECRET_KEY") and value:
            env[key] = value

    env["PYTHONPATH"] = f"{robot_root / '.vendor'}:{robot_root}:{env.get('PYTHONPATH', '')}"
    return env


async def _run_cli(report_type: str, date_from: date, date_to: date) -> Dict[str, Any]:
    robot_root = Path("/app/netpay_robot_edarsahub/netpay_robot_edarsahub")
    if not robot_root.exists():
        raise RuntimeError(f"No existe robot_root NetPay: {robot_root}")

    env = _build_robot_env(robot_root)

    cmd = [
        sys.executable,
        "-m",
        "netpay_robot.cli",
        "run",
        "--report-type",
        report_type,
        "--date-from",
        date_from.isoformat(),
        "--date-to",
        date_to.isoformat(),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(robot_root),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_b, stderr_b = await proc.communicate()

    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")

    return {
        "report_type": report_type,
        "returncode": proc.returncode,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "ok": proc.returncode == 0,
        "success": proc.returncode == 0,
    }


async def execute_netpay_sync_diario(
    db=None,
    *,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    max_days: int = 31,
    report_types: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    if date_from is None or date_to is None:
        date_from, date_to = _default_date_range()

    _validate_range(date_from, date_to, max_days=max_days)

    selected_report_types = tuple(report_types or REPORT_TYPES)
    invalid_report_types = [r for r in selected_report_types if r not in REPORT_TYPES]
    if invalid_report_types:
        raise ValueError(f"Reportes NetPay invalidos: {invalid_report_types}")

    results = []
    for report_type in selected_report_types:
        results.append(await _run_cli(report_type, date_from, date_to))

    ok = all(r["ok"] for r in results)
    return {
        "ok": ok,
        "success": ok,
        "message": (
            f"NetPay sync completado para {date_from.isoformat()} a {date_to.isoformat()}"
            if ok
            else f"NetPay sync con errores para {date_from.isoformat()} a {date_to.isoformat()}"
        ),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "report_types": list(selected_report_types),
        "results": results,
        "reports": results,
    }
