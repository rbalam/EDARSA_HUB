from pathlib import Path
import re
from collections import defaultdict

ROOT = Path("/app/backend")

patterns = re.compile(
    r"EDARSAHUB_HOST|EDARSAHUB_DATABASE|EDARSAHUB_USERNAME|EDARSAHUB_PASSWORD|"
    r"EDARSAHUB_SQL_HOST|EDARSAHUB_SQL_DATABASE|EDARSAHUB_SQL_USER|EDARSAHUB_SQL_PASSWORD",
    re.I
)

ignore_parts = [
    ".bak_",
    "__pycache__",
    "core/config/",
]

non_productive_parts = [
    "/scripts/",
    "/tests/",
    "/test_",
    "/tools/",
    "/backups/",
    "/docs/",
    "audit_",
    "diagnostico",
    "diagnostic",
    "backup",
    "dryrun",
    "dry_run",
    "export_",
    "validate_",
]

rows = []

for p in ROOT.rglob("*.py"):
    rel = str(p.relative_to("/app"))

    if any(x in rel for x in ignore_parts):
        continue

    txt = p.read_text(errors="ignore")

    for i, line in enumerate(txt.splitlines(), start=1):
        if patterns.search(line):
            clasif = "NO_PRODUCTIVO" if any(x in rel.lower() for x in non_productive_parts) else "PRODUCTIVO_REVISAR"
            rows.append((clasif, rel, i, line.strip()))

summary = defaultdict(int)
by_file = defaultdict(int)

for clasif, rel, i, line in rows:
    summary[clasif] += 1
    by_file[(clasif, rel)] += 1

print("=== RESUMEN ===")
for k, v in sorted(summary.items()):
    print(f"  {k}: {v}")

print("\n=== TOP PRODUCTIVO_REVISAR ===")
for (clasif, rel), count in sorted(by_file.items(), key=lambda x: x[1], reverse=True):
    if clasif == "PRODUCTIVO_REVISAR":
        print(f"  {count} | {rel}")

print("\n=== TOP NO_PRODUCTIVO (primeros 30) ===")
cnt = 0
for (clasif, rel), count in sorted(by_file.items(), key=lambda x: x[1], reverse=True):
    if clasif == "NO_PRODUCTIVO":
        print(f"  {count} | {rel}")
        cnt += 1
        if cnt >= 30:
            break

out = Path("/app/docs/auditorias/P2_CREDENCIALES_RESTANTES_CLASIFICADAS_20260605.txt")
out.parent.mkdir(parents=True, exist_ok=True)

with out.open("w", encoding="utf-8") as f:
    f.write("P2 CREDENCIALES RESTANTES CLASIFICADAS\n\n")
    for clasif, rel, i, line in rows:
        safe = re.sub(r"(PASSWORD|PWD)([^\\n]*)", r"\1=***", line, flags=re.I)
        f.write(f"{clasif} | {rel}:{i} | {safe}\n")

print(f"\nReporte guardado: {out}")
