from pathlib import Path
import re
from datetime import datetime

ROOT = Path("/app")
BACKEND = ROOT / "backend"
OUT = ROOT / "docs/auditorias/AUDITORIA_MONGO_RUTAS_ACTIVAS_20260604.md"

mongo_files = []
for p in BACKEND.rglob("*.py"):
    # Skip backups
    if ".bak" in str(p) or "__pycache__" in str(p) or "backup" in str(p).lower():
        continue
    try:
        txt = p.read_text(errors="ignore")
    except:
        continue
    if re.search(r"from\s+motor|from\s+pymongo|import\s+motor|import\s+pymongo|MongoClient|AsyncIOMotorClient", txt):
        mongo_files.append(p)

route_files = []
for p in BACKEND.rglob("*.py"):
    if ".bak" in str(p) or "__pycache__" in str(p) or "backup" in str(p).lower():
        continue
    try:
        txt = p.read_text(errors="ignore")
    except:
        continue
    if re.search(r"@router\.|@app\.", txt):
        route_files.append(p)

def imports_module(route_text, mongo_path):
    rel = mongo_path.relative_to(BACKEND).with_suffix("")
    dotted = ".".join(rel.parts)
    base = mongo_path.stem

    patterns = [
        rf"from\s+{re.escape(dotted)}\s+import",
        rf"import\s+{re.escape(dotted)}",
        rf"from\s+.*\.{re.escape(base)}\s+import",
        rf"from\s+{re.escape(base)}\s+import",
    ]
    return any(re.search(p, route_text) for p in patterns)

md = []
md.append("# AUDITORÍA MONGO — RUTAS ACTIVAS\n\n")
md.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
md.append("Objetivo: identificar si archivos con MongoDB son consumidos por rutas/endpoints activos.\n\n")

md.append("## Archivos con MongoDB detectados\n\n")
md.append(f"Total: {len(mongo_files)}\n\n")
for f in sorted(mongo_files):
    md.append(f"- `{f.relative_to(ROOT)}`\n")

md.append("\n## Archivos con rutas activas\n\n")
md.append(f"Total: {len(route_files)}\n\n")

md.append("\n## Cruce: Rutas que importan archivos Mongo\n\n")
riesgos = []

for mf in mongo_files:
    consumers = []
    for rf in route_files:
        try:
            txt = rf.read_text(errors="ignore")
        except:
            continue
        if imports_module(txt, mf):
            consumers.append(rf)

    if consumers:
        riesgos.append((mf, consumers))

if not riesgos:
    md.append("No se detectaron cruces directos usando patrones de import.\n\n")
else:
    md.append("| Archivo Mongo | Ruta activa consumidora | Riesgo |\n")
    md.append("|---|---|---|\n")
    for mf, consumers in riesgos:
        for c in consumers:
            md.append(f"| `{mf.relative_to(ROOT)}` | `{c.relative_to(ROOT)}` | ALTO |\n")

md.append("\n## Clasificación\n\n")
md.append("- Todo riesgo ALTO debe auditarse manualmente por función.\n")
md.append("- Si participa en endpoint visual/productivo, migrar a EDARSAHUB SQL.\n")
md.append("- Si es solo migración/cache/test, documentar como permitido temporal.\n")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("".join(md), encoding="utf-8")

print(f"Reporte generado: {OUT}")
print(f"Archivos Mongo: {len(mongo_files)}")
print(f"Archivos con rutas: {len(route_files)}")
print(f"Cruces detectados: {sum(len(c) for _, c in riesgos)}")
