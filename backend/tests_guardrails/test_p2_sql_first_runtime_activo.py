"""Guardrail P2: Verificar SQL-First en runtime activo"""
from pathlib import Path
import sys

ROOTS = [
    Path("/app/backend/modules/comercial_v2"),
    Path("/app/backend/modules/inteligencia_comercial"),
    Path("/app/backend/modules/dashboard"),
    Path("/app/backend/modules/admin_sql"),
]

# Solo verificar MongoClient directo (no stubs)
forbidden = ["from pymongo import MongoClient", "import pymongo"]

allow = ["no_mongo", "legacy", "backup", ".bak_", "deprecated", "__pycache__"]

hits = []

for root in ROOTS:
    if not root.exists():
        continue
    for p in root.rglob("*.py"):
        sp = str(p)
        if any(a in sp for a in allow):
            continue
        txt = p.read_text(errors="ignore")
        for term in forbidden:
            if term in txt:
                hits.append((sp, term))

if hits:
    print("FAIL - Mongo directo en runtime activo:")
    for f,t in hits:
        print(f"  {f}: {t}")
    sys.exit(1)

print("OK - SQL-First runtime activo sin Mongo directo")
