from pathlib import Path
import re
from datetime import datetime

ROOT = Path("/app")
TARGET = ROOT / "backend/core/connection_resolver.py"
OUT = ROOT / "docs/auditorias/AUDITORIA_CONNECTION_RESOLVER_SQL_FIRST_20260604.md"

txt = TARGET.read_text(errors="ignore")
lines = txt.splitlines()

md = []
md.append("# AUDITORÍA — connection_resolver.py SQL-FIRST\n\n")
md.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

md.append("## Referencias Mongo / SQL\n\n")
mongo_refs = 0
sql_refs = 0
for i, line in enumerate(lines, start=1):
    if re.search(r"mongo|pymongo|motor|get_mongo|_mongo_", line, re.I):
        md.append(f"- L{i} [MONGO]: `{line.strip()[:80]}`\n")
        mongo_refs += 1
    elif re.search(r"Servidores_Conexiones|EDARSAHUB|SQL|execute_sql|pyodbc|pymssql", line, re.I):
        md.append(f"- L{i} [SQL]: `{line.strip()[:80]}`\n")
        sql_refs += 1

md.append(f"\n**Total Mongo refs: {mongo_refs} | Total SQL refs: {sql_refs}**\n")

md.append("\n## Funciones / Clases\n\n")
for i, line in enumerate(lines, start=1):
    if re.match(r"^(class|def|async def)\s+", line):
        md.append(f"- L{i}: `{line.strip()[:70]}`\n")

md.append("\n## Consumidores del resolver\n\n")
consumers = []
for p in (ROOT / "backend").rglob("*.py"):
    if p == TARGET or ".bak" in str(p) or "__pycache__" in str(p):
        continue
    try:
        t = p.read_text(errors="ignore")
    except:
        continue
    if "connection_resolver" in t or "ConnectionResolver" in t:
        for j, line in enumerate(t.splitlines(), start=1):
            if "connection_resolver" in line or "ConnectionResolver" in line:
                consumers.append((p.relative_to(ROOT), j, line.strip()[:70]))

for rel, j, line in consumers[:30]:
    md.append(f"- `{rel}` L{j}: `{line}`\n")

md.append(f"\n**Total consumidores: {len(consumers)}**\n")

md.append("\n## Dictamen\n\n")
if mongo_refs > sql_refs:
    md.append("⚠️ **RIESGO**: Más referencias Mongo que SQL. Requiere migración P1.\n")
elif mongo_refs > 0:
    md.append("⚠️ **MIXTO**: Tiene referencias Mongo legacy. Evaluar si son productivas o fallback.\n")
else:
    md.append("✅ **SQL-FIRST**: Sin referencias Mongo productivas.\n")

OUT.write_text("".join(md), encoding="utf-8")
print(f"Reporte generado: {OUT}")
print(f"Mongo refs: {mongo_refs}, SQL refs: {sql_refs}")
