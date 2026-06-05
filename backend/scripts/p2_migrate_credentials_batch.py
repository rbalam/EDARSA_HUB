from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path("/app/backend")

TARGETS = [
    ROOT / "modules/finanzas",
    ROOT / "modules/compras",
    ROOT / "modules/sistema",
    ROOT / "modules/fase2_operativo",
]

IMPORT_LINE = "from core.config.edarsahub_config import get_edarsahub_sql_config"

REPLACEMENTS = {
    r"os\.getenv\(['\"]EDARSAHUB_SQL_HOST['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.host",
    r"os\.getenv\(['\"]EDARSAHUB_SQL_PORT['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.port",
    r"os\.getenv\(['\"]EDARSAHUB_SQL_DATABASE['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.database",
    r"os\.getenv\(['\"]EDARSAHUB_SQL_USER['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.user",
    r"os\.getenv\(['\"]EDARSAHUB_SQL_PASSWORD['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.password",

    r"os\.environ\.get\(['\"]EDARSAHUB_SQL_HOST['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.host",
    r"os\.environ\.get\(['\"]EDARSAHUB_SQL_PORT['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.port",
    r"os\.environ\.get\(['\"]EDARSAHUB_SQL_DATABASE['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.database",
    r"os\.environ\.get\(['\"]EDARSAHUB_SQL_USER['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.user",
    r"os\.environ\.get\(['\"]EDARSAHUB_SQL_PASSWORD['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.password",

    r"os\.getenv\(['\"]EDARSAHUB_HOST['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.host",
    r"os\.getenv\(['\"]EDARSAHUB_DATABASE['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.database",
    r"os\.getenv\(['\"]EDARSAHUB_USERNAME['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.user",
    r"os\.getenv\(['\"]EDARSAHUB_PASSWORD['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.password",

    r"os\.environ\.get\(['\"]EDARSAHUB_HOST['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.host",
    r"os\.environ\.get\(['\"]EDARSAHUB_DATABASE['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.database",
    r"os\.environ\.get\(['\"]EDARSAHUB_USERNAME['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.user",
    r"os\.environ\.get\(['\"]EDARSAHUB_PASSWORD['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)": "_edarsa_cfg.password",
}

def has_edarsa_ref(text):
    return bool(re.search(r"EDARSAHUB_(SQL_)?(HOST|PORT|DATABASE|USER|USERNAME|PASSWORD)", text))

def add_import_and_cfg(text):
    if IMPORT_LINE not in text:
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        text = "\n".join(lines) + "\n"

    cfg = "\n_edarsa_cfg = get_edarsahub_sql_config()\n"
    if "_edarsa_cfg = get_edarsahub_sql_config()" not in text:
        text = text.replace(IMPORT_LINE, IMPORT_LINE + cfg, 1)

    return text

changed = []
skipped = []

for base in TARGETS:
    if not base.exists():
        continue

    for p in base.rglob("*.py"):
        original = p.read_text(errors="ignore")
        if not has_edarsa_ref(original):
            continue

        updated = original
        for pat, repl in REPLACEMENTS.items():
            updated = re.sub(pat, repl, updated)

        if updated != original:
            updated = add_import_and_cfg(updated)

            backup = p.with_suffix(p.suffix + f".bak_credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(p, backup)
            p.write_text(updated)
            changed.append(str(p))
        else:
            skipped.append(str(p))

print("CAMBIADOS:")
for x in changed:
    print(x)

print("\nSIN CAMBIO AUTOMÁTICO:")
for x in skipped:
    print(x)

print(f"\nTOTAL CAMBIADOS: {len(changed)}")
print(f"TOTAL SIN CAMBIO: {len(skipped)}")
