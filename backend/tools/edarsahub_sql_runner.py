"""
EDARSAHUB SQL Runner (pymssql version)
Herramienta controlada para ejecutar diagnósticos, migraciones y validaciones SQL Server.

Uso recomendado:
    python backend/tools/edarsahub_sql_runner.py --mode diagnostic --script backend/database/diagnostics/001_diagnostico.sql
    python backend/tools/edarsahub_sql_runner.py --mode dry-run --script backend/database/migrations/001_migracion.sql
    python backend/tools/edarsahub_sql_runner.py --mode migrate --script backend/database/migrations/001_migracion.sql
    python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/001_validacion.sql

Variables de entorno requeridas:
    EDARSAHUB_SQL_SERVER
    EDARSAHUB_SQL_DATABASE
    EDARSAHUB_SQL_USER
    EDARSAHUB_SQL_PASSWORD
    EDARSAHUB_SQL_TIMEOUT_SECONDS=60          # Opcional
    EDARSAHUB_SQL_LOGIN_TIMEOUT_SECONDS=15    # Opcional
    EDARSAHUB_ALLOW_MIGRATIONS=true   # Solo para modo migrate
"""

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

import pymssql
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()



ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "docs" / "reports" / "sql_runner_logs"

ALLOWED_MODES = {"diagnostic", "dry-run", "migrate", "validate"}

FORBIDDEN_PATTERNS = [
    r"\bDROP\s+TABLE\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bDROP\s+DATABASE\b",
    r"\bALTER\s+DATABASE\b",
    r"\bEXEC\s+xp_cmdshell\b",
    r"\bsp_configure\b",
]

DANGEROUS_DELETE_PATTERN = r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)"


def get_env(name: str, required: bool = True, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Falta variable de entorno requerida: {name}")
    return value


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Variable de entorno invalida para entero: {name}") from exc


def get_connection():
    """Crea conexión pymssql a EDARSAHUB."""
    server = get_env("EDARSAHUB_SQL_SERVER")
    database = get_env("EDARSAHUB_SQL_DATABASE")
    user = get_env("EDARSAHUB_SQL_USER")
    password = get_env("EDARSAHUB_SQL_PASSWORD")
    port = int(get_env("EDARSAHUB_SQL_PORT", required=False, default="1433"))
    timeout = get_int_env("EDARSAHUB_SQL_TIMEOUT_SECONDS", 60)
    login_timeout = get_int_env("EDARSAHUB_SQL_LOGIN_TIMEOUT_SECONDS", 15)
    
    return pymssql.connect(
        server=server,
        port=port,
        user=user,
        password=password,
        database=database,
        timeout=timeout,
        login_timeout=login_timeout,
        autocommit=False
    )


def read_sql_file(script_path: Path) -> str:
    if script_path.suffix.lower() != ".sql":
        raise RuntimeError("Solo se permiten archivos .sql")

    if not script_path.exists():
        raise RuntimeError(f"No existe el script: {script_path}")

    return script_path.read_text(encoding="utf-8")


def validate_sql_safety(sql: str, mode: str) -> None:
    sql_upper = sql.upper()

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            raise RuntimeError(f"SQL bloqueado por patrón peligroso: {pattern}")

    if re.search(DANGEROUS_DELETE_PATTERN, sql_upper, re.IGNORECASE):
        raise RuntimeError("SQL bloqueado: DELETE sin WHERE.")

    if mode in {"diagnostic", "validate"}:
        blocked = [
            r"\bCREATE\s+TABLE\b",
            r"\bALTER\s+TABLE\b",
            r"\bDROP\b",
            r"\bINSERT\s+INTO\b",
            r"\bUPDATE\b",
            r"\bDELETE\s+FROM\b",
            r"\bMERGE\b",
        ]
        for pattern in blocked:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                raise RuntimeError(
                    f"El modo {mode} no permite cambios de estructura o datos. Patrón detectado: {pattern}"
                )

    if mode == "migrate":
        allow = os.getenv("EDARSAHUB_ALLOW_MIGRATIONS", "").lower()
        if allow != "true":
            raise RuntimeError(
                "Migración bloqueada. Define EDARSAHUB_ALLOW_MIGRATIONS=true para permitir ejecución."
            )


def split_sql_batches(sql: str) -> list[str]:
    """
    Divide scripts SQL Server por GO en línea independiente.
    """
    batches = re.split(r"^\s*GO\s*$", sql, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]


def execute_sql(sql: str, mode: str) -> dict:
    if mode == "dry-run":
        return {
            "success": True,
            "mode": mode,
            "message": "Dry-run ejecutado. No se aplicaron cambios.",
            "batches": len(split_sql_batches(sql)),
            "results": [],
        }

    batches = split_sql_batches(sql)
    results = []

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        for index, batch in enumerate(batches, start=1):
            cursor.execute(batch)

            if cursor.description:
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                results.append(
                    {
                        "batch": index,
                        "type": "resultset",
                        "columns": columns,
                        "row_count": len(rows),
                        "rows_preview": rows[:20],
                    }
                )
            else:
                results.append(
                    {
                        "batch": index,
                        "type": "command",
                        "rowcount": cursor.rowcount,
                    }
                )

        if mode == "migrate":
            conn.commit()
        else:
            conn.rollback()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "mode": mode,
            "message": "Ejecución completada.",
            "batches": len(batches),
            "results": results,
        }

    except Exception as exc:
        conn.rollback()
        cursor.close()
        conn.close()
        raise RuntimeError(f"Error ejecutando SQL. Se hizo rollback. Detalle: {exc}") from exc


