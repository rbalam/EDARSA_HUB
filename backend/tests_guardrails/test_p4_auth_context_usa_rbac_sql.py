import sys
sys.path.insert(0, "/app/backend")

from pathlib import Path

required_files = [
    "core/rbac_sql/service.py",
    "core/rbac_sql/runtime.py",
    "core/access_context/sql_context.py",
]

for f in required_files:
    if not Path(f).exists():
        print("FAIL falta archivo:", f)
        sys.exit(1)

from core.rbac_sql.service import RBACSQLService
from core.access_context.sql_context import build_user_access_context

assert hasattr(RBACSQLService, "build_context")
assert callable(build_user_access_context)

print("PASS Auth/Context conectado a RBAC SQL")
