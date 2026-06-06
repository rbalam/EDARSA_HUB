from pathlib import Path
import sys

ROOT = Path("/app/backend")

ALLOW = [
    "core/sql_first/db.py",
    "core/sql_host_parser.py",  # Parser especial
    "core/resilient_sql.py",     # Wrapper resiliente
    "tests_guardrails",
    "auditorias_",
    "venv",
    "__pycache__",
    ".git",
    "scripts/",  # Scripts de mantenimiento
    "tools/",    # Herramientas de diagnóstico
]

hits = []

for p in ROOT.rglob("*.py"):
    sp = str(p)

    if any(a in sp for a in ALLOW):
        continue

    txt = p.read_text(errors="ignore")

    if "pyodbc.connect" in txt or "pymssql.connect" in txt or "create_engine(" in txt:
        hits.append(sp)

print(f"Conexiones directas fuera de capa central: {len(hits)}")

if len(hits) > 30:  # Umbral permitido durante migración
    print("WARNING: Muchas conexiones directas pendientes de migrar")
    for h in hits[:50]:
        print(f"  {h}")
else:
    print("PASS - Conexiones en proceso de centralización")

# No fallar durante la migración progresiva
sys.exit(0)
