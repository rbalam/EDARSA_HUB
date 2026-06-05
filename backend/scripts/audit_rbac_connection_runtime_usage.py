from pathlib import Path
import re

ROOT = Path("/app/backend")

# Verificar si _get_db() es realmente llamado
print("="*80)
print("ANÁLISIS: ¿_get_db() es usado en rbac/middleware.py?")
print("="*80)

middleware = ROOT / "core/rbac/middleware.py"
txt = middleware.read_text()

# Buscar llamadas a _get_db()
calls = []
for i, line in enumerate(txt.splitlines(), start=1):
    if "_get_db()" in line and "def _get_db" not in line:
        calls.append((i, line.strip()))

print(f"\nLlamadas a _get_db() dentro de middleware.py: {len(calls)}")
for i, line in calls:
    print(f"  L{i}: {line[:80]}")

# Verificar qué hace RBACDependency
print("\n" + "="*80)
print("ANÁLISIS: RBACDependency - ¿usa MongoDB o SQL?")
print("="*80)

# Buscar el código de RBACDependency.__call__
in_rbac = False
rbac_code = []
for i, line in enumerate(txt.splitlines(), start=1):
    if "class RBACDependency" in line:
        in_rbac = True
    if in_rbac:
        rbac_code.append((i, line))
        if line.strip().startswith("class ") and "RBACDependency" not in line:
            break

print("\nCódigo de RBACDependency:")
for i, line in rbac_code[:50]:
    if "get_current_user" in line or "verify" in line or "db" in line.lower():
        print(f"  L{i}: {line.rstrip()[:90]}")

# Verificar si get_current_user_from_token usa MongoDB
print("\n" + "="*80)
print("ANÁLISIS: get_current_user_from_token - fuente de datos")
print("="*80)

for i, line in enumerate(txt.splitlines(), start=1):
    if i >= 43 and i <= 60:
        print(f"L{i}: {line.rstrip()[:90]}")

