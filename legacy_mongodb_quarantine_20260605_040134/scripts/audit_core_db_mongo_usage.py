from pathlib import Path
import re
from datetime import datetime

ROOT = Path("/app")
TARGET = ROOT / "backend/core/db.py"
OUT = ROOT / "docs/auditorias/AUDITORIA_CORE_DB_MONGO_USAGE_20260604.md"

txt = TARGET.read_text(errors="ignore")
lines = txt.splitlines()

# Buscar definiciones de funciones/clases
defs = []
current = None
for i, line in enumerate(lines, start=1):
    m = re.match(r"^(class|def|async def)\s+([A-Za-z0-9_]+)", line)
    if m:
        current = m.group(2)
        defs.append((i, current))

# Solo buscar símbolos relacionados con mongo
mongo_symbols = []
for i, name in defs:
    if re.search(r"mongo|db|client|database", name, re.I):
        mongo_symbols.append((i, name))

md = []
md.append("# AUDITORÍA P0 — core/db.py Mongo Usage\n\n")
md.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

md.append("## Referencias Mongo directas en core/db.py\n\n")
mongo_refs = []
for i, line in enumerate(lines, start=1):
    if re.search(r"pymongo|motor|MongoClient|AsyncIOMotorClient|_mongo_client|_sync_mongo", line):
        mongo_refs.append((i, line.strip()))
        md.append(f"- L{i}: `{line.strip()[:100]}`\n")

md.append(f"\nTotal referencias: {len(mongo_refs)}\n")

md.append("\n## Funciones Mongo definidas\n\n")
for i, name in mongo_symbols:
    md.append(f"- L{i}: `{name}`\n")

md.append("\n## Uso externo de funciones Mongo\n\n")
risk_count = 0

for i, sym in mongo_symbols[:15]:  # Limitar para no timeout
    uses = []
    for p in (ROOT / "backend").rglob("*.py"):
        if p == TARGET or ".bak" in str(p) or "__pycache__" in str(p):
            continue
        try:
            t = p.read_text(errors="ignore")
        except:
            continue
        if re.search(rf"\b{re.escape(sym)}\b", t):
            for j, line in enumerate(t.splitlines(), start=1):
                if re.search(rf"\b{re.escape(sym)}\b", line):
                    uses.append((p.relative_to(ROOT), j, line.strip()))
                    if len(uses) >= 20:
                        break
        if len(uses) >= 20:
            break

    if uses:
        md.append(f"### `{sym}` (L{i})\n\n")
        for file, line, code in uses[:15]:
            route_risk = "ALTO" if re.search(r"routes|@router|Depends|server\.py", str(file), re.I) else "MEDIO"
            if route_risk == "ALTO":
                risk_count += 1
            code = code.replace("|", "\\|")[:80]
            md.append(f"- [{route_risk}] `{file}` L{line}: `{code}`\n")
        md.append("\n")

md.append("## Dictamen inicial\n\n")
md.append(f"- Riesgos altos por uso en rutas/server: **{risk_count}**\n")
md.append("- `core/db.py` contiene conexiones tanto SQL como MongoDB.\n")
md.append("- Las funciones `get_mongo_*` deben ser deprecadas progresivamente.\n")
md.append("- Cualquier endpoint visual que use MongoDB debe migrarse a SQL-first.\n")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("".join(md), encoding="utf-8")

print(f"Reporte generado: {OUT}")
print(f"Símbolos Mongo: {len(mongo_symbols)}")
print(f"Riesgos altos: {risk_count}")
