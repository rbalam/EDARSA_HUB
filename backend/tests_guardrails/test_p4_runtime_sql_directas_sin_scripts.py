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

hits = []

for p in ROOT.rglob("*.py"):
    sp = str(p).replace("/app/backend/", "")

    if any(a in str(p) for a in ALLOW):
        continue

    txt = p.read_text(errors="ignore")

    if "pyodbc.connect" in txt or "pymssql.connect" in txt or "create_engine(" in txt:
        hits.append(sp)

if hits:
    print("FAIL runtime SQL directo:")
    for h in hits:
        print(h)
    sys.exit(1)

print("PASS runtime sin conexiones SQL directas")
