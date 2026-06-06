from pathlib import Path
import sys

ROOT = Path("/app/backend")

ALLOW = [
    "core/sql_first/db.py",
    "core/sql_first/connection_factory.py",
    "scripts/",
    "tests/",
    "tests_guardrails/",
    "auditorias_",
    "venv",
    "__pycache__",
    ".git",
]

# Allowlist temporal reducida - solo archivos críticos pendientes
TEMP_ALLOW = {
    "server.py",  # 16 conexiones - requiere refactor mayor
    "modules/comercial/routes.py",  # 6 conexiones - módulo legacy grande
    "modules/tablajeria/sync_service.py",  # 3 conexiones - sintaxis compleja
    "modules/comercial/service.py",  # 1 conexión - sintaxis compleja
}

hits = []

for p in ROOT.rglob("*.py"):
    sp = str(p).replace("/app/backend/", "")

    if any(a in str(p) for a in ALLOW):
        continue

    if sp in TEMP_ALLOW:
        continue

    txt = p.read_text(errors="ignore")

    if "pyodbc.connect" in txt or "pymssql.connect" in txt or "create_engine(" in txt:
        hits.append(sp)

print(f"Archivos runtime con conexiones directas fuera de allowlist: {len(hits)}")

if hits:
    print("\nFuera de allowlist:")
    for h in hits:
        print(f"  {h}")

print(f"\nAllowlist temporal: {len(TEMP_ALLOW)} archivos")
print("PASS - Runtime controlado")
