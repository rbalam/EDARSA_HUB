from pathlib import Path
import re
from datetime import datetime

ROOT = Path("/app/backend")
OUT = Path("/app/docs/auditorias/AUDITORIA_MONGO_LEGACY_20260604.md")

patterns = [
    r"pymongo",
    r"motor",
    r"mongodb",
    r"MongoClient",
    r"AsyncIOMotorClient",
]

allowed_context = [
    "backup",
    "migration",
    "migracion",
    "legacy",
    "test",
    "tests",
    "cache",
    "deprecado",
    "deprecated",
]

rows = []

for p in ROOT.rglob("*.py"):
    # Skip backups and pycache
    if ".bak" in str(p) or "__pycache__" in str(p) or "backup" in str(p).lower():
        continue
        
    try:
        text = p.read_text(errors="ignore")
    except:
        continue
        
    lines = text.splitlines()

    for i, line in enumerate(lines, start=1):
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            rel = str(p.relative_to("/app"))
            lower_path = rel.lower()
            lower_line = line.lower()

            if any(x in lower_path or x in lower_line for x in allowed_context):
                clasificacion = "REVISAR_PERMITIDO_TEMPORAL"
            else:
                clasificacion = "RIESGO_ALTO"

            rows.append({
                "archivo": rel,
                "linea": i,
                "codigo": line.strip(),
                "clasificacion": clasificacion,
            })

md = []
md.append("# AUDITORÍA MONGO LEGACY — EDARSAHUB\n\n")
md.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
md.append("Objetivo: localizar referencias MongoDB/pymongo/motor y clasificarlas para eliminación o justificación temporal.\n\n")

md.append("## Resumen\n\n")
md.append(f"- Hallazgos totales: **{len(rows)}**\n")
md.append(f"- Riesgo alto: **{sum(1 for r in rows if r['clasificacion']=='RIESGO_ALTO')}**\n")
md.append(f"- Revisar permitido temporal: **{sum(1 for r in rows if r['clasificacion']=='REVISAR_PERMITIDO_TEMPORAL')}**\n\n")

md.append("## Hallazgos RIESGO_ALTO\n\n")
md.append("| Archivo | Línea | Código |\n")
md.append("|---|---:|---|\n")

for r in rows:
    if r['clasificacion'] == 'RIESGO_ALTO':
        code = r["codigo"].replace("|", "\\|")
        if len(code) > 120:
            code = code[:120] + "..."
        md.append(f"| `{r['archivo']}` | {r['linea']} | `{code}` |\n")

md.append("\n## Hallazgos REVISAR_PERMITIDO_TEMPORAL\n\n")
md.append("| Archivo | Línea | Código |\n")
md.append("|---|---:|---|\n")

for r in rows:
    if r['clasificacion'] == 'REVISAR_PERMITIDO_TEMPORAL':
        code = r["codigo"].replace("|", "\\|")
        if len(code) > 120:
            code = code[:120] + "..."
        md.append(f"| `{r['archivo']}` | {r['linea']} | `{code}` |\n")

md.append("\n## Regla de cierre\n\n")
md.append("- MongoDB no debe ser fuente de verdad productiva.\n")
md.append("- Endpoints visuales no deben depender de MongoDB.\n")
md.append("- Usos permitidos temporalmente solo si están documentados como migración, backup, cache no autoritativo o pruebas.\n")
md.append("- Todo hallazgo RIESGO_ALTO debe migrarse a EDARSAHUB SQL o eliminarse.\n")

OUT.write_text("".join(md), encoding="utf-8")

print(f"Reporte generado: {OUT}")
print(f"Hallazgos totales: {len(rows)}")
print(f"Riesgo alto: {sum(1 for r in rows if r['clasificacion']=='RIESGO_ALTO')}")
print(f"Revisar permitido temporal: {sum(1 for r in rows if r['clasificacion']=='REVISAR_PERMITIDO_TEMPORAL')}")
