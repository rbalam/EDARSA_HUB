from pathlib import Path
import re

root = Path("/app/backend")
py_files = list(root.rglob("*.py"))

# Excluir backups y auditorías
exclude_patterns = ['backup', 'auditorias_p', '.bak', 'test_']

mongo_hits = []
imports_hits = []

for py in py_files:
    # Skip excluded files
    if any(ex in str(py) for ex in exclude_patterns):
        continue
    try:
        txt = py.read_text(encoding="utf-8")
    except Exception:
        continue

    if re.search(r'from pymongo|import pymongo|MongoClient', txt):
        imports_hits.append(str(py))

    for m in re.finditer(r'db\.[A-Za-z_][A-Za-z0-9_]*', txt):
        mongo_hits.append((str(py), m.group(0)))

print("=== IMPORTS PYMONGO / MONGOCLIENT ===")
for x in imports_hits:
    print(x)

print(f"\nTotal archivos con imports: {len(imports_hits)}")

print("\n=== REFERENCIAS db.* (agrupadas) ===")
from collections import Counter
refs = Counter([ref for _, ref in mongo_hits])
for ref, count in refs.most_common(30):
    print(f"  {ref}: {count}")

print(f"\nTotal referencias db.*: {len(mongo_hits)}")