def write_report(script_path: Path, mode: str, sql: str, result: dict | None, error: str | None) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"{timestamp}_{mode}_{script_path.stem}.md"

    server = os.getenv("EDARSAHUB_SQL_SERVER", "NO_DEFINIDO")
    database = _edarsa_cfg.database

    content = []
    content.append(f"# EDARSAHUB SQL Runner Report\n")
    content.append(f"- Fecha: {dt.datetime.now().isoformat()}")
    content.append(f"- Modo: `{mode}`")
    content.append(f"- Servidor: `{server}`")
    content.append(f"- Base de datos: `{database}`")
    content.append(f"- Script: `{script_path}`")
    content.append("")

    if error:
        content.append("## Resultado")
        content.append("ERROR")
        content.append("")
        content.append("## Detalle")
        content.append(f"```text\n{error}\n```")
    else:
        content.append("## Resultado")
        content.append("OK")
        content.append("")
        content.append("## Resumen")
        if result:
            content.append(f"- Batches ejecutados: {result.get('batches', 0)}")
            content.append(f"- Mensaje: {result.get('message', '')}")
            content.append("")
            
            for r in result.get("results", []):
                content.append(f"### Batch {r.get('batch')}")
                if r.get("type") == "resultset":
                    content.append(f"- Tipo: SELECT")
                    content.append(f"- Columnas: {', '.join(r.get('columns', []))}")
                    content.append(f"- Filas: {r.get('row_count', 0)}")
                    if r.get("rows_preview"):
                        content.append("- Preview (primeras 20 filas):")
                        content.append("```")
                        for row in r.get("rows_preview", [])[:10]:
                            content.append(f"  {row}")
                        content.append("```")
                else:
                    content.append(f"- Tipo: Comando")
                    content.append(f"- Filas afectadas: {r.get('rowcount', 0)}")
                content.append("")

    content.append("")
    content.append("## SQL ejecutado / revisado")
    content.append("```sql")
    content.append(sql[:20000])
    content.append("```")

    report_path.write_text("\n".join(content), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="EDARSAHUB SQL Runner (pymssql)")
    parser.add_argument("--mode", required=True, choices=sorted(ALLOWED_MODES))
    parser.add_argument("--script", required=True)

    args = parser.parse_args()

    mode = args.mode
    script_path = Path(args.script).resolve()

    result = None
    error = None
    sql = ""

    try:
        sql = read_sql_file(script_path)
        validate_sql_safety(sql, mode)
        result = execute_sql(sql, mode)

    except Exception as exc:
        error = str(exc)

    report_path = write_report(script_path, mode, sql, result, error)

    if error:
        print(f"ERROR: {error}")
        print(f"Reporte generado: {report_path}")
        return 1

    print("Ejecución completada correctamente.")
    print(f"Reporte generado: {report_path}")
    
    # Imprimir resumen de resultados
    if result:
        for r in result.get("results", []):
            if r.get("type") == "resultset":
                print(f"  Batch {r.get('batch')}: {r.get('row_count')} filas")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
