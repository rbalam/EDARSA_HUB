from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Política EDARSAHUB:
Los dashboards y reportes ejecutivos no deben consultar SoftRestaurant, MPRO,
NetPay ni sistemas externos en tiempo real.

Solo se permite acceso live dentro de jobs de sincronización controlados.
"""

from pathlib import Path


FORBIDDEN_PATTERNS = [
    "pyodbc.connect(",
    "pymssql.connect(",
    "requests.get(",
    "requests.post(",
    "httpx.",
    "aiohttp.",
    "Servidores_Conexiones",
    "api_url",
    "database_name",
]

ALLOWED_PATH_PARTS = [
    "/scheduler/",
    "/jobs/",
    "/sync",
    "/sincronizacion",
    "/adapters.py",  # permitido solo si no se importa desde endpoints de dashboard
]


def is_allowed_live_path(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/").lower()
    return any(part.lower() in normalized for part in ALLOWED_PATH_PARTS)


def scan_file_for_live_access(file_path: Path) -> list[str]:
    if file_path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
        return []

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    violations = []

    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text and not is_allowed_live_path(str(file_path)):
            violations.append(pattern)

    return violations


def scan_project(root: str = "/app") -> list[dict]:
    root_path = Path(root)
    results = []

    for base in ["backend", "frontend"]:
        base_path = root_path / base
        if not base_path.exists():
            continue

        for file_path in base_path.rglob("*"):
            if any(skip in str(file_path) for skip in ["node_modules", ".git", "venv", "__pycache__"]):
                continue

            violations = scan_file_for_live_access(file_path)
            if violations:
                results.append({
                    "file": str(file_path),
                    "violations": violations,
                })

    return results


if __name__ == "__main__":
    findings = scan_project("/app")
    if findings:
        print("VIOLACIONES NO-LIVE DETECTADAS:")
        for item in findings:
            print(f"- {item['file']}: {', '.join(item['violations'])}")
        raise SystemExit(1)

    print("OK: No se detectaron violaciones live fuera de paths permitidos.")
